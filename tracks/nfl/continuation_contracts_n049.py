"""Invented, credential-free examples of three continuation boundaries.

These functions demonstrate metadata admission only. They do not run the private
owner pipeline, fetch source data, fit a model, or turn a reference into a wager.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone


def _require(value, message):
    if not value:
        raise ValueError(message)


def _instant(value):
    _require(isinstance(value, str), "An explicit timestamp is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid timestamp") from error
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
             "A timezone is required")
    return parsed.astimezone(timezone.utc)


def classify_event_reports(events, acquired_at):
    """Retain every event while isolating known timing failures per event.

    Capture time is never backdated to a page's publication time. Passing this
    source check does not establish feature completeness or model readiness.
    Malformed identities or clocks remain errors rather than temporal exclusions.
    """
    captured = _instant(acquired_at)
    _require(isinstance(events, list), "Events must be a list")
    seen, result = set(), []
    for event in events:
        _require(isinstance(event, dict) and set(event) == {
            "event_id", "kickoff_at", "decision_at", "published_at"
        }, "Unexpected event metadata")
        identity = event["event_id"]
        _require(isinstance(identity, str) and identity and identity not in seen,
                 "Event identities must be present and unique")
        seen.add(identity)
        kickoff = _instant(event["kickoff_at"])
        decision = _instant(event["decision_at"])
        _require(decision < kickoff, "The decision must precede kickoff")
        published = None if event["published_at"] is None else _instant(event["published_at"])
        _require(published is None or published <= captured,
                 "Publication cannot follow the captured source")
        if captured >= kickoff:
            status = "NON_PREGAME_TEMPORAL_EXCLUSION"
        elif published is None:
            status = "UNVERIFIED_PUBLICATION_CLOCK"
        elif max(published, captured) > decision:
            status = "AFTER_DECISION_EXCLUSION"
        else:
            status = "SOURCE_AVAILABLE_BY_DECISION"
        result.append({**event, "acquired_at": acquired_at, "status": status})
    return result


def verify_completion_reentry(receipt, expected_identity, payload):
    """Admit exact, complete invented work for reuse without writing anything.

    The caller supplies all identity fields it requires. Their whole mapping,
    including unknown extra fields, must match. A valid payload hash alone does
    not prove that another study, input version, or algorithm is interchangeable.
    """
    _require(isinstance(expected_identity, dict) and bool(expected_identity),
             "An expected identity is required")
    _require(isinstance(receipt, dict) and set(receipt) == {
        "schema", "identity", "status", "payload"
    }, "Unexpected completion metadata")
    _require(receipt["schema"] == "public-completion-example.v1", "Unknown schema")
    _require(receipt["status"] == "COMPLETE", "Incomplete work cannot be reused")
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    _require(canonical(receipt["identity"]) == canonical(expected_identity),
             "Completion identity differs")
    _require(type(payload) is bytes, "Physical bytes are required")
    _require(isinstance(receipt["payload"], dict) and
             type(receipt["payload"].get("bytes")) is int,
             "A typed physical byte count is required")
    physical = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    _require(receipt["payload"] == physical, "Completed payload differs")
    return {"status": "VERIFIED_REUSE", "new_work_units": 0, "payload": physical}


def oriented_threshold_metadata(*, above, equal, below, orientation, settlement):
    """Orient raw and conditional probability metadata to the same predicate.

    STRICT means equality loses; VOID_EQUALITY means equality is excluded from
    scoring. Unknown settlement can retain descriptive predicate probabilities,
    but it never produces a scoring probability or executable-quote claim.
    """
    masses = (above, equal, below)
    _require(all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1
                 for x in masses), "Invalid probability mass")
    _require(abs(sum(masses) - 1) <= 1e-12, "Probability mass must sum to one")
    _require(orientation in {"GREATER_THAN", "LESS_THAN"}, "Unknown orientation")
    _require(settlement in {"STRICT", "VOID_EQUALITY", "UNKNOWN"},
             "Unknown settlement policy")
    numerator = above if orientation == "GREATER_THAN" else below
    conditional = numerator / (1 - equal) if equal < 1 else None
    scoring = (numerator if settlement == "STRICT" else
               conditional if settlement == "VOID_EQUALITY" else None)
    return {
        "orientation": orientation,
        "settlement": settlement,
        "probability_of_predicate": numerator,
        "probability_equal": equal,
        "probability_conditional_on_non_equality": conditional,
        "scoring_probability": scoring,
        "scoring_eligible": scoring is not None,
        "executable_quote_claimed": False,
    }
