"""Invented execution receipts; no real science or external calls."""
import contextlib
import io
import json
import math
import threading
import unittest

from examples.fbs_contracts.measured_progress import ProgressTracker, ProgressReportingError


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.events = []
        self.tracker = ProgressTracker("invented-v052", self.emit,
            monotonic=self.clock, utc_now=lambda: "2030-01-01T00:00:00Z")

    def emit(self, event, **values):
        self.events.append((event, values))

    def test_start_is_immediate_and_unknown_counts_are_not_zero(self):
        row = self.tracker.begin_phase("registry")
        self.assertEqual(len(self.events), 1)
        self.assertEqual(row["phase_elapsed_seconds"], 0)
        self.assertIsNone(row["counts"]["new_base_fits"])
        self.assertEqual(row["eta"]["reason"], "WORK_DENOMINATOR_NOT_OBSERVED")

    def test_elapsed_and_heartbeat_do_not_create_progress(self):
        self.tracker.begin_phase("registry", counts={"new_base_fits": 0})
        self.clock.advance(17)
        row = self.tracker.heartbeat()
        self.assertEqual(row["elapsed_total_seconds"], 17)
        self.assertEqual(row["phase_elapsed_seconds"], 17)
        self.assertEqual(row["counts"]["new_base_fits"], 0)
        self.assertIsNone(row["counts"]["candidates_evaluated"])
        self.assertIsNone(row["seconds_since_observed_work"])

    def test_eta_requires_measured_intervals_and_denominator(self):
        self.tracker.begin_phase("fits", 10, "fits")
        for units, seconds in ((1, 2), (2, 4)):
            self.clock.advance(seconds)
            row = self.tracker.update(completed_units=units)
            self.assertEqual(row["eta"]["status"], "UNKNOWN")
        self.clock.advance(3)
        row = self.tracker.update(completed_units=3, counts={"new_base_fits": 3})
        self.assertEqual(row["eta"]["minimum_seconds"], 14)
        self.assertEqual(row["eta"]["maximum_seconds"], 28)
        self.assertFalse(row["eta"]["completion_guaranteed"])
        self.assertIsNone(row["whole_invocation_eta_seconds"])

    def test_different_phases_never_share_pace_or_sum_reuse(self):
        self.tracker.begin_phase("fits", 3, "fits")
        for n in range(1, 4):
            self.clock.advance(2)
            self.tracker.update(completed_units=n, counts={"reused_fit_states": n})
        self.tracker.end_phase("COMPLETED")
        row = self.tracker.begin_phase("forecasts", 30, "forecasts", counts={"reused_fit_states": 3})
        self.assertEqual(row["eta"]["status"], "UNKNOWN")
        self.assertEqual(row["phase_elapsed_seconds"], 0)
        self.assertEqual(row["elapsed_total_seconds"], 6)
        self.assertEqual(row["counts"]["reused_fit_states"], 3)
        self.assertNotIn("total_reused_fit_states", self.tracker.receipt())

    def test_stall_invalidates_pace_estimate(self):
        self.tracker.begin_phase("fits", 10)
        for n in range(1, 4):
            self.clock.advance(1)
            self.tracker.update(completed_units=n)
        self.clock.advance(31)
        row = self.tracker.heartbeat()
        self.assertEqual(row["eta"]["reason"], "NO_RECENT_COMPLETION_PACE_MAY_HAVE_CHANGED")
        self.assertIsNone(row["eta"]["maximum_seconds"])

    def test_denominator_revision_resets_measured_range(self):
        self.tracker.begin_phase("fixtures", 10)
        for n in range(1, 4):
            self.clock.advance(1)
            self.tracker.update(completed_units=n)
        row = self.tracker.update(total_units=12)
        self.assertEqual(row["eta"]["status"], "UNKNOWN")
        self.assertEqual(row["eta"]["measured_completion_intervals"], 0)
        self.assertEqual(row["work_units"]["denominator_revisions"], 1)

    def test_counter_decrease_and_unknown_reset_are_rejected(self):
        self.tracker.begin_phase("fits", counts={"new_base_fits": 2})
        for count in (1, None, -1, True, 1.0):
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.tracker.update(counts={"new_base_fits": count})
        self.assertEqual(self.tracker.receipt()["active_phase"]["counts"]["new_base_fits"], 2)

    def test_success_requires_declared_work_finished(self):
        self.tracker.begin_phase("fits", 2)
        self.tracker.update(completed_units=1)
        with self.assertRaises(ValueError):
            self.tracker.end_phase("COMPLETED")
        row = self.tracker.end_phase("PARTIAL", evidence={"reason": "budget reached"})
        self.assertEqual(row["work_units"]["completed"], 1)
        self.assertEqual(row["phase_status"], "PARTIAL")

    def test_failure_preserves_counts_and_exact_error_evidence(self):
        self.tracker.begin_phase("fits", 4, counts={"new_base_fits": 0, "reused_fit_states": 2})
        self.clock.advance(4)
        self.tracker.update(completed_units=1, counts={"new_base_fits": 1})
        row = self.tracker.end_phase("FAILED", evidence={"type": "ValueError", "message": "invented refusal"})
        self.assertEqual(row["counts"]["new_base_fits"], 1)
        self.assertEqual(row["counts"]["reused_fit_states"], 2)
        self.assertEqual(row["evidence"]["message"], "invented refusal")
        self.assertIsNone(row["eta"]["minimum_seconds"])
        self.assertEqual(self.tracker.finish("PARTIAL_DIAGNOSTIC")["phases"][0]["phase_status"], "FAILED")

    def test_finish_does_not_infer_success_for_open_phase(self):
        self.tracker.begin_phase("interrupted")
        receipt = self.tracker.finish("DIAGNOSTIC")
        self.assertEqual(receipt["phases"][0]["phase_status"], "STOPPED_WITHOUT_PHASE_COMPLETION")
        self.assertEqual(receipt["scientific_units_created_by_observation"], 0)

    def test_nonfinite_evidence_is_refused_before_mutation(self):
        self.tracker.begin_phase("fits")
        with self.assertRaises(ValueError):
            self.tracker.update(counts={"new_base_fits": 1}, evidence={"bad": math.nan})
        self.assertIsNone(self.tracker.receipt()["active_phase"]["counts"]["new_base_fits"])
        json.dumps(self.tracker.receipt(), allow_nan=False)

    def test_clock_regression_is_not_hidden(self):
        self.tracker.begin_phase("fits")
        self.clock.value = -1
        with self.assertRaises(ValueError):
            self.tracker.heartbeat()

    def test_zero_elapsed_updates_do_not_invent_rate(self):
        self.tracker.begin_phase("cached", 5)
        row = self.tracker.update(completed_units=3)
        self.assertEqual(row["eta"]["measured_completion_intervals"], 0)
        self.assertEqual(row["eta"]["status"], "UNKNOWN")

    def test_caller_mutation_cannot_rewrite_evidence(self):
        original = {"receipt": {"reused": 3}}
        self.tracker.begin_phase("reuse", evidence=original)
        original["receipt"]["reused"] = 999
        self.assertEqual(self.tracker.receipt()["active_phase"]["evidence"]["receipt"]["reused"], 3)

    def test_failed_output_is_visible_and_receipt_survives(self):
        def broken(event, **values):
            raise OSError("invented full output volume")
        tracker = ProgressTracker("invented-failure", broken)
        capture = io.StringIO()
        with contextlib.redirect_stderr(capture), self.assertRaises(ProgressReportingError):
            tracker.begin_phase("registry")
        self.assertIn("V052_PROGRESS_REPORTING_FAILED", capture.getvalue())
        receipt = tracker.receipt()
        self.assertEqual(receipt["reporting_failure_count"], 1)
        self.assertEqual(receipt["active_phase"]["phase_name"], "registry")
        with self.assertRaises(ProgressReportingError):
            tracker.check()

    def test_background_failure_is_reported_to_owner(self):
        attempted = threading.Event()
        def broken_heartbeat(event, **values):
            if event == "V052_PROGRESS_HEARTBEAT":
                attempted.set()
                raise OSError("invented heartbeat failure")
        tracker = ProgressTracker("invented-thread", broken_heartbeat)
        tracker.begin_phase("running")
        capture = io.StringIO()
        with contextlib.redirect_stderr(capture):
            tracker.start_heartbeat(0.01)
            self.assertTrue(attempted.wait(1.0))
            tracker._thread.join(timeout=1.0)
            with self.assertRaises(ProgressReportingError):
                tracker.stop_heartbeat()
        self.assertIn("invented heartbeat failure", capture.getvalue())
        self.assertEqual(tracker.receipt()["heartbeat_thread_failure"]["type"], "OSError")

    def test_heartbeat_cannot_silently_exceed_thirty_seconds(self):
        for interval in (0, -1, 31, math.nan, math.inf, True):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                self.tracker.start_heartbeat(interval)

    def test_resume_baseline_does_not_count_as_new_work(self):
        row = self.tracker.begin_phase("verified resume", 100, completed_units=80,
            counts={"reused_fit_states": 80, "new_base_fits": 0})
        self.assertEqual(row["eta"]["status"], "UNKNOWN")
        self.assertEqual(row["eta"]["measured_completion_intervals"], 0)
        self.assertIsNone(row["seconds_since_observed_work"])


if __name__ == "__main__":
    unittest.main()
