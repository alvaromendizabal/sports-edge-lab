"""Render the authenticated N076 selected outputs without fitting or rescoring."""
import argparse
import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from selected_review_n073 import TEMPLATE

HEALTH='2026-11-12-n076-actual-n077-review.json'
FORECAST='selected_forecasts_n077.json'
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
    page=replace_once(page,'Latest owner execution: frozen research resumed','Actual N076: new forecasts, incomplete champion replay')
    page=replace_once(page,"'Original forecast-input source '+utc(game.source_observed_at_utc)","'Saved source observation '+utc(game.source_observed_at_utc)")
    page=replace_once(page,"utc(game.latest_schedule_observed_at_utc)","utc(game.source_observed_at_utc)")
    page=replace_once(page,"const state=game.current_source_coverage[provider.toLowerCase()];","const state={observation_status:'NO_ADMITTED_COMPARISON_IN_SELECTED_EXPORT'};")
    h=json.dumps(health,sort_keys=True,separators=(',',':'),allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    page=replace_once(page,"const run=data.latest_owner_execution,refresh=data.latest_source_refresh;","const run="+h+";")
    start=page.index("byId('owner-status').textContent=")
    end=page.index('renderGames();renderLeaders();window.nflSelectedReview=',start)
    js=r'''byId('owner-status').textContent='N076 completed '+run.new_fits+' new fits ('+run.new_native_fits+' native / '+run.new_meta_fits+' meta) and '+run.unique_issue_events.toLocaleString('en-US')+' unique issue events across '+run.issued_games+' future games. Latest selected display: '+run.selected_public_rows+' rows for '+run.selected_public_games+' games. Current-season champion replay remains incomplete; no independent promotion.';
byId('owner-elapsed').textContent='Owner elapsed '+run.elapsed_seconds.toFixed(3)+' seconds. '+run.unique_game_recipe_pairs+' game/recipe pairs; '+run.later_issue_events_on_existing_pairs+' later issue events on existing pairs. '+run.unmapped_nonselected_latest_rows_not_published+' latest nonselected rows are excluded from this selected-role view. Whole-instance compute estimate $'+run.compute_time_estimate_usd.toFixed(3)+'; not an AWS bill.';
for(const provider of run.provider_coverage){const tr=document.createElement('tr');for(const item of [provider.provider,provider.captured_winner_rows+' captured winner rows across '+provider.captured_games+' games',provider.qualified_comparison_cells+' qualified comparison cells. '+provider.reason])tr.appendChild(textNode('td',item));byId('latest-sources').appendChild(tr);}
const schedule=document.createElement('tr');for(const item of ['Schedule',data.counts.schedule_games+' games; '+data.counts.completed_games+' completed; '+data.counts.official_time_tbd_games+' kickoff TBD','Updated saved census; missing feature refreshes remain explicit.'])schedule.appendChild(textNode('td',item));byId('latest-sources').appendChild(schedule);
for(const gap of run.source_gaps)byId('source-gaps').appendChild(textNode('li',gap));
for(const row of run.forward_monitor_scorecards){const tr=document.createElement('tr');const metrics=row.target==='win'?[row.correct+'/'+row.games,(100*row.accuracy).toFixed(2)+'%',row.log_loss.toFixed(6),row.brier.toFixed(6),'—','—']:[row.games+' games','—','—','—',row.mae.toFixed(3),row.rmse.toFixed(3)];for(const item of [row.model_alias,row.target,...metrics])tr.appendChild(textNode('td',item));byId('early-scores').appendChild(tr);}
'''
    page=page[:start]+js+page[end:]
    section='''<section class="panel" id="current-monitor"><h2>2026 saved early snapshots: 15 games</h2><p class="note">135 rows represent 15 unique games × three saved combinations × three targets. These are timestamped early snapshots with independent durable pregame delivery and full source-publication clocks unproved. They are not a complete 136-game season score or current-champion replay, and cannot select or promote a model.</p><p>Scores below come from preserved full-precision owner scorecards. No public rounded forecast is rescored. The archived 77-game original-model and 119-game Kalshi panels remain separate in the <a href="CURRENT_MODEL_CARD.md">model card</a>.</p><div class="scroll" tabindex="0" aria-label="Saved early snapshot metrics"><table><thead><tr><th>Saved model</th><th>Target</th><th>Support / correct</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="early-scores"></tbody></table></div></section>'''
    page=replace_once(page,'<section class="panel" id="evidence">',section+'\n<section class="panel" id="evidence">')
    return page


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name(FORECAST))
    parser.add_argument('--health',type=Path,default=Path(__file__).with_name(HEALTH))
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('season_review_n077.html'))
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    page=render(args.input.read_bytes(),json.loads(args.health.read_bytes()))
    if args.check:
        if not args.output.is_file() or args.output.read_text()!=page:
            raise SystemExit('N077 review differs from authenticated saved outputs')
        print('N077 all-game review matches exact authenticated source bytes.')
    else:args.output.write_text(page)


if __name__=='__main__':main()
