"""Regression tests for the published B061 evidence, using only the stdlib.

Run from the repository root:
    python -m unittest discover -s examples/ncaa_review -p 'test_b061_evidence.py' -v

The default input is the committed sibling ``data`` directory. During release
preparation only, B061_PUBLIC_DATA_DIR may point at the staged public exports.
No cloud credentials, private model artifacts, training or network are used.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import re
import unittest


DATA = Path(os.environ.get('B061_PUBLIC_DATA_DIR', str(Path(__file__).parent/'data')))
FILES = (
    'ncaa_observed_games_b060.json',
    'ncaa_observed_games_b060.csv',
    'ncaa_original_replay_completed_b061.json',
    'ncaa_preserved_selected_issues_scored_b061.json',
    'ncaa_original_replay_vs_prior_issued_b061.json',
    'ncaa_metric_role_status_b061.json',
)
REPLAY = 'EXPOSED_RETROSPECTIVE_RECONSTRUCTION_NOT_ORIGINAL_ISSUE'
PREVIEW = 'PRIVATE_UNISSUED_FUTURE_PREVIEW_NOT_PUBLISHED'
NO_REPLAY = 'NO_SAVED_ORIGINAL_INFERENCE_FOR_EXACT_SOURCE_GAME'
TIME_CHANGED = 'RECORDED_EVENT_TIME_CHANGED_NO_AUTHENTICATED_TIME_ALIAS'
MATCHED = 'EXACT_NATIVE_IDS_AND_TIP_OBSERVED_SOURCE_OUTCOME'
TARGET_FIELDS = {'win':'home_win_probability', 'margin':'margin', 'total':'total'}
PRESERVED_FIELDS = (
    'league','event_id','home_team_id','away_team_id','event_time','cutoff_time',
    'issued_at','feature_available_at','training_cutoff','training_origin',
    'historical_input_observed_at','target','metric_role_alias','prediction',
    'units','forecast_status','archive_selection_asof_utc','selection_basis',
    'current_champion_status',
)
# Pinned from the previously published 96-row B059 selected-issue CSV before
# adding any outcomes. The projection deliberately excludes later result fields.
PRESERVED_PROJECTION_SHA256 = 'abc117a9ebcb288c72d4bd870dfb4872fea0aaf81c6163426d2584966cfeff73'


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),
                       ensure_ascii=False,allow_nan=False)+'\n').encode()


def stamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('A timezone-aware timestamp is required')
    return parsed.astimezone(timezone.utc)


def row_key(row, target=True):
    key=(row['league'],row['event_id'],stamp(row['event_time']))
    return key+(row['target'],) if target else key


def metrics(rows, target):
    values=[(float(row['actual']),float(row['prediction'])) for row in rows]
    n=len(values)
    if target=='win':
        accuracy=sum(.5 if p==.5 else float((p>.5)==bool(y)) for y,p in values)/n
        ll=sum(-math.log(max(1e-15,min(1-1e-15,p if y else 1-p))) for y,p in values)/n
        return {'accuracy':accuracy,'log_loss':ll,
                'brier':sum((p-y)**2 for y,p in values)/n}
    residual=[p-y for y,p in values]
    return {'mae':sum(abs(v) for v in residual)/n,
            'rmse':math.sqrt(sum(v*v for v in residual)/n),
            'bias':sum(residual)/n}


def rounding_bound(rows, target, metric):
    """Bound comparison to unrounded metrics using the public rounding policy."""
    if target!='win':
        return .000500001  # Every published point estimate is rounded to .001.
    if metric=='accuracy':
        return 1e-12  # This frozen cohort contains no rounded .5 predictions.
    if metric=='brier':
        return .000001000001
    # Mean-value bound for -log(p_true), with probability rounding to .000001.
    true_probs=[float(r['prediction']) if float(r['actual']) else
                1-float(r['prediction']) for r in rows]
    return sum(.0000005/max(p-.0000005,1e-15) for p in true_probs)/len(rows)+1e-12


class PublicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing=[name for name in FILES if not (DATA/name).is_file()]
        if missing:
            raise AssertionError('Missing committed public evidence: '+', '.join(missing))
        cls.docs={name:json.loads((DATA/name).read_text(encoding='utf-8'))
                  for name in FILES if name.endswith('.json')}
        cls.census=cls.docs['ncaa_observed_games_b060.json']
        cls.replay=cls.docs['ncaa_original_replay_completed_b061.json']
        cls.issues=cls.docs['ncaa_preserved_selected_issues_scored_b061.json']
        cls.paired=cls.docs['ncaa_original_replay_vs_prior_issued_b061.json']
        cls.roles=cls.docs['ncaa_metric_role_status_b061.json']

    def test_all_exports_are_sanitized(self):
        forbidden_keys={'recipe','recipe_id','private_exact_recipe','model_sha256',
          'source_fingerprint','original_feature_values','feature_columns',
          'parameter_input_proofs','coefficients','coefficient_vector',
          'immutable_ledger_reference','bucket','access_key','secret_key','session_token'}
        forbidden_text=re.compile(
          r's3://|arn:aws:|/workspace/|/home/[^/]+/|'
          r'sagemaker-[A-Za-z0-9-]+-\d{12}|'
          r'B\d{3}_[A-Za-z0-9_]+_(?:linear|hist_gradient|current_refit)', re.I)
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden_keys.intersection(value))
                for child in value.values():inspect(child)
            elif isinstance(value,list):
                for child in value:inspect(child)
            elif isinstance(value,str):
                self.assertIsNone(forbidden_text.search(value),value[:120])
        for name,document in self.docs.items():
            with self.subTest(file=name):inspect(document)
        self.assertIsNone(forbidden_text.search((DATA/FILES[1]).read_text(encoding='utf-8')))

    def test_observed_population_has_no_silent_source_omissions(self):
        records=self.census['records']
        self.assertEqual(len(records),3457)
        self.assertEqual(len({(r['league'],r['event_id']) for r in records}),3457)
        self.assertEqual(Counter(r['source_binding_status'] for r in records),{
          'OBSERVED_SOURCE_GAME_WITHOUT_BOUND_MODEL_ROW':2498,
          'UNMATCHED_OFFICIAL_CANDIDATE_RECORD':934,
          'UNRESOLVED_SOURCE_CANDIDATE_RECORD':25})
        self.assertEqual(Counter(r['original_replay_prediction_status'] for r in records),
                         {REPLAY:814,PREVIEW:1139,NO_REPLAY:1504})
        self.assertEqual(sum(r['completed'] is True for r in records),1547)
        normalized=[r for r in records if r['source_binding_status']==
                    'OBSERVED_SOURCE_GAME_WITHOUT_BOUND_MODEL_ROW']
        self.assertEqual(sum(r['completed'] is True for r in normalized),1165)
        self.assertFalse(self.census['complete_official_universe'])
        self.assertEqual(self.census['counts']['normalized_espn_games'],2498)
        self.assertEqual(self.census['counts']['observed_records'],3457)
        self.assertEqual(self.census['selected_retrospective_target_rows_published'],2442)
        for key in ('new_forecasts','new_model_fits','promotions'):
            self.assertEqual(self.census[key],0)

    def test_csv_and_json_have_identical_census_values(self):
        with (DATA/'ncaa_observed_games_b060.csv').open(newline='',encoding='utf-8') as stream:
            reader=csv.DictReader(stream);csv_rows=list(reader)
            self.assertEqual(set(reader.fieldnames),set(self.census['records'][0]))
        self.assertEqual(len(csv_rows),3457)
        for public,wire in zip(self.census['records'],csv_rows):
            self.assertEqual(wire,{key:'' if value is None else str(value)
                                   for key,value in public.items()})

    def test_future_unissued_replay_values_never_reach_public_rows(self):
        cutoff=stamp(self.census['reconciliation_asof'])
        preview_count=0
        for row in self.census['records']:
            fields=['selected_original_'+suffix for suffix in TARGET_FIELDS.values()]
            future=bool(row['event_time']) and stamp(row['event_time'])>cutoff
            preview=row['original_replay_prediction_status']==PREVIEW
            if future or preview:
                self.assertTrue(all(row[field] is None for field in fields))
            if preview:
                preview_count+=1
                self.assertTrue(future)
        self.assertEqual(preview_count,1139)
        for row in self.replay['records']:
            self.assertLessEqual(stamp(row['event_time']),cutoff)
            self.assertIsNone(row['issued_at'])
            self.assertEqual(row['new_issue_credit'],0)

    def test_completed_replay_preserves_target_clock_and_source_limits(self):
        records=self.replay['records']
        self.assertEqual(len(records),2442)
        self.assertEqual(len({row_key(r,False) for r in records}),814)
        self.assertEqual(len({row_key(r) for r in records}),2442)
        self.assertEqual(Counter(r['league'] for r in records),{'ncaam':1245,'ncaaw':1197})
        by_game=defaultdict(set)
        for row in records:
            by_game[row_key(row,False)].add(row['target'])
            self.assertEqual(stamp(row['event_time'])-stamp(row['cutoff_time']),timedelta(hours=1))
            self.assertIsNotNone(row['actual'])
            self.assertEqual(row['evidence_mode'],'retrospective_reconstructed')
            self.assertEqual(row['forecast_status'],REPLAY)
            self.assertEqual(row['model_role_alias'],'preserved_original_frozen_reference')
            self.assertFalse(row['independent_official_phase_verified'])
            self.assertEqual(row['historical_source_clock_basis'],'DECLARED_24H_HISTORICAL_RELEASE_ASSUMPTION')
        self.assertTrue(all(targets=={'win','margin','total'} for targets in by_game.values()))
        self.assertFalse(self.replay['historical_vintages_and_independent_official_phase_verified'])
        self.assertEqual(self.replay['promotions'],0)
        expected={'ncaam':(415,337,.39480662720368886,.12688327066747543),
                  'ncaaw':(399,340,.318015307605635,.10017893982274186)}
        for league,(n,correct,ll,brier) in expected.items():
            subset=[r for r in records if r['league']==league and r['target']=='win']
            scored=metrics(subset,'win')
            self.assertEqual(len(subset),n)
            self.assertEqual(sum((float(r['prediction'])>.5)==bool(r['actual']) for r in subset),correct)
            self.assertAlmostEqual(scored['accuracy'],correct/n)
            self.assertLessEqual(abs(scored['log_loss']-ll),rounding_bound(subset,'win','log_loss'))
            self.assertLessEqual(abs(scored['brier']-brier),rounding_bound(subset,'win','brier'))

    def test_completed_replay_matches_published_game_cells(self):
        # Unresolved source candidates remain in the census even when no tip
        # time is known; they cannot bind to a completed replay record.
        census={row_key(r,False):r for r in self.census['records'] if r['event_time']}
        for row in self.replay['records']:
            game=census[row_key(row,False)]
            self.assertEqual(game['selected_original_'+TARGET_FIELDS[row['target']]],row['prediction'])
            self.assertEqual(game['original_replay_prediction_status'],REPLAY)
            home,away=game['actual_home_points'],game['actual_away_points']
            actual={'win':float(home>away),'margin':home-away,'total':home+away}[row['target']]
            self.assertEqual(actual,row['actual'])

    def test_original_issued_values_and_clocks_match_the_prior_public_export(self):
        records=self.issues['records']
        self.assertEqual(len(records),96)
        projection=[{key:float(row[key]) if key=='prediction' else row[key]
                     for key in PRESERVED_FIELDS} for row in records]
        self.assertEqual(hashlib.sha256(canonical(projection)).hexdigest(),PRESERVED_PROJECTION_SHA256)
        self.assertEqual(len({row_key(r,False) for r in records}),32)
        for row in records:
            self.assertLessEqual(stamp(row['issued_at']),stamp(row['cutoff_time']))
            self.assertLessEqual(stamp(row['training_cutoff']),stamp(row['cutoff_time']))
            self.assertLessEqual(stamp(row['feature_available_at']),stamp(row['cutoff_time']))
            self.assertEqual(row['new_issue_credit'],0)
        self.assertEqual(self.issues['new_issues'],0)
        self.assertEqual(self.issues['promotions'],0)
        self.assertFalse(self.issues['independent_official_final_verified'])

    def test_original_issue_outcomes_retain_two_unresolved_tip_time_cases(self):
        matched=[r for r in self.issues['records'] if r['actual'] is not None]
        missing=[r for r in self.issues['records'] if r['actual'] is None]
        self.assertEqual(self.issues['counts'],{'input_prior_issue_rows':96,
          'matched_rows':90,'matched_games':30,'unmatched_rows':6})
        self.assertEqual(len(matched),90)
        self.assertEqual(len(missing),6)
        self.assertEqual(Counter(r['event_id'] for r in missing),{
          'ncaam:espn:event:401920952':3,'ncaam:espn:event:401929002':3})
        for row in matched:
            self.assertEqual(row['outcome_match_status'],MATCHED)
            self.assertLessEqual(stamp(row['outcome_available_at']),stamp(self.issues['asof']))
            self.assertEqual(row['official_final_link_status'],'INDEPENDENT_OFFICIAL_FINAL_NOT_VERIFIED')
        census={(r['league'],r['event_id']):r for r in self.census['records']}
        expected={
          'ncaam:espn:event:401920952':('2026-11-07T01:30:00+00:00','2026-11-07T02:15:00+00:00'),
          'ncaam:espn:event:401929002':('2026-11-09T04:00:00+00:00','2026-11-09T03:00:00+00:00')}
        for row in missing:
            self.assertEqual(row['outcome_match_status'],TIME_CHANGED)
            self.assertIsNone(row['outcome_available_at'])
            old,new=expected[row['event_id']]
            game=census[row['league'],row['event_id']]
            self.assertEqual(stamp(row['event_time']),stamp(old))
            self.assertEqual(stamp(game['event_time']),stamp(new))
            self.assertEqual(game['forecast_status'],'PRESERVED_ISSUE_EVENT_FOUND_TIP_CLOCK_MISMATCH_UNBOUND')
            self.assertTrue(all(game['selected_issued_'+suffix] is None for suffix in TARGET_FIELDS.values()))
        for league,n,correct in [('ncaam',16,16),('ncaaw',14,10)]:
            subset=[r for r in matched if r['league']==league and r['target']=='win']
            self.assertEqual(len(subset),n)
            self.assertEqual(sum((float(r['prediction'])>.5)==bool(r['actual']) for r in subset),correct)

    def test_paired_scores_match_the_same_games_without_merging_evidence_modes(self):
        replay={row_key(r):r for r in self.replay['records']}
        issued=defaultdict(list);original=defaultdict(list)
        for row in self.issues['records']:
            if row['actual'] is None:continue
            other=replay[row_key(row)]
            self.assertEqual(stamp(other['cutoff_time']),stamp(row['cutoff_time']))
            self.assertEqual(other['actual'],row['actual'])
            group=row['league'],row['target']
            issued[group].append(row);original[group].append(other)
        self.assertEqual(len(self.paired['comparisons']),6)
        for report in self.paired['comparisons']:
            group=report['league'],report['target']
            a,b=original[group],issued[group]
            self.assertEqual(report['games'],16 if report['league']=='ncaam' else 14)
            self.assertEqual(report['candidate_evidence_mode'],'retrospective_reconstructed')
            self.assertEqual(report['reference_evidence_mode'],'original_issued')
            for field in ('same_issued_evidence_policy','independent_confirmation',
                          'promotion_authority','selection_authority'):
                self.assertFalse(report[field])
            self.assertEqual(report['uncertainty']['replicates'],0)
            ma,mb=metrics(a,group[1]),metrics(b,group[1])
            for metric,values in report['metrics'].items():
                self.assertLessEqual(abs(values['candidate']-ma[metric]),rounding_bound(a,group[1],metric))
                self.assertLessEqual(abs(values['reference']-mb[metric]),rounding_bound(b,group[1],metric))
                self.assertAlmostEqual(values['candidate_minus_reference'],values['candidate']-values['reference'])
                self.assertIsNone(values['descriptive_95_percent_interval'])
        self.assertEqual(self.paired['new_fits'],0)
        self.assertEqual(self.paired['promotions'],0)

    def test_historical_metric_roles_preserve_scope_without_new_promotions(self):
        self.assertEqual(len(self.roles['selected_roles']),6)
        self.assertEqual({(r['league'],r['target']) for r in self.roles['selected_roles']},
                         {(league,target) for league in ('ncaam','ncaaw') for target in TARGET_FIELDS})
        self.assertTrue(self.roles['original_frozen_reference_preserved'])
        self.assertTrue(self.roles['historical_research_exposed'])
        self.assertEqual(self.roles['new_promotions'],0)
        self.assertEqual(self.roles['current_outcomes_used_for_selection'],0)
        self.assertEqual(set(self.roles['metric_roles_not_independently_selected_by_this_ledger']),{
          'winner_accuracy','probability_brier','expected_margin_rmse','total_points_rmse',
          'comparable_spread_cover_probability','joint_score_distribution_crps','interval_quality'})
        for row in self.roles['selected_roles']:
            self.assertEqual(row['historical_N'],11507 if row['league']=='ncaam' else 10901)
            self.assertEqual(row['selection_metric'],'LogLoss' if row['target']=='win' else 'MAE')
            self.assertEqual(row['selection_basis'],'EXPOSED_2024_25_AND_2025_26_ONLY_NOT_CONFIRMATORY')
            self.assertFalse(row['promotion_authority'])
            self.assertFalse(row['current_season_outcomes_used_for_selection'])

    def test_provider_gaps_are_explicit_and_not_scored_as_zero(self):
        for row in self.census['records']:
            self.assertEqual(row['provider_comparison_status'],
              'EXACT_CURRENT_QUOTE_LEDGER_NOT_RECOVERED_FOR_MATCHED_SCORING')
            for provider in ('draftkings','kalshi','polymarket'):
                for target in TARGET_FIELDS:
                    self.assertIn(provider+'_'+target+'_status',row)
        self.assertTrue(all(r['reference_model_role']=='preserved_selected_original_issue'
                            for r in self.paired['comparisons']))


if __name__=='__main__':
    unittest.main()
