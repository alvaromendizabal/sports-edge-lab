"""Recovered source observations cannot change forecasts or historical clocks."""
import copy
import unittest

import current_coverage
import current_source_overlay as overlay


class CurrentSourceOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = current_coverage.load_coverage()[0]
        cls.original, cls.receipt = overlay.load_overlay(cls.coverage)

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def reject(self, change):
        change(self.data)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            overlay.validate_overlay(self.data, self.coverage)

    def winner(self, data, provider='Kalshi'):
        return next(r for r in data['winner_rows'] if r['provider'] == provider and r['derived_pick'])

    def point(self, data):
        return next(r for r in data['point_rows'] if r['provider'] == 'Kalshi' and r['line'] is not None)

    def test_all_135_states_have_specific_evidence(self):
        self.assertEqual(self.receipt['current_source_overlay_rows'], 135)
        self.assertEqual(len(self.data['winner_rows']), 45)
        self.assertEqual(len(self.data['point_rows']), 90)
        counts = {(r['provider'], r['target']): r['available_games'] for r in self.data['coverage']}
        self.assertEqual([counts[('Kalshi', t)] for t in ('winner', 'margin', 'total')], [14, 14, 10])
        self.assertFalse(self.receipt['current_source_overlay_completed_owner_acceptance'])
        self.assertFalse(self.receipt['current_source_overlay_model_forecasts_changed'])
        self.assertEqual(self.receipt['current_source_overlay_new_review_provider_requests'], 0)

    def test_partial_checkpoint_cannot_be_accepted_research(self):
        self.reject(lambda d: d.update(owner_pipeline_accepted=True))

    def test_raw_book_cannot_be_published(self):
        self.reject(lambda d: self.winner(d).update(raw_order_book={'ask': .5}))

    def test_private_pointer_cannot_be_published(self):
        self.reject(lambda d: d['limitations'].append('s3://private/provider-original'))

    def test_no_earlier_horizon_promotion(self):
        for horizon in ('T1', 'T2', 'LATEST_PREGAME'):
            with self.subTest(horizon=horizon):
                d = copy.deepcopy(self.original)
                self.winner(d)['horizon'] = horizon
                with self.assertRaises(ValueError):
                    overlay.validate_overlay(d, self.coverage)

    def test_observation_clock_is_not_a_provider_quote(self):
        def change(d):
            r = self.winner(d)
            r['quote_at'] = r['acquired_at']
        self.reject(change)

    def test_missing_quote_requires_exact_observation_only_label(self):
        self.reject(lambda d: self.winner(d).update(quote_clock_kind='PROVIDER_QUOTE'))

    def test_other_provider_cannot_invent_observation_only_exception(self):
        self.reject(lambda d: self.winner(d, 'DraftKings').update(quote_at=None, quote_clock_kind=overlay.OBSERVATION_ONLY))

    def test_capture_after_kickoff_is_rejected(self):
        def change(d):
            r = self.winner(d)
            r['acquired_at'] = next(g['kickoff_utc'] for g in self.coverage['all_games'] if g['game_id'] == r['game_id'])
        self.reject(change)

    def test_capture_after_overlay_clock_is_rejected(self):
        self.reject(lambda d: d.update(as_of='2000-01-01T00:00:00Z'))

    def test_provider_quote_after_acquisition_is_rejected(self):
        self.reject(lambda d: self.winner(d, 'DraftKings').update(quote_at='2026-11-05T00:00:00Z'))

    def test_missing_current_state_cannot_disappear(self):
        self.reject(lambda d: d['winner_rows'].pop())

    def test_duplicate_current_state_is_rejected(self):
        self.reject(lambda d: d['point_rows'].append(copy.deepcopy(d['point_rows'][0])))

    def test_coverage_inflation_is_rejected(self):
        self.reject(lambda d: d['coverage'][0].update(available_games=15))

    def test_threshold_cannot_become_score_projection(self):
        self.reject(lambda d: self.point(d).update(point_estimate=3.5))

    def test_current_reference_cannot_enter_paired_metrics(self):
        self.reject(lambda d: self.point(d).update(metric_eligible=True))

    def test_current_capture_cannot_gain_an_earlier_cutoff(self):
        self.reject(lambda d: self.point(d).update(cutoff_at='2026-11-01T00:00:00Z'))

    def test_unqualified_winner_cannot_gain_a_probability(self):
        def change(d):
            next(r for r in d['winner_rows'] if r['derived_pick'] is None)['p_home'] = .6
        self.reject(change)

    def test_missing_new_reference_preserves_old_usable_reference(self):
        base = {'derived_pick': 'A', 'quote_at': '2026-11-03T12:00:00Z'}
        missing = {'derived_pick': None, 'acquired_at': '2026-11-04T00:00:00Z'}
        self.assertIs(overlay.choose_latest_reference(base, missing, 'derived_pick'), base)

    def test_older_new_quote_cannot_replace_newer_existing_quote(self):
        base = {'line': 3.5, 'quote_at': '2026-11-03T12:00:00Z'}
        older = {'line': 2.5, 'quote_at': '2026-11-03T11:00:00Z'}
        self.assertIs(overlay.choose_latest_reference(base, older, 'line'), base)

    def test_newer_observation_only_reference_remains_observation_only(self):
        base = {'derived_pick': None}
        recovered = self.winner(self.data)
        selected = overlay.choose_latest_reference(base, recovered, 'derived_pick')
        self.assertIs(selected, recovered)
        self.assertIsNone(selected['quote_at'])
        self.assertEqual(selected['quote_clock_kind'], overlay.OBSERVATION_ONLY)

    def test_source_overlay_does_not_contain_model_fields(self):
        self.assertNotIn('forecasts', self.data)
        game = next(g for g in self.coverage['all_games'] if g['game_id'] == '2026_09_JAX_BAL')
        forecast = next(f for f in game['forecasts'] if f['model_id'] == 'selected_latest_origin')
        self.assertEqual((forecast['pick'], forecast['home_margin'], forecast['total']), ('JAX', -4.0, 45.7))


if __name__ == '__main__':
    unittest.main()
