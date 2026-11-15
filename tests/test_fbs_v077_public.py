"""Public accounting and privacy contracts for the actual V076 owner review."""
import json
from pathlib import Path
import re
import unittest

SITE = Path(__file__).resolve().parents[1] / 'docs/fbs/v077'


class PublicV077(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((SITE / 'data/review.json').read_text())
        cls.games = json.loads((SITE / 'data/games.json').read_text())['games']

    def test_owner_counts_and_publication_are_distinct(self):
        d = self.data
        self.assertEqual(d['source_as_of'], '2026-11-14T18:23:50Z')
        self.assertEqual(d['owner_version'], 'V076')
        self.assertFalse(d['v077_owner_execution_claimed'])
        self.assertEqual(d['actual_child_exit_code'], 2)
        self.assertEqual(d['counts']['new_research_model_fits'], 201)
        self.assertEqual(d['counts']['new_winner_calibrators'], 67)
        self.assertEqual(d['counts']['new_own_state_residual_calibrations'], 134)
        self.assertEqual(d['counts']['reused_prior_recipe_states'], 26)
        self.assertEqual(d['counts']['failed_fit_jobs'], 0)
        self.assertEqual(d['counts']['new_genuine_issues'], 0)
        self.assertEqual(d['publication_new_fits'], 0)
        self.assertFalse(d['promotion'])

    def test_current_census_and_coverage_do_not_mix_old_season_gap(self):
        current = [g for g in self.games if g['season'] == 2026]
        self.assertEqual(len(current), 888)
        self.assertEqual(sum(g['status'] == 'final' for g in current), 696)
        self.assertEqual(sum(g['status'] != 'final' for g in current), 192)
        self.assertEqual(sum(g['coverage'] == 'prepared' for g in current), 121)
        self.assertEqual(sum(g['coverage'] == 'missing' for g in current), 71)
        self.assertEqual(sum(g['status'] == 'tbd' for g in current), 53)
        self.assertEqual(sum(g['missing_reason'] == 'T120_ALREADY_PASSED' for g in current), 18)
        self.assertEqual(len(self.games), 2742)
        self.assertEqual(len({g['id'] for g in self.games}), 2742)
        self.assertFalse(self.data['census']['complete_population_proved'])

    def test_all_saved_policy_target_season_metrics_are_present(self):
        scores = self.data['scores']
        self.assertEqual(len(scores), 36)
        self.assertEqual({(r['policy'],r['target'],r['season']) for r in scores},
            {(p,t,s) for p in ('expanding','recent','decayed','control')
             for t in ('winner','margin','total') for s in (2024,2025,2026)})
        for row in scores:
            self.assertEqual(row['n'], {2024:918,2025:934,2026:696}[row['season']])
            self.assertEqual(row['evidence_class'], 'LATER_FITTED_RECONSTRUCTION')
        actual = next(r for r in scores if (r['policy'],r['target'],r['season']) == ('expanding','winner',2026))
        self.assertEqual(actual['log_loss'], 0.5292706378997566)
        self.assertEqual(actual['brier'], 0.17986085841213761)

    def test_all_weights_windows_and_negative_intervals_are_retained(self):
        rows = self.data['comparisons']
        self.assertEqual(len(rows), 54)
        self.assertEqual({r['weight_policy'] for r in rows}, {'primary','equal','current65'})
        self.assertEqual({r['comparison_window'] for r in rows},
                         {'FULL_OBSERVED_SEASON','MATCHED_ELAPSED_SEASON_DAYS'})
        self.assertEqual(sum(r['adjusted95_interval'][0] > 0 for r in rows), 0)
        self.assertEqual(sum(r['adjusted95_interval'][1] < 0 for r in rows), 29)
        for row in rows:
            expected = (918,934,696) if row['comparison_window'] == 'FULL_OBSERVED_SEASON' else (634,645,696)
            self.assertEqual(tuple(row['season_details'][str(s)]['n'] for s in (2024,2025,2026)), expected)
            self.assertLessEqual(*row['adjusted95_interval'])
        total = next(r for r in rows if (r['policy'],r['target'],r['weight_policy'],r['comparison_window']) ==
                     ('recent','total','primary','FULL_OBSERVED_SEASON'))
        self.assertEqual(total['weighted_relative_skill'], -0.029165476068495743)
        self.assertEqual(total['season_weights'], {'2024':.15,'2025':.35,'2026':.5})

    def test_original_archive_is_not_the_newer_shadow_journal(self):
        d = self.data
        self.assertEqual(d['original_issue_archive']['earlier_v075'], {'correct':0,'n':3})
        self.assertEqual(d['original_issue_archive']['current_v076']['correct'], 2)
        self.assertEqual(d['original_issue_archive']['current_v076']['n'], 5)
        self.assertEqual(d['original_issue_archive']['current_v076']['log_loss'], 0.7302624476145937)
        self.assertEqual(d['previous_shadow_journal']['issue_records'], 3588)
        self.assertEqual(d['previous_shadow_journal']['scored_rows'], 0)
        self.assertEqual(d['original_issue_archive']['eligible_original_margin_residuals'], 5)
        self.assertFalse(d['original_issue_archive']['current_ats_or_kalshi_calibration_passed'])

    def test_market_volume_and_worker_count_do_not_invent_acceptance(self):
        self.assertEqual(self.data['market']['normalized_rows'], 9160172)
        self.assertEqual(self.data['market']['qualified_cells'], 0)
        c = self.data['cpu']
        self.assertEqual(c['workers'], 12)
        self.assertFalse(c['sustained_twelve_core_saturation_proved'])
        self.assertFalse(c['fit_speedup_benchmark_performed'])
        self.assertAlmostEqual(c['job_interval_cpu_equivalents'], 36.484761/4.524611)
        self.assertEqual({r['schedule'] for r in c['score_benchmarks']}, {'1x1','4x1','8x1','12x1','6x2','4x3'})
        by = {r['schedule']:r for r in c['score_benchmarks']}
        self.assertGreater(by['12x1']['wall_seconds'], by['8x1']['wall_seconds'])

    def test_multipart_is_not_mislabelled_and_does_not_require_manual_upload(self):
        r = self.data['return']
        self.assertEqual(r['logical_zip_bytes'], 7501483706)
        self.assertEqual(r['part_count'], 14)
        self.assertEqual(r['part_limit_bytes'], 512 << 20)
        self.assertFalse(r['parts_independently_extractable'])
        self.assertFalse(r['review_manual_upload_required'])
        self.assertEqual(r['logical_archive_sha256'], 'a1159acfe77039aea55a94540c2a3e463074f7131b400a49ead22151fb418336')

    def test_public_projection_excludes_private_payloads_and_candidate_grids(self):
        forbidden = re.compile(r's3://|arn:aws:|/home/sagemaker-user|/workspace/|AKIA[0-9A-Z]{16}|BEGIN (?:RSA |EC )?PRIVATE KEY|"(?:model_id|fit_id|state_sha256|coefficients|feature_names|prediction_records)"')
        for path in SITE.rglob('*'):
            if not path.is_file(): continue
            self.assertNotIn(path.suffix, {'.pyz','.zip','.parquet','.pickle','.pkl','.pt','.onnx'})
            self.assertIsNone(forbidden.search(path.read_text()), path.name)
        for game in self.games:
            self.assertEqual(set(game), {'id','season','home','away','kickoff','status','coverage',
                                         'home_score','away_score','missing_reason','source_observed_at'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
