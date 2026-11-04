"""Strict public display of separately replayed historical pregame observations."""
import hashlib
import json
from pathlib import Path
import re
from datetime import timedelta
from market_clock import instant
from point_markets import ROW_FIELDS as POINT_FIELDS, require, scalar

HERE=Path(__file__).resolve().parent
ROOT_FIELDS={'schema','as_of','owner_return_sha256','capture_state','owner_pipeline_accepted',
 'new_fits','new_forecasts','historical_metrics_changed','search_window_seconds',
 'selection_rule','winner_rows','point_rows','coverage','limitations'}
WIN_FIELDS={'game_id','provider','horizon','derived_pick','p_home','correct','quote_at','acquired_at',
 'quote_clock_kind','quote_age_seconds','max_age_seconds','pair_clock_skew_seconds','metric_eligible',
 'availability_status','unavailable_reason','comparison_rule'}


def validate_latest_pregame(data,coverage):
    require(set(data)==ROOT_FIELDS,'Unknown or missing latest-pregame fields')
    require(data['schema']=='sports-edge-lab.nfl.latest-pregame-addendum.n037b.v1','Unknown latest-pregame schema')
    require(data['capture_state']=='AUTHENTICATED_RETROSPECTIVE_LATEST_PREGAME_CANDLES','Unknown historical source role')
    require(data['owner_pipeline_accepted'] is False and data['historical_metrics_changed'] is False,
            'Historical source display does not establish acceptance or rescore models')
    for name in ('new_fits','new_forecasts'):
        require(type(data[name]) is int and data[name]==0,'Historical quotes are not new fits or forecasts')
    require(re.fullmatch('[0-9a-f]{64}',data['owner_return_sha256']) is not None,'Invalid owner-return digest')
    require(data['search_window_seconds']==86400,'Unknown bounded history search window')
    for key in ROOT_FIELDS-{'winner_rows','point_rows','coverage','limitations'}:scalar(data[key])
    require(isinstance(data['limitations'],list) and len(data['limitations'])>=4,'Missing retrospective limitations')
    for value in data['limitations']:scalar(value)
    require('outcome' in data['selection_rule'].lower(),'Outcome-independent selection must remain explicit')
    require(len(data['winner_rows'])==1 and len(data['point_rows'])==2,'This scoped addendum closes three references')
    games={g['game_id']:g for g in coverage['all_games']};seen=set();counts={}
    for group,fields in [('winner_rows',WIN_FIELDS),('point_rows',POINT_FIELDS)]:
        for row in data[group]:
            require(set(row)==fields,'Unknown or missing historical reference fields')
            for value in row.values():scalar(value)
            target=row.get('target','winner');key=(row['game_id'],row['provider'],target)
            require(key not in seen,'Duplicate historical reference');seen.add(key)
            require(row['game_id']=='2026_08_CHI_SEA' and row['provider']=='Kalshi',
                    'This replay is specific to the audited Monday event and provider')
            game=games[row['game_id']];kick=instant(game['kickoff_utc'])
            require(game['completed'] and game['actual'] is not None,'Historical display needs a completed canonical event')
            require(row['horizon']=='LATEST_PREGAME' and row['metric_eligible'] is False,
                    'Later pregame quote cannot replace T1/T2 or enter old metrics')
            quote,acquired=instant(row['quote_at']),instant(row['acquired_at'])
            require(kick-timedelta(seconds=data['search_window_seconds'])<=quote<kick<acquired<=instant(data['as_of']),
                    'A historical pregame quote and later acquisition must retain separate clocks')
            require(row['quote_clock_kind']=='RETROSPECTIVE_PROVIDER_CANDLE_TIMESTAMP',
                    'Provider candle time cannot become an original issue or possession time')
            require(row['availability_status']=='OBSERVED_RETROSPECTIVE_LATEST_PREGAME_REFERENCE',
                    'Historical availability role changed')
            counts[(row['provider'],target)]=counts.get((row['provider'],target),0)+1
            if target=='winner':
                p=row['p_home'];require(type(p) in (int,float) and 0<=p<=1 and abs(p*1000-round(p*1000))<1e-7,
                    'Winner proxy must be a rounded probability')
                require(row['derived_pick']==(game['home'] if p>.5 else game['away']) and p!=.5,
                    'Winner direction contradicts the event or probability')
                require(row['correct'] is (row['derived_pick']==game['actual']['winner']),
                    'Retrospective correctness differs from public result')
                require(abs(row['quote_age_seconds']-(kick-quote).total_seconds())<.001,
                    'Latest quote age uses scheduled kickoff')
                require(row['max_age_seconds']>=row['quote_age_seconds'] and row['pair_clock_skew_seconds']>=0,
                    'Invalid paired winner ages')
            else:
                require(target in ('margin','total') and row['point_estimate'] is None,
                        'Threshold cannot become a mean point forecast')
                require(row['semantics']=='THRESHOLD_CONTRACT_NOT_POINT_PROJECTION',
                        'Point reference must remain a binary threshold')
                require(row['predicate_variable']==('home_margin' if target=='margin' else 'total')
                        and row['operator'] in ('>','>=','<','<='),'Point target orientation changed')
                require(row['line_min']<=row['line']<=row['line_max'] and bool(row['predicate']),
                        'Invalid point threshold')
                require(0<=row['observed_probability']<=1 and abs(row['observed_probability']*1000-round(row['observed_probability']*1000))<1e-7,
                        'Invalid rounded contract probability')
                require(all(type(row[k]) is int and row[k]>0 for k in ('contract_count','source_observation_count','parsed_contract_count'))
                        and row['parsed_contract_count']<=row['contract_count']<=row['source_observation_count'],
                        'Invalid source/contract denominators')
                cutoff=instant(row['cutoff_at']);require(cutoff==kick-timedelta(seconds=1) and quote<=cutoff,
                    'Strict pre-kickoff query boundary differs')
                require(abs(row['quote_age_seconds']-(cutoff-quote).total_seconds())<.001,'Historical candle age differs')
    declared=set();finals=sum(g['completed'] for g in games.values())
    for row in data['coverage']:
        require(set(row)=={'provider','target','available_games','total_completed_games'},'Unknown latest coverage fields')
        key=(row['provider'],row['target']);require(key not in declared,'Duplicate latest coverage');declared.add(key)
        require(row['available_games']==counts.get(key,0) and row['total_completed_games']==finals,'Incorrect latest coverage denominator/numerator')
    require(declared=={(p,t) for p in ('DraftKings','Kalshi','Polymarket') for t in ('winner','margin','total')},'Incomplete latest coverage census')
    return {'latest_pregame_status':'PUBLIC_SCOPED_HISTORICAL_REFERENCE_VALIDATED',
            'latest_pregame_games':1,'latest_pregame_rows':3,'latest_pregame_new_fits':0,
            'latest_pregame_historical_metrics_changed':False}


def load_latest_pregame(coverage):
    p=HERE/'latest_pregame_n035.json';data=json.loads(p.read_text())
    return data,{**validate_latest_pregame(data,coverage),'latest_pregame_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
