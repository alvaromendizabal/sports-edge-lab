"""Public evidence and projection regressions; all constructed inputs are invented."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs/fbs/v090'
spec = importlib.util.spec_from_file_location('fbs090_projection', ROOT / 'examples/fbs_contracts/v090/public_projection.py')
projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projection)


def fixture():
    cards, populations, games = [], [], []
    for year in projection.YEARS:
        for target in projection.METRICS:
            populations.append({'season': year, 'target': target, 'expected_n': 2, 'cohort_sha256': str(year)*16})
        for i in range(2):
            games.append({'season': year, 'game_id': f'fixture-{year}-{i}', 'home_team': f'Fixture Home {i}', 'away_team': f'Fixture Away {i}', 'completed': True, 'kickoff_utc': f'{year}-09-01T18:00:00Z', 'actuals': {'margin': 10, 'total': 40}})
    for target in projection.METRICS:
        for calibration in ('raw', 'calibrated'):
            mid = f'v089/linear/{target}/combined/all_sources/{calibration}'
            for year in projection.YEARS:
                if target == 'winner':
                    metrics = {'n': 2, 'log_loss': .5 if calibration == 'raw' else .6, 'brier': .2 if calibration == 'raw' else .21, 'accuracy': .5 if calibration == 'raw' else 1.0, 'correct_count': 1 if calibration == 'raw' else 2}
                else:
                    metrics = {'n': 2, 'mae': 4 if calibration == 'raw' else 5, 'rmse': 5 if calibration == 'raw' else 6, 'crps': None if calibration == 'raw' else 3, 'crps_n': 0 if calibration == 'raw' else 2}
                cards.append({'model_id': mid, 'target': target, 'evidence_class': 'V13_FROZEN_RECONSTRUCTION', 'horizon_minutes': 120, 'season': year, 'family': 'linear', 'expected_n': 2, 'scored_n': 2, 'missing_n': 0, 'cohort_sha256': str(year)*16, 'complete_coverage': True, 'metrics': metrics, 'promotion': False, 'production_deployed': False, 'test_untouched': False})
    ranks, leaders = [], []
    for target, metrics in projection.METRICS.items():
        for metric in metrics:
            for profile in projection.PROFILES:
                rows = [c for c in cards if c['season'] == 2024 and c['target'] == target]
                rows.sort(key=lambda c: (c['metrics'][metric] is None, (c['metrics'][metric] or 0)*(-1 if metric == 'accuracy' else 1)))
                ranked = 0
                for row in rows:
                    value = row['metrics'][metric]
                    if value is not None:
                        ranked += 1
                    identity = {k: row[k] for k in ('model_id','target','evidence_class','horizon_minutes')}
                    ranks.append({**identity, 'metric': metric, 'profile': profile, 'rank': ranked if value is not None else None, 'selection_score': value, 'eligible': value is not None})
                    if value is not None and ranked == 1:
                        leaders.append({**identity, 'metric': metric, 'profile': profile, 'value': value})
    selection = {'selection_seasons':[2024,2025], 'primary_profile':'50/50', 'test_outcomes_used':False, 'season_training_weights_used':False, 'refits_for_sensitivity':0, 'base_predictions_changed_for_sensitivity':False, 'test_untouched':False, 'prior_test_exposure_disclosed':True, 'ranks':ranks, 'leaders':leaders}
    stage = {'inherited_policy_count':0, 'new_policy_count':6, 'inherited_no_market_control':{'policy_count':0}, 'completed_jobs':0, 'registered_jobs':0, 'new_model_fits':0, 'new_calibrator_fits':0, 'failed_fits':0, 'max_workers_hard_ceiling':2}
    for name in ('scorecards_artifact','selection_artifact','manifest_artifact','binding_report'):
        stage[name] = {'sha256':'a'*64,'bytes':0}
    pointer = {'owner':'FBS','integrity_verified':True,'durable_available':True,'fixture_mode':False,'child_os_exit_code':2,'logical_zip_sha256':'b'*64,'accountability':{'new_model_fits':0,'new_calibrator_fits':0,'failed_fits':0,'new_scored_prediction_rows':0,'new_forecast_rows_including_ungraded':0,'prior_completed_market_jobs_preserved':0,'prior_completed_core_jobs_preserved':0,'owner_executions_failed':0,'cost_breakdown':{'registered_model_work_elapsed_seconds':10,'child_return_finalization_elapsed_seconds':20,'end_to_end_elapsed_seconds':30,'estimated_end_to_end_full_host_compute_usd':.02}}}
    manifest = {'sport':'FBS','as_of':'2026-11-17T12:00:00Z','populations':populations,'games':games,'postseason_included':True,'schedule_completeness_certified':False}
    binding = {'books':['draftkings'],'counts':{'qualified_t120_cells':6,'t120_grid_cells':18},'coverage':[]}
    cpu = [{'scientific_callback_cpu_seconds':1,'maximum_observed_concurrent_fit_workers':2,'occupancy_acceptance':{'full_capacity_pass':False}}]*2
    prepared = {'registered_scientific_jobs':6,'registered_fixed_blend_recipes':0,'summary':'Invented software fixture; no owner science executed.'}
    return [cards,selection,manifest,binding,stage,pointer,copy.deepcopy(selection),copy.deepcopy(cards),cpu,prepared]


class ProjectionTests(unittest.TestCase):
    def test_invented_projection_preserves_all_populations_and_null_crps(self):
        report,games,aliases = projection.project(*fixture())
        self.assertEqual((len(report['models']),len(report['selection']['leaders']),len(games['games'])),(6,45,6))
        self.assertEqual(len(aliases),6)
        missing = [r for r in report['selection']['ranks'] if r['rank'] is None]
        self.assertEqual(len(missing),10)
        self.assertTrue(all(r['selection_score'] is None and not r['eligible'] for r in missing))
    def test_test_outcome_poison_never_changes_saved_selection(self):
        args=fixture();before=projection.project(*args)[0]['selection']
        for row in args[0]:
            if row['season']==2026:
                for metric in projection.METRICS[row['target']]:
                    if row['metrics'][metric] is not None:row['metrics'][metric]=123.456789012
        self.assertEqual(before,projection.project(*args)[0]['selection'])
    def test_football_feature_ablations_are_separate_from_bookmaker_ablations(self):
        args=fixture()
        rename={'v089/linear/winner/combined/all_sources/raw':'v13/fixture/without_fixture_feature/raw',
                'v089/linear/winner/combined/all_sources/calibrated':'v13/fixture/without_fixture_feature/calibrated',
                'v089/linear/margin/combined/all_sources/raw':'v088/linear/margin/combined/without_fixturebook/raw'}
        def replace_ids(value):
            if isinstance(value,dict):
                if value.get('model_id') in rename:value['model_id']=rename[value['model_id']]
                for child in value.values():replace_ids(child)
            elif isinstance(value,list):
                for child in value:replace_ids(child)
        replace_ids(args)
        report,_,aliases=projection.project(*args)
        by_alias={row['alias']:row for row in report['models']}
        for identity,alias in aliases.items():
            if identity[0]==rename['v089/linear/winner/combined/all_sources/raw']:
                self.assertEqual(by_alias[alias]['study_group'],'Retained football feature ablation')
            elif identity[0]==rename['v089/linear/margin/combined/all_sources/raw']:
                self.assertEqual(by_alias[alias]['study_group'],'Single-source ablation')
    def test_shrunken_population_is_rejected(self):
        args=fixture();args[0][0]['expected_n']=1
        with self.assertRaisesRegex(ValueError,'population'):projection.project(*args)
    def test_duplicate_annual_card_is_rejected(self):
        args=fixture();args[0].append(copy.deepcopy(args[0][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'):projection.project(*args)
    def test_selection_on_test_is_rejected(self):
        args=fixture();args[1]['test_outcomes_used']=True
        with self.assertRaisesRegex(ValueError,'safeguards'):projection.project(*args)
    def test_null_crps_cannot_be_promoted_to_zero_score(self):
        args=fixture();r=next(r for r in args[1]['ranks'] if not r['eligible']);r.update(eligible=True,rank=1,selection_score=0)
        with self.assertRaisesRegex(ValueError,'Unavailable metrics'):projection.project(*args)
    def test_validation_rank_score_cannot_use_test_value(self):
        args=fixture();args[1]['ranks'][0]['selection_score']=.123
        with self.assertRaisesRegex(ValueError,'validation weighting'):projection.project(*args)
    def test_private_source_fields_are_not_copied(self):
        args=fixture();args[0][0]['private_transform']={'path':'/home/private-owner/model.bin'};args[3]['credentials']='private fixture sentinel'
        result=json.dumps(projection.project(*args)[:2])
        for text in ('private_transform','private fixture sentinel','/home/','model_id','game_id'):
            self.assertNotIn(text,result)
    def test_unsafe_team_text_is_rejected(self):
        args=fixture();args[2]['games'][0]['home_team']='s3://private-fixture-bucket/object'
        with self.assertRaisesRegex(ValueError,'Unsafe public text'):projection.project(*args)
    def test_physical_pin_rejects_modified_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.json';p.write_bytes(b'{"x":1}')
            pin={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            self.assertEqual(projection.read_pinned(p,pin),{'x':1});p.write_bytes(b'{"x":2}')
            with self.assertRaisesRegex(ValueError,'artifact pin'):projection.read_pinned(p,pin)
    def test_nonfinite_metrics_rejected(self):
        with self.assertRaises(ValueError):projection.scalar(float('nan'))
        with self.assertRaises(ValueError):projection.scalar(float('inf'))


class PublishedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((SITE/'data/review.json').read_text());cls.games=json.loads((SITE/'data/games.json').read_text())
    def test_actual_and_prepared_counts_are_separate(self):
        d=self.report
        self.assertEqual((d['execution']['completed_jobs'],d['execution']['new_model_fits'],d['execution']['new_calibrator_fits'],d['execution']['failed_fits']),(90,90,90,0))
        self.assertEqual(d['prepared']['status'],'PREPARED_NOT_EXECUTED')
        self.assertEqual(d['prepared']['registered_scientific_jobs'],936)
        self.assertEqual(d['publication']['owner_research_executed_by_publication'],0)
        self.assertEqual((len(d['models']),len(d['selection']['leaders']),len(d['selection']['ranks'])),(397,45,5955))
    def test_all_candidate_cards_and_crps_gaps_remain_visible(self):
        for model in self.report['models']:
            for year,n in [('2024',919),('2025',934),('2026',752)]:
                self.assertEqual((model['annual'][year]['expected_n'],model['annual'][year]['scored_n']),(n,n))
        self.assertEqual(sum(r['rank'] is None for r in self.report['selection']['ranks']),680)
    def test_inventory_is_not_shrunk_to_timed_or_completed_games(self):
        games=self.games['games'];self.assertEqual(len(games),2742)
        self.assertEqual({y:sum(g['season']==y and g['completed'] for g in games) for y in (2024,2025,2026)},{2024:919,2025:934,2026:752})
        self.assertEqual(sum(g['season']==2026 and not g['completed'] for g in games),136)
        self.assertEqual(sum(g['season']==2026 and not g['kickoff_utc'] for g in games),10)
        self.assertFalse(self.games['schedule_completeness_certified'])
    def test_public_aliases_and_boundary(self):
        raw=json.dumps([self.report,self.games])
        for forbidden in ['model_id','game_id','owner_relative_path','/home/','s3://','arn:aws:','.pyz','v089/lightgbm/','v088/extra_trees/']:
            self.assertNotIn(forbidden,raw)
        self.assertEqual(len({m['alias'] for m in self.report['models']}),397)
        self.assertEqual(self.report['publication']['status'],'SOURCE_REVIEW_NOT_DEPLOYED')
    def test_named_sources_and_negative_findings_are_preserved(self):
        self.assertIn('DraftKings',self.report['sources']['books'])
        self.assertEqual(len(self.report['sources']['books']),17)
        self.assertEqual(len(self.report['sources']['providers']),4)
        findings=' '.join(self.report['findings'])
        self.assertIn('worse 2026 test results on 8 of 9',findings)
        self.assertIn('calibration worsens',findings)
        self.assertFalse(self.report['selection']['test_untouched'])
        from collections import Counter
        self.assertEqual(Counter(m['study_group'] for m in self.report['models']),{
            'Single-source ablation':204,'All-source control':84,
            'Retained football feature ablation':48,'Retained no-market control':61})

    def test_entire_pre_v090_readme_suffix_is_byte_preserved(self):
        content=(ROOT/'docs/fbs/README.md').read_bytes()
        if content.startswith(b'<!-- FBS_V101_PREPARATION_START -->\n'):
            self.assertEqual(content.count(b'<!-- FBS_V101_PREPARATION_END -->\n\n'),1)
            content=content.split(b'<!-- FBS_V101_PREPARATION_END -->\n\n',1)[1]
        v099_end=b'<!-- FBS_V099_ACTUAL_RETURN_END -->\n\n'
        if content.startswith(b'<!-- FBS_V099_ACTUAL_RETURN_START -->\n'):
            content=content.split(v099_end,1)[1]
        newest_start=b'<!-- FBS_V098_ACTUAL_RETURN_START -->\n'
        newest_end=b'<!-- FBS_V098_ACTUAL_RETURN_END -->\n\n'
        if content.startswith(newest_start):
            self.assertEqual(content.count(newest_end),1)
            content=content.split(newest_end,1)[1]
        current_start=b'<!-- FBS_V097_ACTUAL_RETURN_START -->\n'
        current_end=b'<!-- FBS_V097_ACTUAL_RETURN_END -->\n\n'
        if content.startswith(current_start):
            self.assertEqual(content.count(current_end),1)
            content=content.split(current_end,1)[1]
        latest_start=b'<!-- FBS_V093_READINESS_START -->\n'
        latest_end=b'<!-- FBS_V093_READINESS_END -->\n\n'
        if content.startswith(latest_start):
            self.assertEqual(content.count(latest_end),1)
            content=content.split(latest_end,1)[1]
        start=b'<!-- FBS_V090_VERIFIED_V089_REVIEW_START -->\n'
        end=b'<!-- FBS_V090_VERIFIED_V089_REVIEW_END -->\n\n'
        self.assertTrue(content.startswith(start))
        self.assertEqual(content.count(start),1)
        self.assertEqual(content.count(end),1)
        suffix=content.split(end,1)[1]
        git_blob=hashlib.sha1(b'blob '+str(len(suffix)).encode()+b'\0'+suffix).hexdigest()
        self.assertEqual(git_blob,'ad11e2d190042fc18f37ae8f97036a6e4ea325bd')


if __name__=='__main__':unittest.main(verbosity=2)
