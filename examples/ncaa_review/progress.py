"""Honest progress and empirical ETA on invented, already-committed work.

This pure example neither samples a host nor starts, cancels or retries work.
Callers supply a monotonic phase clock and durable completion counters.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from typing import Literal, Sequence


@dataclass(frozen=True)
class Observation:
    phase: str
    seconds: float
    newly_committed: int
    reused: int = 0
    failed_attempts: int = 0
    workers: int | None = None


@dataclass(frozen=True)
class Progress:
    phase: str
    status: str
    completed: int
    total: int | None
    newly_committed: int
    reused: int
    failed_attempts: int
    remaining: int | None
    fraction: float | None
    phase_elapsed_seconds: float
    wall_elapsed_seconds: float
    workers: int | None
    last_progress_age_seconds: float
    eta_status: str
    eta_seconds: float | None
    observed_pace_low_seconds: float | None
    observed_pace_high_seconds: float | None
    sample_intervals: int
    estimate_scope: str = "CURRENT_PHASE_ONLY"
    estimate_qualification: str = (
        "Observed pace range, not a confidence interval or a completion guarantee. "
        "Task mix, resource contention and later phases can change duration."
    )


def _count(value: int, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a nonnegative integer")
    return value


def _seconds(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + " must be finite and nonnegative")
    if not math.isfinite(value) or value < 0:
        raise ValueError(name + " must be finite and nonnegative")
    return float(value)


def estimate(
    observations: Sequence[Observation], *, total: int | None,
    observed_at: float, wall_elapsed_seconds: float | None = None,
    status: Literal["running", "completed", "failed", "cancelled"] = "running",
    stale_after_seconds: float = 60.0,
) -> Progress:
    """Use recent same-worker completion intervals; never extrapolate reuse.

    A known denominator and two positive completion intervals are needed for an
    ETA. Worker changes reset the sampling window. Idle time is included in
    interval duration, and an extended stall invalidates the estimate.
    """
    if not observations:
        raise ValueError("at least one observation is required")
    if status not in {"running", "completed", "failed", "cancelled"}:
        raise ValueError("unknown phase status")
    if total is not None:
        _count(total, "total")
    observed_at = _seconds(observed_at, "observed_at")
    stale_after_seconds = _seconds(stale_after_seconds, "stale_after_seconds")
    if stale_after_seconds == 0:
        raise ValueError("stale threshold must be positive")
    wall = observed_at if wall_elapsed_seconds is None else _seconds(wall_elapsed_seconds, "wall_elapsed_seconds")
    if wall < observed_at:
        raise ValueError("wall elapsed cannot be shorter than phase elapsed")
    phase = observations[0].phase
    if not isinstance(phase, str) or not phase.strip():
        raise ValueError("phase identity is required")
    previous = None
    segment_start = 0
    last_progress = observations[0].seconds
    for i, point in enumerate(observations):
        _seconds(point.seconds, "phase clock")
        for name in ("newly_committed", "reused", "failed_attempts"):
            _count(getattr(point, name), name)
        if point.workers is not None:
            _count(point.workers, "workers")
            if point.workers == 0:
                raise ValueError("workers must be positive or unknown")
        if point.phase != phase:
            raise ValueError("cannot combine different phases")
        if total is not None and point.newly_committed + point.reused > total:
            raise ValueError("completion exceeds the declared total")
        if previous is not None:
            if point.seconds <= previous.seconds:
                raise ValueError("phase clock must increase strictly")
            for name in ("newly_committed", "reused", "failed_attempts"):
                if getattr(point, name) < getattr(previous, name):
                    raise ValueError("counters cannot move backward within a phase")
            if point.workers != previous.workers:
                segment_start = i
            if point.newly_committed > previous.newly_committed:
                last_progress = point.seconds
        previous = point
    last = observations[-1]
    if observed_at < last.seconds:
        raise ValueError("observation time predates the newest sample")
    completed = last.newly_committed + last.reused
    remaining = None if total is None else total - completed
    if status == "completed" and (total is None or remaining != 0):
        raise ValueError("completed phase requires a closed, satisfied denominator")

    # Samples before a concurrency change cannot support the new pace. A reuse
    # jump changes remaining work but does not count as new processing speed.
    intervals = []
    anchor = observations[segment_start]
    for point in observations[segment_start + 1:]:
        delta = point.newly_committed - anchor.newly_committed
        if delta:
            intervals.append((point.seconds - anchor.seconds, delta))
            anchor = point
    intervals = intervals[-6:]
    age = observed_at - last_progress
    reason = "WARMUP"
    eta = low = high = None
    if status in {"failed", "cancelled"}:
        reason = "STOPPED_WITH_UNFINISHED_WORK"
    elif status == "completed":
        reason = "COMPLETED"
        eta = low = high = 0.0
    elif total is None:
        reason = "UNKNOWN_TOTAL"
    elif remaining == 0:
        reason = "AWAITING_PHASE_FINALIZATION"
    elif age >= stale_after_seconds:
        reason = "STALE_PACE"
    elif len(intervals) < 2:
        reason = "WORKER_CHANGE_WARMUP" if segment_start else "WARMUP"
    else:
        per_unit = [seconds / count for seconds, count in intervals]
        eta = sum(seconds for seconds, _ in intervals) / sum(count for _, count in intervals) * remaining
        low, high = min(per_unit) * remaining, max(per_unit) * remaining
        reason = "EMPIRICAL_PHASE_ESTIMATE"
    return Progress(
        phase=phase, status=status, completed=completed, total=total,
        newly_committed=last.newly_committed, reused=last.reused,
        failed_attempts=last.failed_attempts, remaining=remaining,
        fraction=None if total is None else (1.0 if total == 0 else completed / total),
        phase_elapsed_seconds=observed_at, wall_elapsed_seconds=wall,
        workers=last.workers, last_progress_age_seconds=age,
        eta_status=reason, eta_seconds=eta,
        observed_pace_low_seconds=low, observed_pace_high_seconds=high,
        sample_intervals=len(intervals),
    )


def demo_scenarios() -> list[dict]:
    """Invented clocks and units for the executable example and static UI."""
    def points(rows):
        return [Observation("invented task batch", t, n, reused=r, workers=w)
                for t, n, r, w in rows]

    steady = points([(0, 0, 0, 2), (10, 2, 0, 2), (20, 4, 0, 2), (30, 6, 0, 2)])
    cases = [
        ("warmup", "Warmup", "One completion interval is not enough to estimate a finish.", steady[:2], 12, 10, "running"),
        ("measured", "Measured pace", "Six newly committed units leave six; recent observed pace gives a phase estimate.", steady, 12, 30, "running"),
        ("reused", "Reused work", "Eight restored units reduce remaining work without inflating measured throughput.", points([(0, 0, 8, 2), (10, 2, 8, 2), (20, 4, 8, 2)]), 20, 20, "running"),
        ("unknown", "Unknown total", "Pagination has not established a denominator; count progress without inventing a percentage.", steady, None, 30, "running"),
        ("workers", "Worker change", "A lower worker count starts a fresh pace window; old throughput cannot promise a finish.", points([(0, 0, 0, 4), (10, 8, 0, 4), (20, 16, 0, 4), (25, 17, 0, 1)]), 30, 25, "running"),
        ("stalled", "Stalled", "No newly committed work for over a minute invalidates the old estimate.", steady, 12, 95, "running"),
        ("failed", "Failed", "A failed phase keeps its completed units and unfinished count; it is not 100% complete.", steady, 12, 30, "failed"),
        ("complete", "Complete", "All declared work and phase finalization are complete.", steady, 6, 30, "completed"),
    ]
    return [{"id": key, "label": label, "explanation": note,
             "progress": asdict(estimate(samples, total=total, observed_at=t,
                                         wall_elapsed_seconds=t + 120, status=status))}
            for key, label, note, samples, total, t, status in cases]


def main() -> int:
    print(json.dumps({"source": "INVENTED_EXAMPLE", "scenarios": demo_scenarios()}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
