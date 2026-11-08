"""Current N057 publication audit with immutable prior cohort evidence."""
import copy, hashlib, pathlib
from actual_n056_n057 import validate_active_status
HERE = pathlib.Path(__file__).resolve().parent


def audit(data):
    validate_active_status(data)
    a = copy.deepcopy(data['original_n056_completeness_audit'])
    s = data['n056_actual_results']; display = data['display_schedule_snapshot']
    a.update(schema='nfl.public.completeness_audit.n057.v1', review_date='2026-11-08',
             original_data_modified=False, schedule_changes_from_retained_snapshot=len(data['official_schedule_updates']),
             schedule_revision=data['display_schedule_snapshot'], preserved_owner_schedule=data['owner_n056_schedule_snapshot'])
    a['owner_attempt'] = {
        'cycle': 'N056', 'status': s['owner_status'], 'actual_return_sha256': s['actual_owner_return_sha256'],
        'full_durable_evidence_closure': s['full_durable_evidence_closure'], 'owner_research_acceptance': False,
        'new_native_states': s['new_native_fits'], 'new_meta_states': 0,
        'new_current_origin_states': s['native_current_origin_states'], 'new_retrospective_states': s['native_retrospective_states'],
        'verified_owner_issue_rows': s['verified_owner_issue_rows'], 'global_fit_total': s['top_level_new_fits'],
        'global_issue_total': s['top_level_new_forecasts'], 'failure_stage': s['failure_stage'],
        'qualification': 'Actual N056 completed the refreshed source, supported current family pass and 2,683 issues. The final census failed on a postseason week token. The verified partial work is retained; N057 repairs the reporting boundary. No automatic promotion.',
    }
    a['verified_public_science'].update(next_owner_cycle='N057', next_owner_execution_status='PREPARED_NOT_OWNER_EXECUTED',
        actual_N056_native_states=s['new_native_fits'], actual_N056_meta_states=0,
        actual_N056_owner_issue_rows=s['verified_owner_issue_rows'], actual_N056_selected_family_future_rows=len(data['n056_owner_family_issues']),
        actual_N056_two_game_retrospective_rows=len(data['n056_retrospective_supplement']), publication_new_fits=0, publication_new_issues=0)
    for row in a['completeness']:
        key = row['record_set']
        if key == 'Schedule events':
            row.update(present=len(data['games']), interpretation=f"All 32 teams and 272 games. Owner snapshot: 122 finals/150 future; dated official append: {display['completed']} finals/{display['remaining']} without a captured final. One completed tie.")
        elif key == 'Model role / target cells':
            row.update(expected=272*len(data['lanes'])*3, present=len(data['model_rows']), numeric_values=sum(x.get('value') is not None for x in data['model_rows']), interpretation=f"272 games × {len(data['lanes'])} distinct roles × 3 targets. The default routing view is display-only and adds no model or issue count.")
        elif key == 'Provider / target / horizon cells':
            row.update(expected=272*9*len(data['provider_horizons']), present=len(data['provider_rows']), numeric_values=sum(x.get('value') is not None for x in data['provider_rows']), interpretation=f"272 games × 3 providers × 3 targets × {len(data['provider_horizons'])} horizons. Representative current references and condition curves are separate source-only captures.")
        elif key == 'All-model seasonal metrics':
            row.update(expected=len(data['all_model_metrics']), present=len(data['all_model_metrics']), interpretation='All original full-precision aggregates plus separate two-game retrospective and one-game prospective metric rows. No scores come from rounded display values.')
        elif key in {'DraftKings grid', 'Kalshi grid', 'Polymarket grid'}:
            provider = key.removesuffix(' grid'); rs = [x for x in data['provider_rows'] if x['provider'] == provider]
            row.update(expected=272*3*len(data['provider_horizons']), present=len(rs), numeric_values=sum(x.get('value') is not None for x in rs))
    a['completeness'].extend([
        {'record_set': 'N056 actual owner issues', 'expected': s['top_level_new_forecasts'], 'present': s['verified_owner_issue_rows'], 'numeric_values': s['verified_owner_issue_rows'], 'interpretation': '336 components +336 nearer raw +1,464 long-range raw +450 selected-family +97 conditional. Distinct actual clocks; no retained earlier issues counted again as new.'},
        {'record_set': 'N056 frozen selected future rows', 'expected': 450, 'present': len(data['n056_owner_family_issues']), 'numeric_values': len(data['n056_owner_family_issues']), 'interpretation': '150 owner-future games ×3 targets. Seven new native current-origin states and two retained meta states; no event-specific T1 equivalence claim.'},
        {'record_set': 'N056 separate retrospective supplement', 'expected': 6, 'present': len(data['n056_retrospective_supplement']), 'numeric_values': len(data['n056_retrospective_supplement']), 'interpretation': 'CHI/SEA and JAX/BAL ×3 targets;14 new native retrospective states. Zero historical issue credit; original N055 cohort unchanged.'},
        {'record_set': 'N056 source-only representative cells', 'expected': 252, 'present': len(data['n056_current_provider_rows']), 'numeric_values': sum(x.get('value') is not None for x in data['n056_current_provider_rows']), 'interpretation': '28 bounded games ×3 providers ×3 targets. Capture clocks and source quote clocks retain their own meaning; zero predictive credit.'},
        {'record_set': 'N056 source-only condition curves', 'expected': data['n056_source_capture_summary']['curve_points'], 'present': len(data['n056_provider_curve_points']), 'numeric_values': sum(x.get('observed_threshold_probability') is not None or x['target']=='win' and x.get('value') is not None for x in data['n056_provider_curve_points']), 'interpretation': 'All authenticated captured conditions; full paired and censored points retained. Equal inventory includes explicit causes where a provider/target has no alternate capture.'},
        {'record_set': 'N056 separately scored prospective final', 'expected': 3, 'present': len(data['n056_prospective_metrics']), 'numeric_values': None, 'interpretation': 'One newly observed Cincinnati–Atlanta final, three exact issued targets. Small descriptive sample; outside old matched benchmarks and selection.'},
    ])
    a['official_checks'].append({'label': 'NFL official Week 9 schedule', 'url': 'https://www.nfl.com/schedules/2026/by-week/week-9', 'finding': 'Cincinnati 34, Atlanta 17 FINAL, observed 2026-11-08 at 18:01:55 UTC, after the N056 owner snapshot. Observation time is not an asserted final-whistle time.'})
    a.update(n056_actual_projection_sha256=data['n056_actual_projection_sha256'], active_status_revision=data['n057_active_status_revision'],
             new_numeric_source_values_from_publication=0,
             admitted_prior_N056_source_reference_values=data['n056_source_capture_summary']['source_values'],
             admitted_prior_N056_source_curve_points=data['n056_source_capture_summary']['curve_points'],
             all_current_provider_coverage_claimed=False, all_history_complete=False)
    return a
