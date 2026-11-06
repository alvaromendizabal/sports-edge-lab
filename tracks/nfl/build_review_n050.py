"""Build the small current review from an explicitly sanitized, dated snapshot."""
import argparse,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent


def validate(data):
    if data['schema']!='nfl.public.n049-actual-n050-readiness.v1':raise ValueError('schema')
    if data['owner_research_accepted'] or data['new_native_fits']!=0:raise ValueError('actual acceptance/fit count')
    if data['new_target_forecasts']!=168 or len(data['cards'])!=56:raise ValueError('actual issue count')
    if len(data['games'])!=272 or sum(g['completed'] for g in data['games'])!=122:raise ValueError('schedule census')
    if len({g['game_id'] for g in data['games']})!=272:raise ValueError('duplicate game')
    if data['next']['status']!='PREPARED_NOT_OWNER_EXECUTED':raise ValueError('next state')
    if data['next']['owner_native_fits'] or data['next']['owner_forecasts']:raise ValueError('unexecuted milestone')
    if len(data['winner_references'])!=87 or len(data['point_references'])!=174:raise ValueError('reference cells')
    if len({(c['game_id'],c['stream_id']) for c in data['cards']})!=56:raise ValueError('duplicate card')
    games={g['game_id']:g for g in data['games']}
    for c in data['cards']:
        if games[c['game_id']]['completed']:raise ValueError('postgame issue')
        if c['actual_issue_at']>=games[c['game_id']]['kickoff_utc']:raise ValueError('issue clock')
        if c['final_hour_qualified'] or c['full_pipeline_selection_qualified'] or c['actual_orders']:raise ValueError('research scope')
    for r in data['winner_references']+data['point_references']:
        if r['metric_eligible']:raise ValueError('current references are not a scored cohort')
    source=data['completed_source']
    if source['feature_rows']!=172373 or source['expanded_window_rows']!=4*source['feature_rows']:raise ValueError('window census')
    if source['new_market_path_fits']:raise ValueError('source/model boundary')
    return data


def build(data):
    validate(data)
    template=(ROOT/'review_n050.template.html').read_text()
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return template.replace('__SNAPSHOT_JSON__',payload)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    expected=build(json.loads((ROOT/'current_review_n050.json').read_text()))
    output=ROOT/'review_n050.html'
    if args.check:
        if output.read_text()!=expected:raise SystemExit('Current review differs from sanitized snapshot/template')
        print('N050 current review deterministic check: PASS')
    else:output.write_text(expected)

if __name__=='__main__':main()
