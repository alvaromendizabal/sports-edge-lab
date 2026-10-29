"""Credential-free NFL accounting and coordinator-contract demonstration.

The toy ledger is invented. Public real-run aggregates are validated separately;
this module does not reproduce private training, access AWS, or acquire data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECTS = {"nfl", "ncaa_fbs", "nba", "ncaa_basketball"}
SUBDIRECTORIES = {"src", "config", "data", "runs", "notebooks", "reports", "releases", "archive"}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reconcile_games(schedule, prediction_ids, *, season, target):
    """Outer-universe accounting; the season field governs postseason dates."""
    require(target in {"win", "margin", "total"}, "Unknown target")
    ids = [row["game_id"] for row in schedule]
    require(len(ids) == len(set(ids)), "Duplicate schedule identity")
    predictions = list(prediction_ids)
    require(len(predictions) == len(set(predictions)), "Duplicate prediction identity")
    require(set(predictions) <= set(ids), "Prediction outside schedule universe")
    result = {"season": season, "target": target, "accounted": 0, "scored": 0,
        "regular": 0, "postseason": 0, "ties": 0, "canceled": 0, "unplayed": 0,
        "eligible": 0, "predicted_eligible": 0, "missing_prediction": 0, "rows": []}
    for row in schedule:
        require(row["phase"] in {"REG", "POST"}, "Unknown phase")
        require(type(row["season"]) is int, "Football season must be explicit")
        home, away = row.get("home_score"), row.get("away_score")
        require((home is None) == (away is None), "Partial score pair")
        require(all(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0) for value in (home, away)), "Invalid score")
        if row["season"] != season:
            continue
        result["accounted"] += 1
        result["regular" if row["phase"] == "REG" else "postseason"] += 1
        if row.get("canceled"):
            require(home is None, "Canceled event cannot have invented final scores")
            result["canceled"] += 1; status = "CANCELED"
        elif home is None:
            result["unplayed"] += 1; status = "UNPLAYED"
        else:
            result["scored"] += 1
            tie = home == away
            result["ties"] += int(tie)
            if target == "win" and tie:
                status = "TIE_OUTSIDE_CONDITIONAL_BINARY_TARGET"
            else:
                result["eligible"] += 1
                if row["game_id"] in predictions:
                    result["predicted_eligible"] += 1; status = "PREDICTION_PRESENT"
                else:
                    result["missing_prediction"] += 1; status = "SCORED_WITHOUT_PREDICTION"
        result["rows"].append({"game_id": row["game_id"], "status": status})
    require(result["accounted"] == result["scored"] + result["canceled"] + result["unplayed"], "Accounting closure failed")
    return result


def admit_coordinator(document, *, filename):
    """Illustrative semantic check, not a real filesystem lock implementation."""
    if (not isinstance(document, dict) or document.get("schema") != "sports-edge-lab.workspace-layout.v1"
            or type(document.get("layout_version")) is not int or document["layout_version"] != 1):
        return {"status": "DEFERRED_UNKNOWN_CONTRACT", "mutation_allowed": False}
    projects = document.get("project_directories", [])
    directories = document.get("required_project_subdirectories", [])
    if (not isinstance(projects, list) or len(projects) != len(PROJECTS)
            or not all(isinstance(item, str) for item in projects) or set(projects) != PROJECTS
            or not isinstance(directories, list) or len(directories) != len(SUBDIRECTORIES)
            or not all(isinstance(item, str) for item in directories) or set(directories) != SUBDIRECTORIES):
        return {"status": "DEFERRED_LAYOUT_CONFLICT", "mutation_allowed": False}
    lock = document.get("organization_lock")
    if not isinstance(lock, str) or not re.fullmatch(r"\.[A-Za-z0-9_-]+\.lock", lock):
        return {"status": "DEFERRED_LOCK_CONTRACT", "mutation_allowed": False}
    return {"status": "RECOGNIZED_REQUIRES_ACTUAL_LOCK", "mutation_allowed": False,
        "observed_filename": filename, "advertised_lock": lock, "document_sha256": digest(document),
        "next_gate": "Acquire the actual advertised lock, then recheck the document identity before any mutation."}


def compare_panel(challenger, market):
    for key in ("season", "target", "policy", "games", "cohort_sha256"):
        require(challenger.get(key) == market.get(key), "Matched-cohort identity differs: " + key)
    require(type(challenger["games"]) is int and challenger["games"] > 0, "Invalid matched sample size")
    delta = {}
    for metric, reference in market["metrics"].items():
        value = challenger["metrics"].get(metric)
        require(type(value) in (int, float) and math.isfinite(value), "Missing/nonfinite challenger metric")
        require(type(reference) in (int, float) and math.isfinite(reference), "Missing/nonfinite MARKET metric")
        delta[metric] = value - reference
    return {"delta": delta, "ranking_permitted": challenger["season"] < 2026,
        "promotion_authorized": False, "qualification": "Separate complete historical family required"}


def validate_evidence(data):
    require(data.get("schema") == "sports-edge-lab.nfl.public-review.v1", "Unknown public evidence schema")
    require(data.get("accepted_reference") == "MARKET", "Reference identity changed")
    require(data.get("prediction_tables") == len(data["rows"]) == 316, "Prediction-table closure differs")
    require(sum(len(row["metrics"]) for row in data["rows"]) == data["recomputed_scalars"] == 948, "Metric-scalar closure differs")
    seasons = {row["season"]: row for row in data["seasons"]}
    require(len(seasons) == len(data["seasons"]) == 28 and set(seasons) == set(range(1999, 2027)), "Season universe differs")
    require(sum(row["accounted"] for row in seasons.values()) == data["all_accounted_games"] == 7549, "All-game accounting differs")
    for year, row in seasons.items():
        require(row["regular"] + row["postseason"] == row["accounted"], "Phase accounting differs")
        require(row["scored"] + row["canceled"] + row["unplayed"] == row["accounted"], "Status accounting differs")
        require(row["ties"] <= row["scored"], "Tie accounting differs")
    for year, cohort in ((2024, 280), (2025, 277)):
        require(seasons[year]["accounted"] == 285 and seasons[year]["retained"] == cohort, "Full season and saved cohort were conflated")
    require(seasons[2026]["scored"] == 107 and seasons[2026]["unplayed"] == 165 and seasons[2026]["retained"] == 77, "Monitoring/unplayed boundary changed")
    keys, groups = set(), {}
    for row in data["rows"]:
        require(re.fullmatch(r"N00[23]-[a-f0-9]{10}", row["model_id"]), "Unstable model identifier")
        require(re.fullmatch(r"[a-f0-9]{64}", row["cohort_sha256"]), "Missing cohort identity")
        require(row["season"] in (2024, 2025, 2026), "Unsupported result season")
        require((row["season"] == 2026) == (row["policy"] == "monitoring"), "Exposed monitoring policy changed")
        key = tuple(row[field] for field in ("season", "target", "policy", "model_id"))
        require(key not in keys, "Duplicate result identity"); keys.add(key)
        for value in row["metrics"].values():
            require(type(value) in (int, float) and math.isfinite(value), "Nonfinite metric")
        panel = {field: row[field] for field in ("season", "target", "policy", "games", "cohort_sha256")}
        panel["metrics"] = row["market_metrics"]
        group = tuple(row[field] for field in ("season", "target", "policy"))
        require(group not in groups or groups[group] == panel, "One panel mixes MARKET cohorts")
        groups[group] = panel
        compare_panel(row, panel)
    require(data["qualification"]["passed"] == 0 and data["qualification"]["n003_corrected_comparisons"] == 522, "Qualification boundary changed")
    text = canonical(data).decode()
    require(not re.search(r"/home/|s3://|AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|api[_-]?key|password|credential_value", text, re.I), "Private fields are not public evidence")
    return {"status": "PUBLIC_AGGREGATES_VALIDATED", "seasons": len(seasons), "game_identities": 7549,
        "prediction_tables": 316, "metric_scalars": 948, "matched_panels": len(groups), "private_training_reproduced": False}


def build_review(*, check=False):
    data = json.loads((HERE / "evidence.json").read_text())
    receipt = validate_evidence(data)
    template = (HERE / "review.template.html").read_text()
    embedded = canonical(data).decode().replace("<", "\\u003c")
    page = template.replace("__EVIDENCE_JSON__", embedded).replace("__EVIDENCE_SHA__", digest(data))
    require("__EVIDENCE_" not in page, "Unfilled review template")
    output = HERE / "review.html"
    if check:
        require(output.is_file() and output.read_text() == page, "Generated review differs; run contracts.py --build-review")
    else:
        output.write_text(page)
    return {**receipt, "review": "review.html", "evidence_sha256": digest(data), "generated_page_matches": True}


def demo(*, output):
    rows = [
        {"game_id": "DEMO_REG", "season": 2024, "phase": "REG", "date": "2024-09-01", "home_score": 23, "away_score": 20},
        {"game_id": "DEMO_POST", "season": 2024, "phase": "POST", "date": "2025-01-12", "home_score": 31, "away_score": 28},
        {"game_id": "DEMO_TIE", "season": 2024, "phase": "REG", "date": "2024-10-01", "home_score": 17, "away_score": 17},
        {"game_id": "DEMO_FUTURE", "season": 2026, "phase": "REG", "date": "2026-12-01", "home_score": None, "away_score": None},
        {"game_id": "DEMO_CANCELED", "season": 2022, "phase": "REG", "date": "2023-01-02", "home_score": None, "away_score": None, "canceled": True},
    ]
    contract = {"schema": "sports-edge-lab.workspace-layout.v1", "layout_version": 1,
        "project_directories": sorted(PROJECTS), "required_project_subdirectories": sorted(SUBDIRECTORIES),
        "organization_lock": ".example-coordinator.lock", "preserved_extra": {"owned_by": "invented coordinator"}}
    evidence = {"schema": "sports-edge-lab.nfl.demo.v1", "synthetic": True, "new_scientific_fits": 0,
        "input_sha256": digest(rows), "win": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="win"),
        "margin": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="margin"),
        "future": reconcile_games(rows, [], season=2026, target="win"),
        "canceled": reconcile_games(rows, [], season=2022, target="total"),
        "coordinator": admit_coordinator(contract, filename="workspace_layout_manifest.json")}
    destination = Path(output)
    if destination.exists():
        require(json.loads(destination.read_text()) == evidence, "Refuse changed or corrupted accepted demo artifact")
        return {"status": "REUSED", "new_work_units": 0, "artifact_sha256": digest(evidence), "synthetic": True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="nfl-demo-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(evidence)); stream.flush(); os.fsync(stream.fileno())
        require(json.loads(Path(path).read_text()) == evidence, "Staged demo verification failed")
        os.replace(path, destination)
    finally:
        Path(path).unlink(missing_ok=True)
    return {"status": "CREATED", "new_work_units": 1, "artifact_sha256": digest(evidence), "synthetic": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-review", action="store_true")
    action.add_argument("--build-review", action="store_true")
    action.add_argument("--demo", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.demo:
        parser.error("--demo requires --output") if args.output is None else None
        result = demo(output=args.output)
    else:
        result = build_review(check=args.check_review)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
