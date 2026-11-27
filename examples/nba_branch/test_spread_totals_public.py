"""Public-boundary regressions for the NBA selected-role board."""
import copy
import json
import unittest
from datetime import timedelta

from examples.nba_branch.build_spread_totals import DATA, parse_time, validate


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

    def test_new_week_calendar_retains_saved_research_population_and_gap(self):
        data = validate(self.data)
        self.assertEqual(data["completed_games"], 261)
        self.assertEqual(data["latest_week_calendar"]["final_games"], 22)
        self.assertEqual(data["latest_week_calendar"]["scheduled_games"], 26)
        self.assertEqual(data["latest_week_calendar"]["status_or_score_updated_games"], 9)
        self.assertEqual(data["latest_week_calendar"]["date_game_counts"]["2026-11-26"], 0)
        changed = [g for g in data["games"] if g.get("calendar_observation", {}).get("completed") and not g["completed"]]
        self.assertEqual(len(changed), 9)
        self.assertTrue(all(g["pacific_date"] == "2026-11-25" for g in changed))

    def test_week_calendar_cannot_drop_game_or_claim_season_research_refresh(self):
        data = copy.deepcopy(self.data)
        next(g for g in data["games"] if g["in_week"]).pop("calendar_observation")
        with self.assertRaisesRegex(ValueError, "full saved week"):
            validate(data)
        data = copy.deepcopy(self.data)
        data["latest_week_calendar"]["full_season_census_refreshed"] = True
        with self.assertRaisesRegex(ValueError, "cannot claim"):
            validate(data)

    def test_week_calendar_rejects_rebound_tip_and_unobserved_future_clock(self):
        data = copy.deepcopy(self.data)
        game = next(g for g in data["games"] if g["in_week"])
        game["calendar_observation"]["tip_at_utc"] = "2026-11-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "rebind"):
            validate(data)
        data = copy.deepcopy(self.data)
        after_check = parse_time(data["latest_week_calendar"]["checked_at_utc"]) + timedelta(minutes=1)
        next(g for g in data["games"] if g["in_week"])["calendar_observation"]["source_checked_at_utc"] = after_check.isoformat()
        with self.assertRaisesRegex(ValueError, "outside its observed interval"):
            validate(data)

    def test_week_calendar_rejects_invented_scheduled_score(self):
        data = copy.deepcopy(self.data)
        game = next(g for g in data["games"] if g.get("calendar_observation", {}).get("status") == "SCHEDULED")
        game["calendar_observation"]["away_score"] = 1
        with self.assertRaisesRegex(ValueError, "invent final scores"):
            validate(data)

    def test_live_status_remains_nonfinal_and_cannot_gain_final_score(self):
        data = copy.deepcopy(self.data)
        game = next(g for g in data["games"] if g.get("calendar_observation", {}).get("status") == "SCHEDULED")
        game["calendar_observation"]["status"] = "LIVE"
        calendar = data["latest_week_calendar"]
        calendar["scheduled_games"] -= 1
        calendar["status_counts"]["SCHEDULED"] -= 1
        calendar["status_counts"]["LIVE"] = 1
        calendar["status_or_score_updated_games"] += 1
        self.assertFalse(validate(data)["games"][data["games"].index(game)]["calendar_observation"]["completed"])
        game["calendar_observation"]["away_score"] = 50
        with self.assertRaisesRegex(ValueError, "invent final scores"):
            validate(data)

    def test_calendar_refresh_does_not_establish_fresh_forecasts(self):
        data = copy.deepcopy(self.data)
        data["forecast_freshness"]["model_inputs_refreshed"] = True
        with self.assertRaisesRegex(ValueError, "freshness cannot claim a new model issue"):
            validate(data)

    def test_observed_contracts_keep_alternatives_and_no_model_probability(self):
        self.assertEqual(len(validate(self.data)["observed_contracts"]), 682)
        data = copy.deepcopy(self.data)
        data["observed_contracts"][0]["p_yes"] = .7
        with self.assertRaisesRegex(ValueError, "cannot infer a model probability"):
            validate(data)
        data = copy.deepcopy(self.data)
        data["observed_contracts"].pop()
        with self.assertRaisesRegex(ValueError, "contract denominator"):
            validate(data)

    def test_unavailable_no_ask_quantity_is_not_replaced_with_zero(self):
        data = copy.deepcopy(self.data)
        data["observed_contracts"][0]["no_ask_quantity"] = 0
        with self.assertRaisesRegex(ValueError, "quantity availability differs"):
            validate(data)


if __name__ == "__main__":
    unittest.main()
