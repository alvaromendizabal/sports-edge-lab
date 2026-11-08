"""Latest observations must not rewrite original fixtures or saved forecasts."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]


class CurrentCaptureReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.latest = json.loads((ROOT/'docs/fbs/current-capture.json').read_text())
        cls.original = json.loads((ROOT/'docs/fbs/three-season.json').read_text())

    def test_complete_inventory_and_new_results_are_separate(self):
        old = {r['id']:r for r in self.original['rows']}
        rows = self.latest['rows']
        self.assertEqual(len(rows),2742)
        self.assertEqual({r['id'] for r in rows},set(old))
        self.assertEqual(len({r['id'] for r in rows}),2742)
        changed = []
        for row in rows:
            prior = old[row['id']]
            self.assertEqual(tuple(row[k] for k in ('season','home_id','away_id','kickoff','kickoff_exact','reported_kickoff')),
                             tuple(prior[k] for k in ('season','home_id','away_id','kickoff','kickoff_exact','reported_kickoff')))
            self.assertNotIn('models',row)
            if (row['completed'],row['home_score'],row['away_score']) != (prior['completed'],prior['home_score'],prior['away_score']):
                changed.append(row)
                self.assertFalse(prior['completed'])
                self.assertTrue(row['completed'])
                self.assertEqual(row['season'],2026)
        self.assertEqual(len(changed),18)
        self.assertEqual(sum(r['season']==2026 and r['completed'] for r in rows),647)
        self.assertEqual(sum(old[r['id']]['period']=='current' and r['season']==2026 and r['completed'] for r in rows),25)

    def test_unresolved_kickoff_and_original_studies_are_preserved(self):
        rows=self.latest['rows']
        self.assertEqual(sum(not r['kickoff_exact'] for r in rows),99)
        self.assertTrue(all(r['kickoff'] is None for r in rows if not r['kickoff_exact']))
        self.assertEqual(sum(r['completed'] for r in rows if not r['kickoff_exact']),1)
        self.assertEqual(self.latest['counts']['new_fixture_ids'],0)
        self.assertEqual(self.latest['counts']['changed_fixture_identities'],0)
        for source in self.latest['original_public_assets']:
            body=(ROOT/source['path']).read_bytes()
            self.assertEqual(len(body),source['bytes'])
            self.assertEqual(hashlib.sha256(body).hexdigest(),source['sha256'])

    def test_latest_metrics_use_target_specific_full_precision_cohorts(self):
        for cohort,n in [('2026',647),('current_week',25),('previous_week',56),('newly_observed',18)]:
            rows=self.latest['metrics'][cohort]
            self.assertEqual(len(rows),35)
            self.assertEqual(len({(r['family'],r['target']) for r in rows}),35)
            for row in rows:
                expected=644 if cohort=='2026' and row['family']=='v040_catboost' and row['target']=='winner' else n
                self.assertEqual(row['games'],expected)
                self.assertEqual(len(row['exact_game_ids_sha256']),64)
                self.assertIs(row['promotion_allowed'],False)
            baseline=next(r for r in rows if r['family']=='v038_fixed_equal_blend' and r['target']=='winner')
            cat=next(r for r in rows if r['family']=='v040_catboost' and r['target']=='winner')
            self.assertEqual(cat['exact_game_ids_sha256']==baseline['exact_game_ids_sha256'],cohort!='2026')

    def test_source_rows_keep_distinct_identity_and_clock_qualifications(self):
        d=self.latest['draftkings']
        self.assertEqual(d['event_count'],39)
        self.assertEqual(d['target_rows'],113)
        self.assertEqual(d['source_clock_qualified_rows'],54)
        self.assertEqual(d['post_kickoff_rows'],59)
        self.assertEqual(len(d['events']),39)
        for event in d['events']:
            self.assertTrue(event['status_text'])
            self.assertTrue(event['model_cutoff_status'])
            for target in event['targets'].values():
                self.assertNotIn('outcomes',target)
                self.assertNotIn('odds',target)
        self.assertEqual(self.latest['qualified_cover_outputs'],0)

    def test_publication_is_not_new_execution_or_issuance(self):
        for key in ('new_fits','new_predictions','new_provider_requests'):
            self.assertEqual(self.latest[key],0)
        self.assertIs(self.latest['forecast_issued'],False)
        self.assertIs(self.latest['promotion_allowed'],False)
        self.assertEqual(self.latest['default_selection_unchanged'],'V038 fixed_equal_blend')
        body=json.dumps(self.latest)
        for forbidden in ('s3://','api_key','event_id','fit_identity_sha256','feature_names','model_parameters','raw_body','/workspace/'):
            self.assertNotIn(forbidden,body)
        js=(ROOT/'docs/fbs/current-capture-data.js').read_text()
        self.assertEqual(json.loads(js.split('=',1)[1].removesuffix(';\n')),self.latest)

    @unittest.skipUnless(shutil.which('node'),'Node is required for result-view guards')
    def test_result_snapshot_identity_guards(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('test_current_capture_logic.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
