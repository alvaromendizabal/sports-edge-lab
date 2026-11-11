"""Later failure must never reduce valid forecast coverage or earn issue credit."""
import copy,hashlib,json,unittest
from pathlib import Path
from selected_review_n074 import render,HEALTH
HERE=Path(__file__).resolve().parent
class N073FailureContinuity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=(HERE/'selected_forecasts_n073.json').read_bytes();cls.data=json.loads(cls.original);cls.health=json.loads((HERE/HEALTH).read_bytes());cls.page=(HERE/'season_review_n074.html').read_text()
 def test_saved_page_exactly_reopens(self):self.assertEqual(self.page,render(self.original,self.health))
 def test_original_forecast_payload_retained(self):
  start=self.page.index('<script id="selected-data" type="application/json">')+len('<script id="selected-data" type="application/json">');end=self.page.index('</script>',start)
  self.assertEqual(json.loads(self.page[start:end]),self.data)
  self.assertEqual(hashlib.sha256(self.original).hexdigest(),self.health['retained_forecasts']['sha256'])
 def test_no_coverage_downgrade(self):
  r=self.health['retained_forecasts'];self.assertEqual((r['selected_rows'],r['future_games'],r['historical_primary_roles'],r['fallback_roles']),(772,112,18,9))
  self.assertEqual(len(self.data['games']),272);self.assertEqual(len(self.data['selected_historical_roles']),27)
  self.assertEqual(sum(len(t['current_forecasts'])for g in self.data['games']for t in g['targets'].values()),772)
 def test_failure_totals_remain_unknown(self):
  self.assertIsNone(self.health['new_fits']);self.assertIsNone(self.health['new_forecasts'])
  self.assertEqual(self.health['verified_new_fit_minimum'],0);self.assertEqual(self.health['verified_new_issue_minimum'],0)
  self.assertIn('Latest execution: N073 blocked',self.page);self.assertIn('Forecast-producing execution: retained N072 evidence',self.page)
 def test_no_reissue_or_promotion(self):
  self.assertFalse(self.health['automatic_promotion']);self.assertFalse(self.health['owner_research_acceptance'])
  self.assertFalse(self.health['retained_forecasts']['reissued']);self.assertFalse(self.health['new_release']['owner_executed'])
  for key in ('new_fit_credit','new_inference_credit','new_issue_credit'):self.assertEqual(self.health['retained_forecasts'][key],0)
 def test_reject_mutated_original_bytes(self):
  with self.assertRaisesRegex(ValueError,'RETAINED_FORECAST_BYTES_CHANGED'):render(self.original+b' ',self.health)
 def test_reject_false_promotion(self):
  h=copy.deepcopy(self.health);h['automatic_promotion']=True
  with self.assertRaisesRegex(ValueError,'CANNOT_PROMOTE_OR_REISSUE'):render(self.original,h)
 def test_source_capture_is_not_admitted_science(self):
  s=self.health['source_activity'];self.assertEqual(s['normalized_market_rows'],s['kalshi_rows']+s['polymarket_rows']);self.assertEqual(s['qualified_current_winner_probabilities'],0);self.assertEqual(s['earlier_game_response_studies_executed'],0)
 def test_escape_failure_text(self):
  h=copy.deepcopy(self.health);h['failures'][0]['effect']='</section><script>unsafe()</script>'
  self.assertNotIn('</section><script>unsafe()</script>',render(self.original,h))
 def test_no_private_payload(self):
  s=json.dumps(self.health)
  for token in ('recipe_id','s3://','api_key','/home/sagemaker-user','sagemaker-sports-edge-lab'):self.assertNotIn(token,s)
  self.assertFalse(self.health['publication']['raw_provider_values_included']);self.assertFalse(self.health['publication']['website_deployed'])
if __name__=='__main__':unittest.main()
