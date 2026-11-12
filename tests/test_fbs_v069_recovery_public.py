"""Publication checks for separately recovered, already issued FBS forecasts."""
from pathlib import Path
from datetime import datetime
import base64
import hashlib
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/fbs'

def clock(s): return datetime.fromisoformat(s.replace('Z','+00:00'))

class RecoveredOriginalPublic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((P/'recovered-original-v069.json').read_text())
        cls.rows=cls.data['games']
        cls.page=(P/'latest-games-v068.html').read_text()

    def test_distinct_coverage_does_not_reclassify_replay(self):
        self.assertEqual(len(self.rows),55)
        self.assertEqual(len({r['game_id'] for r in self.rows}),55)
        c=self.data['coverage']
        self.assertEqual(c['preserved_reconstructed_bank_games'],301)
        self.assertEqual(c['overlapping_games'],0)
        self.assertEqual(c['distinct_games_across_evidence_classes'],356)
        self.assertEqual(c['completed_games_outside_both_evidence_classes'],332)
        self.assertEqual(c['distinct_games_across_evidence_classes']+c['completed_games_outside_both_evidence_classes'],688)
        self.assertFalse(self.data['metric_pooling_with_reconstructed_bank_allowed'])

    def test_original_clock_chain_precedes_kickoff(self):
        model=self.data['model']
        self.assertEqual(model['frozen_training_through_season'],2025)
        self.assertLessEqual(clock(model['training_max_label_available_at']),clock(model['model_fit_cutoff_at']))
        for row in self.rows:
            self.assertEqual(row['season'],2026)
            self.assertEqual(row['target'],'home_win_given_non_tie')
            self.assertEqual(row['evidence_class'],'RECOVERED_ORIGINAL_PREGAME_ISSUE')
            self.assertTrue(row['exact_current_identity_join'])
            self.assertTrue(row['completed_in_current_inventory'])
            self.assertNotEqual(row['home_id'],row['away_id'])
            self.assertLessEqual(clock(model['model_fit_cutoff_at']),clock(row['original_input_cutoff_at_utc']))
            self.assertLessEqual(clock(row['original_input_cutoff_at_utc']),clock(row['original_issue_at_utc']))
            self.assertLessEqual(clock(row['original_issue_at_utc']),clock(row['provenance']['original_record_persisted_at_utc']))
            self.assertLess(clock(row['provenance']['original_record_persisted_at_utc']),clock(row['kickoff_utc']))

    def test_recovery_is_not_new_science_or_training_authorization(self):
        for field in ('new_model_fits','new_genuine_forecast_issues','new_inference_rows'):
            self.assertEqual(self.data[field],0)
        for field in ('metrics_recomputed','promotion_authorized','current_season_selection_allowed','historical_training_publication_independently_verified'):
            self.assertFalse(self.data[field])
        self.assertTrue(self.data['rounded_display_values_must_not_be_rescored'])
        for row in self.rows: self.assertFalse(row['newly_issued'])

    def test_public_boundary_and_probability_precision(self):
        forbidden={'model_id','model_sha256','recipe','recipe_id','feature_names','weights','bucket','s3_key','credentials','api_key','raw_quotes'}
        def inspect(obj):
            if isinstance(obj,dict):
                self.assertFalse(set(obj)&forbidden)
                for val in obj.values(): inspect(val)
            elif isinstance(obj,list):
                for val in obj: inspect(val)
            elif isinstance(obj,str):
                self.assertNotRegex(obj,r's3://|arn:aws:|/home/sagemaker-user|/sports-edge-lab/shared/')
        inspect(self.data)
        for row in self.rows:
            self.assertGreater(row['home_probability'],0)
            self.assertLess(row['home_probability'],1)
            self.assertAlmostEqual(row['home_probability'],round(row['home_probability'],6),places=12)

    def test_existing_html_is_byte_preserved_outside_new_section(self):
        marker=r'<!-- FBS_V069_RECOVERED_ORIGINAL_START -->[\s\S]*?<!-- FBS_V069_RECOVERED_ORIGINAL_END -->\n'
        self.assertEqual(len(re.findall(marker,self.page)),1)
        prior=re.sub(r'<!-- FBS_V070_LATEST_ATTEMPT_START -->[\s\S]*?<!-- FBS_V070_LATEST_ATTEMPT_END -->\n','',self.page)
        prior=prior.replace('<main>\n\n','<main>\n',1).replace('<a href="#latest-attempt">Latest execution</a>','<a href="#execution">Latest execution</a>')
        old=re.sub(marker,'',prior).encode()
        blob=hashlib.sha1(b'blob '+str(len(old)).encode()+b'\x00'+old).hexdigest()
        self.assertEqual(blob,'61b315ad682117f1e3d4f4f205bce1c5c458c69d')
        self.assertEqual(self.page.count('data-recovered-game='),55)
        self.assertIn('no combined prospective score',self.page)
        self.assertIn('recovered-original-v069.json',self.page)

    def test_offline_download_contains_exact_public_json(self):
        anchors=re.findall(r'<a href="data:application/json;charset=utf-8;base64,([A-Za-z0-9+/=]+)" download="recovered-original-v069.json">',self.page)
        self.assertEqual(len(anchors),1)
        self.assertEqual(base64.b64decode(anchors[0],validate=True),(P/'recovered-original-v069.json').read_bytes())

if __name__=='__main__': unittest.main()
