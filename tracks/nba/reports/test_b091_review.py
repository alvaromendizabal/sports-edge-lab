"""Review boundary and same-population failure checks using public aggregates."""
import copy
import json
from pathlib import Path
import unittest
from build_b091_review import build, validate

ROOT=Path(__file__).resolve().parent

class ReviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.value=json.loads((ROOT/'B091_CHAMPION_AUDIT_PUBLIC.json').read_text())
    def test_exact_generated_review_and_offline_payload(self):
        output=build();self.assertEqual(output,(ROOT/'b091_review.html').read_bytes())
        self.assertNotIn(b'fetch(',output);self.assertIn(b'id="b091-source-acquisition"',output)
        self.assertIn(b'href="season_comparison.html"',output)
    def test_missing_game_cannot_shrink_the_current_denominator(self):
        for key,number in [('required_games',196)]:
            bad=copy.deepcopy(self.value);bad['current_descriptive_cells'][0][key]=number
            with self.assertRaisesRegex(ValueError,'population'): validate(bad)
        bad=copy.deepcopy(self.value);bad['current_descriptive_cells'][0]['metrics']['games']=196
        with self.assertRaisesRegex(ValueError,'population'): validate(bad)
        bad=copy.deepcopy(self.value);bad['current_descriptive_cells'][0]['population_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'population'): validate(bad)
    def test_reconstruction_cannot_claim_strict_or_original_evidence(self):
        for key,value in [('original_issued_claim',True),('promotion_eligible',True),('strict_point_in_time_metrics',{'brier':0.1})]:
            bad=copy.deepcopy(self.value);bad['current_descriptive_cells'][0][key]=value
            with self.assertRaisesRegex(ValueError,'Reconstruction'): validate(bad)
    def test_private_recipes_fields_and_paths_rejected(self):
        for key,value in [('recipe_id','private-recipe'),('raw_payload',[1,2]),('source_path','private-object')]:
            bad=copy.deepcopy(self.value);bad[key]=value
            with self.assertRaisesRegex(ValueError,'Private'): validate(bad)
        bad=copy.deepcopy(self.value);bad['models'][0]['model_id']='internal-recipe-hash'
        with self.assertRaisesRegex(ValueError,'public alias'): validate(bad)
        bad=copy.deepcopy(self.value);bad['limitations'].append('s3://private/location')
        with self.assertRaisesRegex(ValueError,'Private'): validate(bad)
    def test_current_scores_cannot_change_validation_roles(self):
        changed=copy.deepcopy(self.value)
        for cell in changed['current_descriptive_cells']:
            for key in ('brier','log_loss','mae','rmse','accuracy'):
                if key in cell['metrics']: cell['metrics'][key]=0.001
        validate(changed)
        self.assertEqual(changed['roles'],self.value['roles'])
        bad=copy.deepcopy(self.value);bad['final_champions_selected']=True
        with self.assertRaisesRegex(ValueError,'promotion'): validate(bad)
    def test_comparison_only_policy_is_required(self):
        bad=copy.deepcopy(self.value);bad['source_policy']['comparison_only_providers']=['Kalshi','Polymarket']
        with self.assertRaisesRegex(ValueError,'Comparison-only'): validate(bad)

if __name__=='__main__': unittest.main()
