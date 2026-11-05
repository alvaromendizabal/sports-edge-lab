"""Latest source-observed display is separate from possession and benchmarks."""
import copy
import unittest

from examples.fbs_contracts.market_time import availability_reference_at, known_before_prediction, reference_at


class AvailabilityReferenceTests(unittest.TestCase):
    cutoff = '2026-09-05T23:00:00Z'
    assessed = '2026-11-04T18:00:00Z'

    def row(self, quote='2026-09-05T21:00:00Z', capture='2026-11-03T22:00:00Z', value=.6, **other):
        row = dict(target='winner', quote_at=quote, captured_at=capture, value=value,
                   picked_home=value is not None and value > .5, join_status='matched',
                   reference_kind='minute_candle_close', product='winner')
        row.update(other)
        return row

    def choose(self, rows, **kwargs):
        return availability_reference_at(rows, kwargs.pop('target', 'winner'), self.cutoff,
            assessed_at=kwargs.pop('assessed_at', self.assessed), **kwargs)

    def test_newer_actual_capture_not_hidden_by_older_timestamped_observation(self):
        historical = self.row()
        captured = self.row(quote=None, capture='2026-09-05T22:00:00Z', value=.7)
        for rows in ([historical, captured], [captured, historical]):
            self.assertIs(self.choose(rows), captured)
            # Existing benchmark selector is intentionally unchanged.
            self.assertIs(reference_at(rows, 'winner', self.cutoff), historical)

    def test_later_retrieved_history_remains_visible_with_its_real_clock(self):
        recovered = self.row(quote='2026-09-05T22:59:00Z', capture='2026-11-03T22:00:00Z')
        self.assertIs(self.choose([recovered], strict_before=True), recovered)
        self.assertEqual(recovered['captured_at'], '2026-11-03T22:00:00Z')
        self.assertFalse(known_before_prediction(recovered, self.cutoff))

    def test_postgame_capture_only_cannot_reconstruct_pregame_price(self):
        late = self.row(quote=None, capture='2026-09-05T23:00:01Z')
        self.assertIsNone(self.choose([late], strict_before=True))

    def test_latest_source_quote_wins_even_when_captured_snapshot_is_present(self):
        early_capture = self.row(quote=None, capture='2026-09-05T22:00:00Z')
        late_quote = self.row(quote='2026-09-05T22:59:59Z', value=.7)
        self.assertIs(self.choose([early_capture, late_quote], strict_before=True), late_quote)

    def test_cutoff_boundary_inclusive_only_when_explicit(self):
        for row in (self.row(quote=self.cutoff), self.row(quote=None, capture=self.cutoff)):
            with self.subTest(clock=row['quote_at']):
                self.assertIs(self.choose([row]), row)
                self.assertIsNone(self.choose([row], strict_before=True))

    def test_whole_candle_must_precede_strict_kickoff(self):
        crossing = self.row(quote='2026-09-05T22:59:00Z', interval_end_at='2026-09-05T23:00:01Z')
        ending_at = self.row(quote='2026-09-05T22:59:00Z', interval_end_at=self.cutoff)
        self.assertIsNone(self.choose([crossing]))
        self.assertIsNone(self.choose([ending_at], strict_before=True))
        self.assertIs(self.choose([ending_at]), ending_at)

    def test_reversed_interval_is_an_error_not_a_fallback(self):
        row = self.row(interval_end_at='2026-09-05T20:59:59Z')
        with self.assertRaisesRegex(ValueError, 'Invalid availability'):
            self.choose([row])

    def test_report_cannot_use_retrieval_after_its_assessed_clock(self):
        late_capture = self.row(capture='2026-11-04T18:00:01Z')
        self.assertIsNone(self.choose([late_capture]))
        self.assertIs(self.choose([late_capture], assessed_at=None), late_capture)

    def test_report_cannot_use_future_observation_or_unfinished_interval(self):
        future_quote = self.row(quote='2026-09-05T22:30:00Z', capture='2026-09-05T22:31:00Z')
        self.assertIsNone(self.choose([future_quote], assessed_at='2026-09-05T22:00:00Z'))
        future_end = self.row(quote='2026-09-05T21:59:00Z', capture='2026-09-05T22:00:00Z', interval_end_at='2026-09-05T22:01:00Z')
        self.assertIsNone(self.choose([future_end], assessed_at='2026-09-05T22:00:00Z'))

    def test_same_clock_conflict_quarantined_regardless_of_input_order(self):
        quote = self.row(quote='2026-09-05T22:00:00Z', value=.4)
        capture = self.row(quote=None, capture='2026-09-05T22:00:00Z', value=.6)
        for rows in ([quote, capture], [capture, quote]):
            with self.assertRaisesRegex(ValueError, 'Conflicting availability'):
                self.choose(rows)

    def test_same_value_with_different_product_is_not_averaged(self):
        first, second = self.row(), self.row(product='different_settlement')
        with self.assertRaisesRegex(ValueError, 'Conflicting availability'):
            self.choose([first, second])

    def test_same_value_with_different_winner_identity_is_not_hidden(self):
        first, second = self.row(), self.row(picked_home=False)
        with self.assertRaisesRegex(ValueError, 'Conflicting availability'):
            self.choose([first, second])

    def test_equivalent_sportsbook_aliases_remain_compatible(self):
        first = self.row(reference_kind='archived_devigged_probability', product='SPORTSBOOK_WINNER_H2H_DEVIGGED')
        second = self.row(reference_kind='vig_removed_two_way_probability', product='sportsbook_game_market', capture='2026-11-03T23:00:00Z')
        for rows in ([first, second], [second, first]):
            self.assertIs(self.choose(rows), first)

    def test_proxy_may_not_change_its_registered_window(self):
        row = self.row(target='margin', value=-7.5, registered_cutoff_kind='T120')
        self.assertIsNone(self.choose([row], target='margin', registered_cutoff_kind='T60'))
        self.assertIs(self.choose([row], target='margin', registered_cutoff_kind='T120'), row)

    def test_incompatible_targets_and_unmatched_ids_remain_absent(self):
        self.assertIsNone(self.choose([self.row(target='total', value=52.5)]))
        self.assertIsNone(self.choose([self.row(join_status='quarantined')]))

    def test_missing_nonfinite_and_boolean_values_do_not_become_zero(self):
        for value in (None, True, False, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.assertIsNone(self.choose([self.row(value=value)]))
        zero = self.row(value=0.0)
        self.assertIs(self.choose([zero]), zero)

    def test_missing_capture_is_not_invented_for_timestamped_history(self):
        history = self.row(capture=None)
        self.assertIs(self.choose([history]), history)
        self.assertIsNone(history['captured_at'])
        self.assertFalse(known_before_prediction(history, self.cutoff))
        self.assertIsNone(self.choose([self.row(quote=None, capture=None)]))

    def test_older_conflict_does_not_hide_later_unambiguous_observation(self):
        rows = [self.row(value=.4), self.row(value=.8), self.row(quote='2026-09-05T22:30:00Z')]
        self.assertIs(self.choose(rows), rows[-1])

    def test_scan_bound_raises_instead_of_selecting_truncated_inventory(self):
        with self.assertRaisesRegex(ValueError, 'no partial selection'):
            self.choose((self.row() for _ in range(3)), max_observations=2)
        for limit in (True, 0, 1000001, 1.5):
            with self.subTest(limit=limit), self.assertRaisesRegex(ValueError, 'bounded'):
                self.choose([], max_observations=limit)

    def test_all_input_rows_are_preserved_byte_for_field(self):
        rows = [self.row(), self.row(quote=None, capture='2026-09-05T22:00:00Z')]
        before = copy.deepcopy(rows)
        self.choose(rows)
        self.assertEqual(rows, before)


if __name__ == '__main__':
    unittest.main()
