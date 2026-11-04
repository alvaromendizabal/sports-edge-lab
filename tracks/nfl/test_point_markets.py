"""Point-market display must preserve clocks, target semantics and missingness."""
import copy
import unittest

import current_coverage
import point_markets


class PointMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = current_coverage.load_coverage()[0]
        cls.original, cls.receipt = point_markets.load_point_markets(cls.coverage)

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def reject(self, change):
        change(self.data)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            point_markets.validate_point_markets(self.data, self.coverage)

    def historical(self, data):
        return next(r for r in data['rows'] if r['provider'] == 'Kalshi' and r['horizon'] == 'T1' and r['target'] == 'margin')

    def current(self, data):
        return next(r for r in data['rows'] if r['horizon'] == 'LATEST_OBSERVED' and r['line'] is not None)

    def test_all_completed_kalshi_points_are_retained(self):
        for target in ('margin', 'total'):
            for horizon in ('T1', 'T2'):
                self.assertEqual(sum(r['provider'] == 'Kalshi' and r['target'] == target and r['horizon'] == horizon and r['line'] is not None for r in self.data['rows']), 121)
        self.assertEqual(self.receipt['point_display_new_fits'], 0)
        self.assertFalse(self.receipt['point_display_new_provider_acquisition'])

    def test_contract_cannot_become_a_score_projection(self):
        self.reject(lambda d: self.historical(d).update(point_estimate=3.5))

    def test_contract_cannot_enter_point_regression_scores(self):
        self.reject(lambda d: self.historical(d).update(metric_eligible=True))

    def test_raw_ladder_cannot_be_added(self):
        self.reject(lambda d: self.historical(d).update(raw_order_book={'ask': .5}))

    def test_private_pointer_cannot_be_added(self):
        self.reject(lambda d: d['limitations'].append('s3://private/provider-original'))

    def test_same_reference_cannot_be_counted_twice(self):
        self.reject(lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])))

    def test_known_completed_market_cannot_disappear(self):
        self.reject(lambda d: d['rows'].remove(self.historical(d)))

    def test_home_margin_cannot_silently_flip_orientation(self):
        self.reject(lambda d: self.historical(d).update(predicate_variable='away_margin'))

    def test_probabilities_remain_rounded(self):
        self.reject(lambda d: self.historical(d).update(observed_probability=.5123456))

    def test_later_quote_cannot_enter_earlier_cutoff(self):
        def change(d):
            r = self.historical(d)
            r['quote_at'] = next(g['kickoff_utc'] for g in self.coverage['all_games'] if g['game_id'] == r['game_id'])
        self.reject(change)

    def test_source_acquisition_is_not_backdated_to_a_quote(self):
        self.reject(lambda d: self.historical(d).update(acquired_at='2000-01-01T00:00:00Z'))

    def test_current_quote_after_kickoff_is_rejected(self):
        def change(d):
            r = self.current(d)
            r['acquired_at'] = next(g['kickoff_utc'] for g in self.coverage['all_games'] if g['game_id'] == r['game_id'])
        self.reject(change)

    def test_missing_latest_pregame_cannot_be_filled_with_t1(self):
        self.reject(lambda d: self.historical(d).update(horizon='LATEST_PREGAME'))

    def test_monday_original_forecast_is_separate_and_unchanged(self):
        g = next(g for g in self.coverage['all_games'] if g['game_id'] == '2026_08_CHI_SEA')
        f = next(f for f in g['forecasts'] if f['model_id'] == 'preserved_selected_actual_T1')
        self.assertEqual((g['actual']['winner'], g['actual']['total']), ('CHI', 51.0))
        self.assertEqual((f['pick'], f['home_margin'], f['total'], f['correct']), ('SEA', 5.2, 46.5, False))
        self.assertEqual(f['issue_class'], 'T1_RESEARCH_ACTUAL_ISSUE')
        rows = [r for r in self.data['rows'] if r['game_id'] == g['game_id'] and r['provider'] == 'Kalshi']
        self.assertEqual(len(rows), 4)


if __name__ == '__main__':
    unittest.main()
