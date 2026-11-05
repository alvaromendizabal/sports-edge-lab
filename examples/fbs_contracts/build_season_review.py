"""Render and validate the public FBS all-game report from its sanitized data."""
from pathlib import Path
from datetime import timedelta
from zoneinfo import ZoneInfo
import argparse, hashlib, html, json, math, re
from .market_time import instant, reference_at, availability_reference_at
from .season_transport import pack, unpack
from .source_progress import render_section
from .native_current_snapshot import REGISTRATION, validate_snapshot

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'docs/fbs/season-2026.json'
TEMPLATE=Path(__file__).with_name('season_template.html.in')
OUTPUT=ROOT/'docs/fbs/index.html'
PROVIDERS=('DraftKings','Kalshi','Polymarket US','Polymarket Global')
GAME_KEYS={'id','season','phase','week','kickoff','kickoff_tbd','home','away','completed','home_points','away_points','population','source_at','replay','rolling','decision','stake_usd','markets'}
REFERENCE_KEYS={'target','value','picked_home','quote_at','captured_at','reference_kind','product','evidence_kind','identity_basis','join_status','event_url','executable','interval_end_at','price_status','clock_basis','source_status','source_status_field','point_support','registered_cutoff_kind','source_query_cutoff_kind'}
REPLAY_KEYS={'p_home','picked_home','home_points','away_points','home_margin','total','correct','margin_error','total_error','status','issued_at'}
TOP_KEYS={'schema','season','prepared_at','assessed_at','timezone','owner','inventory','windows','metrics','historical','weekly','matched_draftkings','matched_recovered','provider_coverage','provider_acquisition_summary','reporting_contract','games'}

def require(value,message):
    if not value:raise ValueError(message)

def finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def validate(data):
    data=unpack(data)
    require(set(data)==TOP_KEYS,'Unexpected or missing public root field')
    require(data['schema']=='fbs.public.season-explorer.v1','Wrong public schema')
    require(data['timezone']=='America/Los_Angeles','Wrong display timezone')
    instant(data['assessed_at']);instant(data['prepared_at'])
    require(data['reporting_contract']['predictions_use_current_labels_for_selection'] is False,'Current labels may not select')
    require(data['reporting_contract']['actual_orders']==0 and data['reporting_contract']['stake_usd']==0,'No order publication')
    require(data['owner']['new_fits']+data['owner']['reused_states']==data['owner']['committed_states'],'Owner count closure')
    require(data['owner']['new_issued_forecasts']==0 and data['owner']['new_rolling_fits']==0,'Unexpected forecast evidence needs a versioned contract')
    games=data['games'];ids=[]
    for game in games:
        require(set(game)==GAME_KEYS,'Unexpected or missing public game field')
        require(str(game['id']).isdigit() and game['season']==data['season'],'Invalid game/season identity')
        ids.append(game['id']);instant(game['kickoff']);instant(game['source_at'])
        require(game['home']!=game['away'] and bool(game['home']) and bool(game['away']),'Invalid ordered teams')
        require(game['decision']=='NO BET' and game['stake_usd']==0,'Unexpected betting position')
        require(game['rolling'] is None,'Unproved rolling values')
        require(set(game['markets'])==set(PROVIDERS),'Provider products changed')
        if game['completed']:
            require(all(finite(game[x]) and game[x]>=0 and int(game[x])==game[x] for x in ['home_points','away_points']),'Completed score missing')
        else:
            require(game['home_points'] is None and game['away_points'] is None,'Future scores are not outcomes')
        replay=game['replay']
        if replay is not None:
            require(set(replay)==REPLAY_KEYS,'Unexpected or missing replay field')
            require(game['completed'] and 0<=replay['p_home']<=1,'Replay must have a resolved outcome')
            require(replay['status']=='retrospective_original_replay' and replay['issued_at'] is None,'Replay cannot become an issue')
            require(replay['correct']==(replay['picked_home']==(game['home_points']>game['away_points'])),'Winner correctness differs')
            require(all(finite(replay[x]) for x in ['home_points','away_points','home_margin','total','margin_error','total_error']),'Missing point forecast')
            require(abs(replay['home_points']-replay['away_points']-replay['home_margin'])<.21,'Rounded score/margin coherence')
        for provider,refs in game['markets'].items():
            for ref in refs:
                require(set(ref)==REFERENCE_KEYS,'Unexpected public reference field')
                require(ref['target'] in ['winner','margin','total'],'Incompatible product')
                require(ref['value'] is None or finite(ref['value']),'Nonfinite reference')
                if ref['target']=='winner' and ref['value'] is not None:require(0<=ref['value']<=1,'Invalid reference probability')
                if ref['quote_at']:instant(ref['quote_at'])
                if ref['captured_at']:instant(ref['captured_at'])
                require(ref['quote_at'] or ref['captured_at'],'Reference has no recorded clock')
                require(ref['clock_basis']==('provider_quote_at' if ref['quote_at'] else 'retrieved_at'),'Clock basis cannot fabricate a source quote timestamp')
                require(ref['registered_cutoff_kind'] in [None,'T120','T60','LATEST_BEFORE_KICKOFF',REGISTRATION],'Unknown registered proxy window')
                require(ref['source_query_cutoff_kind'] in [None,'T120','T60','LATEST_BEFORE_KICKOFF','latest_pre_kickoff','current'],'Unknown acquisition query window')
                if ref['registered_cutoff_kind']==REGISTRATION:
                    require(provider!='DraftKings' and ref['quote_at'] is None and ref['source_query_cutoff_kind']=='current'
                            and ref['product']=='verified_native_current_snapshot','Current native display must stay outside historical windows')
                elif ref['registered_cutoff_kind']:
                    require(provider!='DraftKings' and ref['target'] in ['margin','total'] and ref['quote_at'] and ref['reference_kind'].startswith('implied_threshold_center_from_'),'Only historical native point proxies are window-specific')
                support=ref['point_support']
                if support is not None:
                    require(ref['target'] in ['margin','total'] and ref['quote_at'] is None,'Current point support cannot replace historical quotes or winner probabilities')
                    require(set(support)=={'method','status','lower_bound','upper_bound','lower_capture_at','upper_capture_at','support_available_at','diagnostic_probability_band_width'},'Unexpected point-support field')
                    require(support['method']=='CAPTURED_BID_ASK_HALF_PROBABILITY_SUPPORT','Unknown point support method')
                    clocks=[]
                    for side in ['lower','upper']:
                        value=support[side+'_bound'];at=support[side+'_capture_at']
                        require((value is None)==(at is None),'Point bound needs its actual support clock')
                        if value is not None:require(finite(value),'Nonfinite supported point bound');clocks.append(instant(at))
                    require((not clocks and support['support_available_at'] is None) or (clocks and instant(support['support_available_at'])==max(clocks)),'Point-support availability cannot be backdated')
                    width=support['diagnostic_probability_band_width']
                    require(width is None or finite(width) and 0<=width<=1,'Invalid diagnostic probability-band width')
                if ref['interval_end_at']:
                    require(ref['quote_at'] and instant(ref['interval_end_at'])>=instant(ref['quote_at']),'Invalid observation interval')
                require(ref['executable'] is False,'Reference cannot become an executable offer')
                require(ref['join_status']=='matched','Unmatched row entered game')
                if ref['event_url']:require(re.match(r'^https://(?:[a-z0-9-]+\.)?(?:kalshi\.com|polymarket\.com|polymarket\.us)/',ref['event_url']) is not None,'Unexpected event URL')
    require(len(ids)==len(set(ids)),'Duplicate public game ID')
    validate_snapshot(data['reporting_contract'].get('v031_native_current_snapshot'),games,
                      prepared_at=data['prepared_at'],current_week=data['windows']['current_calendar_week'])
    inv=data['inventory']
    require(inv['observed_games']==len(games),'Observed inventory denominator')
    require(inv['completed_games']==sum(g['completed'] for g in games),'Completed denominator')
    require(inv['scheduled_games']==sum(not g['completed'] for g in games),'Scheduled denominator')
    require(inv['original_replay_games']==sum(g['replay'] is not None for g in games),'Replay denominator')
    require(inv['independent_official_completeness_proven'] is False,'Unproved official completeness')
    for name,key in [('previous_complete_week','last_week_games'),('current_calendar_week','current_week_games')]:
        w=data['windows'][name];lo=instant(w['start_inclusive_utc']);hi=instant(w['end_exclusive_utc'])
        count=sum(lo<=instant(g['kickoff'])<hi for g in games)
        require(count==inv[key],'Calendar window count')
        require((hi-lo).total_seconds()/3600==w['elapsed_hours'],'Calendar DST boundary')
    for row in data['provider_coverage']:
        provider=row['provider'];present=[g for g in games if g['markets'][provider]]
        require(row['observed_games']==len(present),'Provider coverage denominator')
        require(row['completed_games']==sum(g['completed'] for g in present),'Provider completed denominator')
        require(row['scheduled_games']==sum(not g['completed'] for g in present),'Provider scheduled denominator')
        require(row['numeric_reference_games']==sum(any(r['value'] is not None for r in g['markets'][provider]) for g in present),'Numeric coverage denominator')
        require(row['timestamped_reference_games']==sum(any(r['value'] is not None and r['quote_at'] is not None for r in g['markets'][provider]) for g in present),'Timestamped coverage denominator')
    for row in data['weekly']:
        cohort=[g for g in games if g['replay'] and g['phase']==row['phase'] and g['week']==row['week']]
        require(row['games']==len(cohort) and row['correct_winner']==sum(g['replay']['correct'] for g in cohort),'Weekly cohort closure')
    require(sum(r['games'] for r in data['weekly'])==inv['original_replay_games'],'Weekly inventory closure')
    for group in ('panels','provider_summary'):
        for row in data['matched_recovered'][group]:
            require(row['provider'] in PROVIDERS and row['target'] in ['winner','margin','total'] and row['season']==2026,'Recovered panel identity')
            require(row['descriptive_only'] and not row['same_model_prediction_cutoff_proven'] and row['actual_issued_predictions']==0,'Recovered report cannot claim a verified prediction clock')
            cohort=[]
            for game in games:
                if not game['completed'] or not game['replay']:continue
                kind=row['cutoff_kind'];cutoff=instant(game['kickoff'])-timedelta(minutes=120 if kind=='T120' else 60 if kind=='T60' else 0)
                source_rows=[r for r in game['markets'][row['provider']] if r['product']==row['product']]
                try:ref=reference_at(source_rows,row['target'],cutoff.isoformat(),strict_before=kind=='LATEST_BEFORE_KICKOFF',registered_cutoff_kind=kind)
                except ValueError:ref=None
                source_kind=ref['reference_kind'].removeprefix('implied_threshold_center_from_') if ref else None
                if ref and ref['product']==row['product'] and (group=='provider_summary' or source_kind==row['reference_kind']):cohort.append(game['id'])
            require(len(cohort)==row['n'],'Recovered matched cohort count')
            pin=hashlib.sha256(json.dumps(sorted(cohort),sort_keys=True,separators=(',',':')).encode()).hexdigest()
            require(pin==row['cohort_sha256'],'Recovered matched cohort identity pin')
            require(row['n']==row['model_metrics']['games']==row['provider_metrics']['games'],'Recovered model/provider denominators')
            if row['target']=='winner':require(row['disagreements']==row['model_correct_on_disagreement']+row['provider_correct_on_disagreement'],'Disagreement outcome closure')
    serialized=json.dumps(data,ensure_ascii=False)
    require(not re.search(r's3://|sagemaker-sports|/home/sagemaker-user|AKIA[0-9A-Z]{16}|secret_access_key|private_model_body|calibration_parameters',serialized),'Private field in public export')
    return data

def fmt(value,places=1):return '—' if value is None else f'{value:.{places}f}'
def winner(game,picked_home):return game['home'] if picked_home else game['away']
def esc(s):return html.escape(str(s))

def static_rows(data):
    result=[]
    for g in data['games']:
        replay=g['replay']; p=replay['p_home'] if replay else None
        score=f"{esc(g['away'])} {g['away_points']:.0f} · {esc(g['home'])} {g['home_points']:.0f}" if g['completed'] else 'Scheduled'
        pick=(f"<strong>{esc(winner(g,replay['picked_home']))}</strong><span class='sub'>{fmt((p if replay['picked_home'] else 1-p)*100,1)}% · {'Correct' if replay['correct'] else 'Incorrect'}</span>" if replay else '<span class="muted">No recorded forecast</span>')
        points=(f"{fmt(replay['away_points'])}–{fmt(replay['home_points'])}<span class='sub'>Home margin {replay['home_margin']:+.1f} · Total {fmt(replay['total'])}</span>" if replay else '<span class="muted">Not issued</span>')
        try:ref=None if g['kickoff_tbd'] else availability_reference_at(g['markets']['DraftKings'],'winner',g['kickoff'],strict_before=True,registered_cutoff_kind='LATEST_BEFORE_KICKOFF',assessed_at=data['prepared_at'])
        except ValueError:ref=None
        market=(f"<strong>{esc(winner(g,ref['picked_home']))}</strong><span class='sub'>{fmt(max(ref['value'],1-ref['value'])*100,1)}% · source {esc(ref['quote_at'])}</span>" if ref else '<span class="muted">No unambiguous stored winner reference</span>')
        local=instant(g['kickoff']).astimezone(ZoneInfo(data['timezone'])).strftime('%b %-d · %-I:%M %p %Z')
        result.append(f'<tr><td>{esc(local)}<span class="sub">{esc(g["phase"])} · week {g["week"]}</span></td><th scope="row">{esc(g["away"])} <span class="at">at</span> {esc(g["home"])}<span class="sub">{esc(g["population"].replace("_"," "))}</span></th><td>{score}</td><td>{pick}</td><td>{points}</td><td>{market}</td><td><span class="pill quiet">Not issued</span></td><td><button class="detail-button" data-game="{esc(g["id"])}" aria-label="Details for {esc(g["away"])} at {esc(g["home"])}">Details</button></td></tr>')
    return '\n'.join(result)

def historical_rows(data):
    return '\n'.join(f'<tr><th scope="row">{esc(r["label"])}</th><td>{r["season"]}</td><td>{r["n"]}</td><td>{r["winner"]["logloss"]:.6f}</td><td>{r["winner"]["brier"]:.6f}</td><td>{r["winner"]["accuracy"]*100:.2f}%</td><td>{r["margin"]["mae"]:.3f} / {r["margin"]["rmse"]:.3f}</td><td>{r["total"]["mae"]:.3f} / {r["total"]["rmse"]:.3f}</td></tr>' for r in data['historical'])

def weekly_rows(data):
    return '\n'.join(f'<tr><th scope="row">{esc(r["phase"])} · {r["week"]}</th><td>{r["games"]}</td><td>{r["correct_winner"]} / {r["games"]-r["correct_winner"]}</td><td>{r["logloss"]:.6f}</td><td>{r["brier"]:.6f}</td><td>{r["ece"]:.6f}</td><td>{r["margin_mae"]:.3f} / {r["margin_rmse"]:.3f}</td><td>{r["total_mae"]:.3f} / {r["total_rmse"]:.3f}</td></tr>' for r in data['weekly'])

def complete_metrics(data):
    result=[]
    for target in ['winner','margin','total']:
        for metric,value in data['metrics']['season'][target].items():
            if isinstance(value,(int,float)):
                last=data['metrics']['last_week'][target].get(metric)
                result.append(f'<tr><th scope="row">{esc(target)} · {esc(metric)}</th><td>{fmt(value,6)}</td><td>{fmt(last,6)}</td></tr>')
    return '\n'.join(result)

def reliability_rows(data):
    return '\n'.join(f'<tr><th scope="row">{r["lower"]:.1f}–{r["upper"]:.1f}</th><td>{r["games"]}</td><td>{r["mean_probability"]:.4f}</td><td>{r["observed_win_rate"]:.4f}</td></tr>' for r in data['metrics']['season']['winner']['reliability_bins'])

def recovered_rows(data,group):
    result=[]
    for row in data['matched_recovered'][group]:
        if row['target']!='winner':continue
        a,b=row['model_metrics'],row['provider_metrics']
        kinds=row.get('reference_kind_counts') or {row['reference_kind']:row['n']}
        source='; '.join(k.replace('_',' ')+' ('+str(v)+')' for k,v in kinds.items())
        interval=row['paired_uncertainty'].get('interval')
        uncertainty=(f'{interval[0]:+.4f} to {interval[1]:+.4f}' if interval else 'Unavailable')
        pair=lambda key:fmt(a.get(key),4)+' / '+fmt(b.get(key),4)
        result.append(f'<tr><th scope="row">{esc(row["provider"])}<span class="sub">{esc(source)}</span></th><td>{esc(row["cutoff_kind"].replace("LATEST_BEFORE_KICKOFF","Latest pregame"))}</td><td>{row["n"]}</td><td>{pair("logloss")}<span class="sub">Δ interval {uncertainty}</span></td><td>{pair("brier")}</td><td>{fmt(a["accuracy"]*100,2)}% / {fmt(b["accuracy"]*100,2)}%</td><td>{pair("roc_auc")}</td><td>{pair("ece")}</td><td>{row["model_correct_on_disagreement"]} / {row["provider_correct_on_disagreement"]}<span class="sub">{row["disagreements"]} disagreements</span></td></tr>')
    return '\n'.join(result) or '<tr><td colspan="9">No qualified recovered comparison is included in this snapshot.</td></tr>'

def recovered_point_rows(data):
    result=[]
    for row in data['matched_recovered']['provider_summary']:
        if row['target']=='winner':continue
        a,b=row['model_metrics'],row['provider_metrics']
        pair=lambda key:fmt(a.get(key),3)+' / '+fmt(b.get(key),3)
        sources='; '.join(k.replace('_',' ')+' ('+str(v)+')' for k,v in row['reference_kind_counts'].items())
        interval=row['paired_uncertainty'].get('interval')
        uncertainty=(f'{interval[0]:+.3f} to {interval[1]:+.3f}' if interval else 'Unavailable: fewer than two phase/week blocks')
        qualification='sportsbook line' if row['provider']=='DraftKings' else 'incomplete-ladder threshold diagnostic'
        result.append(f'<tr><th scope="row">{esc(row["provider"])}<span class="sub">{esc(sources)}</span></th><td>{esc(row["target"])} · {qualification}</td><td>{esc(row["cutoff_kind"].replace("LATEST_BEFORE_KICKOFF","Latest pregame"))}</td><td>{row["n"]}</td><td>{pair("mae")}</td><td>{pair("rmse")}</td><td>{pair("bias")}</td><td>{pair("r2")}</td><td>{uncertainty}</td></tr>')
    return '\n'.join(result) or '<tr><td colspan="9">No comparable point-ladder diagnostic is included.</td></tr>'

def render(data=None):
    data=validate(data or json.loads(DATA.read_text()))
    payload=json.dumps(pack(data),ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    source_section=render_section(json.loads((ROOT/'docs/fbs/official-inventory.json').read_text()),
                                  json.loads((ROOT/'docs/fbs/source-progress.json').read_text()))
    inv=data['inventory']
    source_clock=instant(max(g['source_at'] for g in data['games'])).astimezone(ZoneInfo(data['timezone'])).strftime('%b %-d, %Y · %-I:%M %p %Z')
    return (TEMPLATE.read_text().replace('__SEASON_DATA__',payload)
            .replace('__SOURCE_PROGRESS_SECTION__',source_section)
            .replace('__OBSERVED_GAMES__',str(inv['observed_games']))
            .replace('__COMPLETED_GAMES__',str(inv['completed_games']))
            .replace('__SCHEDULED_GAMES__',str(inv['scheduled_games']))
            .replace('__CURRENT_WEEK_GAMES__',str(inv['current_week_games']))
            .replace('__COMPLETED_UNSCORED__',str(sum(g['completed'] and not g['replay'] for g in data['games'])))
            .replace('__SCHEDULE_CAPTURE__',esc(source_clock))
            .replace('__GAME_ROWS__',static_rows(data)).replace('__HISTORICAL_ROWS__',historical_rows(data))
            .replace('__WEEKLY_ROWS__',weekly_rows(data)).replace('__COMPLETE_METRICS__',complete_metrics(data))
            .replace('__RELIABILITY_ROWS__',reliability_rows(data))
            .replace('__RECOVERED_ROWS__',recovered_rows(data,'provider_summary'))
            .replace('__RECOVERED_KIND_ROWS__',recovered_rows(data,'panels'))
            .replace('__RECOVERED_POINT_ROWS__',recovered_point_rows(data)))

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=render()
    if a.check:require(OUTPUT.read_text()==out,'Generated season page differs')
    else:OUTPUT.write_text(out)
    print('FBS_SEASON_EXPLORER_VERIFIED: all observed games retained; no owner fit performed')

if __name__=='__main__':main()
