"""Later outcomes may score saved reconstructions without becoming issued work."""
from pathlib import Path
from datetime import datetime
import json
import unittest

ROOT=Path(__file__).resolve().parents[3]


class RefreshEvaluationV045Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads((ROOT/'docs/fbs/changed-input-evaluation-v045.json').read_text())
  cls.original=json.loads((ROOT/'docs/fbs/changed-input-study-v044.json').read_text())
  cls.capture=json.loads((ROOT/'docs/fbs/current-capture-v045.json').read_text())
 def test_new_scores_do_not_rewrite_the_original_pending_study_or_count_new_fits(self):
  r=self.report;c=r['counts']
  self.assertEqual((c['registered_games'],c['scored_games'],c['new_result_evaluation_records']),(119,12,384))
  self.assertEqual(self.original['counts']['scored_games'],0)
  self.assertTrue(all(rows==[] for rows in self.original['metrics'].values()))
  self.assertEqual((c['original_base_fits'],c['original_calibration_fits'],c['original_prediction_outputs']),(46,14,3808))
  for key in ('new_local_fits','new_local_prediction_outputs','genuine_issues','qualified_cover_probabilities'):self.assertEqual(c[key],0)
  self.assertFalse(r['forecast_issued']);self.assertFalse(r['promotion_allowed']);self.assertFalse(r['historical_availability_proved'])
  self.assertEqual(r['default_selection_unchanged'],'V038 fixed_equal_blend')
 def test_exact_latest_outcome_intersection_preserves_all_late_computation_clocks(self):
  captured={x['id']:x for x in self.capture['rows']};scored=[x for x in self.original['rows'] if captured[x['id']]['completed']]
  self.assertEqual(len(scored),12);self.assertEqual(sum(len(m) for x in scored for m in x['models'].values()),384)
  for row in scored:
   self.assertTrue(captured[row['id']]['newly_observed'])
   for model in row['models'].values():
    for target in model.values():
     self.assertGreaterEqual(datetime.fromisoformat(target['computed_at_utc'].replace('Z','+00:00')),datetime.fromisoformat(row['cutoff'].replace('Z','+00:00')))
     self.assertIs(target['computed_before_cutoff'],False)
  self.assertEqual(self.report['scored_refresh_outputs_before_cutoff'],0)
  self.assertEqual(self.report['scored_refresh_outputs_at_or_after_cutoff'],384)
  self.assertEqual(self.report['source_capture_physical'],self.capture['capture']['source_capture_physical'])
 def test_full_current_week_inventory_is_not_replaced_by_the_119_target_scope(self):
  coverage=self.report['coverage']
  self.assertEqual((coverage['2026']['identified_games'],coverage['2026']['registered_target_games'],coverage['2026']['observed_completed']),(888,119,12))
  self.assertEqual((coverage['current_week']['identified_games'],coverage['current_week']['registered_target_games'],coverage['current_week']['observed_completed']),(63,14,12))
  self.assertEqual((coverage['newly_observed']['identified_games'],coverage['newly_observed']['registered_target_games']),(13,12))
  for period in ('2024','2025','previous_week'):
   self.assertEqual(coverage[period]['registered_target_games'],0);self.assertEqual(self.report['metrics'][period],[])
 def test_paired_baselines_keep_full_precision_and_exact_target_cohorts(self):
  for period in ('2026','cumulative','current_week','newly_observed'):
   rows=self.report['metrics'][period];index={(r['family'],r['target']):r for r in rows}
   self.assertEqual(len(index),64)
   refreshed=[r for r in rows if r['family'].startswith('v043_refresh_')]
   self.assertEqual(len(refreshed),32);self.assertEqual(self.report['baseline_metric_rows_by_period'][period],32)
   for row in refreshed:
    self.assertEqual(row['games'],12);self.assertEqual(len(row['exact_common_comparisons']),2)
    self.assertEqual({p['comparison'] for p in row['exact_common_comparisons']},{'unchanged_default','same_retained_family'})
    for pair in row['exact_common_comparisons']:
     baseline=index[(pair['reference_family'],row['target'])]
     self.assertEqual(pair['common_games'],12)
     self.assertEqual(pair['exact_game_ids_sha256'],row['exact_game_ids_sha256'])
     self.assertEqual(baseline['exact_game_ids_sha256'],row['exact_game_ids_sha256'])
     for key,value in pair['reference_metrics'].items():self.assertEqual(baseline[key],value)
     for key in ('log_loss','brier','mae','rmse'):
      if key in pair['model_metrics']:self.assertEqual(row[key],pair['model_metrics'][key])
 def test_public_safe_evaluation_and_companion_do_not_add_model_outputs(self):
  text=json.dumps(self.report)
  for forbidden in ('s3://','fit_identity_sha256','model_state_sha256','/workspace/','api_key','raw_probability','feature_names','model_parameters','actual_game_ids','source_input_identity'):self.assertNotIn(forbidden,text)
  self.assertNotIn('rows',self.report)
  js=(ROOT/'docs/fbs/changed-input-evaluation-v045-data.js').read_text()
  self.assertEqual(json.loads(js.split('=',1)[1].removesuffix(';\n')),self.report)


if __name__=='__main__':unittest.main()
