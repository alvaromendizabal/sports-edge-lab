import copy
import math
import unittest

from target_replay import evaluate_target_replay, invented_demo


class TargetReplayTests(unittest.TestCase):
    def setUp(self):
        demo = invented_demo()['result']
        self.selection = copy.deepcopy(demo['selection'])
        self.games = [{'game_id': r['game_id'], 'week': r['week'], 'season': 2026,
                       'kickoff_at': r['kickoff_at'], 'status': 'FINAL',
                       'home_score': 21 if i == 0 else 14, 'away_score': 14 if i == 0 else 21}
                      for i, r in enumerate(demo['ledger'])]
        self.rows = [{k: v for k, v in demo['ledger'][0].items()
                      if k in {'game_id', 'target', 'model_id', 'prediction', 'market_prediction',
                               'decision_at', 'source_available_at', 'latest_training_label_at',
                               'latest_training_label_season',
                               'model_created_at', 'prediction_created_at'}}]

    def run_replay(self):
        return evaluate_target_replay(self.games, self.rows, self.selection)

    def test_exact_matched_probability_metrics_and_accuracy(self):
        r = self.run_replay()
        self.assertEqual(r['census_games'], 2)
        self.assertEqual(r['matched_games'], 1)
        self.assertAlmostEqual(r['season_scores']['model']['log_loss'], -math.log(.7))
        self.assertAlmostEqual(r['season_scores']['market']['log_loss'], -math.log(.6))
        self.assertAlmostEqual(r['season_scores']['model']['brier'], .09)
        self.assertEqual(r['season_scores']['model']['accuracy'], 1)
        self.assertEqual(r['season_scores']['market']['n'], 1)

    def test_uncovered_week_survives_with_unknown_metrics(self):
        r = self.run_replay()
        week = r['weekly'][1]
        self.assertEqual(week['census_games'], 1)
        self.assertEqual(week['model']['n'], 0)
        self.assertIsNone(week['model']['accuracy'])
        self.assertEqual(r['ledger'][1]['state'], 'MISSING_MODEL_OR_MATCHED_MARKET_ROW')

    def test_issued_clocks_are_not_backdated(self):
        row = self.run_replay()['ledger'][0]
        self.assertTrue(row['selection_after_kickoff'])
        self.assertTrue(row['model_created_after_decision'])
        self.assertTrue(row['prediction_created_after_decision'])
        self.assertEqual(row['classification'], 'RECONSTRUCTED_MONITORING_REPLAY_NOT_ORIGINAL_ISSUE')

    def test_tie_is_retained_but_not_scored_as_binary_loss(self):
        self.games[0]['away_score'] = 21
        r = self.run_replay()
        self.assertEqual(r['census_games'], 2)
        self.assertEqual(r['matched_games'], 0)
        self.assertEqual(r['ledger'][0]['state'], 'TIE_OUTSIDE_CONDITIONAL_BINARY_SCORE')

    def test_margin_and_total_have_separate_recipes_and_metrics(self):
        for target, prediction, market, expected in [('margin', 4, 3, 3), ('total', 37, 38, 2)]:
            with self.subTest(target=target):
                self.selection.update(target=target, model_id='invented-'+target)
                self.rows[0].update(target=target, model_id='invented-'+target,
                                    prediction=prediction, market_prediction=market)
                r = self.run_replay()
                self.assertEqual(r['season_scores']['model']['mae'], expected)
                self.assertEqual(r['season_scores']['model']['rmse'], expected)
                self.assertIsNone(r['season_scores']['model']['accuracy'])

    def test_tied_game_can_be_scored_for_margin(self):
        self.games[0]['away_score'] = 21
        self.selection['target'] = self.rows[0]['target'] = 'margin'
        self.rows[0].update(prediction=2, market_prediction=1)
        r = self.run_replay()
        self.assertEqual(r['matched_games'], 1)
        self.assertEqual(r['ledger'][0]['actual'], 0)
        self.assertEqual(r['season_scores']['model']['mae'], 2)

    def test_wrong_target_or_recipe_is_rejected(self):
        for field, value in [('target', 'total'), ('model_id', 'alias-not-declared')]:
            with self.subTest(field=field):
                row = copy.deepcopy(self.rows)
                row[0][field] = value
                with self.assertRaises(ValueError):
                    evaluate_target_replay(self.games, row, self.selection)

    def test_monitoring_cannot_enter_historical_selection(self):
        self.selection['selection_seasons'] = [2025, 2026]
        with self.assertRaises(ValueError): self.run_replay()

    def test_current_training_labels_or_unknown_policy_are_rejected(self):
        for field, value in [('training_policy', 'USES_CURRENT_SEASON_LABELS'),
                             ('latest_training_label_season', 2026),
                             ('latest_training_label_season', True)]:
            with self.subTest(field=field, value=value):
                selection = {**self.selection, field: value}
                with self.assertRaises(ValueError):
                    evaluate_target_replay(self.games, self.rows, selection)

    def test_source_equality_and_future_labels_do_not_score(self):
        for field in ['source_available_at', 'latest_training_label_at']:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[0][field] = rows[0]['decision_at']
                r = evaluate_target_replay(self.games, rows, self.selection)
                self.assertEqual(r['matched_games'], 0)
                self.assertEqual(r['ledger'][0]['state'], 'INFORMATION_BOUNDARY_NOT_ADMITTED')

    def test_strict_day_before_boundary_even_when_decision_is_later(self):
        self.rows[0]['decision_at'] = '2026-09-10T18:00:00Z'
        self.rows[0]['source_available_at'] = '2026-09-10T17:00:00Z'
        self.assertEqual(self.run_replay()['matched_games'], 0)

    def test_naive_clock_is_rejected(self):
        self.rows[0]['source_available_at'] = '2026-09-09T19:00:00'
        with self.assertRaises(ValueError): self.run_replay()

    def test_prediction_before_model_is_rejected(self):
        self.rows[0]['prediction_created_at'] = '2026-09-01T00:00:00Z'
        with self.assertRaises(ValueError): self.run_replay()

    def test_model_cannot_exist_before_training_labels(self):
        self.rows[0]['model_created_at'] = '2026-01-01T00:00:00Z'
        with self.assertRaises(ValueError): self.run_replay()

    def test_prediction_cannot_exist_before_source_availability(self):
        self.rows[0]['model_created_at'] = '2026-08-01T00:00:00Z'
        self.rows[0]['prediction_created_at'] = '2026-09-01T00:00:00Z'
        with self.assertRaises(ValueError): self.run_replay()

    def test_row_training_season_must_match_frozen_declaration(self):
        for season in [2026, None, True]:
            with self.subTest(season=season):
                self.rows[0]['latest_training_label_season'] = season
                with self.assertRaises(ValueError): self.run_replay()

    def test_duplicate_census_or_forecast_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_target_replay(self.games+self.games[:1], self.rows, self.selection)
        with self.assertRaises(ValueError):
            evaluate_target_replay(self.games, self.rows+self.rows, self.selection)

    def test_forecast_outside_census_is_rejected(self):
        self.rows[0]['game_id'] = 'other-event'
        with self.assertRaises(ValueError): self.run_replay()

    def test_nonfinite_and_impossible_probabilities_are_rejected(self):
        for value in [float('nan'), float('inf'), -1, 2, True]:
            with self.subTest(value=value):
                self.rows[0]['prediction'] = value
                with self.assertRaises(ValueError): self.run_replay()

    def test_missing_actual_score_is_not_zero(self):
        self.games[0]['home_score'] = None
        with self.assertRaises(ValueError): self.run_replay()

    def test_pending_and_canceled_games_remain_unscored(self):
        for status in ['SCHEDULED', 'POSTPONED', 'CANCELED']:
            with self.subTest(status=status):
                self.games[0].update(status=status, home_score=None, away_score=None)
                r = self.run_replay()
                self.assertEqual(r['census_games'], 2)
                self.assertEqual(r['matched_games'], 0)
                self.assertEqual(r['ledger'][0]['state'], 'NO_FINAL_OUTCOME')

    def test_accuracy_and_log_loss_answer_different_questions(self):
        self.rows[0].update(prediction=.99, market_prediction=.6)
        self.games[0].update(home_score=14, away_score=21)
        r = self.run_replay()['season_scores']
        self.assertEqual(r['model']['accuracy'], r['market']['accuracy'])
        self.assertGreater(r['model']['log_loss'], r['market']['log_loss'])

    def test_no_promotion_issue_or_profit_claim(self):
        r = self.run_replay()
        self.assertFalse(r['promotion_permitted'])
        self.assertFalse(r['selection_performed'])
        self.assertEqual(r['new_fits'], 0)
        self.assertEqual(r['new_forecast_issues'], 0)
        self.assertEqual(r['actual_orders'], 0)
        self.assertIsNone(r['actual_pnl'])
        self.assertIsNone(r['roi'])

    def test_missing_selection_receipt_remains_unqualified(self):
        self.selection.pop('selection_receipt_sha256')
        with self.assertRaises(ValueError): self.run_replay()


if __name__ == '__main__':
    unittest.main()
