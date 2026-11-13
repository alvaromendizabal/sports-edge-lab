import copy,hashlib,json,re,unittest
from pathlib import Path
import selected_review_n084 as view
ROOT=Path(__file__).parent
RAW=(ROOT/view.FORECAST).read_bytes();DATA=json.loads(RAW);HEALTH=json.loads((ROOT/view.HEALTH).read_bytes())
class N084PublicationTests(unittest.TestCase):
 def test_full_denominator_and_current_projection(self):
  self.assertEqual(view.audit(DATA),dict(completed=137,upcoming=111,live_or_awaiting_final=0,tbd=24,current_issued_rows=444,current_issued_games=111))
  self.assertEqual(hashlib.sha256(RAW).hexdigest(),HEALTH['selected_forecasts_sha256'])
 def test_final_result_preserves_pregame_evidence(self):
  g=next(g for g in DATA['games'] if g['game_id']=='2026_10_WAS_NYG')
  self.assertEqual((g['away_score'],g['home_score']),(24,21));self.assertTrue(g['completed_in_saved_census'])
  self.assertTrue(all(not t['current_forecasts'] for t in g['targets'].values()))
  self.assertTrue(any(t['earlier_saved_forward'] for t in g['targets'].values()))
 def test_exact_fits_and_no_acceptance_inflation(self):
  self.assertEqual((HEALTH['new_fits'],HEALTH['new_native_fits'],HEALTH['new_meta_fits']),(376,354,22))
  bad=copy.deepcopy(HEALTH);bad['owner_research_acceptance']=True
  with self.assertRaisesRegex(ValueError,'ACCEPTANCE'):view.render(DATA,bad)
 def test_new_scorecards_preserved(self):
  rows=HEALTH['new_frozen_cards'];self.assertEqual(len(rows),120);self.assertEqual(len({r['model_alias'] for r in rows}),60)
  self.assertEqual({r['season'] for r in rows},{2024,2025});self.assertEqual({r['horizon_seconds'] for r in rows},{3600})
 def test_previous_2026_cards_stay_dated(self):
  self.assertEqual(len(HEALTH['old_2026_cards']),77);self.assertEqual(len(HEALTH['old_2026_leaders']),35)
  self.assertIn('not updated N083',HEALTH['old_2026_scope'])
 def test_deterministic_saved_page(self):
  self.assertEqual((ROOT/'season_review_n084.html').read_text(),view.render(DATA,HEALTH))
 def test_duplicate_games_rejected(self):
  d=copy.deepcopy(DATA);d['games'][1]['game_id']=d['games'][0]['game_id']
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):view.render(d,HEALTH)
 def test_changed_census_rejected(self):
  d=copy.deepcopy(HEALTH);d['saved_census']['completed']=136
  with self.assertRaisesRegex(ValueError,'CENSUS'):view.render(DATA,d)
 def test_public_boundary(self):
  text=RAW.decode()+json.dumps(HEALTH)
  for token in ['s3://','/home/','"recipe_id"','"feature_columns"','"parameters"','"model_weights"','FITTED_MODEL.bin']:self.assertNotIn(token,text)
  self.assertIsNone(re.search(r'\b[0-9a-f]{24}\b',text))
if __name__=='__main__':unittest.main()
