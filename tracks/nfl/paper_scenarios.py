"""Exact arithmetic for invented NFL paper examples, with no network or orders.

This is an educational contract, not a forecast or provider integration. Inputs
must already describe a supported instrument. Multi-leg entries and exchange
fees require different complete payoff models and are intentionally not inferred.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import product
import json


def number(value, name):
    if isinstance(value, bool) or value is None:
        raise ValueError(name + " must be a finite number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(name + " must be a finite number") from exc
    if not result.is_finite():
        raise ValueError(name + " must be a finite number")
    return result


def probability(value, name):
    result = number(value, name)
    if not Decimal(0) <= result <= Decimal(1):
        raise ValueError(name + " must be between zero and one")
    return result


def decimal_odds(american):
    """American +150 means 1.50 net profit per dollar; -200 means 0.50."""
    value = number(american, "American odds")
    if abs(value) < 100:
        raise ValueError("American odds magnitude must be at least 100")
    return 1 + (value / 100 if value > 0 else 100 / -value)


def no_vig_pair(first, second):
    """Normalize a genuine paired two-side quote once; not a learned forecast."""
    def implied(value):
        decimal_odds(value)  # Validate without rounding the rational calculation.
        odds = Fraction(number(value, "American odds"))
        return 100 / (odds + 100) if odds > 0 else -odds / (100 - odds)
    def dec(value):
        return Decimal(value.numerator) / Decimal(value.denominator)
    a, b = implied(first), implied(second)
    p = dec(a / (a + b))
    return {"first_conditional_non_tie": p,
            "second_conditional_non_tie": 1-p,
            "quoted_probability_sum": dec(a + b),
            "method": "proportional_two_side_normalization"}


def straight_bet(stake, american, conditional_win, *, tie_probability=None,
                 tie_rule, fixed_fee=0):
    """Enumerate a two-way moneyline with an explicitly supported tie rule.

The fixed fee is assumed charged once even on a refund. Unknown tie mass leaves
unconditional expectation unknown. A conditional percentage is never silently
relabelled an unconditional win chance. Other void states are outside this toy
instrument and must be added before evaluating a different real instrument.
"""
    if tie_rule not in {"refund", "loss"}:
        raise ValueError("Explicit supported tie rule is required")
    s, fee = number(stake, "stake"), number(fixed_fee, "fixed fee")
    if s < 0 or fee < 0:
        raise ValueError("Stake and fee cannot be negative")
    p, odds = probability(conditional_win, "conditional win"), decimal_odds(american)
    win, loss = s * (odds - 1) - fee, -s - fee
    tie = -fee if tie_rule == "refund" else loss
    conditional_ev = p * win + (1 - p) * loss
    result = {"stake": s, "decimal_odds": odds, "win_net_profit": win,
              "win_gross_payout_before_fee": s * odds, "loss_net_profit": loss,
              "tie_net_profit": tie, "conditional_non_tie_win": p,
              "conditional_non_tie_ev": conditional_ev,
              "unconditional_win_probability": None, "unconditional_ev": None,
              "tie_probability": None, "tie_rule": tie_rule,
              "fixed_fee_charged_in_every_state": fee}
    if tie_probability is not None:
        t = probability(tie_probability, "tie probability")
        result.update(tie_probability=t, unconditional_win_probability=(1-t)*p,
                      unconditional_ev=(1-t)*conditional_ev + t*tie)
    return result


def budget(weekly_ceiling, already_allocated, requested):
    ceiling, request = number(weekly_ceiling, "ceiling"), number(requested, "request")
    if ceiling < 0 or request < 0:
        raise ValueError("Budget values cannot be negative")
    if already_allocated is None:
        return {"remaining": None, "new_proposed_stake": Decimal(0),
                "status": "UNKNOWN_PRIOR_ALLOCATION"}
    used = number(already_allocated, "already allocated")
    if used < 0:
        raise ValueError("Allocated amount cannot be negative")
    remaining = max(Decimal(0), ceiling-used)
    return {"remaining": remaining, "new_proposed_stake": min(request, remaining),
            "status": "RECONCILED" if used <= ceiling else "CEILING_ALREADY_EXCEEDED"}


def clock(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("Explicit timezone-aware clock required") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Explicit timezone-aware clock required")
    return result


def issue_classification(*, kickoff, source_available, acquired, issued):
    """Actual acquisition/issue cannot be backdated by represented quote time."""
    start, available, got, made = map(clock, (kickoff, source_available, acquired, issued))
    if available > got or got > made:
        raise ValueError("Source, acquisition and issue clocks are inconsistent")
    cutoff = start - timedelta(hours=24)
    if made >= start:
        return "POST_START_ILLUSTRATION"
    return "T24_TIME_BOUNDARY_MET_ONLY" if made <= cutoff else "LATE_MONITORING"


def win_loss_scenarios(positions):
    """Enumerate W/L dollars; no independence or probability claim is made."""
    if not positions or len({p["id"] for p in positions}) != len(positions):
        raise ValueError("Unique nonempty position identities required")
    result = []
    for outcomes in product(("win", "loss"), repeat=len(positions)):
        net = sum((number(p[outcome+"_net_profit"], "net profit")
                   for p, outcome in zip(positions, outcomes)), Decimal(0))
        result.append({"outcomes": dict(zip((p["id"] for p in positions), outcomes)),
                       "net_profit": net, "scenario_probability": None})
    return result


def demo():
    # Invented teams, prices and probabilities; no real-game prediction.
    examples = [straight_bet(100, price, p, tie_rule="refund")
                for price, p in [(-200, "0.63"), (-150, "0.58"),
                                  (120, "0.43"), (-110, "0.49")]]
    positions = [{"id": "invented-"+str(i+1), **row} for i, row in enumerate(examples)]
    return {"scope": "INVENTED_ARITHMETIC_ONLY", "actual_orders": 0,
            "hypothetical_stake_total": Decimal(400),
            "actual_proposed_allocation": budget(400, None, 400),
            "positions": positions, "win_loss_only_scenarios": win_loss_scenarios(positions),
            "unconditional_portfolio_ev": None,
            "limits": ["No tie distribution", "No current offers or eligibility",
                       "No portfolio dependence model", "No multi-leg entry payout"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(demo(), default=str, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
