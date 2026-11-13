"""Actual failed-owner facts, additive page generation and exact science retention."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import b063r9_status as status

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT/'docs/ncaa'
EX = ROOT/'examples/ncaa_review'
R9_LINE = b"    counts.b063r9Status = await require('./test_b063r9_status_browser.cjs').verifyR9(browser, path.join(root, 'docs/ncaa/b063r9.html'));\n"
PRIOR_JSON = {
    'b063r1-data': (86124, '4e8a1cc88bfeaca87a11c33b72907809de6a9321bc5866840a67661499556866'),
    'terminal-data': (3307059, 'f2b624d0ffa336150d0cd219c1732e135ead71cb884bce24dec70b14f2bf5115'),
    'b063-data': (1401241, '54338ffb9cfcf8a4f08d1bfcbcb1297a1f4cfd588d82ac719957dfc079bcfa12'),
}


def blob(value):
    return hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()


class B063R9PublicStatus(unittest.TestCase):
    def setUp(self):
        self.data = status.load_payload()

    def test_actual_source_and_failure_are_authenticated_and_dated(self):
        actual = self.data['latest_actual_owner']
        self.assertEqual(actual['source_sha256'], 'f45ab01b74fd2a67639f90d9933c032a851173e8d1b4d9c20f1b955f50f73235')
        self.assertEqual(actual['release_identity_basis'], 'EXACT_EXECUTABLE_SHA256')
        self.assertEqual(actual['failure_type'], 'ScheduleProjectionError')
        self.assertEqual(actual['failed_stage'], '04_latest_source_refresh')
        self.assertEqual(actual['completed_at_utc'], '2026-11-13T19:32:22.855530+00:00')
        self.assertAlmostEqual(actual['worker_elapsed_seconds'], 231.707490776)
        self.assertTrue(actual['durable_return_verified'])

    def test_return_has_zero_scientific_credit_and_preserves_fixture_scope(self):
        actual = self.data['latest_actual_owner']
        for key in ('new_owner_fits','reused_verified_fits','new_checkpoints','reused_checkpoints',
                    'new_forecasts','new_metric_scores','new_market_quotes','native_fixture_sports_fit_credit'):
            self.assertEqual(actual[key], 0, key)
        self.assertEqual(actual['native_fixture_contracts'], 26)
        self.assertFalse(actual['full_scientific_run_completed'])
        self.assertAlmostEqual(actual['before_first_recorded_science_stage_seconds'],
            actual['reported_science_phase_seconds']-actual['failed_stage_seconds'])

    def test_cap_and_actual_measured_cpu_are_separate(self):
        cpu = self.data['actual_cpu']
        self.assertEqual((cpu['host_effective_vcpus'],cpu['launcher_requested_cap'],
            cpu['configured_project_cap'],cpu['peak_ready_demand_requested_cpus'],cpu['peak_granted_cpus']),
            (48,12,12,1,1))
        self.assertAlmostEqual(cpu['peak_observed_process_tree_cpu_cores'], 1.0004364834119108)
        self.assertEqual(cpu['scientific_native_callback_starts'], 0)
        self.assertFalse(cpu['twelve_core_scientific_acceptance_proven'])

    def test_verified_cache_read_and_get_scopes_do_not_overlap_or_refresh_quotes(self):
        cache = self.data['actual_cache']
        self.assertEqual((cache['verified_local_reads'],cache['verified_local_bytes']), (118,1396887267))
        self.assertEqual((cache['cache_layer_hits'],cache['cache_layer_local_bytes']), (119,1396887736))
        self.assertEqual((cache['full_S3_GETs'],cache['full_S3_GET_bytes']), (2,24079252))
        self.assertAlmostEqual(cache['full_S3_GET_seconds'], 0.3412936580000405)
        self.assertIn('RETURN_PERSISTENCE_SEPARATE', cache['full_GET_scope'])
        self.assertFalse(cache['repeat_frozen_scientific_cache_acceptance_proven'])
        self.assertFalse(cache['cache_hit_clocks_changed'])

    def test_live_log_capture_and_old_label_are_exactly_qualified(self):
        logs = self.data['actual_logging']
        self.assertEqual((logs['jsonl_rows'],logs['heartbeats'],logs['terminal_publisher_sequence']), (55,26,1756))
        self.assertEqual(logs['maximum_captured_UTC_timestamp_gap_seconds'], 10.010604)
        self.assertAlmostEqual(logs['maximum_captured_event_elapsed_gap_seconds'], 10.01060355300001)
        self.assertAlmostEqual(logs['logger_reported_monotonic_max_heartbeat_gap_seconds'], 10.010606480000206)
        self.assertEqual((logs['human_log_captured_bytes'],logs['jsonl_captured_bytes']), (141986,248052))
        self.assertEqual(logs['capture_status'], 'VERIFIED_BOUNDED_PREFIX')
        self.assertEqual(logs['observed_logger_release_label'], 'B063R7')
        self.assertFalse(logs['release_label_is_executable_identity'])
        self.assertFalse(logs['complete_final_owner_log_claimed'])
        self.assertTrue(logs['post_capture_events_remain_external'])

    def test_rate_estimate_is_not_invoice_or_workload_attribution(self):
        cost = self.data['actual_cost']
        self.assertAlmostEqual(cost['estimated_whole_instance_invocation_usd'], 0.1652139763822528)
        self.assertEqual(cost['verified_rate_usd_per_hour'], 2.57)
        self.assertIsNone(cost['actual_invoice_cost_usd'])
        self.assertTrue(cost['overlapping_workload_cost_not_attributed'])
        self.assertFalse(cost['new_infrastructure'])

    def test_all_three_prior_embedded_game_and_science_payloads_remain_byte_exact(self):
        landing = (DOC/'index.html').read_text()
        scripts = dict(re.findall(r'<script id="([^"]+)" type="application/json">(.*?)</script>',landing,re.S))
        self.assertEqual(set(scripts), set(PRIOR_JSON))
        for name,(size,digest) in PRIOR_JSON.items():
            raw = scripts[name].encode()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()), (size,digest), name)
            self.assertIsInstance(json.loads(raw), dict)

    def test_removing_only_new_banner_restores_exact_previous_landing(self):
        landing = (DOC/'index.html').read_text()
        self.assertEqual(landing.count(status.START), 1)
        self.assertEqual(blob(status.strip_banner(landing).encode()), '69b452f8b88c4dcd12dcb772baca6b8958858e1a')
        self.assertEqual(status.render_banner(landing), landing)
        self.assertEqual(status.render_banner(status.strip_banner(landing)), landing)

    def test_previous_readme_and_browser_are_exact_after_removing_only_new_layer(self):
        body = (EX/'README.md').read_bytes()
        self.assertEqual(body.count(b'<!-- B063R9_STATUS_START -->'), 1)
        self.assertEqual(blob(body.split(b'<!-- B063R9_STATUS_END -->\n\n',1)[1]), 'c8da6d02790c4f0fb7aaf9a9f4ff31dfcedeb0ea')
        browser = (EX/'test_dashboard_browser.cjs').read_bytes()
        self.assertEqual(browser.count(R9_LINE), 1)
        self.assertEqual(blob(browser.replace(R9_LINE,b'')), '8843a924e478db549f3f854ec3a2c1054a48b015')

    def test_dated_previous_science_provider_and_selection_data_are_unchanged(self):
        prior = json.loads((EX/'B063R8_PUBLIC_STATUS.json').read_text())
        for key in ('preserved_science','preserved_evidence','metric_policy'):
            self.assertEqual(self.data[key], prior[key], key)
        raw = (DOC/'data/NCAA_B063R2_PUBLIC_SCIENTIFIC_TABLES.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.data['preserved_science']['source_sha256'])
        self.assertEqual(blob((DOC/'b063r8.html').read_bytes()), '42757f0f37b03e3698424a4bb1c4ec5daea87764')

    def test_separate_saved_denominators_and_current_refresh_gaps_remain_visible(self):
        coverage = self.data['coverage_status']
        self.assertEqual(tuple(coverage[key] for key in ('saved_source_records','saved_normalized_espn_records',
            'saved_unmatched_official_candidates','saved_unresolved_source_candidates')), (3457,2498,934,25))
        self.assertEqual(coverage['saved_replay_games_by_league'], {'ncaam':420,'ncaaw':403})
        self.assertEqual((coverage['saved_selected_original_target_rows'],coverage['saved_selected_original_games']), (90,30))
        self.assertTrue(coverage['populations_are_distinct_and_not_added'])
        for key in ('current_season_complete','upcoming_schedule_complete','latest_attempt_refreshed_game_inventory'):
            self.assertFalse(coverage[key], key)
        self.assertEqual(coverage['saved_replay_evidence_asof_utc'], '2026-11-11T22:39:45.642794+00:00')

    def test_render_embedded_payload_download_and_output_routes_are_exact(self):
        rendered = status.render_page()
        page = (DOC/'b063r9.html').read_text()
        self.assertEqual(page, rendered)
        embedded = re.search(r'<script type="application/json" id="b063r9-data">(.*?)</script>',page,re.S)
        self.assertEqual(json.loads(embedded.group(1)),self.data)
        self.assertEqual(embedded.group(1),(EX/'B063R9_PUBLIC_STATUS.json').read_text())
        self.assertEqual((DOC/'data/B063R9_PUBLIC_STATUS.json').read_bytes(),(EX/'B063R9_PUBLIC_STATUS.json').read_bytes())
        outputs = status.status_outputs({DOC/'index.html':(DOC/'index.html').read_text()})
        for path,body in outputs.items():
            self.assertEqual(path.read_text(),body)
        self.assertNotIn('__R9_',page)

    def test_prepared_source_is_qualified_and_never_granted_owner_scientific_credit(self):
        prepared = self.data['prepared_continuation']
        self.assertEqual(prepared['release'],'B063R9')
        self.assertFalse(prepared['owner_execution_performed'])
        self.assertEqual(prepared['new_owner_scientific_fits'],0)
        self.assertFalse(prepared['twelve_core_owner_utilization_proven'])
        replay = prepared['receipt_replay']
        self.assertEqual((replay['selected_files'],replay['distinct_bytes']),(112,666672))
        self.assertAlmostEqual(replay['median_speedup_ratio'],2.389413822673475)
        self.assertFalse(replay['full_adoption_speedup_claimed'])
        self.assertFalse(replay['original_181_second_owner_adoption_workload_reproduced'])
        self.assertTrue(replay['legacy_adoption_chain_still_runs'])
        self.assertTrue(replay['current_files_fully_hashed_at_all_existing_recheck_boundaries'])
        if prepared['source_sha256'] is not None:
            self.assertRegex(prepared['source_sha256'],r'^[0-9a-f]{64}$')
            self.assertGreater(prepared['source_bytes'],0)
            self.assertIsInstance(prepared['validation'],dict)

    def test_false_success_clock_and_coverage_mutations_are_rejected(self):
        changes = [('latest_actual_owner','new_owner_fits',1),
            ('latest_actual_owner','native_fixture_sports_fit_credit',26),
            ('latest_actual_owner','full_scientific_run_completed',True),
            ('actual_cpu','peak_granted_cpus',12),
            ('actual_cpu','twelve_core_scientific_acceptance_proven',True),
            ('actual_cache','full_S3_GETs',0),
            ('actual_cache','cache_hit_clocks_changed',True),
            ('actual_cache','repeat_frozen_scientific_cache_acceptance_proven',True),
            ('actual_logging','complete_final_owner_log_claimed',True),
            ('actual_logging','post_capture_events_remain_external',False),
            ('coverage_status','current_season_complete',True),
            ('coverage_status','upcoming_schedule_complete',True),
            ('coverage_status','populations_are_distinct_and_not_added',False),
            ('actual_cost','actual_invoice_cost_usd',0.1652),
            ('prepared_continuation','owner_execution_performed',True),
            ('prepared_continuation','new_owner_scientific_fits',26),
            ('prepared_continuation','twelve_core_owner_utilization_proven',True)]
        invalid_replay = copy.deepcopy(self.data['prepared_continuation']['receipt_replay'])
        invalid_replay['full_adoption_speedup_claimed'] = True
        changes.append(('prepared_continuation','receipt_replay',invalid_replay))
        original_read = Path.read_text
        for group,key,value in changes:
            altered = copy.deepcopy(self.data)
            altered[group][key] = value
            def read(path,*args,**kwargs):
                if path.name=='B063R9_PUBLIC_STATUS.json':
                    return json.dumps(altered)
                return original_read(path,*args,**kwargs)
            with self.subTest(group=group,key=key),patch.object(Path,'read_text',read):
                with self.assertRaises(ValueError):
                    status.load_payload()

    def test_mutated_previous_metric_is_rejected_instead_of_republished(self):
        altered = copy.deepcopy(self.data)
        altered['preserved_science']['current_observed_replay_leaders'][0]['value'] = 0.999
        original_read = Path.read_text
        def read(path,*args,**kwargs):
            if path.name=='B063R9_PUBLIC_STATUS.json':
                return json.dumps(altered)
            return original_read(path,*args,**kwargs)
        with patch.object(Path,'read_text',read):
            with self.assertRaisesRegex(ValueError,'Dated public scientific evidence changed'):
                status.load_payload()

    def test_ambiguous_duplicate_banner_is_rejected(self):
        body = (DOC/'index.html').read_text()
        with self.assertRaises(ValueError):
            status.strip_banner(body+status.START+status.END)

    def test_public_payload_has_no_private_runtime_paths_or_credentials(self):
        body = (DOC/'b063r9.html').read_text()+(DOC/'data/B063R9_PUBLIC_STATUS.json').read_text()
        for pattern in (r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',
                r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',r'\.pyz\b'):
            self.assertIsNone(re.search(pattern,body),pattern)


if __name__=='__main__':
    unittest.main()
