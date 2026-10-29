"""Invented NBA branch contracts. No model fitting, acquisition or live forecasts.

The local journal illustrates one writer. Production shared acquisition also
requires an account-wide lease and durable request reservations; this module
neither provides that coordination nor grants provider or source rights.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import math
import os
from pathlib import Path
import re
import tempfile

FEATURES = ("incumbent", "candidate")
WINDOWS = ("original", "revised")
VALIDATION_SEASONS = (2025, 2026)
SCHEMA = "public.nba-branch.v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def check_pin(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("a complete content digest is required")


def instant(value):
    if not isinstance(value, str):
        raise ValueError("an explicit source clock is required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone-free source clocks are rejected")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class NBAEvent:
    league: str
    provider: str
    native_id: str
    season_ending: int

    def __post_init__(self):
        if self.league != "nba":
            raise ValueError("NBA-only identity required")
        if any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", v)
               for v in (self.provider, self.native_id)):
            raise ValueError("explicit provider and native identity required")
        if type(self.season_ending) is not int or not 1900 < self.season_ending < 2200:
            raise ValueError("explicit season-ending year required")

    @property
    def identity(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class Experiment:
    league: str
    features: str
    window: str
    validation_season: int
    validation_cohort_sha256: str

    def __post_init__(self):
        if self.league != "nba":
            raise ValueError("NBA-only experiment required")
        if self.features not in FEATURES or self.window not in WINDOWS:
            raise ValueError("unregistered feature or training-window arm")
        if type(self.validation_season) is not int or self.validation_season not in VALIDATION_SEASONS:
            raise ValueError("current-season outcomes cannot select a model")
        check_pin(self.validation_cohort_sha256)

    @property
    def identity(self):
        return digest({"schema": SCHEMA, **asdict(self)})


def fixture_cohorts():
    return {year: digest({"invented_validation_events": [f"fixture_{year}_A", f"fixture_{year}_B"]})
            for year in VALIDATION_SEASONS}


def registration(cohorts=None):
    """Four arms over two fixed seasons; registration is not a fit count."""
    cohorts = fixture_cohorts() if cohorts is None else cohorts
    if set(cohorts) != set(VALIDATION_SEASONS):
        raise ValueError("both independently pinned historical cohorts are required")
    return tuple(Experiment("nba", features, window, year, cohorts[year])
                 for features, window, year in product(FEATURES, WINDOWS, VALIDATION_SEASONS))


def validate_registration(experiments, cohorts=None):
    experiments = tuple(experiments)
    if not all(isinstance(job, Experiment) for job in experiments):
        raise ValueError("typed registered experiments required")
    expected = {job.identity for job in registration(cohorts)}
    actual = [job.identity for job in experiments]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("all four feature/window arms and both seasons are required exactly once")
    return experiments


@dataclass(frozen=True)
class Observation:
    event: NBAEvent
    feature: str
    value: float
    published_at: str
    first_observed_at: str
    retrieved_at: str
    content_sha256: str

    def __post_init__(self):
        if not isinstance(self.event, NBAEvent):
            raise ValueError("typed NBA source identity required")
        if not isinstance(self.feature, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", self.feature):
            raise ValueError("explicit feature identity required")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not math.isfinite(self.value):
            raise ValueError("finite observed value required")
        check_pin(self.content_sha256)
        published, observed, retrieved = map(instant,
            (self.published_at, self.first_observed_at, self.retrieved_at))
        if not published <= observed <= retrieved:
            raise ValueError("source clocks are inconsistent")


def feature_snapshot(event, cutoff_at, observations):
    """Require this exact version to have been published and observed by cutoff.

    These supplied clocks are contract inputs, not independent proof of when a
    source existed. Real use requires authenticated source/observation receipts.
    Reconstructed historical release assumptions belong in a separate tier.
    """
    if not isinstance(event, NBAEvent):
        raise ValueError("typed NBA event required")
    cutoff = instant(cutoff_at)
    observations = sorted(observations, key=lambda row: row.feature)
    if not observations or len({row.feature for row in observations}) != len(observations):
        raise ValueError("nonempty, unique feature observations required")
    for row in observations:
        if row.event != event:
            raise ValueError("source event identity differs from the forecast event")
        if max(instant(row.published_at), instant(row.first_observed_at)) > cutoff:
            raise ValueError("this source version was unavailable at the decision cutoff")
    content = {"schema": SCHEMA, "synthetic": True, "event": asdict(event),
               "cutoff_at": cutoff.isoformat(),
               "observations": [asdict(row) for row in observations]}
    return {**content, "snapshot_sha256": digest(content)}


def read_shared_source(path, expected_sha256):
    """Read exact cached bytes without rewriting them or making a request."""
    check_pin(expected_sha256)
    path = Path(path).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("shared source must be a regular immutable reference")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError("shared source content changed")
    return payload


def _commit(path, payload):
    """Publish a complete immutable file; interrupted temporaries are not receipts."""
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("checkpoint symlink rejected")
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("immutable checkpoint bytes changed")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    try:
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != payload:
                raise ValueError("immutable checkpoint publication conflict")
            return False
        return True
    finally:
        temporary.unlink(missing_ok=True)


class FixtureJournal:
    """Synthetic completion accounting, never a real native-model fit counter."""
    def __init__(self, root, experiment, snapshot_sha256, code_sha256):
        if not isinstance(experiment, Experiment):
            raise ValueError("registered NBA experiment required")
        check_pin(snapshot_sha256); check_pin(code_sha256)
        self.root = Path(root).absolute()
        if any(parent.is_symlink() for parent in (self.root, *self.root.parents)):
            raise ValueError("checkpoint root symlink rejected")
        self.context = {"schema": SCHEMA, "synthetic": True, "league": "nba",
            "experiment_sha256": experiment.identity, "snapshot_sha256": snapshot_sha256,
            "code_sha256": code_sha256}
        _commit(self.root / "context.json", canonical(self.context))

    def _unit(self, slot):
        if not isinstance(slot, str) or re.fullmatch(r"[a-z][a-z0-9_]*", slot) is None:
            raise ValueError("explicit component slot required")
        return digest({"context": self.context, "slot": slot})

    def _completed(self, unit):
        path = self.root / unit / "completed.json"
        started_path = path.parent / "started.json"
        for receipt_path in (path, started_path):
            if any(parent.is_symlink() for parent in (receipt_path, *receipt_path.parents)):
                raise ValueError("checkpoint symlink rejected before receipt read")
        if not path.exists():
            return None
        receipt = json.loads(path.read_text())
        if (receipt.get("unit_id") != unit or receipt.get("context") != self.context
                or receipt.get("state") != "completed_fixture_unit"
                or receipt.get("unit_id") != self._unit(receipt.get("slot"))):
            raise ValueError("completed checkpoint identity changed")
        started = {"unit_id": unit, "context": self.context, "slot": receipt["slot"], "state": "started"}
        if started_path.read_bytes() != canonical(started):
            raise ValueError("completion has no matching start receipt")
        read_shared_source(self.root / unit / "artifact.fixture", receipt["artifact_sha256"])
        return receipt

    def begin(self, slot):
        unit = self._unit(slot)
        if self._completed(unit) is not None:
            return {"unit_id": unit, "work_required": False, "reused_fixture_units": 1}
        _commit(self.root / unit / "started.json", canonical(
            {"unit_id": unit, "context": self.context, "slot": slot, "state": "started"}))
        return {"unit_id": unit, "work_required": True, "reused_fixture_units": 0}

    def complete(self, slot, artifact):
        unit = self._unit(slot)
        self._completed(unit)  # Reject redirected receipt paths before reading a start receipt.
        if not isinstance(artifact, bytes) or not artifact:
            raise ValueError("nonempty invented artifact bytes required")
        started = {"unit_id": unit, "context": self.context, "slot": slot, "state": "started"}
        if (self.root / unit / "started.json").read_bytes() != canonical(started):
            raise ValueError("exact prior start receipt required")
        _commit(self.root / unit / "artifact.fixture", artifact)
        receipt = {"unit_id": unit, "context": self.context, "slot": slot,
            "state": "completed_fixture_unit", "artifact_sha256": hashlib.sha256(artifact).hexdigest()}
        created = _commit(self.root / unit / "completed.json", canonical(receipt))
        self._completed(unit)
        return {"new_fixture_units": int(created), "reused_fixture_units": int(not created), "real_model_fits": 0}

    def counts(self):
        completed = 0
        started = list(self.root.glob("*/started.json"))
        for path in started:
            if any(parent.is_symlink() for parent in (path, *path.parents)):
                raise ValueError("checkpoint symlink rejected before receipt read")
            receipt = json.loads(path.read_text())
            expected = {"unit_id": path.parent.name, "context": self.context,
                        "slot": receipt.get("slot"), "state": "started"}
            if (self._unit(receipt.get("slot")) != path.parent.name
                    or path.read_bytes() != canonical(expected)):
                raise ValueError("started checkpoint identity changed")
            completed += int(self._completed(path.parent.name) is not None)
        if len(list(self.root.glob("*/completed.json"))) != completed:
            raise ValueError("orphaned completion receipt")
        return {"completed_fixture_units": completed, "pending_fixture_units": len(started) - completed,
                "real_model_fits": 0}


def walkthrough():
    event = NBAEvent("nba", "invented_provider", "invented_game", 2025)
    raw = b'{"invented_pace": 99.0}'
    raw_pin = hashlib.sha256(raw).hexdigest()
    observation = Observation(event, "invented_pace", 99.0, "2025-01-02T17:00:00Z",
                              "2025-01-02T17:01:00Z", "2025-01-02T18:00:00Z", raw_pin)
    snapshot = feature_snapshot(event, "2025-01-02T19:00:00Z", [observation])
    jobs = validate_registration(registration())
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "invented-shared-response.json"
        source.write_bytes(raw)
        read_shared_source(source, raw_pin)
        journal = FixtureJournal(root / "nba-derived", jobs[0], snapshot["snapshot_sha256"],
                                 digest({"invented_code": "fixed-public-protocol"}))
        journal.begin("probability")
        first = journal.complete("probability", b"invented artifact; not an estimator")
        reopened = FixtureJournal(root / "nba-derived", jobs[0], snapshot["snapshot_sha256"],
                                  digest({"invented_code": "fixed-public-protocol"}))
        replay = reopened.begin("probability")
        counts = reopened.counts()
    return {"data_kind": "entirely_invented", "league": "nba", "registered_jobs": len(jobs),
        "registration": [asdict(job) for job in jobs], "first_completion": first,
        "reentry": replay, "counts": counts, "actual_model_fits": 0, "network_requests": 0,
        "provider_credits": 0, "owner_execution_proved": False}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, sort_keys=True))
