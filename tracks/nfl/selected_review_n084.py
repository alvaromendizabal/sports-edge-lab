"""Render authenticated selected NFL output and cohort-qualified aggregates offline."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from selected_review_n073 import TEMPLATE
from selected_review_n083 import replace_once

HEALTH = '2026-11-13-n083-actual-n084-review.json'
FORECAST = 'selected_forecasts_n084.json'
GROUPS = ('current_forecasts', 'earlier_saved_forward', 'prior_selected_reconstruction')


def _clock(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('N084_NAIVE_PUBLICATION_CLOCK')
    return parsed


def audit(value):
    games = value['games']
    if len({g['game_id'] for g in games}) != len(games):
        raise ValueError('N084_DUPLICATE_PUBLICATION_GAME')
    if value['counts']['schedule_games'] != len(games):
        raise ValueError('N084_PUBLICATION_DENOMINATOR_MISMATCH')
    cutoff = _clock(value['display_cutoff_utc'])
    result = dict(completed=0, upcoming=0, live_or_awaiting_final=0, tbd=0,
                  current_issued_rows=0, current_issued_games=0)
    for game in games:
        if game['completed_in_saved_census']:
            result['completed'] += 1
        elif game['official_time_tbd']:
            result['tbd'] += 1
        elif _clock(game['kickoff_utc']) <= cutoff:
            result['live_or_awaiting_final'] += 1
        else:
            result['upcoming'] += 1
        rows = [r for target in game['targets'].values() for r in target['current_forecasts']]
        result['current_issued_rows'] += len(rows)
        result['current_issued_games'] += bool(rows)
        for row in rows:
            if game['official_time_tbd'] or not row.get('original_issue_at_utc'):
                raise ValueError('N084_CURRENT_ISSUE_CLOCK_REQUIRED')
            issue = _clock(row['original_issue_at_utc'])
            if issue >= _clock(game['kickoff_utc']) or issue > cutoff:
                raise ValueError('N084_POSTKICKOFF_OR_FUTURE_CURRENT_ISSUE')
    if value['counts']['completed_games'] != result['completed']:
        raise ValueError('N084_PUBLICATION_FINAL_COUNT_MISMATCH')
    if value['counts']['current_selected_rows'] != result['current_issued_rows']:
        raise ValueError('N084_PUBLICATION_CURRENT_ROW_COUNT_MISMATCH')
    if value['counts']['current_selected_games'] != result['current_issued_games']:
        raise ValueError('N084_PUBLICATION_CURRENT_GAME_COUNT_MISMATCH')
    return result



def validate(raw, health):
    if hashlib.sha256(raw).hexdigest() != health['selected_forecasts_sha256']:
        raise ValueError('SELECTED_BYTES_CHANGED')
    if health['owner_return_sha256'] != 'be514bc5c2a488e21b043e88b557ee8f07a59d3f5df1a638d98ace1780afac17':
        raise ValueError('OWNER_RETURN_CHANGED')
    data = json.loads(raw)
    if data['schema'] != 'nfl.n075.rounded-selected-forecast-publication.v1' or data['sport'] != 'NFL':
        raise ValueError('SELECTED_SCHEMA_CHANGED')
    census = audit(data)
    if census != health['saved_census']:
        raise ValueError('CENSUS_CHANGED')
    games = data['games']
    if len(games) != 272 or len({g['game_id'] for g in games}) != len(games):
        raise ValueError('GAME_DENOMINATOR_CHANGED')
    if sum(g['completed_in_saved_census'] for g in games) != 137 or sum(g['official_time_tbd'] for g in games) != 24:
        raise ValueError('GAME_LIFECYCLE_CHANGED')
    current = []
    for game in games:
        if game['official_time_tbd'] and game['kickoff_utc'] is not None:
            raise ValueError('TBD_PLACEHOLDER')
        for target, panel in game['targets'].items():
            for row in panel['current_forecasts']:
                if game['completed_in_saved_census'] or game['official_time_tbd']:
                    raise ValueError('NONFORWARD_CURRENT_ISSUE')
                if row['target'] != target or row['evidence_kind'] != 'original_issued':
                    raise ValueError('ISSUE_CLASS_CHANGED')
                if not datetime.fromisoformat(row['model_completed_at_utc']) <= datetime.fromisoformat(row['original_issue_at_utc']) < datetime.fromisoformat(game['kickoff_utc']):
                    raise ValueError('ISSUE_CLOCK_CHANGED')
                current.append((game['game_id'], row))
            for row in panel['prior_selected_reconstruction']:
                if row['original_issue_at_utc'] is not None:
                    raise ValueError('RECONSTRUCTION_CANNOT_BECOME_ISSUE')
    if len(current) != 444 or len({g for g, r in current}) != 111:
        raise ValueError('CURRENT_ISSUE_DENOMINATOR_CHANGED')
    if (health['new_fits'], health['new_native_fits'], health['new_meta_fits']) != (376, 354, 22):
        raise ValueError('ACTUAL_FIT_COUNTS_CHANGED')
    if health['owner_research_acceptance'] or health['new_n084_owner_science_claimed'] or health['automatic_promotion'] or data['automatic_promotion']:
        raise ValueError('UNSUPPORTED_ACCEPTANCE_OR_PROMOTION')
    if health['new_qualified_market_comparison_cells'] != 0:
        raise ValueError('UNSUPPORTED_MARKET_COMPARISON')
    if len(health['all_historical_cards']) != 1320 or len(health['preserved_omitted_historical_cards']) != 48 or sum(c['scope']=='N082_PRESERVED_OMITTED_FROM_N083_CURRENT_TABLE' for c in health['all_historical_cards']) != 48:
        raise ValueError('HISTORICAL_LEDGER_PRESERVATION_CHANGED')
    if len(health['historical_cards']) != 120 or len({r['model_alias'] for r in health['historical_cards']}) != 60:
        raise ValueError('HISTORICAL_EXPERIMENTS_INCOMPLETE')
    for row in health['historical_cards']:
        if row['season'] not in (2024, 2025) or row['comparison_horizon_seconds'] != 3600 or row.get('promotion_authorized'):
            raise ValueError('HISTORICAL_COHORT_CHANGED')
    if len(health['original_issue_cards']) != 87 or any(c['current_season_selection_allowed'] or c['exact_T1_accuracy_claimed'] for c in health['original_issue_cards']):
        raise ValueError('ORIGINAL_ISSUE_SCOPE_CHANGED')
    if len(health['legacy_cards']) != 333 or any(c['new_model_fits'] or c['new_frozen_policy_retraining'] or c['frozen_champion_selection_eligible'] for c in health['legacy_cards']):
        raise ValueError('LEGACY_CREDIT_OR_RETENTION_CHANGED')
    if len(health['preserved_cards']) != 77 or len(health['preserved_leaders']) != 35:
        raise ValueError('FORMER_SCORECARDS_DROPPED')
    if len(health['monitor_cards']) != health['monitor_scorecard_count']:
        raise ValueError('MONITOR_CARDS_INCOMPLETE')
    for row in health['monitor_cards']:
        if row['season'] != 2026 or row.get('original_issue_credit', 0) or row.get('promotion_authorized', False):
            raise ValueError('MONITOR_ISSUE_OR_PROMOTION_CREDIT')
    for key in ('monitor_cards', 'historical_cards', 'all_historical_cards', 'preserved_cards'):
        cards = health[key]
        if len({(c['model_alias'], c['season'], c['target'], c['comparison_horizon_seconds'], c['cohort_sha256']) for c in cards}) != len(cards):
            raise ValueError('DUPLICATE_SCORECARD')
    all_cards = {}
    for card in health['monitor_cards'] + health['selected_2026_scorecards'] + health['mapped_preserved_cards']:
        key = (card['model_alias'], card['target'], card['comparison_horizon_seconds'], card['cohort_sha256'])
        if key in all_cards and all_cards[key]['metrics'] != card['metrics']:
            raise ValueError('SAME_COHORT_METRICS_CHANGED')
        all_cards[key] = card
    for leaders, source in [(health['monitor_leaders'],health['monitor_cards']), (health['all_2026_leaders'],list(all_cards.values()))]:
        for row in leaders:
            cards = [c for c in source if (c['target'], c['comparison_horizon_seconds'], c['cohort_sha256']) == (row['target'], row['comparison_horizon_seconds'], row['cohort_sha256']) and row['metric'] in c['metrics']]
            if not cards or row['value'] != (max if row['metric'] in ('accuracy','roc_auc') else min)(c['metrics'][row['metric']] for c in cards):
                raise ValueError('LEADER_COHORT_CHANGED')
            if row['games'] != cards[0]['games'] or row['candidates'] != len(cards) or set(row['model_aliases']) != {c['model_alias'] for c in cards if c['metrics'][row['metric']] == row['value']}:
                raise ValueError('LEADER_IDENTITY_CHANGED')
    return data


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')


def render(raw, health):
    value = validate(raw, health)
    page = TEMPLATE.replace('__SELECTED_DATA__', encode(value)).replace('selected_forecasts_n073.json', FORECAST)
    page = replace_once(page, 'no metric is recomputed from rounded display values', 'no headline aggregate is recomputed from rounded display values')
    page = replace_once(page, 'Current-season outcomes did not select the displayed historical champions.', 'Current-season outcomes did not select the displayed historical champions. Per-game display errors use rounded forecast values and are explicitly approximate; headline metrics use saved full-precision aggregates.')
    page = replace_once(page, "'Original forecast-input source '+utc(game.source_observed_at_utc)", "'Saved source observation '+utc(game.source_observed_at_utc)")
    page = replace_once(page, 'utc(game.latest_schedule_observed_at_utc)', 'utc(game.source_observed_at_utc)')
    page = replace_once(page, 'const state=game.current_source_coverage[provider.toLowerCase()];', "const state={observation_status:'NO_ADMITTED_COMPARISON_IN_SELECTED_EXPORT'};")
    page = replace_once(page, "coverage.appendChild(textNode('small','Latest schedule observation '+utc(game.source_observed_at_utc)));", "coverage.appendChild(textNode('small','Separate schedule-refresh clock unavailable in this export.'));coverage.appendChild(textNode('small','Expected home/away score, interval and cover probability: unavailable without an admitted joint distribution and equivalent line.'));")
    page = replace_once(page, "block.appendChild(textNode('small',row.model_alias));", "block.appendChild(textNode('small',row.model_alias));if(game.completed_in_saved_census&&Number.isFinite(game.home_score)&&Number.isFinite(game.away_score)){if(target==='win'){const winner=game.home_score===game.away_score?'Tie':game.home_score>game.away_score?game.home_team:game.away_team;block.appendChild(textNode('small',winner==='Tie'?'Actual: tie; conditional winner score excluded':'Pick '+(row.predicted_winner===winner?'matched':'missed')+' the final winner'));}else{const actual=target==='margin'?game.home_score-game.away_score:game.home_score+game.away_score,pred=target==='margin'?row.home_point_margin:row.total_points;block.appendChild(textNode('small','Actual '+actual+'; approximate display absolute error '+Math.abs(pred-actual).toFixed(1)+' points (rounded forecast only)'));}}")

    page = replace_once(page, 'const run=data.latest_owner_execution,refresh=data.latest_source_refresh;', 'const run=' + encode(health) + ';')
    start = page.index("byId('owner-status').textContent=")
    end = page.index('renderGames();renderLeaders();window.nflSelectedReview=', start)
    page = page[:start] + JS + page[end:]
    page = page.replace('<th scope="col">Support</th>', '<th scope="col">Support</th><th scope="col">2026 same-role replay</th>')
    page = replace_once(page, "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));body.appendChild(tr);", "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));const card=run.selected_2026_scorecards.find(c=>c.current_role_ids.includes(row.role_id)&&c.comparison_horizon_seconds===row.comparison_horizon_seconds),td=textNode('td',formatMetric(card?.metrics?.[row.metric],row.metric));td.appendChild(textNode('small',card?card.games+' scored / 137 completed games; frozen replay':'Matched replay scorecard unavailable'));tr.appendChild(td);body.appendChild(tr);")
    page = replace_once(page, '<option value="future">Upcoming in saved census</option>', '<option value="future">Upcoming · confirmed time</option><option value="live">Live / awaiting final</option>')
    page = replace_once(page, "const roleMap=new Map(data.selected_historical_roles.map(r=>[r.role_id,r]));", "const roleMap=new Map(data.selected_historical_roles.map(r=>[r.role_id,r]));function gameState(g){if(g.completed_in_saved_census)return 'completed';if(g.official_time_tbd)return 'tbd';return new Date(g.kickoff_utc)<=new Date(data.display_cutoff_utc)?'live':'future';}")
    page = replace_once(page, "(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census)", "gameState(g)===status")
    page = replace_once(page, ":'Unplayed in saved census'", ":gameState(game)==='live'?'Live or awaiting final in saved census':gameState(game)==='tbd'?'Kickoff time unconfirmed':'Upcoming in saved census'")
    page = page.replace('<option value="7200">Two hours before kickoff</option>', '')
    cutoff = datetime.fromisoformat(value['display_cutoff_utc']).astimezone(ZoneInfo('America/Los_Angeles'))
    banner = '<section class="panel" id="latest-attempt"><h2>Actual N083 · 376 completed fits</h2><p class="note"><strong>354 native + 22 meta fits committed. Owner acceptance remains incomplete.</strong> All 60 new historical candidates completed. The separate 2026 monitor performed 166 new fits and reused two. Preserved experiments and negative findings stay visible; no automatic production promotion.</p><p>Saved cutoff: <strong>' + value['display_cutoff_utc'] + '</strong> (' + cutoff.strftime('%B %d, %Y at %H:%M:%S Pacific (%Z)') + '). All <strong>272 games: 137 finals, 111 confirmed upcoming, 24 kickoff TBD</strong>. Washington at New York is now final, 24–21; its earlier pregame evidence retains the original clocks. Current issues lead kickoff by 55.66 hours to 52.77 days; historical one-hour selection labels do not turn them into final-hour issues.</p><p>These are N083 owner results. N084 code preparation is separate and earns no new owner-fit credit. <a href="season_review_n083.html">Previous N082 snapshot</a> · <a href="season_review_n080.html">Preserved N079 snapshot</a> · <a href="' + HEALTH + '">Aggregate evidence</a></p></section>'
    page = replace_once(page, '<main class="wrap">', '<main class="wrap">' + banner)
    page = replace_once(page, 'Latest owner execution: frozen research resumed', 'Execution, reuse and remaining work')
    page = replace_once(page, '<th>New observations</th>', '<th>Admitted comparisons</th>')
    page = replace_once(page, '<section class="panel" id="evidence">', PANELS + '<section class="panel" id="evidence">')
    page = replace_once(page, '<a href="#evidence">Evidence limits</a>', '<a href="#monitor">2026 comparison</a><a href="#experiments">New science</a><a href="#preserved">Former models</a><a href="#evidence">Evidence limits</a>')
    return page


PANELS = '''
<section class="panel" id="monitor"><h2>2026 monitor: best on each exact cohort</h2><p class="note">Descriptive frozen replay, not original issues or current-season champion selection. The same target, horizon and exact game cohort are compared. Different cohorts are not ranked together. Missing archived vectors remain missing; the full season census is not a claim that every candidate has 137 scored games.</p><p id="monitor-status"></p><h3>All recovered comparable current-season cards</h3><p>Exact-cohort comparison across the retrieved selected, registered-monitor and preserved sources. The same recipe and cohort are counted once. Missing candidates and incomparable horizons are excluded from each local comparison, not declared inferior.</p><div class="scroll" tabindex="0" aria-label="All recovered current-season cohort leaders"><table><thead><tr><th>Target / metric</th><th>Horizon</th><th>Best alias</th><th>Value</th><th>Games / candidates</th><th>Cohort</th></tr></thead><tbody id="all-cohort-leaders"></tbody></table></div><h3>Registered monitor lane</h3><div class="scroll" tabindex="0" aria-label="2026 exact cohort leaders"><table><thead><tr><th>Target / metric</th><th>Horizon</th><th>Best alias</th><th>Value</th><th>Games / candidates</th><th>Cohort</th></tr></thead><tbody id="monitor-leaders"></tbody></table></div><details><summary>Every saved 2026 monitoring scorecard</summary><div class="scroll" tabindex="0" aria-label="All 2026 monitor scorecards"><table><thead><tr><th>Model</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>ECE</th><th>ROC-AUC</th><th>Cohort</th></tr></thead><tbody id="monitor-cards"></tbody></table></div></details><details><summary>Every current selected-role replay scorecard</summary><div class="scroll" tabindex="0" aria-label="Current selected role scorecards"><table><thead><tr><th>Model</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>ECE</th><th>ROC-AUC</th><th>Cohort</th></tr></thead><tbody id="selected-cards"></tbody></table></div></details><p>No independent rolling production promotion is established. The historical role selections above remain distinct from descriptive 2026 winners.</p></section>
<section class="panel" id="experiments"><h2>60 completed historical candidates · 120 annual scorecards</h2><p>New source-supported interaction candidates completed frozen inner 2023 fits and separate 2024/2025 evaluations. These are development-exposed results; 2026 outcomes do not select the historical champion. Coarse families and aggregate scores are public; active recipes and individual candidate prediction grids remain private.</p><p id="experiment-outcome"></p><div class="toolbar"><label>Season<select id="science-season"><option value="">Both seasons</option><option value="2024">2024</option><option value="2025">2025</option></select></label><label>Target<select id="science-target"><option value="">All targets</option><option value="win">Winner</option><option value="margin">Margin</option><option value="total">Total</option></select></label><label>Family<select id="science-family"><option value="">All families</option></select></label></div><p id="science-count" role="status"></p><div class="scroll" tabindex="0" aria-label="New historical scorecards"><table><thead><tr><th>Model / family</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>ECE</th><th>ROC-AUC</th><th>Cohort</th></tr></thead><tbody id="science-cards"></tbody></table></div></section>
<section class="panel" id="historical-ledger"><h2>Complete recovered historical ledger · 1,320 cards</h2><p>The N083 current table supplies 1,272 cards. Another 48 authentic N082 cards were omitted there and are restored here with their original values and an explicit source label. These are frozen 2024/2025 development evaluations, not new original issues. Recovery earns no new model-fit credit. Earlier dated public aliases and scorecards remain available in their unchanged snapshots.</p><div class="toolbar"><label>Model alias<input id="history-search" type="search" placeholder="e.g. Selected model 4"></label><label>Season<select id="history-season"><option value="">Both seasons</option><option>2024</option><option>2025</option></select></label><label>Target<select id="history-target"><option value="">All targets</option><option value="win">Winner</option><option value="margin">Margin</option><option value="total">Total</option></select></label></div><p id="history-count" role="status"></p><details><summary>Inspect all current and restored historical cards</summary><div class="scroll" tabindex="0" aria-label="Complete recovered historical scorecards"><table><thead><tr><th>Model</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>ECE</th><th>ROC-AUC</th><th>Cohort</th><th>Saved source</th></tr></thead><tbody id="history-cards"></tbody></table></div></details></section>
<section class="panel" id="preserved"><h2>Former and prior evidence remains visible</h2><p>All 77 N079 scorecards remain at their original horizons and cohorts, separately dated. They are not new N083 evaluations. The <a href="season_review_n083.html#new-science">108 N082 candidates and 216 evaluations</a> remain unchanged. The original Torch accuracy/log-loss/Brier records remain separately qualified in the <a href="CURRENT_MODEL_CARD.md">model card</a>; no cross-cohort winner is asserted.</p><p>All 18 former metric-role horizon gaps remain unresolved; a standalone replay does not recover an unknown original selection horizon. Full original-runtime reconstruction was blocked during N083. No missing champion is silently replaced.</p><details><summary>35 preserved N079 cohort-specific leaders</summary><div class="scroll" tabindex="0" aria-label="Preserved N079 leaders"><table><thead><tr><th>Target / metric</th><th>Horizon</th><th>Dated alias</th><th>Value</th><th>Games / candidates</th></tr></thead><tbody id="preserved-leaders"></tbody></table></div></details><div class="scroll" tabindex="0" aria-label="77 preserved former scorecards"><table><thead><tr><th>Dated model</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>CRPS</th><th>ECE</th><th>ROC-AUC</th><th>Cohort</th></tr></thead><tbody id="preserved-cards"></tbody></table></div></section>
<section class="panel" id="original-monitor"><h2>Originally issued forecasts · new outcome monitoring</h2><p>The newly final Washington–New York result produced 87 additional scoring commits; 492 prior evaluations were reused. Across the 579 eligible evaluation records there are 15 unique games. The 87 aggregate groups below each cover 2–15 games and retain their actual origin/horizon class. These are saved original issues, distinct from frozen reconstructed forecasts. No new fit or forecast issue is credited to this scoring.</p><p class="note">Source-closure and aggregate receipts are authenticated; this publication did not refetch and recompute every offloaded original issue body. Per-group exact game-cohort hashes are absent from the saved aggregates. Consequently these groups are not ranked as a global champion, and no exact final-hour or independently validated long-horizon performance is asserted. Zero true-class probability remains an explicit infinite-log-loss finding where recorded.</p><details><summary>All 87 original-issue aggregate groups</summary><div class="scroll" tabindex="0" aria-label="Original issue outcome scorecards"><table><thead><tr><th>Group / owner</th><th>Target / games</th><th>Evidence / horizon</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>Loss qualification</th></tr></thead><tbody id="original-cards"></tbody></table></div></details></section>
<section class="panel" id="legacy"><h2>333 recovered legacy scorecards · separately qualified</h2><p>Older N026 and N022 studies remain visible with their exact saved period, target, cohort and evidence class. These include 324 reconstructed scorecards and nine original-forward scorecards at variable issue horizons. They receive zero new fit, frozen-policy retraining or promotion credit. Earlier study policies are not silently relabeled as the current frozen evaluation; incompatible seasons, source availability, cohorts or horizons are not pooled. Nine preserved pooled cards lack a saved cohort digest and receive no matched ranking claim.</p><details><summary>Inspect all recovered legacy aggregates</summary><div class="scroll" tabindex="0" aria-label="Recovered legacy scorecards"><table><thead><tr><th>Dated alias</th><th>Period / target</th><th>Evidence / horizon</th><th>Games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>Cohort</th></tr></thead><tbody id="legacy-cards"></tbody></table></div></details></section>
<section class="panel" id="markets"><h2>DraftKings, Kalshi and Polymarket</h2><p>No qualified same-cutoff comparison is admitted for the selected 2026 replay. New source observations do not establish earlier historical quotes. A threshold line is not an expected point total or margin. Existing qualified historical comparisons remain separately dated in the model card. Missing quote clocks, settlement equivalence and source rights are explicit limitations; no market win is inferred.</p><div class="scroll" tabindex="0" aria-label="Provider comparison coverage"><table><thead><tr><th>Provider</th><th>Admitted cells</th><th>Scope / missingness</th></tr></thead><tbody id="market-cells"></tbody></table></div><p>Home/away expected-score distributions, coherent intervals and missing distribution metrics are unavailable in this selected export; independently selected margin and total heads are not combined into an asserted coherent score forecast.</p></section>
'''

JS = r'''
byId('owner-status').textContent=run.new_fits+' verified fits ('+run.new_native_fits+' native / '+run.new_meta_fits+' meta); '+run.unique_issue_events+' unique immutable issue events across '+run.issued_games+' games. Latest selected display: 444 rows for 111 upcoming games. Owner acceptance: false.';
byId('owner-elapsed').textContent=run.performance_text;
for(const gap of run.source_gaps)byId('source-gaps').appendChild(textNode('li',gap));
for(const provider of ['DraftKings','Kalshi','Polymarket']){for(const id of ['latest-sources','market-cells']){const tr=document.createElement('tr');for(const v of [provider,'0 qualified selected-replay comparison cells','No authenticated equivalent same-cutoff comparison in this export'])tr.appendChild(textNode('td',v));byId(id).appendChild(tr);}}
byId('monitor-status').textContent=run.monitor_text;
byId('experiment-outcome').textContent=run.experiment_text;
function cardRow(row){const tr=document.createElement('tr');for(const item of [row.model_alias+(row.family?' / '+row.family:''),row.season+' / '+row.target,row.comparison_horizon_seconds+'s / '+row.games,...['accuracy','log_loss','brier','mae','rmse','crps','ece','roc_auc'].map(m=>formatMetric(row.metrics[m],m)),row.cohort_sha256.slice(0,12)])tr.appendChild(textNode('td',item));return tr;}
for(const [id,rows] of [['monitor-leaders',run.monitor_leaders],['all-cohort-leaders',run.all_2026_leaders]])for(const row of rows){const tr=document.createElement('tr');for(const item of [row.target+' / '+row.metric,row.comparison_horizon_seconds+'s',row.model_aliases.join(' / '),formatMetric(row.value,row.metric),row.games+' / '+row.candidates,row.cohort_sha256.slice(0,12)])tr.appendChild(textNode('td',item));byId(id).appendChild(tr);}
for(const row of run.selected_2026_scorecards)byId('selected-cards').appendChild(cardRow(row));
for(const row of run.monitor_cards)byId('monitor-cards').appendChild(cardRow(row));
for(const row of run.preserved_leaders){const tr=document.createElement('tr');for(const item of [row.target+' / '+row.metric,row.comparison_horizon_seconds+'s',row.model_aliases.join(' / '),formatMetric(row.value,row.metric),row.games+' / '+row.selected_candidates_compared])tr.appendChild(textNode('td',item));byId('preserved-leaders').appendChild(tr);}
for(const row of run.preserved_cards)byId('preserved-cards').appendChild(cardRow(row));
for(const row of run.original_issue_cards){const tr=document.createElement('tr');for(const v of [row.group_alias+' / '+row.owner_cycle,row.target+' / '+row.games,row.classification+' / '+row.horizon_class,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(row.metrics[m],m)),row.log_loss_status||'Target-specific loss; exact cohort digest unavailable'])tr.appendChild(textNode('td',v));byId('original-cards').appendChild(tr);}
for(const row of run.legacy_cards){const tr=document.createElement('tr');for(const v of [row.model_alias,row.period+' / '+row.target,row.evidence_class+' / '+row.horizon,row.games,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(row.metrics[m],m)),row.cohort_sha256?row.cohort_sha256.slice(0,12):'Unavailable; no matched ranking'])tr.appendChild(textNode('td',v));byId('legacy-cards').appendChild(tr);}
function renderHistory(){const q=byId('history-search').value.trim().toLowerCase(),season=byId('history-season').value,target=byId('history-target').value,rows=run.all_historical_cards.filter(r=>(!q||r.model_alias.toLowerCase().includes(q))&&(!season||String(r.season)===season)&&(!target||r.target===target));byId('history-cards').replaceChildren();for(const r of rows){const tr=cardRow(r);tr.appendChild(textNode('td',r.scope==='N082_PRESERVED_OMITTED_FROM_N083_CURRENT_TABLE'?'Preserved N082; omitted in N083':'N083 saved table'));byId('history-cards').appendChild(tr);}byId('history-count').textContent=rows.length+' of 1320 preserved historical cards';}byId('history-search').addEventListener('input',renderHistory);for(const id of ['history-season','history-target'])byId(id).addEventListener('change',renderHistory);renderHistory();
for(const family of [...new Set(run.historical_cards.map(r=>r.family))].sort()){const o=textNode('option',family);o.value=family;byId('science-family').appendChild(o);}
function renderScience(){const season=byId('science-season').value,target=byId('science-target').value,family=byId('science-family').value,rows=run.historical_cards.filter(r=>(!season||String(r.season)===season)&&(!target||r.target===target)&&(!family||r.family===family));byId('science-cards').replaceChildren();for(const r of rows)byId('science-cards').appendChild(cardRow(r));byId('science-count').textContent=rows.length+' of '+run.historical_cards.length+' exact-cohort annual scorecards';}
for(const id of ['science-season','science-target','science-family'])byId(id).addEventListener('change',renderScience);renderScience();
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    root=Path(__file__).parent;page=render((root/FORECAST).read_bytes(),json.loads((root/HEALTH).read_bytes()));output=root/'season_review_n084.html'
    if args.check:
        if output.read_text()!=page:raise SystemExit('N084 page differs from authenticated aggregates')
        print('N084 all-game page matches authenticated saved aggregates.')
    else:output.write_text(page)

if __name__=='__main__':main()
