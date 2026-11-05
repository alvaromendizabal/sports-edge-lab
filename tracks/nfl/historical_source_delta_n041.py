"""Source-only historical additions preserve model results and earlier references."""
import hashlib,json,math
from pathlib import Path
from market_clock import instant
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
ROOT={'schema','owner_return_sha256','winner_rows','point_rows','newly_qualified_cells','historical_metrics_changed','events','coverage','newly_qualified_game_provider_arms','newly_qualified_unique_games','new_native_fits','new_issue_rows','owner_pipeline_accepted','accepted_prior_references_changed'}
COMMON={'acquired_at','execution_qualified','game_id','horizon','metric_eligible','provider','quote_at','quote_clock_kind','season','source_price_role','week'}
WIN=COMMON|{'derived_pick','p_home','pair_clock_skew_seconds'}
POINT=COMMON|{'contract_count','line','observed_probability','operator','parsed_contract_count','point_estimate','predicate','predicate_variable','target'}
def validate_historical_delta(d):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.historical-source-delta.n041.v1','Unknown source delta schema')
 require(d['owner_return_sha256']=='144da21ccb8cc133ff68cd9a5e8c048629c4c016ba8ba1e4758a21330ef2541c','Source identity differs')
 require(d['new_native_fits']==d['new_issue_rows']==0 and all(d[k] is False for k in ('accepted_prior_references_changed','historical_metrics_changed','owner_pipeline_accepted')),'Source additions cannot rewrite or promote models')
 require(d['newly_qualified_cells']==30 and d['newly_qualified_game_provider_arms']==10 and d['newly_qualified_unique_games']==9,'Declared delta scope differs')
 expected={('Kalshi','winner'):264,('Kalshi','margin'):267,('Kalshi','total'):271,('Polymarket','winner'):279,('Polymarket','margin'):279,('Polymarket','total'):278}
 require(len(d['coverage'])==6 and {(r['provider'],r['target']):r['available_games'] for r in d['coverage']}==expected and all(r['season']==2025 and r['total_completed_games']==285 for r in d['coverage']),'Source coverage differs')
 events={r['game_id']:r for r in d['events']};require(len(events)==len(d['events'])==9,'Event identity duplication')
 for r in events.values():
  require(set(r)=={'game_id','home_team','away_team','kickoff','season','week'} and r['season']==2025 and 'LA' in (r['home_team'],r['away_team']),'Unexpected source event')
  require(r['game_id'].endswith('_'+r['away_team']+'_'+r['home_team']),'Ordered teams differ')
 require(len(d['winner_rows'])==10 and len(d['point_rows'])==20,'Source delta count differs');seen=set()
 for group,fields in [('winner_rows',WIN),('point_rows',POINT)]:
  for r in d[group]:
   require(set(r)==fields,'Unknown source field');key=(r['game_id'],r['provider'],r.get('target','winner'))
   require(r['game_id'] in events and key not in seen,'Unknown or duplicate source cell');seen.add(key)
   for v in r.values():scalar(v)
   g=events[r['game_id']];require(r['provider'] in ('Kalshi','Polymarket') and r['season']==2025 and str(r['week'])==str(g['week']),'Source event/provider mismatch')
   require(r['horizon']=='LATEST_PREGAME' and r['metric_eligible'] is False and r['execution_qualified'] is False,'Historical source cannot become an earlier model input or fill')
   require(instant(r['quote_at'])<instant(g['kickoff'])<instant(r['acquired_at']) and r['acquired_at'].startswith('2026-11-05T02:'),'Actual historical quote and retrieval clocks differ')
   require(r['quote_clock_kind']==('RETROSPECTIVE_PROVIDER_PRICE_TIMESTAMP' if r['provider']=='Polymarket' else 'RETROSPECTIVE_PROVIDER_CANDLE_TIMESTAMP'),'Wrong historical clock semantics')
   if group=='winner_rows':
    q=r['p_home'];require(type(q) in (int,float) and math.isfinite(q) and 0<=q<=1,'Invalid winner probability')
    require(r['derived_pick']==(g['home_team'] if q>=.5 else g['away_team']) and r['source_price_role']=='ZERO_TIE_BINARY_PAYOUT_PROXY','Winner direction/proxy differs')
   else:
    require(r['target'] in ('margin','total') and r['point_estimate'] is None and r['operator'] in ('>','>=','<','<=') and r['predicate_variable']==('home_margin' if r['target']=='margin' else 'total'),'Threshold cannot become a mean prediction')
    require(r['source_price_role']=='BINARY_THRESHOLD_PROBABILITY_NOT_MEAN_SCORE' and type(r['line']) in (int,float) and math.isfinite(r['line']) and 0<=r['observed_probability']<=1,'Invalid threshold reference')
 require(all(sum(k[:2]==arm for k in seen)==3 for arm in {k[:2] for k in seen}),'Each new game needs three distinct source cells')
 return {'historical_n041_new_cells':30,'historical_n041_new_game_provider_arms':10,'historical_n041_new_unique_games':9,'historical_n041_metrics_changed':False}
def load_historical_delta():
 p=HERE/'historical_source_delta_n041.json';d=json.loads(p.read_text());return d,{**validate_historical_delta(d),'historical_n041_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
