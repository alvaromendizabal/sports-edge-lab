"""Cohort, timing, accounting and public-scope gates for the V078 review."""
from datetime import datetime, timedelta
import gzip
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
        self.assertEqual(d['source_as_of'], '2026-11-15T03:35:19Z')
        self.assertEqual(d['actual_child_exit_code'], 0)
        self.assertEqual(d['counts'], dict(new_fits=35, new_winner_calibrators=11,
            reused_states=192, new_issue_records=2184, new_issue_games=84, failed_fits=0))
        self.assertEqual(d['publication_new_fits'], 0)
        self.assertEqual(d['publication_new_issues'], 0)
        self.assertFalse(d['promotion'])
        self.assertEqual(d['fit_accounting_semantics'], 'EXECUTED_TASKS_NOT_DISTINCT_NEW_INPUT_FITS')
        self.assertIn('26 avoidable strict base refits', d['fit_reuse_caveat'])
        self.assertEqual(d['fit_necessity_audit']['avoidable_repeated_strict_base_fits'], 26)
        self.assertEqual(d['fit_necessity_audit']['changed_training_input_challenger_fits'], 9)
        self.assertEqual(d['fit_necessity_audit']['observed_optimizer_fits'], 35)

    def test_every_observed_game_and_missing_state_remain(self):
        self.assertEqual(len(self.games), 2742)
        self.assertEqual(len({g['id'] for g in self.games}), 2742)
        self.assertEqual(len(self.current), 888)
        self.assertEqual(sum(g['status'] == 'final' for g in self.current), 738)
        self.assertEqual(sum(g['status'] != 'final' for g in self.current), 150)
        self.assertEqual(sum(bool(g['issued_rows']) for g in self.current), 84)
        self.assertEqual(sum(g['issued_rows'] for g in self.current), 2184)
        self.assertFalse(self.data['census']['complete_population_proved'])

    def test_real_issued_cohort_keeps_target_specific_leaders(self):
        models = [r for r in self.data['models'] if r['cohort'] == 'issued']
        self.assertEqual(len(models), 26)
        self.assertEqual({r['n'] for r in models}, {36})
        winner = [r for r in models if r['target'] == 'winner']
        best = min(winner, key=lambda r:r['metrics']['log_loss'])
        self.assertEqual(best['family'], 'LightGBM')
        self.assertEqual(best['metrics']['log_loss'], .4906126093342449)
        self.assertEqual(best['metrics']['brier'], .15737200748293056)
        self.assertEqual(best['metrics']['accuracy'], 29/36)
        self.assertEqual(len(best['conditional_accuracy_interval95']), 2)
        self.assertIn('week', best['uncertainty_limitation'].lower())
        self.assertEqual({r['family'] for r in winner if r['metrics']['accuracy'] == 30/36},
                         {'CatBoost'})
        margin = min((r for r in models if r['target'] == 'margin'), key=lambda r:r['metrics']['mae'])
        total = min((r for r in models if r['target'] == 'total'), key=lambda r:r['metrics']['mae'])
        self.assertEqual(margin['family'], 'LightGBM')
        self.assertEqual(margin['metrics']['mae'], 12.445804257104395)
        self.assertEqual(total['family'], 'Extra Trees')
        self.assertEqual(total['metrics']['mae'], 12.582519838236339)
        self.assertIn('36', self.data['prospective_repair'])
        self.assertIn('156', self.data['prospective_repair'])

    def test_distinct_original_reconstruction_and_saved_monitor_cohorts(self):
        models = self.data['models']
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'original'}, {41})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'reconstruction'}, {738})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'monitor'}, {301})
        tf = next(r for r in models if r['cohort'] == 'monitor' and r['family'] == 'TensorFlow')
        self.assertEqual(tf['metrics']['log_loss'], .46551880819770836)
        self.assertEqual(tf['metrics']['accuracy'], 237/301)
        self.assertEqual(self.data['archive_comparisons'][-1]['label'], 'Unresolved saved market reference')

    def test_same_cohort_scores_and_all_negative_experiments_retained(self):
        self.assertEqual(len(self.data['scores']), 36)
        self.assertEqual(len(self.data['comparisons']), 54)
        for r in self.data['scores']:
            self.assertEqual(r['n'], {2024:918, 2025:934, 2026:738}[r['season']])
            self.assertEqual(r['evidence_class'], 'LATER_FITTED_RECONSTRUCTION')
        self.assertEqual({r['policy'] for r in self.data['scores']}, {'expanding','recent','decayed','control'})
        self.assertEqual({r['weight_policy'] for r in self.data['comparisons']}, {'primary','equal','current65'})
        for r in self.data['comparisons']:
            self.assertLessEqual(*r['adjusted95_interval'])
            self.assertEqual(r['season_details']['2026']['n'], 738)

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
        self.assertEqual(len({g['id'] for g,c in shown if g['status'] == 'final'}), 41)
        for g,c in shown:
            self.assertIn(c['status'], {'original_issued','future_issued'})
            self.assertLess(datetime.fromisoformat(c['issue_time'].replace('Z','+00:00')),
                            datetime.fromisoformat(g['kickoff'].replace('Z','+00:00')))

    def test_return_cpu_and_secondary_progress_are_truthful(self):
        r = self.data['return']
        self.assertEqual(r['logical_zip_bytes'], 3489519417)
        self.assertEqual(r['logical_archive_sha256'], '03b240fdf95455d1377b8700be58f58c994be516ef7750717b1c3c4777853f88')
        self.assertEqual(r['parts'], 7)
        self.assertEqual(r['finalization_status'], 'DURABLE_CLOSURE_VERIFIED')
        self.assertIn('initial finalization check failed', self.data['execution_note'])
        self.assertIn('zero new fits', self.data['execution_note'])
        self.assertEqual(r['part_limit_bytes'], 512 << 20)
        self.assertFalse(r['parts_independently_extractable'])
        self.assertFalse(r['manual_upload_required'])
        self.assertIn('not whole-host saturation proof', self.data['cpu_detail'])
        for text in ['300', '168', '84', 'Zero model fits']:
            self.assertIn(text, self.data['feature_progress'])

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
