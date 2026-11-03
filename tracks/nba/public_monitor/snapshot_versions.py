"""Invented source-version examples, independent of private NBA estimators.

Frozen parameters do not imply identical predictions for different inputs.
Exact issued records and same-input oracle checks are separate contracts.
"""
from __future__ import annotations

from copy import deepcopy
import math

from .contracts import number, timestamp


KEYS = {"data_kind", "snapshot_id", "event", "model_version", "feature_version",
        "kind", "generated_at", "source_possessed_at", "tip_at", "cutoff_at",
        "horizon_minutes", "target", "side", "prediction"}
OBJECTIVES = {"winner": "home", "margin": "home_minus_away", "total": "combined"}


def validate_snapshot(row: dict) -> dict:
    if set(row) != KEYS or row.get("data_kind") != "INVENTED":
        raise ValueError("allowlisted invented prediction snapshot required")
    for field in ("snapshot_id", "event", "model_version", "feature_version"):
        if not isinstance(row[field], str) or not row[field].strip():
            raise ValueError("complete prediction-version identity required")
    if row["kind"] not in {"ISSUED", "RECONSTRUCTION"}:
        raise ValueError("issued and reconstructed evidence must be separate")
    if row["target"] not in OBJECTIVES or OBJECTIVES[row["target"]] != row["side"]:
        raise ValueError("unsupported objective or ordered side")
    number(row["prediction"], lower=0 if row["target"] in {"winner", "total"} else None,
           upper=1 if row["target"] == "winner" else None)
    generated = timestamp(row["generated_at"])
    possessed = timestamp(row["source_possessed_at"])
    cutoff = timestamp(row["cutoff_at"])
    tip = timestamp(row["tip_at"])
    if type(row["horizon_minutes"]) is not int or row["horizon_minutes"] not in {60, 120}:
        raise ValueError("supported declared horizon required")
    if (tip - cutoff).total_seconds() != 60 * row["horizon_minutes"]:
        raise ValueError("declared horizon and cutoff disagree")
    if possessed > generated:
        raise ValueError("input source was not possessed at generation")
    if row["kind"] == "ISSUED" and generated > cutoff:
        raise ValueError("late reconstruction cannot become a pre-cutoff issue")
    return deepcopy(row)


def snapshot_key(row: dict) -> tuple:
    return tuple(row[field] for field in ("snapshot_id", "event", "model_version", "target", "side"))


def append_snapshots(previous: list[dict], incoming: list[dict]) -> list[dict]:
    """New input versions append; reusing an identity with changed bytes rejects.

    The input lists are never modified. A fresh reconstruction is not an edit
    of an earlier issued prediction, even when the fitted parameters match.
    """
    result = {}
    for raw in previous + incoming:
        row = validate_snapshot(raw)
        key = snapshot_key(row)
        if key in result and result[key] != row:
            raise ValueError("immutable prediction snapshot was changed")
        result[key] = row
    return [result[key] for key in sorted(result)]


def select_issued_view(rows: list[dict], *, policy: str) -> list[dict]:
    """A predeclared time-only view; outcomes are not an input to this function.

    Multiple generations remain in the archive. This returns one issue per
    event/model/target/side/cutoff, never the best prediction after scoring.
    """
    if policy not in {"FIRST_BEFORE_CUTOFF", "LAST_BEFORE_CUTOFF"}:
        raise ValueError("predeclared time-only issue policy required")
    groups = {}
    for row in append_snapshots([], rows):
        if row["kind"] != "ISSUED":
            continue
        key = tuple(row[k] for k in ("event", "model_version", "target", "side", "cutoff_at"))
        groups.setdefault(key, []).append(row)
    output = []
    for key in sorted(groups):
        candidates = sorted(groups[key], key=lambda r: (timestamp(r["generated_at"]), r["snapshot_id"]))
        clocks = [timestamp(r["generated_at"]) for r in candidates]
        if len(clocks) != len(set(clocks)):
            raise ValueError("same-clock issue collision needs explicit resolution")
        output.append(candidates[0 if policy == "FIRST_BEFORE_CUTOFF" else -1])
    return output


def input_version_drift(previous: dict, incoming: dict) -> dict:
    old, new = validate_snapshot(previous), validate_snapshot(incoming)
    identity = ("event", "model_version", "target", "side", "cutoff_at")
    if any(old[k] != new[k] for k in identity):
        raise ValueError("drift requires one fixed-model comparison question")
    return {"data_kind": "INVENTED", "same_fitted_model": True,
            "same_feature_version": old["feature_version"] == new["feature_version"],
            "prediction_delta": new["prediction"] - old["prediction"],
            "old_kind": old["kind"], "new_kind": new["kind"],
            "overwrites_original": False, "prospective_credit": 0}


def verify_same_input_oracle(reference: dict, portable: dict) -> bool:
    """Different-source drift must not relax same-input numerical parity."""
    old, new = validate_snapshot(reference), validate_snapshot(portable)
    same_question = ("event", "model_version", "feature_version", "target", "side", "cutoff_at")
    if any(old[k] != new[k] for k in same_question):
        raise ValueError("oracle comparison requires the same input version")
    if not math.isclose(old["prediction"], new["prediction"], rel_tol=0, abs_tol=1e-12):
        raise ValueError("same-input oracle tolerance exceeded")
    return True


def invented_snapshot(*, snapshot_id="toy-original", feature_version="toy-source-a",
                      kind="ISSUED", generated_at="2035-11-01T18:00:00Z",
                      prediction=0.7, target="winner") -> dict:
    return {"data_kind": "INVENTED", "snapshot_id": snapshot_id, "event": "toy-game",
            "model_version": "toy-frozen-parameters", "feature_version": feature_version,
            "kind": kind, "generated_at": generated_at,
            "source_possessed_at": generated_at, "tip_at": "2035-11-01T20:00:00Z",
            "cutoff_at": "2035-11-01T19:00:00Z", "horizon_minutes": 60,
            "target": target, "side": OBJECTIVES[target], "prediction": prediction}


def walkthrough() -> dict:
    original = invented_snapshot()
    refresh = invented_snapshot(snapshot_id="toy-later-reconstruction", feature_version="toy-source-b",
                                kind="RECONSTRUCTION", generated_at="2035-11-02T12:00:00Z",
                                prediction=0.62)
    archive = append_snapshots([original], [refresh])
    issued = select_issued_view(archive, policy="LAST_BEFORE_CUTOFF")
    return {"data_kind": "INVENTED", "archived_versions": len(archive), "issued_view_rows": len(issued),
            "original_probability_unchanged": issued[0]["prediction"] == 0.7,
            "reconstruction_probability": refresh["prediction"],
            "drift": input_version_drift(original, refresh), "new_real_fits": 0,
            "provider_requests": 0}
