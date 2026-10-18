"""Normalize independently licensed CFBD drives and test model-input equivalence.

Read-only scientific adapter: no HTTP, credentials, fitting or model-input
replacement. A passed comparison is review evidence, never a serving promotion.
"""
import hashlib,json,math,re
from collections import Counter
import numpy as np
import pandas as pd
from efficiency import aggregate, METRICS, COLLEGE_COLUMNS

SCHEMA='football-cfbd-drive-compatibility-v065'
SEMANTIC_CONTRACT='v048_regulation_drive_metrics_v1'
KEYS=['track','game_id','team_id','opponent_id']
METRIC_COLUMNS=list(METRICS['ncaaf'])
STAT_COLUMNS=KEYS+METRIC_COLUMNS


def _integer(value, field, positive=False):
    if isinstance(value,(bool,np.bool_)):raise ValueError(field+': boolean is not integer')
    try:n=float(value)
    except (ValueError,TypeError):raise ValueError(field+': integer required')
    if not math.isfinite(n) or n!=int(n) or (positive and n<=0):raise ValueError(field+': invalid integer')
    return int(n)


def _utc(value):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tzinfo is None:raise ValueError('Known timezone-aware timestamp required')
    return t.tz_convert('UTC')


def _empty():return pd.DataFrame(columns=STAT_COLUMNS)


def _canonical(frame, season):
    needed={'track','game_id','season','home_id','away_id','home_name','away_name','home_fbs','away_fbs','completed'}
    if not needed<=set(frame):raise ValueError('Canonical fields missing: '+str(sorted(needed-set(frame))))
    c=frame[(frame.track=='ncaaf')&(frame.season==season)].copy()
    for key in ['game_id','home_id','away_id']:c[key]=c[key].map(lambda v:str(_integer(v,key,True)))
    if c.empty or c.game_id.duplicated().any():raise ValueError('Missing or duplicate current canonical identities')
    if not c.home_fbs.isin([0,1]).all() or not c.away_fbs.isin([0,1]).all():raise ValueError('Unknown FBS classification')
    if not c.completed.map(lambda v:isinstance(v,(bool,np.bool_))).all():raise ValueError('Canonical completion must be boolean')
    if (c.home_id==c.away_id).any():raise ValueError('Canonical self matchup')
    return c


def compare_cfbd_primary(cfbd_drives, primary_aggregate, canonical_games, *,
                         observed_at=None, source_sha256=None, as_of=None,
                         original_observed_at='2026-10-16T18:15:25+00:00',
                         required_primary_game_ids=None, season=2026):
    """Return audit/proof/quarantine plus independently normalized DataFrames.

    Required reference coverage is derived from every current-season primary
    metric game in the entire hash-pinned current-season aggregate; callers
    cannot lower it by supplying a partial canonical schedule. New metrics remain independent
    CFBD research data even if all reference metrics match. No model is changed.
    """
    if not isinstance(cfbd_drives,list) or len(cfbd_drives)>50000:raise ValueError('Bounded CFBD list required')
    c=_canonical(canonical_games,season);lookup=c.set_index('game_id')
    if not set(STAT_COLUMNS)<=set(primary_aggregate):raise ValueError('Primary aggregate columns missing')
    p=primary_aggregate.copy()
    if not (p.track=='ncaaf').all():raise ValueError('Primary inventory must contain only NCAAF metric rows')
    if 'season' in p and not p.season.map(lambda v:_integer(v,'primary season')==season).all():raise ValueError('Primary inventory season mismatch')
    for key in ['game_id','team_id','opponent_id']:p[key]=p[key].map(lambda v:str(_integer(v,key,True)))
    # Derive the required inventory BEFORE joining canonical rows. Missing
    # schedule rows must not silently shrink the scientific comparison domain.
    absent_canonical=sorted(set(p.game_id)-set(c.game_id))
    if absent_canonical:raise ValueError('Primary metric inventory missing from current canonical: '+','.join(absent_canonical))
    if p.empty or p.duplicated(KEYS).any():raise ValueError('Missing or duplicate primary current-season metrics')
    if not np.isfinite(p[METRIC_COLUMNS].to_numpy(float)).all():raise ValueError('Nonfinite primary metrics')
    for gid,g in p.groupby('game_id'):
        can=lookup.loc[gid]
        if not bool(can.completed) or len(g)!=2 or set(zip(g.team_id,g.opponent_id))!={(can.home_id,can.away_id),(can.away_id,can.home_id)}:raise ValueError('Unpaired/conflicting primary metric identity')
    required=set(p.game_id)
    if required_primary_game_ids is not None and set(map(str,required_primary_game_ids))!=required:raise ValueError('Required primary inventory may not be weakened')
    raw=[];quarantine=[];excluded=[];malformed_games=set()
    for ordinal,r in enumerate(cfbd_drives):
        gid=None
        try:
            if not isinstance(r,dict):raise ValueError('Drive must be object')
            gid=str(_integer(r.get('gameId'),'gameId',True))
            if gid not in lookup.index:
                excluded.append(dict(row=ordinal,game_id=gid,reason='not_in_declared_current_canonical'));continue
            g=lookup.loc[gid]
            if not bool(g.completed):
                excluded.append(dict(row=ordinal,game_id=gid,reason='canonical_game_not_completed'));continue
            if not (g.home_fbs==1 or g.away_fbs==1):
                excluded.append(dict(row=ordinal,game_id=gid,reason='standalone_FCS_out_of_scope'));continue
            home=r.get('isHomeOffense')
            if not isinstance(home,bool):raise ValueError('isHomeOffense must be boolean')
            names=(g.home_name,g.away_name) if home else (g.away_name,g.home_name)
            if (r.get('offense'),r.get('defense'))!=names:raise ValueError('Offense/defense names conflict with exact canonical home-side identity')
            did=r.get('id')
            if not isinstance(did,str) or not re.fullmatch(r'[0-9]+',did):raise ValueError('Exact decimal-string drive id required')
            if not isinstance(r.get('driveResult'),str):raise ValueError('Drive result string required')
            x=dict(game_id=gid,drive_id=did,season=season,team_id=g.home_id if home else g.away_id,result=r['driveResult'])
            for source,target in [('yards','yards'),('plays','offensive_plays'),('startPeriod','start_period'),('endPeriod','end_period')]:x[target]=_integer(r.get(source),source)
            # Period numbers cannot move backward within a drive. Quarantine
            # the entire affected game without changing the frozen reference
            # aggregator or its model-input definitions.
            if x['end_period']<x['start_period']:raise ValueError('Drive end period precedes start period')
            raw.append(x)
        except (ValueError,TypeError) as exc:
            quarantine.append(dict(row=ordinal,game_id=gid,reason=str(exc)))
            if gid is not None:malformed_games.add(gid)
    raw_frame=pd.DataFrame(raw,columns=COLLEGE_COLUMNS)
    if len(raw_frame):
        stats,normalization,aggregate_bad=aggregate(raw_frame,'ncaaf',c,'independent_CFBD_drive_response')
        for x in aggregate_bad:malformed_games.add(str(x['game_id']))
        quarantine.extend(aggregate_bad)
        # Never accept a game after dropping an invalid eligible drive.
        stats=stats[~stats.game_id.isin(malformed_games)].copy()
    else:stats=_empty();normalization=dict(input_rows=0,eligible_rows=0,accepted_games=0,accepted_team_games=0)
    if len(stats) and not np.isfinite(stats[METRIC_COLUMNS].to_numpy(float)).all():raise ValueError('Nonfinite normalized statistics')
    merged=p.merge(stats,on=KEYS,how='left',suffixes=('_primary','_cfbd'),validate='one_to_one',indicator=True)
    comparisons={};row_exact=np.ones(len(merged),dtype=bool)
    for metric in METRIC_COLUMNS:
        merged[metric+'_primary']=pd.to_numeric(merged[metric+'_primary'],errors='raise').astype(float)
        merged[metric+'_cfbd']=pd.to_numeric(merged[metric+'_cfbd'],errors='raise').astype(float)
        diff=np.abs(merged[metric+'_primary']-merged[metric+'_cfbd'])
        ok=np.isclose(merged[metric+'_primary'],merged[metric+'_cfbd'],rtol=0,atol=1e-12,equal_nan=False)
        row_exact &= ok
        finite=diff[np.isfinite(diff)]
        comparisons[metric]=dict(required_team_rows=len(merged),compared_team_rows=int(finite.size),equal_team_rows=int(ok.sum()),max_abs_difference=float(finite.max()) if finite.size else None)
    group=merged.assign(exact=row_exact).groupby('game_id').exact.all()
    present=set(stats.game_id);missing=sorted(required-present);unequal=sorted(gid for gid in required&present if not bool(group.loc[gid]))
    exact=sorted(gid for gid in required if bool(group.loc[gid]));full=not missing and not unequal and len(exact)==len(required)
    observation=None;fresh=False;observation_problem=None
    if observed_at is not None:
        try:
            observation=_utc(observed_at);original=_utc(original_observed_at)
            if as_of is not None:
                at=_utc(as_of);fresh=bool(original<observation<=at and at-observation<=pd.Timedelta(hours=24))
        except (ValueError,TypeError) as exc:observation_problem=str(exc)
    source_hash_valid=isinstance(source_sha256,str) and re.fullmatch(r'[0-9a-f]{64}',source_sha256) is not None
    released_missing=[]
    if as_of is not None and 'kickoff' in c:
        at=_utc(as_of);release=pd.to_datetime(c.kickoff,utc=True)+pd.Timedelta(hours=24)
        eligible=c[c.completed & (release<at)]
        released_missing=sorted(set(eligible.game_id)-present)
    declaration_hash=hashlib.sha256(json.dumps(sorted(required),separators=(',',':')).encode()).hexdigest()
    proof=dict(schema=SCHEMA,required_primary_games=len(required),required_primary_game_ids=sorted(required),required_inventory_sha256=declaration_hash,
               exact_prior_games=len(exact),missing_prior_game_ids=missing,mismatching_prior_game_ids=unequal,
               complete_primary_coverage=not missing,semantic_equivalence_proven=full,
               source_observed_at=None if observation is None else observation.isoformat(),source_publication_at=None,
               source_sha256=source_sha256 if source_hash_valid else None,source_hash_valid=bool(source_hash_valid),fresh_observation_verified=fresh,
               candidate_for_manual_review=bool(full and fresh and source_hash_valid and not released_missing and not quarantine),automatic_serving_authorized=False,
               released_canonical_games_missing_statistics=released_missing,
               semantic_contract=SEMANTIC_CONTRACT,original_primary_observed_at=original_observed_at)
    new_ids=sorted(present-required)
    strict=set(c.loc[(c.home_fbs==1)&(c.away_fbs==1),'game_id']);context=set(c.game_id)-strict
    normalized=stats[STAT_COLUMNS].sort_values(KEYS).reset_index(drop=True)
    # Compatiblity is evidence only: no stamped V048 semantic authorization or
    # automatic feature insertion is returned from this diagnostic adapter.
    compatible=normalized[normalized.game_id.isin(exact)].copy()
    audit=dict(schema=SCHEMA,input_rows=len(cfbd_drives),normalized_rows=len(normalized),normalized_games=len(present),
               normalized_strict_FBS_games=len(present&strict),normalized_declared_opponent_context_games=len(present&context),
               new_normalized_game_ids=new_ids,new_normalized_strict_FBS_game_ids=sorted(set(new_ids)&strict),
               prior_comparison=proof,metrics=comparisons,normalization=normalization,quarantined_rows=len(quarantine),
               quarantined_game_ids=sorted(malformed_games),excluded_rows=len(excluded),excluded_reason_counts=dict(Counter(x['reason'] for x in excluded)),
               source_observation_problem=observation_problem,source_publication_at=None,new_model_fits=0,new_forecasts=0,
               model_feature_insertions=0,current_model_inputs_renewed=False,
               current_reconstructor_context_limitation='V064 accepts new stats for strict FBS targets only, while its freshness inventory includes declared FBS/FCS context; separate reviewed adapter change required.',
               status='COMPLETE_EXACT_COMPARISON_REVIEW_REQUIRED' if full else 'INCOMPLETE_OR_NON_EQUIVALENT_RETAINED_SEPARATELY')
    return dict(audit=audit,proof=proof,normalized_stats=normalized,compatible_stats=compatible,quarantine=quarantine,excluded=excluded)


def fixture_inputs():
    """Two completed synthetic games plus one future target; no estimator fit."""
    games=[];rows=[]
    for n in range(3):
        gid=str(1001+n);home=str(10+n*2);away=str(11+n*2)
        games.append(dict(track='ncaaf',game_id=gid,season=2026,home_id=home,away_id=away,home_name='Team '+home,away_name='Team '+away,
                          home_fbs=1,away_fbs=1 if n!=1 else 0,completed=n<2,kickoff=pd.Timestamp('2026-10-10T18:00:00Z')+pd.Timedelta(days=n*4)))
        if n==2:continue
        for side in [True,False]:
            for j,result in enumerate(['TD','FG','PUNT','INT']):
                rows.append(dict(gameId=int(gid),id=gid+str((0 if side else 4)+j+1),offense='Team '+(home if side else away),defense='Team '+(away if side else home),isHomeOffense=side,plays=5,yards=30,driveResult=result,startPeriod=j+1,endPeriod=j+1))
    canonical=pd.DataFrame(games);raw=[]
    for r in rows:
        g=canonical[canonical.game_id==str(r['gameId'])].iloc[0]
        raw.append(dict(game_id=str(r['gameId']),drive_id=r['id'],season=2026,team_id=g.home_id if r['isHomeOffense'] else g.away_id,result=r['driveResult'],yards=r['yards'],offensive_plays=r['plays'],start_period=r['startPeriod'],end_period=r['endPeriod']))
    primary,_,_=aggregate(pd.DataFrame(raw),'ncaaf',canonical,'synthetic_primary')
    return rows,primary,canonical
