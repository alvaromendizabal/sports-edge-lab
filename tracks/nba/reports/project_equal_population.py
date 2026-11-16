"""Convert the private, authenticated evaluator export to dashboard aggregates.

The private evaluator owns game memberships, recipe identities, source lineage
and scoring. This projection publishes only model descriptions, counts,
membership fingerprints and computed scores. It never fills missing rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from equal_population_public import METRICS, validate_public

FAMILIES = {
    "hgb": "Histogram gradient boosting", "hist_gradient_boosting": "Histogram gradient boosting",
    "histgradientboosting": "Histogram gradient boosting", "logistic": "Logistic regression",
    "logistic_ridge": "Logistic ridge", "ridge": "Ridge regression",
    "market_only": "Market-only model", "extra_trees": "Extra Trees",
    "xgboost": "XGBoost", "catboost": "CatBoost", "lightgbm": "LightGBM",
    "preserved_catboost": "Preserved CatBoost", "preserved_lightgbm": "Preserved LightGBM",
    "preserved_ensemble_prior_oof_raw_components": "Preserved prior-OOF ensemble",
}


def _metrics(source):
    if source is None:
        return None
    return {key: source[key] for key in sorted(METRICS) if key in source}


def public_alias(identity):
    # Registry growth must not rename an already displayed candidate. This is
    # a one-way display token, not an exact recipe or model-artifact fingerprint.
    return 'candidate-' + hashlib.sha256(('nba-public-v1\0' + identity).encode()).hexdigest()[:12]


def project(value, source_pin, observed_at_utc):
    if value.get("schema") != "sel.nba.b089.equal_cohort_scoreboard.v1":
        raise ValueError("Unsupported private evaluator schema")
    protocol = value["protocol"]
    if (protocol.get("validation_seasons") != ["2024-25", "2025-26"]
            or protocol.get("test_season") != "2026-27"
            or protocol.get("current_test_previously_exposed") is not True
            or protocol.get("test_used_for_model_selection") is not False
            or protocol.get("all_completed_games_required") is not True
            or protocol.get("automatic_promotion") is not False):
        raise ValueError("Private evaluation violates owner validation/test protocol")
    identities = sorted({model["model_id"] for group in value["groups"] for model in group["models"]})
    aliases = {identity: public_alias(identity) for identity in identities}
    if len(set(aliases.values())) != len(aliases):
        raise ValueError('Public candidate alias collision')
    populations = {}
    groups = []
    for group in value["groups"]:
        if group.get("headline_denominator_reduced_to_intersection") is not False:
            raise ValueError("Private evaluator reduced the requested denominator")
        if group.get("automatic_champion_promotion") is not False:
            raise ValueError("Automatic promotion is not authorized")
        if group["season"] == "2026-27" and (group.get("test_is_untouched") is not False
                or group.get("selection_from_current_test_permitted") is not False):
            raise ValueError("Current-season exposure must stay explicit")
        season, phase = group["season"], group["phase"]
        required = group["required_population_count"]
        population_verified = bool(group.get("population_membership_verified", False)
                                   and group.get("population_complete_for_declared_scope", False))
        population = {"season": season, "phase": phase,
                      "required_games": required, "population_sha256": group["population_sha256"],
                      "population_verified": population_verified,
                      "as_of_utc": group.get("population_observed_at_utc")}
        key = (season, phase)
        if key in populations:
            old = populations[key]
            for field in ("required_games", "population_sha256", "population_verified"):
                if old[field] != population[field]:
                    raise ValueError("Private tracks disagree about the fixed season population")
        else:
            populations[key] = population
        if set(group["required_models"]) != {row["model_id"] for row in group["models"]}:
            raise ValueError("A required private model disappeared")
        rows = []
        for model in group["models"]:
            source_complete = model["eligible_for_full_population_comparison"]
            complete = bool(population_verified and source_complete)
            family = FAMILIES.get(model.get("family"), str(model.get("family") or "Unresolved family").replace("_", " "))
            alias = aliases[model["model_id"]]
            label = model.get("public_label") or f"{family} {alias}"
            blockers = []
            if model["missing_game_count"]:
                blockers.append("MISSING_GAME_PREDICTIONS")
            if model.get("invalid_predictions"):
                blockers.append("INVALID_OR_TIME_UNQUALIFIED_PREDICTIONS")
            if model.get("out_of_population_event_ids"):
                blockers.append("OUT_OF_POPULATION_PREDICTIONS")
            if not population_verified:
                blockers.append("POPULATION_MEMBERSHIP_PROOF_PENDING")
            if not source_complete and not blockers:
                blockers.append(model.get("eligibility_status") or "EVIDENCE_UNQUALIFIED")
            diagnostic = model.get("available_cohort_metrics")
            diagnostic_n = model["evaluated_game_count"] if diagnostic else 0
            diagnostic_status = model.get("available_metrics_scope") or "NO_QUALIFIED_METRICS"
            saved = model.get("saved_metric_receipt")
            if not diagnostic and isinstance(saved, dict):
                # A stored aggregate remains visible only as an explicitly
                # unverified diagnostic. It never proves its game membership.
                candidate = saved.get("saved_metrics", saved.get("metrics", saved))
                if isinstance(candidate, dict) and candidate.get("games", 0) > 0:
                    diagnostic = candidate
                    diagnostic_n = candidate["games"]
                    diagnostic_status = "SAVED_AGGREGATE_MEMBERSHIP_UNPROVEN"
            row = {"alias": alias, "label": label, "family": family,
                   "feature_count": model.get("feature_count"),
                   "qualified_games": model["evaluated_game_count"],
                   "missing_games": model["missing_game_count"],
                   "evaluated_population_sha256": model["evaluated_population_sha256"],
                   "evidence_qualified": model.get("evidence_qualified", source_complete),
                   "full_population_complete": complete,
                   "full_population_metrics": _metrics(model.get("full_population_metrics")) if complete else None,
                   "diagnostic_games": diagnostic_n,
                   "diagnostic_metrics": _metrics(diagnostic),
                   "diagnostic_evidence_status": diagnostic_status,
                   "full_metric_qualifications": {
                       "log_loss_is_positive_infinity": bool(complete and (model.get("full_population_metrics") or {}).get("log_loss_is_positive_infinity")),
                       "accuracy_policy": (model.get("full_population_metrics") or {}).get("accuracy_policy"),
                   },
                   "diagnostic_metric_qualifications": {
                       "log_loss_is_positive_infinity": bool((diagnostic or {}).get("log_loss_is_positive_infinity")),
                       "accuracy_policy": (diagnostic or {}).get("accuracy_policy"),
                   },
                   "blockers": blockers}
            rows.append(row)
        groups.append({"season": season, "phase": phase, "target": group["objective"],
                       "horizon_minutes": group["horizon_minutes"], "evidence_track": group["evidence_class"],
                       "required_games": required, "population_sha256": group["population_sha256"],
                       "population_verified": population_verified,
                       "required_candidate_count": len(rows),
                       "complete_candidate_count": sum(row["full_population_complete"] for row in rows),
                       "all_required_candidates_complete": bool(rows) and all(row["full_population_complete"] for row in rows),
                       "common_intersection_games": group["intersection_diagnostic"]["games"],
                       "models": rows})
    out = {"schema": "sel.nba.equal_population_dashboard.v1", "observed_at_utc": observed_at_utc,
           "source_receipt_sha256": source_pin["sha256"],
           "protocol": {"validation_seasons": ["2024-25", "2025-26"], "test_season": "2026-27",
                        "selection_basis": "VALIDATION_ONLY", "test_exposure_status": "PREVIOUSLY_EXPOSED",
                        "automatic_promotion": False, "intersection_is_headline_population": False},
           "evidence_track_labels": {
               "ORIGINAL_ISSUED": "Original issued before the declared horizon",
               "QUALIFIED_FIXED_REPLAY": "Qualified fixed-state replay",
               "LATER_FITTED_RECONSTRUCTION": "Later-fitted reconstruction",
               "EXPOSED_HISTORICAL_RECONSTRUCTION": "Exposed historical reconstruction",
               "FRONTIER_PRIOR_ONLY_RECONSTRUCTION": "Frontier prior-only reconstruction",
           }, "populations": [populations[key] for key in sorted(populations)], "groups": groups}
    return validate_public(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--observed-at-utc", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    body = Path(args.input).read_bytes()
    source_pin = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    if source_pin["sha256"] != args.expected_sha256:
        raise SystemExit("Private evaluator source hash does not match")
    out = project(json.loads(body), source_pin, args.observed_at_utc)
    encoded = (json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    Path(args.output).write_bytes(encoded)
    print(json.dumps({"status": "PUBLIC_PROJECTION_VERIFIED", "bytes": len(encoded),
                      "sha256": hashlib.sha256(encoded).hexdigest(), "groups": len(out["groups"]),
                      "source_pin": source_pin}, sort_keys=True))


if __name__ == "__main__":
    main()
