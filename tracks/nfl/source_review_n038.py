"""Admit an immutable source-only review without changing model evaluations."""
import hashlib
import json
import math
import re
from pathlib import Path
from market_clock import instant
from point_markets import require, scalar, ROW_FIELDS as CURRENT_POINT_FIELDS
from current_source_overlay import WINNER_FIELDS as CURRENT_WINNER_FIELDS, _clocks

HERE = Path(__file__).resolve().parent
OWNER = 'b52904f3fbdb1e0debb6db277c2ed72c6bfc06a8e8a3ec367044dd0c2cdb1919'
FIELDS = {'schema','owner_return_sha256','source_export_sha256','as_of','owner_status','owner_pipeline_accepted','model_forecasts_changed','historical_metrics_changed','winner_rows','point_rows','historical_coverage','week9_coverage','limitations','draftkings_week9','current_winner_rows','current_point_rows','current_selection_rule'}
COMMON = {'game_id','season','week','provider','horizon','quote_at','acquired_at','quote_clock_kind','metric_eligible','execution_qualified','source_price_role','quote_age_seconds','availability_status'}
WIN = COMMON | {'derived_pick','p_home','pair_clock_skew_seconds','correct'}
POINT = COMMON | {'target','line','point_estimate','predicate_variable','operator','predicate','observed_probability','contract_count','parsed_reference_rows','reason'}

def validate_source_review(data, coverage):
    require(set(data) == FIELDS, 'Unknown public source-review field')
    require(data['schema'] == 'sports-edge-lab.nfl.source-review.n038.v1', 'Source review schema differs')
    require(data['owner_return_sha256'] == OWNER, 'Owner return differs')
    require(re.fullmatch('[0-9a-f]{64}',data['source_export_sha256']), 'Missing source export identity')
    for name in ('owner_pipeline_accepted','model_forecasts_changed','historical_metrics_changed'):
        require(data[name] is False, 'Source review cannot promote research or change a forecast')
    require(data['owner_status']=='PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED','Owner status changed')
    games={g['game_id']:g for g in coverage['all_games'] if g['completed']}
    require(len(games)==121,'Current final census changed')
    seen=set()
    for group,fields in [('winner_rows',WIN),('point_rows',POINT)]:
        for row in data[group]:
            require(set(row)==fields,'Unknown source row field')
            for value in row.values():scalar(value)
            target=row.get('target','winner');key=(row['game_id'],row['provider'],target)
            require(key not in seen,'Duplicate source reference');seen.add(key)
            require(row['game_id'] in games and row['provider'] in ('Kalshi','Polymarket'),'Source reference outside declared cohort')
            game=games[row['game_id']];kick=instant(game['kickoff_utc']);quote=instant(row['quote_at']);acquired=instant(row['acquired_at'])
            require(quote < kick < acquired <= instant(data['as_of']),'Historical quote/acquisition clocks differ')
            require(row['season']==2026 and row['week']==game['week'],'Source game identity differs')
            require(row['metric_eligible'] is False and row['execution_qualified'] is False and row['horizon']=='LATEST_PREGAME','Reference cannot become an earlier forecast or executable offer')
            require(row['availability_status']=='OBSERVED_RETROSPECTIVE_LATEST_PREGAME_REFERENCE','Reference role changed')
            require(abs(row['quote_age_seconds']-(kick-quote).total_seconds())<.001,'Quote age differs')
            require(row['quote_clock_kind']==('RETROSPECTIVE_PROVIDER_CANDLE_TIMESTAMP' if row['provider']=='Kalshi' else 'RETROSPECTIVE_PROVIDER_PRICE_TIMESTAMP'),'Provider clock relabeled')
            probability=row.get('p_home',row.get('observed_probability'))
            require(type(probability) in (int,float) and 0 <= probability <= 1 and abs(probability*1000-round(probability*1000))<1e-7,'Invalid rounded probability')
            if target=='winner':
                require(row['derived_pick'] in (game['home'],game['away']),'Invalid winner direction')
                if probability != .5:require(row['derived_pick']==(game['home'] if probability>.5 else game['away']),'Winner direction differs')
                expected=None if game['actual']['winner']=='TIE' else row['derived_pick']==game['actual']['winner']
                require(row['correct'] is expected,'Winner correctness differs')
                require(row['source_price_role']=='ZERO_TIE_BINARY_PAYOUT_PROXY','Winner settlement proxy changed')
            else:
                require(target in ('margin','total') and row['point_estimate'] is None,'Threshold cannot become a score projection')
                require(row['source_price_role']=='BINARY_THRESHOLD_PROBABILITY_NOT_MEAN_SCORE','Threshold role changed')
                require(row['predicate_variable']==('home_margin' if target=='margin' else 'total') and row['operator'] in ('>','<','>=','<='),'Threshold orientation differs')
                require(type(row['line']) in (int,float) and math.isfinite(row['line']),'Invalid threshold')
                require(type(row['parsed_reference_rows']) is int and row['parsed_reference_rows'] > 0 and type(row['contract_count']) is int and row['contract_count'] > 0,'Invalid contract counts')
    require(seen=={(g,p,t) for g in games for p in ('Kalshi','Polymarket') for t in ('winner','margin','total')},'Current reference population incomplete')
    historical=set()
    for row in data['historical_coverage']:
        require(set(row)=={'available_games','provider','season','target','total_completed_games','scope','status','metric_eligible'},'Coverage fields differ')
        key=(row['season'],row['provider'],row['target']);require(key not in historical,'Duplicate historical coverage');historical.add(key)
        require(row['season'] in (2024,2025,2026) and row['provider'] in ('DraftKings','Kalshi','Polymarket') and row['target'] in ('winner','margin','total'),'Unknown coverage identity')
        require(row['total_completed_games']==(121 if row['season']==2026 else 285),'Historical denominator changed')
        require(0<=row['available_games']<=row['total_completed_games'] and row['metric_eligible'] is False,'Invalid coverage count or metric promotion')
        if row['provider']=='DraftKings':require(row['status']=='NOT_SUPPLIED_TO_PUBLIC_EXPORT' and row['available_games']==0,'Public-only export cannot claim global DraftKings absence')
        elif row['season']==2026:require(row['available_games']==121,'Current full source cohort differs')
    require(len(historical)==27,'Missing historical coverage cell')
    weekly=set()
    for row in data['week9_coverage']:
        require(set(row)=={'provider','target','covered_games','scheduled_games'},'Unknown weekly coverage field')
        key=(row['provider'],row['target']);require(key not in weekly,'Duplicate weekly coverage');weekly.add(key)
        require(row['scheduled_games']==15 and row['covered_games']==(14 if row['provider']=='DraftKings' else 15),'Fresh capture count changed')
    require(weekly=={(p,t) for p in ('DraftKings','Kalshi','Polymarket') for t in ('winner','margin','total')},'Missing current provider cell')
    upcoming={g['game_id']:g for g in coverage['all_games'] if g['week']==9 and not g['completed']}
    dk_seen=set()
    for row in data['draftkings_week9']:
        require(set(row)=={'game_id','provider','horizon','p_home_no_vig','derived_pick','home_spread','home_margin_line_reference','total_line_reference','quote_at','acquired_at','normalization_role','execution_qualified','metric_eligible','spread_total_are_market_lines_not_conditional_means'},'Unknown DraftKings field')
        for value in row.values():scalar(value)
        require(row['game_id'] in upcoming and row['game_id'] not in dk_seen,'Unknown/duplicate DraftKings game');dk_seen.add(row['game_id'])
        game=upcoming[row['game_id']]
        require(row['provider']=='DraftKings' and row['horizon']=='CURRENT_CAPTURE' and row['execution_qualified'] is False and row['metric_eligible'] is False,'DraftKings role changed')
        require(instant(row['quote_at']) <= instant(row['acquired_at']) < instant(game['kickoff_utc']),'DraftKings clock not pregame')
        require(row['home_margin_line_reference']==-row['home_spread'] and row['spread_total_are_market_lines_not_conditional_means'] is True,'DraftKings line orientation/meaning changed')
        p=row['p_home_no_vig'];require(0<=p<=1 and abs(p*1000-round(p*1000))<1e-7,'Unrounded DraftKings display probability')
        require(row['derived_pick']==(game['home'] if p>.5 else game['away']),'DraftKings direction differs')
        expected='DOCUMENTED_KICKOFF_REVISION_RECOVERY' if row['game_id']=='2026_09_LV_SF' else 'DIRECT_EVENT_JOIN'
        require(row['normalization_role']==expected,'DraftKings recovery role changed')
    require(dk_seen==set(upcoming),'Missing DraftKings Week 9 game')
    require('Outcome-independent' in data['current_selection_rule'] and 'two-sided' in data['current_selection_rule'], 'Missing current selection rule')
    current_seen=set()
    for group,fields in [('current_winner_rows',CURRENT_WINNER_FIELDS),('current_point_rows',CURRENT_POINT_FIELDS)]:
        for row in data[group]:
            require(set(row)==fields,'Unknown current source field')
            for value in row.values():scalar(value)
            target=row.get('target','winner');key=(row['game_id'],row['provider'],target)
            require(row['game_id'] in upcoming and row['provider'] in ('Kalshi','Polymarket') and key not in current_seen,'Current identity differs');current_seen.add(key)
            require(row['horizon']=='LATEST_OBSERVED' and row['metric_eligible'] is False,'Current source cannot become an earlier metric')
            _clocks(row,upcoming[row['game_id']],instant(data['as_of']))
            prob=row.get('p_home',row.get('observed_probability'))
            require(type(prob) in (int,float) and 0<=prob<=1 and abs(prob*1000-round(prob*1000))<1e-7,'Invalid current rounded probability')
            if target=='winner':
                g=upcoming[row['game_id']]
                require(row['availability_status']=='OBSERVED_WINNER_REFERENCE' and row['derived_pick']==(g['home'] if prob>.5 else g['away']),'Current direction differs')
            else:
                require(target in ('margin','total') and row['point_estimate'] is None and row['cutoff_at'] is None,'Current threshold cannot become projected score or earlier cutoff')
                require(row['availability_status']=='OBSERVED_THRESHOLD_CONTRACT' and row['semantics']=='THRESHOLD_CONTRACT_NOT_POINT_PROJECTION','Current threshold role differs')
                require(row['predicate_variable']==('home_margin' if target=='margin' else 'total') and row['operator'] in ('>','<','>=','<='),'Current threshold orientation differs')
                require(row['line_min']<=row['line']<=row['line_max'] and row['parsed_contract_count']>0 and row['parsed_contract_count']<=row['contract_count']<=row['source_observation_count'],'Invalid current threshold/source counts')
    require(current_seen=={(g,p,t) for g in upcoming for p in ('Kalshi','Polymarket') for t in ('winner','margin','total')},'Incomplete current references')
    for value in data['limitations']:scalar(value)
    return {'source_n038_current_winner_references':242,'source_n038_current_point_references':484,'source_n038_model_changes':0,'source_n038_metric_changes':0,'source_n038_week9_winner_references':45,'source_n038_week9_point_references':90}

def load_source_review(coverage):
    path=HERE/'source_review_n038.json';data=json.loads(path.read_text())
    return data,{**validate_source_review(data,coverage),'source_n038_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
