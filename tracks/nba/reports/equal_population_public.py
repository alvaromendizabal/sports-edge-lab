"""Strict public contract for the fixed NBA validation/test populations.

This validates a minimal analytical projection. It does not fit, score, choose
models, infer missing game identities, or turn a partial intersection into a
season-wide ranking. Private memberships remain in the owner audit.
"""
from __future__ import annotations

import copy
import math
import re
from datetime import datetime

SEASONS = ("2024-25", "2025-26", "2026-27")
METRICS = {"accuracy", "brier", "log_loss", "mae", "rmse", "crps"}
FORBIDDEN_KEYS = {
    "recipe_id", "model_id", "cohort_id", "game_id", "game_ids",
    "required_game_ids", "missing_game_ids", "predictions", "feature_names",
    "feature_values", "raw_payload", "source_path", "source_url", "account_id",
    "credentials", "access_token", "api_key", "yes_bid", "yes_ask", "no_bid",
    "no_ask", "member_path", "private_recipe", "ordered_features",
}


def _count(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"Invalid {label}")
    return value


def _hash(value, label, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"Invalid {label}")


def _scores(value, label):
    if value is None:
        return
    if not isinstance(value, dict) or set(value) - METRICS:
        raise ValueError(f"Unsupported {label}")
    for name, number in value.items():
        if number is None:
            continue
        if (isinstance(number, bool) or not isinstance(number, (float, int))
                or not math.isfinite(number) or number < 0):
            raise ValueError(f"Invalid {label}")
        if name in ("accuracy", "brier") and number > 1:
            raise ValueError(f"Invalid {label}")


def validate_public(value):
    """Return a copied, checked export; reject inconsistent full-score claims."""
    def privacy(node):
        if isinstance(node, dict):
            if FORBIDDEN_KEYS.intersection(node):
                raise ValueError("Private equal-population evidence field")
            for child in node.values():
                privacy(child)
        elif isinstance(node, list):
            for child in node:
                privacy(child)
        elif isinstance(node, str) and any(term in node.lower() for term in (
                "s3://", "arn:aws:", "/home/", "/workspace/", "nba:espn:event:",
                "http://", "https://")):
            raise ValueError("Private equal-population evidence content")

    privacy(value)
    if value.get("schema") != "sel.nba.equal_population_dashboard.v1":
        raise ValueError("Unsupported equal-population projection")
    datetime.fromisoformat(value["observed_at_utc"].replace("Z", "+00:00"))
    _hash(value["source_receipt_sha256"], "source receipt hash")
    p = value["protocol"]
    if (p["validation_seasons"] != list(SEASONS[:2])
            or p["test_season"] != SEASONS[2]
            or p["selection_basis"] != "VALIDATION_ONLY"
            or p["test_exposure_status"] != "PREVIOUSLY_EXPOSED"
            or p["automatic_promotion"] is not False
            or p["intersection_is_headline_population"] is not False):
        raise ValueError("Validation/test protocol changed")
    populations = {}
    for population in value["populations"]:
        key = (population["season"], population["phase"])
        if key[0] not in SEASONS or key[1] not in ("regular", "postseason") or key in populations:
            raise ValueError("Invalid or duplicate season population")
        _count(population["required_games"], "season population")
        if type(population["population_verified"]) is not bool:
            raise ValueError("Population verification must be explicit")
        _hash(population.get("population_sha256"), "population hash",
              nullable=not population["population_verified"])
        populations[key] = population
    group_keys = set()
    for group in value["groups"]:
        key = (group["season"], group["phase"], group["target"],
               group["horizon_minutes"], group["evidence_track"])
        if key in group_keys or key[:2] not in populations or key[2] not in ("winner", "margin", "total") or key[3] not in (60, 120):
            raise ValueError("Invalid or duplicate evaluation group")
        group_keys.add(key)
        population = populations[key[:2]]
        required = _count(group["required_games"], "required games")
        if (required != population["required_games"]
                or group["population_verified"] != population["population_verified"]
                or group.get("population_sha256") != population.get("population_sha256")):
            raise ValueError("Group reduced or changed the fixed population")
        models = group["models"]
        if group["required_candidate_count"] != len(models) or not models:
            raise ValueError("Required candidate membership is incomplete")
        aliases = set()
        complete = 0
        for model in models:
            alias = model["alias"]
            if not isinstance(alias, str) or not alias or alias in aliases:
                raise ValueError("Invalid or duplicate public model alias")
            aliases.add(alias)
            for text_key in ("label", "family"):
                if not isinstance(model[text_key], str) or not model[text_key]:
                    raise ValueError("Missing public model label")
            if model.get("feature_count") is not None:
                _count(model["feature_count"], "feature count")
            qualified = _count(model["qualified_games"], "qualified games")
            missing = _count(model["missing_games"], "missing games")
            if qualified + missing != required:
                raise ValueError("Model denominator does not reconcile")
            _hash(model.get("evaluated_population_sha256"), "evaluated membership hash", nullable=True)
            if type(model["full_population_complete"]) is not bool:
                raise ValueError("Full-population status must be explicit")
            eligible = (required > 0 and group["population_verified"] and missing == 0
                        and model.get("evaluated_population_sha256") == group["population_sha256"]
                        and model.get("evidence_qualified") is True)
            if model["full_population_complete"] != eligible:
                raise ValueError("False full-population completion claim")
            _scores(model.get("full_population_metrics"), "full-population scores")
            if eligible:
                if not model.get("full_population_metrics"):
                    raise ValueError("Completed model lacks full-population scores")
                complete += 1
            elif model.get("full_population_metrics") is not None:
                raise ValueError("Partial evidence presented as full-population scores")
            _scores(model.get("diagnostic_metrics"), "diagnostic scores")
            for prefix in ("full", "diagnostic"):
                qualifications = model.get(prefix + "_metric_qualifications", {})
                infinite = qualifications.get("log_loss_is_positive_infinity", False)
                if type(infinite) is not bool:
                    raise ValueError("Invalid infinite log-loss qualification")
                score_key = "full_population_metrics" if prefix == "full" else "diagnostic_metrics"
                if infinite and ((model.get(score_key) or {}).get("log_loss") is not None
                                 or (prefix == "full" and not eligible)):
                    raise ValueError("Infinite log-loss qualification conflicts with scores")
            diagnostic_n = _count(model.get("diagnostic_games", 0), "diagnostic games")
            if diagnostic_n > required:
                raise ValueError("Diagnostic exceeds declared season population")
            if diagnostic_n > qualified and model.get("diagnostic_evidence_status") != "SAVED_AGGREGATE_MEMBERSHIP_UNPROVEN":
                raise ValueError("Unproved diagnostic membership requires an explicit label")
            if not diagnostic_n and model.get("diagnostic_metrics"):
                raise ValueError("Scores without diagnostic games")
            if not isinstance(model.get("blockers"), list):
                raise ValueError("Missing per-model exclusion reasons")
        if group["complete_candidate_count"] != complete:
            raise ValueError("Complete candidate count mismatch")
        all_complete = (required > 0 and group["population_verified"] and complete == len(models))
        if group["all_required_candidates_complete"] != all_complete:
            raise ValueError("False all-candidate completion claim")
        common = group.get("common_intersection_games")
        if common is not None and (_count(common, "intersection games") > required):
            raise ValueError("Intersection exceeds fixed population")
    return copy.deepcopy(value)
