"""Invented, credential-free examples of inherited authority and fold isolation.

The caller supplies authenticated original receipt pins. Hashes do not establish
consent by themselves. No real approval, source archive, model or request is used.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from .recovery_plan import Budget, Quota, QuotaJournal, SnapshotRequest, digest, integer, pin

SCHEMA = "public.continuation.v1"


def inherit_authority(original, window, successor_sha256, *, authorization_pin, window_pin):
    """Keep original consent and its original counter baseline unmodified.

    The two expected pins must come from an independently authenticated source;
    this demonstration cannot authenticate an owner or a subscription account.
    """
    pin(successor_sha256); pin(authorization_pin); pin(window_pin)
    if digest(original) != authorization_pin or digest(window) != window_pin:
        raise ValueError("authenticated original authorization or window changed")
    if original.get("approved") is not True or original.get("paid_approved") is not True:
        raise ValueError("both original approvals must be explicit")
    pin(original["source_sha256"])
    if original["source_sha256"] == successor_sha256:
        raise ValueError("continuation requires a distinct source identity")
    if window.get("authorization_sha256") != authorization_pin:
        raise ValueError("original window belongs to different authority")
    limits = deepcopy(original["cumulative_limits"])
    if not limits or set(limits) & set(original["window_limits"]):
        raise ValueError("distinct cumulative and original-window limits required")
    if set(window["counters_before_release"]) != set(original["window_limits"]):
        raise ValueError("original baseline must cover exactly the window counters")
    for name, value in limits.items():
        integer(value)
    for name, allowance in original["window_limits"].items():
        integer(allowance); integer(window["counters_before_release"][name])
        limits[name] = window["counters_before_release"][name] + allowance
    return {"schema": SCHEMA, "source_sha256": successor_sha256,
        "authority": "inherited_original_consent", "additional_allowance": 0,
        "authorization_sha256": authorization_pin, "window_sha256": window_pin,
        "original_authorization": deepcopy(original), "original_window": deepcopy(window),
        "absolute_limits": limits}


def validate_continuation(receipt, source_sha256, *, authorization_pin, window_pin):
    expected = inherit_authority(receipt["original_authorization"], receipt["original_window"],
        source_sha256, authorization_pin=authorization_pin, window_pin=window_pin)
    if digest(receipt) != digest(expected):
        raise ValueError("continuation identity, allowance or original baseline changed")
    return expected


def remaining(receipt, cumulative_usage, *, source_sha256, authorization_pin, window_pin):
    validated = validate_continuation(receipt, source_sha256,
        authorization_pin=authorization_pin, window_pin=window_pin)
    limits = validated["absolute_limits"]
    if set(cumulative_usage) != set(limits):
        raise ValueError("complete cumulative counters required; missing is not zero")
    result = {}
    for name, maximum in limits.items():
        value = cumulative_usage[name]; integer(value)
        baseline = validated["original_window"]["counters_before_release"].get(name, 0)
        if value < baseline or value > maximum:
            raise ValueError("counter reset or cumulative ceiling exceeded")
        result[name] = maximum - value
    return result


def active_floor(measured, reservation, *, verified_closed_seconds=None, adopted_floor=None):
    """Illustrate conservative carry; only an externally verified closure may resolve it.

    Identity/attempt/clock verification belongs to the receipt verifier. The
    numeric argument is not itself evidence that a matching closure exists.
    Once adopted, a floor is monotonic even if a lower closure arrives later.
    """
    integer(measured); integer(reservation)
    if reservation < measured:
        raise ValueError("reservation precedes measured work")
    candidate = reservation
    if verified_closed_seconds is not None:
        integer(verified_closed_seconds)
        if verified_closed_seconds < measured:
            raise ValueError("closure cannot erase measured work")
        candidate = verified_closed_seconds
    if adopted_floor is not None:
        integer(adopted_floor); candidate = max(candidate, adopted_floor)
    return candidate


class InsufficientSupport(ValueError):
    """A declared support gate blocked this fold; identity errors are different."""


@dataclass(frozen=True)
class Fold:
    name: str
    experiment_sha256: str
    cohort_sha256: str
    calibration_count: int
    minimum_calibration: int

    def __post_init__(self):
        if self.name not in {"nba-A", "nba-B", "college-men-A", "college-women-A"}:
            raise ValueError("explicit invented fold namespace required")
        pin(self.experiment_sha256); pin(self.cohort_sha256)
        integer(self.calibration_count); integer(self.minimum_calibration, positive=True)

    @property
    def identity(self):
        return digest(self.__dict__)


def prepare_fold(fold):
    if fold.calibration_count < fold.minimum_calibration:
        raise InsufficientSupport("insufficient_calibration_support")
    return {"fold_sha256": fold.identity, "eligible": True}


def isolate_folds(folds, *, prepare=prepare_fold):
    """Independent preflight only: no fitting, threshold change or blanket catch."""
    folds = tuple(folds)
    if len({fold.name for fold in folds}) != len(folds):
        raise ValueError("duplicate registered fold")
    results = []
    for fold in folds:
        try:
            prepared = prepare(fold)
        except InsufficientSupport as exc:
            results.append({"fold": fold.name, "fold_sha256": fold.identity,
                "status": "BLOCKED_SUPPORT", "reason": str(exc)})
            continue
        if prepared.get("fold_sha256") != fold.identity or prepared.get("eligible") is not True:
            raise ValueError("prepared cohort identity changed")
        results.append({"fold": fold.name, "fold_sha256": fold.identity,
            "status": "ELIGIBLE_PREFLIGHT", "model_execution_claimed": False})
    return results


def fixture_authority():
    original = {"approved": True, "paid_approved": True,
        "source_sha256": digest({"invented_source": "A"}),
        "cumulative_limits": {"active_seconds": 600, "public_requests": 20,
            "provider_requests": 4, "provider_credits": 100},
        "window_limits": {"archive_pages": 12}}
    window = {"authorization_sha256": digest(original), "counters_before_release": {"archive_pages": 3}}
    return original, window


def walkthrough():
    original, window = fixture_authority()
    auth_pin, window_pin = digest(original), digest(window)
    source = digest({"invented_source": "B"})
    receipt = inherit_authority(original, window, source, authorization_pin=auth_pin, window_pin=window_pin)
    floor = active_floor(310, 340)
    usage = {"active_seconds": floor, "public_requests": 7, "provider_requests": 0,
        "provider_credits": 0, "archive_pages": 11}
    headroom = remaining(receipt, usage, source_sha256=source, authorization_pin=auth_pin, window_pin=window_pin)
    folds = [Fold(name, digest({"invented_protocol": "fixed"}), digest({"invented_cohort": name}), count, 10)
        for name, count in (("nba-A", 7), ("college-men-A", 25), ("college-women-A", 23))]
    # The original authority pin persists in the existing journal across code releases.
    budget = Budget(4, 0, 100, 0, auth_pin)
    request = SnapshotRequest("basketball_nba", "2025-01-01T19:00:00Z", ("h2h",), ("us",))
    quota = Quota(100, "2026-10-28T20:00:00Z", digest({"invented_quota": 100}))
    with tempfile.TemporaryDirectory() as directory:
        journal_path = Path(directory) / "invented-quota.jsonl"
        QuotaJournal(journal_path, budget).reserve("invented-attempt", request, quota, quota.observed_at)
        # Reopen without a completion: the request and full credit ceiling remain debited.
        resumed = QuotaJournal(journal_path, budget)
        interrupted_state = resumed.state()
        resumed.complete("invented-attempt", 0, digest({"invented_empty_response": []}), "2026-10-28T20:00:01Z")
        completed_state = resumed.state()
    return {"synthetic": True, "actual_requests": 0, "actual_provider_credits": 0,
        "actual_model_fits": 0, "purpose": "invented contract example; no owner execution",
        "continuation": receipt, "remaining": headroom, "folds": isolate_folds(folds),
        "journal_after_lost_response": interrupted_state, "journal_after_zero_credit_receipt": completed_state}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, sort_keys=True))
