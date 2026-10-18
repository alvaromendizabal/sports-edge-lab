"""Owned-model inference, information-time eligibility and append-only shadow ledger.

No estimator is fitted here. Production issue time is runtime UTC, never a supplied
backdate. Retrospective serving replay does not establish strict historical PIT or
promote a model. Application append-only is not a claim of tamper-proof storage.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import os
import pathlib
from collections import Counter
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

HORIZON_HOURS = {'nfl': 24, 'ncaaf': 1}
TASKS = ('win', 'margin', 'total')
PROTOCOL = 'football-shadow-v064'
MAX_GAMES = 200
MAX_LOOKAHEAD_DAYS = 7
MAX_SNAPSHOT_AGE_HOURS = 24


def _require(value, message):
    if not value:
        raise ValueError(message)


def _utc(value):
    t = pd.Timestamp(value)
    _require(not pd.isna(t) and t.tzinfo is not None, 'Timestamp must be known and timezone-aware')
    return t.tz_convert('UTC')


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _unknown_history_clock(frame, track):
    unknown=pd.Series(False,index=frame.index)
    pairs=[('feature_max_available_at',['home_games','away_games'])]
    if track=='ncaaf':pairs.append(('efficiency_max_available_at',['eff_home_games','eff_away_games']))
    for clock,counts in pairs:
        positive=pd.Series(False,index=frame.index)
        for name in counts:
            if name in frame:positive|=pd.to_numeric(frame[name],errors='coerce').fillna(0)>0
        missing=pd.Series(True,index=frame.index) if clock not in frame else pd.to_datetime(frame[clock],utc=True).isna()
        unknown|=positive&missing
    return bool(unknown.any())


def load_owned_model(path, contract):
    """Verify bytes against an embedded owned-return pin *before* deserialization.

    A hash alone does not establish trustworthy code: the caller must obtain this
    contract from its frozen owned-return manifest, never a downloaded sidecar.
    Only the project's previously fitted sklearn linear objects are accepted.
    """
    p = pathlib.Path(path)
    pin = contract['model_pin']
    _require(contract.get('owned_manifest_sha256') and len(contract['owned_manifest_sha256']) == 64,
             'Missing frozen owned-manifest provenance')
    _require(p.is_file() and not p.is_symlink(), 'Owned model is missing or symlinked')
    raw = p.read_bytes()
    _require(len(raw) == pin['bytes'], 'Owned model byte-count mismatch before deserialization')
    _require(_sha(raw) == pin['sha256'], 'Owned model SHA mismatch before deserialization')
    import sklearn
    _require(sklearn.__version__ == contract['sklearn_version'], 'Owned model sklearn version mismatch')
    # Read verified bytes, not a path that could be replaced between verification/load.
    import io
    model = joblib.load(io.BytesIO(raw))
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    expected = LogisticRegression if contract['task'] == 'win' else Ridge
    if contract['format'] == 'sklearn_pipeline':
        _require(type(model) is Pipeline and len(model.steps) == 2 and
                 type(model.steps[0][1]) is StandardScaler and type(model.steps[1][1]) is expected,
                 'Unsupported owned pipeline type')
    elif contract['format'] == 'linear_bundle':
        _require(type(model) is dict and model.get('family') == 'linear' and
                 model.get('task') == contract['task'] and type(model.get('estimator')) is expected and
                 type(model.get('x_scaler')) is StandardScaler and model.get('y_scaler') is None,
                 'Unsupported owned linear bundle')
        _require(model.get('fixture_iterations_override') is None, 'Fixture model cannot be used in production')
    else:
        raise ValueError('Unsupported owned model format')
    return model


def predict_existing(model, frame, contract):
    cols = contract['features']
    _require(len(cols) > 0 and len(cols) == len(set(cols)) and set(cols) <= set(frame), 'Feature contract mismatch')
    x = frame[cols].to_numpy(dtype=float)
    _require(x.ndim == 2 and len(x) and np.isfinite(x).all(), 'Invalid inference features')
    if contract['format'] == 'linear_bundle':
        _require(model.get('family') == 'linear' and model.get('task') == contract['task'] and
                 model.get('n_features') == x.shape[1], 'Linear model contract mismatch')
        names = model.get('feature_names')
        _require(names is None or list(names) == cols, 'Saved feature order mismatch')
        x = model['x_scaler'].transform(x)
        estimator = model['estimator']
    elif contract['format'] == 'sklearn_pipeline':
        estimator = model
    elif contract['format'] == 'fixture' and contract.get('fixture') is True:
        estimator = model
    else:
        raise ValueError('Unsupported inference format')
    _require(getattr(estimator, 'n_features_in_', x.shape[1]) == x.shape[1], 'Saved feature width mismatch')
    with threadpool_limits(limits=2):
        if contract['task'] == 'win':
            classes = list(estimator.classes_)
            _require(classes == [0, 1] or classes == [0.0, 1.0], 'Invalid win classes')
            p = np.clip(estimator.predict_proba(x)[:, classes.index(1)], 1e-7, 1-1e-7)
        else:
            p = estimator.predict(x)
    p = np.asarray(p, dtype=float)
    _require(p.shape == (len(frame),) and np.isfinite(p).all(), 'Nonfinite or malformed predictions')
    return p


def verify_serving_parity(model, frame, cached_predictions, contract):
    """Replay the exact saved 2026 monitor cohort, with no fit or selection."""
    track, task = contract['track'], contract['task']
    p = cached_predictions.copy()
    p = p[(p.track == track) & (p.task == task) & (p.season == 2026)].copy()
    _require(len(p) == contract['expected_parity_rows'] and len(p) > 0, 'Serving parity cohort count mismatch')
    _require(not p.game_id.duplicated().any(), 'Duplicate serving parity reference')
    f = frame[(frame.track == track) & (frame.season == 2026) & frame.completed].copy()
    if track == 'ncaaf':
        f = f[(f.home_fbs == 1) & (f.away_fbs == 1)]
    if task == 'win':
        f = f[f.win.notna()]
    _require(not f.game_id.duplicated().any() and set(f.game_id) == set(p.game_id), 'Serving parity identity mismatch')
    f = f.set_index('game_id').loc[p.game_id].reset_index()
    _require(np.array_equal(f[task].to_numpy(float), p.target.to_numpy(float)), 'Serving parity target mismatch')
    _require(np.array_equal(pd.to_datetime(f.kickoff, utc=True).astype('int64'),
                            pd.to_datetime(p.kickoff, utc=True).astype('int64')), 'Serving parity kickoff mismatch')
    cutoff = pd.to_datetime(f.kickoff, utc=True) - pd.Timedelta(hours=HORIZON_HOURS[track])
    _require(not _unknown_history_clock(f,track),'Serving parity positive history has unknown availability clock')
    if 'decision_at' in p:
        _require(np.array_equal(cutoff.astype('int64'), pd.to_datetime(p.decision_at, utc=True).astype('int64')),
                 'Serving parity decision mismatch')
    for col in ['feature_max_available_at', 'efficiency_max_available_at']:
        if col in f and (track == 'ncaaf' or col == 'feature_max_available_at'):
            clock = pd.to_datetime(f[col], utc=True)
            _require(not (clock >= cutoff).any(), 'Serving parity consumes unavailable history')
    _require(_utc(contract['train_latest_release']) < cutoff.min(), 'Serving parity train-release overlap')
    got = predict_existing(model, f, contract)
    expected = p[contract['reference_column']].to_numpy(float)
    _require(np.isfinite(expected).all() and np.allclose(got, expected, atol=1e-10, rtol=1e-10), 'Serving parity predictions mismatch')
    return dict(model_id=contract['id'], track=track, task=task, n=len(f), max_absolute_difference=float(np.max(np.abs(got-expected))),
                status='PASS', new_fits=0, prospective_evidence=False, model_promoted=False,
                feature_order_sha256=_sha(_json_bytes(contract['features'])), model_sha256=contract['model_pin']['sha256'])


def _record_key(record):
    fields = [PROTOCOL, record['track'], record['game_id'], record['task'], record['model_id'], record['decision_at'], record['status']]
    if record['status'] == 'abstained':
        fields.append(record['issued_at'])
    return _sha(_json_bytes(fields))


def issue_forecasts(frame, canonical, contracts, models, snapshot, fixture_now=None):
    """Issue finite next-seven-day predictions or durable, reasoned abstentions.

    Frozen histories must be at most 24h old AND cover every newly released team
    result in the supplied current canonical inventory. Passing does not prove
    the inventory contains every source revision. This is frozen-snapshot shadow
    inference, not an updated feature rebuild or known-starter model.
    """
    fixture = snapshot.get('fixture') is True
    _require(fixture_now is None or fixture, 'Production issuance time cannot be supplied or backdated')
    issued = _utc(fixture_now if fixture_now is not None else datetime.now(timezone.utc))
    _require(snapshot.get('max_age_hours', MAX_SNAPSHOT_AGE_HOURS) == MAX_SNAPSHOT_AGE_HOURS,
             'Frozen snapshot freshness limit cannot be expanded')
    _require(snapshot.get('lookahead_days', MAX_LOOKAHEAD_DAYS) == MAX_LOOKAHEAD_DAYS, 'Lookahead cannot be expanded')
    _require(not frame.duplicated(['track','game_id']).any(), 'Duplicate feature identity')
    _require(not canonical.duplicated(['track','game_id']).any(), 'Duplicate canonical identity')
    _require(len({c['id'] for c in contracts}) == len(contracts), 'Duplicate model contract')
    source_observed = _utc(snapshot['feature_observed_at'])
    canonical_observed = _utc(snapshot['canonical_observed_at'])
    games = canonical[(canonical.track.isin(HORIZON_HOURS)) & ~canonical.completed].copy()
    games['kickoff'] = pd.to_datetime(games.kickoff, utc=True)
    games = games[(games.kickoff > issued) & (games.kickoff <= issued+pd.Timedelta(days=MAX_LOOKAHEAD_DAYS))]
    # No FCS target is scored, including an abstention record; report excluded population.
    excluded = int(((games.track == 'ncaaf') & ~((games.home_fbs == 1) & (games.away_fbs == 1))).sum())
    games = games[(games.track == 'nfl') | ((games.home_fbs == 1) & (games.away_fbs == 1))]
    _require(len(games) <= MAX_GAMES, 'Finite upcoming-game bound exceeded')
    completed = canonical[canonical.completed].copy()
    completed['kickoff'] = pd.to_datetime(completed.kickoff, utc=True)
    records = []
    for g in games.sort_values(['kickoff','track','game_id'], kind='stable').to_dict('records'):
        track_snapshot=snapshot.get('tracks',{}).get(g['track'],{})
        source_observed=_utc(track_snapshot.get('feature_observed_at',snapshot['feature_observed_at']))
        canonical_observed=_utc(track_snapshot.get('canonical_observed_at',snapshot['canonical_observed_at']))
        cutoff = _utc(g['kickoff'])-pd.Timedelta(hours=HORIZON_HOURS[g['track']])
        row = frame[(frame.track == g['track']) & (frame.game_id.astype(str) == str(g['game_id']))]
        reason = [];inherited=None;efficiency_observed=None
        if issued > cutoff: reason.append('issue_deadline_passed')
        if source_observed > issued or canonical_observed > issued: reason.append('source_observed_after_issue')
        if issued-source_observed > pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS): reason.append('frozen_feature_snapshot_stale')
        if issued-canonical_observed > pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS): reason.append('canonical_snapshot_stale')
        if source_observed >= cutoff or canonical_observed >= cutoff: reason.append('source_not_observed_before_cutoff')
        if len(row) != 1:
            reason.append('missing_exact_feature_row')
        else:
            fr = row.iloc[0]
            if snapshot.get('reconstructed'):
                if 'reconstruction_ready' not in row or not bool(fr.reconstruction_ready):
                    reason.append('reconstructed_feature_inputs_not_ready')
                    if 'reconstruction_reasons' in row:
                        extra=json.loads(fr.reconstruction_reasons) if isinstance(fr.reconstruction_reasons,str) else fr.reconstruction_reasons
                        _require(isinstance(extra,list) and all(isinstance(x,str) for x in extra),'Invalid reconstruction readiness reasons')
                        reason.extend(extra)
                if 'fresh_feature_available_at' not in row or pd.isna(fr.fresh_feature_available_at):
                    reason.append('reconstructed_feature_observation_unknown')
                else:
                    observed=_utc(fr.fresh_feature_available_at)
                    if observed>issued or observed>=cutoff:reason.append('reconstructed_feature_observation_not_available')
                if g['track']=='ncaaf':
                    verified='current_efficiency_freshness_verified' in row and bool(fr.current_efficiency_freshness_verified)
                    try:efficiency_observed=_utc(fr.get('current_efficiency_observed_at'))
                    except (ValueError,TypeError):pass
                    if efficiency_observed is None:reason.append('efficiency_observation_or_equivalence_unverified')
                    elif efficiency_observed>issued or efficiency_observed>=cutoff:reason.append('current_efficiency_observation_not_available')
                    elif issued-efficiency_observed>pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):reason.append('current_efficiency_source_stale')
                    elif not verified:reason.append('efficiency_observation_or_equivalence_unverified')
            if _unknown_history_clock(row,g['track']):reason.append('positive_history_has_unknown_availability_clock')
            if str(fr.home_id) != str(g['home_id']) or str(fr.away_id) != str(g['away_id']) or _utc(fr.kickoff) != _utc(g['kickoff']):
                reason.append('canonical_feature_identity_or_kickoff_changed')
            if bool(fr.completed): reason.append('feature_row_already_completed')
            if 'source_snapshot_at' in row:
                try:inherited = _utc(fr.source_snapshot_at)
                except (ValueError,TypeError):reason.append('inherited_feature_source_vintage_unknown')
                if inherited is not None:
                    if inherited > issued: reason.append('feature_source_vintage_after_issue')
                    if issued-inherited > pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS): reason.append('inherited_feature_source_stale')
            for col in ['feature_max_available_at','efficiency_max_available_at']:
                if col in row and (g['track'] == 'ncaaf' or col == 'feature_max_available_at') and not pd.isna(fr[col]):
                    t = _utc(fr[col])
                    if t >= cutoff or t > issued: reason.append('feature_history_not_available')
            past = completed[(completed.track == g['track']) & (completed.kickoff+pd.Timedelta(hours=24) < min(cutoff, issued))]
            team = {str(g['home_id']),str(g['away_id'])}
            past = past[past.home_id.astype(str).isin(team) | past.away_id.astype(str).isin(team)]
            frozen = frame[(frame.track == g['track']) & frame.completed]
            missing = sorted(set(past.game_id.astype(str))-set(frozen.game_id.astype(str)))
            if missing: reason.append('newly_released_team_result_missing_from_frozen_history')
            # Revisions to a known result are also stale input, not merely missing IDs.
            common = past.merge(frozen[['game_id','home_points','away_points']],on='game_id',suffixes=('','_frozen'))
            if len(common) and ((common.home_points != common.home_points_frozen) | (common.away_points != common.away_points_frozen)).any():
                reason.append('released_result_revised_since_frozen_features')
        for c in [c for c in contracts if c['track'] == g['track']]:
            reasons = list(reason)
            if c['id'] not in models: reasons.append('verified_model_unavailable')
            if _utc(c['model_available_at']) > issued: reasons.append('model_not_available_at_issue')
            if _utc(c['train_latest_release']) >= cutoff or _utc(c['train_latest_release']) > issued: reasons.append('training_label_not_available')
            if snapshot.get('parity_by_model', {}).get(c['id']) != 'PASS': reasons.append('serving_parity_unverified')
            if len(row) == 1:
                try:
                    valid = set(c['features']) <= set(row) and np.isfinite(row[c['features']].to_numpy(float)).all()
                except (ValueError, TypeError): valid = False
                if not valid: reasons.append('nonfinite_or_missing_features')
            rec = dict(protocol=PROTOCOL, record_type='shadow_forecast', track=g['track'], game_id=str(g['game_id']),
                       home_id=str(g['home_id']), away_id=str(g['away_id']), season=int(g['season']),
                       task=c['task'], model_id=c['id'], model_role=c['role'], model_sha256=c['model_pin']['sha256'],
                       feature_snapshot_sha256=snapshot['feature_sha256'], feature_order_sha256=_sha(_json_bytes(c['features'])),
                       kickoff=_utc(g['kickoff']).isoformat(), decision_at=cutoff.isoformat(), issued_at=issued.isoformat(),
                       horizon_hours=HORIZON_HOURS[g['track']], actual_lead_hours=(_utc(g['kickoff'])-issued).total_seconds()/3600,
                       feature_observed_at=source_observed.isoformat(), canonical_observed_at=canonical_observed.isoformat(),
                       current_efficiency_observed_at=None if efficiency_observed is None else efficiency_observed.isoformat(),
                       current_efficiency_domain_required=bool(snapshot.get('reconstructed') and g['track']=='ncaaf'),
                       source_publication_at=None, strict_historical_point_in_time_verified=False,
                       shadow=True, new_model_promotion=False, known_starting_qb_used=False,
                       feature_policy=track_snapshot.get('feature_policy','frozen_snapshot_max_24h_with_known_released_team_history_check'),
                       legacy_prior_opponent_context=bool(c.get('legacy_prior_opponent_context',False)),
                       training_target_scope=c['training_target_scope'], status='abstained' if reasons else 'issued',
                       reasons=sorted(set(reasons)), prediction=None, fixture=fixture)
            if not reasons: rec['prediction'] = float(predict_existing(models[c['id']], row, c)[0])
            # Inference can cross a deadline. Production timestamps describe the
            # completed forecast, never the earlier start of a slow batch.
            final_issued = issued if fixture_now is not None else _utc(datetime.now(timezone.utc))
            rec['issued_at'] = final_issued.isoformat()
            rec['actual_lead_hours'] = (_utc(g['kickoff'])-final_issued).total_seconds()/3600
            if final_issued > cutoff: rec['reasons'].append('issue_deadline_passed')
            if final_issued-source_observed > pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):
                rec['reasons'].append('frozen_feature_snapshot_stale')
            if final_issued-canonical_observed > pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):
                rec['reasons'].append('canonical_snapshot_stale')
            if efficiency_observed is not None and final_issued-efficiency_observed>pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):
                rec['reasons'].append('current_efficiency_source_stale')
            if inherited is not None and final_issued-inherited>pd.Timedelta(hours=MAX_SNAPSHOT_AGE_HOURS):
                rec['reasons'].append('inherited_feature_source_stale')
            rec['reasons']=sorted(set(rec['reasons']))
            if rec['reasons']: rec['status']='abstained';rec['prediction']=None
            rec['record_key'] = _record_key(rec)
            records.append(rec)
    counts = Counter(r['status'] for r in records)
    return records, dict(protocol=PROTOCOL, issued_at=issued.isoformat(), eligible_schedule_games=len(games),
                         excluded_non_fbs_games=excluded, records=len(records), forecasts=counts['issued'],
                         abstentions=counts['abstained'], reasons=dict(Counter(x for r in records for x in r['reasons'])),
                         new_fits=0, new_provider_requests=0, new_model_promotions=0,
                         no_latest_history_claim=True, fixture=fixture)


def append_records(path, records):
    """Locked local append-only hash chain; root syncs the committed ledger.

    Identical retries reuse records. A conflicting forecast under the same
    game/model/horizon identity is rejected; no overwrite or backfill is allowed.
    """
    import fcntl
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with open(str(p)+'.lock','a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        old=[];by={};previous=None;existing_bytes=b''
        if p.exists():
            existing_bytes=p.read_bytes()
            _require(not existing_bytes or existing_bytes.endswith(b'\n'),'Incomplete existing ledger')
            for line in existing_bytes.decode().splitlines():
                x=json.loads(line);body={k:v for k,v in x.items() if k!='record_hash'}
                _require(x.get('previous_hash')==previous and _sha(_json_bytes(body))==x.get('record_hash'),'Ledger integrity mismatch')
                _require(x['record_key'] not in by,'Duplicate existing ledger key')
                old.append(x);by[x['record_key']]=x;previous=x['record_hash']
        additions=[];reused=0
        for record in records:
            r=copy.deepcopy(record)
            _require(r['record_key']==_record_key(r),'Invalid record identity')
            if r['record_key'] in by:
                prior={k:v for k,v in by[r['record_key']].items() if k not in ('record_hash','previous_hash')}
                _require(prior==r,'Conflicting immutable forecast/abstention')
                reused+=1;continue
            r['previous_hash']=previous;r['record_hash']=_sha(_json_bytes(r));previous=r['record_hash']
            additions.append(r);by[r['record_key']]=r
        # An empty finite queue is a successful explicit artifact, not a missing
        # file that breaks the outer stage checkpoint.
        if additions or not p.exists():
            # Atomic publication avoids a torn final JSON line on interruption.
            # The previous bytes remain an exact prefix; only new records follow.
            import tempfile
            tmp=None
            try:
                with tempfile.NamedTemporaryFile(dir=p.parent,prefix=p.name+'.pending-',delete=False) as out:
                    tmp=pathlib.Path(out.name);out.write(existing_bytes)
                    for r in additions:out.write(_json_bytes(r)+b'\n')
                    out.flush();os.fsync(out.fileno())
                os.replace(tmp,p)
                fd=os.open(p.parent,os.O_RDONLY)
                try:os.fsync(fd)
                finally:os.close(fd)
            finally:
                if tmp is not None and tmp.exists():tmp.unlink()
        return dict(appended=len(additions),reused=reused,total=len(old)+len(additions),head_sha256=previous,
                    immutability='application append-only; not WORM storage',new_fits=0)


class _FixturePredictor:
    classes_=np.array([0,1])
    def __init__(self,n,task):self.n_features_in_=n;self.task=task
    def predict(self,x):return np.full(len(x),3.0 if self.task=='margin' else 45.0)
    def predict_proba(self,x):return np.tile([.45,.55],(len(x),1))


def fixture_api(now='2030-01-03T00:00:00+00:00'):
    """Pure synthetic worker fixtures; zero fits and no real-data model loading."""
    now=_utc(now);past=now-pd.Timedelta(days=8);future=now+pd.Timedelta(days=2)
    rows=[];contracts=[];models={}
    for track in HORIZON_HOURS:
        for i,t in enumerate([past,future]):
            rows.append(dict(track=track,game_id=track+str(i),season=2026,week=i+1,kickoff=t,home_id=track+'A',away_id=track+'B',
                completed=i==0,home_points=24. if i==0 else np.nan,away_points=21. if i==0 else np.nan,
                home_fbs=1,away_fbs=1,win=1. if i==0 else np.nan,margin=3. if i==0 else np.nan,total=45. if i==0 else np.nan,
                x=1.,source_snapshot_at=(now-pd.Timedelta(hours=2)).isoformat(),feature_max_available_at=past+pd.Timedelta(hours=24)))
        for task in TASKS:
            cid=track+'_'+task
            c=dict(id=cid,track=track,task=task,format='fixture',fixture=True,features=['x'],model_pin={'sha256':'a'*64,'bytes':1},
                train_latest_release=(past-pd.Timedelta(days=5)).isoformat(),model_available_at=(now-pd.Timedelta(days=1)).isoformat(),
                role='synthetic_shadow_fixture',training_target_scope='NFL' if track=='nfl' else 'FBS versus FBS only',
                legacy_prior_opponent_context=track=='ncaaf',expected_parity_rows=1,reference_column='accepted')
            contracts.append(c);models[cid]=_FixturePredictor(1,task)
    frame=pd.DataFrame(rows)
    snapshot=dict(fixture=True,feature_observed_at=(now-pd.Timedelta(hours=2)).isoformat(),canonical_observed_at=(now-pd.Timedelta(hours=1)).isoformat(),
                  feature_sha256='b'*64,max_age_hours=24,parity_by_model={c['id']:'PASS' for c in contracts})
    return dict(frame=frame,canonical=frame.copy(),contracts=contracts,models=models,snapshot=snapshot,fixture_now=now.isoformat())


def prepare_serving(ctx):
    """Root-worker adapter; cache is fetched/hash-pinned by the existing runtime.

    The source contract is embedded in the PYZ. A current canonical frame is
    optional only for diagnosis: absence uses the explicitly stale frozen frame
    and cannot establish current readiness. This adapter never fetches data.
    """
    root=pathlib.Path(ctx.root)
    if ctx.fixture:
        d=fixture_api()
        parity=[dict(model_id=c['id'],status='PASS',n=1,fixture=True,new_fits=0,
                     method='explicit synthetic constant inference fixture; production parity tested separately') for c in d['contracts']]
        d['parity']=parity
        return d
    plan=json.loads((root/'source/prospective_model_assets.json').read_text())
    cache=root/'cache'
    # Verify the scientific input pins here too before loading any model.
    pin_by={a['name']:a for a in plan['assets']}
    for name in ['v057_qb_features.parquet','v060_evaluation_predictions.parquet']:
        p=cache/name;a=pin_by[name];raw=p.read_bytes()
        _require(len(raw)==a['bytes'] and _sha(raw)==a['sha256'], 'Serving input pin mismatch: '+name)
    frame=pd.read_parquet(cache/'v057_qb_features.parquet')
    reference=pd.read_parquet(cache/'v060_evaluation_predictions.parquet')
    contracts=plan['contracts'];models={};parity=[]
    for c in contracts:
        model=load_owned_model(cache/c['model_asset'],c)
        parity.append(verify_serving_parity(model,frame,reference,c));models[c['id']]=model
    source_vintages=pd.to_datetime(frame.source_snapshot_at,utc=True)
    _require(source_vintages.notna().all(),'Feature source vintage missing')
    observation=source_vintages.min().isoformat()
    snapshot=dict(feature_observed_at=observation,canonical_observed_at=observation,
                  feature_sha256=pin_by['v057_qb_features.parquet']['sha256'],max_age_hours=24,
                  parity_by_model={x['model_id']:x['status'] for x in parity},fixture=False,
                  canonical_inventory='frozen feature snapshot; no current canonical observation verified',
                  current_vintage_required='Fresh hash-pinned canonical and exact feature vintage, or full input-equivalence proof. Acquisition/job timestamps do not refresh features.')
    canonical=frame.copy()
    # Optional current canonical inventory is only used with an embedded immutable
    # pin and source observation. It does not refresh the frozen feature timestamp.
    cur=plan.get('canonical_asset')
    if cur:
        p=cache/cur['name'];raw=p.read_bytes()
        _require(len(raw)==cur['bytes'] and _sha(raw)==cur['sha256'],'Canonical serving pin mismatch')
        canonical=pd.read_parquet(p)
        snapshot['canonical_observed_at']=_utc(cur['observed_at']).isoformat()
        snapshot['canonical_inventory']='separately pinned canonical inventory; feature vintage unchanged'
        snapshot['canonical_sha256']=cur['sha256']
    return dict(frame=frame,canonical=canonical,contracts=contracts,models=models,snapshot=snapshot,parity=parity)
