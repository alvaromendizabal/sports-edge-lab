"""Build the public V10 dashboard from preserved, authenticated public exports.

No optimizer, S3, provider call, or model artifacts are loaded by this module.
Large historical tables are separate assets and are loaded only on request.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / 'dashboard_n088'
FORECAST = ROOT / 'selected_forecasts_n086.json'
HEALTH = ROOT / '2026-11-13-n085-actual-n086-review.json'


def encode(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def build_payload():
    from selected_review_n086 import validate
    raw = FORECAST.read_bytes()
    health = json.loads(HEALTH.read_bytes())
    source = validate(raw, health)
    games = []
    for g in source['games']:
        item = {k:v for k,v in g.items() if k != 'targets'}
        item['targets'] = {}
        for target,panel in g['targets'].items():
            item['targets'][target] = {'status': panel['status'], 'rows': []}
            for kind in ('current_forecasts', 'earlier_saved_forward', 'prior_selected_reconstruction'):
                for row in panel[kind]:
                    item['targets'][target]['rows'].append(dict(row, saved_group=kind))
        games.append(item)
    phase_path = ROOT / 'phase_a_n088_public.json'
    phase = json.loads(phase_path.read_bytes()) if phase_path.exists() else None
    if phase is not None:
        if phase.get('new_model_fits') != 0 or phase.get('automatic_promotion') is not False:
            raise ValueError('PHASE_A_FIT_OR_PROMOTION_CLAIM')
    return {
        'schema': 'nfl.v10.public-dashboard.n088.v1',
        'owner': 'NFL', 'season':2026, 'release':'N088',
        'saved_schedule_cutoff_utc': source['display_cutoff_utc'],
        'schedule_refresh_claimed':False,
        'source_forecast_sha256':hashlib.sha256(raw).hexdigest(),
        'source_aggregate_sha256':hashlib.sha256(HEALTH.read_bytes()).hexdigest(),
        'games':games, 'historical_roles':source['selected_historical_roles'],
        'prior_cohort_leaders':health['all_2026_leaders'],
        'phase_a':phase,
        'execution': {
            'actual_owner_version':'N087',
            'owner_return_sha256':'56f6a59b43ab6e15f7c4c663e699189f930dee94def067c8f45dedb7a5d76102',
            'status':'PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED',
            'elapsed_seconds':678.674439974,
            'mean_cpu_core_equivalents':0.3990816279314138,
            'peak_cpu_core_equivalents':1.2130259559366778,
            'verified_completed_new_scientific_receipts':0,
            'final_fit_totals':None,
            'observed_optimizer_callbacks':0,
            'paid_calls':15,
            'live_log_bytes':325727,'live_jsonl_bytes':743769,
            'failure':'V4_CHILD_RESPONSE_MISSING',
            'independently_reproduced_cold_import_failure':'RecursionError',
            'reproduction_seconds':0.0435498509905301,
            'reproduction_network_calls':0,
            'reproduction_model_fits':0,
        },
        'market_status':{p:{'new_qualified_comparison_cells':0,
            'reason':'No new exact game, contract and observed pregame-clock matched evidence admitted to this public export.'}
            for p in ('DraftKings','Kalshi','Polymarket','Circa')},
        'new_fits':0,'automatic_promotion':False,'automatic_rolling_refits':False,
    }, health


def fallback(games):
    rows=[]
    for g in games:
        result=f"{g['away_team']} {g['away_score']} / {g['home_team']} {g['home_score']}" if g['completed_in_saved_census'] else 'Kickoff TBD' if g['official_time_tbd'] else 'Upcoming in saved census'
        rows.append('<tr><td>'+html.escape(g['game_id'])+'</td><td>'+html.escape(g['kickoff_utc'] or 'TBD')+'</td><td>'+html.escape(result)+'</td></tr>')
    return '<table><thead><tr><th>Every saved game ID</th><th>Kickoff UTC</th><th>Saved status / actual</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'


def assets():
    data,health=build_payload()
    template=(ROOT/'dashboard_n088_template.html').read_text()
    page=template.replace('__DASHBOARD_DATA__',encode(data)).replace('__FALLBACK__',fallback(data['games']))
    out={'index.html':page.encode(), '.nojekyll':b''}
    out['historical.json']=encode({'cards':health['all_historical_cards'], 'original_issue_cards':health['original_issue_cards'], 'legacy_cards':health['legacy_cards'], 'preserved_cards':health['preserved_cards'], 'current_cards':health['monitor_cards']+health['selected_2026_scorecards']+health['mapped_preserved_cards']}).encode()
    out['publication.json']=encode({'schema':'nfl.n088.static-build.v1','source_forecast_sha256':data['source_forecast_sha256'],'source_aggregate_sha256':data['source_aggregate_sha256'],'games':len(data['games']),'schedule_refresh_claimed':False,'new_fits':0,'status':'PREPARED','assets':{name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in out.items()}}).encode()
    return out


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args()
    result=assets()
    for name,raw in result.items():
        path=args.output/name
        if args.check:
            if not path.is_file() or path.read_bytes()!=raw:raise SystemExit('DASHBOARD_BUILD_MISMATCH: '+str(path))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(json.dumps({'status':'PASS','assets':{n:len(b) for n,b in result.items()},'new_fits':0,'schedule_refresh_claimed':False}))


if __name__=='__main__':main()
