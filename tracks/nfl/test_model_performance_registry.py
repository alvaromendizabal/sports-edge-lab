import copy,json,unittest
from pathlib import Path
from model_performance_registry import build_registry,load_registry
from current_issues_n046 import load_current_issues,validate_current_issues
from historical_reference_n046 import load_historical_reference
from current_source_n046 import load_current_source
HERE=Path(__file__).parent
class ModelEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.coverage=json.loads((HERE/'current_coverage.json').read_text());cls.issues=load_current_issues(cls.coverage)[0]
 def test_new_injury_source_cannot_rewrite_owner_inputs(self):
  from injury_source_update_n047 import load_injury_source_update
  new=load_injury_source_update(self.issues)[0]
  self.assertEqual((new["normalized_rows"],new["team_tables"]),(340,30))
  self.assertEqual((self.issues["source_census"]["listed_rows"],self.issues["source_census"]["team_sections"]),(295,29))
  self.assertEqual(new["new_forecasts"],0)
 def test_every_selectable_stream_has_record(self):
  d=load_registry()[0];expected={m['id']for m in self.coverage['model_sets']}
  for version in ('042','043','044','045','046','047','048'):expected.update(s['id']for s in json.loads((HERE/f'current_issues_n{version}.json').read_text())['streams'])
  expected.update(('experimental_injury_issue','experimental_injury_refresh','experimental_injury_n040','experimental_injury_n041'))
  self.assertEqual(expected,{m['id']for m in d['models']})
 def test_actual_forward_issues_do_not_borrow_retrospective_metrics(self):
  for m in build_registry()['models']:
   if m['kind']=='GENUINELY_ISSUED_EARLY_RESEARCH':self.assertEqual(m['records'],[]);self.assertEqual(m['issued_resolved_games'],0)
 def test_legacy_metric_rows_equal_published_cohorts(self):
  for m in build_registry()['models']:
   if m['kind']=='PRESERVED_PUBLIC_STREAM':self.assertEqual(m['records'],[x for x in self.coverage['season_metrics']if x['model_id']==m['id']])
 def test_no_unverified_cover_probabilities(self):
  self.assertTrue(all(m['target_readiness']['spread_cover']['status']==('ISSUED_UNVALIDATED_DISTRIBUTION_TRANSFER' if m['id'] in ('n047_designation','n048_designation')else 'NOT_CALIBRATED_FOR_EXECUTABLE_LINE')for m in build_registry()['models']))
 def test_current_and_historical_provider_census(self):
  self.assertEqual(len(load_current_source(self.coverage)[0]['coverage']),9);self.assertEqual(load_historical_reference(self.coverage)[1]['latest_kalshi_polymarket_games_each'],121)
 def test_designation_unknown_block_cannot_become_complete(self):
  d=copy.deepcopy(self.issues);c=d['streams'][-1]['cards'][1];c['designation_report_teams_known']={k:True for k in c['designation_report_teams_known']}
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_completed_game_cannot_become_new_issue(self):
  d=copy.deepcopy(self.issues);d['streams'][-1]['cards'][0]['game_id']='2026_08_CHI_SEA'
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_source_after_issue_rejected(self):
  d=copy.deepcopy(self.issues);d['streams'][-1]['cards'][0]['base_feature_asof_at']='2026-11-06T02:00:00+00:00'
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_unsupported_acceptance_rejected(self):
  d=copy.deepcopy(self.issues);d['owner_pipeline_accepted']=True
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
if __name__=='__main__':unittest.main()
