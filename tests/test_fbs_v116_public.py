"""Custody and time-boundary checks for retained science and fresh diagnostics."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fbs_v116_review', ROOT / 'examples/fbs_contracts/v116/build_review.py')
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class SelectedReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(review.DATA.read_text())

    def reject(self, mutation, message):
        data = copy.deepcopy(self.data)
        mutation(data)
        with self.assertRaisesRegex(ValueError, message):
            review.validate(data)

    def test_deterministic_page_preserves_embedded_data(self):
        output = review.OUTPUT.read_bytes()
        self.assertEqual(review.render(self.data), output)
        payload = re.search(r'<script id="fbs-evidence" type="application/json">(.*?)</script>', output.decode(), re.S).group(1)
        self.assertEqual(json.loads(payload), self.data)
        self.assertIn(hashlib.sha256(payload.encode()).hexdigest(), output.decode())

    def test_entire_previous_fbs_readme_is_preserved(self):
        raw = (ROOT / 'docs/fbs/README.md').read_bytes()
        if raw.startswith(b'<!-- FBS_V120_SPREAD_TOTALS_START -->\n'):
            self.assertEqual(raw.count(b'<!-- FBS_V120_SPREAD_TOTALS_END -->\n\n'), 1)
            raw = raw.split(b'<!-- FBS_V120_SPREAD_TOTALS_END -->\n\n', 1)[1]
        if raw.startswith(b'<!-- FBS_V119_SPREAD_TOTALS_START -->\n'):
            self.assertEqual(raw.count(b'<!-- FBS_V119_SPREAD_TOTALS_END -->\n\n'), 1)
            raw = raw.split(b'<!-- FBS_V119_SPREAD_TOTALS_END -->\n\n', 1)[1]
        if raw.startswith(b'<!-- FBS_V117_SPREAD_TOTALS_START -->\n'):
            self.assertEqual(raw.count(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n'), 1)
            raw = raw.split(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n', 1)[1]
        start = b'<!-- FBS_V116_SELECTED_REVIEW_START -->\n'
        end = b'<!-- FBS_V116_SELECTED_REVIEW_END -->\n\n'
        self.assertTrue(raw.startswith(start))
        self.assertEqual(raw.count(start), 1)
        self.assertEqual(raw.count(end), 1)
        prior = raw.split(end, 1)[1]
        self.assertEqual(len(prior), 81196)
        self.assertEqual(hashlib.sha256(prior).hexdigest(), 'c49621248c2abd38606469a98c57cf895a1e9a6af8c12fa104db8d6a39c8e9fb')

    def test_failure_and_no_new_science_cannot_be_reclassified(self):
        self.reject(lambda d: d['execution'].update(owner_executions_successful=1), 'Failed owner execution')
        self.reject(lambda d: d['execution'].update(new_model_fits=1), 'unearned new science')
        self.reject(lambda d: d['execution'].update(new_current_census_calls=2), 'unearned new science')
        self.reject(lambda d: d['execution'].update(scientific_occupancy_measured=True), 'CPU and cost')

    def test_return_integrity_and_invoice_scope_are_explicit(self):
        self.reject(lambda d: d['execution'].update(return_sha256='0'*64), 'return identity')
        self.reject(lambda d: d['execution'].update(estimate_is_invoice=True), 'CPU and cost')

    def test_selection_boundary_cannot_use_test_or_reweight_training(self):
        self.reject(lambda d: d['selection'].update(test_used_for_selection=True), 'Scientific boundaries')
        self.reject(lambda d: d['selection'].update(training_season_reweighting=True), 'Scientific boundaries')
        self.reject(lambda d: d['selection'].update(ratio_changes_refit_estimators=True), 'Scientific boundaries')
        self.reject(lambda d: d['selection'].update(test_previously_exposed=False), 'prior exposure')

    def test_annual_metrics_do_not_inherit_new_census_denominators(self):
        self.reject(lambda d: d['metrics'][0]['annual'][2].update(scored_n=824, expected_n=824), 'Dated metric populations')
        self.reject(lambda d: d['metrics'][0].update(selection_score=0), 'primary mean')

    def test_all_games_and_missing_policy_cells_are_retained(self):
        self.assertEqual(self.data['snapshot']['weekly_games'], 69)
        self.assertEqual(self.data['snapshot']['weekly_missing_policy_games'], 14)
        self.assertEqual(self.data['snapshot']['game_count'], 895)
        self.reject(lambda d: d['games'].pop(), 'Unshrunk game populations')
        self.reject(lambda d: d['games'][0]['selected'].pop('P08'), 'Unexpected public fields')

    def test_missingness_cannot_be_imputed_for_public_display(self):
        missing = next(i for i, game in enumerate(self.data['games']) if game['covered_policies'] == 0)
        self.reject(lambda d: d['games'][missing]['selected']['P08'].update(value=0.5), 'Missing values stay null')

    def test_source_flags_and_original_issuance_are_not_inferred(self):
        available = next(i for i, game in enumerate(self.data['games']) if game['covered_policies'] == 8)
        self.reject(lambda d: d['games'][available]['selected']['P08'].update(original_issued=True), 'issue credit')
        pending = next(i for i, game in enumerate(self.data['games']) if not game['completed_at_snapshot'] and game['covered_policies'] == 8)
        self.assertIsNone(self.data['games'][pending]['selected']['P08']['prior_fallback'])
        self.assertTrue(self.data['games'][pending]['selected']['P05']['prior_fallback'])
        self.reject(lambda d: d['games'][pending]['selected']['P05'].update(all_market_sources_absent=False), 'source absence')

    def test_no_fabricated_current_exchange_or_bookmaker_prices(self):
        self.reject(lambda d: d['providers'].update(current_week_qualified_quotes=1), 'fabricated current quotes')
        index = next(i for i, row in enumerate(self.data['providers']['rows']) if row['provider'] == 'kalshi')
        self.reject(lambda d: d['providers']['rows'][index].update(paired_n=1, missing_n=918), 'exchange qualification gaps')

    def test_current_census_does_not_overwrite_retained_science(self):
        current=self.data.get('current_diagnostic')
        if current is None:self.skipTest('No separate fresh diagnostic attached')
        self.assertEqual(current['game_count'],895)
        self.assertEqual(current['completed_games'],824)
        self.assertEqual(self.data['snapshot']['completed_games'],822)
        self.reject(lambda d:d['current_diagnostic'].update(new_model_fits=1),'Frozen inference')
        self.reject(lambda d:d['current_diagnostic'].update(historical_metrics_recomputed=True),'Diagnostic boundaries')
        self.reject(lambda d:d['current_diagnostic']['games'].pop(),'Fresh full policy population')

    def test_current_market_qualification_is_measured_per_provider_and_horizon(self):
        current=self.data.get('current_diagnostic')
        if current is None:self.skipTest('No separate fresh diagnostic attached')
        self.assertEqual(current['all_bookmaker_observed_rows'],11916)
        self.assertEqual(current['all_bookmaker_qualified_rows'],11916)
        self.assertEqual(current['all_bookmaker_labels'],83)
        self.assertEqual(len(current['market_rows']),598)
        self.reject(lambda d:d['current_diagnostic']['market_rows'][0].update(strict_t60_model_input_qualified=True),'never become T60')
        self.reject(lambda d:d['current_diagnostic']['market_coverage'][0].update(qualified_rows=0),'coverage totals')

    def test_fresh_outputs_remain_unissued_and_cannot_fill_unavailable_cells(self):
        current=self.data.get('current_diagnostic')
        if current is None:self.skipTest('No separate fresh diagnostic attached')
        self.reject(lambda d:d['current_diagnostic']['games'][0]['selected']['P01'].update(original_issued=True),'no issue credit')
        self.assertEqual(current['current_census_calls'],4)
        self.assertEqual(current['market_source_calls'],2)
        self.assertEqual(current['paid_market_calls'],1)
        self.assertEqual(current['paid_market_credits'],30)

    def test_new_824_game_diagnostic_preserves_old_822_cards_and_selection(self):
        scored=self.data.get('current_test_diagnostic')
        if scored is None:self.skipTest('No separate completed-game diagnostic attached')
        self.assertEqual(scored['completed_games'],824)
        self.assertEqual(scored['scored_policy_game_rows'],6592)
        self.assertEqual(scored['distribution_scored_policy_game_rows'],1648)
        self.assertEqual(scored['upcoming_preview_rows_excluded'],568)
        self.assertEqual(len(scored['objectives']),9)
        self.assertTrue(all(r['annual'][2]['scored_n']==822 for r in self.data['metrics']))
        self.reject(lambda d:d['current_test_diagnostic'].update(new_selection=True),'cannot select or overwrite')
        self.reject(lambda d:d['current_test_diagnostic']['objectives'][0].update(expected_n=822),'new test denominators')

    def test_private_fields_and_private_addresses_are_excluded(self):
        self.reject(lambda d: d['policies']['P01'].update(active_transform={'coefficient': 1}), 'Unexpected public fields')
        self.reject(lambda d: d['policies']['P01'].update(features='s3://private-owner-evidence/raw.json'), 'Private or out-of-scope')

    def test_render_is_self_contained_and_does_not_publish(self):
        html = review.OUTPUT.read_text()
        self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="https?://')
        self.assertIn('PREPARED_SOURCE_NOT_PUBLISHED', html)
        self.reject(lambda d: d['publication'].update(owner_run_started_by_page=True), 'cannot execute or promote')
        self.reject(lambda d: d['publication'].update(production_model_promoted=True), 'cannot execute or promote')


if __name__ == '__main__':
    unittest.main(verbosity=2)
