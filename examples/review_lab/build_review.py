"""Render the public evidence page from its sanitized aggregate JSON export."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
from pathlib import Path


def validate_evidence(data: dict) -> None:
    if data.get("schema") != "sports-edge-public-evidence-v3":
        raise ValueError("unsupported evidence schema")
    seen = set()
    for row in data["rows"]:
        identity = (row["sport"], row["campaign"])
        if identity in seen or row["games"] < 1:
            raise ValueError("duplicate or empty cohort")
        seen.add(identity)
        records = [row[key] for key in ("market", "matched_control", "learned", "direct", "challenger", "retained_log_loss_reference", "retained_brier_reference")]
        expected_frameworks = {"LightGBM", "XGBoost", "PyTorch", "TensorFlow", "Equal-weight ensemble"}
        if set(row["new_frameworks"]) != expected_frameworks:
            raise ValueError("incomplete native framework panel")
        records += list(row["new_frameworks"].values())
        score_laws = {"PyTorch D0", "PyTorch D1", "TensorFlow D0", "TensorFlow D1", "Ensemble D0", "Ensemble D1", "Learned MARKET distribution"}
        if set(row["score_law_binary"]) != score_laws or set(row["score_law_distribution"]) != score_laws:
            raise ValueError("incomplete score-law panel")
        records += list(row["score_law_binary"].values())
        distribution_cohorts = set()
        for record in row["score_law_distribution"].values():
            distribution_cohorts.add((record["games"], record["ties"], record["cohort_sha256"]))
            if record["games"] - record["ties"] != row["games"]:
                raise ValueError("binary and distribution cohorts disagree")
            for key in ("joint_nll", "mean_marginal_crps", "margin_mae", "total_mae"):
                if not math.isfinite(record[key]) or record[key] < 0:
                    raise ValueError("invalid distribution score")
            for key in ("margin_coverage_80", "margin_coverage_95", "total_coverage_80", "total_coverage_95"):
                if not math.isfinite(record[key]) or not 0 <= record[key] <= 1:
                    raise ValueError("invalid interval coverage")
        if len(distribution_cohorts) != 1:
            raise ValueError("unmatched distribution cohorts")
        for record in records:
            if not all(math.isfinite(record[k]) for k in ("brier", "logloss", "accuracy", "auc")):
                raise ValueError("non-finite aggregate score")
            if not 0 <= record["brier"] <= 1 or record["logloss"] < 0:
                raise ValueError("invalid proper score")
            if not 0 <= record["accuracy"] <= 1 or not 0 <= record["auc"] <= 1:
                raise ValueError("invalid secondary score")
    if len(seen) != 8:
        raise ValueError("expected eight declared sport/origin cohorts")


def render(data: dict, source_sha256: str) -> str:
    validate_evidence(data)
    payload = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    rows = []
    for row in data["rows"]:
        values = [row[k]["logloss"] for k in ("market", "matched_control", "learned", "direct", "challenger", "retained_log_loss_reference")]
        cells = [f'<td class="numeric {"best" if v == min(values) else ""}">{v:.6f}</td>' for v in values]
        rows.append(f'<tr><th scope="row">{html.escape(row["sport"])}</th><td>{html.escape(row["campaign"])}</td><td class="numeric">{row["games"]}</td>'+"".join(cells)+"</tr>")
    body = "\n".join(rows)
    families = "".join('<tr><th scope="row">'+html.escape(row['model'])+'</th><td>'+html.escape(row['information'])+'</td><td>'+html.escape(row['boundary'])+'</td></tr>' for row in data['feature_families'])
    factors = "".join('<tr><th scope="row">'+('NFL' if row['track']=='nfl' else 'FBS')+'</th><td>'+html.escape(row['protocol'].replace('_',' '))+'</td><td class="numeric">'+f"{row['interaction_logloss']:+.6f}"+'</td><td>'+('Unavailable: six blocks' if row['ci95'] is None else f"[{row['ci95'][0]:+.6f}, {row['ci95'][1]:+.6f}]")+'</td></tr>' for row in data['joint_evidence'] if row['protocol'] in ('development_2023_pooled','exposed_fixed_2024_2025','monitor_2026'))
    return TEMPLATE.replace("__ROWS__", body).replace("__FAMILIES__", families).replace("__FACTORS__", factors).replace("__PAYLOAD__", payload).replace("__SHA__", source_sha256)


TEMPLATE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Sports Edge Lab: inspect matched forecasting evidence, data contracts and a reproducible synthetic ML example.">
<title>Sports Edge Lab · Evidence Review</title>
<style>
:root{--ink:#12263a;--muted:#52677a;--line:#dce5eb;--paper:#f5f8fa;--teal:#087c74;--teal-light:#e5f3ef;--amber:#79540b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:4px}a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #f2b43b;outline-offset:4px}.shell{max-width:1180px;margin:auto;padding:0 28px}.top{border-bottom:1px solid var(--line);background:white}.nav{min-height:74px;display:flex;justify-content:space-between;align-items:center;gap:18px}.brand{font-weight:750;letter-spacing:-.6px;font-size:20px}.brand i{display:inline-block;width:11px;height:24px;background:var(--teal);vertical-align:middle;margin-right:10px;border-radius:2px}.navlinks{display:flex;gap:22px;font-size:14px}.navlinks a{text-decoration:none;color:var(--ink)}.hero{padding:55px 0 30px;display:grid;grid-template-columns:1.4fr 1fr;gap:48px;align-items:end}.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:11px;color:var(--teal);font-weight:750}.hero h1{font-size:clamp(32px,4vw,50px);line-height:1.12;letter-spacing:-2px;margin:13px 0 18px;max-width:700px}.hero p{max-width:630px;color:var(--muted);margin:0}.scope{border-left:3px solid var(--teal);padding:4px 0 4px 22px;font-size:14px;color:var(--muted)}.scope strong{color:var(--ink);display:block;margin-bottom:6px}.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}.chip{font-size:11px;padding:5px 9px;border:1px solid var(--line);border-radius:4px;background:white}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:22px 0 34px}.card{background:white;border:1px solid var(--line);border-radius:10px;padding:22px}.card .label{font-size:12px;color:var(--muted);margin-bottom:9px}.card .value{font-size:32px;letter-spacing:-1px;line-height:1.1;font-weight:720}.card .detail{font-size:12px;color:var(--muted);margin:10px 0 0}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:26px;margin-bottom:24px}.section-title{display:flex;justify-content:space-between;align-items:start;gap:20px}.section-title h2{margin:0;font-size:22px;letter-spacing:-.6px}.subtitle{font-size:13px;color:var(--muted);margin:7px 0 0}.filters{display:flex;gap:12px;flex-wrap:wrap;margin:23px 0 18px}label{font-size:12px;color:var(--muted);display:grid;gap:6px}select{font:inherit;font-size:14px;background:#fff;color:var(--ink);border:1px solid #bccbd6;border-radius:5px;padding:9px 34px 9px 10px;min-width:140px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px;text-align:left}caption{text-align:left;color:var(--muted);font-size:12px;padding:0 0 12px}th,td{padding:13px 12px;border-bottom:1px solid var(--line);white-space:nowrap}thead{background:#f1f5f7;color:#425b70;font-size:11px}thead th{font-weight:650}.numeric{text-align:right;font-variant-numeric:tabular-nums}.best{font-weight:750;color:#066a61;background:#edf8f3}.note{font-size:12px;color:var(--muted);margin:15px 0 0}.callout{padding:14px 16px;background:#fff6e5;border-left:3px solid #c48d23;font-size:13px;margin-top:18px;color:#644b1b}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}.two .panel{height:100%}.mini-table{font-size:12px}.mini-table th,.mini-table td{padding:10px 6px;white-space:normal}.steps{list-style:none;margin:20px 0 0;padding:0;counter-reset:steps}.steps li{counter-increment:steps;padding:0 0 19px 38px;position:relative;color:var(--muted);font-size:13px}.steps li:before{content:counter(steps);position:absolute;left:0;top:0;background:var(--teal-light);color:var(--teal);height:25px;width:25px;text-align:center;line-height:25px;border-radius:50%;font-weight:700}.steps b{color:var(--ink);display:block;font-weight:650}.boundary{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:22px 0 0}.boundary h3{font-size:14px;margin:0 0 7px}.boundary p{font-size:13px;margin:0;color:var(--muted)}footer{font-size:11px;color:var(--muted);padding:22px 0 40px;overflow-wrap:anywhere}.sr-only{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap}code{font:12px ui-monospace,monospace;background:#f1f5f7;padding:2px 4px}.links{display:flex;gap:18px;margin-top:16px;font-size:13px}.tag{background:var(--teal-light);padding:5px 9px;border-radius:4px;color:var(--teal);font-size:11px;white-space:nowrap}@media(max-width:760px){.shell{padding:0 18px}.nav{align-items:start;padding:18px 0;flex-direction:column}.navlinks{gap:16px;font-size:12px}.hero{grid-template-columns:1fr;gap:24px;padding-top:34px}.hero h1{letter-spacing:-1px}.kpis{grid-template-columns:1fr 1fr;gap:10px}.card{padding:17px}.card .value{font-size:28px}.two,.boundary{grid-template-columns:1fr}.panel{padding:18px}.section-title{flex-direction:column;gap:9px}.filters{gap:10px}select{min-width:130px}th,td{padding:11px 9px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}@media print{.navlinks,.filters{display:none}body{background:white}.shell{max-width:none}.panel{break-inside:avoid}.hero{padding-top:20px}.kpis{margin-bottom:20px}}
</style></head><body>
<div class="top"><nav class="shell nav" aria-label="Main navigation"><div class="brand"><i aria-hidden="true"></i>Sports Edge Lab</div><div class="navlinks"><a href="../../README.md">Project</a><a href="../MODEL_CARD_CURRENT.md">Model card</a><a href="../../examples/review_lab/README.md">Run the example</a></div></nav></div>
<main class="shell"><section class="hero" aria-labelledby="title"><div><div class="eyebrow">Applied ML · Scientific evaluation · Reliable systems</div><h1 id="title">Forecasts that come<br>with evidence.</h1><p>A research system for NFL and FBS forecasting. Inspect what improved, what failed, and which engineering controls keep those conclusions trustworthy.</p><div class="chips"><span class="chip">LightGBM</span><span class="chip">XGBoost</span><span class="chip">PyTorch</span><span class="chip">TensorFlow</span><span class="chip">AWS execution</span></div></div><aside class="scope"><strong>October 26, 2026 · audited experiment</strong>V120 completed 48 new score-law fits and reused 192 comparison cells. Both historical candidate gates failed. Current-season monitoring still ends October 15. Selected references are descriptive leaders, not an independent demonstration of profitability.</aside></section>
<section class="kpis" aria-label="Verified engineering snapshot"><div class="card"><div class="label">Latest owner verification</div><div class="value">1,278</div><p class="detail">Tests passed in completed V120</p></div><div class="card"><div class="label">Current research coverage</div><div class="value">69 games</div><p class="detail">4,749 rows across multiple models</p></div><div class="card"><div class="label">Integrated experiment</div><div class="value">240 cells</div><p class="detail">48 new fits + 192 reused controls</p></div><div class="card"><div class="label">Admitted wagering actions</div><div class="value">0</div><p class="detail">Stale prices kept action gates closed</p></div></section>
<section class="panel" aria-labelledby="evidence"><div class="section-title"><div><h2 id="evidence">Compare the same games.</h2><p class="subtitle">Raw MARKET, the complete C / L / U / UL experiment, and the strongest retained reference.</p></div><span class="tag">Lower proper score is better</span></div>
<div class="filters"><label for="sport">Sport<select id="sport"><option value="all">All sports</option><option>NFL</option><option>FBS</option></select></label><label for="campaign">Campaign<select id="campaign"><option value="all">All campaigns</option><option value="2024">2024–2025</option><option value="2025">2025–2026</option><option value="2026">2026–2027 so far</option></select></label><label for="metric">Proper score<select id="metric"><option value="logloss">Log loss</option><option value="brier">Brier score</option></select></label></div>
<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable matched-cohort results"><table id="scores"><caption id="caption">Eight declared sport/origin cohorts. Best displayed score is emphasized.</caption><thead><tr><th scope="col">Sport</th><th scope="col">Campaign / policy</th><th scope="col" class="numeric">Games</th><th scope="col" class="numeric">MARKET</th><th scope="col" class="numeric">C · compact</th><th scope="col" class="numeric">L · learned</th><th scope="col" class="numeric">U · direct</th><th scope="col" class="numeric">UL · combined</th><th scope="col" class="numeric">Retained best</th></tr></thead><tbody>__ROWS__</tbody></table></div><p class="note" id="count" aria-live="polite">Showing 8 cohorts.</p><p class="note">MARKET means archived bookmaker consensus after paired de-vig. It is not an executable quote. Fixed and annual origins differ; the annual NFL retained reference is an older fixed model. The best Brier reference is selected separately.</p><div class="callout">Completed execution. Negative scientific decision. The combined UL model failed both historical qualification gates and trails the selected retained leaders. A favorable current-season cell cannot override that result.</div></section>
<section class="panel" aria-labelledby="framework-title"><div class="section-title"><div><h2 id="framework-title">Four implementations. One comparison contract.</h2><p class="subtitle">Combined UL probabilities from native LightGBM, XGBoost, PyTorch and TensorFlow; selectors above control both tables.</p></div><span class="tag">Retained V119R1 comparison</span></div><div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable native framework results"><table id="framework-scores"><caption id="framework-caption">Combined UL results, equal-weight ensemble and selected retained reference.</caption><thead><tr><th>Sport</th><th>Campaign / policy</th><th class="numeric">Games</th><th class="numeric">LightGBM</th><th class="numeric">XGBoost</th><th class="numeric">PyTorch</th><th class="numeric">TensorFlow</th><th class="numeric">Ensemble UL</th><th class="numeric">Retained best</th></tr></thead><tbody></tbody></table></div><p class="note">Framework diversity is a diagnostic dimension. It is not four independent confirmations of an edge.</p></section>
<section class="panel" aria-labelledby="distribution-title"><div class="section-title"><div><h2 id="distribution-title">A richer target needs its own test.</h2><p class="subtitle">V120 turns the integrated feature bank into a joint final-score law. D0 shares its uncertainty structure; D1 conditions uncertainty and dependence on the matchup.</p></div><a href="../CASE_STUDY_SCORE_DISTRIBUTIONS.md">Read the experiment</a></div>
<div class="callout">Both historical candidate gates and both season-stability guards failed. The new models produce coherent probabilities, but no model was promoted. Mathematical validity and predictive value are different results.</div>
<h3>Winner probabilities derived from the score law</h3><p class="subtitle">Uses the sport, campaign and binary proper-score selectors above. Every value shares the same non-tied game cohort.</p>
<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable score-law winner results"><table id="score-law-binary"><caption id="score-law-binary-caption">Conditional win log loss; selected retained best and MARKET remain visible.</caption><thead><tr><th>Sport</th><th>Campaign / policy</th><th class="numeric">Games</th><th class="numeric">MARKET raw</th><th class="numeric">Retained best</th><th class="numeric">D0 ensemble</th><th class="numeric">D1 ensemble</th><th class="numeric">Learned MARKET law</th><th class="numeric">PyTorch D0</th><th class="numeric">PyTorch D1</th><th class="numeric">TensorFlow D0</th><th class="numeric">TensorFlow D1</th></tr></thead><tbody></tbody></table></div>
<h3>Joint outcomes, including ties</h3><div class="filters"><label for="distribution-metric">Distribution score<select id="distribution-metric"><option value="joint_nll">Joint negative log likelihood</option><option value="mean_marginal_crps">Mean marginal CRPS</option></select></label></div>
<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable joint distribution results"><table id="score-law-distribution"><caption id="score-law-distribution-caption">Joint score-law comparison; ties included.</caption><thead><tr><th>Sport</th><th>Campaign / policy</th><th class="numeric">Games incl. ties</th><th class="numeric">Learned MARKET law</th><th class="numeric">D0 ensemble</th><th class="numeric">D1 ensemble</th><th class="numeric">PyTorch D0</th><th class="numeric">PyTorch D1</th><th class="numeric">TensorFlow D0</th><th class="numeric">TensorFlow D1</th></tr></thead><tbody></tbody></table></div>
<p class="note">The learned MARKET law is a fitted score-distribution baseline. Raw MARKET moneyline consensus does not provide a joint score distribution, so it has no joint NLL or CRPS cell. Joint and binary losses have different targets and scales. NFL 2026 has 78 joint outcomes but 77 non-tied winner outcomes.</p>
<div class="boundary"><div><h3>Public reproduction</h3><p>The generic finite-law example tests log-space mixtures, exact support, ties, CRPS and contract payouts with invented probabilities. It exposes a numerical failure mode without exposing the private model.</p></div><div><h3>Decision boundary</h3><p>A conditional winner probability does not directly price every contract. Preserve tie mass and apply the specific settlement rule before purchase price, fees and freshness checks.</p></div></div></section>
<section class="panel" aria-labelledby="joint-title"><div class="section-title"><div><h2 id="joint-title">Did the features work together?</h2><p class="subtitle">Paired 2×2 contrast: Loss(UL) − Loss(U) − Loss(L) + Loss(C). Negative suggests complementarity on this loss scale.</p></div><a href="../CASE_STUDY_JOINT_EVIDENCE.md">Read the decision</a></div><div class="table-wrap"><table><caption>Equal-weight ensemble · exposed descriptive estimates · paired weekly-block 95% intervals</caption><thead><tr><th>Sport</th><th>Panel</th><th class="numeric">Interaction log loss</th><th>95% interval</th></tr></thead><tbody>__FACTORS__</tbody></table></div><p class="note">Every displayed estimable interval crosses zero. A negative interaction alone would still not prove MARKET outperformance, causality or profitability. The public synthetic evaluator demonstrates this distinction with complementary, redundant and harmful fixtures.</p></section>
<div class="two"><section class="panel" aria-labelledby="coverage"><h2 id="coverage">Coverage is a contract.</h2><p class="subtitle">Source inventory and unresolved exceptions stay separate.</p><table class="mini-table"><caption>Current source audit</caption><thead><tr><th>Source layer</th><th>Verified coverage</th><th>Open issue</th></tr></thead><tbody><tr><th scope="row">NFL play by play</th><td>106 / 106 finals</td><td>12 enrichment-game gaps</td></tr><tr><th scope="row">FBS bulk drives</th><td>566 / 566 finals</td><td>Detailed-source checks remain separate</td></tr><tr><th scope="row">FBS detailed summaries</th><td>566 / 566 games</td><td>17 conflicts corroborated; 2 native drives quarantined</td></tr><tr><th scope="row">Current price admission</th><td>0 fresh named quotes</td><td>Forecasting success does not imply actionability</td></tr></tbody></table><p class="note">Publication time, first observation, revision and event time are different. A successful download does not certify a valid historical feature.</p></section>
<section class="panel" aria-labelledby="review"><h2 id="review">Follow the engineering.</h2><ol class="steps"><li><b>Validate before fitting</b>Reject identity conflicts, future observations and unmatched cohorts.</li><li><b>Compare complete systems</b>Preserve controls, interactions and chronological evaluation.</li><li><b>Record decisions honestly</b>Separate execution success, negative science and deployment readiness.</li><li><b>Recover without changing history</b>Verify artifacts and reuse accepted work without hidden retraining.</li></ol><div class="links"><a href="../../examples/review_lab/README.md">Reproduce the public example</a><a href="../SYSTEM_DESIGN.md">Explore the design</a></div></section></div>
<section class="panel" style="margin-top:24px" aria-labelledby="family-title"><h2 id="family-title">What information does each model use?</h2><p class="subtitle">Feature families explain the experiment; private formulas and fitted weights remain outside the public artifact.</p><div class="table-wrap"><table class="mini-table"><thead><tr><th>System</th><th>Information families</th><th>Interpretation</th></tr></thead><tbody>__FAMILIES__</tbody></table></div><p class="note">Kalshi is a separate execution venue with contract-specific prices, fees and settlement rules. It is not the raw MARKET benchmark displayed above.</p></section>
<section class="panel" style="margin-top:24px" aria-labelledby="boundary"><h2 id="boundary">An explicit reproducibility boundary.</h2><div class="boundary"><div><h3>Public and executable</h3><p>Chronological synthetic training, proper scoring, identity and time guards, integrity-checked artifacts, tests, notebooks and these sanitized aggregate results.</p></div><div><h3>Private research assets</h3><p>Licensed observations, individual forecasts, fitted production weights, exact active feature transforms, tuning and decision configuration. The public example does not reproduce the private scores.</p></div></div></section>
</main><footer class="shell">Built from <a href="../evidence/2026-10-26-v120.json">the public aggregate evidence export</a>. SHA-256: <code>__SHA__</code><br>Sports Edge Lab · Alvaro Mendizabal · No credentials, external requests or individual betting recommendations in this page.</footer>
<script type="application/json" id="evidence-data">__PAYLOAD__</script><script>
'use strict';
const evidence = JSON.parse(document.getElementById('evidence-data').textContent);
function tableRows(selector, visible, metric, recordsFor){const tbody=document.querySelector(selector);tbody.replaceChildren();for(const row of visible){const records=recordsFor(row);const scores=records.map(r=>r[metric]);const tr=document.createElement('tr');for(const [i,value] of [row.sport,row.campaign,row.games].entries()){const cell=document.createElement(i===0?'th':'td');if(i===0)cell.scope='row';if(i===2)cell.className='numeric';cell.textContent=value;tr.append(cell)}scores.forEach((score,i)=>{const td=document.createElement('td');td.className='numeric'+(score===Math.min(...scores)?' best':'');td.textContent=score.toFixed(6);td.title=records[i].label;tr.append(td)});tbody.append(tr)}}
function update(){const sport=document.getElementById('sport').value;const campaign=document.getElementById('campaign').value;const metric=document.getElementById('metric').value;const visible=evidence.rows.filter(r=>(sport==='all'||r.sport===sport)&&(campaign==='all'||r.campaign.startsWith(campaign)));const ref=metric==='brier'?'retained_brier_reference':'retained_log_loss_reference';tableRows('#scores tbody',visible,metric,row=>[row.market,row.matched_control,row.learned,row.direct,row.challenger,row[ref]]);tableRows('#framework-scores tbody',visible,metric,row=>[...['LightGBM','XGBoost','PyTorch','TensorFlow','Equal-weight ensemble'].map(name=>row.new_frameworks[name]),row[ref]]);const binaryOrder=['Ensemble D0','Ensemble D1','Learned MARKET distribution','PyTorch D0','PyTorch D1','TensorFlow D0','TensorFlow D1'];tableRows('#score-law-binary tbody',visible,metric,row=>[row.market,row[ref],...binaryOrder.map(name=>row.score_law_binary[name])]);const distributionMetric=document.getElementById('distribution-metric').value;const distributionOrder=['Learned MARKET distribution','Ensemble D0','Ensemble D1','PyTorch D0','PyTorch D1','TensorFlow D0','TensorFlow D1'];const distributionRows=visible.map(row=>({...row,games:row.score_law_distribution['Ensemble D0'].games}));tableRows('#score-law-distribution tbody',distributionRows,distributionMetric,row=>distributionOrder.map(name=>row.score_law_distribution[name]));document.getElementById('score-law-binary-caption').textContent=(metric==='brier'?'Brier score':'Log loss')+' · conditional non-tie winner probabilities on the same games.';document.getElementById('score-law-distribution-caption').textContent=(distributionMetric==='joint_nll'?'Joint negative log likelihood':'Mean marginal CRPS')+' · tied games included · lower is better.';document.getElementById('count').textContent='Showing '+visible.length+' cohorts.';document.getElementById('caption').textContent=(metric==='brier'?'Brier score':'Log loss')+' on matched games. Best displayed score is emphasized.';document.getElementById('framework-caption').textContent=(metric==='brier'?'Brier score':'Log loss')+' · combined UL implementations on the identical cohort.'}
for(const id of ['sport','campaign','metric','distribution-metric'])document.getElementById(id).addEventListener('change',update);
update();
</script></body></html>'''


def render_overview(data: dict) -> str:
    """Zero-based, target-specific static companion to the live comparison table."""
    validate_evidence(data)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="610" viewBox="0 0 1100 610" role="img" aria-labelledby="title desc">',
        '<title id="title">V120: coherent distributions, unchanged winner leaders</title>',
        '<desc id="desc">Four matched conditional-win log losses for each sport: raw MARKET, retained leader, new D0 and D1 joint-score ensembles. Lower is better. All bars start at zero.</desc>',
        '<rect width="1100" height="610" rx="14" fill="#f4f8fa"/>',
        '<g font-family="Arial, sans-serif" fill="#12263a">',
        '<text x="42" y="42" font-size="12" letter-spacing="2" fill="#087c74">V120 · COMPLETED EXPERIMENT · 48 NEW FITS</text>',
        '<text x="42" y="81" font-size="29" font-weight="700">Richer predictions. The same standard of evidence.</text>',
        '<text x="42" y="110" font-size="15" fill="#52677a">2026–27 conditional-win log loss · lower is better · included games through October 15</text>']
    for index,row in enumerate(r for r in data['rows'] if r['campaign'].startswith('2026')):
        x=42+index*530
        parts.extend([f'<text x="{x}" y="162" font-size="22" font-weight="700">{row["sport"]}</text>',f'<text x="{x+70}" y="162" font-size="14" fill="#52677a">{row["games"]} matched non-tied games</text>'])
        values=[('MARKET raw',row['market']['logloss'],'#899cac'),('Retained leader',row['retained_log_loss_reference']['logloss'],'#087c74'),('D0 · joint-score ensemble',row['score_law_binary']['Ensemble D0']['logloss'],'#577fa9'),('D1 · conditional uncertainty',row['score_law_binary']['Ensemble D1']['logloss'],'#8a76a9')]
        minimum=min(v[1] for v in values)
        for pos,(label,score,color) in enumerate(values):
            y=194+pos*64;width=380*score/.7;weight='700' if score==minimum else '400'
            parts.extend([f'<text x="{x}" y="{y}" font-size="12" fill="#52677a">{label}</text>',f'<rect x="{x}" y="{y+9}" width="{width:.3f}" height="22" rx="3" fill="{color}"/>',f'<text x="{x+width+9:.3f}" y="{y+26}" font-size="14" font-weight="{weight}">{score:.6f}</text>'])
        parts.extend([f'<line x1="{x}" y1="431" x2="{x+380}" y2="431" stroke="#cbd8e2"/>',f'<text x="{x}" y="450" font-size="11" fill="#52677a">0</text>',f'<text x="{x+359}" y="450" font-size="11" fill="#52677a">0.70</text>'])
    parts.extend(['<rect x="42" y="482" width="1016" height="91" rx="7" fill="#fff4df"/>',
        '<text x="60" y="508" font-size="14" fill="#644b1b">Decision: retain the prior leaders. Both historical candidate gates and season-stability guards failed.</text>',
        '<text x="60" y="531" font-size="13" fill="#644b1b">Joint-distribution metrics include ties and appear separately in the evidence explorer.</text>',
        '<text x="60" y="552" font-size="13" fill="#644b1b">Exposed monitoring; no independent prospective profit claim. MARKET raw is archived bookmaker consensus.</text>',
        '</g></svg>'])
    return '\n'.join(parts)+'\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed page differs from the aggregate export")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / "docs/evidence/2026-10-26-v120.json"
    output = root / "docs/review/index.html"
    data = json.loads(source.read_text())
    expected = render(data, hashlib.sha256(source.read_bytes()).hexdigest())
    graphic = root / "docs/assets/evidence-overview.svg"
    expected_graphic = render_overview(data)
    if args.check:
        if output.read_text() != expected:
            raise SystemExit("Evidence page differs; rebuild it from its source export")
        if graphic.read_text() != expected_graphic:
            raise SystemExit("Evidence graphic differs; rebuild it from its source export")
        print("PASS: evidence page and graphic exactly match source export")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected)
        graphic.parent.mkdir(parents=True, exist_ok=True)
        graphic.write_text(expected_graphic)
        print(output)


if __name__ == "__main__":
    main()
