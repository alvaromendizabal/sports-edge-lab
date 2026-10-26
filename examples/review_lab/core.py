"""A small, inspectable chronological ML example using the Python standard library.

All training data and learned parameters in this module are synthetic. The public
football evidence is an independent aggregate export and is never used for fitting.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Iterable


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return e / (1.0 + e)


def validate_rows(rows: Iterable[dict]) -> list[dict]:
    rows = list(rows)
    if not rows:
        raise ValueError("empty cohort")
    identities: set[str] = set()
    for row in rows:
        identity = row["event_id"]
        if not isinstance(identity, str) or not identity or identity in identities:
            raise ValueError("missing or duplicate event identity")
        identities.add(identity)
        decision = timestamp(row["decision_at"])
        observed = timestamp(row["features_observed_at"])
        published = timestamp(row["features_published_at"])
        kickoff = timestamp(row["event_at"])
        available = timestamp(row["label_available_at"])
        if not published <= observed < decision < kickoff <= available:
            raise ValueError("information-time contract violated")
        if row["label"] not in (0, 1):
            raise ValueError("target must be binary")
        if not 0 < row["market_probability"] < 1:
            raise ValueError("MARKET probability must be strictly between zero and one")
        if not all(math.isfinite(row[k]) for k in ("market_probability", "context_a", "context_b")):
            raise ValueError("non-finite feature")
    return rows


def synthetic_events(count: int = 320, seed: int = 119) -> list[dict]:
    """Create invented events with a learnable interaction, not football records."""
    if count < 40:
        raise ValueError("use at least forty synthetic events")
    rng = random.Random(seed)
    start = datetime(2023, 1, 1, 20, tzinfo=timezone.utc)
    rows = []
    for i in range(count):
        event = start + timedelta(days=2 * i)
        decision = event - timedelta(days=1)
        market_logit = rng.gauss(0, 0.9)
        a, b = rng.uniform(-1, 1), rng.uniform(-1, 1)
        latent = 0.8 * market_logit + 0.65 * a - 0.2 * b + 0.9 * a * b
        rows.append({
            "event_id": f"SIM-{i:04d}",
            "event_at": event.isoformat(),
            "decision_at": decision.isoformat(),
            "features_published_at": (decision - timedelta(hours=4)).isoformat(),
            "features_observed_at": (decision - timedelta(hours=3)).isoformat(),
            "label_available_at": (event + timedelta(hours=6)).isoformat(),
            "market_probability": sigmoid(market_logit),
            "context_a": a, "context_b": b,
            "label": int(rng.random() < sigmoid(latent)),
        })
    return validate_rows(rows)


def vector(row: dict, interactions: bool) -> tuple[float, ...]:
    p = row["market_probability"]
    base = (1.0, math.log(p / (1 - p)), row["context_a"], row["context_b"])
    return base + ((row["context_a"] * row["context_b"],) if interactions else ())


@dataclass(frozen=True)
class SyntheticModel:
    coefficients: tuple[float, ...]
    interactions: bool
    fitted_at: str
    training_cohort_sha256: str
    training_rows: int


def fit_synthetic(rows: Iterable[dict], fitted_at: str, *, interactions: bool) -> SyntheticModel:
    rows = validate_rows(rows)
    fit_time = timestamp(fitted_at)
    if any(timestamp(r["label_available_at"]) >= fit_time for r in rows):
        raise ValueError("training label was not available at fit time")
    xs = [vector(r, interactions) for r in rows]
    coefficients = [0.0] * len(xs[0])
    # Deliberately simple, fixed educational settings, unrelated to private models.
    for _ in range(600):
        gradients = [0.0] * len(coefficients)
        for x, row in zip(xs, rows):
            error = sigmoid(sum(w * v for w, v in zip(coefficients, x))) - row["label"]
            for j, v in enumerate(x):
                gradients[j] += error * v
        for j in range(len(coefficients)):
            penalty = 0.02 * coefficients[j] if j else 0.0
            coefficients[j] -= 0.1 * (gradients[j] / len(rows) + penalty)
    return SyntheticModel(tuple(coefficients), interactions, fitted_at,
                          digest([r["event_id"] for r in rows]), len(rows))


def predict_synthetic(model: SyntheticModel, rows: Iterable[dict]) -> dict[str, float]:
    rows = validate_rows(rows)
    fitted = timestamp(model.fitted_at)
    if any(fitted >= timestamp(r["decision_at"]) for r in rows):
        raise ValueError("model unavailable at prediction decision")
    return {r["event_id"]: sigmoid(sum(w * v for w, v in zip(model.coefficients, vector(r, model.interactions))))
            for r in rows}


def score_matched(labels: dict[str, int], probabilities: dict[str, float]) -> dict:
    if not labels or set(labels) != set(probabilities):
        raise ValueError("prediction and target cohorts must match exactly")
    if any(y not in (0, 1) for y in labels.values()):
        raise ValueError("target must be binary")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
        raise ValueError("invalid probability")
    losses, squared, correct = [], [], []
    for identity in sorted(labels):
        y, p = labels[identity], probabilities[identity]
        clipped = min(1 - 1e-15, max(1e-15, p))
        losses.append(-y * math.log(clipped) - (1 - y) * math.log(1 - clipped))
        squared.append((p - y) ** 2)
        correct.append(int((p >= 0.5) == bool(y)))
    n = len(labels)
    return {"games": n, "log_loss": sum(losses) / n, "brier": sum(squared) / n,
            "accuracy": sum(correct) / n, "cohort_sha256": digest(sorted(labels))}


def run_synthetic(seed: int = 119) -> dict:
    rows = synthetic_events(seed=seed)
    training, evaluation = rows[:240], rows[240:]
    fitted = (timestamp(evaluation[0]["decision_at"]) - timedelta(seconds=1)).isoformat()
    labels = {r["event_id"]: r["label"] for r in evaluation}
    models = {"additive": fit_synthetic(training, fitted, interactions=False),
              "joint": fit_synthetic(training, fitted, interactions=True)}
    forecasts = {"MARKET_synthetic": {r["event_id"]: r["market_probability"] for r in evaluation}}
    forecasts.update({name: predict_synthetic(model, evaluation) for name, model in models.items()})
    return {"schema": "sports-edge-public-synthetic-v1", "data_kind": "synthetic",
            "real_football_performance": False, "seed": seed,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "training_rows": len(training), "evaluation_rows": len(evaluation),
            "fitted_at": fitted, "training_cohort_sha256": models["joint"].training_cohort_sha256,
            "scores": {name: score_matched(labels, p) for name, p in forecasts.items()},
            "decision": "Illustrative software verification; no production promotion or wagering claim"}


def verify_manifest(directory: Path) -> dict:
    directory = directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("schema") != "sports-edge-public-artifact-v1":
        raise ValueError("unsupported manifest")
    if [entry.get("path") for entry in manifest.get("files", [])] != ["report.json"]:
        raise ValueError("unexpected artifact inventory")
    for entry in manifest["files"]:
        path = (directory / entry["path"]).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError("manifest path escapes artifact or is missing")
        body = path.read_bytes()
        if len(body) != entry["bytes"] or hashlib.sha256(body).hexdigest() != entry["sha256"]:
            raise ValueError("artifact integrity failure")
    return {"status": "PASS", "files_verified": len(manifest["files"])}


def write_run(directory: Path, seed: int = 119) -> dict:
    if directory.exists():
        verify_manifest(directory)
        body = (directory / "report.json").read_bytes()
        report = json.loads(body)
        if report.get("seed") != seed or report.get("implementation_sha256") != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
            raise ValueError("refusing to overwrite a different accepted run")
        return {"status": "REUSED", "new_fits": 0, "report_sha256": hashlib.sha256(body).hexdigest()}
    report = run_synthetic(seed)
    body = canonical_bytes(report)
    directory.mkdir(parents=True)
    (directory / "report.json").write_bytes(body)
    manifest = {"schema": "sports-edge-public-artifact-v1", "data_kind": "synthetic",
                "files": [{"path": "report.json", "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}]}
    (directory / "manifest.json").write_bytes(canonical_bytes(manifest))
    verify_manifest(directory)
    return {"status": "CREATED", "new_fits": 2, "report_sha256": hashlib.sha256(body).hexdigest()}
