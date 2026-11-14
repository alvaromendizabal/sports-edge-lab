"""Chronological totals challenger on version-specific N094 owner comparisons. Standard library only."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import hashlib
import json
import math
import os
import tempfile

POLICIES = ((0.15, 0.35, 0.50), (1/3, 1/3, 1/3), (0.10, 0.20, 0.70))
ARMS = ('market', 'model', 'blend', 'equal', 'negative')

def clock(stamp):
    value = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Missing source timezone')
    return value

def save(path, value):
    with tempfile.NamedTemporaryFile(dir=path.parent, mode='w', delete=False) as out:
        json.dump(value, out, sort_keys=True, allow_nan=False, separators=(',', ':'))
        out.write('\n')
        out.flush()
        os.fsync(out.fileno())
    os.replace(out.name, path)

def compute(studies):
    fits, rows, withheld = [], [], []
    for study in studies:
        family, version, season = study['family'], study['model_version'], int(study['season'])
        cases = [r for r in study['evaluation_rows'] if all(isinstance(r.get(k), (float, int)) and math.isfinite(r[k]) for k in ('actual_total', 'point_total', 'total_market_line', 'week')) and r.get('label_available_at') and r.get('virtual_origin')]
        if len({r['game_id'] for r in cases}) != len(cases):
            raise ValueError('Duplicate registered game')
        for week in sorted({r['week'] for r in cases}):
            query = [r for r in cases if r['week'] == week]
            cut = min(clock(r['virtual_origin']) for r in query)
            prior = [r for r in cases if r['week'] < week and clock(r['label_available_at']) < cut]
            if len(prior) < 24 or len({r['week'] for r in prior}) < 3:
                withheld.append(dict(family=family, season=season, week=week, rows=len(query)))
                continue
            x = [r['point_total']-r['total_market_line'] for r in prior]
            y = [r['actual_total']-r['total_market_line'] for r in prior]
            weight = max(0., min(1., sum(a*b for a,b in zip(x,y)) / (10. + sum(a*a for a in x))))
            fits.append(dict(family=family, model_version=version, season=season, week=week, weight=weight, n=len(prior), origin=cut.isoformat(), latest_label=max(clock(r['label_available_at']) for r in prior).isoformat()))
            for r in query:
                m, d = r['total_market_line'], r['point_total']-r['total_market_line']
                estimates = (m, m+d, m+weight*d, m+0.5*d, m-weight*d)
                rows.append(dict(family=family, season=season, week=week, game_id=r['game_id'], model_version=version, weight=weight, actual=r['actual_total'], errors={a: v-r['actual_total'] for a,v in zip(ARMS, estimates)}))
    families = sorted({s['family'] for s in studies})
    seen = defaultdict(set)
    for r in rows:
        seen[(r['season'],r['game_id'])].add(r['family'])
    paired = [r for r in rows if len(seen[(r['season'],r['game_id'])])==len(families)]
    seasonal, weighted = [], []
    for fam in families:
        byseason = []
        for yr in (2024,2025,2026):
            chunk=[r for r in paired if r['family']==fam and r['season']==yr]
            if not chunk: continue
            mae={k:sum(abs(r['errors'][k]) for r in chunk)/len(chunk) for k in ARMS}
            byseason.append(mae)
            seasonal.append(dict(family=fam, season=yr, games=len(chunk), weeks=sorted({r['week'] for r in chunk}), mae=mae))
        if len(byseason)==3:
            for w in POLICIES:
                losses={k:sum(a*b[k] for a,b in zip(w,byseason)) for k in ARMS}
                weighted.append(dict(family=fam, policy_2024_25_26=w, mae=losses, market_minus_blend=losses['market']-losses['blend']))
    return dict(schema='nfl.n095.registered-market-anchor.v1', historical_quote_possession_verified=False, new_native_fits=0, statistical_weekly_estimates=len(fits), fits=fits, rows=paired, seasonal=seasonal, weighted=weighted, withheld=withheld, promotion=False)

def run(source_path, output_path):
    src=Path(source_path);out=Path(output_path)
    raw=src.read_bytes()
    result=compute(json.loads(raw))
    result['source_sha256']=hashlib.sha256(raw).hexdigest()
    save(out,result)
    return result['statistical_weekly_estimates']
