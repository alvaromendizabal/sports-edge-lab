"""Source-only historical additions preserve model results and earlier references."""
import hashlib,json,math
from pathlib import Path
from market_clock import instant
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
ROOT={'schema','owner_return_sha256','owner_public_export_sha256','newly_qualified_source_cells','games','provider','season','winner_rows','point_rows','accepted_prior_references_changed','historical_model_metrics_changed','new_fits','new_forecasts','owner_pipeline_accepted','validation_scope','limitations','events','combined_2025_polymarket_coverage'}
COMMON={'acquired_at','execution_qualified','game_id','horizon','metric_eligible','provider','quote_at','quote_clock_kind','season','source_price_role','week'}
WIN=COMMON|{'derived_pick','p_home','pair_clock_skew_seconds'}
POINT=COMMON|{'contract_count','line','observed_probability','operator','parsed_contract_count','point_estimate','predicate','predicate_variable','target'}
def validate_historical_delta(d):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.historical-source-delta.n040.v1','Unknown source delta schema')
 require(d['owner_return_sha256']=='4edc7477d39ea9a13254f48dc628c5b5b3de5f2c554c158347c6084588d394ae' and d['owner_public_export_sha256']=='75bddecf38e2028934c57563bea69a057ce211c5cae94fb651f20011681a6de6','Source delta identity differs')
 require(d['new_fits']==d['new_forecasts']==0 and all(d[k] is False for k in ('accepted_prior_references_changed','historical_model_metrics_changed','owner_pipeline_accepted')),'Source additions cannot rewrite or promote models')
 require(d['newly_qualified_source_cells']==51 and d['games']==17 and d['season']==2025 and d['provider']=='Polymarket','Declared delta scope differs')
 require(d['combined_2025_polymarket_coverage']=={'winner':276,'margin':276,'total':275,'total_games':285},'Coverage denominators differ')
 events={r['game_id']:r for r in d['events']};require(len(events)==len(d['events'])==17,'Event identity duplication')
 for r in events.values():
  require(set(r)=={'game_id','home_team','away_team','kickoff','season','week'} and r['season']==2025 and 'LA' in (r['home_team'],r['away_team']),'Unexpected source event')
  require(r['game_id'].endswith('_'+r['away_team']+'_'+r['home_team']),'Ordered teams differ')
 require(len(d['winner_rows'])==17 and len(d['point_rows'])==34,'Source delta count differs');seen=set()
 for group,fields in [('winner_rows',WIN),('point_rows',POINT)]:
  for r in d[group]:
   require(set(r)==fields,'Unknown source field');key=(r['game_id'],r.get('target','winner'))
   require(r['game_id'] in events and key not in seen,'Unknown or duplicate source cell');seen.add(key)
   for v in r.values():scalar(v)
   g=events[r['game_id']];require(r['provider']=='Polymarket' and r['season']==2025 and str(r['week'])==str(g['week']),'Source event/provider mismatch')
   require(r['horizon']=='LATEST_PREGAME' and r['metric_eligible'] is False and r['execution_qualified'] is False,'Historical source cannot become an earlier model input or fill')
   require(instant(r['quote_at'])<instant(g['kickoff'])<instant(r['acquired_at']) and r['acquired_at'].startswith('2026-11-05T01:'),'Actual historical quote and retrieval clocks differ')
   require(r['quote_clock_kind']=='RETROSPECTIVE_PROVIDER_PRICE_TIMESTAMP','Wrong historical clock semantics')
   if group=='winner_rows':
    q=r['p_home'];require(type(q) in (int,float) and math.isfinite(q) and 0<=q<=1,'Invalid winner probability')
    require(r['derived_pick']==(g['home_team'] if q>=.5 else g['away_team']) and r['source_price_role']=='ZERO_TIE_BINARY_PAYOUT_PROXY','Winner direction/proxy differs')
   else:
    require(r['target'] in ('margin','total') and r['point_estimate'] is None and r['operator'] in ('>','>=','<','<=') and r['predicate_variable']==('home_margin' if r['target']=='margin' else 'total'),'Threshold cannot become a mean prediction')
    require(r['source_price_role']=='BINARY_THRESHOLD_PROBABILITY_NOT_MEAN_SCORE' and type(r['line']) in (int,float) and math.isfinite(r['line']) and 0<=r['observed_probability']<=1,'Invalid threshold reference')
 require(all(sum(k[0]==gid for k in seen)==3 for gid in events),'Each new game needs three distinct source cells')
 return {'historical_n040_new_cells':51,'historical_n040_new_games':17,'historical_n040_metrics_changed':False}
def load_historical_delta():
 p=HERE/'historical_source_delta_n040.json';d=json.loads(p.read_text());return d,{**validate_historical_delta(d),'historical_n040_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
