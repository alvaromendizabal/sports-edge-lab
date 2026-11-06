"""Invented spread probability and ATS records with explicit clocks and settlement.

This public example is independent of private production models and feeds. It
does not estimate a real game's distribution, fit a model, or submit an order.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import json


class ContractError(ValueError):
    """An input cannot support the requested comparison."""


def clock(value: str | None) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("MISSING_CLOCK")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("INVALID_CLOCK") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ContractError("CLOCK_WITHOUT_TIMEZONE")
    return result.astimezone(timezone.utc)


def half_point(value: str) -> Decimal:
    """Use exact decimal arithmetic; a rounded margin must never create a push."""
    if not isinstance(value, str):
        raise ContractError("SPREAD_MUST_BE_EXACT_DECIMAL_TEXT")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ContractError("INVALID_SPREAD") from exc
    if not result.is_finite() or result * 2 != (result * 2).to_integral_value():
        raise ContractError("UNSUPPORTED_SPREAD_INCREMENT")
    return result


@dataclass(frozen=True)
class Reference:
    game: str
    league: str
    home: str
    away: str
    provider: str
    product: str
    tipoff: str
    horizon_minutes: int
    settlement: str = "FULL_GAME_WITH_OVERTIME"


@dataclass(frozen=True)
class Quote:
    reference: Reference
    home_spread: str
    quote_at: str | None
    source_available_at: str | None
    captured_at: str | None
    source_version_verified: bool


def validate_quote(quote: Quote, reference: Reference, tier: str) -> datetime:
    if quote.reference != reference:
        raise ContractError("REFERENCE_IDENTITY_MISMATCH")
    if reference.league not in {"ncaam", "ncaaw"}:
        raise ContractError("UNSUPPORTED_LEAGUE")
    if not reference.game or not reference.home or not reference.away or reference.home == reference.away:
        raise ContractError("INCOMPLETE_GAME_BINDING")
    if reference.provider not in {"Kalshi", "Polymarket", "DraftKings"}:
        raise ContractError("UNSUPPORTED_PROVIDER")
    products = {"US", "INTERNATIONAL"} if reference.provider == "Polymarket" else {"US"}
    if reference.product not in products:
        raise ContractError("UNSUPPORTED_PRODUCT")
    if reference.settlement != "FULL_GAME_WITH_OVERTIME":
        raise ContractError("INCOMPATIBLE_SETTLEMENT")
    if type(reference.horizon_minutes) is not int or reference.horizon_minutes not in {0, 60, 120}:
        raise ContractError("UNREGISTERED_HORIZON")
    if tier not in {"CAPTURED_BEFORE_CUTOFF", "SOURCE_SUPPORTED_RECONSTRUCTION"}:
        raise ContractError("UNSUPPORTED_EVIDENCE_TIER")
    half_point(quote.home_spread)
    cutoff = clock(reference.tipoff) - timedelta(minutes=reference.horizon_minutes)
    quoted, available = clock(quote.quote_at), clock(quote.source_available_at)
    if available < quoted:
        raise ContractError("IMPOSSIBLE_SOURCE_CLOCK_ORDER")
    if quote.source_version_verified is not True:
        raise ContractError("UNVERIFIED_SOURCE_VERSION")
    if quoted >= cutoff or available >= cutoff:
        raise ContractError("QUOTE_NOT_AVAILABLE_BEFORE_CUTOFF")
    if tier == "CAPTURED_BEFORE_CUTOFF":
        captured = clock(quote.captured_at)
        if captured < available:
            raise ContractError("IMPOSSIBLE_CAPTURE_CLOCK_ORDER")
        if captured >= cutoff:
            raise ContractError("NOT_CAPTURED_BEFORE_CUTOFF")
    return cutoff


def probability_at_spread(mass, quote: Quote, reference: Reference,
                          model_available_at: str | None,
                          tier="CAPTURED_BEFORE_CUTOFF") -> dict:
    """Partition a supplied home-minus-away margin distribution without fitting.

    The caller must establish that the distribution is a valid, calibrated model
    artifact. Passing this arithmetic contract does not establish calibration.
    """
    cutoff = validate_quote(quote, reference, tier)
    if clock(model_available_at) >= cutoff:
        raise ContractError("MODEL_NOT_AVAILABLE_BEFORE_CUTOFF")
    if not mass:
        raise ContractError("MISSING_MARGIN_DISTRIBUTION")
    points = []
    seen = set()
    for margin, probability in mass:
        if type(margin) is not int or margin in seen:
            raise ContractError("INVALID_OR_DUPLICATE_MARGIN")
        if not isinstance(probability, str):
            raise ContractError("MASS_MUST_BE_EXACT_RATIONAL_TEXT")
        try:
            p = Fraction(probability)
        except (ValueError, ZeroDivisionError) as exc:
            raise ContractError("INVALID_PROBABILITY_MASS") from exc
        if p < 0 or p > 1:
            raise ContractError("INVALID_PROBABILITY_MASS")
        seen.add(margin)
        points.append((margin, p))
    if sum((p for _, p in points), Fraction(0)) != 1:
        raise ContractError("PROBABILITY_MASS_DOES_NOT_SUM_TO_ONE")
    spread = half_point(quote.home_spread)
    parts = {key: Fraction(0) for key in ("cover", "push", "loss")}
    for margin, p in points:
        adjusted = Decimal(margin) + spread
        parts["cover" if adjusted > 0 else "loss" if adjusted < 0 else "push"] += p
    return {
        "home": {key: float(value) for key, value in parts.items()},
        "away": {"cover": float(parts["loss"]), "push": float(parts["push"]), "loss": float(parts["cover"])},
        "home_win_probability": float(sum((p for m, p in points if m > 0), Fraction(0))),
        "home_spread": str(spread),
        "away_spread": str(-spread),
        "evidence_tier": tier,
        "calibration_proved_by_this_calculation": False,
        "orders": 0,
    }


@dataclass(frozen=True)
class Result:
    quote: Quote
    home_score: int | None
    away_score: int | None
    completed_at: str | None
    result_available_at: str | None
    status: str = "COMPLETED"


def ats_record(results, *, team: str, target: Reference, target_cutoff: str,
               tier="CAPTURED_BEFORE_CUTOFF", venue="ALL", previous=None) -> dict:
    """Report an earlier-known team record for one provider/product/horizon/tier.

    Conflicting versions of the same earlier game are quarantined together.
    Exact repeated copies collapse. The win rate excludes pushes explicitly.
    There is no cross-provider best-line selection or invented missing label.
    """
    cutoff = clock(target_cutoff)
    if cutoff > clock(target.tipoff) - timedelta(minutes=target.horizon_minutes):
        raise ContractError("TARGET_CUTOFF_AFTER_DECLARED_HORIZON")
    if venue not in {"ALL", "HOME", "AWAY"}:
        raise ContractError("UNSUPPORTED_VENUE")
    if previous is not None and (type(previous) is not int or previous < 1):
        raise ContractError("INVALID_PREVIOUS_WINDOW")
    if team not in {target.home, target.away}:
        raise ContractError("TARGET_TEAM_MISMATCH")
    raw = list(results)
    unique = list(dict.fromkeys(raw))
    def game_contract(row):
        r = row.quote.reference
        return (r.game, r.league, r.provider, r.product, r.horizon_minutes, r.settlement)
    by_game = Counter(game_contract(row) for row in unique)
    excluded = Counter()
    eligible = []
    for result in unique:
        q = result.quote
        r = q.reference
        try:
            if by_game[game_contract(result)] > 1:
                raise ContractError("CONFLICTING_GAME_VERSIONS")
            if r.game == target.game:
                raise ContractError("TARGET_GAME_EXCLUDED")
            if (r.league, r.provider, r.product, r.horizon_minutes, r.settlement) != (target.league, target.provider, target.product, target.horizon_minutes, target.settlement):
                raise ContractError("COHORT_CONTRACT_MISMATCH")
            if team not in {r.home, r.away}:
                raise ContractError("TEAM_NOT_IN_GAME")
            if venue == "HOME" and team != r.home or venue == "AWAY" and team != r.away:
                raise ContractError("VENUE_NOT_IN_WINDOW")
            validate_quote(q, r, tier)
            if result.status != "COMPLETED":
                raise ContractError("UNSETTLED_OR_VOID_RESULT")
            if any(type(v) is not int or v < 0 for v in (result.home_score, result.away_score)):
                raise ContractError("MISSING_OR_INVALID_FINAL_SCORES")
            completed, known = clock(result.completed_at), clock(result.result_available_at)
            if completed <= clock(r.tipoff) or known < completed:
                raise ContractError("IMPOSSIBLE_RESULT_CLOCK_ORDER")
            if completed >= cutoff or known >= cutoff:
                raise ContractError("RESULT_NOT_KNOWN_BEFORE_TARGET")
            adjusted = Decimal(result.home_score - result.away_score) + half_point(q.home_spread)
            if team == r.away:
                adjusted = -adjusted
            eligible.append((completed, r.game, "win" if adjusted > 0 else "loss" if adjusted < 0 else "push"))
        except ContractError as exc:
            excluded[str(exc)] += 1
    eligible.sort(key=lambda x: (x[0], x[1]))
    before_window = len(eligible)
    if previous is not None:
        eligible = eligible[-previous:]
    counts = Counter(row[2] for row in eligible)
    decisions = counts["win"] + counts["loss"]
    return {
        "wins": counts["win"], "losses": counts["loss"], "pushes": counts["push"],
        "win_rate_excluding_pushes": counts["win"] / decisions if decisions else None,
        "decisive_denominator": decisions, "settled_record_denominator": len(eligible),
        "input_rows": len(raw), "distinct_input_rows": len(unique),
        "exact_duplicates_collapsed": len(raw) - len(unique),
        "eligible_before_window": before_window,
        "outside_previous_window": before_window - len(eligible),
        "excluded": dict(sorted(excluded.items())),
        "evidence_tier": tier, "venue": venue, "previous": previous,
        "future_cover_probability": None, "profit": None, "orders": 0,
    }


def demo():
    target = Reference("invented-next", "ncaam", "HOME", "AWAY", "DraftKings", "US", "2025-03-10T18:00:00Z", 60)
    quote = Quote(target, "-3.5", "2025-03-10T16:55:00Z", "2025-03-10T16:55:00Z", "2025-03-10T16:56:00Z", True)
    mass = [(-7, "1/10"), (-1, "3/20"), (3, "1/5"), (4, "1/4"), (10, "3/10")]
    probabilities = {}
    for name, spread in (("favorite_half", "-3.5"), ("favorite_integer", "-3"), ("underdog_half", "3.5")):
        probabilities[name] = probability_at_spread(mass, replace(quote, home_spread=spread), target, "2025-03-10T16:45:00Z")
    results = []
    for day, margin in ((1, 6), (3, 1), (5, 3), (7, 8)):
        r = replace(target, game=f"invented-past-{day}", tipoff=f"2025-03-{day:02d}T18:00:00Z")
        q = Quote(r, "-3", f"2025-03-{day:02d}T16:55:00Z", f"2025-03-{day:02d}T16:55:00Z", f"2025-03-{day:02d}T16:56:00Z", True)
        results.append(Result(q, 70 + margin, 70, f"2025-03-{day:02d}T20:00:00Z", f"2025-03-{day:02d}T20:05:00Z"))
    missing = replace(results[-1], quote=replace(results[-1].quote, reference=replace(results[-1].quote.reference, game="invented-unknown")), result_available_at=None)
    results.append(missing)
    record = ats_record(results, team="HOME", target=target, target_cutoff="2025-03-10T17:00:00Z")
    late = replace(quote, captured_at="2025-03-10T17:01:00Z")
    try:
        probability_at_spread(mass, late, target, "2025-03-10T16:45:00Z")
    except ContractError as exc:
        late_status = str(exc)
    return {
        "scope": "INVENTED_EXAMPLE_NOT_NCAA_PERFORMANCE", "probabilities": probabilities,
        "record": record, "late_capture_status": late_status,
        "model_available_at": "2025-03-10T16:45:00Z", "quote_captured_at": quote.captured_at,
        "decision_cutoff": "2025-03-10T17:00:00Z", "orders": 0,
    }


if __name__ == "__main__":
    print(json.dumps(demo(), sort_keys=True, indent=2, allow_nan=False))
