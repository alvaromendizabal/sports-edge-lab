import copy
import json
from pathlib import Path
import unittest
from model_market_public import validate_public, scores

ROOT=Path(__file__).parent

class PublicModelMarketTests(unittest.TestCase):
    def test_metric_projection_keeps_only_matching_game_counts(self):
        self.assertEqual(scores({'games':3,'brier':.2,'private_aux':'excluded'},3),{'brier':.2})
        with self.assertRaisesRegex(ValueError,'denominators'): scores({'games':2,'brier':.2},3)

    @classmethod
    def setUpClass(cls):
        cls.value=json.loads((ROOT/'model_market_comparison.json').read_bytes())
        cls.models=json.loads((ROOT/'equal_cohort_scoreboard.json').read_bytes())

    def test_complete_required_population_remains_192(self):
        checked=validate_public(self.value,self.models)
        self.assertEqual(len(checked['groups']),18)
        for g in checked['groups']:
            self.assertEqual((g['required_games'],g['market_games'],g['missing_market_games']),(192,183,9))
            self.assertFalse(g['all_required_candidates_complete'])
            self.assertTrue(all(m['full_model_metrics'] is None and m['full_market_metrics'] is None for m in g['models']))

    def test_partial_diagnostic_cannot_become_full_score(self):
        value=copy.deepcopy(self.value);m=value['groups'][0]['models'][0]
        m['full_model_metrics']={'mae':1.0}
        with self.assertRaisesRegex(ValueError,'Partial'): validate_public(value,self.models)

    def test_different_membership_or_omitted_candidate_rejected(self):
        value=copy.deepcopy(self.value);value['groups'][0]['population_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'population'): validate_public(value,self.models)
        value=copy.deepcopy(self.value);value['groups'][0]['models'].pop()
        with self.assertRaisesRegex(ValueError,'candidates'): validate_public(value,self.models)

    def test_private_game_array_and_exposed_test_relabeling_rejected(self):
        value=copy.deepcopy(self.value);value['groups'][0]['event_ids']=['private']
        with self.assertRaisesRegex(ValueError,'Private'): validate_public(value,self.models)
        value=copy.deepcopy(self.value);value['current_test_previously_exposed']=False
        with self.assertRaisesRegex(ValueError,'policy'): validate_public(value,self.models)

if __name__=='__main__': unittest.main()
