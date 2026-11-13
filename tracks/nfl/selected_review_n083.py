"""Render the authenticated N082 selected outputs without fitting or rescoring."""
import argparse
import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from selected_review_n073 import TEMPLATE

HEALTH='2026-11-13-n082-actual-n083-review.json'
FORECAST='selected_forecasts_n083.json'
GROUPS=('current_forecasts','earlier_saved_forward','prior_selected_reconstruction')


def validate(raw,health):
    if hashlib.sha256(raw).hexdigest()!=health['selected_forecasts_sha256']:
        raise ValueError('SELECTED_ORIGINAL_BYTES_CHANGED')
    value=json.loads(raw)
    if value.get('schema')!='nfl.n075.rounded-selected-forecast-publication.v1' or value.get('sport')!='NFL':
        raise ValueError('SELECTED_SCHEMA_MISMATCH')
    games=value['games']; counts=value['counts']
    if len(games)!=counts['schedule_games'] or len({g['game_id'] for g in games})!=len(games):
        raise ValueError('SELECTED_GAME_DENOMINATOR_MISMATCH')
    if value['automatic_promotion'] or health['automatic_promotion']:
        raise ValueError('INDEPENDENT_PROMOTION_NOT_ESTABLISHED')
    selected=[]
    for g in games:
        if g['official_time_tbd'] and g['kickoff_utc'] is not None:
            raise ValueError('TBD_PLACEHOLDER_KICKOFF')
        for target,panel in g['targets'].items():
            for row in panel['current_forecasts']:
                if g['completed_in_saved_census'] or g['official_time_tbd']:
                    raise ValueError('CURRENT_ISSUE_NOT_FORWARD')
                if row['target']!=target or row['evidence_kind']!='original_issued':
                    raise ValueError('CURRENT_ISSUE_CLASS_MISMATCH')
                issued=datetime.fromisoformat(row['original_issue_at_utc'])
                fitted=datetime.fromisoformat(row['model_completed_at_utc'])
                cutoff=datetime.fromisoformat(g['kickoff_utc'])
                if not fitted<=issued<cutoff:
                    raise ValueError('CURRENT_ISSUE_CLOCK_INVALID')
                selected.append((g['game_id'],row))
            for row in panel['prior_selected_reconstruction']:
                if row['original_issue_at_utc'] is not None or row['evidence_kind']!='historical_reconstruction':
                    raise ValueError('RECONSTRUCTION_ORIGINAL_ISSUE_CREDIT')
    if len(selected)!=counts['current_selected_rows'] or len({g for g,_ in selected})!=counts['current_selected_games']:
        raise ValueError('SELECTED_ROW_DENOMINATOR_MISMATCH')
    if health['selected_public_rows']!=len(selected) or health['selected_public_games']!=len({g for g,_ in selected}):
        raise ValueError('HEALTH_SELECTED_COUNT_MISMATCH')
    if health['forward_monitor_rows']!=135 or health['forward_monitor_unique_games']!=15:
        raise ValueError('EARLY_MONITOR_DENOMINATOR_MISMATCH')
    if any(c['games']!=15 or c['automatic_promotion'] or c['current_season_selection_eligible'] for c in health['forward_monitor_scorecards']):
        raise ValueError('EARLY_MONITOR_SELECTION_CREDIT')
    if health['new_fits'] is not None or health['new_native_fits'] is not None or health['new_meta_fits'] is not None or health['owner_research_acceptance'] or (health['verified_new_fit_minimum'],health['verified_new_native_fit_minimum'],health['verified_new_meta_fit_minimum']) != (337,324,13):
        raise ValueError('N082_MINIMUM_AND_UNKNOWN_TOTAL_MUST_REMAIN_VISIBLE')
    if health['new_n083_owner_science_claimed'] or health['complete_current_season_champion_replay']:
        raise ValueError('UNOBSERVED_OWNER_COMPLETION_CLAIM')
    role_map={r['role_id']:r for r in value['selected_historical_roles']}
    if len(health['selected_2026_scorecards']) != len(role_map):
        raise ValueError('CURRENT_ROLE_CENSUS_INCOMPLETE')
    for card in health['selected_2026_scorecards']:
        role=role_map[card['role_id']]
        if any(card[k] != role[k] for k in ('model_alias','target','metric','comparison_horizon_seconds')):
            raise ValueError('ROLE_OR_HORIZON_MISMATCH')
        if card['original_issue_credit'] or card['promotion_authorized'] or card['games']>card['completed_games']:
            raise ValueError('REPLAY_CREDIT_OR_DENOMINATOR_INVALID')
    if len(health['former_unresolved_roles'])!=18 or any(r['comparison_horizon_seconds'] is not None or r['current_same_role_metric'] is not None for r in health['former_unresolved_roles']):
        raise ValueError('FORMER_ROLE_HORIZON_INVENTED')
    if health['new_qualified_market_comparison_cells'] != 0:
        raise ValueError('UNSUPPORTED_MARKET_COMPARISON')
    return value


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('RENDER_TEMPLATE_ANCHOR_CHANGED: '+old[:70])
    return text.replace(old,new,1)


def _render_base(raw,health):
    value=validate(raw,health)
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    data=data.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=TEMPLATE.replace('__SELECTED_DATA__',data)
    page=page.replace('selected_forecasts_n073.json',FORECAST)
    page=page.replace('<a href="#evidence">Evidence limits</a>', '<a href="#replay-current">2026 replay leaders</a><a href="#matched-markets">Markets</a><a href="#evidence">Evidence limits</a><a href="'+HEALTH+'" download>Metric evidence</a>')
    page=replace_once(page,'Latest owner execution: frozen research resumed','Actual N082: 337 verified fits; owner acceptance incomplete')
    page=replace_once(page,"'Original forecast-input source '+utc(game.source_observed_at_utc)","'Saved source observation '+utc(game.source_observed_at_utc)")
    page=replace_once(page,"utc(game.latest_schedule_observed_at_utc)","utc(game.source_observed_at_utc)")
    page=replace_once(page,"const state=game.current_source_coverage[provider.toLowerCase()];","const state={observation_status:'NO_ADMITTED_COMPARISON_IN_SELECTED_EXPORT'};")
    h=json.dumps(health,sort_keys=True,separators=(',',':'),allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=replace_once(page,"const run=data.latest_owner_execution,refresh=data.latest_source_refresh;","const run="+h+";")
    start=page.index("byId('owner-status').textContent=")
    end=page.index('renderGames();renderLeaders();window.nflSelectedReview=',start)
    js=r'''const availablePrimary=new Set(data.games.flatMap(g=>Object.values(g.targets).flatMap(t=>t.roles.filter(r=>r.current_forecast_available&&r.role_id.startsWith('primary_')).map(r=>r.role_id))));
byId('owner-status').textContent='N082 completed at least '+run.verified_new_fit_minimum+' verified fits ('+run.verified_new_native_fit_minimum+' native / '+run.verified_new_meta_fit_minimum+' meta); the whole-run fit total remains unknown after an earlier failed stage. Elapsed '+(run.elapsed_seconds/60).toFixed(2)+' minutes. Owner research acceptance: false. '+run.unique_issue_events.toLocaleString('en-US')+' unique issue events across '+run.issued_games+' genuinely upcoming games. Latest selected display: '+run.selected_public_rows+' rows for '+run.selected_public_games+' games. '+availablePrimary.size+' of '+data.counts.primary_metric_roles+' primary historical roles have current outputs. Authenticated 2026 replay metrics are now shown below; missing cohorts remain explicit. No rolling promotion or N083 owner-science result is claimed.';
byId('owner-elapsed').textContent='Main scientific child started '+(run.seconds_until_main_scientific_child/60).toFixed(2)+' minutes after invocation. '+run.reused_complete_batches+' completed batches reused; '+run.observed_concurrent_optimizer_calls+' concurrent native optimizer calls verified from entry/return intervals. Sampled process-tree CPU mean '+run.observed_process_tree_mean_cores.toFixed(3)+' cores; maximum retained instantaneous row '+run.maximum_retained_instantaneous_cores.toFixed(3)+' cores over '+run.maximum_retained_instantaneous_seconds.toFixed(3)+' seconds. Monitor-reported cumulative peak '+run.observed_process_tree_peak_cores.toFixed(3)+'; its underlying instantaneous row is not retained. This is not sustained 12-core utilization. '+run.cache_hits+' cache hits / '+run.cache_misses+' misses; '+run.cache_byte_reuse_percent.toFixed(2)+'% bytes reused. '+run.new_paid_calls+' paid calls. Whole-instance compute estimate $'+run.compute_time_estimate_usd.toFixed(3)+'; not an AWS bill. '+run.unique_game_recipe_pairs+' game/recipe pairs and '+run.later_issue_events_on_existing_pairs+' later issues on existing pairs are not independent games.';
for(const row of run.selected_2026_descriptive_leaders){const tr=document.createElement('tr');for(const item of [row.target,row.metric,(row.comparison_horizon_seconds/60)+' min',row.model_aliases.join(' / '),formatMetric(row.value,row.metric),row.games+' games; '+row.selected_candidates_compared+' selected candidates',row.cohort_sha256.slice(0,12)])tr.appendChild(textNode('td',item));byId('replay-leaders').appendChild(tr);}
for(const row of run.other_actual_horizon_scorecards){const tr=document.createElement('tr');for(const item of [row.model_alias,row.target,row.comparison_horizon_seconds+' seconds',row.games,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(row.metrics[m],m))])tr.appendChild(textNode('td',item));byId('other-horizon-scores').appendChild(tr);}
for(const row of run.former_unresolved_roles){const tr=document.createElement('tr');for(const item of [row.role_alias,row.target,row.metric,'Original horizon unrecovered','Unavailable; no substitute horizon'])tr.appendChild(textNode('td',item));byId('former-roles').appendChild(tr);}
for(const row of run.current_replay_comparison_missing){const tr=document.createElement('tr');for(const item of [row.provider,row.target,0,row.rows+' replay rows examined',row.reason.replaceAll('_',' ').toLowerCase()])tr.appendChild(textNode('td',item));byId('replay-markets').appendChild(tr);}
for(const provider of run.provider_coverage){const tr=document.createElement('tr');for(const item of [provider.provider,'Current selected export: no quote values',provider.qualified_comparison_cells+' qualified comparison cells. '+provider.reason])tr.appendChild(textNode('td',item));byId('latest-sources').appendChild(tr);}
const schedule=document.createElement('tr');for(const item of ['Schedule',data.counts.schedule_games+' games; '+data.counts.completed_games+' completed; '+data.counts.official_time_tbd_games+' kickoff TBD','Updated saved census; missing feature refreshes remain explicit.'])schedule.appendChild(textNode('td',item));byId('latest-sources').appendChild(schedule);
for(const gap of run.source_gaps)byId('source-gaps').appendChild(textNode('li',gap));
for(const row of run.forward_monitor_scorecards){const tr=document.createElement('tr');const metrics=row.target==='win'?[row.correct+'/'+row.games,(100*row.accuracy).toFixed(2)+'%',row.log_loss.toFixed(6),row.brier.toFixed(6),'—','—']:[row.games+' games','—','—','—',row.mae.toFixed(3),row.rmse.toFixed(3)];for(const item of [row.model_alias,row.target,...metrics])tr.appendChild(textNode('td',item));byId('early-scores').appendChild(tr);}
'''
    page=page[:start]+js+page[end:]
    section='''<section class="panel" id="current-monitor"><h2>Preserved N079 early snapshots: 15 games</h2><p class="note">135 rows represent 15 unique games × three saved combinations × three targets. These are timestamped early snapshots with independent durable pregame delivery and full source-publication clocks unproved. They are not a complete 136-game season score or current-champion replay, and cannot select or promote a model.</p><p>These dated N079 scores are unchanged by this publication and are not new N082 evaluations. Scores below come from preserved full-precision owner scorecards. No public rounded forecast is rescored. The archived 77-game original-model and 119-game Kalshi panels remain separate in the <a href="CURRENT_MODEL_CARD.md">model card</a>.</p><div class="scroll" tabindex="0" aria-label="Saved early snapshot metrics"><table><thead><tr><th>Saved model</th><th>Target</th><th>Support / correct</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="early-scores"></tbody></table></div></section>'''
    page=replace_once(page,'<section class="panel" id="evidence">',section+'\n<section class="panel" id="evidence">')
    page=page.replace('<th scope="col">Support</th>','<th scope="col">Support</th><th scope="col">2026 exact-horizon replay / current issues</th>')
    page=page.replace("tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));body.appendChild(tr);", "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));const card=run.selected_2026_scorecards.find(c=>c.role_id===row.role_id),td=textNode('td',formatMetric(card?.metrics?.[row.metric],row.metric));if(card){td.appendChild(textNode('small',card.games+' scored / '+card.completed_games+' completed games; frozen replay'));td.appendChild(textNode('small',card.current_issued_games+' current issued games; no rolling promotion'));if(card.status!=='SCORED_FROZEN_REPLAY')td.appendChild(textNode('small',card.status.replaceAll('_',' ').toLowerCase()));}tr.appendChild(td);body.appendChild(tr);")
    former='<section class="panel" id="former-leaders"><h2>Former and rolling champions</h2><p>Original Torch AB remains the saved 557-game accuracy leader (388 correct). Original Torch B remains the saved log-loss leader (0.595426) and Brier leader (0.204637). Those original cohorts differ from the 569-game historical probability selections above; no cross-cohort ranking is valid.</p><p>These candidates remain preserved. Their fresh original runtime and complete current-season comparison are unresolved. The 18 exact former-role comparison gaps below preserve their missing original horizons. No independent rolling production promotion is established. Other metric-specific former roles remain explicit in the retained private registry.</p><p>Home/away score distributions, prediction intervals and current same-cutoff market values are unavailable in this selected export. Independent margin and total heads are not combined into an asserted coherent score distribution.</p></section>'
    page=replace_once(page,'<section class="panel" id="evidence">',former+'<section class="panel" id="evidence">')
    replay = '<section class="panel" id="replay-current"><h2>2026: measured leaders on the available replay cohort</h2><p class="note">Best among the displayed selected candidates at the identical target, horizon and game cohort. This is exposed descriptive monitoring, not fresh selection, original-issue performance or a rolling promotion. Each winner row has 119 scored games; point rows have 120. The saved census has 136 finals: 16 have archived vectors only at other actual horizons in this projection, and conditional winner scoring excludes one tie. Unplayed games remain unscored.</p><p>The one-hour and two-hour cohorts remain separate. Values come from saved full-precision owner scorecards, never rounded forecast rescoring. CRPS is unavailable where a complete earlier out-of-sample residual distribution is absent. The table above tracks the same historical selections through 2024, 2025 and 2026; this table answers which of the displayed selected and retained candidates has the best descriptive metric on that exact cohort.</p><div class="scroll" tabindex="0" aria-label="Current selected replay leaders"><table><thead><tr><th>Target</th><th>Metric</th><th>Horizon</th><th>Best selected model</th><th>Value</th><th>Support</th><th>Exact cohort digest</th></tr></thead><tbody id="replay-leaders"></tbody></table></div></section>'
    replay += '<section class="panel" id="other-horizons"><h2>Other archived horizons: separate standalone scores</h2><p>These dated retained aggregates include the original two-hour comparison and separate actual lead times: 14 games at86,400seconds and one each at4,738.345284 and170,544.720703seconds. The two-hour cohort is never pooled with the current one-hour selection or the other actual horizons. Across all actual horizons, some point replay is available for all 136 finals and conditional winner replay for 135 non-ties. This does not establish any one comparable 136-game selected-role score. The one-game groups are observations, not useful performance estimates. No horizon is invented or combined with another; no original-issue or promotion credit is given.</p><div class="scroll" tabindex="0" aria-label="Other actual horizon selected model scores"><table><thead><tr><th>Selected model</th><th>Target</th><th>Actual horizon</th><th>Games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="other-horizon-scores"></tbody></table></div></section>'
    replay += '<section class="panel" id="former-role-gaps"><h2>Preserved former roles: unresolved horizon comparisons</h2><p>All 18 unresolved former metric roles remain visible. A replay at an observed horizon does not recover the original selection horizon. No missing score is treated as zero or silently replaced by a later champion. The original Torch accuracy/log-loss/Brier records remain separately qualified above.</p><div class="scroll" tabindex="0" aria-label="Former metric role gaps"><table><thead><tr><th>Former role</th><th>Target</th><th>Metric</th><th>Original horizon</th><th>Comparable 2026 score</th></tr></thead><tbody id="former-roles"></tbody></table></div></section>'
    replay += '<section class="panel" id="matched-markets"><h2>2026 same-cutoff market comparisons</h2><p>No qualified comparison is admitted for this selected replay. The counts below are target-specific replay rows examined, not unique games or quote captures. Winner quotes require an authentic fresh equivalent cutoff; expected margin and total cannot be replaced by conditional threshold contracts. Earlier separately qualified saved venue panels remain in the model card.</p><div class="scroll" tabindex="0" aria-label="Current season market comparison coverage"><table><thead><tr><th>Provider</th><th>Target</th><th>Admitted comparisons</th><th>Examined denominator</th><th>Missing reason</th></tr></thead><tbody id="replay-markets"></tbody></table></div></section>'
    page=replace_once(page,'<section class="panel" id="evidence">',replay+'<section class="panel" id="evidence">')

    return page


def render(raw,health):
    from zoneinfo import ZoneInfo
    value=validate(raw,health)
    c=health['saved_census'];science=health['new_science']
    if (c['games'],c['completed'],c['live'],c['confirmed_future'],c['kickoff_tbd'])!=(272,136,1,111,24):
        raise ValueError('LIVE_FUTURE_FINAL_CENSUS_CHANGED')
    if sum(c[k]for k in ('completed','live','confirmed_future','kickoff_tbd'))!=len(value['games']):
        raise ValueError('LIFECYCLE_PARTITION_INCOMPLETE')
    if len(science['cards'])!=216 or len({r['model_alias']for r in science['cards']})!=108:
        raise ValueError('NEW_EXPERIMENT_CARDS_INCOMPLETE')
    if any(r['prospective'] or r['promotion_authorized'] or r['season']not in (2024,2025)or r['comparison_horizon_seconds']!=3600 for r in science['cards']):
        raise ValueError('NEW_EXPERIMENT_COHORT_OR_PROMOTION_INVALID')
    if any(r['improvement_over_preserved_best']>0 or r['prospective_or_statistical_superiority_claimed']for r in science['matched_new_vs_preserved']):
        raise ValueError('UNOBSERVED_NEW_CANDIDATE_SUPERIORITY')
    page=_render_base(raw,health)
    cutoff=datetime.fromisoformat(value['display_cutoff_utc']).astimezone(ZoneInfo('America/Los_Angeles'))
    banner='<section class="panel" id="latest-attempt"><h2>Real model work completed · N082 · November 12, 2026 Pacific</h2><p class="note"><strong>337 verified completed fits: 324 native + 13 meta. Owner acceptance remains false.</strong> An earlier urgent refresh failed its frozen-recipe identity check, so the original global fit counters remain unknown. The successful stage and its completed work remain preserved.</p><p>Saved evidence cutoff: <strong>'+html.escape(value['display_cutoff_utc'])+'</strong> ('+cutoff.strftime('%B %d, %Y at %H:%M:%S Pacific (%Z)')+'). All 272 games remain visible: <strong>136 finals, 1 live, 111 confirmed future and 24 kickoff TBD</strong>. The live Washington–New York game retains earlier pregame issues only; no new post-kickoff prediction is substituted.</p><p>108 new candidates completed 216 frozen 2024/2025 scorecards. <strong>None beat the preserved best on the matched pooled selection cohorts.</strong> The current view shows 444 selected outputs for 111 upcoming games; 888 owner issue events include a second set of later genuine issues. No new N083 owner result, complete-season validation, rolling production promotion or website deployment is claimed.</p><p><a href="season_review_n082.html">Prior failed N081 attempt</a> · <a href="season_review_n080.html">Preserved N079 dashboard</a> · <a href="'+HEALTH+'">Current aggregate evidence</a></p></section>'
    page=replace_once(page,'<main class="wrap">','<main class="wrap">'+banner)
    page=page.replace('grid-template-columns:repeat(4,1fr)','grid-template-columns:repeat(5,1fr)')
    page=replace_once(page,'<div class="stat"><b id="forward">','<div class="stat"><b id="live-count">1</b><span>live in the saved source census</span></div><div class="stat"><b id="forward">')
    page=replace_once(page,'<option value="future">Upcoming in saved census</option>','<option value="future">Upcoming · confirmed time</option><option value="live">Live / started, not final</option>')
    page=replace_once(page,"const words=","function gameState(g){if(g.completed_in_saved_census)return 'completed';if(g.official_time_tbd)return 'tbd';return Date.parse(g.kickoff_utc)<=Date.parse(data.display_cutoff_utc)?'live':'future';}\nconst words=")
    page=replace_once(page,"(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census)","gameState(g)===status")
    page=replace_once(page,"'Unplayed in saved census'","gameState(game)==='live'?'LIVE · '+game.official_date_status:'Upcoming in saved census'")
    page=page.replace('<option value="7200">Two hours before kickoff</option>','')
    panels='''<section class="panel" id="new-science"><h2>New experiments: completed, measured, retained</h2><p id="science-timing"></p><p>These 108 native history-weighting candidates use two existing source-admitted feature frames and nine model families. All 324 frozen fit/cohort checks completed across inner 2023 and evaluation 2024/2025; 13 additional ensembles or calibrations use earlier out-of-fold or out-of-sample predictions. No new raw-source feature claim or automatic promotion is made.</p><p class="note">The best new candidates did not improve the preserved best on any of the nine matched pooled target/metric comparisons. Negative results remain visible. This is development-exposed selection evidence; there is no independent prospective superiority claim.</p><div class="scroll" tabindex="0" aria-label="New versus preserved matched metrics"><table><thead><tr><th>Target / metric</th><th>New candidate</th><th>Best new</th><th>Preserved best</th><th>Improvement</th><th>Exact support</th></tr></thead><tbody id="new-vs-preserved"></tbody></table></div><div class="toolbar"><label>Evaluation season<select id="science-season"><option value="">Both seasons</option><option value="2024">2024</option><option value="2025">2025</option></select></label><label>Target<select id="science-target"><option value="">All targets</option><option value="win">Winner</option><option value="margin">Margin</option><option value="total">Total</option></select></label><label>Model family<select id="science-family"><option value="">All families</option></select></label></div><p id="science-count" class="count" role="status"></p><div class="scroll" tabindex="0" aria-label="All 216 new frozen evaluation scorecards"><table class="roles"><thead><tr><th>Candidate / family</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>Cohort digest</th></tr></thead><tbody id="science-cards"></tbody></table></div><p class="muted">Each value is copied from the saved full-precision aggregate. Candidate aliases are local to this study. Sorting or filtering never pools horizons, seasons or distinct cohorts. Missing target-specific metrics remain unavailable.</p></section>
<section class="panel" id="all-current-scores"><h2>2026 selected and retained candidates: all 77 preserved scorecards</h2><p>All 77 authenticated N079 scorecards remain preserved across 34 candidates. The 40 cards in the latest export exactly match 40 of these; 37 additional retained cards are kept here, including 15 at the two-hour horizon. There are zero newly scored 2026 cases in N082. Each row keeps its own target, exact horizon and cohort. A retained candidate's standalone replay does not recover its former role's unknown selection horizon. These are reconstructed descriptive scores with zero original-issue credit.</p><div class="scroll" tabindex="0" aria-label="All 77 preserved replay scorecards"><table class="roles"><thead><tr><th>Model</th><th>Target / horizon</th><th>Games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>Cohort digest</th></tr></thead><tbody id="all-current-cards"></tbody></table></div></section>
<section class="panel" id="prior-selections"><h2>Preserved N079 selections · separate dated roles</h2><p>The earlier 27 metric/horizon roles remain below at their original one- and two-hour horizons. Their aliases belong to N079 and must not be matched by label to the current snapshot. These historical selections are preserved evidence, not current champion promotion. The original <a href="season_review_n080.html">N079 all-game view</a> retains all earlier issue clocks and values.</p><div class="scroll" tabindex="0" aria-label="Prior N079 selected metric roles"><table class="roles"><thead><tr><th>Dated role</th><th>Prior alias</th><th>Horizon</th><th>2024</th><th>2025</th><th>Pooled selection</th><th>2026 exact-role replay</th></tr></thead><tbody id="prior-roles"></tbody></table></div></section>'''
    page=replace_once(page,'<section class="panel" id="current-monitor">',panels+'<section class="panel" id="current-monitor">')
    page=replace_once(page,'<a href="#replay-current">2026 replay leaders</a>','<a href="#replay-current">2026 replay leaders</a><a href="#new-science">New experiments</a><a href="#prior-selections">Prior selections</a>')
    js=r'''
byId('science-timing').textContent=run.new_science.total_verified_fit_minimum+' verified fits in '+run.new_science.scientific_stage_seconds.toFixed(3)+' seconds of scientific-stage time ('+run.new_science.scientific_stage_fits_per_hour.toFixed(1)+' fits/hour); whole-invocation rate '+run.new_science.invocation_fits_per_hour.toFixed(1)+' fits/hour. First optimizer began '+run.seconds_until_first_optimizer.toFixed(3)+' seconds after invocation. The parent spent '+run.new_science.post_science_parent_tail_seconds.toFixed(3)+' additional seconds after the scientific child. Raw-source migration alone took '+run.new_science.raw_source_migration_seconds.toFixed(3)+' seconds for '+run.new_science.raw_source_rows.toLocaleString('en-US')+' rows and '+run.new_science.raw_source_partitions.toLocaleString('en-US')+' persistent Parquet partitions. Completed migration and fits must be reused.';
const cpuFit=run.new_science.scientific_cpu_sample;byId('science-timing').textContent+=' A retained process-tree sample measured '+cpuFit.measured_process_tree_cores.toFixed(3)+' cores over '+cpuFit.measurement_seconds.toFixed(3)+' seconds at '+cpuFit.observed_at_utc+', with three genuine optimizer intervals active at its end. This sample includes other process-tree work and is not a sustained fitting rate.';
for(const row of run.new_science.matched_new_vs_preserved){const tr=document.createElement('tr');for(const item of [row.target+' / '+row.metric,row.model_aliases.join(' / '),formatMetric(row.value,row.metric),formatMetric(row.preserved_best_value,row.metric),formatMetric(row.improvement_over_preserved_best,row.metric),row.n+' games · 2024+2025 · '+row.horizon_seconds+'s; '+row.candidate_count+' new / '+row.preserved_candidate_count+' preserved'])tr.appendChild(textNode('td',item));byId('new-vs-preserved').appendChild(tr);}
for(const family of Object.keys(run.new_science.family_counts).sort()){const option=textNode('option',family);option.value=family;byId('science-family').appendChild(option);}
function renderScience(){const season=byId('science-season').value,target=byId('science-target').value,family=byId('science-family').value,rows=run.new_science.cards.filter(r=>(!season||String(r.season)===season)&&(!target||r.target===target)&&(!family||r.family===family));byId('science-cards').replaceChildren();for(const row of rows){const tr=document.createElement('tr');for(const item of [row.model_alias+' / '+row.family,row.season+' / '+row.target,row.comparison_horizon_seconds+'s / '+row.games,...['accuracy','log_loss','brier','mae','rmse','crps'].map(m=>formatMetric(row.metrics[m],m)),row.cohort_sha256.slice(0,12)])tr.appendChild(textNode('td',item));byId('science-cards').appendChild(tr);}byId('science-count').textContent=rows.length+' of 216 exact-cohort scorecards · 108 completed candidates';}
for(const id of ['science-season','science-target','science-family'])byId(id).addEventListener('change',renderScience);renderScience();
for(const row of run.selected_and_retained_2026_scorecards){const tr=document.createElement('tr');for(const item of [row.model_alias,row.target+' / '+row.comparison_horizon_seconds+'s',row.games,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(row.metrics[m],m)),row.cohort_sha256.slice(0,12)])tr.appendChild(textNode('td',item));byId('all-current-cards').appendChild(tr);}
for(const row of run.previous_selected_roles.roles){const card=run.previous_selected_roles.role_2026_scorecards.find(r=>r.role_id===row.role_id),tr=document.createElement('tr');for(const item of [row.label,'N079 / '+row.model_alias,row.comparison_horizon_seconds+'s',...[2024,2025].map(year=>{const c=row.season_metrics.find(x=>x.season===year);return formatMetric(c?.metrics?.[row.metric],row.metric)+' / '+(c?.games??0)+' games';}),formatMetric(row.selection_value,row.metric)+' / '+row.selection_games+' games',formatMetric(card?.metrics?.[row.metric],row.metric)+' / '+(card?.games??0)+' games'])tr.appendChild(textNode('td',item));byId('prior-roles').appendChild(tr);}
'''
    page=replace_once(page,'renderGames();renderLeaders();window.nflSelectedReview=',js+'renderGames();renderLeaders();window.nflSelectedReview=')
    return page


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name(FORECAST))
    parser.add_argument('--health',type=Path,default=Path(__file__).with_name(HEALTH))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('season_review_n083.html'))
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    page=render(args.input.read_bytes(),json.loads(args.health.read_bytes()))
    if args.check:
        if not args.output.is_file() or args.output.read_text()!=page:
            raise SystemExit('N083 review differs from authenticated saved outputs')
        print('N083 all-game review matches exact authenticated source bytes.')
    else:args.output.write_text(page)


if __name__=='__main__':main()
