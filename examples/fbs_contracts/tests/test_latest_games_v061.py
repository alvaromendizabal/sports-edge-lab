"""Public saved-output contracts: no fitting, rescoring, or provider requests."""
from pathlib import Path
import base64
import csv
import datetime
import gzip
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'docs/fbs'
DATA = json.loads(gzip.decompress((DOCS / 'latest-games-v061.json.gz').read_bytes()))


class LatestGamesV061Tests(unittest.TestCase):
    def test_denominator_and_identity(self):
        self.assertEqual(len(DATA['games']), 888)
        self.assertEqual(len({g['game_id'] for g in DATA['games']}), 888)
        self.assertTrue(all(g['season'] == 2026 for g in DATA['games']))

    def test_schedule_partition(self):
        self.assertEqual(sum(g['completed'] for g in DATA['games']), 685)
        self.assertEqual(sum(g['schedule_status'] == 'CURRENT_ORIGIN_REFRESH_DUE' for g in DATA['games']),145)
        self.assertEqual(sum(g['kickoff_utc'] is None for g in DATA['games']),55)
        self.assertEqual(sum(not g['completed'] and g['kickoff_utc'] is not None and
            g['schedule_status'] != 'CURRENT_ORIGIN_REFRESH_DUE' for g in DATA['games']),3)

    def test_layer_coverage_and_missingness(self):
        counts = {name: sum(g['layers'][name]['values']['p_home'] is not None for g in DATA['games'])
                  for name in DATA['layer_definitions']}
        self.assertEqual(counts, {'original':148,'calibrated':122,'mixture_global':114,'mixture_gated':114,'replay':790})
        for g in DATA['games']:
            for layer in g['layers'].values():
                self.assertIsNone(layer['values']['exact_line_cover'])
                self.assertFalse(layer['new_issue_created_by_export'])

    def test_saved_issues_precede_target_kickoff(self):
        def timestamp(x): return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
        for g in DATA['games']:
            for name, layer in g['layers'].items():
                if name == 'replay' or layer['values']['p_home'] is None: continue
                self.assertLess(timestamp(layer['information_cutoff_utc']),timestamp(g['kickoff_utc']))
                self.assertLess(timestamp(layer['original_durable_observed_at']),timestamp(g['kickoff_utc']))
                self.assertEqual(layer['horizon'],'CURRENT_ORIGIN_OUTLOOK')
                self.assertFalse(layer['production_champion'])

    def test_replay_is_never_issued(self):
        for g in DATA['games']:
            replay = g['layers']['replay']
            self.assertFalse(replay['forecast_issued'])
            self.assertFalse(replay['historical_availability_proved'])
            self.assertIsNone(replay['information_cutoff_utc'])

    def test_all_future_baselines_new_and_reused_have_distinct_clocks(self):
        future=[g for g in DATA['games'] if g['schedule_status']=='CURRENT_ORIGIN_REFRESH_DUE']
        self.assertEqual(len(future),145)
        self.assertTrue(all(g['layers']['original']['values']['p_home'] is not None for g in future))
        self.assertEqual(sum(g['owner_baseline_continuation']['recovery_status']=='NEW' for g in future),40)
        self.assertEqual(sum(g['owner_baseline_continuation']['recovery_status']=='REUSED' for g in future),105)
        for g in future:
            b=g['owner_baseline_continuation'];original=g['layers']['original']
            self.assertEqual(b['actual_information_cutoff_utc'],original['information_cutoff_utc'])
            self.assertEqual(b['actual_durable_observation_at'],original['original_durable_observed_at'])
            self.assertFalse(b['metric_champion'])
            if b['recovery_status']=='REUSED':
                self.assertLess(b['actual_information_cutoff_utc'],b['requested_current_origin_cutoff'])

    def test_no_invented_champion(self):
        self.assertEqual(DATA['champion_status']['authorized_metric_champions'],0)
        self.assertIsNone(DATA['summary']['new_champion_forecasts'])
        self.assertEqual(DATA['summary']['new_genuine_forecasts_root_scope'],40)
        self.assertTrue(all(g['metric_champion_forecast'] is None for g in DATA['games']))
        self.assertTrue(all(r['selected_model'] is None for r in DATA['champion_status']['roles']))

    def test_every_provider_target_resolves_with_identity(self):
        names={'DraftKings','Kalshi','Polymarket Global','Polymarket US'}
        for g in DATA['games']:
            self.assertEqual(set(g['provider_reference_ids']),names)
            for provider, targets in g['provider_reference_ids'].items():
                self.assertEqual(set(targets),{'winner','margin','total','cover_probability'})
                for target,index in targets.items():
                    record=DATA['provider_evidence'][index]
                    self.assertEqual((record['provider'],record['target']),(provider,target))
                    self.assertIn('quote_at',record); self.assertIn('acquired_at',record)
                    self.assertFalse(record['reference_is_model_expected_score'])

    def test_probability_and_point_rounding(self):
        for g in DATA['games']:
            for layer in g['layers'].values():
                for key,value in layer['values'].items():
                    if value is None or isinstance(value,dict): continue
                    places=4 if key in ('p_home','exact_line_cover') else 1
                    self.assertEqual(value,round(value,places))
                    if key=='p_home': self.assertTrue(0<=value<=1)

    def test_csv_complete_five_layer_denominator(self):
        with (DOCS/'latest-games-v061.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),4440)
        self.assertEqual(len({(r['game_id'],r['layer']) for r in rows}),4440)
        self.assertEqual({r['game_id'] for r in rows},{g['game_id'] for g in DATA['games']})

    def test_browser_payload_exactly_matches_download(self):
        js=(DOCS/'latest-games-v061-data.js').read_text()
        encoded=re.fullmatch(r'window.FBS_LATEST_V061_GZIP="([A-Za-z0-9+/=]+)";\n',js).group(1)
        self.assertEqual(base64.b64decode(encoded),(DOCS/'latest-games-v061.json.gz').read_bytes())

    def test_public_boundary_no_private_cloud_or_recipe_keys(self):
        raw=json.dumps(DATA)
        for forbidden in ('s3://','/home/sagemaker-user','arn:aws:','recipe_policy_sha256',
                          'model_snapshot_sha256','candidate_id','raw_response','api_key','source_rows'):
            self.assertNotIn(forbidden,raw)

    def test_leaders_keep_support_and_exposed_status(self):
        self.assertEqual(len(DATA['historical_cohort_leaders']),49)
        for row in DATA['historical_cohort_leaders']:
            self.assertGreater(row['games'],0)
            self.assertEqual(len(row['cohort_sha256']),64)
            self.assertEqual(row['selection_status'],'EXPOSED_DESCRIPTIVE_COHORT_LEADER_NOT_PROMOTED')

    def test_recovered_narrow_cohort_remains_separate_and_unpromoted(self):
        r=DATA['previously_omitted_231_game_record']
        self.assertEqual(r['games'],231)
        self.assertEqual(r['best_saved_log_loss'],0.416199)
        self.assertEqual(r['best_loss_model_correct'],188)
        self.assertEqual(r['best_accuracy_model_correct'],191)
        self.assertEqual(r['complete_book_correct'],185)
        self.assertEqual(r['draftkings_correct'],186)
        self.assertTrue(r['full_precision_machine_evidence_authenticated'])
        self.assertFalse(r['promotion'])
        self.assertFalse(r['selection_permitted'])
        self.assertTrue(r['not_full_season'])
        self.assertTrue(r['not_same_as_301_game_panel'])
        self.assertTrue(r['not_kalshi_only'])
        self.assertEqual(DATA['current_low_logloss_evidence']['games'],301)

    def test_page_has_download_and_clock_fallback(self):
        text=(DOCS/'latest-games-v061.html').read_text()
        self.assertIn('<noscript>',text)
        self.assertIn('latest-games-v061.csv',text)
        self.assertIn('latest-games-v061.json.gz',text)
        self.assertIn('01:29:35',text)
        self.assertNotIn('https://cdn.',text)


if __name__=='__main__': unittest.main()
