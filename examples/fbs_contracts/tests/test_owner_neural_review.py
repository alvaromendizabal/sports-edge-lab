import json
import unittest
from collections import Counter
from pathlib import Path
from examples.fbs_contracts.build_owner_neural_review import ALIASES, PINS

ROOT = Path(__file__).resolve().parents[3]
D = json.loads((ROOT/'docs/fbs/owner-neural-study.json').read_text())
T = json.loads((ROOT/'docs/fbs/three-season.json').read_text())


class OwnerNeuralReviewTests(unittest.TestCase):
    def test_original_owner_work_is_not_recounted_as_new_publication_fits(self):
        self.assertEqual(D['counts']['original_owner_completed_base_fits'],1362)
        self.assertEqual(D['counts']['original_owner_completed_calibration_fits'],454)
        self.assertEqual(D['counts']['original_owner_prediction_outputs'],21627)
        for field in ('current_reporting_new_fits','current_reporting_new_predictions','current_reporting_provider_requests'):
            self.assertEqual(D[field],0)
        self.assertEqual(D['default_selection_unchanged'],'V038 fixed_equal_blend')
        for field in ('forecast_issued','historical_availability_proved','promotion_allowed'):
            self.assertIs(D[field],False)
        self.assertTrue(D['registered_workload_complete'])

    def test_all_saved_families_and_targets_keep_exact_fixture_clocks(self):
        games = {r['id']:r for r in T['rows']}
        self.assertEqual(len(D['rows']),2403)
        self.assertEqual(len({r['id'] for r in D['rows']}),2403)
        self.assertEqual(Counter(r['season'] for r in D['rows']),{2024:679,2025:934,2026:790})
        self.assertEqual(sum(games[r['id']]['period']=='current' for r in D['rows']),63)
        self.assertEqual(sum(games[r['id']]['period']=='previous' for r in D['rows']),56)
        for row in D['rows']:
            g = games[row['id']]
            self.assertTrue(g['kickoff_exact'])
            self.assertEqual((row['season'],row['kickoff'],row['cutoff']),(g['season'],g['kickoff'],g['cutoff']))
            self.assertEqual(set(row['models']),set(ALIASES.values()))
            for family, targets in row['models'].items():
                self.assertEqual(set(targets),{'winner','margin','total'})
                self.assertTrue(0 <= targets['winner']['prediction'] <= 1)
                self.assertIsNone(targets['margin']['cover_probability'])
                for target in ('margin','total'):
                    if family.endswith('blend'):
                        self.assertNotIn('interval80',targets[target])
                    else:
                        for interval in ('interval80','interval95'):
                            self.assertEqual(len(targets[target][interval]),2)
                            self.assertLessEqual(*targets[target][interval])
                for saved in targets.values():
                    self.assertTrue(D['original_computation_first'] <= saved['computed_at_utc'] <= D['original_computation_last'])

    def test_metrics_retain_target_denominators_and_partial_catboost_mismatch(self):
        for cohort, expected in [('2024',678),('2025',934),('2026',629),('previous_week',56),('current_week',7)]:
            rows = D['metrics'][cohort]
            self.assertEqual(len(rows),35)
            neural = [r for r in rows if r['family'] in ALIASES.values()]
            self.assertEqual(len(neural),9)
            self.assertEqual({r['games'] for r in neural},{expected})
            self.assertEqual(len({r['exact_game_ids_sha256'] for r in neural}),1)
            self.assertTrue(all(r['matches_complete_neural_scored_cohort'] for r in neural))
            mismatches=[r for r in rows if not r['matches_complete_neural_scored_cohort']]
            if cohort=='2026':
                self.assertEqual([(r['family'],r['target'],r['games']) for r in mismatches],[('v040_catboost','winner',626)])
            else:self.assertEqual(mismatches,[])

    def test_missing_fixtures_remain_explicit_and_do_not_become_zero_predictions(self):
        predicted={r['id'] for r in D['rows']}
        missing=[r for r in T['rows'] if r['id'] not in predicted]
        self.assertEqual(len(missing),339)
        self.assertEqual(sum(not r['kickoff_exact'] for r in missing),99)
        self.assertEqual(sum(r['projection_status']=='INSUFFICIENT_PRIOR_OUTCOMES' for r in missing),240)

    def test_public_sources_and_original_negative_findings_are_preserved(self):
        for source in D['sources']:
            self.assertEqual((source['bytes'],source['sha256']),PINS[source['file']])
        text=json.dumps(D)
        for forbidden in ('s3://','fit_identity_sha256','model_state_sha256','feature_names','calibration_game_ids','/workspace/','model_parameters'):
            self.assertNotIn(forbidden,text)
        rows={(r['family'],r['target']):r for r in D['metrics']['2026']}
        baseline=rows[('v038_fixed_equal_blend','winner')]
        self.assertLess(rows[('v041_pytorch','winner')]['log_loss'],baseline['log_loss'])
        for family in ('v041_pytorch','v041_tensorflow','v041_neural_fixed_equal_blend'):
            for target in ('margin','total'):
                self.assertGreater(rows[(family,target)]['mae'],rows[('v038_fixed_equal_blend',target)]['mae'])
        self.assertNotIn('regularization configuration',text)


if __name__=='__main__':unittest.main()
