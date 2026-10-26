"""Behavioral tests for chronology, exact cohorts and artifact recovery."""
from copy import deepcopy
from datetime import timedelta
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.review_lab.core import (fit_synthetic, predict_synthetic, run_synthetic,
    score_matched, synthetic_events, timestamp, validate_rows, verify_manifest, write_run)


class ChronologyTests(unittest.TestCase):
    def setUp(self):
        self.rows = synthetic_events(40)

    def test_valid_timestamps_and_unique_identity(self):
        self.assertEqual(len(validate_rows(self.rows)), 40)

    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_rows(self.rows + [self.rows[0]])

    def test_future_observation_rejected(self):
        self.rows[0]["features_observed_at"] = self.rows[0]["event_at"]
        with self.assertRaisesRegex(ValueError, "information-time"):
            validate_rows(self.rows)

    def test_same_time_observation_rejected(self):
        self.rows[0]["features_observed_at"] = self.rows[0]["decision_at"]
        with self.assertRaisesRegex(ValueError, "information-time"):
            validate_rows(self.rows)

    def test_publication_after_observation_rejected(self):
        self.rows[0]["features_published_at"] = self.rows[0]["decision_at"]
        with self.assertRaisesRegex(ValueError, "information-time"):
            validate_rows(self.rows)

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            timestamp("2026-10-25T12:00:00")

    def test_unreleased_training_label_rejected(self):
        with self.assertRaisesRegex(ValueError, "training label"):
            fit_synthetic(self.rows, self.rows[-1]["label_available_at"], interactions=True)

    def test_unavailable_model_rejected(self):
        fit_time = (timestamp(self.rows[30]["decision_at"]) - timedelta(seconds=1)).isoformat()
        model = fit_synthetic(self.rows[:30], fit_time, interactions=True)
        with self.assertRaisesRegex(ValueError, "model unavailable"):
            predict_synthetic(model, self.rows[:1])

    def test_nonfinite_input_rejected(self):
        self.rows[0]["context_a"] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_rows(self.rows)


class MetricTests(unittest.TestCase):
    def test_known_binary_scores(self):
        result = score_matched({"a": 1, "b": 0}, {"a": 0.8, "b": 0.2})
        self.assertAlmostEqual(result["log_loss"], -math.log(0.8))
        self.assertAlmostEqual(result["brier"], 0.04)
        self.assertEqual(result["accuracy"], 1)

    def test_alignment_by_identity_not_order(self):
        a = score_matched({"a": 1, "b": 0}, {"b": 0.1, "a": 0.9})
        b = score_matched({"b": 0, "a": 1}, {"a": 0.9, "b": 0.1})
        self.assertEqual(a, b)

    def test_equal_count_different_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError, "cohorts"):
            score_matched({"a": 1}, {"b": 0.8})

    def test_invalid_probabilities_rejected(self):
        for p in (-0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(p=p), self.assertRaisesRegex(ValueError, "probability"):
                score_matched({"a": 1}, {"a": p})

    def test_boundary_probabilities_stay_finite(self):
        result = score_matched({"a": 1, "b": 0}, {"a": 0.0, "b": 1.0})
        self.assertTrue(math.isfinite(result["log_loss"]))
        self.assertEqual(result["brier"], 1)


class ExecutionTests(unittest.TestCase):
    def test_deterministic_training_and_evaluation(self):
        self.assertEqual(run_synthetic(), run_synthetic())

    def test_models_share_the_same_evaluation_cohort(self):
        report = run_synthetic()
        self.assertEqual({r["games"] for r in report["scores"].values()}, {80})
        self.assertEqual(len({r["cohort_sha256"] for r in report["scores"].values()}), 1)
        self.assertFalse(report["real_football_performance"])

    def test_reentry_has_zero_fits(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            created = write_run(directory)
            with patch("examples.review_lab.core.run_synthetic", side_effect=AssertionError("must not refit")):
                reused = write_run(directory)
            self.assertEqual(created["new_fits"], 2)
            self.assertEqual(reused["new_fits"], 0)
            self.assertEqual(created["report_sha256"], reused["report_sha256"])

    def test_changed_seed_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            write_run(directory)
            before = (directory / "report.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite"):
                write_run(directory, seed=7)
            self.assertEqual(before, (directory / "report.json").read_bytes())

    def test_corrupted_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            write_run(directory)
            (directory / "report.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "integrity"):
                write_run(directory)

    def test_manifest_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            write_run(directory)
            path = directory / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["files"][0]["path"] = "../outside.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "inventory"):
                verify_manifest(directory)


if __name__ == "__main__":
    unittest.main()
