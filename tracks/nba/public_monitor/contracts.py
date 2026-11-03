"""Small, invented examples of forecast admission, not private NBA models.

The module has no third-party dependencies, network calls, model loading, or
real forecast data. It demonstrates information-time and accounting contracts.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path


def timestamp(value: str) -> datetime:
    """Require an explicit timezone; normalize to UTC before comparison."""
    if not isinstance(value, str):
        raise ValueError("an ISO timestamp with timezone is required")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid ISO timestamp") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone is required")
    return result.astimezone(timezone.utc)


def number(value, *, lower=None, upper=None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite numeric observation required")
    if lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError("observation outside its allowed range")
    return float(value)


def admit_forecast(row: dict) -> dict:
    """Validate a toy immutable issue against the stated information cutoff.

    A declared horizon is not evidence that issuance actually happened at that
    horizon. The returned timing label makes that distinction explicit.
    """
    if row.get("data_kind") != "INVENTED":
        raise ValueError("this public demonstration accepts invented data only")
    for field in ("event", "model_version", "issue_id", "side", "settlement"):
        if not isinstance(row.get(field), str) or not row[field]:
            raise ValueError("missing issue identity")
    if row.get("track") not in {"frozen", "rolling"}:
        raise ValueError("frozen and rolling tracks must be explicit")
    if row.get("target") != "winner" or row["side"] != "home":
        raise ValueError("toy example requires home-side winner probabilities")
    if type(row.get("horizon_minutes")) is not int or row["horizon_minutes"] not in {60, 120}:
        raise ValueError("declare a supported pregame cutoff")
    tip = timestamp(row["tip_at"])
    cutoff = timestamp(row["cutoff_at"])
    issue = timestamp(row["issued_at"])
    if (tip - cutoff).total_seconds() != row["horizon_minutes"] * 60:
        raise ValueError("cutoff does not match the declared horizon")
    if issue > cutoff:
        raise ValueError("late issue cannot become a pre-cutoff forecast")
    published = timestamp(row["source_published_at"])
    possessed = timestamp(row["source_possessed_at"])
    if published > possessed or possessed > issue:
        raise ValueError("source version was not possessed before issue")
    number(row["probability"], lower=0, upper=1)
    return dict(row, issue_timing="AT_DECLARED_CUTOFF" if issue == cutoff else "EARLY_OUTLOOK")


def issue_union(previous: list[dict], fresh: list[dict]) -> list[dict]:
    """Keep every original version; exact repeats reuse, changed bytes reject."""
    issues = {}
    for row in previous + fresh:
        admit_forecast(row)
        identity = row["issue_id"]
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if identity in issues and issues[identity][0] != canonical:
            raise ValueError("an immutable issue was changed")
        issues[identity] = (canonical, row)
    return [issues[key][1] for key in sorted(issues)]


def merge_results(previous: list[dict], fresh: list[dict]) -> list[dict]:
    """Absence in a later response cannot delete a previously held final.

    Corrections are not silently chosen: a conflicting final must be reviewed
    separately and versioned before a new scoring snapshot is admitted.
    """
    results = {}
    for row in previous + fresh:
        if row.get("data_kind") != "INVENTED" or not row.get("event"):
            raise ValueError("invented, identified final required")
        if row.get("official_final") is not True or type(row.get("home_win")) is not int or row["home_win"] not in {0, 1}:
            raise ValueError("qualified binary official final required")
        if timestamp(row["published_at"]) > timestamp(row["possessed_at"]):
            raise ValueError("impossible final possession order")
        event = row["event"]
        if event in results:
            old = results[event]
            if old["home_win"] != row["home_win"]:
                raise ValueError("conflicting final needs a versioned correction")
            # Keep the earliest *actual* possession, not an inferred finish time.
            if timestamp(old["possessed_at"]) <= timestamp(row["possessed_at"]):
                continue
        results[event] = dict(row)
    return [results[key] for key in sorted(results)]


def eligible_update_results(results: list[dict], fit_started_at: str) -> list[dict]:
    """Only previously possessed finals may inform a toy rolling update."""
    cutoff = timestamp(fit_started_at)
    return [row for row in merge_results([], results) if timestamp(row["possessed_at"]) < cutoff]


def frozen_parameters_unchanged(before: dict, after: dict) -> bool:
    """The frozen control is a distinct object, not overwritten by an update."""
    if before != after:
        raise ValueError("frozen control parameters changed")
    return True


def score_issues(issues: list[dict], results: list[dict], as_of: str) -> dict:
    """Score each model/event once; preserve all versions outside this view.

    Duplicate versions for the same model/event require an explicit selection
    policy. This small demo rejects ambiguity instead of choosing after results.
    """
    clock = timestamp(as_of)
    held = {row["event"]: row for row in merge_results([], results)
            if timestamp(row["possessed_at"]) <= clock}
    scored, seen = [], set()
    for row in issue_union([], issues):
        issue = admit_forecast(row)
        key = (issue["event"], issue["model_version"], issue["track"])
        if key in seen:
            raise ValueError("multiple versions require a predeclared issue policy")
        seen.add(key)
        if timestamp(issue["issued_at"]) > clock:
            raise ValueError("future issue relative to scoring clock")
        result = held.get(issue["event"])
        if result is None:
            continue
        if timestamp(result["published_at"]) <= timestamp(issue["tip_at"]):
            raise ValueError("a final result cannot predate the invented game")
        p = issue["probability"]
        y = result["home_win"]
        clipped = min(1 - 1e-15, max(1e-15, p))
        scored.append({"event": issue["event"], "model_version": issue["model_version"],
                       "track": issue["track"], "correct": int((p >= 0.5) == bool(y)),
                       "brier": (p - y) ** 2,
                       "log_loss": -(y * math.log(clipped) + (1 - y) * math.log1p(-clipped))})
    groups = {}
    for row in scored:
        groups.setdefault((row["model_version"], row["track"]), []).append(row)
    metrics = [{"model_version": model, "track": track, "n": len(rows),
                "correct": sum(r["correct"] for r in rows),
                "accuracy": sum(r["correct"] for r in rows) / len(rows),
                "brier": sum(r["brier"] for r in rows) / len(rows),
                "log_loss": sum(r["log_loss"] for r in rows) / len(rows)}
               for (model, track), rows in sorted(groups.items())]
    return {"data_kind": "INVENTED", "scored_rows": scored, "metrics": metrics}


def match_products(model: dict, market: dict) -> bool:
    """Require the same question; an unmatched provider is not a loss or zero."""
    fields = ("event", "side", "target", "line", "horizon_minutes", "settlement", "product")
    if any(field not in model or field not in market for field in fields):
        raise ValueError("complete product identity required")
    if any(model[field] != market[field] for field in fields):
        return False
    cutoff = timestamp(model["cutoff_at"])
    quote = timestamp(market["quoted_at"])
    possession = timestamp(market["possessed_at"])
    if quote > possession:
        raise ValueError("impossible quote possession order")
    return quote <= cutoff and possession <= cutoff


def paper_decision(*, probability, decimal_odds=None, fees=None,
                   executable_depth=None, settlement_verified=False) -> dict:
    """One-unit educational arithmetic only; incomplete evidence means NO BET.

    It is not a staking policy. The demonstration always allocates zero.
    """
    number(probability, lower=0, upper=1)
    if decimal_odds is None or fees is None or executable_depth is None or not settlement_verified:
        return {"decision": "NO BET", "unit_expected_value": None, "historical_pnl": None,
                "allocation": 0, "reason": "missing executable-price evidence"}
    number(decimal_odds, lower=1)
    number(fees, lower=0)
    number(executable_depth, lower=0)
    if executable_depth < 1:
        return {"decision": "NO BET", "unit_expected_value": None, "historical_pnl": None,
                "allocation": 0, "reason": "insufficient executable depth"}
    expected = probability * decimal_odds - 1 - fees
    return {"decision": "HYPOTHETICAL POSITIVE EV" if expected > 0 else "NO BET",
            "unit_expected_value": expected, "historical_pnl": None,
            "allocation": 0, "reason": "invented one-unit arithmetic; no orders or staking recommendation"}


def owner_accounting(planned: int, completed_ids: list[str], owner_exit: int | None,
                     publication_verified: bool) -> dict:
    if type(planned) is not int or planned < 0:
        raise ValueError("nonnegative planned count required")
    if len(set(completed_ids)) != len(completed_ids) or len(completed_ids) > planned:
        raise ValueError("duplicate or excessive completed work")
    if owner_exit is not None and (type(owner_exit) is not int or owner_exit < 0):
        raise ValueError("owner exit must be an observed integer or unknown")
    complete = owner_exit == 0 and publication_verified and len(completed_ids) == planned
    return {"planned": planned, "completed": len(completed_ids), "new_credit_on_reuse": 0,
            "owner_status": "COMPLETED" if complete else "FAILED_OR_PARTIAL",
            "publication_verified": publication_verified}


def walkthrough() -> dict:
    fixtures = json.loads(Path(__file__).with_name("fixtures.json").read_text())
    original = fixtures["previous_results"]
    fresh = fixtures["fresh_results"]
    combined = merge_results(original, fresh)
    issues = issue_union([], fixtures["issues"])
    return {"data_kind": "INVENTED", "network_requests": 0, "real_fits": 0,
            "previous_finals": len(original), "fresh_finals": len(fresh),
            "loss_preserved_after_refresh": any(row["event"] == "invented-01" and row["home_win"] == 0 for row in combined),
            "qualified_union_finals": len(combined),
            "toy_scores": score_issues(issues, combined, "2035-11-03T12:00:00Z"),
            "eligible_update_outcomes": len(eligible_update_results(combined, "2035-11-02T12:00:00Z")),
            "missing_market": paper_decision(probability=0.6),
            "partial_owner": owner_accounting(3, ["invented-fit-a", "invented-fit-b", "invented-fit-c"], 2, False)}
