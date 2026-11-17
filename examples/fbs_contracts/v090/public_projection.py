"""Project authenticated saved FBS aggregates into a bounded public report.

This reads supplied local evidence only. It never fits, retrieves providers, or
publishes a site. Source locations and private policy identities are not exported.
The caller supplies the independently authenticated latest-return pointer.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

YEARS = (2024, 2025, 2026)
PROFILES = ("50/50", "40/60", "30/70", "20/80", "10/90")
METRICS = {"winner": ("log_loss", "brier", "accuracy"), "margin": ("mae", "rmse", "crps"), "total": ("mae", "rmse", "crps")}
FAMILIES = {
    "linear": "Linear models", "logistic": "Logistic regression", "ridge": "Ridge regression",
    "extra_trees": "Extra Trees", "hist_gradient_boosting": "Histogram gradient boosting",
    "xgboost": "XGBoost", "lightgbm": "LightGBM", "catboost": "CatBoost",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "v038_fixed_equal_blend": "Retained fixed blend", "v039_fixed_equal_blend": "Retained fixed blend",
    "v041_fixed_equal_blend": "Retained fixed blend",
}
BOOKS = {"betmgm": "BetMGM", "betonlineag": "BetOnline", "betrivers": "BetRivers", "betus": "BetUS", "bovada": "Bovada", "draftkings": "DraftKings", "fanatics": "Fanatics", "fanduel": "FanDuel", "gtbets": "GTBets", "lowvig": "LowVig", "mybookieag": "MyBookie", "pointsbetus": "PointsBet US", "superbook": "SuperBook", "unibet": "Unibet", "unibet_us": "Unibet US", "williamhill_us": "William Hill US", "wynnbet": "WynnBET"}
METRIC_FIELDS = set(x for values in METRICS.values() for x in values) | {"n", "correct_count", "bias", "crps_n", "interval80_coverage", "interval80_mean_width", "interval80_n", "interval95_coverage", "interval95_mean_width", "interval95_n"}
PRIVATE_PATTERN = re.compile(r"s3://|arn:aws:|/home/|/workspace/|sagemaker-user|AKIA[0-9A-Z]{16}|\.pyz\b|\b\d{12}\b", re.I)


def safe_text(value):
    if not isinstance(value, str) or len(value) > 4000 or PRIVATE_PATTERN.search(value):
        raise ValueError("Unsafe public text")
    return value


def scalar(value):
    if value is None:
        return None
    if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("Non-finite or non-numeric aggregate")
    return value


def identity(row):
    return (row["model_id"], row["target"], row["evidence_class"], int(row["horizon_minutes"]))


def model_group(model_id):
    if "/market_only/" in model_id:
        return "Market only"
    if "/combined/" in model_id:
        return "Football + markets"
    return "Football only"


def read_pinned(path, pin):
    blob = Path(path).read_bytes()
    if len(blob) != pin["bytes"] or hashlib.sha256(blob).hexdigest() != pin["sha256"]:
        raise ValueError("Input bytes fail their authenticated artifact pin")
    return json.loads(blob)


def project(cards, selection, manifest, binding, stage, pointer, prior_selection, stress, cpu_reports, prepared):
    if manifest["sport"] != "FBS" or pointer["owner"].upper() != "FBS":
        raise ValueError("FBS owner required")
    if not pointer["integrity_verified"] or not pointer["durable_available"] or pointer.get("fixture_mode"):
        raise ValueError("A verified actual owner return is required")
    if selection["selection_seasons"] != [2024, 2025] or selection["primary_profile"] != "50/50":
        raise ValueError("Annual validation-only selection required")
    if selection["test_outcomes_used"] is not False or selection["season_training_weights_used"] is not False or selection["refits_for_sensitivity"] != 0 or selection["base_predictions_changed_for_sensitivity"] is not False:
        raise ValueError("Selection-only sensitivity safeguards required")
    if selection["test_untouched"] is not False or selection["prior_test_exposure_disclosed"] is not True:
        raise ValueError("Prior test exposure must remain disclosed")
    populations = {(r["season"], r["target"]): r for r in manifest["populations"]}
    expected = {}
    for year in YEARS:
        counts = {populations[(year, target)]["expected_n"] for target in METRICS}
        if len(counts) != 1:
            raise ValueError("Annual target populations are not identical")
        expected[year] = counts.pop()
    grouped = defaultdict(dict)
    for row in cards:
        key, year = identity(row), row["season"]
        if key[1] not in METRICS or key[2] != "V13_FROZEN_RECONSTRUCTION" or key[3] != 120 or year not in YEARS:
            raise ValueError("Unexpected target, evidence class, horizon or season")
        if year in grouped[key]:
            raise ValueError("Duplicate annual candidate card")
        pop = populations[(year, key[1])]
        if row["expected_n"] != expected[year] or row["scored_n"] + row["missing_n"] != expected[year] or row["cohort_sha256"] != pop["cohort_sha256"]:
            raise ValueError("A candidate shrank or changed the full annual population")
        if row.get("promotion") or row.get("production_deployed") or row.get("test_untouched"):
            raise ValueError("Promotion or pristine-test claim cannot be projected")
        grouped[key][year] = row
    models, aliases, counters = [], {}, defaultdict(int)
    for key, annual in sorted(grouped.items()):
        if set(annual) != set(YEARS):
            raise ValueError("All three annual cards are required")
        mid, target, evidence_class, horizon = key
        counters[target] += 1
        alias = "F090-" + target[0].upper() + f"{counters[target]:03d}"
        aliases[key] = alias
        family_code = annual[2024]["family"]
        if family_code not in FAMILIES:
            raise ValueError("Unreviewed public model-family label")
        family = FAMILIES[family_code]
        calibration = "Calibrated" if mid.endswith("/calibrated") else "Raw" if mid.endswith("/raw") else "Retained policy"
        release = "V089 extension" if mid.startswith("v089/") else "V088 market study" if mid.startswith("v088/") else "Retained earlier control"
        study_group = ("Single-source ablation" if mid.startswith("v088/") and "/without_" in mid
                       else "Retained football feature ablation" if "/without_" in mid
                       else "All-source control" if "/all_sources/" in mid else "Retained no-market control")
        models.append({"alias": alias, "family": family, "label": family + " · " + target,
                       "target": target, "input_group": model_group(mid), "calibration": calibration,
                       "study_group": study_group, "release": release, "evidence_class": evidence_class,
                       "horizon_minutes": horizon, "verified_historical_champion": False,
                       "annual": {str(year): {"season": year, "role": "TEST" if year == 2026 else "VALIDATION",
                            "expected_n": annual[year]["expected_n"], "scored_n": annual[year]["scored_n"],
                            "missing_n": annual[year]["missing_n"], "complete_coverage": annual[year]["complete_coverage"],
                            "cohort_sha256": annual[year]["cohort_sha256"],
                            "metrics": {k: scalar(v) for k, v in annual[year]["metrics"].items() if k in METRIC_FIELDS}}
                            for year in YEARS}})
    ranks, leaders = [], []
    for row in selection["ranks"]:
        key = identity(row)
        if key not in aliases or row["profile"] not in PROFILES or row["metric"] not in METRICS[key[1]]:
            raise ValueError("Rank points outside the authenticated candidate population")
        # Recheck the saved score using annual validation metrics only. No estimator is invoked.
        w1, w2 = (float(x) / 100 for x in row["profile"].split("/"))
        m1, m2 = (grouped[key][year]["metrics"].get(row["metric"]) for year in (2024, 2025))
        if m1 is None or m2 is None:
            if row["eligible"] is not False or row["rank"] is not None or row["selection_score"] is not None:
                raise ValueError("Unavailable metrics must not receive a score or rank")
        else:
            wanted = w1 * m1 + w2 * m2
            if row["eligible"] is not True or not math.isclose(wanted, row["selection_score"], rel_tol=1e-13, abs_tol=1e-13):
                raise ValueError("Saved rank score is not the declared annual validation weighting")
        ranks.append({"alias": aliases[key], "target": key[1], "metric": row["metric"], "profile": row["profile"],
                      "rank": row["rank"], "eligible": row["eligible"], "selection_score": scalar(row["selection_score"])})
    for row in selection["leaders"]:
        key = identity(row)
        leaders.append({"alias": aliases[key], "target": key[1], "metric": row["metric"], "profile": row["profile"], "value": scalar(row["value"]), "primary": row["profile"] == "50/50"})
    for target, metrics in METRICS.items():
        for metric in metrics:
            for profile in PROFILES:
                rr = [r for r in ranks if (r["target"], r["metric"], r["profile"]) == (target, metric, profile)]
                ll = [r for r in leaders if (r["target"], r["metric"], r["profile"]) == (target, metric, profile)]
                eligible = [r for r in rr if r["eligible"]]
                if len(rr) != counters[target] or sorted(r["rank"] for r in eligible) != list(range(1, len(eligible) + 1)) or len(ll) != 1:
                    raise ValueError("Complete candidate ranking or leader set is missing")
                ordered = sorted(eligible, key=lambda r: r["rank"])
                scores = [r["selection_score"] * (-1 if metric == "accuracy" else 1) for r in ordered]
                if scores != sorted(scores):
                    raise ValueError("Saved ranks are not ordered by their validation score")
                # Equal-score ties retain the saved deterministic rank; never use test results.
                best = ordered[0]
                if ll[0]["alias"] != best["alias"] or ll[0]["value"] != best["selection_score"]:
                    raise ValueError("Leader and rank evidence disagree")
    if len(leaders) != 45 or len(models) != stage["inherited_policy_count"] + stage["new_policy_count"]:
        raise ValueError("Delivered policy or leader accounting mismatch")
    primary = [r for r in selection["leaders"] if r["profile"] == "50/50"]
    prior_primary = {(r["target"], r["metric"]): r for r in prior_selection["leaders"] if r["profile"] == "50/50"}
    worse, better, changed = 0, 0, 0
    for lead in primary:
        previous = prior_primary[(lead["target"], lead["metric"])]
        a = grouped[identity(lead)][2026]["metrics"][lead["metric"]]
        b = grouped[identity(previous)][2026]["metrics"][lead["metric"]]
        sign = -1 if lead["metric"] == "accuracy" else 1
        worse += (a-b)*sign > 0
        better += (a-b)*sign < 0
        changed += identity(lead) != identity(previous)
    winner = next(r for r in primary if r["target"] == "winner" and r["metric"] == "log_loss")
    winner_key = identity(winner)
    raw_key = (winner_key[0].rsplit("/", 1)[0] + "/raw", *winner_key[1:])
    calibrated_key = (winner_key[0].rsplit("/", 1)[0] + "/calibrated", *winner_key[1:])
    def validation_metric(key, metric):
        return sum(grouped[key][y]["metrics"][metric] for y in (2024, 2025)) / 2
    findings = [
        f"All {changed} primary objective leaders change from the preceding market study after the five-framework extension. Their identities are selected only on the two validation seasons.",
        f"The new primary leaders have worse 2026 test results on {worse} of 9 objectives and better results on {better}. This diagnostic comparison does not alter the validation-selected leaders or define the next research campaign.",
        f"For the selected winner model family, calibration worsens equal-year validation log loss from {validation_metric(raw_key, 'log_loss'):.6f} raw to {validation_metric(calibrated_key, 'log_loss'):.6f} calibrated. Raw and calibrated policies remain separate candidates.",
        f"The comparison preserves {stage['inherited_no_market_control']['policy_count']} earlier no-market controls and the prior source-ablation study. Nonlinear source ablations, broader interactions and validated blends remain separately registered work."
    ]
    stress_index = {(identity(r), r["season"]): r for r in stress}
    brier_leader = next(r for r in primary if r["target"] == "winner" and r["metric"] == "brier")
    bk = identity(brier_leader)
    if all((bk, y) in stress_index for y in (2024, 2025)):
        absent = sum(stress_index[(bk, y)]["metrics"]["brier"] for y in (2024, 2025)) / 2
        findings.append(f"Removing all market sources from the selected winner-Brier model changes its validation Brier score from {validation_metric(bk, 'brier'):.6f} to {absent:.6f}. The missing-source stress keeps every completed game in the denominator.")
    a = pointer["accountability"]
    for field in ("new_model_fits", "new_calibrator_fits", "failed_fits"):
        if a[field] != stage[field]:
            raise ValueError("Actual execution counters disagree")
    cost = a["cost_breakdown"]
    cpu_sum = sum(r["scientific_callback_cpu_seconds"] for r in cpu_reports)
    peaks = [r["maximum_observed_concurrent_fit_workers"] for r in cpu_reports]
    full_pass = all(r["occupancy_acceptance"]["full_capacity_pass"] for r in cpu_reports)
    as_of = manifest["as_of"]
    current_pending = sum(g["season"] == 2026 and not g["completed"] for g in manifest["games"])
    unresolved = sum(g["season"] == 2026 and not g["completed"] and not g.get("kickoff_utc") for g in manifest["games"])
    games = []
    for index, game in enumerate(sorted(manifest["games"], key=lambda g: (g["season"], g.get("kickoff_utc") or "9999", g["game_id"])), 1):
        home = away = None
        if game["completed"]:
            total, margin = game["actuals"].get("total"), game["actuals"].get("margin")
            if total is not None and margin is not None:
                home, away = (scalar(total)+scalar(margin))/2, (total-margin)/2
        games.append({"alias": f"F090-G{index:04d}", "season": game["season"], "home_team": safe_text(game["home_team"]),
                      "away_team": safe_text(game["away_team"]), "kickoff_utc": game.get("kickoff_utc"), "completed": bool(game["completed"]),
                      "home_points": home, "away_points": away})
    for book in binding["books"]:
        if book not in BOOKS:
            raise ValueError("Unreviewed bookmaker display label")
    report = {
        "schema": "fbs.public.saved-evidence.v090", "owner": "FBS", "as_of": as_of,
        "cohorts": [{"season": y, "expected_n": expected[y], "role": "TEST" if y == 2026 else "VALIDATION"} for y in YEARS],
        "models": models,
        "selection": {"primary_profile": "50/50", "test_outcomes_used": False, "season_training_weights_used": False,
                      "refits_for_sensitivity": 0, "base_predictions_changed_for_sensitivity": False,
                      "prior_test_exposure_disclosed": True, "test_untouched": False, "leaders": leaders, "ranks": ranks},
        "execution": {"release": "V089", "completed_jobs": stage["completed_jobs"], "registered_jobs": stage["registered_jobs"],
                      "new_model_fits": stage["new_model_fits"], "new_calibrator_fits": stage["new_calibrator_fits"],
                      "failed_fits": stage["failed_fits"], "total_policy_count": len(models),
                      "new_scored_prediction_rows": a["new_scored_prediction_rows"], "new_forecast_rows": a["new_forecast_rows_including_ungraded"],
                      "prior_market_jobs_preserved": a["prior_completed_market_jobs_preserved"], "prior_core_jobs_preserved": a["prior_completed_core_jobs_preserved"],
                      "operational_failures": a["owner_executions_failed"], "child_exit_code": pointer["child_os_exit_code"],
                      "summary": "The five-framework extension completed. Source, frontier-feature, benchmark and publication requirements still keep the full scientific program partial.",
                      "note": "This observed exit 2 denotes partial scientific-program status. The saved run has zero operationally failed executions and zero failed fits. Earlier work remains preserved; publication adds no owner fits or source requests."},
        "sources": {"books": [BOOKS[b] for b in binding["books"]], "qualified_t120_cells": binding["counts"]["qualified_t120_cells"],
                    "t120_grid_cells": binding["counts"]["t120_grid_cells"], "coverage": [{k: r[k] for k in ("season", "target", "section", "rows", "rows_with_any_admitted_source", "all_sources_absent_rows")} for r in binding["coverage"]],
                    "note": "The executed models reuse the admitted T120 source context. Source ablations rebuild aggregate inputs from the retained source set. Movement history and native exchange contract adapters remain incomplete.",
                    "providers": [{"name": "DraftKings", "state": "Allowed; admitted within bookmaker inputs", "note": "Included when its pregame identity, rights and clocks qualify. The new framework run does not establish a newly matched DraftKings benchmark comparison."},
                                  {"name": "Kalshi", "state": "Allowed; exact adapter not bound", "note": "The native contract, product and settlement join remains incomplete. Permission to use a source does not prove a usable historical benchmark."},
                                  {"name": "Polymarket Global", "state": "Allowed; exact adapter not bound", "note": "Product-specific qualification remains incomplete. Earlier public references keep their own observation dates and are not refreshed by this report."},
                                  {"name": "Polymarket US", "state": "Allowed; exact adapter not bound", "note": "Kept separate from the global product. Missing eligible comparison evidence remains explicit rather than being filled with synthetic values."}]},
        "findings": findings,
        "compute": {"model_stage_seconds": cost["registered_model_work_elapsed_seconds"], "return_finalization_seconds": cost["child_return_finalization_elapsed_seconds"],
                    "end_to_end_seconds": cost["end_to_end_elapsed_seconds"], "estimated_cost_usd": cost["estimated_end_to_end_full_host_compute_usd"],
                    "worker_ceiling": stage["max_workers_hard_ceiling"], "fit_callback_cpu_seconds": cpu_sum,
                    "cpu_acceptance": "Measured pass" if full_pass else "Conditional; sustained gate not proved",
                    "note": f"Both scientific queues reached {min(peaks)} concurrent fit callbacks. Callback CPU includes reuse, inference and fitting; optimizer-only CPU was not measured. The finite queues were shorter than the three-minute sustained acceptance window. The estimate uses the full host and ends at the saved measurement; it is not an invoice."},
        "prepared": {"release": "V090", "registered_scientific_jobs": int(prepared["registered_scientific_jobs"]),
                     "registered_fixed_blend_recipes": int(prepared.get("registered_fixed_blend_recipes", 0)),
                     "status": "PREPARED_NOT_EXECUTED", "summary": safe_text(prepared["summary"])},
        "remaining": ["The complete V12/V13 football, injury/replacement and frontier-feature program is unfinished.",
                      "Native Kalshi and Polymarket contract adapters, market movement and broader pregame horizons remain incomplete.",
                      "Separate full-denominator DraftKings, Kalshi and Polymarket benchmark comparisons require further exact-horizon qualification.",
                      "Official schedule completeness, original historical source possession and genuine prospective issue evidence remain distinct acceptance gates.",
                      "The next finite campaign follows registered feature and source gaps; 2026 outcomes do not choose its recipes, calibrators, blends or champions."],
        "provenance": {"owner_return_sha256": pointer["logical_zip_sha256"], "artifacts": [
                        {"label": label, "sha256": stage[field]["sha256"]} for label, field in (("Annual scorecards", "scorecards_artifact"), ("Validation selection lock", "selection_artifact"), ("Observed game manifest", "manifest_artifact"), ("Source binding", "binding_report"))]},
        "publication": {"status": "SOURCE_REVIEW_NOT_DEPLOYED", "owner_research_executed_by_publication": 0, "production_promoted": False},
    }
    inventory = {"schema": "fbs.public.game-inventory.v090", "as_of": as_of, "observed_game_count": len(games),
                 "postseason_included": manifest["postseason_included"], "schedule_completeness_certified": manifest["schedule_completeness_certified"],
                 "qualification": f"All {current_pending} observed 2026 nonfinal fixtures remain visible, including {unresolved} unresolved kickoffs. Numerical unissued candidate outputs are not published. An older unconfirmed fixture remains in its original season; it is not counted as a completed evaluation game.",
                 "games": games}
    # Scan text values, not decimal metric digits that resemble account identifiers.
    def public_strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for k, v in value.items():
                yield str(k)
                yield from public_strings(v)
        elif isinstance(value, list):
            for item in value:
                yield from public_strings(item)
    # A final content boundary catches accidental text carry-through in all allowed fields.
    for value in (report, inventory):
        text = json.dumps(value, allow_nan=False)
        if any(PRIVATE_PATTERN.search(s) for s in public_strings(value)):
            raise ValueError("Private locator or executable appeared in the public projection")
        for key in aliases:
            if key[0] in text:
                raise ValueError("Private policy identity appeared in the public projection")
    return report, inventory, aliases


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", required=True, type=Path, help="Local private input-location manifest; never publish this file")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.inputs.read_text())
    pointer = json.loads(Path(cfg["latest_return"]).read_text())
    ret = read_pinned(cfg["return_manifest"], pointer["manifest"])
    stage = read_pinned(cfg["stage"], ret["payloads"][cfg["stage_member"]])
    cards = read_pinned(cfg["cards"], stage["scorecards_artifact"])
    selection = read_pinned(cfg["selection"], stage["selection_artifact"])
    manifest = read_pinned(cfg["manifest"], stage["manifest_artifact"])
    binding = read_pinned(cfg["binding"], stage["binding_report"])
    old_stage = read_pinned(cfg["prior_stage"], stage["inherited_v088_market_stage"])
    prior_selection = read_pinned(cfg["prior_selection"], old_stage["selection_artifact"])
    stress = read_pinned(cfg["stress"], stage["stress_scorecards_artifact"])
    cpu = [read_pinned(r["path"], ret["payloads"][r["member"]]) for r in cfg["cpu_reports"]]
    report, inventory, aliases = project(cards, selection, manifest, binding, stage, pointer, prior_selection, stress, cpu, cfg["prepared"])
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("review.json", report), ("games.json", inventory)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"public_models": len(report["models"]), "annual_cards": len(cards), "leaders": len(report["selection"]["leaders"]), "validation_ranks": len(report["selection"]["ranks"]), "observed_games": len(inventory["games"]), "owner_fits_performed": 0, "provider_requests": 0, "private_policy_ids_published": 0}))


if __name__ == "__main__":
    main()
