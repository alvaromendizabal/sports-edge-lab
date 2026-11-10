"""Validate the sanitized, dated partial-run report without fitting or rescoring.

This publication contract checks evidence shape and scope. It cannot authenticate
an unpublished run from a digest alone. No provider access is performed.
"""
from datetime import datetime
import re


FIELDS = {
    '': 'schema owner_release status started_at finished_at owner_return_sha256 evidence_authentication execution frozen_comparison current_capture preserved_evidence prepared_successor publication',
    'evidence_authentication': 'manifest_payloads_verified all_manifest_payloads_verified',
    'execution': 'new_base_fits new_calibration_fits new_mixture_fits new_scalar_prediction_outputs new_rolling_fits new_genuine_forecasts frozen_stage_new_genuine_forecasts champion_stage_new_genuine_forecasts worker_exit supervisor_exit outer_shell_exit worker_seconds_before_packaging observer_elapsed_seconds timing_scopes_overlap provider_requests known_odds_credits full_research_complete live_throughput_benchmark',
    'frozen_comparison': 'registered_cases completed_cases remaining_cases global_comparison_complete rolling_champions_authorized completed_season_gate selection_seasons current_season_used_for_selection evidence_class certified_novel_feature_concepts requested_novel_concept_target',
    'current_capture': 'observed_at completed_at fixtures observed_finals exact_kickoffs unresolved_exact_kickoffs all_season_fixtures changes_saved_game_layer refreshes_prior_metrics',
    'preserved_evidence': 'owner_release source_capture_completed_at issue_contexts unique_issue_games fixtures negative_mixture_evaluation_games negative_mixture_evaluation_season negative_mixture_computed_at original_forecasts_modified saved_metrics_rescored',
    'prepared_successor': 'release status owner_execution_observed new_owner_science_credited method study_maximum_starts study_scheduling_budget_seconds existing_frozen_maximum_starts existing_frozen_scheduling_budget_seconds existing_shared_maximum_starts existing_shared_scheduling_budget_seconds progress_policy recovery_policy completion_adapter_scope validation_class',
    'publication': 'new_model_fits new_forecast_issues new_provider_requests historical_rescoring prospective_advantage_claim automatic_promotion',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(stamp.tzinfo is not None, 'timezone required')
    return stamp


def count(value):
    require(type(value) is int and value >= 0, 'nonnegative integer count required')
    return value


def validate(data):
    require(type(data) is dict, 'object required')
    for section, fields in FIELDS.items():
        value = data if not section else data.get(section)
        require(type(value) is dict and set(value) == set(fields.split()),
                'unexpected or missing public fields: ' + section)
    require(data['schema'] == 'sports-edge-lab.public-fbs-owner-status.v1', 'unsupported schema')
    require(data['owner_release'] == 'V055', 'owner identity changed')
    require(data['status'] == 'V055_PARTIAL_BOUNDED_RECOVERY_CHECKPOINTED_NO_LIVE_BENCHMARK', 'partial status required')
    require(re.fullmatch('[0-9a-f]{64}', data['owner_return_sha256']) is not None, 'return digest required')
    require(timestamp(data['started_at']) < timestamp(data['finished_at']), 'owner clocks reversed')
    e, f, c, p, n = (data[k] for k in ('execution', 'frozen_comparison', 'current_capture', 'preserved_evidence', 'prepared_successor'))
    for key in ('registered_cases', 'completed_cases', 'remaining_cases', 'rolling_champions_authorized', 'certified_novel_feature_concepts', 'requested_novel_concept_target'):
        count(f[key])
    require(f['completed_cases'] + f['remaining_cases'] == f['registered_cases'], 'scientific-case accounting mismatch')
    require(f['remaining_cases'] > 0 and f['global_comparison_complete'] is False, 'incomplete comparison cannot claim completion')
    require(f['rolling_champions_authorized'] == 0 and f['current_season_used_for_selection'] is False, 'unsupported champion selection')
    require(f['selection_seasons'] == [2024, 2025], 'selection seasons changed')
    require(f['certified_novel_feature_concepts'] == 0 and f['requested_novel_concept_target'] == 200, 'novelty target remains open')
    for key in ('new_base_fits', 'new_calibration_fits', 'new_mixture_fits', 'new_scalar_prediction_outputs', 'new_rolling_fits', 'frozen_stage_new_genuine_forecasts', 'champion_stage_new_genuine_forecasts', 'provider_requests', 'known_odds_credits'):
        count(e[key])
    require(e['new_genuine_forecasts'] is None, 'unknown root issuance must remain null')
    require(e['outer_shell_exit'] is None, 'unproved outer exit must remain null')
    require(e['worker_exit'] == e['supervisor_exit'] == 2, 'partial process exits required')
    require(e['frozen_stage_new_genuine_forecasts'] == e['champion_stage_new_genuine_forecasts'] == e['new_rolling_fits'] == 0, 'unsupported stage execution')
    require(e['full_research_complete'] is False and e['live_throughput_benchmark'] is False and e['timing_scopes_overlap'] is True, 'execution scope changed')
    for key in ('fixtures', 'observed_finals', 'exact_kickoffs', 'unresolved_exact_kickoffs', 'all_season_fixtures'):
        count(c[key])
    require(c['exact_kickoffs'] + c['unresolved_exact_kickoffs'] == c['fixtures'], 'kickoff coverage mismatch')
    require(c['observed_finals'] <= c['fixtures'] <= c['all_season_fixtures'], 'fixture coverage mismatch')
    require(timestamp(c['observed_at']) <= timestamp(c['completed_at']), 'capture clocks reversed')
    require(timestamp(p['source_capture_completed_at']) < timestamp(c['observed_at']), 'preserved capture cannot be redated')
    require(timestamp(p['negative_mixture_computed_at']) < timestamp(c['observed_at']), 'prior metrics cannot be redated')
    require(c['changes_saved_game_layer'] is False and c['refreshes_prior_metrics'] is False, 'capture is not rescoring')
    require(p['original_forecasts_modified'] is False and p['saved_metrics_rescored'] is False, 'prior evidence must be preserved')
    require(n['release'] == 'V056' and n['status'] == 'PREPARED_OWNER_EXECUTION_PENDING', 'successor is preparation')
    require(n['owner_execution_observed'] is False and n['new_owner_science_credited'] is False, 'preparation creates no owner science')
    for key in ('study_maximum_starts', 'study_scheduling_budget_seconds', 'existing_frozen_maximum_starts', 'existing_frozen_scheduling_budget_seconds', 'existing_shared_maximum_starts', 'existing_shared_scheduling_budget_seconds'):
        count(n[key])
    require(n['study_maximum_starts'] <= n['existing_frozen_maximum_starts'] <= n['existing_shared_maximum_starts'], 'fit budget hierarchy')
    require(n['study_scheduling_budget_seconds'] <= n['existing_frozen_scheduling_budget_seconds'] <= n['existing_shared_scheduling_budget_seconds'], 'time budget hierarchy')
    pub = data['publication']
    require(all(type(pub[k]) is int and pub[k] == 0 for k in ('new_model_fits', 'new_forecast_issues', 'new_provider_requests')), 'publication creates no science')
    require(all(pub[k] is False for k in ('historical_rescoring', 'prospective_advantage_claim', 'automatic_promotion')), 'unsupported publication claim')
    return data
