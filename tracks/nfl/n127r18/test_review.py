"""Public NFL report contracts using invented inputs; no fitting or provider access."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("nfl_r18_public_renderer", HERE / "build_review.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


def fixture():
    status = {
        "schema_version": 1, "owner": "NFL", "revision": "N127R18", "evidence_as_of_utc": "2000-01-01T00:00:00Z",
        "owner_run": {"status": "PARTIAL_RESUMABLE", "return_sha256": "a" * 64,
                      "return_bytes": 101, "return_parts": 1, "return_integrity": "VERIFIED", "pointer_readback": True,
                      "new_estimator_fits": 0, "reused_fold_groups": 8, "requested_workers": 36,
                      "sustained_occupancy_claimed": False, "production_promotions": 0,
                      "elapsed_seconds_before_seal": 60, "compute_estimate_before_seal_usd": .1},
        "stage_counts": {"COMPLETED": 1, "REUSED": 1, "PARTIAL": 1, "DEFERRED": 1},
        "stages": [{"name": "example_stage", "status": "COMPLETED", "elapsed_seconds": 1.5}],
        "science": {"full_games_by_season": {"2024": 10, "2025": 11, "2026": 4},
                    "objective_clock_groups": 1, "prior_test_exposure": True, "weights_used_in_training": False,
                    "validation_ratios": [[50, 50], [10, 90]], "primary_ratio": [50, 50]},
        "source_admissions": [{"source": "invented", "status": "BLOCKED", "reasons": ["Clock unverified"],
                               "coverage": [{"season": 2024, "horizon_minutes": 60, "retained_source_rows": 3,
                                             "admissible_team_rows": 0, "both_team_admissible_games": 0}]}],
        "preparation": {"tests_passed": 2, "tests_failed": 0, "tests_errors": 0, "tests_skipped": 0},
        "parquet_benchmarks": [{"dataset": "Invented table", "rows": 10, "columns": 2, "csv_ms": 1,
                                "parquet_ms": 2, "csv_rss_mib": 3, "parquet_rss_mib": 4}],
        "remaining_work": ["Complete the invented evidence"],
        "publication": {"kind": "GitHub source update", "hosted_deployment": False},
        "evidence": [{"id": "invented_reference", "sha256": "b" * 64}],
    }
    row = {"role_alias": "Role 1", "model_family": "Invented family", "objective": "winner_log_loss",
           "clock_group": "T60", "information_clock": "T−60", "weight_2024": 50, "weight_2025": 50,
           "primary": True, "season_2024": .321123456, "season_2025": .654234567, "test_2026": None,
           "games_2024": 10, "games_2025": 11, "games_2026": None, "ids_2024": "c" * 64,
           "ids_2025": "d" * 64, "ids_2026": None, "validation_score": .487679,
           "rank": 1, "eligible_policy_rows": 2, "validation_coleader_count": 1,
           "test_status": "INCOMPLETE_COVERAGE", "evidence": "Reconstruction"}
    metrics = {"schema_version": 1, "status": "VALIDATION_NOMINATIONS_PARTIAL_ACCEPTANCE", "prior_test_exposure": True, "rows": [row]}
    return status, metrics


class PublicReviewTests(unittest.TestCase):
    def test_deterministic_and_no_input_mutation(self):
        status, metrics = fixture()
        before = copy.deepcopy((status, metrics))
        self.assertEqual(renderer.render(status, metrics), renderer.render(status, metrics))
        self.assertEqual((status, metrics), before)

    def test_saved_values_and_denominators_remain_visible(self):
        status, metrics = fixture()
        page = renderer.render(status, metrics)
        for text in ("0.321123", "0.654235", "n = 10", "n = 11", "0.487679", "c" * 64, "d" * 64):
            self.assertIn(text, page)

    def test_null_test_is_gap_not_a_zero_score(self):
        status, metrics = fixture()
        page = renderer.render(status, metrics)
        self.assertIn('<span class="gap">Gap</span><small>n = not available</small>', page)
        self.assertIn("INCOMPLETE_COVERAGE", page)

    def test_true_zero_is_preserved_as_zero(self):
        self.assertIn('>0<small>n = 4</small>', renderer.metric_cell(0, 4))

    def test_hostile_text_is_escaped(self):
        status, metrics = fixture()
        attack = '<img src=x onerror="alert(1)"></script><script>alert(2)</script>'
        metrics["rows"][0]["role_alias"] = attack
        status["remaining_work"] = [attack]
        page = renderer.render(status, metrics)
        self.assertNotIn(attack, page)
        self.assertIn("&lt;img", page)
        self.assertEqual(page.count("<script>"), 1)

    def test_private_field_is_rejected_even_if_not_rendered(self):
        status, metrics = fixture()
        metrics["rows"][0]["feature_columns"] = ["invented_hidden_column"]
        with self.assertRaisesRegex(ValueError, "Private field"):
            renderer.render(status, metrics)

    def test_private_address_is_rejected(self):
        status, metrics = fixture()
        status["remaining_work"] = ["s3:" + "//invented-private/object"]
        with self.assertRaisesRegex(ValueError, "Private infrastructure"):
            renderer.render(status, metrics)

    def test_non_finite_metrics_rejected(self):
        status, metrics = fixture()
        metrics["rows"][0]["season_2024"] = math.nan
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            renderer.render(status, metrics)

    def test_exposure_and_training_weight_boundaries(self):
        for target, key, value in (("science", "prior_test_exposure", False), ("science", "weights_used_in_training", True)):
            status, metrics = fixture()
            status[target][key] = value
            with self.assertRaises(ValueError):
                renderer.render(status, metrics)

    def test_no_hosting_claim_without_reviewed_receipt(self):
        status, metrics = fixture()
        status["publication"]["hosted_deployment"] = True
        with self.assertRaisesRegex(ValueError, "hosted deployment"):
            renderer.render(status, metrics)

    def test_preparation_cannot_stand_in_for_verified_owner_return(self):
        status, metrics = fixture()
        status["owner_run"]["return_integrity"] = "PENDING"
        with self.assertRaisesRegex(ValueError, "verified partial"):
            renderer.render(status, metrics)

    def test_ratio_does_not_choose_by_test_outcome(self):
        status, metrics = fixture()
        second = copy.deepcopy(metrics["rows"][0])
        second.update(role_alias="Role 2", weight_2024=10, weight_2025=90, primary=False, test_2026=.0001, games_2026=4)
        metrics["rows"].append(second)
        page = renderer.render(status, metrics)
        self.assertIn('<option value="50/50" selected>', page)
        self.assertIn('<option value="T60" selected>', page)
        self.assertEqual(page.count('data-weight="50/50"'), 1)
        self.assertEqual(page.count('data-weight="10/90"'), 1)
        self.assertIn("Role 1", page)
        self.assertIn("Role 2", page)

    def test_prose_clock_uses_retained_information_clock(self):
        status, metrics = fixture()
        row = metrics["rows"][0]
        row["clock_group"] = "All models available one hour before kickoff"
        row["information_clock"] = "T-60 minutes"
        page = renderer.render(status, metrics)
        self.assertIn('<option value="All models available one hour before kickoff" selected>', page)

    def test_retained_objects_do_not_become_eligible_source_rows(self):
        status, metrics = fixture()
        coverage = status["source_admissions"][0]["coverage"][0]
        coverage.update(full_games=10, full_team_rows=20, retained_source_objects_for_year=6)
        page = renderer.render(status, metrics)
        self.assertIn("Retained objects for year", page)
        self.assertIn("Retained source rows", page)
        self.assertIn("<td>2024</td><td>T−60</td><td>10</td><td>20</td><td>3</td><td>6</td><td>0</td><td>0</td>", page)

    def test_source_reason_codes_are_readable_without_changing_evidence(self):
        status, metrics = fixture()
        code = "NO_REGISTERED_AUTHENTICATED_FEATURE_MATRIX"
        status["source_admissions"][0]["reasons"] = [code]
        page = renderer.render(status, metrics)
        self.assertIn("<li>No registered authenticated feature matrix</li>", page)
        self.assertEqual(status["source_admissions"][0]["reasons"], [code])

    def test_failure_counts_do_not_conflate_builds_or_attribute_io_origin(self):
        status, metrics = fixture()
        status["failure_accounting"] = {"scope": "Invented scoped ledger", "attributable_builds": 5,
                                        "identified_owner_recovery_or_completion_failures": 1}
        status["prior_r17_incident"] = {"status": "FAILED_RECOVERY_REQUIRED", "cause": "I/O resource-admission refusal",
                                        "wait_seconds_each": 120, "current_io_full_percent": 90,
                                        "ten_second_io_full_percent": 80, "exclusive_origin_established": False,
                                        "forecast_corruption_established": False, "overlapping_fit_pids": 12,
                                        "peak_fit_core_equivalents": 10}
        page = renderer.render(status, metrics)
        self.assertIn("<td>Attributable builds</td><td>5</td>", page)
        self.assertIn("<td>Identified owner recovery or completion failures</td><td>1</td>", page)
        self.assertIn("Exclusive pressure origin established: <strong>No</strong>", page)
        self.assertIn("Forecast corruption established: <strong>No</strong>", page)

    def test_real_public_inputs_and_committed_page_agree(self):
        if not (HERE / "status.json").is_file() or not (HERE / "selected_metrics.json").is_file():
            self.skipTest("Public evidence has not been prepared")
        expected = renderer.build()
        self.assertEqual((HERE / "index.html").read_text(encoding="utf-8"), expected)
        self.assertIn("Research remains partial", expected)
        self.assertIn("hosted website deployment is a separate event", expected)


if __name__ == "__main__":
    unittest.main()
