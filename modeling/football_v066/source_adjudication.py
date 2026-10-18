"""Read-only clock and result diagnostics for independently captured CFBD drives.

A candidate is a derived research value, never an authoritative source repair.
This module does not return model inputs or mutate source rows.
"""
import copy
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

SCHEMA = 'football-cfbd-source-adjudication-v066'
METHOD = 'exact-clock-equation-with-neighbor-check-v1'
KNOWN_RESULTS = frozenset({
    'TD', 'FG', 'PUNT', 'DOWNS', 'INT', 'FUMBLE', 'MISSED FG', 'INT TD', 'SF',
    'FUMBLE TD', 'PUNT RETURN TD', 'PUNT TD', 'FUMBLE RETURN TD', 'MISSED FG TD',
    'DOWNS TD', 'END OF GAME TD', 'END OF HALF TD', 'KICKOFF',
    'POSSESSION (FOR OT DRIVES)', 'END OF GAME', 'END OF HALF', 'END OF QUARTER',
})


def _integer(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _clock(x):
    if not isinstance(x, dict):
        return None
    minute, second = x.get('minutes'), x.get('seconds')
    if not (_integer(minute) and _integer(second)):
        return None
    if not (0 <= minute <= 15 and 0 <= second < 60):
        return None
    total = minute * 60 + second
    return total if total <= 900 else None


def _json(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _sha(x):
    return hashlib.sha256(_json(x).encode()).hexdigest()


def _period(x):
    return _integer(x) and 1 <= x <= 4


def _identity(row):
    return (isinstance(row, dict) and _integer(row.get('gameId')) and row['gameId'] > 0
            and isinstance(row.get('id'), str) and re.fullmatch('[0-9]+', row['id']) is not None
            and _integer(row.get('driveNumber')) and row['driveNumber'] > 0)


def _instant(row, side):
    period = row.get(side + 'Period')
    clock = _clock(row.get(side + 'Time'))
    if not _period(period) or clock is None:
        return None
    if side == 'end' and (not _period(row.get('startPeriod')) or period < row['startPeriod']):
        return None
    return (period - 1) * 900 + (900 - clock)


def _neighbor_check(row, same_game, start, end):
    """Check only unique immediately adjacent drive numbers; never bridge gaps."""
    number = row['driveNumber']
    checks = []
    for side, step in [('previous', -1), ('next', 1)]:
        neighbors = [x for x in same_game if x.get('driveNumber') == number + step]
        if len(neighbors) != 1:
            checks.append({'side': side, 'status': 'unknown', 'reason': 'missing_or_duplicate_adjacent_drive_number'})
            continue
        neighbor = neighbors[0]
        if sum(x['id'] == neighbor['id'] for x in same_game) != 1:
            checks.append({'side': side, 'status': 'unknown', 'reason': 'duplicate_neighbor_drive_id'})
            continue
        at = _instant(neighbor, 'end' if side == 'previous' else 'start')
        if at is None:
            checks.append({'side': side, 'status': 'unknown', 'reason': 'invalid_neighbor_period_or_clock', 'drive_id': neighbor['id']})
            continue
        okay = at <= start if side == 'previous' else end <= at
        checks.append({'side': side, 'status': 'consistent' if okay else 'conflict',
                       'drive_id': neighbor['id'], 'neighbor_elapsed_game_seconds': at})
    return checks


def adjudicate_cfbd_drives(rows, *, source_sha256, source_observed_at):
    """Return JSON-safe diagnostics; no source correction or automatic insertion.

    End-period candidates are restricted to malformed regulation-start rows.
    Both boundary clocks and insufficient/corrupt chronology remain explicit.
    Duration is accepted only in the same bounded minute/second form as clocks;
    longer or unrecognized representations fail closed for inference.
    """
    if not isinstance(rows, list) or len(rows) > 50000:
        raise ValueError('Bounded list of at most 50000 CFBD rows required')
    if not isinstance(source_sha256, str) or re.fullmatch('[0-9a-f]{64}', source_sha256) is None:
        raise ValueError('Exact lowercase source SHA256 required')
    if not isinstance(source_observed_at, str):
        raise ValueError('Timezone-aware source observation required')
    try:
        timestamp = datetime.fromisoformat(source_observed_at.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Timezone-aware source observation required') from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError('Timezone-aware source observation required')
    before = _sha(rows)
    grouped = defaultdict(list)
    id_counts = Counter()
    for row in rows:
        if _identity(row):
            grouped[row['gameId']].append(row)
            id_counts[(row['gameId'], row['id'])] += 1
    periods, results, invalid_rows = [], [], []
    for ordinal, row in enumerate(rows):
        provenance = {'row': ordinal, 'row_sha256': _sha(row), 'source_sha256': source_sha256,
                      'source_observed_at': source_observed_at, 'source_publication_at': None}
        if not _identity(row):
            invalid_rows.append(dict(provenance, status='invalid_identity', reason='exact_game_drive_number_identity_required'))
            continue
        provenance.update(game_id=str(row['gameId']), drive_id=row['id'], drive_number=row['driveNumber'])
        result = row.get('driveResult')
        if not isinstance(result, str) or result not in KNOWN_RESULTS:
            results.append(dict(provenance, original_result=copy.deepcopy(result),
                                status='authoritative_result_evidence_required', mapped_result=None,
                                reason='unsupported_result_never_inferred_from_score_or_neighbor'))
        sp, ep = row.get('startPeriod'), row.get('endPeriod')
        malformed = not (_integer(sp) and _integer(ep)) or sp < 1 or ep < sp or ep < 1
        if not malformed:
            # Valid reported periods and overtime are outside this inference task.
            continue
        entry = dict(provenance, original_start_period=sp, original_end_period=ep,
                     candidate_end_period=None, method=METHOD, derived_not_authoritative=True,
                     automatic_serving_authorized=False, neighbor_checks=[])
        periods.append(entry)
        if not _period(sp):
            entry.update(status='unresolved', reason='invalid_or_overtime_start_period'); continue
        if not _integer(ep):
            entry.update(status='unresolved', reason='invalid_end_period_representation'); continue
        if id_counts[(row['gameId'], row['id'])] != 1 or sum(x['driveNumber'] == row['driveNumber'] for x in grouped[row['gameId']]) != 1:
            entry.update(status='unresolved', reason='duplicate_drive_identity_or_number'); continue
        start, end, elapsed = (_clock(row.get(k)) for k in ['startTime', 'endTime', 'elapsed'])
        entry.update(start_clock_seconds=start, end_clock_seconds=end, elapsed_seconds=elapsed)
        if None in (start, end, elapsed):
            entry.update(status='unresolved', reason='invalid_clock_or_elapsed'); continue
        numerator = elapsed - start + end
        if numerator % 900:
            entry.update(status='unresolved', reason='clock_equation_has_no_integer_period'); continue
        candidate = sp + numerator // 900
        if not sp <= candidate <= 4:
            entry.update(status='unresolved', reason='candidate_not_regulation_or_precedes_start'); continue
        if sp <= 2 < candidate:
            entry.update(status='unresolved', reason='drive_cannot_cross_halftime'); continue
        entry['candidate_end_period'] = candidate
        if start in (0, 900) or end in (0, 900):
            entry.update(status='boundary_ambiguous', reason='quarter_boundary_clock_not_uniquely_corroborated'); continue
        checks = _neighbor_check(row, grouped[row['gameId']], (sp - 1) * 900 + 900 - start,
                                 (candidate - 1) * 900 + 900 - end)
        entry['neighbor_checks'] = checks
        if any(x['status'] == 'conflict' for x in checks):
            entry.update(status='neighbor_conflict', reason='adjacent_drive_temporal_conflict')
        elif all(x['status'] == 'consistent' for x in checks):
            entry.update(status='derived_candidate_corroborated', reason='exact_clock_equation_and_both_adjacent_drives_consistent')
        else:
            entry.update(status='derived_candidate_uncorroborated', reason='exact_clock_equation_but_neighbor_evidence_incomplete')
    after = _sha(rows)
    if before != after:
        raise AssertionError('Source mutated')
    status_counts = dict(Counter(x['status'] for x in periods))
    reason_counts = dict(Counter(x['reason'] for x in periods))
    audit = {'schema': SCHEMA, 'input_rows': len(rows), 'source_sha256': source_sha256,
             'source_observed_at': source_observed_at, 'source_publication_at': None,
             'raw_rows_unchanged': True, 'canonical_raw_rows_sha256': before,
             'malformed_period_rows': len(periods), 'malformed_period_games': len({x['game_id'] for x in periods}),
             'period_status_counts': status_counts, 'period_reason_counts': reason_counts,
             'unsupported_result_rows': len(results), 'unsupported_result_games': len({x['game_id'] for x in results}),
             'unsupported_result_counts': dict(Counter(str(x['original_result']) for x in results)),
             'invalid_identity_rows': len(invalid_rows), 'model_feature_insertions': 0, 'new_model_fits': 0,
             'source_corrections': 0, 'semantic_equivalence_claimed': False,
             'automatic_serving_authorized': False,
             'scope': 'diagnostic of captured rows; canonical completion and FBS target eligibility remain separate gates',
             'method': METHOD}
    return {'audit': audit, 'period_candidates': periods, 'unsupported_results': results, 'invalid_rows': invalid_rows}


def fixture_inputs(include_edge_cases=False):
    """Three synthetic drives, with one malformed middle period; no fitting."""
    rows = []
    for number, start, end, elapsed, period in [(1, 600, 500, 100, 2), (2, 500, 400, 100, 0), (3, 400, 300, 100, 2)]:
        rows.append({'id': '1001' + str(number), 'gameId': 1001, 'driveNumber': number,
                     'driveResult': 'PUNT', 'startPeriod': 2, 'endPeriod': period,
                     'startTime': {'minutes': start // 60, 'seconds': start % 60},
                     'endTime': {'minutes': end // 60, 'seconds': end % 60},
                     'elapsed': {'minutes': elapsed // 60, 'seconds': elapsed % 60}})
    if include_edge_cases:
        unknown = copy.deepcopy(rows[0]); unknown.update(gameId=1002, id='10021', driveResult='Uncategorized')
        ambiguous = copy.deepcopy(rows[1]); ambiguous.update(gameId=1003, id='10032', endTime={'minutes': 0, 'seconds': 0}, elapsed={'minutes': 8, 'seconds': 20})
        rows.extend([unknown, ambiguous])
    return rows
