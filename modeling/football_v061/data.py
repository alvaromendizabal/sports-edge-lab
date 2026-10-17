"""Pinned schedule normalization and explicitly retrospective lagged features."""
import collections
import gzip
import heapq
import json
import math
import pathlib
import re
from datetime import timedelta

import numpy as np
import pandas as pd

from common import GateError, require

ALIASES = {'LAR': 'LA', 'STL': 'LA', 'OAK': 'LV', 'SD': 'LAC', 'JAC': 'JAX'}
NFL_TEAMS = set('ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS'.split())
FEATURES = ['elo_diff', 'home_elo', 'away_elo', 'pf_diff', 'pa_diff', 'total_recent', 'margin_recent_diff', 'home_games', 'away_games', 'home_rest', 'away_rest', 'rest_diff', 'neutral', 'home_fbs', 'away_fbs', 'season_progress']


def missing(x):
    return x is None or (isinstance(x, (str, np.str_)) and not x.strip()) or bool(pd.isna(x))


def integer(x, name):
    require(not missing(x), 'SCHEMA', name + ' missing')
    f = float(x)
    require(math.isfinite(f) and f == int(f), 'SCHEMA', name + ' not an integer')
    return int(f)


def boolean(x, name):
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if x in (0, 1) and not missing(x):
        return bool(x)
    raise GateError('SCHEMA', name + ' not boolean')


def score(x):
    if missing(x):
        return None
    n = integer(x, 'score')
    require(0 <= n <= 150, 'SCHEMA', 'score out of bounds')
    return n


def utc(x):
    p = pd.Timestamp(x)
    require(not pd.isna(p) and p.tzinfo is not None, 'SCHEMA', 'kickoff must have timezone')
    return p.tz_convert('UTC')


def normalize_nfl(row, source):
    season = integer(row['season'], 'season')
    if not 2016 <= season <= 2026 or row['game_type'] not in {'REG', 'WC', 'DIV', 'CON', 'SB'}:
        return None
    gid = str(row['game_id'])
    require(re.fullmatch(r'\d{4}_\d{2}_[A-Z]{2,3}_[A-Z]{2,3}', gid) is not None, 'SCHEMA', 'invalid NFL game ID')
    h, a = (ALIASES.get(str(row[k]), str(row[k])) for k in ['home_team', 'away_team'])
    require(h in NFL_TEAMS and a in NFL_TEAMS and h != a, 'SCHEMA', 'unknown or identical NFL teams')
    gy,gw,ga,gh=gid.split('_')
    require(int(gy)==season and int(gw)==integer(row['week'],'week') and ALIASES.get(gh,gh)==h and ALIASES.get(ga,ga)==a,'SCHEMA','NFL ID/team/week mismatch')
    require(not missing(row['gametime']), 'SCHEMA', 'TBD NFL kickoff')
    t = pd.Timestamp(str(row['gameday']) + ' ' + str(row['gametime'])).tz_localize('America/New_York', ambiguous='raise', nonexistent='raise').tz_convert('UTC')
    hs, aws = score(row['home_score']), score(row['away_score'])
    require((hs is None) == (aws is None), 'SCHEMA', 'partial NFL score')
    require(row['location'] in {'Home', 'Neutral'}, 'SCHEMA', 'unknown NFL site')
    return {'track':'nfl', 'game_id':gid, 'season':season, 'week':integer(row['week'],'week'), 'season_type': 'regular' if row['game_type']=='REG' else 'postseason', 'kickoff':t, 'home_id':h, 'away_id':a, 'home_name':h, 'away_name':a, 'home_points':hs, 'away_points':aws, 'completed':hs is not None, 'neutral':row['location']=='Neutral', 'home_fbs':1, 'away_fbs':1, 'source':source}


def normalize_ncaa(row, source, cfbd=False):
    get = lambda a, b: row[b if cfbd else a]
    season = integer(row['season'], 'season')
    st = get('season_type', 'seasonType')
    hd, ad = str(get('home_division','homeClassification')).lower(), str(get('away_division','awayClassification')).lower()
    if not 2016 <= season <= 2026 or st not in {'regular','postseason'} or 'fbs' not in {hd,ad}:
        return None
    gid = str(integer(get('game_id', 'id'), 'game_id'))
    hi, ai = str(integer(get('home_id','homeId'),'home_id')), str(integer(get('away_id','awayId'),'away_id'))
    require(hi != ai and int(hi)>0 and int(ai)>0 and int(gid)>0,'SCHEMA','invalid college IDs')
    require(boolean(get('start_time_tbd','startTimeTBD'),'kickoff TBD') is False,'SCHEMA','TBD college kickoff')
    t = utc(get('start_date','startDate'))
    hs, aws = score(get('home_points','homePoints')), score(get('away_points','awayPoints'))
    completed = boolean(row['completed'],'completed')
    require(not completed or (hs is not None and aws is not None),'SCHEMA','completed college game lacks scores')
    # In-progress scores are never labels or feature-history updates.
    if not completed:
        hs = aws = None
    require(hd in {'fbs','fcs'} and ad in {'fbs','fcs'},'SCHEMA','unverified opponent division')
    return {'track':'ncaaf','game_id':gid,'season':season,'week':integer(row['week'],'week'),'season_type':st,'kickoff':t,'home_id':hi,'away_id':ai,'home_name':str(get('home_team','homeTeam')),'away_name':str(get('away_team','awayTeam')),'home_points':hs,'away_points':aws,'completed':completed,'neutral':boolean(get('neutral_site','neutralSite'),'neutral'),'home_fbs':int(hd=='fbs'),'away_fbs':int(ad=='fbs'),'source':source}


def canonicalize(assets, cache, snapshot):
    rows, bad, counts = [], [], collections.Counter()
    for asset in assets:
        p = pathlib.Path(cache) / asset['name']
        if asset['kind']=='nfl_csv':
            raw = pd.read_csv(p).to_dict('records')
            fun = lambda r: normalize_nfl(r, asset['key'])
        elif asset['kind']=='ncaa_parquet':
            raw = pd.read_parquet(p).to_dict('records')
            fun = lambda r: normalize_ncaa(r, asset['key'])
        elif asset['kind']=='cfbd_json':
            raw = json.loads(gzip.decompress(p.read_bytes()))
            require(isinstance(raw,list),'SCHEMA','CFBD schedule must be a list')
            fun = lambda r: normalize_ncaa(r, asset['key'], True)
        else:
            raise GateError('SCHEMA','Unapproved asset kind')
        for i, r in enumerate(raw):
            counts['input_rows']+=1
            try:
                out = fun(r)
                if out is None:
                    counts['out_of_scope']+=1
                    continue
                require(out['season'] <= out['kickoff'].year <= out['season']+1,'SCHEMA','season/date mismatch')
                require(not out['completed'] or out['kickoff'] < utc(snapshot),'SCHEMA','future completed result')
                rows.append(out)
            except (GateError, ValueError, TypeError, KeyError) as e:
                bad.append({'source':asset['key'],'row':i,'game_id':str(r.get('game_id',r.get('id',''))),'reason':str(e)})
    d = pd.DataFrame(rows)
    require(len(d)>0,'DATA','No usable games')
    keep=[]
    for _, group in d.groupby(['track','game_id'],sort=False):
        if len(group)==1:
            keep.append(group.index[0]); continue
        # Even seemingly harmless duplicated identities require an explicit audit.
        cols=[c for c in d if c!='source']
        if len(group[cols].drop_duplicates())==1:
            keep.append(group.index[0]); counts['identical_duplicates_removed']+=len(group)-1
        else:
            for ix,r in group.iterrows():
                bad.append({'source':r.source,'row':int(ix),'game_id':r.game_id,'reason':'conflicting duplicate ID'})
    d=d.loc[keep].sort_values(['track','kickoff','game_id']).reset_index(drop=True)
    # A team cannot play overlapping events on the same UTC day in this scope.
    used={}; overlaps=set()
    for i,r in d.iterrows():
        for team in [r.home_id,r.away_id]:
            k=(r.track,team,str(r.kickoff.date()))
            if k in used:
                overlaps.update([i,used[k]])
            used[k]=i
    for i in sorted(overlaps):
        r=d.loc[i];bad.append({'source':r.source,'row':int(i),'game_id':r.game_id,'reason':'team/date collision'})
    d=d.drop(index=list(overlaps)).reset_index(drop=True)
    d['margin']=d.home_points-d.away_points
    d['total']=d.home_points+d.away_points
    d['win']=np.where(d.completed & (d.margin!=0),(d.margin>0).astype(float),np.nan)
    d['source_snapshot_at']=snapshot
    d['strict_point_in_time_verified']=False
    counts.update({'accepted_games':len(d),'quarantined':len(bad),'completed_games':int(d.completed.sum()),'ties':int((d.completed & (d.margin==0)).sum())})
    coverage=d.groupby(['track','season']).agg(games=('game_id','count'),completed=('completed','sum')).reset_index().to_dict('records')
    return d, {'counts':dict(counts),'coverage':coverage,'quarantine':bad,'point_in_time':'retrospective revised archives; publication timestamps unverified'}


def build_features(games, delay_hours=24):
    output=[]
    for track,d in games.groupby('track',sort=True):
        state={}; pending=[]; serial=0
        def entry(team, season):
            s=state.setdefault(team,{'elo':1500.0,'season':season,'history':collections.deque(maxlen=8),'last':None,'released':None})
            if s['season']<season:
                s['elo']=1500+(s['elo']-1500)*(2/3)**(season-s['season'])
                s['season']=season
                # Rolling history crosses seasons; rest is capped, cold history exposed.
            return s
        def update(r, release):
            h,a=entry(r.home_id,r.season),entry(r.away_id,r.season)
            p=1/(1+10**(-(h['elo']-a['elo']+(0 if r.neutral else 55))/400))
            actual=1.0 if r.margin>0 else 0.0 if r.margin<0 else 0.5
            change=20*(actual-p);h['elo']+=change;a['elo']-=change
            for s,pf,pa in [(h,r.home_points,r.away_points),(a,r.away_points,r.home_points)]:
                s['history'].append((float(pf),float(pa)))
                s['last']=r.kickoff;s['released']=release
        for r in d.sort_values(['kickoff','game_id']).itertuples():
            while pending and pending[0][0] < r.kickoff:
                release,_,prev=heapq.heappop(pending);update(prev,release)
            h,a=entry(r.home_id,r.season),entry(r.away_id,r.season)
            def summary(s):
                hist=list(s['history'])
                pf=np.mean([x[0] for x in hist]) if hist else 0.0
                pa=np.mean([x[1] for x in hist]) if hist else 0.0
                rest=min(60.,(r.kickoff-s['last']).total_seconds()/86400) if s['last'] is not None else 60.
                return pf,pa,len(hist),rest
            hp,ha,hn,hr=summary(h);ap,aa,an,ar=summary(a)
            release=max([s['released'] for s in [h,a] if s['released'] is not None],default=None)
            require(release is None or release<r.kickoff,'DATA','Future feature-history timestamp')
            item=r._asdict()
            item.update({'elo_diff':h['elo']-a['elo'],'home_elo':h['elo'],'away_elo':a['elo'],'pf_diff':hp-ap,'pa_diff':ha-aa,'total_recent':hp+ap,'margin_recent_diff':(hp-ha)-(ap-aa),'home_games':hn,'away_games':an,'home_rest':hr,'away_rest':ar,'rest_diff':hr-ar,'neutral':int(r.neutral),'season_progress':min(r.week,25),'feature_max_available_at':release,'assumed_result_delay_hours':delay_hours})
            output.append(item)
            if r.completed:
                serial+=1;heapq.heappush(pending,(r.kickoff+pd.Timedelta(hours=delay_hours),serial,r))
    f=pd.DataFrame(output).drop(columns=['Index'],errors='ignore')
    require(np.isfinite(f[FEATURES].to_numpy(dtype=float)).all(),'DATA','Nonfinite feature values')
    return f


def split_rows(f, track, task, train_through, eval_seasons):
    d=f[(f.track==track) & f.completed & f[task].notna()].copy()
    train=d[d.season<=train_through]
    test=d[d.season.isin(eval_seasons)]
    require(len(train)>=80 and len(test)>=15,'DATA','Insufficient chronological partition: '+track+'/'+task)
    require(train.kickoff.max()+pd.Timedelta(hours=24)<test.kickoff.min(),'DATA','Train labels overlap evaluation start')
    if task=='win':
        require(set(train.win.unique())=={0.,1.},'DATA','Training lacks both outcome classes')
    return train,test
