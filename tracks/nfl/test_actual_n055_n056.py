import copy,gzip,json,pathlib,unittest
from build_season_review_n054 import load
from actual_recovery_n055 import enrich as prior_enrich
from actual_n055_n056 import enrich,load_overlay,validate_overlay,validate_active_status
from publication_audit_n056 import audit

class ActualN055Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=load();cls.prior=prior_enrich(cls.base);cls.data=enrich(cls.base);cls.overlay=load_overlay()
 def test_complete_equal_inventory_and_unchanged_scientific_ancestors(self):
  d=self.data;p=self.prior
  self.assertEqual(len(d['games']),272);self.assertEqual(len({t for g in d['games'] for t in [g['home'],g['away']]}),32)
  self.assertEqual(len(d['model_rows']),len(d['games'])*len(d['lanes'])*3)
  self.assertEqual(len(d['provider_rows']),len(d['games'])*3*3*len(d['provider_horizons']))
  for key in ['games','raw_per_game','scale_per_game','scale_comparisons','matched_current_metrics','matched_current_comparisons','n054_market_per_game','n054_owner_raw_issues','n054_owner_long_range_issues','review_long_range_issues']:
   self.assertEqual(d[key],p[key],key)
  self.assertEqual(d['model_rows'][:len(p['model_rows'])],p['model_rows'])
  self.assertEqual(d['provider_rows'][:len(p['provider_rows'])],p['provider_rows'])
  self.assertEqual(d['all_model_metrics'][:len(p['all_model_metrics'])],p['all_model_metrics'])
 def test_actual_native_meta_job_and_reuse_accounting(self):
  s=self.data['n055_actual_results'];f=self.data['family_status']
  self.assertEqual(sum(x['n055_native_states'] for x in f),1378);self.assertEqual(sum(x['n055_meta_states'] for x in f),45)
  self.assertEqual(s['new_optimizer_starts'],s['new_optimizer_returns']);self.assertEqual(s['new_optimizer_returns'],s['new_durable_state_commits'])
  self.assertEqual(s['all_completed_job_checkpoints'],s['completed_native_cutoff_jobs']+s['completed_fitted_meta_jobs']+s['fixed_equal_blend_no_fit_jobs'])
  self.assertEqual(s['total_reuse_job_events'],s['native_reuse_job_events']+s['meta_reuse_job_events']);self.assertEqual(s['total_reuse_job_events'],1891)
  self.assertEqual(s['distinct_reused_identities'],461);self.assertEqual(s['unique_train_transforms_reconstructed'],477)
  self.assertTrue(all(s[k] is None for k in ['top_level_new_fits','top_level_new_native_fits','top_level_new_forecasts']))
 def test_full_cohorts_and_no_two_game_backfill(self):
  d=self.data;r=self.overlay;self.assertEqual(len({x['model'] for x in r['annual_predictions']}),23)
  validate_overlay(r)
  for game in ['2026_08_CHI_SEA','2026_09_JAX_BAL']:
   self.assertTrue(next(g for g in d['games'] if g['game_id']==game)['completed'])
   family=[x for x in d['model_rows'] if x['game_id']==game and (x['lane_id'].startswith('n055_annual_') or x['lane_id']=='n055_selected_event')]
   self.assertEqual(len(family),24*3);self.assertTrue(all(not x['available'] and '120-point / 119-winner' in x['reason'] for x in family))
  for target,n in [('win',119),('margin',120),('total',120)]:
   self.assertEqual(len([x for x in r['selected_event_predictions'] if x['season']==2026 and x['target']==target]),n)
 def test_new_issue_clocks_and_frozen_source_are_explicit(self):
  d=self.data;s=d['n055_actual_results'];f=d['future_game_forecast_coverage']
  self.assertEqual(len(d['n055_owner_component_issues']),168);self.assertEqual(f['owner_issue_rows'],2233+168)
  self.assertEqual(f['owner_nearer_game_issue_games']+f['owner_long_range_outlook_games'],150)
  self.assertEqual(s['new_four_lane_raw_issues'],0);self.assertEqual(s['recorded_future_issue_rows'],0)
  self.assertEqual(sum(r['injury_reports_qualified'] for r in d['n055_owner_component_issues']),84)
  self.assertTrue(all(not r['final_hour_qualified_card'] and r['new_native_fit_credit']==0 for r in d['n055_owner_component_issues']))
 def test_source_capture_cannot_replace_scored_horizons(self):
  d=self.data;rows=[r for r in d['provider_rows'] if r['horizon']=='N055_CURRENT_CAPTURE']
  self.assertEqual(len(rows),272*9);self.assertEqual(sum(r['available'] for r in rows),223)
  self.assertTrue(all(not r['eligible'] and r['source_only_predictive_credit']==0 for r in rows))
  self.assertEqual(d['n055_source_capture_summary']['normalized_rows'],660)
  self.assertEqual(d['n055_source_capture_summary']['quote_clock_missing_rows'],172)
 def test_status_and_capabilities_match_actual_arrays(self):
  d=self.data;validate_active_status(d)
  self.assertTrue(all(q.startswith('For the retained N053R1 four-arm study:') for q in d['qualifications'] if 'Selected winner remains' in q));self.assertEqual(d['next']['cycle'],'N056');self.assertEqual(d['next']['actual_owner_results'],0)
  self.assertEqual(audit(d)['completeness'][-5]['present'],len(d['n055_family_per_game']))
  self.assertEqual(len(audit(d)['completeness']),14)
  self.assertTrue(all('original N054 preparation' in r.get('retained_prior_evidence','') for r in d['family_status'] if r.get('retained_prior_evidence')))
 def test_stale_status_and_count_mutations_fail(self):
  for mutate in [lambda d:d['family_status'][0].update(n055_native_states=-1),lambda d:d['future_game_forecast_coverage'].update(actual_N055_owner_issue_rows=0),lambda d:d['next'].update(cycle='N055'),lambda d:d['n055_current_provider_rows'][0].update(eligible=True)]:
   d=copy.deepcopy(self.data);mutate(d)
   if d['n055_current_provider_rows'][0]['eligible']:
    next(r for r in d['provider_rows'] if r['horizon']=='N055_CURRENT_CAPTURE' and r['game_id']==d['n055_current_provider_rows'][0]['game_id'] and r['provider']==d['n055_current_provider_rows'][0]['provider'] and r['target']==d['n055_current_provider_rows'][0]['target'])['eligible']=True
   with self.assertRaises(ValueError):validate_active_status(d)
 def test_new_overlay_is_deterministic_and_isolated(self):
  self.assertEqual(enrich(self.base),self.data);self.assertEqual(enrich(self.data),self.data)
  self.assertEqual(self.data['original_n055_publication_snapshot']['family_status'],self.prior['family_status'])

if __name__=='__main__':unittest.main()
