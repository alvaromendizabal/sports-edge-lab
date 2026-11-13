"""Render saved authorized NBA aggregates without private inputs or new scoring."""
from pathlib import Path
from b083_html import expand_html
import hashlib
import html
import json
import re
import sys

ROOT=Path(__file__).parent
SCHEMA='sports-edge-lab.nba.owner-model-review.v1'
BEGIN='<!-- NBA OWNER MODEL REVIEW BEGIN -->'
END='<!-- NBA OWNER MODEL REVIEW END -->'

def _fail(reason):
    raise ValueError('NBA_MODEL_REVIEW_'+reason)

def validate_model_review(value):
    if value.get('schema')!=SCHEMA or value.get('original_issues_modified') is not False:_fail('SCHEMA_OR_IMMUTABILITY')
    for field in ('publication_new_fits','publication_new_inference','publication_new_metric_scoring','production_promotions'):
        if value.get(field)!=0:_fail('DISPLAY_ONLY_BOUNDARY')
    body=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode().decode()
    for token in ('recipe_id','feature_names','s3://','/home/','/workspace/','api_key','apiKey','PRIVATE KEY'):
        if token in body:_fail('PRIVATE_FIELD_OR_PATH')
    for row in value['metric_rows']:
        if row.get('promotion_allowed') is not False:_fail('AUTOMATIC_PROMOTION')
        if row['evidence_track']!='ORIGINAL_ISSUED_ROLLING' and row.get('original_issue_claim') is not False:
            _fail('RETROSPECTIVE_ORIGINAL_ISSUE_CLAIM')
    return True


def render_section(review):
    validate_model_review(review)
    embedded=json.dumps(review,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return BEGIN+'''\n<section id="nba-owner-review" aria-labelledby="nba-owner-review-title">
<style>#nba-owner-review{margin:26px 0;padding:20px;border:1px solid #cddbd8;border-radius:8px;background:#f3f8f5}#nba-owner-review .scroll{max-height:500px;overflow:auto}#nba-owner-review label{min-width:135px}#nba-owner-review td{overflow-wrap:anywhere}#nba-owner-review h3{margin:22px 0 10px}</style>
<h2 id="nba-owner-review-title">Saved model performance by season and evidence policy</h2>
<p>Latest original issue: <strong>'''+html.escape(review['latest_original_issue_at_utc'] or 'Unavailable')+'''</strong>. Evidence snapshot: '''+html.escape(review['evidence_as_of_utc'] or 'Unavailable')+'''. This panel copies saved metrics; publication creates no fit, inference, score or forecast.</p>
<p>Season-start frozen refreshes have their own training cutoff and actual new/reused-fit counts. The logical cutoff and actual materialization clock are separate: a new retrospective state was not necessarily available at the earlier cutoff. Fixed-state replay and preserved arrays remain retrospective. No production promotion or newly issued forecast is inferred from these rows.</p>
<p><a href="latest_model_review.json">Download complete saved aggregate review</a></p>
<details><summary>Source-stage status, new fits and reuse</summary><div id="nba-owner-source-status"></div></details>
<div class="filters"><label>Season<select id="nba-owner-season"><option value="all">All seasons</option><option>2024-25</option><option>2025-26</option><option>2026-27</option></select></label><label>Evidence policy<select id="nba-owner-track"><option value="all">All separate policies</option></select></label><label>Target<select id="nba-owner-target"><option value="all">All targets</option><option>winner</option><option>margin</option><option>total</option></select></label></div>
<p id="nba-owner-count" class="small"></p><div class="scroll"><table id="nba-owner-metrics"><thead><tr><th>Season / policy</th><th>Role / family</th><th>Target / phase / horizon</th><th>Scored / denominator</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>Missingness / state origin</th></tr></thead><tbody></tbody></table></div>
<h3>Descriptive historical numerical peaks</h3><p>Saved 1,230-game regular-season extrema, by season and horizon. These exposed per-season peaks are separate from selected two-season roles. Equal counts do not establish exact matched game sets.</p><div class="scroll"><table id="nba-owner-peaks"><thead><tr><th>Season / horizon</th><th>Target / metric</th><th>Coarse families</th><th>Saved value</th><th>Games / ties</th></tr></thead><tbody></tbody></table></div>
<h3>Matched selected/former-model comparisons</h3><p>Each row preserves its saved evidence policy and exact matched support. Values are left / right; differences and week counts do not create independent confirmation.</p><div class="scroll"><table id="nba-owner-pairs"><thead><tr><th>Policy / target / horizon</th><th>Left / right family</th><th>Matched / denominator / weeks</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody></tbody></table></div>
<h3>Named-venue coverage and saved comparisons</h3><p>Maximum matched games in one saved view is not an additive full-season count. Raw bid/ask midpoints are not automatically fair probabilities; winner references do not identify expected margins or totals.</p><div class="scroll"><table id="nba-owner-coverage"><thead><tr><th>Season</th><th>Venue</th><th>Maximum matched games</th><th>Status</th></tr></thead><tbody></tbody></table></div>
<div class="scroll"><table id="nba-owner-venues"><thead><tr><th>Season / policy</th><th>Venue / model family / horizon</th><th>Matched games</th><th>Accuracy · model / reference</th><th>Log loss · model / reference</th><th>Brier · model / reference</th><th>Fair-probability games / weeks</th></tr></thead><tbody></tbody></table></div>
<h3>Nomination and production review gates</h3><p>Regular-season historical nomination requires at least 250 games in each frozen season, 500 total and 30 week clusters. Postseason nomination requires 40 in each, 80 total and 8 week clusters. Exact baseline games, seasonal stability, calibration and an available exact refit adapter are required. A positive adjusted paired interval is reported but is not a historical nomination requirement.</p>
<p>Registered production review requires 500 matched games and 30 week clusters, multiplicity-adjusted comparison, calibration and stability guardrails, new post-registration originally issued evidence and independent review. Automatic promotion remains disabled. There is no universal absolute accuracy, loss or point-error threshold.</p>
<p class="small">Missing source sections and unsupported scores remain unavailable. Repeated model roles, horizons, revisions and paired views are not independent games. Historical and retrospective performance do not replace registered forward evidence and independent production review.</p>
<script id="nba-owner-review-data" type="application/json">'''+embedded+'''</script>
<script>(()=>{'use strict';const R=JSON.parse(document.getElementById('nba-owner-review-data').textContent),q=id=>document.getElementById(id),e=x=>String(x??'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),w=x=>String(x??'Unavailable').replaceAll('_',' '),s=(x,m)=>typeof x!=='number'?'Unavailable':m==='accuracy'?(100*x).toFixed(2)+'%':x.toFixed(6),keys=['accuracy','log_loss','brier','mae','rmse'],cells=a=>a.map(v=>'<td>'+e(v)+'</td>').join('');
for(const track of [...new Set(R.metric_rows.map(r=>r.evidence_track))]){const o=document.createElement('option');o.value=track;o.textContent=w(track);q('nba-owner-track').appendChild(o);}
function draw(){const rows=R.metric_rows.filter(r=>['season','target'].every(k=>q('nba-owner-'+k).value==='all'||q('nba-owner-'+k).value===r[k])&&(q('nba-owner-track').value==='all'||q('nba-owner-track').value===r.evidence_track));q('nba-owner-count').textContent=rows.length+' saved metric rows; separate evidence policies and denominators.';q('nba-owner-metrics').tBodies[0].innerHTML=rows.map(r=>'<tr>'+cells([r.season+' / '+w(r.evidence_track),w(r.role_alias)+' / '+r.family,r.target+' / '+w(r.phase)+' / T'+r.horizon_minutes,(r.scored_games??'Unavailable')+' / '+(r.completed_game_denominator??'Unavailable'),...keys.map(k=>s(r.metrics[k],k)),Object.entries(r.missing_reasons||{}).map(([k,v])=>w(k)+': '+v).join('; ')+(r.state_origin?' / '+w(r.state_origin):'')])+'</tr>').join('');}
q('nba-owner-source-status').innerHTML=R.source_sections.map(r=>'<p>'+e(w(r.section))+': '+e(w(r.status))+'; '+Object.entries(r).filter(([k])=>['new_estimator_fits','reused_fits','reused_estimator_fits','reused_current_origin_states','new_calibration_fits','new_preprocessor_fits','new_prediction_rows','reused_prediction_rows'].includes(k)).map(([k,v])=>e(w(k))+': '+e(v)).join('; ')+'; cutoff '+e(r.training_cutoff_utc)+'</p>').join('');
q('nba-owner-peaks').tBodies[0].innerHTML=R.historical_descriptive_peaks.map(r=>'<tr>'+cells([r.season+' / T'+r.horizon_minutes,r.target+' / '+w(r.metric),r.families.join('; '),s(r.saved_metric_value,r.metric),r.games+' / '+r.tied_saved_rows])+'</tr>').join('');
q('nba-owner-pairs').tBodies[0].innerHTML=R.model_pairs.map(r=>'<tr>'+cells([w(r.evidence_track)+' / '+r.target+' / T'+r.horizon_minutes,r.left_families.join('; ')+' / '+r.right_families.join('; '),(r.matched_games??'Unavailable')+' / '+(r.completed_phase_games??'Unavailable')+' / '+(r.matched_week_clusters??'Unavailable'),...keys.map(k=>s(r.left_on_matched_games[k],k)+' / '+s(r.right_on_matched_games[k],k))])+'</tr>').join('');
q('nba-owner-coverage').tBodies[0].innerHTML=R.venue_coverage.map(r=>'<tr>'+cells([r.season,w(r.provider),r.maximum_matched_games_in_one_saved_view,w(r.status)])+'</tr>').join('');
q('nba-owner-venues').tBodies[0].innerHTML=R.venue_comparisons.map(r=>'<tr>'+cells([r.season+' / '+w(r.evidence_track),w(r.provider)+' / '+r.family+' / '+w(r.model_alias)+' / T'+(r.horizon_minutes??'Unavailable'),r.model_on_same_reference_games.games,...keys.slice(0,3).map(k=>s(r.model_on_same_reference_games[k],k)+' / '+s(r.raw_bbo_midpoint_reference[k],k)),(r.fair_probability_games??'Unavailable')+' / '+(r.week_clusters??'Unavailable')])+'</tr>').join('');
for(const k of ['season','target','track'])q('nba-owner-'+k).addEventListener('change',draw);draw();})();</script></section>\n'''+END+'\n'


def attach_model_review(base_html,review):
    clean=re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?','',base_html,flags=re.S)
    anchor='<p><a href="latest_research_outputs.json.gz" data-sel-json="latest_research_outputs.json">Complete observed schedule and selected outputs</a> · <a href="validate_research_snapshot.py">Public evidence validator</a> · <a href="../README.md">NBA research history</a></p>\n'
    section=render_section(review)
    historical_end='<!-- NBA B077 REVIEW END -->\n'
    if clean.count(historical_end)==1:return clean.replace(historical_end,historical_end+section,1)
    if clean.count(anchor)==1:return clean.replace(anchor,anchor+section,1)
    v9_anchor='<!-- NBA V9 ACCEPTANCE BEGIN -->'
    if clean.count(v9_anchor)==1:return clean.replace(v9_anchor,section+v9_anchor,1)
    if clean.count('</main>')!=1:_fail('UNIQUE_HTML_INSERTION_POINT_REQUIRED')
    return clean.replace('</main>',section+'</main>',1)



def build(check=False):
    from restore_snapshot_assets import restore
    if (ROOT/'snapshot_asset_manifest.json').exists():restore(ROOT)
    saved=json.loads((ROOT/'latest_model_review.json').read_bytes())
    public=json.loads((ROOT/'latest_research_outputs.json').read_bytes())
    if saved['evidence_as_of_utc']!=public['evidence_as_of_utc'] or saved['latest_original_issue_at_utc']!=public['latest_forecast_issue_at_utc']:
        _fail('SAVED_SOURCE_CLOCK_MISMATCH')
    path=ROOT/'latest_research_outputs.html'; current=expand_html(path.read_text())
    result=attach_model_review(current,saved)
    if check and result!=current:_fail('SAVED_MODEL_DISPLAY_STALE')
    if not check:path.write_text(result)
    return {'status':'PASS' if check else 'BUILT','saved_metric_rows':len(saved['metric_rows']),
        'new_fits':0,'new_inference':0,'new_scoring':0,'sha256':hashlib.sha256(result.encode()).hexdigest()}

if __name__=='__main__':print(json.dumps(build('--check' in sys.argv),sort_keys=True))
