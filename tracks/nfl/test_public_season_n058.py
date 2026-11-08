"""Meaningful public privacy, evidence, complete-grid and regression contracts."""
import base64,copy,gzip,json,pathlib,re,tempfile,unittest
from build_season_review_n054 import load,validate,build,HERE
class PublicSeasonN058(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load()
 def rejected(self,mutate):
  value=copy.deepcopy(self.data);mutate(value)
  with self.assertRaises(ValueError):validate(value)
 def test_complete_equal_inventory(self):
  d=self.data;self.assertEqual(len(d['games']),272);self.assertEqual(d['counts']['private_model_cells'],93840);self.assertEqual(d['counts']['private_provider_cells'],39168)
  self.assertEqual(sum(len(r['horizons']) for g in d['games'] for r in g['source_coverage']),39168)
 def test_all_three_season_aggregates(self):
  self.assertEqual(len(self.data['scoreboards']),1139)
  self.assertTrue({2024,2025,2026}.issubset({r['season'] for r in self.data['scoreboards']}))
  self.assertTrue(any(r.get('log_loss')==0.6551848899532826 or (r.get('log_loss') is not None and abs(r['log_loss']-.655184889953)<1e-10) for r in self.data['scoreboards']))
 def test_precise_counts_not_fit_counts(self):
  d=self.data;self.assertEqual((d['counts']['actual_latest_native_fits'],d['counts']['actual_latest_meta_fits'],d['counts']['actual_latest_issue_rows']),(0,0,117))
  self.assertEqual((d['counts']['latest_reused_raw_states'],d['counts']['latest_reused_cutoff_jobs'],d['counts']['synthetic_smoke_operations']),(3396,7148,18))
  self.assertIsNone(d['active_research_status']['top_level_fit_total']);self.assertIsNone(d['active_research_status']['top_level_issue_total'])
 def test_deterministic_self_contained_payload(self):
  html=(HERE/'season_review_n054.html').read_text();self.assertEqual(html,build(self.data));payload=re.search(r'<script id="nfl-public-payload"[^>]*>([^<]+)</script>',html)[1]
  self.assertEqual(json.loads(gzip.decompress(base64.b64decode(payload))),self.data)
 def test_full_archive_field_rejected(self):self.rejected(lambda d:d.update(model_rows=[{'prediction':.7}]))
 def test_candidate_field_in_game_rejected(self):self.rejected(lambda d:d['games'][0].update(candidate_predictions=[.7]))
 def test_hidden_recipe_in_frontier_metadata_rejected(self):self.rejected(lambda d:d['frontier_feature_status'].update(configuration={'private_parameter':.12}))
 def test_distribution_metrics_complete(self):
  self.assertEqual(len(self.data['distribution_scoreboards']),140);self.assertEqual(len({(r['public_variant_id'],r['season'],r['target']) for r in self.data['distribution_scoreboards']}),140)
 def test_hidden_recipe_in_card_rejected(self):self.rejected(lambda d:d['issued_cards'][0].update(recipe='private-current-recipe'))
 def test_source_values_outside_exception_rejected(self):self.rejected(lambda d:d['games'][0]['source_coverage'][0]['horizons'][0].update(value=.7))
 def test_missing_game_rejected(self):self.rejected(lambda d:d['games'].pop())
 def test_missing_provider_rejected(self):self.rejected(lambda d:d['games'][0]['source_coverage'].pop())
 def test_missing_horizon_rejected(self):self.rejected(lambda d:d['games'][0]['source_coverage'][0]['horizons'].pop())
 def test_stale_active_role_count_rejected(self):self.rejected(lambda d:d['counts'].update(private_model_roles=113))
 def test_fabricated_rolling_fit_rejected(self):self.rejected(lambda d:d['rolling_policy'].update(actual_new_V4_owner_fits=1))
 def test_backdated_card_rejected(self):self.rejected(lambda d:d['issued_cards'][0].update(issue_at='2027-01-01T00:00:00+00:00'))
 def test_future_source_claim_rejected(self):self.rejected(lambda d:d['issued_cards'][0].update(source_as_of='2027-01-01T00:00:00+00:00'))
 def test_full_issue_archive_rejected(self):self.rejected(lambda d:d['issued_cards'].extend(copy.deepcopy(d['issued_cards'])))
 def test_raw_private_pointer_rejected(self):self.rejected(lambda d:d['qualifications'].append('s3://private-owner-object'))
 def test_anonymous_names_required(self):self.rejected(lambda d:d['scoreboards'][0].update(public_model_id='Exact active selected configuration'))
 def test_unknown_source_status_rejected(self):self.rejected(lambda d:d['games'][0]['source_coverage'][0]['horizons'][0].update(status='UNKNOWN'))
 def test_original_cohorts_remain_explicit(self):
  text=json.dumps(self.data['cohorts']);self.assertIn('92',text);self.assertIn('91',text);self.assertIn('119',text);self.assertIn('120',text);self.assertIn('Original minute-path support before Rams restoration',text)
 def test_synthetic_tests_do_not_admit_owner_features(self):self.rejected(lambda d:d['frontier_feature_status'].update(admitted=1))
 def test_feature_candidate_counts_reconcile(self):self.rejected(lambda d:d['frontier_feature_status'].update(proposed=212))
 def test_all_score_target_filters_normalized(self):self.assertEqual({r['target'] for r in self.data['scoreboards']},{'win','margin','total'})
 def test_site_export_refuses_stale_or_private_extra_files(self):
  from export_season_site_n054 import validate_output_directory
  with tempfile.TemporaryDirectory() as root:
   folder=pathlib.Path(root);(folder/'owner-report.json').write_text('{}')
   with self.assertRaises(ValueError):validate_output_directory(folder)
   (folder/'owner-report.json').unlink();(folder/'index.html').write_text('bounded page');(folder/'provenance.json').write_text('{}');validate_output_directory(folder)
 def test_old_complete_carriers_not_active_public_inputs(self):
  for name in ['current_season_n054.json.gz','n054_actual_recovery_n055.json.gz','n055_actual_results_n056.json.gz','n056_actual_results_n057.json.gz']:
   self.assertFalse((HERE/name).exists(),name)
if __name__=='__main__':unittest.main()
