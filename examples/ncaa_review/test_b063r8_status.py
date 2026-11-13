"""R7 waiting cannot be upgraded to new science; older evidence remains exact."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch
import b063r8_status as status

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/ncaa'
EX=ROOT/'examples/ncaa_review'
R8_LINE=b"    counts.b063r8Status = await require('./test_b063r8_status_browser.cjs').verifyR8(browser, path.join(root, 'docs/ncaa/b063r8.html'));\n"


def blob(body):
    return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()


class B063R8PublicStatus(unittest.TestCase):
    def setUp(self):
        self.data=status.load_payload()

    def test_actual_admission_wait_has_zero_scientific_credit(self):
        actual=self.data['latest_actual_owner']
        self.assertEqual(actual['release'],'B063R7')
        self.assertEqual(actual['new_owner_fits'],0)
        self.assertEqual(actual['scientific_fit_attempts'],0)
        self.assertFalse(actual['native_preflight_entered'])
        self.assertFalse(actual['selftests_entered'])
        self.assertFalse(actual['full_scientific_run_completed'])
        self.assertAlmostEqual(actual['admission_phase_seconds'],120.02053888299997)

    def test_measured_CPU_headroom_is_not_a_resource_grant(self):
        admission=self.data['actual_admission']
        self.assertEqual(admission['decisions'],118)
        self.assertEqual(admission['reason_counts'],{'IO_FULL_PRESSURE':118})
        self.assertEqual(admission['reserved_cpus'],0)
        self.assertEqual(admission['cpu_ready_observations'],117)
        self.assertFalse(admission['available_CPU_is_safe_IO_capacity'])
        self.assertEqual(admission['observation_bounds']['available_cpu_cores'],
            {'observations':117,'minimum':45.717489343521706,'maximum':46.98019801980198})
        self.assertEqual(admission['observation_bounds']['io_full_avg10'],
            {'observations':118,'minimum':27.69,'maximum':41.29})

    def test_actual_logging_prefix_and_CPU_scopes_are_explicit(self):
        observer=self.data['actual_observer']
        self.assertEqual((observer['JSONL_rows'],observer['human_event_records'],observer['human_physical_lines']),(33,33,93))
        self.assertEqual(observer['heartbeats'],15)
        self.assertTrue(observer['heartbeat_interval_verified'])
        self.assertLess(observer['maximum_monotonic_heartbeat_gap_seconds'],15)
        self.assertEqual(observer['terminal_publisher_sequence'],47)
        self.assertTrue(observer['terminal_flush_acknowledged'])
        self.assertFalse(observer['complete_terminal_log_claimed'])
        self.assertTrue(observer['post_capture_events_remain_external'])
        self.assertEqual(observer['scientific_workers'],0)
        self.assertAlmostEqual(observer['admission_owner_CPU_seconds'],0.851888)

    def test_uninitialized_cache_is_not_zero_download_acceptance(self):
        cache=self.data['actual_cache_and_cost']
        self.assertFalse(cache['store_initialized'])
        self.assertFalse(cache['historical_cache_benchmark_exercised'])
        self.assertFalse(cache['zero_defaults_measure_all_S3_calls'])
        self.assertTrue(cache['return_persistence_is_separate'])
        self.assertIsNone(cache['estimated_cost_usd'])

    def test_saved_champion_populations_and_clocks_remain_exact(self):
        science=self.data['preserved_science']
        original=(DOC/'data/NCAA_B063R2_PUBLIC_SCIENTIFIC_TABLES.json').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),science['source_sha256'])
        self.assertEqual(science['evidence_asof'],'2026-11-11T22:39:45.642794+00:00')
        rows=science['current_observed_replay_leaders']
        for league,games in [('ncaam',420),('ncaaw',403)]:
            group=[x for x in rows if x['league']==league]
            self.assertEqual({x['metric_name_for_display'] for x in group},set(self.data['metric_policy']['metrics']))
            self.assertTrue(all(x['games']==games and x['evaluation_mode']=='retrospective_reconstructed' for x in group))
            self.assertTrue(all(not x['selection_or_promotion_authority'] and not x['full_official_season_coverage_certified'] for x in group))
        self.assertEqual((science['historical_candidate_metric_panels'],science['historical_per_season_leaders'],science['historical_pooled_leaders']),(164,28,14))

    def test_run_scoped_recovery_counts_are_not_added_or_retrained(self):
        saved=self.data['preserved_evidence']
        self.assertEqual((saved['authenticated_prior_target_fits'],saved['exact_content_objects_reverified']),(22,134))
        self.assertEqual((saved['broader_B062_target_fit_receipts'],saved['broader_B062_terminal_commit_references']),(115,2793))
        self.assertFalse(saved['distinct_run_inventories_summed'])
        self.assertFalse(saved['all_broader_model_bytes_reopened'])
        self.assertEqual(saved['new_fit_credit_for_preservation'],0)

    def test_prior_landing_and_dated_reports_remain_identical(self):
        pins=self.data['source_attribution']['preserved_git_blobs']
        body=(DOC/'index.html').read_text()
        self.assertEqual(blob(status.strip_banner(body).encode()),pins['docs/ncaa/index.html'])
        for path,expected in pins.items():
            if path.startswith('docs/ncaa/') and path!='docs/ncaa/index.html':
                self.assertEqual(blob((ROOT/path).read_bytes()),expected,path)
        readme=(EX/'README.md').read_bytes().split(b'<!-- B063R8_STATUS_END -->\n\n',1)[1]
        self.assertEqual(blob(readme),pins['examples/ncaa_review/README.md'])
        browser=(EX/'test_dashboard_browser.cjs').read_bytes().replace(R8_LINE,b'')
        self.assertEqual(blob(browser),pins['examples/ncaa_review/test_dashboard_browser.cjs'])

    def test_render_download_and_banner_are_exact_and_idempotent(self):
        page=(DOC/'b063r8.html').read_text()
        match=re.search(r'<script id="b063r8-data" type="application/json">(.*?)</script>',page,re.S)
        self.assertEqual(json.loads(match.group(1)),self.data)
        self.assertEqual(json.loads((DOC/'data/B063R8_PUBLIC_STATUS.json').read_text()),self.data)
        self.assertEqual(page,status.render_page())
        self.assertNotIn('__B063R8_',page)
        self.assertIn('new Blob([exact]',page)
        self.assertEqual(status.render_banner((DOC/'index.html').read_text()),(DOC/'index.html').read_text())
        self.assertEqual(page.count('<tr>'),15)

    def test_prepared_policy_stays_qualified_and_bounded(self):
        prepared=self.data['prepared_continuation']
        self.assertEqual(prepared['release'],'B063R8')
        self.assertTrue(prepared['CPU_and_IO_admission_separated'])
        self.assertEqual(prepared['moderate_IO_aggregate_lanes_per_owner'],1)
        self.assertTrue(prepared['severe_or_unknown_IO_deferred'])
        self.assertTrue(prepared['CPU_memory_disk_fairness_guards_retained'])
        self.assertFalse(prepared['owner_execution_verified'])
        self.assertFalse(prepared['scientific_twelve_core_acceptance_passed'])
        if prepared['source_sha256'] is not None:
            continuity=prepared['science_identity_continuity']
            self.assertEqual(continuity['fitted_family_identities_unchanged'],7)
            self.assertTrue(continuity['all_seven_fitted_families_preserved'])
            self.assertTrue(continuity['rolling_v7_execution_identity_changed'])
            self.assertFalse(continuity['all_eight_unchanged_claimed'])
            self.assertEqual(continuity['exact_prior_archive_reconstructions'],['B062','B063R2','B063R3','B063R4','B063R5','B063R6','B063R7'])

    def test_dated_sealed_shared_logger_binding_preserves_generic_source(self):
        prepared=self.data['prepared_continuation'];binding=prepared['shared_logger_binding']
        self.assertEqual(binding['module_sha256'],'607954a6f5dc4eba98e3edd121360d52aa00ff4a148c8630dd79f125b44b6947')
        self.assertEqual(binding['module_bytes'],61565)
        self.assertEqual(binding['matching_test_sha256'],'be68fabfddb481a0859d6bde4d8775d10f06b281b7055f8466aaca7d54e18a89')
        self.assertEqual(binding['matching_test_bytes'],24774)
        self.assertTrue(binding['generic_fit_scope_metadata_and_measured_human_log_PIDs'])
        self.assertFalse(binding['public_shared_files_modified'])
        self.assertTrue(binding['prior_R7_logger_provenance_retained'])
        if prepared['source_sha256'] is not None:
            self.assertEqual(binding['status'],'PASS')
            self.assertTrue(binding['sealed_package_members_reopened'])

    def test_mutations_cannot_promote_waiting_or_old_science(self):
        changes=[('latest_actual_owner','new_owner_fits',1),
            ('latest_actual_owner','native_preflight_entered',True),
            ('actual_admission','reserved_cpus',12),
            ('actual_admission','available_CPU_is_safe_IO_capacity',True),
            ('actual_observer','complete_terminal_log_claimed',True),
            ('actual_observer','scientific_workers',12),
            ('actual_cache_and_cost','historical_cache_benchmark_exercised',True),
            ('actual_cache_and_cost','estimated_cost_usd',0.01),
            ('preserved_evidence','distinct_run_inventories_summed',True),
            ('prepared_continuation','owner_execution_verified',True),
            ('prepared_continuation','moderate_IO_aggregate_lanes_per_owner',12),
            ('metric_policy','current_season_complete',True)]
        if self.data['prepared_continuation']['source_sha256'] is not None:
            bad=copy.deepcopy(self.data['prepared_continuation']['science_identity_continuity']);bad['all_eight_unchanged_claimed']=True
            changes.append(('prepared_continuation','science_identity_continuity',bad))
        for group,key,value in changes:
            altered=copy.deepcopy(self.data);altered[group][key]=value
            with self.subTest(group=group,key=key),patch.object(status.json,'loads',return_value=altered):
                with self.assertRaises(ValueError):status.load_payload()

    def test_public_payload_contains_no_private_runtime_paths_or_models(self):
        body=(DOC/'b063r8.html').read_text()+(DOC/'data/B063R8_PUBLIC_STATUS.json').read_text()+status.BANNER
        for forbidden in [r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',
                          r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',
                          r'\.pyz(?:\b|["\'])']:
            self.assertIsNone(re.search(forbidden,body),forbidden)


if __name__=='__main__':
    unittest.main()
