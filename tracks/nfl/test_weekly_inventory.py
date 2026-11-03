"""Public weekly outputs must preserve identity, chronology and missing coverage."""
import copy
import unittest
from datetime import timedelta
import weekly_inventory as weekly


class WeeklyDisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.receipt = weekly.load_weekly()

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def reject(self, mutation):
        mutation(self.data)
        with self.assertRaises((ValueError, KeyError)):
            weekly.validate_weekly(self.data)

    def test_complete_schedule_and_two_week_denominators(self):
        self.assertEqual(self.receipt['schedule_games'], 272)
        self.assertEqual(self.receipt['weekly_disagreements'], 48)
        self.assertEqual(sum(bool(x['upcoming_issue_join']) for x in self.data['inventory']), 29)
        self.assertFalse(self.receipt['private_training_reproduced'])

    def test_missing_scheduled_game_fails(self):
        self.reject(lambda d: d['inventory'].pop())

    def test_excluded_chicago_cannot_vanish_from_week(self):
        self.reject(lambda d: d['week8'].pop())

    def test_missing_model_stream_cannot_disappear(self):
        self.reject(lambda d: d['week9'][0]['forecasts'].pop())

    def test_wrong_event_join_fails(self):
        self.reject(lambda d: d['week9'][0].update(home='SEA'))

    def test_provider_reintroduction_fails(self):
        self.reject(lambda d: d['active_providers'].append('MARKET'))

    def test_nested_raw_quote_is_rejected(self):
        self.reject(lambda d: d['week9'][0]['providers'][0].update(raw_quote={'ask': .42}))

    def test_private_recipe_is_rejected(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(recipe='production-transform'))

    def test_private_path_in_note_is_rejected(self):
        self.reject(lambda d: d['notes'].append('s3://private-bucket/models'))

    def test_unrounded_public_probability_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(home_win_probability=.3223123))

    def test_backdated_early_qualification_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(actual_issue_at=d['week9'][0]['kickoff_utc']))

    def test_late_model_cannot_support_prior_issue(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(fit_completed=d['week9'][0]['kickoff_utc']))

    def test_reconstruction_cannot_gain_issue_clock(self):
        self.reject(lambda d: d['week8'][0]['forecasts'][1].update(actual_issue_at='2026-10-20T00:00:00+00:00'))

    def test_final_hour_promotion_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(eligible_final_hour=True))

    def test_unsupported_stake_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(stake=5))

    def test_future_correctness_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(correct=True))

    def test_score_center_incoherence_fails(self):
        self.reject(lambda d: d['week9'][0]['forecasts'][0].update(home_score_center=100))

    def test_provider_missingness_cannot_be_hidden(self):
        self.reject(lambda d: d['provider_coverage']['week9']['Kalshi'].update(winner_covered=15))

    def test_removing_lost_disagreement_fails(self):
        self.reject(lambda d: d['week8_disagreements'].pop(next(i for i,r in enumerate(d['week8_disagreements']) if not r['model_won'])))

    def test_cannot_mark_every_model_right(self):
        self.reject(lambda d: d['week8_disagreements'][0].update(model_won=True, provider_won=False))


if __name__ == '__main__':
    unittest.main()
