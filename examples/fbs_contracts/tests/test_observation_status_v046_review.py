"""V4 publishes verified observations and status, not a new unissued value grid."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT=Path(__file__).resolve().parents[3]


class ObservationStatusV046Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body=(ROOT/'docs/fbs/observation-status-v046.json').read_bytes()
        cls.data=json.loads(cls.body)
        cls.original=json.loads((ROOT/'docs/fbs/three-season.json').read_text())
        cls.prior=json.loads((ROOT/'docs/fbs/current-capture-v045.json').read_text())

    def test_exact_authenticated_metadata_pin_and_script(self):
        self.assertEqual(len(self.body),4265556)
        self.assertEqual(hashlib.sha256(self.body).hexdigest(),'4a1db5f4243993789fbeee7e71791702e0cfc9c49c0eadc514ac51dd6f3d00b0')
        text=(ROOT/'docs/fbs/observation-status-v046-data.js').read_text()
        self.assertEqual(json.loads(text.split('=',1)[1].removesuffix(';\n')),self.data)

    def test_two_new_scores_and_three_new_fixture_epochs_remain_distinct(self):
        original={row['id']:row for row in self.original['rows']}
        prior={row['id']:row for row in self.prior['rows']}
        rows=self.data['rows'];self.assertEqual(len(rows),2742)
        self.assertEqual({row['id'] for row in rows},set(original))
        resolved=[];new=[]
        for row in rows:
            old=original[row['id']]
            for key in ('season','home_id','away_id'):self.assertEqual(str(row[key]),str(old[key]))
            if row['kickoff']!=old['kickoff']:
                resolved.append(row['id']);self.assertFalse(old['kickoff_exact']);self.assertIsNone(old['kickoff'])
                self.assertTrue(row['kickoff_exact']);self.assertEqual(row['binding_status'],'TBD_RESOLUTION_NEW_FIXTURE_EPOCH')
                self.assertFalse(row['old_prediction_rebound']);self.assertEqual(row['four_epoch_models'],{})
            if row['newly_observed_since_prior_capture']:
                new.append(row['id']);self.assertTrue(row['completed']);self.assertFalse(prior[row['id']]['completed'])
        self.assertEqual(set(resolved),{'401858519','401866463','401866469'})
        self.assertEqual(set(new),{'401860912','401864535'})
        self.assertEqual(sum(not row['kickoff_exact'] for row in rows),96)
        self.assertEqual(sum(row['season']==2026 and row['completed'] for row in rows),685)

    def test_periods_are_disjoint_and_upcoming_includes_two_pending_epochs(self):
        p=self.data['periods'];expected={'previous_week':(56,56),'current_week':(63,63),'upcoming_week':(53,0)}
        seen=set();lookup={r['id']:r for r in self.data['rows']}
        for key,(count,finals) in expected.items():
            ids=set(p[key]['game_ids']);self.assertEqual(len(ids),count);self.assertFalse(seen&ids);seen|=ids
            self.assertEqual(sum(lookup[i]['completed'] for i in ids),finals)
        upcoming=set(p['upcoming_week']['game_ids'])
        self.assertEqual(upcoming&set(self.data['resolved_tbd_game_ids']),{'401858519','401866463'})
        self.assertEqual(sum(bool(lookup[i]['four_epoch_models']) for i in upcoming),51)

    def test_status_metadata_has_no_new_forecast_values_recipes_or_issues(self):
        targets=[]
        for row in self.data['rows']:
            for model in row['four_epoch_models'].values():targets.extend(model.values())
        self.assertEqual(len(targets),3360)
        for target in targets:
            self.assertIs(target['available'],True);self.assertIs(target['forecast_issued'],False)
            self.assertIs(target['new_numerical_value_public'],False)
            self.assertTrue(target['computed_at_utc']);self.assertTrue(target['registered_cutoff_utc'])
            for key in ('prediction','raw_probability','model_state_sha256','fit_identity_sha256','feature_names','model_parameters','interval80','interval95'):self.assertNotIn(key,target)
        for token in ('s3://','/workspace/','api_key','access_token'):self.assertNotIn(token,self.body.decode())
        self.assertEqual(self.data['actual_new_fits_in_this_export'],0)
        self.assertEqual(self.data['scientific_metrics']['new_local_evaluations'],0)
        self.assertTrue(self.data['scientific_metrics']['older683_game_metrics_remain_dated'])

    def test_prior_numeric_report_and_its_pins_remain_exact(self):
        for pin in self.prior['original_public_assets']:
            raw=(ROOT/pin['path']).read_bytes()
            self.assertEqual(len(raw),pin['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
        self.assertEqual(self.prior['counts']['seasons']['2026']['completed'],683)
        self.assertEqual(self.data['counts']['all_saved_output_records'],91270)

    def test_latest_market_metadata_keeps_exact_association_separate_from_model_qualification(self):
        raw=(ROOT/'docs/fbs/market-status-v046.json').read_bytes()
        self.assertEqual(len(raw),101437)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'b4911cba6409e5719cf109d7421cf9602d0d06d1cab3295fa8c956082ef1c732')
        data=json.loads(raw)
        self.assertEqual((data['event_count'],data['target_rows']),(67,201))
        self.assertEqual((data['exact_display_bound_events'],data['exact_display_bound_target_rows']),(33,99))
        self.assertEqual(data['source_available_t120_exact_identity_rows'],99)
        self.assertEqual(data['source_available_t60_exact_identity_rows'],99)
        self.assertEqual(data['qualified_model_cover_rows'],0)
        self.assertEqual(data['new_scientific_evaluations'],0)
        for event in data['events']:
            self.assertFalse(event['strict_model_input_eligible'])
            for key in ('source_event_id','outcomes','odds','prices','prediction'):self.assertNotIn(key,event)
        js=(ROOT/'docs/fbs/market-status-v046-data.js').read_text()
        self.assertEqual(json.loads(js.split('=',1)[1].removesuffix(';\n')),data)


if __name__=='__main__':unittest.main()
