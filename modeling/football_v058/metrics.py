"""Proper scores, discrimination, calibration, point and interval diagnostics."""
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score
from common import require

def loss(y,p,task,metric=None):
 y=np.asarray(y,float);p=np.asarray(p,float)
 require(len(y)>0 and y.shape==p.shape and np.isfinite(y).all() and np.isfinite(p).all(),'METRIC','Invalid scoring arrays')
 if task=='win':
  require(set(np.unique(y))<={0.,1.} and ((p>0)&(p<1)).all(),'METRIC','Invalid binary probabilities/outcomes')
  return (p-y)**2 if metric=='brier' else -(y*np.log(p)+(1-y)*np.log1p(-p))
 return (p-y)**2 if metric=='squared_error' else np.abs(p-y)

def calibration(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);bins=np.minimum((p*10).astype(int),9);rows=[]
 for b in range(10):
  mask=bins==b;n=int(mask.sum())
  if not n:continue
  observed=float(y[mask].mean());mean=float(p[mask].mean());z=1.95996398454;den=1+z*z/n;center=(observed+z*z/(2*n))/den;half=z*np.sqrt(observed*(1-observed)/n+z*z/(4*n*n))/den
  rows.append(dict(bin=b,n=n,predicted=mean,observed=observed,observed_wilson_low=float(max(0,center-half)),observed_wilson_high=float(min(1,center+half))))
 return rows

def score(y,p,task):
 y=np.asarray(y,float);p=np.asarray(p,float);primary=loss(y,p,task);r=dict(n=len(y),metric='log_loss' if task=='win' else 'mae',value=float(primary.mean()))
 if task=='win':
  bins=calibration(y,p);r.update(brier=float(loss(y,p,task,'brier').mean()),auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,accuracy=float(((p>=.5)==y).mean()),base_rate=float(y.mean()),mean_probability=float(p.mean()),probability_bias=float((p-y).mean()),ece10=float(sum(x['n']*abs(x['predicted']-x['observed']) for x in bins)/len(y)),calibration=bins)
 else:r.update(rmse=float(np.sqrt(np.mean((p-y)**2))),median_absolute_error=float(np.median(primary)),p90_absolute_error=float(np.quantile(primary,.9)),bias=float((p-y).mean()))
 return r

def paired_interval(frame,candidate,reference,task,metric=None,seed=5601):
 delta=loss(frame.target,candidate,task,metric)-loss(frame.target,reference,task,metric)
 q=pd.DataFrame(dict(block=frame.season.astype(str)+'-'+frame.week.astype(str),delta=delta));s=q.groupby('block').delta.agg(['sum','count']).to_numpy()
 if len(s)<8:return dict(difference=float(delta.mean()),lower95=None,upper95=None,blocks=len(s),replicates=0,status='insufficient_blocks',method='At least eight season-week blocks required; no confidence interval asserted')
 rng=np.random.default_rng(seed);ix=rng.integers(0,len(s),size=(1000,len(s)));draws=s[ix,0].sum(axis=1)/s[ix,1].sum(axis=1)
 return dict(difference=float(delta.mean()),lower95=float(np.quantile(draws,.025)),upper95=float(np.quantile(draws,.975)),blocks=len(s),replicates=1000,method='paired season-week bootstrap; descriptive after development, no multiplicity guarantee')

def interval_score(y,lower,upper,alpha):
 y=np.asarray(y,float);lower=np.asarray(lower,float);upper=np.asarray(upper,float)
 require(0<alpha<1 and y.shape==lower.shape==upper.shape and np.isfinite(y).all() and np.isfinite(lower).all() and np.isfinite(upper).all() and (lower<=upper).all(),'METRIC','Invalid prediction intervals')
 return upper-lower+2/alpha*(lower-y)*(y<lower)+2/alpha*(y-upper)*(y>upper)

def residual_intervals(calibration_frame,evaluation,arm):
 require(len(calibration_frame)>=40,'METRIC','Too little chronological interval calibration')
 require(pd.to_datetime(calibration_frame.kickoff,utc=True).max()+pd.Timedelta(hours=24)<pd.to_datetime(evaluation.snapshot_at,utc=True).min(),'METRIC','Interval calibration overlaps evaluation')
 residual=calibration_frame.target.to_numpy()-calibration_frame[arm].to_numpy();p=evaluation[arm].to_numpy();y=evaluation.target.to_numpy();out=[]
 for alpha in [.2,.1]:
  lo,hi=np.quantile(residual,[alpha/2,1-alpha/2],method='inverted_cdf');lower=p+lo;upper=p+hi
  out.append(dict(nominal_coverage=1-alpha,coverage=float(((y>=lower)&(y<=upper)).mean()),mean_width=float(hi-lo),mean_interval_score=float(interval_score(y,lower,upper,alpha).mean()),calibration_rows=len(residual),evaluation_rows=len(y),residual_lower=float(lo),residual_upper=float(hi),method='chronological empirical residual intervals; no exchangeability or guaranteed-coverage claim'))
 return out


def brier_skill(y,p,reference):
 """Same-row Brier skill: 1 - candidate Brier / reference Brier.

 Endpoint probabilities are valid for this Brier-only calculation. A perfect
 reference makes relative skill undefined; it is never replaced by an epsilon.
 """
 y=np.asarray(y,float);p=np.asarray(p,float);reference=np.asarray(reference,float)
 require(y.ndim==1 and len(y)>0 and y.shape==p.shape==reference.shape and np.isfinite(y).all() and np.isfinite(p).all() and np.isfinite(reference).all(),'METRIC','Invalid aligned Brier skill arrays')
 require(set(np.unique(y))<={0.,1.} and ((p>=0)&(p<=1)).all() and ((reference>=0)&(reference<=1)).all(),'METRIC','Invalid Brier skill probabilities/outcomes')
 candidate_brier=float(np.mean((p-y)**2));reference_brier=float(np.mean((reference-y)**2))
 return dict(n=len(y),value=None if reference_brier==0 else float(1-candidate_brier/reference_brier),candidate_brier=candidate_brier,reference_brier=reference_brier,reason='zero_reference_brier' if reference_brier==0 else None,formula='1 - candidate_brier / reference_brier',same_cohort=True)
