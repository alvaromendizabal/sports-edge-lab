"""Credential-free acquisition contracts using invented inputs only.

This module demonstrates compatible batch planning, selective recovery and a
performance gate. It is not the private owner executable, a provider entitlement
check, a network benchmark or a source-authentication service.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable, Mapping


class QualificationError(ValueError):
    """Evidence or identity is insufficient for the requested operation."""


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise QualificationError(f"{name} must be an integer >= {minimum}")
    return value


def _number(value, name, minimum=0.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QualificationError(f"{name} must be a finite number")
    if not math.isfinite(value) or value < minimum:
        raise QualificationError(f"{name} must be a finite number >= {minimum}")
    return float(value)


@dataclass(frozen=True)
class Window:
    provider: str
    access_mode: str
    route: str
    item_id: str
    lower: int
    upper: int
    period_seconds: int
    supports_batch: bool = True

    def __post_init__(self):
        for key in ("provider", "access_mode", "route", "item_id"):
            if not isinstance(getattr(self, key), str) or not getattr(self, key):
                raise QualificationError(f"Missing {key}")
        _integer(self.lower, "lower")
        _integer(self.upper, "upper")
        _integer(self.period_seconds, "period_seconds", 1)
        if self.upper < self.lower or type(self.supports_batch) is not bool:
            raise QualificationError("Invalid window or batching capability")

    @property
    def compatibility(self):
        return (self.provider, self.access_mode, self.route, self.lower,
                self.upper, self.period_seconds, self.supports_batch)

    @property
    def conservative_points(self):
        # Two endpoints account for unaligned interval edges. A larger single
        # item must first be split by a separately validated window planner.
        return math.ceil((self.upper - self.lower) / self.period_seconds) + 2


def plan_batches(windows: Iterable[Window], *, item_limit: int,
                 response_point_limit: int) -> list[tuple[Window, ...]]:
    """Group exact-compatible windows without changing any input boundary."""
    _integer(item_limit, "item_limit", 1)
    _integer(response_point_limit, "response_point_limit", 1)
    groups, identities = {}, set()
    for window in windows:
        key = (window.provider, window.access_mode, window.route, window.item_id,
               window.lower, window.upper, window.period_seconds)
        if key in identities:
            raise QualificationError("Duplicate request identity")
        identities.add(key)
        if window.conservative_points > response_point_limit:
            raise QualificationError("Single-item window requires prior splitting")
        groups.setdefault(window.compatibility, []).append(window)
    batches = []
    for group in groups.values():
        bound = min(item_limit, response_point_limit // group[0].conservative_points)
        if not group[0].supports_batch:
            bound = 1
        ordered = sorted(group, key=lambda item: item.item_id)
        batches.extend(tuple(ordered[start:start + bound])
                       for start in range(0, len(ordered), bound))
    return batches


def recovery_partition(requested_ids: Iterable[str], records: Iterable[Mapping],
                       *, validate: Callable[[Mapping], bool]):
    """Preserve valid members and retry missing/invalid members only.

    Validation is a caller-supplied evidence check. This example makes no
    cryptographic authenticity assertion from a plain success flag. Duplicate or
    foreign identities quarantine the batch instead of selecting an arbitrary
    value. Original bodies and failure receipts belong in the caller's archive.
    """
    expected = tuple(requested_ids)
    if (not expected or any(not isinstance(x, str) or not x for x in expected)
            or len(set(expected)) != len(expected)):
        raise QualificationError("Requested identity set is invalid")
    observed = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise QualificationError("Response record is not an object")
        identity = record.get("item_id")
        if not isinstance(identity, str) or identity not in expected:
            raise QualificationError("Unexpected response identity")
        if identity in observed:
            raise QualificationError("Duplicate response identity")
        observed[identity] = record
    kept = {}
    retry = []
    for identity in expected:
        record = observed.get(identity)
        if record is not None and validate(record) is True:
            kept[identity] = record
        else:
            retry.append(identity)
    return {"verified_members": kept, "retry_ids": tuple(retry),
            "original_batch_evidence_must_be_preserved": True}


@dataclass(frozen=True)
class Measurement:
    environment: str
    workers: int
    elapsed_seconds: float
    verified_contracts: int
    requests: int
    tickers_requested: int
    s3_operations: int
    http_429: int
    http_5xx: int
    integrity_failures: int
    peak_requests_per_second: float
    request_latencies_seconds: tuple[float, ...]
    attributed_cost_usd: float | None = None

    def __post_init__(self):
        if self.environment not in {"synthetic", "local_replay", "provider_and_canonical_storage"}:
            raise QualificationError("Unknown measurement environment")
        _integer(self.workers, "workers", 1)
        for name in ("verified_contracts", "requests", "tickers_requested", "s3_operations",
                     "http_429", "http_5xx", "integrity_failures"):
            _integer(getattr(self, name), name)
        if _number(self.elapsed_seconds, "elapsed_seconds") <= 0:
            raise QualificationError("Elapsed time must be positive")
        _number(self.peak_requests_per_second, "peak_requests_per_second")
        if len(self.request_latencies_seconds) != self.requests:
            raise QualificationError("Every attempted request needs its latency")
        for value in self.request_latencies_seconds:
            _number(value, "request latency")
        if self.http_429 + self.http_5xx > self.requests:
            raise QualificationError("Provider error count exceeds request count")
        if self.attributed_cost_usd is not None:
            _number(self.attributed_cost_usd, "attributed_cost_usd")

    def metrics(self):
        latencies = sorted(self.request_latencies_seconds)
        def percentile(q):
            if not latencies:
                return None
            position = (len(latencies) - 1) * q
            lower = int(position)
            upper = min(lower + 1, len(latencies) - 1)
            return latencies[lower] + (latencies[upper] - latencies[lower]) * (position - lower)
        return {
            "verified_contracts_per_second": self.verified_contracts / self.elapsed_seconds,
            "requests_per_second": self.requests / self.elapsed_seconds,
            "tickers_per_request": self.tickers_requested / self.requests if self.requests else None,
            "s3_operations_per_verified_contract": self.s3_operations / self.verified_contracts if self.verified_contracts else None,
            "http_429": self.http_429, "http_5xx": self.http_5xx,
            "p50_request_seconds": percentile(.5), "p95_request_seconds": percentile(.95),
            "cost_per_verified_contract_usd": self.attributed_cost_usd / self.verified_contracts
                if self.attributed_cost_usd is not None and self.verified_contracts else None,
        }


def full_run_decision(sample: Measurement, *, active_prior_owner: bool,
                      fresh_resource_admission: bool, provider_mode_authorized: bool,
                      permitted_peak_requests_per_second: float | None,
                      admitted_workers: int, target_contracts_per_second=10.0):
    """Require measured completion, resource/ownership admission and rate authority."""
    for name, value in (("active_prior_owner", active_prior_owner),
                        ("fresh_resource_admission", fresh_resource_admission),
                        ("provider_mode_authorized", provider_mode_authorized)):
        if type(value) is not bool:
            raise QualificationError(f"{name} must be an explicit boolean")
    _integer(admitted_workers, "admitted_workers")
    target = _number(target_contracts_per_second, "target_contracts_per_second")
    if target <= 0:
        raise QualificationError("Target must be positive")
    if permitted_peak_requests_per_second is not None:
        _number(permitted_peak_requests_per_second, "permitted provider peak")
    reasons = []
    if active_prior_owner:
        reasons.append("ACTIVE_PRIOR_OWNER")
    if not fresh_resource_admission or admitted_workers < sample.workers:
        reasons.append("RESOURCE_ADMISSION_UNQUALIFIED")
    if not provider_mode_authorized or permitted_peak_requests_per_second is None:
        reasons.append("PROVIDER_MODE_OR_LIMIT_UNQUALIFIED")
    elif sample.peak_requests_per_second > permitted_peak_requests_per_second:
        reasons.append("PROVIDER_RATE_EXCEEDS_AUTHORIZED_BUDGET")
    if sample.environment != "provider_and_canonical_storage":
        reasons.append("BENCHMARK_ENVIRONMENT_UNQUALIFIED")
    if sample.integrity_failures:
        reasons.append("INTEGRITY_FAILURES")
    if sample.http_429 or sample.http_5xx:
        reasons.append("PROVIDER_ERRORS_REQUIRE_REASSESSMENT")
    metrics = sample.metrics()
    if metrics["verified_contracts_per_second"] < target:
        reasons.append("VERIFIED_THROUGHPUT_TARGET_NOT_REACHED")
    return {"decision": "GO" if not reasons else "NO_GO", "reasons": reasons,
            "metrics": metrics, "full_run_speed_guaranteed": False,
            "qualification_scope": "THIS_MEASURED_SAMPLE_AND_RESOURCE_ADMISSION_ONLY"}
