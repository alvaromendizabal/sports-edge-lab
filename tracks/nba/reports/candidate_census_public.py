"""Public aggregate projection of an authenticated all-candidate NBA audit.

Raw predictions, exact recipes, private identifiers and ordered feature lists
are excluded. Missing test evidence stays missing for every recovered candidate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import defaultdict

from equal_population_public import METRICS, validate_public
from project_equal_population import FAMILIES, public_alias
from model_market_public import scores, validate_public as validate_market

SEASONS = {2025: "2024-25", 2026: "2025-26", 2027: "2026-27"}


def _scores(value):
    return {k: value[k] for k in sorted(METRICS) if k in value} if value else None


def project_ledger(raw, expected_sha256, *, observed_at_utc, audit_verified_at_utc):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Candidate ledger fingerprint mismatch")
    source = json.loads(raw)
    if (source.get("schema") not in ("sel.nba.b090.all_season_candidate_ledger.v1",
                                     "sel.nba.b090.all_season_candidate_ledger.current_refresh.v1")
            or source.get("validation_policy") != "2024-25_AND_2025-26_ONLY;FIXED_PHASE_TARGET_HORIZON;GAME_WEIGHTED"
            or source.get("automatic_promotions") != 0 or source.get("new_estimator_fits") != 0
            or source.get("provider_credits") != 0):
        raise ValueError("Unsupported candidate audit policy")
    populations = {}
    for p in source["populations"]:
        key = (SEASONS[p["season_end_year"]], p["phase"])
        row = {"season": key[0], "phase": key[1], "required_games": p["required_games"],
               "population_sha256": p["population_sha256"], "population_verified": True,
               "as_of_utc": observed_at_utc}
        if key in populations and populations[key] != row:
            raise ValueError("Candidate tracks disagree about the fixed season population")
        populations[key] = row
    groups = defaultdict(list)
    scopes = set()
    for candidate in source["models"]:
        legacy_unselected = (candidate.get("source") == "AUTHENTICATED_B051_ORIGINAL_NATIVE_ARRAYS"
                             and candidate.get("validation_selection_eligible") is False)
        if (candidate.get("test_used_for_selection", False if legacy_unselected else None) is not False
                or candidate.get("automatic_promotion", False if legacy_unselected else None) is not False):
            raise ValueError("Candidate audit used test selection or promotion")
        alias = public_alias(candidate["model_id"])
        scope = (alias, candidate["phase"], candidate["objective"], candidate["horizon_minutes"])
        if scope in scopes:
            raise ValueError("Duplicate candidate scope")
        scopes.add(scope)
        family = FAMILIES.get(candidate["family"], candidate["family"].replace("_", " "))
        label = candidate.get("label") or f'{family} · {candidate["raw_feature_count"]} features · legacy'
        if candidate["negative_control"]:
            label = "Negative control · " + label
        for cell in candidate["evaluation_cells"]:
            season = SEASONS[cell["season_end_year"]]
            key = (season, candidate["phase"], candidate["objective"], candidate["horizon_minutes"], cell["evidence_class"])
            p = populations[key[:2]]
            n, missing, required = cell["games"], cell["missing_games"], cell["required_games"]
            if n + missing != required or required != p["required_games"] or cell["population_sha256"] != p["population_sha256"]:
                raise ValueError("Candidate changed its required game population")
            complete = bool(required > 0 and cell["complete_membership_and_declared_clock_checks"]
                            and n == required and not missing
                            and cell["evaluated_population_sha256"] == p["population_sha256"])
            if not complete and cell["full_population_metrics"] is not None:
                raise ValueError("Incomplete candidate has a full population score")
            available = cell.get("available_population_metrics")
            full = cell.get("full_population_metrics")
            blockers = []
            if missing: blockers.append("MISSING_GAME_PREDICTIONS")
            if cell.get("invalid_reasons"): blockers.append("INVALID_OR_TIME_UNQUALIFIED_PREDICTIONS")
            if not required: blockers.append("NO_COMPLETED_GAMES")
            row = {"alias": alias, "label": label, "family": family,
                   "feature_count": candidate["raw_feature_count"],
                   "qualified_games": n, "missing_games": missing,
                   "evaluated_population_sha256": cell["evaluated_population_sha256"],
                   "evidence_qualified": complete,
                   "full_population_complete": complete,
                   "full_population_metrics": _scores(full) if complete else None,
                   "full_descriptive_reconstruction_metrics": _scores(cell.get("full_descriptive_reconstruction_metrics")),
                   "strict_point_in_time_qualified_metrics": _scores(cell.get("strict_point_in_time_qualified_metrics")),
                   "original_source_possession_proved": cell.get("original_source_possession_proved", False),
                   "independent_clean_test_claim": cell.get("independent_clean_test_claim", False),
                   "diagnostic_games": n if available else 0,
                   "diagnostic_metrics": _scores(available),
                   "diagnostic_evidence_status": "EXPOSED_RECONSTRUCTION_SOURCE_AVAILABILITY_UNPROVED" if available else "NO_QUALIFIED_METRICS",
                   "full_metric_qualifications": {
                       "log_loss_is_positive_infinity": bool(complete and (full or {}).get("log_loss_is_positive_infinity")),
                       "accuracy_policy": (full or {}).get("accuracy_policy")},
                   "diagnostic_metric_qualifications": {
                       "log_loss_is_positive_infinity": bool((available or {}).get("log_loss_is_positive_infinity")),
                       "accuracy_policy": (available or {}).get("accuracy_policy")},
                   "blockers": blockers, "negative_control": candidate["negative_control"],
                   "in_preserved_shortlist": candidate.get("in_b089_shortlist", candidate.get("in_b089_registry", False)),
                   "historical_source_availability_proved": False,
                   "chronology_observations": copy.deepcopy(cell.get("chronology_observations", {}))}
            groups[key].append(row)
    public_groups = []
    for key, models in sorted(groups.items()):
        p = populations[key[:2]]
        count = sum(m["full_population_complete"] for m in models)
        public_groups.append({"season": key[0], "phase": key[1], "target": key[2],
            "horizon_minutes": key[3], "evidence_track": key[4],
            "required_games": p["required_games"], "population_sha256": p["population_sha256"],
            "population_verified": True, "required_candidate_count": len(models),
            "complete_candidate_count": count,
            "all_required_candidates_complete": bool(p["required_games"] and count == len(models)),
            "common_intersection_games": None,
            "models": sorted(models, key=lambda m: (m["negative_control"], m["family"], m["feature_count"] or 0, m["alias"]))})
    public = {"schema": "sel.nba.equal_population_dashboard.v1", "observed_at_utc": observed_at_utc,
        "audit_verified_at_utc": audit_verified_at_utc, "source_receipt_sha256": expected_sha256,
        "source_receipt_representation": "DECODED_JSON_UTF8_BYTES",
        "protocol": {"validation_seasons": ["2024-25", "2025-26"], "test_season": "2026-27",
            "selection_basis": "VALIDATION_ONLY", "test_exposure_status": "PREVIOUSLY_EXPOSED",
            "automatic_promotion": False, "intersection_is_headline_population": False},
        "evidence_track_labels": {
            "EXPOSED_HISTORICAL_RECONSTRUCTION": "Exposed historical reconstruction; source availability unproved",
            "QUALIFIED_FIXED_REPLAY": "Saved fixed-state reconstruction; historical availability unproved",
            "LATER_FITTED_RECONSTRUCTION": "Later-fitted reconstruction",
            "ORIGINAL_ISSUED": "Original issued before the declared horizon"},
        "census": {k: source["census"][k] for k in ("unique_recipe_ids", "model_phase_target_horizon_scopes",
            "evaluation_cells", "negative_control_scopes", "complete_prior_cells", "complete_current_cells")},
        "global_historical_recovery_complete": source.get("global_historical_recovery_complete", False),
        "strict_current_point_in_time_metric_cells": sum(m["strict_point_in_time_qualified_metrics"] is not None
            for g in public_groups if g["season"] == "2026-27" for m in g["models"]),
        "historical_source_availability_proved": False,
        "new_estimator_fits_in_audit": 0, "provider_credits_in_audit": 0,
        "populations": [populations[k] for k in sorted(populations)], "groups": public_groups}
    if sum(len(g["models"]) for g in public_groups) != source["census"]["evaluation_cells"]:
        raise ValueError("Candidate audit omitted evaluation cells")
    return validate_public(public)


def expand_saved_market_scope(saved, previous_population, population):
    """Retain authenticated paired scores; add explicit zero-evidence candidates."""
    validate_market(saved, previous_population)
    result = copy.deepcopy(saved)
    result["model_scoreboard_source_sha256"] = population["source_receipt_sha256"]
    added = 0
    for group in result["groups"]:
        matches = [g for g in population["groups"] if
            (g["season"], g["phase"], g["target"], g["horizon_minutes"], g["evidence_track"]) ==
            (group["season"], group["phase"], group["target"], group["horizon_minutes"], group["evidence_track"])]
        if len(matches) != 1 or matches[0]["population_sha256"] != group["population_sha256"]:
            raise ValueError("Expanded paired scope changed the test population")
        reference = matches[0]
        prior = {m["alias"]: m for m in group["models"]}
        rows = []
        excluded = {m["alias"]: m for m in group["common_diagnostic"]["excluded_candidates"]}
        for candidate in reference["models"]:
            alias = candidate["alias"]
            if alias in prior:
                row = prior.pop(alias)
                if row["model_games"] != candidate["qualified_games"]:
                    raise ValueError("Saved model coverage changed during public expansion")
                row["label"] = candidate["label"]
                row["feature_count"] = candidate["feature_count"]
            else:
                if candidate["qualified_games"] != 0:
                    raise ValueError("New current predictions require actual paired scoring")
                row = {"alias": alias, "label": candidate["label"], "feature_count": candidate["feature_count"],
                    "model_games": 0, "market_games": group["market_games"], "paired_games": 0,
                    "missing_model_games": group["required_games"], "missing_market_games": group["missing_market_games"],
                    "full_population_complete": False, "full_model_metrics": None, "full_market_metrics": None}
                excluded[alias] = {"alias": alias, "label": candidate["label"]}
                added += 1
            rows.append(row)
        if prior:
            raise ValueError("Expanded census dropped a previously required model")
        group["models"] = rows
        group["all_required_candidates_complete"] = all(m["full_population_complete"] for m in rows)
        group["common_diagnostic"]["excluded_candidates"] = sorted(excluded.values(), key=lambda m: m["alias"])
    result["scope_expansion"] = {"added_explicit_zero_evidence_candidate_cells": added,
        "saved_model_and_market_metric_values_changed": False, "new_scoring": 0,
        "original_paired_source_receipt_sha256": saved["source_receipt_sha256"],
        "candidate_census_source_receipt_sha256": population["source_receipt_sha256"]}
    # The saved score receipt stays pinned; the separate scope proof describes
    # additions and does not pretend that a dashboard projection rescored them.
    return validate_market(result, population)


def project_current_market(raw, expected_sha256, population):
    """Keep every required candidate and the full refreshed provider population.

    The private audit's per-candidate subsets are not a shared leaderboard.
    A zero all-candidate intersection stays explicitly empty; older subset
    diagnostics remain in their immutable, dated source artifact.
    """
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Current paired audit fingerprint mismatch")
    source = json.loads(raw)
    if (source.get("schema") != "sel.nba.b090.all_candidates.same_cohort_model_market.v1"
            or source.get("automatic_promotions") != 0
            or source.get("test_outcomes_used_for_selection") is not False
            or source.get("no_silently_reduced_candidate_or_game_population") is not True):
        raise ValueError("Current paired audit scope changed")
    groups = []
    for saved in source["groups"]:
        key = (SEASONS[saved["season_end_year"]], saved["phase"], saved["objective"],
               saved["horizon_minutes"], saved["evidence_class"])
        matches = [g for g in population["groups"] if
            (g["season"], g["phase"], g["target"], g["horizon_minutes"], g["evidence_track"]) == key]
        if len(matches) != 1:
            raise ValueError("Current paired group absent from candidate census")
        reference = matches[0]
        required, market_n = saved["required_games"], saved["market_qualified_games"]
        if (required != reference["required_games"] or required != source["required_games"]
                or saved["population_sha256"] != reference["population_sha256"]
                or len(saved["market_missing_event_ids"]) + market_n != required
                or saved["drop_zero_evidence_candidates_from_comparison"] is not False):
            raise ValueError("Current paired population changed")
        candidates = {m["alias"]: m for m in reference["models"]}
        if {public_alias(i) for i in saved["required_model_ids"]} != set(candidates):
            raise ValueError("Current paired audit omitted required candidates")
        rows = []
        for original in saved["rows"]:
            alias = public_alias(original["model_id"])
            if alias not in candidates:
                raise ValueError("Current paired candidate absent from registry")
            candidate = candidates[alias]
            if (original["required_games"] != required or original["population_sha256"] != saved["population_sha256"]
                    or original["model_games"] != candidate["qualified_games"]
                    or original["market_games"] != market_n):
                raise ValueError("Current paired candidate coverage changed")
            complete = bool(original["paired_games"] == required and candidate["full_population_complete"])
            if complete != original["full_population_comparison_available"]:
                raise ValueError("False current full-population comparison")
            rows.append({"alias": alias, "label": candidate["label"], "feature_count": candidate["feature_count"],
                "model_games": original["model_games"], "market_games": market_n,
                "paired_games": original["paired_games"], "missing_model_games": required-original["model_games"],
                "missing_market_games": required-market_n, "full_population_complete": complete,
                "full_model_metrics": scores(original["model_metrics"], required),
                "full_market_metrics": scores(original["market_metrics"], required),
                "full_comparison_evidence_status": "DESCRIPTIVE_RECONSTRUCTION_SOURCE_AVAILABILITY_UNPROVED" if complete else "INCOMPLETE",
                "independent_clean_test_claim": False})
        if saved["all_required_candidates_shared_games"] != 0:
            raise ValueError("Nonempty shared population requires its own common-score proof")
        provider_full = scores(saved["full_population_market_metrics"], required)
        if provider_full is not None and market_n != required:
            raise ValueError("Partial provider population has a full score")
        groups.append({"season": key[0], "phase": key[1], "target": key[2], "horizon_minutes": key[3],
            "evidence_track": key[4], "required_games": required, "population_sha256": saved["population_sha256"],
            "market_games": market_n, "missing_market_games": required-market_n,
            "all_required_candidates_complete": all(m["full_population_complete"] for m in rows),
            "provider_only_full_population_metrics": provider_full,
            "models": sorted(rows, key=lambda m: (m["label"], m["alias"])),
            "common_diagnostic": {"games": 0, "missing_required_games": required,
                "population_sha256": hashlib.sha256(b"[]").hexdigest(), "market_metrics": None,
                "models": [], "excluded_candidates": [{"alias": m["alias"], "label": m["label"]}
                    for m in rows if m["model_games"] == 0],
                "scope": "ALL_REQUIRED_CANDIDATES_NO_ZERO_EVIDENCE_CANDIDATE_DROPPED"}})
    result = {"schema": "sel.nba.public_model_market_comparison.v1", "as_of_utc": source["frozen_test_cutoff"],
        "source_receipt_sha256": expected_sha256, "provider": "DraftKings",
        "source_receipt_representation": "DECODED_JSON_UTF8_BYTES",
        "normalized_quotes_sha256": source["market_source_pin"]["sha256"],
        "model_scoreboard_source_sha256": population["source_receipt_sha256"],
        "current_test_previously_exposed": True, "automatic_promotion": False, "settlement_or_roi_claim": False,
        "comparison_requires_all_candidates": True, "groups": groups}
    return validate_market(result, population)


def attach_current_market_uncertainty(public, raw, expected_sha256, population):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Current uncertainty fingerprint mismatch")
    source = json.loads(raw)
    if (source.get("schema") != "sel.nba.b090.full197_paired_market_uncertainty.v1"
            or source.get("status") != "PASS" or source.get("automatic_promotions") != 0
            or source.get("current_outcomes_used_for_selection") is not False):
        raise ValueError("Current uncertainty policy changed")
    result = copy.deepcopy(public); seen = set()
    for saved in source["results"]:
        alias = public_alias(saved["model_id"]); metric = saved["metric"]
        matches = [(g,m) for g in result["groups"] if
            (g["target"],g["horizon_minutes"],g["evidence_track"]) ==
            (saved["objective"],saved["horizon_minutes"],saved["evidence_class"])
            for m in g["models"] if m["alias"] == alias]
        if len(matches) != 1: raise ValueError("Current uncertainty model scope mismatch")
        group, model = matches[0]; key = (alias,group["target"],group["horizon_minutes"],group["evidence_track"],metric)
        if (key in seen or not model["full_population_complete"]
                or saved["games"] != group["required_games"] or saved["required_games"] != group["required_games"]
                or saved["population_sha256"] != group["population_sha256"]
                or saved["current_test_used_for_selection_or_tuning"] is not False
                or saved["independent_clean_test_claim"] is not False or saved["promotion_allowed"] is not False
                or saved["negative_means_model_worse"] is not True):
            raise ValueError("Current uncertainty population or policy changed")
        for field, score in (("model_score",model["full_model_metrics"]),("market_score",model["full_market_metrics"])):
            if metric not in score or not math.isclose(saved[field],score[metric],rel_tol=0,abs_tol=1e-12):
                raise ValueError("Current uncertainty score disagrees with full population")
        expected = saved["model_score"]-saved["market_score"] if metric == "accuracy" else saved["market_score"]-saved["model_score"]
        if not math.isclose(expected,saved["model_improvement_over_market"],rel_tol=0,abs_tol=1e-12):
            raise ValueError("Current uncertainty improvement orientation changed")
        seen.add(key)
        model.setdefault("full_population_paired_uncertainty",{})[metric] = {k:copy.deepcopy(saved[k]) for k in
            ("model_improvement_over_market","paired_95pct_interval","interval_contains_zero","draws",
             "pacific_monday_week_blocks","negative_means_model_worse","relative_skill_vs_market")}
    expected_count = sum(len(set(m["full_model_metrics"] or {}) & set(m["full_market_metrics"] or {}))
        for g in result["groups"] for m in g["models"] if m["full_population_complete"])
    if len(seen) != source["metric_comparisons"] or len(seen) != expected_count:
        raise ValueError("Current full-population uncertainty omitted scored metrics")
    result["full_population_uncertainty"] = {"source_receipt_sha256": expected_sha256,
        "comparisons": len(seen),"draws": source["draws"],"week_blocks": source["pacific_monday_week_blocks"],
        "intervals_include_zero": source["intervals_include_zero"],
        "market_better_point_estimate_on_all_reported_metrics": source["market_better_point_estimate_on_all_reported_metrics"],
        "post_selection_descriptive": True,"multiple_comparison_adjusted": False,"current_selection_allowed": False}
    return validate_market(result,population)
