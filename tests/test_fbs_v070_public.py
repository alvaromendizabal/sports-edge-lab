"""Verify actual failed invocation reporting without rescoring sports outcomes."""
from pathlib import Path
from datetime import datetime
import base64
import gzip
import hashlib
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/fbs'

def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def dt(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def strip_current_section(page):
    page=re.sub(r'<!-- FBS_V070_LATEST_ATTEMPT_START -->[\s\S]*?<!-- FBS_V070_LATEST_ATTEMPT_END -->\n','',page)
    return page.replace('<main>\n\n','<main>\n',1).replace('<a href="#latest-attempt">Latest execution</a>','<a href="#execution">Latest execution</a>')

class ActualV069PublicEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(P/'latest-attempt-v070.json').read_bytes()
        cls.data=json.loads(cls.raw)
        cls.old=json.loads(gzip.decompress((P/'latest-games-v068.json.gz').read_bytes()))
        cls.page=(P/'latest-games-v068.html').read_text()

    def test_actual_failure_precedes_science_without_invented_zero_phase_counts(self):
        a=self.data['actual_owner_attempt']
        self.assertEqual(self.data['latest_actual_owner_release'],'V069')
        self.assertEqual(a['status'],'V069_PARTIAL_DIAGNOSTIC_PRESERVED')
        self.assertEqual((a['worker_exit'],a['supervisor_exit']),(2,2))
        for k in ('reported_new_model_fits','reported_new_genuine_forecasts','reported_new_prediction_outputs'):
            self.assertEqual(a[k],0)
        for k in ('unreached_phase_optimizer_starts','unreached_phase_completed_optimizers','unreached_phase_failed_fit_attempts','measured_parallel_fit_utilization'):
            self.assertIsNone(a[k])
        for k in ('current_source_refresh_reached','frozen_training_reached','champion_stage_reached','successful_archive_delivery_is_scientific_success'):
            self.assertFalse(a[k])
        self.assertEqual(a['return_integrity']['manifest_pins_verified'],73)
        self.assertEqual(a['return_integrity']['zip_members'],74)
        self.assertEqual(a['return_integrity']['sha256'],'7ea5ab2a934d5f58c41b095eab2515f1ee416947e37ac5efed59e517064dd9c0')

    def test_catalog_clock_is_the_actual_fallback_observation(self):
        a=self.data['actual_owner_attempt']
        self.assertEqual(a['fallback_price_observed_at_utc'],'2026-11-10T23:52:44.244368+00:00')
        self.assertEqual(a['maximum_fresh_age_seconds'],86400)
        self.assertAlmostEqual(a['fallback_age_seconds'],151478.247722,places=6)
        self.assertGreater(a['fallback_age_seconds'],a['maximum_fresh_age_seconds'])
        self.assertLess(abs((dt(a['failed_at_utc'])-dt(a['fallback_price_observed_at_utc'])).total_seconds()-a['fallback_age_seconds']),0.01)
        self.assertEqual(a['reason_code'],'V7_PRICE_CATALOG_STALE_OR_FROM_FUTURE')

    def test_saved_forecasts_and_all_annual_metrics_are_unchanged(self):
        self.assertEqual(self.data['annual_descriptive_leaders'],self.old['annual_descriptive_leaders'])
        self.assertEqual(self.data['matched_new_vs_restored'],self.old['new_research'])
        self.assertEqual(self.data['separate_231_draftkings_comparison'],self.old['saved_231_draftkings_comparison'])
        self.assertEqual(len(self.data['annual_descriptive_leaders']),21)
        c=self.data['retained_forecast_evidence']
        self.assertEqual(c['source_owner_release'],'V067')
        self.assertEqual(c['first_selected_issue_at_utc'],'2026-11-11T23:31:03.995204Z')
        self.assertEqual(c['last_selected_issue_at_utc'],'2026-11-11T23:32:11.232957Z')
        self.assertEqual((c['observed_current_season_games'],c['observed_finals'],c['timed_future_contexts_at_original_capture'],c['unresolved_kickoff_games']),(888,688,146,54))
        self.assertFalse(c['all_upcoming_games_refreshed_on_november_12'])
        self.assertFalse(c['all_former_models_refreshed_across_full_current_season'])
        self.assertFalse(c['those_two_classes_may_be_pooled_as_prospective'])
        self.assertEqual(c['reconstructed_former_model_cohort_games']+c['separately_recovered_original_issued_games'],c['distinct_games_across_those_two_evidence_classes'])

    def test_all_named_venues_years_and_targets_have_explicit_denominators(self):
        rows=self.data['qualified_named_provider_cohorts']
        self.assertEqual(len(rows),12)
        self.assertEqual({(r['season'],r['venue']) for r in rows},{(s,p) for s in (2024,2025,2026) for p in ('DraftKings','Kalshi','Polymarket Global','Polymarket US')})
        for r in rows:
            self.assertEqual((r['observed_games'],r['observed_finals']),{2024:(920,919),2025:(934,934),2026:(888,688)}[r['season']])
            self.assertEqual(r['qualified_games_by_target'],dict.fromkeys(('winner','margin','total','cover_probability'),0))
            self.assertTrue(r['missing_report_qualification_is_not_proof_of_no_owned_source_history'])
        c=self.data['champions']
        self.assertEqual(c['last_completed_champion_check'],'V064')
        self.assertEqual(c['last_authorized_rolling_champion_count'],0)
        self.assertFalse(c['latest_v069_champion_check_reached'])
        self.assertFalse(c['automatic_promotion'])
        self.assertFalse(self.data['prepared_successor']['owner_execution_observed'])

    def test_original_page_and_readme_preserved_outside_documented_additions(self):
        self.assertEqual(blob(strip_current_section(self.page).encode()),'814fb0949d0de0d3d8cdb78140cc2422e5a44b02')
        readme=(P/'README.md').read_text()
        old=re.sub(r'<!-- FBS_V070_LATEST_ATTEMPT_START -->[\s\S]*?<!-- FBS_V070_LATEST_ATTEMPT_END -->\n\n','',readme)
        self.assertEqual(blob(old.encode()),'dfc20e0084b77e7a74f91af05c0f4f06c0babfa6')
        self.assertEqual(self.page.count('data-provider-cohort='),12)
        self.assertIn('No November 12 forecast refresh is claimed.',self.page)

    def test_download_and_public_boundary(self):
        a=re.findall(r'<a id="latest-attempt-download" href="data:application/json;charset=utf-8;base64,([A-Za-z0-9+/=]+)" download="latest-attempt-v070.json">',self.page)
        self.assertEqual(len(a),1)
        self.assertEqual(base64.b64decode(a[0],validate=True),self.raw)
        forbidden={'model_id','model_sha256','recipe','recipe_id','feature_names','weights','bucket','s3_key','credentials','api_key','raw_quotes'}
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&forbidden)
                for v in value.values():inspect(v)
            elif isinstance(value,list):
                for v in value:inspect(v)
            elif isinstance(value,str):self.assertNotRegex(value,r's3://|arn:aws:|/home/sagemaker-user|/sports-edge-lab/shared/')
        inspect(self.data)
        p=self.data['public_projection']
        self.assertEqual((p['new_fits'],p['new_inference_rows'],p['new_forecast_issues']),(0,0,0))
        self.assertFalse(p['metric_rescoring'])
        self.assertFalse(p['private_model_recipes_published'])

if __name__=='__main__':unittest.main()
