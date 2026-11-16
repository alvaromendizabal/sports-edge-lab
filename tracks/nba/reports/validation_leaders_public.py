"""Project previously scored validation leaders without private model recipes.

Every displayed season score must match a complete, authenticated public
population. This projection does not refit, score predictions, or promote a
model; current-test results have no influence on its retained ordering.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from equal_population_public import FORBIDDEN_KEYS, validate_public as validate_population
from project_equal_population import public_alias

SEASONS = ("2024-25", "2025-26")


def _reference(population, group, row, season):
    matches = [(g, m) for g in population["groups"]
               if (g["season"], g["phase"], g["target"], g["horizon_minutes"], g["evidence_track"]) ==
                  (season, group["phase"], group["target"], group["horizon_minutes"], row["seasons"][season]["evidence_track"])
               for m in g["models"] if m["alias"] == row["alias"]]
    if len(matches) != 1:
        raise ValueError("Validation leader identity or evidence track is not unique")
    return matches[0]


def validate_public(value, population):
    validate_population(population)
    def privacy(node):
        if isinstance(node, dict):
            if (FORBIDDEN_KEYS | {"exact_recipe", "original_constructor", "base_names", "derived_names"}).intersection(node):
                raise ValueError("Private validation leader field")
            for child in node.values(): privacy(child)
        elif isinstance(node, list):
            for child in node: privacy(child)
        elif isinstance(node, str) and any(x in node.lower() for x in
                ("s3://", "arn:aws:", "/home/", "/workspace/", "nba:espn:event:", "https://", "http://")):
            raise ValueError("Private validation leader content")
    privacy(value)
    if (value.get("schema") != "sel.nba.public_validation_leaders.v1"
            or value.get("selection_seasons") != list(SEASONS)
            or value.get("test_used_for_ranking") is not False
            or value.get("automatic_promotion") is not False
            or value.get("all_registered_candidates_complete") is not False
            or value.get("historical_reconstruction") is not True
            or value.get("model_scoreboard_source_sha256") != population["source_receipt_sha256"]):
        raise ValueError("Validation leader scope changed")
    seen = set()
    for group in value["groups"]:
        key = (group["phase"], group["target"], group["horizon_minutes"], group["metric"])
        if key in seen or group["eligible_candidates"] < len(group["leaders"]) or not group["leaders"]:
            raise ValueError("Invalid validation leader group")
        seen.add(key)
        previous = None
        if "leading_score_tie_count" in group:
            tied = sum(m["pooled_metric"] == group["leaders"][0]["pooled_metric"] for m in group["leaders"])
            if group["leading_score_tie_count"] < tied:
                raise ValueError("Validation ties were omitted")
        for row in group["leaders"]:
            if set(row["seasons"]) != set(SEASONS):
                raise ValueError("Validation leader needs both complete seasons")
            weighted, total = 0.0, 0
            for season in SEASONS:
                g, m = _reference(population, group, row, season)
                s = row["seasons"][season]
                if (not g["population_verified"] or not m["full_population_complete"]
                        or s["games"] != g["required_games"]
                        or s["population_sha256"] != g["population_sha256"]
                        or s["metric"] != m["full_population_metrics"][group["metric"]]
                        or row["label"] != m["label"] or row["feature_count"] != m["feature_count"]):
                    raise ValueError("Validation leader does not match a complete season score")
                weighted += s["games"] * (s["metric"] ** 2 if group["metric"] == "rmse" else s["metric"])
                total += s["games"]
            expected = math.sqrt(weighted / total) if group["metric"] == "rmse" else weighted / total
            if not math.isclose(row["pooled_metric"], expected, abs_tol=1e-12, rel_tol=0):
                raise ValueError("Validation pool does not match the two season scores")
            ordered = -row["pooled_metric"] if group["metric"] == "accuracy" else row["pooled_metric"]
            if previous is not None and ordered < previous:
                raise ValueError("Validation leader order changed")
            previous = ordered
        uncertainty = group.get("paired_validation_uncertainty")
        if uncertainty:
            if (uncertainty["leader_alias"] != group["leaders"][0]["alias"]
                    or uncertainty["runner_up_alias"] != group["leaders"][1]["alias"]
                    or uncertainty["test_outcomes_used"] is not False
                    or uncertainty["multiple_comparison_adjusted"] is not False
                    or uncertainty["post_selection_descriptive"] is not True):
                raise ValueError("Validation uncertainty scope changed")
    return copy.deepcopy(value)


def project(raw, expected_sha256, population):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Private owner table fingerprint mismatch")
    source = json.loads(raw)
    if source.get("schema") == "sel.nba.b090.independent_raw_validation_audit.v1":
        return project_full_audit(source, expected_sha256, population)
    p = source["protocol"]
    if (p["validation_seasons"] != list(SEASONS) or p["test_season"] != "2026-27"
            or p["test_used_for_model_selection"] is not False or p["automatic_promotion"] is not False
            or p["current_test_previously_exposed"] is not True):
        raise ValueError("Private validation policy changed")
    private_models = {(m["model_id"], m["phase"], m["objective"], m["horizon_minutes"]): m for m in source["models"]}
    groups = []
    for original in source["front_runners_by_validation_metric"]:
        if original["test_outcomes_used_for_ranking"] is not False or original["automatic_promotion"] is not False:
            raise ValueError("Current test cannot choose validation leaders")
        g = {"phase": original["phase"], "target": original["objective"],
             "horizon_minutes": original["horizon_minutes"], "metric": original["metric"],
             "eligible_candidates": original["eligible_candidates"], "leaders": []}
        for candidate in original["top_three"]:
            private = private_models[(candidate["model_id"], g["phase"], g["target"], g["horizon_minutes"])]
            row = {"alias": public_alias(candidate["model_id"]), "seasons": {},
                   "pooled_metric": candidate["pooled_metric"], "feature_count": candidate["feature_count"]}
            for season, year in zip(SEASONS, ("2025", "2026")):
                saved = private["validation_seasons"][year]
                row["seasons"][season] = {"games": candidate["per_season_games"][year],
                    "metric": candidate["per_season_metric"][year],
                    "evidence_track": saved["evidence_class"], "population_sha256": saved["population_sha256"]}
            _, public = _reference(population, g, row, SEASONS[0])
            row["label"] = public["label"]
            row["family"] = public["family"]
            g["leaders"].append(row)
        groups.append(g)
    return validate_public({"schema": "sel.nba.public_validation_leaders.v1", "as_of_utc": source["as_of_utc"],
        "source_receipt_sha256": expected_sha256,
        "model_scoreboard_source_sha256": population["source_receipt_sha256"],
        "selection_seasons": list(SEASONS), "test_used_for_ranking": False,
        "automatic_promotion": False, "all_registered_candidates_complete": False,
        "historical_reconstruction": True, "groups": groups}, population)


def project_full_audit(source, expected_sha256, population):
    """Copy the broad audit's ordered leaders and verify every displayed score."""
    policy = source["selection_policy"]
    if (policy["test_weight"] != 0 or policy["test_previously_exposed"] is not True
            or policy["negative_controls_ineligible"] is not True
            or source["automatic_promotions"] != 0):
        raise ValueError("Broader audit validation policy changed")
    groups = []
    for saved in source["validation_rankings_all_authentic_complete_candidates"]:
        if saved["automatic_promotion"] is not False or saved["test_outcomes_used_for_ranking"] is not False:
            raise ValueError("Broader audit used test selection")
        g = {"phase": saved["phase"], "target": saved["objective"],
             "horizon_minutes": saved["horizon_minutes"], "metric": saved["metric"],
             "eligible_candidates": saved["eligible_candidates"], "leaders": []}
        best = saved["top_ten"][0]["value"]
        ties = sum(m["value"] == best for m in saved["top_ten"])
        if ties == len(saved["top_ten"]) < saved["eligible_candidates"]:
            raise ValueError("Complete leading tie membership is not established")
        g["leading_score_tie_count"] = ties
        for candidate in saved["top_ten"][:3]:
            row = {"alias": public_alias(candidate["recipe_id"]), "seasons": {},
                   "pooled_metric": candidate["value"], "feature_count": candidate["feature_count"]}
            for season, year in zip(SEASONS, ("2025", "2026")):
                matches = [(a, m) for a in population["groups"] if
                    (a["season"], a["phase"], a["target"], a["horizon_minutes"]) ==
                    (season, g["phase"], g["target"], g["horizon_minutes"])
                    for m in a["models"] if m["alias"] == row["alias"] and m["full_population_complete"]]
                if len(matches) != 1 or matches[0][1].get("negative_control") is True:
                    raise ValueError("Broader validation leader lacks unique eligible evidence")
                a, m = matches[0]
                if candidate['feature_count'] is not None and candidate['feature_count'] != m['feature_count']:
                    raise ValueError('Broader audit feature count conflicts with the candidate ledger')
                row['feature_count'] = m['feature_count']
                metric = candidate["per_season_metrics"][year]
                row["seasons"][season] = {"games": metric["games"], "metric": metric[g["metric"]],
                    "evidence_track": a["evidence_track"], "population_sha256": a["population_sha256"]}
                row["label"] = m["label"]
                row["family"] = m["family"]
            g["leaders"].append(row)
        groups.append(g)
    return validate_public({"schema": "sel.nba.public_validation_leaders.v1",
        "as_of_utc": population["observed_at_utc"],
        "source_receipt_sha256": expected_sha256,
        "model_scoreboard_source_sha256": population["source_receipt_sha256"],
        "selection_seasons": list(SEASONS), "test_used_for_ranking": False,
        "automatic_promotion": False, "all_registered_candidates_complete": False,
        "historical_reconstruction": True, "groups": groups}, population)


def attach_uncertainty(public, raw, expected_sha256, population):
    """Attach independently computed, paired validation intervals by exact scope."""
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Validation uncertainty fingerprint mismatch")
    source = json.loads(raw)
    if (source.get("schema") != "sel.nba.b090.validation_leader_uncertainty.v1"
            or source.get("current_season_rows_read") != 0
            or source.get("fixed_validation_seasons") != list(SEASONS)
            or source.get("automatic_promotions") != 0):
        raise ValueError("Validation uncertainty policy changed")
    result = copy.deepcopy(public)
    matched = set()
    for saved in source["results"]:
        key = (saved["phase"], saved["objective"], saved["horizon_minutes"], saved["metric"])
        groups = [g for g in result["groups"] if (g["phase"],g["target"],g["horizon_minutes"],g["metric"]) == key]
        if len(groups) != 1 or key in matched:
            raise ValueError("Validation uncertainty group mismatch")
        group = groups[0]; matched.add(key)
        if (saved["eligible_candidate_count"] != group["eligible_candidates"]
                or saved["test_outcomes_used"] is not False or saved["promotion"] is not False):
            raise ValueError("Validation uncertainty candidate universe changed")
        for role, row in zip(("leader", "runner_up"), group["leaders"][:2]):
            if (public_alias(saved[role]["model_id"]) != row["alias"]
                    or not math.isclose(saved[role]["value"], row["pooled_metric"], rel_tol=0, abs_tol=1e-12)):
                raise ValueError("Validation uncertainty comparison does not match leader scores")
        for season in saved["seasons"]:
            p = group["leaders"][0]["seasons"]["2024-25" if season["season_end_year"] == 2025 else "2025-26"]
            if season["games"] != p["games"] or season["population_sha256"] != p["population_sha256"]:
                raise ValueError("Validation uncertainty season membership changed")
        group["paired_validation_uncertainty"] = {
            "leader_alias": group["leaders"][0]["alias"], "runner_up_alias": group["leaders"][1]["alias"],
            "leader_interval_95": saved["leader"]["descriptive_95pct_interval"],
            "runner_up_interval_95": saved["runner_up"]["descriptive_95pct_interval"],
            "leader_improvement": saved["leader_improvement_over_runner_up"],
            "paired_interval_95": saved["paired_95pct_interval"],
            "paired_interval_includes_zero": saved["paired_interval_includes_zero"],
            "resamples": saved["resamples"], "test_outcomes_used": False,
            "method": "PAIRED_PACIFIC_WEEK_BOOTSTRAP_WITHIN_EACH_VALIDATION_SEASON",
            "post_selection_descriptive": True, "multiple_comparison_adjusted": False}
    if len(matched) != len(result["groups"]):
        raise ValueError("Validation uncertainty groups omitted")
    result["uncertainty_source_receipt_sha256"] = expected_sha256
    return validate_public(result, population)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--scoreboard", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    value = project(Path(args.input).read_bytes(), args.expected_sha256,
                    json.loads(Path(args.scoreboard).read_bytes()))
    body = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    Path(args.output).write_bytes(body)
    print(json.dumps({"status": "PUBLIC_VALIDATION_LEADERS_VERIFIED", "groups": len(value["groups"]),
                      "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}))


if __name__ == "__main__":
    main()
