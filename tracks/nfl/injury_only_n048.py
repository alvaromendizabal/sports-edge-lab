"""Public aggregate study: report absent inputs beside every model score."""
import hashlib,json,math
from pathlib import Path
from point_markets import require
HERE=Path(__file__).resolve().parent

def validate_study(d):
 require(d['schema']=='sports-edge-lab.nfl.injury-only-study.n048.v1','Unknown injury study')
 require(d['owner_status']=='PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED'and d['study_completed']is True,'Study cannot erase source failure')
 require([d[k]for k in ['new_native_fits','restored_study_fits','failed_cells','blocked_cells','native_candidates','fixed_pair_blends','named_means','new_injury_only_issues']]==[288,0,0,0,16,56,4,0],'Study accounting differs')
 require(len(d['research_candidates'])==76 and len({r['id']for r in d['research_candidates']})==76 and all(r['forecast_status']=='NOT_ISSUED'and r['promotion_status']=='RESEARCH_ONLY_NOT_PROMOTED'for r in d['research_candidates']),'Research candidates became issued/promotion')
 require(d['aggregate_season_metric_rows']==1368 and d['aggregate_weekly_metric_rows']==26904,'Full aggregate coverage differs')
 for n,sha in d['aggregate_csv_sha256'].items():require(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha,'Full aggregate export differs')
 require(d['automatic_promotion']is False,'Unsupported promotion')
 require(len(d['native_metrics'])==288 and len(d['selected_metrics'])==21,'Metric closure differs')
 keys=[(r['family'],r['fields'],r['target'],r['season'])for r in d['native_metrics']]
 require(len(set(keys))==288 and len(set(r[0]for r in keys))==8,'Native study duplicate or missing arm')
 for r in d['native_metrics']:
  require(r['fields']in(75,107)and r['target']in('winner','margin','total')and r['season']in range(2021,2027),'Unknown arm')
  require(all(v is None or isinstance(v,(str,int,float))for v in r.values()),'Private nested metadata')
  if r['target']=='winner':require(0<=r['brier']<=1 and r['log_loss']>=0 and 0<=r['correct']<=r['games'],'Invalid winner metric')
  else:require(r['rmse']>=r['mae']>=0,'Invalid point metric')
 for season in(2025,2026):
  r=next(x for x in d['source_support']if x['season']==season)
  require(r['both_teams_injury75_supported']==0 and r['all_injury75_vectors_zero']is True,'Missing historical reports silently became healthy')
 r=next(r for r in d['selected_metrics']if r['season']==2026 and r['target']=='winner')
 require(r['correct']==62 and r['games']==119 and r['auc']==.5 and abs(r['log_loss']-.6938993146624816)<1e-12,'Constant selected winner differs')
 require(abs(d['current_selected_winner_constant_home_probability']-.5495069073301084)<1e-14 and len(d['qualifications'])>=4,'Missing support-collapse qualification')
 return d

def load_study():
 p=HERE/'injury_only_n048.json';d=validate_study(json.loads(p.read_text()));return d,{'injury_only_n048_validation':'PASS','injury_only_n048_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'injury_only_native_metrics':len(d['native_metrics'])}
