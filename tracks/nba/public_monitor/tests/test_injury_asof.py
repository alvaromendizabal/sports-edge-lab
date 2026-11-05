"""Public boundary and information-time tests using invented inputs only."""
import copy
import unittest

from tracks.nba.public_monitor import injury_asof as injuries


class InjuryAsOfTests(unittest.TestCase):
    def choose(self, reports, horizon="T60", mode="ACTUAL_POSSESSION", **changes):
        args = dict(event="invented-game", team="Example Home", tip_at="2035-01-10T20:00:00Z", horizon=horizon, mode=mode)
        args.update(changes)
        return injuries.select_snapshot(reports, **args)

    def test_t120_t60_latest_are_distinct(self):
        reports = [injuries.invented_snapshot(), injuries.invented_snapshot(
            report_id="r2", published_at="2035-01-10T18:30:00Z", possessed_at="2035-01-10T18:35:00Z"),
            injuries.invented_snapshot(report_id="r3", published_at="2035-01-10T19:30:00Z", possessed_at="2035-01-10T19:35:00Z")]
        self.assertEqual([self.choose(reports, h)["snapshot"]["report_id"] for h in injuries.HORIZONS], ["invented-report-1", "r2", "r3"])

    def test_cutoff_inclusive_tip_exclusive(self):
        on_t60 = injuries.invented_snapshot(published_at="2035-01-10T19:00:00Z", possessed_at="2035-01-10T19:00:00Z")
        self.assertEqual(self.choose([on_t60])["status"], "ELIGIBLE_REPORT_SNAPSHOT")
        on_tip = injuries.invented_snapshot(published_at="2035-01-10T20:00:00Z", possessed_at="2035-01-10T20:00:00Z")
        self.assertEqual(self.choose([on_tip], "LATEST_BEFORE_TIP")["status"], "MISSING_ELIGIBLE_REPORT")

    def test_late_possession_only_in_retrospective_reconstruction(self):
        old = injuries.invented_snapshot()
        later = injuries.invented_snapshot(report_id="r2", published_at="2035-01-10T18:30:00Z", possessed_at="2035-01-11T10:00:00Z")
        self.assertEqual(self.choose([old, later])["snapshot"]["report_id"], old["report_id"])
        reconstructed = self.choose([old, later], mode="PUBLICATION_RECONSTRUCTION")
        self.assertEqual(reconstructed["snapshot"]["report_id"], "r2")
        self.assertFalse(reconstructed["prospective_forecast_claimed"])
        self.assertEqual(reconstructed["snapshot"]["possessed_at"], later["possessed_at"])

    def test_unknown_possession_does_not_become_health(self):
        chosen = self.choose([injuries.invented_snapshot(possessed_at=None)])
        self.assertEqual(chosen["status"], "UNKNOWN_POSSESSION_CLOCK")
        self.assertIsNone(injuries.player_status(chosen, "Example Player")["status"])

    def test_unknown_newer_possession_is_explicit_gap(self):
        reports = [injuries.invented_snapshot(), injuries.invented_snapshot(report_id="r2", published_at="2035-01-10T18:30:00Z", possessed_at=None)]
        self.assertEqual(self.choose(reports)["status"], "UNKNOWN_POSSESSION_CLOCK")

    def test_unsubmitted_latest_blocks_old_player_carry_forward(self):
        reports = [injuries.invented_snapshot(), injuries.invented_snapshot(report_id="r2", published_at="2035-01-10T18:30:00Z", possessed_at="2035-01-10T18:35:00Z", submission="NOT_YET_SUBMITTED", players=[])]
        chosen = self.choose(reports)
        self.assertEqual(chosen["status"], "NOT_YET_SUBMITTED")
        self.assertEqual(chosen["player_rows"], [])

    def test_absent_player_is_unknown_not_healthy_or_old_status(self):
        old = injuries.invented_snapshot()
        newer = injuries.invented_snapshot(report_id="r2", published_at="2035-01-10T18:30:00Z", possessed_at="2035-01-10T18:35:00Z", players=[])
        state = injuries.player_status(self.choose([old, newer]), "Example Player")
        self.assertIsNone(state["status"])
        self.assertEqual(state["reason"], "ABSENT_FROM_SELECTED_REPORT")

    def test_status_probabilities_are_not_invented(self):
        chosen = self.choose([injuries.invented_snapshot()])
        state = injuries.player_status(chosen, "Example Player")
        self.assertEqual(state["status"], "Questionable")
        self.assertIsNone(state["absence_probability"])

    def test_incomplete_unknown_and_conflicting_snapshots_block(self):
        self.assertEqual(self.choose([injuries.invented_snapshot(complete=False)])["status"], "INCOMPLETE_REPORT_PARSE")
        unknown = injuries.invented_snapshot(players=[{"player": "Example Player", "status": "Unknown"}])
        self.assertEqual(self.choose([unknown])["status"], "UNKNOWN_PLAYER_STATUS")
        self.assertEqual(self.choose([injuries.invented_snapshot(), injuries.invented_snapshot(report_id="other")])["status"], "CONFLICTING_REPORTS_AT_PUBLICATION_CLOCK")

    def test_identity_event_team_and_timezone_boundaries(self):
        row = injuries.invented_snapshot()
        before = copy.deepcopy(row)
        self.assertEqual(self.choose([row], event="different")["status"], "MISSING_ELIGIBLE_REPORT")
        self.assertEqual(self.choose([row], team="different")["status"], "MISSING_ELIGIBLE_REPORT")
        self.assertEqual(self.choose([row], tip_at="2035-01-10T15:00:00-05:00")["snapshot"], row)
        self.assertEqual(row, before)
        with self.assertRaises(ValueError): self.choose([row], tip_at="2035-01-10T20:00:00")

    def test_immutable_identity_duplicates_and_real_inputs(self):
        row = injuries.invented_snapshot()
        self.assertEqual(len(injuries.snapshot_union([row, row])), 1)
        for changed in (injuries.invented_snapshot(complete=False),):
            with self.assertRaises(ValueError): injuries.snapshot_union([row, changed])
        with self.assertRaises(ValueError): injuries.validate(injuries.invented_snapshot(data_kind="REAL"))
        with self.assertRaises(ValueError): injuries.validate(injuries.invented_snapshot(possessed_at="2035-01-10T15:00:00Z"))
        with self.assertRaises(ValueError): injuries.validate(injuries.invented_snapshot(players=row["players"] * 2))

    def test_four_arms_register_without_fits_selection_or_orders(self):
        protocol = injuries.preregistered_arms()
        self.assertEqual(len(protocol["arms"]), 4)
        self.assertFalse(protocol["current_season_selection"])
        self.assertFalse(protocol["existing_forecasts_revised"])
        for arm in protocol["arms"][1:]:
            self.assertEqual(arm["status"], "BLOCKED_MISSING_CAUSAL_INPUTS")
        for field in ("new_fits", "new_forecasts", "new_orders"):
            self.assertEqual(protocol[field], 0)


if __name__ == "__main__":
    unittest.main()
