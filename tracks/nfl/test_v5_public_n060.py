"""Prevent unsupported execution, exposure, metric and privacy claims in V5 UI."""
import copy,gzip,json,unittest
from build_season_review_n054 import HERE,load,validate,build

class V5PublicN060(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=load(HERE/'public_projection_n060.json.gz')
    def rejects(self,mutate):
        data=copy.deepcopy(self.data);mutate(data)
        with self.assertRaises(ValueError):validate(data)
    def test_all_inherited_n059_public_evidence_exact(self):
        prior=json.loads(gzip.decompress((HERE/'public_projection_n059.json.gz').read_bytes()))
        for key,value in prior.items():
            if key not in {'schema','publication_cycle'}:self.assertEqual(self.data[key],value,key)
    def test_execution_and_scientific_cycles_are_separate(self):
        status=self.data['n060_owner_status']
        self.assertEqual((status['cycle'],status['latest_scientific_cycle']),('N059','N058'))
        self.assertEqual((status['new_fits'],status['new_forecasts'],status['completed_research_stages']),(0,0,0))
        self.assertEqual(self.data['counts']['actual_latest_native_fits'],27)
    def test_five_lanes_and_three_targets(self):
        rows=self.data['v5_scope']['comparison_lanes'];self.assertEqual(len(rows),15)
        self.assertEqual(len({r['lane'] for r in rows}),5)
        self.assertTrue(all(r['evaluated_games']==0 and r['eligible_games'] is None for r in rows))
    def test_zero_owner_features_distinct_from_implementation(self):
        counts=self.data['v5_scope']['candidate_counts']
        self.assertEqual(counts['inherited_proposed'],211)
        self.assertTrue(all(counts[k]==0 for k in ['owner_materialized','owner_admitted','owner_evaluated','owner_promoted']))
    def test_invented_log_loss_rejected(self):self.rejects(lambda d:d['v5_scope']['comparison_lanes'][0].update(log_loss=.5))
    def test_invented_admission_rejected(self):self.rejects(lambda d:d['v5_scope']['candidate_counts'].update(owner_admitted=1))
    def test_invented_fit_rejected(self):self.rejects(lambda d:d['n060_owner_status'].update(new_fits=1))
    def test_shadow_promotion_rejected(self):self.rejects(lambda d:d['v5_scope'].update(automatic_promotion=True))
    def test_missing_exposure_rejected(self):self.rejects(lambda d:d['v5_scope']['evaluation_exposure'].pop())
    def test_missing_comparison_target_rejected(self):self.rejects(lambda d:d['v5_scope']['comparison_lanes'].pop())
    def test_false_population_rejected(self):self.rejects(lambda d:d['v5_scope']['comparison_lanes'][0].update(eligible_games=272))
    def test_failure_relabel_rejected(self):self.rejects(lambda d:d['n060_owner_status'].update(status='COMPLETED'))
    def test_private_params_rejected(self):self.rejects(lambda d:d['v5_scope'].update(learning_rate=.2))
    def test_private_support_text_rejected(self):self.rejects(lambda d:d['v5_scope']['support_status'].append('s3://private/path'))
    def test_template_exposes_v5_controls_without_new_scores(self):
        body=build(self.data)
        for marker in ['id="v5-target"','id="v5-comparison-table"','id="v5-exposure-table"','id="v5-feature-counts"']:
            self.assertIn(marker,body)
        self.assertIn('Evaluation exposure',body)

if __name__=='__main__':unittest.main()
