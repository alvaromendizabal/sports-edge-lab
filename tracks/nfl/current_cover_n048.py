"""Validate a new issue using unchanged distribution states and explicit settlement."""
import hashlib,json,math
from pathlib import Path
from point_markets import require
from market_clock import instant
HERE=Path(__file__).resolve().parent

def validate_current_cover(d,coverage,issues):
 require(d['schema']=='sports-edge-lab.nfl.current-cover.n048.v1','Unknown cover issue schema')
 require(d['owner_return_sha256']==issues['owner_return_sha256'],'Wrong actual owner')
 require(d['owner_status']=='PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED'and d['owner_research_acceptance']is False,'Partial run promoted')
 require(d['new_distribution_fits']==0 and d['restored_distribution_states']==15,'Restored states cannot be new fits')
 require(d['native_parent_stream']=='n048_designation' and d['actual_issue_at_utc']=='2026-11-06T01:46:21.340570+00:00','Issue parent or clock changed')
 require(all(d[k]is False for k in ['automatic_promotion','calibration_validated'])and d['actual_orders']==d['final_hour_qualified_cards']==0,'Unsupported readiness')
 require(len(d['cards'])==28 and len(d['threshold_rows'])==78,'Issue scope changed')
 parents={c['game_id']:c for s in issues['streams']if s['role']=='designation'for c in s['cards']}
 require({r['game_id']for r in d['cards']}==set(parents),'Parent cohort differs')
 for c in d['cards']:
  p=parents[c['game_id']];require(c['home_margin']==p['home_margin'],'Parent margin differs')
  require(c['parent_point_issue_at_utc']==p['actual_issue_at']and c['parent_feature_asof_at_utc']==p['base_feature_asof_at'],'Parent clocks differ')
  issue=instant(c['actual_issue_at_utc']);require(issue==instant(d['actual_issue_at_utc'])and instant(c['parent_point_issue_at_utc'])<=issue<instant(c['kickoff_utc']),'Issue unavailable')
  require(instant(c['distribution_maximum_training_label_available_at'])<=instant(c['distribution_fit_completed_at'])<=issue,'Future label/state')
  require(c['actual']is None and c['automatic_promotion']is False and c['calibration_validated']is False,'Invented outcome/calibration')
  prev=None
  for q in['50','80','90','95']:
   a,b=c['intervals'][q];require(type(a)is int and type(b)is int and a<=b,'Invalid margin interval')
   if prev:require(a<=prev[0]and b>=prev[1],'Non-nested intervals')
   prev=(a,b)
 counts={p:0 for p in ['kalshi','polymarket','draftkings']}
 for r in d['threshold_rows']:
  require(r['game_id']in parents and r['provider']in counts,'Unknown provider/event');counts[r['provider']]+=1
  require(instant(r['observed_at_utc'])<=instant(r['actual_issue_at_utc'])and r['actual_issue_at_utc']==d['actual_issue_at_utc'],'Quote after issue')
  probs=[r[k]for k in['probability_above_threshold','probability_equal_threshold','probability_below_threshold']]
  require(all(type(x)in(int,float)and math.isfinite(x)and 0<=x<=1 for x in probs)and abs(sum(probs)-1)<=.00101,'Probability mass invalid')
  expected=r['probability_below_threshold']if r['orientation']=='HOME_MARGIN_STRICTLY_LESS_THAN'else r['probability_above_threshold']
  require(r['probability_of_observed_margin_predicate']==expected,'Predicate orientation differs')
  require(r['actual']is None and r['executable_quote_claimed']is False and r['fee_adjusted_ev']is None,'Invented bet result')
  if r['settlement_policy']=='UNKNOWN':require(r['settlement_scoring_eligible']is False and r['scoring_probability']is None,'Unknown settlement scored')
  else:require(r['settlement_scoring_eligible']is True and r['scoring_probability']==expected,'Strict settlement differs')
 require(counts=={'kalshi':14,'polymarket':14,'draftkings':50},'Provider issue scope differs')
 return{'n048_current_cover_validation':'PASS','n048_cover_rows':78,'n048_interval_cards':28,'n048_new_distribution_fits':0}

def load_current_cover(coverage,issues):
 p=HERE/'current_cover_n048.json';d=json.loads(p.read_text());return d,{**validate_current_cover(d,coverage,issues),'current_cover_n048_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
