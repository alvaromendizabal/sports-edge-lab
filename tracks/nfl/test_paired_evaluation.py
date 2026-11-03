"""Negative cases and scientific invariants for the public invented example."""
import copy
import math
import unittest

from paired_evaluation import (
    _scores, calibration, confidence_diagnostics, invented_fixture,
    paired_week_bootstrap,
)
from uniform_comparison import compare_fixed_cohort


class PairedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.contract,self.games,self.models,self.refs,self.clusters=invented_fixture()

    def comparison(self):
        return compare_fixed_cohort(self.contract,self.games,self.models,self.refs)

    def bootstrap(self,result=None,clusters=None,**kwargs):
        return paired_week_bootstrap(
            self.comparison() if result is None else result,
            self.clusters if clusters is None else clusters,
            resamples=100,**kwargs)

    def test_identical_predictions_have_zero_paired_uncertainty(self):
        for model,ref in zip(self.models,self.refs):ref['value']=model['value']
        result=self.bootstrap()
        for interval in result['intervals'].values():
            self.assertEqual(interval,dict(advantage=0.,lower_95=0.,upper_95=0.))
        self.assertFalse(result['selection_adjusted'])
        self.assertFalse(result['model_refitted_in_resamples'])
        self.assertFalse(result['interweek_dependence_preserved'])

    def test_seed_and_row_order_are_reproducible_without_mutation(self):
        result=self.comparison(); original=copy.deepcopy(result)
        before=self.bootstrap(result)
        self.assertEqual(result,original)
        result['ledger'].reverse()
        self.assertEqual(before,self.bootstrap(result,dict(reversed(list(self.clusters.items())))))

    def test_swapping_model_and_reference_reverses_advantages_and_intervals(self):
        result=self.comparison(); before=self.bootstrap(result)
        for row in result['ledger']:row['model'],row['reference']=row['reference'],row['model']
        after=self.bootstrap(result)
        for metric,a in before['intervals'].items():
            b=after['intervals'][metric]
            self.assertAlmostEqual(a['advantage'],-b['advantage'])
            self.assertAlmostEqual(a['lower_95'],-b['upper_95'])
            self.assertAlmostEqual(a['upper_95'],-b['lower_95'])

    def test_advantage_matches_independent_complete_cohort_scores(self):
        result=self.comparison(); intervals=self.bootstrap(result)['intervals']
        model=result['headline_scores']['model']; ref=result['headline_scores']['reference']
        for metric,sign in [('log_loss',-1),('brier',-1),('accuracy',1)]:
            self.assertAlmostEqual(intervals[metric]['advantage'],sign*(model[metric]-ref[metric]))

    def test_missing_provider_blocks_bootstrap_but_diagnostics_label_subset(self):
        self.refs.pop();result=self.comparison()
        with self.assertRaisesRegex(ValueError,'shrunken'):self.bootstrap(result)
        d=confidence_diagnostics(result)
        self.assertEqual(d['coverage_scope'],'INCOMPLETE_FIXED_COHORT')
        self.assertEqual((d['fixed_n'],d['matched_n']),(12,11))
        self.assertNotEqual(d['fixed_cohort_sha256'],d['evaluated_cohort_sha256'])

    def test_inconsistent_counts_cannot_disguise_subset_as_complete(self):
        for field,value in [('fixed_n',11),('matched_n',11),('matched_n',True),
                            ('fixed_cohort_sha256','wrong')]:
            with self.subTest(field=field,value=value):
                result=self.comparison();result[field]=value
                with self.assertRaises(ValueError):self.bootstrap(result)

    def test_duplicate_and_outside_cohort_matches_fail(self):
        result=self.comparison();result['ledger'].append(copy.deepcopy(result['ledger'][0]))
        with self.assertRaises(ValueError):self.bootstrap(result)
        result=self.comparison();result['ledger'][0]['in_fixed_cohort']=False
        with self.assertRaises(ValueError):confidence_diagnostics(result)

    def test_cluster_mapping_is_exact_and_requires_multiple_clusters(self):
        invalid=[None,{},dict(self.clusters,extra='invented-season:REG_99'),
                 {k:'' for k in self.clusters},{k:True for k in self.clusters},
                 {k:'one-week' for k in self.clusters}]
        for clusters in invalid:
            with self.subTest(clusters=clusters):
                with self.assertRaises(ValueError):
                    paired_week_bootstrap(self.comparison(),clusters,resamples=100)

    def test_whole_week_resampling_preserves_unequal_cluster_sizes(self):
        # Three positive-advantage games share week A, one negative game week B.
        # The observed statistic weights games, while a replicate samples two
        # complete weeks, producing only advantage -0.6, +0.3 or +0.6.
        self.contract['game_ids']=self.contract['game_ids'][:4]
        from uniform_comparison import cohort_digest
        self.contract['cohort_sha256']=cohort_digest(self.contract['game_ids'])
        self.games=self.games[:4];self.models=self.models[:4];self.refs=self.refs[:4]
        self.clusters={r['game_id']:('A' if i<3 else 'B') for i,r in enumerate(self.games)}
        for i,(g,m,r) in enumerate(zip(self.games,self.models,self.refs)):
            g['actual']=1;m['value']=.8 if i<3 else .2;r['value']=.2 if i<3 else .8
        intervals=self.bootstrap()['intervals']
        self.assertAlmostEqual(intervals['brier']['advantage'],.3)
        self.assertAlmostEqual(intervals['brier']['lower_95'],-.6)
        self.assertAlmostEqual(intervals['brier']['upper_95'],.6)

    def test_invalid_numeric_values_rejected_on_both_sides(self):
        for field in ('model','reference'):
            for value in (float('nan'),float('inf'),True,-.1,1.1):
                with self.subTest(field=field,value=value):
                    result=self.comparison();result['ledger'][0][field]=value
                    with self.assertRaises(ValueError):confidence_diagnostics(result)
                    with self.assertRaises(ValueError):self.bootstrap(result)

    def test_confidence_uses_chosen_side_and_excludes_exact_sixty(self):
        result=self.comparison()
        cases=[(.45,.8,1),(.40,.8,1),(.50,.4,0),(.59,.4,0)]
        for row,(p,ref,actual) in zip(result['ledger'],cases*3):
            row.update(model=p,reference=ref,actual=actual)
        d=confidence_diagnostics(result)
        self.assertEqual(d['reference_only_right'],12)
        self.assertEqual(d['losing_disagreements_in_50s'],9)
        self.assertEqual(d['disagreements'][0]['model_pick'],'AWAY')
        self.assertAlmostEqual(d['disagreements'][0]['model_pick_probability'],.55)
        self.assertFalse(d['disagreements'][1]['confidence_in_50s'])
        self.assertEqual(d['disagreements'][2]['model_pick'],'HOME')

    def test_empty_matched_subset_is_explicit_not_all_season_zero_record(self):
        self.refs=[];d=confidence_diagnostics(self.comparison())
        self.assertEqual(d['matched_n'],0)
        self.assertEqual(d['coverage_scope'],'INCOMPLETE_FIXED_COHORT')
        self.assertEqual(d['disagreements'],[])

    def test_calibration_boundaries_and_independent_ece(self):
        rows=[dict(model=0.,actual=0),dict(model=.5,actual=1),dict(model=1.,actual=1)]
        result=calibration(iter(rows),'model',bins=2)
        self.assertEqual([b['n'] for b in result['bins']],[1,2])
        self.assertAlmostEqual(result['ece'],1/6)
        self.assertTrue(result['bins'][-1]['upper_inclusive'])
        self.assertIsNone(calibration([],'model')['ece'])
        for bins in (True,1,101,2.5):
            with self.assertRaises(ValueError):calibration(rows,'model',bins=bins)

    def test_point_scores_bias_and_large_finite_rmse(self):
        rows=[dict(actual=10.,model=13.),dict(actual=10.,model=9.)]
        scores=_scores(rows,'margin','model')
        self.assertEqual(scores['mae'],2.)
        self.assertEqual(scores['bias'],1.)
        self.assertAlmostEqual(scores['rmse'],math.sqrt(5))
        large=_scores([dict(actual=0.,model=1.7e308)]*2,'margin','model')
        self.assertTrue(math.isfinite(large['rmse']))
        self.assertAlmostEqual(large['rmse']/1.7e308,1.)
        with self.assertRaises(ValueError):_scores([dict(actual=-1e308,model=1e308)],'margin','model')
        with self.assertRaises(ValueError):_scores([dict(actual=-1,model=1)],'total','model')

    def test_probability_diagnostics_cannot_be_applied_to_point_target(self):
        result=self.comparison();result['target']='margin'
        with self.assertRaises(ValueError):confidence_diagnostics(result)

    def test_seed_and_resample_validation(self):
        for seed,resamples in [(True,100),(2024,99),(2024,100001),(2024,True)]:
            with self.assertRaises(ValueError):
                paired_week_bootstrap(self.comparison(),self.clusters,seed=seed,resamples=resamples)


if __name__=='__main__':unittest.main()
