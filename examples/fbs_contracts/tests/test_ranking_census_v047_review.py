"""Authenticated source census: exact copy, run-specific gaps and no new outcomes."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'docs/fbs'

class RankingCensusV047Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (DOCS / 'ranking-research-v047.json').read_bytes()
        cls.data = json.loads(cls.raw)

    def test_census_is_the_exact_authenticated_safe_export(self):
        self.assertEqual(len(self.raw), 13646)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), 'fee6a8726277cf31d4ff33c7c4fe5ac719b79ecf2a3f2a99517dce6f49275441')
        script = (DOCS / 'ranking-research-v047-data.js').read_text()
        self.assertEqual(json.loads(script.removeprefix('window.FBS_RANKING_RESEARCH_V047=').removesuffix(';\n')), self.data)
        self.assertFalse(self.data['raw_rows_public'])
        self.assertEqual(len(self.data['rows']), 19)
        self.assertEqual(self.data['ranking_request_count'], 9)

    def test_new_source_clock_does_not_rewrite_unchanged_results_or_metrics(self):
        data=self.data
        self.assertEqual(data['capture']['observed_at'], '2026-11-08T22:12:26Z')
        self.assertTrue(data['capture']['canonical_original_verified'])
        self.assertTrue(data['capture']['original_bodies_and_receipts_verified'])
        self.assertEqual(data['counts']['new_or_changed_fixture_result_coordinates'], 0)
        self.assertEqual(data['counts']['fixtures'], 2742)
        self.assertEqual(data['counts']['current_season_completed'], 685)
        self.assertEqual(data['counts']['exact_kickoffs'], 2646)
        self.assertEqual(data['counts']['unresolved_kickoffs'], 96)
        self.assertTrue(data['fixture_result_equivalence']['new_result_clock_not_assigned_to_unchanged_results'])
        self.assertEqual(data['new_fit_count'], 0)
        self.assertEqual(data['new_prediction_count'], 0)
        self.assertTrue(data['no_new_metrics_computed'])
        prior=json.loads((DOCS/'current-capture-v045.json').read_text())
        self.assertEqual(prior['counts']['seasons']['2026']['completed'], 683)

    def test_polls_ratings_and_unproved_publication_remain_separate(self):
        rows=self.data['rows']
        self.assertEqual({r['season'] for r in rows if r['source_kind']=='ORGANIZATION_POLL'}, {2022,2023,2024,2025,2026})
        self.assertEqual({r['season'] for r in rows if r['source_kind']=='COMPUTER_RATING'}, {2026})
        self.assertEqual({r['source_key'] for r in rows}, {'AP','COACHES','CFP','ELO','SRS','SP','FPI'})
        self.assertTrue(all(r['publication_timestamps_present']==0 for r in rows))
        self.assertTrue(all(r['admitted_feature_values']==r['evaluated_feature_values']==r['materialized_feature_values']==0 for r in rows))
        self.assertEqual(sum(self.data['excluded_non_fbs_poll_rows'].values()), 4757)
        by_key={(r['season'],r['source_key']):r for r in rows}
        self.assertEqual(by_key[2026,'CFP']['editions'], 1)
        self.assertEqual(by_key[2024,'AP']['records'], 426)
        self.assertEqual(by_key[2026,'SRS']['records'], 268)
        self.assertEqual(by_key[2026,'SRS']['teams'], 266)

    def test_public_export_has_no_raw_values_recipes_or_forecast_grid(self):
        forbidden={'prediction','probability','rank','points','firstPlaceVotes','state_key','recipe','params','hyperparameters','s3_uri','bucket','key','prediction_identity_sha256'}
        def check(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values():check(child)
            elif isinstance(value,list):
                for child in value:check(child)
        check(self.data)
        self.assertNotRegex(self.raw.decode(),r's3://|arn:aws:|X-Amz-Signature')

    def test_latest_market_associations_are_separate_from_raw_clock_counts(self):
        raw=(DOCS/'market-status-v047.json').read_bytes()
        self.assertEqual(len(raw),101849)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'1b1ce96abeb3d1d559ac76508afc7a330f2d30f872837d313758e0d13ad57d21')
        data=json.loads(raw)
        script=(DOCS/'market-status-v047-data.js').read_text()
        self.assertEqual(json.loads(script.removeprefix('window.FBS_MARKET_STATUS_V047=').removesuffix(';\n')),data)
        self.assertEqual(data['source_observed_at'],'2026-11-08T22:12:25Z')
        self.assertEqual((data['target_rows'],data['event_count']),(201,67))
        self.assertEqual((data['exact_display_bound_events'],data['exact_display_bound_target_rows']),(33,99))
        self.assertEqual(data['source_available_t120_exact_identity_rows'],99)
        self.assertEqual(data['source_available_t60_exact_identity_rows'],99)
        self.assertEqual(data['raw_source_available_t120_rows'],201)
        self.assertEqual(data['raw_source_available_t60_rows'],201)
        self.assertEqual(data['qualified_model_cover_rows'],0)
        self.assertEqual(data['new_scientific_evaluations'],0)
        self.assertEqual(sum(len(e['targets']) for e in data['events'] if e['id'] is not None),99)
        self.assertTrue(all(not e['qualified_exact_line_cover'] and not e['strict_model_input_eligible'] for e in data['events']))
        forbidden={'price','odds','probability','prediction','point','outcomes','source_event_id','provider_event_id','source_reference','s3_uri','bucket','key'}
        def check(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values():check(child)
            elif isinstance(value,list):
                for child in value:check(child)
        check(data)
        self.assertNotRegex(raw.decode(),r's3://|arn:aws:|X-Amz-Signature|SPORTSBOOK')

if __name__=='__main__': unittest.main()
