"""Display actual N083 evidence without fitting or rescoring public rounded rows."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime
from selected_review_n073 import TEMPLATE
FORECAST='selected_forecasts_n084.json'
HEALTH='2026-11-13-n083-actual-n084-review.json'

def validate(raw,h):
    if hashlib.sha256(raw).hexdigest()!=h['selected_forecasts_sha256']:raise ValueError('FORECAST_DIGEST')
    p=json.loads(raw)
    if p['automatic_promotion'] or h['automatic_promotion']:raise ValueError('PROMOTION')
    if len(p['games'])!=p['counts']['schedule_games'] or len({g['game_id'] for g in p['games']})!=len(p['games']):raise ValueError('GAME_DENOMINATOR')
    n=0;ids=set()
    for g in p['games']:
        if g['official_time_tbd'] and g['kickoff_utc'] is not None:raise ValueError('TBD_CLOCK')
        for target,panel in g['targets'].items():
            for r in panel['current_forecasts']:
                if g['completed_in_saved_census'] or g['official_time_tbd'] or r['target']!=target:raise ValueError('FORWARD_COHORT')
                if r['evidence_kind']!='original_issued' or not datetime.fromisoformat(r['model_completed_at_utc'])<=datetime.fromisoformat(r['original_issue_at_utc'])<datetime.fromisoformat(g['kickoff_utc']):raise ValueError('FORWARD_CLOCK')
                n+=1;ids.add(g['game_id'])
            for r in panel['prior_selected_reconstruction']:
                if r['original_issue_at_utc'] is not None or r['evidence_kind']!='historical_reconstruction':raise ValueError('REPLAY_CREDIT')
    if (n,len(ids))!=(p['counts']['current_selected_rows'],p['counts']['current_selected_games']):raise ValueError('ROW_DENOMINATOR')
    if h['new_fits']!=h['new_native_fits']+h['new_meta_fits']:raise ValueError('FIT_ACCOUNTING')
    if h['qualified_provider_comparison_cells']!=0 or h['owner_research_acceptance']:raise ValueError('UNSUPPORTED_ACCEPTANCE')
    return p

def replace(page,old,new):
    if page.count(old)!=1:raise ValueError('TEMPLATE_ANCHOR '+old[:80])
    return page.replace(old,new,1)

def render(raw,h):
    p=validate(raw,h)
    encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=TEMPLATE.replace('__SELECTED_DATA__',encode(p)).replace('selected_forecasts_n073.json',FORECAST)
    page=page.replace('Latest owner execution: frozen research resumed','Actual N083: 376 new fits; complete game census')
    page=replace(page,"'Original forecast-input source '+utc(game.source_observed_at_utc)","'Saved source observation '+utc(game.source_observed_at_utc)")
    page=replace(page,'utc(game.latest_schedule_observed_at_utc)','utc(game.source_observed_at_utc)')
    page=replace(page,'const state=game.current_source_coverage[provider.toLowerCase()];',"const state={observation_status:'NO_ADMITTED_SAME_CUTOFF_COMPARISON'};")
    page=replace(page,"(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census)","(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census&&!g.official_time_tbd&&Date.parse(g.kickoff_utc)>Date.parse(data.display_cutoff_utc))")
    page=page.replace('<option value="future">Upcoming in saved census</option>','<option value="future">Upcoming · confirmed time</option>')
    start=page.index('const run=data.latest_owner_execution,refresh=data.latest_source_refresh;');end=page.index('renderGames();renderLeaders();window.nflSelectedReview=',start)
    script='const run='+encode(h)+r''';
byId('owner-status').textContent='N083 completed '+run.new_fits+' new fits ('+run.new_native_fits+' native + '+run.new_meta_fits+' meta) and recorded '+run.new_forecast_events+' forecast events. The selected display contains '+data.counts.current_selected_rows+' outputs across '+data.counts.current_selected_games+' upcoming games. Whole-owner status remains partial; completed scientific work is preserved. No production promotion is established.';
byId('owner-elapsed').textContent='Invocation '+(run.elapsed_seconds/60).toFixed(2)+' minutes; completed '+utc(run.finished_at_utc)+'. Whole-instance compute estimate $'+run.compute_estimate_usd.toFixed(3)+' (not a bill; excludes storage, requests and data charges). '+run.new_paid_calls+' paid calls. The current-season monitor launched '+run.current_2026_monitor.physical_worker_launches+' workers, with '+run.current_2026_monitor.new_fits+' new fits and '+run.current_2026_monitor.replay_rows+' replay rows. Its peak of '+run.current_2026_monitor.peak_leased_native_processes+' leased native processes is not proof of sustained CPU use.';
for(const provider of ['DraftKings','Kalshi','Polymarket']){const tr=document.createElement('tr');for(const s of [provider,'0 admitted comparison values','Missing same-cutoff quotes in this selected export; no market win claimed'])tr.appendChild(textNode('td',s));byId('latest-sources').appendChild(tr);}
for(const gap of run.source_gaps)byId('source-gaps').appendChild(textNode('li',gap));
'''
    page=page[:start]+script+page[end:]
    panel='''<section class="panel" id="current-monitor"><h2>2026 replay and former champions</h2><p class="note">The new current-season monitor has explicit coverage gaps. Its detailed scorecards were offloaded and are absent from the supplied return ZIP. This page does not invent a new 2026 winner or relabel an older leaderboard as the latest result.</p><p>The <a href="season_review_n083.html#all-current-scores">prior review preserves all 77 dated 2026 scorecards</a>, 35 same-cohort leader rows and former champion gaps. The historical leader table below preserves same-candidate 2024/2025 metrics. Operational fallbacks have their own rows and never replace missing primary roles. No independently validated rolling production champion is established.</p><p>All 272 regular-season games are shown: 137 finals, 111 upcoming games with confirmed times and 24 with kickoff TBD. Earlier pregame forecasts for Washington at New York remain earlier issues after the newly observed final result. Missing predictions and provider values stay blank.</p><p><a href="2026-11-13-n083-actual-n084-review.json">Actual execution evidence</a> · <a href="season_review_n083.html">Prior dated review</a></p></section>'''
    from html import escape
    cols=('model_alias','model_family','season','target','n','comparison_horizon_seconds','accuracy','log_loss','brier','mae','rmse','ece')
    rows=''.join('<tr>'+''.join('<td>'+escape(str(r.get(k,'—')))+'</td>' for k in cols)+'</tr>' for r in h['new_historical']['cards'])
    panel+='<section class="panel" id="new-science"><h2>60 new candidates · 120 frozen scorecards</h2><p>'+escape(h['new_historical']['qualification'])+'</p><div class="scroll" tabindex="0"><table><thead><tr>'+''.join('<th>'+escape(k)+'</th>' for k in cols)+'</tr></thead><tbody id="science-cards">'+rows+'</tbody></table></div></section>'
    page=replace(page,'<section class="panel" id="leaders">',panel+'<section class="panel" id="leaders">')
    page=page.replace('<option value="7200">Two hours before kickoff</option>','')
    return page

def main():
    a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');args=a.parse_args();root=Path(__file__).parent
    page=render((root/FORECAST).read_bytes(),json.loads((root/HEALTH).read_bytes()));output=root/'season_review_n084.html'
    if args.check:
        if output.read_text()!=page:raise SystemExit('RENDER_MISMATCH')
        print('N084 source digest, clocks, counts and deterministic HTML verified.')
    else:output.write_text(page)
if __name__=='__main__':main()
