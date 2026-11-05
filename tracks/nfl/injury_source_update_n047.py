"""A new source observation cannot revise an already-issued model input."""
import hashlib,json
from pathlib import Path
from point_markets import require
from market_clock import instant
HERE=Path(__file__).parent
SHA='22add08af7e4fbd9e241b66d73bc75eed5a51b4de1b0531744cf63b0b8f07a6c'
def load_injury_source_update(issues):
 p=HERE/'injury_source_update_n047.json';require(hashlib.sha256(p.read_bytes()).hexdigest()==SHA,'Reviewed injury observation changed');d=json.loads(p.read_text())
 require(d['source_rows']==d['normalized_rows']==340 and d['team_tables']==d['team_slots']==30,'Listed report coverage differs')
 require(sum(r['admitted_rows']for r in d['coverage'])==340 and len({r['team']for r in d['coverage']})==30,'Team census does not close')
 require(d['new_fits']==d['new_forecasts']==0 and d['earlier_issues_modified'] is False,'New capture cannot become owner science')
 require(all(instant(s['actual_issue_at'])<instant(d['observed_at'])for s in issues['streams']),'Capture must remain later than all prior issues')
 require(d['historical_publication_clock_proven'] is False and d['full_roster_health_proven'] is False,'Observation cannot establish historical availability or full health')
 return d,{'n047_review_injury_source':'PASS_SOURCE_ONLY','n047_review_injury_team_tables':30,'n047_review_injury_rows':340,'n047_review_injury_new_fits':0}
