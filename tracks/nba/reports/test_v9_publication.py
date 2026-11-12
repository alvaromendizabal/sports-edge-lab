"""Invented V9 publication fixtures; no sources, fits, inference or rescoring."""
import copy
import hashlib
import json
import unittest

import v9_publication as subject

CLOCK = '2026-11-12T02:15:00Z'


def fixture():
    roles = {'winner_T60': 'regular_winner_accuracy_t60', 'total_T120': 'regular_total_mae_t120'}
    game = {'season': '2026-27', 'phase': 'regular', 'home_team': 'AAA', 'away_team': 'BBB',
            'scheduled_start_utc': '2026-11-13T02:00:00Z', 'last_confirmed_status': 'SCHEDULED',
            'last_confirmed_status_asof_utc': CLOCK, 'schedule_source_asof_utc': CLOCK,
            'tip_time_relation_at_report': 'FUTURE_TIP', 'identity_status': 'RESOLVED_MATCHUP'}
    coverage = {'applicable_role_group': 'regular', 'current_role_ids_available': [roles['winner_T60']],
                'current_role_ids_missing': [roles['total_T120']], 'target_horizon': {}}
    for target in ('winner', 'margin', 'total'):
        for horizon in (60, 120):
            key = f'{target}_T{horizon}'; present = key == 'winner_T60'; expected = key in roles
            coverage['target_horizon'][key] = {'expected_roles': int(expected),
                'current_roles_available': int(present), 'at_issue_roles_available': int(present),
                'status': 'AVAILABLE_ORIGINAL_ISSUES' if present else 'NO_ORIGINAL_ISSUE_FOR_CURRENT_CHAMPION' if expected else 'NO_ACTIVE_CHAMPION_FOR_TARGET_HORIZON'}
    return {'evidence_as_of_utc': CLOCK, 'latest_forecast_issue_at_utc': CLOCK,
            'games': {'FAKE_GAME_1': game}, 'game_coverage': {'FAKE_GAME_1': coverage},
            'role_groups': {'regular': sorted(roles.values())},
            'role_views': [{'game_id': 'FAKE_GAME_1', 'champion_role': roles['winner_T60'], 'current_issue_ref': 'FAKE_ISSUE_1'}],
            'issues': {'FAKE_ISSUE_1': {'game_id': 'FAKE_GAME_1', 'original_pregame_issue': True,
                'target': 'winner', 'horizon_minutes': 60, 'prediction': .624321,
                'issued_at_utc': CLOCK, 'source_asof_utc': '2026-11-12T02:10:00Z',
                'actual_lead_minutes': 1425.0, 'issue_horizon_class': 'EARLY_OUTLOOK',
                'source_age_seconds_at_issue': 300.0, 'prediction_intervals': {'80': [.4, .8]}}},
            'coverage': {'official_schedule_games': 1},
            'schedule_observation': {'regular_season_expected_full_count': 2,
                'regular_season_not_observed_count': 1, 'future_full_schedule_complete': False,
                'owner_release': 'FAKE', 'snapshot_finished_at_utc': CLOCK}}


class V9PublicationTests(unittest.TestCase):
    def test_observed_inventory_and_full_schedule_gap_are_separate(self):
        result = subject.build_v9_review(fixture())
        cov = result['coverage']
        self.assertEqual((cov['observed_games'], cov['regular_full_season_denominator'], cov['unobserved_regular_slots']), (1, 2, 1))
        self.assertEqual((cov['expected_current_role_cells'], cov['available_current_role_cells'], cov['missing_current_role_cells']), (2, 1, 1))
        self.assertTrue(cov['observed_inventory_reconciled'])
        self.assertFalse(cov['full_season_completion_claim'])
        self.assertFalse(cov['future_full_schedule_complete'])
        self.assertEqual(len(result['game_rows'][0]['target_horizon']), 6)

    def test_missing_game_coverage_and_hidden_role_fail(self):
        for mode in ('game', 'role', 'target'):
            data = fixture()
            if mode == 'game': data['game_coverage'] = {}
            elif mode == 'role': data['game_coverage']['FAKE_GAME_1']['current_role_ids_missing'] = []
            else: data['game_coverage']['FAKE_GAME_1']['target_horizon'].pop('margin_T120')
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.build_v9_review(data)

    def test_expected_official_denominator_cannot_be_silently_replaced(self):
        data = fixture(); data['schedule_observation']['regular_season_not_observed_count'] = 0
        with self.assertRaisesRegex(ValueError, 'FULL_REGULAR_DENOMINATOR'):
            subject.build_v9_review(data)

    def test_original_predictions_intervals_and_clocks_are_exact_and_immutable(self):
        data = fixture(); before = subject.canonical(data)
        result = subject.build_v9_review(data)
        ref = result['game_rows'][0]['selected_original_issues'][0]
        source = data['issues']['FAKE_ISSUE_1']
        for key in ('prediction', 'prediction_intervals', 'issued_at_utc', 'source_asof_utc', 'actual_lead_minutes', 'source_age_seconds_at_issue', 'issue_horizon_class'):
            self.assertEqual(ref[key], source[key])
        self.assertEqual(subject.canonical(data), before)
        self.assertEqual(result['selected_output_sha256'], hashlib.sha256(before + b'\n').hexdigest())

    def test_no_final_score_or_score_forecast_or_error_is_inferred(self):
        data = fixture(); data['games']['FAKE_GAME_1']['scheduled_start_utc'] = '2026-10-01T00:00:00Z'
        row = subject.build_v9_review(data)['game_rows'][0]
        self.assertEqual(row['last_confirmed_status'], 'SCHEDULED')
        self.assertIsNone(row['actual']['home_points'])
        self.assertEqual(row['joint_home_away_score_center_status'], 'NO_COHERENT_JOINT_SCORE_CENTER_ADMITTED')
        self.assertEqual(row['per_game_error_status'], 'NO_SAVED_PER_GAME_ERROR_EXPORT_SUPPLIED')

    def test_source_bound_final_score_keeps_actual_observation_clock(self):
        data = fixture(); game = data['games']['FAKE_GAME_1']; game['last_confirmed_status'] = 'FINAL'
        game['result_observation'] = {'status': 'FINAL', 'home_points': 101, 'away_points': 100,
            'ended_at_utc': '2026-11-13T04:00:00Z', 'observed_at_utc': '2026-11-13T04:01:00Z',
            'available_at_utc': '2026-11-13T04:01:00Z', 'evidence_track': 'SAVED_OWNER_RESULT_WITH_BOUND_SOURCE_REFERENCE'}
        actual = subject.build_v9_review(data)['game_rows'][0]['actual']
        self.assertEqual((actual['home_points'], actual['away_points']), (101, 100))
        self.assertEqual(actual['observed_at_utc'], game['result_observation']['observed_at_utc'])
        self.assertNotIn('margin', actual)
        self.assertFalse(actual['new_score_calculation'])

    def test_availability_requires_matching_original_game_issue(self):
        for field, value in [('game_id', 'OTHER_GAME'), ('original_pregame_issue', False)]:
            data = fixture(); data['issues']['FAKE_ISSUE_1'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'ORIGINAL_ISSUE_IDENTITY'):
                subject.build_v9_review(data)

    def test_configured_workers_and_synthetic_success_do_not_prove_native_fit_acceptance(self):
        owner = {'V9_parallel': {'status': 'PASS', 'configured_workers': 12, 'synthetic_only': True,
                                'acceptance_passed': True, 'private_root': '/home/private', 'recipe_id': 'DO_NOT_PUBLISH'}}
        row = next(x for x in subject.build_v9_review(fixture(), owner)['runtime_receipts'] if x['section'] == 'V9_parallel')
        self.assertEqual(row['measurements']['configured_workers'], 12)
        self.assertTrue(row['source_acceptance_claim'])
        self.assertFalse(row['verified_acceptance_claim'])
        self.assertNotIn('observed_native_fit_peak', row['measurements'])
        self.assertNotIn('/home', json.dumps(row)); self.assertNotIn('recipe_id', json.dumps(row))

    def test_absent_cache_receipt_is_unverified_not_zero_gets(self):
        row = next(x for x in subject.build_v9_review(fixture())['runtime_receipts'] if x['section'] == 'V9_cache')
        self.assertEqual(row['status'], 'OWNER_RUN_EVIDENCE_NOT_SUPPLIED')
        self.assertEqual(row['measurements'], {})
        self.assertFalse(row['verified_acceptance_claim'])

    def test_scalar_native_measurements_and_benchmarks_are_copied(self):
        owner = {'V9_parallel': {'status': 'MEASURED_OWNER_NATIVE_FITS', 'observed_native_fit_peak': 8,
            'native_cpu_equivalents_peak': 12, 'heartbeat_max_gap_seconds': 22.4,
            'benchmarks': [{'workers': 4, 'native_threads_per_worker': 3, 'completed_fits': 12,
                            'elapsed_seconds': 3.2, 'private_cloud_path': 's3://secret'}]}}
        row = next(x for x in subject.build_v9_review(fixture(), owner)['runtime_receipts'] if x['section'] == 'V9_parallel')
        self.assertEqual(row['measurements']['observed_native_fit_peak'], 8)
        self.assertEqual(row['benchmarks'][0]['elapsed_seconds'], 3.2)
        self.assertNotIn('s3://', json.dumps(row))

    def test_full_current_best_cannot_be_inferred_from_saved_subset_metric(self):
        model = {'metric_rows': [{'evidence_track': 'CURRENT_FIXED_STATE_REPLAY', 'role_alias': 'saved_subset', 'metrics': {'accuracy': 1}, 'scored_games': 1}]}
        result = subject.build_v9_review(fixture(), model_review=model)
        self.assertEqual(next(x for x in result['model_policy_coverage'] if x['evidence_track'] == 'CURRENT_FIXED_STATE_REPLAY')['saved_metric_rows'], 1)
        self.assertTrue(all(x['full_current_season_best_claim'] is False for x in result['window_coverage']))
        self.assertTrue(all(x['saved_metric_rows'] == 0 for x in result['window_coverage']))

    def test_owner_window_metrics_copy_without_scoring_or_selection(self):
        source = {'window': 'LAST_1_WEEK', 'evidence_track': 'NEW_SEASON_FROZEN_REFRESH',
            'role_alias': 'selected_winner_accuracy_t60', 'target': 'winner', 'horizon_minutes': 60,
            'scored_games': 2, 'completed_game_denominator': 3, 'missing_games': 1,
            'metrics': {'accuracy': .5, 'log_loss': .6123456789, 'ece_10_fixed_bins': .07},
            'status': 'SAVED_OWNER_METRICS', 'window_start_utc': '2026-11-05T00:00:00Z', 'window_end_utc': CLOCK}
        owner = {'V9_science': {'window_metrics': [source]}}; before = copy.deepcopy(owner)
        row = subject.build_v9_review(fixture(), owner)['window_metric_rows'][0]
        self.assertEqual(row['metrics']['log_loss'], .612346)
        self.assertEqual(row['metrics']['ece_10_fixed_bins'], .07)
        self.assertFalse(row['selection_or_promotion_allowed'])
        self.assertEqual(owner, before)
        owner['V9_science']['window_metrics'][0]['missing_games'] = 0
        with self.assertRaisesRegex(ValueError, 'WINDOW_DENOMINATOR_CLOSURE'):
            subject.build_v9_review(fixture(), owner)

    def test_merge_does_not_assert_deployment(self):
        lifecycle = {'prepared': {'verified': True, 'status': 'PREPARED'},
            'merged': {'verified': True, 'status': 'MERGED', 'commit_sha': 'a' * 40}}
        output = subject.build_v9_review(fixture(), lifecycle=lifecycle)['publication_lifecycle']
        self.assertTrue(output['merged']['verified']); self.assertFalse(output['deployed']['verified'])
        self.assertFalse(output['source_publication_is_website_deployment'])
        with self.assertRaisesRegex(ValueError, 'DEPLOYMENT_EVIDENCE'):
            subject.publication_lifecycle({'deployed': {'verified': True, 'status': 'DEPLOYED'}})

    def test_renderer_is_idempotent_embeds_exact_data_and_preserves_base(self):
        data = fixture(); value = subject.build_v9_review(data); base = '<html><main>ORIGINAL CONTENT</main></html>'
        once = subject.attach_review(base, value); twice = subject.attach_review(once, value)
        self.assertEqual(once, twice)
        self.assertIn('ORIGINAL CONTENT', once)
        self.assertEqual(once.count(subject.BEGIN), 1)
        self.assertIn(subject.canonical(value).decode(), once)
        files, receipt = subject.publication_payloads(data, None, None, base)
        self.assertEqual(set(files), {'latest_v9_acceptance.json', 'latest_research_outputs.html'})
        self.assertEqual(receipt['new_metric_scoring'], 0)

    def test_bad_clocks_nonfinite_numbers_and_duplicate_roles_rejected(self):
        for mode in ('clock', 'number', 'duplicate'):
            data = fixture()
            if mode == 'clock': data['issues']['FAKE_ISSUE_1']['issued_at_utc'] = '2026-11-12'
            elif mode == 'number': data['issues']['FAKE_ISSUE_1']['prediction'] = float('nan')
            else: data['role_views'].append(copy.deepcopy(data['role_views'][0]))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.build_v9_review(data)


if __name__ == '__main__':
    unittest.main()
