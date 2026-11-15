"""Contracts for the dated NCAA current-game and model/market publication."""
from __future__ import annotations

import base64
from collections import Counter
from datetime import datetime
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs/ncaa'
DATA = json.loads((DOCS / 'v12_r14_public_evidence.json').read_text())
UNCERTAINTY = json.loads((DOCS / 'v12_r14_descriptive_uncertainty.json').read_text())


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.ids.append(values['id'])
        if tag == 'a' and values.get('href'):
            self.links.append(values['href'])


class CurrentSnapshotTests(unittest.TestCase):
    def test_snapshot_is_dated_and_incomplete(self):
        self.assertEqual(DATA['schema'], 'sel.ncaa.public.v12.r14.v1')
        self.assertEqual(DATA['census_asof'], '2026-11-15T01:37:50.675790+00:00')
        self.assertFalse(DATA['coverage']['complete_official_season_universe'])
        self.assertFalse(DATA['coverage']['all_provider_history_complete'])
        self.assertFalse(DATA['selection']['current_champion_established'])
        self.assertFalse(DATA['selection']['new_three_season_weighted_leaderboard_complete'])

    def test_game_counts_close_without_mixing_denominators(self):
        self.assertEqual(len(DATA['games']), 2503)
        self.assertEqual(Counter(r['league'] for r in DATA['games']), {'ncaam': 1255, 'ncaaw': 1248})
        expected = {'ncaam': {'completed': 791, 'scheduled': 439, 'in_progress': 22, 'source_status_unqualified': 3},
                    'ncaaw': {'completed': 790, 'scheduled': 455, 'in_progress': 1, 'source_status_unqualified': 2}}
        for league, counts in expected.items():
            self.assertEqual(Counter(r['status'] for r in DATA['games'] if r['league'] == league), counts)
        self.assertEqual(DATA['coverage']['official_observed_records'], 2516)
        self.assertEqual(DATA['coverage']['exact_reconciled_source_identities'] + DATA['coverage']['source_records_without_qualified_official_binding'], 2503)
        self.assertEqual(DATA['coverage']['missing_source_dates'], 7)

    def test_public_game_keys_and_fields_are_bounded(self):
        keys = [r['game_key'] for r in DATA['games']]
        self.assertEqual(len(set(keys)), 2503)
        allowed = {'game_key', 'league', 'away_team', 'home_team', 'event_time', 'status',
                   'away_score', 'home_score', 'source_observed_at', 'model_evidence_status',
                   'model_issued_forecast', 'provider_comparison_status'}
        for row in DATA['games']:
            self.assertEqual(set(row), allowed)
            self.assertRegex(row['game_key'], r'^[0-9a-f]{20}$')
            self.assertFalse(row['model_issued_forecast'])

    def test_final_scores_and_future_clocks_are_separate(self):
        asof = datetime.fromisoformat(DATA['census_asof'])
        future = Counter()
        passed = Counter()
        for row in DATA['games']:
            self.assertLessEqual(datetime.fromisoformat(row['source_observed_at']), asof)
            if row['status'] == 'completed':
                self.assertIsInstance(row['away_score'], (int, float))
                self.assertIsInstance(row['home_score'], (int, float))
            if row['status'] == 'scheduled':
                target = future if datetime.fromisoformat(row['event_time'].replace('Z', '+00:00')) > asof else passed
                target[row['league']] += 1
        self.assertEqual(future, {'ncaam': 438, 'ncaaw': 455})
        self.assertEqual(passed, {'ncaam': 1})

    def test_current_models_cannot_be_promoted_or_called_issued(self):
        self.assertEqual(len(DATA['current_models']), 6)
        pairs = {(r['league'], r['target']) for r in DATA['current_models']}
        self.assertEqual(pairs, {(l, t) for l in ['ncaam', 'ncaaw'] for t in ['win', 'margin', 'total']})
        for row in DATA['current_models']:
            self.assertEqual(row['games'], 578 if row['league'] == 'ncaam' else 585)
            self.assertEqual(row['horizon_minutes'], 60)
            self.assertEqual(row['evidence_class'], 'RETROSPECTIVE_RECONSTRUCTION')
            self.assertEqual(row['issued_forecast_credit'], 0)
            self.assertEqual(row['competing_models_on_cohort'], 0)
            self.assertFalse(row['promotion_authority'])
        for value in DATA['current_scored_coverage'].values():
            self.assertEqual(value['scored'] + value['without_this_score'], value['completed'])

    def test_current_winner_metric_values_are_preserved(self):
        actual = {r['league']: r['metrics'] for r in DATA['current_models'] if r['target'] == 'win'}
        self.assertAlmostEqual(actual['ncaam']['accuracy'], 0.7889273356401384)
        self.assertAlmostEqual(actual['ncaam']['log_loss'], 0.418217972049612)
        self.assertAlmostEqual(actual['ncaam']['brier'], 0.13691177050794198)
        self.assertAlmostEqual(actual['ncaaw']['accuracy'], 0.8170940170940171)
        self.assertAlmostEqual(actual['ncaaw']['log_loss'], 0.35896524828486986)
        self.assertAlmostEqual(actual['ncaaw']['brier'], 0.11606122335086849)

    def test_missing_provider_metrics_stay_null(self):
        rows = DATA['provider_comparisons']
        self.assertEqual(len(rows), 8)
        self.assertEqual({(r['league'], r['provider_product']) for r in rows},
                         {(l, p) for l in ['ncaam', 'ncaaw'] for p in ['draftkings_us', 'kalshi_us', 'polymarket_international', 'polymarket_us']})
        for row in rows:
            self.assertEqual(row['candidate_games'], 578 if row['league'] == 'ncaam' else 585)
            self.assertEqual(row['matched_games'], 0)
            self.assertEqual(row['target'], 'win')
            self.assertEqual(row['horizon_minutes'], 60)
            for key in ['model_log_loss', 'provider_log_loss', 'model_brier', 'provider_brier']:
                self.assertIsNone(row[key])
            self.assertEqual(row['provider_evidence_class'], 'NO_QUALIFIED_QUOTES')

    def test_per_game_gap_scope_is_not_whole_season(self):
        counts = Counter(r['provider_comparison_status'] for r in DATA['games'])
        self.assertEqual(counts['No qualified winner pair in the scored aggregate cohort'], 1163)
        self.assertEqual(counts['Outside the scored aggregate cohort; per-game provider coverage not established'], 1340)
        self.assertNotIn('provider_price', (DOCS / 'v12_r14_public_evidence.json').read_text())

    def test_historical_roles_stay_outside_current_selection(self):
        self.assertEqual(len(DATA['historical_roles']), 14)
        for row in DATA['historical_roles']:
            self.assertEqual(set(row['seasons']), {'2025', '2026'})
            self.assertEqual(row['evidence_class'], 'EXPOSED_HISTORICAL_RESEARCH')
            self.assertFalse(row['independent_confirmation'])
            self.assertFalse(row['promotion_authority'])
            self.assertEqual(row['games'], sum(s['games'] for s in row['seasons'].values()))

    def test_execution_credit_remains_typed(self):
        value = DATA['execution']
        self.assertEqual((value['new_target_fits'], value['new_scalar_calibration_fits'], value['verified_reused_target_fits']), (0, 2, 60))
        self.assertEqual(value['reused_historical_target_study_fits'], 108)
        self.assertEqual(value['new_issued_forecasts'], 0)
        self.assertEqual(value['automatic_promotions'], 0)
        self.assertEqual(value['requested_cores'], 42)
        self.assertEqual(value['selected_capacity_acceptance'], 'NOT_DEMONSTRATED')

    def test_latest_execution_is_r15_and_comparison_remains_r14(self):
        value = DATA['latest_execution']
        self.assertEqual(value['return_release'], 'R15')
        self.assertEqual(DATA['return_release'], 'R14')
        self.assertEqual(value['status'], 'ADMISSION_DEFERRED')
        self.assertEqual((value['new_target_fits'], value['new_scalar_calibration_fits'], value['verified_reused_target_fits']), (0, 0, 0))
        self.assertEqual(value['recovered_checkpoint_references'], 2793)
        self.assertFalse(value['checkpoint_references_are_fit_credit'])
        self.assertEqual(value['requested_cores'], 48)
        self.assertEqual(value['leased_cores_at_deferral'], 1)
        self.assertEqual(value['memory_full_pressure_avg10'], 3.1)
        self.assertEqual(value['cause_diagnosis'], 'FRESH_PRESSURE_GATE_CHECKPOINT_WAIT_EXHAUSTED')
        self.assertAlmostEqual(value['checkpoint_admission_wait_seconds'], 15.016700029998901)
        self.assertEqual(value['memory_full_pressure_avg10_during_later_packaging'], 0.93)
        self.assertEqual(value['pressure_blockers_during_later_packaging'], [])
        self.assertFalse(value['science_resumed_after_pressure_recovered'])
        self.assertFalse(value['new_comparison_completed'])
        self.assertFalse(value['new_source_refresh_claimed'])
        self.assertAlmostEqual(value['summary_elapsed_seconds_before_return_finalization'], 109.5966174669993)
        self.assertAlmostEqual(value['startup_fixture_tests_seconds'], 88.14597212800072)
        self.assertAlmostEqual(value['science_phase_seconds_before_first_numbered_stage'], 16.016921452001043)
        self.assertEqual(value['return_published_at'], '2026-11-15T04:23:50+00:00')
        self.assertEqual(value['selected_capacity_acceptance'], 'NOT_DEMONSTRATED')

    def test_r14_scientific_snapshot_is_unchanged_by_r15_status(self):
        preserved = {key: value for key, value in DATA.items() if key != 'latest_execution'}
        serialized = json.dumps(preserved, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(serialized).hexdigest(), '75aa87382b79c7f44f5f3442fa043e7fcafbf66b875ff3937afc361b582c8b06')

    def test_latest_execution_and_preserved_science_are_explicit_in_page(self):
        page = (DOCS / 'v12.html').read_text()
        self.assertIn('Latest execution: R15 deferred. Latest model comparison: R14.', page)
        self.assertIn('memory-pressure admission deferral during checkpoint authentication', page)
        self.assertIn('109.60 seconds before return finalization', page)
        self.assertIn('1 core leased at the failure-time admission decision', page)
        self.assertIn('id="prior-execution-r14"', page)
        self.assertIn('2,793 recovered checkpoint references are references, not model fits', page)

    def test_uncertainty_audit_is_descriptive_and_uses_unchanged_cohort(self):
        value = UNCERTAINTY
        self.assertEqual(value['analysis_role'], 'POST_HOC_DESCRIPTIVE_AUDIT_OF_KNOWN_METRICS')
        self.assertEqual(value['scientific_comparison_return'], 'R14')
        self.assertEqual(value['replicates'], 10000)
        self.assertEqual(value['confidence_level'], .95)
        for key in ['new_fits', 'new_calibrators', 'new_forecasts', 'provider_calls', 'model_promotions', 'original_issued_forecast_credit']:
            self.assertEqual(value[key], 0)
        for league, row in value['leagues'].items():
            self.assertEqual(row['n_games'], 578 if league == 'ncaam' else 585)
            self.assertEqual(row['utc_date_clusters'], 14)
            self.assertEqual(row['model_count_in_this_comparison'], 1)
            self.assertEqual(row['market_prices_used'], 0)
        self.assertTrue(any('Repeated teams' in item for item in value['limitations']))
        self.assertIn('selected cohort', (DOCS / 'v12.html').read_text())

    def test_uncertainty_estimates_match_preserved_model_scorecards(self):
        for model in DATA['current_models']:
            prefix = '' if model['target'] == 'win' else model['target'] + '_'
            for metric, estimate in model['metrics'].items():
                key = prefix + metric
                if key not in UNCERTAINTY['leagues'][model['league']]['metrics']:
                    continue
                interval = UNCERTAINTY['leagues'][model['league']]['metrics'][key]
                self.assertAlmostEqual(interval['estimate'], estimate, places=12)
                self.assertLessEqual(interval['lower95'], interval['estimate'])
                self.assertLessEqual(interval['estimate'], interval['upper95'])
        men = UNCERTAINTY['leagues']['ncaam']['metrics']['accuracy']
        women = UNCERTAINTY['leagues']['ncaaw']['metrics']['accuracy']
        self.assertAlmostEqual(men['lower95'], .7333333333333333)
        self.assertAlmostEqual(men['upper95'], .8374487414387297)
        self.assertAlmostEqual(women['lower95'], .7828442375411021)
        self.assertAlmostEqual(women['upper95'], .8507800045097256)

    def test_public_surfaces_have_no_private_fields_or_other_contest_marker(self):
        excluded_contest = ''.join(map(chr, [99, 105, 114, 99, 97]))
        for name in ['v12.html', 'v12_r14_public_evidence.json', 'v12_r14_descriptive_uncertainty.json', 'v11.html', 'v10.html']:
            text = (DOCS / name).read_text()
            decoded = []
            for attrs, payload in re.findall(r'<script([^>]*)>(.*?)</script>', text, re.S):
                if 'application/octet-stream' in attrs:
                    decoded.append(gzip.decompress(base64.b64decode(payload)).decode())
            surface = '\n'.join([text, *decoded]).lower()
            for marker in [excluded_contest, 's3://', 'arn:aws', 'secret_access_key', '/home/sagemaker-user']:
                self.assertNotIn(marker, surface, name)
        current = (DOCS / 'v12_r14_public_evidence.json').read_text()
        for marker in ['chosen_recipe', 'ordered_columns', 'model_sha256', 'raw_reference', 'source_manifest', 'B032_', 'espn:event:']:
            self.assertNotIn(marker, current)

    def test_navigation_and_current_archive_links(self):
        page = Page()
        page.feed((DOCS / 'v12.html').read_text())
        self.assertEqual(len(page.ids), len(set(page.ids)))
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            if parts.path:
                self.assertTrue((DOCS / parts.path).exists(), link)
            elif parts.fragment:
                self.assertIn(parts.fragment, page.ids)
        for name in ['index.html', 'v11.html']:
            text = (DOCS / name).read_text()
            self.assertIn('id="v12-current-evidence"', text)
            self.assertIn('href="v12.html"', text)

    def test_browser_script_logic_in_dom_harness(self):
        self.assertIsNotNone(shutil.which('node'), 'The existing dashboard test contract requires Node.js.')
        result = subprocess.run(['node', str(Path(__file__).with_name('test_v12_dashboard.cjs'))], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS', result.stdout)


if __name__ == '__main__':
    unittest.main()
