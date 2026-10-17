"""NFL neutral-situation, attack-type histories; cache-only retrospective research.

This is distinct from V048's situation-blind game averages. All seven measures
use regulation Q1-Q3, absolute pre-play score differential <=8, and more than
120 seconds left in the half. Early-down measures use down1/2 only. Dropbacks
include sacks and scrambles; designed runs exclude all identified dropbacks.
No provider EPA, win-probability model, pace proxy or upcoming-starter claim.

Game data is assumed released at kickoff+24h and can affect predictions only
strictly before kickoff-24h. Unknown publication times remain null. Histories
use at most eight completed team games within365days, with100opportunity prior
shrinkage. Additive opponent adjustment is computed from strictly earlier
release groups; same-release games never inform each other. Adjusted rate
indices are not probabilities and can lie outside[0,1]. All settings are fixed
heuristics, not fitted or tuned estimates of optimal football parameters.
"""
from collections import Counter, defaultdict
import re
import numpy as np
import pandas as pd
from common import require
from data import FEATURES, ALIASES

RAW_COLUMNS = ['game_id','play_id','posteam','defteam','play_type','down','ydstogo',
 'yards_gained','qb_dropback','qb_scramble','sack','qb_kneel','qb_spike','penalty',
 'play_deleted','two_point_attempt','qtr','half_seconds_remaining','score_differential']
REQUIRED_COLUMNS = RAW_COLUMNS
METRICS = ('ed_dropback_ypp','ed_dropback_success','ed_run_ypp','ed_run_success',
           'neutral_dropback_share','neutral_dropback_explosive','neutral_run_explosive')
FALLBACK = dict(zip(METRICS,(6.,.45,4.2,.40,.58,.08,.10)))
CONTROLS = ('prior_games_scaled','ed_dropbacks_scaled','ed_runs_scaled','neutral_plays_scaled')
PRIOR_OPPORTUNITIES = 100.
MAX_HISTORY_GAMES = 8
MAX_HISTORY_DAYS = 365
NFL_TEAMS = set('ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS'.split())
STATS = [x for m in METRICS for x in (m+'_sum',m+'_n')]
PANEL_COLUMNS = ['game_id','team_id','opponent_id','kickoff','available_at',
 'neutral_plays','ed_dropbacks','ed_runs',*STATS,'source_publication_at','strict_point_in_time_verified']


def feature_columns():
 return list(FEATURES)+['sit_'+side+'_'+unit+'_'+m for side in ('home','away') for unit in ('off','allowed') for m in METRICS]+['sit_'+side+'_'+c for side in ('home','away') for c in CONTROLS]


def _team(value):return ALIASES.get(str(value),str(value))


def _canonical(frame):
 needed={'track','game_id','home_id','away_id','kickoff','completed'}
 require(needed<=set(frame),'SCHEMA','Missing canonical identity fields')
 f=frame.loc[frame.track=='nfl'].copy()
 require(not f.game_id.duplicated().any(),'DATA','Duplicate canonical NFL game')
 for r in f.itertuples():
  gid=str(r.game_id);bits=gid.split('_');h,a=_team(r.home_id),_team(r.away_id)
  require(bool(re.fullmatch(r'\d{4}_\d{2}_[A-Z]{2,3}_[A-Z]{2,3}',gid)),'DATA','Malformed NFL game ID')
  require(h in NFL_TEAMS and a in NFL_TEAMS and h!=a and _team(bits[2])==a and _team(bits[3])==h,'DATA','Canonical game/team identity mismatch')
  require(getattr(r,'season',int(bits[0]))==int(bits[0]) and getattr(r,'week',int(bits[1]))==int(bits[1]),'DATA','Canonical season/week identity mismatch')
  t=pd.Timestamp(r.kickoff);require(pd.notna(t) and t.tzinfo is not None,'DATA','Timezone-aware kickoff required')
  require(isinstance(r.completed,(bool,np.bool_)),'DATA','Canonical completed must be boolean')
 f['kickoff']=pd.to_datetime(f.kickoff,utc=True)
 return f


def aggregate_pbp(raw,canonical):
 """One row per observed completed team/game; quarantine malformed source rows.

 Exact duplicates count once. A conflicting duplicate play key quarantines the
 entire game, preventing biased partial game summaries. Out-of-canonical and
 unfinished game rows are explicitly excluded, not silently relabeled.
 """
 require(set(RAW_COLUMNS)<=set(raw),'SCHEMA','Missing required situation PBP columns')
 canon=_canonical(canonical);done=canon[canon.completed]
 d=raw[RAW_COLUMNS].copy().reset_index(drop=True);d['_source_row']=np.arange(len(d))
 audit=Counter(input_rows=len(d));bad=[]
 def reject(mask,reason):
  nonlocal d
  x=d.loc[mask]
  bad.extend(dict(source_row=int(r['_source_row']),game_id=str(r['game_id']),play_id=str(r['play_id']),reason=reason) for r in x.to_dict('records'))
  audit['quarantine_'+reason]+=len(x);d=d.loc[~mask].copy()
 scope=d.game_id.isin(canon.game_id);audit['noncanonical_rows_excluded']=int((~scope).sum());d=d.loc[scope].copy()
 completed=d.game_id.isin(done.game_id);audit['unfinished_game_rows_excluded']=int((~completed).sum());d=d.loc[completed].copy()
 ids=pd.to_numeric(d.play_id,errors='coerce');reject(~np.isfinite(ids)|(ids<0)|(ids%1!=0),'invalid_play_id')
 exact=d.duplicated(RAW_COLUMNS);audit['identical_duplicates_removed']=int(exact.sum());d=d.loc[~exact].copy()
 conflict=d.duplicated(['game_id','play_id'],keep=False);conflict_games=set(d.loc[conflict,'game_id']);audit['conflicting_duplicate_games']=len(conflict_games)
 reject(d.game_id.isin(conflict_games),'conflicting_duplicate_game')
 observed=set(d.game_id)
 plays=d.play_type.isin(['pass','run']);audit['non_offensive_rows_excluded']=int((~plays).sum());d=d.loc[plays].copy()
 flags=['qb_dropback','qb_scramble','sack','qb_kneel','qb_spike','penalty','play_deleted','two_point_attempt']
 for c in flags:d[c]=pd.to_numeric(d[c],errors='coerce')
 reject(~d[flags].isin([0,1]).all(axis=1),'invalid_binary_flags')
 excluded=(d[['qb_kneel','qb_spike','penalty','play_deleted','two_point_attempt']]==1).any(axis=1)
 audit['administrative_or_penalty_plays_excluded']=int(excluded.sum());d=d.loc[~excluded].copy()
 d=d.merge(done[['game_id','home_id','away_id']],on='game_id',validate='many_to_one',how='left')
 for c in ['posteam','defteam','home_id','away_id']:d[c]=d[c].map(_team)
 identity=((d.posteam==d.home_id)&(d.defteam==d.away_id))|((d.posteam==d.away_id)&(d.defteam==d.home_id))
 reject(~identity,'game_team_mismatch')
 impossible=((d.play_type=='pass')&(d.qb_dropback!=1))|((d.qb_scramble==1)&((d.qb_dropback!=1)|(d.play_type!='run')))|((d.sack==1)&((d.qb_dropback!=1)|(d.play_type!='pass')))|((d.play_type=='run')&(d.qb_dropback==1)&(d.qb_scramble!=1))
 reject(impossible,'inconsistent_attack_flags')
 numeric=['down','ydstogo','yards_gained','qtr','half_seconds_remaining','score_differential']
 for c in numeric:d[c]=pd.to_numeric(d[c],errors='coerce')
 invalid=(~np.isfinite(d[numeric]).all(axis=1))|(~d.down.isin([1,2,3,4]))|(d.ydstogo<=0)|(d.ydstogo>100)|(d.yards_gained.abs()>99)|(d.qtr<1)|(d.qtr>10)|(d.qtr%1!=0)|(d.half_seconds_remaining<0)|(d.half_seconds_remaining>1800)|(d.score_differential.abs()>99)
 reject(invalid,'invalid_situation_values')
 neutral=(d.qtr<=3)&(d.score_differential.abs()<=8)&(d.half_seconds_remaining>120)
 audit['nonneutral_plays_excluded']=int((~neutral).sum());d=d.loc[neutral].copy()
 ed=d.down.isin([1,2]);db=d.qb_dropback.eq(1);run=~db
 success=d.yards_gained>=np.where(d.down.eq(1),.4,.6)*d.ydstogo
 selectors=[ed&db,ed&db,ed&run,ed&run,pd.Series(True,index=d.index),db,run]
 values=[d.yards_gained,success.astype(float),d.yards_gained,success.astype(float),db.astype(float),(d.yards_gained>=20).astype(float),(d.yards_gained>=10).astype(float)]
 for m,mask,value in zip(METRICS,selectors,values):d[m+'_sum']=np.where(mask,value,0.);d[m+'_n']=mask.astype(int)
 d['neutral_plays']=1;d['ed_dropbacks']=(ed&db).astype(int);d['ed_runs']=(ed&run).astype(int)
 sums=d.groupby(['game_id','posteam'],sort=True)[['neutral_plays','ed_dropbacks','ed_runs',*STATS]].sum()
 out=[]
 for g in done[done.game_id.isin(observed)].itertuples():
  for team,opp in [(_team(g.home_id),_team(g.away_id)),(_team(g.away_id),_team(g.home_id))]:
   row=dict(game_id=g.game_id,team_id=team,opponent_id=opp,kickoff=g.kickoff,available_at=g.kickoff+pd.Timedelta(hours=24),source_publication_at=None,strict_point_in_time_verified=False)
   row.update(sums.loc[(g.game_id,team)].to_dict() if (g.game_id,team) in sums.index else {c:0. for c in ['neutral_plays','ed_dropbacks','ed_runs',*STATS]});out.append(row)
 panel=pd.DataFrame(out,columns=PANEL_COLUMNS);audit.update(accepted_neutral_plays=len(d),accepted_early_dropbacks=int((ed&db).sum()),accepted_early_runs=int((ed&run).sum()),observed_games=len(observed),team_games=len(panel))
 return panel,dict(counts=dict(audit),metric_definitions=list(METRICS),source_publication_at=None,strict_point_in_time_verified=False),pd.DataFrame(bad,columns=['source_row','game_id','play_id','reason'])


def _checked_panel(panel,canon):
 require(set(PANEL_COLUMNS)<=set(panel),'SCHEMA','Incomplete situation panel')
 require(not panel.duplicated(['game_id','team_id']).any(),'DATA','Duplicate situation team/game')
 known={r.game_id:r for r in canon.itertuples()};by={}
 for r in panel.itertuples():
  require(r.game_id in known,'DATA','Noncanonical situation game');g=known[r.game_id]
  require(g.completed and {r.team_id,r.opponent_id}=={_team(g.home_id),_team(g.away_id)} and r.team_id!=r.opponent_id,'DATA','Panel game/team mismatch')
  require(pd.Timestamp(r.kickoff)==g.kickoff and pd.Timestamp(r.available_at)==g.kickoff+pd.Timedelta(hours=24),'DATA','Panel release mismatch')
  require(pd.isna(r.source_publication_at) and not r.strict_point_in_time_verified,'DATA','Unsupported source-publication claim')
  values=np.array([getattr(r,c) for c in ['neutral_plays','ed_dropbacks','ed_runs',*STATS]],dtype=float)
  require(np.isfinite(values).all(),'DATA','Nonfinite panel statistics')
  counts=[r.neutral_plays,r.ed_dropbacks,r.ed_runs]+[getattr(r,m+'_n') for m in METRICS]
  require(all(x>=0 and x%1==0 for x in counts),'DATA','Invalid opportunity counts')
  require(r.ed_dropbacks+r.ed_runs<=r.neutral_plays,'DATA','Early opportunities exceed neutral plays')
  for m in METRICS:
   n=getattr(r,m+'_n');s=getattr(r,m+'_sum')
   require(n<=r.neutral_plays and (abs(s)<=99*n if m.endswith('ypp') else 0<=s<=n),'DATA','Impossible metric sum/denominator')
  require(r.ed_dropback_ypp_n==r.ed_dropback_success_n==r.ed_dropbacks and r.ed_run_ypp_n==r.ed_run_success_n==r.ed_runs and r.neutral_dropback_share_n==r.neutral_plays,'DATA','Metric opportunity mismatch')
  require(r.neutral_dropback_explosive_n+r.neutral_run_explosive_n==r.neutral_plays and r.neutral_dropback_share_sum==r.neutral_dropback_explosive_n,'DATA','Attack opportunity mismatch')
  by[(r.game_id,r.team_id)]=r
 for gid in set(panel.game_id):require(sum(k[0]==gid for k in by)==2,'DATA','Unpaired situation game')
 return by


def build_features(frame,panel):
 """Preserve upstream rows/columns and append52-column NFL representation."""
 f=frame.copy();canon=_canonical(f)
 require(f.index.is_unique and set(FEATURES)<=set(f),'DATA','Upstream index/baseline schema invalid')
 require(np.isfinite(f.loc[f.track=='nfl',FEATURES].to_numpy(float)).all(),'DATA','Invalid upstream baseline values')
 by=_checked_panel(panel,canon);state=defaultdict(list);league_sum=Counter();league_n=Counter();pos=0;latest=None
 groups=list(canon[canon.completed].assign(release=lambda d:d.kickoff+pd.Timedelta(hours=24)).sort_values(['release','game_id']).groupby('release',sort=True))
 newcols=feature_columns()[len(FEATURES):]
 for c in newcols:f[c]=np.nan
 f['situation_decision_at']=pd.NaT;f['situation_max_available_at']=pd.NaT
 f['situation_decision_at']=pd.to_datetime(f.situation_decision_at,utc=True);f['situation_max_available_at']=pd.to_datetime(f.situation_max_available_at,utc=True)
 provenance=[];updates=0;missing_games=0
 def prior():return {m:league_sum[m]/league_n[m] if league_n[m] else FALLBACK[m] for m in METRICS}
 def history(team,t):return [x for x in state[team] if x['kickoff']>=t-pd.Timedelta(days=MAX_HISTORY_DAYS)][-MAX_HISTORY_GAMES:]
 def pooled(items,unit,p,kind):
  return {m:(sum(x[kind+'_'+unit+'_sum'][m] for x in items)+PRIOR_OPPORTUNITIES*p[m])/(sum(x[unit+'_n'][m] for x in items)+PRIOR_OPPORTUNITIES) for m in METRICS}
 def stat(gid,team):
  row=by.get((gid,team))
  return ({m:float(getattr(row,m+'_sum')) for m in METRICS},{m:float(getattr(row,m+'_n')) for m in METRICS},row) if row else ({m:0. for m in METRICS},{m:0. for m in METRICS},None)
 for idx,g in canon.sort_values(['kickoff','game_id'],kind='stable').iterrows():
  cutoff=g.kickoff-pd.Timedelta(hours=24)
  while pos<len(groups) and groups[pos][0]<cutoff:
   release,games=groups[pos];pos+=1;p=prior();pending=[]
   # All opponents in this release group see exactly the pre-group state.
   for old in games.itertuples():
    h,a=_team(old.home_id),_team(old.away_id)
    hs,hn,hr=stat(old.game_id,h);as_,an,ar=stat(old.game_id,a)
    if hr is None or ar is None:missing_games+=1
    profiles={t:{unit:pooled(history(t,release),unit,p,'raw') for unit in ('off','allowed')} for t in (h,a)}
    for team,opp,own_s,own_n,opp_s,opp_n,row in [(h,a,hs,hn,as_,an,hr),(a,h,as_,an,hs,hn,ar)]:
     adjusted_off={m:own_s[m]+own_n[m]*(p[m]-profiles[opp]['allowed'][m]) for m in METRICS}
     adjusted_allowed={m:opp_s[m]+opp_n[m]*(p[m]-profiles[opp]['off'][m]) for m in METRICS}
     pending.append((team,dict(game_id=old.game_id,kickoff=old.kickoff,available_at=release,raw_off_sum=own_s,raw_allowed_sum=opp_s,adj_off_sum=adjusted_off,adj_allowed_sum=adjusted_allowed,off_n=own_n,allowed_n=opp_n,neutral_plays=float(row.neutral_plays) if row else 0.,ed_dropbacks=float(row.ed_dropbacks) if row else 0.,ed_runs=float(row.ed_runs) if row else 0.,source_present=row is not None)))
   for team,item in pending:
    state[team].append(item);league_sum.update(item['raw_off_sum']);league_n.update(item['off_n']);updates+=1
   latest=release
  p=prior();prov=dict(game_id=g.game_id,decision_at=cutoff,league_latest_release=latest,source_publication_at=None,strict_point_in_time_verified=False)
  for side,team in [('home',_team(g.home_id)),('away',_team(g.away_id))]:
   items=history(team,cutoff)
   for unit in ('off','allowed'):
    value=pooled(items,unit,p,'adj')
    for m in METRICS:f.loc[idx,'sit_'+side+'_'+unit+'_'+m]=value[m]
   controls=dict(prior_games_scaled=len(items)/8.,ed_dropbacks_scaled=min(sum(x['ed_dropbacks'] for x in items),400.)/400.,ed_runs_scaled=min(sum(x['ed_runs'] for x in items),400.)/400.,neutral_plays_scaled=min(sum(x['neutral_plays'] for x in items),800.)/800.)
   for c,value in controls.items():f.loc[idx,'sit_'+side+'_'+c]=value
   prov[side+'_history_game_ids']=[x['game_id'] for x in items];prov[side+'_history_latest_release']=max([x['available_at'] for x in items],default=None);prov[side+'_covered_history_games']=sum(x['source_present'] for x in items)
  f.loc[idx,'situation_decision_at']=cutoff;f.loc[idx,'situation_max_available_at']=latest;provenance.append(prov)
 require(np.isfinite(f.loc[f.track=='nfl',feature_columns()].to_numpy(float)).all(),'DATA','Nonfinite situation features')
 pd.testing.assert_frame_equal(f[frame.columns],frame)
 q=f[f.track=='nfl'];require(not(q.situation_max_available_at>=q.situation_decision_at).any(),'DATA','Situation history release at/after decision')
 return f,dict(nfl_rows=len(canon),feature_count=len(feature_columns()),delayed_team_game_updates=updates,missing_released_games=missing_games,delay_hours=24,decision_lead_hours=24,history_games=8,history_days=365,prior_opportunities=100,simultaneous_release_batching=True,opponent_adjustment='raw mean minus pre-release opponent counterpart profile plus prior-only league mean',vendor_epa_wp_used=False,pace_used=False,source_publication_at=None,strict_point_in_time_verified=False),pd.DataFrame(provenance)
