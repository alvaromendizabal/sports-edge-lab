"""Invented injury-report snapshots with explicit pregame information clocks.

This example accepts invented inputs only. It has no real games, players,
source responses, active features, models, provider calls or financial actions.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import json

from .contracts import timestamp

HORIZONS = {"T120": 120, "T60": 60, "LATEST_BEFORE_TIP": 0}
MODES = {"ACTUAL_POSSESSION", "PUBLICATION_RECONSTRUCTION"}
STATUSES = {"Out", "Doubtful", "Questionable", "Probable", "Available", "Unknown"}


def validate(snapshot: dict) -> dict:
    """Reject impossible clocks and contradictory or ambiguous row identities."""
    row = deepcopy(snapshot)
    if row.get("data_kind") != "INVENTED":
        raise ValueError("the public example accepts invented inputs only")
    for field in ("event", "team", "report_id"):
        if not isinstance(row.get(field), str) or not row[field]:
            raise ValueError("an event, team and immutable report identity are required")
    publication = timestamp(row["published_at"])
    if row.get("possessed_at") is not None and timestamp(row["possessed_at"]) < publication:
        raise ValueError("possession cannot precede publication")
    if row.get("submission") not in {"SUBMITTED", "NOT_YET_SUBMITTED", "UNKNOWN"}:
        raise ValueError("explicit report submission state required")
    if type(row.get("complete")) is not bool or not isinstance(row.get("players"), list):
        raise ValueError("explicit parse completeness and player rows required")
    identities = set()
    for player in row["players"]:
        name = player.get("player")
        if not isinstance(name, str) or not name or name in identities:
            raise ValueError("unique player identity required within a snapshot")
        identities.add(name)
        if player.get("status") not in STATUSES:
            raise ValueError("unsupported status requires explicit normalization review")
    if row["submission"] != "SUBMITTED" and row["players"]:
        raise ValueError("unsubmitted or unknown reports cannot assert player states")
    return row


def snapshot_union(snapshots: list[dict]) -> list[dict]:
    """Exact repeats coalesce; an immutable report ID cannot acquire new content."""
    records = {}
    for item in snapshots:
        row = validate(item)
        identity = (row["event"], row["team"], row["report_id"])
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if identity in records and records[identity][0] != canonical:
            raise ValueError("immutable report content changed")
        records[identity] = (canonical, row)
    return [records[key][1] for key in sorted(records)]


def select_snapshot(snapshots: list[dict], *, event: str, team: str,
                    tip_at: str, horizon: str, mode: str = "ACTUAL_POSSESSION") -> dict:
    """Select one whole team report, retaining publication and possession separately.

    T60/T120 admit observations exactly at their cutoff. Latest-before-tip uses
    a strict boundary. A publication reconstruction never becomes an issued
    forecast or evidence that a report was possessed at a historical cutoff.
    """
    if horizon not in HORIZONS or mode not in MODES:
        raise ValueError("explicit supported horizon and mode required")
    cutoff = timestamp(tip_at) - timedelta(minutes=HORIZONS[horizon])
    before = (lambda value: value < cutoff) if horizon == "LATEST_BEFORE_TIP" else (lambda value: value <= cutoff)
    candidates, unknown = [], []
    for row in snapshot_union(snapshots):
        if row["event"] != event or row["team"] != team or not before(timestamp(row["published_at"])):
            continue
        if mode == "ACTUAL_POSSESSION":
            if row.get("possessed_at") is None:
                unknown.append(row)
                continue
            if not before(timestamp(row["possessed_at"])):
                continue
        candidates.append(row)
    result = {"data_kind": "INVENTED", "event": event, "team": team,
              "tip_at": tip_at, "horizon": horizon, "cutoff_at": cutoff.isoformat(),
              "mode": mode, "prospective_forecast_claimed": False,
              "status": "MISSING_ELIGIBLE_REPORT", "snapshot": None,
              "player_rows": [], "new_fits": 0, "new_forecasts": 0, "new_orders": 0}
    latest = max((timestamp(row["published_at"]) for row in candidates), default=None)
    if unknown and (latest is None or max(timestamp(row["published_at"]) for row in unknown) >= latest):
        result["status"] = "UNKNOWN_POSSESSION_CLOCK"
        return result
    if latest is None:
        return result
    newest = [row for row in candidates if timestamp(row["published_at"]) == latest]
    if len(newest) != 1:
        result["status"] = "CONFLICTING_REPORTS_AT_PUBLICATION_CLOCK"
        return result
    selected = newest[0]
    result["snapshot"] = deepcopy(selected)
    if selected["submission"] != "SUBMITTED":
        result["status"] = selected["submission"]
    elif not selected["complete"]:
        result["status"] = "INCOMPLETE_REPORT_PARSE"
    elif any(player["status"] == "Unknown" for player in selected["players"]):
        result["status"] = "UNKNOWN_PLAYER_STATUS"
    else:
        result["status"] = "ELIGIBLE_REPORT_SNAPSHOT"
        result["player_rows"] = deepcopy(selected["players"])
    return result


def player_status(selection: dict, player: str) -> dict:
    """Absence and reporting gaps never assert that a player is healthy."""
    if selection["status"] != "ELIGIBLE_REPORT_SNAPSHOT":
        return {"status": None, "reason": selection["status"], "absence_probability": None}
    for row in selection["player_rows"]:
        if row["player"] == player:
            return {"status": row["status"], "reason": "REPORTED_CATEGORICAL_STATUS",
                    "absence_probability": None}
    return {"status": None, "reason": "ABSENT_FROM_SELECTED_REPORT", "absence_probability": None}


def preregistered_arms() -> dict:
    """Specify an experiment contract without fitting or claiming useful impacts."""
    return {"data_kind": "INVENTED", "arms": [
        {"name": "FIXED_BASELINE", "status": "REGISTERED_NOT_EXECUTED"},
        {"name": "INJURY_ONLY", "status": "BLOCKED_MISSING_CAUSAL_INPUTS"},
        {"name": "BASELINE_PLUS_INJURY", "status": "BLOCKED_MISSING_CAUSAL_INPUTS"},
        {"name": "INJURY_INTERACTIONS", "status": "BLOCKED_MISSING_CAUSAL_INPUTS"}],
        "selection": "PRIOR_SEASON_CHRONOLOGICAL_TRAINING_ONLY",
        "refit_cadence": "WEEKLY", "current_season_selection": False,
        "preprocessing_and_calibration": "TRAINING_ONLY",
        "required_inputs": ["PRIOR_FIXED_RECIPE", "ASOF_INJURY_SNAPSHOTS",
                            "LABEL_AVAILABILITY_BEFORE_TRAINING_ORIGIN",
                            "CAUSAL_MINUTES_AND_PLAYER_CONTRIBUTIONS",
                            "CAUSAL_REPLACEMENT_CONTRIBUTIONS_FOR_INTERACTIONS"],
        "status_probability_conversion": None, "existing_forecasts_revised": False,
        "new_fits": 0, "new_forecasts": 0, "new_orders": 0}


def invented_snapshot(**changes) -> dict:
    row = {"data_kind": "INVENTED", "event": "invented-game", "team": "Example Home",
           "report_id": "invented-report-1", "published_at": "2035-01-10T16:00:00Z",
           "possessed_at": "2035-01-10T16:05:00Z", "submission": "SUBMITTED",
           "complete": True, "players": [{"player": "Example Player", "status": "Questionable"}]}
    row.update(changes)
    return row


if __name__ == "__main__":
    reports = [invented_snapshot(), invented_snapshot(report_id="invented-report-2",
        published_at="2035-01-10T18:30:00Z", possessed_at="2035-01-10T19:05:00Z",
        players=[{"player": "Example Player", "status": "Out"}])]
    print(json.dumps({"selections": [select_snapshot(reports, event="invented-game",
        team="Example Home", tip_at="2035-01-10T20:00:00Z", horizon=horizon, mode=mode)
        for mode in sorted(MODES) for horizon in HORIZONS], "protocol": preregistered_arms()}, indent=2))
