"""Raw outcome aggregation and strictly delayed online opponent adjustment.

No vendor EPA/WP or full-season rating columns enter these features. Fixed priors
and update rules are assumptions, not claimed reproductions of a public system.
"""
import collections
import heapq
import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from common import atomic_json, require, read_json, GateError
from data import ALIASES, FEATURES

METRICS = {
    'nfl': {'yards_per_play':5.4, 'down_success_rate':.42, 'explosive_rate':.10,
            'turnovers_per_play':.025, 'eligible_plays':60.},
    'ncaaf': {'drive_yards_per_play':5.5, 'td_drives_rate':.25,
              'turnover_drives_rate':.10, 'plays_per_drive':5.5, 'yards_per_drive':30.},
}
NFL_COLUMNS = ['game_id','play_id','season','home_team','away_team','posteam','defteam',
               'play_type','down','ydstogo','yards_gained','qb_kneel','qb_spike',
               'penalty','play_deleted','two_point_attempt','interception','fumble_lost']
COLLEGE_COLUMNS = ['game_id','drive_id','season','team_id','result','yards',
                   'offensive_plays','start_period','end_period']
BAD_DRIVE_RESULTS = {'KICKOFF','POSSESSION (FOR OT DRIVES)','END OF GAME','END OF HALF','END OF QUARTER'}
KNOWN_DRIVE_RESULTS = {'TD','FG','PUNT','DOWNS','INT','FUMBLE','MISSED FG','INT TD','SF',
                       'FUMBLE TD','PUNT RETURN TD','PUNT TD','FUMBLE RETURN TD','MISSED FG TD',
                       'DOWNS TD','END OF GAME TD','END OF HALF TD'} | BAD_DRIVE_RESULTS


def feature_columns(track, adjusted=False):
    cols=list(FEATURES)+['eff_home_games','eff_away_games','eff_home_missing','eff_away_missing']
    for metric in METRICS[track]:
        for side in ['home','away']:
            cols += [f'raw_{side}_off_{metric}',f'raw_{side}_allowed_{metric}']
            if adjusted:cols += [f'adj_{side}_off_{metric}',f'adj_{side}_allowed_{metric}']
    return cols


def exact_int_series(series):
    n=pd.to_numeric(series,errors='coerce')
    return n.map(lambda x:str(int(x)) if pd.notna(x) and np.isfinite(x) and x==int(x) and x>0 else '')


def deduplicate(raw, ids, audit, quarantine):
    d=raw.drop_duplicates().copy();audit['identical_duplicates_removed']=len(raw)-len(d)
    conflict=d.duplicated(ids,keep=False)
    if conflict.any():
        quarantine.extend({'game_id':str(r.game_id),'reason':'conflicting duplicate '+','.join(ids)} for r in d.loc[conflict].itertuples())
        # A conflicting play/drive can corrupt all game totals: omit that game.
        games=set(d.loc[conflict,'game_id']);d=d[~d.game_id.isin(games)].copy()
        audit['conflicting_games']=len(games)
    return d


def aggregate(raw, track, games, source='fixture'):
    required=NFL_COLUMNS if track=='nfl' else COLLEGE_COLUMNS
    require(set(required)<=set(raw),'SCHEMA',f'{source}: required columns missing: '+str(sorted(set(required)-set(raw))))
    raw=raw[required].copy();audit={'source':source,'track':track,'input_rows':len(raw)};bad=[]
    if track=='ncaaf':raw['game_id']=exact_int_series(raw.game_id)
    else:raw['game_id']=raw.game_id.astype(str)
    raw=deduplicate(raw,['game_id','play_id' if track=='nfl' else 'drive_id'],audit,bad)
    canonical=games[(games.track==track)&games.completed].copy()
    require(not canonical.game_id.duplicated().any(),'DATA','Duplicate canonical game during efficiency join')
    audit['out_of_scope_rows']=int((~raw.game_id.isin(canonical.game_id)).sum())
    d=raw.merge(canonical[['game_id','season','home_id','away_id']],on='game_id',how='inner',suffixes=('','_canonical'),validate='many_to_one')
    require(len(d)>0,'DATA',source+': no canonical completed-game overlap')
    valid_season=pd.to_numeric(d.season,errors='coerce')==d.season_canonical
    for r in d.loc[~valid_season].itertuples():bad.append({'game_id':r.game_id,'reason':'season mismatch'})
    d=d.loc[valid_season].copy()
    if track=='nfl':
        for c in ['home_team','away_team','posteam','defteam']:d[c]=d[c].map(lambda x:ALIASES.get(str(x),str(x)))
        # Same raw event ID AND exact team identities, never name-only matching.
        identities=(d.home_team==d.home_id)&(d.away_team==d.away_id)
        identities &= ((d.posteam==d.home_id)&(d.defteam==d.away_id))|((d.posteam==d.away_id)&(d.defteam==d.home_id))
        selected=d.play_type.isin(['pass','run'])
        for flag in ['qb_kneel','qb_spike','penalty','play_deleted','two_point_attempt']:
            selected &= pd.to_numeric(d[flag],errors='coerce').fillna(0)==0
        selected &= pd.to_numeric(d.down,errors='coerce').isin([1,2,3,4])
        nums=['ydstogo','yards_gained','interception','fumble_lost']
        for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
        valid=identities & d.ydstogo.between(1,100) & d.yards_gained.between(-99,100)
        valid &= d.interception.isin([0,1]) & d.fumble_lost.isin([0,1]) & d.play_id.notna()
        for r in d.loc[selected&~valid].itertuples():bad.append({'game_id':r.game_id,'row_id':str(r.play_id),'reason':'invalid eligible play/team join'})
        d=d.loc[selected&valid].copy()
        d['team_id']=d.posteam;d['opponent_id']=d.defteam
        fraction=d.down.map({1:.4,2:.6,3:1.,4:1.})
        d['down_success']=(d.yards_gained>=fraction*d.ydstogo).astype(float)
        d['explosive']=(d.yards_gained>=np.where(d.play_type=='pass',20,10)).astype(float)
        d['turnover']=((d.interception==1)|(d.fumble_lost==1)).astype(float)
        out=d.groupby(['game_id','team_id','opponent_id'],as_index=False).agg(
            yards_per_play=('yards_gained','mean'),down_success_rate=('down_success','mean'),
            explosive_rate=('explosive','mean'),turnovers_per_play=('turnover','mean'),eligible_plays=('play_id','count'))
        out=out[out.eligible_plays>=20].copy()
    else:
        d['team_id']=exact_int_series(d.team_id)
        identities=(d.team_id==d.home_id)|(d.team_id==d.away_id)
        d['opponent_id']=np.where(d.team_id==d.home_id,d.away_id,d.home_id)
        for c in ['yards','offensive_plays','start_period','end_period']:d[c]=pd.to_numeric(d[c],errors='coerce')
        known=d.result.isin(KNOWN_DRIVE_RESULTS)
        selected=(d.offensive_plays>0)&(~d.result.isin(BAD_DRIVE_RESULTS))
        # Regulation-only drives avoid changing college overtime rules.
        selected &= d.start_period.between(1,4)&d.end_period.between(1,4)
        valid=identities & known & d.yards.between(-100,100) & d.offensive_plays.between(1,40) & d.drive_id.notna()
        for r in d.loc[selected&~valid].itertuples():bad.append({'game_id':r.game_id,'row_id':str(r.drive_id),'reason':'invalid eligible drive/team/result'})
        d=d.loc[selected&valid].copy()
        d['td']=(d.result=='TD').astype(float)
        d['turnover']=d.result.isin(['INT','FUMBLE','INT TD','FUMBLE TD','FUMBLE RETURN TD']).astype(float)
        out=d.groupby(['game_id','team_id','opponent_id'],as_index=False).agg(yards=('yards','sum'),plays=('offensive_plays','sum'),
            td_drives_rate=('td','mean'),turnover_drives_rate=('turnover','mean'),plays_per_drive=('offensive_plays','mean'),
            yards_per_drive=('yards','mean'),eligible_drives=('drive_id','count'))
        out['drive_yards_per_play']=out.yards/out.plays
        out=out[(out.eligible_drives>=4)&(out.plays>=20)].copy()
    audit['eligible_rows']=len(d);audit['quarantine_rows']=len(bad)
    # Both sides must survive the same parser and minimum evidence gate.
    counts=out.groupby('game_id').team_id.nunique();paired=set(counts[counts==2].index)
    audit['unpaired_games']=int((counts!=2).sum());out=out[out.game_id.isin(paired)].copy()
    out['track']=track
    require(np.isfinite(out[list(METRICS[track])].to_numpy(float)).all(),'DATA','Nonfinite efficiency aggregate')
    audit['accepted_games']=len(paired);audit['accepted_team_games']=len(out)
    return out[['track','game_id','team_id','opponent_id',*METRICS[track]]],audit,bad


def aggregate_assets(ctx, games, cache):
    tables=[];audits=[];quarantine=[]
    for i,a in enumerate(ctx.config['assets']):
        ctx.check_budget();name=f"aggregate_{a['kind']}_{a['season']}";folder=ctx.root/'aggregates';folder.mkdir(exist_ok=True)
        out=folder/(name+'.parquet');meta=folder/(name+'.json');badp=folder/(name+'_quarantine.json')
        old=ctx.cp.lookup(name)
        if old is None:
            cols=NFL_COLUMNS if a['kind']=='nfl_pbp' else COLLEGE_COLUMNS;p=pathlib.Path(cache)/a['name']
            if p.name.endswith('.csv.gz'):
                available=pd.read_csv(p,nrows=0).columns
                require(set(cols)<=set(available),'SCHEMA',a['name']+': missing required CSV fields')
                raw=pd.read_csv(p,usecols=cols,low_memory=False)
            else:
                available=pq.ParquetFile(p).schema_arrow.names
                require(set(cols)<=set(available),'SCHEMA',a['name']+': missing required parquet fields')
                raw=pq.read_table(p,columns=cols).to_pandas()
            table,audit,bad=aggregate(raw,'nfl' if a['kind']=='nfl_pbp' else 'ncaaf',games,a['key'])
            table.to_parquet(out,index=False);atomic_json(meta,audit);atomic_json(badp,bad)
            ctx.cp.commit(name,[out,meta,badp],audit)
        else:ctx.event('checkpoint_reused',item=name)
        tables.append(pd.read_parquet(out));audits.append(read_json(meta));quarantine.extend(read_json(badp))
        ctx.sync([out,meta,badp,ctx.root/'checkpoints'/(name+'.json')])
        ctx.event('aggregation_complete',item=name,completed=i+1,total=len(ctx.config['assets']),remaining=len(ctx.config['assets'])-i-1)
    stats=pd.concat(tables,ignore_index=True)
    require(not stats.duplicated(['track','game_id','team_id']).any(),'DATA','Cross-file team/game duplicate')
    coverage=[]
    for (track,season),g in games[games.completed].groupby(['track','season']):
        covered=set(stats[stats.track==track].game_id)&set(g.game_id);fraction=len(covered)/len(g)
        coverage.append({'track':track,'season':int(season),'completed_games':len(g),'efficiency_games':len(covered),'coverage':fraction})
        require(fraction>=.80,'DATA',f'{track} {season} efficiency coverage {fraction:.1%} below 80%; no silent coverage shift')
    audit={'assets':audits,'coverage':coverage,'quarantine_count':len(quarantine),'strict_point_in_time_verified':False,
           'original_publication_at':None,'vendor_epa_wp_used':False,'delay_assumption_hours':24,
           'definitions':{'nfl':'Penalty-free nondeleted regulation/OT run/pass plays, excluding kneels/spikes/conversions; down-success thresholds 40/60/100%; explosive run >=10 yards or pass >=20; both teams >=20 eligible plays.',
                          'ncaaf':'Regulation completed offensive drives with >0 offensive plays; exclude end-of-period and kickoff bookkeeping; both teams >=4 drives and >=20 plays. Net drive yards include penalties; drive TD excludes return touchdowns. Not interchangeable with NFL play-yardage efficiency.'}}
    return stats,audit,quarantine


def augment_features(frame, stats, delay_hours=24):
    require(not stats.duplicated(['track','game_id','team_id']).any(),'DATA','Duplicate efficiency stats')
    output=[];updates=0
    by={(r.track,r.game_id,r.team_id):r for r in stats.itertuples()}
    for track,games in frame.groupby('track',sort=True):
        metrics=list(METRICS[track]);prior=np.array(list(METRICS[track].values()));state={};pending=[];serial=0
        def entry(team,season):
            s=state.setdefault(team,{'season':season,'off':np.zeros(len(prior)),'allowed':np.zeros(len(prior)),
                    'raw_off':collections.deque(maxlen=8),'raw_allowed':collections.deque(maxlen=8),'last':None})
            if s['season']<season:
                decay=(2/3)**(season-s['season']);s['off']*=decay;s['allowed']*=decay;s['season']=season
            return s
        def update(r, release):
            nonlocal updates
            h,a=entry(r.home_id,r.season),entry(r.away_id,r.season)
            hs=by[(track,r.game_id,r.home_id)];as_=by[(track,r.game_id,r.away_id)]
            hv=np.array([getattr(hs,m) for m in metrics]);av=np.array([getattr(as_,m) for m in metrics])
            # Both residuals use pre-update states. Each offense/defense receives
            # half of a fixed 0.20 combined residual step; no future opponents.
            he=hv-(prior+h['off']+a['allowed']);ae=av-(prior+a['off']+h['allowed'])
            h['off']+=.10*he;a['allowed']+=.10*he;a['off']+=.10*ae;h['allowed']+=.10*ae
            h['raw_off'].append(hv);h['raw_allowed'].append(av);a['raw_off'].append(av);a['raw_allowed'].append(hv)
            h['last']=a['last']=release;updates+=1
        for r in games.sort_values(['kickoff','game_id']).itertuples():
            while pending and pending[0][0]<r.kickoff:
                release,_,prev=heapq.heappop(pending);update(prev,release)
            h,a=entry(r.home_id,r.season),entry(r.away_id,r.season);item=r._asdict()
            last=max([s['last'] for s in [h,a] if s['last'] is not None],default=None)
            require(last is None or last<r.kickoff,'DATA','Efficiency history from future/equal kickoff')
            item['efficiency_max_available_at']=last
            for side,s in [('home',h),('away',a)]:
                n=len(s['raw_off']);item['eff_'+side+'_games']=n;item['eff_'+side+'_missing']=int(n==0)
                for unit in ['off','allowed']:
                    history=s['raw_'+unit];raw=(np.sum(history,axis=0)+2*prior)/(n+2) if n else prior
                    for j,m in enumerate(metrics):
                        item[f'raw_{side}_{unit}_{m}']=float(raw[j]);item[f'adj_{side}_{unit}_{m}']=float(s[unit][j])
            output.append(item)
            if r.completed and (track,r.game_id,r.home_id) in by and (track,r.game_id,r.away_id) in by:
                hs=by[(track,r.game_id,r.home_id)];aa=by[(track,r.game_id,r.away_id)]
                require(hs.opponent_id==r.away_id and aa.opponent_id==r.home_id,'DATA','Efficiency opponent identity mismatch')
                serial+=1;heapq.heappush(pending,(r.kickoff+pd.Timedelta(hours=delay_hours),serial,r))
    out=pd.DataFrame(output).drop(columns=['Index'],errors='ignore')
    for track in METRICS:
        if not (out.track==track).any():continue
        require(np.isfinite(out.loc[out.track==track,feature_columns(track,True)].to_numpy(float)).all(),'DATA','Nonfinite augmented features')
    require(out[['track','game_id']].to_records(index=False).tolist()==frame[['track','game_id']].to_records(index=False).tolist(),'DATA','Predecessor row order changed')
    return out,{'rows':len(out),'delayed_game_updates':updates,'future_history_violations':0,'delay_hours':delay_hours,
               'strict_point_in_time_verified':False,'columns':{t:feature_columns(t,True) for t in METRICS},
               'priors':METRICS,'raw_history_games':8,'raw_prior_pseudogames':2,'online_total_step':.20,'annual_rating_decay':2/3}
