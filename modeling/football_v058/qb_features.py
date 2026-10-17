"""Cache-only, retrospectively lagged NFL quarterback state; no starter claim.

A game becomes usable at canonical kickoff + 24h. Each feature is frozen at
kickoff - 24h, using only releases strictly before that cutoff. Publication
metadata remains unknown. This assumption is not strict point-in-time proof.
"""
from collections import Counter, defaultdict
import re
import numpy as np
import pandas as pd

ARMS = ('continuity_control', 'qb_values')
BASELINE = ['elo_diff','home_elo','away_elo','pf_diff','pa_diff','total_recent','margin_recent_diff','home_games','away_games','home_rest','away_rest','rest_diff','neutral','home_fbs','away_fbs','season_progress']
ALIASES = {'LAR':'LA','STL':'LA','OAK':'LV','SD':'LAC','JAC':'JAX'}
NFL_TEAMS = set('ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS'.split())
RAW_COLUMNS = ['game_id','posteam','passer_player_id','qb_dropback','qb_scramble','sack','complete_pass','interception','yards_gained','play_id','play_type']
REQUIRED_COLUMNS = RAW_COLUMNS
CONTROLS = ['has_prior_qb','last_primary_share','recent_team_qb_switch_rate','qb_history_dropbacks_scaled','days_since_last_scaled','identity_missing_rate']
VALUES = ['completion_rate','net_yards_per_dropback','sack_rate','interception_rate']
FALLBACK = {'completion_rate':.63,'net_yards_per_dropback':6.,'sack_rate':.065,'interception_rate':.025}
TOTALS = ['dropbacks','completions','net_yards','sacks','interceptions']
PANEL_COLUMNS = ['game_id','team_id','player_id','kickoff','available_at','primary_id','primary_share','eligible_dropbacks','identified_dropbacks','identity_missing_rate','primary_tie'] + TOTALS + ['source_publication_at','strict_point_in_time_verified']


def columns(arm):
    if arm not in ARMS:
        raise ValueError('Unknown QB arm')
    return BASELINE + ['qb_'+s+'_'+c for s in ('home','away') for c in CONTROLS + (VALUES if arm=='qb_values' else [])]


def _team(x):
    return ALIASES.get(str(x),str(x))


def _utc(x):
    t=pd.Timestamp(x)
    if pd.isna(t) or t.tzinfo is None:
        raise ValueError('Canonical kickoff must be timezone aware')
    return t.tz_convert('UTC')


def _canonical(frame):
    required={'track','game_id','home_id','away_id','kickoff','completed'}
    if not required.issubset(frame):
        raise ValueError('Missing canonical columns: '+str(sorted(required-set(frame))))
    f=frame.loc[frame.track=='nfl'].copy()
    if f.game_id.duplicated().any():
        raise ValueError('Duplicate canonical NFL game ID')
    for r in f.itertuples():
        bits=str(r.game_id).split('_')
        if len(bits)!=4 or not re.fullmatch(r'\d{4}_\d{2}_[A-Z]{2,3}_[A-Z]{2,3}',str(r.game_id)):
            raise ValueError('Malformed canonical NFL game ID')
        h,a=_team(r.home_id),_team(r.away_id)
        if h not in NFL_TEAMS or a not in NFL_TEAMS or h==a or _team(bits[2])!=a or _team(bits[3])!=h:
            raise ValueError('Canonical game/team mismatch')
        if getattr(r,'season',int(bits[0]))!=int(bits[0]) or getattr(r,'week',int(bits[1]))!=int(bits[1]):
            raise ValueError('Canonical game/season/week mismatch')
        _utc(r.kickoff)
        if not isinstance(r.completed,(bool,np.bool_)):
            raise ValueError('Canonical completion flag must be boolean')
    return f


def aggregate_pbp(raw, canonical):
    """Aggregate identified, non-scramble dropbacks; retain rejected-row evidence.

    Duplicate conflicting play IDs reject every version. Exact duplicates count
    once. Passer identity must be GSIS; no fuzzy player or game matching exists.
    """
    if not set(RAW_COLUMNS).issubset(raw):
        raise ValueError('Missing PBP columns: '+str(sorted(set(RAW_COLUMNS)-set(raw))))
    canon=_canonical(canonical)
    games={str(r.game_id):r for r in canon.itertuples()}
    d=raw[RAW_COLUMNS].copy().reset_index(drop=True)
    counts=Counter(input_rows=len(d),quarantined_rows=0,identical_duplicate_rows_removed=0,incomplete_game_rows_excluded=0,non_dropback_rows_excluded=0,scramble_rows_excluded=0); bad=[]; valid=[]; eligible=Counter(); observed=set()
    def reject(i,r,reason):
        counts['quarantined_rows']+=1;counts['reason_'+reason]+=1
        bad.append({'row':int(i),'game_id':str(r.get('game_id')),'team_id':str(r.get('posteam')),'play_id':str(r.get('play_id')),'reason':reason})
    # Validate identity keys before grouping, so null/fractional IDs cannot merge.
    valid_indices=[]
    for i,r in d.iterrows():
        gid=str(r.game_id)
        if gid not in games:
            reject(i,r,'noncanonical_game');continue
        game=games[gid]
        if not game.completed:
            counts['incomplete_game_rows_excluded']+=1;continue
        observed.add(gid)
        try:
            pi=float(r.play_id)
            if not np.isfinite(pi) or pi<0 or pi!=int(pi):raise ValueError()
        except (TypeError,ValueError):
            reject(i,r,'invalid_play_id');continue
        valid_indices.append(i)
    d=d.loc[valid_indices]
    conflicts=set()
    for _,g in d.groupby(['game_id','play_id'],sort=False):
        if len(g)>1:
            if len(g.drop_duplicates(subset=RAW_COLUMNS))>1:
                # One rejected logical play can reduce identity coverage even
                # though neither conflicting version supplies player values.
                affected=set()
                for rr in g.itertuples():
                    gg=games[str(rr.game_id)];tt=_team(rr.posteam)
                    if rr.qb_dropback==1 and rr.qb_scramble!=1 and tt in {_team(gg.home_id),_team(gg.away_id)}:
                        affected.add((str(rr.game_id),tt))
                for key in affected:eligible[key]+=1
                for i,r in g.iterrows():reject(i,r,'conflicting_duplicate_play');conflicts.add(i)
            else:
                counts['identical_duplicate_rows_removed']+=len(g)-1
                conflicts.update(g.index[1:])
    for i,r in d.drop(index=list(conflicts)).iterrows():
        # NaNs on kickoffs, timeouts and metadata records are normal, not passes.
        if r.qb_dropback!=1:
            if r.play_type=='pass' and r.qb_dropback not in (0,1):reject(i,r,'invalid_dropback_flag')
            else:counts['non_dropback_rows_excluded']+=1
            continue
        gid=str(r.game_id);game=games[gid];team=_team(r.posteam)
        if team not in {_team(game.home_id),_team(game.away_id)}:
            reject(i,r,'noncanonical_team');continue
        if r.qb_scramble==1:
            counts['scramble_rows_excluded']+=1;continue
        eligible[(gid,team)]+=1
        vals=[r.qb_scramble,r.sack,r.complete_pass,r.interception]
        if any(pd.isna(x) or x not in (0,1) for x in vals):
            reject(i,r,'invalid_binary_flags');continue
        if r.play_type!='pass':
            reject(i,r,'invalid_dropback_play_type');continue
        if r.sack+r.complete_pass>1 or r.sack+r.interception>1 or r.complete_pass+r.interception>1:
            reject(i,r,'impossible_binary_flags');continue
        try:
            yards=float(r.yards_gained)
            if not np.isfinite(yards) or not -99<=yards<=99:raise ValueError()
        except (TypeError,ValueError):
            reject(i,r,'invalid_yards');continue
        pid=str(r.passer_player_id)
        if not re.fullmatch(r'00-\d{7}',pid):
            reject(i,r,'unassigned_or_invalid_passer');continue
        valid.append({'game_id':gid,'team_id':team,'player_id':pid,'dropbacks':1,'completions':int(r.complete_pass),'net_yards':yards,'sacks':int(r.sack),'interceptions':int(r.interception)})
    stats=pd.DataFrame(valid)
    if len(stats):
        stats=stats.groupby(['game_id','team_id','player_id'],sort=True)[TOTALS].sum().reset_index()
    out=[]
    for gid in sorted(observed):
        game=games[gid];kickoff=_utc(game.kickoff)
        for team in (_team(game.home_id),_team(game.away_id)):
            ps=stats[(stats.game_id==gid)&(stats.team_id==team)] if len(stats) else pd.DataFrame()
            total=int(ps.dropbacks.sum()) if len(ps) else 0
            n=max(eligible[(gid,team)],total)
            winners=ps.loc[ps.dropbacks==ps.dropbacks.max(),'player_id'].tolist() if len(ps) else []
            primary=winners[0] if len(winners)==1 else None
            primary_count=int(ps.loc[ps.player_id==primary,'dropbacks'].sum()) if primary else 0
            shared={'game_id':gid,'team_id':team,'kickoff':kickoff,'available_at':kickoff+pd.Timedelta(hours=24),'primary_id':primary,'primary_share':primary_count/n if n else 0.,'eligible_dropbacks':n,'identified_dropbacks':total,'identity_missing_rate':1-total/n if n else 1.,'primary_tie':len(winners)>1,'source_publication_at':None,'strict_point_in_time_verified':False}
            if len(ps):
                for pr in ps.to_dict('records'):out.append(dict(shared,**{k:pr[k] for k in ['player_id']+TOTALS}))
            else:out.append(dict(shared,player_id=None,**{k:0 for k in TOTALS}))
    panel=pd.DataFrame(out,columns=PANEL_COLUMNS)
    counts['valid_identified_dropbacks']=len(valid);counts['team_games']=len(panel[['game_id','team_id']].drop_duplicates()) if out else 0
    counts['unique_games']=len(observed)
    counts['team_games_unknown_primary']=sum(1 for _,g in panel.groupby(['game_id','team_id']) if pd.isna(g.primary_id.iloc[0])) if len(panel) else 0
    audit={'counts':dict(counts),'scope':'identified non-scramble NFL dropbacks only; sacks included when passer GSIS is present','source_publication_at':None,'strict_point_in_time_verified':False,'quarantine_reason_counts':dict(Counter(x['reason'] for x in bad))}
    return panel,audit,pd.DataFrame(bad,columns=['row','game_id','team_id','play_id','reason'])


def _rates(totals, prior=None):
    db=float(totals.get('dropbacks',0)); sacks=float(totals.get('sacks',0)); attempts=db-sacks
    if prior is None:
        return {'completion_rate':float(totals.get('completions',0))/attempts if attempts else FALLBACK['completion_rate'],'net_yards_per_dropback':float(totals.get('net_yards',0))/db if db else FALLBACK['net_yards_per_dropback'],'sack_rate':sacks/db if db else FALLBACK['sack_rate'],'interception_rate':float(totals.get('interceptions',0))/db if db else FALLBACK['interception_rate']}
    # The fixed 100 prior dropbacks imply 100*(1-prior sack rate) pass attempts.
    pa=100*(1-prior['sack_rate'])
    return {'completion_rate':(float(totals.get('completions',0))+pa*prior['completion_rate'])/(attempts+pa),'net_yards_per_dropback':(float(totals.get('net_yards',0))+100*prior['net_yards_per_dropback'])/(db+100),'sack_rate':(sacks+100*prior['sack_rate'])/(db+100),'interception_rate':(float(totals.get('interceptions',0))+100*prior['interception_rate'])/(db+100)}


def build_qb_features(frame, panel):
    """Augment every upstream row without altering any existing feature or label."""
    f=frame.copy();canonical=_canonical(f)
    if not f.index.is_unique:raise ValueError('Duplicate upstream row index')
    if not set(BASELINE).issubset(f):raise ValueError('Missing accepted baseline columns')
    if not np.isfinite(f[BASELINE].to_numpy(float)).all():raise ValueError('Nonfinite baseline features')
    if not set(PANEL_COLUMNS).issubset(panel):raise ValueError('Incomplete QB panel schema')
    if panel.duplicated(['game_id','team_id','player_id']).any():raise ValueError('Duplicate QB panel identity')
    known={str(r.game_id):r for r in canonical.itertuples()}; panels={}
    for (gid,team),g in panel.groupby(['game_id','team_id'],sort=False):
        if gid not in known or team not in {_team(known[gid].home_id),_team(known[gid].away_id)}:raise ValueError('Panel canonical mismatch')
        r=known[gid];kickoff=_utc(r.kickoff)
        if not r.completed:raise ValueError('Incomplete game in QB panel')
        if any(_utc(x)!=kickoff for x in g.kickoff) or any(_utc(x)!=kickoff+pd.Timedelta(hours=24) for x in g.available_at):raise ValueError('Panel release mismatch')
        for c in ['primary_id','primary_share','eligible_dropbacks','identified_dropbacks','identity_missing_rate','primary_tie']:
            if g[c].nunique(dropna=False)!=1:raise ValueError('Inconsistent team-game panel metadata')
        if not np.isfinite(g[TOTALS].to_numpy(float)).all() or (g[['dropbacks','completions','sacks','interceptions']]<0).any().any():raise ValueError('Invalid aggregate statistics')
        if int(g.dropbacks.sum())!=int(g.identified_dropbacks.iloc[0]):raise ValueError('Aggregate count mismatch')
        integer_cols=['dropbacks','completions','sacks','interceptions']
        if (g[integer_cols].to_numpy(float)%1!=0).any():raise ValueError('Fractional aggregate counts')
        if ((g.sacks+g.completions>g.dropbacks)|(g.sacks+g.interceptions>g.dropbacks)|(g.completions+g.interceptions>g.dropbacks)).any():raise ValueError('Impossible aggregate counts')
        if (g.net_yards.abs()>99*g.dropbacks).any():raise ValueError('Impossible aggregate yards')
        identified=int(g.dropbacks.sum());eligible_n=float(g.eligible_dropbacks.iloc[0])
        if not np.isfinite(eligible_n) or eligible_n%1 or eligible_n<identified:raise ValueError('Invalid aggregate coverage')
        expected_missing=1-identified/eligible_n if eligible_n else 1.
        if not np.isclose(float(g.identity_missing_rate.iloc[0]),expected_missing):raise ValueError('Incorrect aggregate missingness')
        positive=g[g.dropbacks>0];winners=positive.loc[positive.dropbacks==positive.dropbacks.max(),'player_id'].tolist() if len(positive) else []
        expected_primary=winners[0] if len(winners)==1 else None
        actual_primary=g.primary_id.iloc[0] if pd.notna(g.primary_id.iloc[0]) else None
        if actual_primary!=expected_primary or bool(g.primary_tie.iloc[0])!=(len(winners)>1):raise ValueError('Incorrect aggregate primary passer')
        expected_share=float(positive.loc[positive.player_id==expected_primary,'dropbacks'].sum())/eligible_n if expected_primary and eligible_n else 0.
        if not np.isclose(float(g.primary_share.iloc[0]),expected_share):raise ValueError('Incorrect aggregate primary share')
        if not g.source_publication_at.isna().all() or g.strict_point_in_time_verified.any():raise ValueError('Unsupported publication/PIT claim')
        if any(pd.notna(x) and not re.fullmatch(r'00-\d{7}',str(x)) for x in g.player_id):raise ValueError('Invalid panel GSIS ID')
        panels[(gid,team)]=g
    # Include every completed canonical team-game, including missing PBP, so a
    # missing recent game's QB is not silently replaced by an older identity.
    events=[]
    for r in canonical.itertuples():
        if r.completed:events.append((_utc(r.kickoff)+pd.Timedelta(hours=24),str(r.game_id),r))
    events.sort(key=lambda x:(x[0],x[1])); pos=0
    team_hist=defaultdict(list);players=defaultdict(list);league=Counter();rows={};prov=[]
    for idx,r in canonical.sort_values(['kickoff','game_id']).iterrows():
        cutoff=_utc(r.kickoff)-pd.Timedelta(hours=24)
        while pos<len(events) and events[pos][0]<cutoff:
            released,gid,old=events[pos];pos+=1
            for team in (_team(old.home_id),_team(old.away_id)):
                g=panels.get((gid,team));primary=None;share=0.;missing=1.
                if g is not None:
                    h=g.iloc[0];primary=h.primary_id if pd.notna(h.primary_id) else None;share=float(h.primary_share);missing=float(h.identity_missing_rate)
                    for pr in g.to_dict('records'):
                        if pr['player_id'] is not None and pd.notna(pr['player_id']) and pr['dropbacks']>0:
                            item={k:float(pr[k]) for k in TOTALS};item.update(available_at=released,kickoff=_utc(old.kickoff),game_id=gid,team_id=team)
                            players[pr['player_id']].append(item);league.update({k:float(pr[k]) for k in TOTALS})
                team_hist[team].append({'primary':primary,'share':share,'missing':missing,'available_at':released,'kickoff':_utc(old.kickoff),'game_id':gid})
        prior=_rates(league);features={};provenance={'game_id':str(r.game_id),'prediction_cutoff':cutoff,'source_publication_at':None,'strict_point_in_time_verified':False,'actual_starting_qb_known':False}
        for side,team in [('home',_team(r.home_id)),('away',_team(r.away_id))]:
            th=team_hist[team];last=th[-1] if th else None;pid=last['primary'] if last else None
            history=[x for x in players.get(pid,[]) if x['kickoff']>=cutoff-pd.Timedelta(days=365)][-8:] if pid else []
            totals=Counter()
            for x in history:totals.update({k:x[k] for k in TOTALS})
            recent=[x for x in th[-8:] if x['kickoff']>=cutoff-pd.Timedelta(days=365)]
            pairs=[(a['primary'],b['primary']) for a,b in zip(recent,recent[1:]) if a['primary'] and b['primary']]
            latest=history[-1]['kickoff'] if history else None
            value={'has_prior_qb':float(pid is not None),'last_primary_share':last['share'] if last else 0.,'recent_team_qb_switch_rate':sum(a!=b for a,b in pairs)/len(pairs) if pairs else 0.,'qb_history_dropbacks_scaled':min(float(totals['dropbacks']),400.)/400.,'days_since_last_scaled':min(max((cutoff-latest).total_seconds()/86400,0.),365.)/365. if latest is not None else 1.,'identity_missing_rate':last['missing'] if last else 1.}
            value.update(_rates(totals,prior));features.update({'qb_'+side+'_'+k:float(v) for k,v in value.items()})
            provenance.update({side+'_last_observed_qb':pid,side+'_last_team_game':last['game_id'] if last else None,side+'_last_team_release':last['available_at'] if last else None,side+'_qb_history_games':len(history),side+'_qb_history_dropbacks':float(totals['dropbacks']),side+'_qb_history_latest_release':max([x['available_at'] for x in history],default=None)})
        provenance['league_prior_dropbacks']=float(league['dropbacks']);provenance['league_prior_latest_release']=events[pos-1][0] if pos else None
        rows[idx]=features;prov.append(provenance)
    qbcols=[c for c in columns('qb_values') if c not in BASELINE]
    for c in qbcols:f[c]=[rows.get(i,{}).get(c,0.) for i in f.index]
    f['qb_decision_at']=pd.to_datetime([_utc(r.kickoff)-pd.Timedelta(hours=24) if r.track=='nfl' else pd.NaT for r in f.itertuples()],utc=True)
    if len(f)!=len(frame) or not f[frame.columns].equals(frame):raise ValueError('Upstream rows/columns modified')
    if not np.isfinite(f[qbcols].to_numpy(float)).all():raise ValueError('Nonfinite QB features')
    pf=pd.DataFrame(prov)
    late=0
    if 'feature_max_available_at' in canonical:
        ts=pd.to_datetime(canonical.feature_max_available_at,utc=True)
        late=int((ts>=pd.to_datetime(canonical.kickoff,utc=True)-pd.Timedelta(hours=24)).sum())
    audit={'rows_preserved':len(f),'nfl_rows_augmented':len(canonical),'other_track_rows_unchanged':len(f)-len(canonical),'feature_counts':{arm:len(columns(arm)) for arm in ARMS},'nfl_home_prior_qb_rows':int((f.loc[f.track=='nfl','qb_home_has_prior_qb']>0).sum()),'nfl_away_prior_qb_rows':int((f.loc[f.track=='nfl','qb_away_has_prior_qb']>0).sum()),'baseline_history_at_or_after_qb_cutoff_rows':late,'strict_point_in_time_verified':False,'source_publication_at':None,'selection':'last released prior team-game dominant observed passer; not upcoming starter','clock':'release=kickoff+24h; QB cutoff=target kickoff-24h; release strictly before cutoff','history':'latest 8 player appearances within 365 days; career follows GSIS across teams','shrinkage':'100 prior dropbacks toward strictly prior expanding league totals; initial fixed fallback','excluded':'scrambles, unassigned passer plays, invalid/conflicting plays; no name matching','caveat':'Descriptive passing outcomes confound quarterback, teammates, opponents and scheme; no causal quarterback-value claim. Baseline feature clock remains its accepted upstream contract.'}
    return f,audit,pf
