"""All-game public evidence must keep missingness, chronology and both outcomes."""
import copy
import unittest
import current_coverage as coverage


class CurrentCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.receipt = coverage.load_coverage()

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def reject(self, change):
        change(self.data)
        with self.assertRaises((ValueError, KeyError)):
            coverage.validate_coverage(self.data)

    def provider(self, data, provider='Kalshi', horizon='T2'):
        return next(p for p in data['all_games'][0]['providers'] if p['provider'] == provider and p['horizon'] == horizon)

    def issue(self, data):
        return next((g, f) for g in data['all_games'] for f in g['forecasts'] if f['issue_class'] == 'EARLY_FORWARD_RESEARCH_ISSUE')

    def test_all_games_all_weeks_and_new_derived_coverage(self):
        self.assertEqual(self.receipt['current_schedule_games'], 272)
        self.assertEqual(self.receipt['current_completed_games'], 121)
        self.assertEqual(self.receipt['current_disagreement_pairs'], 296)
        self.assertFalse(self.receipt['owner_pipeline_accepted'])
        self.assertEqual(sum(g['week'] == 9 for g in self.data['all_games']), 15)

    def test_final_cannot_disappear(self):
        self.reject(lambda d: d['all_games'].pop(0))

    def test_unknown_nested_provider_payload_rejected(self):
        self.reject(lambda d: self.provider(d).update(raw_book={'ask': .3}))

    def test_unknown_model_recipe_rejected(self):
        self.reject(lambda d: d['all_games'][0]['forecasts'][0].update(recipe='private'))

    def test_private_location_rejected(self):
        self.reject(lambda d: d['limitations'].append('s3://private/models'))

    def test_owner_failure_cannot_be_promoted(self):
        self.reject(lambda d: d.update(owner_run_status='COMPLETE'))

    def test_data_reanalysis_is_not_live_acquisition(self):
        self.reject(lambda d: d['summary'].update(source_refreshed_in_derivation=True))

    def test_wrong_return_identity_rejected(self):
        self.reject(lambda d: d['provenance'].update(owner_return_sha256='0' * 64))

    def test_unsupported_provider_is_rejected(self):
        self.reject(lambda d: d['active_providers'].append('player-prop-reference'))

    def test_missing_provider_horizon_stays_visible(self):
        self.reject(lambda d: d['all_games'][0]['providers'].pop())

    def test_later_quote_cannot_enter_two_hour_comparison(self):
        self.reject(lambda d: self.provider(d).update(quote_at=d['all_games'][0]['kickoff_utc']))

    def test_missing_pregame_observation_cannot_be_invented(self):
        self.reject(lambda d: self.provider(d, horizon='LATEST_PREGAME').update(derived_pick='SEA', correct=True))

    def test_original_frozen_missingness_cannot_be_hidden(self):
        self.reject(lambda d: d['all_games'][0]['forecasts'].pop(0))

    def test_no_reconstructed_issue_clock(self):
        self.reject(lambda d: next(f for f in d['all_games'][0]['forecasts'] if f['issue_class'] == 'RECONSTRUCTED_NOT_ORIGINAL_ISSUED').update(actual_issue_at='2026-09-01T00:00:00Z'))

    def test_model_cannot_finish_after_actual_issue(self):
        self.reject(lambda d: self.issue(d)[1].update(fit_completed=self.issue(d)[0]['kickoff_utc']))

    def test_source_cannot_follow_actual_issue(self):
        self.reject(lambda d: self.issue(d)[1].update(source_asof=self.issue(d)[0]['kickoff_utc']))

    def test_unqualified_stake_cannot_be_added(self):
        self.reject(lambda d: self.issue(d)[1].update(stake=5))

    def test_display_probability_must_remain_rounded(self):
        self.reject(lambda d: self.issue(d)[1].update(home_win_probability=.322319491))

    def test_upcoming_correctness_cannot_be_invented(self):
        self.reject(lambda d: self.issue(d)[1].update(correct=True))

    def test_losing_disagreement_cannot_be_removed(self):
        self.reject(lambda d: d['disagreements'].pop(next(i for i, r in enumerate(d['disagreements']) if r['provider_right'])))

    def test_disagreement_result_cannot_be_reversed(self):
        self.reject(lambda d: d['disagreements'][0].update(model_right=not d['disagreements'][0]['model_right']))

    def test_compared_model_and_provider_need_same_count(self):
        self.reject(lambda d: d['season_metrics'][0]['provider_metrics'].update(games=1))

    def test_latest_states_are_present_without_fake_quotes(self):
        self.assertEqual(self.data['summary']['latest_pregame_observations'], 0)
        self.assertEqual(sum(p['horizon'] == 'LATEST_PREGAME' for g in self.data['all_games'] for p in g['providers']), 272 * 3)

    def test_captured_history_is_separate_from_settlement_admission(self):
        for year, expected in [(2024, (188, 186, 2)), (2025, (259, 93, 166)), (2026, (92, 92, 0))]:
            for horizon in ('T1', 'T2'):
                row = next(r for r in self.data['coverage'] if (r['season'], r['provider'], r['horizon']) == (year, 'Polymarket', horizon))
                self.assertEqual(tuple(row[k] for k in ('captured_both_contract_games', 'metric_admitted_games', 'settlement_unverified_games')), expected)

    def test_unverified_settlement_does_not_become_missing_acquisition(self):
        self.reject(lambda d: next(r for r in d['coverage'] if r['season'] == 2025 and r['provider'] == 'Polymarket').update(both_contract_games=93))

    def test_captured_rows_cannot_all_become_metric_eligible(self):
        self.reject(lambda d: next(r for r in d['coverage'] if r['season'] == 2025 and r['provider'] == 'Polymarket').update(metric_admitted_games=259))

    def test_historical_coverage_census_cannot_disappear(self):
        self.reject(lambda d: d['coverage'].pop())

    def test_saved_original_values_remain_without_invented_horizon(self):
        rows = [f for g in self.data['all_games'] for f in g['forecasts'] if f['model_id'] == 'original_saved' and f['pick']]
        self.assertEqual(len(rows), 76)
        self.assertTrue(all(f['horizon'] == 'ORIGINAL_HORIZON_UNVERIFIED' and f['actual_issue_at'] is None for f in rows))
        self.assertFalse(any(r['model_id'] == 'original_saved' for r in self.data['weekly_metrics'] + self.data['season_metrics']))

    def test_original_saved_horizon_cannot_be_assumed_from_model_name(self):
        for horizon in ('T2', 'T24'):
            with self.subTest(horizon=horizon):
                self.reject(lambda d: next(f for g in d['all_games'] for f in g['forecasts'] if f['model_id'] == 'original_saved' and f['pick']).update(horizon=horizon))

    def test_unknown_original_horizon_cannot_enter_matched_metrics(self):
        self.reject(lambda d: d['season_metrics'][0].update(model_id='original_saved'))


if __name__ == '__main__':
    unittest.main()
