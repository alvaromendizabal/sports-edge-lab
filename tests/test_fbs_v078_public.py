"""Cohort, timing, accounting and public-scope gates for the V078 review."""
from datetime import datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs/fbs/v078'


class PublicV078(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((SITE / 'data/review.json').read_text())
        cls.games = json.loads(gzip.decompress((SITE / 'data/games.json.gz').read_bytes()))['games']
        cls.current = [g for g in cls.games if g['season'] == 2026]

    def test_owner_work_is_separate_from_read_only_publication(self):
        d = self.data
        self.assertEqual(d['owner_version'], 'V078')
        self.assertEqual(d['source_as_of'], '2026-11-15T05:10:30Z')
        self.assertEqual(d['actual_child_exit_code'], 0)
        self.assertEqual(d['counts'], dict(new_fits=0, new_winner_calibrators=3,
            reused_states=218, new_issue_records=364, new_issue_games=14, failed_fits=0,
            newly_added_unique_forecast_games=0, reused_base_estimators=9,
            reused_issue_games=70, reused_issue_records=1820,
            total_current_issue_games=84, total_current_issue_records=2184))
        self.assertEqual(d['publication_new_fits'], 0)
        self.assertEqual(d['publication_new_issues'], 0)
        self.assertFalse(d['promotion'])
        self.assertIn('zero new base estimators', d['fit_reuse_caveat'])
        self.assertIn('6 residual calibrations', d['fit_reuse_caveat'])
        self.assertIn('previous 03:35 UTC execution', d['fit_reuse_caveat'])
        self.assertEqual(d['forecast_coverage']['updated_issue_games'], 14)
        self.assertEqual(d['forecast_coverage']['reused_issue_games'], 70)
        self.assertEqual(d['forecast_coverage']['new_unique_games'], 0)

    def test_every_observed_game_and_missing_state_remain(self):
        self.assertEqual(len(self.games), 2742)
        self.assertEqual(len({g['id'] for g in self.games}), 2742)
        self.assertEqual(len(self.current), 888)
        self.assertEqual(sum(g['status'] == 'final' for g in self.current), 744)
        self.assertEqual(sum(g['status'] != 'final' for g in self.current), 144)
        self.assertEqual(sum(g['status'] == 'pending' for g in self.current), 91)
        self.assertEqual(sum(g['status'] == 'tbd' for g in self.current), 53)
        self.assertEqual(sum(bool(g['issued_rows']) for g in self.current), 14)
        self.assertEqual(sum(g['issued_rows'] for g in self.current), 364)
        self.assertFalse(self.data['census']['complete_population_proved'])

    def test_real_issued_cohort_keeps_target_specific_leaders(self):
        models = [r for r in self.data['models'] if r['cohort'] == 'issued']
        self.assertEqual(len(models), 26)
        self.assertEqual({r['n'] for r in models}, {41})
        winner = [r for r in models if r['target'] == 'winner']
        best = min(winner, key=lambda r:r['metrics']['log_loss'])
        self.assertEqual(best['family'], 'CatBoost')
        self.assertEqual(best['metrics']['log_loss'], .5840039078172258)
        self.assertEqual(best['metrics']['brier'], .19813684004368032)
        self.assertEqual(best['metrics']['accuracy'], 31/41)
        self.assertEqual(len(best['conditional_accuracy_interval95']), 2)
        self.assertIn('week', best['uncertainty_limitation'].lower())
        self.assertEqual({r['family'] for r in winner if r['metrics']['accuracy'] == 31/41},
                         {'CatBoost'})
        margin = min((r for r in models if r['target'] == 'margin'), key=lambda r:r['metrics']['mae'])
        total = min((r for r in models if r['target'] == 'total'), key=lambda r:r['metrics']['mae'])
        self.assertEqual(margin['family'], 'TensorFlow')
        self.assertEqual(margin['metrics']['mae'], 13.263457729417151)
        self.assertEqual(margin['metrics']['rmse'], 16.586628814241994)
        self.assertEqual(total['family'], 'Extra Trees')
        self.assertEqual(total['metrics']['mae'], 12.052584621359037)
        self.assertIn('41 distinct games', self.data['prospective_repair'])
        self.assertIn('182 rows', self.data['prospective_repair'])

    def test_distinct_original_reconstruction_and_saved_monitor_cohorts(self):
        models = self.data['models']
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'original'}, {46})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'reconstruction'}, {744})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'monitor'}, {301})
        tf = next(r for r in models if r['cohort'] == 'monitor' and r['family'] == 'TensorFlow')
        self.assertEqual(tf['metrics']['log_loss'], .46551880819770836)
        self.assertEqual(tf['metrics']['accuracy'], 237/301)
        self.assertEqual(self.data['archive_comparisons'][-1]['label'], 'Unresolved saved market reference')

    def test_same_cohort_scores_and_all_negative_experiments_retained(self):
        self.assertEqual(len(self.data['scores']), 36)
        self.assertEqual(len(self.data['comparisons']), 54)
        for r in self.data['scores']:
            self.assertEqual(r['n'], {2024:918, 2025:934, 2026:744}[r['season']])
            self.assertEqual(r['evidence_class'], 'LATER_FITTED_RECONSTRUCTION')
        self.assertEqual({r['policy'] for r in self.data['scores']}, {'expanding','recent','decayed','control'})
        self.assertEqual({r['weight_policy'] for r in self.data['comparisons']}, {'primary','equal','current65'})
        for r in self.data['comparisons']:
            self.assertLessEqual(*r['adjusted95_interval'])
            self.assertEqual(r['season_details']['2026']['n'], 744)

    def test_provider_schema_repair_is_not_qualification(self):
        counts = {('draftkings','winner'):600, ('draftkings','margin'):675, ('draftkings','total'):675,
            ('kalshi','winner'):708, ('kalshi','margin'):594, ('kalshi','total'):594,
            ('polymarket_global','winner'):702, ('polymarket_global','margin'):601,
            ('polymarket_global','total'):603, ('polymarket_us','winner'):680,
            ('polymarket_us','margin'):0, ('polymarket_us','total'):0}
        for (provider,target), expected in counts.items():
            cells = [g['providers'][provider][target] for g in self.current]
            self.assertEqual(sum(c['observed_reference'] for c in cells), expected)
            self.assertFalse(any(c['status'] == 'qualified' for c in cells))
        self.assertEqual(self.data['market']['qualified_cells'], 0)
        self.assertEqual(self.data['market']['normalized_rows'], 15450173)

    def test_only_clock_and_identity_admitted_archived_scalars_display(self):
        shown = []
        for g in self.current:
            for provider, targets in g['providers'].items():
                for target, c in targets.items():
                    if c['value'] is None: continue
                    shown.append((provider,target))
                    self.assertTrue(c['display_eligible'])
                    self.assertTrue(c['identity_matched_reference'])
                    self.assertEqual(c['status'], 'archived_unqualified')
                    cutoff = datetime.fromisoformat(g['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120)
                    for key in ['quote_time','observation_time']:
                        self.assertLessEqual(datetime.fromisoformat(c[key].replace('Z','+00:00')), cutoff)
                    self.assertIn('unqualified', c['display_status'])
                    self.assertTrue(c['value_label'])
        self.assertEqual(len(shown), 194)
        self.assertEqual({p for p,t in shown}, {'draftkings'})
        self.assertEqual(sum(t == 'winner' for p,t in shown), 64)

    def test_preserved_selected_original_values_keep_real_issue_clocks(self):
        shown = [(g,c) for g in self.games for c in g['model'].values()]
        self.assertEqual(len(shown), 399)
        self.assertEqual(len({g['id'] for g,c in shown}), 133)
        self.assertEqual(len({g['id'] for g,c in shown if g['status'] == 'final'}), 46)
        for g,c in shown:
            self.assertIn(c['status'], {'original_issued','future_issued'})
            self.assertLess(datetime.fromisoformat(c['issue_time'].replace('Z','+00:00')),
                            datetime.fromisoformat(g['kickoff'].replace('Z','+00:00')))

    def test_return_cpu_and_secondary_progress_are_truthful(self):
        r = self.data['return']
        self.assertEqual(r['logical_zip_bytes'], 3517855949)
        self.assertEqual(r['logical_archive_sha256'], '6c855777915fe8aed1f3613720598f33f61de6103e30755555442d1d4cda70ea')
        self.assertEqual(r['parts'], 7)
        self.assertEqual(r['finalization_status'], 'VERIFIED_OWNER_RECEIPT')
        self.assertIn('zero new base estimators', self.data['execution_note'])
        self.assertEqual(r['part_limit_bytes'], 512 << 20)
        self.assertFalse(r['parts_independently_extractable'])
        self.assertFalse(r['manual_upload_required'])
        self.assertIn('not whole-host saturation proof', self.data['cpu_detail'])
        for text in ['288', '168', '84', 'Zero model fits']:
            self.assertIn(text, self.data['feature_progress'])

    def test_original_weight_binding_keeps_evaluation_limits(self):
        r = self.data['original_weight_recovery']
        self.assertEqual(r['saved_games'], 301)
        self.assertEqual(r['new_fits'], 0)
        self.assertEqual(r['new_inference'], 0)
        self.assertIn('later-fitted reconstruction', r['detail'])
        self.assertIn('not pregame possession or promotion evidence', r['detail'])

    def test_fixed_audit_baseline_is_pending_only_and_preserves_issue_clocks(self):
        selection = self.data['audit_baseline_selection']
        self.assertEqual(selection['rule'], {'winner':'Logistic regression','margin':'Ridge regression','total':'Ridge regression'})
        self.assertFalse(selection['promotion'])
        self.assertEqual([selection[k] for k in ['new_fits','new_inference','new_issues']], [0,0,0])
        self.assertTrue(all(selection['gates'].values()))
        self.assertEqual(selection['admitted_cells'], 252)
        self.assertEqual(selection['admitted_games'], 84)
        self.assertEqual(selection['missing_games'], 60)
        self.assertEqual(selection['missing_cell_reasons'], {'KICKOFF_UNRESOLVED':159,'TARGET_NOT_FUTURE_BEFORE_T120_CUTOFF':21})
        chosen = datetime.fromisoformat(selection['selection_time'].replace('Z','+00:00'))
        observed = datetime.fromisoformat(self.data['source_as_of'].replace('Z','+00:00'))
        admitted = []
        after_observation = 0
        for game in self.games:
            cells = game.get('audit_model', {})
            if not cells: continue
            self.assertEqual(game['season'], 2026)
            self.assertNotEqual(game['status'], 'final')
            self.assertEqual(set(cells), {'winner','margin','total'})
            for target, cell in cells.items():
                self.assertEqual(cell['family'], selection['rule'][target])
                self.assertEqual(cell['source_alias'], 'Fixed audit baseline')
                if cell['value'] is None:
                    self.assertTrue(cell['reason'])
                    continue
                self.assertEqual(cell['admission_status'], 'PASS')
                self.assertEqual(cell['status'], 'genuine_issued_research')
                clocks = {k:datetime.fromisoformat(cell[k].replace('Z','+00:00')) for k in ['fit_completed_at','prepared_at','issue_time','information_cutoff','requested_horizon_cutoff','selection_time']}
                self.assertLessEqual(clocks['fit_completed_at'], clocks['prepared_at'])
                self.assertLessEqual(clocks['information_cutoff'], clocks['prepared_at'])
                self.assertLessEqual(clocks['prepared_at'], clocks['issue_time'])
                self.assertLessEqual(clocks['issue_time'], chosen)
                self.assertEqual(clocks['selection_time'], chosen)
                self.assertLess(chosen, clocks['requested_horizon_cutoff'])
                self.assertEqual(clocks['requested_horizon_cutoff'], datetime.fromisoformat(game['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120))
                after_observation += clocks['issue_time'] > observed
                admitted.append((game['id'],target))
        self.assertEqual(len(admitted), 252)
        self.assertEqual(len({g for g,t in admitted}), 84)
        self.assertEqual(after_observation, 42, 'Observation precedes the 14 games of legitimate later issuance')

    def test_prior_public_snapshot_bytes_are_preserved(self):
        prior = ROOT / 'docs/fbs/v078-20261115T033519Z'
        receipt = json.loads((prior/'RENDER_RECEIPT.json').read_text())
        self.assertEqual(receipt['source_as_of'], '2026-11-15T03:35:19Z')
        for entry in receipt['files']:
            raw = (prior/entry['path']).read_bytes()
            self.assertEqual(len(raw), entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
        previous = json.loads((prior/'data/review.json').read_text())
        self.assertEqual(previous['counts']['new_fits'], 35)
        self.assertEqual(previous['fit_necessity_audit']['avoidable_repeated_strict_base_fits'], 26)
        self.assertIn('../v078-20261115T033519Z/', (SITE/'index.html').read_text())

    def test_private_material_and_out_of_sport_presentation_absent(self):
        forbidden = re.compile(r's3://|arn:aws:|/home/sagemaker-user|/workspace/|AKIA[0-9A-Z]{16}|BEGIN (?:RSA |EC )?PRIVATE KEY|"(?:model_id|fit_id|state_sha256|coefficients|feature_names|prediction_records)"')
        for p in SITE.rglob('*'):
            if not p.is_file(): continue
            self.assertNotIn(p.suffix, {'.pyz','.zip','.parquet','.pickle','.pkl','.pt','.onnx'})
            self.assertIsNone(forbidden.search((gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()).decode()), p.name)
        for p in (ROOT/'docs/fbs').rglob('*'):
            if not p.is_file(): continue
            body = gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes()
            self.assertNotIn(b'circa', body.lower(), str(p.relative_to(ROOT)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
