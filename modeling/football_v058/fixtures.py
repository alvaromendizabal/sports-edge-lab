"""Deterministic synthetic data. Never an actual Sports Edge result."""
import numpy as np
import pandas as pd


def synthetic_games():
    rng=np.random.default_rng(47);rows=[]
    for track in ['nfl','ncaaf']:
        for year in range(2016,2027):
            for week in range(1,19):
                for match in range(4):
                    h=(match*2+week)%8;a=(h+1)%8
                    margin=int(round((h-a)*1.8+2+rng.normal(0,10)))
                    ap=max(0,int(round(24+rng.normal(0,5))));hp=max(0,ap+margin)
                    t=pd.Timestamp(f'{year}-08-01T18:00:00Z')+pd.Timedelta(days=7*week,hours=match)
                    complete=year<2026 or week<9
                    rows.append({'track':track,'game_id':f'{track}-{year}-{week}-{match}','season':year,'week':week,'season_type':'regular','kickoff':t,'home_id':str(h),'away_id':str(a),'home_name':f'Team {h}','away_name':f'Team {a}','home_points':hp if complete else np.nan,'away_points':ap if complete else np.nan,'completed':complete,'neutral':week%5==0,'home_fbs':1,'away_fbs':int(match!=3),'source':'synthetic fixture','margin':hp-ap if complete else np.nan,'total':hp+ap if complete else np.nan,'win':float(hp>ap) if complete and hp!=ap else np.nan,'source_snapshot_at':'2026-10-16T23:30:05Z','strict_point_in_time_verified':False})
    return pd.DataFrame(rows)


def fixture_data(config=None):
 from data import build_features
 from experiments import columns,prepare
 games=synthetic_games();frame=build_features(games);rng=np.random.default_rng(5801)
 for track in ['nfl','ncaaf']:
  for name in columns(track):
   if name not in frame:frame[name]=rng.normal(0,1,len(frame))
 frame['efficiency_max_available_at']=frame['feature_max_available_at'];frame,_=prepare(frame);market=[]
 for g in games[(games.season>=2022)&games.completed].itertuples():
  for task,pr in [('win',.55),('margin',3.),('total',48.)]:
   if pd.isna(getattr(g,task)):continue
   market.append(dict(track=g.track,game_id=g.game_id,season=g.season,week=g.week,kickoff=g.kickoff,task=task,target=getattr(g,task),model_prediction=pr,market_prediction=pr,snapshot_at=g.kickoff-pd.Timedelta(hours=1)))
 return dict(frame=frame,market=pd.DataFrame(market),readiness=dict(synthetic=True,core_modeling_ready=False,live_wagering_ready=False,tracking_video_confirmed=False))
