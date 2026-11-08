"""Protect actual N056 accounting, dated results and complete NFL projections."""
import copy,json,unittest
from build_season_review_n054 import load
from actual_n055_n056 import enrich as prior_enrich
from actual_n056_n057 import enrich,validate_active_status,load_overlay,validate_overlay,instant,ISSUE_KEYS
from publication_audit_n057 import audit

class ActualN056Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=prior_enrich(load());cls.data=enrich(cls.original);cls.overlay=validate_overlay(load_overlay())
 def test_original_scientific_arrays_remain_unchanged(self):
  d=self.data;o=self.original
  self.assertEqual(d['model_rows'][:len(o['model_rows'])],o['model_rows']);self.assertEqual(d['provider_rows'][:len(o['provider_rows'])],o['provider_rows'])
  self.assertEqual(d['all_model_metrics'][:len(o['all_model_metrics'])],o['all_model_metrics'])
  for k in ['n055_family_per_game','n055_family_season_metrics','n055_family_weekly_metrics','n055_family_comparisons','raw_per_game','scale_per_game','n054_market_per_game','n054_owner_raw_issues','n054_owner_component_issues','n055_owner_component_issues']:
   self.assertEqual(d[k],o[k],k)
 def test_new_issue_types_native_states_and_reuse_are_separate(self):
  d=self.data;s=d['n056_actual_results'];self.assertEqual(sum(len(d['n056_'+k]) for k in ISSUE_KEYS),2683);self.assertEqual(s['top_level_new_forecasts'],2683)
  self.assertEqual(s['new_native_fits'],21);self.assertEqual(s['native_current_origin_states'],7);self.assertEqual(s['native_retrospective_states'],14);self.assertEqual(s['new_meta_fits'],0)
  self.assertEqual(sum(s['family_native_counts'].values()),21);self.assertEqual(len(d['n056_family_current_job_ledger']),21)
  self.assertEqual(s['synthetic_smoke_fits'],18);self.assertEqual(s['synthetic_nfl_scientific_fit_credit'],0);self.assertFalse(s['owner_research_acceptance']);self.assertTrue(s['full_durable_evidence_closure'])
  self.assertEqual(s['repeated_raw_fits'],0);self.assertEqual(s['repeated_designation_cells'],0);self.assertEqual(s['repeated_injury_cells'],0);self.assertEqual(s['repeated_correction_states'],0);self.assertFalse(s['six_controls_changed'])
 def test_owner_and_official_display_schedule_are_dated_separately(self):
  d=self.data;self.assertEqual(len(d['games']),272);self.assertEqual(sum(g['completed'] for g in d['games']),123)
  self.assertEqual(d['owner_n056_schedule_snapshot']['completed'],122);self.assertEqual(d['display_schedule_snapshot']['remaining'],149)
  previous={g['game_id']:g for g in self.original['games']};changed=[g['game_id'] for g in d['games'] if g!=previous[g['game_id']]];self.assertEqual(changed,['2026_09_CIN_ATL'])
  g=next(g for g in d['games'] if g['game_id']=='2026_09_CIN_ATL');self.assertEqual(g['actual']['home_margin'],-17);self.assertEqual(g['actual']['total'],51)
 def test_default_view_is_complete_without_an_extra_model(self):
  d=self.data;self.assertEqual(len(d['lanes']),113);self.assertEqual(len(d['model_rows']),272*113*3);self.assertEqual(len(d['provider_rows']),272*9*len(d['provider_horizons']))
  self.assertEqual(len(d['default_review_selection']),272);self.assertNotIn(d['default_view_id'],{x['id'] for x in d['lanes']})
  index={(x['game_id'],x['lane_id'],x['target']):x for x in d['model_rows']}
  for route in d['default_review_selection']:
   self.assertFalse(route['new_issue_credit']);self.assertFalse(route['new_model_credit'])
   for target in ['margin','total']:self.assertTrue(index[route['game_id'],route['lane_id'],target]['available'])
 def test_supplement_and_prospective_metrics_do_not_replace_the_original(self):
  d=self.data;self.assertEqual(len(d['n056_retrospective_supplement']),6);self.assertEqual({x['game_id'] for x in d['n056_retrospective_supplement']},{'2026_08_CHI_SEA','2026_09_JAX_BAL'})
  self.assertFalse(any(x.get('new_issue_credit') for x in d['n056_retrospective_supplement']))
  self.assertEqual({x['games'] for x in d['n056_retrospective_metrics']},{2});self.assertEqual({x['games'] for x in d['n056_prospective_metrics']},{1});self.assertEqual(len(d['all_model_metrics']),1064)
  self.assertEqual({x['games'] for x in d['n055_family_season_metrics'] if x['season']==2026 and x['policy']=='selected_per_event_rolling' and x['target']=='win'},{119})
  self.assertFalse(d['n056_prospective_review']['rounded_public_values_used_for_scores'])
 def test_actual_future_issue_clock_qualification(self):
  d=self.data;family=d['n056_owner_family_issues'];self.assertEqual(len(family),450);self.assertEqual(len({x['game_id'] for x in family}),150)
  for r in family:
   self.assertLess(instant(r['maximum_training_label_available_at']),instant(r['source_feature_asof_at_utc']));self.assertLessEqual(instant(r['model_completed_at_utc']),instant(r['actual_issue_at_utc']));self.assertLess(instant(r['actual_issue_at_utc']),instant(r['kickoff_utc']))
   self.assertFalse(r['automatic_promotion']);self.assertFalse(r['near_term_T1_equivalence_claimed'])
 def test_equal_provider_curves_never_claim_predictive_or_scoring_credit(self):
  d=self.data;rows=[x for x in d['provider_rows'] if x['horizon'].startswith('N056_')]
  self.assertEqual(len(rows),272*9*2);self.assertFalse(any(x['eligible'] or x['source_only_predictive_credit'] for x in rows))
  curves=d['n056_provider_curve_points'];self.assertEqual(len(curves),d['n056_source_capture_summary']['curve_points']);self.assertEqual(len({x['curve_point_id'] for x in curves}),len(curves))
  for r in curves:
   self.assertFalse(r['eligible']);self.assertFalse(r['source_only_predictive_credit']);self.assertTrue(r['known_before_kickoff'])
   if r['target']!='win':self.assertIn(r['operator'],['GREATER_THAN','LESS_THAN']);self.assertEqual(r['value_semantics'],'CONDITIONAL_THRESHOLD_NOT_POINT_FORECAST')
   if not r['complete_midpoint_probability']:self.assertIsNone(r['value'] if r['target']=='win' else r['observed_threshold_probability'])
 def test_active_counts_match_arrays_and_next_is_prepared(self):
  d=self.data;validate_active_status(d);a=audit(d);self.assertEqual(a['owner_attempt']['cycle'],'N056');self.assertEqual(d['next']['cycle'],'N057');self.assertEqual(d['next']['actual_owner_results'],0)
  self.assertEqual(d['future_game_forecast_coverage']['owner_issue_rows'],5084);self.assertEqual(d['future_game_forecast_coverage']['actual_N056_owner_issue_rows'],2683);self.assertEqual(len(a['official_checks']),4)
 def test_mutated_active_metadata_and_source_credit_are_rejected(self):
  mutations=[lambda d:d['family_status'][0].update(n056_native_states=99),lambda d:d['future_game_forecast_coverage'].update(actual_N056_owner_issue_rows=0),lambda d:d['future_game_forecast_coverage'].update(future_origin_native_fits=21),lambda d:next(c for c in d['capabilities'] if c['name']=='Every future game has a dated outlook').update(status='ACTUAL_N054_OWNER_ISSUED_UNVALIDATED_LONG_RANGE'),lambda d:d['next'].update(cycle='N056'),lambda d:d['default_review_selection'][0].update(new_model_credit=1),lambda d:d['n056_provider_curve_points'][0].update(eligible=True)]
  for mutate in mutations:
   d=dict(self.data)
   for key in ['family_status','capabilities','default_review_selection','n056_provider_curve_points']:d[key]=[dict(x) for x in self.data[key]]
   for key in ['future_game_forecast_coverage','next']:d[key]=dict(self.data[key])
   mutate(d)
   with self.assertRaises(ValueError):validate_active_status(d)

if __name__=='__main__':unittest.main()
