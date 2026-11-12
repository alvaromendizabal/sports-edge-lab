"""Resource-deferred output cannot invent telemetry, issues or market scores."""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from selected_review_n076 import HEALTH,render

HERE=Path(__file__).resolve().parent


class N075ResourceDeferralContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(HERE/'selected_forecasts_n073.json').read_bytes()
        cls.data=json.loads(cls.original)
        cls.health=json.loads((HERE/HEALTH).read_bytes())
        cls.page=(HERE/'season_review_n076.html').read_text()

    def test_saved_page_exactly_reopens(self):
        self.assertEqual(self.page,render(self.original,self.health))

    def test_original_payload_is_unchanged(self):
        marker='<script id="selected-data" type="application/json">'
        start=self.page.index(marker)+len(marker)
        self.assertEqual(json.loads(self.page[start:self.page.index('</script>',start)]),self.data)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(),self.health['retained_forecasts']['sha256'])

    def test_all_games_roles_and_outputs_retained(self):
        self.assertEqual(len(self.data['games']),272)
        self.assertEqual(len(self.data['selected_historical_roles']),27)
        self.assertEqual(sum(len(t['current_forecasts']) for g in self.data['games'] for t in g['targets'].values()),772)
        self.assertEqual(self.health['retained_forecasts']['future_games'],112)

    def test_known_zeros_are_not_missing_totals(self):
        for key in ('new_fits','new_native_fits','new_meta_fits','new_forecasts'):
            self.assertIs(type(self.health[key]),int)
            self.assertEqual(self.health[key],0)
        self.assertEqual(self.health['source_activity']['new_paid_calls'],0)
        self.assertIn('N075 resource-deferred',self.page)
        self.assertIn('36.301 seconds',self.page)

    def test_missing_fabricated_and_boolean_counts_rejected(self):
        for value in (None,1,False):
            h=copy.deepcopy(self.health);h['new_fits']=value
            with self.assertRaisesRegex(ValueError,'KNOWN_ZERO_DEFERRAL'):
                render(self.original,h)

    def test_absent_current_capacity_remains_absent(self):
        for key,value in [('current_effective_vcpus',48),('current_per_project_ceiling',12),('measured_pressure',0),('requested_or_granted_threads',1)]:
            h=copy.deepcopy(self.health);h['resource_admission'][key]=value
            with self.assertRaisesRegex(ValueError,'UNOBSERVED_RESOURCE_TELEMETRY'):
                render(self.original,h)

    def test_unproven_causes_rejected(self):
        for key in ('other_owner_cause_proven','pressure_was_stale_proven'):
            h=copy.deepcopy(self.health);h['resource_admission'][key]=True
            with self.assertRaisesRegex(ValueError,'UNPROVEN_RESOURCE_CAUSE'):
                render(self.original,h)

    def test_no_false_source_or_schedule_refresh(self):
        for section,key in [('source_activity','source_refresh_invoked'),('current_census','refreshed_by_latest_execution')]:
            h=copy.deepcopy(self.health);h[section][key]=True
            with self.assertRaisesRegex(ValueError,'NO_SOURCE_OR_CENSUS_REFRESH'):
                render(self.original,h)

    def test_actual_deferral_reason_bound(self):
        h=copy.deepcopy(self.health);h['resource_admission']['observed_reason']='MEMORY_PRESSURE'
        with self.assertRaisesRegex(ValueError,'ACTUAL_DEFERRAL_REASON'):
            render(self.original,h)

    def test_no_reissue_or_promotion(self):
        self.assertFalse(self.health['owner_research_acceptance'])
        self.assertFalse(self.health['new_release']['owner_executed'])
        for key in ('new_fit_credit','new_inference_credit','new_issue_credit'):
            self.assertEqual(self.health['retained_forecasts'][key],0)
        for key in ('automatic_promotion','original_predictions_changed'):
            h=copy.deepcopy(self.health);h[key]=True
            with self.assertRaisesRegex(ValueError,'CANNOT_PROMOTE_OR_REISSUE'):
                render(self.original,h)

    def test_mutated_forecasts_rejected(self):
        with self.assertRaisesRegex(ValueError,'RETAINED_FORECAST_BYTES_CHANGED'):
            render(self.original+b' ',self.health)

    def test_failure_text_is_escaped(self):
        h=copy.deepcopy(self.health);h['failures'][0]['effect']='</section><script>unsafe()</script>'
        self.assertNotIn('</section><script>unsafe()</script>',render(self.original,h))

    def test_health_has_no_private_payload(self):
        s=json.dumps(self.health)
        for token in ('recipe_id','s3://','api_key','/home/sagemaker-user','sagemaker-sports-edge-lab'):
            self.assertNotIn(token,s)
        self.assertIsNone(re.search(r'(?<![A-Za-z0-9])[0-9]{12}(?![A-Za-z0-9])',s))
        self.assertFalse(self.health['publication']['raw_provider_values_included'])
        self.assertFalse(self.health['publication']['website_deployed'])


if __name__=='__main__':unittest.main()
