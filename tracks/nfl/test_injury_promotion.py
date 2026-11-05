from dataclasses import replace
import unittest
from injury_promotion import Source, Experiment, source_status, promotion_status, demo

class SourceEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.s = Source('2026-01-01T00:00:00Z', '2023-09-10T14:00:00Z', 2023, 2023, True, True)
        self.cutoff = '2023-09-10T16:00:00Z'
    def test_later_acquisition_does_not_erase_real_publication(self):
        self.assertEqual(source_status(self.s, self.cutoff, historical=True), 'ELIGIBLE_AT_CUTOFF')
    def test_current_observation_cannot_backdate_a_source(self):
        self.assertEqual(source_status(self.s, self.cutoff, historical=False), 'AFTER_CUTOFF')
    def test_missing_historical_publication_cannot_use_download_time(self):
        self.assertEqual(source_status(replace(self.s, published_at=None), self.cutoff, historical=True), 'HISTORICAL_AVAILABILITY_UNVERIFIED')
    def test_cutoff_is_inclusive_without_future_admission(self):
        for t, status in [('2023-09-10T16:00:00Z','ELIGIBLE_AT_CUTOFF'),('2023-09-10T16:00:01Z','AFTER_CUTOFF')]:
            self.assertEqual(source_status(replace(self.s,published_at=t),self.cutoff,historical=True),status)
    def test_current_roster_does_not_establish_health(self):
        self.assertEqual(source_status(replace(self.s,current_roster_only=True),self.cutoff,historical=True),'CONTEXT_ONLY_ROSTER_IS_NOT_INJURY_STATUS')
    def test_vintage_and_identity_required(self):
        for changes in ({'report_season':None},{'report_season':2022},{'player_identity_verified':False},{'content_replayed':False}):
            self.assertNotEqual(source_status(replace(self.s,**changes),self.cutoff,historical=True),'ELIGIBLE_AT_CUTOFF')
    def test_clock_conflicts_and_naive_clocks_rejected(self):
        self.assertEqual(source_status(replace(self.s,observed_at='2022-01-01T00:00:00Z'),self.cutoff,historical=True),'PUBLICATION_AFTER_OBSERVATION_CONFLICT')
        with self.assertRaises(ValueError):source_status(self.s,'2023-09-10T16:00:00',historical=True)

class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.e=Experiment('winner',('a','b'),('b','a'),('2022-01-01T00:00:00Z',),'2024-01-01T00:00:00Z',True,True,'2022-01-01T00:00:00Z','2023-01-01T00:00:00Z',(-.03,-.01),True,True)
    def test_matched_reordered_events_do_not_change_result(self):
        self.assertTrue(promotion_status(self.e).startswith('DEMO_PROMOTION_ELIGIBLE'))
    def test_mismatched_and_duplicate_cohorts_fail(self):
        for c in [('a','c'),('a','a'),()]:self.assertEqual(promotion_status(replace(self.e,candidate_events=c)),'BLOCKED_UNMATCHED_OR_DUPLICATE_EVENTS')
    def test_exposed_selection_labels_block_promotion(self):
        for labels in [(),('2024-01-01T00:00:00Z',),('2026-01-01T00:00:00Z',)]:
            self.assertEqual(promotion_status(replace(self.e,selection_label_times=labels)),'BLOCKED_SELECTION_LABEL_AVAILABILITY')
    def test_own_or_future_labels_block_fold(self):
        for t in ['2023-01-01T00:00:00Z','2023-01-02T00:00:00Z']:
            self.assertEqual(promotion_status(replace(self.e,max_fold_training_label_at=t)),'BLOCKED_FOLD_LABEL_LEAKAGE')
    def test_model_identity_and_recipe_freeze_required(self):
        for flag in ['frozen_before_evaluation','native_models_authenticated']:
            self.assertEqual(promotion_status(replace(self.e,**{flag:False})),'BLOCKED_RECIPE_OR_MODEL_IDENTITY')
    def test_crossing_zero_is_not_an_established_gain(self):
        for interval in [(-.03,.01),(-.03,0),(0,.03)]:
            self.assertEqual(promotion_status(replace(self.e,paired_improvement_interval=interval)),'RESEARCH_ONLY_IMPROVEMENT_NOT_ESTABLISHED')
    def test_missing_uncertainty_does_not_promote(self):
        self.assertEqual(promotion_status(replace(self.e,paired_improvement_interval=None)),'RESEARCH_ONLY_UNCERTAINTY_UNAVAILABLE')
    def test_current_inputs_and_acceptance_remain_separate(self):
        self.assertEqual(promotion_status(replace(self.e,current_input_coverage_verified=False)),'RESEARCH_ONLY_CURRENT_INPUTS_INCOMPLETE')
        self.assertEqual(promotion_status(replace(self.e,registered_acceptance_passed=False)),'RESEARCH_ONLY_ACCEPTANCE_PENDING')
    def test_nan_and_reversed_intervals_rejected(self):
        for interval in [(float('nan'),-.01),(-.01,-.03),(True,False)]:
            with self.assertRaises(ValueError):promotion_status(replace(self.e,paired_improvement_interval=interval))
    def test_demo_never_claims_owner_work(self):
        self.assertTrue(demo()['no_owner_research_or_promotion_performed'])
if __name__=='__main__':unittest.main()
