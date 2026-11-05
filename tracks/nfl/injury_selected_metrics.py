"""Preserved target-specific injury-study metrics; current sources cannot promote them."""
import hashlib,json,math
from html import escape
from pathlib import Path
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
ROOT={'schema','retrieved_in_owner_return_sha256','source_member_sha256','source_member_bytes','scientific_origin','new_fits','promotion_accepted','rows','limitations','historical_report_coverage'}
NUMBERS={'games','correct','accuracy','log_loss','brier','auc','ece','mae','rmse','bias','interval_coverage','mean_interval_width','uncalibrated_games','uncalibrated_correct','uncalibrated_accuracy','uncalibrated_log_loss','uncalibrated_brier'}
ROW=NUMBERS|{'season','target','evaluation','direct_injury_features'}
def validate_selected_metrics(d):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.retained-injury-selected-metrics.v1','Unknown selected-metric schema')
 require(d['retrieved_in_owner_return_sha256']=='4edc7477d39ea9a13254f48dc628c5b5b3de5f2c554c158347c6084588d394ae' and d['source_member_sha256']=='d480d84104d8da6b38c8b21216f90dfbe3b48f2b3bec07b06f3e289d7933bb2a' and d['source_member_bytes']==4683,'Retained metric source identity differs')
 require(d['new_fits']==0 and d['promotion_accepted'] is False,'Restored metrics cannot become a new promoted model')
 require(d['historical_report_coverage']==[{'season':2024,'eligible_games':285,'qualified_injury_report_games':284,'unknown_report_games':1},{'season':2025,'eligible_games':285,'qualified_injury_report_games':0,'unknown_report_games':285},{'season':2026,'eligible_games':120,'qualified_injury_report_games':0,'unknown_report_games':120}],'Historical missing injury reports cannot become covered')
 require(len(d['rows'])==9,'Three seasons and three targets required');seen=set()
 for r in d['rows']:
  require(set(r)==ROW,'Unknown metric field');key=(r['season'],r['target'])
  require(key not in seen and r['season'] in (2024,2025,2026) and r['target'] in ('win','margin','total'),'Duplicate/unknown target-season');seen.add(key)
  for v in r.values():scalar(v)
  require(r['evaluation']=='Frozen pre2024 calibration;2024/25development-exposed;2026descriptive','Exposure qualification differs')
  require(r['direct_injury_features'] is (r['target']!='win'),'Selected winner cannot be called injury augmented')
  expected=285 if r['season']==2024 or r['season']==2025 and r['target']!='win' else 284 if r['season']==2025 else 119 if r['target']=='win' else 120
  require(r['games']==r['uncalibrated_games']==expected,'Exact scored cohort differs')
  for k in NUMBERS:require(r[k] is None or type(r[k]) in (int,float) and math.isfinite(r[k]),'Nonfinite metric')
  if r['target']=='win':
   require(abs(r['accuracy']-r['correct']/r['games'])<1e-12 and abs(r['uncalibrated_accuracy']-r['uncalibrated_correct']/r['games'])<1e-12,'Accuracy/count mismatch')
   require(all(r[k] is None for k in ('mae','rmse','bias','interval_coverage','mean_interval_width')),'Winner and point metric roles mixed')
   require(all(0<=r[k]<=1 for k in ('accuracy','brier','auc','ece')) and r['log_loss']>=0,'Invalid winner losses')
  else:
   require(all(r[k] is None for k in ('correct','accuracy','log_loss','brier','auc','ece')),'Point and winner metric roles mixed')
   require(0<=r['mae']<=r['rmse'] and 0<=r['interval_coverage']<=1 and r['mean_interval_width']>0,'Invalid point errors/intervals')
 require(isinstance(d['limitations'],list) and len(d['limitations'])>=5,'Missing evaluation limitations')
 return {'retained_injury_metric_rows':9,'retained_injury_metric_new_fits':0,'retained_injury_metric_promoted':False}
def load_selected_metrics():
 p=HERE/'injury_selected_metrics_n037.json';d=json.loads(p.read_text());return d,{**validate_selected_metrics(d),'retained_injury_metric_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def render_selected_metrics(d):
 def table(caption,headers,rows):
  return '<div class="scroll table-wrap" tabindex="0" role="region" aria-label="'+escape(caption)+'"><table><caption class="table-caption">'+escape(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+escape(str(v))+('</th>' if i==0 else '</td>') for i,v in enumerate(row))+'</tr>' for row in rows)+'</tbody></table></div>'
 winner=sorted((r for r in d['rows'] if r['target']=='win'),key=lambda r:r['season'])
 points=sorted((r for r in d['rows'] if r['target']!='win'),key=lambda r:(r['season'],r['target']))
 return table('Selected winner target · matched base, frozen pre-2024 calibration',['Season','Correct / games','Accuracy','Log loss ↓','Brier ↓','AUC','ECE ↓'],[[r['season'],str(r['correct'])+' / '+str(r['games']),f"{r['accuracy']:.1%}",f"{r['log_loss']:.4f}",f"{r['brier']:.4f}",f"{r['auc']:.4f}",f"{r['ece']:.4f}"] for r in winner])+table('Selected injury point targets · retained historical evaluation',['Season / target','Games','MAE ↓','RMSE ↓','Bias','Interval coverage','Mean width'],[[str(r['season'])+' / '+r['target'],r['games'],f"{r['mae']:.3f}",f"{r['rmse']:.3f}",f"{r['bias']:+.3f}",f"{r['interval_coverage']:.1%}",f"{r['mean_interval_width']:.2f}"] for r in points])
