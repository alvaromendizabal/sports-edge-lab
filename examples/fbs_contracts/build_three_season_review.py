"""Project sealed three-season FBS evidence into permitted public display fields.

This creates no forecasts, fit receipts, provider observations or metric values.
The original V038 public snapshot remains byte-for-byte separate.
"""
from pathlib import Path
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import math
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = 'RETROSPECTIVE_DEVELOPMENT_TIMING_UNCERTIFIED'
PINS = {
    'COMPLETE_PREDICTIONS.json.gz': (6309092, 'e0829084fa546f1871f68452482f0de069a3132e016b257cd227a3e32b70be61'),
    'COMPLETE_SCIENTIFIC_RESULTS.json': (213641, '9a9e2779b9b650939a5ce12dd1ee0925f35f0b3c6380422239cddc3719b1dddd'),
    'RETAINED_INPUT_DATASET.json.gz': (1406697, '809261a967a25299ad45929c19237f2ddcffa5f35b8d4f8af74d927e88e5f75f'),
}
FAMILIES = {'fixed_equal_blend', 'logistic', 'linear', 'ridge', 'extra_trees', 'hist_gradient_boosting'}

def physical(path, expected=None):
    body = Path(path).read_bytes()
    identity = (len(body), hashlib.sha256(body).hexdigest())
    if expected is not None and identity != expected:
        raise ValueError('Physical source identity mismatch: ' + Path(path).name)
    return body, {'file': Path(path).name, 'bytes': identity[0], 'sha256': identity[1]}

def display_target(row):
    """Only derived display output; exclude weights, features and private state IDs."""
    value = row['prediction']
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Non-finite prediction')
    if row['target'] == 'winner' and not 0 <= value <= 1:
        raise ValueError('Probability outside unit interval')
    result = {'prediction': round(value, 4 if row['target'] == 'winner' else 2),
              'computed_at_utc': row['computed_at_utc']}
    for key in ('interval80', 'interval95'):
        if key in row:
            interval = row[key]
            if len(interval) != 2 or not all(math.isfinite(v) for v in interval) or interval[0] > interval[1]:
                raise ValueError('Invalid saved interval')
            result[key] = [round(v, 2) for v in interval]
    for key in ('distribution_status', 'calibration_status'):
        if key in row:
            result[key] = row[key]
    if row['target'] == 'margin':
        cover = row.get('spread_cover', {})
        if cover.get('probability') is not None:
            raise ValueError('A cover value needs a separately authenticated exact-line admission')
        result['cover_probability'] = None
        result['cover_status'] = cover.get('status', 'NO_AUTHENTICATED_CUTOFF_COMPATIBLE_HOME_SPREAD')
    return result

def build(source, seed, output, official):
    source, seed, output = Path(source), Path(seed), Path(output)
    bodies, identities = {}, []
    for name, pin in PINS.items():
        body, identity = physical(source / name, pin)
        bodies[name] = body
        identities.append(identity)
    seed_body, seed_identity = physical(seed, (69332265, '5183f89fa8087d556a982cbefa960352cdc8a4f681b95281f7a9f8965bf1ccab'))
    identities.append(seed_identity)
    del seed_body
    official_body, official_identity = physical(Path(official), (22685842, '93333d34a4f337cf436938717950173f8fd05f0b5d81eb8e58b85a33871c5ad0'))
    official_rows = {r['game_id']: r['latest_authenticated_dated_official_observation'] for r in json.loads(official_body)['games']}
    identities.append(official_identity)
    del official_body
    predictions = json.loads(gzip.decompress(bodies['COMPLETE_PREDICTIONS.json.gz']))
    scientific = json.loads(bodies['COMPLETE_SCIENTIFIC_RESULTS.json'])
    dataset = json.loads(gzip.decompress(bodies['RETAINED_INPUT_DATASET.json.gz']))
    if scientific['evidence_class'] != EVIDENCE or scientific['forecast_issued'] or scientific['historical_availability_proved']:
        raise ValueError('Unexpected scientific evidence class')
    with zipfile.ZipFile(seed) as archive:
        historical = json.loads(gzip.decompress(archive.read('games.json.gz')))
        outcomes = {str(r['game_id']): r for r in json.loads(gzip.decompress(archive.read('results.json.gz')))}
    current = json.loads((output / 'complete-season.json').read_text())
    current_rows = {r[0]: dict(zip(current['columns'], r)) for r in current['rows']}
    inputs = {r['game_id']: r for r in dataset['rows']}
    excluded = {r['game_id']: r for r in dataset['excluded_fixtures']}
    by_id = {}
    for row in historical:
        gid = str(row['game_id']); outcome = outcomes.get(gid)
        exact = not row['kickoff_tbd']
        h = int(outcome['home_points']) if outcome else None
        a = int(outcome['away_points']) if outcome else None
        game = {'id': gid, 'season': row['season'], 'away': row['away_team'], 'home': row['home_team'],
                'away_id': row['away_id'], 'home_id': row['home_id'], 'kickoff': row['kickoff_utc'] if exact else None,
                'reported_kickoff': row['kickoff_utc'], 'kickoff_exact': exact, 'week': row['week'],
                'phase': row['season_type'], 'population': 'HISTORICAL_IDENTIFIED_FIXTURE',
                'completed': outcome is not None, 'native_completed': row['completed'], 'away_score': a, 'home_score': h,
                'winner': row['home_team'] if outcome and h > a else row['away_team'] if outcome and a > h else None,
                'home_margin': h - a if outcome else None, 'total_points': h + a if outcome else None,
                'period': 'historical', 'schedule_join': 'EXACT_ID_ORDERED_TEAMS_AND_KICKOFF' if exact else 'EXACT_KICKOFF_UNRESOLVED',
                'fixture_source_capture_at': row['source_reference']['verified_at'],
                'source_row_sha256': row['source_row_sha256'],
                'replay_status': 'NOT_PROJECTED_FOR_THIS_SEASON',
                'provider_status': 'HISTORICAL_PROVIDER_MATRIX_NOT_PROJECTED',
                'cover_status': 'NO_AUTHENTICATED_CUTOFF_COMPATIBLE_HOME_SPREAD', 'models': {}}
        if gid in by_id:
            raise ValueError('Duplicate historical ID')
        by_id[gid] = game
    for gid, row in current_rows.items():
        if gid in by_id:
            raise ValueError('Duplicate cross-season ID')
        exact = gid not in excluded
        o = official_rows[gid]
        assert (o['season'], o['away_team'], o['home_team'], o['kickoff_utc']) == (2026, row['away'], row['home'], row['kickoff'])
        assert exact is (not o['kickoff_tbd'])
        assert o['home_id'] and o['away_id'] and o['home_id'] != o['away_id']
        by_id[gid] = {'id': gid, 'season': 2026, 'away': row['away'], 'home': row['home'],
                     'away_id': o['away_id'], 'home_id': o['home_id'],
                     'kickoff': row['kickoff'] if exact else None, 'reported_kickoff': row['kickoff'],
                     'kickoff_exact': exact, 'week': row['week'], 'phase': row['phase'],
                     'population': row['population'], 'completed': row['completed'],
                     'away_score': row['away_score'], 'home_score': row['home_score'], 'winner': row['winner'],
                     'home_margin': row['home_margin'], 'total_points': row['total_points'],
                     'period': row['period'], 'schedule_join': row['schedule_join'],
                     'fixture_source_capture_at': current['source_observed_at'],
                     'provider_status': 'SEPARATE_RETAINED_2026_REFERENCE_REPORT',
                     'cover_status': 'NO_AUTHENTICATED_CUTOFF_COMPATIBLE_HOME_SPREAD', 'models': {}}
    assert set(by_id) == set(inputs) | set(excluded)
    for gid, i in inputs.items():
        g = by_id[gid]
        assert (g['season'], g['away'], g['home'], g['away_id'], g['home_id'], g['kickoff']) == (i['season'], i['away_team'], i['home_team'], i['away_id'], i['home_id'], i['kickoff_utc'])
        assert i['cutoff_utc'] < g['kickoff']
        g['cutoff'] = i['cutoff_utc']
    seen = set()
    for row in predictions:
        gid = row['official_game_id']; g = by_id[gid]; i = inputs[gid]
        assert row['game_id'] == gid and row['season'] == g['season']
        assert row['family'] in FAMILIES and row['target'] in ('winner', 'margin', 'total')
        assert row['evidence_class'] == EVIDENCE and not row['forecast_issued'] and not row['historical_availability_proved']
        assert (row['home_id'], row['away_id'], row['kickoff_utc'], row['reconstructed_cutoff_utc']) == (g['home_id'], g['away_id'], g['kickoff'], i['cutoff_utc'])
        key = (gid, row['family'], row['target'])
        if key in seen:
            raise ValueError('Duplicate completed prediction identity')
        seen.add(key)
        g['models'].setdefault(row['family'], {})[row['target']] = display_target(row)
    for g in by_id.values():
        g['projection_status'] = 'RECONSTRUCTED_DEVELOPMENT' if g['models'] else 'EXACT_KICKOFF_UNRESOLVED' if not g['kickoff_exact'] else 'INSUFFICIENT_PRIOR_OUTCOMES'
        if g['models']:
            assert set(g['models']['fixed_equal_blend']) == {'winner', 'margin', 'total'}
    seasons = []
    for year in (2024, 2025, 2026):
        rows = [g for g in by_id.values() if g['season'] == year]
        seasons.append({'season': year, 'identified': len(rows), 'observed_complete': sum(g['completed'] for g in rows),
                        'predicted': sum(bool(g['models']) for g in rows), 'exact_kickoff_unresolved': sum(not g['kickoff_exact'] for g in rows),
                        'insufficient_history': sum(g['projection_status'] == 'INSUFFICIENT_PRIOR_OUTCOMES' for g in rows)})
    assert [(s['identified'], s['predicted']) for s in seasons] == [(920, 679), (934, 934), (888, 790)]
    report = {'schema': 'sports-edge-lab.fbs-three-season-explorer.v039', 'evidence_class': EVIDENCE,
              'forecast_issued': False, 'historical_availability_proved': False, 'promotion_allowed': False,
              'display_rounding': {'winner_probability_decimals': 4, 'point_decimals': 2, 'metrics_rescored_from_display': False},
              'sources': identities, 'retained_scientific_results_generated_at': scientific['generated_at'],
              'current_schedule_observed_at': current['source_observed_at'],
              'historical_source_capture_note': 'Fixture source capture is retained separately; it does not prove pregame possession or result publication time.',
              'new_fits': 0, 'new_provider_requests': 0, 'new_issues': 0,
              'seasons': seasons, 'identified_games': len(by_id), 'predicted_games': sum(bool(g['models']) for g in by_id.values()),
              'rows': sorted(by_id.values(), key=lambda g: (g['season'], g['kickoff'] or '9999', g['id']))}
    text = json.dumps(report, separators=(',', ':'), sort_keys=True)
    for forbidden in ('s3://', 'source_reference', 'feature_names', 'model_state_sha256', 'raw_probability', 'api_key', 'fit_identity_sha256'):
        assert forbidden not in text
    (output / 'three-season.json').write_text(text + '\n')
    (output / 'three-season-data.js').write_text('window.FBS_THREE_SEASONS=' + text + ';\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--source', required=True); parser.add_argument('--seed', required=True); parser.add_argument('--official', required=True)
    parser.add_argument('--output', default=str(ROOT / 'docs/fbs')); args = parser.parse_args()
    result = build(args.source, args.seed, args.output, args.official)
    print(json.dumps({k: result[k] for k in ('identified_games', 'predicted_games', 'seasons', 'new_fits', 'new_provider_requests', 'new_issues', 'sources')}))
