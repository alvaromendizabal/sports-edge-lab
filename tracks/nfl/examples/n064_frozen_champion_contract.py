"""Credential-free, invented-input research-contract demonstration.

This is not the private NFL model, active recipe, or an outcome forecast.
Run tests from repository root with python -m unittest discover -s
tracks/nfl/tests -p test_n064_frozen_champion_contract.py.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Iterable


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone-aware clock required")
    return result


@dataclass(frozen=True)
class Label:
    event_id: str
    occurred_at: str
    available_at: str
    value: float


def training_key(labels: Iterable[Label], frozen_at: str, recipe: str,
                 schema: str, algorithm: str) -> str:
    """Future labels cannot alter an earlier frozen training snapshot."""
    cutoff = utc(frozen_at)
    eligible = sorted((x for x in labels
                       if utc(x.occurred_at) < cutoff
                       and utc(x.available_at) < cutoff), key=lambda x: x.event_id)
    if len({x.event_id for x in eligible}) != len(eligible):
        raise ValueError("duplicate event")
    body = {"cutoff": frozen_at, "recipe": recipe, "schema": schema,
            "algorithm": algorithm, "labels": [vars(x) for x in eligible]}
    return sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest()


def admit_forward_fit(recipe: str, selected_by_metric: dict[str, str],
                      ensemble_components: tuple[str, ...] = ()) -> None:
    permitted = set(selected_by_metric.values()) | set(ensemble_components)
    if recipe not in permitted:
        raise ValueError("unselected candidate cannot enter forward refitting")


def preserve_issue(ledger: dict[str, dict], issue_id: str, prediction: dict) -> str:
    """Same identity with different contents is a conflict, never an update."""
    copy = json.loads(json.dumps(prediction, sort_keys=True, allow_nan=False))
    if issue_id in ledger:
        if ledger[issue_id] != copy:
            raise ValueError("immutable issue conflict")
        return "reused"
    ledger[issue_id] = copy
    return "new"


def retain_experiment(history: list[dict], experiment: dict) -> None:
    """A negative combination remains available for other registered contexts."""
    if any(x["experiment_id"] == experiment["experiment_id"] for x in history):
        raise ValueError("experiment identity already recorded")
    history.append(json.loads(json.dumps(experiment, allow_nan=False)))
