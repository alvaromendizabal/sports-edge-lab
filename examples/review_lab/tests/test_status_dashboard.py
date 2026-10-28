import json
import unittest
from examples.review_lab.build_status_dashboard import payload, render, ROOT, OUTPUT


class StatusDashboardTests(unittest.TestCase):
    def test_generated_page_is_exact(self):
        self.assertEqual(OUTPUT.read_text(), render())

    def test_actual_counts_reconcile(self):
        x = payload()["latest"]
        self.assertEqual(x["inherited_completed_units"] + x["new_completed_units"], x["cumulative_completed_units"])
        self.assertEqual(x["new_completed_optimizer_calls"] + x["new_certified_zero_call_endpoints"], x["new_completed_units"])
        self.assertEqual(x["cumulative_completed_units"] + x["remaining_units"], x["registered_units"])
        self.assertEqual(x["cumulative_attempts"] - x["cumulative_failed_attempts"], x["cumulative_completed_units"])

    def test_failure_and_serving_truth(self):
        x = payload()["latest"]
        self.assertEqual(x["status"], "SUCCESS")
        self.assertEqual(x["next_owner_execution"], "PENDING")
        self.assertEqual(x["new_current_forecasts"], 83)
        self.assertEqual(x["research_status"], "COMPLETE")
        self.assertLessEqual(x["certificate"]["new_accepted_gap_max"], x["certificate"]["gap_limit"])
        self.assertEqual(x["historical_gates_passed"], 0)
        self.assertEqual(x["financial"]["qualified_executions"], 0)

    def test_partial_historical_panels_are_matched(self):
        rows = [r for r in payload()["rows"] if r["release"] == "V131"]
        self.assertEqual(len(rows), 20)
        for year in (2024, 2025):
            for policy in ("annual", "fixed"):
                selected = [r for r in rows if r["season"] == year and r["policy"] == policy]
                self.assertEqual(len(selected), 5)
                self.assertEqual(len({r["games"] for r in selected}), 1)
                self.assertEqual(len({r["cohort_sha256"] for r in selected}), 1)
                self.assertTrue(all(r["qualification"] == "INCOMPLETE" for r in selected if r["model"] != "MARKET reference"))
                market = next(r for r in selected if r["model"] == "MARKET reference")
                for r in selected:
                    self.assertGreaterEqual(r["win_logloss"], market["win_logloss"])
                    self.assertGreaterEqual(r["win_brier"], market["win_brier"])

    def test_monitoring_preserves_old_vintage(self):
        rows = [r for r in payload()["rows"] if r["season"] == 2026 and r["release"] == "V129"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["release"] == "V129" and r["qualification"] == "NOT_FOR_SELECTION" for r in rows))
        self.assertEqual({r["games"] for r in rows}, {77, 301})

    def test_synthetic_outputs_reproduced(self):
        from examples.review_lab.fault_isolation import walkthrough
        for name, result in payload()["scenarios"].items():
            self.assertEqual(result, walkthrough(name))

    def test_public_allowlist(self):
        x = payload()["latest"]
        for row in x["panels"]:
            self.assertLessEqual(set(row), {"season", "policy", "games", "win_logloss", "win_brier", "ece10", "correct", "incorrect", "cohort_sha256", "origin", "model", "league", "scope", "mode", "qualification", "delta_ci95"})
        self.assertNotIn("weights", json.dumps(x))
        self.assertNotIn("/home/", json.dumps(x))
        self.assertNotIn("run_id", x)

    def test_latest_panels_complete_and_monitoring_reconstructed(self):
        x=payload();rows=[r for r in x["rows"] if r["release"]=="V132"]
        self.assertEqual(len(rows),50)
        self.assertEqual(len(x["rows"]),80)
        for row in rows:
            if row["season"]==2026:
                self.assertEqual(row["qualification"],"NOT_FOR_SELECTION")
                self.assertIn("not archived pregame",row["scope"])
        self.assertTrue(x["latest"]["serving"]["issued_before_remaining_research"])
        self.assertEqual(sum(x["latest"]["serving"]["native_week_counts"].values()),83)

    def test_recoverable_demo_has_no_new_work_on_reentry(self):
        x=payload()["recovery"]
        self.assertEqual(x["reentry"]["new_attempts"],0)
        self.assertEqual(x["reentry"]["reused_stages"],8)
        self.assertTrue(x["forecast_identity_preserved"])

    def test_market_benchmark_is_not_a_failed_challenger(self):
        for row in payload()["rows"]:
            if row["model"] == "MARKET reference" and row["season"] < 2026:
                self.assertEqual(row["qualification"],"REFERENCE_NOT_A_CHALLENGER")
