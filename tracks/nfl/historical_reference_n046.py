"""Latest pregame coverage is distinct from a timed evaluation cohort."""
import hashlib,json
from pathlib import Path
from point_markets import require
from market_clock import instant
HERE=Path(__file__).parent
SHA='c1e00edd293186d2c7375a62cc157fcec1a0b447f2d7f677a2c175194dab4828'
def load_historical_reference(coverage):
 p=HERE/'historical_reference_n046.json';require(hashlib.sha256(p.read_bytes()).hexdigest()==SHA,'Historical source content changed');d=json.loads(p.read_text())
 games={g['game_id']:g for g in coverage['all_games'] if g['completed']}
 for provider in ('Kalshi','Polymarket'):
  for target,group in [('winner','winner_rows'),('margin','point_rows'),('total','point_rows')]:
   rows=[r for r in d[group] if r['provider']==provider and r['season']==2026 and r.get('target','winner')==target]
   require(len(rows)==121 and {r['game_id']for r in rows}==set(games),'Latest completed-game coverage differs')
   require(all(r['metric_eligible'] is False and r['execution_qualified'] is False and instant(r['quote_at'])<instant(games[r['game_id']]['kickoff_utc'])for r in rows),'Latest quote cannot become timed metric or execution')
 return d,{'historical_reference_n046_validation':'PASS','latest_kalshi_polymarket_games_each':121,'historical_reference_n046_sha256':SHA}
