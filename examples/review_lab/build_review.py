"""Render the public evidence page from its sanitized aggregate JSON export."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
from pathlib import Path


def validate_evidence(data: dict) -> None:
    if data.get("schema") != "sports-edge-public-evidence-v1":
        raise ValueError("unsupported evidence schema")
    seen = set()
    for row in data["rows"]:
        identity = (row["sport"], row["campaign"])
        if identity in seen or row["games"] < 1:
            raise ValueError("duplicate or empty cohort")
        seen.add(identity)
        for key in ("market", "matched_control", "challenger", "retained_log_loss_reference", "retained_brier_reference"):
            record = row[key]
            if not all(math.isfinite(record[k]) for k in ("brier", "logloss", "accuracy", "auc")):
                raise ValueError("non-finite aggregate score")
            if not 0 <= record["brier"] <= 1 or record["logloss"] < 0:
                raise ValueError("invalid proper score")
    if len(seen) != 8:
        raise ValueError("expected eight declared sport/origin cohorts")


def render(data: dict, source_sha256: str) -> str:
    validate_evidence(data)
    payload = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    rows = []
    for row in data["rows"]:
        values = [row[k]["logloss"] for k in ("market", "matched_control", "challenger", "retained_log_loss_reference")]
        cells = [f'<td class="numeric {"best" if v == min(values) else ""}">{v:.6f}</td>' for v in values]
        rows.append(f'<tr><th scope="row">{html.escape(row["sport"])}</th><td>{html.escape(row["campaign"])}</td><td class="numeric">{row["games"]}</td>'+"".join(cells)+"</tr>")
    body = "\n".join(rows)
    return TEMPLATE.replace("__ROWS__", body).replace("__PAYLOAD__", payload).replace("__SHA__", source_sha256)


TEMPLATE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Sports Edge Lab: inspect matched forecasting evidence, data contracts and a reproducible synthetic ML example.">
<title>Sports Edge Lab · Evidence Review</title>
<style>
:root{--ink:#12263a;--muted:#52677a;--line:#dce5eb;--paper:#f5f8fa;--teal:#087c74;--teal-light:#e5f3ef;--amber:#79540b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:4px}a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #f2b43b;outline-offset:4px}.shell{max-width:1180px;margin:auto;padding:0 28px}.top{border-bottom:1px solid var(--line);background:white}.nav{min-height:74px;display:flex;justify-content:space-between;align-items:center;gap:18px}.brand{font-weight:750;letter-spacing:-.6px;font-size:20px}.brand i{display:inline-block;width:11px;height:24px;background:var(--teal);vertical-align:middle;margin-right:10px;border-radius:2px}.navlinks{display:flex;gap:22px;font-size:14px}.navlinks a{text-decoration:none;color:var(--ink)}.hero{padding:55px 0 30px;display:grid;grid-template-columns:1.4fr 1fr;gap:48px;align-items:end}.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:11px;color:var(--teal);font-weight:750}.hero h1{font-size:clamp(32px,4vw,50px);line-height:1.12;letter-spacing:-2px;margin:13px 0 18px;max-width:700px}.hero p{max-width:630px;color:var(--muted);margin:0}.scope{border-left:3px solid var(--teal);padding:4px 0 4px 22px;font-size:14px;color:var(--muted)}.scope strong{color:var(--ink);display:block;margin-bottom:6px}.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}.chip{font-size:11px;padding:5px 9px;border:1px solid var(--line);border-radius:4px;background:white}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:22px 0 34px}.card{background:white;border:1px solid var(--line);border-radius:10px;padding:22px}.card .label{font-size:12px;color:var(--muted);margin-bottom:9px}.card .value{font-size:32px;letter-spacing:-1px;line-height:1.1;font-weight:720}.card .detail{font-size:12px;color:var(--muted);margin:10px 0 0}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:26px;margin-bottom:24px}.section-title{display:flex;justify-content:space-between;align-items:start;gap:20px}.section-title h2{margin:0;font-size:22px;letter-spacing:-.6px}.subtitle{font-size:13px;color:var(--muted);margin:7px 0 0}.filters{display:flex;gap:12px;flex-wrap:wrap;margin:23px 0 18px}label{font-size:12px;color:var(--muted);display:grid;gap:6px}select{font:inherit;font-size:14px;background:#fff;color:var(--ink);border:1px solid #bccbd6;border-radius:5px;padding:9px 34px 9px 10px;min-width:140px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px;text-align:left}caption{text-align:left;color:var(--muted);font-size:12px;padding:0 0 12px}th,td{padding:13px 12px;border-bottom:1px solid var(--line);white-space:nowrap}thead{background:#f1f5f7;color:#425b70;font-size:11px}thead th{font-weight:650}.numeric{text-align:right;font-variant-numeric:tabular-nums}.best{font-weight:750;color:#066a61;background:#edf8f3}.note{font-size:12px;color:var(--muted);margin:15px 0 0}.callout{padding:14px 16px;background:#fff6e5;border-left:3px solid #c48d23;font-size:13px;margin-top:18px;color:#644b1b}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}.two .panel{height:100%}.mini-table{font-size:12px}.mini-table th,.mini-table td{padding:10px 6px;white-space:normal}.steps{list-style:none;margin:20px 0 0;padding:0;counter-reset:steps}.steps li{counter-increment:steps;padding:0 0 19px 38px;position:relative;color:var(--muted);font-size:13px}.steps li:before{content:counter(steps);position:absolute;left:0;top:0;background:var(--teal-light);color:var(--teal);height:25px;width:25px;text-align:center;line-height:25px;border-radius:50%;font-weight:700}.steps b{color:var(--ink);display:block;font-weight:650}.boundary{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:22px 0 0}.boundary h3{font-size:14px;margin:0 0 7px}.boundary p{font-size:13px;margin:0;color:var(--muted)}footer{font-size:11px;color:var(--muted);padding:22px 0 40px;overflow-wrap:anywhere}.sr-only{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap}code{font:12px ui-monospace,monospace;background:#f1f5f7;padding:2px 4px}.links{display:flex;gap:18px;margin-top:16px;font-size:13px}.tag{background:var(--teal-light);padding:5px 9px;border-radius:4px;color:var(--teal);font-size:11px;white-space:nowrap}@media(max-width:760px){.shell{padding:0 18px}.nav{align-items:start;padding:18px 0;flex-direction:column}.navlinks{gap:16px;font-size:12px}.hero{grid-template-columns:1fr;gap:24px;padding-top:34px}.hero h1{letter-spacing:-1px}.kpis{grid-template-columns:1fr 1fr;gap:10px}.card{padding:17px}.card .value{font-size:28px}.two,.boundary{grid-template-columns:1fr}.panel{padding:18px}.section-title{flex-direction:column;gap:9px}.filters{gap:10px}select{min-width:130px}th,td{padding:11px 9px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}@media print{.navlinks,.filters{display:none}body{background:white}.shell{max-width:none}.panel{break-inside:avoid}.hero{padding-top:20px}.kpis{margin-bottom:20px}}
</style></head><body>
<div class="top"><nav class="shell nav" aria-label="Main navigation"><div class="brand"><i aria-hidden="true"></i>Sports Edge Lab</div><div class="navlinks"><a href="../../README.md">Project</a><a href="../MODEL_CARD_CURRENT.md">Model card</a><a href="../../examples/review_lab/README.md">Run the example</a></div></nav></div>
<main class="shell"><section class="hero" aria-labelledby="title"><div><div class="eyebrow">Applied ML · Scientific evaluation · Reliable systems</div><h1 id="title">Forecasts that come<br>with evidence.</h1><p>A research system for NFL and FBS forecasting. Inspect what improved, what failed, and which engineering controls keep those conclusions trustworthy.</p><div class="chips"><span class="chip">LightGBM</span><span class="chip">XGBoost</span><span class="chip">PyTorch</span><span class="chip">TensorFlow</span><span class="chip">AWS execution</span></div></div><aside class="scope"><strong>October 25, 2026 · research snapshot</strong>Results below are matched, exposed comparisons. Current-season monitoring ends October 15. Selected references are descriptive leaders, not an independent demonstration of profitability.</aside></section>
<section class="kpis" aria-label="Verified engineering snapshot"><div class="card"><div class="label">Latest owner verification</div><div class="value">927</div><p class="detail">Tests passed in completed V118</p></div><div class="card"><div class="label">Current research coverage</div><div class="value">39 games</div><p class="detail">2,058 rows across multiple models</p></div><div class="card"><div class="label">New fits in serving run</div><div class="value">0</div><p class="detail">Saved models reused with provenance</p></div><div class="card"><div class="label">Admitted wagering actions</div><div class="value">0</div><p class="detail">Stale prices kept action gates closed</p></div></section>
<section class="panel" aria-labelledby="evidence"><div class="section-title"><div><h2 id="evidence">Compare the same games.</h2><p class="subtitle">Raw MARKET, matched control, new joint challenger and the strongest retained reference.</p></div><span class="tag">Lower proper score is better</span></div>
<div class="filters"><label for="sport">Sport<select id="sport"><option value="all">All sports</option><option>NFL</option><option>FBS</option></select></label><label for="campaign">Campaign<select id="campaign"><option value="all">All campaigns</option><option value="2024">2024–2025</option><option value="2025">2025–2026</option><option value="2026">2026–2027 so far</option></select></label><label for="metric">Proper score<select id="metric"><option value="logloss">Log loss</option><option value="brier">Brier score</option></select></label></div>
<div class="table-wrap" tabindex="0" role="region" aria-label="Scrollable matched-cohort results"><table id="scores"><caption id="caption">Eight declared sport/origin cohorts. Best displayed score is emphasized.</caption><thead><tr><th scope="col">Sport</th><th scope="col">Campaign / policy</th><th scope="col" class="numeric">Games</th><th scope="col" class="numeric">MARKET</th><th scope="col" class="numeric">Control</th><th scope="col" class="numeric">Challenger</th><th scope="col" class="numeric">Retained best</th></tr></thead><tbody>__ROWS__</tbody></table></div><p class="note" id="count" aria-live="polite">Showing 8 cohorts.</p><p class="note">MARKET means archived bookmaker consensus after paired de-vig. It is not an executable quote. Fixed and annual origins differ; the annual NFL retained reference is an older fixed model. The best Brier reference is selected separately.</p><div class="callout">The new challenger failed both historical qualification gates. Positive current NFL effects remain visible; they do not override that decision.</div></section>
<div class="two"><section class="panel" aria-labelledby="coverage"><h2 id="coverage">Coverage is a contract.</h2><p class="subtitle">Source inventory and unresolved exceptions stay separate.</p><table class="mini-table"><caption>Current source audit</caption><thead><tr><th>Source layer</th><th>Verified coverage</th><th>Open issue</th></tr></thead><tbody><tr><th scope="row">NFL play by play</th><td>105 / 105 finals</td><td>11 enrichment-game gaps</td></tr><tr><th scope="row">FBS bulk drives</th><td>566 / 566 finals</td><td>Detailed-source checks remain separate</td></tr><tr><th scope="row">FBS detailed summaries</th><td>549 / 566 games</td><td>17 kickoff conflicts quarantined</td></tr><tr><th scope="row">Current price admission</th><td>0 fresh named quotes</td><td>Forecasting success does not imply actionability</td></tr></tbody></table><p class="note">Publication time, first observation, revision and event time are different. A successful download does not certify a valid historical feature.</p></section>
<section class="panel" aria-labelledby="review"><h2 id="review">Follow the engineering.</h2><ol class="steps"><li><b>Validate before fitting</b>Reject identity conflicts, future observations and unmatched cohorts.</li><li><b>Compare complete systems</b>Preserve controls, interactions and chronological evaluation.</li><li><b>Record decisions honestly</b>Separate execution success, negative science and deployment readiness.</li><li><b>Recover without changing history</b>Verify artifacts and reuse accepted work without hidden retraining.</li></ol><div class="links"><a href="../../examples/review_lab/README.md">Reproduce the public example</a><a href="../SYSTEM_DESIGN.md">Explore the design</a></div></section></div>
<section class="panel" style="margin-top:24px" aria-labelledby="boundary"><h2 id="boundary">An explicit reproducibility boundary.</h2><div class="boundary"><div><h3>Public and executable</h3><p>Chronological synthetic training, proper scoring, identity and time guards, integrity-checked artifacts, tests, notebooks and these sanitized aggregate results.</p></div><div><h3>Private research assets</h3><p>Licensed observations, individual forecasts, fitted production weights, exact active feature transforms, tuning and decision configuration. The public example does not reproduce the private scores.</p></div></div></section>
</main><footer class="shell">Built from <a href="../evidence/2026-10-25.json">the public aggregate evidence export</a>. SHA-256: <code>__SHA__</code><br>Sports Edge Lab · Alvaro Mendizabal · No credentials, external requests or individual betting recommendations in this page.</footer>
<script type="application/json" id="evidence-data">__PAYLOAD__</script><script>
'use strict';
const evidence = JSON.parse(document.getElementById('evidence-data').textContent);
function update(){const sport=document.getElementById('sport').value;const campaign=document.getElementById('campaign').value;const metric=document.getElementById('metric').value;const visible=evidence.rows.filter(r=>(sport==='all'||r.sport===sport)&&(campaign==='all'||r.campaign.startsWith(campaign)));const tbody=document.querySelector('#scores tbody');tbody.replaceChildren();for(const row of visible){const tr=document.createElement('tr');const ref=metric==='brier'?'retained_brier_reference':'retained_log_loss_reference';const records=[row.market,row.matched_control,row.challenger,row[ref]];const scores=records.map(r=>r[metric]);const first=document.createElement('th');first.scope='row';first.textContent=row.sport;tr.append(first);const period=document.createElement('td');period.textContent=row.campaign;tr.append(period);const count=document.createElement('td');count.className='numeric';count.textContent=row.games;tr.append(count);scores.forEach((score,i)=>{const td=document.createElement('td');td.className='numeric'+(score===Math.min(...scores)?' best':'');td.textContent=score.toFixed(6);td.title=records[i].label;tr.append(td)});tbody.append(tr)}document.getElementById('count').textContent='Showing '+visible.length+' cohorts.';document.getElementById('caption').textContent=(metric==='brier'?'Brier score':'Log loss')+' on matched games. Best displayed score is emphasized.'}
for(const id of ['sport','campaign','metric'])document.getElementById(id).addEventListener('change',update);
update();
</script></body></html>'''


def render_overview(data: dict) -> str:
    """A precise static companion graphic; all bars start at zero."""
    validate_evidence(data)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="470" viewBox="0 0 1100 470" role="img" aria-labelledby="title desc">',
             '<title id="title">Current monitoring: matched log loss</title>',
             '<desc id="desc">MARKET compared with the strongest retained reference on exposed 2026 monitoring cohorts. Lower is better; this does not establish prospective profitability.</desc>',
             '<rect width="1100" height="470" rx="14" fill="#f4f8fa"/>',
             '<g font-family="Arial, sans-serif" fill="#12263a">',
             '<text x="42" y="44" font-size="12" letter-spacing="2" fill="#087c74">2026–2027 · EXPOSED MONITORING</text>',
             '<text x="42" y="84" font-size="29" font-weight="700">Compare the same games. Keep the caveats.</text>',
             '<text x="42" y="113" font-size="15" fill="#52677a">Log loss · lower is better · games through October 15, 2026</text>']
    for index, row in enumerate(r for r in data['rows'] if r['campaign'].startswith('2026')):
        x = 42 + index * 530
        parts += [f'<text x="{x}" y="170" font-size="22" font-weight="700">{row["sport"]}</text>',
                  f'<text x="{x+70}" y="170" font-size="14" fill="#52677a">{row["games"]} matched games</text>']
        for pos, (key, label, color) in enumerate([('market', 'MARKET', '#8da1b3'), ('retained_log_loss_reference', 'Retained reference', '#087c74')]):
            y = 205 + pos * 67
            score = row[key]['logloss']
            width = 400 * score / .7
            parts += [f'<text x="{x}" y="{y}" font-size="12" fill="#52677a">{label}</text>',
                      f'<rect x="{x}" y="{y+9}" width="{width:.3f}" height="24" rx="3" fill="{color}"/>',
                      f'<text x="{x+width+9:.3f}" y="{y+27}" font-size="14" fill="#12263a">{score:.6f}</text>']
        parts += [f'<line x1="{x}" y1="321" x2="{x+400}" y2="321" stroke="#d1dce4"/>',
                  f'<text x="{x}" y="340" font-size="11" fill="#52677a">0</text>',
                  f'<text x="{x+379}" y="340" font-size="11" fill="#52677a">0.70</text>']
    parts += ['<rect x="42" y="370" width="1016" height="67" rx="7" fill="#fff4df"/>',
              '<text x="60" y="396" font-size="14" fill="#644b1b">Retained references were selected on exposed outcomes. Both new-challenger historical gates failed.</text>',
              '<text x="60" y="418" font-size="13" fill="#644b1b">MARKET is archived bookmaker consensus, not an executable quote. No prospective profit is established.</text>',
              '</g></svg>']
    return '\n'.join(parts) + '\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed page differs from the aggregate export")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = root / "docs/evidence/2026-10-25.json"
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
