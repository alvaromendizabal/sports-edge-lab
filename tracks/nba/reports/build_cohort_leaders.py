"""Display authenticated saved-score leaders within distinct exact cohorts."""
import hashlib
import html
import json
from pathlib import Path
from b083_html import expand_html
import re
import sys

ROOT=Path(__file__).parent
SCHEMA='sports-edge-lab.nba.saved-current-cohort-leaders.v1'
BEGIN='<!-- NBA CURRENT COHORT LEADERS BEGIN -->'
END='<!-- NBA CURRENT COHORT LEADERS END -->'
PIN='2ed1ae7c3abb0dd13daaaa0e7b2c882e800db5b4c939122ea079b390f06a0acd'

def validate(value,model):
    if value.get('schema')!=SCHEMA or value.get('release')!='B082':raise ValueError('COHORT_SCHEMA')
    if (value['entire_current_season_best_claim'] or value['independent_confirmation_claim'] or value['original_issue_claim']
            or not value['no_cross_cohort_ranking'] or value['selection_exposure']!='EXPOSED_RETROSPECTIVE_CURRENT_MONITORING_ONLY'):
        raise ValueError('COHORT_EXPOSURE_OR_SCOPE')
    for name in ['new_estimator_fits','new_inference','new_metric_scoring','production_promotions']:
        if value[name]!=0:raise ValueError('COHORT_DISPLAY_ONLY')
    if value['evidence_as_of_utc']!=model['evidence_as_of_utc']:raise ValueError('COHORT_SOURCE_CLOCK')
    rows={row['row_id']:row for row in model['metric_rows']}
    if len(rows)!=len(model['metric_rows']):raise ValueError('COHORT_SOURCE_ROW_IDENTITY')
    seen=set();scopes={}
    for row in value['rows']:
        key=(row['cohort_alias'],row['metric'])
        if key in seen:raise ValueError('COHORT_DUPLICATE_METRIC')
        seen.add(key)
        if (row['selection_or_promotion_allowed'] or row['entire_current_season_best_claim'] or row['original_issue_claim']
                or row['new_paired_interval_calculated'] or not row['exact_same_official_game_set_verified']):
            raise ValueError('COHORT_ROW_SCOPE')
        if row['scored_games']+row['missing_games']!=row['completed_game_denominator']:raise ValueError('COHORT_DENOMINATOR')
        scope=tuple(row[k] for k in ['season','phase','target','horizon_minutes','scored_games','completed_game_denominator','evidence_track'])
        if row['cohort_alias'] in scopes and scopes[row['cohort_alias']]!=scope:raise ValueError('COHORT_DISTINCT_SUPPORTS_COLLAPSED')
        scopes[row['cohort_alias']]=scope
        if not row['source_rows']:raise ValueError('COHORT_SAVED_SOURCE_REQUIRED')
        for reference in row['source_rows']:
            source=rows.get(reference['row_id'])
            if source is None or any(source.get(k)!=v for k,v in reference.items()):raise ValueError('COHORT_SOURCE_ROW_IDENTITY')
            if source['metrics'].get(row['metric'])!=row['saved_metric_value']:raise ValueError('COHORT_SAVED_SCORE_CHANGED')
            for k in ['season','phase','target','horizon_minutes','scored_games','completed_game_denominator','evidence_track']:
                if source[k]!=row[k]:raise ValueError('COHORT_SOURCE_SCOPE_CHANGED')
    for token in ['recipe_id','s3://','/home/','/workspace/','api_key','apiKey','feature_names','PRIVATE KEY']:
        if token in json.dumps(value):raise ValueError('COHORT_PRIVATE_DATA')
    return {'rows':len(value['rows']),'distinct_exact_cohorts':len(scopes)}

def render(value,model):
    validate(value,model)
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return BEGIN+'''
<section id="nba-current-cohorts" aria-labelledby="nba-current-cohorts-title">
<style>#nba-current-cohorts{margin:24px 0;padding:20px;border:1px solid #cddbd8;border-radius:8px;background:#f3f8f5}#nba-current-cohorts .scroll{max-height:500px;overflow:auto}#nba-current-cohorts td,#nba-current-cohorts p{overflow-wrap:anywhere}</style>
<h2 id="nba-current-cohorts-title">Current-season descriptive leaders on identical saved games</h2>
<p>These 40 copied metric leaders belong to 16 separate exact game-set, evidence-policy, target, phase and horizon cohorts. Fixed-state replay and newly refreshed season-frozen states have separate cohort aliases. Compare models within the same cohort alias. Different aliases remain separate even when their game counts match. The completed-game denominator and missing games are shown for every row; a cohort containing one eligible model establishes no head-to-head advantage.</p>
<p><strong>Exposed retrospective monitoring; no full-season best-model claim, independent confirmation or promotion.</strong> Scores are copied from saved evaluations. No new inference, rescoring or paired uncertainty calculation occurs here. Originally issued rolling evidence and market comparisons remain in their separate panels.</p>
<div class="filters"><label>Evidence policy<select id="nba-cohort-evidence_track"><option value="all">Both separate policies</option><option value="CURRENT_FIXED_STATE_REPLAY">Fixed-state replay</option><option value="NEW_SEASON_FROZEN_REFRESH">New season-frozen refresh</option></select></label><label>Target<select id="nba-cohort-target"><option value="all">All targets</option><option>winner</option><option>margin</option><option>total</option></select></label><label>Nominal horizon<select id="nba-cohort-horizon"><option value="all">Both horizons</option><option value="60">T60</option><option value="120">T120</option></select></label><label>Metric<select id="nba-cohort-metric"><option value="all">All requested metrics</option><option>accuracy</option><option>log_loss</option><option>brier</option><option>mae</option><option>rmse</option></select></label></div>
<p id="nba-cohort-count" aria-live="polite"></p><div class="scroll"><table id="nba-cohort-leaders"><thead><tr><th>Exact saved cohort / policy</th><th>Target / phase / horizon</th><th>Metric</th><th>Leading saved families and roles</th><th>Saved value</th><th>Scored / completed / missing</th><th>Eligible models / role views</th></tr></thead><tbody></tbody></table></div>
<p><a href="current_saved_cohort_leaders.json">Download source-bound saved cohort leaders</a> · <a href="latest_model_review.json">Inspect all saved model rows and missingness</a></p>
<script id="nba-cohort-data" type="application/json">'''+data+'''</script>
<script>(()=>{'use strict';const R=JSON.parse(document.getElementById('nba-cohort-data').textContent),q=id=>document.getElementById(id),w=x=>String(x??'Unavailable').replaceAll('_',' '),e=x=>String(x??'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),cells=a=>a.map(v=>'<td>'+e(v)+'</td>').join('');
function draw(){const rows=R.rows.filter(r=>['target','metric','evidence_track'].every(k=>q('nba-cohort-'+k).value==='all'||q('nba-cohort-'+k).value===r[k])&&(q('nba-cohort-horizon').value==='all'||Number(q('nba-cohort-horizon').value)===r.horizon_minutes));q('nba-cohort-count').textContent=rows.length+' saved metric leaders; '+new Set(rows.map(r=>r.cohort_alias)).size+' separate exact cohorts; no cross-cohort ranking.';q('nba-cohort-leaders').tBodies[0].innerHTML=rows.map(r=>'<tr data-cohort="'+e(r.cohort_alias)+'" data-metric="'+e(r.metric)+'">'+cells([r.cohort_alias+' / '+w(r.evidence_track),r.target+' / '+w(r.phase)+' / T'+r.horizon_minutes,w(r.metric),r.families.join('; ')+' / '+r.source_rows.map(x=>w(x.role_alias)).join('; '),r.metric==='accuracy'?(100*r.saved_metric_value).toFixed(2)+'%':r.saved_metric_value.toFixed(6),r.scored_games+' / '+r.completed_game_denominator+' / '+r.missing_games,r.distinct_saved_recipes+' / '+r.eligible_saved_role_views])+'</tr>').join('');}
for(const name of ['target','horizon','metric','evidence_track'])q('nba-cohort-'+name).addEventListener('change',draw);draw();})();</script>
</section>
'''+END+'\n'

def attach(body,value,model):
    if body.count(BEGIN)!=body.count(END) or body.count(BEGIN)>1:raise ValueError('COHORT_DUPLICATE_OR_UNCLOSED')
    clean=re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?','',body,flags=re.S)
    anchor='<!-- NBA OWNER MODEL REVIEW END -->\n'
    if clean.count(anchor)!=1:raise ValueError('COHORT_OWNER_PANEL_ANCHOR_REQUIRED')
    return clean.replace(anchor,anchor+render(value,model),1)

def build(check=False):
    from restore_snapshot_assets import restore
    if (ROOT/'snapshot_asset_manifest.json').exists():restore(ROOT)
    raw=(ROOT/'current_saved_cohort_leaders.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('COHORT_PIN_REVIEW_REQUIRED')
    value=json.loads(raw);modelbody=(ROOT/'latest_model_review.json').read_bytes();model=json.loads(modelbody)
    pin={'bytes':len(modelbody),'sha256':hashlib.sha256(modelbody).hexdigest()}
    if value['source_public_file_pin']!=pin:raise ValueError('COHORT_MODEL_REVIEW_PIN_CHANGED')
    receipt=validate(value,model);path=ROOT/'latest_research_outputs.html';body=expand_html(path.read_text());result=attach(body,value,model)
    if check and body!=result:raise ValueError('COHORT_DISPLAY_STALE')
    if not check:path.write_text(result)
    return {'status':'PASS' if check else 'BUILT',**receipt,'new_fits':0,'new_scores':0,'display_sha256':hashlib.sha256(result.encode()).hexdigest()}

if __name__=='__main__':print(json.dumps(build('--check' in sys.argv),sort_keys=True))
