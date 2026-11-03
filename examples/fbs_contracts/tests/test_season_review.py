"""Release checks for the public all-game explorer; these create no owner fits."""
import copy
import json
import unittest
from examples.fbs_contracts.build_season_review import DATA, OUTPUT, render, validate
from examples.fbs_contracts.market_time import known_before_prediction, reference_at


class SeasonReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())

    def altered(self):
        return copy.deepcopy(self.data)

    def test_deterministic_page_keeps_all_888_games_without_script(self):
        page = render(self.data)
        self.assertEqual(page, OUTPUT.read_text())
        self.assertEqual(page.count('data-game="'), 888)
        self.assertIn('Aug 29 · 9:00 AM PDT', page)

    def test_game_loss_is_not_hidden_as_a_provider_filter(self):
        data = self.altered(); data['games'].pop()
        with self.assertRaisesRegex(ValueError, 'denominator'):
            validate(data)

    def test_duplicate_games_are_rejected(self):
        data = self.altered(); data['games'][1]['id'] = data['games'][0]['id']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate(data)

    def test_postgame_outcome_cannot_fill_future_model_or_actual(self):
        data = self.altered(); game = next(g for g in data['games'] if not g['completed'])
        game['home_points'] = 24
        with self.assertRaisesRegex(ValueError, 'Future scores'):
            validate(data)

    def test_unissued_replay_cannot_become_prospective(self):
        data = self.altered(); data['games'][0]['replay']['issued_at'] = '2026-08-29T10:00:00Z'
        with self.assertRaisesRegex(ValueError, 'Replay cannot become an issue'):
            validate(data)

    def test_private_transform_or_raw_feed_is_not_a_public_field(self):
        data = self.altered(); data['games'][0]['markets']['DraftKings'][0]['raw_bid_array'] = [.5]
        with self.assertRaisesRegex(ValueError, 'public reference field'):
            validate(data)

    def test_private_path_is_rejected_even_in_a_text_field(self):
        data = self.altered(); data['games'][0]['home'] = 's3://private/example'
        with self.assertRaisesRegex(ValueError, 'Private field'):
            validate(data)

    def test_catalog_without_quote_clock_is_preserved_but_not_cutoff_qualified(self):
        row = {'target':'winner','value':.6,'join_status':'matched',
               'quote_at':None,'captured_at':'2026-11-03T12:00:00Z'}
        self.assertIsNone(reference_at([row], 'winner', '2026-11-03T13:00:00Z'))
        self.assertFalse(known_before_prediction(row, '2026-11-03T13:00:00Z'))

    def test_candle_bucket_cannot_cross_cutoff(self):
        row = {'target':'winner','value':.6,'join_status':'matched',
               'quote_at':'2026-11-03T12:59:00Z','interval_end_at':'2026-11-03T13:01:00Z',
               'captured_at':'2026-11-03T13:02:00Z'}
        self.assertIsNone(reference_at([row], 'winner', '2026-11-03T13:00:00Z'))
        self.assertFalse(known_before_prediction(row, '2026-11-03T13:00:00Z'))

    def test_dst_calendar_week_and_native_week_are_distinct(self):
        data = self.data
        self.assertEqual(data['windows']['previous_complete_week']['elapsed_hours'],169)
        self.assertEqual(data['inventory']['last_week_games'],56)
        self.assertEqual(sum(r['games'] for r in data['weekly']),622)
        self.assertEqual(sum(r['correct_winner'] for r in data['weekly']),465)

    def test_executable_quote_or_order_requires_new_contract(self):
        data = self.altered(); data['games'][0]['markets']['DraftKings'][0]['executable'] = True
        with self.assertRaisesRegex(ValueError, 'executable'):
            validate(data)

    def test_replayed_winner_correctness_cannot_be_reversed(self):
        data = self.altered(); data['games'][0]['replay']['correct'] = not data['games'][0]['replay']['correct']
        with self.assertRaisesRegex(ValueError, 'Winner correctness'):
            validate(data)


if __name__ == '__main__':
    unittest.main()
