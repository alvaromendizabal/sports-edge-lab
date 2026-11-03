"""Resource admission contracts with invented inputs; standard library only.

This is an adapter-independent example, not an owner runtime or host monitor.
The sampler must measure the same scope as its CPU capacity and available
memory, including effective affinity/quotas and memory limits when applicable.
Aggregate busy CPU includes all processes, children and exited tasks. Process
counters exclude reaped-child CPU and are diagnostic only: do not subtract them
again from aggregate headroom or subtract summed RSS from available memory.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import json
import math
import time
from typing import Callable, Iterator, Protocol


class MeasurementUnavailable(ValueError):
    """Missing or inconsistent resource evidence; never an idle-machine value."""


def _number(value: float, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeasurementUnavailable("numeric measurement required")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise MeasurementUnavailable("finite nonnegative measurement required")
    return value


def _bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MeasurementUnavailable("nonnegative integer byte count required")
    return value


@dataclass(frozen=True)
class ProcessCounter:
    # A stable identity includes a start token; a PID alone can be reused.
    key: str
    parent_key: str | None
    cpu_seconds: float
    resident_bytes: int


@dataclass(frozen=True)
class AggregateSample:
    scope: str
    at_seconds: float
    cpu_capacity_cores: float
    busy_cpu_seconds: float
    memory_available_bytes: int
    processes: tuple[ProcessCounter, ...] = ()


@dataclass(frozen=True)
class Capacity:
    scope: str
    window_seconds: float
    busy_cpu_cores: float
    available_cpu_cores: float
    memory_available_bytes: int
    observed_tree_cpu_cores: float | None
    tree_rss_sum_bytes: int | None
    incomplete_process_keys: tuple[str, ...]
    process_accounting_status: str


def _processes(sample: AggregateSample) -> dict[str, ProcessCounter]:
    rows: dict[str, ProcessCounter] = {}
    for row in sample.processes:
        if not row.key or row.key in rows:
            raise MeasurementUnavailable("missing or duplicate process identity")
        _number(row.cpu_seconds)
        _bytes(row.resident_bytes)
        rows[row.key] = row
    for key in rows:
        seen = set()
        while key in rows:
            if key in seen:
                raise MeasurementUnavailable("cyclic process ancestry")
            seen.add(key)
            key = rows[key].parent_key
    return rows


def _tree_usage(before: AggregateSample, after: AggregateSample,
                roots: tuple[str, ...], elapsed: float) -> tuple:
    earlier, later = _processes(before), _processes(after)
    members = set(roots)
    while True:
        expanded = members | {p.key for p in (*earlier.values(), *later.values())
                              if p.parent_key in members}
        if expanded == members:
            break
        members = expanded
    cpu_seconds, missing = 0.0, []
    for key in sorted(members):
        if key not in earlier or key not in later:
            missing.append(key)
        else:
            delta = later[key].cpu_seconds - earlier[key].cpu_seconds
            if delta < 0:
                missing.append(key)
            else:
                cpu_seconds += delta
    return (cpu_seconds / elapsed,
            sum(later[key].resident_bytes for key in members if key in later),
            tuple(missing), "partial" if missing else "complete")


def measure(before: AggregateSample, after: AggregateSample,
            roots: tuple[str, ...] = ()) -> Capacity:
    """Derive CPU cores from a sampled cumulative counter, plus tree diagnostics."""
    for sample in (before, after):
        if not isinstance(sample.scope, str) or not sample.scope:
            raise MeasurementUnavailable("measurement scope required")
        _number(sample.at_seconds)
        _number(sample.cpu_capacity_cores, positive=True)
        _number(sample.busy_cpu_seconds)
        _bytes(sample.memory_available_bytes)
    if before.scope != after.scope or before.cpu_capacity_cores != after.cpu_capacity_cores:
        raise MeasurementUnavailable("scope or CPU capacity changed across sample")
    elapsed = after.at_seconds - before.at_seconds
    used = after.busy_cpu_seconds - before.busy_cpu_seconds
    if elapsed <= 0 or used < 0:
        raise MeasurementUnavailable("nonpositive window or reset CPU counter")
    busy_cores = _number(used / elapsed)
    process_usage = (None, None, (), "not_requested")
    if roots:
        try:
            process_usage = _tree_usage(before, after, roots, elapsed)
        except MeasurementUnavailable:
            # Aggregate counters remain usable when optional process detail fails.
            process_usage = (None, None, (), "unavailable")
    return Capacity(
        scope=after.scope, window_seconds=elapsed, busy_cpu_cores=busy_cores,
        available_cpu_cores=max(0.0, after.cpu_capacity_cores - busy_cores),
        memory_available_bytes=after.memory_available_bytes,
        observed_tree_cpu_cores=process_usage[0], tree_rss_sum_bytes=process_usage[1],
        incomplete_process_keys=process_usage[2], process_accounting_status=process_usage[3],
    )


@dataclass(frozen=True)
class Demand:
    worker_cpu_cores: float
    worker_memory_bytes: int
    max_workers: int
    reserve_cpu_cores: float
    reserve_memory_bytes: int

    def validate(self) -> None:
        _number(self.worker_cpu_cores, positive=True)
        _number(self.reserve_cpu_cores)
        _bytes(self.worker_memory_bytes)
        _bytes(self.reserve_memory_bytes)
        if self.worker_memory_bytes == 0:
            raise ValueError("worker memory must be positive")
        if isinstance(self.max_workers, bool) or not isinstance(self.max_workers, int) or self.max_workers < 1:
            raise ValueError("positive integer worker limit required")


def select_workers(capacity: Capacity, demand: Demand) -> tuple[int, tuple[str, ...]]:
    demand.validate()
    _number(capacity.available_cpu_cores)
    _bytes(capacity.memory_available_bytes)
    cpu_slots = math.floor(min(demand.max_workers,
                              max(0, capacity.available_cpu_cores - demand.reserve_cpu_cores)
                              / demand.worker_cpu_cores))
    memory_slots = max(0, capacity.memory_available_bytes - demand.reserve_memory_bytes) // demand.worker_memory_bytes
    reasons = tuple(reason for available, reason in
                    ((cpu_slots, "cpu_headroom"), (memory_slots, "memory_headroom")) if available < 1)
    return min(cpu_slots, memory_slots, demand.max_workers), reasons


class CanonicalLock(Protocol):
    """Existing canonical project lock: nonblocking acquire; release own token only.

    An adapter must bind key to the actual canonical lock and retain ownership
    until release. No alternate lock, stale-lock deletion or process termination
    operation is part of this policy. Process listings cannot prove ownership.
    """
    key: str

    def try_acquire(self) -> object | None: ...
    def release(self, token: object) -> None: ...


@dataclass(frozen=True)
class AdmissionResult:
    status: str
    reason: str
    workers: int
    waited_seconds: float
    canonical_lock: str
    attempts: tuple[dict, ...]


@contextmanager
def admission(probe: Callable[[float], Capacity], lock: CanonicalLock, demand: Demand,
              *, wait_seconds: float, poll_seconds: float,
              clock: Callable[[], float] = time.monotonic,
              pause: Callable[[float], None] = time.sleep) -> Iterator[AdmissionResult]:
    """Yield one admission or bounded diagnostic; hold only our acquired token.

    probe receives the remaining time budget and must honor it. try_acquire is
    nonblocking. The deadline is rechecked after each call, so evidence returned
    late cannot authorize a start. The loop cannot interrupt a broken adapter's
    unbounded blocking call; real adapters need their own timeouts.
    """
    demand.validate()
    _number(wait_seconds, positive=True)
    _number(poll_seconds, positive=True)
    canonical_key = lock.key
    if not isinstance(canonical_key, str) or not canonical_key:
        raise ValueError("canonical lock identity required")
    start = _number(clock())
    last_clock = start
    deadline = _number(start + wait_seconds, positive=True)
    attempts: list[dict] = []
    held = None
    workers = 0
    status, reason = "diagnostic", "wait_budget_exhausted"

    def now() -> float:
        nonlocal last_clock
        current = _number(clock())
        if current < last_clock:
            raise MeasurementUnavailable("monotonic clock moved backwards")
        last_clock = current
        return current

    try:
        try:
            while now() < deadline:
                row: dict = {"elapsed_seconds": last_clock - start}
                try:
                    capacity = probe(deadline - last_clock)
                    count, blocked = select_workers(capacity, demand)
                    row.update(capacity=asdict(capacity), workers=count,
                               reasons=list(blocked))
                except MeasurementUnavailable:
                    count = 0
                    row.update(workers=0, reasons=["measurement_unavailable"])
                attempts.append(row)
                if now() >= deadline:
                    reason = "wait_budget_exhausted_during_measurement"
                    break
                if count:
                    if lock.key != canonical_key:
                        reason = "canonical_lock_identity_changed"
                        break
                    try:
                        held = lock.try_acquire()
                    except OSError:
                        reason = "canonical_lock_error"
                        break
                    if now() >= deadline:
                        reason = "wait_budget_exhausted_during_lock_attempt"
                        break
                    if held is not None:
                        status, reason, workers = "admitted", "capacity_and_lock_available", count
                        break
                    row["reasons"] = ["canonical_project_lock_busy"]
                remaining = deadline - last_clock
                if remaining <= 0:
                    break
                before_pause = last_clock
                pause(min(poll_seconds, remaining))
                if now() == before_pause:
                    reason = "clock_did_not_advance"
                    break
        except MeasurementUnavailable:
            reason = "invalid_monotonic_clock"
        if status != "admitted" and held is not None:
            token, held = held, None
            lock.release(token)
        yield AdmissionResult(status, reason, workers, last_clock - start,
                              canonical_key, tuple(attempts))
    finally:
        if held is not None:
            token, held = held, None
            lock.release(token)


def demo() -> dict:
    """Invented scope, process identities and budgets; no host or lock mutation."""
    before = AggregateSample("invented-scope", 10, 6, 90, 9_000,
        (ProcessCounter("invented-p4101:start-a", None, 1, 500),
         ProcessCounter("invented-p4102:start-b", "invented-p4101:start-a", 3, 700)))
    after = AggregateSample("invented-scope", 12, 6, 94, 8_000,
        (ProcessCounter("invented-p4101:start-a", None, 1, 500),
         ProcessCounter("invented-p4102:start-b", "invented-p4101:start-a", 7, 700)))
    measured = measure(before, after, ("invented-p4101:start-a",))
    demand = Demand(1, 1_500, 5, 0.5, 1_000)

    class InventedLock:
        key = "invented-canonical-project-lock"
        token = None

        def try_acquire(self):
            self.token = object()
            return self.token

        def release(self, token):
            assert token is self.token
            self.token = None

    lock = InventedLock()
    with admission(lambda remaining: measured, lock, demand,
                   wait_seconds=3, poll_seconds=1, clock=lambda: 0) as result:
        report = asdict(result)
        report["lock_held_inside_context"] = lock.token is not None
    report.update(lock_released_after_context=lock.token is None,
                  evidence_kind="invented_resource_contract", new_real_fits=0,
                  scientific_eligibility_changed=False)
    return report


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
