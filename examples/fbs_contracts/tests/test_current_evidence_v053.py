"""Public saved-evidence contracts. No provider calls or model evaluation."""
import base64,gzip,hashlib,json,shutil,subprocess,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

class CurrentEvidenceV053Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(gzip.decompress((ROOT/'docs/fbs/current-evidence-v053.json.gz').read_bytes()))
        cls.status=json.loads((ROOT/'docs/fbs/execution-status-v053.json').read_text())

    def test_every_game_and_separate_issue_population_is_retained(self):
        d=self.data;self.assertEqual(len(d['games']),2742)
        self.assertEqual(len({g['id'] for g in d['games']}),2742)
        self.assertEqual(sum(g['season']==2026 for g in d['games']),888)
        originals=[g for g in d['games'] if g['original']['p_home'] is not None]
        revisions=[g for g in d['games'] if g['calibrated']['p_home'] is not None]
        self.assertEqual(len(originals),122);self.assertEqual(len(revisions),122)
        self.assertEqual({g['id'] for g in originals},{g['id'] for g in revisions})
        self.assertEqual(sum(g['season']==2026 and g['original']['p_home'] is None for g in d['games']),766)
        self.assertFalse(d['all_game_forecasts_complete'])

    def test_issues_keep_their_own_strict_future_clocks(self):
        for g in self.data['games']:
            for name in ('original','calibrated'):
                v=g[name]
                if v['p_home'] is not None:
                    self.assertLess(v['original_durable_observed_at'],g['kickoff_utc'])
                    self.assertLess(v['information_cutoff_utc'],g['kickoff_utc'])
                    self.assertEqual(v['horizon'],'CURRENT_ORIGIN_OUTLOOK')
                    self.assertFalse(v['production_champion'])
            self.assertFalse(g['historical']['forecast_issued'])
        self.assertEqual(sum(g['original']['original_durable_observed_at']<'2026-11-09T22:00:00Z'
                             for g in self.data['games'] if g['original']['p_home'] is not None),108)

    def test_failed_packaging_does_not_erase_science_or_become_accepted_delivery(self):
        s=self.status
        self.assertEqual((s['new_base_fits'],s['new_calibration_fits']),(46,2))
        self.assertEqual(s['new_genuine_issues'],136)
        self.assertEqual(s['new_unique_foundation_games']+s['new_calibrated_revision_issues'],136)
        self.assertEqual(s['failed_delivery']['bytes']-s['failed_delivery']['strict_limit_bytes'],820499)
        self.assertTrue(s['failed_delivery']['complete_zip_validated'])
        self.assertFalse(s['failed_delivery']['accepted_owner_return'])
        self.assertEqual((s['worker_exit_observed'],s['supervisor_exit_observed']),(1,1))
        self.assertFalse(s['outer_observer_shell_exit_independently_proved'])
        self.assertFalse(s['prepared_successor_execution_claimed'])

    def test_saved_comparison_has_fixed_scope_and_no_promoted_champion(self):
        c=self.data['saved_r12_comparison'];self.assertEqual(c['games'],211)
        self.assertEqual(c['season'],2025);self.assertEqual(c['uncertainty']['blocks'],6)
        self.assertEqual(c['aggregate']['control']['joint_log_loss'],7.750528827609312)
        self.assertEqual(c['aggregate']['calibrated']['joint_log_loss'],7.745092375707569)
        lo,hi=c['uncertainty']['metrics']['joint_log_loss']['percentile95']
        self.assertLess(lo,0);self.assertGreater(hi,0)
        self.assertFalse(c['automatic_promotion']);self.assertFalse(c['historical_availability_proved'])

    def test_calendar_and_provider_gaps_are_exact_not_inferred(self):
        current=self.data['season_counts']['2026']
        self.assertEqual((current['final_games'],current['exact_kickoff_games'],current['kickoff_not_published_games']),(685,807,81))
        self.assertEqual(current['calendar_display_period_games']['current_week'],67)
        self.assertEqual(self.data['provider_capture']['target_rows'],201)
        self.assertEqual(self.data['provider_capture']['new_identity_admitted_rows'],0)
        self.assertEqual(self.data['provider_capture']['qualified_four_provider_baseline_games'],0)
        for g in self.data['games']:
            self.assertEqual(set(g['providers']),{'DraftKings','Kalshi','Polymarket US','Polymarket Global'})
            self.assertTrue(all(not v['qualified_baseline'] for p in g['providers'].values() for v in p.values()))

    def test_earlier_readme_and_data_are_preserved_as_history(self):
        raw=(ROOT/'docs/fbs/README-history-v052.md').read_bytes()
        self.assertEqual(self.status['prior_readme'],{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        earlier=json.loads((ROOT/'docs/fbs/execution-status-v052.json').read_text())
        self.assertEqual(earlier['owner_release'],'V051');self.assertEqual(earlier['new_base_fits'],0)

    def test_public_whitelist_and_offline_javascript_match(self):
        raw=json.dumps(self.data,sort_keys=True)
        for forbidden in ('s3://','arn:aws:','sagemaker-sports','/workspace/','.pyz','fit_identities','recipe_policy',
                          'joint_components','source_event_id','training_game_ids','record_identity_sha256'):
            self.assertNotIn(forbidden,raw)
        compressed=(ROOT/'docs/fbs/current-evidence-v053.json.gz').read_bytes()
        script=(ROOT/'docs/fbs/current-evidence-v053-data.js').read_text().splitlines()[0]
        self.assertEqual(base64.b64decode(json.loads(script.removeprefix('window.FBS_CURRENT_EVIDENCE_V053_GZIP=').rstrip(';'))),compressed)
        for name,var,obj in [('execution-status-v053','FBS_EXECUTION_STATUS_V053',self.status)]:
            script=(ROOT/'docs/fbs'/(name+'-data.js')).read_text()
            self.assertEqual(json.loads(script.removeprefix('window.'+var+'=').rstrip(';\n')),obj)

    @unittest.skipUnless(shutil.which('node'),'Node required for browser-independent presentation contracts')
    def test_filtering_csv_and_layer_contracts(self):
        r=subprocess.run(['node','--test',str(Path(__file__).with_suffix('.cjs'))],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

if __name__=='__main__':unittest.main()
