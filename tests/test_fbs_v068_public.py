"""Check the selected V067 issue projection without fitting or rescoring."""
import base64
from collections import Counter
import csv
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

P=Path(__file__).resolve().parents[1]/'docs/fbs'
def dt(v): return datetime.fromisoformat(v.replace('Z','+00:00'))

class V068PublicEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.gz=(P/'latest-games-v068.json.gz').read_bytes()
  cls.raw=gzip.decompress(cls.gz)
  cls.data=json.loads(cls.raw)
  cls.old=json.loads(gzip.decompress((P/'latest-games-v067.json.gz').read_bytes()))
  cls.games=cls.data['games']
  cls.current=[g for g in cls.games if g['layers']['current_v067']['values']['p_home'] is not None]

 def test_inventory_and_all_selected_layers_are_complete(self):
  self.assertEqual(self.data['schema'],'fbs.public.v068.latest-authenticated-game-view.v1')
  self.assertEqual(len(self.games),888)
  self.assertEqual(len({g['game_id'] for g in self.games}),888)
  self.assertEqual(Counter(g['schedule_status'] for g in self.games),{
   'HISTORICAL_ISSUES_RETAINED_NO_BACKDATED_REISSUE':688,'CURRENT_ORIGIN_REFRESH_DUE':146,'EXACT_KICKOFF_NOT_PUBLISHED':54})
  self.assertEqual(len(self.current),146)
  self.assertTrue(all(len(g['layers'])==7 for g in self.games))

 def test_prior_six_layer_objects_and_saved_metrics_are_preserved(self):
  old={g['game_id']:g for g in self.old['games']}
  for g in self.games:
   for layer,value in old[g['game_id']]['layers'].items():self.assertEqual(g['layers'][layer],value)
  for key in ['historical_cohort_leaders','current_retained_metric_evidence','saved_231_draftkings_comparison',
              'native_latest_label_monitor','latest_saved_bank_verification','provider_evidence','new_research']:
   self.assertEqual(self.data[key],self.old[key])
  self.assertEqual(self.data['publication_projection']['previous_public_gzip_sha256'],
   hashlib.sha256((P/'latest-games-v067.json.gz').read_bytes()).hexdigest())

 def test_all_current_issues_precede_exact_kickoff_with_original_clocks(self):
  for g in self.current:
   layer=g['layers']['current_v067']
   self.assertFalse(g['completed'])
   self.assertLess(dt(layer['information_cutoff_utc']),dt(layer['original_durable_observed_at']))
   self.assertLess(dt(layer['original_durable_observed_at']),dt(g['kickoff_utc']))
   self.assertLessEqual(dt(layer['maximum_information_available_at']),dt(layer['information_cutoff_utc']))
   self.assertEqual(layer['horizon'],'CURRENT_ORIGIN_OUTLOOK')
   self.assertFalse(layer['production_champion'])
   self.assertFalse(layer['calibration_proved'])
   self.assertFalse(layer['new_issue_created_by_export'])
   self.assertIsNone(layer['values']['exact_line_cover'])
  times=[g['layers']['current_v067']['original_durable_observed_at'] for g in self.current]
  self.assertEqual(min(times),'2026-11-11T23:31:03.995204Z')
  self.assertEqual(max(times),'2026-11-11T23:32:11.232957Z')

 def test_new_issue_fills_one_gap_without_backfilling_older_original(self):
  g=next(g for g in self.games if g['game_id']=='401858532')
  self.assertIsNone(g['layers']['original']['values']['p_home'])
  self.assertIsNotNone(g['layers']['current_v067']['values']['p_home'])
  self.assertEqual((g['away'],g['home']),('Rutgers','Penn State'))
  self.assertEqual(self.data['summary']['future_baseline_refresh_gaps'],0)
  self.assertEqual(self.data['summary']['original_issue_covered_games'],148)
  for g in self.games:
   if g not in self.current:
    self.assertTrue(all(v is None for v in g['layers']['current_v067']['values'].values()))

 def test_single_fit_and_output_counts_do_not_hide_partial_failure(self):
  a=self.data['latest_execution']
  self.assertEqual(a['status'],'V067_PARTIAL_LEDGER_DELIVERY_FAILED')
  self.assertEqual((a['new_model_fits'],a['new_genuine_forecasts'],a['new_prediction_outputs']),(1,146,739))
  self.assertEqual((a['new_forward_scalar_outputs'],a['new_former_model_inference_rows']),(438,301))
  self.assertEqual(a['new_owner_metric_evaluations'],1)
  self.assertEqual((a['actual_worker_interpreter_exit'],a['actual_supervisor_interpreter_exit']),(2,2))
  self.assertFalse(a['outer_shell_exit_independently_observed'])
  self.assertFalse(a['ledger_delivery_complete'])
  self.assertFalse(a['parallel_frozen_fit_phase_reached'])
  self.assertEqual(a['owned_market_requests_normalized'],128)
  self.assertEqual((a['provider_requests'],a['new_paid_odds_requests']),(13,0))
  self.assertEqual(len(a['errors']),2)
  self.assertEqual({e['message'] for e in a['errors']},{'V067_FOUNDATION_REFRESH_EXACT_PACKAGE_AUTHORIZATION_REQUIRED'})

 def test_new_former_model_evaluation_keeps_its_301_game_limits(self):
  m=self.data['v067_restored_probability_evaluation']
  self.assertEqual((m['games'],m['correct'],m['new_inference_rows']),(301,237,301))
  self.assertEqual(m['log_loss'],0.46551880819770836)
  self.assertEqual(m['brier'],0.15263011173024496)
  self.assertEqual(m['completed_games_outside_saved_design'],387)
  self.assertEqual(m['label_snapshot_as_of'],'2026-11-11T23:30:41Z')
  for k in ['selection_allowed','promotion_authorized','full_current_season_evaluation','historical_source_possession_proved','original_pregame_issue_proved','export_recomputed_metrics']:
   self.assertFalse(m[k])

 def test_annual_leaders_keep_distinct_populations_and_roles(self):
  rows=self.data['annual_descriptive_leaders']
  self.assertEqual(len(rows),21)
  self.assertEqual(Counter(r['season'] for r in rows),{2024:7,2025:7,2026:7})
  for r in rows:
   self.assertEqual(r['games'],{2024:918,2025:934,2026:688}[r['season']])
   self.assertFalse(r['promotion_authorized'])
  self.assertEqual(next(r['value'] for r in rows if r['season']==2025 and r['metric']=='log_loss'),0.4852833984420019)
  self.assertEqual(next(r['value'] for r in rows if r['season']==2026 and r['target']=='total' and r['metric']=='rmse'),16.236818941008934)

 def test_no_champion_or_future_science_is_claimed(self):
  self.assertEqual(self.data['champion_status']['authorized_metric_champions'],0)
  self.assertTrue(all(g['metric_champion_forecast'] is None for g in self.games))
  self.assertFalse(self.data['prepared_continuation']['actual_owner_execution_observed'])
  self.assertEqual(self.data['prepared_continuation']['owner_release'],'V068')
  self.assertEqual(self.data['new_sports_metrics_calculated_by_export'],0)
  self.assertEqual(self.data['registry_status']['completed_frozen_cases'],247)
  self.assertFalse(self.data['registry_status']['global_evidence_complete'])

 def test_csv_matches_seven_selected_layers_including_blank_values(self):
  rows=list(csv.DictReader((P/'latest-games-v068.csv').read_text().splitlines()))
  self.assertEqual(len(rows),6216)
  self.assertEqual(len({(r['game_id'],r['layer']) for r in rows}),6216)
  by={g['game_id']:g for g in self.games}
  for r in rows:
   layer=by[r['game_id']]['layers'][r['layer']]
   for field in ['p_home','home_margin','total_points','home_score','away_score','exact_line_cover']:
    self.assertEqual(None if r[field]=='' else float(r[field]),layer['values'][field])
   self.assertEqual(r['original_durable_observed_at'],layer['original_durable_observed_at'] or '')
  inventory=list(csv.DictReader((P/'season-inventory-v068.csv').read_text().splitlines()))
  self.assertEqual(Counter(r['season'] for r in inventory),{'2024':920,'2025':934,'2026':888})

 def test_embedded_data_is_exact_and_private_material_is_absent(self):
  js=(P/'latest-games-v068-data.js').read_text()
  encoded=re.fullmatch(r'window\.FBS_LATEST_V068_GZIP="([A-Za-z0-9+/=]+)";\n',js)
  self.assertIsNotNone(encoded)
  self.assertEqual(base64.b64decode(encoded[1],validate=True),self.gz)
  text=self.raw.decode()
  for pattern in ['s3://','/home/sagemaker-user','sagemaker-sports-edge','joint_components','fit_identities','recipe_policy_sha256','model_snapshot_sha256','ridge_']:
   self.assertNotIn(pattern,text)
  self.assertFalse(self.data['publication_projection']['full_immutable_forecast_archive_published'])

if __name__=='__main__':unittest.main()
