"""Recover partial owner science without collapsing source, fit and issue identities."""
import copy,gzip,json,pathlib,re,unittest
from build_season_review_n054 import validate,build,load,pack,RETIRED
HERE=pathlib.Path(__file__).resolve().parent
class N054RecoveredScienceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=validate(load());cls.games={g['game_id']:g for g in cls.data['games']}
 def test_every_game_team_and_role_is_present(self):
  d=self.data;self.assertEqual(len(d['games']),272);self.assertEqual(sum(g['completed'] for g in d['games']),122);self.assertEqual(len(d['lanes']),63);self.assertEqual(len(d['model_rows']),51408);self.assertEqual(sum(r['available'] for r in d['model_rows']),8921)
  self.assertEqual(len({g['away'] for g in d['games']}|{g['home'] for g in d['games']}),32)
  for g in ['2026_08_CHI_SEA','2026_09_JAX_BAL']:
   self.assertTrue(self.games[g]['completed']);self.assertEqual(len([r for r in d['model_rows'] if r['game_id']==g and r['lane_id'].startswith('n053r1_raw_') and r['available']]),12)
 def test_actual_jobs_states_reuse_and_partial_totals(self):
  o=self.data['owner_execution'];self.assertEqual(o['completed_cutoff_jobs'],o['unique_native_states']+o['exact_reused_cutoff_jobs']);self.assertEqual(o['optimizer_starts'],3432);self.assertEqual(o['optimizer_returns'],3432);self.assertEqual(o['durable_commits'],3432);self.assertIsNone(o['top_level_fit_counter']);self.assertIsNone(o['top_level_issue_counter']);self.assertEqual(self.data['new_owner_fits'],3502)
 def test_new_current_issues_and_original_clocks(self):
  rows=[r for r in self.data['model_rows'] if r['lane_id'].startswith('n053r1_issued_') and r['available']];self.assertEqual(len(rows),672);self.assertEqual(len({r['game_id'] for r in rows}),28);self.assertTrue(all(r['actual_issue_eligible'] and r['issued_at'] and r['fit_completed_at'] for r in rows));self.assertEqual(self.data['new_owner_issues'],len(rows)+len(self.data['conditional_rows']))
  self.assertEqual(self.data['current_raw_numerical_replay']['forecast_rows_replayed'],336);self.assertLess(self.data['current_raw_numerical_replay']['maximum_absolute_prediction_error'],1e-12);self.assertEqual(len(self.data['prior_conditional_rows']),82);self.assertEqual({r['conditional_semantics_version'] for r in self.data['conditional_rows']},{'N049 v1'})
 def test_every_future_game_has_a_separately_dated_forecast(self):
  d=self.data;rows=[r for r in d['model_rows'] if r['lane_id'].startswith('n054_outlook_') and r['available']];self.assertEqual(len(rows),1464);self.assertEqual(len({r['game_id'] for r in rows}),122);self.assertTrue(all(r['new_owner_issue_credit']==0 and r['new_review_issue_credit']==1 and not r['long_horizon_accuracy_validated'] for r in rows));self.assertEqual(d['future_game_forecast_coverage']['covered_future_games'],150);self.assertEqual(len(d['raw_provider_timing_exclusions']),8)
 def test_all_conditional_display_fields_preserve_oriented_probabilities(self):
  rows=self.data['conditional_rows'];self.assertEqual(len(rows),82);self.assertEqual(len({r['game_id'] for r in rows}),27)
  self.assertEqual(sum(r['orientation']=='HOME_MARGIN_STRICTLY_LESS_THAN' for r in rows),48);self.assertEqual(sum(r['orientation']=='HOME_MARGIN_STRICTLY_GREATER_THAN' for r in rows),34)
  for r in rows:
   side='probability_below' if r['orientation']=='HOME_MARGIN_STRICTLY_LESS_THAN' else 'probability_above'
   self.assertEqual(r['probability_of_predicate'],r[side]);self.assertAlmostEqual(r['probability_given_not_equal'],r['probability_of_predicate']/(1-r['probability_equal']),delta=.00015)
 def test_wrong_or_absent_conditional_display_field_is_rejected(self):
  for mutation in [{'probability_of_predicate':None},{'probability_of_predicate':.1234},{'probability_given_not_equal':.1234}]:
   d=dict(self.data);d['conditional_rows']=[dict(r) for r in self.data['conditional_rows']];d['conditional_rows'][0].update(mutation)
   with self.assertRaisesRegex(ValueError,'conditional (display probability|predicate orientation|unequal probability)'):validate(d)
 def test_zero_repeated_protected_studies_and_source_credit(self):
  for k in ['protected_refits','repeated_designation_cells','repeated_injury_cells','repeated_correction_states','controls_changed','source_only_predictive_credit']:self.assertEqual(self.data['owner_execution'][k],0)
  self.assertFalse(self.data['original_evidence_modified']);self.assertEqual(self.data['next']['actual_owner_results'],0);self.assertEqual(len(self.data['correction_comparisons']),255)
 def test_frozen_and_expanded_current_cohorts_are_distinct(self):
  self.assertEqual(sum(g['frozen_point_benchmark'] for g in self.data['games']),120);self.assertEqual(sum(g['frozen_binary_benchmark'] for g in self.data['games']),119)
  rows=[r for r in self.data['raw_season_metrics'] if r['season']==2026 and r['arm']!='unchanged_frozen201_mean'];self.assertEqual({r['games'] for r in rows if r['target']=='win'},{121});self.assertEqual({r['games'] for r in rows if r['target']!='win'},{122})
  for r in self.data['raw_season_metrics']:
   if r['season']>=2024:self.assertFalse(r['selection_period_eligible'])
 def test_complete_equal_provider_horizons_and_exact_metrics(self):
  d=self.data;self.assertEqual(len(d['provider_rows']),272*3*3*len(d['provider_horizons']));self.assertIn('N054_REVIEW_LATEST_AVAILABLE',d['provider_horizons']);self.assertIn('N053R1_LATEST_OBSERVED',d['provider_horizons']);self.assertEqual(d['current_source_readback']['verified_objects'],181)
  for c in d['coverage_rows']:
   rs=[r for r in d['provider_rows'] if r['horizon']==c['horizon'] and r['provider']==c['provider'] and r['target']==c['target'] and self.games[r['game_id']]['completed']];self.assertEqual(len(rs),122);self.assertEqual(sum(r['available'] for r in rs),c['available']);self.assertEqual(sum(r['eligible'] for r in rs),c['eligible'])
  self.assertEqual(len(d['matched_current_metrics']),35);self.assertEqual(len(d['matched_current_comparisons']),56);self.assertEqual({r['games'] for r in d['matched_current_metrics'] if r['cohort']=='EXACT91_T2'},{91});self.assertEqual({r['games'] for r in d['matched_current_metrics'] if r['cohort']=='COMMON119_T2_PROVIDERS'},{119})
 def test_scale_negative_findings_and_complete_exports(self):
  d=self.data;self.assertEqual(len(d['scale_per_game']),35252);self.assertEqual(len(d['scale_season_metrics']),140);self.assertEqual(len(d['scale_comparisons']),260);self.assertTrue(all(r['primary_p_holm']>=.05 for r in d['scale_comparisons']));self.assertEqual(len(d['raw_current_issues']),336);self.assertEqual(len(d['raw_per_game']),18889);self.assertEqual(len(d['all_model_metrics']),638)
 def test_dated_week10_recovery_preserves_real_gaps(self):
  d=self.data;c={(r['provider'],r['target']):r['available_games'] for r in d['current_provider_counts'] if r['week']==10};self.assertEqual((c['DraftKings','winner'],c['Kalshi','winner'],c['Polymarket','winner']),(13,14,14));self.assertEqual((c['Kalshi','margin'],c['Kalshi','total'],c['Polymarket','margin'],c['Polymarket','total']),(1,1,14,14));self.assertEqual(sum(r.get('one_sided_known_threshold_games',0) for r in d['current_provider_counts'] if r['week']==10),5);self.assertEqual(d['draftkings_sea_lv_gap']['exact_event_matches'],0);self.assertEqual(d['review_provider_capture']['predictive_credit'],0);self.assertTrue(d['review_provider_capture']['acquired_after_N053R1_issues'])
 def test_original_minute_registration_unchanged(self):
  s=self.data['source_diagnostics'];self.assertEqual(s['registered_games'],121);self.assertEqual(s['feature_rows'],172373);self.assertEqual(s['expanded_window_rows'],689492);self.assertFalse(s['completed_study_recomputed'])
 def test_additive_rams_paths_never_rewrite_original_scope(self):
  r=self.data['additive_polymarket_path_repair'];self.assertEqual((r['original_polymarket_path_games'],r['newly_supported_polymarket_paths'],r['additive_observed_polymarket_path_games']),(113,8,121));self.assertEqual(r['new_source_path_observations'],5911);self.assertEqual(r['new_predictive_credit'],0);self.assertEqual(r['internal_gaps_over120seconds'],35);self.assertTrue(r['all80_objects_authenticated']);self.assertEqual(r['remaining_completed_game_outside_original121_scope'],'2026_09_JAX_BAL')
  for m in ['1','3','5','10']:
   v=r['per_minute_window_counts'][m];self.assertEqual(v['complete_supported_windows']+v['sparse_or_censored_windows'],5911)
 def test_later_selection_is_rejected(self):
  d=dict(self.data);d['raw_season_metrics']=[dict(r) for r in d['raw_season_metrics']];next(r for r in d['raw_season_metrics'] if r['season']==2026)['selection_period_eligible']=True
  with self.assertRaisesRegex(ValueError,'later season selection'):validate(d)
 def test_fabricated_missing_model_is_rejected(self):
  d=dict(self.data);d['model_rows']=list(d['model_rows']);i=next(i for i,r in enumerate(d['model_rows']) if not r['available']);d['model_rows'][i]=dict(d['model_rows'][i],value=.7)
  with self.assertRaisesRegex(ValueError,'fabricated absent'):validate(d)
 def test_active_public_boundaries(self):
  for name in ['season_review_n054.template.html','README.md','SEASON_REVIEW_N054.md']:
   self.assertIsNone(RETIRED.search((HERE/name).read_text()),name)
  self.assertIsNone(re.search(r's3://|arn:aws:|X-Amz-|model_sha256|component_bindings|lambda=|direct201_',json.dumps(self.data)))
 def test_deterministic_lossless_publication(self):
  self.assertEqual((HERE/'current_season_n054.json.gz').read_bytes(),pack(self.data));self.assertEqual(build(self.data),(HERE/'season_review_n054.html').read_text());self.assertLess((HERE/'current_season_n054.json.gz').stat().st_size,10_000_000)
class N054StaticPublicationTests(unittest.TestCase):
 def test_runtime_links_are_preserved_and_static_links_are_pinned(self):
  from export_season_site_n054 import projection
  commit='748ae11daa69bb114460dd30a96cf414f72c5936'
  source='<a href="README.md">source</a><script>const link=`<a href="${esc(u)}">official source</a>`;</script>'
  result=projection(source,commit)
  self.assertIn('/blob/'+commit+'/tracks/nfl/README.md',result)
  self.assertIn('href="${esc(u)}"',result)
 def test_missing_static_file_still_blocks_publication(self):
  from export_season_site_n054 import projection
  with self.assertRaisesRegex(ValueError,'Unresolved public link'):
   projection('<a href="missing-unregistered-public-file.json">missing</a>','748ae11daa69bb114460dd30a96cf414f72c5936')
 def test_complete_real_page_has_no_unresolved_static_links(self):
  from export_season_site_n054 import projection
  result=projection((HERE/'season_review_n054.html').read_text(),'748ae11daa69bb114460dd30a96cf414f72c5936')
  self.assertIn('href="${esc(u)}"',result)
  self.assertTrue('href="previous.html"' in result,'Previous dated archive link was not mapped')
  self.assertIn('forecast: 28 nearer games plus 122',result)
if __name__=='__main__':unittest.main()
