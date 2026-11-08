"""Add authenticated N056 owner outputs and a dated official result revision.

The prior carriers remain immutable. Display routing is not another model,
source-only curves are not forecasts, and old cohorts are never rescored here.
"""
import collections, copy, datetime, gzip, hashlib, json, math, pathlib, re
from actual_n055_n056 import enrich as enrich_n055
from actual_recovery_n055 import ARMS, LABELS, LEGACY_COUNTERS

HERE = pathlib.Path(__file__).resolve().parent
TARGETS = ('win', 'margin', 'total')
DEFAULT_VIEW = 'VIEW_FROZEN_SELECTED_BY_EVIDENCE'
ISSUE_KEYS = ('owner_component_issues', 'owner_raw_issues', 'owner_long_range_issues', 'owner_family_issues', 'owner_conditional_issues')


def instant(value):
    stamp = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('N056 clock timezone missing')
    return stamp


def load_overlay():
    return json.loads(gzip.decompress((HERE / 'n056_actual_results_n057.json.gz').read_bytes()))


def validate_overlay(r):
    s = r['summary']
    expected = dict(zip(ISSUE_KEYS, (336, 336, 1464, 450, 97)))
    for key, count in expected.items():
        if len(r[key]) != count:
            raise ValueError('N056 actual issue closure: ' + key)
    if sum(expected.values()) != s['verified_owner_issue_rows'] or s['verified_owner_issue_rows'] != s['top_level_new_forecasts']:
        raise ValueError('N056 native issue totals differ from actual owner summary')
    if (s['new_native_fits'], s['new_meta_fits'], s['new_optimizer_starts'], s['new_optimizer_returns'], s['new_durable_state_commits']) != (21, 0, 21, 21, 21):
        raise ValueError('N056 native start/return/commit closure')
    if sum(s['family_native_counts'].values()) != s['new_native_fits']:
        raise ValueError('N056 active family native accounting')
    if not s['full_durable_evidence_closure'] or not s['independent_issue_chronology_pass']:
        raise ValueError('N056 independent actual admission incomplete')
    if s['automatic_promotion'] or s['current_season_recipe_selection'] or s['source_only_predictive_credit']:
        raise ValueError('N056 scientific scope changed')
    if len(r['retrospective_supplement']) != 6 or {x['game_id'] for x in r['retrospective_supplement']} != {'2026_08_CHI_SEA', '2026_09_JAX_BAL'}:
        raise ValueError('N056 separate two-game supplement closure')
    for key in ISSUE_KEYS[:-1]:
        rows = r[key]
        identities = {(x['game_id'], x['target'], x.get('arm'), x.get('component_role')) for x in rows}
        if len(identities) != len(rows):
            raise ValueError('N056 duplicate issue identity: ' + key)
        for x in rows:
            cutoff = instant(x['kickoff_utc']) - datetime.timedelta(hours=1)
            issue = instant(x['actual_issue_at_utc'])
            source = instant(x['source_feature_asof_at_utc'])
            if not instant(x['maximum_training_label_available_at']) < source <= issue < cutoff:
                raise ValueError('N056 real earlier label/source/issue clocks: ' + key)
            if instant(x['model_completed_at_utc']) > issue:
                raise ValueError('N056 model must exist before issue')
    for x in r['owner_conditional_issues']:
        less = x['orientation'] == 'HOME_MARGIN_STRICTLY_LESS_THAN'
        if x['orientation'] not in ('HOME_MARGIN_STRICTLY_LESS_THAN', 'HOME_MARGIN_STRICTLY_GREATER_THAN'):
            raise ValueError('N056 conditional orientation')
        p = x['probability_below'] if less else x['probability_above']
        if p != x['probability_of_predicate'] or abs(p / (1 - x['probability_equal']) - x['probability_given_not_equal']) > .000002:
            raise ValueError('N056 conditional unequal orientation')
        if not instant(x['parent_feature_asof']) <= instant(x['parent_point_issued_at']) <= instant(x['issued_at']) < instant(x['kickoff_utc']) - datetime.timedelta(hours=1):
            raise ValueError('N056 conditional source/parent/issue clocks')
        if x['historical_evaluation_qualified'] or x['calibration_validated'] or x['automatic_promotion']:
            raise ValueError('N056 conditional research qualification')
    if any(x.get('new_issue_credit', 0) for x in r['retrospective_supplement']):
        raise ValueError('Retrospective supplement cannot create an earlier issue')
    return r


def enrich(data):
    if 'n056_actual_results' in data:
        return validate_active_status(data)
    original = enrich_n055(data)
    r = validate_overlay(load_overlay())
    d = copy.deepcopy(original)
    s = r['summary']
    from publication_audit_n056 import audit as previous_audit
    d['original_n056_completeness_audit'] = previous_audit(original)
    owner_games = {g['game_id']: g for g in original['games']}
    d['original_n056_publication_snapshot'] = {
        'status': 'DATED_N056_PREPARATION_SUPERSEDED_BY_ACTUAL_N056_OWNER_RETURN',
        'original_base_as_of': original['as_of'],
        **{k: copy.deepcopy(original[k]) for k in ('family_status', 'capabilities', 'future_game_forecast_coverage', 'next', 'active_accounting', 'current_provider_counts')},
    }
    d['owner_n056_schedule_snapshot'] = {
        'as_of': s['owner_schedule_as_of'], 'games': 272, 'completed': 122,
        'decisive': 121, 'ties': 1, 'remaining': 150,
        'status': 'AUTHENTICATED_OWNER_SOURCE_SNAPSHOT_UNCHANGED',
    }
    d['official_schedule_updates'] = copy.deepcopy(r['official_schedule_updates'])
    d['schedule_timing_qualifications'] = copy.deepcopy(r['schedule_timing_qualifications'])
    for update in d['official_schedule_updates']:
        g = next(g for g in d['games'] if g['game_id'] == update['game_id'])
        if owner_games[g['game_id']]['completed']:
            raise ValueError('Official append must not rewrite an earlier final')
        home, away = update['home_score'], update['away_score']
        g.update(completed=True, tie=home == away, actual={'home_score': home, 'away_score': away, 'home_margin': home-away, 'total': home+away}, official_result_observed_at=update['observed_at_utc'], official_result_source=update['source_url'], phase_status='OFFICIAL_FINAL_AFTER_OWNER_SNAPSHOT')
    d['display_schedule_snapshot'] = {
        'as_of': max(x['observed_at_utc'] for x in d['official_schedule_updates']),
        'games': len(d['games']), 'completed': sum(g['completed'] for g in d['games']),
        'decisive': sum(g['completed'] and not g['tie'] for g in d['games']),
        'ties': sum(g['tie'] for g in d['games']),
        'remaining': sum(not g['completed'] for g in d['games']),
        'status': 'DATED_OFFICIAL_RESULT_APPEND_TO_AUTHENTICATED_OWNER_SNAPSHOT',
        'remaining_does_not_mean_all_kickoffs_are_in_the_future': True,
    }
    d['recent_final_ids'] = [x['game_id'] for x in d['official_schedule_updates']] + original['recent_final_ids']

    def add_lane(lid, title, qualification, rows, issue=True):
        lookup = {(x['game_id'], x['target']): x for x in rows}
        if len(lookup) != len(rows):
            raise ValueError('Duplicate N056 target in role ' + lid)
        lane = {'id': lid, 'label': title, 'qualification': qualification,
                'classification': 'ACTUAL_N056_OWNER_ISSUE' if issue else 'N056_SEPARATE_RETROSPECTIVE_SUPPLEMENT',
                'available_games': len({x['game_id'] for x in rows}), 'new_fit_credit_this_review': 0}
        d['lanes'].append(lane)
        for g in d['games']:
            for target in TARGETS:
                rec = lookup.get((g['game_id'], target))
                x = {'game_id': g['game_id'], 'lane_id': lid, 'target': target,
                     'value': None, 'available': False, 'eligible': False,
                     'reason': 'This N056 role has no authenticated numerical output for this game and target. The complete event and all other dated roles remain in the inventory.',
                     'classification': lane['classification'], 'issued_at': None, 'feature_asof': None,
                     'fit_completed_at': None, 'actual_issue_eligible': False, 'precise_source_value': False,
                     'completed': g['completed'], 'horizon': 'ACTUAL_CURRENT_KNOWLEDGE_ISSUE' if issue else 'SEPARATE_FROZEN_POLICY_RETROSPECTIVE_APPEND',
                     'actual': None, 'correct': None, 'absolute_error': None, 'automatic_promotion': False}
                if rec:
                    x.update(value=rec['prediction'], available=True, eligible=not issue,
                             classification=rec['classification'], reason=qualification,
                             actual=rec.get('actual'), feature_asof=rec['source_feature_asof_at_utc'],
                             fit_completed_at=rec['model_completed_at_utc'],
                             maximum_training_label_available_at=rec['maximum_training_label_available_at'],
                             new_owner_issue_credit=int(issue), new_native_fit_credit=0,
                             issue_origin='N056_OWNER' if issue else None,
                             near_term_T1_equivalence_claimed=False)
                    if issue:
                        x.update(issued_at=rec['actual_issue_at_utc'], actual_issue_eligible=True,
                                 source_age_seconds=(instant(rec['actual_issue_at_utc'])-instant(rec['source_feature_asof_at_utc'])).total_seconds())
                    for field in ('injury_reports_qualified', 'injury_feature_cutoff_at', 'designation_feature_cutoff_at', 'designation_reports_qualified', 'designation_max_report_available_at_utc', 'injury_max_report_available_at_utc', 'injury_max_auxiliary_available_at_utc', 'training_rows', 'horizon_days', 'outlook_scope', 'current_injury_persistence_assumed', 'unplayed_intervening_results_assumed', 'historical_source_possession_verified', 'historical_source_publication_verified', 'policy', 'model', 'component_role', 'both_team_reports_observed', 'personnel_report_rows', 'personnel_source_available_at', 'personnel_source_publication_clock_known', 'missing_personnel_does_not_mean_healthy', 'depth_chart_inferred', 'individual_talent_inferred', 'injury_causation_inferred', 'personnel_support_reason'):
                        if field in rec:
                            x[field] = rec[field]
                    if target == 'win':
                        x.update(pick=g['home'] if x['value'] >= .5 else g['away'], pick_probability=max(x['value'], 1-x['value']))
                        if not issue and x['actual'] is not None:
                            x['correct'] = rec['correct']
                    elif not issue and x['actual'] is not None:
                        x['absolute_error'] = rec['absolute_error']
                d['model_rows'].append(x)

    for role, title in [('original', 'Original champion · retained November 4 source'), ('shadow', 'Shadow blend · retained November 4 source'), ('fresh', 'Fresh rolling component'), ('designation', 'Current designation component')]:
        add_lane('n056_component_' + role, 'N056 owner · ' + title,
                 'Actual N056 owner component issue with its original source, training and issue clocks. Original/shadow retain the older November 4 base source; fresh/designation use the authenticated refreshed source. Injury qualification is per event. No automatic promotion or replacement of historical horizons.',
                 [x for x in r['owner_component_issues'] if x['component_role'] == role])
    for arm in ARMS:
        add_lane('n056_issued_' + arm, 'N056 nearer-game owner · ' + LABELS[arm],
                 'Actual N056 issue on the owner snapshot of 28 nearer games, using an authenticated refreshed source and retained raw football states. No repeated raw fitting. The current-origin issue is distinct from a registered event-specific T1 issue.',
                 [x for x in r['owner_raw_issues'] if x['arm'] == arm])
        add_lane('n056_outlook_' + arm, 'N056 long-range owner · ' + LABELS[arm],
                 'Actual N056 owner outlook on the owner snapshot of 122 later games. It reuses completed raw states and retains real source/model/issue clocks. Event-specific future injury reports and intervening results are not assumed; long-horizon accuracy is unvalidated.',
                 [x for x in r['owner_long_range_issues'] if x['arm'] == arm])
    add_lane('n056_selected_future', 'N056 frozen selection · actual owner issues',
             'The N055 procedure was selected on full identical 2022/23 cohorts including the unchanged baseline and remained frozen. N056 issued all three targets for 150 games at actual current-origin clocks, using seven new native states and retained OOF meta states; another 14 new states belong to the separate retrospective supplement. These are early research issues, with no automatic promotion or exact T1-equivalence claim.', r['owner_family_issues'])
    add_lane('n056_two_game_retrospective', 'N056 frozen selection · separate two-game supplement',
             'Separate retrospective evaluation for CHI/SEA and JAX/BAL under the unchanged 2022/23 selection. These six rows complete the additive current-season family accounting but are not original pregame issues. The original N055 105,075-row study and 120-point/119-winner cohort remain immutable.', r['retrospective_supplement'], issue=False)

    for key in ISSUE_KEYS:
        d['n056_' + key] = r[key]
    d['n056_retrospective_supplement'] = r['retrospective_supplement']
    d['n056_retrospective_metrics'] = r['retrospective_metrics']
    d['n056_prospective_review'] = r['prospective_review']
    d['n056_prospective_metrics'] = r['prospective_metrics']
    d['n056_family_current_job_ledger'] = r['family_current_job_ledger']
    d['n056_personnel_support'] = r['personnel_support']
    d['n056_actual_results'] = s
    d['n056_actual_projection_sha256'] = hashlib.sha256((HERE / 'n056_actual_results_n057.json.gz').read_bytes()).hexdigest()
    for group, key, horizon in [('N056 separate two-game frozen-policy supplement', 'retrospective_metrics', 'SEPARATE_RETROSPECTIVE_APPEND'), ('N056 actual issued forecast · one-game prospective review', 'prospective_metrics', 'ACTUAL_CURRENT_ORIGIN_ISSUE')]:
        for metric in r[key]:
            row = dict(metric)
            row.update(identity='Frozen selected event procedure', group=group, horizon=horizon,
                       qualification='Separate small descriptive cohort; exact full-precision private predictions were scored independently. No replacement of old metrics, recipe selection or automatic promotion.')
            d['all_model_metrics'].append(row)

    source = r['current_source']
    d['n056_source_capture_summary'] = source['summary']
    d['n056_current_provider_rows'] = source['provider_rows']
    d['n056_provider_curve_points'] = source['curve_points']
    d['n056_provider_curve_inventory'] = source['curve_inventory']
    d['n056_current_provider_counts'] = source['current_provider_counts']
    d['n056_source_schedule_reconciliation'] = source['schedule_reconciliation']
    d['current_provider_counts'] = copy.deepcopy(source['current_provider_counts'])
    for horizon, source_rows in [('N056_CURRENT_CAPTURE', source['provider_rows']), ('N056_ALTERNATE_CURVE_CAPTURE', source['curve_inventory'])]:
        d['provider_horizons'].append(horizon)
        lookup = {(x['game_id'], x['provider'], x['target']): x for x in source_rows}
        for g in d['games']:
            for provider in ('DraftKings', 'Kalshi', 'Polymarket'):
                for target in TARGETS:
                    row = lookup.get((g['game_id'], provider, target))
                    if row is None:
                        row = {'game_id': g['game_id'], 'provider': provider, 'target': target,
                               'horizon': horizon, 'value': None, 'available': False, 'eligible': False,
                               'reason': 'The N056 current capture was bounded to 28 owner-future games. This event lies outside that acquisition scope; retained historical horizons and other provider observations stay separately selectable.',
                               'classification': 'OUTSIDE_N056_CURRENT_CAPTURE', 'quote_at': None, 'acquired_at': None,
                               'completed': owner_games[g['game_id']]['completed'], 'source_only_predictive_credit': 0,
                               'complete_midpoint_probability': False, 'one_sided_known_threshold': False}
                    d['provider_rows'].append(copy.deepcopy(row))
    d['default_review_selection'] = [
        {'game_id': g['game_id'], 'lane_id': 'n056_selected_future' if not owner_games[g['game_id']]['completed'] else 'n056_two_game_retrospective' if g['game_id'] in {'2026_08_CHI_SEA', '2026_09_JAX_BAL'} else 'n055_selected_event',
         'display_only': True, 'new_model_credit': 0, 'new_issue_credit': 0}
        for g in d['games']
    ]
    d['default_view_id'] = DEFAULT_VIEW
    d['default_view_label'] = 'Frozen selected procedure · dated evidence for every game'
    d['denominator_bridge'].extend([
        {'label': 'Dated official display after the owner snapshot', 'count': d['display_schedule_snapshot']['completed'], 'denominator': 272,
         'reason': 'The authenticated N056 owner snapshot retains 122 completed games. The separately observed November 8 Cincinnati 34–Atlanta 17 final adds one display result; no historical benchmark is enlarged.'},
        {'label': 'N056 separate family retrospective supplement', 'count': 2, 'denominator': 122,
         'reason': 'CHI/SEA and JAX/BAL each have three frozen-policy target rows. The original family study remains 120 point / 119 winner; this additive two-game cohort has no original-issue credit.'},
        {'label': 'N056 separately observed prospective final', 'count': len(r['prospective_review']['game_ids']), 'denominator': 150,
         'reason': 'The N056 selected future issue existed before its source/model/issue cutoff. Cincinnati–Atlanta is scored separately from full-precision issued rows after the official final was observed. A one-game result does not establish superiority.'},
    ])
    return refresh_active_status(d, original)


def refresh_active_status(d, original):
    s = d['n056_actual_results']
    for row in d['family_status']:
        row['retained_n055_evidence'] = 'Actual N055 historical study: ' + row['evidence']
        added = s['family_native_counts'].get(row.get('backend'), 0)
        row.update(n056_native_states=added, n056_meta_states=0, n056_status='ACTUAL_N056_SUPPORTED_CURRENT_PASS',
                   status='ACTUAL_N055_HISTORICAL_AND_N056_CURRENT_RESULTS',
                   status_label=f"{row['n055_native_states']} N055 + {added} N056 native states" if row.get('backend') else '45 retained N055 meta states; no new N056 meta fit')
        row['evidence'] = (f"The authenticated N056 current pass completed {added} new native states for this family. " if row.get('backend') else 'N056 reuses completed OOF meta states; no new meta fitting. ') + row['retained_n055_evidence'] + ' The three inherited unresolved starts remain quarantined and receive no completed-state credit.'
    near = d['n056_owner_raw_issues']; far = d['n056_owner_long_range_issues']; family = d['n056_owner_family_issues']
    ng = {x['game_id'] for x in near}; fg = {x['game_id'] for x in far}
    prior = d['n054_actual_recovery']['independently_recovered_owner_issue_rows'] + len(d['n055_owner_component_issues'])
    d['future_game_forecast_coverage'] = {
        'scope': 'ACTUAL_N056_OWNER_SNAPSHOT_WITH_SEPARATE_LATER_OFFICIAL_RESULT',
        'owner_snapshot_as_of': s['owner_schedule_as_of'], 'scheduled_future_games_at_owner_snapshot': 150,
        'currently_remaining_games': d['display_schedule_snapshot']['remaining'],
        'owner_nearer_game_issue_games': len(ng), 'owner_long_range_outlook_games': len(fg),
        'covered_future_games': len(ng | fg), 'actual_N056_owner_issue_rows': s['verified_owner_issue_rows'],
        'owner_issue_rows': prior + s['verified_owner_issue_rows'], 'retained_N054_owner_issue_rows': 2233,
        'retained_N055_owner_issue_rows': 168,
        'owner_raw_nearer_issue_rows': len(near), 'owner_long_range_issue_rows': len(far),
        'owner_component_issue_rows': len(d['n056_owner_component_issues']),
        'owner_conditional_issue_rows': len(d['n056_owner_conditional_issues']),
        'owner_family_issue_rows': len(family), 'owner_family_nearer_rows': sum(x['game_id'] in ng for x in family),
        'owner_family_later_rows': sum(x['game_id'] in fg for x in family),
        'new_raw_fits_for_owner_issues': 0, 'new_selected_family_native_fits_total': s['new_native_fits'],
        'future_origin_native_fits': s['native_current_origin_states'],
        'retrospective_native_fits': s['native_retrospective_states'],
        'original_review_rows_in_owner_total': 0, 'near_term_T1_equivalence_claimed': False,
        'long_horizon_accuracy_validated': False,
    }
    for c in d['capabilities']:
        name = c['name']
        if name in {'Complete season and versioned models', 'Actual rolling research issues', 'Three-provider reference alignment', 'Current football issues', 'Every future game has a dated outlook', 'Broad family and OOF meta research', 'Position and line continuity frontier'}:
            c['status'] = 'ACTUAL_N056_SUPPORTED_EVIDENCE_WITH_RETAINED_PRIOR_RESULTS'
        if name == 'Complete season and versioned models':
            c.update(evidence=f"272 games and {len(d['lanes'])} distinct retained, reconstructed or issued model roles. The official display adds one final after the unchanged owner snapshot; every target retains its evidence reason.", evidence_counts={'games': 272, 'model_roles': len(d['lanes'])})
        elif name == 'Actual rolling research issues':
            c.update(status_label='2,683 actual N056 owner rows', evidence='N056 adds 336 component, 336 nearer raw, 1,464 long-range raw, 450 selected-family and 97 conditional issues. N054 2,233 and N055 168 rows remain separately dated.', limit='Different issue origins and source ages are not interchangeable. The original/shadow base source remains November 4. No publication-time fit or issue is created.', evidence_counts={'actual_N056_owner_issue_rows': s['verified_owner_issue_rows'], 'retained_N054_owner_issue_rows': 2233, 'retained_N055_owner_issue_rows': 168})
        elif name == 'Three-provider reference alignment':
            q = d['n056_source_capture_summary']
            c.update(status_label='N056 representative references and condition curves', evidence=f"{q['normalized_rows']:,} authenticated normalized observations support {q['observed_target_cells']} representative target cells and {q['curve_points']} separately dated condition-curve points. Every provider has the same schedule/target inventory.", limit='Source-only references earn zero predictive credit. Capture time and source quote time remain distinct. Missing paired prices and unsupported curve coverage are explicit; old T1/T2 records are unchanged.', evidence_counts={'normalized_rows': q['normalized_rows'], 'derived_target_values': q['observed_target_cells'], 'curve_points': q['curve_points'], 'source_only_predictive_credit': 0})
        elif name == 'Current football issues':
            c.update(status_label='336 actual N056 nearer-game raw rows', evidence='Four retained raw football arms × three targets × 28 nearer owner-snapshot games. Fresh source routing succeeded; source/model/issue clocks are independently checked.', limit='The four-lane native states were reused, with zero repeated raw optimization. These actual current-origin issues do not establish event-specific T1 equivalence.', evidence_counts={'owner_raw_issue_rows': len(near), 'nearer_games': len(ng), 'new_raw_fits': 0})
        elif name == 'Every future game has a dated outlook':
            c.update(status_label='150 owner-snapshot games covered; one later final', evidence='N056 issued all targets in the frozen selected-family procedure for 150 games: 28 nearer and 122 later. Four raw arms also retain 336 nearer and 1,464 later rows. The dated official display now has 149 games without a captured final.', limit='Event-specific future injury status and intervening outcomes are not assumed. Long-horizon accuracy remains unvalidated. Older N054/N055 issues stay in their own dated roles.', evidence_counts={'owner_long_range_issue_rows': len(far), 'later_games': len(fg), 'nearer_games': len(ng), 'covered_future_games': len(ng | fg), 'family_issue_rows': len(family), 'new_raw_fits': 0})
        elif name == 'Broad family and OOF meta research':
            c.update(status_label='N055 complete historical research; N056 current pass', evidence='N055 retains 1,378 native and 45 meta states, 105,075 historical rows, 411 seasonal metrics and 339 paired comparisons. N056 adds 21 native states, zero meta fits, 450 actual future issues and a separate six-row retrospective supplement.', limit='The original 120-point/119-winner family cohort and all negative findings remain unchanged. Two-game retrospective and one-game prospective reviews remain separate; no selection on later results or automatic promotion.', evidence_counts={'retained_N055_native_states': 1378, 'retained_N055_meta_states': 45, 'new_N056_native_states': s['new_native_fits'], 'new_N056_meta_states': 0, 'new_N056_family_issue_rows': len(family), 'retrospective_rows': 6})
        elif name == 'Position and line continuity frontier':
            c.update(status_label='Retained position features; actual per-game source support', evidence='The fixed QB, RB/FB and OL status-count interactions remain in the completed 46/58/60/72-column football arms. N056 verifies report-source timing for 42 of the 450 selected-family target rows; 408 keep explicitly unsupported event-specific personnel values.', limit='Missing support does not mean healthy. Individual talent, depth charts, lineup continuity, future injury persistence and injury causation are not inferred. No new injury-study fit or performance credit is created.', evidence_counts={'personnel_target_rows': len(d['n056_personnel_support']), 'with_reports': s['personnel_target_rows_with_reports'], 'without_reports': s['personnel_target_rows_without_reports']})
    d['next'] = {
        'cycle': 'N057', 'status': 'PREPARED_NOT_OWNER_EXECUTED', 'actual_owner_results': 0,
        'title': 'N057 repairs the final census parser and continues exact-state reuse.',
        'paragraphs': [
            'Authenticate the actual partial N056 return, every exact recovered object and its later external completion. Preserve the completed source refresh, 21 new native states and 2,683 actual issues alongside all prior completed and negative studies.',
            'Repair regular-season versus postseason schedule-token handling at the failed final census boundary. Preserve the original owner 272/122/121 snapshot and explain later official result updates separately. Reuse exact compatible states; do not repeat the protected studies or six controls.',
            'Continue only supported current-origin issues with genuine source, model and issue clocks. Retain bounded source curves and missing-support reasons without source-only predictive credit. Current-season results select no recipe.',
            'N057 is prepared for owner execution. This public review creates zero new scientific fits or forecast issues; no automatic promotion is authorized.',
        ],
    }
    d['active_accounting'] = {
        'scope': 'N057_REVIEW_PUBLICATION_ONLY',
        'retained_N053R1': copy.deepcopy(original['active_accounting']['retained_N053R1']),
        'retained_N054': copy.deepcopy(original['active_accounting']['retained_N054']),
        'retained_N055': copy.deepcopy(original['active_accounting']['actual_N055']),
        'actual_N056': {'status': s['owner_status'], 'native_states': s['new_native_fits'], 'meta_states': 0,
                        'optimizer_starts': 21, 'optimizer_returns': 21, 'durable_commits': 21,
                        'owner_issue_rows': s['verified_owner_issue_rows'], 'global_fit_total': s['top_level_new_fits'],
                        'global_issue_total': s['top_level_new_forecasts'], 'owner_research_acceptance': False,
                        'retrospective_rows': 6, 'retrospective_issue_credit': 0},
        'N057': {'status': 'PREPARED_NOT_OWNER_EXECUTED', 'new_native_fits': 0, 'new_meta_fits': 0, 'new_owner_issues': 0, 'new_source_requests': 0},
    }
    for key in LEGACY_COUNTERS:
        d[key] = 0
    d['n057_active_status_revision'] = 1
    return validate_active_status(d)


def validate_active_status(d):
    s = d['n056_actual_results']; f = d['future_game_forecast_coverage']
    games = {g['game_id']: g for g in d['games']}
    if len(games) != 272 or len({g['away'] for g in games.values()} | {g['home'] for g in games.values()}) != 32:
        raise ValueError('N057 all scheduled games and teams')
    if any(n != 17 for n in collections.Counter(t for g in games.values() for t in (g['away'], g['home'])).values()):
        raise ValueError('N057 complete team schedule')
    if len(d['schedule_timing_qualifications']) != 24 or any(x['exact_start_time_verified'] or x['registered_kickoff_utc'] != games[x['game_id']]['kickoff_utc'] for x in d['schedule_timing_qualifications']):
        raise ValueError('Registered placeholder kickoff qualification')
    active = d['display_schedule_snapshot']; old = d['owner_n056_schedule_snapshot']
    if (old['completed'], old['decisive'], old['remaining']) != (122, 121, 150):
        raise ValueError('Owner schedule snapshot changed')
    if (active['completed'], active['decisive'], active['remaining']) != (123, 122, 149) or active['completed'] != sum(g['completed'] for g in games.values()):
        raise ValueError('Dated official schedule revision')
    for gid, scores in [('2026_08_CHI_SEA', (34, 17)), ('2026_09_JAX_BAL', (33, 10)), ('2026_09_CIN_ATL', (34, 17))]:
        if (games[gid]['actual']['away_score'], games[gid]['actual']['home_score']) != scores:
            raise ValueError('Official result identity: ' + gid)
    expected_models = {(g, l['id'], t) for g in games for l in d['lanes'] for t in TARGETS}
    expected_providers = {(g, p, t, h) for g in games for p in ('DraftKings', 'Kalshi', 'Polymarket') for t in TARGETS for h in d['provider_horizons']}
    if len(d['model_rows']) != len(expected_models) or {(x['game_id'], x['lane_id'], x['target']) for x in d['model_rows']} != expected_models:
        raise ValueError('N057 complete unique model-target grid')
    if len(d['provider_rows']) != len(expected_providers) or {(x['game_id'], x['provider'], x['target'], x['horizon']) for x in d['provider_rows']} != expected_providers:
        raise ValueError('N057 complete equal provider grid')
    if len(d['default_review_selection']) != len(games) or {x['game_id'] for x in d['default_review_selection']} != set(games):
        raise ValueError('N057 default view event closure')
    if any(x['new_issue_credit'] or x['new_model_credit'] or not x['display_only'] for x in d['default_review_selection']):
        raise ValueError('Display mapping cannot create model credit')
    for row in d['model_rows'] + d['provider_rows']:
        if not row['available'] and row.get('value') is not None:
            raise ValueError('Invented absent value')
        if not isinstance(row.get('reason'), str) or len(row['reason'].strip()) < 15:
            raise ValueError('Specific support reason required')
        if row.get('value') is not None and (not math.isfinite(row['value']) or (row['target'] == 'win' and not 0 <= row['value'] <= 1)):
            raise ValueError('Invalid numerical reference')
    new = [x for x in d['provider_rows'] if x['horizon'] == 'N056_CURRENT_CAPTURE']
    if any(x['eligible'] or x['source_only_predictive_credit'] for x in new + d['n056_provider_curve_points']):
        raise ValueError('Source-only boundary')
    if sum(x['available'] for x in new) != d['n056_source_capture_summary']['observed_target_cells'] or len(d['n056_provider_curve_points']) != d['n056_source_capture_summary']['curve_points']:
        raise ValueError('Source values and active count mismatch')
    if len(d['n055_family_per_game']) != 105075 or len(d['n055_family_season_metrics']) != 411 or len(d['n055_family_comparisons']) != 339:
        raise ValueError('Protected family study changed')
    personnel = d['n056_personnel_support']
    if len(personnel) != 450 or sum(bool(x['personnel_report_rows']) for x in personnel) != s['personnel_target_rows_with_reports'] or sum(not x['personnel_report_rows'] for x in personnel) != s['personnel_target_rows_without_reports']:
        raise ValueError('Per-event personnel support count')
    if any(x['depth_chart_inferred'] or x['individual_talent_inferred'] or x['injury_causation_inferred'] or not x['missing_personnel_does_not_mean_healthy'] for x in personnel):
        raise ValueError('Unsupported personnel inference')
    near = {x['game_id'] for x in d['n056_owner_raw_issues']}; far = {x['game_id'] for x in d['n056_owner_long_range_issues']}
    actual = sum(len(d['n056_' + k]) for k in ISSUE_KEYS)
    if near & far or (len(near), len(far), len(near | far)) != (28, 122, 150) or {x['game_id'] for x in d['n056_owner_family_issues']} != near | far:
        raise ValueError('Owner-snapshot complete future coverage')
    if actual != s['verified_owner_issue_rows'] or f['actual_N056_owner_issue_rows'] != actual or f['owner_issue_rows'] != 2233 + 168 + actual:
        raise ValueError('Active owner issue count mismatch')
    if f['covered_future_games'] != 150 or f['currently_remaining_games'] != 149 or f['original_review_rows_in_owner_total']:
        raise ValueError('Dated future/current distinction')
    if (f['future_origin_native_fits'], f['retrospective_native_fits'], f['new_selected_family_native_fits_total']) != (s['native_current_origin_states'], s['native_retrospective_states'], s['new_native_fits']):
        raise ValueError('Current and retrospective fitted states must stay distinct')
    if sum(x['n056_native_states'] for x in d['family_status']) != s['new_native_fits'] or any(x['n056_meta_states'] for x in d['family_status']):
        raise ValueError('Active N056 family count mismatch')
    if any(x['n056_status'] != 'ACTUAL_N056_SUPPORTED_CURRENT_PASS' for x in d['family_status']):
        raise ValueError('Stale active family status')
    cards = {x['name']: x for x in d['capabilities']}
    if cards['Complete season and versioned models']['evidence_counts'] != {'games': len(games), 'model_roles': len(d['lanes'])}:
        raise ValueError('Active role capability mismatch')
    if cards['Broad family and OOF meta research']['evidence_counts']['new_N056_native_states'] != s['new_native_fits']:
        raise ValueError('Active broad-family capability mismatch')
    if cards['Three-provider reference alignment']['evidence_counts']['curve_points'] != len(d['n056_provider_curve_points']):
        raise ValueError('Active curve capability mismatch')
    for name in ['Complete season and versioned models', 'Actual rolling research issues', 'Three-provider reference alignment', 'Current football issues', 'Every future game has a dated outlook', 'Broad family and OOF meta research', 'Position and line continuity frontier']:
        if cards[name]['status'] != 'ACTUAL_N056_SUPPORTED_EVIDENCE_WITH_RETAINED_PRIOR_RESULTS':
            raise ValueError('Stale underlying active capability status')
    if d['next']['cycle'] != 'N057' or d['next']['actual_owner_results'] or d['next']['status'] != 'PREPARED_NOT_OWNER_EXECUTED':
        raise ValueError('Next owner status mismatch')
    if any(d[k] for k in LEGACY_COUNTERS) or d['active_accounting']['scope'] != 'N057_REVIEW_PUBLICATION_ONLY':
        raise ValueError('Publication-only counter scope')
    if d['active_accounting']['actual_N056']['owner_issue_rows'] != actual or d['active_accounting']['actual_N056']['native_states'] != s['new_native_fits']:
        raise ValueError('Active owner count mismatch')
    from build_season_review_n054 import RETIRED
    public = json.dumps(d, ensure_ascii=False)
    if RETIRED.search(public) or re.search(r's3://|arn:aws:|sagemaker|/workspace/|/home/|X-Amz-|model_sha256|component_bindings|lambda=|direct201_', public):
        raise ValueError('Research-only public content boundary')
    return d
