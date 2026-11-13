from datetime import datetime
"""Offline all-game selected-role research view; no private arrays or model work."""
import argparse
import json
from pathlib import Path

SCHEMA='nfl.n075.rounded-selected-forecast-publication.v1'


def _old_render(value):
    if value.get('schema')!=SCHEMA or value.get('sport')!='NFL':
        raise ValueError('SELECTED_REVIEW_SCHEMA_REQUIRED')
    if len(value['games'])!=value['counts']['schedule_games']:
        raise ValueError('SELECTED_REVIEW_DENOMINATOR_MISMATCH')
    if len({g['game_id']for g in value['games']})!=len(value['games']):
        raise ValueError('SELECTED_REVIEW_DUPLICATE_GAME')
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    raw=raw.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    return TEMPLATE.replace('__SELECTED_DATA__',raw)


TEMPLATE=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NFL season research · Sports Edge Lab</title>
<style>
:root{color-scheme:light;--ink:#14382f;--muted:#52645e;--line:#dce5df;--green:#176346;--pale:#eef5ef;--amber:#765116}
*{box-sizing:border-box}body{margin:0;background:#f6f8f4;color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--green);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}button,input,select{font:inherit}button,a,input,select,summary{touch-action:manipulation}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #568fce;outline-offset:3px}
.skip{position:absolute;left:16px;top:-70px;background:white;padding:12px;z-index:9}.skip:focus{top:10px}
header{background:#123a2f;color:white;border-bottom:6px solid #b5d8a5}header .wrap{padding-top:38px;padding-bottom:34px}.wrap{max-width:1440px;margin:auto;padding:24px 32px}.brand{letter-spacing:.15em;font-size:12px;font-weight:700;margin:0 0 17px}.headrow{display:flex;gap:24px;align-items:flex-start;justify-content:space-between}h1{font-size:clamp(30px,4vw,48px);line-height:1.12;letter-spacing:-.03em;margin:0 0 15px;max-width:900px}header p{max-width:900px;color:#dfece1}header a{color:#e6f6c6}.badge{white-space:nowrap;background:#d9edc5;color:#183e2c;border-radius:20px;padding:8px 14px;font-size:12px;font-weight:700}nav{display:flex;gap:22px;flex-wrap:wrap;margin-top:23px;font-size:13px}
h2{font-size:25px;letter-spacing:-.025em;line-height:1.2;margin:0 0 11px}h3{font-size:16px;margin:0 0 7px}p{margin:0 0 13px}.muted,small{color:var(--muted)}small{display:block;font-size:12px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 22px}.stat{background:white;border:1px solid var(--line);border-radius:11px;padding:21px}.stat b{display:block;font-size:34px;line-height:1.15;letter-spacing:-.04em}.stat span{font-size:12px;color:var(--muted)}.note{background:#fff7e7;border-left:4px solid #b78a3e;padding:16px 20px;border-radius:0 8px 8px 0}.panel{background:white;border:1px solid var(--line);border-radius:13px;padding:25px;margin:25px 0}.sectionhead{display:flex;gap:20px;justify-content:space-between;align-items:flex-start}.count{font-weight:650;margin:14px 0}.toolbar{display:grid;grid-template-columns:minmax(190px,2fr) repeat(3,minmax(120px,1fr));gap:12px;margin-top:22px}label{display:block;font-size:12px;font-weight:650}input,select{display:block;width:100%;padding:10px 12px;margin-top:5px;border:1px solid #9dad9f;border-radius:6px;color:var(--ink);background:white;min-height:44px}button{cursor:pointer;border:1px solid var(--green);color:var(--green);background:white;padding:9px 15px;border-radius:6px;min-height:44px;white-space:nowrap}button:hover{background:var(--pale)}.scroll{overflow:auto;border:1px solid var(--line);border-radius:8px;max-height:760px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{background:#eaf2eb;position:sticky;top:0;z-index:1;font-size:11px;text-transform:uppercase;letter-spacing:.035em}tbody tr:last-child td{border-bottom:0}.games{min-width:1080px}.games th:first-child{min-width:180px}.games th:not(:first-child){min-width:180px}.game-title{font-size:16px;font-weight:750;margin-bottom:5px}.pill{display:inline-block;font-size:10px;font-weight:700;line-height:1.25;padding:4px 6px;border-radius:4px;background:var(--pale);margin:0 0 5px}.pill.replay{background:#f5ebdc;color:#755023}.pill.early{background:#edf0fa;color:#364f83}.forecast{padding:7px 0;border-bottom:1px dotted var(--line)}.forecast:last-child{border-bottom:0}.number{font-size:17px;font-weight:750;font-variant-numeric:tabular-nums}.forecast small{font-size:10px;max-width:230px;overflow-wrap:anywhere}.missing{color:var(--amber);font-size:12px}.sources{margin-top:10px;font-size:11px;color:var(--muted)}details{margin:10px 0}summary{cursor:pointer;font-weight:600}.legend{display:flex;gap:16px;flex-wrap:wrap;margin:15px 0;font-size:12px}.footgrid{display:grid;grid-template-columns:1fr 1fr;gap:26px}.roles{min-width:750px}.roles td:nth-child(n+3){font-variant-numeric:tabular-nums}.empty{padding:35px;text-align:center;color:var(--muted)}footer{padding:20px 0;color:var(--muted);font-size:12px}code{background:var(--pale);padding:2px 4px;border-radius:3px;overflow-wrap:anywhere}.qualified{color:#755023}
@media(max-width:760px){.wrap{padding:22px 16px}.headrow,.sectionhead{display:block}.badge{display:inline-block;margin-top:8px}.stats{grid-template-columns:1fr 1fr;gap:10px}.stat{padding:16px}.stat b{font-size:29px}.panel{padding:18px 14px}.toolbar{grid-template-columns:1fr 1fr}.toolbar label:first-child{grid-column:1/-1}.footgrid{grid-template-columns:1fr}.sectionhead button{margin-top:12px}nav{gap:16px}th,td{padding:11px}.scroll{max-height:650px}}
@media print{header{background:white;color:var(--ink)}header p,header a{color:var(--ink)}.toolbar,button,nav{display:none}.scroll{max-height:none;overflow:visible}.wrap{padding:16px}.panel{break-inside:avoid}.games{font-size:9px;min-width:0}th{position:static}.forecast small{font-size:8px}.number{font-size:12px}}
</style></head><body><a class="skip" href="#season">Skip to season games</a>
<header><div class="wrap"><p class="brand">SPORTS EDGE LAB / NFL</p><div class="headrow"><div><h1>Every game. Selected forecasts.<br>Evidence that stays intact.</h1><p>A complete season view of preserved winner probabilities, point margins and totals, with separate historical leaders, operational fallbacks and original issue clocks.</p></div><span class="badge">RESEARCH ONLY</span></div><small id="snapshot" style="color:#cbded0"></small><nav aria-label="Research sections"><a href="#season">Season games</a><a href="#leaders">Metric leaders</a><a href="#evidence">Evidence limits</a><a href="README.md">Project evidence</a><a href="selected_forecasts_n075.json" download>Selected data</a></nav></div></header>
<main class="wrap"><div class="stats" aria-label="Season coverage"><div class="stat"><b id="scheduled">—</b><span>scheduled games in saved census</span></div><div class="stat"><b id="completed">—</b><span>completed games in saved census</span></div><div class="stat"><b id="forward">—</b><span>games with current selected issues</span></div><div class="stat"><b id="missing">—</b><span>games awaiting confirmed kickoff</span></div></div>
<p class="note" id="coverage-note"></p>
<section class="panel" id="season"><div class="sectionhead"><div><h2>2026 season games</h2><p class="muted">Select a week, team or evidence class. All scheduled games stay visible when filters are clear. Times and final scores reflect the saved source census.</p></div><button id="download" type="button">Export visible rows</button></div>
<div class="toolbar"><label>Team or game<input id="search" type="search" placeholder="e.g. SEA, BUF, week/game ID"></label><label>Week<select id="week"><option value="">All weeks</option></select></label><label>Game status<select id="status"><option value="">All games</option><option value="future">Upcoming in saved census</option><option value="completed">Completed</option><option value="tbd">Kickoff time TBD</option></select></label><label>Evidence shown<select id="evidence-filter"><option value="">All preserved panels</option><option value="current_forecasts">Current selected issues</option><option value="earlier_saved_forward">Earlier saved forward</option><option value="prior_selected_reconstruction">Historical reconstruction</option><option value="missing">No prediction evidence</option></select></label></div>
<div class="legend"><span><span class="pill">ORIGINAL ISSUE</span> pregame owner issue</span><span><span class="pill early">EARLY SNAPSHOT</span> timestamped; durable delivery unproved</span><span><span class="pill replay">RECONSTRUCTION</span> model actually fitted later</span></div><p id="visible-count" class="count" role="status" aria-live="polite"></p>
<div class="scroll" tabindex="0" aria-label="Scrollable all-game forecast table"><table class="games"><thead><tr><th scope="col">Game / result / kickoff UTC</th><th scope="col">Home win probability</th><th scope="col">Expected home margin</th><th scope="col">Expected total points</th><th scope="col">Role and source coverage</th></tr></thead><tbody id="games"></tbody></table></div><p id="empty" class="empty" hidden>No games match these filters.</p></section>
<section class="panel" id="leaders"><div class="sectionhead"><div><h2>Metric-specific historical leaders</h2><p class="muted">Each row follows the same selected candidate through 2024 and 2025. The selected development objective and its support are preserved. Fallback roles are shown separately.</p></div></div><p class="note">These seasons have been examined during development. Selection supports forward shadow monitoring; it does not establish independent production promotion. Accuracy, probability quality and point error can favor different models.</p>
<label style="max-width:270px;margin:16px 0">Selected role group<select id="role-group"><option value="primary">Historical leaders</option><option value="fallback">Operational fallbacks</option><option value="all">Both groups</option></select></label><div class="scroll" tabindex="0" aria-label="Scrollable champion scorecards"><table class="roles"><thead><tr><th scope="col">Role</th><th scope="col">Public model alias</th><th scope="col">2024</th><th scope="col">2025</th><th scope="col">Pooled selection</th><th scope="col">Support</th></tr></thead><tbody id="champions"></tbody></table></div></section>
<section class="panel" id="evidence"><h2>What the evidence supports</h2><div class="footgrid"><div><h3>Originals and reconstructions stay separate</h3><p>Original owner issues retain their actual fit and issue clocks. The qualified early snapshots have timestamps but lack proven durable original delivery. Historical reconstruction rows were fitted after the games and cannot be counted as original forecasts.</p><p>No combined season score is calculated from these mixed policies, and no metric is recomputed from rounded display values. Current-season outcomes did not select the displayed historical champions.</p></div><div><h3>Availability is part of the result</h3><p>A missing historical leader is shown as unavailable even when an operational fallback has an original forecast. A TBD kickoff is displayed without the provider’s placeholder time.</p><p>DraftKings, Kalshi and Polymarket quote values are absent from this selected-output export. Each remains a separate source gap here; saved market comparisons and exact coverage receipts are documented in the project evidence. A conditional spread contract is never presented as an expected margin.</p></div></div><details><summary>Display qualifications and source freshness</summary><ul id="qualifications"></ul><p class="muted">This file is a saved snapshot. Opening it does not acquire a score, refresh an injury, infer a forecast, change a model, or create a wager. The latest source-observation clock for every game remains visible.</p></details></section>
<footer>Sports Edge Lab · NFL · Source publication, owner execution and website deployment are separate events. This research view contains selected rounded outputs and no raw feed, private recipe, stake or order control.</footer></main>
<script id="selected-data" type="application/json">__SELECTED_DATA__</script>
<script>
'use strict';
const data=JSON.parse(document.getElementById('selected-data').textContent);
const byId=id=>document.getElementById(id);
const groups=['current_forecasts','earlier_saved_forward','prior_selected_reconstruction'];
const targets=['win','margin','total'];
const roleMap=new Map(data.selected_historical_roles.map(r=>[r.role_id,r]));
const words={EXACT_SELECTED_CURRENT_SOURCE_OR_STATE_UNAVAILABLE:'Exact selected current inputs or state unavailable',ALREADY_COMPLETED_WITHOUT_AN_ORIGINAL_CURRENT_CHAMPION_ISSUE:'No original current-champion issue before this completed game',OFFICIAL_KICKOFF_TIME_TBD_NO_ISSUE:'Official kickoff time unconfirmed; precise issue horizon unavailable',OFFICIAL_KICKOFF_TIME_TBD_NO_PRECISE_ISSUE_HORIZON:'Official kickoff time unconfirmed; precise issue horizon unavailable'};
function textNode(tag,text,cls){const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node;}
function utc(value){if(!value)return 'Unavailable';const d=new Date(value);return Number.isNaN(d.getTime())?'Unavailable':d.toISOString().replace('T',' ').replace(/\.\d+Z$/,' UTC');}
function totalRows(game){return targets.reduce((n,t)=>n+groups.reduce((m,g)=>m+game.targets[t][g].length,0),0);}
function evidenceKind(row,group){if(row.evidence_kind==='historical_reconstruction'||group==='prior_selected_reconstruction')return 'replay';if(row.evidence_kind==='timestamped_saved_snapshot')return 'early';return 'original';}
function chosenGroups(){const e=byId('evidence-filter').value;return groups.includes(e)?[e]:groups;}
function formatMetric(value,metric){if(value===null||value===undefined)return 'Unavailable';return metric==='accuracy'?(100*value).toFixed(2)+'%':Number(value).toFixed(metric==='mae'||metric==='rmse'||metric==='crps'?3:4);}
function predictionText(row,target){if(target==='win')return 'Home '+row.home_win_percent.toFixed(1)+'% · '+row.predicted_winner;if(target==='margin')return (row.home_point_margin>0?'+':'')+row.home_point_margin.toFixed(1)+' home points';return row.total_points.toFixed(1)+' total points';}
function renderForecastCell(game,target){const td=document.createElement('td');let count=0;
 for(const group of chosenGroups())for(const row of game.targets[target][group]){count++;const block=textNode('div','','forecast'),kind=evidenceKind(row,group);block.appendChild(textNode('span',kind==='replay'?'RECONSTRUCTION':kind==='early'?'EARLY SNAPSHOT':'ORIGINAL ISSUE','pill '+(kind==='original'?'':kind)));
 block.appendChild(textNode('div',predictionText(row,target),'number'));block.appendChild(textNode('small',row.model_alias));
 const roles=game.targets[target].roles.filter(r=>r.model_alias===row.model_alias&&r.current_forecast_available).map(r=>roleMap.get(r.role_id)?.label||r.role_id);if(group==='current_forecasts'&&roles.length)block.appendChild(textNode('small',roles.join('; ')));
 block.appendChild(textNode('small',row.original_issue_at_utc?'Issued '+utc(row.original_issue_at_utc):'Original issue not established'));if(kind==='replay')block.appendChild(textNode('small','Model fitted '+utc(row.model_completed_at_utc)));block.appendChild(textNode('small',row.evidence_class));td.appendChild(block);}
 if(!count)td.appendChild(textNode('p',game.official_time_tbd?'Kickoff time unconfirmed. No admitted forecast.':words[game.targets[target].status]||'No forecast in this evidence panel.','missing'));return td;}
let visible=[];
function renderGames(){const q=byId('search').value.trim().toLowerCase(),week=byId('week').value,status=byId('status').value,evidence=byId('evidence-filter').value;
 visible=data.games.filter(g=>(!q||[g.home_team,g.away_team,g.game_id].join(' ').toLowerCase().includes(q))&&(!week||String(g.week)===week)&&(!status||(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census))&&(!evidence||(evidence==='missing'?totalRows(g)===0:targets.some(t=>g.targets[t][evidence].length))));
 const body=byId('games');body.replaceChildren();for(const game of visible){const tr=document.createElement('tr'),identity=document.createElement('td');identity.appendChild(textNode('div',game.away_team+' at '+game.home_team,'game-title'));identity.appendChild(textNode('small','Week '+game.week+' · '+game.game_id));identity.appendChild(textNode('p',game.official_time_tbd?'Kickoff time TBD · '+game.official_date_status:utc(game.kickoff_utc)));identity.appendChild(textNode('small',game.completed_in_saved_census?'Final: '+game.away_team+' '+game.away_score+' / '+game.home_team+' '+game.home_score:'Unplayed in saved census'));tr.appendChild(identity);for(const target of targets)tr.appendChild(renderForecastCell(game,target));
 const coverage=document.createElement('td'),missing=targets.flatMap(t=>game.targets[t].roles.filter(r=>!r.current_forecast_available&&r.role_id.startsWith('primary_')));coverage.appendChild(textNode('small','Source observed '+utc(game.source_observed_at_utc)));
 if(missing.length){const detail=document.createElement('details');detail.appendChild(textNode('summary',missing.length+' historical-leader roles unavailable'));for(const role of missing)detail.appendChild(textNode('small',(roleMap.get(role.role_id)?.label||role.role_id)+': '+(words[role.missing_reason]||role.missing_reason)));coverage.appendChild(detail);}
 const sources=document.createElement('details');sources.className='sources';sources.appendChild(textNode('summary','Provider coverage in this export'));for(const provider of ['DraftKings','Kalshi','Polymarket'])sources.appendChild(textNode('small',provider+': quote absent; no same-cutoff value or source-age claim.'));coverage.appendChild(sources);tr.appendChild(coverage);body.appendChild(tr);}
 byId('visible-count').textContent=visible.length+' of '+data.games.length+' games · '+chosenGroups().map(g=>({current_forecasts:'current selected issues',earlier_saved_forward:'earlier forward evidence',prior_selected_reconstruction:'historical reconstructions'})[g]).join(' / ');byId('empty').hidden=visible.length!==0;return visible;}
function renderLeaders(){const group=byId('role-group').value,body=byId('champions');body.replaceChildren();for(const row of data.selected_historical_roles){if(group!=='all'&&!row.role_id.startsWith(group+'_'))continue;const tr=document.createElement('tr');tr.appendChild(textNode('td',row.label));tr.appendChild(textNode('td',row.model_alias));for(const year of [2024,2025]){const card=(row.season_metrics||[]).find(s=>s.season===year),td=textNode('td',formatMetric(card?.metrics?.[row.metric],row.metric));if(card)td.appendChild(textNode('small',card.games+' games'));tr.appendChild(td);}tr.appendChild(textNode('td',formatMetric(row.selection_value,row.metric)));tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));body.appendChild(tr);}}
byId('snapshot').textContent='Display prepared '+utc(data.display_cutoff_utc)+' · saved evidence, not a live data refresh';for(const [id,key]of [['scheduled','schedule_games'],['completed','completed_games'],['forward','current_selected_games'],['missing','official_time_tbd_games']])byId(id).textContent=data.counts[key];
byId('coverage-note').textContent=(data.counts.games_with_any_preserved_evidence??data.games.filter(g=>totalRows(g)>0).length)+' games have at least one preserved prediction or reconstruction; '+(data.counts.games_without_prediction_evidence_in_this_projection??data.games.filter(g=>!totalRows(g)).length)+' have none in this export. These evidence classes overlap and are never pooled into a claimed prospective season score.';
for(const week of [...new Set(data.games.map(g=>g.week))].sort((a,b)=>a-b)){const o=textNode('option','Week '+week);o.value=String(week);byId('week').appendChild(o);}for(const item of data.qualifications)byId('qualifications').appendChild(textNode('li',item));
byId('search').addEventListener('input',renderGames);for(const id of ['week','status','evidence-filter'])byId(id).addEventListener('change',renderGames);byId('role-group').addEventListener('change',renderLeaders);
byId('download').addEventListener('click',()=>{const body={schema:data.schema,display_cutoff_utc:data.display_cutoff_utc,selection_filters:{week:byId('week').value,status:byId('status').value,evidence:byId('evidence-filter').value,search:byId('search').value},games:visible};const blob=new Blob([JSON.stringify(body,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='nfl-selected-visible-research.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
renderGames();renderLeaders();window.nflSelectedReview={renderGames,renderLeaders,getVisible:()=>visible,data};
</script></body></html>'''


def _base_render(value):
    page = _old_render(value)
    header = '<th scope="col">Support</th>'
    statement = "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));body.appendChild(tr);"
    if page.count(header) != 1 or page.count(statement) != 1:
        raise ValueError('N080_DASHBOARD_TEMPLATE_CONTRACT_CHANGED')
    page = page.replace(header, header + '<th scope="col">Current-season availability</th>')
    page = page.replace(statement,
        "tr.appendChild(textNode('td',row.selection_games+' games · development exposed'));"
        "const current=data.games.filter(g=>Object.values(g.targets).some(t=>t.roles.some(r=>r.role_id===row.role_id&&r.current_forecast_available))).length;"
        "tr.appendChild(textNode('td',current+' current issued games; 2026 metric scorecard not supplied in selected export; rolling promotion not established'));body.appendChild(tr);")
    return page

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


def _replace(page, old, new):
    if page.count(old) != 1:
        raise ValueError('N084_DASHBOARD_TEMPLATE_CHANGED')
    return page.replace(old, new)


def _dashboard_render(value):
    audit(value)
    page = _base_render(value)
    page = _replace(page, '<option value="future">Upcoming in saved census</option>',
        '<option value="future">Upcoming, confirmed kickoff</option><option value="live">Live / awaiting final</option>')
    page = _replace(page, "const roleMap=new Map(data.selected_historical_roles.map(r=>[r.role_id,r]));",
        "const roleMap=new Map(data.selected_historical_roles.map(r=>[r.role_id,r]));\n"
        "function gameState(g){if(g.completed_in_saved_census)return 'completed';if(g.official_time_tbd)return 'tbd';return new Date(g.kickoff_utc)<=new Date(data.display_cutoff_utc)?'live':'future';}")
    page = _replace(page, "(status==='completed'?g.completed_in_saved_census:status==='tbd'?g.official_time_tbd:!g.completed_in_saved_census)",
        "gameState(g)===status")
    page = _replace(page, ":'Unplayed in saved census'", ":gameState(game)==='live'?'Live or awaiting final in saved census':gameState(game)==='tbd'?'Kickoff time unconfirmed':'Upcoming in saved census'")
    return page


HEALTH='2026-11-13-n083-actual-n084-review.json'
FORECAST='selected_forecasts_n084.json'

def render(value,health):
    import hashlib,html
    counts=audit(value)
    if health['saved_census']!=counts or health['display_cutoff_utc']!=value['display_cutoff_utc']:
        raise ValueError('N084_AUDIT_CENSUS_MISMATCH')
    if health['new_fits']!=health['new_native_fits']+health['new_meta_fits']:
        raise ValueError('N084_FIT_TOTAL_MISMATCH')
    if health['owner_research_acceptance'] or health['automatic_promotion']:
        raise ValueError('N084_UNSUPPORTED_ACCEPTANCE')
    page=_dashboard_render(value).replace('selected_forecasts_n075.json',FORECAST)
    summary='<section class="panel" id="n083-execution"><h2>Actual N083 execution</h2><p><strong>'+str(health['new_fits'])+' new fits: '+str(health['new_native_fits'])+' native + '+str(health['new_meta_fits'])+' meta.</strong> '+str(len(health['new_frozen_cards']))+' new frozen 2024/2025 scorecards across 60 source-interaction experiments. Elapsed '+format(health['elapsed_seconds']/60,'.2f')+' minutes. Owner acceptance remains incomplete.</p><p>'+html.escape(health['failure'])+'</p><p>'+html.escape(health['forecast_scope'])+'</p><p><a href="season_review_n083.html">Preserved N082 review and prior champion roles</a> · <a href="'+HEALTH+'">Aggregate evidence</a></p></section>'
    page=page.replace('<main class="wrap">','<main class="wrap">'+summary,1)
    panel='<section class="panel" id="new-frozen"><h2>New frozen 2024/2025 experiment scorecards</h2><p>These are development-exposed historical comparisons, not prospective validation. All 60 candidates and both evaluation seasons remain visible. Missing target metrics remain unavailable.</p><label>Season<select id="new-season"><option value="">Both years</option><option>2024</option><option>2025</option></select></label><p id="new-count"></p><div class="scroll"><table><thead><tr><th>Candidate</th><th>Season / target</th><th>Horizon / games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="new-cards"></tbody></table></div></section><section class="panel" id="retained"><h2>Preserved current-season metric leaders</h2><p>'+html.escape(health['old_2026_scope'])+'</p><p class="note">'+html.escape(health['current_2026_status'])+'</p><div class="scroll"><table><thead><tr><th>Target / metric</th><th>Model</th><th>Value</th><th>Horizon</th><th>Games / candidates</th></tr></thead><tbody id="old-leaders"></tbody></table></div><details><summary>All 77 retained scorecards</summary><div class="scroll"><table><thead><tr><th>Model</th><th>Target / horizon</th><th>Games</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th></tr></thead><tbody id="old-cards"></tbody></table></div></details><p>No full-season all-model winner is certified. Original former roles, prior selections and rolling promotion gaps remain visible in the linked preceding review.</p></section>'
    page=page.replace('<section class="panel" id="evidence">',panel+'<section class="panel" id="evidence">',1)
    encoded=json.dumps(health,sort_keys=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    js="""
const latest=HEALTH_DATA;
function addRow(id,values){const tr=document.createElement('tr');for(const v of values)tr.appendChild(textNode('td',String(v)));byId(id).appendChild(tr);}
function renderNew(){const year=byId('new-season').value,rows=latest.new_frozen_cards.filter(r=>!year||String(r.season)===year);byId('new-cards').replaceChildren();for(const r of rows)addRow('new-cards',[r.model_alias,r.season+' / '+r.target,r.horizon_seconds+'s / '+r.games,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(r.metrics[m],m))]);byId('new-count').textContent=rows.length+' of '+latest.new_frozen_cards.length+' scorecards';}
byId('new-season').addEventListener('change',renderNew);renderNew();
for(const r of latest.old_2026_leaders)addRow('old-leaders',[r.target+' / '+r.metric,r.model_aliases.join(' / '),formatMetric(r.value,r.metric),r.comparison_horizon_seconds+'s',r.games+' / '+r.selected_candidates_compared]);
for(const r of latest.old_2026_cards)addRow('old-cards',[r.model_alias,r.target+' / '+r.comparison_horizon_seconds+'s',r.games,...['accuracy','log_loss','brier','mae','rmse'].map(m=>formatMetric(r.metrics[m],m))]);
""".replace('HEALTH_DATA',encoded)
    page=page.replace('renderGames();renderLeaders();window.nflSelectedReview=',js+'renderGames();renderLeaders();window.nflSelectedReview=',1)
    return page

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    root=Path(__file__).parent;value=json.loads((root/FORECAST).read_bytes());health=json.loads((root/HEALTH).read_bytes())
    page=render(value,health);out=root/'season_review_n084.html'
    if args.check:
        if out.read_text()!=page:raise SystemExit('N084 page differs from saved evidence')
        print('N084 exact deterministic rendering passed')
    else:out.write_text(page)
if __name__=='__main__':main()
