"""Generic discrete-distribution checks on invented scores; no football model.

This module accepts an already specified finite probability law. It contains no
feature engineering, fitting, market calibration, private parameters or data.
Log probabilities remain the scoring authority when a tiny mass underflows in
an ordinary floating-point probability. A missing outcome has probability zero.
"""
from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


def logsumexp(values: Iterable[float]) -> float:
    values = tuple(values)
    if not values:
        return -math.inf
    if any(math.isnan(v) or v == math.inf for v in values):
        raise ValueError("log values must be finite or negative infinity")
    peak = max(values)
    if peak == -math.inf:
        return peak
    return peak + math.log(math.fsum(math.exp(v - peak) for v in values))


@dataclass(frozen=True)
class DiscreteScoreLaw:
    """A normalized finite law over arbitrary integer score pairs."""

    log_mass: Mapping[tuple[int, int], float]

    def __post_init__(self) -> None:
        copied = dict(self.log_mass)
        if not copied:
            raise ValueError("empty support")
        for pair, value in copied.items():
            if not isinstance(pair, tuple) or len(pair) != 2 or any(type(v) is not int for v in pair):
                raise ValueError("score support must contain integer pairs")
            if not math.isfinite(value):
                raise ValueError("stored log masses must be finite")
        if abs(logsumexp(copied.values())) > 1e-10:
            raise ValueError("probability law is not normalized")
        from types import MappingProxyType
        object.__setattr__(self, "log_mass", MappingProxyType(copied))

    @classmethod
    def from_log_weights(cls, rows: Iterable[tuple[int, int, float]]) -> "DiscreteScoreLaw":
        weights = {}
        for home, away, weight in rows:
            key = (home, away)
            if key in weights:
                raise ValueError("duplicate score pair")
            if not math.isfinite(weight):
                raise ValueError("log weights must be finite")
            weights[key] = weight
        if not weights:
            raise ValueError("empty support")
        normalizer = logsumexp(weights.values())
        return cls({pair: weight - normalizer for pair, weight in weights.items()})

    def event_log_probability(self, predicate) -> float:
        return logsumexp(value for pair, value in self.log_mass.items() if predicate(*pair))

    def outcome_probabilities(self) -> dict[str, float]:
        return {name: math.exp(self.event_log_probability(predicate)) for name, predicate in (
            ("home", lambda h, a: h > a), ("away", lambda h, a: h < a), ("tie", lambda h, a: h == a))}

    def conditional_win_logs(self) -> tuple[float, float]:
        home = self.event_log_probability(lambda h, a: h > a)
        away = self.event_log_probability(lambda h, a: h < a)
        normalizer = logsumexp((home, away))
        if normalizer == -math.inf:
            raise ValueError("non-tie conditioning event has zero mass")
        return home - normalizer, away - normalizer

    def joint_nll(self, home: int, away: int) -> float:
        return -self.log_mass.get((home, away), -math.inf)

    def conditional_win_nll(self, home_won: bool) -> float:
        if type(home_won) is not bool:
            raise ValueError("conditional binary outcome must be a boolean")
        logs = self.conditional_win_logs()
        return -logs[0 if home_won else 1]

    def marginal_crps(self, axis: int, observed: float) -> float:
        """E|X-y| - E|X-X'|/2 for one finite score marginal."""
        if axis not in (0, 1) or not math.isfinite(observed):
            raise ValueError("invalid marginal or observed value")
        masses: dict[int, float] = {}
        for pair, value in self.log_mass.items():
            masses[pair[axis]] = masses.get(pair[axis], 0.0) + math.exp(value)
        first = math.fsum(p * abs(x - observed) for x, p in masses.items())
        second = math.fsum(p * q * abs(x - z) for x, p in masses.items() for z, q in masses.items())
        return first - 0.5 * second

    def expected_settlement(self, *, home_payout: float, away_payout: float, tie_payout: float) -> float:
        """Expected contract settlement, excluding purchase price and all fees."""
        payouts = {"home": home_payout, "away": away_payout, "tie": tie_payout}
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in payouts.values()):
            raise ValueError("settlements must be finite unit-contract payouts")
        probabilities = self.outcome_probabilities()
        return math.fsum(probabilities[key] * value for key, value in payouts.items())


def mixture(laws: Iterable[DiscreteScoreLaw], weights: Iterable[float]) -> DiscreteScoreLaw:
    laws, weights = tuple(laws), tuple(weights)
    if not laws or len(laws) != len(weights):
        raise ValueError("law and mixture-weight counts differ or are empty")
    if any(not math.isfinite(w) or w < 0 for w in weights) or abs(math.fsum(weights) - 1) > 1e-12:
        raise ValueError("mixture weights must be nonnegative and sum to one")
    support = set().union(*(law.log_mass for law in laws))
    combined = {}
    for pair in support:
        value = logsumexp(math.log(w) + law.log_mass.get(pair, -math.inf) for law, w in zip(laws, weights) if w > 0)
        if value != -math.inf:
            combined[pair] = value
    return DiscreteScoreLaw(combined)


def demonstration() -> dict:
    """An invented tie-heavy example; these are not fitted football forecasts."""
    first = DiscreteScoreLaw.from_log_weights([(1, 0, math.log(.45)), (0, 1, math.log(.05)), (1, 1, math.log(.50))])
    second = DiscreteScoreLaw.from_log_weights([(1, 0, math.log(.10)), (0, 1, math.log(.80)), (1, 1, math.log(.10))])
    joint = mixture([first, second], [.5, .5])
    naive = .5 * math.exp(first.conditional_win_logs()[0]) + .5 * math.exp(second.conditional_win_logs()[0])
    return {
        "data_kind": "invented_probability_laws", "real_football_performance": False,
        "joint_mixture_outcomes": joint.outcome_probabilities(),
        "mixture_then_condition_home": math.exp(joint.conditional_win_logs()[0]),
        "incorrect_average_of_conditional_home": naive,
        "unit_contract_half_tie_expected_settlement": joint.expected_settlement(home_payout=1, away_payout=0, tie_payout=.5),
        "purchase_price_and_fees_included": False,
    }


if __name__ == "__main__":
    print(json.dumps(demonstration(), indent=2, allow_nan=False))
