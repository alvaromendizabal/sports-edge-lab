"""Build the public FBS evidence page from aggregate facts and invented execution."""
import argparse
import html
import json
from pathlib import Path
import tempfile
from .core import run_demo

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/fbs/index.html'


def evidence():
    data = json.loads((ROOT / 'docs/fbs/evidence.json').read_text())
    old = data['last_completed_science']
    plan = data['prepared_program']
    assert data['latest_owner_attempt']['new_real_fits'] == 0
    assert old['fbs_recent_completed_fits'] == 18 and old['fbs_recent_fit_attempts'] == 19
    assert plan['total_registered_fit_units'] == plan['core_registered_fit_units'] + plan['cross_fitted_pool_gate_units'] == 203
    assert plan['completed_owner_fit_units'] == 0 and plan['2026_used_for_selection'] is False
    assert data['current_paper_policy']['cash_usd'] == data['current_paper_policy']['budget_usd'] == 100
    assert data['current_paper_policy']['qualified_stake_usd'] == 0
    return data


def render():
    data = evidence()
    with tempfile.TemporaryDirectory() as temporary:
        demo = run_demo(temporary)
        reentry = run_demo(temporary)
    assert demo['new_synthetic_fits'] == 3 and reentry['new_synthetic_fits'] == 0
    labels = {'raw_market': 'MARKET reference', 'v130_minimax_conditional_pool': 'Retained minimax',
              'v133_market_calibration': 'Calibration control', 'v133_orthogonal_innovation': 'Orthogonal innovation'}
    panels = []
    for year in (2024, 2025, 2026):
        rows = [x for x in data['panels'] if x['season'] == year]
        best = {k: min(x[k] for x in rows) for k in ('win_brier', 'win_logloss', 'ece10')}
        def value(x, k):
            text = f'{x[k]:.6f}'
            return '<strong>' + text + '</strong>' if x[k] == best[k] else text
        table_rows = ''.join('<tr><th scope="row">' + labels[x['arm']] + '</th><td>' + str(x['games']) + '</td>'
                             + ''.join('<td>' + value(x, key) + '</td>' for key in ('win_brier', 'win_logloss', 'ece10'))
                             + f'<td>{x["correct"]}/{x["games"]}</td></tr>' for x in rows)
        kind = 'Exposed monitoring only' if year == 2026 else 'Repeatedly examined historical season'
        panels.append(f'<section class="panel" data-season="{year}"><h3>{year} · {kind}</h3><div class="tablewrap"><table><thead><tr><th>Model</th><th>Games</th><th>Brier ↓</th><th>Log loss ↓</th><th>ECE10 ↓</th><th>Correct</th></tr></thead><tbody>{table_rows}</tbody></table></div></section>')
    synthetic_rows = ''.join(f'<tr><th>{x["season"]}</th><td>{x["training_games"]}</td><td>{x["market"]["brier"]:.5f}</td><td>{x["candidate"]["brier"]:.5f}</td><td>{x["classification"]}</td></tr>' for x in demo['results'])
    payload = json.dumps({'evidence': data, 'invented': demo, 'reentry_new_synthetic_fits': reentry['new_synthetic_fits']}, sort_keys=True).replace('<', '\\u003c')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NCAA FBS · Research and evidence</title><style>
:root{color-scheme:light;--ink:#17332e;--muted:#536b66;--green:#0a6554;--line:#d4e1dc}*{box-sizing:border-box}body{margin:0;background:#f3f5ef;color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:48px 24px}header{border-top:8px solid var(--green);padding-top:28px}.eyebrow{letter-spacing:.16em;text-transform:uppercase;font-size:12px;color:var(--green);font-weight:750}h1{font-size:clamp(36px,5vw,60px);line-height:1.08;max-width:850px;margin:18px 0}h2{font-size:28px;margin:38px 0 12px}h3{font-size:19px}p{max-width:900px}a{color:#075c9a}code{background:#e8eee8;padding:2px 5px;border-radius:4px}pre{white-space:pre-wrap;padding:20px;background:#17332e;color:#e9f5e9;border-radius:12px}.lead{font-size:20px;color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:28px 0}.card,.panel{background:white;border:1px solid var(--line);padding:22px;border-radius:14px}.card .number{font-size:38px;line-height:1.2;font-weight:750}.card p{margin:8px 0 0;color:var(--muted);font-size:14px}.warn{border-left:5px solid #a16b12;background:#fff4d9;padding:16px 20px;margin:24px 0}.panel{margin-top:16px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:right;padding:11px;border-bottom:1px solid var(--line);white-space:nowrap}th:first-child,td:first-child{text-align:left}thead{color:var(--muted)}select{font:inherit;padding:10px;border:1px solid var(--line);border-radius:8px;background:white;color:var(--ink)}.small{font-size:13px;color:var(--muted)}footer{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;color:var(--muted)}@media(max-width:700px){.cards{grid-template-columns:1fr}main{padding:24px 16px}.card{padding:18px}th,td{padding:8px}}
</style></head><body><main><header><div class="eyebrow">Sports Edge Lab / NCAA FBS / Evidence review</div><h1>A failed run adds zero fits.</h1><p class="lead">The independent FBS branch preserves the last completed science, records the V135 packaging failure, and prepares a broader chronological program.</p><p><a href="../../README.md">Project</a> · <a href="README.md">FBS study notes</a> · <a href="evidence.json">Aggregate receipt</a> · <a href="../../examples/fbs_contracts/README.md">Run the invented example</a></p></header>
<div class="cards"><article class="card"><div class="eyebrow">Latest owner attempt</div><div class="number">0 new fits</div><p>V135 failed a required source-contract test before research began. 3,239 tests ran; one errored.</p></article><article class="card"><div class="eyebrow">Retained FBS sequence</div><div class="number">18 / 19</div><p>Completed fits / consumed attempts, counted from explicit FBS identities. This is not the project lifetime total.</p></article><article class="card"><div class="eyebrow">Prepared FBS program</div><div class="number">203 units</div><p>183 core registrations plus 20 chronological cross-fit pool/gate units. Owner completion remains pending.</p></article></div>
<div class="warn"><strong>MARKET remains the operational reference.</strong> No new candidate passed the inherited historical qualification. The FBS paper policy holds its full $100 as cash, with $0 qualified stake and no orders or fills.</div>
<h2>What the saved comparisons establish</h2><p>Calibration improves 2025 loss but does not repeat the gain in 2024. Orthogonal innovation regresses in both historical seasons. Its lower 2026 losses are descriptive monitoring; they cannot choose a model, calibrator, feature or threshold. Bold values identify the best displayed value in each panel, not a qualified replacement.</p><label for="season">Show season </label><select id="season"><option value="all">All three panels</option><option>2024</option><option>2025</option><option>2026</option></select>
''' + ''.join(panels) + '''
<p class="small">The 2024/2025 panels are repeatedly exposed. Matching chronology and denominators do not restore an untouched holdout. V134 innovation values are carried from the supplied prior audit. Eight saved MARKET/minimax comparisons were independently recomputed from their prediction rows with exact numerical agreement.</p>
<h2>Reproduce the engineering on invented data</h2><p>The public example runs three small estimators on invented teams and probabilities. Publication and observation clocks both control admission. FBS–FCS games remain in the declared population. The atomic journal preserves failed and interrupted attempts, validates content hashes, and reenters with zero new fits. A complete shared-source catalog still grants no purchase authority.</p>
<pre>python -m examples.fbs_contracts --output /tmp/fbs-review
python -m examples.fbs_contracts --output /tmp/fbs-review
python -m unittest discover -s examples/fbs_contracts/tests -v</pre>
<div class="tablewrap"><table><thead><tr><th>Invented season</th><th>Training games</th><th>Invented market Brier</th><th>Invented candidate Brier</th><th>Use</th></tr></thead><tbody>''' + synthetic_rows + '''</tbody></table></div>
<p class="small">These synthetic scores establish executable mechanics. They provide no evidence of sports forecasting skill, market advantage or profitability. The fixed-step example does not claim an independently certified optimum.</p>
<h2>The next owner evidence</h2><p>The new release must establish each fit's code/data identity, training origins, convergence, exact paired evaluation, timing and durable output. Optional acquisition or exchange failures must preserve completed science. The next owner return determines which of the 203 registrations actually completed.</p><footer>As of October 28, 2026 · No individual forecasts, paid raw observations, private source locations or credentials appear in this public view.</footer>
<script type="application/json" id="fbs-payload">''' + payload + '''</script><script>document.getElementById('season').addEventListener('change',function(){document.querySelectorAll('[data-season]').forEach(panel=>{panel.hidden=this.value!=='all'&&panel.dataset.season!==this.value;});});</script></main></body></html>\n'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit('FBS page is stale: python -m examples.fbs_contracts.build_review')
        print('FBS aggregate page exactly matches real evidence and invented execution')
    else:
        OUTPUT.write_text(text)
        print(OUTPUT.relative_to(ROOT))


if __name__ == '__main__': main()
