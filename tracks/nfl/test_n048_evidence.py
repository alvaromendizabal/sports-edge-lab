import copy,json,unittest
from pathlib import Path
from current_issues_n048 import validate_current_issues
from current_cover_n048 import validate_current_cover
from current_source_n048 import validate_current_source
from injury_only_n048 import validate_study
HERE=Path(__file__).resolve().parent
class N048EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.coverage=json.loads((HERE/'current_coverage.json').read_text());cls.issues=json.loads((HERE/'current_issues_n048.json').read_text());cls.cover=json.loads((HERE/'current_cover_n048.json').read_text());cls.study=json.loads((HERE/'injury_only_n048.json').read_text());cls.source=json.loads((HERE/'current_source_n048.json').read_text())
 def test_current_four_streams_close(self):validate_current_issues(self.issues,self.coverage)
 def test_restored_current_cannot_claim_historical_new_fits(self):
  d=copy.deepcopy(self.issues);d['new_native_fits']=288
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_partial_owner_not_promoted(self):
  d=copy.deepcopy(self.issues);d['owner_pipeline_accepted']=True
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_cover_predicates_and_stale_fit_clock(self):validate_current_cover(self.cover,self.coverage,self.issues)
 def test_less_predicate_cannot_use_above_probability(self):
  d=copy.deepcopy(self.cover);r=next(r for r in d['threshold_rows']if r['orientation'].endswith('LESS_THAN')and r['probability_above_threshold']!=r['probability_below_threshold']);r['probability_of_observed_margin_predicate']=r['probability_above_threshold']
  with self.assertRaises(ValueError):validate_current_cover(d,self.coverage,self.issues)
 def test_unknown_settlement_cannot_be_scored(self):
  d=copy.deepcopy(self.cover);r=next(r for r in d['threshold_rows']if r['settlement_policy']=='UNKNOWN');r['scoring_probability']=.6
  with self.assertRaises(ValueError):validate_current_cover(d,self.coverage,self.issues)
 def test_future_quote_rejected(self):
  d=copy.deepcopy(self.cover);d['threshold_rows'][0]['observed_at_utc']='2026-12-01T00:00:00Z'
  with self.assertRaises(ValueError):validate_current_cover(d,self.coverage,self.issues)
 def test_all_study_cells_and_candidates(self):validate_study(self.study)
 def test_missing_historical_support_not_healthy(self):
  d=copy.deepcopy(self.study);next(r for r in d['source_support']if r['season']==2026)['both_teams_injury75_supported']=120
  with self.assertRaises(ValueError):validate_study(d)
 def test_historical_candidate_not_issued(self):
  d=copy.deepcopy(self.study);d['research_candidates'][0]['forecast_status']='ISSUED'
  with self.assertRaises(ValueError):validate_study(d)
 def test_new_pregame_exclusions_are_explicit(self):
  validate_current_source(self.source,self.coverage)
  for group in('winner_rows','point_rows'):
   rs=[r for r in self.source[group]if r['game_id']=='2026_09_JAX_BAL'];self.assertTrue(rs);self.assertTrue(all(r['availability_status']=='NO_QUALIFIED_CURRENT_REFERENCE'for r in rs))
 def test_market_path_full_status_closure(self):
  d=json.loads((HERE/'market_paths_n048.json').read_text());rows=d['cells'];self.assertEqual(len(rows),1089);self.assertEqual(len({(r['game_id'],r['provider'],r['target'])for r in rows}),1089);self.assertEqual(sum(r['rows']for r in rows),172373);self.assertEqual(sum(r['contracts']for r in rows),936);self.assertEqual(len({r['game_id']for r in rows if r['provider']=='polymarket'and not r['rows']}),8);self.assertEqual(len({r['game_id']for r in rows}),121)
