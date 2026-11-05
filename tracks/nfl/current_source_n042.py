"""A new capture is an additional observation, never a rewritten issue."""
import hashlib,json
from pathlib import Path
from current_source_overlay import validate_overlay, WINNER_FIELDS, _clocks
from point_markets import ROW_FIELDS as POINT_FIELDS, scalar
from market_clock import instant
from point_markets import require
HERE=Path(__file__).resolve().parent
OWNER='7ee0412dfef66645a924486905c7605215944e5414cc7d5fd7b4046be14da31f'
FIELDS={'schema','owner_return_sha256','as_of','winner_rows','point_rows','coverage','draftkings_fresh_games','draftkings_retained_games','additional_week10_draftkings_games','selection_rule','historical_metrics_changed','model_forecasts_changed','owner_pipeline_accepted','limitations','owner_schedule_recovery_available','retained_reference_origin','original_normalized_week9_games','owner_schedule_recovered_week9_games','recovery_evidence_sha256'}
def validate_current_source(data,coverage):
 require(set(data)==FIELDS and data['schema']=='sports-edge-lab.nfl.current-source.n042.v1','Unknown current-source schema')
 require(data['owner_return_sha256']==OWNER,'Current-source owner identity differs')
 require(data['owner_schedule_recovery_available'] is True and data['retained_reference_origin'] is None,'Retained public evidence cannot become successful owner fallback or fresh capture')
 require(all(data[k] is False for k in ('historical_metrics_changed','model_forecasts_changed','owner_pipeline_accepted')),'Source-only evidence cannot promote research')
 require(data['draftkings_fresh_games']==15 and data['draftkings_retained_games']==0,'Fresh and retained DraftKings coverage differs')
 require(data['original_normalized_week9_games']==14 and data['owner_schedule_recovered_week9_games']==1 and data['recovery_evidence_sha256']=='fc54b10fb792d2fc902e8eb0c21e76574cf9e9590567146f7682b6b538ee0cba','Owner schedule recovery must not rewrite original normalization')
 overlay={'schema':'sports-edge-lab.nfl.current-source-overlay.n035b.v1','as_of':data['as_of'],'capture_state':'PARTIAL_OWNER_SOURCE_CHECKPOINT_RECOVERY','owner_pipeline_accepted':False,'provenance':'Separate authenticated current source observation; preserves earlier evidence.','limitations':data['limitations'],'selection_rule':data['selection_rule'],'winner_rows':[r for r in data['winner_rows'] if r['game_id'].startswith('2026_09_')],'point_rows':[r for r in data['point_rows'] if r['game_id'].startswith('2026_09_')],'coverage':data['coverage']}
 checked=validate_overlay(overlay,coverage)
 require(all(r['available_games']==15 for r in data['coverage']),'New display must retain all current game references')
 for group in ('winner_rows','point_rows'):
  for row in data[group]:
   if row['provider'] in ('Kalshi','Polymarket'):
    require(row['acquired_at'].startswith('2026-11-05T04:'),'Fresh provider capture clock differs')
   elif row['game_id']=='2026_09_LV_SF':
    require(row['acquired_at']=='2026-11-05T04:34:39Z' and row['quote_at']=='2026-11-05T04:33:35+00:00','Recovered current capture clocks changed')
   else:require(row['acquired_at'].startswith('2026-11-05T04:'),'Fresh DraftKings clock differs')
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
 return {'source_n042_status':'CURRENT_REFERENCES_VALIDATED_WITH_OWNER_SCHEDULE_RECOVERY','source_n042_winner_rows':len(data['winner_rows']),'source_n042_point_rows':len(data['point_rows']),'source_n042_draftkings_fresh_games':15,'source_n042_draftkings_retained_games':0,'source_n042_new_model_fits':0,'source_n042_new_model_issues':0}
def load_current_source(coverage):
 p=HERE/'current_source_n042.json';d=json.loads(p.read_text());return d,{**validate_current_source(d,coverage),'source_n042_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
