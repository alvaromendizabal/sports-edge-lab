"""Build the current evidence page; reject mixed status, clocks and row units."""
import argparse,datetime,json,pathlib,math
ROOT=pathlib.Path(__file__).resolve().parent


def instant(value):
    result=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('Timezone required')
    return result


def validate(data):
    if data['schema']!='nfl.public.n052-actual-n053-prepared.v1':raise ValueError('schema')
    if data['owner_research_accepted'] or data['actual_orders'] or data['protected_original_refits']:raise ValueError('research boundary')
    if data['new_native_fits']!=0 or data['new_correction_fits']!=150 or data['new_target_forecasts']!=336 or data['new_cover_references']!=82 or data['new_total_issue_rows']!=418:raise ValueError('actual counters')
    if len(data['cards'])!=112 or len({(r['game_id'],r['stream_id']) for r in data['cards']})!=112:raise ValueError('card closure')
    games={g['game_id']:g for g in data['games']}
    if len(games)!=272 or len(data['games'])!=272 or sum(g['completed'] for g in games.values())!=122:raise ValueError('schedule')
    for card in data['cards']:
        game=games[card['game_id']];issued=instant(card['actual_issue_at'])
        if game['completed'] or issued>=instant(game['kickoff_utc']):raise ValueError('postgame issue')
        if instant(card['base_feature_asof'])>issued or max(map(instant,card['fit_completed_by_target'].values()))>issued:raise ValueError('issue clock')
        if card['actual_orders'] or card['final_hour_qualified'] or card['full_pipeline_selection_qualified']:raise ValueError('issue qualification')
    if len(data['winner_references'])!=87 or len(data['point_references'])!=174:raise ValueError('provider closure')
    if len({(r['game_id'],r['provider']) for r in data['winner_references']})!=87 or len({(r['game_id'],r['provider'],r['target']) for r in data['point_references']})!=174:raise ValueError('provider duplicates')
    for r in data['winner_references']+data['point_references']:
        if r['metric_eligible']:raise ValueError('current references are not a scored cohort')
        if r['acquired_at'] and instant(r['acquired_at'])>=instant(games[r['game_id']]['kickoff_utc']):raise ValueError('postgame reference')
        if r['quote_at'] and instant(r['quote_at'])>instant(r['acquired_at']):raise ValueError('future quote')
    covers=data['cover_references']
    if len(covers)!=82:raise ValueError('cover count')
    for c in covers:
        if c['execution_qualified'] or c['calibration_validated'] or c['actual_orders'] or c['automatic_promotion']:raise ValueError('cover boundary')
        if c['orientation']!=c['conditional_cover_probability_orientation']:raise ValueError('conditional orientation')
        probability=c['probability_below_threshold'] if c['orientation']=='HOME_MARGIN_STRICTLY_LESS_THAN' else c['probability_above_threshold'] if c['orientation']=='HOME_MARGIN_STRICTLY_GREATER_THAN' else None
        if probability is None or abs(probability/(1-c['probability_equal_threshold'])-c['conditional_cover_probability_nonpush'])>.002:raise ValueError('conditional probability')
        if instant(c['actual_issue_at_utc'])>=instant(games[c['game_id']]['kickoff_utc']):raise ValueError('cover clock')
    science=data['science'];counts=science['counts']
    if (counts['registered_cells'],counts['completed_cells'],counts['paired_comparisons'],counts['protected_original_refits'])!=(144,144,864,0):raise ValueError('study closure')
    if science['selection_years']!=[2021,2022,2023] or science['development_exposed_years']!=[2024,2025] or science['descriptive_years']!=[2026]:raise ValueError('selection boundary')
    if len(science['paired_comparisons'])!=864 or len({(r['family'],r['target'],r['season'],r['control']) for r in science['paired_comparisons']})!=864:raise ValueError('paired closure')
    for r in science['paired_comparisons']:
        if not all(math.isfinite(r[k]) for k in ['delta','ci_low','ci_high']) or r['ci_low']>r['ci_high']:raise ValueError('paired diagnostics')
    future=data['next']
    if future['status']!='PREPARED_NOT_OWNER_EXECUTED' or any(future[k] for k in ['owner_native_fits','owner_correction_fits','owner_forecasts']):raise ValueError('future execution credit')
    if future['planned_error_scale_states']!=70 or future['planned_distribution_season_variants']!=140 or future['expected_report_rows']!=35252 or future['selection_years']!=[2022,2023]:raise ValueError('future registration')
    if data['completed_source']['new_market_path_fits'] or data['completed_source']['new_market_path_forecasts'] or data['completed_source']['completed_study_recomputed']:raise ValueError('source-only reuse')
    correction=data['correction']
    expected={'actual_completed_correction_states':150,'binary_states':50,'point_states':100,'report_rows':41503,'baseline_rows':3773,'corrected_prediction_rows':37730,'season_metrics':165,'weekly_metrics':3168,'support_metrics':825,'paired_comparisons':255,'nested_checks':3,'independent_remote_states_verified':150,'independent_remote_receipts_verified':150}
    if any(correction[k]!=v for k,v in expected.items()):raise ValueError('correction closure')
    if len(correction['paired_rows'])!=255 or len(correction['season_metric_rows'])!=165 or len(correction['nested_rows'])!=3:raise ValueError('correction aggregate closure')
    periods={'2022_2023','2024','2025','2024_2025','2026'}
    if {r['period'] for r in correction['selected_pairs']}!=periods or len(correction['selected_pairs'])!=15:raise ValueError('correction period labels')
    for period in periods:
        if len([r for r in correction['selected_metrics'] if r['period']==period])!=6 or {r['target'] for r in correction['selected_pairs'] if r['period']==period}!={'win','margin','total'}:raise ValueError('correction period closure')
    pairs=correction['paired_rows']
    if len({(r['season'],r['target'],r['left_id'],r['right_id'],r['contrast']) for r in pairs})!=255:raise ValueError('correction duplicate comparisons')
    if correction['selection']['seasons']!=[2022,2023] or correction['current_season_selection'] or correction['selection']['selected_designation_content_targets']!=0:raise ValueError('correction selection boundary')
    if not correction['selection']['freeze_verified_before_all90later_state_starts'] or instant(correction['selection']['frozen_at_utc'])>=instant(correction['selection']['earliest_later_start']):raise ValueError('correction freeze clock')
    if correction['automatic_promotion'] or correction['selection']['automatic_promotion'] or not correction['numerics']['all150_converged']:raise ValueError('correction diagnostic boundary')
    for r in pairs:
        if not all(math.isfinite(r[k]) for k in ['left_minus_right','bootstrap_95_low','bootstrap_95_high']) or r['bootstrap_95_low']>r['bootstrap_95_high']:raise ValueError('correction interval')
    if science['repeated_designation_only_fits'] or science['repeated_injury_only_fits']:raise ValueError('protected study reuse')
    if data['bootstrap']['new_hydration_total']!=180:raise ValueError('metadata hydration')
    return data


def build(data):
    validate(data)
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return (ROOT/'review_n053.template.html').read_text().replace('__SNAPSHOT_JSON__',payload)


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    expected=build(json.loads((ROOT/'current_review_n053.json').read_text()));output=ROOT/'review_n053.html'
    if a.check:
        if output.read_text()!=expected:raise SystemExit('Current review differs from sanitized evidence')
        print('N053 current review deterministic check: PASS')
    else:output.write_text(expected)


if __name__=='__main__':main()
