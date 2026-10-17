"""Frozen model-capacity test; reused linear forecasts and no baseline refits."""
import time
import numpy as np,pandas as pd,joblib
from common import require,atomic_json,read_json
from data import split_rows
from qb_features import columns as qb_columns
from efficiency import feature_columns
from families import fit_model,predict_model
from metrics import score,paired_interval,residual_intervals
TASKS=('win','margin','total');ARMS={'nfl':('hgb','mlp'),'ncaaf':('mlp',)};REFERENCES=('accepted','same_features_linear')
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
 p=te[['track','game_id','season','week','kickoff','decision_at','information_upper_bound_at',task]].copy();p['target']=p[task];p['prediction']=pr
 rec=dict(id=name,track=track,task=task,arm=arm,train_through=through,phase=phase,train_rows=len(tr),evaluation_rows=len(te),features=columns(track),seconds=time.monotonic()-start,score=score(te[task],pr,task),family_config=bundle['config'],architecture=bundle['architecture'],epochs_completed=bundle['epochs_completed'],train_latest_release=str(tr.kickoff.max()+pd.Timedelta(hours=24)),first_evaluation_decision=str(te.decision_at.min()),fixture_epochs_override=bundle['fixture_epochs_override'])
 folder=ctx.root/'models';folder.mkdir(exist_ok=True);mp=folder/(name+'.joblib');pp=folder/(name+'.parquet');rp=folder/(name+'.json');joblib.dump(bundle,mp,compress=3);p.to_parquet(pp,index=False);rec.update(model=str(mp.relative_to(ctx.root)),predictions=str(pp.relative_to(ctx.root)));atomic_json(rp,rec);ctx.cp.commit(name,[mp,pp,rp],rec);ctx.sync([mp,pp,rp,ctx.root/'checkpoints'/(name+'.json')]);ctx.event('fit_completed',item=name,seconds=rec['seconds'],score=rec['score']['value']);return rec,p

def assemble(ctx,frame,track,task,through,years,phase):
 _,te=split_rows(frame,track,task,through,years);p=te[['track','game_id','season','week','kickoff','decision_at','information_upper_bound_at',task]].copy().reset_index(drop=True);p['target']=p[task];ref=baseline(ctx,te,track,task,through,phase)
 for c in REFERENCES:p[c]=ref[c].to_numpy()
 records=[]
 for arm in ARMS[track]:
  r,q=fit(ctx,frame,track,task,arm,through,years,phase);require(p.game_id.tolist()==q.game_id.tolist() and np.array_equal(p.target,q.target),'METRIC','Forecast pairing changed');p[arm]=q.prediction.to_numpy();records.append(r)
 p['task']=task;p['phase']=phase;return p,records

def compare(p,track,task):
 arms=REFERENCES+ARMS[track];s={a:score(p.target,p[a],task) for a in arms};c={}
 for a in ARMS[track]:c[a]=dict(relative_to_accepted=s[a]['value']/s['accepted']['value']-1,relative_to_same_features=s[a]['value']/s['same_features_linear']['value']-1,vs_references={r:paired_interval(p,p[a],p[r],task,seed=5801) for r in REFERENCES})
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
   c=compare(pd.concat(parts),track,task);rows.append(dict(track=track,task=task,**c,selection={a:gates(c,a,task,folds) for a in ARMS[track]}))
 pd.concat(tables,ignore_index=True).to_parquet(ctx.root/'validation_predictions.parquet',index=False);r=dict(by_task=rows,fit_records=records,seasons=[2022,2023],already_exposed=True);atomic_json(ctx.root/'validation.json',r);selection={x['track']+'/'+x['task']:x['selection'] for x in rows};sp=ctx.root/'selection_locked.json'
 if sp.exists():require(read_json(sp)==selection,'SOURCE_STATE','Frozen development decision changed')
 else:atomic_json(sp,selection)
 ctx.sync([sp]);return r

def market_compare(p,track,task,market):
 m=market[(market.track==track)&(market.task==task)&market.season.isin(p.season.unique())].copy();require(not m.duplicated('game_id').any(),'METRIC','Duplicate market event')
 j=p.merge(m[['game_id','kickoff','target','model_prediction','market_prediction','snapshot_at']],on='game_id',validate='one_to_one',suffixes=('','_market'))
 require(len(j)>0 and np.array_equal(j.target,j.target_market) and pd.to_datetime(j.kickoff,utc=True).equals(pd.to_datetime(j.kickoff_market,utc=True)),'METRIC','Market target/kickoff mismatch');require(np.allclose(j.accepted,j.model_prediction,atol=1e-12,rtol=0),'METRIC','Market accepted prediction mismatch');require((j.information_upper_bound_at<pd.to_datetime(j.snapshot_at,utc=True)).all(),'METRIC','Feature history not strictly before quote')
 return dict(n=len(j),quotes_before_nominal_decision=int((pd.to_datetime(j.snapshot_at,utc=True)<j.decision_at).sum()),scores={a:score(j.target,j[a],task) for a in REFERENCES+ARMS[track]}|{'market':score(j.target,j.market_prediction,task)},vs_market={a:paired_interval(j,j[a],j.market_prediction,task,seed=5801) for a in ARMS[track]},decision_horizon_note='Nominal cutoff is NFL24h/NCAAF1h. NFL quotes are later; college quotes may be earlier than the nominal decision. Actual used history is verified before each quote, but this is not a controlled matched-horizon market-edge claim.',roi_estimated=False)
def evaluate(ctx,frame,market):
 tables=[];rows=[];slices=[];intervals=[];vp=pd.read_parquet(ctx.root/'validation_predictions.parquet')
 for track in ARMS:
  for task in TASKS:
   for end,years,phase in [(2023,[2024,2025],'holdout'),(2025,[2026],'monitor')]:
    p,r=assemble(ctx,frame,track,task,end,years,phase);tables.append(p);c=compare(p,track,task);rows.append(dict(track=track,task=task,phase=phase,**c,market=market_compare(p,track,task,market),fit_records=r,untouched_test=False))
    for yr,q in p.groupby('season'):
     for a in REFERENCES+ARMS[track]:slices.append(dict(track=track,task=task,phase=phase,season=int(yr),arm=a,**score(q.target,q[a],task)))
    if task!='win':
     cal=vp[(vp.track==track)&(vp.task==task)];ev=p.rename(columns={'decision_at':'snapshot_at'})
     for a in REFERENCES+ARMS[track]:intervals.append(dict(track=track,task=task,phase=phase,arm=a,intervals=residual_intervals(cal,ev,a)))
 out=pd.concat(tables,ignore_index=True);out.to_parquet(ctx.root/'evaluation_predictions.parquet',index=False);r=dict(by_task=rows,season_slices=slices,prediction_intervals=intervals,interval_coverage_guaranteed=False,new_live_forecasts=0,retrospective_prediction_rows=len(out));atomic_json(ctx.root/'evaluation.json',r);return r
