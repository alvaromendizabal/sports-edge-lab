"""Dependency-free guards for sanitized B062 aggregate evidence.

The constants below were independently read from authenticated predecessor
aggregate reports. Invented mutations test refusal of misleading publication.
No owner package, model, source provider, credentials, or network is required.
"""
import copy
import json
import math
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
EXPECTED_CURRENT = {
    'ncaam': (415, 337, 0.39480662720368886, 0.12688327066747543),
    'ncaaw': (399, 340, 0.318015307605635, 0.10017893982274186),
}
EXPECTED_ISSUED = {
    'ncaam': (16, 16, 0.17669122487255026, 0.041296552412613444),
    'ncaaw': (14, 10, 0.44518998446140173, 0.15962258566262202),
}
EXPECTED_HISTORICAL = {
    ('ncaam', 2025): (5758, 0.5214815135867005, 8.979033825234044, 12.929473421062825),
    ('ncaam', 2026): (5749, 0.5238873160433043, 9.162618730992724, 13.687858425800115),
    ('ncaaw', 2025): (5280, 0.45211932742946104, 9.691400394381871, 12.57927939843677),
    ('ncaaw', 2026): (5621, 0.45473728543321623, 9.671339695146882, 12.597916463977597),
}
METRIC_ROLES = {
    'winner_accuracy', 'probability_log_loss', 'probability_brier',
    'margin_mae', 'margin_rmse', 'total_mae', 'total_rmse',
}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def close(left, right):
    return isinstance(left, (int, float)) and math.isfinite(left) and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def validate_evidence(document):
    require(document['schema'] == 'sel.ncaa.public.b062.evidence.v1', 'SCHEMA')
    require(document['project'] == 'ncaa_basketball' and document['release'] == 'B062', 'TRACK')
    require(set(document['scope']) == {'ncaam', 'ncaaw'}, 'LEAGUES')
    preparation = document['preparation']
    require(all(preparation[name] == 0 for name in ('new_owner_fits', 'new_issued_forecasts', 'new_promotions')), 'PREPARED_RESULT_IS_NOT_NEW_SCIENCE')
    require(all(preparation[name] is False for name in ('owner_execution_performed', 'aws_speedup_measured', 'source_qualification_upgraded', 'original_issued_values_modified')), 'PREPARATION_BOUNDARY')
    owner = document['actual_owner']
    require(owner['release'] == 'B060' and owner['status'] == 'RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED', 'ACTUAL_OWNER')
    require(close(owner['elapsed_seconds'], 8101.620773345003), 'OWNER_ELAPSED')
    require(close(owner['accounted_cpu_seconds'], 5043.558846), 'CPU_ACCOUNTING')
    require(close(owner['average_accounted_cpu_cores'], owner['accounted_cpu_seconds'] / owner['process_usage_wall_seconds']), 'CPU_RATE')
    require(owner['requested_max_cores'] == 12 and owner['twelve_concurrent_fits_observed'] is False, 'CAP_IS_NOT_MEASURED_CONCURRENCY')
    require(owner['complete_new_physical_fit_count'] is None, 'UNKNOWN_FIT_COUNT')
    require(owner['verified_fit_lower_bounds'] == {'target_estimator': 9, 'scalar_calibration': 3, 'empirical_residual': 6}, 'FIT_LOWER_BOUNDS')
    require(owner['reused_historical_target_fits'] == 108, 'REUSED_FITS')
    failure = document['b061_launch_failure']
    require(failure['boundary'] == 'BEFORE_ARCHIVE_CODE' and failure['observed_shell_exit'] == 1, 'LAUNCH_BOUNDARY')
    require(failure['owner_entrypoint_started'] is False and failure['model_fits_started'] == 0, 'LAUNCH_DID_NOT_FIT')
    require(failure['local_file_observed_pin'] is None and failure['local_file_cause_determined'] is False, 'UNKNOWN_LOCAL_FILE_CAUSE')
    current = document['current_frozen_reference']
    issued = document['preserved_issues']
    require(current['mode'] == 'EXPOSED_RETROSPECTIVE_RECONSTRUCTION' and current['original_issue_credit'] == 0, 'REPLAY_IS_NOT_ISSUED')
    require(issued['mode'] == 'ORIGINAL_ISSUES_WITH_LATER_OBSERVED_LABELS', 'ISSUED_MODE')
    for section, expected in ((current, EXPECTED_CURRENT), (issued, EXPECTED_ISSUED)):
        require({row['league'] for row in section['rows']} == set(expected) and len(section['rows']) == 2, 'ROW_LEAGUES')
        require(section['independent_official_finals_verified'] is False, 'FINAL_LABEL_QUALIFICATION')
        for row in section['rows']:
            games, correct, loss, brier = expected[row['league']]
            require((row['games'], row['correct_winners']) == (games, correct), 'COHORT_COUNTS')
            require(close(row['accuracy'], correct / games), 'WINNER_ACCURACY')
            require(close(row['log_loss'], loss) and close(row['brier'], brier), 'PRESERVED_METRICS')
            require(0 <= row['brier'] <= 1 and row['log_loss'] >= 0, 'PROBABILITY_METRIC_BOUNDS')
            for target in ('margin', 'total'):
                require(0 <= row[target]['mae'] <= row[target]['rmse'], 'POINT_METRIC_ORDER')
    require(current['completed_games'] == sum(row['games'] for row in current['rows']) == 814, 'REPLAY_DENOMINATOR')
    require(issued['scored_games'] == sum(row['games'] for row in issued['rows']) == 30, 'ISSUED_DENOMINATOR')
    require(issued['preserved_games'] == issued['scored_games'] + issued['unscored_games'] == 32, 'UNSCORED_CLOSURE')
    require(issued['preserved_target_outputs'] == 3 * issued['preserved_games'] == 96, 'ISSUED_TARGET_COUNT')
    require(issued['scored_target_outputs'] == 3 * issued['scored_games'] == 90, 'SCORED_TARGET_COUNT')
    historical = document['historical_leaders']
    require(historical['mode'] == 'EXPOSED_COMPLETED_SEASON_RESEARCH', 'HISTORICAL_EXPOSURE')
    require(historical['paired_cohorts_reverified_from_aggregates'] is False and historical['same_model_across_metric_columns'] is False, 'AGGREGATES_ARE_NOT_PAIRED_ROW_PROOF')
    require(len(historical['rows']) == 4, 'HISTORICAL_PARTITIONS')
    require({(row['league'], row['season_end_year']) for row in historical['rows']} == set(EXPECTED_HISTORICAL), 'HISTORICAL_SEASONS')
    for row in historical['rows']:
        games, loss, margin, total = EXPECTED_HISTORICAL[row['league'], row['season_end_year']]
        require(row['games'] == games and close(row['log_loss'], loss) and close(row['margin_mae'], margin) and close(row['total_mae'], total), 'HISTORICAL_METRICS')
    roles = document['metric_role_extension']
    require(set(roles['metrics_per_league']) == METRIC_ROLES and len(roles['metrics_per_league']) == 7, 'ROLE_SET')
    require(roles['registered_role_count'] == roles['league_count'] * len(METRIC_ROLES) == 14, 'ROLE_COUNT')
    require(roles['promotion_authority'] is False and roles['full_historical_row_selection_executed'] is False and roles['current_season_outcomes_select_roles'] is False, 'ROLE_PREPARATION_NOT_PROMOTION')
    inventory = document['source_inventory']
    require(inventory['unit'] == 'SOURCE_RECORDS_NOT_CERTIFIED_UNIQUE_GAMES' and inventory['certified_complete_season_denominator'] is False, 'SOURCE_RECORDS_ARE_NOT_COMPLETE_GAMES')
    require(inventory['observed_records'] == inventory['normalized_espn_records'] + inventory['unmatched_official_candidates'] + inventory['unresolved_candidates'] == 3457, 'SOURCE_DENOMINATOR')
    require(inventory['normalized_observed_completed_records'] == 1165 and inventory['original_reference_scored_games'] == 814, 'COVERAGE_GAP')
    previews = document['unissued_previews']
    require(previews['games'] == 1139 and previews['public_prediction_values'] is None and previews['original_issue_credit'] == 0, 'UNISSUED_VALUES_STAY_NULL')
    market = document['market_comparisons']
    require(market['kalshi']['qualified_current_season_result'] is None, 'NO_QUALIFIED_KALSHI_RESULT')
    require(market['historical_matched_provider'] == 'polymarket_international' and market['historical_matched_games'] == 265, 'MARKET_PRODUCT_IDENTITY')
    require(market['historical_market_comparison_is_new_b062_result'] is False and market['historical_tick_histories_complete'] is False and market['r13_r20_new_real_data_findings'] == 0, 'MARKET_SOURCE_GAPS')
    require(all(value is False for value in document['publication_boundary'].values()), 'PUBLIC_PRIVATE_BOUNDARY')
    text = json.dumps(document, sort_keys=True)
    require(not re.search(r'arn:aws:|s3://|/workspace/|/home/|sagemaker-sports-edge-lab-|[?&](?:token|sig|credential)=', text, re.I), 'PRIVATE_LOCATION_OR_CREDENTIAL')
    return True


def validate_publication_pin(document):
    value = document['canonical_source']
    require(type(value['bytes']) is int and value['bytes'] > 0, 'CANONICAL_BYTES_UNRESOLVED')
    require(isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None and value['sha256'] != '0' * 64, 'CANONICAL_SHA256_UNRESOLVED')
    require(value['status'] == 'FINAL_VALIDATED_SOURCE', 'CANONICAL_VALIDATION_PENDING')
    return True


class B062PublicEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / 'B062_STATUS.json').read_text())

    def test_saved_aggregate_numeric_and_denominator_closure(self):
        self.assertTrue(validate_evidence(self.document))

    def test_canonical_source_pin_is_bound_before_publication(self):
        self.assertTrue(validate_publication_pin(self.document))

    def rejects(self, edit, reason):
        changed = copy.deepcopy(self.document)
        edit(changed)
        with self.assertRaisesRegex(ValueError, reason):
            validate_evidence(changed)

    def test_prepared_code_cannot_claim_new_fits(self):
        self.rejects(lambda d: d['preparation'].update(new_owner_fits=1), 'PREPARED_RESULT')

    def test_failed_preflight_cannot_claim_owner_entry(self):
        self.rejects(lambda d: d['b061_launch_failure'].update(owner_entrypoint_started=True), 'LAUNCH_DID_NOT_FIT')

    def test_replay_cannot_receive_original_issue_credit(self):
        self.rejects(lambda d: d['current_frozen_reference'].update(original_issue_credit=814), 'REPLAY_IS_NOT_ISSUED')

    def test_twelve_core_ceiling_cannot_be_measured_utilization(self):
        self.rejects(lambda d: d['actual_owner'].update(average_accounted_cpu_cores=12), 'CPU_RATE')

    def test_wrong_winner_accuracy_is_rejected(self):
        self.rejects(lambda d: d['current_frozen_reference']['rows'][0].update(accuracy=0.9), 'WINNER_ACCURACY')

    def test_source_record_denominator_must_close(self):
        self.rejects(lambda d: d['source_inventory'].update(normalized_espn_records=3457), 'SOURCE_DENOMINATOR')

    def test_source_records_cannot_be_certified_as_unique_games(self):
        self.rejects(lambda d: d['source_inventory'].update(certified_complete_season_denominator=True), 'SOURCE_RECORDS')

    def test_unscored_issues_cannot_silently_disappear(self):
        self.rejects(lambda d: d['preserved_issues'].update(unscored_games=0), 'UNSCORED_CLOSURE')

    def test_fourteen_roles_are_not_fourteen_promotions(self):
        self.rejects(lambda d: d['metric_role_extension'].update(promotion_authority=True), 'ROLE_PREPARATION')

    def test_role_count_matches_both_leagues(self):
        self.rejects(lambda d: d['metric_role_extension'].update(registered_role_count=28), 'ROLE_COUNT')

    def test_unissued_values_cannot_be_zero_filled(self):
        self.rejects(lambda d: d['unissued_previews'].update(public_prediction_values=0), 'UNISSUED_VALUES')

    def test_absent_kalshi_benchmark_remains_null(self):
        self.rejects(lambda d: d['market_comparisons']['kalshi'].update(qualified_current_season_result=0.4), 'NO_QUALIFIED_KALSHI')

    def test_historical_metric_mutation_is_rejected(self):
        self.rejects(lambda d: d['historical_leaders']['rows'][0].update(log_loss=0.4), 'HISTORICAL_METRICS')

    def test_private_cloud_location_cannot_enter_export(self):
        self.rejects(lambda d: d['evidence_sources'].append('s3://' + 'invented-private-location'), 'PRIVATE_LOCATION')

    def test_unresolved_release_pin_is_rejected(self):
        changed = copy.deepcopy(self.document)
        changed['canonical_source'] = {'bytes': None, 'sha256': None, 'status': 'PENDING'}
        with self.assertRaisesRegex(ValueError, 'UNRESOLVED'):
            validate_publication_pin(changed)


if __name__ == '__main__':
    unittest.main()
