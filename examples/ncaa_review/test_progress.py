"""Meaningful progress failures using invented counters, clocks and workers."""
from dataclasses import replace
import json
import unittest

from progress import Observation, demo_scenarios, estimate


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.points = [Observation("fit batch", 0, 0, workers=2),
                       Observation("fit batch", 10, 2, workers=2),
                       Observation("fit batch", 20, 4, workers=2)]

    def run_estimate(self, points=None, **kwargs):
        args = dict(total=10, observed_at=20)
        args.update(kwargs)
        return estimate(self.points if points is None else points, **args)

    def test_counts_and_empirical_rate(self):
        x = self.run_estimate()
        self.assertEqual((x.completed, x.remaining, x.fraction), (4, 6, .4))
        self.assertEqual((x.eta_seconds, x.observed_pace_low_seconds, x.observed_pace_high_seconds), (30, 30, 30))
        self.assertEqual(x.estimate_scope, "CURRENT_PHASE_ONLY")
        self.assertIn("not a confidence interval", x.estimate_qualification)

    def test_restored_units_reduce_remaining_without_inflating_throughput(self):
        points = [replace(p, reused=100) for p in self.points]
        x = self.run_estimate(points, total=110)
        self.assertEqual((x.completed, x.newly_committed, x.reused), (104, 4, 100))
        self.assertEqual(x.eta_seconds, 30)

    def test_later_reuse_jump_is_not_a_speed_sample(self):
        points = [self.points[0], replace(self.points[1], reused=2), replace(self.points[2], reused=3)]
        x = self.run_estimate(points, total=10)
        self.assertEqual((x.completed, x.eta_seconds), (7, 15))

    def test_late_reuse_cannot_revive_a_stale_new_work_rate(self):
        points = self.points + [replace(self.points[-1], seconds=100, reused=3)]
        x = self.run_estimate(points, observed_at=100)
        self.assertEqual(x.completed, 7)
        self.assertEqual(x.eta_status, "STALE_PACE")
        self.assertIsNone(x.eta_seconds)

    def test_unknown_total_does_not_invent_percentage_or_eta(self):
        x = self.run_estimate(total=None)
        self.assertEqual(x.completed, 4)
        self.assertIsNone(x.fraction)
        self.assertIsNone(x.remaining)
        self.assertIsNone(x.eta_seconds)
        self.assertEqual(x.eta_status, "UNKNOWN_TOTAL")

    def test_only_restored_units_cannot_supply_processing_rate(self):
        points = [Observation("restore", 0, 0, 0), Observation("restore", 10, 0, 9)]
        x = self.run_estimate(points)
        self.assertEqual(x.completed, 9)
        self.assertEqual(x.sample_intervals, 0)
        self.assertIsNone(x.eta_seconds)

    def test_one_positive_interval_stays_in_warmup(self):
        self.assertEqual(self.run_estimate(self.points[:2]).eta_status, "WARMUP")

    def test_idle_samples_do_not_erase_idle_time(self):
        points = [self.points[0], Observation("fit batch", 10, 0, workers=2),
                  Observation("fit batch", 20, 1, workers=2),
                  Observation("fit batch", 30, 2, workers=2)]
        x = self.run_estimate(points, total=4, observed_at=30)
        self.assertEqual(x.eta_seconds, 30)
        self.assertEqual((x.observed_pace_low_seconds, x.observed_pace_high_seconds), (20, 40))

    def test_stalled_phase_retires_old_estimate(self):
        x = self.run_estimate(observed_at=80)
        self.assertEqual(x.completed, 4)
        self.assertEqual(x.eta_status, "STALE_PACE")
        self.assertIsNone(x.eta_seconds)

    def test_worker_change_requires_new_measurements(self):
        points = self.points + [Observation("fit batch", 25, 5, workers=1)]
        x = self.run_estimate(points, observed_at=25)
        self.assertEqual(x.eta_status, "WORKER_CHANGE_WARMUP")
        self.assertIsNone(x.eta_seconds)

    def test_new_worker_segment_does_not_multiply_by_worker_count(self):
        points = self.points + [Observation("fit batch", 25, 5, workers=1),
                               Observation("fit batch", 35, 6, workers=1),
                               Observation("fit batch", 45, 7, workers=1)]
        x = self.run_estimate(points, observed_at=45)
        self.assertEqual(x.sample_intervals, 2)
        self.assertEqual(x.eta_seconds, 30)

    def test_failure_keeps_unfinished_count_without_zero_eta(self):
        x = self.run_estimate(status="failed")
        self.assertEqual((x.completed, x.remaining), (4, 6))
        self.assertEqual(x.eta_status, "STOPPED_WITH_UNFINISHED_WORK")
        self.assertIsNone(x.eta_seconds)

    def test_failed_attempts_are_not_completed_units(self):
        x = self.run_estimate([replace(p, failed_attempts=3) for p in self.points])
        self.assertEqual((x.completed, x.failed_attempts), (4, 3))

    def test_all_units_do_not_imply_phase_finalization(self):
        x = self.run_estimate(total=4)
        self.assertEqual(x.fraction, 1)
        self.assertEqual(x.eta_status, "AWAITING_PHASE_FINALIZATION")
        self.assertIsNone(x.eta_seconds)

    def test_complete_phase_requires_satisfied_known_denominator(self):
        for total in (None, 10):
            with self.assertRaises(ValueError):
                self.run_estimate(total=total, status="completed")
        x = self.run_estimate(total=4, status="completed")
        self.assertEqual((x.eta_status, x.eta_seconds), ("COMPLETED", 0))

    def test_empty_completed_plan_is_explicit(self):
        x = estimate([Observation("empty plan", 0, 0)], total=0, observed_at=0, status="completed")
        self.assertEqual((x.completed, x.total, x.fraction), (0, 0, 1))

    def test_wall_and_phase_clocks_remain_separate(self):
        x = self.run_estimate(wall_elapsed_seconds=900)
        self.assertEqual((x.phase_elapsed_seconds, x.wall_elapsed_seconds, x.eta_seconds), (20, 900, 30))
        with self.assertRaises(ValueError):
            self.run_estimate(wall_elapsed_seconds=19)

    def test_mixed_phases_backward_clocks_and_counters_are_rejected(self):
        mutations = [replace(self.points[-1], phase="another phase"),
                     replace(self.points[-1], seconds=9),
                     replace(self.points[-1], seconds=10),
                     replace(self.points[-1], newly_committed=1)]
        for point in mutations:
            with self.subTest(point=point), self.assertRaises(ValueError):
                self.run_estimate(self.points[:2] + [point])

    def test_invalid_measurements_are_rejected(self):
        for value in (True, -1, 1.5):
            with self.subTest(total=value), self.assertRaises(ValueError):
                self.run_estimate(total=value)
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(clock=value), self.assertRaises(ValueError):
                self.run_estimate(observed_at=value)
        with self.assertRaises(ValueError):
            self.run_estimate(total=3)
        with self.assertRaises(ValueError):
            self.run_estimate(observed_at=19)
        with self.assertRaises(ValueError):
            self.run_estimate(stale_after_seconds=0)

    def test_demo_is_valid_json_and_has_no_production_side_effects(self):
        scenarios = demo_scenarios()
        self.assertEqual(len(scenarios), 8)
        self.assertEqual(len({s['id'] for s in scenarios}), 8)
        payload = json.dumps(scenarios, allow_nan=False)
        self.assertIn("UNKNOWN_TOTAL", payload)
        self.assertIn("STOPPED_WITH_UNFINISHED_WORK", payload)
        self.assertNotIn("s3://", payload)


if __name__ == "__main__":
    unittest.main()
