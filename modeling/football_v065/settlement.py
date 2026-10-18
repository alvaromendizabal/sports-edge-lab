"""V065 zero-fit settlement of previously issued, immutable shadow forecasts.

The minimum issuance cutoff is not the actual forecast lead. All scoring uses
original predictions and explicitly observed final labels. This module does not
fetch, fit, issue forecasts, infer unknown publication times, or select models.
Application append-only files are not WORM storage or independent timestamping.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import pathlib
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

PROTOCOL = 'football-settlement-v065'
MINIMUM_HOURS = {'nfl': 24, 'ncaaf': 1}
TASKS = ('win', 'margin', 'total')
RELEASE_HOURS = 24
MIN_GAMES = 100
MIN_BLOCKS = 8


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _hash(value):
    return _sha(_json(value))


def _is_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _utc(value):
    try:
        t = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Invalid timezone-aware timestamp') from exc
    _require(not pd.isna(t) and t.tzinfo is not None, 'Timestamp must be known and timezone-aware')
    return t.tz_convert('UTC')


def _id(value):
    _require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}', value)
             and value.lower() not in {'nan', 'none', 'null', 'inf'}, 'Malformed exact ID')
    return value


def _identity(record):
    track = record.get('track')
    _require(track in MINIMUM_HOURS, 'Unsupported forecast track')
    game, home, away = (_id(record.get(k)) for k in ('game_id', 'home_id', 'away_id'))
    _require(home != away, 'Home and away exact IDs cannot match')
    if not record.get('fixture'):
        if track == 'ncaaf':
            _require(all(x.isdigit() and int(x) > 0 for x in (game, home, away)), 'Malformed FBS numeric identity')
        else:
            _require(re.fullmatch(r'\d{4}_\d{2}_[A-Z]{2,4}_[A-Z]{2,4}', game) is not None,
                     'Malformed NFL game identity')
            _require(re.fullmatch('[A-Z]{2,4}', home) and re.fullmatch('[A-Z]{2,4}', away), 'Malformed NFL team identity')
            _require(game.endswith('_' + away + '_' + home), 'NFL game identity disagrees with teams')
    _utc(record.get('kickoff'))
    return track, game, home, away


def _forecast_key(record):
    values = [record['protocol'], record['track'], record['game_id'], record['task'],
              record['model_id'], record['decision_at'], record['status']]
    if record['status'] == 'abstained':
        values.append(record['issued_at'])
    return _hash(values)


def validate_forecast_chains(records, expected_head=None):
    """Validate one chain or a list of independent chains; preserve original rows.

    ``expected_head`` may be one hash, or an ordered list for multiple chains.
    Exact raw bytes/size are verified by the runtime adapter before JSON parsing.
    """
    _require(isinstance(records, (list, tuple)), 'Forecast records must be a list')
    chains = list(records) if records and isinstance(records[0], (list, tuple)) else [list(records)]
    expected = ([expected_head] if not isinstance(expected_head, (list, tuple)) else list(expected_head))
    if expected_head is not None:
        _require(len(expected) == len(chains), 'Expected chain head count mismatch')
    all_rows = []
    heads = []
    for index, chain in enumerate(chains):
        previous = None
        keys = set()
        for raw in chain:
            _require(isinstance(raw, dict), 'Forecast row must be an object')
            r = copy.deepcopy(raw)
            body = {k: v for k, v in r.items() if k != 'record_hash'}
            _require(r.get('previous_hash') == previous and _is_hash(r.get('record_hash'))
                     and _hash(body) == r['record_hash'], 'Forecast hash chain integrity mismatch')
            _identity(r)
            _require(r.get('task') in TASKS and isinstance(r.get('protocol'), str)
                     and r['protocol'].startswith('football-shadow-'), 'Unsupported forecast task/protocol')
            _id(r.get('model_id'))
            _require(_is_hash(r.get('model_sha256')), 'Model hash missing or malformed')
            _require(r.get('status') in {'issued', 'abstained'} and r.get('record_type') == 'shadow_forecast',
                     'Unsupported forecast status/type')
            _require(r.get('record_key') == _forecast_key(r), 'Forecast record identity mismatch')
            _require(r['record_key'] not in keys, 'Duplicate key within forecast chain')
            keys.add(r['record_key'])
            issue, kickoff, decision = (_utc(r[k]) for k in ('issued_at', 'kickoff', 'decision_at'))
            horizon = MINIMUM_HOURS[r['track']]
            _require(r.get('horizon_hours') == horizon and decision == kickoff-pd.Timedelta(hours=horizon),
                     'Forecast minimum cutoff contract mismatch')
            actual = (kickoff-issue).total_seconds()/3600
            _require(isinstance(r.get('actual_lead_hours'), (int, float))
                     and not isinstance(r['actual_lead_hours'], bool)
                     and math.isfinite(r['actual_lead_hours'])
                     and abs(actual-r['actual_lead_hours']) <= 1e-6, 'Actual lead does not match original issuance')
            _require(isinstance(r.get('reasons'), list), 'Forecast reasons missing')
            if r['status'] == 'issued':
                _require(issue <= decision and issue < kickoff, 'Late issued forecast cannot be settled')
                _require(not r['reasons'], 'Issued forecast contains failed eligibility reasons')
                prediction = r.get('prediction')
                _require(isinstance(prediction, (int, float)) and not isinstance(prediction, bool)
                         and math.isfinite(prediction), 'Invalid issued prediction')
                if r['task'] == 'win':
                    _require(0 < prediction < 1, 'Win probability outside open unit interval')
                for name in ('canonical_observed_at', 'feature_observed_at'):
                    clock = _utc(r.get(name))
                    _require(clock <= issue and clock < decision and issue-clock <= pd.Timedelta(hours=24),
                             'Issued input observation is unknown, late or stale')
                if r.get('current_efficiency_domain_required'):
                    clock = _utc(r.get('current_efficiency_observed_at'))
                    _require(clock <= issue and clock < decision and issue-clock <= pd.Timedelta(hours=24),
                             'Issued efficiency observation is unknown, late or stale')
            else:
                _require(r.get('prediction') is None and r['reasons'], 'Abstention must have reasons and no prediction')
            all_rows.append(r)
            previous = r['record_hash']
        heads.append(previous)
        if expected_head is not None:
            _require(previous == expected[index], 'Pinned forecast chain head mismatch')
    return all_rows, heads


def _observation(value, track):
    if isinstance(value, dict) and track in value:
        value = value[track]
    if isinstance(value, dict):
        return dict(observed_at=value.get('observed_at'), source_sha256=value.get('sha256', value.get('source_sha256')),
                    source_publication_at=value.get('source_publication_at'))
    return dict(observed_at=value, source_sha256=None, source_publication_at=None)


def _score(value):
    _require(not isinstance(value, (bool, np.bool_)) and isinstance(value, (int, float, np.number))
             and math.isfinite(value) and value == int(value) and 0 <= value <= 200, 'Invalid final score')
    return int(value)


def _primary_identity(r):
    # No version/protocol/deadline in this key: a version increment cannot reset
    # earliest qualifying forecast selection for an unchanged fitted model.
    return (r['track'], r['game_id'], r['model_sha256'], r['task'])


def _select_earliest(rows):
    selected = {}
    copies = 0
    excluded_later = 0
    model_hashes = {}
    seen_hashes = set()
    for r in sorted(rows, key=lambda x: (_utc(x['issued_at']), x['record_hash'])):
        key = (r['model_id'], r['task'])
        if key in model_hashes:
            _require(model_hashes[key] == r['model_sha256'], 'Model identity reused with conflicting model hash')
        model_hashes[key] = r['model_sha256']
        if r['record_hash'] in seen_hashes:
            copies += 1
            continue
        seen_hashes.add(r['record_hash'])
        if r['status'] != 'issued':
            continue
        key = _primary_identity(r)
        if key not in selected:
            selected[key] = r
        else:
            old = selected[key]
            _require(_identity(old) == _identity(r) and _utc(old['kickoff']) == _utc(r['kickoff']),
                     'Conflicting issued game identity across ledgers')
            if _utc(old['issued_at']) == _utc(r['issued_at']):
                _require(old['prediction'] == r['prediction'], 'Conflicting simultaneous forecast predictions')
            excluded_later += 1
    return selected, copies, excluded_later


def _label_for(record, rows, observed_at, as_of):
    """Choose only an unambiguous latest visible source version; no score guessing."""
    possible = [dict(r) for r in rows if r.get('track') == record['track']
                and str(r.get('game_id')) == record['game_id']]
    if not possible:
        return None, 'missing_exact_game_label'
    versions = []
    for row in possible:
        if any(str(row.get(k)) != record[k] for k in ('home_id', 'away_id')):
            return None, 'label_team_identity_mismatch'
        try:
            kickoff = _utc(row.get('kickoff'))
        except ValueError:
            return None, 'label_kickoff_unknown'
        if kickoff != _utc(record['kickoff']):
            return None, 'label_kickoff_changed'
        if row.get('season') != record.get('season'):
            return None, 'label_season_mismatch'
        obs = _observation(observed_at, record['track'])
        if row.get('source_observed_at') is not None:
            obs['observed_at'] = row['source_observed_at']
        if row.get('source_sha256') is not None:
            obs['source_sha256'] = row['source_sha256']
        if row.get('source_publication_at') is not None and not pd.isna(row['source_publication_at']):
            obs['source_publication_at'] = row['source_publication_at']
        try:
            clock = _utc(obs['observed_at'])
        except ValueError:
            return None, 'label_observation_unknown'
        if clock > as_of:
            continue
        versions.append((clock, row, obs))
    if not versions:
        return None, 'label_observed_after_as_of'
    latest = max(x[0] for x in versions)
    choices = [x for x in versions if x[0] == latest]
    # Different scores/statuses in the same source observation are ambiguous.
    signatures = set()
    for _, row, _ in choices:
        fields = [str(row.get(k)) for k in ('completed', 'home_points', 'away_points', 'status', 'week', 'season')]
        signatures.add(tuple(fields))
    _require(len(signatures) == 1, 'Conflicting label duplicates at identical observation')
    clock, row, obs = choices[0]
    if not isinstance(row.get('completed'), (bool, np.bool_)) or not bool(row['completed']):
        return None, 'official_final_not_observed'
    if row.get('status') is not None and str(row['status']).lower() in {'cancelled', 'canceled', 'postponed', 'suspended', 'in_progress', 'in progress'}:
        return None, 'nonfinal_or_changed_game_status'
    release = _utc(record['kickoff']) + pd.Timedelta(hours=RELEASE_HOURS)
    if as_of < release:
        return None, 'assumed_label_release_not_reached'
    if clock < release:
        return None, 'final_source_observed_before_assumed_release'
    publication = obs['source_publication_at']
    if publication is not None:
        try:
            pub = _utc(publication)
        except ValueError:
            return None, 'label_publication_invalid'
        if pub > clock:
            return None, 'label_publication_after_observation'
        publication = pub.isoformat()
    if not _is_hash(obs['source_sha256']):
        return None, 'final_source_hash_missing_or_invalid'
    try:
        home, away = _score(row.get('home_points')), _score(row.get('away_points'))
    except ValueError:
        return None, 'invalid_final_score'
    if record['track'] == 'ncaaf' and not (row.get('home_fbs') == 1 and row.get('away_fbs') == 1):
        return None, 'non_FBS_label_scope'
    season = row.get('season', record.get('season'))
    week = row.get('week')
    block = None
    if isinstance(season, (int, float, np.number)) and isinstance(week, (int, float, np.number)):
        if math.isfinite(season) and math.isfinite(week) and int(season) == season and int(week) == week and 1 <= week <= 30:
            block = f'{int(season)}-{int(week):02}'
    return dict(home_points=home, away_points=away, observed_at=clock.isoformat(),
                source_sha256=obs['source_sha256'], source_publication_at=publication,
                label_release_at=release.isoformat(), season_week_block=block), None


def _auc(y, p):
    n1 = int(np.sum(y == 1)); n0 = len(y)-n1
    if not n1 or not n0:
        return None
    ranks = pd.Series(p).rank(method='average').to_numpy()
    return float((np.sum(ranks[y == 1])-n1*(n1+1)/2)/(n1*n0))


def score_settlements(rows):
    """Descriptive original-prediction losses, never model selection or ROI."""
    groups = defaultdict(list)
    for r in rows:
        if r['status'] == 'settled':
            groups[(r['track'], r['model_id'], r['task'])].append(r)
    scores = []
    for (track, model, task), group in sorted(groups.items()):
        _require(len({r['game_id'] for r in group}) == len(group), 'Duplicate game in settlement score cohort')
        y = np.asarray([r['target'] for r in group], dtype=float)
        p = np.asarray([r['prediction'] for r in group], dtype=float)
        error = p-y
        if task == 'win':
            losses = -(y*np.log(p)+(1-y)*np.log1p(-p))
            metrics = dict(log_loss=float(losses.mean()), Brier=float(np.mean(error**2)),
                           probability_bias=float(error.mean()), AUC=_auc(y, p))
            calibration = []
            indices = np.minimum((p*10).astype(int), 9)
            for i in range(10):
                mask = indices == i; n = int(mask.sum())
                calibration.append(dict(bin_lower=i/10, bin_upper=(i+1)/10, count=n,
                                        mean_prediction=float(p[mask].mean()) if n else None,
                                        observed_frequency=float(y[mask].mean()) if n else None))
            metrics['calibration'] = calibration
        else:
            losses = np.abs(error)
            metrics = dict(MAE=float(losses.mean()), RMSE=float(np.sqrt(np.mean(error**2))),
                           median_absolute_error=float(np.median(losses)),
                           p90_absolute_error=float(np.quantile(losses, .9)), signed_bias=float(error.mean()))
        blocks = [r['season_week_block'] for r in group]
        block_count = len(set(b for b in blocks if b is not None))
        eligible = len(group) >= MIN_GAMES and block_count >= MIN_BLOCKS and all(b is not None for b in blocks)
        interval = None
        reason = 'insufficient_games_or_season_week_blocks'
        if eligible:
            unique = sorted(set(blocks)); arrays = [losses[np.asarray(blocks) == b] for b in unique]
            rng = np.random.default_rng(6501)
            boot = [float(np.concatenate([arrays[i] for i in rng.integers(0, len(arrays), len(arrays))]).mean())
                    for _ in range(1000)]
            interval = [float(x) for x in np.quantile(boot, [.025, .975])]
            reason = None
        scores.append(dict(track=track, model_id=model, task=task, n=len(group), metrics=metrics,
                           season_week_blocks=block_count, actual_lead_hours_min=min(r['actual_lead_hours'] for r in group),
                           actual_lead_hours_max=max(r['actual_lead_hours'] for r in group),
                           uncertainty=dict(available=eligible, reason=reason, primary_loss_interval=interval,
                                            method='descriptive_season_week_block_percentile_bootstrap_1000' if eligible else None,
                                            confirmatory=False), model_promoted=False))
    return scores


def settle_records(records, games, observed_at, as_of, expected_head=None):
    """Pure validation/selection/label join. Returns candidate evidence, no writes."""
    now = _utc(as_of)
    rows, heads = validate_forecast_chains(records, expected_head)
    selected, copies, later = _select_earliest(rows)
    game_rows = games.to_dict('records') if isinstance(games, pd.DataFrame) else list(games)
    _require(all(isinstance(x, dict) for x in game_rows), 'Labels must be objects')
    settlements, pending = [], []
    for key, record in sorted(selected.items()):
        _require(_utc(record['issued_at']) <= now, 'Forecast was issued after evaluation as_of')
        label, reason = _label_for(record, game_rows, observed_at, now)
        base = dict(protocol=PROTOCOL, record_type='shadow_settlement',
                    forecast_record_hash=record['record_hash'], forecast_record_key=record['record_key'],
                    forecast_protocol=record['protocol'], track=record['track'], game_id=record['game_id'],
                    home_id=record['home_id'], away_id=record['away_id'], kickoff=record['kickoff'],
                    model_id=record['model_id'], model_sha256=record['model_sha256'], task=record['task'],
                    prediction=record['prediction'], issued_at=record['issued_at'], decision_at=record['decision_at'],
                    actual_lead_hours=record['actual_lead_hours'], minimum_issue_lead_hours=record['horizon_hours'],
                    fixture=record.get('fixture', False), primary_identity_sha256=_hash(list(key)))
        if reason is not None:
            pending.append(dict(base, status='pending', reason=reason))
            continue
        home, away = label['home_points'], label['away_points']
        target = home-away if record['task'] == 'margin' else home+away if record['task'] == 'total' else None if home == away else int(home > away)
        status = 'excluded_tie' if record['task'] == 'win' and home == away else 'settled'
        semantic = dict(track=record['track'], game_id=record['game_id'], home_id=record['home_id'],
                        away_id=record['away_id'], kickoff=_utc(record['kickoff']).isoformat(),
                        home_points=home, away_points=away)
        settlements.append(dict(base, status=status, target=target, home_points=home, away_points=away,
                                label_observed_at=label['observed_at'], label_release_at=label['label_release_at'],
                                label_source_sha256=label['source_sha256'], source_publication_at=label['source_publication_at'],
                                label_release_assumption_hours=RELEASE_HOURS,
                                season_week_block=label['season_week_block'], label_fingerprint=_hash(semantic)))
    unique_rows = {r['record_hash']: r for r in rows}
    tracks = {}
    for track in MINIMUM_HOURS:
        incoming = [r for r in unique_rows.values() if r['track'] == track]
        chosen = [r for r in selected.values() if r['track'] == track]
        ready = [r for r in settlements if r['track'] == track]
        pending_track = [r for r in pending if r['track'] == track]
        tracks[track] = dict(schedule_games=len({r['game_id'] for r in incoming}), input_records=len(incoming),
                            issued_records=len(chosen), issued_games=len({r['game_id'] for r in chosen}),
                            abstained_records=sum(r['status'] == 'abstained' for r in incoming),
                            matured_records=len(ready), matured_games=len({r['game_id'] for r in ready}),
                            scored_records=sum(r['status'] == 'settled' for r in ready),
                            excluded_tie_records=sum(r['status'] == 'excluded_tie' for r in ready),
                            pending_records=len(pending_track), pending_games=len({r['game_id'] for r in pending_track}))
    audit = dict(protocol=PROTOCOL, as_of=now.isoformat(), status='SETTLEMENT_CHECK_COMPLETE',
                 predecessor_heads=heads, original_records=len(rows), unique_original_records=len(unique_rows),
                 duplicate_chain_records_reused=copies, later_issued_records_not_primary=later,
                 selected_forecasts=len(selected), matured_records=len(settlements),
                 scored_records=sum(x['status'] == 'settled' for x in settlements), pending_records=len(pending),
                 abstention_records=sum(r['status'] == 'abstained' for r in unique_rows.values()),
                 pending_reasons=dict(Counter(r['reason'] for r in pending)), tracks=tracks,
                 scorecards=score_settlements(settlements),
                 metrics_available=any(x['status'] == 'settled' for x in settlements),
                 minimum_games_for_aggregate_uncertainty=MIN_GAMES, minimum_season_week_blocks=MIN_BLOCKS,
                 label_release_assumption_hours=RELEASE_HOURS, model_promotions=0, new_real_fits=0,
                 new_live_forecasts=0, provider_calls=0, betting_performance_verified=False,
                 prospective_quality_established=False,
                 primary_selection='earliest qualifying issuance across supplied ledgers for exact game/task/model',
                 scope='Only the supplied, verified ledger history; not an unverified account-wide ledger inventory',
                 horizon_semantics='minimum issuance cutoff and actual issue-to-kickoff lead are distinct',
                 source_publication_at=None)
    return dict(audit=audit, settlements=settlements, pending=pending,
                forecast_selection=[dict(primary_identity=list(k), forecast_record_hash=r['record_hash'],
                                         issued_at=r['issued_at'], actual_lead_hours=r['actual_lead_hours'])
                                    for k, r in sorted(selected.items())])


def _atomic_bytes(path, raw):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.is_symlink(), 'Refuse symlinked settlement output')
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name+'.pending-', delete=False) as f:
            temp = pathlib.Path(f.name); f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def _validate_settlement_chain(raw):
    _require(not raw or raw.endswith(b'\n'), 'Incomplete settlement ledger')
    rows = []; previous = None; latest = {}; hashes = set()
    for line in raw.decode().splitlines():
        row = json.loads(line)
        _require(isinstance(row, dict), 'Settlement row must be an object')
        body = {k: v for k, v in row.items() if k != 'record_hash'}
        _require(row.get('protocol') == PROTOCOL and row.get('record_type') == 'shadow_settlement'
                 and row.get('previous_hash') == previous and _hash(body) == row.get('record_hash'),
                 'Settlement hash chain integrity mismatch')
        _require(row['record_hash'] not in hashes, 'Duplicate settlement record hash')
        identity = row['primary_identity_sha256']; prior = latest.get(identity)
        _require(row['revision'] == (prior['revision']+1 if prior else 1)
                 and row['supersedes'] == (prior['record_hash'] if prior else None), 'Settlement revision chain mismatch')
        if prior:
            _require(row['forecast_record_hash'] == prior['forecast_record_hash'], 'Settlement revised original forecast')
            _require(_utc(row['label_observed_at']) > _utc(prior['label_observed_at']), 'Settlement correction observation not newer')
        latest[identity] = row; hashes.add(row['record_hash']); previous = row['record_hash']; rows.append(row)
    return rows, latest, previous


def append_settlements(path, candidates):
    """Atomic locked append; unchanged finals reuse, newer score corrections supersede."""
    import fcntl
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.is_symlink(), 'Refuse symlinked settlement ledger')
    with open(str(path)+'.lock', 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = path.read_bytes() if path.exists() else b''
        rows, latest, head = _validate_settlement_chain(old)
        additions = []; reused = 0
        for candidate in candidates:
            r = copy.deepcopy(candidate)
            _require(not any(k in r for k in ('record_hash', 'previous_hash', 'revision', 'supersedes')),
                     'Candidate contains mutable chain fields')
            _require(r.get('protocol') == PROTOCOL and r.get('record_type') == 'shadow_settlement'
                     and r.get('status') in {'settled', 'excluded_tie'}, 'Invalid settlement candidate')
            identity = r['primary_identity_sha256']; prior = latest.get(identity)
            if prior:
                _require(prior['forecast_record_hash'] == r['forecast_record_hash'], 'Cannot replace original primary forecast')
                if prior['label_fingerprint'] == r['label_fingerprint']:
                    for name in ('target', 'prediction', 'status', 'home_points', 'away_points'):
                        _require(prior[name] == r[name], 'Conflicting settlement under identical label fingerprint')
                    reused += 1
                    continue
                _require(_utc(r['label_observed_at']) > _utc(prior['label_observed_at']),
                         'Score correction needs a strictly newer source observation')
            r.update(revision=prior['revision']+1 if prior else 1,
                     supersedes=prior['record_hash'] if prior else None, previous_hash=head)
            r['record_hash'] = _hash(r); head = r['record_hash']; additions.append(r); latest[identity] = r
        if additions or not path.exists():
            _atomic_bytes(path, old+b''.join(_json(r)+b'\n' for r in additions))
        return dict(appended=len(additions), reused=reused, total=len(rows)+len(additions),
                    active=len(latest), head_sha256=head, bytes=path.stat().st_size,
                    sha256=_sha(path.read_bytes()), immutability='application append-only; not WORM storage')


def _load_pinned_ledger(path, pin):
    path = pathlib.Path(path)
    _require(path.is_file() and not path.is_symlink(), 'Predecessor ledger missing or symlinked')
    _require(isinstance(pin, dict) and type(pin.get('bytes')) is int and pin['bytes'] >= 0
             and _is_hash(pin.get('sha256')) and 'head_sha256' in pin, 'Predecessor pin incomplete')
    raw = path.read_bytes()
    _require(len(raw) == pin['bytes'] and _sha(raw) == pin['sha256'], 'Predecessor ledger bytes/hash mismatch')
    _require(not raw or raw.endswith(b'\n'), 'Incomplete predecessor ledger')
    rows = [json.loads(x) for x in raw.decode().splitlines()]
    _, heads = validate_forecast_chains(rows, pin['head_sha256'])
    _require(heads == [pin['head_sha256']], 'Pinned forecast chain head mismatch')
    return rows


def build_settlement(ctx, prior_ledger_path, current_games_path, observation_by_track, *, fixture_pin=None):
    """Runtime adapter; requires frozen ``config['settlement_predecessor']`` pin.

    Results/checkpoints are owned by this module. Root remains responsible for
    its outer four-stage progress record and return archive. Production time is
    sampled once and frozen in a synced pending batch before any ledger append.
    """
    root = pathlib.Path(ctx.root)
    files = [root/n for n in ('settlement_audit.json', 'settlement_ledger.jsonl', 'settlement_pending.json', 'settlement_batch.json')]
    _require(fixture_pin is None or ctx.fixture, 'Production predecessor pin cannot be overridden')
    pin = fixture_pin if fixture_pin is not None else ctx.config.get('settlement_predecessor')
    rows = _load_pinned_ledger(prior_ledger_path, pin)
    _require(all(r.get('fixture') is ctx.fixture for r in rows), 'Fixture and production predecessor scope cannot mix')
    games_path = pathlib.Path(current_games_path)
    _require(games_path.is_file() and not games_path.is_symlink(), 'Current game input missing or symlinked')
    games_hash = _sha(games_path.read_bytes())
    observations_hash = _hash(observation_by_track)
    fingerprint = dict(prior_sha256=pin['sha256'], prior_bytes=pin['bytes'], prior_head=pin['head_sha256'],
                       current_games_sha256=games_hash, observations_sha256=observations_hash)
    saved = ctx.cp.lookup('settlement_outputs')
    if saved is not None:
        _require(saved['inputs'] == fingerprint, 'Settlement checkpoint inputs changed')
        return json.loads((root/'settlement_audit.json').read_text())
    pending_cp = ctx.cp.lookup('pending_settlement_batch')
    if pending_cp is None:
        _require(not (root/'settlement_ledger.jsonl').exists(), 'Settlement ledger exists without durable pending batch')
        games = pd.read_parquet(games_path)
        as_of = ctx.args.get('settlement_fixture_as_of') if ctx.fixture else None
        if as_of is None:
            as_of = datetime.now(timezone.utc).isoformat()
        result = settle_records(rows, games, observation_by_track, as_of, pin['head_sha256'])
        batch = dict(inputs=fingerprint, result=result)
        _atomic_bytes(root/'settlement_batch.json', _json(batch)+b'\n')
        ctx.cp.commit('pending_settlement_batch', [root/'settlement_batch.json'], dict(inputs=fingerprint))
    else:
        _require(pending_cp['inputs'] == fingerprint, 'Pending settlement inputs changed')
    batch = json.loads((root/'settlement_batch.json').read_text())
    _require(batch['inputs'] == fingerprint, 'Durable pending settlement fingerprint changed')
    ctx.sync([root/'settlement_batch.json', root/'checkpoints/pending_settlement_batch.json'])
    result = batch['result']
    appended = append_settlements(root/'settlement_ledger.jsonl', result['settlements'])
    if ctx.args.get('inject_failure') == 'SETTLED':
        raise RuntimeError('Intentional crash after settlement append before completion checkpoint')
    audit = dict(result['audit'], settlement_ledger=appended, inputs=fingerprint,
                 predecessor_bytes_preserved=True, forecast_bytes_not_rewritten=True)
    _atomic_bytes(root/'settlement_audit.json', _json(audit)+b'\n')
    _atomic_bytes(root/'settlement_pending.json', _json(dict(protocol=PROTOCOL, as_of=audit['as_of'],
                                                         records=result['pending'], forecast_selection=result['forecast_selection']))+b'\n')
    ctx.cp.commit('settlement_outputs', files, dict(inputs=fingerprint))
    ctx.sync(files+[root/'checkpoints/settlement_outputs.json'])
    return audit


def fixture_inputs():
    """Zero-fit synthetic ledger: one mature and one pending NFL game, three heads each."""
    as_of = _utc('2030-01-10T00:00:00Z')
    rows = []; games = []; previous = None
    for i, kickoff in enumerate([as_of-pd.Timedelta(days=2), as_of+pd.Timedelta(days=2)]):
        issued = kickoff-pd.Timedelta(hours=48) if i == 0 else as_of-pd.Timedelta(hours=1)
        game_id = 'nfl_fixture_' + str(i)
        for task in TASKS:
            r = dict(protocol='football-shadow-v064', record_type='shadow_forecast',
                     track='nfl', game_id=game_id, season=2030, home_id='AAA', away_id='BBB',
                     task=task, model_id='fixture_nfl_'+task, model_sha256=_sha(task.encode()),
                     kickoff=kickoff.isoformat(), issued_at=issued.isoformat(),
                     decision_at=(kickoff-pd.Timedelta(hours=24)).isoformat(), horizon_hours=24,
                     actual_lead_hours=(kickoff-issued).total_seconds()/3600,
                     canonical_observed_at=(issued-pd.Timedelta(hours=1)).isoformat(),
                     feature_observed_at=(issued-pd.Timedelta(hours=1)).isoformat(),
                     current_efficiency_domain_required=False, status='issued', reasons=[],
                     prediction=.6 if task=='win' else 3.0 if task=='margin' else 45.0, fixture=True)
            r['record_key'] = _forecast_key(r); r['previous_hash'] = previous
            r['record_hash'] = _hash(r); previous = r['record_hash']; rows.append(r)
        games.append(dict(track='nfl', game_id=game_id, home_id='AAA', away_id='BBB', season=2030,
                          week=1+i, kickoff=kickoff.isoformat(), completed=i==0, home_points=24. if i==0 else None,
                          away_points=20. if i==0 else None, home_fbs=1, away_fbs=1))
    obs = {'nfl': dict(observed_at=(as_of-pd.Timedelta(hours=1)).isoformat(), sha256='c'*64, source_publication_at=None)}
    return rows, pd.DataFrame(games), obs, as_of.isoformat()
