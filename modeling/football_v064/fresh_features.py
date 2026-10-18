"""Reconstruct the existing NFL16/FBS60 inputs from observed canonical vintages.

This is deterministic feature-state replay, not model fitting. The historical
algorithm remains retrospective: source publication is unknown and kickoff+24h
is a conservative release convention. Prospective inputs additionally require
actual observations no later than the reconstruction as-of time. New FBS targets
are FBS-versus-FBS; inherited prior-opponent state remains explicitly declared.
"""
import copy
import json
import pathlib
from collections import Counter

import numpy as np
import pandas as pd

from data import FEATURES, build_features
from efficiency import METRICS, augment_features, feature_columns

BASE_COLUMNS=['track','game_id','season','week','season_type','kickoff','home_id','away_id',
              'home_name','away_name','home_points','away_points','completed','neutral',
              'home_fbs','away_fbs','source','margin','total','win','source_snapshot_at',
              'strict_point_in_time_verified']
STATS_COLUMNS=['track','game_id','team_id','opponent_id',*METRICS['ncaaf']]
SEMANTIC_CONTRACT='v048_regulation_drive_metrics_v1'
HORIZON={'nfl':24,'ncaaf':1}


def _need(ok,message):
    if not ok:raise ValueError(message)


def _utc(value):
    t=pd.Timestamp(value)
    _need(not pd.isna(t) and t.tzinfo is not None,'Known timezone-aware observation required')
    return t.tz_convert('UTC')


def _canonical(frame):
    d=frame.copy()
    required=set(BASE_COLUMNS)-{'margin','total','win','strict_point_in_time_verified','source','source_snapshot_at','home_name','away_name','season_type'}
    _need(required<=set(d),'Missing canonical columns: '+str(sorted(required-set(d))))
    for c in ['game_id','home_id','away_id']:d[c]=d[c].astype(str)
    _need(not d.duplicated(['track','game_id']).any(),'Duplicate canonical game identity')
    _need(d.track.isin(HORIZON).all(),'Unexpected sport in feature reconstruction')
    d['kickoff']=pd.to_datetime(d.kickoff,utc=True)
    _need(d.kickoff.notna().all() and (d.home_id!=d.away_id).all(),'Invalid canonical kickoff/team identity')
    _need(d.completed.isin([True,False,0,1]).all(),'Unknown completion status')
    d['completed']=d.completed.astype(bool)
    for col in ['home_points','away_points']:
        d[col]=pd.to_numeric(d[col],errors='coerce')
        ok=d.loc[d.completed,col]
        _need(np.isfinite(ok).all() and (ok>=0).all() and (ok<=150).all() and (ok==np.floor(ok)).all(),'Invalid completed score')
    _need(d.home_points.notna().equals(d.away_points.notna()),'Partial game result')
    for col in ['home_fbs','away_fbs','neutral']:_need(d[col].isin([0,1,True,False]).all(),'Invalid scope/venue flag')
    d['margin']=d.home_points-d.away_points;d['total']=d.home_points+d.away_points
    d['win']=np.where(d.completed&(d.margin!=0),(d.margin>0).astype(float),np.nan)
    defaults={'home_name':d.home_id,'away_name':d.away_id,'season_type':'regular','source':'owned canonical',
              'source_snapshot_at':None,'strict_point_in_time_verified':False}
    for col,value in defaults.items():
        if col not in d:d[col]=value
    return d[BASE_COLUMNS].sort_values(['track','kickoff','game_id'],kind='stable').reset_index(drop=True)


def _stats(frame,canonical):
    _need(set(STATS_COLUMNS)<=set(frame),'Missing historical drive sufficient statistics')
    s=frame[STATS_COLUMNS].copy()
    for c in ['game_id','team_id','opponent_id']:s[c]=s[c].astype(str)
    s=s[s.track=='ncaaf']
    _need(not s.duplicated(['track','game_id','team_id']).any(),'Duplicate drive team/game')
    _need(np.isfinite(s[list(METRICS['ncaaf'])].to_numpy(float)).all(),'Nonfinite drive metric')
    for c in ['td_drives_rate','turnover_drives_rate']:_need(s[c].between(0,1).all(),'Impossible drive rate')
    _need((s.plays_per_drive>0).all(),'Nonpositive drive plays')
    games=canonical[(canonical.track=='ncaaf')&canonical.completed].set_index('game_id')
    _need(set(s.game_id)<=set(games.index),'Drive game absent from completed canonical inventory')
    for gid,g in s.groupby('game_id',sort=False):
        row=games.loc[gid];teams={row.home_id,row.away_id}
        _need(len(g)==2 and set(g.team_id)==teams and set(g.opponent_id)==teams and (g.team_id!=g.opponent_id).all(),'Drive game/team pairing mismatch: '+gid)
    return s.reset_index(drop=True)


def replay_frozen_features(frozen_frame,historical_fbs_stats):
    """Exact definition parity over every saved row, with no model inference/fit."""
    canonical=_canonical(frozen_frame);stats=_stats(historical_fbs_stats,canonical)
    rebuilt=build_features(canonical);rebuilt,_=augment_features(rebuilt,stats)
    rows=[]
    for track in HORIZON:
        cols=FEATURES if track=='nfl' else feature_columns('ncaaf',True)
        expected=frozen_frame[frozen_frame.track==track].copy();actual=rebuilt[rebuilt.track==track].set_index('game_id')
        _need(set(actual.index)==set(expected.game_id.astype(str)),'Frozen replay game cohort mismatch')
        actual=actual.loc[expected.game_id.astype(str)]
        a=actual[cols].to_numpy(float);b=expected[cols].to_numpy(float)
        _need(np.isfinite(a).all() and np.isfinite(b).all(),'Frozen replay nonfinite feature')
        delta=np.abs(a-b)
        _need(np.allclose(a,b,atol=1e-10,rtol=1e-12),'Frozen model feature definition parity failed: '+track)
        rows.append(dict(track=track,rows=len(expected),features=len(cols),values=int(a.size),max_absolute_difference=float(delta.max()),status='PASS'))
    return dict(status='PASS',tracks=rows,new_fits=0,original_source_publication_at=None,
                strict_historical_publication_verified=False,legacy_prior_opponent_context_preserved=True)


def _observation(record):
    if not record:return None,'current_schedule_observation_missing'
    try:t=_utc(record.get('observed_at'))
    except (ValueError,TypeError):return None,'current_schedule_observation_unknown'
    digest=record.get('sha256') or record.get('rawpin',{}).get('sha256')
    if record.get('input_usable') is False:return t,'current_schedule_input_unusable'
    if not isinstance(digest,str) or len(digest)!=64:return t,'current_schedule_source_hash_missing'
    if record.get('complete_schedule') is not True:return t,'current_schedule_coverage_not_verified'
    return t,None


def reconstruct_features(frozen_frame,historical_fbs_stats,current_games,current_fbs_stats,observations,as_of):
    """Return full rebuilt frame, audit and per-future-target provenance.

    Current source snapshots may be full canonical frames; only their declared
    season is updated. No original historical source timestamp is overwritten.
    The returned target source_snapshot_at is the genuine current schedule
    observation, never the job/reconstruction time. Unapproved secondary drives
    are excluded and produce persistent opponent-state readiness taint.
    """
    as_of=_utc(as_of);frozen=_canonical(frozen_frame);current=_canonical(current_games)
    historical=_stats(historical_fbs_stats,frozen)
    merged=frozen.set_index(['track','game_id']);track_reasons={t:[] for t in HORIZON};obs={};audit_tracks={};new_ids=set();revised_ids=set()
    frozen_complete={(r.track,r.game_id):r for r in frozen[frozen.completed].itertuples()}
    for track in HORIZON:
        receipt=observations.get(track,{});seen,reason=_observation(receipt);obs[track]=seen
        if reason:track_reasons[track].append(reason)
        if receipt.get('input_usable') is False:track_reasons[track].extend(receipt.get('reasons',[]))
        if seen is not None and seen>as_of:track_reasons[track].append('schedule_observed_after_as_of')
        season=int(receipt.get('season',2026));patch=current[(current.track==track)&(current.season==season)].copy()
        if track=='ncaaf':patch=patch[(patch.home_fbs==1)|(patch.away_fbs==1)]
        old=frozen[(frozen.track==track)&(frozen.season==season)]
        if track=='ncaaf':old=old[(old.home_fbs==1)|(old.away_fbs==1)]
        missing=sorted(set(old.game_id)-set(patch.game_id))
        if missing:track_reasons[track].append('current_schedule_omits_known_target_games')
        if patch.empty:track_reasons[track].append('current_schedule_empty')
        changes=[];added=[]
        # Unknown/after-as-of observation cannot revise state, even if bytes exist.
        usable=seen is not None and seen<=as_of and not reason
        if usable:
            _need(not (patch.completed & (patch.kickoff>=seen)).any(),'Completed game before kickoff/source observation')
            for row in patch.to_dict('records'):
                key=(track,row['game_id'])
                if key in merged.index:
                    before=merged.loc[key]
                    _need(str(before.home_id)==row['home_id'] and str(before.away_id)==row['away_id'],'Canonical identity changed for an existing game')
                    if bool(before.completed):
                        _need(row['completed'],'Previously final game became incomplete')
                        if before.home_points!=row['home_points'] or before.away_points!=row['away_points']:
                            revised_ids.add(key);changes.append(row['game_id'])
                    elif row['completed']:new_ids.add(key);added.append(row['game_id'])
                elif row['completed']:new_ids.add(key);added.append(row['game_id'])
                row['source_snapshot_at']=seen.isoformat()
                if key in merged.index:
                    merged.loc[key,:]=[row[c] for c in merged.columns]
                else:
                    added_row=pd.DataFrame([row]).set_index(['track','game_id'])
                    merged=pd.concat([merged,added_row[merged.columns]],axis=0)
        audit_tracks[track]=dict(observed_at=None if seen is None else seen.isoformat(),source_sha256=receipt.get('sha256') or receipt.get('rawpin',{}).get('sha256'),
            current_rows=len(patch),current_completed=int(patch.completed.sum()),new_completed_ids=sorted(added),revised_result_ids=sorted(changes),
            new_completed_fbs_vs_fbs_ids=sorted(set(added)&set(patch.loc[(patch.home_fbs==1)&(patch.away_fbs==1),'game_id'])) if track=='ncaaf' else [],
            missing_known_game_ids=missing,schedule_input_usable=usable,reasons=track_reasons[track])
    canonical=merged.reset_index().sort_values(['track','kickoff','game_id'],kind='stable').reset_index(drop=True)
    _need(not canonical.duplicated(['track','game_id']).any(),'Merged canonical identity collision')
    # Prior target-cohort restriction does not erase declared archived opponents.
    eligible=canonical.completed & (canonical.kickoff+pd.Timedelta(hours=24)<as_of)
    eligible_keys=set(zip(canonical.loc[eligible,'track'],canonical.loc[eligible,'game_id']))
    stats=historical.copy();accepted_current=[];rejected=[];observed_drive={};new_stats_games=set()
    if len(current_fbs_stats):
        needed=set(STATS_COLUMNS)|{'source_observed_at','source_sha256','semantic_contract'}
        _need(needed<=set(current_fbs_stats),'New drive stats require observation/hash/semantic contract')
        raw=current_fbs_stats.copy()
        for c in ['game_id','team_id','opponent_id']:raw[c]=raw[c].astype(str)
        _need(not raw.duplicated(['track','game_id','team_id']).any(),'Duplicate new drive identity')
        for gid,g in raw.groupby('game_id',sort=False):
            reason=None
            try:
                _need((g.track=='ncaaf').all(),'New drive track mismatch')
                can=canonical[(canonical.track=='ncaaf')&(canonical.game_id==gid)]
                _need(len(can)==1 and bool(can.iloc[0].completed),'New drive game not completed')
                _need(can.iloc[0].home_fbs==1 and can.iloc[0].away_fbs==1,'New drive target not FBS versus FBS')
                _need((g.semantic_contract==SEMANTIC_CONTRACT).all(),'Secondary drive semantics unverified')
                clocks=[_utc(x) for x in g.source_observed_at]
                _need(max(clocks)<=as_of,'Drive observed after as-of')
                _need(g.source_sha256.map(lambda x:isinstance(x,str) and len(x)==64).all(),'Missing drive source hash')
                _need(('ncaaf',gid) in eligible_keys,'Drive conservative release not reached')
                valid=_stats(g,can);accepted_current.append(valid);observed_drive[gid]=max(clocks);new_stats_games.add(gid)
            except (ValueError,TypeError) as exc:reason=str(exc)
            if reason:rejected.append(dict(game_id=gid,reason=reason))
    if accepted_current:
        stats=stats[~stats.game_id.isin(new_stats_games)];stats=pd.concat([stats,*accepted_current],ignore_index=True)
    # Score revisions without renewed matching drive evidence cannot reuse old
    # efficiency silently. Old pre-existing declared missing games remain gaps.
    revised_fbs={gid for track,gid in revised_ids if track=='ncaaf'}
    stats=stats[~stats.game_id.isin(revised_fbs-new_stats_games)]
    stats=stats[stats.game_id.isin(canonical.loc[eligible&(canonical.track=='ncaaf'),'game_id'])]
    model_games=canonical.copy();model_games.loc[~eligible,'completed']=False
    built=build_features(model_games);built,_=augment_features(built,stats)
    # Restore canonical status/labels; flags used for state replay are internal.
    original=canonical.set_index(['track','game_id'])
    for col in ['completed','home_points','away_points','margin','total','win']:
        built[col]=[original.loc[(r.track,r.game_id),col] for r in built.itertuples()]
    tainted={};taint_events=[];covered=set(stats.game_id)
    for r in canonical[eligible&(canonical.track=='ncaaf')].sort_values(['kickoff','game_id']).itertuples():
        key=('ncaaf',r.game_id);why=set()
        if (key in new_ids or key in revised_ids) and r.game_id not in covered:why.add(r.game_id)
        inherited=set(tainted.get(r.home_id,set()))|set(tainted.get(r.away_id,set()))
        # An observed efficient game uses both pre-update opponent states.
        if r.game_id in covered:why|=inherited
        if why:
            tainted.setdefault(r.home_id,set()).update(why);tainted.setdefault(r.away_id,set()).update(why)
            taint_events.append(dict(game_id=r.game_id,missing_compatible_drive_game_ids=sorted(why)))
    # A newer schedule does not reobserve existing current-season drive metrics.
    # Without actual compatible metric rows for the complete contributing
    # current-season inventory, its observation clock remains unknown. Historical
    # season aggregates remain frozen by the saved-model definition.
    current_eff_ids=set(canonical.loc[eligible&(canonical.track=='ncaaf')&(canonical.season==int(observations.get('ncaaf',{}).get('season',2026))),'game_id']) & covered
    eff_reobserved=bool(current_eff_ids) and current_eff_ids<=new_stats_games
    original_eff=observations.get('ncaaf_efficiency',{})
    original_eff_observed=None
    if original_eff.get('semantic_contract')==SEMANTIC_CONTRACT and all(isinstance(original_eff.get(k),str) and len(original_eff[k])==64 for k in ['sha256','aggregate_sha256']):
        try:original_eff_observed=_utc(original_eff.get('observed_at'))
        except (ValueError,TypeError):pass
    eff_observed=min((observed_drive[g] for g in current_eff_ids),default=None) if eff_reobserved else original_eff_observed
    eff_domain=dict(required_current_season_metric_games=len(current_eff_ids),
        reobserved_current_season_metric_games=len(current_eff_ids&new_stats_games),
        complete_current_season_reobservation=eff_reobserved,
        observed_at=None if eff_observed is None else eff_observed.isoformat(),
        source_publication_at=None,original_current_efficiency_observation_unknown=original_eff_observed is None,
        original_source_observed_at=None if original_eff_observed is None else original_eff_observed.isoformat(),
        original_raw_sha256=original_eff.get('sha256'),original_aggregate_sha256=original_eff.get('aggregate_sha256'),
        proof='all contributing current-season compatible metric rows reobserved' if eff_reobserved else original_eff.get('source'))
    future=canonical[~canonical.completed & (canonical.kickoff>as_of)].copy()
    future=future[(future.track=='nfl')|((future.home_fbs==1)&(future.away_fbs==1))]
    future_keys=set(zip(future.track,future.game_id));provenance=[]
    built['reconstruction_ready']=False;built['reconstruction_reasons']='[]';built['fresh_feature_available_at']=pd.Series(pd.NaT,index=built.index,dtype='datetime64[ns, UTC]')
    built['current_efficiency_observed_at']=pd.Series(pd.NaT,index=built.index,dtype='datetime64[ns, UTC]')
    built['current_efficiency_freshness_verified']=False
    built['source_publication_at']=None;built['strict_point_in_time_verified']=False
    for ix,r in built.iterrows():
        key=(r.track,r.game_id)
        if key not in future_keys:continue
        cutoff=_utc(r.kickoff)-pd.Timedelta(hours=HORIZON[r.track]);reasons=list(track_reasons[r.track]);seen=obs[r.track]
        missing=[]
        if r.track=='ncaaf':
            missing=sorted(set(tainted.get(r.home_id,set()))|set(tainted.get(r.away_id,set())))
            if missing:reasons.append('released_history_missing_compatible_drive_statistics')
            if eff_observed is not None:built.at[ix,'current_efficiency_observed_at']=eff_observed
            if eff_observed is None:reasons.append('efficiency_observation_or_equivalence_unverified')
            elif eff_observed>as_of:reasons.append('current_efficiency_observation_after_as_of')
            elif as_of-eff_observed>pd.Timedelta(hours=24):reasons.append('current_efficiency_source_stale')
            else:built.at[ix,'current_efficiency_freshness_verified']=True
        consumed=[_utc(frozen_frame.source_snapshot_at.dropna().min())]
        if seen is not None:consumed.append(seen)
        if r.track=='ncaaf':
            consumed.extend(observed_drive.values())
            if eff_observed is not None:consumed.append(eff_observed)
        availability=max(consumed)
        if availability>as_of:reasons.append('input_observed_after_as_of')
        if availability>=cutoff:reasons.append('input_not_observed_before_decision')
        if as_of>cutoff:reasons.append('issue_deadline_passed')
        if seen is None or as_of-seen>pd.Timedelta(hours=24):reasons.append('current_schedule_snapshot_stale_or_unknown')
        # The timestamp is a genuine input observation, not wall-clock refresh.
        built.at[ix,'source_snapshot_at']=None if seen is None else seen.isoformat()
        built.at[ix,'fresh_feature_available_at']=availability
        built.at[ix,'reconstruction_ready']=not reasons;built.at[ix,'reconstruction_reasons']=json.dumps(sorted(set(reasons)))
        cols=FEATURES if r.track=='nfl' else feature_columns('ncaaf',True)
        _need(np.isfinite(built.loc[[ix],cols].to_numpy(float)).all(),'Nonfinite rebuilt model features')
        provenance.append(dict(track=r.track,game_id=r.game_id,decision_at=cutoff,as_of=as_of,
            source_observed_at=seen,feature_available_at=availability,source_publication_at=None,
            assumed_label_release_hours=24,reconstruction_ready=not reasons,reasons=json.dumps(sorted(set(reasons))),
            missing_drive_game_ids=json.dumps(missing),feature_count=len(cols),legacy_prior_opponent_context=r.track=='ncaaf',
            current_efficiency_observed_at=eff_observed if r.track=='ncaaf' else None,
            current_efficiency_freshness_verified=bool(built.at[ix,'current_efficiency_freshness_verified']) if r.track=='ncaaf' else None,
            strict_historical_publication_verified=False))
    prov=pd.DataFrame(provenance)
    audit=dict(status='RECONSTRUCTED_WITH_EXPLICIT_ELIGIBILITY',as_of=as_of.isoformat(),tracks=audit_tracks,
        canonical_rows=len(canonical),historical_drive_team_rows=len(historical),current_compatible_drive_games=len(new_stats_games),
        rejected_current_drive_games=rejected,eligible_released_completed_games=len(eligible_keys),
        future_target_games=len(prov),ready_future_targets=int(prov.reconstruction_ready.sum()) if len(prov) else 0,
        reasons=dict(Counter(reason for row in provenance for reason in json.loads(row['reasons']))),
        current_efficiency_domain=eff_domain,taint_events=taint_events,new_fits=0,new_provider_requests=0,source_publication_at=None,
        historical_publication_verified=False,feature_definitions_changed=False,
        source_timestamps_not_reset_from_job_clock=True,legacy_prior_opponent_context_preserved=True,
        new_college_targets='FBS versus FBS only')
    return built,audit,prov


def _runtime_utc_now():
    return pd.Timestamp.now(tz='UTC')


def rebuild_serving(ctx,serving,sources):
    """Root-worker adapter; writes four checkpointable zero-fit artifacts."""
    root=pathlib.Path(ctx.root)
    cp=getattr(ctx,'cp',None)
    if cp is not None and cp.lookup('exact_feature_reconstruction_and_serving') is not None:
        # lookup verifies every checkpoint hash, including snapshot and parity.
        result=dict(serving);result['frame']=pd.read_parquet(root/'fresh_features.parquet')
        result['canonical']=result['frame'][BASE_COLUMNS].copy()
        result['snapshot']=json.loads((root/'snapshot_contract.json').read_text())
        result['parity']=json.loads((root/'serving_parity.json').read_text())
        result['reconstruction_audit']=json.loads((root/'feature_reconstruction.json').read_text())
        result['feature_replay_parity']=json.loads((root/'feature_replay_parity.json').read_text())
        return result
    if ctx.fixture:
        frozen=serving['frame'].copy()
        for col,value in [('neutral',0),('season_type','regular'),('source','synthetic fixture')]:
            if col not in frozen:frozen[col]=value
        stats=[]
        for r in frozen[(frozen.track=='ncaaf')&frozen.completed].itertuples():
            for team,opp in [(r.home_id,r.away_id),(r.away_id,r.home_id)]:stats.append(dict(track='ncaaf',game_id=r.game_id,team_id=team,opponent_id=opp,**METRICS['ncaaf']))
        stats=pd.DataFrame(stats,columns=STATS_COLUMNS)
        frozen,_=augment_features(build_features(_canonical(frozen)),stats)
        # Synthetic constant serving fixture has one explicit input, unrelated
        # to research-model fitting; it remains labeled as fixture.
        frozen['x']=1.
        current=sources.get('current_games',frozen).copy()
        for col,value in [('neutral',0),('season_type','regular'),('source','synthetic fixture')]:
            if col not in current:current[col]=value
        asof=pd.Timestamp(serving['fixture_now'])
    else:
        frozen=serving['frame']
        paths=sorted((root/'cache').glob('aggregate_ncaaf_drives_*.parquet'))
        _need(len(paths)==11,'Exactly11 owned historical FBS aggregate assets required')
        stats=pd.concat([pd.read_parquet(p) for p in paths],ignore_index=True)
        current=sources['current_games'];asof=_runtime_utc_now()
    replay=replay_frozen_features(frozen,stats)
    observations=copy.deepcopy(sources['observations'])
    if not ctx.fixture and observations.get('ncaaf_efficiency',{}).get('aggregate_sha256'):
        import hashlib
        pinned_current=root/'cache'/'aggregate_ncaaf_drives_2026.parquet'
        _need(hashlib.sha256(pinned_current.read_bytes()).hexdigest()==observations['ncaaf_efficiency']['aggregate_sha256'],
              'Original efficiency observation is not bound to loaded current-season aggregate')
    if ctx.fixture:
        for t in HORIZON:
            observations.setdefault(t,{})
            observations[t].update(observed_at=(asof-pd.Timedelta(hours=1)).isoformat(),sha256='d'*64,complete_schedule=True,season=2026)
    current_stats=sources.get('current_fbs_stats',pd.DataFrame(columns=STATS_COLUMNS))
    if ctx.fixture:
        # Explicit synthetic full reobservation; never applies to real sources.
        current_stats=stats.copy();current_stats['source_observed_at']=(asof-pd.Timedelta(hours=1)).isoformat()
        current_stats['source_sha256']='d'*64;current_stats['semantic_contract']=SEMANTIC_CONTRACT
    frame,audit,prov=reconstruct_features(frozen,stats,current,current_stats,observations,asof)
    if ctx.fixture:frame['x']=1.
    frame.to_parquet(root/'fresh_features.parquet',index=False);prov.to_parquet(root/'feature_provenance.parquet',index=False)
    (root/'feature_reconstruction.json').write_text(json.dumps(audit,indent=2)+'\n')
    (root/'feature_replay_parity.json').write_text(json.dumps(replay,indent=2)+'\n')
    result=dict(serving);result['frame']=frame;result['canonical']=_canonical(current)
    # Include archived history so the existing per-team missing/revision guard
    # remains meaningful; the rebuilt frame uses the same merged canonical rows.
    result['canonical']=frame[BASE_COLUMNS].copy()
    snapshot=copy.deepcopy(serving['snapshot']);snapshot['tracks']={}
    for track,record in audit['tracks'].items():
        seen=record['observed_at'] or snapshot['feature_observed_at']
        snapshot['tracks'][track]=dict(feature_observed_at=seen,canonical_observed_at=seen,
            feature_policy='reconstructed_saved_definitions_from_observed_inputs',source_sha256=record['source_sha256'])
    import hashlib
    snapshot['tracks']['ncaaf']['current_efficiency_domain']=audit['current_efficiency_domain']
    snapshot['feature_sha256']=hashlib.sha256((root/'fresh_features.parquet').read_bytes()).hexdigest()
    snapshot['reconstructed']=True;snapshot['canonical_inventory']='merged observed current schedules and preserved pinned historical rows'
    result['snapshot']=snapshot;result['reconstruction_audit']=audit;result['feature_replay_parity']=replay
    return result
