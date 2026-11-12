"""Audit the public V071 result, original clocks and bounded reporting scope."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import io
import json
import re
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'docs/fbs'


def dt(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


class ActualV071PublicEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (P / 'latest-v072.json').read_text()
        cls.d = json.loads(cls.raw)
        cls.games = cls.d['games']
        cls.prior = json.loads((P / 'latest-v071.json').read_text())

    def test_distinct_new_reused_gap_fit_evaluation_and_output_accounting(self):
        counts, sweep = self.d['run_counts'], self.d['refresh']
        self.assertEqual((counts['new_model_fits'], counts['new_genuine_forecasts'], counts['new_prediction_outputs']), (0, 72, 517))
        self.assertEqual(counts['new_prediction_outputs'], counts['new_foundation_outputs'] + counts['new_native_replay_outputs'])
        self.assertEqual((counts['new_foundation_outputs'], counts['new_native_replay_outputs'], counts['new_owner_metric_evaluations']), (216, 301, 251))
        self.assertEqual(sweep['eligible_tasks'], sweep['new_issues'] + sweep['reused_issues'] + sweep['explicit_fixture_gaps'])
        self.assertEqual((sweep['eligible_tasks'], sweep['new_issues'], sweep['reused_issues'], sweep['explicit_fixture_gaps'], sweep['unattempted_tasks']), (143, 72, 70, 1, 0))
        self.assertEqual(counts['runtime_exit_code'], 2)
        self.assertFalse(self.d['parallel_work']['broad_parallel_fit_stage_reached'])
        self.assertIsNone(self.d['parallel_work']['measured_12_core_throughput_this_run'])

    def test_every_game_and_missing_context_is_accounted(self):
        self.assertEqual(len(self.games), 2742)
        self.assertEqual(len({(g['season'], g['id']) for g in self.games}), 2742)
        self.assertEqual(Counter(g['season'] for g in self.games), {2024:920, 2025:934, 2026:888})
        current = [g for g in self.games if g['season'] == 2026]
        self.assertEqual(sum(g['completed'] for g in current), 691)
        self.assertEqual(sum(not g['completed'] for g in current), 197)
        self.assertEqual(sum(not g['kickoff'] for g in current), 54)
        self.assertEqual([sum(bool(g[key]) for g in current) for key in ('current', 'latest', 'saved', 'recovered_original')], [142,72,148,55])
        self.assertEqual(sum(g['completed'] and bool(g['saved']) for g in current), 6)
        gap = next(g for g in current if g['id'] == '401866465')
        self.assertTrue(gap['fixture_gap'])
        self.assertIsNone(gap['current']); self.assertIsNone(gap['latest']); self.assertIsNone(gap['saved'])
        self.assertTrue(all(g['current'] is None and g['latest'] is None for g in current if g['completed'] or not g['kickoff']))

    def test_reused_issues_keep_values_and_original_clocks(self):
        prior = {g['id']:g for g in self.prior['games']}
        reused = [g for g in self.games if g['current'] and g['current']['run_status'] == 'REUSED_ORIGINAL_ISSUE']
        self.assertEqual(len(reused), 70)
        for g in reused:
            x, old = g['current'], prior[g['id']]['latest']
            self.assertIsNotNone(old)
            for key in ('probability','margin','total','home_score','away_score','issue_at','cutoff_at','computed_at'):
                self.assertEqual(x[key], old[key])
            self.assertGreater(dt(x['fixture_observed_at']), dt(x['issue_at']))
            self.assertIsNone(x['source_at'])
            self.assertIsNone(g['latest'])
        continuity = self.d['continuity']
        self.assertEqual((continuity['V070_eligible_issue_versions'], continuity['V071_eligible_issue_versions'], continuity['earlier_eligible_issue_versions_lost']), (239,536,0))
        self.assertEqual(continuity['newly_visible_eligible_versions'], continuity['new_original_V071_issues'] + continuity['additional_recovered_older_versions'])

    def test_selected_forecast_values_and_information_clocks(self):
        for g in self.games:
            for layer in ('current','latest','saved','recovered_original'):
                x = g[layer]
                if x is None:
                    continue
                self.assertLessEqual(dt(x['cutoff_at']), dt(x['issue_at']))
                self.assertLess(dt(x['issue_at']), dt(g['kickoff']))
                self.assertFalse(x['promotion_authorized'])
                self.assertGreaterEqual(x['probability'],0); self.assertLessEqual(x['probability'],1)
                for interval_key in ('margin_intervals','total_intervals'):
                    if x.get(interval_key):
                        for endpoints in x[interval_key].values():
                            self.assertEqual(len(endpoints),2); self.assertLessEqual(*endpoints)
                if layer in ('current','latest'):
                    self.assertLessEqual(dt(x['maximum_information_at']),dt(x['cutoff_at']))
                    self.assertLessEqual(dt(x['model_at']),dt(x['cutoff_at']))
                    self.assertLessEqual(dt(x['cutoff_at']),dt(x['computed_at']))
                    self.assertLessEqual(dt(x['computed_at']),dt(x['issue_at']))
                    self.assertEqual(x['horizon'],'CURRENT_ORIGIN_OUTLOOK')
                if layer == 'latest':
                    self.assertEqual(x['run_status'],'NEW_V071_ISSUE')
                if layer == 'recovered_original':
                    self.assertIsNone(x['margin']); self.assertIsNone(x['total'])

    def test_annual_banks_and_fresh_monitor_remain_separate(self):
        rows = self.d['annual_leaders']
        self.assertEqual(Counter(r['season'] for r in rows), {2024:7,2025:7,2026:7})
        keys = ('season','target','metric','value','games','families')
        self.assertEqual([{k:r[k] for k in keys} for r in rows], [{k:r[k] for k in keys} for r in self.prior['annual_leaders']])
        self.assertEqual({r['games'] for r in rows if r['season']==2026},{688})
        fresh = self.d['fresh_301_monitor']
        self.assertEqual((fresh['games'],fresh['full_current_finals'],fresh['finals_without_source_bank'],fresh['new_owner_metric_evaluations']), (301,691,390,251))
        self.assertEqual(fresh['new_model_fits'],0)
        values = {r['metric']:r['value'] for r in fresh['leaders']}
        self.assertAlmostEqual(values['accuracy'],0.7906976744186046,places=14)
        self.assertAlmostEqual(values['log_loss'],0.46551880819770836,places=14)
        self.assertAlmostEqual(values['brier'],0.15263011173024493,places=14)
        self.assertAlmostEqual(values['ece10'],0.024234917692009743,places=14)
        self.assertEqual(self.d['separate_685_catboost_winner']['games'],685)
        self.assertEqual({r['cohort_games'] for r in self.d['separate_231_comparison']},{231})
        self.assertEqual(len(self.d['champion_roles']),8)
        self.assertEqual(self.d['champions']['qualified_new_global_or_rolling_champions'],0)
        retained = self.d['retained_cohort_roles']
        self.assertEqual(len(retained),81)
        cohorts = {(r['season'],r['target'],r['cohort_alias'],r['games'],r['protocol'],r['period']) for r in retained}
        self.assertEqual(len(cohorts),33)
        self.assertTrue(all(not r['new_V071_metric_evaluation'] and not r['promotion_authorized'] for r in retained))

    def test_provider_clock_states_are_not_qualified_values(self):
        qualified = self.d['provider_qualified_cohorts']
        self.assertEqual(len(qualified),12)
        for row in qualified:
            self.assertEqual([row[k] for k in ('qualified_winner_games','qualified_margin_games','qualified_total_games','qualified_cover_games')],[0,0,0,0])
        for item in self.d['provider_evidence']:
            self.assertFalse(item['statistically_usable_baseline'])
            self.assertNotIn('saved_reference_value',item)
            for key in ('quote_at','acquired_at'):
                if item[key]: dt(item[key])
        for g in self.games:
            self.assertEqual(len(g['providers']),4)
            for targets in g['providers']:
                self.assertEqual(len(targets),4)
                for code in targets:
                    self.assertGreaterEqual(code,0); self.assertLess(code,len(self.d['provider_evidence']))

    def test_embedded_json_and_csv_preserve_selected_data(self):
        html = (P/'latest-v072.html').read_text()
        embedded = re.search(r'<script id="report-data" type="application/json">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(embedded),self.d)
        rows = list(csv.DictReader(io.StringIO((P/'issued-v071-selected.csv').read_text())))
        by = {g['id']:g for g in self.games if g['current']}
        self.assertEqual(len(rows),142); self.assertEqual({r['game_id'] for r in rows},set(by))
        self.assertEqual(sum(r['run_status']=='NEW_V071_ISSUE' for r in rows),72)
        for r in rows:
            x = by[r['game_id']]['current']
            self.assertEqual(float(r['home_probability']),x['probability'])
            self.assertEqual(r['issue_at_utc'],x['issue_at'])
            self.assertEqual(r['model_at_utc'],x['model_at'])
        self.assertEqual(len(list(csv.DictReader(io.StringIO((P/'season-inventory-v072.csv').read_text())))),2742)

    def test_public_boundary_and_original_source_identity(self):
        forbidden = {'model_id','model_sha256','model_snapshot_sha256','original_record_identity_sha256','recipe','recipe_id','recipe_policy_sha256','feature_names','weights','bucket','s3_key','credentials','api_key','raw_quotes','saved_reference_value','promotion_thresholds','promotion_support'}
        def visit(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&forbidden)
                for item in value.values(): visit(item)
            elif isinstance(value,list):
                for item in value: visit(item)
            elif isinstance(value,str):
                self.assertNotRegex(value,r's3://|arn:aws:|/home/sagemaker-user|/sports-edge-lab/shared/|\b(?:betting|wager|bankroll|stake|ROI)\b')
        visit(self.d)
        self.assertFalse(self.d['publication']['metrics_rescored_from_public_values'])
        self.assertFalse(self.d['publication']['entire_immutable_issue_archive_published'])
        self.assertEqual(self.d['source_owner_return_sha256'],'5f8c142f71fc9df9e743796ed111c76005a823779d4a58e3ef2aaf16413a69a4')

    def test_prior_landing_and_numerical_assets_remain_preserved(self):
        expected = {'current.html': '8002f35a65db433f2bff6c7bbc53d7cd0d862639', 'complete.html': '774dc58ea661154a3fd6606e73a0f47401bdcee0', 'README.md': 'e23fc1e711ca0c4469dbdc2b3af79266d50cf7c6', 'latest-v071.html': 'd6d63deedd125ef609bdb7363135b6cb1acc637c', 'latest-v071.json': '5ea77062f7d2db6fb7b8ebb10343bef404bdc084', 'issued-v070-selected.csv': 'e274a05c60fb85f840b8c0e62c8afa12e97eb5c5', 'season-inventory-v071.csv': 'a9e191e973a30539ecd43299be5f2b08065f9b5f'}
        for name in ('current.html','complete.html'):
            text = (P/name).read_text()
            clean = re.sub(r'<!-- FBS_V072_LATEST_LINK_START -->.*?<!-- FBS_V072_LATEST_LINK_END -->','',text,flags=re.S)
            self.assertEqual(blob(clean.encode()),expected[name])
        text = (P/'README.md').read_text()
        clean = re.sub(r'<!-- FBS_V072_ACTUAL_V071_START -->.*?<!-- FBS_V072_ACTUAL_V071_END -->\n\n','',text,flags=re.S)
        self.assertEqual(blob(clean.encode()),expected['README.md'])
        for name in ('latest-v071.html','latest-v071.json','issued-v070-selected.csv','season-inventory-v071.csv'):
            self.assertEqual(blob((P/name).read_bytes()),expected[name])

    def test_export_adds_latest_report_and_preserves_prior_entrypoints(self):
        export = runpy.run_path(str(ROOT/'examples/fbs_contracts/export_site.py'))
        self.assertEqual(export['SOURCE_FILES']['index.html'],'latest-v072.html')
        self.assertEqual(export['SOURCE_FILES']['season-archive.html'],'index.html')
        self.assertEqual(len(export['ASSETS']),len(set(export['ASSETS'])))
        for name in ('latest-v072.html','latest-v072.js','latest-v072.css','latest-v072.json','issued-v071-selected.csv','season-inventory-v072.csv','latest-v071.html','current.html','complete.html'):
            self.assertIn(name,export['ASSETS'])


if __name__ == '__main__':
    unittest.main()
