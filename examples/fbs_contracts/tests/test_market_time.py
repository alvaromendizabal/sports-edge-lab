import unittest
from examples.fbs_contracts.market_time import instant, known_before_prediction, preserve_inventory, reference_at


class MarketTimeTests(unittest.TestCase):
    def row(self, quote='2026-09-05T22:00:00Z', capture='2026-11-03T22:00:00Z', value=.6, **other):
        return dict(target='winner', quote_at=quote, captured_at=capture, value=value,
                    join_status='matched', reference_kind='minute_candle_close', product='winner', **other)

    def test_backfilled_history_is_visible_but_was_not_possessed(self):
        row = self.row()
        self.assertIs(reference_at([row], 'winner', '2026-09-05T23:00:00Z'), row)
        self.assertFalse(known_before_prediction(row, '2026-09-05T23:00:00Z'))

    def test_later_market_price_cannot_enter_earlier_cutoff(self):
        earlier, later = self.row(), self.row('2026-09-05T23:01:00Z', value=.8)
        self.assertIs(reference_at([later, earlier], 'winner', '2026-09-05T23:00:00Z'), earlier)

    def test_prekickoff_is_strict_but_fixed_cutoff_is_inclusive(self):
        row = self.row()
        self.assertIsNone(reference_at([row], 'winner', row['quote_at'], strict_before=True))
        self.assertIs(reference_at([row], 'winner', row['quote_at']), row)

    def test_late_capture_does_not_change_source_clock_order(self):
        early = self.row('2026-09-05T20:00:00Z', '2026-11-03T23:00:00Z')
        late = self.row('2026-09-05T22:00:00Z', '2026-10-01T23:00:00Z')
        self.assertIs(reference_at([early, late], 'winner', '2026-09-05T23:00:00Z'), late)

    def test_same_time_conflict_is_not_order_dependent(self):
        for rows in ([self.row(value=.4), self.row(value=.6)], [self.row(value=.6), self.row(value=.4)]):
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                reference_at(rows, 'winner', '2026-09-05T23:00:00Z')

    def test_missing_or_incompatible_value_is_not_zero(self):
        self.assertIsNone(reference_at([self.row(value=None)], 'winner', '2026-09-05T23:00:00Z'))
        self.assertIsNone(reference_at([self.row()], 'margin', '2026-09-05T23:00:00Z'))

    def test_zero_valid_reference_is_not_missing(self):
        row = self.row(value=0.0)
        self.assertIs(reference_at([row], 'winner', '2026-09-05T23:00:00Z'), row)

    def test_no_market_cannot_remove_a_game(self):
        rows, quarantine = preserve_inventory([{'id': 'a'}, {'id': 'b'}], [{'game_id': 'a'}, {'game_id': 'x'}])
        self.assertEqual([row['game']['id'] for row in rows], ['a', 'b'])
        self.assertEqual(rows[1]['observations'], [])
        self.assertEqual(quarantine, [{'game_id': 'x'}])

    def test_identity_duplication_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            preserve_inventory([{'id': 'a'}, {'id': 'a'}], [])

    def test_timezone_required_and_offsets_are_equivalent(self):
        with self.assertRaisesRegex(ValueError, 'timezone'):
            instant('2026-11-03T16:00:00')
        self.assertEqual(instant('2026-11-03T16:00:00-08:00'), instant('2026-11-04T00:00:00Z'))

    def test_unverified_identity_cannot_enter_market_comparison(self):
        row = self.row(); row['join_status'] = 'quarantined'
        self.assertIsNone(reference_at([row], 'winner', '2026-09-05T23:00:00Z'))

    def test_recorded_capture_can_be_earlier_than_later_prediction(self):
        row = self.row(capture='2026-09-05T22:00:01Z')
        self.assertTrue(known_before_prediction(row, '2026-09-05T23:00:00Z'))

    def test_capture_without_source_clock_cannot_reconstruct_an_old_price(self):
        row = self.row(quote=None)
        self.assertIsNone(reference_at([row], 'winner', '2026-09-05T23:00:00Z'))
        self.assertFalse(known_before_prediction(row, '2026-09-05T23:00:00Z'))

    def test_source_timed_history_is_preferred_to_an_early_capture_fallback(self):
        history = self.row(quote='2026-09-05T21:58:00Z')
        captured = self.row(quote=None, capture='2026-09-05T22:00:00Z')
        self.assertIs(reference_at([captured, history], 'winner', '2026-09-05T23:00:00Z'), history)
        self.assertIs(reference_at([captured], 'winner', '2026-09-05T23:00:00Z'), captured)
        self.assertTrue(known_before_prediction(captured, '2026-09-05T23:00:00Z'))

    def test_earlier_query_quote_remains_available_for_a_later_window(self):
        earlier=self.row(source_query_cutoff_kind='T120')
        self.assertIs(reference_at([earlier],'winner','2026-09-05T23:00:00Z',strict_before=True,registered_cutoff_kind='LATEST_BEFORE_KICKOFF'),earlier)

    def test_point_proxy_stays_in_its_registered_window(self):
        earlier=self.row(value=14.5,registered_cutoff_kind='T120');earlier['target']='margin'
        later=self.row(quote='2026-09-05T21:00:00Z',value=16.5,registered_cutoff_kind='LATEST_BEFORE_KICKOFF');later['target']='margin'
        self.assertIs(reference_at([earlier,later],'margin','2026-09-05T23:00:00Z',strict_before=True,registered_cutoff_kind='LATEST_BEFORE_KICKOFF'),later)
        self.assertIsNone(reference_at([earlier],'margin','2026-09-05T23:00:00Z',registered_cutoff_kind='T60'))

    def test_equivalent_archived_sportsbook_tie_retains_captured_evidence(self):
        old=self.row(capture=None);old.update(product='SPORTSBOOK_WINNER_H2H_DEVIGGED',reference_kind='archived_devigged_probability')
        new=self.row();new.update(product='sportsbook_game_market',reference_kind='vig_removed_two_way_probability')
        for observations in [[old,new],[new,old]]:
            self.assertIs(reference_at(observations,'winner','2026-09-05T23:00:00Z'),new)
        new['value']=.7
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            reference_at([old,new],'winner','2026-09-05T23:00:00Z')

    def test_equal_values_do_not_merge_incompatible_products(self):
        old,new=self.row(),self.row();new['product']='different_settlement_product'
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            reference_at([old,new],'winner','2026-09-05T23:00:00Z')


if __name__ == '__main__':
    unittest.main()
