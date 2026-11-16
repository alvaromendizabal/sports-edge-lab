"""Aggregate-only ATS arithmetic; never an issued betting strategy."""
import collections
import hashlib
import json
import math

from project_equal_population import public_alias

SCHEMA = "sel.nba.public_ats_point_diagnostics.v1"
FLAGS = {
    "diagnostic_rule_registered_after_current_test_exposure": True,
    "historical_issued_strategy_claim": False,
    "calibrated_cover_probability_available": False,
    "probabilities_inferred": False,
    "settlement_or_roi_claim": False,
    "current_test_used_for_selection": False,
    "automatic_promotions": 0,
}
COUNTS = (
    "games", "required_games", "mathematical_cover_wins", "mathematical_cover_losses",
    "mathematical_pushes", "no_edge_games", "selected_point_choices",
    "home_point_choices", "away_point_choices", "non_push_decided_games",
)


def _references(market):
    return {(m["alias"], g["horizon_minutes"], g["evidence_track"]): (g, m)
            for g in market["groups"] if g["target"] == "margin"
            for m in g["models"]}


def validate_public(value, market):
    allowed = {"schema", "source_receipt_sha256", "source_receipt_representation",
        "observed_at_utc", "model_market_source_sha256", "required_games",
        "population_sha256", "required_margin_model_cells", "full_model_cells",
        "incomplete_required_cells", "summaries", "rule",
        "identical_official_game_membership_verified", *FLAGS}
    if set(value) != allowed or value["schema"] != SCHEMA or any(value.get(k) != v for k, v in FLAGS.items()):
        raise ValueError("ATS diagnostic policy changed")
    if (value["model_market_source_sha256"] != market["source_receipt_sha256"]
            or value["identical_official_game_membership_verified"] is not True):
        raise ValueError("ATS population provenance changed")
    required = _references(market); observed = set()
    if value["required_margin_model_cells"] != len(required):
        raise ValueError("ATS required candidate population reduced")
    full_keys = {k for k, (_, m) in required.items() if m["full_population_complete"]}
    for row in value["summaries"]:
        key = (row["alias"], row["horizon_minutes"], row["evidence_track"])
        if key in observed or key not in full_keys:
            raise ValueError("ATS full comparison scope changed")
        observed.add(key); group, model = required[key]
        if (row["label"] != model["label"] or row["required_games"] != group["required_games"]
                or row["games"] != value["required_games"]
                or group["population_sha256"] != value["population_sha256"]):
            raise ValueError("ATS full population changed")
        if set(row) != {"alias", "label", "horizon_minutes", "evidence_track",
                         "mathematical_cover_fraction_excluding_pushes", *COUNTS}:
            raise ValueError("Unapproved ATS summary field")
        if any(not isinstance(row[k], int) or row[k] < 0 for k in COUNTS):
            raise ValueError("Invalid ATS count")
        wins, losses, pushes, none = (row[k] for k in (
            "mathematical_cover_wins", "mathematical_cover_losses", "mathematical_pushes", "no_edge_games"))
        selected = wins + losses + pushes
        fraction = wins/(wins+losses) if wins+losses else None
        if (selected + none != row["games"] or selected != row["selected_point_choices"]
                or row["home_point_choices"] + row["away_point_choices"] != selected
                or wins + losses != row["non_push_decided_games"]
                or fraction != row["mathematical_cover_fraction_excluding_pushes"]):
            raise ValueError("ATS arithmetic mismatch")
    if observed != full_keys or len(observed) != value["full_model_cells"]:
        raise ValueError("ATS complete candidate omitted")
    for row in value["incomplete_required_cells"]:
        key = (row["alias"], row["horizon_minutes"], row["evidence_track"])
        if key in observed or key not in required or key in full_keys:
            raise ValueError("ATS missing candidate population changed")
        group, model = required[key]; observed.add(key)
        if (set(row) != {"alias", "label", "horizon_minutes", "evidence_track", "required_games",
                        "full_ats_diagnostics", "reason"}
                or row["label"] != model["label"] or row["full_ats_diagnostics"] is not None
                or row["required_games"] != group["required_games"]):
            raise ValueError("Incomplete ATS result invented")
    if observed != set(required):
        raise ValueError("ATS missing candidate omitted")
    return value


def project(raw, expected_sha256, market, required_official_game_ids):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("ATS diagnostic fingerprint mismatch")
    source = json.loads(raw)
    if (source.get("schema") != "sel.nba.b090.full197_ats_point_diagnostics.v1"
            or source.get("status") != "PASS" or source.get("new_fits") != 0
            or source.get("new_provider_calls") != 0
            or any(source.get(k) != v for k, v in FLAGS.items() if k != "current_test_used_for_selection")):
        raise ValueError("ATS source policy changed")
    references = _references(market); full_rows = collections.defaultdict(list)
    for row in source["rows"]:
        key = (public_alias(row["model_id"]), row["horizon_minutes"], row["evidence_class"])
        if key not in references or not references[key][1]["full_population_complete"]:
            raise ValueError("ATS raw row outside complete margin scope")
        for k in ("actual_bet_or_trade", "forecast_issued", "verified_sportsbook_settlement"):
            if row.get(k) is not False:
                raise ValueError("ATS raw row claims issued strategy or settlement")
        if row.get("calibrated_cover_probability") is not None or row.get("calibrated_push_probability") is not None:
            raise ValueError("ATS probability invented")
        actual, prediction, home_line, away_line = (row[k] for k in (
            "actual_home_minus_away", "predicted_home_minus_away", "home_spread_line", "away_spread_line"))
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (actual, prediction, home_line, away_line)):
            raise ValueError("Invalid ATS numeric source")
        edge = prediction + home_line
        side = "HOME" if edge > 0 else "AWAY" if edge < 0 else "NO_EDGE"
        residual = actual + home_line
        chosen = residual if side == "HOME" else -residual if side == "AWAY" else None
        outcome = "NO_EDGE" if side == "NO_EDGE" else "WIN" if chosen > 0 else "LOSS" if chosen < 0 else "PUSH"
        if (home_line != -away_line or side != row["chosen_side"]
                or outcome != row["mathematical_cover_outcome"]):
            raise ValueError("ATS orientation or point-choice arithmetic mismatch")
        full_rows[key].append(row)
    summaries = []
    for row in source["summaries"]:
        key = (public_alias(row["model_id"]), row["horizon_minutes"], row["evidence_class"])
        if key not in full_rows:
            raise ValueError("ATS aggregate lacks raw arithmetic")
        group, model = references[key]; rows = full_rows[key]
        ids = [r["official_game_id"] for r in rows]
        if len(ids) != len(set(ids)) or set(ids) != set(required_official_game_ids):
            raise ValueError("ATS official game membership changed")
        if (row["population_sha256"] != group["population_sha256"] or not row["complete_membership"]
                or any(row.get(k) is not False for k in (
                    "current_test_used_for_selection", "actual_bet_or_trade",
                    "original_issued_strategy", "verified_sportsbook_settlement"))
                or any(row.get(k) is not None for k in (
                    "calibrated_cover_probability", "calibrated_push_probability",
                    "comparison_against_market_cover_probability"))):
            raise ValueError("ATS aggregate qualification changed")
        outcomes = collections.Counter(r["mathematical_cover_outcome"] for r in rows)
        sides = collections.Counter(r["chosen_side"] for r in rows)
        for field, count in (
            ("games", len(rows)), ("mathematical_cover_wins", outcomes["WIN"]),
            ("mathematical_cover_losses", outcomes["LOSS"]), ("mathematical_pushes", outcomes["PUSH"]),
            ("no_edge_games", outcomes["NO_EDGE"]), ("home_point_choices", sides["HOME"]),
            ("away_point_choices", sides["AWAY"])):
            if row[field] != count: raise ValueError("ATS aggregate does not reproduce")
        errors = [r["predicted_home_minus_away"] - r["actual_home_minus_away"] for r in rows]
        for metric, score in (("mae", sum(map(abs, errors))/len(errors)),
                              ("rmse", math.sqrt(sum(v*v for v in errors)/len(errors)))):
            if not math.isclose(score, model["full_model_metrics"][metric], rel_tol=0, abs_tol=1e-11):
                raise ValueError("ATS model values differ from the full-population comparison")
        summaries.append({"alias": key[0], "label": model["label"], "horizon_minutes": key[1],
            "evidence_track": key[2], **{k: row[k] for k in COUNTS},
            "mathematical_cover_fraction_excluding_pushes": row["mathematical_cover_fraction_excluding_pushes"]})
    missing = []
    for row in source["incomplete_required_cells"]:
        key = (public_alias(row["model_id"]), row["horizon_minutes"], row["evidence_class"])
        if key not in references or row["full_ats_diagnostics"] is not None:
            raise ValueError("Invalid ATS missing scope")
        missing.append({"alias": key[0], "label": references[key][1]["label"],
            "horizon_minutes": key[1], "evidence_track": key[2], "required_games": row["required_games"],
            "full_ats_diagnostics": None, "reason": row["reason"]})
    return validate_public({
        "schema": SCHEMA, "source_receipt_sha256": expected_sha256,
        "source_receipt_representation": "DECODED_JSON_UTF8_BYTES",
        "observed_at_utc": market["as_of_utc"], "model_market_source_sha256": market["source_receipt_sha256"],
        "required_games": source["required_games"], "population_sha256": source["population_sha256"],
        "required_margin_model_cells": source["required_margin_model_cells"],
        "full_model_cells": source["full_model_cells"], "incomplete_required_cells": missing,
        "summaries": sorted(summaries, key=lambda r: (r["horizon_minutes"], r["evidence_track"], r["alias"])),
        "rule": source["rule"], "identical_official_game_membership_verified": True, **FLAGS}, market)
