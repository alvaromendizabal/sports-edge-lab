"""Synthetic, CPU-only regression for the chronological total-line blend."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import n095_market_anchor as market_anchor


def study(year, family):
    rows = []
    for week in range(1, 6):
        for k in range(8):
            # Eight games per week put the first admissible cutoff exactly at 24.
            day = week * 3
            rows.append(dict(game_id=f'g-{year}-{week}-{k}', week=week,
                             actual_total=41.0, point_total=42.0, total_market_line=40.0,
                             virtual_origin=f'{year}-09-{day:02d}T01:00:00+00:00',
                             label_available_at=f'{year}-09-{day+1:02d}T01:00:00+00:00'))
    return dict(family=family, model_version=f'synthetic-{family}-{year}',
                season=year, evaluation_rows=rows)


def main():
    studies = [study(y, f) for y in (2024, 2025, 2026) for f in ('synthetic-A','synthetic-B')]
    with TemporaryDirectory() as tmp:
        inp = Path(tmp) / 'input.json'
        out = Path(tmp) / 'scores.json'
        inp.write_text(json.dumps(studies))
        assert market_anchor.run(inp, out) == 12
        before = out.read_bytes()
        result = json.loads(before)
        assert market_anchor.run(inp, out) == 12 and before == out.read_bytes()
        assert result['source_sha256'] == hashlib.sha256(inp.read_bytes()).hexdigest()
    assert len(result['rows']) == 96 and len(result['weighted']) == 6
    assert len(result['seasonal']) == 6 and len(result['withheld']) == 18
    assert all(f['n'] == (f['week']-1)*8 for f in result['fits'])
    assert all(market_anchor.clock(f['latest_label']) < market_anchor.clock(f['origin']) for f in result['fits'])
    early = next(f for f in result['fits'] if f['week']==4)
    assert abs(early['weight'] - 48/(10+96)) < 1e-12
    row = next(r for r in result['rows'] if r['week']==4)
    assert abs(row['errors']['blend'] - (-1+2*early['weight'])) < 1e-12
    assert row['errors']['negative'] < row['errors']['market'] < row['errors']['equal'] < row['errors']['model']
    # A label at the test-origin instant cannot influence the estimate.
    late = deepcopy(studies[0])
    late['evaluation_rows'][0]['label_available_at'] = late['evaluation_rows'][24]['virtual_origin']
    tested = market_anchor.compute([late])
    assert [f['week'] for f in tested['fits']] == [5]
    # A missing family-game cannot remain in another family's reported cohort.
    removed = deepcopy(studies)
    omitted = removed[1]['evaluation_rows'].pop(24)['game_id']
    assert all(row['game_id'] != omitted for row in market_anchor.compute(removed)['rows'])
    duplicate = deepcopy(studies[0])
    duplicate['evaluation_rows'].append(duplicate['evaluation_rows'][0])
    try:
        market_anchor.compute([duplicate])
    except ValueError as exc:
        assert 'Duplicate' in str(exc)
    else:
        raise AssertionError('duplicate case accepted')
    assert not result['historical_quote_possession_verified'] and not result['promotion']
    assert result['new_native_fits']==0
    print(json.dumps({'python_version':sys.version.split()[0], 'test_scope':'SYNTHETIC_FIXTURE',
                      'real_owner_fit_credit':0, 'data_source':'fully generated',
                      'synthetic_weekly_estimates':12, 'synthetic_paired_rows':96,
                      'source_bytes':len(before), 'status':'PASS'}, sort_keys=True))

if __name__ == '__main__':
    main()
