"""Public-boundary regressions for the NBA selected-role board."""
import copy
import json
import unittest

from examples.nba_branch.build_spread_totals import DATA, validate


class PublicBoardBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())

    def test_observed_manifest_and_week_are_preserved(self):
        data = validate(self.data)
        self.assertEqual(len(data["games"]), 1200)
        week = [g for g in data["games"] if g["in_week"]]
        self.assertEqual(len(week), 48)
        self.assertEqual(sum(g["completed"] for g in week), 13)
        game = next(g for g in week if g["game_id"] == "0022600305")
        self.assertIsNone(game["horizons"]["120"]["total"]["value"])
        self.assertIn("fixture time", game["horizons"]["120"]["total"]["missing_reason"])

    def test_private_recipe_field_is_rejected_even_when_nested(self):
        data = copy.deepcopy(self.data)
        data["games"][0]["horizons"]["120"]["winner"]["candidate_id"] = "private"
        with self.assertRaisesRegex(ValueError, "private fields"):
            validate(data)

    def test_reconstruction_cannot_become_pregame_issue(self):
        data = copy.deepcopy(self.data)
        game = next(g for g in data["games"] if g["horizons"]["120"]["winner"]["value"] is not None)
        game["horizons"]["120"]["winner"]["issued_at_utc"] = game["tip_at_utc"]
        with self.assertRaisesRegex(ValueError, "pregame issue"):
            validate(data)

    def test_missing_game_cannot_shrink_denominator(self):
        data = copy.deepcopy(self.data)
        data["games"].pop()
        with self.assertRaisesRegex(ValueError, "denominator"):
            validate(data)

    def test_test_result_cannot_replace_primary_validation_score(self):
        data = copy.deepcopy(self.data)
        role = data["roles"][0]
        role["primary_score"] = role["annual"][2]["metrics"][role["objective"]]
        with self.assertRaisesRegex(ValueError, "annual validation"):
            validate(data)


if __name__ == "__main__":
    unittest.main()
