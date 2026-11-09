"""Measured execution progress, separate from scientific achievement.

This module observes clocks and caller-supplied receipts.  It never performs a
fit, supplies missing counters, predicts progress from a stage name, or delays
work to make a run look busy.  ETA describes only the current phase's observed
pace; a new phase starts with no timing model.
"""
from collections import deque
from datetime import datetime, timezone
import json
import math
import re
import sys
import threading
import time


SCHEMA = "fbs.v052.measured-execution-progress.v1"
COUNTERS = (
    "new_base_fits", "new_calibration_fits", "completed_optimizers",
    "reused_fit_states", "recovered_fit_states", "failed_fit_attempts",
    "new_prediction_outputs", "reused_prediction_outputs",
    "new_genuine_forecast_issues", "candidates_registered",
    "candidates_materialized", "candidates_evaluated", "provider_requests",
    "cache_hits",
)
END_STATES = frozenset(("COMPLETED", "PARTIAL", "FAILED", "DEFERRED",
                        "CANCELLED", "SKIPPED", "STOPPED_WITHOUT_PHASE_COMPLETION"))
MAX_PHASES = 128
MAX_EVIDENCE_BYTES = 32768
MAX_ERRORS = 16
PACE_WINDOW = 12
MIN_PACE_INTERVALS = 3


def _finite_json(value):
    """Copy caller-owned values while refusing NaN and non-JSON objects."""
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def _count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name + " must be a nonnegative integer")
    return value


def _label(value, name):
    if not isinstance(value, str) or not value or len(value) > 200:
        raise ValueError(name + " must be a nonempty bounded string")
    return value


def _default_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProgressReportingError(RuntimeError):
    def __init__(self, record):
        self.record = record
        super().__init__("Execution progress reporting failed: " + record["message"])


class ProgressTracker:
    """Thread-safe observer for one invocation and sequential work phases.

    ``counts`` are absolute snapshots within the named phase.  Unobserved
    counters remain null.  Counts are never summed across phases: different
    phases may refer to the same immutable fit or forecast.

    The caller owns scientific accounting and phase boundaries.  Invoke
    ``check`` from the existing cancellation/check callback so an asynchronous
    reporting failure becomes a visible owner failure with a retained receipt.
    ``receipt`` remains readable after failures for diagnostic preservation.
    """

    def __init__(self, run_id, emit, *, monotonic=None, utc_now=None):
        self.run_id = _label(run_id, "run_id")
        if not callable(emit):
            raise TypeError("emit must be callable")
        self._emit = emit
        self._clock = monotonic or time.monotonic
        self._utc = utc_now or _default_utc
        self._lock = threading.RLock()
        self._last_clock = None
        self._started = self._now()
        self._created_at = self._utc_stamp()
        self._phase = None
        self._phases = []
        self._finished = None
        self._run_status = "RUNNING"
        self._errors = []
        self._error_count = 0
        self._thread_failure = None
        self._thread = None
        self._stop = threading.Event()
        self._heartbeat_interval = None
        self._events = 0

    def _now(self):
        value = self._clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Monotonic clock must be finite")
        if self._last_clock is not None and value < self._last_clock:
            raise ValueError("Monotonic clock moved backwards")
        self._last_clock = float(value)
        return self._last_clock

    def _utc_stamp(self):
        value = _label(self._utc(), "UTC timestamp")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError("Progress timestamp must be timezone-aware UTC")
        return value

    def _require_running(self):
        self.check()
        if self._finished is not None:
            raise RuntimeError("Invocation progress is already finished")

    def check(self):
        with self._lock:
            if self._thread_failure is not None:
                raise ProgressReportingError(dict(self._thread_failure))
            if self._errors:
                raise ProgressReportingError(dict(self._errors[-1]))

    def _failure(self, error, event):
        message = str(error)
        record = {"type": type(error).__name__, "message": message[:4096],
                  "message_truncated": len(message) > 4096,
                  "event": event, "observed_at_utc": self._utc_stamp(),
                  "scientific_failure_count_credit": 0}
        self._error_count += 1
        if len(self._errors) < MAX_ERRORS:
            self._errors.append(record)
        # A broken journal must not hide a reporting-thread failure.
        print("V052_PROGRESS_REPORTING_FAILED=" + json.dumps(record, sort_keys=True,
              ensure_ascii=False, allow_nan=False), file=sys.stderr, flush=True)
        return ProgressReportingError(record)

    def _publish(self, event, snapshot):
        snapshot = _finite_json(snapshot)
        try:
            self._emit(event, **snapshot)
        except BaseException as error:
            raise self._failure(error, event) from error
        self._events += 1
        return snapshot

    @staticmethod
    def _counter_snapshot(old, supplied):
        new = dict(old)
        if supplied is None:
            return new
        if not isinstance(supplied, dict):
            raise TypeError("counts must be a dictionary of absolute phase counters")
        for name, value in supplied.items():
            if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", name):
                raise ValueError("Invalid counter name")
            if value is None:
                if new.get(name) is not None:
                    raise ValueError("An observed counter cannot become unknown")
                new[name] = None
                continue
            _count(value, name)
            if new.get(name) is not None and value < new[name]:
                raise ValueError("Absolute phase counter decreased: " + name)
            new[name] = value
        return new

    @staticmethod
    def _evidence(value):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError("evidence must be a dictionary")
        copy = _finite_json(value)
        if len(json.dumps(copy, ensure_ascii=False, allow_nan=False).encode()) > MAX_EVIDENCE_BYTES:
            raise ValueError("Progress evidence exceeds the bounded record allowance")
        return copy

    def begin_phase(self, name, total_units=None, unit_name=None, counts=None,
                    *, completed_units=0, evidence=None):
        with self._lock:
            self._require_running()
            if self._phase is not None:
                raise RuntimeError("End the current phase before beginning another")
            if len(self._phases) >= MAX_PHASES:
                raise ValueError("Progress phase allowance reached; no phase silently discarded")
            _label(name, "phase name")
            unit_name = _label(unit_name or "work_units", "unit name")
            completed = _count(completed_units, "completed_units")
            if total_units is not None:
                _count(total_units, "total_units")
                if completed > total_units:
                    raise ValueError("Completed units exceed the declared denominator")
            current_counts = self._counter_snapshot({k: None for k in COUNTERS}, counts)
            current_evidence = self._evidence(evidence)
            moment = self._now()
            self._phase = {
                "name": name, "sequence": len(self._phases) + 1,
                "status": "RUNNING", "started": moment,
                "started_at_utc": self._utc_stamp(), "finished": None,
                "unit_name": unit_name, "completed_units": completed,
                "total_units": total_units, "counts": current_counts,
                "evidence": current_evidence, "last_work": None,
                "pace_clock": moment, "pace_units": completed,
                "pace": deque(maxlen=PACE_WINDOW), "denominator_revisions": 0,
            }
            # Immediate event: no timer, provider call, or first fit is required.
            return self._publish("V052_PROGRESS_PHASE_STARTED", self._snapshot(moment))

    def update(self, completed_units=None, total_units=None, counts=None, evidence=None):
        with self._lock:
            self._require_running()
            if self._phase is None:
                raise RuntimeError("No active phase")
            phase = self._phase
            completed = phase["completed_units"] if completed_units is None else _count(completed_units, "completed_units")
            total = phase["total_units"] if total_units is None else _count(total_units, "total_units")
            if completed < phase["completed_units"] or (total is not None and completed > total):
                raise ValueError("Completed units regress or exceed the declared denominator")
            new_counts = self._counter_snapshot(phase["counts"], counts)
            new_evidence = phase["evidence"] if evidence is None else self._evidence(evidence)
            moment = self._now()
            advanced = completed > phase["completed_units"] or any(
                value is not None and value > (phase["counts"].get(key) or 0)
                for key, value in new_counts.items())
            if total != phase["total_units"]:
                phase["pace"].clear()
                phase["pace_clock"] = moment
                phase["pace_units"] = completed
                phase["denominator_revisions"] += 1
            elif completed > phase["pace_units"]:
                duration = moment - phase["pace_clock"]
                if duration > 0:
                    phase["pace"].append({"seconds": duration,
                        "units": completed - phase["pace_units"]})
                phase["pace_clock"] = moment
                phase["pace_units"] = completed
            phase.update(completed_units=completed, total_units=total,
                         counts=new_counts, evidence=new_evidence)
            if advanced:
                phase["last_work"] = moment
            return self._publish("V052_PROGRESS_OBSERVED", self._snapshot(moment))

    def _eta(self, phase, moment):
        out = {"scope": "CURRENT_PHASE_ONLY", "status": "UNKNOWN",
               "minimum_seconds": None, "maximum_seconds": None,
               "measured_completion_intervals": len(phase["pace"]),
               "whole_invocation_eta_seconds": None,
               "completion_guaranteed": False}
        if phase["status"] != "RUNNING":
            out["reason"] = "PHASE_TERMINAL_NO_FUTURE_ESTIMATE"
        elif phase["total_units"] is None:
            out["reason"] = "WORK_DENOMINATOR_NOT_OBSERVED"
        elif phase["completed_units"] == phase["total_units"]:
            out.update(status="DECLARED_UNITS_COMPLETE", minimum_seconds=0.0,
                       maximum_seconds=0.0, reason="PHASE_FINALIZATION_NOT_INCLUDED")
        elif len(phase["pace"]) < MIN_PACE_INTERVALS:
            out["reason"] = "INSUFFICIENT_MEASURED_COMPLETION_INTERVALS"
        elif moment - phase["pace_clock"] > max(30.0, 3 * max(x["seconds"] for x in phase["pace"])):
            out["reason"] = "NO_RECENT_COMPLETION_PACE_MAY_HAVE_CHANGED"
        else:
            seconds_per_unit = [x["seconds"] / x["units"] for x in phase["pace"]]
            remaining = phase["total_units"] - phase["completed_units"]
            low, high = min(seconds_per_unit) * remaining, max(seconds_per_unit) * remaining
            if not math.isfinite(low) or not math.isfinite(high):
                out["reason"] = "MEASURED_RANGE_NOT_FINITE"
            else:
                out.update(status="MEASURED_CURRENT_PHASE_PACE_RANGE",
                    minimum_seconds=low, maximum_seconds=high,
                    reason="OBSERVED_PACE_RANGE_NOT_A_CONFIDENCE_INTERVAL",
                    measurement_window_intervals=PACE_WINDOW)
        return out

    def _snapshot(self, moment):
        out = {"schema": SCHEMA, "run_id": self.run_id,
               "observed_at_utc": self._utc_stamp(),
               "elapsed_total_seconds": (self._finished if self._finished is not None else moment) - self._started,
               "invocation_status": self._run_status,
               "elapsed_time_is_not_scientific_progress": True,
               "cross_phase_counter_totals_inferred": False,
               "whole_invocation_eta_seconds": None,
               "heartbeat_interval_seconds": self._heartbeat_interval}
        phase = self._phase
        if phase is None:
            out.update(phase_name=None, phase_sequence=None, phase_status=None,
                       phase_elapsed_seconds=None, counts=None, work_units=None,
                       seconds_since_observed_work=None,
                       eta={"status": "UNKNOWN", "reason": "NO_ACTIVE_PHASE",
                            "minimum_seconds": None, "maximum_seconds": None})
        else:
            end = phase["finished"] if phase["finished"] is not None else moment
            out.update(phase_name=phase["name"], phase_sequence=phase["sequence"],
                phase_status=phase["status"], phase_started_at_utc=phase["started_at_utc"],
                phase_elapsed_seconds=end - phase["started"],
                counts=dict(phase["counts"]), counter_scope="CURRENT_PHASE_ABSOLUTE_RECEIPT_SNAPSHOT",
                work_units={"name": phase["unit_name"], "completed": phase["completed_units"],
                    "total": phase["total_units"], "denominator_revisions": phase["denominator_revisions"]},
                seconds_since_observed_work=None if phase["last_work"] is None else end - phase["last_work"],
                evidence=phase["evidence"], eta=self._eta(phase, end))
        return out

    def heartbeat(self):
        with self._lock:
            self._require_running()
            return self._publish("V052_PROGRESS_HEARTBEAT", self._snapshot(self._now()))

    def end_phase(self, status, *, evidence=None):
        with self._lock:
            self._require_running()
            if self._phase is None:
                raise RuntimeError("No active phase")
            if status not in END_STATES:
                raise ValueError("Unknown phase completion status")
            phase = self._phase
            if status == "COMPLETED" and phase["total_units"] is not None and phase["completed_units"] != phase["total_units"]:
                raise ValueError("Cannot complete a phase with unfinished declared work units")
            new_evidence = phase["evidence"] if evidence is None else self._evidence(evidence)
            moment = self._now()
            phase.update(status=status, finished=moment, evidence=new_evidence)
            snapshot = self._snapshot(moment)
            # Preserve the terminal snapshot even if the output journal fails.
            self._phases.append(_finite_json(snapshot))
            try:
                return self._publish("V052_PROGRESS_PHASE_FINISHED", snapshot)
            finally:
                self._phase = None

    def _heartbeat_loop(self):
        while not self._stop.wait(self._heartbeat_interval):
            try:
                self.heartbeat()
            except BaseException as error:
                with self._lock:
                    failure = error if isinstance(error, ProgressReportingError) else self._failure(error, "V052_PROGRESS_HEARTBEAT")
                    self._thread_failure = dict(failure.record)
                self._stop.set()
                return

    def start_heartbeat(self, interval_seconds=10.0):
        with self._lock:
            self._require_running()
            if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, (int, float)) or not math.isfinite(interval_seconds) or not 0 < interval_seconds <= 30:
                raise ValueError("Heartbeat interval must be finite, positive and at most 30 seconds")
            if self._thread is not None:
                raise RuntimeError("Heartbeat already started")
            self._heartbeat_interval = float(interval_seconds)
            self._thread = threading.Thread(target=self._heartbeat_loop,
                name="fbs-v052-progress", daemon=True)
            self._thread.start()

    def stop_heartbeat(self):
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
            if thread.is_alive():
                # Do not wait without a bound or kill somebody else's thread.
                raise self._failure(RuntimeError("Heartbeat output callback did not stop within two seconds"),
                                    "V052_PROGRESS_HEARTBEAT_STOP")
        self.check()

    def finish(self, status):
        _label(status, "invocation status")
        self.stop_heartbeat()
        with self._lock:
            self._require_running()
            if self._phase is not None:
                self.end_phase("STOPPED_WITHOUT_PHASE_COMPLETION")
            self._finished = self._now()
            self._run_status = status
            self._publish("V052_PROGRESS_INVOCATION_FINISHED", self._snapshot(self._finished))
            return self.receipt()

    def receipt(self):
        """Diagnostic snapshot; remains available if a journal/thread failed."""
        with self._lock:
            moment = self._finished if self._finished is not None else self._now()
            return _finite_json({"schema": SCHEMA, "run_id": self.run_id,
                "created_at_utc": self._created_at, "status": self._run_status,
                "elapsed_total_seconds": moment - self._started,
                "finished": self._finished is not None, "phases": self._phases,
                "active_phase": self._snapshot(moment) if self._phase is not None else None,
                "events_successfully_emitted": self._events,
                "reporting_failure_count": self._error_count,
                "reporting_failures": self._errors,
                "reporting_failures_omitted": self._error_count - len(self._errors),
                "heartbeat_thread_failure": self._thread_failure,
                "heartbeat_interval_seconds": self._heartbeat_interval,
                "counters_are_observed_phase_snapshots_not_cross_phase_totals": True,
                "scientific_units_created_by_observation": 0,
                "whole_invocation_eta_seconds": None})
