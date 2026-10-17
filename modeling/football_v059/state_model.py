"""V059 fixed Gaussian joint-score filter; no optimization or backward smoothing.

Inspired adaptation of Glickman/Stern dynamic team-strength models, not an exact
reproduction: this model separates offense/defense and models both scores, uses
fixed heuristic hyperparameters and exact conditional Gaussian filtering instead
of MCMC, and explicitly freezes each forecast before consuming later results.
"""
import copy
import math
import numpy as np
import pandas as pd
from scipy.special import ndtr, ndtri, log_ndtr, logsumexp
from threadpoolctl import threadpool_limits

ARMS=('static','dynamic')
TRACKS=('nfl','ncaaf')
FIXED_CONFIG={
 'nfl':dict(population_score_mean=22.,population_score_sd=5.,home_margin_mean=2.5,home_margin_sd=2.,team_sd=4.,observation_score_sd=10.,observation_correlation=.10,decision_lead_hours=24),
 'ncaaf':dict(population_score_mean=27.,population_score_sd=5.,home_margin_mean=3.,home_margin_sd=2.,team_sd=6.,observation_score_sd=13.,observation_correlation=.10,decision_lead_hours=1),
}
HALF_LIFE_DAYS=365.
RESULT_RELEASE_HOURS=24
METHOD_REFERENCES=['https://www.glicko.net/research/nfl.pdf','https://www.glicko.net/research/nfl-chapter.pdf']
METHOD_MEMO="""Research-informed adaptation, not a paper reproduction. Glickman and Stern
model changing football team strength with Gaussian score-difference observations,
autoregressive evolution, home advantage and uncertainty. Their original model
uses posterior simulation for unknown hyperparameters. The chapter discusses
identifiability, shrinkage and changing strengths; retrospective smoothing in its
examples is not appropriate evidence for forecasts made before outcomes.

V059 instead models a two-vector of home/away scores. Means are mu + h/2 + offense
home - defense away and mu - h/2 + offense away - defense home, with h=0 at neutral
sites. Population mean and home-margin effects have proper Gaussian priors and
are updated forward with team states. Team offense/defense priors are independent,
proper, zero-centered Gaussians. The likelihood has offset confounding; proper
priors make the conditional posterior proper, but absolute offense/defense states
are not uniquely identified by likelihood alone and are not causal player value.

The dynamic arm uses an Ornstein-Uhlenbeck transition with a 365-day half-life and
stationary team variance equal to initial team variance. This yields about 0.71
retention across a six-month gap and avoids unbounded offseason random-walk
variance. The static control sets retention=1 and process noise=0 while sharing
every prior, score likelihood, observation and prequential update. Both learn from
released earlier evaluation outcomes; static means static latent abilities, not
frozen posterior learning. Hyperparameters are fixed heuristics, not optimized,
validated or copied estimates. NFL residual margin SD is sqrt(180)=13.42 and FBS
sqrt(304.2)=17.44 before latent uncertainty. Broad team/population priors express
uncertainty; they do not prove a correctly calibrated predictive distribution.

The OU clock is indexed by assumed outcome release time (kickoff+24 hours), not
physical kickoff. A result is assimilated only when its release is strictly before
the target decision (NFL kickoff-24 hours; FBS kickoff-1 hour). Prediction projects
forward to the target outcome-release clock without mutating the filter or using
future labels. Source publication times remain unknown/null; this is a declared
retrospective availability assumption, not reconstructed historical provenance.
Only FBS-v-FBS college observations enter this state. No FCS result or feature is
used. Same-time forecasts cannot consume each other's outcomes.

The joint Gaussian is continuous and permits negative and non-football scores.
Margin/total moments are exact linear transforms of the same joint distribution.
Binary win probability uses the approximate rounded-margin non-tie event
P(M>0.5 | |M|>0.5); continuous P(M>0) and tie-band mass are also retained. Neither
is an exact score lattice or overtime model. Gaussian CRPS, NLL, interval coverage,
width and marginal negative-score mass are diagnostics, not coverage guarantees
or profitability evidence. All examined seasons remain exposed development data.
"""


def _require(ok,message):
    if not ok:raise ValueError(message)


def _utc(x):
    t=pd.Timestamp(x);_require(not pd.isna(t) and t.tzinfo is not None,'Timezone-aware timestamp required')
    return t.tz_convert('UTC')


def _config(track,arm):
    _require(track in TRACKS and arm in ARMS,'Unsupported state track/arm')
    c=copy.deepcopy(FIXED_CONFIG[track]);c.update(arm=arm,half_life_days=HALF_LIFE_DAYS if arm=='dynamic' else None,result_release_hours=RESULT_RELEASE_HOURS)
    return c


def _validate(frame,track,training):
    needed={'track','game_id','season','kickoff','home_id','away_id','neutral','completed','home_points','away_points'}
    _require(needed<=set(frame),'Missing canonical state columns')
    f=frame.copy().reset_index(drop=True)
    _require((f.track==track).all(),'Mixed or wrong state track')
    _require(not f.game_id.duplicated().any(),'Duplicate state game IDs')
    for r in f.itertuples():
        _require(isinstance(r.game_id,str) and bool(r.game_id),'Invalid state game ID')
        _require(pd.notna(r.home_id) and pd.notna(r.away_id) and bool(str(r.home_id).strip()) and bool(str(r.away_id).strip()) and str(r.home_id)!=str(r.away_id),'Invalid team identity')
        _require(isinstance(r.completed,(bool,np.bool_)),'Completion flag must be boolean')
        _require(pd.notna(r.neutral) and r.neutral in (0,1,False,True),'Invalid neutral venue flag')
        _utc(r.kickoff)
        _require(not training or r.completed,'Training outcomes must be complete')
        if r.completed:
            y=np.array([r.home_points,r.away_points],float)
            _require(np.isfinite(y).all() and (y>=0).all() and (y<=150).all() and (y%1==0).all(),'Invalid completed football scores')
        if track=='ncaaf':
            _require('home_fbs' in f and 'away_fbs' in f and r.home_fbs==1 and r.away_fbs==1,'Only FBS-v-FBS observations are permitted')
    return f


class _Filter:
    """Exact linear Gaussian filtering conditional on the fixed specification."""
    def __init__(self,config):
        self.config=copy.deepcopy(config);self.mean=np.array([config['population_score_mean'],config['home_margin_mean']],float)
        self.cov=np.diag([config['population_score_sd']**2,config['home_margin_sd']**2]);self.teams={};self.team_games={};self.clock=None;self.updates=0
        v=config['observation_score_sd']**2;self.noise=v*np.array([[1.,config['observation_correlation']],[config['observation_correlation'],1.]])
    def ensure_team(self,team):
        team=str(team)
        if team not in self.teams:
            n=len(self.mean);self.teams[team]=(n,n+1);self.team_games[team]=0
            self.mean=np.pad(self.mean,(0,2));new=np.zeros((n+2,n+2));new[:n,:n]=self.cov;new[n,n]=new[n+1,n+1]=self.config['team_sd']**2;self.cov=new
    def design(self,home,away,neutral):
        self.ensure_team(home);self.ensure_team(away);h=np.zeros((2,len(self.mean)));h[:,0]=1.;h[:,1]=[0.,0.] if neutral else [.5,-.5]
        ho,hd=self.teams[str(home)];ao,ad=self.teams[str(away)];h[0,ho]=1.;h[0,ad]=-1.;h[1,ao]=1.;h[1,hd]=-1.;return h
    def moments_at(self,at):
        at=_utc(at);_require(self.clock is None or at>=self.clock,'Filter clock cannot move backward')
        if self.clock is None or self.config['arm']=='static':return self.mean.copy(),self.cov.copy()
        days=(at-self.clock).total_seconds()/86400.;rho=math.exp(-math.log(2)*days/self.config['half_life_days']);scale=np.ones(len(self.mean));scale[2:]=rho
        m=self.mean*scale;p=self.cov*scale[:,None]*scale[None,:]
        ix=np.arange(2,len(self.mean));p[ix,ix]+=self.config['team_sd']**2*(-math.expm1(-2*math.log(2)*days/self.config['half_life_days']))
        return m,p
    def predict(self,home,away,neutral,target_release):
        # A new participant receives a temporary exchangeable prior. Forecasting
        # must not expand or otherwise mutate the persistent filtering state.
        work=self
        if str(home) not in self.teams or str(away) not in self.teams:
            work=copy.copy(self);work.mean=self.mean.copy();work.cov=self.cov.copy();work.teams=dict(self.teams);work.team_games=dict(self.team_games)
        h=work.design(home,away,neutral);m,p=work.moments_at(target_release);mu=h@m;cov=h@p@h.T+work.noise;cov=(cov+cov.T)/2
        _require(np.isfinite(mu).all() and np.isfinite(cov).all(),'Nonfinite predictive moments');np.linalg.cholesky(cov)
        return mu,cov
    def update(self,row,release):
        h=self.design(row.home_id,row.away_id,bool(row.neutral));m,p=self.moments_at(release);y=np.array([row.home_points,row.away_points],float)
        cross=p@h.T;s=h@cross+self.noise;s=(s+s.T)/2;np.linalg.cholesky(s)
        gain=np.linalg.solve(s,cross.T).T;self.mean=m+gain@(y-h@m);self.cov=p-gain@cross.T;self.cov=(self.cov+self.cov.T)/2
        _require(np.isfinite(self.mean).all() and np.isfinite(self.cov).all() and (np.diag(self.cov)>=-1e-8).all(),'Invalid posterior moments')
        self.clock=_utc(release);self.updates+=1;self.team_games[str(row.home_id)]+=1;self.team_games[str(row.away_id)]+=1
    def dump(self):
        return dict(config=copy.deepcopy(self.config),mean=self.mean.tolist(),covariance=self.cov.tolist(),team_indices={k:list(v) for k,v in self.teams.items()},team_games=dict(self.team_games),last_consumed_release=None if self.clock is None else self.clock.isoformat(),updates=self.updates,source_publication_at=None,strict_point_in_time_verified=False)


def project_scores(mean,cov):
    mean=np.asarray(mean,float);cov=np.asarray(cov,float)
    _require(mean.shape==(2,) and cov.shape==(2,2) and np.isfinite(mean).all() and np.isfinite(cov).all() and np.allclose(cov,cov.T,rtol=0,atol=1e-9),'Invalid joint-score moments')
    np.linalg.cholesky(cov)
    margin=float(mean[0]-mean[1]);total=float(mean.sum());mv=float(cov[0,0]+cov[1,1]-2*cov[0,1]);tv=float(cov[0,0]+cov[1,1]+2*cov[0,1]);sd=math.sqrt(mv)
    log_home=float(log_ndtr((margin-.5)/sd));log_away=float(log_ndtr((-margin-.5)/sd));den=float(logsumexp([log_home,log_away]));conditional=float(math.exp(log_home-den))
    tie=float(max(0.,ndtr((.5-margin)/sd)-ndtr((-.5-margin)/sd)))
    return dict(home_mean=float(mean[0]),away_mean=float(mean[1]),cov_hh=float(cov[0,0]),cov_ha=float(cov[0,1]),cov_aa=float(cov[1,1]),margin_mean=margin,margin_var=mv,total_mean=total,total_var=tv,win_probability=float(np.clip(conditional,1e-7,1-1e-7)),continuous_win_probability=float(ndtr(margin/sd)),tie_probability_approx=tie,home_win_probability_approx=float(math.exp(log_home)),away_win_probability_approx=float(math.exp(log_away)),negative_home_score_probability=float(ndtr(-mean[0]/math.sqrt(cov[0,0]))),negative_away_score_probability=float(ndtr(-mean[1]/math.sqrt(cov[1,1]))))


def fit_predict(train_frame,eval_frame,track,arm,through=None,years=None,progress=None):
    """One joint-state fit with declared forward evaluation learning.

    Returns predictions in the original evaluation row order, serializable final
    state and diagnostics. All score heads share the same state; this is one fit.
    The caller owns fit reservation/checkpointing and should count one attempt.
    """
    config=_config(track,arm);train=_validate(train_frame,track,True);evaluation=_validate(eval_frame,track,False)
    _require(len(evaluation)>0,'No evaluation games');_require(set(train.game_id).isdisjoint(evaluation.game_id),'Training/evaluation IDs overlap')
    if through is not None:_require((train.season<=through).all(),'Training exceeds declared through season')
    if years is not None:_require(evaluation.season.isin(list(years)).all(),'Evaluation outside declared years')
    evaluation['decision_at']=pd.to_datetime(evaluation.kickoff,utc=True)-pd.Timedelta(hours=config['decision_lead_hours'])
    first_decision=evaluation.decision_at.min();release=lambda r:_utc(r.kickoff)+pd.Timedelta(hours=RESULT_RELEASE_HOURS)
    train_events=sorted([(release(r),str(r.game_id),r) for r in train.itertuples()],key=lambda x:(x[0],x[1]))
    _require(not train_events or train_events[-1][0]<first_decision,'Training release is not strictly before first decision')
    pending=sorted([(release(r),str(r.game_id),r) for r in evaluation.itertuples() if r.completed],key=lambda x:(x[0],x[1]));position=0
    state=_Filter(config);output={};notify=progress if progress is not None else lambda done,total:None
    _require(callable(notify),'Progress callback must be callable');total=len(train_events)+len(evaluation);done=0;notify(done,total)
    with threadpool_limits(limits=2):
        for t,_,row in train_events:
            state.update(row,t);done+=1
            if done%100==0:notify(done,total)
        for row in evaluation.sort_values(['decision_at','game_id']).itertuples():
            cutoff=_utc(row.decision_at)
            while position<len(pending) and pending[position][0]<cutoff:
                t,_,old=pending[position];state.update(old,t);position+=1
                if position%100==0:notify(done,total)
            _require(state.clock is None or state.clock<cutoff,'Consumed result at/after forecast decision')
            mean,cov=state.predict(row.home_id,row.away_id,bool(row.neutral),release(row));rec=project_scores(mean,cov)
            rec.update(decision_at=cutoff,information_upper_bound_at=state.clock,forecast_state_at=release(row),home_state_games=state.team_games.get(str(row.home_id),0),away_state_games=state.team_games.get(str(row.away_id),0),source_publication_at=None,strict_point_in_time_verified=False,prequential_eval_results_consumed=position)
            output[row.Index]=rec;done+=1
            if done%100==0:notify(done,total)
    notify(total,total)
    result=evaluation.copy()
    for key in next(iter(output.values())):result[key]=[output[i][key] for i in range(len(evaluation))]
    diagnostics=dict(track=track,arm=arm,joint_fit_attempts=1,train_games=len(train),evaluation_games=len(evaluation),training_updates=len(train_events),evaluation_results_consumed=position,evaluation_results_unconsumed=len(pending)-position,team_states=len(state.teams),latent_dimensions=len(state.mean),latest_training_release=None if not train_events else train_events[-1][0].isoformat(),first_evaluation_decision=first_decision.isoformat(),prequential_evaluation_learning=True,backward_smoothing=False,hyperparameter_optimization=False,fcs_observations=0,config=config,source_publication_at=None,strict_point_in_time_verified=False,conditional_model='Gaussian posterior conditional on fixed heuristic parameters and proper priors',identifiability='Proper priors identify posterior; offense/defense likelihood offsets remain confounded',win_probability_definition='P(M>0.5 | abs(M)>0.5), rounded-margin non-tie approximation; not exact overtime/scoring model')
    return result,state.dump(),diagnostics


def gaussian_crps(y,mean,variance):
    y=np.asarray(y,float);mean=np.asarray(mean,float);variance=np.asarray(variance,float)
    _require(y.shape==mean.shape==variance.shape and y.size>0 and np.isfinite(y).all() and np.isfinite(mean).all() and np.isfinite(variance).all() and (variance>0).all(),'Invalid Gaussian CRPS arrays')
    sd=np.sqrt(variance);z=(y-mean)/sd;phi=np.exp(-.5*z*z)/math.sqrt(2*math.pi)
    return sd*(z*(2*ndtr(z)-1)+2*phi-1/math.sqrt(math.pi))


def distribution_scores(yhome,yaway,p):
    """Joint NLL and marginal proper/interval diagnostics; no score truncation."""
    yh=np.asarray(yhome,float);ya=np.asarray(yaway,float)
    _require(yh.ndim==1 and len(yh)>0 and yh.shape==ya.shape and len(p)==len(yh) and np.isfinite(yh).all() and np.isfinite(ya).all(),'Invalid distribution targets')
    needed=['home_mean','away_mean','cov_hh','cov_ha','cov_aa','margin_mean','margin_var','total_mean','total_var']
    _require(set(needed)<=set(p),'Missing predictive distribution columns');q=p[needed].to_numpy(float);_require(np.isfinite(q).all(),'Nonfinite predictive distribution')
    hh=p.cov_hh.to_numpy(float);ha=p.cov_ha.to_numpy(float);aa=p.cov_aa.to_numpy(float);det=hh*aa-ha*ha
    _require((hh>0).all() and (aa>0).all() and (det>0).all(),'Nonpositive joint covariance')
    _require(np.allclose(p.margin_mean,p.home_mean-p.away_mean,rtol=1e-10,atol=1e-10) and np.allclose(p.total_mean,p.home_mean+p.away_mean,rtol=1e-10,atol=1e-10) and np.allclose(p.margin_var,hh+aa-2*ha,rtol=1e-10,atol=1e-10) and np.allclose(p.total_var,hh+aa+2*ha,rtol=1e-10,atol=1e-10),'Incoherent joint-score transformations')
    dh=yh-p.home_mean.to_numpy(float);da=ya-p.away_mean.to_numpy(float);quad=(aa*dh*dh-2*ha*dh*da+hh*da*da)/det
    out=dict(n=len(yh),joint_gaussian_nll=float(np.mean(.5*(2*math.log(2*math.pi)+np.log(det)+quad))),margin={},total={})
    for task,target in [('margin',yh-ya),('total',yh+ya)]:
        mean=p[task+'_mean'].to_numpy(float);var=p[task+'_var'].to_numpy(float);sd=np.sqrt(var);intervals=[]
        for coverage in [.80,.95]:
            z=float(ndtri((1+coverage)/2));lo=mean-z*sd;hi=mean+z*sd;alpha=1-coverage
            interval_score=(hi-lo)+2/alpha*(lo-target)*(target<lo)+2/alpha*(target-hi)*(target>hi)
            intervals.append(dict(nominal_coverage=coverage,empirical_coverage=float(np.mean((target>=lo)&(target<=hi))),mean_width=float(np.mean(hi-lo)),mean_interval_score=float(np.mean(interval_score)),coverage_guaranteed=False))
        out[task]=dict(gaussian_crps=float(np.mean(gaussian_crps(target,mean,var))),gaussian_nll=float(np.mean(.5*(np.log(2*math.pi*var)+(target-mean)**2/var))),intervals=intervals)
    home_mass=ndtr(-p.home_mean.to_numpy(float)/np.sqrt(hh));away_mass=ndtr(-p.away_mean.to_numpy(float)/np.sqrt(aa))
    out['negative_score_mass']=dict(home_marginal_mean=float(home_mass.mean()),away_marginal_mean=float(away_mass.mean()),any_negative_union_bound_mean=float(np.minimum(1,home_mass+away_mass).mean()),joint_probability_not_computed=True,scores_not_truncated=True)
    out['assumptions']=['Continuous joint Gaussian permits negative/non-football scores.','Intervals include latent-state uncertainty and observation noise; coverage is not guaranteed.','Binary win uses rounded-margin conditional non-tie probability; tied observations still update the score state.','Conditional fixed-hyperparameter uncertainty omits parameter-selection/model-misspecification uncertainty.']
    return out
