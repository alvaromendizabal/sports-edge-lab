import json
import unittest
from collections import Counter
from pathlib import Path
from examples.fbs_contracts.build_catboost_review import PINS

ROOT=Path(__file__).resolve().parents[3]
D=json.loads((ROOT/'docs/fbs/catboost-study.json').read_text())
T=json.loads((ROOT/'docs/fbs/three-season.json').read_text())
O=json.loads((ROOT/'docs/fbs/optional-study.json').read_text())


class CatBoostReviewTests(unittest.TestCase):
    def test_new_family_complete_without_refitting_old_families(self):
        self.assertGreater(len(D['rows']),0);self.assertLessEqual(len(D['rows']),2403)
        self.assertEqual(len({r['id'] for r in D['rows']}),len(D['rows']))
        self.assertEqual(set(r['season'] for r in D['rows']),{2024,2025,2026})
        self.assertEqual(D['counts']['new_prediction_outputs'],sum(len(r['models']['v040_catboost']) for r in D['rows']))
        self.assertLessEqual(D['counts']['unique_successful_new_base_fits'],681)
        self.assertLessEqual(D['counts']['successful_new_calibration_fits'],227)
        self.assertEqual(D['default_selection_unchanged'],'V038 fixed_equal_blend')
        for key in ['forecast_issued','historical_availability_proved','promotion_allowed']:
            self.assertFalse(D[key])

    def test_pending_winner_identity_is_not_silently_retried_or_filled(self):
        self.assertFalse(D['registered_workload_complete'])
        self.assertEqual(D['counts']['unique_successful_new_base_fits'],680)
        self.assertEqual(D['counts']['successful_new_calibration_fits'],226)
        self.assertEqual(D['counts']['durable_optimizer_intents'],681)
        self.assertEqual(D['counts']['pending_optimizer_identities'],1)
        self.assertEqual(D['counts']['games_with_all_three_optional_targets'],2400)
        self.assertEqual({r['game_id'] for r in D['pending_output_gaps']},{'401856811','401858225','401858226'})
        self.assertEqual({r['target'] for r in D['pending_output_gaps']},{'winner'})
        self.assertEqual(D['target_coverage']['2026'],{'winner':787,'margin':790,'total':790})

    def test_all_targets_match_fixture_clocks_and_keep_real_intervals(self):
        games={r['id']:r for r in T['rows']}
        self.assertEqual(sum(games[r['id']]['period']=='current' for r in D['rows']),63)
        for row in D['rows']:
            g=games[row['id']]
            self.assertTrue(g['kickoff_exact'])
            self.assertEqual((row['season'],row['kickoff'],row['cutoff']),(g['season'],g['kickoff'],g['cutoff']))
            self.assertEqual(set(row['models']),{'v040_catboost'})
            m=row['models']['v040_catboost']
            self.assertTrue(set(m)<={'winner','margin','total'})
            self.assertEqual(set(row['missing_targets']),{'winner','margin','total'}-set(m))
            if 'winner' in m:self.assertTrue(0<=m['winner']['prediction']<=1)
            for target in ['margin','total']:
                if target not in m:continue
                if target=='margin':self.assertIsNone(m[target]['cover_probability'])
                for field in ['interval80','interval95']:
                    self.assertEqual(len(m[target][field]),2)
                    self.assertLessEqual(m[target][field][0],m[target][field][1])
                self.assertTrue(m[target]['computed_at_utc'])

    def test_full_precision_exact_common_cohorts_and_old_metrics(self):
        for cohort,n in [('2024',678),('2025',934),('2026',629),('previous_week',56),('current_week',7)]:
            metrics=D['metrics'][cohort]
            self.assertEqual(len(metrics),26)
            self.assertTrue(all(0 < m['games'] <= n for m in metrics))
            self.assertEqual(Counter(m['study'] for m in metrics),{'V038':14,'V039':9,'V040':3})
            old={(m['family'],m['target']):m for m in O['metrics'][cohort]}
            for m in metrics:
                if (m['family'],m['target']) not in old:
                    continue
                original=old[(m['family'],m['target'])]
                if (m['games'],m['exact_game_ids_sha256']) != (original['games'],original['exact_game_ids_sha256']):continue
                for key,value in original.items():
                    if key not in ['display_name','study','source_family']:
                        self.assertEqual(m[key],value)

    def test_physical_source_pins_and_public_boundary(self):
        for p in D['sources']:
            self.assertEqual((p['bytes'],p['sha256']),PINS[p['file']])
        text=json.dumps(D)
        for forbidden in ['s3://','api_key','model_state_sha256','fit_identity_sha256','calibration_game_ids','feature_names','source_reference']:
            self.assertNotIn(forbidden,text)
        self.assertEqual(set(D['unexecuted_families']),{'pytorch','tensorflow'})


if __name__=='__main__':
    unittest.main()
