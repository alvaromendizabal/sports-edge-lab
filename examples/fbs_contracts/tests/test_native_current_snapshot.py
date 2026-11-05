"""Invented current-only display contracts; no raw feeds, model or cloud."""
from copy import deepcopy
import unittest

from examples.fbs_contracts.native_current_snapshot import (
    BOUNDS, MISSING, POSTGAME, PROVIDERS, REGISTRATION, SCHEMA, TARGETS, WINNER,
    validate_snapshot,
)


CAPTURE = "2026-11-05T05:25:00Z"
ASSESSMENT = "2026-11-05T07:00:00Z"
WINDOW = {"start_inclusive_utc": "2026-11-02T08:00:00Z", "end_exclusive_utc": "2026-11-09T08:00:00Z"}


def fixture():
    game = {"id": "100", "season": 2026, "phase": "regular", "week": 10,
            "kickoff": "2026-11-07T20:00:00Z", "markets": {p: [] for p in PROVIDERS}}
    slots = [{"captured_at": None, "game_id": "100", "lower_bound": None, "observed_contracts": 0,
              "p_home": None, "provider": p, "quote_at": None, "status": MISSING,
              "support_available_at": None, "target": t, "upper_bound": None} for p in PROVIDERS for t in TARGETS]
    slot = slots[0]
    slot.update(captured_at=CAPTURE, observed_contracts=2, p_home=.6, status=WINNER)
    row = {"captured_at": CAPTURE, "quote_at": None, "price_status": WINNER,
           "source_query_cutoff_kind": "current", "registered_cutoff_kind": REGISTRATION,
           "product": "verified_native_current_snapshot", "evidence_kind": "current_public_observation",
           "executable": False, "target": "winner", "value": .6, "picked_home": True, "point_support": None}
    game["markets"]["Kalshi"].append(row)
    counts = {}
    for s in slots:
        key = f'{s["provider"]}:{s["target"]}:{s["status"]}'
        counts[key] = counts.get(key, 0) + 1
    snapshot = {
        "captured_at_max": CAPTURE, "captured_at_min": CAPTURE,
        "expected_margin_or_total_invented": False, "genuine_forecasts_issued": 0,
        "inconsistent_us_margin_groups": 0, "inconsistent_us_total_groups": 0,
        "individual_quote_clock_proved": False, "latest_pre_kickoff_history_complete": False,
        "model_input_admitted": False, "official_current_week_games": 1, "orders": 0,
        "phase": "regular", "point_basis": "Invented median interval, not expected score",
        "product_slots": 9, "quote_at": None, "registered_cutoff_kind": REGISTRATION,
        "schema": SCHEMA, "season": 2026, "slots": slots, "source_release": "V030",
        "source_time_not_replaced_with_review_time": True, "stake_usd": 0, "status_counts": counts,
        "us_literal_side_prices_and_quotes_not_used_as_book": True,
        "view": "current", "week": 10, "winner_basis": "Invented descriptive midpoint",
    }
    return snapshot, [game]


def recount(snapshot):
    counts = {}
    for s in snapshot["slots"]:
        key = f'{s["provider"]}:{s["target"]}:{s["status"]}'
        counts[key] = counts.get(key, 0) + 1
    snapshot["status_counts"] = counts


class NativeCurrentSnapshotTests(unittest.TestCase):
    def check(self, snapshot, games):
        return validate_snapshot(snapshot, games, prepared_at=ASSESSMENT, current_week=WINDOW)

    def test_complete_invented_grid_and_missing_slots_remain(self):
        snapshot, games = fixture()
        self.assertIs(self.check(snapshot, games), snapshot)
        self.assertEqual(len(snapshot["slots"]), 9)
        self.assertEqual(sum(s["status"] == MISSING for s in snapshot["slots"]), 8)

    def test_current_references_require_explicit_grid(self):
        _, games = fixture()
        with self.assertRaisesRegex(ValueError, "complete explicit slot grid"):
            self.check(None, games)

    def test_missing_product_never_acquires_a_clock(self):
        snapshot, games = fixture(); snapshot["slots"][1]["captured_at"] = CAPTURE
        with self.assertRaisesRegex(ValueError, "Missing native product"):
            self.check(snapshot, games)

    def test_duplicate_slot_cannot_preserve_only_total_count(self):
        snapshot, games = fixture(); snapshot["slots"][1] = deepcopy(snapshot["slots"][0])
        with self.assertRaisesRegex(ValueError, "duplicate or foreign"):
            self.check(snapshot, games)

    def test_foreign_game_slot_cannot_replace_an_official_game(self):
        snapshot, games = fixture(); snapshot["slots"][1]["game_id"] = "101"
        with self.assertRaisesRegex(ValueError, "foreign identity"):
            self.check(snapshot, games)

    def test_changed_rounded_winner_value_breaks_reference_closure(self):
        snapshot, games = fixture(); games[0]["markets"]["Kalshi"][0]["value"] = .7
        with self.assertRaisesRegex(ValueError, "winner"):
            self.check(snapshot, games)

    def test_current_capture_cannot_admit_model_or_history(self):
        for flag in ("model_input_admitted", "latest_pre_kickoff_history_complete", "individual_quote_clock_proved"):
            snapshot, games = fixture(); snapshot[flag] = True
            with self.assertRaisesRegex(ValueError, "model/history/mean"):
                self.check(snapshot, games)

    def test_quote_clock_is_not_invented_from_capture(self):
        snapshot, games = fixture(); snapshot["slots"][0]["quote_at"] = CAPTURE
        with self.assertRaisesRegex(ValueError, "invented quote clock"):
            self.check(snapshot, games)

    def test_unknown_nested_field_rejected_before_publication(self):
        snapshot, games = fixture(); snapshot["slots"][0]["raw_book"] = [.4, .8]
        with self.assertRaisesRegex(ValueError, "Unknown native product slot field"):
            self.check(snapshot, games)

    def test_status_count_must_equal_all_retained_slots(self):
        snapshot, games = fixture(); snapshot["status_counts"][f"Kalshi:winner:{WINNER}"] = 2
        with self.assertRaisesRegex(ValueError, "status counts"):
            self.check(snapshot, games)

    def test_postgame_capture_is_retained_without_pregame_value(self):
        snapshot, games = fixture(); games[0]["kickoff"] = "2026-11-04T20:00:00Z"
        snapshot["slots"][0].update(status=POSTGAME, p_home=None)
        games[0]["markets"]["Kalshi"][0].update(price_status=POSTGAME, value=None, picked_home=None)
        recount(snapshot)
        self.assertIs(self.check(snapshot, games), snapshot)

    def test_false_postgame_classification_rejected(self):
        snapshot, games = fixture(); snapshot["slots"][0].update(status=POSTGAME, p_home=None)
        games[0]["markets"]["Kalshi"][0].update(price_status=POSTGAME, value=None, picked_home=None)
        recount(snapshot)
        with self.assertRaisesRegex(ValueError, "Postgame classification"):
            self.check(snapshot, games)

    def test_mean_or_scalar_cannot_replace_median_interval(self):
        snapshot, games = fixture()
        slot = snapshot["slots"][1]
        slot.update(status=BOUNDS, observed_contracts=4, captured_at=CAPTURE, lower_bound=3.5,
                    upper_bound=5.5, support_available_at=CAPTURE)
        support = {"lower_bound": 3.5, "upper_bound": 5.5, "support_available_at": CAPTURE}
        row = dict(games[0]["markets"]["Kalshi"][0], target="margin", price_status=BOUNDS,
                   value=None, picked_home=None, point_support=support)
        games[0]["markets"]["Kalshi"].append(row)
        recount(snapshot)
        self.assertIs(self.check(snapshot, games), snapshot)
        row["value"] = 4.5
        with self.assertRaisesRegex(ValueError, "invented scalar"):
            self.check(snapshot, games)

    def test_future_capture_not_allowed_in_older_assessment(self):
        snapshot, games = fixture()
        with self.assertRaisesRegex(ValueError, "future"):
            validate_snapshot(snapshot, games, prepared_at="2026-11-04T00:00:00Z", current_week=WINDOW)


if __name__ == "__main__":
    unittest.main()
