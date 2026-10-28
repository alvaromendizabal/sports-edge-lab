"""Invented offline workflow: research, reference serving and paper readiness are separate.

No sports observations, private model implementation, network calls or order API.
Reference rows are examples; "SERVED" means a validated synthetic output artifact.
This is exception isolation inside one process, not a process-crash supervisor.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from datetime import datetime
from typing import Callable


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def clock(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an explicit UTC string")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp must be UTC")
    return t


def reference_slate(rows, *, decision_time, policy):
    """Fail closed on invalid input; never select using research results or outcomes."""
    now = clock(decision_time)
    if policy != {"id": "invented-frozen-market-v1", "type": "MARKET_REFERENCE", "historical_qualification": "NO_LEARNED_QUALIFIER"}:
        raise ValueError("unknown frozen policy")
    forecasts = []
    seen = set()
    for row in rows:
        if set(row) != {"game", "market_probability", "observed_at", "kickoff"}:
            raise ValueError("only outcome-free fixture fields allowed")
        p = row["market_probability"]
        if isinstance(p, bool) or not isinstance(p, (float, int)) or not math.isfinite(p) or not 0 < p < 1:
            raise ValueError("invalid reference probability")
        age = (now - clock(row["observed_at"])).total_seconds()
        if not 0 <= age <= 600 or clock(row["kickoff"]) <= now:
            raise ValueError("inadmissible fixture clocks")
        if not isinstance(row["game"], str) or not row["game"] or row["game"] in seen:
            raise ValueError("invalid or duplicate fixture identity")
        seen.add(row["game"])
        forecasts.append({"game": row["game"], "probability": p,
                          "classification": "SYNTHETIC_MARKET_REFERENCE", "learned_edge": None,
                          "decision_time": decision_time, "policy_sha256": identity(policy)})
    if not forecasts:
        raise ValueError("no admissible fixture rows")
    return {"status": "SERVED", "forecasts": forecasts, "policy_sha256": identity(policy), "fresh_real_forecasts": 0}


def pipeline(research: Callable[[], dict], rows, *, decision_time, policy):
    """A failed callback cannot skip reference serving; paper eligibility stays separate.

    Catch ordinary callback errors, preserving their type without leaking error text.
    Real process death, memory exhaustion and external storage require stronger isolation.
    """
    frozen = copy.deepcopy(policy)
    reference_rows = copy.deepcopy(rows)
    try:
        research_result = research()
        if not isinstance(research_result, dict) or research_result.get("status") != "COMPLETED":
            raise ValueError("research did not produce a completion receipt")
        research_state = {"status": "COMPLETED", "selection_changed": False}
    except Exception as error:
        research_state = {"status": "FAILED", "error_type": type(error).__name__, "selection_changed": False}
    try:
        serving = reference_slate(reference_rows, decision_time=decision_time, policy=frozen)
    except Exception as error:
        serving = {"status": "BLOCKED", "error_type": type(error).__name__, "forecasts": [], "fresh_real_forecasts": 0}
    execution = {"status": "NOT_ELIGIBLE", "reason": "No independently qualified model edge or executable venue evidence in this fixture.",
                 "actual_orders": 0, "paper_stake": 0, "profit": None}
    return {"evidence": "INVENTED_OFFLINE_DEMONSTRATION", "research": research_state,
            "serving": serving, "execution": execution}


def walkthrough(scenario="research_failure"):
    if scenario not in {"research_failure", "research_complete", "stale_reference", "future_reference"}:
        raise ValueError("unknown scenario")
    policy = {"id": "invented-frozen-market-v1", "type": "MARKET_REFERENCE", "historical_qualification": "NO_LEARNED_QUALIFIER"}
    rows = [{"game": "Invented Amber vs Indigo", "market_probability": 0.57,
             "observed_at": "2030-01-01T12:00:00Z", "kickoff": "2030-01-01T15:00:00Z"},
            {"game": "Invented Cedar vs Silver", "market_probability": 0.46,
             "observed_at": "2030-01-01T12:01:00Z", "kickoff": "2030-01-01T18:00:00Z"}]
    if scenario == "stale_reference": rows[0]["observed_at"] = "2030-01-01T11:00:00Z"
    if scenario == "future_reference": rows[0]["observed_at"] = "2030-01-01T12:06:00Z"
    def research():
        if scenario != "research_complete": raise ArithmeticError("invented certificate rejection")
        return {"status": "COMPLETED"}
    return pipeline(research, rows, decision_time="2030-01-01T12:05:00Z", policy=policy)


if __name__ == "__main__":
    print(json.dumps({name: walkthrough(name) for name in ("research_failure", "research_complete", "stale_reference", "future_reference")}, indent=2))
