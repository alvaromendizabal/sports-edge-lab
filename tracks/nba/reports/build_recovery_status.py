"""Render a sanitized recovery notice without changing the saved NBA snapshot."""
from pathlib import Path
import argparse
import html
import json

ROOT = Path(__file__).resolve().parent
SCHEMA = 'sports-edge-lab.nba.recovery-status.v1'


def validate(value):
    assert value['schema'] == SCHEMA
    assert value['review_date'] == '2026-11-14'
    assert value['saved_public_snapshot']['evidence_as_of_utc'] == '2026-11-13T17:53:05.203284Z'
    assert value['saved_public_snapshot']['latest_original_issue_at_utc'] == '2026-11-13T17:26:12.502657Z'
    assert [row['native_estimator_fit_returns'] for row in value['attempts']] == [318, 28, 0]
    assert value['attempts'][1]['unique_model_count'] is None
    assert value['attempts'][1]['pipeline_exit_code'] == 2
    assert value['attempts'][1]['finalizer_exit_code'] == 1
    assert value['attempts'][2]['external_exit_code'] == 3
    assert value['attempts'][2]['failure_class'] == 'AGGREGATE_RETURN_TRANSPORT_ADMISSION'
    assert value['replacement']['release'] == 'B085'
    assert value['replacement']['owner_execution_observed'] is False
    assert value['publication_effects'] == {'new_fits': 0, 'new_forecasts': 0, 'new_scoring': 0,
                                          'data_refresh': False, 'automatic_promotions': 0}
    body = json.dumps(value, sort_keys=True)
    forbidden = ('s3://', '/home/', '/workspace/', 'recipe_id', 'feature_names', 'api_key',
                 '.pyz', 'PRIVATE KEY', 'sha256', 'private_recipient')
    assert not any(token in body for token in forbidden), 'Public recovery status contains a private field'
    return value


def render(value):
    validate(value)
    e = lambda text: html.escape(str(text), quote=True)
    rows = ''.join('<tr><th scope="row">'+e(row['label'])+'</th><td>'+e(row['started_at_utc'])+
        '</td><td>'+str(row['native_estimator_fit_returns'])+'</td><td>'+e(row['outcome'])+'</td></tr>'
        for row in value['attempts'])
    options = ''.join('<option value="'+e(row['id'])+'">'+e(row['label'])+'</option>' for row in value['attempts'])
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).replace('<', '\\u003c')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sports Edge Lab · NBA Recovery Status</title>
<meta name="description" content="Verified NBA execution status and the preserved all-game research dashboard, with original evidence clocks and incomplete work clearly shown.">
<style>
:root{color-scheme:light;--ink:#123343;--muted:#4b6572;--line:#c6d8e0;--blue:#075b82;--paper:#f2f7fa}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{padding:44px 24px 32px;background:#123343;color:#fff}header>div,main,footer{max-width:1160px;margin:auto}header p{max-width:800px;color:#d8e8ee}h1{font-size:clamp(28px,4vw,42px);line-height:1.16;margin:8px 0 18px}h2{font-size:24px;line-height:1.3;margin-top:0}.eyebrow{letter-spacing:.12em;text-transform:uppercase;font-size:12px;font-weight:750}
main{padding:28px 24px 48px}section{margin:0 0 24px;padding:25px;background:white;border:1px solid var(--line);border-radius:10px}p{margin:0 0 16px}p:last-child{margin-bottom:0}a{color:var(--blue)}.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}.button,button{display:inline-block;background:var(--blue);color:white;padding:10px 16px;border:1px solid transparent;border-radius:5px;text-decoration:none;font:inherit;cursor:pointer}.button.secondary{background:white;color:var(--blue);border-color:var(--line)}.status{display:inline-block;border-radius:4px;background:#ffedbf;color:#654800;font-weight:700;padding:4px 10px;margin-bottom:16px}.columns{display:grid;grid-template-columns:1.1fr 1fr;gap:24px}.small{font-size:14px;color:var(--muted)}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:13px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}thead{background:#eaf3f7}th{min-width:150px}td{min-width:110px}select{max-width:100%;padding:10px;border:1px solid #7f9daa;border-radius:4px;background:white;color:var(--ink);font:inherit;margin:8px 0 18px}#attempt-detail{padding:16px;background:#f3f8fa;border-left:3px solid var(--blue)}summary{cursor:pointer;font-weight:700;padding:8px 0}li{margin:8px 0}iframe{width:100%;height:1100px;border:1px solid var(--line);border-radius:6px;margin-top:18px}footer{padding:0 24px 36px;color:var(--muted);font-size:14px}p,li,td,th,a,code{overflow-wrap:anywhere}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #e5a821;outline-offset:3px}@media(max-width:650px){header{padding:30px 18px 24px}main{padding:18px 14px 30px}section{padding:18px}.columns{grid-template-columns:1fr;gap:0}h2{font-size:22px}.actions{gap:8px}}
</style></head><body>
<header><div><div class="eyebrow">Sports Edge Lab · NBA</div><h1>Recovery status &amp; saved research</h1>
<p>Two later owner attempts are now recovered. Their operational evidence is separate from the forecasts and scores in the preserved public dashboard.</p></div></header>
<main>
<section aria-labelledby="recovery-title"><span class="status">Recovery required · no automatic promotion</span>
<h2 id="recovery-title">The latest attempt stopped before new training</h2>
<p id="latest-attempt-summary">The later B082 attempt began November 13 at 23:33 UTC and finished November 14 at 00:08 UTC. It returned <strong>zero new native estimator fits</strong> and exit 3. A total-return transport budget prevented scientific admission despite approximately <strong>519 GiB free disk space</strong>.</p>
<p id="b084-summary">The intervening B084 attempt did run: <strong>28 native estimator method returns</strong>, all in priority forecast issuance, with peak native-fit concurrency one. Its pending V9 study stage failed on an immutable provenance-receipt conflict. Its pipeline exited 2 and finalizer exited 1. These 28 calls are not a verified count of unique models or newly promoted champions.</p>
<div class="actions"><a class="button" href="latest_research_outputs.html">Open the saved all-game dashboard</a><button id="download-recovery" type="button">Download recovery status JSON</button><a class="button secondary" href="https://github.com/alvaromendizabal/sports-edge-lab/tree/main/tracks/nba">NBA source &amp; dated history</a></div>
</section>
<div class="columns"><section aria-labelledby="snapshot-title"><h2 id="snapshot-title">The displayed forecasts keep their original clocks</h2>
<p id="snapshot-clock">Saved public evidence closes at <strong>2026-11-13 17:53:05.203284 UTC</strong>. The latest original issue in that snapshot is <strong>17:26:12.502657 UTC</strong>.</p>
<p>The preserved dashboard contains 1,274 observed canonical games and the earlier B082 result of 318 native fit returns. Original issues, exposed historical replay, missing coverage and metric-specific roles retain their existing labels. Later recovered operational summaries do not refresh those game rows or rescore them.</p>
<p class="small">Publication adds zero fits, forecasts, scores or provider refreshes. A later operational report is not a new forecast timestamp.</p></section>
<section aria-labelledby="next-title"><h2 id="next-title">What must happen next</h2>
<p id="replacement-status"><strong>B085 owner execution remains unobserved.</strong> Its continuation must remove the aggregate transport gate, preserve all scientific evidence, recover strict champion recipes and compare new time-valid work before any promotion decision.</p>
<details id="recovery-gates"><summary>Required recovery and evidence gates</summary><ul>
<li>One complete logical return, with ordered parts of at most 512 MiB when needed; test reconstruction and missing or corrupt parts.</li>
<li>Reuse prior cryptographic proofs only for proven identical files; report changed, missing and unverified bytes honestly.</li>
<li>Preserve completed fits and immutable provenance receipts while admitting independent ready science under actual resource leases.</li>
<li>Measure useful CPU work and new versus reused model results. A twelve-core reservation is not twelve-core utilization.</li>
<li>Retain source-rights, leakage, exact-recipe, actual-disk and promotion gates. Current-season model-versus-market completeness is still pending.</li>
</ul></details></section></div>
<section aria-labelledby="attempts-title"><h2 id="attempts-title">Recovered attempts, in time order</h2>
<div class="scroll"><table id="attempt-table"><thead><tr><th>Attempt</th><th>Started (UTC)</th><th>Native fit returns</th><th>Observed outcome</th></tr></thead><tbody>'''+rows+'''</tbody></table></div>
<p class="small">Counts describe native method returns in each invocation. Repeated replay passes, forecast rows and scientific model commits have different denominators.</p>
<label for="attempt-selector">Inspect an attempt</label><br><select id="attempt-selector">'''+options+'''</select><div id="attempt-detail" aria-live="polite"></div>
</section>
<section aria-labelledby="saved-title"><h2 id="saved-title">Preserved interactive research dashboard</h2><p>The original saved page below is kept intact. Its dated engineering section and scientific data describe the earlier snapshot; this recovery notice supplies later operational status.</p>
<details id="saved-dashboard"><summary>Show the all-game dashboard in this page</summary><iframe title="Preserved NBA all-game research dashboard" src="latest_research_outputs.html" loading="lazy"></iframe></details>
<p class="small"><a href="latest_research_outputs.html">Open the saved dashboard at full width</a> · <a href="latest_execution_review.json">Earlier B082 saved execution review</a> · <a href="recovery_status.json">Recovery status JSON</a></p></section>
</main><footer>Research and engineering evidence only. The current public data snapshot, source publication and website deployment are separate events. Original issues and missing evidence remain explicit.</footer>
<script type="application/json" id="nba-recovery-data">'''+data+'''</script>
<script>
'use strict';
const recovery=JSON.parse(document.getElementById('nba-recovery-data').textContent);
const selector=document.getElementById('attempt-selector'),detail=document.getElementById('attempt-detail');
function showAttempt(){const row=recovery.attempts.find(item=>item.id===selector.value);detail.replaceChildren();const strong=document.createElement('strong');strong.textContent=row.label+' — '+row.native_estimator_fit_returns+' native fit returns';const p=document.createElement('p');p.textContent=row.explanation;detail.append(strong,p);detail.dataset.attempt=row.id;}
selector.addEventListener('change',showAttempt);selector.value='b082-latest';showAttempt();
document.getElementById('download-recovery').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(recovery,null,2)+'\\n'],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='nba_recovery_status_2026-11-14.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
</script></body></html>
'''


def build(check=False):
    value = json.loads((ROOT / 'recovery_status.json').read_text())
    body = render(value)
    target = ROOT / 'recovery_status.html'
    if check:
        assert target.read_text() == body, 'Recovery status HTML is stale'
    else:
        target.write_text(body)
    return {'status': 'PASS' if check else 'BUILT', 'new_fits': 0, 'source_refresh': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true')
    print(json.dumps(build(parser.parse_args().check)))
