"""A new source observation cannot silently change historical evaluation."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from source_review_n038 import validate_source_review

HERE=Path(__file__).resolve().parent
class SourceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((HERE/'source_review_n038.json').read_text())
        cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
    def test_both_providers_have_all_current_finals_and_targets(self):
        result=validate_source_review(self.data,self.coverage)
        self.assertEqual(result['source_n038_current_winner_references'],242)
        self.assertEqual(result['source_n038_current_point_references'],484)
        self.assertEqual(result['source_n038_metric_changes'],0)
    def test_old_forecasts_and_metrics_are_not_mutated(self):
        before=deepcopy(self.coverage);validate_source_review(self.data,self.coverage)
        self.assertEqual(before,self.coverage)
    def test_reject_postkickoff_quote(self):
        data=deepcopy(self.data);row=data['winner_rows'][0]
        row['quote_at']=row['acquired_at']
        with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_missing_and_duplicate_cells_are_rejected(self):
        for mutate in [lambda d:d['winner_rows'].pop(),lambda d:d['point_rows'].append(deepcopy(d['point_rows'][0]))]:
            data=deepcopy(self.data);mutate(data)
            with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_cannot_promote_later_quote_into_earlier_cutoff_or_metric(self):
        for field,value in [('horizon','T1'),('metric_eligible',True),('execution_qualified',True)]:
            data=deepcopy(self.data);data['winner_rows'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_threshold_cannot_become_mean_score(self):
        data=deepcopy(self.data);data['point_rows'][0]['point_estimate']=3.5
        with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_private_fields_rejected(self):
        data=deepcopy(self.data);data['point_rows'][0]['raw_source']={'key':'private'}
        with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_no_claim_that_absent_draftkings_export_means_no_history(self):
        data=deepcopy(self.data)
        next(r for r in data['historical_coverage'] if r['provider']=='DraftKings')['status']='NO_HISTORY'
        with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_fresh_draftkings_gap_cannot_be_filled_by_older_capture(self):
        data=deepcopy(self.data)
        next(r for r in data['week9_coverage'] if r['provider']=='DraftKings')['covered_games']=15
        with self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_draftkings_recovery_keeps_original_clocks(self):
        row=next(r for r in self.data['draftkings_week9'] if r['game_id']=='2026_09_LV_SF')
        self.assertEqual(row['normalization_role'],'DOCUMENTED_KICKOFF_REVISION_RECOVERY')
        self.assertEqual(row['quote_at'],'2026-11-04T17:31:26+00:00')
        self.assertEqual(row['acquired_at'],'2026-11-04T17:32:23+00:00')
    def test_draftkings_point_orientation_and_recovery_identity_rejected(self):
        for field,value in [('home_margin_line_reference',-10),('normalization_role','DIRECT_EVENT_JOIN'),('quote_at','2026-11-09T00:00:00+00:00')]:
            data=deepcopy(self.data);row=next(r for r in data['draftkings_week9'] if r['game_id']=='2026_09_LV_SF');row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_source_review(data,self.coverage)
    def test_current_sources_have_separate_observation_clocks(self):
        self.assertEqual(len(self.data['current_winner_rows']),30)
        self.assertEqual(len(self.data['current_point_rows']),60)
        self.assertTrue(all(r['quote_at'] is None for r in self.data['current_point_rows'] if r['provider']=='Kalshi'))
    def test_current_source_guard_rejects_missing_cells_bad_clocks_and_mean_score(self):
        for mutate in [lambda d:d['current_winner_rows'].pop(),lambda d:d['current_point_rows'][0].update(point_estimate=3.5),lambda d:d['current_point_rows'][0].update(acquired_at='2027-01-01T00:00:00Z'),lambda d:d['current_point_rows'][0].update(metric_eligible=True),lambda d:d['current_point_rows'][0].update(parsed_contract_count=9999)]:
            d=deepcopy(self.data);mutate(d)
            with self.assertRaises(ValueError):validate_source_review(d,self.coverage)
    def test_wrong_return_and_research_promotion_rejected(self):
        for field,value in [('owner_return_sha256','0'*64),('owner_pipeline_accepted',True),('historical_metrics_changed',True),('model_forecasts_changed',True)]:
            data=deepcopy(self.data);data[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_source_review(data,self.coverage)
if __name__=='__main__':unittest.main()
