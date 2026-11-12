"""Validate the public V066 projection; inspect saved values, never rescore them."""
from __future__ import annotations

import base64
from collections import Counter
import csv
from datetime import datetime
import gzip
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs/fbs"
LAYERS = ("original", "retained_v061", "calibrated", "mixture_global", "mixture_gated", "replay")


class PublicProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compressed = (PUBLIC / "latest-games-v066.json.gz").read_bytes()
        cls.raw = gzip.decompress(cls.compressed)
        cls.data = json.loads(cls.raw)
        cls.games = cls.data["games"]
        cls.csv = list(csv.DictReader((PUBLIC / "latest-games-v066.csv").read_text().splitlines()))

    def test_complete_denominator_and_partition(self):
        self.assertEqual(self.data["schema"], "fbs.public.v066.latest-authenticated-game-view.v1")
        self.assertEqual(len(self.games), 888)
        self.assertEqual(len({game["game_id"] for game in self.games}), 888)
        self.assertEqual(Counter(game["schedule_status"] for game in self.games), {
            "HISTORICAL_ISSUES_RETAINED_NO_BACKDATED_REISSUE": 688,
            "CURRENT_ORIGIN_REFRESH_DUE": 146,
            "EXACT_KICKOFF_NOT_PUBLISHED": 54})
        for game in self.games:
            self.assertEqual(game["season"], 2026)
            self.assertEqual(game["completed"], game["schedule_status"] == "HISTORICAL_ISSUES_RETAINED_NO_BACKDATED_REISSUE")
            self.assertEqual(game["kickoff_utc"] is None, game["schedule_status"] == "EXACT_KICKOFF_NOT_PUBLISHED")

    def test_original_future_and_completed_records_are_distinct(self):
        covered = [game for game in self.games if game["layers"]["original"]["values"]["p_home"] is not None]
        self.assertEqual(len(covered), 148)
        self.assertEqual(sum(game["completed"] for game in covered), 3)
        self.assertEqual(sum(game["schedule_status"] == "CURRENT_ORIGIN_REFRESH_DUE" for game in covered), 145)
        for game in covered:
            item = game["layers"]["original"]
            kickoff = datetime.fromisoformat(game["kickoff_utc"])
            self.assertLess(datetime.fromisoformat(item["original_durable_observed_at"]), kickoff)
            self.assertLess(datetime.fromisoformat(item["information_cutoff_utc"]), kickoff)
            self.assertFalse(item["production_champion"])
            self.assertFalse(item["new_issue_created_by_export"])

    def test_single_timed_gap_remains_missing_in_every_forecast_layer(self):
        gaps = [game for game in self.games if game["schedule_status"] == "CURRENT_ORIGIN_REFRESH_DUE"
                and game["layers"]["original"]["values"]["p_home"] is None]
        self.assertEqual([game["game_id"] for game in gaps], ["401858532"])
        game = gaps[0]
        self.assertIn("Rutgers", game["away"])
        self.assertIn("Penn State", game["home"])
        self.assertEqual(game["kickoff_utc"], "2026-11-21T20:30:00Z")
        for name in LAYERS:
            if name == "replay":
                continue
            for target in ("p_home", "home_margin", "total_points", "home_score", "away_score"):
                self.assertIsNone(game["layers"][name]["values"][target])
        csv_original = next(row for row in self.csv if row["game_id"] == game["game_id"] and row["layer"] == "original")
        self.assertTrue(all(csv_original[target] == "" for target in ("p_home", "home_margin", "total_points", "home_score", "away_score")))

    def test_all_current_refreshes_are_blocked_and_not_backfilled(self):
        attempted = [game for game in self.games if game["current_owner_baseline_refresh"]["attempted"]]
        self.assertEqual(len(attempted), 146)
        for game in attempted:
            refresh = game["current_owner_baseline_refresh"]
            self.assertEqual(refresh["reason_code"], "EXACT_REGISTERED_POOL_HAS_NO_EXISTING_STATE_NO_REFIT")
            self.assertEqual(refresh["status"], "CURRENT_ORIGIN_REFRESH_BLOCKED")
            self.assertEqual(refresh["new_issues"], 0)
            self.assertEqual(refresh["reused_current_context_issues"], 0)
            self.assertTrue(refresh["earlier_archive_is_not_a_current_refresh"])
        self.assertIsNone(self.data["summary"]["new_genuine_forecasts_root_scope"])
        self.assertEqual(self.data["summary"]["new_genuine_forecast_issues_in_reported_scientific_phases"], 0)

    def test_six_layers_and_exact_selected_archive_continuity(self):
        self.assertEqual({name: sum(game["layers"][name]["values"]["p_home"] is not None for game in self.games)
                          for name in LAYERS},
                         {"original": 148, "retained_v061": 148, "calibrated": 122,
                          "mixture_global": 114, "mixture_gated": 114, "replay": 790})
        self.assertEqual(sum(game["archive_continuity"]["earlier_v062_missing_original_restored"] for game in self.games), 26)
        self.assertEqual(sum(game["archive_continuity"]["earlier_v062_older_selection_recovered"] for game in self.games), 14)
        for game in self.games:
            self.assertEqual(set(game["layers"]), set(LAYERS))
            archive, original = game["layers"]["retained_v061"], game["layers"]["original"]
            if archive["values"]["p_home"] is not None:
                self.assertEqual(archive["values"], original["values"])
                self.assertEqual(archive["original_durable_observed_at"], original["original_durable_observed_at"])
            self.assertFalse(game["layers"]["replay"]["forecast_issued"])
            self.assertFalse(game["layers"]["replay"]["historical_availability_proved"])

    def test_no_champion_or_promotion_is_invented(self):
        status = self.data["champion_status"]
        self.assertEqual(status["authorized_metric_champions"], 0)
        self.assertEqual(status["requested_tasks"], 146)
        self.assertEqual(status["gap_count"], 584)
        self.assertEqual(len(status["roles"]), 9)
        for role in status["roles"]:
            self.assertIsNone(role["selected_model"])
            self.assertEqual(role["status"], "NO_AUTHORIZED_ROLLING_CHAMPION")
        for game in self.games:
            self.assertIsNone(game["metric_champion_forecast"])
        self.assertFalse(self.data["new_research"]["new_candidates_were_promoted"])
        self.assertFalse(self.data["native_latest_label_monitor"]["promotion_authorized"])

    def test_current_metrics_keep_old_computation_and_new_verification_clocks(self):
        point = self.data["current_retained_metric_evidence"]
        self.assertEqual(point["metric_report_owner_version"], "V062")
        self.assertEqual(point["original_report_source_capture_at"], "2026-11-11T07:24:15Z")
        self.assertEqual(point["current_verification_capture_at"], "2026-11-11T19:38:28Z")
        self.assertFalse(point["new_scores_or_predictions_computed"])
        self.assertFalse(point["older_point_leaders_full_current_season_replay_complete"])
        self.assertTrue(point["original_pregame_issue_ledger_is_separate"])
        self.assertEqual(len(point["leader_roles"]), 7)
        for role in point["leader_roles"]:
            self.assertEqual(role["games"], 688)
            self.assertFalse(role["selection_or_promotion_authorized"])
            self.assertEqual(role["candidate_family_count"], 10 if role["target"] == "winner" else 12)
        interval = point["total_mae_leader_vs_fixed_control_saved_uncertainty"]["percentile95"]
        self.assertLess(interval[0], 0)
        self.assertGreater(interval[1], 0)

    def test_saved_cohorts_retain_separate_support(self):
        monitor = self.data["native_latest_label_monitor"]
        self.assertEqual(monitor["games"], 301)
        self.assertEqual(monitor["completed_games_outside_saved_bank"], 387)
        self.assertEqual(monitor["preserved_arms_evaluated"], 250)
        self.assertEqual(monitor["distinct_preserved_probability_vectors"], 212)
        self.assertFalse(monitor["market_is_kalshi"])
        self.assertTrue(monitor["all_250_primary_metric_sets_unchanged_from_V062"])
        self.assertEqual(len(self.data["historical_cohort_leaders"]), 49)
        rows = self.data["new_research"]["new_vs_restored_metric_rows"]
        self.assertEqual(len(rows), 14)
        for row in rows:
            self.assertEqual(row["games"], {2024: 917, 2025: 933}[int(row["season"])])
            if row["metric"] == "accuracy":
                self.assertGreater(row["restored_selected_control"], row["best_new_value"])
            else:
                self.assertLess(row["restored_selected_control"], row["best_new_value"])

    def test_provider_reference_dictionary_preserves_targets_and_gaps(self):
        evidence = self.data["provider_evidence"]
        providers = {"DraftKings", "Kalshi", "Polymarket Global", "Polymarket US"}
        targets = {"winner", "margin", "total", "cover_probability"}
        for game in self.games:
            self.assertEqual(set(game["provider_reference_ids"]), providers)
            for provider, target_rows in game["provider_reference_ids"].items():
                self.assertEqual(set(target_rows), targets)
                for target, index in target_rows.items():
                    reference = evidence[index]
                    self.assertEqual((reference["provider"], reference["target"]), (provider, target))
                    self.assertFalse(reference["statistically_usable_baseline"])
                    self.assertIn("quote_at", reference)
                    self.assertIn("acquired_at", reference)
                    self.assertIn("age_status", reference)
        self.assertEqual(self.data["new_sports_metrics_calculated_by_export"], 0)

    def test_csv_is_complete_and_matches_saved_projection(self):
        self.assertEqual(len(self.csv), 5328)
        self.assertEqual(len({(row["game_id"], row["layer"]) for row in self.csv}), 5328)
        indexed = {game["game_id"]: game for game in self.games}
        for row in self.csv:
            values = indexed[row["game_id"]]["layers"][row["layer"]]["values"]
            for target in ("p_home", "home_margin", "total_points", "home_score", "away_score", "exact_line_cover"):
                self.assertEqual(None if row[target] == "" else float(row[target]), values[target])
            self.assertEqual(row["production_champion"], "False")
            self.assertEqual(row["new_issue_created_by_export"], "False")

    def test_embedded_bytes_and_source_clocks_are_exact(self):
        text = (PUBLIC / "latest-games-v066-data.js").read_text()
        match = re.fullmatch(r'window\.FBS_LATEST_V066_GZIP="([A-Za-z0-9+/=]+)";\n', text)
        self.assertIsNotNone(match)
        self.assertEqual(base64.b64decode(match[1], validate=True), self.compressed)
        self.assertEqual(self.data["source_capture_started_at"], "2026-11-11T19:38:28Z")
        self.assertEqual(self.data["source_capture_completed_at"], "2026-11-11T19:38:54Z")
        self.assertEqual(self.data["owner_release"], "V064")
        self.assertEqual(self.data["report_release"], "V066")
        self.assertEqual(self.data["source_owner_return_sha256"], "0d75211dc3323cbe68436e3ee8e507961eb52d7c313793e534e9988b2f32ff33")

    def test_latest_execution_is_failed_v065_without_new_scientific_credit(self):
        actual = self.data["latest_execution"]
        self.assertEqual(self.data["latest_actual_owner_release"], "V065")
        self.assertEqual(self.data["scientific_source_owner_release"], "V064")
        self.assertEqual(self.data["summary_counts_owner_release"], "V064")
        self.assertEqual(actual["status"], "V065_PARTIAL_DIAGNOSTIC_PRESERVED")
        self.assertEqual(actual["runtime_exit_code"], 2)
        self.assertEqual(actual["source_owner_return_sha256"], "9c2aa96c07d5f444ab601909b2c1d35c4b3d4abc753c6ef88b061c0036f6a29b")
        for key in ("new_model_fits", "new_prediction_outputs", "new_genuine_forecasts",
                    "provider_requests", "new_sports_metric_evaluations"):
            self.assertEqual(actual[key], 0)
        for key in ("source_acquisition_reached", "saved_metric_delivery_stage_reached", "forward_refresh_reached",
                    "champion_selection_reached", "last_valid_state_gap_was_retested"):
            self.assertFalse(actual[key])
        self.assertEqual(len(actual["errors"]), 2)
        self.assertEqual({error["message"] for error in actual["errors"]}, {"V7_SERIAL_OWNER_RESOURCE_DEFERRED"})

    def test_failed_fallback_is_dated_and_does_not_replace_latest_valid_view(self):
        fallback = self.data["failed_owner_report_fallback"]
        self.assertEqual(fallback["source_capture_started_at"], "2026-11-09T23:29:41Z")
        self.assertEqual((fallback["final_games"], fallback["timed_not_observed_complete_games"],
                          fallback["kickoff_unresolved_games"], fallback["selected_original_games"]), (685, 122, 81, 122))
        self.assertFalse(fallback["used_as_this_report_scientific_source"])
        self.assertFalse(fallback["complete_immutable_archive_deletion_proved"])
        self.assertTrue(self.data["latest_actual_owner_does_not_replace_last_valid_science"])
        self.assertEqual(self.data["summary"]["final_games"], 688)
        self.assertEqual(self.data["summary"]["original_issue_covered_games"], 148)

    def test_prepared_v066_is_not_invented_as_observed_aws_success(self):
        prepared = self.data["prepared_continuation"]
        self.assertEqual(prepared["owner_release"], "V066")
        self.assertFalse(prepared["actual_owner_execution_observed"])
        self.assertEqual(prepared["local_preparation_real_sports_computation"], 0)
        for key in ("new_actual_owner_fits", "new_actual_owner_predictions", "new_actual_owner_issues",
                    "new_actual_owner_source_capture", "new_promotions"):
            self.assertIsNone(prepared[key])
        html = (PUBLIC / "latest-games-v066.html").read_text()
        self.assertIn('id="execution"', html)
        self.assertIn('id="continuation-status"', html)
        self.assertIn("V066 is prepared, not an observed successful owner run", html)

    def test_saved_draftkings_comparison_is_cohort_specific_and_never_issued_or_promoted(self):
        comparison = self.data["saved_231_draftkings_comparison"]
        self.assertTrue(comparison["same_archived_game_cohort"])
        self.assertTrue(comparison["saved_metrics_copied_without_rescoring"])
        self.assertEqual(comparison["games"], 231)
        self.assertEqual(comparison["evidence_class"], "2026_MONITORING_RECONSTRUCTION_NOT_PREGAME_ISSUANCE")
        self.assertEqual(comparison["common_archived_game_cohort_sha256"], "babcd4fb3c791ce4cf9723c73243f981e772c00fe3ee02bf18dfcda5d0eefd82")
        for key in ("currently_qualified_horizon_source_clock_comparison", "original_pregame_issuance_proved_by_comparison",
                    "independent_promotion_evidence", "promotion_authorized", "kalshi_comparison"):
            self.assertFalse(comparison[key])
        expected = [("Saved probability-loss leader", 188, 81.3853, 0.416199, 0.133223),
                    ("Saved accuracy leader", 191, 82.6840, 0.422463, 0.135483),
                    ("DraftKings saved reference", 186, 80.5195, 0.434092, 0.140001)]
        for row, values in zip(comparison["rows"], expected, strict=True):
            self.assertEqual((row["role"], row["correct"], row["accuracy_percent"], row["log_loss"], row["brier"]), values)
            self.assertEqual(row["games"], 231)
        html = (PUBLIC / "latest-games-v066.html").read_text()
        self.assertIn('id="draftkings231-rows"', html)
        self.assertIn("not a currently qualified horizon/source-clock comparison", html)

    def test_public_boundary_and_static_fallback(self):
        for token in (b"s3://", b"/home/sagemaker-user", b"arn:aws:", b"recipe_policy_sha256",
                      b"model_snapshot_sha256", b"candidate_id", b"raw_response", b"api_key",
                      b"source_rows", b"fit_identity_sha256", b"model_pin"):
            self.assertNotIn(token, self.raw)
        self.assertFalse(self.data["summary"]["full_immutable_issue_archive_published"])
        html = (PUBLIC / "latest-games-v066.html").read_text()
        for name in ("latest-games-v066.js", "latest-games-v066-data.js", "latest-games-v066.css",
                     "latest-games-v066.csv", "latest-games-v066.json.gz", "V066_ACTUAL_OWNER_REVIEW_2026-11-11.md"):
            self.assertIn(name, html)
            self.assertTrue((PUBLIC / name).is_file(), name)
        self.assertIn("<noscript>", html)
        self.assertIn("all 888 games", html)
        self.assertIn("authorized zero rolling champions", html)
        self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="https?://')


if __name__ == "__main__":
    unittest.main(verbosity=2)
