"""Sanitized actual owner-study evidence; no private recipe or prediction arrays."""
import hashlib,json,math
from html import escape
from pathlib import Path
from point_markets import require
HERE=Path(__file__).resolve().parent
ROOT={'schema','owner_return_sha256','derived_manifest_sha256','status','evaluated_recipes','new_interior_recipes','new_recipe_selections','new_native_fits','restored_native_and_calibration_identities','new_derived_issue_rows','automatic_promotion','owner_pipeline_accepted','selection_period','matched_baseline','historical_injury_coverage','season_metrics','pooled_metrics','limitations'}
NUMBERS={'model_accuracy','model_auc','model_brier','model_correct','model_ece','model_games','model_log_loss','control_accuracy','control_auc','control_brier','control_correct','control_ece','control_games','control_log_loss','paired_primary_delta','ci_low','ci_high','model_bias','model_mae','model_rmse','control_bias','control_mae','control_rmse'}
ROW=NUMBERS|{'target','season','cohort','evaluation'}

def validate_contribution(d):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.injury-contribution.n041.v1','Unknown contribution evidence')
 require(d['owner_return_sha256']=='144da21ccb8cc133ff68cd9a5e8c048629c4c016ba8ba1e4758a21330ef2541c' and d['derived_manifest_sha256']=='7ab2f98189f2781f4798feef662afb9070e37505215b834df442b5e41d812b5f','Study identity differs')
 require(d['status']=='COMPLETE_ELIGIBLE_DERIVED_RESEARCH' and d['evaluated_recipes']==960 and d['new_interior_recipes']==576 and d['new_recipe_selections']==3,'Declared study scope differs')
 require(d['new_native_fits']==d['new_derived_issue_rows']==0 and d['restored_native_and_calibration_identities']==2772,'Derived selection is not native fitting or issuance')
 require(d['automatic_promotion'] is False and d['owner_pipeline_accepted'] is False and d['selection_period']=='ELIGIBLE_PRE2024_OOF_ONLY','Exposed evaluation cannot become selection or promotion')
 require(d['historical_injury_coverage']==[{'season':2024,'qualified_both_team_games':284,'total_games':285},{'season':2025,'qualified_both_team_games':0,'total_games':285},{'season':2026,'qualified_both_team_games':0,'total_games':120}],'Missing injury inputs cannot become qualified')
 require(len(d['season_metrics'])==18,'Three targets, seasons and two cohorts required');seen=set()
 for r in d['season_metrics']:
  require(set(r)==ROW,'Unknown metric field');key=(r['target'],r['season'],r['cohort']);require(key not in seen,'Duplicate metric cell');seen.add(key)
  require(r['target'] in ('win','margin','total') and r['season'] in (2024,2025,2026) and r['cohort'] in ('ALL_BASE_UNKNOWN_REPORTS_FLAGGED','QUALIFIED_BOTH_TEAM_REPORTS'),'Unknown cohort identity')
  require(r['evaluation']==('DESCRIPTIVE_MONITORING_NOT_SELECTION' if r['season']==2026 else 'DEVELOPMENT_EXPOSED_RETROSPECTIVE'),'Exposed evaluation mislabeled')
  n=284 if r['cohort']=='QUALIFIED_BOTH_TEAM_REPORTS' and r['season']==2024 else 0 if r['cohort']=='QUALIFIED_BOTH_TEAM_REPORTS' else (285 if r['season']==2024 or r['season']==2025 and r['target']!='win' else 284 if r['season']==2025 else 119 if r['target']=='win' else 120)
  require(r['model_games']==r['control_games']==n,'Exact matched cohort changed')
  for k in NUMBERS:require(r[k] is None or type(r[k]) in (int,float) and math.isfinite(r[k]),'Nonfinite metric')
  if not n:
   require(all(r[k] is None for k in NUMBERS-{'model_games','control_games'}),'Empty cohort cannot have scores');continue
  loss='log_loss' if r['target']=='win' else 'mae'
  require(abs(r['paired_primary_delta']-(r['model_'+loss]-r['control_'+loss]))<1e-10,'Paired loss difference mismatch')
  require(r['ci_low']<=r['ci_high'],'Invalid uncertainty interval')
  if r['target']=='win':
   for prefix in ('model_','control_'):
    require(abs(r[prefix+'accuracy']-r[prefix+'correct']/n)<1e-12 and 0<=r[prefix+'brier']<=1,'Winner metrics do not reconcile')
   require(all(r[k] is None for k in ('model_mae','model_rmse','model_bias','control_mae','control_rmse','control_bias')),'Target metric mismatch')
  else:
   require(0<=r['model_mae']<=r['model_rmse'] and 0<=r['control_mae']<=r['control_rmse'],'Invalid point errors')
 require(len(d['pooled_metrics'])==3 and {r['target'] for r in d['pooled_metrics']}=={'win','margin','total'},'Pooled target coverage changed')
 for r in d['pooled_metrics']:
  require(set(r)<= {'target','seasons','cohort','evaluation','games','log_loss','brier','accuracy','correct','ece','auc','mae','rmse','bias'},'Private/unknown pooled field')
  require(r['seasons']=='2024+2025' and r['cohort']=='ALL_BASE_UNKNOWN_REPORTS_FLAGGED' and r['evaluation']=='DEVELOPMENT_EXPOSED_RETROSPECTIVE' and r['games']==(569 if r['target']=='win' else 570),'Pooled cohort/exposure changed')
 require(len(d['limitations'])>=7,'Missing research qualifications')
 return {'injury_contribution_recipes':960,'injury_contribution_selections':3,'injury_contribution_new_native_fits':0,'injury_contribution_promoted':False}

def load_contribution():
 p=HERE/'injury_contribution_n041.json';d=json.loads(p.read_text());return d,{**validate_contribution(d),'injury_contribution_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def render_contribution(d):
 def table(caption,headers,rows):
  return '<div class="scroll table-wrap" tabindex="0" role="region" aria-label="'+escape(caption)+'"><table><caption class="table-caption">'+escape(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+escape(str(v))+('</th>' if i==0 else '</td>') for i,v in enumerate(row))+'</tr>' for row in rows)+'</tbody></table></div>'
 def f(x,n=4):return 'Unavailable' if x is None else f'{x:.{n}f}'
 rows=[r for r in d['season_metrics'] if r['cohort']=='ALL_BASE_UNKNOWN_REPORTS_FLAGGED']
 win=[r for r in rows if r['target']=='win'];points=[r for r in rows if r['target']!='win']
 out=table('New derived winner recipe · same-event native baseline',['Season','Correct / games','Log loss ↓','Brier ↓','AUC / ECE','Loss difference [paired interval]'],[[r['season'],f"{r['model_correct']} / {r['model_games']}",f(r['model_log_loss']),f(r['model_brier']),f(r['model_auc'])+' / '+f(r['model_ece']),f(r['paired_primary_delta'])+' ['+f(r['ci_low'])+', '+f(r['ci_high'])+']'] for r in win])
 out+=table('New derived point recipes · exact matched cohorts',['Season / target','Games','MAE ↓','RMSE ↓','Bias','MAE difference [paired interval]'],[[str(r['season'])+' / '+r['target'],r['model_games'],f(r['model_mae'],3),f(r['model_rmse'],3),f(r['model_bias'],3),f(r['paired_primary_delta'],3)+' ['+f(r['ci_low'],3)+', '+f(r['ci_high'],3)+']'] for r in points])
 out+=table('How much of each evaluation has qualified injury reports?',['Season','All point games','Both-team injury-qualified games','What the scores can establish'],[[r['season'],r['total_games'],r['qualified_both_team_games'],'Qualified injury subset is separately scored' if r['qualified_both_team_games'] else 'Unknown-report treatment; no rich-injury information gain claim'] for r in d['historical_injury_coverage']])
 return out
