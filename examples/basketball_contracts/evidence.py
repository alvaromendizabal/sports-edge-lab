"""Validate and inspect committed aggregate basketball research evidence.

No estimator is loaded or fitted. The evidence is a sanitized export of an
audited private run, separate from the invented contract walkthrough.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

EVIDENCE_PATH = Path(__file__).resolve().parents[2] / "docs/evidence/2026-10-27-basketball-b002.json"


def validate_evidence(value: dict[str, Any]) -> None:
    if value.get("schema") != "sports-edge-public-basketball-evidence-v1":
        raise ValueError("unknown aggregate evidence schema")
    policy = value["evaluation"]
    if (policy["historical_validation_seasons"] != [2025, 2026]
            or policy["final_selection_max_season_ending"] != 2026
            or policy["protected_monitoring_season_ending"] != 2027
            or policy["current_outcomes_used_for_selection_or_fitting"] is not False):
        raise ValueError("historical selection and protected monitoring boundary changed")
    if policy["market_advantage_established"] is not False:
        raise ValueError("B002 did not establish MARKET advantage")
    owner = value["owner_execution"]
    counts = [owner["completed_native_fit_units"], *owner["fit_units_by_kind"].values(), *owner["fit_units_by_league"].values()]
    if any(type(n) is not int or n < 0 for n in counts):
        raise ValueError("fit counts must be nonnegative integers")
    if (sum(owner["fit_units_by_kind"].values()) != owner["completed_native_fit_units"]
            or sum(owner["fit_units_by_league"].values()) != owner["completed_native_fit_units"]):
        raise ValueError("native fit accounting does not reconcile")
    if owner["actual_orders"] != 0 or owner["profit"] is not None:
        raise ValueError("research output cannot acquire invented execution or profit")
    if owner["forecast_kind"] != "early_outlook_before_declared_horizon":
        raise ValueError("early outlooks cannot become lock forecasts")
    if any(value["publication_boundary"].values()):
        raise ValueError("private records are outside this aggregate export")
    scopes = {(t["league"], t["horizon_minutes"]) for t in value["tracks"]}
    expected = {(league, horizon) for league in ("nba", "ncaam", "ncaaw") for horizon in (60, 1440)}
    if scopes != expected or len(value["tracks"]) != len(expected):
        raise ValueError("league and horizon scopes must remain distinct")
    if sum(t["completed_native_fit_units"] for t in value["tracks"]) != owner["completed_native_fit_units"]:
        raise ValueError("track fit totals do not reconcile")
    for track in value["tracks"]:
        cohorts = {}
        keys = set()
        for row in track["season_scorecards"]:
            key = (row["cohort"], row["validation_season"], row["recipe"])
            if key in keys:
                raise ValueError("duplicate aggregate scorecard")
            keys.add(key)
            if row["validation_season"] not in (2025, 2026) or row["phase"] != "historical_validation":
                raise ValueError("monitoring rows cannot enter historical validation")
            if (row["league"], row["horizon_minutes"]) != (track["league"], track["horizon_minutes"]):
                raise ValueError("scorecard scope differs from its track")
            if type(row["n"]) is not int or row["n"] <= 0 or row["correct"]+row["incorrect"] != row["n"]:
                raise ValueError("scorecard outcome accounting does not reconcile")
            if not math.isclose(row["accuracy"], row["correct"]/row["n"], rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("accuracy differs from correct pick accounting")
            for field in ("brier", "log_loss", "ece_10_fixed_bins"):
                if isinstance(row[field], bool) or not math.isfinite(row[field]) or row[field] < 0:
                    raise ValueError("nonfinite or invalid scoring metric")
            group = (row["cohort"], row["validation_season"])
            identity = (row["n"], row["event_cohort_sha256"])
            if group in cohorts and cohorts[group] != identity:
                raise ValueError("comparison recipes do not share an exact aggregate cohort identity")
            cohorts[group] = identity


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text())
    validate_evidence(value)
    return value


def selected_season_rows(value: dict[str, Any], horizon: int = 60) -> list[dict[str, Any]]:
    """Return the frozen full-cohort selected recipe for each historical season."""
    validate_evidence(value)
    if horizon not in (60, 1440):
        raise ValueError("unsupported horizon")
    result = []
    for track in value["tracks"]:
        if track["horizon_minutes"] != horizon:
            continue
        choice = next(s for s in track["selections"] if s["cohort"] == "full_basketball")
        for season in (2025, 2026):
            probability = next(r for r in track["season_scorecards"] if r["validation_season"] == season
                               and r["cohort"] == "full_basketball" and r["recipe"] == choice["selected_recipe"])
            point = next(r for r in track["season_scorecards"] if r["validation_season"] == season
                         and r["cohort"] == "full_basketball" and r["recipe"] == choice["score_selected_recipe"])
            result.append({**probability, "point_estimator": "shared_Ridge", "point_margin": point["margin"], "point_total": point["total"]})
    return result


def results_markdown(value: dict[str, Any]) -> str:
    """Render the public tables from the same validated aggregate export."""
    validate_evidence(value)
    names = {"nba":"NBA", "ncaam":"NCAA men", "ncaaw":"NCAA women"}
    recipes = {"basketball_strength":"Strength · regularized logistic", "basketball_style":"Style · regularized logistic",
               "basketball_combined":"Combined · regularized logistic", "basketball_lightgbm":"Combined · LightGBM",
               "basketball_xgboost":"Combined · XGBoost", "basketball_catboost":"Combined · CatBoost",
               "Elo":"Elo", "historical_prior":"Historical prior", "MARKET_raw":"Raw MARKET"}
    lines = ["# B002 basketball historical results", "",
             "[Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Model card](BASKETBALL_MODEL_CARD.md) · [Aggregate export](evidence/2026-10-27-basketball-b002.json)", "",
             "These tables are generated from the audited aggregate export. All completed tracks use reconstructed research under a 24-hour historical release assumption. T−60 is primary; T−24h is separately retained in the export. No strict historical availability or MARKET-advantage claim is made.", "",
             "## Separate league leaderboards at T−60", "",
             "Each table is sorted by pooled 2025–2026 log loss, the declared historical selection criterion. The two seasons remain separate columns. Pooled results are selected development evidence. More favorable accuracy alone does not replace the primary proper-score selection. Every recipe within a league's full-cohort comparison shares its game IDs; the aggregate cohort digests are retained in the export.", ""]
    for track in value["tracks"]:
        if track["horizon_minutes"] != 60:
            continue
        selection = next(s for s in track["selections"] if s["cohort"] == "full_basketball")
        rows = [r for r in track["season_scorecards"] if r["cohort"] == "full_basketball"]
        lookup = {(r["recipe"],r["validation_season"]):r for r in rows}
        counts = [next(r["n"] for r in rows if r["validation_season"]==year) for year in (2025,2026)]
        lines += [f"### {names[track['league']]}", "", f"Games: {counts[0]:,} in ending 2025 and {counts[1]:,} in ending 2026. Selected probability recipe: {recipes[selection['selected_recipe']]}; this selection is not an independent prospective win.", "",
                  "| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |", "|---|---:|---:|---:|---:|---:|"]
        for row in selection["leaderboard"]:
            a,b = lookup[(row["recipe"],2025)],lookup[(row["recipe"],2026)]
            lines.append(f"| {recipes[row['recipe']]} | {a['log_loss']:.6f} | {b['log_loss']:.6f} | {a['brier']:.6f} | {b['brier']:.6f} | {row['log_loss']:.6f} |")
        lines.append("")
    lines += ["## Selected probability and point-head diagnostics", "",
              "Point metrics below belong to the separately selected shared Ridge margin/total head, not to a CatBoost score regressor. The selection's probability and point recipes may differ. Home and away point errors, calibration bias, and every comparison model are retained in the JSON export.", "",
              "| League | Season | Games | Correct / incorrect | Accuracy | Calibration error ↓ | Margin MAE / RMSE ↓ | Total MAE / RMSE ↓ |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in selected_season_rows(value):
        m,t = r["point_margin"],r["point_total"]
        lines.append(f"| {names[r['league']]} | {r['validation_season']} | {r['n']:,} | {r['correct']:,} / {r['incorrect']:,} | {r['accuracy']:.2%} | {r['ece_10_fixed_bins']:.6f} | {m['mae']:.3f} / {m['rmse']:.3f} | {t['mae']:.3f} / {t['rmse']:.3f} |")
    lines += ["", "## Raw MARKET versus the selected basketball recipe on identical games", "",
              "The basketball recipe here is the full-cohort historical selection, evaluated on the exact MARKET-matched subset. It is not a separately selected per-year winner. A blank comparison means no eligible matched events; it is never counted as a loss or abstention. Positive Δ means basketball log loss is worse than MARKET.", "",
              "| League | Horizon | Season | Matched games | Basketball log loss ↓ | Raw MARKET log loss ↓ | Δ basketball − MARKET |", "|---|---:|---:|---:|---:|---:|---:|"]
    for track in value["tracks"]:
        choice = next(s for s in track["selections"] if s["cohort"] == "full_basketball")
        for year in (2025,2026):
            rows = [r for r in track["season_scorecards"] if r["cohort"]=="matched_MARKET" and r["validation_season"]==year]
            if not rows:
                lines.append(f"| {names[track['league']]} | T−{track['horizon_minutes']}m | {year} | 0 | Unavailable | Unavailable | Unavailable |")
                continue
            raw = next(r for r in rows if r["recipe"]=="MARKET_raw")
            model = next(r for r in rows if r["recipe"]==choice["selected_recipe"])
            lines.append(f"| {names[track['league']]} | T−{track['horizon_minutes']}m | {year} | {raw['n']:,} | {model['log_loss']:.6f} | {raw['log_loss']:.6f} | {model['log_loss']-raw['log_loss']:+.6f} |")
    lines += ["", "Learned MARKET-only and integrated MARKET/basketball classifiers did not fit: their eligible training cohorts were below the declared requirements. The result is unavailable, not a zero score. No league qualified a model advantage. The 2026 men's T−60 style-model result is exploratory: 118 games, 13 blocks, Δ log loss −0.006053 with a 95% block interval [−0.041032, 0.035094], and no matched 2025 cohort.", "",
              "## Representation interactions and uncertainty", "",
              "These contrasts compare the combined representation with its strength and style controls on the same full basketball games. Negative Δ favors the combined model. The seven-calendar-day block intervals are descriptive after model selection; repeated-team and longer-term dependence may remain. They do not establish superiority to MARKET.", "",
              "| League | Contrast at T−60 | Games | Δ log loss | Descriptive 95% interval | Blocks |", "|---|---|---:|---:|---|---:|"]
    for track in value["tracks"]:
        if track["horizon_minutes"] != 60:
            continue
        for c in track["representation_contrasts"]:
            lo,hi=c['ci95']
            lines.append(f"| {names[track['league']]} | Combined − {recipes[c['control']]} | {c['n']:,} | {c['delta_log_loss_a_minus_b']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | {c['unique_blocks']} |")
    lines += ["", "## Forward monitoring", "",
              "B002's 110 issued rows span 61 future games and are explicitly early outlooks before their named locks. Zero qualified current MARKET probabilities were present, and zero forecasted games had settled at issue. Prospective proper scores, accuracy and profit were unavailable. Retrospective 2027 monitoring is stored separately and cannot select model parameters. B003 owner execution and all proposed coverage/efficiency improvements remain pending.", ""]
    return "\n".join(lines)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--write-results", action="store_true")
    mode.add_argument("--check-results", action="store_true")
    args=parser.parse_args()
    evidence = load_evidence()
    destination=EVIDENCE_PATH.parents[1]/"BASKETBALL_RESULTS.md"
    if args.write_results:
        destination.write_text(results_markdown(evidence))
    if args.check_results:
        if destination.read_text() != results_markdown(evidence):
            raise ValueError("public basketball tables differ from the aggregate evidence")
        print(json.dumps({"status":"PASS", "generated_results_match_evidence":True, "real_models_fitted_by_this_command":0}))
        return
    print(json.dumps({"status":"PASS", "owner_native_fit_units":evidence["owner_execution"]["completed_native_fit_units"],
                      "aggregate_tracks":len(evidence["tracks"]), "real_models_fitted_by_this_command":0,
                      "selected_T60_season_rows":selected_season_rows(evidence)}, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
