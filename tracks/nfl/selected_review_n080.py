"""Render the authenticated N079 selected outputs without fitting or rescoring."""
import argparse
import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from selected_review_n073 import TEMPLATE

HEALTH='2026-11-12-n079-actual-n080-review.json'
FORECAST='selected_forecasts_n080.json'
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
    if health['new_fits'] != 0 or health['new_native_fits'] != 0 or health['new_meta_fits'] != 0 or health['owner_research_acceptance']:
        raise ValueError('N079_ZERO_NEW_FITS_MUST_REMAIN_VISIBLE')
    if health['new_n080_owner_science_claimed'] or health['complete_current_season_champion_replay']:
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


def render(raw,health):
    value=validate(raw,health)
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    data=data.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=TEMPLATE.replace('__SELECTED_DATA__',data)
    page=page.replace('selected_forecasts_n073.json',FORECAST)
    page=page.replace('<a href="#evidence">Evidence limits</a>', '<a href="#replay-current">2026 replay leaders</a><a href="#matched-markets">Markets</a><a href="#evidence">Evidence limits</a><a href="'+HEALTH+'" download>Metric evidence</a>')
    page=replace_once(page,'Latest owner execution: frozen research resumed','Actual N079: 84 minutes, zero new fits')
    page=replace_once(page,"'Original forecast-input source '+utc(game.source_observed_at_utc)","'Saved source observation '+utc(game.source_observed_at_utc)")
    page=replace_once(page,"utc(game.latest_schedule_observed_at_utc)","utc(game.source_observed_at_utc)")
    page=replace_once(page,"const state=game.current_source_coverage[provider.toLowerCase()];","const state={observation_status:'NO_ADMITTED_COMPARISON_IN_SELECTED_EXPORT'};")
    h=json.dumps(health,sort_keys=True,separators=(',',':'),allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=replace_once(page,"const run=data.latest_owner_execution,refresh=data.latest_source_refresh;","const run="+h+";")
    start=page.index("byId('owner-status').textContent=")
    end=page.index('renderGames();renderLeaders();window.nflSelectedReview=',start)
    js=r'''const availablePrimary=new Set(data.games.flatMap(g=>Object.values(g.targets).flatMap(t=>t.roles.filter(r=>r.current_forecast_available&&r.role_id.startsWith('primary_')).map(r=>r.role_id))));
byId('owner-status').textContent='N079 completed '+run.new_fits+' new fits ('+run.new_native_fits+' native / '+run.new_meta_fits+' meta) in '+(run.elapsed_seconds/60).toFixed(2)+' minutes. Owner research acceptance: false. '+run.unique_issue_events.toLocaleString('en-US')+' unique issue events across '+run.issued_games+' future games. Latest selected display: '+run.selected_public_rows+' rows for '+run.selected_public_games+' games. '+availablePrimary.size+' of '+data.counts.primary_metric_roles+' primary historical roles have current outputs. Authenticated 2026 replay metrics are now shown below; missing cohorts remain explicit. No rolling promotion or N080 owner-science result is claimed.';
byId('owner-elapsed').textContent='Main scientific child started '+(run.seconds_until_main_scientific_child/60).toFixed(2)+' minutes after invocation. '+run.reused_complete_batches+' completed batches reused; '+run.observed_concurrent_optimizer_calls+' observed concurrent optimizer calls. Sampled process-tree CPU mean '+run.observed_process_tree_mean_cores.toFixed(3)+' cores, peak '+run.observed_process_tree_peak_cores.toFixed(3)+'; short-lived workers between samples may be omitted. '+run.cache_hits+' cache hits / '+run.cache_misses+' misses; '+run.cache_byte_reuse_percent.toFixed(2)+'% bytes reused. '+run.new_paid_calls+' paid calls. Whole-instance compute estimate $'+run.compute_time_estimate_usd.toFixed(3)+'; not an AWS bill. '+run.unique_game_recipe_pairs+' game/recipe pairs and '+run.later_issue_events_on_existing_pairs+' later issues on existing pairs are not independent games.';
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
    section='''<section class="panel" id="current-monitor"><h2>2026 saved early snapshots: 15 games</h2><p class="note">135 rows represent 15 unique games × three saved combinations × three targets. These are timestamped early snapshots with independent durable pregame delivery and full source-publication clocks unproved. They are not a complete 136-game season score or current-champion replay, and cannot select or promote a model.</p><p>Scores below come from preserved full-precision owner scorecards. No public rounded forecast is rescored. The archived 77-game original-model and 119-game Kalshi panels remain separate in the <a href="CURRENT_MODEL_CARD.md">model card</a>.</p><div class="scroll" tabindex="0" aria-label="Saved early snapshot metrics"><table><thead><tr><th>Saved model</th><th>Target</th><th>Support / correct</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="early-scores"></tbody></table></div></section>'''
    page=replace_once(page,'<section class="panel" id="evidence">',section+'\n<section class="panel" id="evidence">')
    page=page.replace('<th scope="col">Support</th>','<th scope="col">Support</th><th scope="col">2026 exact-horizon replay / current issues</th>')
    page=page.replace("tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));body.appendChild(tr);", "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));const card=run.selected_2026_scorecards.find(c=>c.role_id===row.role_id),td=textNode('td',formatMetric(card?.metrics?.[row.metric],row.metric));if(card){td.appendChild(textNode('small',card.games+' scored / '+card.completed_games+' completed games; frozen replay'));td.appendChild(textNode('small',card.current_issued_games+' current issued games; no rolling promotion'));if(card.status!=='SCORED_FROZEN_REPLAY')td.appendChild(textNode('small',card.status.replaceAll('_',' ').toLowerCase()));}tr.appendChild(td);body.appendChild(tr);")
    former='<section class="panel" id="former-leaders"><h2>Former and rolling champions</h2><p>Original Torch AB remains the saved 557-game accuracy leader (388 correct). Original Torch B remains the saved log-loss leader (0.595426) and Brier leader (0.204637). Those original cohorts differ from the 569-game historical probability selections above; no cross-cohort ranking is valid.</p><p>These candidates remain preserved. Their fresh original runtime and complete current-season comparison are unresolved. The 18 exact former-role comparison gaps below preserve their missing original horizons. No independent rolling production promotion is established. Other metric-specific former roles remain explicit in the retained private registry.</p><p>Home/away score distributions, prediction intervals and current same-cutoff market values are unavailable in this selected export. Independent margin and total heads are not combined into an asserted coherent score distribution.</p></section>'
    page=replace_once(page,'<section class="panel" id="evidence">',former+'<section class="panel" id="evidence">')
    replay = '<section class="panel" id="replay-current"><h2>2026: measured leaders on the available replay cohort</h2><p class="note">Best among the displayed selected candidates at the identical target, horizon and game cohort. This is exposed descriptive monitoring, not fresh selection, original-issue performance or a rolling promotion. Each winner row has 119 scored games; point rows have 120. The saved census has 136 finals: 16 have archived vectors only at other actual horizons in this projection, and conditional winner scoring excludes one tie. Unplayed games remain unscored.</p><p>The one-hour and two-hour cohorts remain separate. Values come from saved full-precision owner scorecards, never rounded forecast rescoring. CRPS is unavailable where a complete earlier out-of-sample residual distribution is absent. The table above tracks the same historical selections through 2024, 2025 and 2026; this table answers which of those displayed candidates currently has the best descriptive metric.</p><div class="scroll" tabindex="0" aria-label="Current selected replay leaders"><table><thead><tr><th>Target</th><th>Metric</th><th>Horizon</th><th>Best selected model</th><th>Value</th><th>Support</th><th>Exact cohort digest</th></tr></thead><tbody id="replay-leaders"></tbody></table></div></section>'
    replay += '<section class="panel" id="other-horizons"><h2>Other archived horizons: separate standalone scores</h2><p>These selected-model replay aggregates retain their actual lead times: 14 games at 86,400 seconds, one at 4,738.345284 seconds and one at 170,544.720703 seconds. Across all actual horizons, some point replay is available for all 136 finals and conditional winner replay for 135 non-ties. This does not establish any one comparable 136-game selected-role score. The one-game groups are observations, not useful performance estimates. No horizon is invented or combined with another; no original-issue or promotion credit is given.</p><div class="scroll" tabindex="0" aria-label="Other actual horizon selected model scores"><table><thead><tr><th>Selected model</th><th>Target</th><th>Actual horizon</th><th>Games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="other-horizon-scores"></tbody></table></div></section>'
    replay += '<section class="panel" id="former-role-gaps"><h2>Preserved former roles: unresolved horizon comparisons</h2><p>All 18 unresolved former metric roles remain visible. A replay at an observed horizon does not recover the original selection horizon. No missing score is treated as zero or silently replaced by a later champion. The original Torch accuracy/log-loss/Brier records remain separately qualified above.</p><div class="scroll" tabindex="0" aria-label="Former metric role gaps"><table><thead><tr><th>Former role</th><th>Target</th><th>Metric</th><th>Original horizon</th><th>Comparable 2026 score</th></tr></thead><tbody id="former-roles"></tbody></table></div></section>'
    replay += '<section class="panel" id="matched-markets"><h2>2026 same-cutoff market comparisons</h2><p>No qualified comparison is admitted for this selected replay. The counts below are target-specific replay rows examined, not unique games or quote captures. Winner quotes require an authentic fresh equivalent cutoff; expected margin and total cannot be replaced by conditional threshold contracts. Earlier separately qualified saved venue panels remain in the model card.</p><div class="scroll" tabindex="0" aria-label="Current season market comparison coverage"><table><thead><tr><th>Provider</th><th>Target</th><th>Admitted comparisons</th><th>Examined denominator</th><th>Missing reason</th></tr></thead><tbody id="replay-markets"></tbody></table></div></section>'
    page=replace_once(page,'<section class="panel" id="evidence">',replay+'<section class="panel" id="evidence">')

    return page


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name(FORECAST))
    parser.add_argument('--health',type=Path,default=Path(__file__).with_name(HEALTH))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('season_review_n080.html'))
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    page=render(args.input.read_bytes(),json.loads(args.health.read_bytes()))
    if args.check:
        if not args.output.is_file() or args.output.read_text()!=page:
            raise SystemExit('N080 review differs from authenticated saved outputs')
        print('N080 all-game review matches exact authenticated source bytes.')
    else:args.output.write_text(page)


if __name__=='__main__':main()
