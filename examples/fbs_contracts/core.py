"""Invented-data chronology, content closure and recoverable FBS fit receipts.

No network, provider account, private source, paid price or real forecast is used.
This compact example is independently executable with Python's standard library.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import fcntl
import hashlib
import json
import math
import os
import random
import tempfile
from typing import Callable

SCHEMA = "sports-edge-lab.public-fbs-contracts.v1"
UTC = timezone.utc


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def instant(value):
    if not isinstance(value, str):
        raise ValueError("timezone-aware clock required")
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("timezone-aware clock required")
    return value.astimezone(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(encoded(value) + b"\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@dataclass(frozen=True)
class Game:
    game_id: str
    season: int
    week: int
    home: str
    away: str
    home_fbs: bool
    away_fbs: bool
    kickoff: str
    outcome_available_at: str
    outcome_observed_at: str
    home_points: int
    away_points: int
    market_home: float
    market_published_at: str
    market_observed_at: str
    neutral: bool = False

    def validate(self):
        if not all(isinstance(v, str) and v for v in (self.game_id, self.home, self.away)) or self.home == self.away:
            raise ValueError("exact ordered event identity required")
        if not isinstance(self.home_fbs, bool) or not isinstance(self.away_fbs, bool):
            raise ValueError("FBS classification must be explicit")
        if not self.home_fbs and not self.away_fbs:
            raise ValueError("FCS-only games are outside this FBS population")
        if any(type(v) is not int or v < 0 for v in (self.home_points, self.away_points)):
            raise ValueError("finite nonnegative integer scores required")
        if type(self.season) is not int or type(self.week) is not int or self.week < 1:
            raise ValueError("explicit season and native week required")
        if type(self.market_home) not in (int, float) or not math.isfinite(self.market_home) or not 0 < self.market_home < 1 or self.home_points == self.away_points:
            raise ValueError("invented binary game probability/outcome invalid")
        start = instant(self.kickoff)
        if instant(self.outcome_available_at) <= start or instant(self.outcome_observed_at) < instant(self.outcome_available_at):
            raise ValueError("outcome availability/observation clocks invalid")
        if instant(self.market_observed_at) < instant(self.market_published_at):
            raise ValueError("market observation precedes publication")
        return self


def source_catalog(scopes, required_scopes, bodies, request_id):
    """A complete declared scope is required even when a receipt has no prices."""
    if set(scopes) != set(required_scopes):
        raise ValueError("all declared shared scopes must be present")
    requests = set()
    content_hashes = set()
    for scope in scopes.values():
        if scope.get("complete") is not True or scope.get("unresolved", 0) != 0:
            raise ValueError("partial or unresolved listing cannot prove absence")
        for item in scope["objects"]:
            identity = item["body_sha256"]
            if identity not in bodies or hashlib.sha256(bodies[identity]).hexdigest() != identity:
                raise ValueError("raw content closure failed")
            if not isinstance(item.get("request_id"), str) or not item["request_id"]:
                raise ValueError("original request receipt required")
            content_hashes.add(identity)
            requests.add(item["request_id"])
    return {"request_status": "CAPTURED" if request_id in requests else "NOT_FOUND_IN_DECLARED_SCOPES",
            "unique_content_objects": len(content_hashes), "unique_request_receipts": len(requests),
            "may_dispatch": False, "actual_requests": 0, "credits_spent": 0,
            "boundary": "Scoped inventory never grants a paid request or proves universal absence."}


def pregame_rows(games):
    """Prior outcomes must have both clocks before the target's 24-hour cutoff."""
    games = sorted((game.validate() for game in games), key=lambda g: (instant(g.kickoff), g.game_id))
    if len({game.game_id for game in games}) != len(games):
        raise ValueError("duplicate native game id")
    rows, history = [], []
    for game in games:
        cutoff = instant(game.kickoff) - timedelta(hours=24)
        if max(instant(game.market_published_at), instant(game.market_observed_at)) > cutoff:
            raise ValueError("market unavailable at pregame cutoff")
        eligible = [prior for prior in history if max(instant(prior.outcome_available_at), instant(prior.outcome_observed_at)) <= cutoff]
        def strength(team):
            values = [prior.home_points - prior.away_points if prior.home == team else prior.away_points - prior.home_points
                      for prior in eligible if team in (prior.home, prior.away)]
            return sum(values) / (len(values) + 5), len(values)
        home, nh = strength(game.home)
        away, na = strength(game.away)
        rows.append({"game_id": game.game_id, "season": game.season, "week": game.week,
                     "cutoff": iso(cutoff), "kickoff": game.kickoff,
                     "label_available_at": game.outcome_available_at,
                     "label_observed_at": game.outcome_observed_at,
                     "market_home": game.market_home, "y": int(game.home_points > game.away_points),
                     "football_strength": (home - away) / 14, "home_edge": int(not game.neutral),
                     "home_history": nh, "away_history": na,
                     "source_game_ids": [prior.game_id for prior in eligible],
                     "feature_max_observed_at": max([prior.outcome_observed_at for prior in eligible], default=None),
                     "population": "FBS_FBS" if game.home_fbs and game.away_fbs else "FBS_FCS",
                     "invented": True})
        history.append(game)
    return rows


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-40.0, min(40.0, x))))


def design(row):
    p = row["market_home"]
    return [1.0, math.log(p / (1 - p)), row["football_strength"], row["home_edge"]]


def fit_model(rows, target_year):
    if target_year not in (2024, 2025, 2026) or not rows:
        raise ValueError("registered chronological origin required")
    cutoff = datetime(target_year, 8, 1, tzinfo=UTC)
    if any(r["season"] >= target_year or r["season"] >= 2026 for r in rows):
        raise ValueError("target-season and 2026 outcomes cannot enter fitting")
    if any(max(instant(r["label_available_at"]), instant(r["label_observed_at"])) >= cutoff for r in rows):
        raise ValueError("training labels unavailable at fit cutoff")
    coefficients = [0.0, 1.0, 0.0, 0.0]
    prior = coefficients[:]
    # Fixed deterministic steps are this invented estimator definition, not a
    # research time/cost ceiling. Each call creates one actual synthetic fit.
    for _ in range(600):
        gradient = [0.03 * (b - a) for b, a in zip(coefficients, prior)]
        for row in rows:
            x = design(row)
            error = sigmoid(sum(b * v for b, v in zip(coefficients, x))) - row["y"]
            for index, value in enumerate(x):
                gradient[index] += error * value / len(rows)
        coefficients = [b - 0.12 * g for b, g in zip(coefficients, gradient)]
    if not all(math.isfinite(v) for v in coefficients):
        raise ValueError("nonfinite estimator")
    return {"schema": SCHEMA, "invented": True, "target_year": target_year,
            "fit_cutoff": iso(cutoff), "training_seasons": sorted({r["season"] for r in rows}),
            "training_games": len(rows), "coefficients": coefficients,
            "maximum_absolute_gradient": max(map(abs, gradient)),
            "convergence_claim": "Fixed-step synthetic demonstration; no independent optimum certificate.",
            "training_identity": digest(rows), "actual_owner_fits": 0}


def predict(model, row):
    if row["season"] < model["target_year"] or instant(row["cutoff"]) < instant(model["fit_cutoff"]):
        raise ValueError("model applied before its registered target season")
    return sigmoid(sum(b * x for b, x in zip(model["coefficients"], design(row))))


class FitJournal:
    """One locked atomic journal; interrupted reservations remain visible."""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal = self.root / "fit_journal.json"

    def fit(self, unit, inputs, callback: Callable):
        if not unit or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in unit):
            raise ValueError("safe unit identifier required")
        identity = digest(inputs)
        with (self.root / "journal.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            ledger = json.loads(self.journal.read_text()) if self.journal.exists() else {"schema": SCHEMA, "attempts": []}
            previous = [x for x in ledger["attempts"] if x["unit"] == unit]
            if any(x["input_identity"] != identity for x in previous):
                raise ValueError("changed input identity requires a new unit")
            complete = [x for x in previous if x["status"] == "COMPLETE"]
            if complete:
                record = complete[-1]
                output_path = (self.root / record["output_path"]).resolve()
                if not output_path.is_relative_to(self.root.resolve()) or output_path.is_symlink():
                    raise ValueError("saved model path escapes journal")
                body = output_path.read_bytes()
                if hashlib.sha256(body).hexdigest() != record["output_sha256"]:
                    raise ValueError("saved model hash mismatch")
                return json.loads(body), True
            for record in previous:
                if record["status"] == "RUNNING":
                    record["status"] = "INTERRUPTED"
            record = {"unit": unit, "input_identity": identity, "attempt": len(ledger["attempts"]) + 1,
                      "status": "RUNNING", "invented": True}
            ledger["attempts"].append(record)
            atomic_json(self.journal, ledger)
            try:
                model = callback()
                path = f"models/{unit}_attempt_{record['attempt']:04d}.json"
                atomic_json(self.root / path, model)
                record.update(status="COMPLETE", output_path=path,
                              output_sha256=hashlib.sha256((self.root / path).read_bytes()).hexdigest())
            except Exception as exc:
                record.update(status="FAILED", error_type=type(exc).__name__)
                atomic_json(self.journal, ledger)
                raise
            atomic_json(self.journal, ledger)
            return model, False


def fixture():
    rng = random.Random(20261028)
    games = []
    teams = [f"invented_fbs_{i}" for i in range(7)] + ["invented_fcs_7"]
    strength = [0.95, 0.7, 0.4, 0.1, -0.1, -0.4, -0.7, -0.95]
    for year in range(2023, 2027):
        for week in range(1, 9):
            order = list(range(8))
            rng.shuffle(order)
            for index in range(0, 8, 2):
                hi, ai = order[index:index + 2]
                kickoff = datetime(year, 9, 1, 20, tzinfo=UTC) + timedelta(days=7 * (week - 1), hours=index)
                p = sigmoid(0.16 + 0.55 * (strength[hi] - strength[ai]))
                home_wins = rng.random() < sigmoid(0.24 + 0.72 * (strength[hi] - strength[ai]))
                margin = rng.randrange(1, 24) * (1 if home_wins else -1)
                games.append(Game(f"invented_{year}_{week}_{index}", year, week, teams[hi], teams[ai], hi != 7, ai != 7,
                                  iso(kickoff), iso(kickoff + timedelta(hours=4)), iso(kickoff + timedelta(hours=5)),
                                  28 + max(margin, 0), 28 + max(-margin, 0), p,
                                  iso(kickoff - timedelta(hours=25)), iso(kickoff - timedelta(hours=25)), week == 1))
    return games


def scores(rows, probabilities):
    if len(rows) != len(probabilities) or not rows or len({x["game_id"] for x in rows}) != len(rows):
        raise ValueError("exact unique paired cohort required")
    if any(not math.isfinite(p) or not 0 < p < 1 for p in probabilities):
        raise ValueError("finite probabilities strictly inside zero and one required")
    return {"games": len(rows), "brier": sum((p - r["y"]) ** 2 for p, r in zip(probabilities, rows)) / len(rows),
            "log_loss": sum(-math.log(max(1e-15, p if r["y"] else 1 - p)) for p, r in zip(probabilities, rows)) / len(rows)}


def run_demo(root):
    rows = pregame_rows(fixture())
    journal = FitJournal(root)
    source_identity = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    results, new_fits, reused = [], 0, 0
    for target in (2024, 2025, 2026):
        train = [row for row in rows if row["season"] < target]
        inputs = {"source_identity": source_identity, "training_rows": train, "target": target,
                  "kind": "fixed_synthetic_logistic", "forecast_feature_contract": SCHEMA}
        model, cached = journal.fit(f"invented_for{target}", inputs, lambda: fit_model(train, target))
        new_fits += not cached
        reused += cached
        evaluation = [row for row in rows if row["season"] == target]
        results.append({"season": target, "classification": "INVENTED_MONITORING_ONLY" if target == 2026 else "INVENTED_HISTORICAL",
                        "market": scores(evaluation, [row["market_home"] for row in evaluation]),
                        "candidate": scores(evaluation, [predict(model, row) for row in evaluation]),
                        "model_identity": digest(model), "training_games": len(train)})
    raw = b'{"invented":true,"events":[]}'
    h = hashlib.sha256(raw).hexdigest()
    scopes = {name: {"complete": True, "objects": [{"body_sha256": h, "request_id": "invented_request_1"}]}
              for name in ("fbs", "basketball", "march")}
    catalog = source_catalog(scopes, scopes, {h: raw}, "invented_request_1")
    return {"schema": SCHEMA, "data_kind": "WHOLLY_INVENTED", "results": results,
            "new_synthetic_fits": int(new_fits), "reused_synthetic_fits": int(reused),
            "actual_owner_fits": 0, "provider_requests": 0, "actual_orders": 0,
            "operational_policy": "MARKET_REFERENCE_UNCHANGED", "automatic_promotions": 0,
            "shared_catalog": catalog, "2026_used_for_selection": False}
