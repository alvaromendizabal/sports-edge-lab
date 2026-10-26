"""Evaluate a generic 2×2 prediction experiment on identical, invented events.

This public teaching implementation contains no private football features,
forecasts, fit recipes or production decision thresholds. It evaluates already
frozen predictions; it does not select or fit a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ARMS = ("base", "A", "B", "AB", "MARKET", "retained")


@dataclass(frozen=True)
class Observation:
    event_id: str
    block: str
    outcome: int
    probability: float


def _index(rows: list[Observation]) -> dict[str, Observation]:
    out = {}
    for row in rows:
        if not row.event_id or not row.block or row.event_id in out:
            raise ValueError("empty identity/block or duplicate event")
        if type(row.outcome) is not int or row.outcome not in (0, 1):
            raise ValueError("outcomes must be observed binary integers")
        if isinstance(row.probability, bool) or not isinstance(row.probability, (int, float)):
            raise ValueError("probability must be numeric")
        if not math.isfinite(row.probability) or not 0 < row.probability < 1:
            raise ValueError("probabilities must be finite and strictly between zero and one")
        out[row.event_id] = row
    if not out:
        raise ValueError("empty experiment")
    return out


def log_loss(row: Observation) -> float:
    return -math.log(row.probability if row.outcome else 1 - row.probability)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def block_interval(values: list[float], blocks: list[str], *, seed: int = 17,
                   resamples: int = 1000, minimum_blocks: int = 8) -> dict:
    """Paired event-weighted bootstrap, resampling entire blocks with replacement.

    Blocks, not individual games, are the sampling units. Unequal sampled block
    sizes retain their event counts. This interval does not correct selection,
    establish stationarity, or prove a causal interaction.
    """
    if len(values) != len(blocks) or not values:
        raise ValueError("values and blocks must have matching nonempty lengths")
    if any(not math.isfinite(v) for v in values) or any(not b for b in blocks):
        raise ValueError("invalid contrast or block")
    if resamples < 100 or minimum_blocks < 2:
        raise ValueError("invalid bootstrap support policy")
    groups = defaultdict(list)
    for value, block in zip(values, blocks):
        groups[block].append(value)
    keys = sorted(groups)
    result = {"estimate": mean(values), "blocks": len(keys), "games": len(values),
              "interval": None, "resamples": 0, "status": "insufficient_blocks"}
    if len(keys) < minimum_blocks:
        return result
    rng = random.Random(seed)
    draws = []
    for _ in range(resamples):
        selected = [groups[rng.choice(keys)] for _ in keys]
        draws.append(sum(map(sum, selected)) / sum(map(len, selected)))
    result.update(interval=[_quantile(draws, .025), _quantile(draws, .975)],
                  resamples=resamples, status="descriptive_interval")
    return result


def evaluate(predictions: dict[str, list[Observation]], *, seed: int = 17) -> dict:
    if set(predictions) != set(ARMS):
        raise ValueError("require exactly base, A, B, AB, MARKET and retained arms")
    indexed = {name: _index(rows) for name, rows in predictions.items()}
    keys = sorted(indexed["base"])
    for name, rows in indexed.items():
        if set(rows) != set(keys):
            raise ValueError(f"cohort mismatch: {name}")
        for key in keys:
            base, row = indexed["base"][key], rows[key]
            if (row.outcome, row.block) != (base.outcome, base.block):
                raise ValueError(f"label/block mismatch: {name}")
    losses = {name: [log_loss(rows[key]) for key in keys] for name, rows in indexed.items()}
    blocks = [indexed["base"][key].block for key in keys]
    scores = {name: {"log_loss": mean(losses[name]),
                     "brier": mean((rows[key].probability - rows[key].outcome) ** 2 for key in keys)}
              for name, rows in indexed.items()}
    # Negative interaction means the combined loss reduction exceeds the sum of
    # the two isolated reductions on this fixed probability / log-loss scale.
    interaction = [ab - a - b + base for ab, a, b, base in
                   zip(losses["AB"], losses["A"], losses["B"], losses["base"])]
    contrasts = {name: block_interval([a - b for a, b in zip(losses["AB"], losses[name])],
                                      blocks, seed=seed)
                 for name in ("MARKET", "base", "retained")}
    complementarity = block_interval(interaction, blocks, seed=seed)
    beats = all(scores["AB"]["log_loss"] < scores[reference]["log_loss"] and
                scores["AB"]["brier"] <= scores[reference]["brier"]
                for reference in ("MARKET", "base", "retained"))
    supported = all(c["interval"] is not None and c["interval"][1] < 0
                    for c in contrasts.values())
    return {"schema": "public-factorial-example-v1", "data_origin": "caller_supplied_prediction_tables",
            "cohort_sha256": hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest(),
            "games": len(keys), "scores": scores, "joint_minus_reference": contrasts,
            "interaction": complementarity,
            "joint_point_scores_improve_all_references": beats,
            "descriptive_joint_evidence": beats and supported,
            "prospective_qualification": "not_established_by_this_example",
            "actual_wagers": 0}


def fixture(kind: str = "complementary") -> dict[str, list[Observation]]:
    """Three transparent loss scenarios, not an optimized prediction exercise."""
    if kind not in ("complementary", "redundant", "harmful"):
        raise ValueError("unknown invented scenario")
    rows = {name: [] for name in ARMS}
    # Probabilities assigned to the known outcome make the intended mathematical
    # contrast explicit. These are invented score fixtures, not forecast claims.
    confidence = {"base": .60, "A": .64, "B": .65, "MARKET": .66, "retained": .68,
                  "AB": {"complementary": .79, "redundant": .66, "harmful": .54}[kind]}
    for index in range(48):
        outcome = index % 2
        drift = ((index % 7) - 3) * .003
        for name in ARMS:
            p = confidence[name] + drift
            rows[name].append(Observation(f"invented-{index:03d}", f"week-{index//6:02d}",
                                          outcome, p if outcome else 1-p))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {kind: {**evaluate(fixture(kind)), "fixture_origin": "transparent_invented_score_fixture"}
              for kind in ("complementary", "redundant", "harmful")}
    body = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body)
    print(body)


if __name__ == "__main__":
    main()
