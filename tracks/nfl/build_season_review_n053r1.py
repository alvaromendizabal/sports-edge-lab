"""Validate and render an evidence-complete schedule without filling absent values."""
import argparse,base64,datetime,gzip,json,math,pathlib,re

HERE=pathlib.Path(__file__).resolve().parent
SCHEMA='nfl.public.n052-full-season-n053r1-prepared.v1'
PROVIDERS={'DraftKings','Kalshi','Polymarket'}
TARGETS={'win','margin','total'}
RETIRED=re.compile(r'\b(?:bet|bets|betting|wager|wagers|wagering|gambling|stake|stakes|staking|profit|profits|profitable|EV)\b',re.I)

def instant(s):
    t=datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('clock timezone')
    return t

def validate(data):
    if data['schema']!=SCHEMA:raise ValueError('schema')
    games=data['games'];index={g['game_id']:g for g in games}
    if len(games)!=272 or len(index)!=272 or sum(g['completed'] for g in games)!=122:raise ValueError('complete season closure')
    if sum(not g['completed'] for g in games)!=150:raise ValueError('future season closure')
    if sum(g['completed'] and g['actual']['home_score']==g['actual']['away_score'] for g in games)!=1:raise ValueError('tie closure')
    for g in games:
        if g['season']!=2026 or g['completed']!=(g['actual'] is not None):raise ValueError('schedule status')
        if g['completed'] and (g['actual']['home_margin']!=g['actual']['home_score']-g['actual']['away_score'] or g['actual']['total']!=g['actual']['home_score']+g['actual']['away_score']):raise ValueError('actual score closure')
    recent=[index[x] for x in data['recent_final_ids']]
    if len(recent)!=2 or {frozenset([g['away'],g['home']]) for g in recent}!={frozenset(['JAX','BAL']),frozenset(['CHI','SEA'])} or not all(g['completed'] for g in recent):raise ValueError('recent finals must remain visible')
    lanes={l['id']:l for l in data['lanes']}
    if len(lanes)!=len(data['lanes']) or data['default_lane_id'] not in lanes:raise ValueError('lane identities')
    model_keys={(r['game_id'],r['lane_id'],r['target']) for r in data['model_rows']}
    expected_model={(g,l,t) for g in index for l in lanes for t in TARGETS}
    if model_keys!=expected_model or len(data['model_rows'])!=len(expected_model):raise ValueError('model complete grid')
    horizons=set(data['provider_horizons'])
    if not {'T1','T2','LATEST_PREGAME','LATEST_OBSERVED','RETAINED_OBSERVED'}.issubset(horizons) or len(horizons)!=len(data['provider_horizons']) or data['default_provider_horizon'] not in horizons:raise ValueError('provider horizon identities')
    provider_keys={(r['game_id'],r['provider'],r['target'],r['horizon']) for r in data['provider_rows']}
    expected_provider={(g,p,t,h) for g in index for p in PROVIDERS for t in TARGETS for h in horizons}
    if provider_keys!=expected_provider or len(data['provider_rows'])!=len(expected_provider):raise ValueError('provider complete grid')
    for kind,rows in [('model',data['model_rows']),('provider',data['provider_rows'])]:
        for row in rows:
            if type(row['available']) is not bool or type(row['eligible']) is not bool:raise ValueError('availability type')
            if not isinstance(row['reason'],str) or len(row['reason'].strip())<15 or row['reason'].strip().lower() in {'unknown','unavailable','missing','no data'}:raise ValueError('specific evidence reason')
            if not row['available'] and row.get('value') is not None:raise ValueError('fabricated absent value')
            if row.get('value') is not None and (not isinstance(row['value'],(int,float)) or not math.isfinite(row['value'])):raise ValueError('finite value')
            if row['target']=='win' and row.get('value') is not None and not 0<=row['value']<=1:raise ValueError('winner probability')
            if row['eligible'] and (not row['available'] or not index[row['game_id']]['completed']):raise ValueError('scoring eligibility')
            if kind=='model' and row.get('actual_issue_eligible') and row.get('issued_at'):
                if instant(row['issued_at'])>=instant(index[row['game_id']]['kickoff_utc']):raise ValueError('backdated or postgame issue')
                for field in ['feature_asof','fit_completed_at']:
                    if row.get(field) and instant(row[field])>instant(row['issued_at']):raise ValueError('model information clock')
    if len(data['conditional_rows'])!=82 or sum('LESS' in r['orientation'] for r in data['conditional_rows'])!=48 or sum('GREATER' in r['orientation'] for r in data['conditional_rows'])!=34:raise ValueError('conditional orientation closure')
    for r in data['conditional_rows']:
        if instant(r['issued_at'])>=instant(index[r['game_id']]['kickoff_utc']):raise ValueError('conditional issue chronology')
        if abs(r['probability_above']+r['probability_below']+r['probability_equal']-1)>.002:raise ValueError('conditional probability mass')
        if r['calibration_validated'] or r['automatic_promotion']:raise ValueError('conditional qualification')
    if any(r['denominator']!=122 for r in data['coverage_rows']):raise ValueError('equal completed provider denominator')
    if {r['provider'] for r in data['coverage_rows']}!=PROVIDERS:raise ValueError('equal provider coverage')
    for r in data['coverage_rows']:
        if not 0<=r['eligible']<=r['available']<=122:raise ValueError('coverage accounting')
    if data['new_owner_fits'] or data['new_owner_issues'] or data['new_source_acquisitions']:raise ValueError('reporting repair cannot claim execution')
    if data['next']['status']!='PREPARED_NOT_OWNER_EXECUTED' or data['next']['actual_owner_results']!=0:raise ValueError('prepared scope')
    if len(data['correction_comparisons'])!=255 or len(data['correction_summary'])!=3:raise ValueError('preserved correction closure')
    raw=json.dumps(data,ensure_ascii=False)
    if RETIRED.search(raw):raise ValueError('active terminology boundary')
    if re.search(r's3://|arn:aws:|sagemaker|/workspace/|/home/|X-Amz-|model_sha256|component_bindings|lambda=|direct201_',raw):raise ValueError('private publication boundary')
    return data

def pack(data):
    body=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode()
    compressed=gzip.compress(body,compresslevel=9,mtime=0)
    return compressed[:9]+bytes([255])+compressed[10:]

def load(path=HERE/'current_season_n053r1.json.gz'):
    return json.loads(gzip.decompress(path.read_bytes()))

def build(data):
    validate(data)
    source=(HERE/'season_review_n053r1.template.html').read_text()
    if RETIRED.search(source):raise ValueError('active template terminology')
    payload=base64.b64encode(pack(data)).decode()
    return source.replace('__SEASON_GZIP_BASE64__',payload)

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    html=build(load());out=HERE/'season_review_n053r1.html'
    if a.check:
        if out.read_text()!=html:raise SystemExit('Season page differs from the validated complete grid')
        print('N053R1 complete-season deterministic render: PASS')
    else:out.write_text(html)

if __name__=='__main__':main()
