import copy,json,unittest
from pathlib import Path
from current_issues_n044 import validate_current_issues
from current_source_n044 import validate_current_source
from three_provider_directions import validate_three_provider
HERE=Path(__file__).parent
class OwnerRecoveryN044(unittest.TestCase):
 def setUp(self):
  self.coverage=json.loads((HERE/'current_coverage.json').read_text());self.issues=json.loads((HERE/'current_issues_n044.json').read_text());self.source=json.loads((HERE/'current_source_n044.json').read_text());self.common=json.loads((HERE/'three_provider_directions.json').read_text())
 def test_three_distinct_issued_streams(self):
  self.assertEqual(validate_current_issues(self.issues,self.coverage)['n044_actual_target_rows'],261)
  self.assertEqual(validate_current_source(self.source,self.coverage)['source_n044_draftkings_fresh_games'],15)
 def test_restored_models_cannot_be_new(self):
  self.issues['new_native_fits']=5
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
 def test_source_refresh_cannot_refresh_original_base_clock(self):
  c=self.issues['streams'][0]['cards'][0];c['base_feature_asof_at']=self.issues['streams'][2]['cards'][0]['base_feature_asof_at']
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
 def test_fresh_stream_cannot_borrow_120_game_training_count(self):
  self.issues['streams'][2]['current_training_games']=120
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
 def test_expanded_preparation_does_not_promote(self):
  self.issues['owner_pipeline_accepted']=True
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
 def test_latest_reference_cannot_be_historical(self):
  self.source['winner_rows'][0]['horizon']='T2'
  with self.assertRaises(ValueError):validate_current_source(self.source,self.coverage)
 def test_all_three_compare_identical_events(self):
  self.assertEqual(validate_three_provider(self.common,self.coverage)['three_provider_common_games'],91)
 def test_common_cohort_cannot_drop_a_provider(self):
  self.common['games'][0]['providers'].pop('DraftKings')
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_common_cohort_cannot_change_a_pick(self):
  g=self.common['games'][0];p=g['providers']['Kalshi'];p['pick']=g['away']if p['pick']==g['home']else g['home']
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_common_cohort_cannot_invent_probability_loss_or_profit(self):
  for field in ['probability_metrics','pnl']:
   d=copy.deepcopy(self.common);d['summary'][0][field]=0
   with self.assertRaises(ValueError):validate_three_provider(d,self.coverage)
 def test_common_cohort_cannot_hide_losses(self):
  self.common['summary'][0]['disagreements_lost']=0
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_saved_quote_clock_cannot_be_invented(self):
  self.common['games'][0]['providers']['DraftKings']['quote_at']='2026-09-01T00:00:00Z'
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_recovered_quote_after_cutoff_rejected(self):
  self.common['restored_draftkings_t2']['rows'][0]['quote_at']='2026-11-05T00:00:00Z'
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_retroactive_possession_rejected(self):
  self.common['restored_draftkings_t2']['rows'][0]['contemporaneously_possessed_by_t2']=True
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_restored_reference_not_latest_or_profit(self):
  for field in ['latest_quote_claim','execution_qualified']:
   d=copy.deepcopy(self.common);d['restored_draftkings_t2'][field]=True
   with self.assertRaises(ValueError):validate_three_provider(d,self.coverage)
 def test_restored_reference_not_new_forecast(self):
  self.common['restored_draftkings_t2']['new_forecasts']=120
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_probability_comparison_cannot_change_denominator(self):
  self.common['restored_probability_review']['metrics'][0]['n']=119
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_probability_comparison_cannot_replace_loss(self):
  self.common['restored_probability_review']['metrics'][0]['log_loss']=.45
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_original_label_proxy_cannot_be_upgraded(self):
  self.common['restored_probability_review']['model_label_clock_publication_proxy_unverified']=False
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
 def test_probability_interval_cannot_hide_uncertainty(self):
  self.common['restored_probability_review']['intervals'][0]['ci95_high']=-.001
  with self.assertRaises(ValueError):validate_three_provider(self.common,self.coverage)
if __name__=='__main__':unittest.main()
