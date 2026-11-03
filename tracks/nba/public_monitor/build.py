"""Render a network-free public NBA evidence page from allowlisted aggregates."""
from __future__ import annotations

import argparse
from html import escape
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).with_name("evidence-v2.json")
OUTPUT = ROOT / "docs/nba/monitor.html"
PROVIDERS = ["DraftKings", "Kalshi", "Polymarket US", "Polymarket international"]
METRIC_KEYS = {"season", "model", "view", "evidence_class", "n", "correct", "log_loss", "brier", "accuracy", "auc", "ece", "margin_mae", "margin_rmse", "total_mae", "total_rmse"}
TOP_KEYS = {"schema", "evidence_kind", "published_on", "snapshot_finished_at", "snapshot_label", "current_evidence_class", "historical_development_exposed", "raw_source_pretip_possession_closure", "current_season_selection_allowed", "rolling_current_protocol", "latest_execution", "metrics", "providers", "market_conclusion", "paper_decision", "historical_pnl", "public_real_model_fits", "public_network_requests", "public_fixture_kind", "scope_note"}
TOP_KEYS |= {"latest_refresh", "active_provider_families", "provider_policy_effective_on"}


def validate(data: dict) -> dict:
    """Fail closed on unreviewed fields, inflated execution, or widened cohorts."""
    if set(data) != TOP_KEYS or data.get("schema") != "public.nba.monitor.v2":
        raise ValueError("allowlisted public aggregate schema required")
    if data["evidence_kind"] != "SANITIZED_AUTHENTICATED_AGGREGATES":
        raise ValueError("actual aggregate evidence class required")
    for key, expected in (("historical_development_exposed", True),
                          ("raw_source_pretip_possession_closure", False),
                          ("current_season_selection_allowed", False),
                          ("rolling_current_protocol", "INACTIVE"),
                          ("current_evidence_class", "RETROSPECTIVE_FIXED_CAUSAL_RECONSTRUCTION_NOT_ISSUED"),
                          ("market_conclusion", "EDGE_NOT_ESTABLISHED"),
                          ("paper_decision", "NO BET"), ("historical_pnl", None),
                          ("public_real_model_fits", 0), ("public_network_requests", 0),
                          ("public_fixture_kind", "INVENTED")):
        if data[key] != expected or type(data[key]) is not type(expected):
            raise ValueError("scientific evidence boundary changed: " + key)
    execution = data["latest_execution"]
    expected_execution = {"owner_status", "historical_fits_completed", "historical_fits_planned", "prior_completed_study_fits", "current_season_fits", "challenger_promotions", "fresh_results_admitted", "failure_class", "new_credit_from_reusing_completed_fits"}
    if set(execution) != expected_execution:
        raise ValueError("execution accounting must use reviewed public fields")
    if (execution["owner_status"] != "FAILED" or execution["fresh_results_admitted"] is not False
            or execution["historical_fits_completed"] != 366 or execution["historical_fits_planned"] != 366
            or execution["prior_completed_study_fits"] != 654
            or any(execution[key] != 0 for key in ("current_season_fits", "challenger_promotions", "new_credit_from_reusing_completed_fits"))):
        raise ValueError("completed historical work cannot upgrade a failed owner")
    refresh = data["latest_refresh"]
    expected_refresh = {"owner_status", "new_estimator_fits", "reused_completed_historical_fits",
                        "software_tests_passed", "current_season_fits", "challenger_promotions",
                        "fresh_results_admitted", "failure_class"}
    if (set(refresh) != expected_refresh or refresh["owner_status"] != "FAILED"
            or refresh["fresh_results_admitted"] is not False
            or refresh["reused_completed_historical_fits"] != 366
            or refresh["software_tests_passed"] != 758
            or any(refresh[k] != 0 for k in ("new_estimator_fits", "current_season_fits", "challenger_promotions"))):
        raise ValueError("latest failed refresh cannot gain fit or publication credit")
    if (data["active_provider_families"] != ["DraftKings", "Kalshi", "Polymarket"]
            or data["provider_policy_effective_on"] != "2026-11-03"):
        raise ValueError("active three-provider policy changed without review")
    expected_cohorts = [("2024–25", 1164, 762), ("2025–26", 1164, 791), ("2026–27", 94, 61)]
    if [(r.get("season"), r.get("n"), r.get("correct")) for r in data["metrics"]] != expected_cohorts:
        raise ValueError("dated fixed-model cohorts changed without a new publication review")
    for row in data["metrics"]:
        if set(row) != METRIC_KEYS or row["model"] != "B003 frozen control":
            raise ValueError("reviewed control aggregates only; no individual forecasts")
        if abs(row["accuracy"] - row["correct"] / row["n"]) > 1e-12:
            raise ValueError("accuracy and exact denominator disagree")
        if row["season"] == "2026–27" and row["evidence_class"] != data["current_evidence_class"]:
            raise ValueError("reconstructions are not genuinely issued forecasts")
        if row["season"] != "2026–27" and row["evidence_class"] != "DEVELOPMENT_EXPOSED_RECONSTRUCTION":
            raise ValueError("historical exposure must remain visible")
        for key in ("log_loss", "brier", "accuracy", "auc", "ece", "margin_mae", "margin_rmse", "total_mae", "total_rmse"):
            value = row[key]
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
                raise ValueError("finite nonnegative diagnostic required")
            if key in {"brier", "accuracy", "auc", "ece"} and value > 1:
                raise ValueError("probability diagnostic outside range")
    if [row.get("provider") for row in data["providers"]] != PROVIDERS:
        raise ValueError("all provider scopes must remain separate and visible")
    for row in data["providers"]:
        if set(row) != {"provider", "qualified_current_games", "disagreement_accuracy", "profit", "gap",
                       "raw_historical_coverage", "disagreement_model_right", "disagreement_provider_right"}:
            raise ValueError("only public provider coverage aggregates are allowed")
        if row["qualified_current_games"] != 0 or row["disagreement_accuracy"] is not None or row["profit"] is not None:
            raise ValueError("unestablished provider edge or profit")
        if (row["raw_historical_coverage"] != "NOT_EVALUATED"
                or row["disagreement_model_right"] is not None or row["disagreement_provider_right"] is not None):
            raise ValueError("unknown provider history cannot become zero or fabricated disagreement counts")
    serialized = json.dumps(data, ensure_ascii=False)
    if re.search(r"s3://|/home/|/workspace/|[a-f0-9]{64}|\.pyz|return_[0-9]|AKIA[0-9A-Z]{16}", serialized):
        raise ValueError("private operational identifier in public evidence")
    return data


def metric(value, digits=4, percent=False):
    if value is None:
        return "Not reported"
    return f"{value * 100:.1f}%" if percent else f"{value:.{digits}f}"


def render(data):
    validate(data)
    current = data["metrics"][-1]
    rows = []
    columns = [("winner", "log_loss", 4, False), ("winner", "brier", 4, False),
               ("winner", "accuracy", 1, True), ("winner", "auc", 4, False), ("winner", "ece", 4, False),
               ("margin", "margin_mae", 2, False), ("margin", "margin_rmse", 2, False),
               ("total", "total_mae", 2, False), ("total", "total_rmse", 2, False)]
    for row in data["metrics"]:
        cells = "".join(f'<td data-objective="{objective}">{metric(row[key], digits, percent)}</td>'
                        for objective, key, digits, percent in columns)
        label = "Fixed-model diagnostic; not issued" if row["season"] == "2026–27" else "Development-exposed reconstruction"
        rows.append(f'<tr data-season="{escape(row["season"])}"><th scope="row">{escape(row["season"])}<small>{label}</small></th><td>{row["n"]:,}</td>{cells}</tr>')
    providers = "".join(f'<tr><th scope="row">{escape(row["provider"])}</th><td>0 admitted</td><td>Not evaluated</td><td>Not estimable</td><td>Unknown</td><td>{escape(row["gap"])}</td></tr>' for row in data["providers"])
    # No private payload is embedded: the interactive page only filters existing
    # aggregate table cells and runs a two-event invented arithmetic example.
    return TEMPLATE.replace("{{ROWS}}", "\n".join(rows)).replace("{{PROVIDERS}}", providers).replace(
        "{{CURRENT_LL}}", metric(current["log_loss"])).replace("{{CURRENT_BRIER}}", metric(current["brier"])).replace(
        "{{CURRENT_ACC}}", metric(current["accuracy"], percent=True)).replace("{{CURRENT_ECE}}", metric(current["ece"])).replace(
        "{{SNAPSHOT}}", escape(data["snapshot_finished_at"]))


TEMPLATE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A dated NBA frozen-control diagnostic, honest provider coverage, and a reproducible example of retaining a loss when a source refresh drops an older final.">
<title>NBA evidence monitor | Sports Edge Lab</title>
<style>
:root{color-scheme:light;--ink:#172d3d;--muted:#4b6273;--navy:#102a3a;--teal:#006c68;--line:#cddce3;--paper:#f3f7f8;--warm:#fff4dc;--warn:#704800}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:#00677e;text-underline-offset:3px}button,select{font:inherit}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #ba6400;outline-offset:4px}[hidden]{display:none!important}.skip{position:absolute;left:20px;top:-100px;background:#fff;padding:12px;z-index:10}.skip:focus{top:12px}
header{background:var(--navy);color:#fff}header>div,main,footer{max-width:1200px;margin:auto;padding:32px}nav{display:flex;gap:22px;flex-wrap:wrap;font-size:.9rem}header a{color:#c5efec}.eyebrow{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;font-weight:750;margin:0 0 10px}h1{font-size:clamp(2.1rem,4.7vw,3.7rem);line-height:1.12;letter-spacing:-.035em;max-width:850px;margin:24px 0 18px}h2{font-size:1.6rem;line-height:1.25;letter-spacing:-.02em;margin:0 0 14px}h3{font-size:1.05rem;margin:0 0 8px}.lede{max-width:850px;color:#d5e8ef;font-size:1.09rem}.header-line{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:24px}.badge{border-radius:6px;padding:4px 10px;font-size:.78rem;font-weight:750;background:#daf1e8;color:#105242}.badge.warn{background:var(--warm);color:var(--warn)}.header-line small{color:#d5e8ef}
main{padding-top:28px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.metric,.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px}.metric strong{font-size:2.2rem;line-height:1.2;display:block;margin:6px 0}.metric span{font-size:.84rem;color:var(--muted)}.metric .unit{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em}.panel{margin-top:24px}.boundary{border-left:5px solid #ba7a1a;background:var(--warm);border-radius:8px;padding:20px 24px;margin:22px 0}.boundary p{margin:4px 0}.muted{color:var(--muted)}.small{font-size:.86rem}.split{display:grid;grid-template-columns:1fr 1fr;gap:28px}.filters{display:flex;flex-wrap:wrap;gap:18px;align-items:end;margin:18px 0}.field label{display:block;font-size:.85rem;font-weight:650;margin-bottom:5px}select{border:1px solid #8297a4;border-radius:7px;background:#fff;color:var(--ink);padding:8px 12px;min-width:180px;min-height:44px}.scroll{overflow-x:auto;max-width:100%;border-radius:8px}table{border-collapse:collapse;width:100%;font-size:.9rem}caption{text-align:left;color:var(--muted);padding:8px 0 12px;font-size:.85rem}th,td{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}thead th{background:#edf4f6;font-size:.78rem;white-space:nowrap}tbody th{min-width:165px}th small{display:block;font-weight:400;font-size:.73rem;line-height:1.45;color:var(--muted);min-width:150px}td{white-space:nowrap}.providers td:last-child{white-space:normal;min-width:270px}.status{margin:8px 0;font-size:.85rem;color:var(--muted)}.legend{font-size:.84rem;color:var(--muted);max-width:950px}
.path{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.step{border:1px solid var(--line);border-top:4px solid var(--teal);padding:18px;border-radius:8px}.step p{margin:5px 0 0;font-size:.9rem}.step.fail{border-top-color:#b16a05}.step .count{font-size:2rem;font-weight:750;margin:6px 0;line-height:1.2}.demo{background:#edf7f5;border:1px solid #b4d6ce;border-radius:10px;padding:22px}.demo-output{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}.demo-output div{background:#fff;border-radius:7px;padding:14px}.demo-output strong{display:block;font-size:1.45rem}.demo-output span{font-size:.79rem;color:var(--muted)}.no-bet{border:1px solid #d7bd86;background:var(--warm);padding:14px 18px;border-radius:8px}details{border-top:1px solid var(--line);padding:16px 0}summary{cursor:pointer;font-weight:650;min-height:35px}code{background:#e9f0f3;border-radius:4px;padding:2px 5px;overflow-wrap:anywhere}pre{background:#102a3a;color:#e5f2f4;border-radius:10px;padding:18px;overflow-x:auto;font-size:.83rem}pre code{background:none;padding:0;color:inherit}.links{display:flex;flex-wrap:wrap;gap:18px;margin-top:14px}footer{color:var(--muted);font-size:.83rem;padding-top:24px}
@media(max-width:820px){header>div,main,footer{padding:22px}.metrics{grid-template-columns:repeat(2,1fr)}.split,.path{grid-template-columns:1fr}.panel{padding:20px}.metric{padding:18px}.metric strong{font-size:1.9rem}}@media(max-width:460px){.metrics,.demo-output{grid-template-columns:1fr 1fr}.metric strong{font-size:1.75rem}.demo-output div:last-child{grid-column:1/-1}.filters{display:block}.field{margin:12px 0}select{width:100%}h1{font-size:2.35rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{header{background:#fff;color:#172d3d}header a,.lede,.header-line small{color:#172d3d}.filters{display:none}.panel,.metric{break-inside:avoid}a{color:inherit}}
</style><script src="monitor.js" defer></script></head><body>
<a class="skip" href="#main">Skip to evidence</a>
<header><div><nav aria-label="Project navigation"><a href="../../README.md">Sports Edge Lab</a><a href="../../tracks/nba/README.md">NBA track</a><a href="index.html">Preserved October 29 snapshot</a><a href="../../tracks/nba/public_monitor/README.md">Reproduce this example</a></nav>
<h1>NBA evidence.<br>Measured progress, explicit limits.</h1>
<p class="lede">A frozen-model diagnostic, honest three-provider coverage, and executable examples of preserving both a prior loss and an original prediction.</p>
<div class="header-line"><span class="badge warn">Last admitted snapshot · 94 games</span><span class="badge warn">No qualified market edge</span><small>Published November 3, 2026 · not a live feed</small></div></div></header>
<main id="main" tabindex="-1">
<section class="metrics" aria-label="Dated current-season frozen-model diagnostics">
<div class="metric"><span class="unit">Log loss · lower is better</span><strong>{{CURRENT_LL}}</strong><span>94-game fixed-model diagnostic</span></div>
<div class="metric"><span class="unit">Brier score · lower is better</span><strong>{{CURRENT_BRIER}}</strong><span>Same 94 games, same probability target</span></div>
<div class="metric"><span class="unit">Winner accuracy</span><strong>{{CURRENT_ACC}}</strong><span>61 correct / 94 · descriptive only</span></div>
<div class="metric"><span class="unit">Calibration ECE · 10 bins</span><strong>{{CURRENT_ECE}}</strong><span>Imperfect calibration remains visible</span></div></section>
<aside class="boundary" aria-labelledby="boundary-title"><h2 id="boundary-title">94 reconstructions are not 94 issued forecasts.</h2><p>The model parameters are frozen, but this aggregate is a <strong>retrospective fixed causal reconstruction</strong>. Actual raw-source pre-tip possession closure is not established. It must not be presented as a prospective 94-game track record or a betting return.</p><p class="small">Last fully admitted owner finished <time datetime="{{SNAPSHOT}}">November 2, 2026, 6:57 p.m. Pacific</time>. Two later owner attempts remain failed: a missing older final, then a reconstruction-version mismatch. This page does not silently substitute either newer frame. No current-season model selection or promotion is permitted.</p></aside>
<section class="panel" aria-labelledby="diagnostics-title"><p class="eyebrow">One control · consistent definitions</p><h2 id="diagnostics-title">Three seasons, three prediction objectives</h2><p class="muted">This is the original B003 control, not an all-model leaderboard. Each row uses the displayed common game cohort for winner, margin and total diagnostics. Current-season performance cannot select a replacement model.</p>
<div class="filters" id="filters" hidden><div class="field"><label for="season-filter">Season</label><select id="season-filter"><option value="all">All seasons</option><option value="2024–25">2024–25</option><option value="2025–26">2025–26</option><option value="2026–27">2026–27</option></select></div><div class="field"><label for="objective-filter">Prediction objective</label><select id="objective-filter"><option value="all">All objectives</option><option value="winner">Winner</option><option value="margin">Margin</option><option value="total">Total points</option></select></div></div>
<p class="status" id="filter-status" role="status" aria-live="polite">Showing all 3 dated cohorts and all objectives.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable season diagnostic table"><table id="metrics-table"><caption>Natural-log loss; binary Brier; home-win threshold 0.5; points for margin/total errors. Ten-bin ECE is descriptive.</caption><thead><tr><th scope="col">Season / evidence</th><th scope="col">Games</th><th scope="col" data-objective="winner">Log loss ↓</th><th scope="col" data-objective="winner">Brier ↓</th><th scope="col" data-objective="winner">Accuracy ↑</th><th scope="col" data-objective="winner">ROC AUC ↑</th><th scope="col" data-objective="winner">ECE ↓</th><th scope="col" data-objective="margin">Margin MAE ↓</th><th scope="col" data-objective="margin">Margin RMSE ↓</th><th scope="col" data-objective="total">Total MAE ↓</th><th scope="col" data-objective="total">Total RMSE ↓</th></tr></thead><tbody>{{ROWS}}</tbody></table></div>
<p class="legend">Historical seasons are development-exposed, with incomplete original point-in-time provenance. Better retrospective scores alone do not qualify a promotion. Equal metric definitions do not make different seasons the same comparison cohort. No 0.46 current-season NBA log loss is supported by this admitted snapshot.</p></section>
<section class="panel" aria-labelledby="execution-title"><p class="eyebrow">Execution accounting</p><h2 id="execution-title">Useful completed work is preserved. Overall failure stays failure.</h2><div class="path"><article class="step"><h3>Previously completed study</h3><p class="count">654</p><p>Historical estimator fits from the last completed study. Reuse earns zero additional fit credit.</p></article><article class="step"><h3>Preserved historical branch</h3><p class="count">366 / 366</p><p>Historical fits completed with saved evidence. The subsequent refresh reused them; it performed zero new fits.</p></article><article class="step fail"><h3>Latest refresh owner</h3><p class="count">FAILED</p><p>758 software tests passed, but a retained reconstruction changed after source inputs refreshed. Publication stopped; original forecasts were not overwritten.</p></article></div><p class="legend">Tests are not estimator fits. Two failed owners remain failed. Historical base out-of-fold provenance remains unverified, and proxy label-release times are not actual possession timestamps. The rolling current-season protocol remains inactive.</p></section>
<section class="panel" aria-labelledby="demo-title"><div class="split"><div><p class="eyebrow">Reproducible failure case · invented data</p><h2 id="demo-title">A source refresh must not erase a loss.</h2><p>In this two-event toy example, the first home favorite loses and the second wins. Both probabilities are 70%. The fresh response contains only the second final.</p><p>Replacing stored results would make the model look perfect. A qualified result union preserves the earlier loss; a conflicting correction stops for explicit versioning.</p><p class="small muted">These are invented events and probabilities, not NBA picks. The public code has no production model, network request, or real estimator fit. Rolling and frozen toy tracks remain separate; differing sample counts are not compared as a matched experiment.</p></div>
<div class="demo"><label for="demo-mode"><strong>Result handling</strong></label><select id="demo-mode" disabled><option value="union">Preserve qualified finals (accepted)</option><option value="fresh">Replace with fresh response (rejected)</option></select><p id="demo-status" role="status" aria-live="polite">Accepted toy union: the prior loss remains.</p><div class="demo-output"><div><span>Winner accuracy</span><strong id="demo-accuracy">50.0%</strong></div><div><span>Log loss</span><strong id="demo-log-loss">0.7803</strong></div><div><span>Invented scored games</span><strong id="demo-games">2</strong></div></div></div></div></section>
<section class="panel" aria-labelledby="versions-title"><div class="split"><div><p class="eyebrow">Second reproducible example · invented data</p><h2 id="versions-title">Frozen parameters. Versioned inputs. Immutable issues.</h2><p>A fitted model may produce 70% on an earlier source snapshot and 62% on a later one. That difference is input drift, not permission to rewrite its original 70% issue.</p><p>Separate the original pre-cutoff issue from the later reconstruction. Same-input numerical parity remains a strict test; different-source reconstructions are archived as new versions with zero prospective credit.</p><p class="small muted">The numbers and events in this example are invented. No actual NBA forecast or private feature recipe is published.</p></div><div class="demo"><label for="version-mode"><strong>Prediction evidence view</strong></label><select id="version-mode" disabled><option value="issued">Original issued snapshot</option><option value="reconstruction">Later reconstruction (not issued)</option></select><p id="version-status" role="status" aria-live="polite">Original invented issue remains 70.0%; no source refresh can edit it.</p><div class="demo-output"><div><span>Displayed home-win probability</span><strong id="version-probability">70.0%</strong></div><div><span>Immutable archived versions</span><strong>2</strong></div><div><span>New prospective credit from refresh</span><strong>0</strong></div></div></div></div></section>
<section class="panel" aria-labelledby="market-title"><p class="eyebrow">Three providers · uniform comparison</p><h2 id="market-title">Zero admitted comparisons does not mean zero source coverage.</h2><p>The active scope is <strong>DraftKings, Kalshi and Polymarket</strong>, effective November 3. Polymarket US and international remain distinct products. Older provider evidence is preserved in the versioned archive, not silently deleted or newly acquired.</p><p>Each comparison must match event, ordered side, target and line, declared horizon, quote and possession clocks, product, and settlement. Winner probabilities and executable financial returns have different evidence requirements.</p><div class="scroll" tabindex="0" role="region" aria-label="Scrollable provider coverage table"><table class="providers"><caption>Admitted current common-cohort comparisons for this dated public snapshot. Raw historical coverage is not independently evaluated here. Model-right/provider-wrong and provider-right/model-wrong counts both remain unknown.</caption><thead><tr><th scope="col">Provider scope</th><th scope="col">Current comparisons</th><th scope="col">Raw history</th><th scope="col">Disagreement accuracy</th><th scope="col">Profit / ROI</th><th scope="col">What remains missing</th></tr></thead><tbody>{{PROVIDERS}}</tbody></table></div><p class="no-bet"><strong>NO BET · Edge not established.</strong> No quoted price, fee, depth, profit or joint outcome probability is invented. Missing historical P&amp;L is unknown, not zero. The publication does not assume provider or jurisdiction access.</p></section>
<section class="panel" aria-labelledby="reproduce-title"><p class="eyebrow">Five-minute engineering review</p><h2 id="reproduce-title">Inspect the boundary, then run the negative tests.</h2><p>Python standard library plus optional Node.js; no data credentials, package downloads, private model files or paid provider calls.</p><pre><code>python -m tracks.nba.public_monitor
python -m unittest discover -s tracks/nba/public_monitor/tests -v
python -m tracks.nba.public_monitor.build --check
node --test docs/nba/monitor.test.cjs</code></pre><div class="links"><a href="../../tracks/nba/public_monitor/README.md">Walkthrough and limitations</a><a href="../../tracks/nba/public_monitor/evidence-v2.json">Current publication capsule</a><a href="../../tracks/nba/public_monitor/evidence.json">Preserved earlier capsule</a><a href="../../tracks/nba/public_monitor/snapshot_versions.py">Source-version contracts</a><a href="../PUBLICATION_BOUNDARY.md">Public/private boundary</a></div>
<details><summary>What would establish a stronger claim?</summary><p>A separately registered rolling policy; verified historical source possession; pre-cutoff immutable issues; genuinely unseen prospective evaluation; exact matched provider products and quotes; executable depth, fees and settlement; uncertainty intervals that reflect weeks and repeated research. More fits or a polished dashboard do not substitute for these.</p></details>
<details><summary>What this public demo does and does not reproduce</summary><p>It reproduces invented information-time gates, result-union behavior, immutable issue handling, basic metric arithmetic, and partial-owner accounting. It does not reproduce licensed datasets, proprietary estimators, the complete private modeling study, current game picks, or a live betting system. Browser interaction logic and HTML semantics are tested; this is not a claim of a complete external accessibility audit.</p></details>
<noscript><p class="boundary">JavaScript is off. All aggregate tables remain visible. Run the Python demonstration for the complete invented example; interactive filters are optional.</p></noscript></section>
</main><footer>Sports Edge Lab · NBA-specific public evidence, November 3, 2026. Dated snapshots remain immutable. No raw licensed data, individual forecasts, private runtime identities or production models are published.</footer></body></html>
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    content = render(json.loads(EVIDENCE.read_text()))
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != content:
            raise SystemExit("NBA monitor does not match the sanitized evidence and renderer")
        print("NBA monitor matches dated aggregates; owner failure and unknown market edge preserved.")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content)


if __name__ == "__main__":
    main()
