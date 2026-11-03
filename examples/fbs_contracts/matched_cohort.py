"""Generic scoring contracts demonstrated only on invented public observations.

Equal denominators do not establish a paired comparison. Identity, target,
season, kickoff and label must agree before any comparison is calculated.
Declared pre-kickoff timestamps are checked; this code does not authenticate
historical possession or turn a retrospective row into a prospective issue.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math


@dataclass(frozen=True)
class Forecast:
    event: str
    season: int
    target: str
    actual: float
    prediction: float
    kickoff: str
    issued_at: str


def _clock(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone-aware clock required")
    return parsed


def _indexed(rows):
    indexed = {}
    for row in rows:
        if not isinstance(row, Forecast):
            raise ValueError("named Forecast records required")
        if not row.event or type(row.season) is not int or row.target not in {"winner", "margin", "total"}:
            raise ValueError("invalid identity, season or target")
        if not all(type(v) in (int, float) and math.isfinite(v) for v in (row.actual, row.prediction)):
            raise ValueError("finite numeric label and prediction required")
        if row.target == "winner" and (row.actual not in (0, 1) or not 0 <= row.prediction <= 1):
            raise ValueError("binary outcome and probability in [0, 1] required")
        if _clock(row.issued_at) >= _clock(row.kickoff):
            raise ValueError("forecast must declare an issue time before kickoff")
        key = (row.season, row.event, row.target)
        if key in indexed:
            raise ValueError("duplicate event/season/target identity")
        indexed[key] = row
    if not indexed:
        raise ValueError("empty cohort")
    return indexed


def cohort_commitment(rows):
    """Order-independent commitment to identity + labels, not predictions."""
    indexed = _indexed(rows)
    payload = [[*key, float(indexed[key].actual), _clock(indexed[key].kickoff).isoformat()]
               for key in sorted(indexed)]
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def score_matched(models):
    """Return aggregate-only scores after strict all-model pairing.

    Log loss clips probabilities at 1e-15 for numerical evaluation. Accuracy
    uses p >= .5. Point bias is prediction minus observed points. The caller
    must supply the complete registered model set; no intersection is taken.
    """
    if len(models) < 2 or any(not isinstance(name, str) or not name for name in models):
        raise ValueError("at least two named models required")
    indexed = {name: _indexed(rows) for name, rows in models.items()}
    first = next(iter(indexed.values()))
    for rows in indexed.values():
        if set(rows) != set(first):
            raise ValueError("exact event identities required; no intersection scoring")
        for key, row in rows.items():
            other = first[key]
            if row.actual != other.actual or _clock(row.kickoff) != _clock(other.kickoff):
                raise ValueError("paired labels and kickoffs must agree")
    result = []
    groups = sorted({(r.season, r.target) for r in first.values()})
    for name, indexed_rows in indexed.items():
        for season, target in groups:
            rows = [r for r in indexed_rows.values() if (r.season, r.target) == (season, target)]
            n = len(rows)
            record = {"model": name, "season": season, "target": target, "games": n,
                      "cohort_sha256": cohort_commitment(rows)}
            if target == "winner":
                clipped = [(min(1 - 1e-15, max(1e-15, r.prediction)), r.actual) for r in rows]
                correct = sum((r.prediction >= .5) == bool(r.actual) for r in rows)
                record["metrics"] = {
                    "logloss": -math.fsum(y * math.log(p) + (1 - y) * math.log1p(-p) for p, y in clipped) / n,
                    "brier": math.fsum((r.prediction - r.actual) ** 2 for r in rows) / n,
                    "correct": correct, "accuracy": correct / n,
                }
            else:
                residual = [r.prediction - r.actual for r in rows]
                record["metrics"] = {"mae": math.fsum(abs(x) for x in residual) / n,
                                     "rmse": math.sqrt(math.fsum(x * x for x in residual) / n),
                                     "bias": math.fsum(residual) / n}
            result.append(record)
    return result


def pool_additive(panels, metric):
    """Pool additive metric sufficient statistics; ECE and MCC cannot be pooled.

    Panels must be disjoint (for example, two distinct seasons). Aggregate
    counts cannot independently prove disjointness: the caller must establish
    that before calling. RMSE pools squared error, never the mean of RMSEs.
    """
    if metric not in {"logloss", "brier", "accuracy", "mae", "rmse", "bias"}:
        raise ValueError("metric cannot be pooled from these aggregate statistics")
    if not panels or any(type(p["games"]) is not int or p["games"] <= 0 for p in panels):
        raise ValueError("positive integer denominators required")
    values = [p["metrics"][metric] for p in panels]
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
        raise ValueError("missing or non-finite metric")
    n = sum(p["games"] for p in panels)
    value = math.fsum(p["games"] * (x * x if metric == "rmse" else x)
                      for p, x in zip(panels, values)) / n
    return math.sqrt(value) if metric == "rmse" else value


def invented_comparison():
    """Two invented events, with hand-checkable scores and no sports data."""
    first = [Forecast("invented-a", 2024, "winner", 1, .8, "2024-10-01T18:00:00Z", "2024-10-01T17:00:00Z"),
             Forecast("invented-b", 2024, "winner", 0, .3, "2024-10-02T18:00:00Z", "2024-10-02T17:00:00Z")]
    other = [Forecast(r.event, r.season, r.target, r.actual, p, r.kickoff, r.issued_at)
             for r, p in zip(first, (.6, .4))]
    return {"invented-reference": first, "invented-challenger": other}


if __name__ == "__main__":
    print(json.dumps({"status": "Wholly invented; no forecasting-skill claim",
                      "panels": score_matched(invented_comparison())}, indent=2, allow_nan=False))
