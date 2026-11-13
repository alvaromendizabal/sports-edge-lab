import unittest,json,copy
from pathlib import Path
from selected_review_n084 import validate,render,FORECAST,HEALTH
R=Path(__file__).parent
class N084(unittest.TestCase):
 def setUp(self):self.raw=(R/FORECAST).read_bytes();self.h=json.loads((R/HEALTH).read_bytes())
 def test_actual_counts(self):
  p=validate(self.raw,self.h);self.assertEqual((len(p['games']),p['counts']['completed_games'],p['counts']['current_selected_games'],p['counts']['official_time_tbd_games']),(272,137,111,24));self.assertEqual(len(self.h['new_historical']['cards']),120)
 def test_reject_corruption(self):
  with self.assertRaisesRegex(ValueError,'DIGEST'):validate(self.raw+b' ',self.h)
 def test_reject_promotion(self):
  self.h['automatic_promotion']=True
  with self.assertRaisesRegex(ValueError,'PROMOTION'):validate(self.raw,self.h)
 def test_reject_market_fabrication(self):
  self.h['qualified_provider_comparison_cells']=1
  with self.assertRaisesRegex(ValueError,'ACCEPTANCE'):validate(self.raw,self.h)
 def test_reject_fit_double_count(self):
  self.h['new_fits']+=1
  with self.assertRaisesRegex(ValueError,'FIT_ACCOUNTING'):validate(self.raw,self.h)
 def test_render_reentry(self):self.assertEqual(render(self.raw,self.h),(R/'season_review_n084.html').read_text())
 def test_boundary(self):
  for name in (FORECAST,HEALTH,'season_review_n084.html'):
   text=(R/name).read_text()
   for token in ('s3://','/home/sagemaker-user','560403859723','recipe_id','apiKey='):
    self.assertNotIn(token,text)
if __name__=='__main__':unittest.main()
