"""Synthetic football source exercise; no actual readiness or performance claims."""
import numpy as np
import pandas as pd
from data import build_features as baseline_features
from nfl_situation import aggregate_pbp, RAW_COLUMNS
TEAMS=('ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE')
def synthetic_games():
 rng=np.random.default_rng(6101);rows=[]
 for year in range(2016,2027):
  for week in range(1,13):
   for match in range(4):
    h=TEAMS[(2*match+week)%8];a=TEAMS[(2*match+week+1)%8];kickoff=pd.Timestamp(f'{year}-08-01T18:00:00Z')+pd.Timedelta(days=7*week,hours=match)
    away=int(rng.integers(10,31));home=max(0,away+int(rng.integers(-20,21)));complete=year<2026 or week<=6
    rows.append(dict(track='nfl',game_id=f'{year}_{week:02d}_{a}_{h}',season=year,week=week,season_type='regular',kickoff=kickoff,home_id=h,away_id=a,home_name=h,away_name=a,home_points=home if complete else np.nan,away_points=away if complete else np.nan,completed=complete,neutral=week%6==0,home_fbs=0,away_fbs=0,source='synthetic',margin=home-away if complete else np.nan,total=home+away if complete else np.nan,win=float(home>away) if complete and home!=away else np.nan,source_snapshot_at=None,strict_point_in_time_verified=False))
 return pd.DataFrame(rows)
def synthetic_raw(games):
 rows=[]
 for g in games[games.completed].itertuples():
  for j,team in enumerate([g.home_id,g.away_id]):
   opp=g.away_id if j==0 else g.home_id
   for play in range(24):
    dropback=play%3!=0;scramble=int(dropback and play%11==0);sack=int(dropback and not scramble and play%13==0);yard=-5 if sack else (play*3+g.week+j)%18
    rows.append(dict(game_id=g.game_id,play_id=float(j*100+play+1),posteam=team,defteam=opp,play_type='run' if not dropback or scramble else 'pass',down=1.+play%2,ydstogo=10.,yards_gained=float(yard),qb_dropback=float(dropback),qb_scramble=float(scramble),sack=float(sack),qb_kneel=0.,qb_spike=0.,penalty=0.,play_deleted=0.,two_point_attempt=0.,qtr=1.+play%3,half_seconds_remaining=1500.-play*20,score_differential=0.))
 return pd.DataFrame(rows,columns=RAW_COLUMNS)
def fixture_data(config=None):
 games=synthetic_games();frame=baseline_features(games);raw=synthetic_raw(games);panel,audit,quarantine=aggregate_pbp(raw,frame);market=[]
 for g in games[(games.season>=2022)&games.completed].itertuples():
  for task,value in [('win',.55),('margin',3.),('total',48.)]:
   if pd.notna(getattr(g,task)):market.append(dict(track=g.track,game_id=g.game_id,season=g.season,week=g.week,kickoff=g.kickoff,task=task,target=getattr(g,task),model_prediction=value,market_prediction=value,snapshot_at=g.kickoff-pd.Timedelta(hours=1)))
 return dict(frame=frame,raw=raw,panel=panel,aggregation_audit=audit,quarantine=quarantine,market=pd.DataFrame(market),readiness=dict(fixture=True,core_modeling_ready=False,live_wagering_ready=False,tracking_video_confirmed=False))
