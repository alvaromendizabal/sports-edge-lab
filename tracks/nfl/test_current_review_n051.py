import copy,json,pathlib,re,unittest
from build_review_n051 import build,validate,retained
from export_site_n051 import projection
ROOT=pathlib.Path(__file__).resolve().parent


class CurrentReviewN051Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.review=json.loads((ROOT/'current_review_n051.json').read_text())

    def test_deterministic_current_review(self):
        self.assertEqual((ROOT/'review_n051.html').read_text(),build(self.review))

    def test_retained_scientific_object_is_unchanged(self):
        page=build(self.review)
        payload=re.search(r'<script id="nfl-current-review-data" type="application/json">(.*?)</script>',page,re.S).group(1)
        envelope=json.loads(payload)
        self.assertEqual(envelope['retained_snapshot'],json.loads((ROOT/'current_review_n050.json').read_text()))
        self.assertEqual(len(envelope['retained_snapshot']['cards']),56)
        self.assertEqual(envelope['retained_snapshot']['as_of'],'2026-11-06T06:17:17.122290+00:00')

    def test_new_attempt_cannot_recredit_retained_science(self):
        for field in ['new_native_fits','new_target_forecasts','new_source_acquisitions','completed_scientific_stages','paid_provider_calls','protected_original_refits','actual_orders']:
            data=copy.deepcopy(self.review);data['latest_owner_attempt'][field]=1
            with self.subTest(field=field),self.assertRaises(ValueError):validate(data)

    def test_failed_attempt_cannot_be_promoted(self):
        for change in ({'owner_research_accepted':True},{'status':'COMPLETED'}):
            data=copy.deepcopy(self.review);data['latest_owner_attempt'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):validate(data)

    def test_future_preparation_cannot_award_execution(self):
        for field in ['owner_native_fits','owner_forecasts']:
            data=copy.deepcopy(self.review);data['next'][field]=1
            with self.subTest(field=field),self.assertRaises(ValueError):validate(data)

    def test_retained_snapshot_cannot_be_redated(self):
        data=copy.deepcopy(self.review);data['retained_snapshot']['evidence_as_of']='2026-11-06T08:23:03.315123+00:00'
        with self.assertRaises(ValueError):validate(data)

    def test_completion_clock_must_follow_summary(self):
        data=copy.deepcopy(self.review);data['latest_owner_attempt']['later_external_completion']['final_return_readback_at']=data['latest_owner_attempt']['finished_at']
        with self.assertRaises(ValueError):validate(data)

    def test_no_automatic_promotion_or_repeat_fit(self):
        for field in ['automatic_promotion','repeated_completed_injury_study','unrestricted_history_acquisition']:
            data=copy.deepcopy(self.review);data['next'][field]=True
            with self.subTest(field=field),self.assertRaises(ValueError):validate(data)

    def test_hosted_projection_preserves_all_embedded_objects(self):
        original=(ROOT/'review.html').read_text();current=build(self.review)
        published,history=projection(current,original,json.loads((ROOT/'readiness_n049.json').read_text()),'a'*40)
        pattern=r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
        self.assertEqual(re.findall(pattern,original,re.S),re.findall(pattern,history,re.S))
        self.assertEqual(re.findall(pattern,current,re.S),re.findall(pattern,published,re.S))
        self.assertIn('N050 actual / N051 prepared',history)
        self.assertIn('Canonical commit:',published)

    def test_no_private_paths_or_active_model_recipe(self):
        self.assertIsNone(re.search(r's3://|arn:aws:|/workspace/|/home/|X-Amz-|AKIA[A-Z0-9]{16}|component_bindings|model_sha256',json.dumps(self.review)))


if __name__=='__main__':unittest.main()
