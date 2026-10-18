"""Offline zero-fit settlement/coverage/immutability regressions."""
import copy
import hashlib
import json
import pathlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import pandas as pd
from common import Checkpoints
from settlement import (settle_records, score_settlements, append_settlements,
                        validate_forecast_chains, build_settlement, fixture_inputs,
                        _json, _hash, _forecast_key, _load_pinned_ledger)


def rechain(rows):
    previous = None
    for r in rows:
        r.pop('record_hash', None)
        r['record_key'] = _forecast_key(r); r['previous_hash'] = previous
        r['record_hash'] = _hash(r); previous = r['record_hash']
    return rows


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.games, self.obs, self.as_of = fixture_inputs()

    def run_case(self, **kwargs):
        return settle_records(kwargs.get('records', self.rows), kwargs.get('games', self.games),
                              kwargs.get('observed_at', self.obs), kwargs.get('as_of', self.as_of),
                              kwargs.get('expected_head', self.rows[-1]['record_hash']))

    def test_three_settled_three_pending_zero_fits(self):
        result = self.run_case(); a = result['audit']
        self.assertEqual((a['selected_forecasts'], a['matured_records'], a['pending_records']), (6,3,3))
        self.assertEqual((a['new_real_fits'], a['new_live_forecasts'], a['provider_calls']), (0,0,0))
        self.assertFalse(a['prospective_quality_established'])

    def test_scores_match_manual_losses_and_no_small_sample_ci(self):
        cards = {x['task']:x for x in self.run_case()['audit']['scorecards']}
        self.assertAlmostEqual(cards['win']['metrics']['Brier'], .16)
        self.assertAlmostEqual(cards['win']['metrics']['log_loss'], -__import__('math').log(.6))
        self.assertEqual(cards['margin']['metrics']['MAE'], 1)
        self.assertEqual(cards['total']['metrics']['RMSE'], 1)
        self.assertIsNone(cards['win']['metrics']['AUC'])
        self.assertTrue(all(not x['uncertainty']['available'] for x in cards.values()))
        self.assertEqual(sum(b['count'] for b in cards['win']['metrics']['calibration']), 1)

    def test_no_mature_labels_produce_no_fake_zero_scores(self):
        self.games['completed'] = False
        a = self.run_case()['audit']
        self.assertEqual(a['pending_records'],6); self.assertEqual(a['scorecards'],[])
        self.assertFalse(a['metrics_available'])

    def test_original_actual_leads_and_minimum_cutoff_separate(self):
        result = self.run_case()
        self.assertEqual({r['actual_lead_hours'] for r in result['settlements']}, {48})
        self.assertEqual({r['actual_lead_hours'] for r in result['pending']}, {49})
        self.assertEqual({r['minimum_issue_lead_hours'] for r in result['settlements']}, {24})

    def test_empty_ledger_is_explicit_empty_result(self):
        r = settle_records([], [], None, self.as_of)
        self.assertEqual(r['audit']['selected_forecasts'],0)
        self.assertEqual(r['audit']['scorecards'],[])

    def test_tampered_chain_rejected(self):
        self.rows[0]['prediction'] = .7
        with self.assertRaisesRegex(ValueError,'hash chain'):self.run_case()

    def test_wrong_pinned_head_rejected(self):
        with self.assertRaisesRegex(ValueError,'head mismatch'):self.run_case(expected_head='f'*64)

    def test_bad_previous_hash_rejected(self):
        self.rows[1]['previous_hash'] = 'f'*64
        with self.assertRaisesRegex(ValueError,'hash chain'):self.run_case()

    def test_wrong_record_key_rejected(self):
        self.rows[-1]['record_key'] = 'f'*64; self.rows[-1].pop('record_hash')
        self.rows[-1]['record_hash'] = _hash(self.rows[-1])
        with self.assertRaisesRegex(ValueError,'identity mismatch'):self.run_case()

    def test_malformed_exact_id_rejected(self):
        for value in ['', 'nan', 'one two', '../secret', None, True]:
            rows=copy.deepcopy(self.rows); rows[0]['game_id']=value; rechain(rows)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError,'ID'):
                self.run_case(records=rows,expected_head=rows[-1]['record_hash'])

    def test_production_numeric_fbs_and_nfl_shapes_enforced(self):
        self.rows[0]['fixture']=False; rechain(self.rows)
        with self.assertRaisesRegex(ValueError,'NFL game'):self.run_case()

    def test_same_home_away_rejected(self):
        self.rows[0]['away_id']=self.rows[0]['home_id'];rechain(self.rows)
        with self.assertRaisesRegex(ValueError,'cannot match'):self.run_case()

    def test_late_issued_forecast_rejected(self):
        r=self.rows[0];r['issued_at']=(pd.Timestamp(r['kickoff'])-pd.Timedelta(hours=12)).isoformat()
        r['actual_lead_hours']=12;rechain(self.rows)
        with self.assertRaisesRegex(ValueError,'Late issued'):self.run_case()

    def test_actual_lead_cannot_be_relabeled_to_minimum(self):
        self.rows[0]['actual_lead_hours']=24;rechain(self.rows)
        with self.assertRaisesRegex(ValueError,'Actual lead'):self.run_case()

    def test_unknown_or_late_input_observation_rejected(self):
        for val in [None, '2030-01-07T01:00:00Z']:
            rows=copy.deepcopy(self.rows); rows[0]['feature_observed_at']=val;rechain(rows)
            with self.subTest(val=val),self.assertRaises(ValueError):
                self.run_case(records=rows,expected_head=rows[-1]['record_hash'])

    def test_future_issuance_not_backdated_for_scoring(self):
        with self.assertRaisesRegex(ValueError,'issued after'):
            self.run_case(as_of='2030-01-06T00:00:00Z')

    def test_final_observation_before_release_stays_pending(self):
        self.obs['nfl']['observed_at']='2030-01-08T12:00:00Z'
        r=self.run_case();self.assertEqual(len(r['settlements']),0)
        self.assertEqual(r['pending'][0]['reason'],'final_source_observed_before_assumed_release')

    def test_as_of_before_release_stays_pending(self):
        rows=rechain(copy.deepcopy(self.rows[:3]));self.obs['nfl']['observed_at']='2030-01-08T10:00:00Z'
        r=self.run_case(records=rows,expected_head=rows[-1]['record_hash'],as_of='2030-01-08T12:00:00Z')
        self.assertTrue(all(x['reason']=='assumed_label_release_not_reached' for x in r['pending']))

    def test_future_label_observation_stays_pending(self):
        self.obs['nfl']['observed_at']='2030-01-11T00:00:00Z'
        r=self.run_case();self.assertTrue(all(x['reason']=='label_observed_after_as_of' for x in r['pending']))

    def test_unknown_label_observation_stays_pending(self):
        r=self.run_case(observed_at=None)
        self.assertTrue(all(x['reason']=='label_observation_unknown' for x in r['pending']))

    def test_final_source_hash_required_even_with_known_observation(self):
        for digest in [None, '', 'a'*63, 'g'*64]:
            obs=copy.deepcopy(self.obs);obs['nfl']['sha256']=digest
            r=self.run_case(observed_at=obs)
            self.assertEqual(r['audit']['scored_records'],0)
            self.assertEqual(r['pending'][0]['reason'],'final_source_hash_missing_or_invalid')

    def test_same_game_id_wrong_label_season_stays_pending(self):
        self.games.loc[0,'season']=2029
        r=self.run_case();self.assertEqual(r['pending'][0]['reason'],'label_season_mismatch')

    def test_abstentions_are_never_scored_as_predictions(self):
        for r in self.rows:
            r['status']='abstained';r['prediction']=None;r['reasons']=['source_stale']
        rechain(self.rows);r=self.run_case()
        self.assertEqual(r['audit']['abstention_records'],6)
        self.assertEqual(r['audit']['selected_forecasts'],0)
        self.assertEqual(r['audit']['scorecards'],[])

    def test_unknown_publication_stays_null(self):
        self.assertTrue(all(x['source_publication_at'] is None for x in self.run_case()['settlements']))

    def test_impossible_publication_stays_pending(self):
        self.obs['nfl']['source_publication_at']='2030-01-10T01:00:00Z'
        r=self.run_case();self.assertEqual(len(r['settlements']),0)
        self.assertEqual(r['pending'][0]['reason'],'label_publication_after_observation')

    def test_missing_game_and_changed_identity_stay_pending(self):
        r=self.run_case(games=self.games.iloc[0:0]);self.assertEqual(r['audit']['pending_records'],6)
        self.games.loc[0,'away_id']='CCC';r=self.run_case()
        self.assertEqual(r['pending'][0]['reason'],'label_team_identity_mismatch')

    def test_changed_kickoff_stays_pending(self):
        self.games.loc[0,'kickoff']='2030-01-08T01:00:00+00:00'
        r=self.run_case();self.assertEqual(r['pending'][0]['reason'],'label_kickoff_changed')

    def test_cancelled_or_incomplete_status_not_settled(self):
        for status in ['cancelled','postponed','in_progress','suspended']:
            games=self.games.copy();games['status']=status
            r=self.run_case(games=games)
            self.assertEqual(r['audit']['matured_records'],0)

    def test_non_boolean_completed_not_accepted(self):
        games=self.games.astype({'completed':object});games.loc[0,'completed']='true'
        r=self.run_case(games=games);self.assertEqual(r['audit']['matured_records'],0)

    def test_invalid_scores_stay_pending(self):
        for score in [float('nan'),-1,2.5,201,float('inf')]:
            games=self.games.copy();games.loc[0,'home_points']=score
            self.assertEqual(self.run_case(games=games)['audit']['matured_records'],0)

    def test_tie_excludes_win_but_scores_margin_total(self):
        self.games.loc[0,'away_points']=24
        r=self.run_case();a=r['audit']
        self.assertEqual(a['matured_records'],3);self.assertEqual(a['scored_records'],2)
        self.assertEqual({x['task'] for x in a['scorecards']},{'margin','total'})
        self.assertEqual(next(x for x in r['settlements'] if x['task']=='win')['status'],'excluded_tie')

    def test_conflicting_same_observation_labels_rejected(self):
        extra=self.games.iloc[[0]].copy();extra['home_points']=25
        with self.assertRaisesRegex(ValueError,'Conflicting label duplicates'):
            self.run_case(games=pd.concat([self.games,extra]))

    def test_identical_label_duplicates_deduplicated(self):
        r=self.run_case(games=pd.concat([self.games,self.games.iloc[[0]]]))
        self.assertEqual(r['audit']['matured_records'],3)

    def test_latest_unambiguous_explicit_revision_chosen(self):
        games=self.games.copy();games['source_observed_at']='2030-01-09T10:00:00Z'
        extra=games.iloc[[0]].copy();extra['source_observed_at']='2030-01-09T11:00:00Z';extra['home_points']=27
        r=self.run_case(games=pd.concat([games,extra]))
        self.assertEqual(next(x for x in r['settlements'] if x['task']=='margin')['target'],7)

    def test_global_earliest_selection_across_versions(self):
        later=copy.deepcopy(self.rows)
        for r in later:
            r['protocol']='football-shadow-v999';r['issued_at']=(pd.Timestamp(r['issued_at'])+pd.Timedelta(minutes=1)).isoformat()
            r['actual_lead_hours']-=1/60
            if r['task']=='total':r['prediction']=99
        rechain(later)
        r=self.run_case(records=[later,self.rows],expected_head=[later[-1]['record_hash'],self.rows[-1]['record_hash']])
        self.assertEqual(r['audit']['selected_forecasts'],6)
        self.assertEqual(r['audit']['later_issued_records_not_primary'],6)
        self.assertEqual(next(x for x in r['settlements'] if x['task']=='total')['prediction'],45)

    def test_model_alias_does_not_reset_earliest_forecast(self):
        later=copy.deepcopy(self.rows)
        for r in later:
            r['model_id']='renamed_'+r['model_id'];r['protocol']='football-shadow-v999'
            r['issued_at']=(pd.Timestamp(r['issued_at'])+pd.Timedelta(minutes=1)).isoformat()
            r['actual_lead_hours']-=1/60
        rechain(later)
        r=self.run_case(records=[self.rows,later],expected_head=[self.rows[-1]['record_hash'],later[-1]['record_hash']])
        self.assertEqual(r['audit']['selected_forecasts'],6)
        self.assertEqual(r['audit']['later_issued_records_not_primary'],6)

    def test_repeated_chain_reused_without_double_count(self):
        r=self.run_case(records=[self.rows,self.rows],expected_head=[self.rows[-1]['record_hash']]*2)
        self.assertEqual(r['audit']['duplicate_chain_records_reused'],6)
        self.assertEqual(r['audit']['selected_forecasts'],6)

    def test_same_time_conflicting_prediction_rejected(self):
        other=copy.deepcopy(self.rows);other[0]['protocol']='football-shadow-v999';other[0]['prediction']=.7;rechain(other)
        with self.assertRaisesRegex(ValueError,'Conflicting simultaneous'):
            self.run_case(records=[self.rows,other],expected_head=[self.rows[-1]['record_hash'],other[-1]['record_hash']])

    def test_model_id_hash_conflict_rejected(self):
        self.rows[3]['model_sha256']='f'*64;rechain(self.rows)
        with self.assertRaisesRegex(ValueError,'conflicting model hash'):self.run_case()

    def test_append_retry_and_newer_correction_preserve_prefix(self):
        result=self.run_case()
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'ledger.jsonl'
            a=append_settlements(path,result['settlements']);raw=path.read_bytes()
            self.assertEqual(a['appended'],3)
            b=append_settlements(path,result['settlements']);self.assertEqual(b['reused'],3);self.assertEqual(path.read_bytes(),raw)
            games=self.games.copy();games.loc[0,'home_points']=27
            obs=copy.deepcopy(self.obs);obs['nfl']['observed_at']='2030-01-10T00:00:00Z'
            corrected=self.run_case(games=games,observed_at=obs)['settlements']
            c=append_settlements(path,corrected);self.assertEqual(c['appended'],3)
            self.assertTrue(path.read_bytes().startswith(raw))
            rows=[json.loads(x) for x in path.read_text().splitlines()]
            self.assertTrue(all(x['revision']==2 and x['supersedes'] for x in rows[3:]))
            self.assertEqual(append_settlements(path,corrected)['reused'],3)

    def test_unchanged_new_observation_does_not_duplicate_settlement(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'ledger.jsonl';append_settlements(path,self.run_case()['settlements']);raw=path.read_bytes()
            obs=copy.deepcopy(self.obs);obs['nfl']['observed_at']='2030-01-10T00:00:00Z'
            r=append_settlements(path,self.run_case(observed_at=obs)['settlements'])
            self.assertEqual(r['reused'],3);self.assertEqual(path.read_bytes(),raw)

    def test_older_correction_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'ledger.jsonl';append_settlements(path,self.run_case()['settlements'])
            self.games.loc[0,'home_points']=27
            with self.assertRaisesRegex(ValueError,'strictly newer'):
                append_settlements(path,self.run_case()['settlements'])

    def test_atomic_publication_failure_preserves_prior_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'ledger.jsonl';append_settlements(path,self.run_case()['settlements']);old=path.read_bytes()
            self.games.loc[0,'home_points']=27
            obs=copy.deepcopy(self.obs);obs['nfl']['observed_at']='2030-01-10T00:00:00Z'
            candidates=self.run_case(observed_at=obs)['settlements']
            with mock.patch('settlement.os.replace', side_effect=OSError('simulated publish interruption')):
                with self.assertRaises(OSError):append_settlements(path,candidates)
            self.assertEqual(path.read_bytes(),old)
            self.assertEqual(list(path.parent.glob('*.pending-*')),[])
            self.assertEqual(append_settlements(path,candidates)['appended'],3)

    def test_corrupt_settlement_chain_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'ledger.jsonl';append_settlements(path,self.run_case()['settlements'])
            path.write_bytes(path.read_bytes().replace(b'"prediction":3.0',b'"prediction":9.0'))
            with self.assertRaisesRegex(ValueError,'integrity'):append_settlements(path,[])

    def test_pinned_raw_size_and_sha_before_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'prior.jsonl';raw=b''.join(_json(x)+b'\n' for x in self.rows);p.write_bytes(raw)
            pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),head_sha256=self.rows[-1]['record_hash'])
            self.assertEqual(len(_load_pinned_ledger(p,pin)),6)
            pin['bytes']+=1
            with self.assertRaisesRegex(ValueError,'bytes/hash'):_load_pinned_ledger(p,pin)

    def test_null_pinned_head_cannot_skip_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'prior.jsonl';raw=b''.join(_json(x)+b'\n' for x in self.rows);p.write_bytes(raw)
            pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),head_sha256=None)
            with self.assertRaisesRegex(ValueError,'head mismatch'):_load_pinned_ledger(p,pin)

    def test_duplicate_scoring_rows_rejected(self):
        r=self.run_case()['settlements'][0]
        with self.assertRaisesRegex(ValueError,'Duplicate game'):score_settlements([r,r])

    def test_runtime_crash_resume_same_pending_and_no_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);raw=b''.join(_json(x)+b'\n' for x in self.rows)
            prior=root/'prior.jsonl';prior.write_bytes(raw);games=root/'games.parquet';self.games.to_parquet(games,index=False)
            pin=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),head_sha256=self.rows[-1]['record_hash'])
            ctx=SimpleNamespace(root=root,fixture=True,config={},args={'settlement_fixture_as_of':self.as_of,'inject_failure':'SETTLED'},
                                cp=Checkpoints(root,'test'),sync=lambda files:None)
            with self.assertRaisesRegex(RuntimeError,'Intentional crash'):
                build_settlement(ctx,prior,games,self.obs,fixture_pin=pin)
            batch=(root/'settlement_batch.json').read_bytes();ledger=(root/'settlement_ledger.jsonl').read_bytes()
            ctx.args.pop('inject_failure')
            a=build_settlement(ctx,prior,games,self.obs,fixture_pin=pin)
            self.assertEqual(a['settlement_ledger']['reused'],3)
            self.assertEqual((root/'settlement_batch.json').read_bytes(),batch)
            self.assertEqual((root/'settlement_ledger.jsonl').read_bytes(),ledger)
            self.assertEqual(build_settlement(ctx,prior,games,self.obs,fixture_pin=pin),a)
            self.assertEqual(prior.read_bytes(),raw)

    def test_runtime_pin_override_production_prohibited(self):
        ctx=SimpleNamespace(root=pathlib.Path('/tmp'),fixture=False,config={})
        with self.assertRaisesRegex(ValueError,'cannot be overridden'):
            build_settlement(ctx,'unused','unused',{},fixture_pin={})

    def test_enough_blocks_produces_descriptive_interval_only(self):
        base=self.run_case()['settlements'][0]
        rows=[]
        for i in range(100):
            x=copy.deepcopy(base);x['game_id']='game'+str(i);x['season_week_block']='2030-'+str(i%10);rows.append(x)
        card=score_settlements(rows)[0]
        self.assertTrue(card['uncertainty']['available']);self.assertFalse(card['uncertainty']['confirmatory'])
        self.assertFalse(card['model_promoted'])


if __name__=='__main__':unittest.main()
