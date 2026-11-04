"""Invented resource/process fixtures; no host inspection or production locks."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import admission as a


ROOT = "invented-p4101:start-a"
CHILD = "invented-p4102:start-b"
GRANDCHILD = "invented-p4103:start-c"
DEMAND = a.Demand(1, 1_500, 5, 0.5, 1_000)


def capacity(*, busy_cores=2, memory=8_000):
    return a.measure(
        a.AggregateSample("invented-scope", 10, 6, 90, memory),
        a.AggregateSample("invented-scope", 12, 6, 90 + 2 * busy_cores, memory))


class Clock:
    def __init__(self):
        self.value = 0.0
        self.pauses = []

    def __call__(self):
        return self.value

    def pause(self, duration):
        self.pauses.append(duration)
        self.value += duration


class Lock:
    key = "invented-canonical-project-lock"

    def __init__(self, busy_attempts=0):
        self.busy_attempts = busy_attempts
        self.calls = 0
        self.held = None
        self.released = []

    def try_acquire(self):
        self.calls += 1
        if self.calls <= self.busy_attempts:
            return None
        if self.held is not None:
            raise AssertionError("duplicate owner")
        self.held = object()
        return self.held

    def release(self, token):
        if token is not self.held:
            raise AssertionError("cannot release another owner's lock")
        self.released.append(token)
        self.held = None


def wait(probe, lock, clock, **options):
    return a.admission(probe, lock, DEMAND, clock=clock, pause=clock.pause,
                       wait_seconds=options.get("wait_seconds", 3),
                       poll_seconds=options.get("poll_seconds", 1))


class AggregateAccountingTests(unittest.TestCase):
    def test_idle_parent_busy_child_and_grandchild_count_once(self):
        before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000, (
            a.ProcessCounter(ROOT, None, 5, 500),
            a.ProcessCounter(CHILD, ROOT, 2, 700),
            a.ProcessCounter(GRANDCHILD, CHILD, 1, 800)))
        after = replace(before, at_seconds=12, busy_cpu_seconds=94, processes=(
            a.ProcessCounter(ROOT, None, 5, 500),
            a.ProcessCounter(CHILD, ROOT, 4, 700),
            a.ProcessCounter(GRANDCHILD, CHILD, 3, 800)))
        measured = a.measure(before, after, (ROOT, CHILD))
        self.assertEqual(measured.observed_tree_cpu_cores, 2)
        self.assertEqual(measured.available_cpu_cores, 4)
        self.assertEqual(measured.process_accounting_status, "complete")
        # Subtracting the already-counted descendants a second time would allow 1.
        self.assertEqual(a.select_workers(measured, DEMAND), (3, ()))

    def test_exited_child_still_consumes_aggregate_capacity(self):
        before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000, (
            a.ProcessCounter(ROOT, None, 5, 500), a.ProcessCounter(CHILD, ROOT, 1, 700)))
        after = replace(before, at_seconds=12, busy_cpu_seconds=101,
                        processes=(a.ProcessCounter(ROOT, None, 5, 500),))
        measured = a.measure(before, after, (ROOT,))
        self.assertEqual(measured.incomplete_process_keys, (CHILD,))
        self.assertEqual(measured.process_accounting_status, "partial")
        self.assertEqual(measured.available_cpu_cores, 0.5)
        self.assertEqual(a.select_workers(measured, DEMAND), (0, ("cpu_headroom",)))

    def test_reused_pid_does_not_become_a_negative_or_huge_delta(self):
        replacement = "invented-p4102:start-new"
        before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000, (
            a.ProcessCounter(ROOT, None, 5, 500), a.ProcessCounter(CHILD, ROOT, 200, 700)))
        after = replace(before, at_seconds=12, busy_cpu_seconds=94, processes=(
            a.ProcessCounter(ROOT, None, 5, 500),
            a.ProcessCounter(replacement, ROOT, 1, 700)))
        measured = a.measure(before, after, (ROOT,))
        self.assertEqual(set(measured.incomplete_process_keys), {CHILD, replacement})
        self.assertEqual(measured.observed_tree_cpu_cores, 0)
        self.assertEqual(measured.available_cpu_cores, 4)

    def test_rss_diagnostic_is_not_subtracted_from_available_memory(self):
        before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000,
                                   (a.ProcessCounter(ROOT, None, 5, 99_000),))
        after = replace(before, at_seconds=12, busy_cpu_seconds=94)
        measured = a.measure(before, after, (ROOT,))
        self.assertEqual(measured.tree_rss_sum_bytes, 99_000)
        self.assertEqual(measured.memory_available_bytes, 8_000)
        self.assertEqual(a.select_workers(measured, DEMAND)[0], 3)

    def test_unavailable_optional_process_detail_does_not_veto_valid_aggregate(self):
        for rows in ((a.ProcessCounter(ROOT, None, 1, 1), a.ProcessCounter(ROOT, None, 1, 1)),
                     (a.ProcessCounter(ROOT, CHILD, 1, 1), a.ProcessCounter(CHILD, ROOT, 1, 1))):
            before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000, rows)
            after = replace(before, at_seconds=12, busy_cpu_seconds=94)
            measured = a.measure(before, after, (ROOT,))
            self.assertEqual(measured.process_accounting_status, "unavailable")
            self.assertIsNone(measured.observed_tree_cpu_cores)
            self.assertEqual(a.select_workers(measured, DEMAND)[0], 3)

    def test_many_idle_foreign_processes_are_not_an_admission_veto(self):
        rows = tuple(a.ProcessCounter(f"invented-p{5000 + i}:start-a", None, 1, 10)
                     for i in range(100))
        before = a.AggregateSample("invented-scope", 10, 6, 90, 8_000, rows)
        after = replace(before, at_seconds=12, busy_cpu_seconds=92)
        measured = a.measure(before, after)
        self.assertEqual(a.select_workers(measured, DEMAND)[0], 4)

    def test_cpu_memory_reserves_and_worker_limit_all_apply(self):
        self.assertEqual(a.select_workers(capacity(memory=4_000), DEMAND), (2, ()))
        self.assertEqual(a.select_workers(capacity(), replace(DEMAND, max_workers=1)), (1, ()))
        self.assertEqual(a.select_workers(capacity(busy_cores=6, memory=1_000), DEMAND),
                         (0, ("cpu_headroom", "memory_headroom")))

    def test_fractional_cpu_capacity_floors_worker_count(self):
        before = a.AggregateSample("invented-quota", 10, 2.5, 5, 8_000)
        after = replace(before, at_seconds=12, busy_cpu_seconds=6.5)
        demand = a.Demand(0.5, 1_000, 10, 0.5, 0)
        self.assertEqual(a.select_workers(a.measure(before, after), demand), (2, ()))

    def test_missing_nonfinite_and_boolean_measurements_are_not_zero_usage(self):
        good = a.AggregateSample("invented-scope", 10, 6, 90, 8_000)
        for field, value in (("memory_available_bytes", None), ("memory_available_bytes", True),
                             ("cpu_capacity_cores", float("nan")), ("busy_cpu_seconds", float("inf")),
                             ("at_seconds", True)):
            with self.subTest(field=field, value=value), self.assertRaises(a.MeasurementUnavailable):
                a.measure(good, replace(good, at_seconds=12, **{field: value})
                          if field != "at_seconds" else replace(good, at_seconds=value))

    def test_scope_capacity_clock_and_counter_changes_are_explicitly_unavailable(self):
        good = a.AggregateSample("invented-scope", 10, 6, 90, 8_000)
        after = replace(good, at_seconds=12, busy_cpu_seconds=94)
        for changed in (replace(after, scope="another-invented-scope"),
                        replace(after, cpu_capacity_cores=3),
                        replace(after, at_seconds=10), replace(after, busy_cpu_seconds=89)):
            with self.assertRaises(a.MeasurementUnavailable):
                a.measure(good, changed)


class BoundedAdmissionTests(unittest.TestCase):
    def test_hold_canonical_lock_for_work_then_release_own_token(self):
        lock, clock = Lock(), Clock()
        with wait(lambda remaining: capacity(), lock, clock) as result:
            self.assertEqual((result.status, result.workers), ("admitted", 3))
            self.assertIsNotNone(lock.held)
            self.assertEqual(lock.released, [])
        self.assertIsNone(lock.held)
        self.assertEqual(len(lock.released), 1)
        self.assertEqual(clock.pauses, [])

    def test_scientific_callback_failure_still_releases_only_our_token(self):
        lock, clock = Lock(), Clock()
        with self.assertRaisesRegex(RuntimeError, "invented work failed"):
            with wait(lambda remaining: capacity(), lock, clock):
                raise RuntimeError("invented work failed")
        self.assertIsNone(lock.held)
        self.assertEqual(len(lock.released), 1)

    def test_busy_project_lock_cannot_be_bypassed_with_free_resources(self):
        lock, clock = Lock(busy_attempts=100), Clock()
        with wait(lambda remaining: capacity(), lock, clock) as result:
            self.assertEqual((result.status, result.workers), ("diagnostic", 0))
            self.assertEqual(result.reason, "wait_budget_exhausted")
            self.assertTrue(all(row["reasons"] == ["canonical_project_lock_busy"]
                                for row in result.attempts))
        self.assertEqual(lock.calls, 3)
        self.assertEqual(lock.released, [])

    def test_resource_wait_does_not_hold_lock_and_can_admit_later(self):
        lock, clock = Lock(), Clock()
        budgets = []
        def probe(remaining):
            budgets.append(remaining)
            self.assertIsNone(lock.held)
            return capacity(busy_cores=6 if len(budgets) == 1 else 2)
        with wait(probe, lock, clock) as result:
            self.assertEqual(result.status, "admitted")
            self.assertEqual(result.waited_seconds, 1)
            self.assertEqual(result.attempts[0]["reasons"], ["cpu_headroom"])
            self.assertEqual(result.workers, 3)
        self.assertEqual(budgets, [3, 2])
        self.assertEqual(lock.calls, 1)

    def test_last_sleep_is_clipped_and_timeout_is_one_diagnostic(self):
        lock, clock = Lock(), Clock()
        yielded = []
        with wait(lambda remaining: capacity(busy_cores=6), lock, clock,
                  wait_seconds=2.5, poll_seconds=2) as result:
            yielded.append(result)
        self.assertEqual(len(yielded), 1)
        self.assertEqual((result.status, result.waited_seconds), ("diagnostic", 2.5))
        self.assertEqual(clock.pauses, [2, 0.5])
        self.assertEqual(len(result.attempts), 2)
        self.assertEqual(lock.calls, 0)

    def test_sample_that_uses_entire_budget_cannot_authorize_start(self):
        lock, clock = Lock(), Clock()
        def probe(remaining):
            clock.value += remaining
            return capacity()
        with wait(probe, lock, clock) as result:
            self.assertEqual(result.reason, "wait_budget_exhausted_during_measurement")
            self.assertEqual(result.workers, 0)
        self.assertEqual(lock.calls, 0)

    def test_late_acquisition_releases_our_token_before_diagnostic(self):
        clock = Clock()
        class LateLock(Lock):
            def try_acquire(self):
                token = super().try_acquire()
                clock.value += 3
                return token
        lock = LateLock()
        with wait(lambda remaining: capacity(), lock, clock) as result:
            self.assertEqual(result.reason, "wait_budget_exhausted_during_lock_attempt")
            self.assertIsNone(lock.held)
            self.assertEqual(result.workers, 0)
        self.assertEqual(len(lock.released), 1)

    def test_unknown_measurement_waits_then_returns_explicit_reason(self):
        lock, clock = Lock(), Clock()
        def unavailable(remaining):
            raise a.MeasurementUnavailable("invented absent counter")
        with wait(unavailable, lock, clock) as result:
            self.assertEqual(result.status, "diagnostic")
            self.assertTrue(all(row["reasons"] == ["measurement_unavailable"]
                                for row in result.attempts))
        self.assertEqual(lock.calls, 0)

    def test_changed_lock_identity_is_a_diagnostic_not_an_alternate_lock(self):
        lock, clock = Lock(busy_attempts=1), Clock()
        def probe(remaining):
            if clock.value:
                lock.key = "invented-alternate-lock"
            return capacity()
        with wait(probe, lock, clock) as result:
            self.assertEqual(result.reason, "canonical_lock_identity_changed")
            self.assertEqual(result.canonical_lock, "invented-canonical-project-lock")
        self.assertEqual(lock.calls, 1)
        self.assertEqual(lock.released, [])

    def test_nonadvancing_clock_cannot_spin_forever(self):
        lock, clock = Lock(), Clock()
        with a.admission(lambda remaining: capacity(busy_cores=6), lock, DEMAND,
                         wait_seconds=3, poll_seconds=1,
                         clock=clock, pause=lambda seconds: None) as result:
            self.assertEqual(result.reason, "clock_did_not_advance")
            self.assertEqual(len(result.attempts), 1)

    def test_clock_regression_after_acquire_returns_diagnostic_and_releases(self):
        clock = Clock()
        clock.value = 10
        class BrokenClockLock(Lock):
            def try_acquire(self):
                token = super().try_acquire()
                clock.value = 9
                return token
        lock = BrokenClockLock()
        with wait(lambda remaining: capacity(), lock, clock) as result:
            self.assertEqual(result.reason, "invalid_monotonic_clock")
            self.assertIsNone(lock.held)
        self.assertEqual(len(lock.released), 1)

    def test_lock_error_returns_diagnostic_without_releasing_foreign_lock(self):
        class BrokenLock(Lock):
            def try_acquire(self):
                raise OSError("invented adapter failure")
        lock, clock = BrokenLock(), Clock()
        with wait(lambda remaining: capacity(), lock, clock) as result:
            self.assertEqual(result.reason, "canonical_lock_error")
        self.assertEqual(lock.released, [])

    def test_invalid_budgets_and_demand_fail_before_acquiring_lock(self):
        for seconds in (0, -1, float("inf"), True):
            lock, clock = Lock(), Clock()
            with self.assertRaises(ValueError):
                with wait(lambda remaining: capacity(), lock, clock, wait_seconds=seconds):
                    self.fail("invalid budget yielded a result")
            self.assertEqual(lock.calls, 0)
        for demand in (replace(DEMAND, worker_cpu_cores=0),
                       replace(DEMAND, worker_memory_bytes=0),
                       replace(DEMAND, max_workers=True)):
            with self.assertRaises(ValueError):
                a.select_workers(capacity(), demand)

    def test_demo_is_explicitly_invented_and_makes_no_scientific_claim(self):
        report = a.demo()
        self.assertEqual(report["evidence_kind"], "invented_resource_contract")
        self.assertEqual(report["new_real_fits"], 0)
        self.assertFalse(report["scientific_eligibility_changed"])
        self.assertTrue(report["lock_held_inside_context"])
        self.assertTrue(report["lock_released_after_context"])


if __name__ == "__main__":
    unittest.main()
