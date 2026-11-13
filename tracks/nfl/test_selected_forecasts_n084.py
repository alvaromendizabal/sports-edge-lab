"""Actual N083 publication identities, temporal exclusions and cohort boundaries."""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
import selected_review_n084 as view
ROOT=Path(__file__).parent
RAW=(ROOT/view.FORECAST).read_bytes()
DATA=json.loads(RAW)

class ActualN083PublicationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.health=json.loads((ROOT/view.HEALTH).read_bytes())
 def test_all_lifecycle_counts(self):
  self.assertEqual(view.audit(DATA),dict(completed=137,upcoming=111,live_or_awaiting_final=0,tbd=24,current_issued_rows=444,current_issued_games=111))
 def test_duplicate_game_rejected(self):
  d=copy.deepcopy(DATA);d['games'][1]['game_id']=d['games'][0]['game_id']
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):view.audit(d)
 def test_changed_census_rejected(self):
  h=copy.deepcopy(self.health);h['saved_census']['completed']=136
  with self.assertRaisesRegex(ValueError,'CENSUS'):view.validate(RAW,h)
 def test_naive_clock_rejected(self):
  d=copy.deepcopy(DATA);d['display_cutoff_utc']='2026-11-13T06:51:24'
  with self.assertRaisesRegex(ValueError,'NAIVE'):view.audit(d)
 def test_exact_projection_and_final_result(self):
  self.assertEqual(hashlib.sha256(RAW).hexdigest(),self.health['selected_forecasts_sha256'])
  g=next(g for g in DATA['games']if g['game_id']=='2026_10_WAS_NYG')
  self.assertEqual((g['completed_in_saved_census'],g['away_score'],g['home_score']),(True,24,21))
  self.assertTrue(all(not p['current_forecasts']for p in g['targets'].values()))
  self.assertTrue(any(p['earlier_saved_forward']for p in g['targets'].values()))
 def test_exact_page_and_stated_pacific_clock(self):
  page=view.render(RAW,self.health)
  self.assertEqual(page,(ROOT/'season_review_n084.html').read_text())
  self.assertIn('November 12, 2026 at 22:51:24 Pacific (PST)',page)
 def test_source_boundary(self):
  body=RAW.decode()+json.dumps(self.health)
  for forbidden in ('/home/','s3://','"recipe_id"','"parameters"','"feature_columns"','"model_weights"','FITTED_MODEL.bin'):
   self.assertNotIn(forbidden,body)
  self.assertIsNone(re.search(r'\b[0-9a-f]{24}\b',body))
 def test_original_projection_change_rejected(self):
  with self.assertRaisesRegex(ValueError,'BYTES_CHANGED'):view.validate(RAW+b' ',self.health)
 def test_fabricated_science_or_promotion_rejected(self):
  for key,value in [('new_fits',0),('new_native_fits',376),('owner_research_acceptance',True),('new_n084_owner_science_claimed',True),('automatic_promotion',True),('new_qualified_market_comparison_cells',1)]:
   with self.subTest(key=key):
    h=copy.deepcopy(self.health);h[key]=value
    with self.assertRaises(ValueError):view.validate(RAW,h)
 def test_preserved_card_loss_rejected(self):
  h=copy.deepcopy(self.health);h['preserved_cards'].pop()
  with self.assertRaisesRegex(ValueError,'FORMER_SCORECARDS'):view.validate(RAW,h)
 def test_historical_future_label_or_card_loss_rejected(self):
  for mutate in (lambda h:h['historical_cards'].pop(),lambda h:h['historical_cards'][0].update(season=2026)):
   h=copy.deepcopy(self.health);mutate(h)
   with self.assertRaises(ValueError):view.validate(RAW,h)
 def test_historical_omission_cannot_disappear(self):
  self.assertEqual(len(self.health['all_historical_cards']),1320)
  restored=self.health['preserved_omitted_historical_cards'];self.assertEqual(len(restored),48)
  self.assertTrue(all(c in self.health['all_historical_cards'] for c in restored))
  h=copy.deepcopy(self.health);h['all_historical_cards'].pop()
  with self.assertRaisesRegex(ValueError,'HISTORICAL_LEDGER'):view.validate(RAW,h)
 def test_monitor_backdating_rejected(self):
  h=copy.deepcopy(self.health);h['monitor_cards'][0]['original_issue_credit']=1
  with self.assertRaisesRegex(ValueError,'MONITOR_ISSUE'):view.validate(RAW,h)
 def test_cohort_substitution_rejected(self):
  h=copy.deepcopy(self.health);h['monitor_leaders'][0]['cohort_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'LEADER_COHORT'):view.validate(RAW,h)
 def test_leader_relabel_or_support_change_rejected(self):
  for key,value in [('model_aliases',['invented']),('games',1)]:
   h=copy.deepcopy(self.health);h['monitor_leaders'][0][key]=value
   with self.assertRaisesRegex(ValueError,'LEADER_IDENTITY'):view.validate(RAW,h)
 def test_no_current_outcomes_select_or_promote(self):
  self.assertFalse(DATA['automatic_promotion']);self.assertFalse(self.health['automatic_promotion'])
  self.assertTrue(all(c['season']in(2024,2025)for c in self.health['historical_cards']))
 def test_legacy_rows_and_missing_cohort_remain_qualified(self):
  cards=self.health['legacy_cards'];self.assertEqual(len(cards),333)
  self.assertEqual(sum(c['cohort_sha256'] is None for c in cards),9)
  self.assertEqual(sum(c['evidence_class']=='EARLY_FORWARD_RESEARCH_ISSUE'for c in cards),9)
  self.assertTrue(all(not c['new_model_fits'] and not c['new_frozen_policy_retraining'] and not c['frozen_champion_selection_eligible']for c in cards))
 def test_old_leaders_retained(self):
  old=json.loads((ROOT/'2026-11-13-n082-actual-n083-review.json').read_bytes())
  leaders=copy.deepcopy(old['selected_2026_descriptive_leaders'])
  for row in leaders:row['model_aliases']=['N079 / '+a for a in row['model_aliases']]
  self.assertEqual(len(leaders),35);self.assertEqual(leaders,self.health['preserved_leaders'])
 def test_old_cards_exact_preserved(self):
  old=json.loads((ROOT/'2026-11-13-n082-actual-n083-review.json').read_bytes())
  oldcards=copy.deepcopy(old['selected_and_retained_2026_scorecards'])
  for c in oldcards:c['model_alias']='N079 / '+c['model_alias']
  self.assertEqual(oldcards,self.health['preserved_cards'])

if __name__=='__main__':unittest.main()
