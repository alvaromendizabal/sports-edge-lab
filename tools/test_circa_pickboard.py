"""Credential-free mathematical and provenance tests; not sports model fits."""

from __future__ import annotations

import unittest

from circa_pickboard import InvalidBoard, build_board


ASOF = "2026-11-13T21:00:00Z"


def game(i: int = 1) -> dict:
    return {
        "game_id": f"TEST_GAME_{i}",
        "home_team": f"TEST_HOME_{i}",
        "away_team": f"TEST_AWAY_{i}",
        "kickoff_utc": "2026-11-15T18:00:00Z",
        "forecast_id": f"TEST_FORECAST_{i}",
        "model_issued_at_utc": "2026-11-13T15:00:00Z",
        "line_captured_at_utc": "2026-11-12T18:00:00Z",
        "official_circa_contest_line": True,
        "contest_line_source": "Circa Million VIII official contest line TEST DATA",
        "spread_home": -3,
        "margin_pmf": {"-3": 0.2, "3": 0.2, "6": 0.6},
    }


class PickBoardTests(unittest.TestCase):
    def test_cover_push_and_expected_contest_points(self):
        result = build_board({"games": [game()]}, ASOF)
        self.assertEqual(result["status"], "INSUFFICIENT_VALID_LINES_OR_FORECASTS")
        self.assertEqual(result["games_with_declared_official_lines"], 1)
        self.assertEqual(len(result["all_eligible_sides"]), 2)
        home = next(x for x in result["all_eligible_sides"] if x["side"] == "HOME")
        away = next(x for x in result["all_eligible_sides"] if x["side"] == "AWAY")
        self.assertEqual(home["p_cover"], 0.6)
        self.assertEqual(home["p_push"], 0.2)
        self.assertEqual(home["p_fail"], 0.2)
        self.assertEqual(home["expected_contest_points"], 0.7)
        self.assertEqual(away["expected_contest_points"], 0.3)
        self.assertEqual(home["contest_spread"], -3)
        self.assertEqual(away["contest_spread"], 3)

    def test_top_five_unique_games_sorted(self):
        result = build_board({"games": [game(i) for i in range(1, 8)]}, ASOF)
        self.assertEqual(result["status"], "FIVE_CANDIDATES_FROM_SUPPLIED_DATA")
        self.assertEqual(len(result["all_eligible_sides"]), 14)
        self.assertEqual(len(result["top_five"]), 5)
        self.assertEqual(len({r["game_id"] for r in result["top_five"]}), 5)
        self.assertTrue(all(x["expected_contest_points"] == 0.7 for x in result["top_five"]))
        self.assertTrue(all(x["side"] == "HOME" for x in result["top_five"]))

    def test_refuses_to_invent_missing_line(self):
        item = game()
        item["official_circa_contest_line"] = False
        result = build_board({"games": [item]}, ASOF)
        self.assertEqual(len(result["all_eligible_sides"]), 0)
        self.assertEqual(result["skipped_games"][0]["reason"], "NO_DECLARED_OFFICIAL_CIRCA_CONTEST_LINE")

    def test_timestamp_after_game_cannot_create_pregame_forecast(self):
        item = game()
        item["model_issued_at_utc"] = "2026-11-15T19:00:00Z"
        result = build_board({"games": [item]}, "2026-11-15T17:00:00Z")
        self.assertEqual(result["skipped_games"][0]["reason"], "INVALID_SOURCE_OR_DISTRIBUTION")
        self.assertIn("precede actual kickoff", result["skipped_games"][0]["detail"])

    def test_started_game_is_not_a_future_pick(self):
        result = build_board({"games": [game()]}, "2026-11-15T18:30:00Z")
        self.assertEqual(result["skipped_games"][0]["reason"], "GAME_ALREADY_STARTED")

    def test_quoted_line_not_yet_captured_as_of_board(self):
        item = game()
        item["line_captured_at_utc"] = "2026-11-14T10:00:00Z"
        result = build_board({"games": [item]}, ASOF)
        self.assertEqual(result["skipped_games"][0]["reason"], "FUTURE_MODEL_OR_LINE_CAPTURE")

    def test_rejects_bad_distribution(self):
        item = game()
        item["margin_pmf"] = {"3": 0.8}
        result = build_board({"games": [item]}, ASOF)
        self.assertIn("sum to 1", result["skipped_games"][0]["detail"])

    def test_rejects_nonhalfpoint_line(self):
        item = game()
        item["spread_home"] = -3.25
        result = build_board({"games": [item]}, ASOF)
        self.assertEqual(result["skipped_games"][0]["reason"], "INVALID_SOURCE_OR_DISTRIBUTION")

    def test_rejects_duplicate_game_id(self):
        with self.assertRaisesRegex(InvalidBoard, "duplicate game_id"):
            build_board({"games": [game(), game()]}, ASOF)

    def test_rejects_naive_timestamps(self):
        with self.assertRaisesRegex(InvalidBoard, "timezone must be explicit"):
            build_board({"games": []}, "2026-11-13T21:00:00")

    def test_pmf_integer_score_and_push_symmetry(self):
        item = game()
        item["margin_pmf"] = {"3": 1.0}
        result = build_board({"games": [item]}, ASOF)
        self.assertEqual(len(result["all_eligible_sides"]), 2)
        self.assertTrue(all(x["p_push"] == 1.0 for x in result["all_eligible_sides"]))
        self.assertTrue(all(x["expected_contest_points"] == 0.5 for x in result["all_eligible_sides"]))


if __name__ == "__main__":
    unittest.main()
