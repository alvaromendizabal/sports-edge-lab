"""Strict, aggregate-only publication contract for the dated FBS V024 study."""
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/fbs/V024_AGGREGATE_2026-11-03.json"
METRICS = ("winner_logloss", "winner_brier", "winner_accuracy", "winner_correct",
           "winner_ece", "winner_mcc", "margin_mae", "margin_rmse", "margin_bias",
           "total_mae", "total_rmse", "total_bias")
MODELS = ("earlier-baseline", "earlier-study", "previous-study", "registered-challenger",
          "fixed-control-a", "fixed-control-b", "fixed-control-c")


def _keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"unexpected or missing public fields: {where}")


def _number(value, low=None, high=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite numeric value required; missing does not mean zero")
    if low is not None and value < low or high is not None and value > high:
        raise ValueError("metric outside declared range")


def validate_release(data):
    _keys(data, ("schema", "release", "as_of", "result", "comparison_status", "exposure", "execution",
                 "verification", "pairing", "models", "panels", "intervals", "source_scope", "limitations"), "root")
    if data["schema"] != "sports-edge-lab.fbs.public-release.v1" or data["release"] != "V024":
        raise ValueError("unsupported public release")
    exposure = data["exposure"]
    _keys(exposure, ("selection_seasons", "evaluation_seasons", "evaluation_status",
                     "current_season_used_for_selection", "prospective_forecasts_issued",
                     "live_feature_values_recomputed"), "exposure")
    if (exposure["selection_seasons"] != [2021, 2022, 2023] or exposure["evaluation_seasons"] != [2024, 2025]
            or exposure["current_season_used_for_selection"] is not False
            or exposure["live_feature_values_recomputed"] is not False
            or exposure["prospective_forecasts_issued"] != 0):
        raise ValueError("historical evidence cannot become prospective evidence")
    execution = data["execution"]
    _keys(execution, ("fresh_completed_fits", "reused_fits", "failed_fits", "inner_selection_fits",
                      "historical_evaluation_fits", "frozen_state_fits", "elapsed_seconds",
                      "new_paid_provider_calls", "fresh_rolling_fits", "original_objects_verified"), "execution")
    for key, value in execution.items():
        _number(value, 0)
        if key != "elapsed_seconds" and type(value) is not int:
            raise ValueError("integer count required")
    if execution["fresh_completed_fits"] != sum(execution[k] for k in (
            "inner_selection_fits", "historical_evaluation_fits", "frozen_state_fits")):
        raise ValueError("fit accounting does not close")
    if any(execution[k] != 0 for k in ("reused_fits", "failed_fits", "new_paid_provider_calls", "fresh_rolling_fits")):
        raise ValueError("dated execution facts changed")
    verification = data["verification"]
    _keys(verification, ("return_bytes", "return_sha256", "completion_bytes", "completion_sha256",
                         "completion_after_research", "exit_code", "pinned_reports_verified",
                         "public_reproduction"), "verification")
    for key in ("return_sha256", "completion_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", verification[key]):
            raise ValueError("SHA256 commitment required")
    if verification["completion_after_research"] is not True or verification["exit_code"] != 0:
        raise ValueError("completion evidence is not a successful post-research receipt")
    for key in ("return_bytes", "completion_bytes", "pinned_reports_verified"):
        if type(verification[key]) is not int or verification[key] <= 0:
            raise ValueError("positive integer verification count required")
    if len(data["models"]) != len(MODELS):
        raise ValueError("complete registered public comparison set required")
    for model in data["models"]:
        _keys(model, ("id", "label", "role"), "model")
    if [m["id"] for m in data["models"]] != list(MODELS):
        raise ValueError("unexpected public comparison identifiers")
    pairing = data["pairing"]
    _keys(pairing, ("evidence_class", "canonicalization", "seasons", "independently_recomputed_metrics",
                    "absolute_tolerance", "individual_rows_published"), "pairing")
    if pairing["individual_rows_published"] is not False or pairing["absolute_tolerance"] != 1e-12:
        raise ValueError("private verification and public reproduction must remain distinct")
    if not set(pairing["independently_recomputed_metrics"]) <= set(METRICS):
        raise ValueError("unknown metric verification claim")
    cohorts = {}
    for cohort in pairing["seasons"]:
        _keys(cohort, ("season", "games", "cohort_labels_sha256", "exact_identity_teams_labels_verified",
                      "prediction_columns_verified"), "cohort attestation")
        if cohort["season"] not in (2024, 2025) or cohort["season"] in cohorts:
            raise ValueError("duplicate or unexpected cohort attestation")
        if (not re.fullmatch(r"[0-9a-f]{64}", cohort["cohort_labels_sha256"])
                or cohort["exact_identity_teams_labels_verified"] is not True
                or cohort["prediction_columns_verified"] != 21
                or cohort["games"] != {2024: 918, 2025: 934}[cohort["season"]]):
            raise ValueError("invalid private pairing attestation")
        cohorts[cohort["season"]] = cohort["cohort_labels_sha256"]
    if set(cohorts) != {2024, 2025}:
        raise ValueError("missing cohort attestation")
    expected = {(season, name) for season in (2024, 2025) for name in MODELS}
    seen = set()
    for panel in data["panels"]:
        _keys(panel, ("model", "season", "games", "metrics", "cohort_sha256"), "panel")
        identity = (panel["season"], panel["model"])
        if identity not in expected or identity in seen:
            raise ValueError("duplicate or unregistered aggregate panel")
        seen.add(identity)
        if panel["cohort_sha256"] != cohorts[panel["season"]]:
            raise ValueError("cohort commitment drift")
        n = panel["games"]
        if type(n) is not int or n != {2024: 918, 2025: 934}[panel["season"]]:
            raise ValueError("denominator drift")
        _keys(panel["metrics"], METRICS, "metrics")
        for metric, value in panel["metrics"].items():
            _number(value)
            if metric.endswith(("logloss", "mae", "rmse")):
                _number(value, 0)
            if metric in ("winner_brier", "winner_accuracy", "winner_ece"):
                _number(value, 0, 1)
            if metric == "winner_mcc":
                _number(value, -1, 1)
        correct = panel["metrics"]["winner_correct"]
        if type(correct) is not int or not 0 <= correct <= n:
            raise ValueError("correct count outside cohort")
        if not math.isclose(panel["metrics"]["winner_accuracy"], correct / n, abs_tol=1e-14):
            raise ValueError("accuracy and count disagree")
        for target in ("margin", "total"):
            if panel["metrics"][target + "_rmse"] < panel["metrics"][target + "_mae"]:
                raise ValueError("RMSE cannot be below MAE on the same cohort")
    if seen != expected:
        raise ValueError("missing registered aggregate panel")
    seen_intervals = set()
    for interval in data["intervals"]:
        _keys(interval, ("season", "target", "games", "covered", "empirical_coverage", "mean_width",
                         "nominal_coverage", "descriptive_only"), "interval")
        key = (interval["season"], interval["target"])
        if key not in {(s, t) for s in (2024, 2025) for t in ("margin", "total")} or key in seen_intervals:
            raise ValueError("invalid or duplicate interval panel")
        seen_intervals.add(key)
        n = interval["games"]
        if n != {2024: 918, 2025: 934}[interval["season"]] or interval["descriptive_only"] is not True:
            raise ValueError("interval denominator or use changed")
        if type(interval["covered"]) is not int or not 0 <= interval["covered"] <= n:
            raise ValueError("invalid covered count")
        if not math.isclose(interval["empirical_coverage"], interval["covered"] / n, abs_tol=1e-14):
            raise ValueError("interval coverage and count disagree")
        _number(interval["mean_width"], 0)
        if interval["nominal_coverage"] != .9:
            raise ValueError("dated nominal interval changed")
    if len(seen_intervals) != 4:
        raise ValueError("missing interval panel")
    scope = data["source_scope"]
    _keys(scope, ("observed_at", "upcoming_strict_7_days", "upcoming_extended_schedule", "original_summary_7_day_count",
                  "window_correction", "quote_rows_all", "quote_rows_game_markets", "quote_rows_player_props",
                  "mapped_game_market_rows", "quarantined_game_market_rows", "mapped_events", "observed_events",
                  "certified_60_or_120_minute_rows"), "source scope")
    for key, value in scope.items():
        if key not in ("observed_at", "window_correction") and (type(value) is not int or value < 0):
            raise ValueError("source count must be a nonnegative integer")
    if scope["quote_rows_all"] != scope["quote_rows_game_markets"] + scope["quote_rows_player_props"]:
        raise ValueError("game and player-prop scopes do not close")
    if scope["quote_rows_game_markets"] != scope["mapped_game_market_rows"] + scope["quarantined_game_market_rows"]:
        raise ValueError("mapped and quarantined game-market scopes do not close")
    if scope["upcoming_strict_7_days"] > scope["upcoming_extended_schedule"] or scope["mapped_events"] > scope["observed_events"]:
        raise ValueError("invalid source subset counts")
    serialized = json.dumps(data, allow_nan=False).lower()
    for forbidden in ("s3://", "arn:", "api_key", "account_id", "bucket", "/workspace/", "/home/",
                      "v024_full_", "v024_combined_", "extra_trees", "private_forecast", "game_id"):
        if forbidden in serialized:
            raise ValueError("private or unapproved publication content")
    return data


def release():
    return validate_release(json.loads(SOURCE.read_text()))


if __name__ == "__main__":
    data = release()
    print(json.dumps({"release": data["release"], "aggregate_panels": len(data["panels"]),
                      "new_owner_fits_here": 0, "status": "PUBLIC_AGGREGATE_VALIDATED"}, indent=2))
