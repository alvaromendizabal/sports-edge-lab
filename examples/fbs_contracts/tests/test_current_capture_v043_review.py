"""The additive V043 capture preserves fixtures, forecasts and two earlier views."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT=Path(__file__).resolve().parents[3]


class CurrentCaptureV043Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.latest=json.loads((ROOT/'docs/fbs/current-capture-v043.json').read_text())
        cls.prior=json.loads((ROOT/'docs/fbs/current-capture.json').read_text())
        cls.original=json.loads((ROOT/'docs/fbs/three-season.json').read_text())

    def test_twenty_new_results_keep_all_original_identities_and_forecasts(self):
        original={r['id']:r for r in self.original['rows']}
        prior={r['id']:r for r in self.prior['rows']}
        rows=self.latest['rows']
        self.assertEqual(len(rows),2742)
        self.assertEqual(len({r['id'] for r in rows}),2742)
        self.assertEqual({r['id'] for r in rows},set(original))
        changed=[]
        for row in rows:
            old=original[row['id']];previous=prior[row['id']]
            identity=('season','home_id','away_id','kickoff','kickoff_exact','reported_kickoff')
            self.assertEqual(tuple(row[k] for k in identity),tuple(old[k] for k in identity))
            self.assertNotIn('models',row)
            changed_result=(row['completed'],row['home_score'],row['away_score'])!=(previous['completed'],previous['home_score'],previous['away_score'])
            self.assertEqual(row['newly_observed'],changed_result)
            if changed_result:
                changed.append(row['id']);self.assertFalse(previous['completed']);self.assertTrue(row['completed'])
        self.assertEqual(len(changed),20)
        self.assertEqual(sum(r['season']==2026 and r['completed'] for r in rows),667)
        self.assertEqual(sum(original[r['id']]['period']=='current' and r['season']==2026 and r['completed'] for r in rows),45)
        self.assertEqual(sum(r['completed'] and not original[r['id']]['completed'] for r in rows),38)
        self.assertEqual(self.latest['counts']['newly_observed'],20)
        self.assertEqual(self.latest['counts']['newly_observed_since_original_snapshot'],38)
        self.assertTrue(self.latest['delta_basis'])

    def test_tbd_and_all_sixteen_prior_numeric_assets_remain_exact(self):
        self.assertEqual(sum(not r['kickoff_exact'] for r in self.latest['rows']),99)
        self.assertTrue(all(r['kickoff'] is None for r in self.latest['rows'] if not r['kickoff_exact']))
        self.assertEqual(len(self.latest['original_public_assets']),16)
        for pin in self.latest['original_public_assets']:
            raw=(ROOT/pin['path']).read_bytes()
            self.assertEqual(len(raw),pin['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])

    def test_target_specific_cohorts_and_original_default_stay_separate(self):
        for period,n in [('2026',667),('current_week',45),('previous_week',56),('newly_observed',20),('cumulative',2279)]:
            rows=self.latest['metrics'][period]
            self.assertEqual(len(rows),35)
            self.assertEqual(len({(r['family'],r['target']) for r in rows}),35)
            for row in rows:
                gap=3 if period in ('2026','cumulative') and row['family']=='v040_catboost' and row['target']=='winner' else 0
                self.assertEqual(row['games'],n-gap)
                self.assertIs(row['promotion_allowed'],False)
                self.assertEqual(len(row['exact_game_ids_sha256']),64)
        self.assertEqual(self.latest['new_outcome_evaluation_records'],700)
        self.assertEqual(self.latest['original_prediction_records'],84102)
        for key in ('new_fits','new_predictions','new_provider_requests','qualified_cover_outputs'):
            self.assertEqual(self.latest[key],0)
        self.assertIs(self.latest['forecast_issued'],False)
        self.assertIs(self.latest['promotion_allowed'],False)
        self.assertEqual(self.latest['default_selection_unchanged'],'V038 fixed_equal_blend')

    def test_latest_provider_rows_keep_identity_and_cutoff_distinct(self):
        d=self.latest['draftkings']
        self.assertEqual(d['event_count'],26);self.assertEqual(d['target_rows'],77)
        self.assertEqual(d['exact_game_events'],8);self.assertEqual(d['exact_game_target_rows'],24)
        self.assertEqual(d['source_clock_qualified_rows'],39);self.assertEqual(d['post_kickoff_rows'],38)
        self.assertEqual(d['source_available_t120_exact_identity_rows'],18)
        self.assertEqual(d['source_available_t60_exact_identity_rows'],24)
        self.assertEqual(len(d['events']),26)
        self.assertEqual(d['source_clock_qualified_rows']+d['post_kickoff_rows'],77)
        for event in d['events']:
            self.assertTrue(event['status_text']);self.assertTrue(event['model_cutoff_status'])
            self.assertIs(event['historical_possession_proved'],False)
            self.assertIsNone(event['qualified_cover_probability'])
            for target in event['targets'].values():
                if event['id'] is None:self.assertIsNone(target['value'])
                self.assertNotIn('outcomes',target);self.assertNotIn('odds',target)
                if 'strict_model_input_eligible' in target:self.assertIs(target['strict_model_input_eligible'],False)

    def test_public_safe_projection_matches_companion_script(self):
        text=json.dumps(self.latest)
        for forbidden in ('s3://','api_key','event_id','fit_identity_sha256','feature_names','model_parameters','raw_body','/workspace/','decimal_price','actual_game_ids'):
            self.assertNotIn(forbidden,text)
        js=(ROOT/'docs/fbs/current-capture-v043-data.js').read_text()
        self.assertEqual(json.loads(js.split('=',1)[1].removesuffix(';\n')),self.latest)
        html=(ROOT/'docs/fbs/complete.html').read_text()
        for value in ('latest','prior','original','v043','v042'):
            self.assertIn('value="'+value+'"',html)


if __name__=='__main__':unittest.main()
