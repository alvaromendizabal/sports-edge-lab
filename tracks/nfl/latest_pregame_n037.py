"""Validate sanitized owner-replayed completed-game references, without rescoring."""
import hashlib,json,math,re
from pathlib import Path
from datetime import timedelta
from market_clock import instant
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
ROOT_FIELDS={'schema','as_of','owner_return_sha256','owner_export_sha256','private_replay_receipt_sha256','private_full_body_proofs','private_selected_row_replays','owner_pipeline_accepted','historical_metrics_changed','new_fits','new_forecasts','selection_rule','winner_rows','point_rows','coverage','limitations'}
COMMON={'game_id','provider','horizon','quote_at','acquired_at','quote_clock_kind','quote_age_seconds','metric_eligible','execution_qualified','availability_status','season','week','source_price_role'}
WIN=COMMON|{'derived_pick','p_home','correct','pair_clock_skew_seconds','max_age_seconds'}
POINT=COMMON|{'target','point_estimate','predicate_variable','operator','line','predicate','observed_probability','contract_count','parsed_contract_count','cutoff_at','semantics','reason'}

def validate_latest_n037(data,coverage):
 require(set(data)==ROOT_FIELDS,'Unknown N037 latest fields')
 require(data['schema']=='sports-edge-lab.nfl.latest-pregame.n037.v1','Unknown N037 latest schema')
 require(data['owner_pipeline_accepted']is False and data['historical_metrics_changed']is False,'Source export is not model acceptance or rescoring')
 for k in ('new_fits','new_forecasts'):require(type(data[k])is int and data[k]==0,'Source review cannot claim fits or forecasts')
 for k in ('owner_return_sha256','owner_export_sha256','private_replay_receipt_sha256'):require(re.fullmatch('[0-9a-f]{64}',data[k])is not None,'Invalid evidence identity')
 require(data['private_full_body_proofs']==907 and data['private_selected_row_replays']==484,'Exact owner replay proof counts differ')
 for k in ROOT_FIELDS-{'winner_rows','point_rows','coverage','limitations'}:scalar(data[k])
 require('outcome' in data['selection_rule'].lower(),'Outcome-independent selection required')
 require(isinstance(data['limitations'],list)and len(data['limitations'])>=4,'Missing source limitations')
 for v in data['limitations']:scalar(v)
 games={g['game_id']:g for g in coverage['all_games']};finals={k for k,g in games.items()if g['completed']};require(len(finals)==121,'Exact current final cohort differs')
 require(len(data['winner_rows'])==121 and len(data['point_rows'])==242,'Exact owner reference population differs')
 seen=set();counts={};asof=instant(data['as_of'])
 for group,fields in (('winner_rows',WIN),('point_rows',POINT)):
  for r in data[group]:
   require(set(r)==fields,'Unknown or missing reference fields')
   for v in r.values():scalar(v)
   t=r.get('target','winner');key=(r['game_id'],t);require(key not in seen,'Duplicate target reference');seen.add(key)
   require(r['game_id']in finals and r['provider']=='Kalshi','Reference not in audited provider/final cohort')
   g=games[r['game_id']];require(r['season']==2026 and r['week']==g['week'],'Reference season/week differs');kick=instant(g['kickoff_utc']);q=instant(r['quote_at']);a=instant(r['acquired_at'])
   require(q<kick<a<=asof and q<=a,'Quote must precede kickoff; retrospective acquisition remains later')
   require(r['horizon']=='LATEST_PREGAME'and r['metric_eligible']is False and r['execution_qualified']is False,'Historical benchmark cannot replace original horizon or executable offer')
   require(r['quote_clock_kind']=='RETROSPECTIVE_PROVIDER_CANDLE_TIMESTAMP'and r['availability_status']=='OBSERVED_RETROSPECTIVE_LATEST_PREGAME_REFERENCE','Provider clock or source role changed')
   require(abs(r['quote_age_seconds']-(kick-q).total_seconds())<.001,'Quote age differs from kickoff')
   counts[t]=counts.get(t,0)+1
   if t=='winner':
    p=r['p_home'];require(type(p)in(int,float)and 0<=p<=1 and p!=.5 and abs(p*1000-round(p*1000))<1e-7,'Invalid rounded winner probability')
    require(r['derived_pick']==(g['home']if p>.5 else g['away']),'Winner direction differs')
    expected=None if g['actual']['winner']=='TIE'else r['derived_pick']==g['actual']['winner'];require(r['correct']is expected,'Correctness differs from canonical result')
    require(r['pair_clock_skew_seconds']>=0 and r['max_age_seconds']==r['quote_age_seconds'],'Paired winner age differs')
    require(r['source_price_role']=='ZERO_TIE_BINARY_PAYOUT_PROXY','Winner tie-proxy role changed')
   else:
    require(t in ('margin','total')and r['point_estimate']is None,'Threshold is not a mean score')
    require(r['semantics']=='THRESHOLD_CONTRACT_NOT_POINT_PROJECTION'and r['source_price_role']=='BINARY_THRESHOLD_PROBABILITY_NOT_MEAN_SCORE','Point semantics changed')
    require(r['predicate_variable']==('home_margin'if t=='margin'else'total')and r['operator']in('>','>=','<','<='),'Point orientation differs')
    require(type(r['line'])in(int,float)and math.isfinite(r['line'])and bool(r['predicate']),'Invalid settlement threshold')
    p=r['observed_probability'];require(type(p)in(int,float)and 0<=p<=1 and abs(p*1000-round(p*1000))<1e-7,'Invalid rounded contract probability')
    require(type(r['contract_count'])is int and type(r['parsed_contract_count'])is int and 0<r['parsed_contract_count']<=r['contract_count'],'Invalid actual contract counts')
    require(instant(r['cutoff_at'])==kick-timedelta(seconds=1)and q<=instant(r['cutoff_at']),'Strict pre-kickoff boundary differs')
 for target in ('winner','margin','total'):require({gid for gid,t in seen if t==target}==finals,'Reference cohort incomplete')
 expected={(p,t)for p in('DraftKings','Kalshi','Polymarket')for t in('winner','margin','total')};declared=set()
 for r in data['coverage']:
  require(set(r)=={'provider','target','available_games','total_completed_games'},'Coverage schema differs');key=(r['provider'],r['target']);require(key in expected and key not in declared,'Duplicate/unknown coverage');declared.add(key)
  require(r['total_completed_games']==121 and r['available_games']==(121 if r['provider']=='Kalshi'else 0),'Coverage counts differ')
 require(declared==expected,'Incomplete provider census')
 return {'latest_n037_status':'PUBLIC_SANITIZED_OWNER_REPLAY_VALIDATED','latest_n037_games':121,'latest_n037_winner_rows':121,'latest_n037_point_rows':242,'latest_n037_private_training_reproduced':False,'latest_n037_owner_acceptance':False}

def load_latest_n037(coverage):
 p=HERE/'latest_pregame_n037.json';data=json.loads(p.read_text());return data,{**validate_latest_n037(data,coverage),'latest_n037_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
