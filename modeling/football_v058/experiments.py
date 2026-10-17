"""Frozen model-capacity test; reused linear forecasts and no baseline refits."""
import time
import numpy as np,pandas as pd,joblib
from common import require,atomic_json,read_json
from data import split_rows
from qb_features import columns as qb_columns
from efficiency import feature_columns
from families import fit_model,predict_model
from metrics import score,paired_interval,residual_intervals,brier_skill,loss
TASKS=('win','margin','total');ARMS={'nfl':('hgb','mlp'),'ncaaf':('mlp',)};REFERENCES=('accepted','same_features_linear')

# Reporting metadata/labels never enter columns(track), fitting or promotion.
REPORT_MIN_ROWS=30
REPORT_LEVELS={
 'venue':('neutral','home_venue','unknown'),
 'prior_history':('both_prior_history','one_prior_history','no_prior_history','unknown'),
 'information_coverage':('both_available','one_available','neither_available','unknown'),
 'matchup':('fbs_vs_fbs','fbs_vs_fcs','neither_fbs','unknown','not_applicable'),
}
def reporting_columns(track):
 return ['neutral','home_fbs','away_fbs','home_games','away_games']+(['qb_home_has_prior_qb','qb_away_has_prior_qb'] if track=='nfl' else ['eff_home_missing','eff_away_missing'])

def reporting_labels(p,track):
 require(track in ARMS,'DATA','Unknown diagnostic track')
 require(set(reporting_columns(track))<=set(p),'DATA','Missing predeclared reporting metadata')
 labels=pd.DataFrame(index=p.index)
 neutral=pd.to_numeric(p.neutral,errors='coerce')
 labels['venue']=np.select([neutral==1,neutral==0],['neutral','home_venue'],default='unknown')
 h=pd.to_numeric(p.home_games,errors='coerce');a=pd.to_numeric(p.away_games,errors='coerce');known=np.isfinite(h)&np.isfinite(a)&(h>=0)&(a>=0)
 labels['prior_history']=np.select([known&(h>0)&(a>0),known&((h>0)^(a>0)),known&(h==0)&(a==0)],['both_prior_history','one_prior_history','no_prior_history'],default='unknown')
 names=reporting_columns(track)[-2:];h=pd.to_numeric(p[names[0]],errors='coerce');a=pd.to_numeric(p[names[1]],errors='coerce');known=h.isin([0,1])&a.isin([0,1])
 available=1 if track=='nfl' else 0
 ha=h==available;aa=a==available
 labels['information_coverage']=np.select([known&ha&aa,known&(ha^aa),known&~ha&~aa],['both_available','one_available','neither_available'],default='unknown')
 if track=='nfl':labels['matchup']='not_applicable'
 else:
  h=pd.to_numeric(p.home_fbs,errors='coerce');a=pd.to_numeric(p.away_fbs,errors='coerce');known=h.isin([0,1])&a.isin([0,1])
  labels['matchup']=np.select([known&(h==1)&(a==1),known&((h==1)^(a==1)),known&(h==0)&(a==0)],['fbs_vs_fbs','fbs_vs_fcs','neither_fbs'],default='unknown')
 for dimension,levels in REPORT_LEVELS.items():require(labels[dimension].isin(levels).all(),'DATA','Non-exhaustive reporting slice labels')
 return labels

def attach_reporting(p,track):
 out=p.copy();labels=reporting_labels(out,track)
 for dimension in REPORT_LEVELS:out['report_'+dimension]=labels[dimension]
 return out

def diagnostic_slices(p,track,task):
 """Predeclared separate partitions, never subgroup selection or promotion."""
 labels=reporting_labels(p,track);arms=REFERENCES+ARMS[track];rows=[]
 for dimension,levels in REPORT_LEVELS.items():
  for label in levels:
   q=p.loc[labels[dimension]==label];n=len(q);blocks=len(q[['season','week']].drop_duplicates())
   support='empty' if n==0 else 'insufficient_rows' if n<REPORT_MIN_ROWS else 'insufficient_blocks' if blocks<8 else 'diagnostic_only'
   scores={a:score(q.target,q[a],task) for a in arms} if n else None
   uncertainty={}
   for a in ARMS[track]:
    uncertainty[a]={}
    for ref in REFERENCES:
     if n>=REPORT_MIN_ROWS:
      interval=paired_interval(q,q[a],q[ref],task,seed=5801)
     else:
      delta=float(np.mean(loss(q.target,q[a],task)-loss(q.target,q[ref],task))) if n else None
      interval=dict(difference=delta,lower95=None,upper95=None,blocks=blocks,replicates=0,status=support,method='At least 30 rows and eight season-week blocks required for diagnostic uncertainty')
     uncertainty[a][ref]=interval
   rows.append(dict(dimension=dimension,label=label,n=n,season_week_blocks=blocks,support=support,scores=scores,paired_uncertainty=uncertainty,brier_skill_vs_references={a:{ref:brier_skill(q.target,q[a],q[ref]) for ref in REFERENCES} for a in ARMS[track]} if task=='win' and n else None,subgroup_promotion=False))
 for dimension in REPORT_LEVELS:require(sum(r['n'] for r in rows if r['dimension']==dimension)==len(p),'METRIC','Diagnostic partition lost or duplicated rows')
 return dict(n=len(p),partitions_mutually_exclusive_and_exhaustive=True,dimensions_are_separate_partitions_not_intersections=True,minimum_uncertainty_rows=REPORT_MIN_ROWS,minimum_uncertainty_blocks=8,information_coverage_definition='prior observed QB identity' if track=='nfl' else 'prior efficiency availability',subgroup_promotion=False,rows=rows)

def columns(track):return qb_columns('qb_values') if track=='nfl' else feature_columns('ncaaf',True)
def prepare(frame):
 f=frame.copy();require(not f.duplicated(['track','game_id']).any(),'DATA','Duplicate canonical games')
 f['decision_at']=pd.to_datetime(f.kickoff,utc=True)-pd.to_timedelta(np.where(f.track=='nfl',24,1),unit='h')
 f['information_upper_bound_at']=f.decision_at
 college=f.track=='ncaaf'
 f.loc[college,'information_upper_bound_at']=pd.concat([pd.to_datetime(f.loc[college,c],utc=True) for c in ['feature_max_available_at','efficiency_max_available_at']],axis=1).max(axis=1)
 audit=[]
 for track in ARMS:
  q=f[f.track==track];require(np.isfinite(q[columns(track)].to_numpy(float)).all(),'DATA','Nonfinite cached features '+track)
  times=['feature_max_available_at']+(['efficiency_max_available_at'] if track=='ncaaf' else [])
  for c in times:
   t=pd.to_datetime(q[c],utc=True);require(not(t>=q.decision_at).any(),'DATA','Cached history at/after decision: '+track+'/'+c)
  audit.append(dict(track=track,rows=len(q),completed=int(q.completed.sum()),features=len(columns(track)),decision_lead_hours=24 if track=='nfl' else 1))
 return f,dict(tracks=audit,raw_pbp_reprocessed=False,new_acquisition=0,source_publication_at=None,strict_historical_point_in_time_verified=False)
def pair(test,p,task):
 require(not p.duplicated(['track','game_id']).any(),'DATA','Duplicate cached reference')
 require(set(p.game_id)==set(test.game_id),'DATA','Cached evaluation cohort differs')
 q=test[['track','game_id','season','kickoff',task]].merge(p,on=['track','game_id'],validate='one_to_one',suffixes=('','_cached'))
 require(np.array_equal(q.season,q.season_cached) and np.array_equal(q[task],q.target) and pd.to_datetime(q.kickoff,utc=True).equals(pd.to_datetime(q.kickoff_cached,utc=True)),'DATA','Cached identity/target/kickoff differs')
 require(np.isfinite(q[list(REFERENCES)].to_numpy()).all(),'DATA','Invalid cached predictions');return q[list(REFERENCES)].reset_index(drop=True)
def baseline(ctx,test,track,task,through,phase):
 if ctx.fixture:
  value=.55 if task=='win' else 3. if task=='margin' else 48.
  return pd.DataFrame({c:np.full(len(test),value) for c in REFERENCES})
 if track=='nfl':
  name='v057_validation_predictions.parquet' if phase=='validation' else 'v057_evaluation_predictions.parquet';p=pd.read_parquet(ctx.root/'cache'/name);p=p[(p.task==task)&p.season.isin(test.season.unique())].copy();p=p.rename(columns={'accepted_v047':'accepted','qb_values':'same_features_linear'})
  p=p[['track','game_id','season','kickoff','target',*REFERENCES]]
 else:
  p=pd.read_parquet(ctx.root/'cache/models'/f'fit_ncaaf_{task}_adjusted_linear_{through}_{phase}.parquet');p['target']=p[task];p['accepted']=p.prediction;p['same_features_linear']=p.prediction;p=p[['track','game_id','season','kickoff','target',*REFERENCES]]
 return pair(test,p,task)
def fit(ctx,frame,track,task,arm,through,years,phase):
 name=f'fit_{track}_{task}_{arm}_{through}_{phase}';old=ctx.cp.lookup(name)
 if old is not None:ctx.event('checkpoint_reused',item=name);return old,pd.read_parquet(ctx.root/old['predictions'])
 ctx.check_budget();tr,te=split_rows(frame,track,task,through,years);require(tr.kickoff.max()+pd.Timedelta(hours=24)<te.decision_at.min(),'DATA','Training label release overlaps decisions');ctx.reserve_fit(name);start=time.monotonic()
 def progress(done,total):ctx.check_budget();ctx.event('training_progress',item=name,iteration=done,total_iterations=total,remaining_iterations=total-done)
 bundle=fit_model(tr[columns(track)],tr[task],task,arm,progress=progress,epochs=8 if ctx.fixture and arm=='mlp' else None);pr=predict_model(bundle,te[columns(track)])
 p=te[['track','game_id','season','week','kickoff','decision_at','information_upper_bound_at',task,*reporting_columns(track)]].copy();p['target']=p[task];p['prediction']=pr;p=attach_reporting(p,track)
 rec=dict(id=name,track=track,task=task,arm=arm,train_through=through,phase=phase,train_rows=len(tr),evaluation_rows=len(te),features=columns(track),seconds=time.monotonic()-start,score=score(te[task],pr,task),family_config=bundle['config'],architecture=bundle['architecture'],epochs_completed=bundle['epochs_completed'],train_latest_release=str(tr.kickoff.max()+pd.Timedelta(hours=24)),first_evaluation_decision=str(te.decision_at.min()),fixture_epochs_override=bundle['fixture_epochs_override'])
 folder=ctx.root/'models';folder.mkdir(exist_ok=True);mp=folder/(name+'.joblib');pp=folder/(name+'.parquet');rp=folder/(name+'.json');joblib.dump(bundle,mp,compress=3);p.to_parquet(pp,index=False);rec.update(model=str(mp.relative_to(ctx.root)),predictions=str(pp.relative_to(ctx.root)));atomic_json(rp,rec);ctx.cp.commit(name,[mp,pp,rp],rec);ctx.sync([mp,pp,rp,ctx.root/'checkpoints'/(name+'.json')]);ctx.event('fit_completed',item=name,seconds=rec['seconds'],score=rec['score']['value']);return rec,p

def assemble(ctx,frame,track,task,through,years,phase):
 _,te=split_rows(frame,track,task,through,years);p=te[['track','game_id','season','week','kickoff','decision_at','information_upper_bound_at',task,*reporting_columns(track)]].copy().reset_index(drop=True);p['target']=p[task];ref=baseline(ctx,te,track,task,through,phase)
 for c in REFERENCES:p[c]=ref[c].to_numpy()
 records=[]
 for arm in ARMS[track]:
  r,q=fit(ctx,frame,track,task,arm,through,years,phase);require(p.game_id.tolist()==q.game_id.tolist() and np.array_equal(p.target,q.target),'METRIC','Forecast pairing changed');p[arm]=q.prediction.to_numpy();records.append(r)
 p['task']=task;p['phase']=phase;p=attach_reporting(p,track);return p,records

def compare(p,track,task):
 arms=REFERENCES+ARMS[track];s={a:score(p.target,p[a],task) for a in arms};c={}
 for a in ARMS[track]:c[a]=dict(relative_to_accepted=s[a]['value']/s['accepted']['value']-1,relative_to_same_features=s[a]['value']/s['same_features_linear']['value']-1,vs_references={r:paired_interval(p,p[a],p[r],task,seed=5801) for r in REFERENCES})
 for a in ARMS[track]:c[a]['brier_skill_vs_references']={r:brier_skill(p.target,p[a],p[r]) for r in REFERENCES} if task=='win' else None
 return dict(scores=s,candidates=c)
def gates(c,arm,task,folds=None):
 s=c['scores'];g={}
 for ref in REFERENCES:
  u=c['candidates'][arm]['vs_references'][ref]['upper95'];g['gain_1pct_vs_'+ref]=s[arm]['value']<=.99*s[ref]['value'];g['paired_upper_negative_vs_'+ref]=u is not None and u<0
  g['secondary_guard_vs_'+ref]=s[arm]['brier']<=s[ref]['brier'] if task=='win' else s[arm]['rmse']<=1.01*s[ref]['rmse']
  if folds is not None:g['stable_folds_vs_'+ref]=all(x[arm]['value']<=1.01*x[ref]['value'] for x in folds)
 return dict(eligible=all(g.values()),gates=g,production_promoted=False,exploratory=True)
def validation(ctx,frame):
 tables=[];records=[];rows=[]
 for track in ARMS:
  for task in TASKS:
   parts=[];folds=[]
   for year in [2022,2023]:
    p,r=assemble(ctx,frame,track,task,year-1,[year],'validation');tables.append(p);parts.append(p);records+=r;folds.append(compare(p,track,task)['scores'])
   c=compare(pd.concat(parts),track,task);rows.append(dict(track=track,task=task,**c,diagnostic_slices=diagnostic_slices(pd.concat(parts),track,task),selection={a:gates(c,a,task,folds) for a in ARMS[track]}))
 pd.concat(tables,ignore_index=True).to_parquet(ctx.root/'validation_predictions.parquet',index=False);r=dict(by_task=rows,fit_records=records,seasons=[2022,2023],already_exposed=True);atomic_json(ctx.root/'validation.json',r);selection={x['track']+'/'+x['task']:x['selection'] for x in rows};sp=ctx.root/'selection_locked.json'
 if sp.exists():require(read_json(sp)==selection,'SOURCE_STATE','Frozen development decision changed')
 else:atomic_json(sp,selection)
 ctx.sync([sp]);return r

def market_compare(p,track,task,market):
 m=market[(market.track==track)&(market.task==task)&market.season.isin(p.season.unique())].copy();require(not m.duplicated('game_id').any(),'METRIC','Duplicate market event')
 j=p.merge(m[['game_id','kickoff','target','model_prediction','market_prediction','snapshot_at']],on='game_id',validate='one_to_one',suffixes=('','_market'))
 require(len(j)>0 and np.array_equal(j.target,j.target_market) and pd.to_datetime(j.kickoff,utc=True).equals(pd.to_datetime(j.kickoff_market,utc=True)),'METRIC','Market target/kickoff mismatch');require(np.allclose(j.accepted,j.model_prediction,atol=1e-12,rtol=0),'METRIC','Market accepted prediction mismatch');require((j.information_upper_bound_at<pd.to_datetime(j.snapshot_at,utc=True)).all(),'METRIC','Feature history not strictly before quote')
 return dict(n=len(j),quotes_before_nominal_decision=int((pd.to_datetime(j.snapshot_at,utc=True)<j.decision_at).sum()),scores={a:score(j.target,j[a],task) for a in REFERENCES+ARMS[track]}|{'market':score(j.target,j.market_prediction,task)},vs_market={a:paired_interval(j,j[a],j.market_prediction,task,seed=5801) for a in ARMS[track]},brier_skill_vs_market={a:brier_skill(j.target,j[a],j.market_prediction) for a in REFERENCES+ARMS[track]} if task=='win' else None,decision_horizon_note='Nominal cutoff is NFL24h/NCAAF1h. NFL quotes are later; college quotes may be earlier than the nominal decision. Actual used history is verified before each quote, but this is not a controlled matched-horizon market-edge claim.',roi_estimated=False)
def evaluate(ctx,frame,market):
 tables=[];rows=[];slices=[];intervals=[];vp=pd.read_parquet(ctx.root/'validation_predictions.parquet')
 for track in ARMS:
  for task in TASKS:
   for end,years,phase in [(2023,[2024,2025],'holdout'),(2025,[2026],'monitor')]:
    p,r=assemble(ctx,frame,track,task,end,years,phase);tables.append(p);c=compare(p,track,task);rows.append(dict(track=track,task=task,phase=phase,**c,diagnostic_slices=diagnostic_slices(p,track,task),market=market_compare(p,track,task,market),fit_records=r,untouched_test=False))
    for yr,q in p.groupby('season'):
     for a in REFERENCES+ARMS[track]:slices.append(dict(track=track,task=task,phase=phase,season=int(yr),arm=a,**score(q.target,q[a],task)))
    if task!='win':
     cal=vp[(vp.track==track)&(vp.task==task)];ev=p.rename(columns={'decision_at':'snapshot_at'})
     for a in REFERENCES+ARMS[track]:intervals.append(dict(track=track,task=task,phase=phase,arm=a,intervals=residual_intervals(cal,ev,a)))
 out=pd.concat(tables,ignore_index=True);out.to_parquet(ctx.root/'evaluation_predictions.parquet',index=False);r=dict(by_task=rows,season_slices=slices,prediction_intervals=intervals,interval_coverage_guaranteed=False,new_live_forecasts=0,retrospective_prediction_rows=len(out));atomic_json(ctx.root/'evaluation.json',r);return r
