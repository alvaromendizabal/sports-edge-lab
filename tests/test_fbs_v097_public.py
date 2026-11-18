"""Focused contracts for the verified actual-return public projection.

These are offline engineering checks. They do not fit models, query providers,
modify owner checkpoints or launch an owner execution.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fbs_v097_review', ROOT / 'examples/fbs_contracts/v097/build_review.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
DATA = json.loads(BUILD.DATA.read_text())


class ActualReturnContracts(unittest.TestCase):
    def reject(self, change):
        mutated = copy.deepcopy(DATA)
        change(mutated)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            BUILD.validate(mutated)

    def test_committed_html_is_deterministic_and_self_contained(self):
        output = BUILD.render(DATA)
        self.assertEqual(output, BUILD.OUTPUT.read_bytes())
        self.assertEqual(output, BUILD.render(copy.deepcopy(DATA)))
        html = output.decode()
        self.assertFalse(re.search(r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://', html))
        self.assertNotIn('fetch(', html)

    def test_embedded_evidence_is_exact_and_bound_to_digest(self):
        html = BUILD.OUTPUT.read_text()
        raw = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(raw), DATA)
        self.assertIn("expected='" + hashlib.sha256(raw.encode()).hexdigest() + "'", html)

    def test_publication_does_not_claim_deployment_or_other_owner(self):
        for field, value in [('owner', 'NBA'), ('extra_private_payload', {})]:
            with self.subTest(field=field):
                self.reject(lambda d: d.update({field:value}))
        self.reject(lambda d: d['publication'].update(website_deployed=True))
        self.reject(lambda d: d['execution'].update(raw_path='/home/private-owner/return'))

    def test_operational_closure_and_scientific_completion_stay_separate(self):
        self.reject(lambda d: d['execution'].update(child_exit_code=1))
        self.reject(lambda d: d['execution'].update(scientific_complete=True))
        self.reject(lambda d: d['execution'].update(return_integrity_verified=False))

    def test_tally_counts_authenticated_attempt_once(self):
        self.reject(lambda d: d['execution'].update(historical_failed_attempts=7))
        self.reject(lambda d: d['execution'].update(operationally_finished_attempts=0))
        self.reject(lambda d: d['execution'].update(fully_v13_complete_attempts=1))

    def test_reuse_and_calibrators_are_not_new_base_fits(self):
        self.reject(lambda d: d['execution'].update(new_model_fits=936))
        self.reject(lambda d: d['execution']['branch_counts'][0].update(new_model_fits=306))
        self.reject(lambda d: d['cpu'].update(gate_completions_include_calibrators=False))

    def test_earlier_qualifying_window_survives_queue_exhaustion(self):
        self.reject(lambda d: d['cpu'].update(useful_gate_status='CONDITIONAL_INSUFFICIENT_INDEPENDENT_WORK'))
        self.reject(lambda d: d['cpu'].update(useful_gate_seconds=179))
        self.reject(lambda d: d['cpu'].update(useful_gate_workers=24))
        self.reject(lambda d: d['cpu'].update(gate_includes_preparation=False))

    def test_phase_cpu_and_queue_wait_definitions_cannot_be_swapped(self):
        self.reject(lambda d: d['cpu'].update(optimizer_cpu_seconds=d['cpu']['scoring_cpu_seconds']))
        self.reject(lambda d: d['cpu'].update(legacy_not_ready_includes_busy_preparation=False))
        self.reject(lambda d: d['cpu'].update(pending_preparation_with_idle_slots_seconds=100))

    def test_selection_uses_validation_only_without_refit(self):
        self.reject(lambda d: d['selection'].update(test_used_for_selection=True))
        self.reject(lambda d: d['selection'].update(season_training_weights=True))
        self.reject(lambda d: d['selection'].update(sensitivity_refits=1))
        self.reject(lambda d: d['selection']['leaders'][0].update(selection_score=0.99))

    def test_all_objectives_and_sensitivity_ranks_remain_present(self):
        self.assertEqual(len(DATA['selection']['leaders']), 45)
        self.reject(lambda d: d['selection']['leaders'].pop())
        self.reject(lambda d: d['selection']['leaders'][0].update(primary_policy_rank=2))
        self.reject(lambda d: d['selection']['leaders'][0].update(same_policy_as_primary=False))

    def test_full_known_denominators_do_not_certify_official_census(self):
        self.reject(lambda d: d['selection']['leaders'][0].update(scored_n=[919,934,752]))
        self.reject(lambda d: d['population'].update(official_population_complete=True))
        self.reject(lambda d: d['population']['retained_pending_groups'][0].update(covered=133))
        self.reject(lambda d: d['selection'].update(test_previously_exposed=False))

    def test_source_coverage_keeps_market_benchmarks_and_clocks_separate(self):
        self.reject(lambda d: d['sources'].update(coverage_is_scored_benchmark=True))
        self.reject(lambda d: d['sources'].update(historical_possession_created=True))
        self.reject(lambda d: d['sources']['t120_completed_coverage'][0].update(expected_n=1))
        self.reject(lambda d: d['sources']['t120_completed_coverage'].pop())

    def test_storage_and_cost_do_not_hide_scope(self):
        self.reject(lambda d: d['storage'].update(new_scientific_payload_bytes=d['storage']['control_zip_bytes']))
        self.reject(lambda d: d['storage'].update(aggregate_science_cap=512*1024*1024))
        self.reject(lambda d: d['next_preparation']['summary_comparison'].update(future_total_return_size_claimed=True))
        self.reject(lambda d: d['cost'].update(invoice=True))
        self.reject(lambda d: d['cost'].update(wall_zero_waives_guard=True))

    def test_preparation_cannot_become_executed_or_unverified_installed(self):
        self.reject(lambda d: d['next_preparation'].update(owner_runs_launched=1))
        self.reject(lambda d: d['next_preparation'].update(status='PREPARED_NOT_EXECUTED', native_verified=False))
        self.reject(lambda d: d['next_preparation'].update(planned_jobs_are_new_fit_promise=True))
        self.reject(lambda d: d['next_preparation'].update(reuse_completed_registered_jobs=0))

    def test_public_projection_preserves_dated_history(self):
        pinned = {
            'docs/fbs/v093/index.html':'97491a5a0265a88a2b3e0837028800cebf5cf6244b220d3689f1fef392513281',
            'docs/fbs/v093/data/status.json':'24bf5f275b0dadecf5f5cbbf2822708e58bf25a6713228828972cf799976095c',
            'examples/fbs_contracts/v093/build_review.py':'7be816e96cb58cd2c6eb2108f14b74338f2a08e572bd46ac85891ed940e52cd4',
        }
        for relative, digest in pinned.items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
