import json
import unittest
from collections import Counter
from pathlib import Path
from examples.fbs_contracts.build_optional_review import PINS, ALIASES

ROOT=Path(__file__).resolve().parents[3]
D=json.loads((ROOT/'docs/fbs/optional-study.json').read_text())
T=json.loads((ROOT/'docs/fbs/three-season.json').read_text())
R=json.loads((ROOT/'docs/fbs/development-2026.json').read_text())

class OptionalStudyReviewTests(unittest.TestCase):
    def test_new_completed_work_is_separate_from_reused_originals(self):
        c=D['counts'];self.assertEqual(c['unique_successful_new_base_fits'],1362)
        self.assertEqual(c['successful_new_calibration_fits'],454)
        self.assertEqual(c['new_prediction_outputs'],21627)
        self.assertEqual(c['successful_base_plus_calibration_fits'],1816)
        self.assertEqual(c['states_reused_by_full_cohort'],24)
        self.assertEqual(c['old_sklearn_fits_repeated'],0)
        self.assertEqual(c['new_genuine_forecast_issues'],0)
        self.assertEqual(c['new_strict_qualified_scientific_fits'],0)
        self.assertEqual(R['cumulative_work']['total_successful_base_plus_calibration_fits'],3178)
        self.assertEqual(D['default_selection_unchanged'],'V038 fixed_equal_blend')
    def test_all_new_families_cover_the_same_admitted_games(self):
        byid={r['id']:r for r in T['rows']};ids=[r['id'] for r in D['rows']]
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),2403)
        self.assertEqual(Counter(r['season'] for r in D['rows']),{2024:679,2025:934,2026:790})
        self.assertEqual(sum(byid[i]['period']=='current' for i in ids),63)
        self.assertEqual(sum(byid[i]['period']=='previous' for i in ids),56)
        for row in D['rows']:
            self.assertEqual(row['kickoff'],byid[row['id']]['kickoff'])
            self.assertEqual(row['cutoff'],byid[row['id']]['cutoff'])
            self.assertEqual(set(row['models']),set(ALIASES.values()))
            for family,values in row['models'].items():
                self.assertEqual(set(values),{'winner','margin','total'})
                self.assertTrue(0<=values['winner']['prediction']<=1)
                self.assertIsNone(values['margin']['cover_probability'])
                self.assertTrue(all(v['computed_at_utc'] for v in values.values()))
                if family=='v039_fixed_equal_optional_blend':self.assertNotIn('interval80',values['margin'])
                else:self.assertIn('interval80',values['margin']);self.assertIn('interval95',values['total'])
    def test_exact_common_metric_denominators_and_original_values(self):
        for cohort,n in [('2024',678),('2025',934),('2026',629),('current_week',7)]:
            metrics=D['metrics'][cohort]
            self.assertEqual({m['games'] for m in metrics},{n})
            self.assertEqual(len({m['exact_game_ids_sha256'] for m in metrics}),1)
            self.assertEqual(len(metrics),23)
            original={(m['family'],m['target']):m for m in R['metrics'][cohort]}
            for m in metrics:
                if m['study']=='V038':
                    for key,value in original[(m['source_family'],m['target'])].items():
                        if key=='family':continue
                        self.assertEqual(m[key],value)
        self.assertEqual({m['games'] for m in D['metrics']['previous_week']},{56})
    def test_public_private_boundary_and_no_promotion(self):
        for p in D['sources']:self.assertEqual((p['bytes'],p['sha256']),PINS[p['file']])
        text=json.dumps(D)
        for forbidden in ['s3://','api_key','model_state_sha256','fit_identity_sha256','calibration_game_ids','feature_names','source_reference']:
            self.assertNotIn(forbidden,text)
        for k in ['promotion_allowed','historical_availability_proved','forecast_issued']:self.assertFalse(D[k])
        self.assertEqual(set(D['unexecuted_families']),{'catboost','pytorch','tensorflow'})
        self.assertEqual(D['resources']['new_sports_provider_requests'],0)
        self.assertIsNone(D['resources']['dollar_cost'])

if __name__=='__main__':unittest.main()
