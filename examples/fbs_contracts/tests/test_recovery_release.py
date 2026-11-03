import copy
import json
import unittest
from examples.fbs_contracts.build_recovery_review import DATA,OUTPUT,fixtures,render,validate

class RecoveryReleaseTests(unittest.TestCase):
    def setUp(self):self.data=json.loads(DATA.read_text())
    def test_page_is_generated_from_complete_evidence_and_demo(self):self.assertEqual(OUTPUT.read_text(),render())
    def test_public_provider_scope_is_exact_and_weekly_population_complete(self):
        data=validate(self.data)
        self.assertEqual([r['provider'] for r in data['active_provider_coverage']],['DraftKings','Kalshi','Polymarket'])
        self.assertEqual(sum(r['games'] for r in data['original_replay_2026']['weekly']),622)
        self.assertEqual(sum(r['correct_winner'] for r in data['original_replay_2026']['weekly']),465)
    def test_private_or_unknown_nested_field_rejected(self):
        self.data['owner_attempt']['private_model_body']={'invented':1}
        with self.assertRaisesRegex(ValueError,'Unknown public field'):validate(self.data)
    def test_missing_or_duplicate_week_rejected(self):
        self.data['original_replay_2026']['weekly'][1]=copy.deepcopy(self.data['original_replay_2026']['weekly'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):validate(self.data)
    def test_game_market_and_prop_denominators_not_combined(self):
        self.data['source_snapshot']['game_market_rows']+=18
        with self.assertRaisesRegex(ValueError,'denominator'):validate(self.data)
    def test_partial_execution_cannot_publish_complete_new_performance(self):
        self.data['owner_attempt']['new_complete_performance_comparison']=True
        with self.assertRaisesRegex(ValueError,'Partial owner'):validate(self.data)
    def test_future_capture_clock_rejected(self):
        self.data['source_snapshot']['capture_end']='2026-12-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'capture clock'):validate(self.data)
    def test_matched_panels_keep_exact_same_denominators_and_active_scope(self):
        panels=validate(self.data)['historical_matched_comparisons']['panels']
        self.assertEqual([p['n'] for p in panels],[192,199,199])
        self.assertEqual(panels[0]['model']['correct'],132)
        self.assertEqual(panels[0]['provider_metrics']['correct'],136)
        self.data['historical_matched_comparisons']['panels'][0]['provider_metrics']['games']=191
        with self.assertRaisesRegex(ValueError,'denominator'):validate(self.data)
    def test_historical_panel_cannot_become_live_or_add_unsupported_provider(self):
        self.data['historical_matched_comparisons']['live_execution_qualified']=True
        with self.assertRaisesRegex(ValueError,'qualification'):validate(self.data)
        self.data['historical_matched_comparisons']['live_execution_qualified']=False
        self.data['historical_matched_comparisons']['panels'][0]['provider']='Invented fourth provider'
        with self.assertRaisesRegex(ValueError,'Unsupported matched provider'):validate(self.data)
    def test_independent_certificate_changes_decision_without_rewriting_solver_flag(self):
        cases=fixtures();bad,good,infeasible=[r['certificate'] for r in cases]
        self.assertTrue(bad['solver_reported_success']);self.assertFalse(bad['numerically_certified'])
        self.assertFalse(good['solver_reported_success']);self.assertTrue(good['numerically_certified'])
        self.assertGreater(infeasible['primal_violation'],0);self.assertIsNone(infeasible['convex_suboptimality_upper_bound'])

if __name__=='__main__':unittest.main()
