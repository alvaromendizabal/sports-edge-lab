"""Strict disclosure and semantic checks for a sanitized NFL public snapshot.

This validates public aggregates; it neither authenticates private owner bytes nor
reproduces training. Unknown fields are rejected, including nested raw quotes and
production recipes. The exact generated page is bound by contracts.build_review.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = "sports-edge-lab.nfl.public-review.v2"
ALLOWED_FIELDS = {'$': ('as_of',
       'benchmarks',
       'cohorts',
       'common_provider_metrics',
       'disagreement_examples',
       'execution',
       'history',
       'limitations',
       'models',
       'provenance',
       'providers',
       'resolved_forecast_example',
       'schema',
       'season',
       'uncertainty',
       'upcoming',
       'weekly'),
 '$.benchmarks[]': ('accuracy',
                    'brier',
                    'correct',
                    'ece_10',
                    'games',
                    'horizon',
                    'label',
                    'log_loss',
                    'qualification',
                    'season'),
 '$.cohorts': ('current_cohort_sha256',
               'excluded_latest_final',
               'historical_binary_games',
               'historical_point_games',
               'kalshi_finals',
               'kalshi_non_ties',
               'latest_week',
               'latest_week_common_games',
               'latest_week_source_finals',
               'scored_finals',
               'scored_non_ties',
               'source_finals',
               'source_non_ties'),
 '$.cohorts.historical_binary_games': ('2024', '2025'),
 '$.cohorts.historical_point_games': ('2024', '2025'),
 '$.common_provider_metrics[]': ('accuracy',
                                 'bias',
                                 'brier',
                                 'cohort_sha256',
                                 'correct',
                                 'games',
                                 'label',
                                 'log_loss',
                                 'mae',
                                 'qualification',
                                 'rmse',
                                 'season',
                                 'target'),
 '$.disagreement_examples[]': ('actual_winner',
                               'away_score',
                               'away_team',
                               'disagreement_winner',
                               'game_id',
                               'home_score',
                               'home_team',
                               'kalshi_horizon',
                               'kalshi_pick',
                               'kickoff_utc',
                               'model',
                               'model_origin',
                               'model_pick',
                               'model_pick_probability_percent',
                               'qualification',
                               'season',
                               'week'),
 '$.execution': ('annual_base_cells_completed',
                 'annual_base_cells_registered',
                 'authorized_paid_calls',
                 'current_quote_capture_end_utc',
                 'current_quote_capture_start_utc',
                 'families',
                 'historical_study_elapsed_seconds',
                 'independently_scored_game_rows',
                 'new_base_fits',
                 'new_issued_forecasts',
                 'new_owner_fits',
                 'new_stack_fits',
                 'paid_credits',
                 'pairwise_blends_completed',
                 'pairwise_blends_registered',
                 'protected_original_refits',
                 'provider_calls',
                 'qualification',
                 'restored_annual_fits',
                 'restored_rolling_fit_uses',
                 'rooted_blocks',
                 'season_scalar_checks',
                 'source_final_games',
                 'source_play_by_play_rows',
                 'source_public_requests',
                 'source_statistics_team_rows',
                 'weekly_provider_scalar_checks'),
 '$.history[]': ('criterion', 'label', 'ranking_period', 'seasons', 'selection', 'target'),
 '$.history[].seasons[]': ('accuracy',
                           'bias',
                           'brier',
                           'correct',
                           'ece_10',
                           'games',
                           'log_loss',
                           'mae',
                           'rmse',
                           'season'),
 '$.models[]': ('accuracy',
                'all_losses_probability_50_to_60',
                'brier',
                'correct',
                'disagreements_lost',
                'disagreements_won',
                'ece_10',
                'evaluation',
                'games',
                'horizon',
                'label',
                'log_loss',
                'lost_disagreements_probability_50_to_60',
                'season'),
 '$.provenance': ('external_completion_receipt',
                  'owner_return_bytes',
                  'owner_return_sha256',
                  'physical_manifest_crc_payload_verification',
                  'public_scope',
                  'research_status'),
 '$.providers[]': ('coverage', 'provider', 'qualification', 'status'),
 '$.providers[].coverage[]': ('eligible', 'rows', 'season', 'target'),
 '$.resolved_forecast_example': ('correct',
                                 'feature_as_of_utc',
                                 'final',
                                 'game',
                                 'horizon',
                                 'issued_at_utc',
                                 'kickoff_utc',
                                 'model_margin_pick',
                                 'model_pick',
                                 'model_pick_probability_percent',
                                 'model_total',
                                 'qualification'),
 '$.uncertainty': ('advantage_supported', 'method', 'small_confidence_band_note', 'statement'),
 '$.upcoming': ('archived_early_cards',
                'games',
                'new_final_hour_issues',
                'next_kickoff_utc',
                'status',
                'week'),
 '$.weekly[]': ('common_games',
                'current_week_finals',
                'evaluation',
                'horizon_qualification',
                'kalshi_accuracy',
                'kalshi_brier',
                'kalshi_correct',
                'kalshi_log_loss',
                'kalshi_quote_horizon',
                'kalshi_right_disagreements',
                'label',
                'model_accuracy',
                'model_binary_games',
                'model_brier',
                'model_correct',
                'model_log_loss',
                'model_origin',
                'model_right_disagreements',
                'season',
                'week')}

FORBIDDEN = re.compile(r"s3://|arn:aws:|/home/|/workspace/|AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|https?://[^\s]+[?&](?:token|key|signature)=|n0[0-9]{2}_[a-z]|__direct[0-9]|X-Amz-(?:Signature|Credential|Security-Token)=|api[_-]?key\s*[:=]", re.I)
PROVIDERS = {"MARKET", "DraftKings", "PrizePicks", "Underdog", "Kalshi", "Polymarket"}

REQUIRED_FIELDS = {
    "$.models[]": {"label", "evaluation", "horizon", "season", "games", "correct", "accuracy", "log_loss", "brier", "ece_10"},
    "$.benchmarks[]": set(ALLOWED_FIELDS["$.benchmarks[]"]),
    "$.history[]": set(ALLOWED_FIELDS["$.history[]"]),
    "$.history[].seasons[]": {"season", "games"},
    "$.common_provider_metrics[]": {"season", "target", "label", "cohort_sha256", "qualification", "games"},
    "$.weekly[]": set(ALLOWED_FIELDS["$.weekly[]"]),
    "$.providers[]": set(ALLOWED_FIELDS["$.providers[]"]),
    "$.providers[].coverage[]": set(ALLOWED_FIELDS["$.providers[].coverage[]"]),
    "$.disagreement_examples[]": set(ALLOWED_FIELDS["$.disagreement_examples[]"]),
}
for _path in ("$.provenance", "$.cohorts", "$.cohorts.historical_binary_games", "$.cohorts.historical_point_games", "$.resolved_forecast_example", "$.upcoming", "$.uncertainty", "$.execution"):
    REQUIRED_FIELDS[_path] = set(ALLOWED_FIELDS[_path])


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_tree(value, path="$", field=""):
    if isinstance(value, dict):
        require(path in ALLOWED_FIELDS, "Unknown public object: " + path)
        require(set(value) <= set(ALLOWED_FIELDS[path]), "Unknown public fields: " + path)
        require(REQUIRED_FIELDS.get(path, set()) <= set(value), "Required public fields missing: " + path)
        for key, item in value.items():
            validate_tree(item, path + "." + key, key)
    elif isinstance(value, list):
        for item in value:
            validate_tree(item, path + "[]", field)
    elif isinstance(value, str):
        require(not FORBIDDEN.search(value), "Private source or recipe material is not public: " + path)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        require(math.isfinite(value), "Nonfinite public value: " + path)
        if field in {"accuracy", "brier", "ece_10", "model_accuracy", "kalshi_accuracy", "model_brier", "kalshi_brier"}:
            require(0 <= value <= 1, "Invalid bounded score: " + path)
        if field.endswith("log_loss") or field in {"mae", "rmse"}:
            require(value >= 0, "Negative loss: " + path)
    else:
        require(value is None or isinstance(value, bool), "Unsupported public value: " + path)


def validate_snapshot(data):
    require(set(data) == set(ALLOWED_FIELDS["$"]), "Incomplete or expanded public snapshot")
    require(data["schema"] == SCHEMA and data["season"] == 2026, "Unsupported public snapshot")
    validate_tree(data)
    provenance = data["provenance"]
    require(re.fullmatch(r"[0-9a-f]{64}", provenance["owner_return_sha256"] or ""), "Missing physical return identity")
    require(0 < provenance["owner_return_bytes"] < 150_000_000, "Invalid owner return size")
    require(provenance["physical_manifest_crc_payload_verification"] == "PASS", "Owner authentication not established")
    c = data["cohorts"]
    require(c["source_finals"] >= c["scored_finals"] >= c["scored_non_ties"], "Coverage census is inconsistent")
    require(c["kalshi_non_ties"] == c["scored_non_ties"], "Current Kalshi/model cohorts differ")
    require(c["latest_week_common_games"] <= c["latest_week_source_finals"], "Weekly coverage exceeds source")
    labels = {m["label"] for m in data["models"]}
    require(len(labels) == len(data["models"]), "Duplicate model labels")
    for row in data["models"] + data["benchmarks"]:
        require(row["games"] == c["scored_non_ties"], "Headline cohort differs")
        require(0 <= row["correct"] <= row["games"], "Invalid correct count")
        require(abs(row["accuracy"] - row["correct"] / row["games"]) < 1e-12, "Accuracy/count mismatch")
    require({p["provider"] for p in data["providers"]} == PROVIDERS, "Provider inventory is incomplete")
    require(len(data["providers"]) == len(PROVIDERS), "Duplicate provider")
    for history in data["history"]:
        required_metrics = {"accuracy", "log_loss", "brier"} if history["target"] == "win" else {"mae", "rmse"}
        require({str(x["season"]) for x in history["seasons"]} == {"2024", "2025", "2026", "pooled"}, "Missing historical season")
        for row in history["seasons"]:
            require(required_metrics <= set(row), "Required history metrics missing")
    groups = {}
    for row in data["common_provider_metrics"]:
        required_metrics = {"accuracy", "log_loss", "brier"} if row["target"] == "win" else {"mae", "rmse", "bias"}
        require(required_metrics <= set(row), "Required common metrics missing")
        key = row["season"], row["target"]
        identity = row["games"], row["cohort_sha256"]
        require(key not in groups or groups[key] == identity, "Provider comparison mixes exact event cohorts")
        groups[key] = identity
    require(set(groups) == {(y, t) for y in (2024, 2025, 2026) for t in ("win", "margin", "total")}, "Missing provider target/season cell")
    examples = data["disagreement_examples"]
    seen = set()
    for row in examples:
        key = row["model"], row["game_id"]
        require(key not in seen, "Duplicate resolved example"); seen.add(key)
        require(row["model"] in labels, "Unknown public model label")
        require(type(row["home_score"]) is int and type(row["away_score"]) is int, "Only resolved score examples may be published")
        require(row["home_score"] != row["away_score"], "Non-tie disagreement example is tied")
        actual = row["home_team"] if row["home_score"] > row["away_score"] else row["away_team"]
        require(row["actual_winner"] == actual, "Actual winner differs from score")
        require({row["model_pick"], row["kalshi_pick"]} == {row["home_team"], row["away_team"]}, "Example is not a winner disagreement")
        winner = "model" if row["model_pick"] == actual else "Kalshi"
        require(row["disagreement_winner"] == winner, "Disagreement outcome differs")
        probability = row["model_pick_probability_percent"]
        require(type(probability) in (int, float) and 50 <= probability <= 100, "Invalid pick probability")
        require(abs(probability * 10 - round(probability * 10)) < 1e-8, "Public probability must be rounded to 0.1 percentage point")
        require(datetime.fromisoformat(row["kickoff_utc"]) < datetime.fromisoformat(data["as_of"]), "Future examples are private")
    for model in data["models"]:
        if "disagreements_won" in model and model["label"] in {r["model"] for r in examples}:
            rows = [r for r in examples if r["model"] == model["label"]]
            won = sum(r["disagreement_winner"] == "model" for r in rows)
            lost = len(rows) - won
            low_losses = sum(r["disagreement_winner"] == "Kalshi" and 50 <= r["model_pick_probability_percent"] < 60 for r in rows)
            require((won, lost) == (model["disagreements_won"], model["disagreements_lost"]), "Both disagreement directions must reconcile")
            require(low_losses == model["lost_disagreements_probability_50_to_60"], "Confidence-band loss count differs")
    issue = data["resolved_forecast_example"]
    require(datetime.fromisoformat(issue["feature_as_of_utc"]) <= datetime.fromisoformat(issue["issued_at_utc"]) <= datetime.fromisoformat(issue["kickoff_utc"]) - timedelta(hours=1), "Resolved issue misses its T1 clock")
    require(data["execution"]["new_owner_fits"] == data["execution"]["new_base_fits"] + data["execution"]["new_stack_fits"], "New fit counts do not reconcile")
    require(data["execution"]["protected_original_refits"] == 0, "Protected original refit")
    require(data["execution"]["new_issued_forecasts"] == data["upcoming"]["new_final_hour_issues"] == 0, "Unsupported new issue claim")
    require(data["uncertainty"]["advantage_supported"] is False, "Unsupported durable edge claim")
    return {"status": "PUBLIC_CURRENT_EVIDENCE_VALIDATED", "public_models": len(data["models"]), "resolved_examples": len(examples), "provider_target_cells": len(groups), "private_training_reproduced": False}


def load_snapshot():
    raw = (HERE / "current_evidence.json").read_bytes()
    data = json.loads(raw)
    receipt = validate_snapshot(data)
    with (HERE / "current_disagreements.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        require(set(reader.fieldnames or ()) == set(ALLOWED_FIELDS["$.disagreement_examples[]"]), "CSV fields differ from public disclosure schema")
    expected = [{k: str(v) for k, v in row.items()} for row in data["disagreement_examples"]]
    require(rows == expected, "CSV does not exactly preserve the resolved public examples")
    return data, {**receipt, "current_evidence_sha256": hashlib.sha256(raw).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(load_snapshot()[1], sort_keys=True))
