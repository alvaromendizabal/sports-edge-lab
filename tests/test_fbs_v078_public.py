"""Cohort, timing, accounting and public-scope gates for the V078 review."""
from datetime import datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs/fbs/v078-20261115T194012Z'


class PublicV078R4Archive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((SITE / 'data/review.json').read_text())
        cls.games = json.loads(gzip.decompress((SITE / 'data/games.json.gz').read_bytes()))['games']
        cls.current = [g for g in cls.games if g['season'] == 2026]

    def test_owner_work_is_separate_from_read_only_publication(self):
        d = self.data
        self.assertEqual(d['owner_version'], 'V078')
        self.assertEqual(d['source_as_of'], '2026-11-15T19:40:12Z')
        self.assertEqual(d['actual_child_exit_code'], 2)
        self.assertEqual(d['counts'], dict(new_fits=0, new_winner_calibrators=11,
            reused_states=192, new_issue_records=0, new_issue_games=0, failed_fits=0,
            newly_added_unique_forecast_games=0, reused_base_estimators=35,
            reused_issue_games=83, reused_issue_records=2158,
            total_current_issue_games=83, total_current_issue_records=2158))
        self.assertEqual(d['publication_new_fits'], 0)
        self.assertEqual(d['publication_new_issues'], 0)
        self.assertFalse(d['promotion'])
        self.assertIn('zero new base estimators', d['fit_reuse_caveat'].lower())
        self.assertIn('35 reused base estimators', d['fit_reuse_caveat'])
        self.assertIn('ONE_BASE_STATE_PER_FIT_REQUIRED', d['owner_status_summary'])
        self.assertIn('No new forecast was committed', d['execution_note'])
        self.assertEqual(d['forecast_coverage']['updated_issue_games'], 0)
        self.assertEqual(d['forecast_coverage']['reused_issue_games'], 83)
        self.assertEqual(d['forecast_coverage']['new_unique_games'], 0)

    def test_every_observed_game_and_missing_state_remain(self):
        self.assertEqual(len(self.games), 2742)
        self.assertEqual(len({g['id'] for g in self.games}), 2742)
        self.assertEqual(len(self.current), 888)
        self.assertEqual(sum(g['status'] == 'final' for g in self.current), 751)
        self.assertEqual(sum(g['status'] != 'final' for g in self.current), 137)
        self.assertEqual(sum(g['status'] == 'pending' for g in self.current), 87)
        self.assertEqual(sum(g['status'] == 'tbd' for g in self.current), 50)
        self.assertEqual(sum(bool(g['issued_rows']) for g in self.current), 0)
        self.assertEqual(sum(g['issued_rows'] for g in self.current), 0)
        self.assertEqual(sum(bool(g.get('retained_issue_rows',0)) for g in self.current), 83)
        self.assertEqual(sum(g.get('retained_issue_rows',0) for g in self.current), 2158)
        self.assertFalse(self.data['census']['complete_population_proved'])

    def test_real_issued_cohort_keeps_target_specific_leaders(self):
        models = [r for r in self.data['models'] if r['cohort'] == 'issued']
        self.assertEqual(len(models), 26)
        self.assertEqual({r['n'] for r in models}, {47})
        winner = [r for r in models if r['target'] == 'winner']
        best = min(winner, key=lambda r:r['metrics']['log_loss'])
        self.assertEqual(best['family'], 'CatBoost')
        self.assertEqual(best['metrics']['log_loss'], .600278431842188)
        self.assertEqual(best['metrics']['brier'], .20557745833172103)
        self.assertEqual(best['metrics']['accuracy'], 34/47)
        self.assertEqual(len(best['conditional_accuracy_interval95']), 2)
        self.assertIn('week', best['uncertainty_limitation'].lower())
        self.assertEqual({r['family'] for r in winner if r['metrics']['accuracy'] == 36/47},
                         {'TensorFlow'})
        margin = min((r for r in models if r['target'] == 'margin'), key=lambda r:r['metrics']['mae'])
        total = min((r for r in models if r['target'] == 'total'), key=lambda r:r['metrics']['mae'])
        self.assertEqual(margin['family'], 'TensorFlow')
        self.assertEqual(margin['metrics']['mae'], 14.38822346546689)
        self.assertEqual(margin['metrics']['rmse'], 18.894541814609624)
        self.assertEqual(total['family'], 'Extra Trees')
        self.assertEqual(total['metrics']['mae'], 12.098242900786335)
        self.assertIn('47 distinct games', self.data['prospective_repair'])
        self.assertIn('208 rows', self.data['prospective_repair'])

    def test_distinct_original_reconstruction_and_saved_monitor_cohorts(self):
        models = self.data['models']
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'original'}, {52})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'reconstruction'}, {751})
        self.assertEqual({r['n'] for r in models if r['cohort'] == 'monitor'}, {301})
        tf = next(r for r in models if r['cohort'] == 'monitor' and r['family'] == 'TensorFlow')
        self.assertEqual(tf['metrics']['log_loss'], .46551880819770836)
        self.assertEqual(tf['metrics']['accuracy'], 237/301)
        self.assertEqual(self.data['archive_comparisons'][-1]['label'], 'Unresolved saved market reference')

    def test_newer_one_game_states_do_not_pool_with_the_matched_cohort(self):
        main=[r for r in self.data['models'] if r['cohort']=='issued']
        single=[r for r in self.data['models'] if r['cohort']=='issued_newer_state_single_game']
        self.assertEqual((len(main),len(single)),(26,26))
        self.assertEqual({r['n'] for r in main},{47})
        self.assertEqual({r['n'] for r in single},{1})
        c=next(r for r in self.data['model_cohorts'] if r['id']=='issued_newer_state_single_game')
        self.assertIn('not a 48th distinct game',c['description'])
        self.assertIn('superiority cannot be inferred',c['description'])
        best=min((r for r in main if r['target']=='total'),key=lambda r:r['metrics']['rmse'])
        self.assertEqual(best['family'],'Ridge regression')
        self.assertEqual(best['metrics']['rmse'],14.578537617662615)

    def test_five_objective_roles_preserve_prior_issues_and_state_qualification(self):
        s=self.data['research_objective_selection']
        expected={'winner_probability':('winner','log_loss','CatBoost'),
            'winner_accuracy':('winner','accuracy','TensorFlow'),
            'margin_mae':('margin','mae','TensorFlow'),
            'total_mae':('total','mae','ExtraTrees'),
            'total_rmse':('total','rmse','Ridge regression')}
        self.assertEqual(set(s['roles']),set(expected))
        self.assertEqual([s[k] for k in ['admitted_cells','admitted_games','pending_games']],[415,83,137])
        self.assertEqual([s[k] for k in ['new_fits','new_inference','new_issues']],[0,0,0])
        self.assertFalse(s['promotion']);self.assertFalse(s['historical_leader_backfill'])
        self.assertTrue(all(s['gates'].values()))
        self.assertIn('latest failed-issuance return omits those journal payloads',s['provenance_note'])
        selected=datetime.fromisoformat(s['selection_time'].replace('Z','+00:00'))
        observed=datetime.fromisoformat(self.data['source_as_of'].replace('Z','+00:00'))
        for key,(target,objective,family) in expected.items():
            role=s['roles'][key]
            self.assertEqual((role['target'],role['objective'],role['family']),(target,objective,family))
            self.assertEqual(role['cohort_games'],47)
            self.assertEqual((role['admitted_cells'],role['evaluation_state_matches'],role['evaluation_state_mismatches']),(83,0,83))
            self.assertEqual(role['missing_cell_reasons'],{'KICKOFF_UNRESOLVED':50,'NO_EARLIER_COMMITTED_SELECTED_STATE':3,'TARGET_NOT_FUTURE_BEFORE_T120_CUTOFF':1})
            self.assertIn('another state',role['caveat'])
            values=[];missing=[]
            for g in self.games:
                cells=g.get('research_objective_models',{})
                if g['season']!=2026 or g['status']=='final':
                    self.assertFalse(cells);continue
                self.assertEqual(set(cells),set(expected))
                c=cells[key];self.assertEqual(c['family'],family)
                if c['value'] is None:
                    self.assertEqual(c['status'],'unavailable');self.assertTrue(c['reason']);missing.append(c);continue
                self.assertEqual(c['admission_status'],'PASS');self.assertEqual(c['status'],'genuine_issued_research')
                self.assertTrue(c['retained_from_prior_verified_return']);self.assertFalse(c['evaluation_state_matches'])
                self.assertEqual((c['evaluation_cohort_games'],c['objective']),(47,objective))
                clocks={k:datetime.fromisoformat(c[k].replace('Z','+00:00')) for k in ['fit_completed_at','prepared_at','issue_time','information_cutoff','requested_horizon_cutoff','selection_time']}
                self.assertLessEqual(clocks['fit_completed_at'],clocks['prepared_at'])
                self.assertLessEqual(clocks['information_cutoff'],clocks['prepared_at'])
                self.assertLessEqual(clocks['prepared_at'],clocks['issue_time'])
                self.assertLess(clocks['issue_time'],observed);self.assertEqual(clocks['selection_time'],selected)
                self.assertLess(selected,clocks['requested_horizon_cutoff'])
                self.assertEqual(clocks['requested_horizon_cutoff'],datetime.fromisoformat(g['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120))
                values.append(c)
            self.assertEqual((len(values),len(missing)),(83,54))

    def test_cached_provider_candidates_are_not_qualified_comparison_credit(self):
        p=self.data['market']['bounded_source_progress']
        self.assertEqual((p['owned_raw_events_read'],p['pre_t120_candidate_games'],p['pre_t120_candidate_rows']),(63,53,159))
        self.assertEqual((p['fully_qualified_added_cells'],p['new_paid_credits'],p['new_provider_calls']),(0,0,0))
        self.assertEqual(self.data['market']['qualified_cells'],0)

    def test_current_receipt_binds_actual_rendered_bytes(self):
        r=json.loads((SITE/'RENDER_RECEIPT.json').read_text())
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['source_as_of'],self.data['source_as_of'])
        for e in r['files']:
            raw=(SITE/e['path']).read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(e['bytes'],e['sha256']))

    def test_same_cohort_scores_and_all_negative_experiments_retained(self):
        self.assertEqual(len(self.data['scores']), 36)
        self.assertEqual(len(self.data['comparisons']), 54)
        for r in self.data['scores']:
            self.assertEqual(r['n'], {2024:918, 2025:934, 2026:751}[r['season']])
            self.assertEqual(r['evidence_class'], 'LATER_FITTED_RECONSTRUCTION')
        self.assertEqual({r['policy'] for r in self.data['scores']}, {'expanding','recent','decayed','control'})
        self.assertEqual({r['weight_policy'] for r in self.data['comparisons']}, {'primary','equal','current65'})
        for r in self.data['comparisons']:
            self.assertLessEqual(*r['adjusted95_interval'])
            self.assertEqual(r['season_details']['2026']['n'], 751)

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
        self.assertEqual(len({g['id'] for g,c in shown if g['status'] == 'final'}), 52)
        for g,c in shown:
            self.assertIn(c['status'], {'original_issued','future_issued'})
            self.assertLess(datetime.fromisoformat(c['issue_time'].replace('Z','+00:00')),
                            datetime.fromisoformat(g['kickoff'].replace('Z','+00:00')))

    def test_return_cpu_and_secondary_progress_are_truthful(self):
        r = self.data['return']
        self.assertEqual(r['logical_zip_bytes'], 3523246344)
        self.assertEqual(r['logical_archive_sha256'], '158d30f9b8e965d5e9de48cc4fd49945db155820e14cdae5b3c1028260c7174a')
        self.assertEqual(r['parts'], 7)
        self.assertEqual(r['finalization_status'], 'VERIFIED_OWNER_RECEIPT')
        self.assertIn('zero new base estimators', self.data['execution_note'].lower())
        self.assertEqual(r['part_limit_bytes'], 512 << 20)
        self.assertFalse(r['parts_independently_extractable'])
        self.assertFalse(r['manual_upload_required'])
        self.assertIn('do not prove sustained full capacity occupancy', self.data['cpu_detail'])
        for text in ['274', '172', '86', 'No feature ablation', 'new fit or measured improvement']:
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
        self.assertEqual(selection['admitted_cells'], 249)
        self.assertEqual(selection['admitted_games'], 83)
        self.assertEqual(selection['missing_games'], 54)
        self.assertEqual(selection['missing_cell_reasons'], {'KICKOFF_UNRESOLVED':150,'NO_EARLIER_COMMITTED_SELECTED_STATE':9,'TARGET_NOT_FUTURE_BEFORE_T120_CUTOFF':3})
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
        self.assertEqual(len(admitted), 249)
        self.assertEqual(len({g for g,t in admitted}), 83)
        self.assertEqual(after_observation, 0, 'Latest failure does not re-date retained earlier issues')

    def test_selected_research_leaders_are_future_only_and_state_qualified(self):
        selection = self.data['research_leader_selection']
        self.assertEqual(selection['rule'], {'winner':'CatBoost','margin':'TensorFlow','total':'ExtraTrees'})
        self.assertEqual(selection['selection_cohort_games'], 47)
        self.assertFalse(selection['promotion'])
        self.assertFalse(selection['historical_leader_backfill'])
        self.assertTrue(selection['performance_state_differs_from_current_issued_state'])
        self.assertEqual([selection[k] for k in ['new_fits','new_inference','new_issues']], [0,0,0])
        self.assertTrue(all(selection['gates'].values()))
        self.assertEqual([selection[k] for k in ['admitted_cells','admitted_games','missing_games']], [249,83,54])
        self.assertIn('cross zero', selection['uncertainty_limitation'])
        chosen = datetime.fromisoformat(selection['selection_time'].replace('Z','+00:00'))
        admitted=[]; missing=[]
        for target,role in selection['selection_objectives'].items():
            self.assertEqual(role['cohort_games'], 47)
            self.assertFalse(role['current_state_is_earlier_scored_state'])
            self.assertEqual(role['evaluation_state_matches'],0)
            self.assertEqual(role['evaluation_state_mismatches'],83)
            self.assertEqual(role['objective'], 'log_loss' if target=='winner' else 'mae')
        for game in self.games:
            cells=game.get('research_leader_model',{})
            if not cells: continue
            self.assertEqual(game['season'],2026)
            self.assertNotEqual(game['status'],'final')
            self.assertEqual(set(cells), {'winner','margin','total'})
            for target,cell in cells.items():
                self.assertEqual(cell['family'],selection['rule'][target])
                self.assertEqual(cell['source_alias'],'Selected research leaders')
                self.assertIn('Earlier committed issue',cell['evidence'])
                if cell['value'] is not None:
                    self.assertFalse(cell['evaluation_state_matches'])
                    self.assertTrue(cell['retained_from_prior_verified_return'])
                if cell['value'] is None:
                    self.assertTrue(cell['reason']);missing.append((game['id'],target));continue
                self.assertEqual(cell['admission_status'],'PASS')
                self.assertEqual(cell['status'],'genuine_issued_research')
                clocks={k:datetime.fromisoformat(cell[k].replace('Z','+00:00')) for k in ['fit_completed_at','prepared_at','issue_time','information_cutoff','requested_horizon_cutoff','selection_time']}
                self.assertLessEqual(clocks['fit_completed_at'],clocks['prepared_at'])
                self.assertLessEqual(clocks['information_cutoff'],clocks['prepared_at'])
                self.assertLessEqual(clocks['prepared_at'],clocks['issue_time'])
                self.assertLessEqual(clocks['issue_time'],chosen)
                self.assertEqual(clocks['selection_time'],chosen)
                self.assertLess(chosen,clocks['requested_horizon_cutoff'])
                self.assertEqual(clocks['requested_horizon_cutoff'],datetime.fromisoformat(game['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120))
                admitted.append((game['id'],target))
        self.assertEqual(len(admitted),249)
        self.assertEqual(len({g for g,t in admitted}),83)
        self.assertEqual(len(missing),162)

    def test_prior_public_snapshot_bytes_are_preserved(self):
        prior = ROOT / 'docs/fbs/v078-20261115T051030Z'
        receipt = json.loads((prior/'RENDER_RECEIPT.json').read_text())
        self.assertEqual(receipt['source_as_of'], '2026-11-15T05:10:30Z')
        for entry in receipt['files']:
            raw = (prior/entry['path']).read_bytes()
            self.assertEqual(len(raw), entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
        previous = json.loads((prior/'data/review.json').read_text())
        self.assertEqual(previous['counts']['new_fits'], 0)
        self.assertEqual(previous['counts']['new_issue_records'], 364)
        self.assertEqual(previous['counts']['reused_states'], 218)
        self.assertIn('../v078-20261115T051030Z/', (SITE/'index.html').read_text())

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


class PublicV078R5Current(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = ROOT / 'docs/fbs/v078'
        cls.data = json.loads((cls.site/'data/review.json').read_text())
        cls.games = json.loads(gzip.decompress((cls.site/'data/games.json.gz').read_bytes()))['games']
        cls.current = [g for g in cls.games if g['season'] == 2026]
        cls.r4 = json.loads((SITE/'data/review.json').read_text())
        cls.r4_games = json.loads(gzip.decompress((SITE/'data/games.json.gz').read_bytes()))['games']

    def test_actual_successor_completion_keeps_scientific_limits(self):
        d = self.data
        self.assertEqual(d['source_as_of'], '2026-11-15T20:39:57Z')
        self.assertEqual(d['actual_child_exit_code'], 0)
        self.assertEqual(d['counts'], dict(new_fits=26, new_winner_calibrators=8,
            reused_states=201, failed_fits=0, reused_base_estimators=0,
            new_issue_records=2236, new_issue_games=86,
            reused_issue_records=0, reused_issue_games=0,
            newly_added_unique_forecast_games=3,
            total_current_issue_games=86, total_current_issue_records=2236))
        self.assertEqual(d['scientific_acceptance'], 'PARTIAL; NO_AUTOMATIC_PROMOTION')
        self.assertFalse(d['promotion'])
        self.assertEqual((d['publication_new_fits'], d['publication_new_issues']), (0,0))
        self.assertIn('operational completion is not full scientific acceptance',d['owner_status_summary'].lower())
        self.assertIn('9,150 to 9,152 rows',d['owner_status_summary'])
        self.assertIn('no identical-input base fit was repeated',d['owner_status_summary'])
        self.assertEqual(self.r4['actual_child_exit_code'],2)
        self.assertEqual(self.r4['counts']['new_issue_records'],0)
        self.assertIn('ONE_BASE_STATE_PER_FIT_REQUIRED',self.r4['owner_status_summary'])

    def test_every_fixture_and_current_issue_is_accounted_for(self):
        self.assertEqual(len(self.games),2742)
        self.assertEqual(len({g['id'] for g in self.games}),2742)
        self.assertEqual((len(self.current),sum(g['status']=='final' for g in self.current)),(888,751))
        self.assertEqual(sum(g['status']!='final' for g in self.current),137)
        self.assertEqual(sum(g['status']=='tbd' for g in self.current),50)
        self.assertEqual(sum(g['issued_rows'] for g in self.current),2236)
        self.assertEqual(sum(g['issued_rows']>0 for g in self.current),86)
        self.assertEqual({g['issued_rows'] for g in self.current if g['issued_rows']},{26})
        self.assertEqual(sum(g.get('retained_issue_rows',0) for g in self.current),0)
        self.assertTrue(all(g['status']!='final' for g in self.current if g['issued_rows']))
        self.assertFalse(self.data['census']['complete_population_proved'])

    def test_new_issue_clocks_and_five_objectives_are_independently_qualified(self):
        s=self.data['research_objective_selection']
        expected={'winner_probability':('winner','log_loss','CatBoost'),
            'winner_accuracy':('winner','accuracy','TensorFlow'),
            'margin_mae':('margin','mae','TensorFlow'),
            'total_mae':('total','mae','ExtraTrees'),
            'total_rmse':('total','rmse','Ridge regression')}
        self.assertEqual(set(s['roles']),set(expected))
        self.assertEqual((s['admitted_cells'],s['admitted_games'],s['pending_games']),(430,86,137))
        self.assertTrue(all(s['gates'].values()))
        self.assertEqual([s[k] for k in ['new_fits','new_inference','new_issues']],[0,0,0])
        self.assertFalse(s['promotion']);self.assertFalse(s['historical_leader_backfill'])
        observed=datetime.fromisoformat(self.data['source_as_of'].replace('Z','+00:00'))
        selected=datetime.fromisoformat(s['selection_time'].replace('Z','+00:00'))
        for key,(target,objective,family) in expected.items():
            role=s['roles'][key]
            self.assertEqual((role['target'],role['objective'],role['family']),(target,objective,family))
            self.assertEqual(role['cohort_games'],47)
            self.assertEqual((role['admitted_cells'],role['evaluation_state_matches'],role['evaluation_state_mismatches']),(86,0,86))
            self.assertEqual(role['missing_cell_reasons'],{'KICKOFF_UNRESOLVED':50,'TARGET_NOT_FUTURE_BEFORE_T120_CUTOFF':1})
            values=[];missing=[]
            for g in self.games:
                cells=g.get('research_objective_models',{})
                if g['season']!=2026 or g['status']=='final':
                    self.assertFalse(cells);continue
                self.assertEqual(set(cells),set(expected))
                c=cells[key]
                if c['value'] is None:
                    self.assertEqual(c['status'],'unavailable');self.assertTrue(c['reason']);missing.append(c);continue
                self.assertEqual((c['status'],c['admission_status']),('genuine_issued_research','PASS'))
                self.assertFalse(c['retained_from_prior_verified_return']);self.assertFalse(c['evaluation_state_matches'])
                self.assertEqual((c['family'],c['objective'],c['evaluation_cohort_games']),(family,objective,47))
                clocks={k:datetime.fromisoformat(c[k].replace('Z','+00:00')) for k in ['fit_completed_at','prepared_at','issue_time','information_cutoff','requested_horizon_cutoff','selection_time']}
                self.assertLessEqual(clocks['fit_completed_at'],clocks['prepared_at'])
                self.assertLessEqual(clocks['information_cutoff'],clocks['prepared_at'])
                self.assertLessEqual(clocks['prepared_at'],clocks['issue_time'])
                self.assertGreater(clocks['issue_time'],observed)
                self.assertLessEqual(clocks['issue_time'],selected)
                self.assertEqual(clocks['selection_time'],selected)
                self.assertLess(selected,clocks['requested_horizon_cutoff'])
                self.assertEqual(clocks['requested_horizon_cutoff'],datetime.fromisoformat(g['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120))
                self.assertGreater(g['issued_rows'],0)
                values.append(c)
            self.assertEqual((len(values),len(missing)),(86,51))

    def test_fixed_audit_and_original_foundation_are_separate(self):
        self.assertEqual(self.data['audit_baseline_selection']['rule'],{'winner':'Logistic regression','margin':'Ridge regression','total':'Ridge regression'})
        for key,field in [('audit_baseline_selection','audit_model'),('research_leader_selection','research_leader_model')]:
            s=self.data[key]
            self.assertEqual((s['admitted_cells'],s['admitted_games'],s['missing_games']),(258,86,51))
            self.assertTrue(all(s['gates'].values()))
            self.assertFalse(s['promotion'])
            self.assertEqual(sum(c['value'] is not None for g in self.games for c in g.get(field,{}).values()),258)
            self.assertTrue(all(g['status']!='final' and g['season']==2026 for g in self.games if g.get(field)))
        before={g['id']:g['model'] for g in self.r4_games}
        self.assertEqual({g['id']:g['model'] for g in self.games},before)

    def test_new_issue_delivery_does_not_add_historical_scored_games(self):
        m=self.data['models']
        self.assertEqual(len([r for r in m if r['cohort']=='issued']),26)
        self.assertEqual({r['n'] for r in m if r['cohort']=='issued'},{47})
        self.assertEqual(len([r for r in m if r['cohort']=='issued_newer_state_single_game']),26)
        self.assertEqual({r['n'] for r in m if r['cohort']=='issued_newer_state_single_game'},{1})
        prior={(r['cohort'],r['target'],r['family']):r['metrics'] for r in self.r4['models'] if r['cohort'].startswith('issued')}
        current={(r['cohort'],r['target'],r['family']):r['metrics'] for r in m if r['cohort'].startswith('issued')}
        self.assertEqual(current,prior)
        self.assertEqual(len(self.data['scores']),36)
        self.assertEqual(len(self.data['comparisons']),54)
        self.assertEqual({r['evidence_class'] for r in self.data['scores']},{'LATER_FITTED_RECONSTRUCTION'})
        self.assertEqual({r['n'] for r in self.data['scores'] if r['season']==2026},{751})

    def test_provider_grid_is_complete_about_missingness(self):
        products={'draftkings','kalshi','polymarket_global','polymarket_us'}
        observed={('draftkings','winner'):600,('draftkings','margin'):675,('draftkings','total'):675,
            ('kalshi','winner'):708,('kalshi','margin'):594,('kalshi','total'):594,
            ('polymarket_global','winner'):702,('polymarket_global','margin'):601,('polymarket_global','total'):603,
            ('polymarket_us','winner'):680,('polymarket_us','margin'):0,('polymarket_us','total'):0}
        for g in self.current:
            self.assertEqual(set(g['providers']),products)
            for cells in g['providers'].values():self.assertEqual(set(cells),{'winner','margin','total'})
        for (provider,target),count in observed.items():
            cells=[g['providers'][provider][target] for g in self.current]
            self.assertEqual(sum(c['observed_reference'] for c in cells),count)
            self.assertFalse(any(c['status']=='qualified' for c in cells))
        shown=[(g,c) for g in self.current for cells in g['providers'].values() for c in cells.values() if c['value'] is not None]
        self.assertEqual(len(shown),194)
        for g,c in shown:
            self.assertTrue(c['display_eligible']);self.assertTrue(c['identity_matched_reference'])
            self.assertEqual(c['status'],'archived_unqualified')
            cutoff=datetime.fromisoformat(g['kickoff'].replace('Z','+00:00'))-timedelta(minutes=120)
            self.assertLessEqual(datetime.fromisoformat(c['observation_time'].replace('Z','+00:00')),cutoff)
            self.assertLessEqual(datetime.fromisoformat(c['quote_time'].replace('Z','+00:00')),cutoff)
        self.assertEqual(self.data['market']['qualified_cells'],0)
        p=self.data['market']['bounded_source_progress']
        self.assertEqual((p['owned_raw_events_read'],p['pre_t120_candidate_games'],p['pre_t120_candidate_rows']),(63,53,159))
        self.assertEqual((p['fully_qualified_added_cells'],p['new_paid_credits'],p['new_provider_calls']),(0,0,0))

    def test_current_logical_return_is_two_parts_and_science_is_partial(self):
        r=self.data['return']
        self.assertEqual((r['parts'],r['logical_zip_bytes'],r['part_limit_bytes']),(2,539995588,536870912))
        self.assertEqual(r['logical_archive_sha256'],'979c6e1642e0cd16d58655db3b27fadc90214fc2f1208dea4a373e1b48b4799d')
        self.assertFalse(r['manual_upload_required']);self.assertFalse(r['parts_independently_extractable'])
        gate=next(g for g in self.data['gates'] if g['gate']=='Complete logical return')
        self.assertIn('2 ordered byte-split pieces',gate['detail'])
        self.assertIn('do not prove sustained full capacity occupancy',self.data['cpu_detail'])
        self.assertIn('No feature ablation, new fit or measured improvement',self.data['feature_progress'])

    def test_current_receipt_and_both_dated_archives_bind_the_actual_files(self):
        for route,clock in [('v078','2026-11-15T20:39:57Z'),('v078-20261115T194012Z','2026-11-15T19:40:12Z'),('v078-20261115T051030Z','2026-11-15T05:10:30Z')]:
            site=ROOT/'docs/fbs'/route
            receipt=json.loads((site/'RENDER_RECEIPT.json').read_text())
            self.assertEqual(receipt['source_as_of'],clock)
            for entry in receipt['files']:
                raw=(site/entry['path']).read_bytes()
                self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(entry['bytes'],entry['sha256']))
        html=(self.site/'index.html').read_text()
        self.assertIn('../v078-20261115T194012Z/',html)
        self.assertIn('../v078-20261115T051030Z/',html)
        forbidden=re.compile(r's3://|arn:aws:|/home/sagemaker-user|/workspace/|AKIA[0-9A-Z]{16}|"(?:model_id|fit_id|state_sha256|coefficients|feature_names|prediction_records)"')
        for p in self.site.rglob('*'):
            if not p.is_file():continue
            body=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
            self.assertIsNone(forbidden.search(body.decode()),p.name)
            self.assertNotIn(b'circa',body.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)
