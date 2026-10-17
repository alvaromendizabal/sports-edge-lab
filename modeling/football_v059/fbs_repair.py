"""Bounded FBS scope audit and explicit-overtime ordering repair.

No provider access, model fitting, outcome imputation, or legacy-source edits.
The eight targeted games were previously rejected because NCAA overtime rows
have explicit period > 4 while start/end period fields are null. Preserve those
rows and exclude them before the unchanged V054 regulation validation gate.
"""
import collections
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

from common import GateError, require
from legacy_recovery import canonical_check, clean, ident, normalize_drives

TARGET_GAME_IDS = (
    '400869390', '401121942', '401309619', '401415029',
    '401415624', '401532629', '401628511', '401778314',
)


def verify_local_inputs(cache, pins):
    """Verify every declared local pin; never use a glob or mutable latest key."""
    cache = pathlib.Path(cache)
    seen = set()
    for pin in pins:
        name = pin['name']
        require(name == pathlib.Path(name).name and name not in seen,
                'SOURCE_STATE', 'Unsafe or duplicate repair input name')
        seen.add(name)
        path = cache / name
        require(path.is_file(), 'SOURCE_STATE', 'Missing pinned repair input: ' + name)
        require(path.stat().st_size == pin['bytes'], 'SOURCE_STATE', 'Repair input size mismatch: ' + name)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256'],
                'SOURCE_STATE', 'Repair input hash mismatch: ' + name)


def prepare_fbs_scope(canonical, frozen_features=None):
    """Return FBS-v-FBS targets and separately labeled FBS/FCS history context."""
    canonical_check(canonical)
    require({'home_fbs', 'away_fbs'} <= set(canonical), 'SCHEMA', 'Division flags missing')
    c = canonical[canonical.track.eq('ncaaf')].copy()
    require(c[['home_fbs', 'away_fbs']].isin([0, 1]).all().all(), 'DATA', 'Invalid division flags')
    require(((c.home_fbs == 1) | (c.away_fbs == 1)).all(), 'DATA', 'Standalone non-FBS game in scoped canonical data')
    target = c[(c.home_fbs == 1) & (c.away_fbs == 1)].copy()
    context = c[c.home_fbs != c.away_fbs].copy()
    context['data_role'] = 'fbs_history_context_only'
    context['prediction_eligible'] = False
    target['data_role'] = 'fbs_vs_fbs_prediction_population'
    target['prediction_eligible'] = True
    changes = []
    frozen_counts = None
    if frozen_features is not None:
        f = frozen_features[frozen_features.track.eq('ncaaf')].copy()
        require(not f.game_id.duplicated().any(), 'DATA', 'Duplicate frozen college games')
        require(set(c.game_id) == set(f.game_id), 'DATA', 'Canonical/frozen college population mismatch')
        cols = ['game_id', 'season', 'home_id', 'away_id', 'home_fbs', 'away_fbs', 'kickoff',
                'completed', 'home_points', 'away_points']
        m = c[cols].merge(f[cols], on='game_id', suffixes=('_canonical', '_frozen'), validate='one_to_one')
        for key in ['season', 'home_id', 'away_id', 'home_fbs', 'away_fbs', 'kickoff']:
            require(m[key + '_canonical'].eq(m[key + '_frozen']).all(), 'DATA', 'Frozen/canonical context conflict: ' + key)
        for r in m.to_dict('records'):
            old, new = bool(r['completed_frozen']), bool(r['completed_canonical'])
            require(not (old and not new), 'DATA', 'Completed result regressed')
            if old:
                require(r['home_points_canonical'] == r['home_points_frozen'] and
                        r['away_points_canonical'] == r['away_points_frozen'], 'DATA', 'Frozen completed score changed')
            if new and not old:
                changes.append(dict(game_id=r['game_id'], season=r['season_canonical'],
                                    home_points=r['home_points_canonical'], away_points=r['away_points_canonical'],
                                    fbs_vs_fbs=r['home_fbs_canonical'] == r['away_fbs_canonical'] == 1,
                                    action='use_canonical_final_for_future_state_updates_after_eligibility; preserve_frozen_features'))
        frozen_counts = dict(completed_total=int(f.completed.sum()),
                             completed_fbs_vs_fbs=int((f.completed & f.home_fbs.eq(1) & f.away_fbs.eq(1)).sum()))
    by_year = []
    for year, d in c.groupby('season'):
        both = d.home_fbs.eq(1) & d.away_fbs.eq(1)
        by_year.append(dict(season=int(year), completed_fbs_vs_fbs=int((d.completed & both).sum()),
                            completed_fbs_history_context=int((d.completed & ~both).sum()),
                            uncompleted_fbs_vs_fbs=int((~d.completed & both).sum()),
                            uncompleted_fbs_history_context=int((~d.completed & ~both).sum())))
    audit = dict(by_season=by_year, completed_fbs_vs_fbs=int(target.completed.sum()),
                 completed_fbs_history_context=int(context.completed.sum()),
                 standalone_fcs_games=0, context_prediction_rows=0,
                 frozen_counts=frozen_counts, newly_completed_since_frozen=changes,
                 frozen_features_modified=False, strict_point_in_time_verified=False,
                 source_publication_at=None)
    return target, context, clean(audit)


def exclude_explicit_overtime(raw):
    """Exclude only positive-play rows with explicit integral OT period.

    Null endpoint fields are acceptable for exclusion; contradictory or malformed
    non-null endpoints are not. Zero-play rows retain the legacy exclusion path.
    Unknown regulation outcomes are never inferred or dropped here.
    """
    require({'period', 'quarter', 'start_period', 'end_period', 'n_plays'} <= set(raw),
            'SCHEMA', 'Explicit NCAA period evidence missing')
    p = pd.to_numeric(raw.period, errors='coerce')
    n = pd.to_numeric(raw.n_plays, errors='coerce')
    ot = p.notna() & np.isfinite(p) & p.eq(p.round()) & p.between(5, 20) & n.gt(0)
    for name in ['quarter', 'start_period', 'end_period']:
        original = raw[name]
        z = pd.to_numeric(original, errors='coerce')
        invalid = original.notna() & (z.isna() | ~np.isfinite(z) | ~z.eq(z.round()) | ~z.between(5, 20))
        require(not (ot & invalid).any(), 'DATA', 'Explicit overtime contradicts ' + name)
    require(not (ot & (~np.isfinite(n) | ~n.eq(n.round()) | ~n.between(1, 40))).any(),
            'DATA', 'Invalid overtime offensive play count')
    return raw.loc[~ot].copy(), raw.loc[ot].copy()


def repair_targeted_games(canonical, queue, links, raw_by_season, sources,
                          target_game_ids=TARGET_GAME_IDS):
    """Return repaired secondary aggregates, evidence and scoped remaining queues.

    raw_by_season contains only pinned local DataFrames. sources is season->pin.
    links is the accepted V054 exact-identity receipt, not a name-only join.
    """
    target, context, scope = prepare_fbs_scope(canonical)
    target_ids = set(target.game_id)
    context_ids = set(context.game_id)
    require(len(queue) == len({r['game_id'] for r in queue}), 'DATA', 'Duplicate recovery queue')
    by_id = {r['game_id']: dict(r) for r in queue}
    require(set(by_id) <= target_ids | context_ids, 'DATA', 'Queue outside FBS scope')
    selected = tuple(target_game_ids)
    require(len(selected) == len(set(selected)), 'DATA', 'Duplicate targeted repair ID')
    require(set(selected) <= target_ids & set(by_id), 'DATA', 'Repair target is not an FBS-v-FBS gap')
    link_by_id = {r['game_id']: r for r in links}
    require(len(link_by_id) == len(links), 'DATA', 'Duplicate identity receipt')
    games = canonical.set_index('game_id')
    tables, excluded, decisions = [], [], []
    repaired = set()
    for gid in selected:
        row, g = by_id[gid], games.loc[gid]
        require(g.completed and row['recovery_reason'] == 'invalid_drive_period',
                'DATA', 'Repair target does not match registered rejection')
        require(gid in link_by_id, 'DATA', 'Missing exact identity receipt')
        link = link_by_id[gid]
        require((link['season'], link['home_id'], link['away_id']) == (g.season, g.home_id, g.away_id),
                'DATA', 'Identity receipt/canonical mismatch')
        require(pd.Timestamp(link['kickoff']) == pd.Timestamp(g.kickoff), 'DATA', 'Identity receipt kickoff mismatch')
        source = sources[int(g.season)]
        require((source['key'], source['sha256']) == (link['source']['key'], link['source']['sha256']),
                'SOURCE_STATE', 'Raw source differs from validated identity receipt')
        raw = raw_by_season[int(g.season)]
        selected_raw = raw.loc[raw.espn_game_id.map(ident).eq(gid)].copy()
        require(len(selected_raw) == link['raw_rows'], 'SOURCE_STATE', 'Raw targeted row count changed')
        try:
            regulation, overtime = exclude_explicit_overtime(selected_raw)
            require(len(overtime) > 0, 'DATA', 'Registered OT repair excluded no rows')
            # Use the validated identity receipt's conservative source time.
            table, bad, normalization, proof = normalize_drives(regulation, [link], canonical, link['source'])
            require(not bad and len(table) == 2, 'DATA', 'Unchanged regulation validation did not pass')
            table['repair_method'] = 'explicit_overtime_exclusion_before_regulation_validation'
            table['baseline_replacement_permitted'] = False
            tables.append(table)
            repaired.add(gid)
            for record in overtime.to_dict('records'):
                excluded.append(dict(game_id=gid, source_key=source['key'], source_sha256=source['sha256'],
                                     exclusion_reason='explicit_source_period_gt_4', raw=clean(record)))
            decisions.append(dict(game_id=gid, status='validated_secondary_regulation_repair',
                                  excluded_overtime_rows=len(overtime), accepted_team_rows=2,
                                  normalization=normalization, identity_receipt=link, proof=proof))
        except GateError as error:
            decisions.append(dict(game_id=gid, status='remains_quarantined', reason=str(error)))
    remaining = [dict(r, scope='fbs_vs_fbs_prediction_gap') for r in queue
                 if r['game_id'] in target_ids and r['game_id'] not in repaired]
    historical_context = [dict(r, scope='fbs_history_context_only', targeted_repair=False)
                          for r in queue if r['game_id'] in context_ids]
    features = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    audit = dict(scope=scope, selected_fbs_games=len(selected), repaired_fbs_games=len(repaired),
                 accepted_team_rows=len(features), excluded_overtime_rows=len(excluded),
                 original_fbs_gaps=sum(r['game_id'] in target_ids for r in queue),
                 remaining_fbs_gaps=len(remaining), historical_context_gaps=len(historical_context),
                 remaining_by_reason=dict(collections.Counter(r['recovery_reason'] for r in remaining)),
                 new_provider_calls=0, new_fits=0, fcs_recovery_attempts=0,
                 baseline_replacement_permitted=False, source_interchangeability_approved=False,
                 original_publication_at=None, strict_point_in_time_verified=False)
    return dict(features=features, excluded_overtime=clean(excluded), decisions=clean(decisions),
                remaining_fbs_queue=clean(remaining), historical_context_queue=clean(historical_context),
                audit=clean(audit))
