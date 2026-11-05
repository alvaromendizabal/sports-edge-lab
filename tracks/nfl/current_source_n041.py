"""A new capture is an additional observation, never a rewritten issue."""
import hashlib,json
from pathlib import Path
from current_source_overlay import validate_overlay, WINNER_FIELDS, _clocks
from point_markets import ROW_FIELDS as POINT_FIELDS, scalar
from market_clock import instant
from point_markets import require
HERE=Path(__file__).resolve().parent
OWNER='144da21ccb8cc133ff68cd9a5e8c048629c4c016ba8ba1e4758a21330ef2541c'
FIELDS={'schema','owner_return_sha256','as_of','winner_rows','point_rows','coverage','draftkings_fresh_games','draftkings_retained_games','additional_week10_draftkings_games','selection_rule','historical_metrics_changed','model_forecasts_changed','owner_pipeline_accepted','limitations','n041_owner_fallback_available','retained_reference_origin','original_normalized_week9_games','review_recovered_week9_games','review_recovery_evidence_sha256'}
def validate_current_source(data,coverage):
 require(set(data)==FIELDS and data['schema']=='sports-edge-lab.nfl.current-source.n041.v1','Unknown current-source schema')
 require(data['owner_return_sha256']==OWNER,'Current-source owner identity differs')
 require(data['n041_owner_fallback_available'] is False and data['retained_reference_origin'] is None,'Retained public evidence cannot become successful owner fallback or fresh capture')
 require(all(data[k] is False for k in ('historical_metrics_changed','model_forecasts_changed','owner_pipeline_accepted')),'Source-only evidence cannot promote research')
 require(data['draftkings_fresh_games']==15 and data['draftkings_retained_games']==0,'Fresh and retained DraftKings coverage differs')
 require(data['original_normalized_week9_games']==14 and data['review_recovered_week9_games']==1 and data['review_recovery_evidence_sha256']=='64ad74c9e8bde4b7a5801f0840c52a1546fb282c5d6fcd0f5dc4249f7be24d77','Review recovery must not rewrite original owner normalization')
 overlay={'schema':'sports-edge-lab.nfl.current-source-overlay.n035b.v1','as_of':data['as_of'],'capture_state':'PARTIAL_OWNER_SOURCE_CHECKPOINT_RECOVERY','owner_pipeline_accepted':False,'provenance':'Separate authenticated current source observation; preserves earlier evidence.','limitations':data['limitations'],'selection_rule':data['selection_rule'],'winner_rows':[r for r in data['winner_rows'] if r['game_id'].startswith('2026_09_')],'point_rows':[r for r in data['point_rows'] if r['game_id'].startswith('2026_09_')],'coverage':data['coverage']}
 checked=validate_overlay(overlay,coverage)
 require(all(r['available_games']==15 for r in data['coverage']),'New display must retain all current game references')
 for group in ('winner_rows','point_rows'):
  for row in data[group]:
   if row['provider'] in ('Kalshi','Polymarket'):
    require(row['acquired_at'].startswith('2026-11-05T02:'),'Fresh provider capture clock differs')
   elif row['game_id']=='2026_09_LV_SF':
    require(row['acquired_at']=='2026-11-05T02:25:27Z' and row['quote_at']=='2026-11-05T02:24:03+00:00','Recovered current capture clocks changed')
   else:require(row['acquired_at'].startswith('2026-11-05T02:'),'Fresh DraftKings clock differs')
 games={g['game_id']:g for g in coverage['all_games'] if g['week']==10 and not g['completed']}
 extra=set()
 for group,fields in [('winner_rows',WINNER_FIELDS),('point_rows',POINT_FIELDS)]:
  for row in data[group]:
   if row['game_id'].startswith('2026_09_'):continue
   target=row.get('target','winner');key=(row['game_id'],target)
   require(set(row)==fields and row['game_id'] in games and row['provider']=='DraftKings' and key not in extra,'Unexpected future reference');extra.add(key)
   for value in row.values():scalar(value)
   require(row['horizon']=='LATEST_OBSERVED' and row['metric_eligible'] is False,'Future reference promoted')
   _clocks(row,games[row['game_id']],instant(data['as_of']))
   if target=='winner':
    p=row['p_home'];g=games[row['game_id']]
    require(type(p) in (float,int) and 0<=p<=1 and abs(p*1000-round(p*1000))<1e-7 and row['derived_pick']==(g['home'] if p>.5 else g['away']),'Invalid future winner')
   else:
    require(target in ('margin','total') and row['point_estimate'] is None and row['observed_probability'] is None and row['semantics']=='QUOTED_LINE_NOT_POINT_PROJECTION','Future quoted line promoted')
    require(row['predicate_variable']==('home_margin' if target=='margin' else 'total') and row['line_min']==row['line']==row['line_max'],'Future line orientation differs')
 require(data['additional_week10_draftkings_games']==13 and len(extra)==39 and all(sum(k[0]==g for k in extra)==3 for g in {k[0] for k in extra}),'Future DraftKings coverage differs')
 return {'source_n041_status':'CURRENT_REFERENCES_VALIDATED_WITH_DATED_FALLBACK','source_n041_winner_rows':len(data['winner_rows']),'source_n041_point_rows':len(data['point_rows']),'source_n041_draftkings_fresh_games':15,'source_n041_draftkings_retained_games':0,'source_n041_new_model_fits':0,'source_n041_new_model_issues':0}
def load_current_source(coverage):
 p=HERE/'current_source_n041.json';d=json.loads(p.read_text());return d,{**validate_current_source(d,coverage),'source_n041_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
