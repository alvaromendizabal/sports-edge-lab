"""Render retained V125 scores beside separately audited V126 serving evidence."""
from __future__ import annotations
import argparse
import hashlib
from html import escape
import json
import math
from pathlib import Path
from .serving_lineage import SOURCE as EXECUTION_SOURCE, validate_public_receipt

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/evidence/2026-10-27-v125.json"
OUTPUT = ROOT / "docs/current/index.html"
FIGURE = ROOT / "docs/assets/current-evidence.svg"
METRICS = ("win_logloss", "win_brier", "win_accuracy", "win_auc", "probability_bias", "ece10", "home_score_mae", "home_score_rmse", "away_score_mae", "away_score_rmse", "margin_mae", "margin_rmse", "total_mae", "total_rmse", "joint_nll", "mean_marginal_crps")
ROW_FIELDS = set(METRICS) | {"arm", "label", "track", "protocol", "scope", "origin", "season", "games", "cohort_sha256", "correct", "incorrect", "ties", "bank", "purpose"}


def panel_key(row: dict) -> tuple:
    return tuple(row.get(key, "") for key in ("track", "bank", "protocol", "scope", "origin", "season", "cohort_sha256", "games"))


def validate_evidence(data: dict) -> dict:
    if data.get("schema") != "sports-edge-lab.public-v125-aggregate-review":
        raise ValueError("unsupported aggregate schema")
    allowed_top = {"schema", "as_of_local", "owner_return_sha256", "owner_report_sha256", "owner", "selection_boundary", "decisions", "rows", "comparisons", "venue_rows", "venue_coverage", "limitations", "historical_profit", "actual_orders"}
    if set(data) != allowed_top:
        raise ValueError("unexpected aggregate top-level field")
    venue_fields = {"track", "cohort", "target", "cohort_sha256", "arm", "model_label", "n", "log_loss", "brier", "accuracy", "status", "reason"}
    comparison_fields = {"track", "season", "arm", "reference", "paired_logloss_difference", "brier_difference", "ci95", "league_week_blocks", "uncertainty_reason", "inference"}
    if any(set(row) - venue_fields for row in data["venue_rows"]) or any(set(row) - comparison_fields for row in data["comparisons"]):
        raise ValueError("unexpected venue or comparison field")
    boundary = data["selection_boundary"]
    if boundary["forward_first_season"] != 2026 or boundary["forward_model_selection"] is not False:
        raise ValueError("2026 must remain monitoring only")
    if any(year >= 2026 for year in boundary["historical_selection_seasons"]):
        raise ValueError("historical selection contains a forward season")
    if data["actual_orders"] != 0 or data["historical_profit"] is not None:
        raise ValueError("this export has no executable historical profit evidence")
    expected_owner = {"status": "SUCCESS", "new_fits": 20, "fit_attempts": 20, "owner_tests": 2523, "retained_native_cells": 456, "retained_fusion_fits": 6, "actual_wagers": 0, "automatic_promotions": 0}
    if any(data["owner"].get(key) != value for key, value in expected_owner.items()):
        raise ValueError("owner snapshot differs from the declared V125 review")
    seen, panels, cohort_sizes = set(), set(), {}
    for row in data["rows"]:
        if set(row) - ROW_FIELDS:
            raise ValueError("unexpected aggregate field")
        if row["track"] not in ("nfl", "ncaaf") or row["bank"] not in ("native", "experts", "fusion", "points", "distribution"):
            raise ValueError("unknown league or model bank")
        if type(row["games"]) is not int or row["games"] < 10:
            raise ValueError("invalid aggregate sample size")
        cohort = row["cohort_sha256"]
        if len(cohort) != 64 or any(c not in "0123456789abcdef" for c in cohort):
            raise ValueError("invalid exact-cohort fingerprint")
        if cohort in cohort_sizes and cohort_sizes[cohort] != row["games"]:
            raise ValueError("same cohort has conflicting sample sizes")
        cohort_sizes[cohort] = row["games"]
        forward = row.get("season") == 2026 or "2026" in row["protocol"] or row.get("scope") == "season_2026"
        if forward != (row["purpose"] == "FORWARD_MONITORING_ONLY"):
            raise ValueError("forward outcomes escaped the monitoring boundary")
        for name in METRICS:
            value = row.get(name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError("non-finite aggregate metric")
        for name in ("win_brier", "win_accuracy", "win_auc", "ece10"):
            if row.get(name) is not None and not 0 <= row[name] <= 1:
                raise ValueError("probability metric out of range")
        if "correct" in row and (any(type(row[name]) is not int or row[name] < 0 for name in ("correct", "incorrect")) or row["correct"] + row["incorrect"] != row["games"]):
            raise ValueError("pick counts do not reconcile")
        identity = panel_key(row) + (row["arm"],)
        if identity in seen:
            raise ValueError("duplicate model on an exact panel")
        seen.add(identity); panels.add(panel_key(row))
    for record in data["decisions"].values():
        if record["historical_candidate_gate"] is not False or record["current2026_used_for_selection"] or record["automatic_promotion"] or record["economic_readiness"]:
            raise ValueError("decision contradicts the recorded negative gate")
    return {"rows": len(seen), "panels": len(panels), "venue_rows": len(data["venue_rows"]), "forward_selection": False}


TEMPLATE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sports Edge Lab · Evidence & decision boundaries</title><style>
:root{--ink:#132a3d;--muted:#536a7c;--accent:#006f76;--line:#cbd9df;--paper:#f2f7f8}*{box-sizing:border-box}body{font:15px/1.6 system-ui,sans-serif;margin:0;background:var(--paper);color:var(--ink)}a{color:var(--accent)}header{padding:48px max(24px,calc((100vw - 1200px)/2));background:#132a3d;color:#fff}header a{color:#9de7dc}.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#9de7dc}h1{font-size:clamp(30px,5vw,54px);line-height:1.08;max-width:900px;font-weight:650;margin:16px 0}h2{font-size:25px;font-weight:600;margin:0 0 12px}h3{font-weight:500}header p{max-width:900px;color:#d5e2e9;font-size:18px}.shell{max-width:1248px;margin:0 auto;padding:30px 24px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}.card,.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:24px}.number{font-size:36px;line-height:1.2;color:var(--accent);margin:8px 0}.small,caption{color:var(--muted);font-size:13px}.panel{margin-bottom:24px}.boundary{background:#e6f5f1;border-left:4px solid var(--accent);padding:18px;margin:20px 0}.filters{display:grid;grid-template-columns:1fr 1fr 2fr;gap:14px}.filters label{display:flex;flex-direction:column;font-size:13px;color:var(--muted);gap:6px}select,input{font:inherit;padding:10px;border:1px solid #a9bec8;border-radius:5px;background:white;color:var(--ink);min-width:0}.table-wrap{overflow:auto;max-height:650px;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:13px}caption{text-align:left;padding:14px;caption-side:top}th,td{padding:10px 12px;border-bottom:1px solid #e0e8ec;text-align:left;white-space:nowrap}th{font-weight:500;background:#edf4f6}thead{position:sticky;top:0}td.numeric{text-align:right;font-variant-numeric:tabular-nums}.winner{font-weight:700;color:#00694f}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}code{font-size:12px;overflow-wrap:anywhere}.tag{display:inline-block;border:1px solid #6aa7a7;border-radius:20px;padding:4px 12px;color:#bce7df;font-size:12px}ul{padding-left:22px}footer{color:var(--muted);padding-bottom:35px}@media(max-width:800px){.cards,.two{grid-template-columns:1fr 1fr}.filters{grid-template-columns:1fr}h1{font-size:36px}}@media(max-width:500px){.cards,.two{grid-template-columns:1fr}header{padding:30px 24px}}
a:focus-visible,select:focus-visible,input:focus-visible,.table-wrap:focus-visible{outline:3px solid #b96c00;outline-offset:4px}.skip-link{position:absolute;top:-60px;left:16px;z-index:2;background:#fff;color:#132a3d;padding:12px}.skip-link:focus{top:12px}meter{width:100%;height:20px}th[scope=row]{font-weight:400;background:transparent}</style><a class="skip-link" href="#main">Skip to evidence</a><header><div class="eyebrow">Alvaro Mendizabal · Sports Edge Lab</div><h1>Evidence that survives<br>the decision boundary.</h1><p>Historical model selection. Immutable decisions. Forward monitoring that cannot silently choose the winner.</p><span class="tag">V126 completed · historical selection verified</span><p><a href="../../README.md">Project overview</a> · <a href="../HISTORICAL_SELECTION_BOUNDARY.md">Review the contract</a> · <a href="../../notebooks/engineering_review.ipynb">Executed notebook</a></p></header>
<main id="main" class="shell">__EXECUTION_CARDS____EXECUTION_PANEL__<noscript><section class="panel"><h2>Evidence without JavaScript</h2><p>The execution summary below is static. Interactive score filters require JavaScript; the <a href="../evidence/2026-10-27-v125.json">complete aggregate score export</a> remains available.</p></section></noscript>
<section class="panel"><h2>Retained model research. A negative scientific decision.</h2><p>V125 added chronological conditional experts to the retained systems. Both NFL and FBS historical qualification gates failed. Successful fitting and a lower isolated score do not establish a qualified champion.</p><div class="boundary">The 2026–2027 campaign is monitoring only. Its outcomes cannot select a champion, calibrator, feature set, ensemble, threshold or staking policy. Every retrospectively inspected historical panel is already exposed. A credible new claim requires a frozen decision and later evidence.</div><p class="small">Historical comparisons below may emphasize only a numeric minimum on an identical cohort, protocol and origin. This is a descriptive score comparison, not a promotion or significance claim. Forward panels always use stable model identifiers, with no winner emphasis or performance ordering.</p></section>
<section class="panel"><h2>Inspect an exact comparison panel.</h2><p class="small">Choose the scientific role first, then the league and panel. Sample size and cohort fingerprints prevent unmatched games from becoming a leaderboard.</p><div class="filters"><label>Evidence role<select id="role"><option value="historical">Historical evaluation · exposed</option><option value="monitor">2026–2027 · monitoring only</option><option value="development">2023 development · exposed</option></select></label><label>League<select id="league"><option value="nfl">NFL</option><option value="ncaaf">FBS</option></select></label><label>Exact panel<select id="panel"></select></label><label>Metric<select id="metric"><option value="win_logloss">Win log loss ↓</option><option value="win_brier">Win Brier score ↓</option><option value="win_accuracy">Win accuracy ↑</option><option value="ece10">Calibration ECE10 ↓</option><option value="home_score_mae">Home points MAE ↓</option><option value="away_score_mae">Away points MAE ↓</option><option value="margin_mae">Margin MAE ↓</option><option value="total_mae">Total MAE ↓</option><option value="joint_nll">Joint NLL ↓</option><option value="mean_marginal_crps">Marginal CRPS ↓</option></select></label><label>Model filter<input id="search" type="search" placeholder="Stable model identifier"></label></div><p id="status" class="small" aria-live="polite"></p><div class="table-wrap" tabindex="0" role="region" aria-label="Exact matched model metrics"><table><caption id="caption"></caption><thead><tr><th scope="col">Model / information bank</th><th scope="col">Games</th><th scope="col">Metric</th><th scope="col">Correct</th><th scope="col">Incorrect</th><th scope="col">Origin</th></tr></thead><tbody id="scores"></tbody></table></div><p id="fingerprint" class="small"></p><p class="small">A missing value means this metric was not emitted for that model/task. The model filter does not redefine the comparison winner. Correct picks reflect the target in the source scorecard; ties and joint-score tasks have distinct cohorts.</p></section>
<div class="two"><section class="panel"><h2>Execution is a separate claim.</h2><p>Kalshi and Polymarket US are retained as distinct diagnostics. Archive completeness does not prove an available ask, sufficient displayed depth, a fee schedule, a fill or the correct settlement payoff.</p><div class="table-wrap"><table><caption>2026 archive intersection counts · no profit estimate</caption><thead><tr><th scope="col">League</th><th scope="col">Venue cohort</th><th scope="col">Games</th></tr></thead><tbody>__VENUES__</tbody></table></div><p class="small">NFL comparisons use a conditional non-tie probability versus contract-midpoint proxy. That target mismatch prevents an economic interpretation. Historical net profit remains unavailable.</p><a href="../evidence/2026-10-27-v125.json">Full aggregate export, including 1,586 venue diagnostics</a></section><section class="panel"><h2>Inspect the mechanisms.</h2><ul><li><a href="../../examples/review_lab/historical_selection.py">Historical selection guard</a>: rejects forward outcomes, mismatched cohorts and post-freeze evidence.</li><li><a href="../../examples/review_lab/decision_replay.py">Immutable paper ledger</a>: freezes an outcome-free decision before separate settlement.</li><li><a href="../CASE_STUDY_SELECTION_TO_DECISION.md">Selection-to-decision case study</a>: connects chronology, interaction research and execution evidence.</li><li><a href="../PUBLICATION_BOUNDARY.md">Publication boundary</a>: public mechanics and aggregate evidence; private research assets stay private.</li></ul><p class="small">Examples use invented data and illustrative rules. They are not the private football selection recipe, a market connector or an automated trading system.</p></section></div>
<section class="panel"><h2>Preserve uncertainty and rejected hypotheses.</h2><p>The export retains paired weekly-block uncertainty for 180 expert comparisons. These are exposed exploratory comparisons, with no multiplicity correction or prospective claim. Conditional experts may capture interactions, but feature complexity and a favorable current-season score do not overrule failed historical qualification.</p><p><a href="../CASE_STUDY_JOINT_EVIDENCE.md">Earlier factorial interaction experiment</a> · <a href="../CASE_STUDY_SCORE_DISTRIBUTIONS.md">Joint score distributions</a> · <a href="../CASE_STUDY_PROVENANCE.md">Content-pinned recovery</a> · <a href="../review/index.html">Dated V120 archive</a></p></section></main><footer class="shell">Generated without external requests from sanitized aggregate evidence. Score export SHA-256 <code>__SHA__</code>.<br>V126 execution export SHA-256 <code>__EXECUTION_SHA__</code>.<br>Public reproduction validates engineering mechanics; it does not reproduce private football training or certify a market edge.</footer><script type="application/json" id="current-data">__PAYLOAD__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('current-data').textContent);
const ids=['track','bank','protocol','scope','origin','season','cohort_sha256','games'];
const key=r=>JSON.stringify(ids.map(k=>r[k]??''));
const role=r=>r.purpose==='FORWARD_MONITORING_ONLY'?'monitor':r.protocol.startsWith('development')?'development':'historical';
const stable=(a,b)=>a.arm.localeCompare(b.arm)||String(a.label||'').localeCompare(String(b.label||''));
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function panels(){const league=document.getElementById('league').value, chosen=document.getElementById('role').value;const options=new Map();for(const row of data.rows)if(row.track===league&&role(row)===chosen)options.set(key(row),row);return [...options.entries()].sort((a,b)=>a[0].localeCompare(b[0]));}
function setPanels(){const element=document.getElementById('panel');element.replaceChildren();for(const [value,row]of panels()){const option=document.createElement('option');option.value=value;option.textContent=[row.bank,row.protocol,row.scope,row.origin||'',row.games+' games'].filter(Boolean).join(' · ');element.append(option);}element.value=element.children.length?element.children[0].value:'';render();}
function render(){const selected=document.getElementById('panel').value,metric=document.getElementById('metric').value,search=document.getElementById('search').value.toLowerCase();const full=data.rows.filter(r=>key(r)===selected).sort(stable);const visible=full.filter(r=>(r.arm+' '+(r.label||'')).toLowerCase().includes(search));const values=full.map(r=>r[metric]).filter(finite);const best=values.length>=2?(metric==='win_accuracy'?Math.max(...values):Math.min(...values)):null;const monitoring=document.getElementById('role').value==='monitor';const table=document.getElementById('scores');table.replaceChildren();for(const row of visible){const tr=document.createElement('tr');const entries=[row.label?row.arm+' · '+row.label:row.arm,row.games,finite(row[metric])?row[metric].toFixed(6):'—',row.correct??'—',row.incorrect??'—',row.origin||'chronological'];entries.forEach((value,i)=>{const td=document.createElement(i===0?'th':'td');if(i===0)td.scope='row';td.textContent=String(value);td.className=i>0&&i<5?'numeric':'';if(i===2&&!monitoring&&best!==null&&row[metric]===best)td.className+=' winner';tr.append(td)});table.append(tr);}document.getElementById('status').textContent=visible.length+' of '+full.length+' model rows · stable identifier order · '+(monitoring?'MONITORING ONLY; no winner selection':'exposed historical diagnostics; no promotion');document.getElementById('caption').textContent=metric+' · '+(monitoring?'2026 monitoring, no performance ranking':'exact-cohort descriptive comparison');document.getElementById('fingerprint').textContent=full.length?'Cohort SHA-256: '+full[0].cohort_sha256:'';}
for(const id of ['role','league'])document.getElementById(id).addEventListener('change',setPanels);
for(const id of ['panel','metric'])document.getElementById(id).addEventListener('change',render);
document.getElementById('search').addEventListener('input',render);setPanels();
</script></html>'''


def execution_panel(data: dict, verified: dict) -> tuple[str, str]:
    owner = data["owner"]
    cards = '<section class="cards" aria-label="Verified V126 owner result">'
    for label, value, detail in (
        ("Selected market references", verified["reference_rows"], "Benchmark rules; zero learned policies qualified"),
        ("Owner verification", owner["owner_tests"], "Passed in the actual AWS execution"),
        ("Worker elapsed", f"{owner['worker_seconds']:.1f} s", "Zero new fits; prior fitted work retained"),
        ("Actual orders", owner["actual_wagers"], "No automatic promotion; profit unavailable")):
        rendered = f"{value:,}" if type(value) is int else value
        cards += f'<div class="card"><div>{escape(label)}</div><div class="number">{escape(str(rendered))}</div><div class="small">{escape(detail)}</div></div>'
    cards += '</section>'
    clocks = (("Historical policy available", data["selection"]["available_at"]),
              ("References actually issued", data["issue"]["issued_at"]),
              ("Authoritative ledger created", data["ledger"]["created_at"]))
    rows = ''.join(f'<tr><th scope="row">{escape(label)}</th><td>{escape(clock)}</td></tr>' for label, clock in clocks)
    stages = sorted(data["performance_stages"], key=lambda item: (-item["seconds"], item["stage"]))[:5]
    bars = ''.join(f'<tr><th scope="row">{escape(item["stage"].replace("_", " ").title())}</th><td class="numeric">{item["seconds"]:.2f} s</td><td><meter min="0" max="{owner["worker_seconds"]}" value="{item["seconds"]}" aria-label="{escape(item["stage"])} fraction of worker time">{item["seconds"]:.2f} seconds</meter></td></tr>' for item in stages)
    panel = f'<section class="panel" aria-labelledby="owner-result"><h2 id="owner-result">The selected policy is the served policy.</h2><p>V126 verified the same frozen historical-selection identity in current serving and the authoritative native-week ledger. Neither league had an admitted historical qualifier, so both served raw MARKET references. The {verified["separate_research_forecast_rows"]:,} separate research forecasts do not become approved predictions.</p><div class="two"><div><h3>Actual availability clocks · UTC</h3><div class="table-wrap" tabindex="0" role="region" aria-label="Actual V126 evidence clocks"><table><caption>Recorded availability is never replaced by a historical training cutoff.</caption><thead><tr><th scope="col">Evidence</th><th scope="col">Timestamp</th></tr></thead><tbody>{rows}</tbody></table></div><p class="small">Shared selection identity: <code>{data["selection"]["sha256"]}</code></p></div><div><h3>Where elapsed time went</h3><div class="table-wrap" tabindex="0" role="region" aria-label="Five largest V126 worker stages"><table><caption>Five largest exclusive stages, from the owner performance receipt. These are elapsed durations, not publication clocks.</caption><thead><tr><th scope="col">Stage</th><th scope="col">Seconds</th><th scope="col">Fraction of worker</th></tr></thead><tbody>{bars}</tbody></table></div></div></div><p><a href="../CASE_STUDY_SERVING_LINEAGE.md">Review the correction</a> · <a href="../../examples/review_lab/serving_lineage.py">Run the public lineage check</a> · <a href="../evidence/2026-10-27-v126-execution.json">Sanitized owner receipt</a></p><p class="small">{data["ledger"]["native_week_rows"]} native league-week rows; zero strict eligible forecast games. Historical profit is unavailable, not $0. Passing lineage checks does not establish a profitable contract edge.</p></section>'
    return cards, panel


def execution_figure(data: dict, verified: dict) -> str:
    values = ((40, str(verified["reference_rows"]), "Selected market references"), (340, f"{data['owner']['owner_tests']:,}", "Owner checks passed"), (650, "2026", "Monitoring only"), (960, "0", "Orders / promotions"))
    cells = ''.join(f'<text x="{x}" y="184" fill="#9de7dc" font-size="44">{escape(value)}</text><text x="{x}" y="216" fill="#d5e2e9" font-size="17">{escape(label)}</text>' for x, value, label in values)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="350" viewBox="0 0 1200 350" role="img" aria-labelledby="title desc"><title id="title">V126 verified selection and serving lineage</title><desc id="desc">83 history-selected market references, 2595 passed owner checks, zero qualified learned-policy forecasts, orders or promotions. The 2026 season is monitoring only.</desc><rect width="1200" height="350" rx="18" fill="#132a3d"/><g font-family="Arial,sans-serif"><text x="40" y="46" fill="#9de7dc" font-size="14" letter-spacing="2">SPORTS EDGE LAB · VERIFIED V126 EXECUTION</text><text x="40" y="96" fill="#ffffff" font-size="34">One policy identity from selection to serving.</text><path d="M40 124 H1160" stroke="#486374"/>{cells}<text x="40" y="284" fill="#ffffff" font-size="18">Historical fallback: raw MARKET · no qualified learned challenger</text><text x="40" y="316" fill="#b8cdd8" font-size="14">83 references and 7,908 research forecasts are different evidence. Executable historical profit remains unavailable.</text></g></svg>'


def render(data: dict, source_bytes: bytes, execution_bytes: bytes | None = None) -> tuple[str, str]:
    summary = validate_evidence(data)
    execution_bytes = EXECUTION_SOURCE.read_bytes() if execution_bytes is None else execution_bytes
    execution = json.loads(execution_bytes)
    verified = validate_public_receipt(execution)
    cards, panel = execution_panel(execution, verified)
    # This allowlist contains aggregates only; no individual event forecasts.
    payload = json.dumps({"rows": data["rows"]}, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    venues = "".join("<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format("NFL" if r["track"] == "nfl" else "FBS", r["cohort"], r["n"]) for r in data["venue_coverage"])
    page = TEMPLATE.replace("__ROW_COUNT__", f"{summary['rows']:,}").replace("__VENUES__", venues).replace("__SHA__", hashlib.sha256(source_bytes).hexdigest()).replace("__PAYLOAD__", payload).replace("__EXECUTION_CARDS__", cards).replace("__EXECUTION_PANEL__", panel).replace("__EXECUTION_SHA__", hashlib.sha256(execution_bytes).hexdigest())
    figure = execution_figure(execution, verified)
    return page, figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = SOURCE.read_bytes(); data = json.loads(raw)
    page, figure = render(data, raw)
    for path, value in ((OUTPUT, page), (FIGURE, figure)):
        if args.check:
            if not path.is_file() or path.read_text() != value:
                raise SystemExit("generated current review differs: " + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)
    print(json.dumps({"status": "PASS", **validate_evidence(data), "deterministic": True, "check": args.check}))


if __name__ == "__main__":
    main()
