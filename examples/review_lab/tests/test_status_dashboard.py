import json
import unittest
from examples.review_lab.build_status_dashboard import payload, render, ROOT, OUTPUT


class StatusDashboardTests(unittest.TestCase):
    def test_generated_page_is_exact(self):
        self.assertEqual(OUTPUT.read_text(), render())

    def test_actual_counts_reconcile(self):
        x = payload()["completed_research"]
        self.assertEqual(x["inherited_completed_units"] + x["new_completed_units"], x["cumulative_completed_units"])
        self.assertEqual(x["new_completed_optimizer_calls"] + x["new_certified_zero_call_endpoints"], x["new_completed_units"])
        self.assertEqual(x["cumulative_completed_units"] + x["remaining_units"], x["registered_units"])
        self.assertEqual(x["cumulative_attempts"] - x["cumulative_failed_attempts"], x["cumulative_completed_units"])

    def test_failure_and_serving_truth(self):
        x = payload()["completed_research"]
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
        x = payload()["completed_research"]
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
        self.assertTrue(x["completed_research"]["serving"]["issued_before_remaining_research"])
        self.assertEqual(sum(x["completed_research"]["serving"]["native_week_counts"].values()),83)

    def test_recoverable_demo_has_no_new_work_on_reentry(self):
        x=payload()["recovery"]
        self.assertEqual(x["reentry"]["new_attempts"],0)
        self.assertEqual(x["reentry"]["reused_stages"],8)
        self.assertTrue(x["forecast_identity_preserved"])

    def test_market_benchmark_is_not_a_failed_challenger(self):
        for row in payload()["rows"]:
            if row["model"] == "MARKET reference" and row["season"] < 2026:
                self.assertEqual(row["qualification"],"REFERENCE_NOT_A_CHALLENGER")


class LatestOwnerBoundaryTests(unittest.TestCase):
    def test_latest_failure_is_distinct_from_completed_prior_research(self):
        x = payload()
        self.assertEqual(x["previous_owner"]["status"], "FAILED")
        self.assertEqual(x["completed_research"]["status"], "SUCCESS")
        self.assertEqual(x["previous_owner"]["extension_completed_units"], 0)
        self.assertEqual(x["previous_owner"]["extension_attempts"], 0)
        self.assertEqual(x["previous_owner"]["extension_predictive_qualification"], "NOT_EVALUATED")
        self.assertEqual(x["previous_owner"]["new_model_comparison_panels"], 0)
        self.assertFalse(any(row["release"] == "V133" for row in x["rows"]))

    def test_fresh_forecast_counts_and_prior_financial_boundary(self):
        x = payload()["previous_owner"]
        self.assertEqual(sum(x["serving"]["native_week_counts"].values()), 82)
        self.assertEqual(x["serving"]["remaining_current_week_games_covered"], 68)
        self.assertEqual(x["financial"]["new_report_status"], "NOT_COMPLETED")
        self.assertEqual(x["financial"]["last_completed_report_release"], "V132")
        self.assertIsNone(x["financial"]["realized_profit"])
        self.assertFalse(x["financial"]["inherited_result_is_actual_profit"])

    def test_actual_dependency_counts_reconcile(self):
        rows = payload()["previous_owner"]["return_dependency_audit"]
        for row in rows:
            self.assertEqual(row["present_verified_files"] + row["missing_files"], row["receipt_required_files"])
            self.assertEqual(row["return_only_closure_complete"], row["missing_files"] == 0)
        self.assertEqual(sum(row["missing_files"] for row in rows), 2318)

    def test_public_owner_export_contains_no_private_paths_or_predictions(self):
        x = json.dumps(payload()["previous_owner"])
        for forbidden in ('/home/', 's3://', 'source_sha256', 'weights', 'player_id', 'api_key', 'contract_id'):
            self.assertNotIn(forbidden, x)
        self.assertNotIn('panels', payload()["previous_owner"])

    def test_portability_demo_separates_readiness_from_execution(self):
        x = payload()["portability"]
        self.assertEqual(x["real_fits"], 0)
        self.assertTrue(x["independent_research_ready"])
        self.assertFalse(x["sparse"]["all_selected_stages_ready"])
        self.assertTrue(x["portable"]["all_selected_stages_ready"])
        self.assertTrue(x["original_decision_preserved"])

    def test_visible_latest_status_matches_owner_receipt(self):
        page = render()
        self.assertIn('Actual V134 owner: SUCCESS', page)
        self.assertIn('89 MARKET-reference games', page)
        self.assertIn('V135 owner execution remains pending', page)
        self.assertNotIn('V133 owner execution remains pending', page)


class V134CompletionTests(unittest.TestCase):
    def test_count_and_qualification_boundaries(self):
        x=payload()['owner']
        self.assertEqual(x['status'],'SUCCESS')
        self.assertEqual(x['extension_completed_units'],12)
        self.assertEqual(x['combined_completed_units'],x['retained_original_units']+x['extension_completed_units'])
        self.assertEqual(x['combined_attempts']-x['combined_completed_units'],x['preserved_failed_attempts'])
        self.assertEqual(x['historical_gates_passed'],0)
        self.assertEqual(x['automatic_promotions'],0)
        self.assertEqual(sum(x['serving']['native_week_counts'].values()),89)
        self.assertIsNone(x['financial']['realized_profit'])
        for stage in x['return_dependency_audit']:
            self.assertEqual(stage['declared_outputs'],stage['verified_outputs'])
            self.assertEqual(stage['missing_outputs'],0)

    def test_reference_issue_uses_saved_forecast_issuance_clock(self):
        self.assertEqual(payload()["owner"]["serving"]["issued_at"], "2026-10-28T22:41:33.675073Z")
        self.assertIn("Issued at 22:41:33.675073 UTC", render())
        self.assertNotIn("22:41:26.368680", render())

    def test_shared_inventory_demo_is_not_actual_owner_coverage(self):
        x=payload()['shared_inventory']
        self.assertEqual(x['unique_observations'],1)
        self.assertEqual(x['actual_requests'],0)
        self.assertEqual(x['actual_credits'],0)
        self.assertIn('Invented',x['boundary'])

    def test_latest_receipt_has_no_private_artifacts(self):
        serialized=json.dumps(payload()['owner'])
        for forbidden in ('/home/', 's3://', 'source_sha256', 'weights', 'player_id', 'api_key', 'contract_id'):
            self.assertNotIn(forbidden,serialized)

