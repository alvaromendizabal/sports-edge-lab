"""Finite six-cell source addition preserves all prior accepted references."""
import hashlib,json
from pathlib import Path
from point_markets import require
from market_clock import instant
HERE=Path(__file__).parent
SHA='f380293a748ea514e09ba19ff9652e05f4fa4bc3f393503308f28550443dc8e1'
def load_historical_reference(coverage):
 p=HERE/'historical_reference_n047.json';require(hashlib.sha256(p.read_bytes()).hexdigest()==SHA,'Historical addition changed');d=json.loads(p.read_text())
 old=json.loads((HERE/'historical_reference_n046.json').read_text());gids={'2025_18_CAR_TB','2025_18_SEA_SF'}
 require(len(d['winner_rows'])==2 and len(d['point_rows'])==4,'Finite repair scope differs')
 for group in ('winner_rows','point_rows'):
  oldids={(x['game_id'],x['provider'],x.get('target','winner'))for x in old[group]}
  for x in d[group]:
   require(x['provider']=='Polymarket'and x['season']==2025 and x['game_id']in gids,'Repair expanded scope')
   require((x['game_id'],x['provider'],x.get('target','winner'))not in oldids,'Accepted reference overwritten')
   require(x['metric_eligible'] is False and x['execution_qualified'] is False,'Source repair became metric or executable quote')
 for target,n in [('winner',281),('margin',281),('total',280)]:
  require(next(x for x in d['coverage']if x['provider']=='Polymarket'and x['season']==2025 and x['target']==target)['available_games']==n,'Combined coverage differs')
 return d,{'historical_reference_n047_validation':'PASS','new_latest_pregame_cells':6,'historical_reference_n047_sha256':SHA}
