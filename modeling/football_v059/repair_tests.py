"""Offline tests for the bounded FBS overtime repair; no model fits or network."""
import copy
import hashlib
import pathlib
import tempfile
import unittest

import numpy as np
import pandas as pd

from common import GateError
from fbs_repair import (exclude_explicit_overtime, prepare_fbs_scope,
                        repair_targeted_games, verify_local_inputs)


def fixture():
    games = pd.DataFrame([dict(track='ncaaf', game_id='1000', season=2020, week=1,
        kickoff=pd.Timestamp('2020-09-01T18:00:00Z'), home_id='1', away_id='2',
        home_name='Alpha', away_name='Beta', home_points=20., away_points=14.,
        completed=True, home_fbs=1, away_fbs=1)])
    source = dict(key='pinned/2020.parquet', sha256='a'*64,
                  observed_at='2026-10-16T00:00:00Z')
    rows=[]
    for i in range(8):
        rows.append(dict(contest_id='9000', espn_game_id='1000', season=2020,
            drive_number=str(i+1), team='Alpha' if i<4 else 'Beta', period=1,
            quarter=1., start_period=1., end_period=1., n_plays=5, yards=25,
            end_how='PUNT'))
    for i in range(2):
        rows.append(dict(contest_id='9000', espn_game_id='1000', season=2020,
            drive_number=str(9+i), team='Alpha' if i==0 else 'Beta', period=5,
            quarter=np.nan, start_period=np.nan, end_period=np.nan,
            n_plays=3, yards=25, end_how='TD'))
    raw=pd.DataFrame(rows)
    links=[dict(game_id='1000', contest_id='9000', season=2020,
        ncaa_names={'11':'Alpha','22':'Beta'}, ncaa_to_canonical={'11':'1','22':'2'},
        home_id='1',away_id='2',kickoff='2020-09-01T18:00:00Z',raw_rows=10,
        source=source)]
    queue=[dict(game_id='1000',season=2020,recovery_reason='invalid_drive_period',
                recovery_status='source_validation_rejected')]
    return games,queue,links,{2020:raw},{2020:source}


class RepairTests(unittest.TestCase):
    def run_repair(self, values=None):
        return repair_targeted_games(*(values or fixture()),target_game_ids=('1000',))

    def test_explicit_ot_repaired_unchanged_regulation_gate(self):
        out=self.run_repair()
        self.assertEqual(out['audit']['repaired_fbs_games'],1)
        self.assertEqual(len(out['features']),2)
        self.assertEqual(out['audit']['excluded_overtime_rows'],2)
        self.assertFalse(out['audit']['baseline_replacement_permitted'])
        self.assertFalse(out['audit']['source_interchangeability_approved'])

    def test_exclusion_preserves_original_rows_and_pin(self):
        x=fixture();before=x[3][2020].copy(deep=True);out=self.run_repair(x)
        pd.testing.assert_frame_equal(before,x[3][2020])
        self.assertEqual(out['excluded_overtime'][0]['raw']['period'],5)
        self.assertEqual(out['excluded_overtime'][0]['source_sha256'],'a'*64)
        self.assertIsNone(out['excluded_overtime'][0]['raw']['start_period'])

    def test_contradictory_regulation_boundary_rejected(self):
        x=fixture();x[3][2020].loc[8,'start_period']=4
        out=self.run_repair(x)
        self.assertEqual(out['audit']['repaired_fbs_games'],0)
        self.assertEqual(len(out['remaining_fbs_queue']),1)

    def test_fractional_ot_period_not_accepted(self):
        x=fixture();x[3][2020]['period']=x[3][2020].period.astype(float)
        x[3][2020].loc[8,'period']=5.5
        self.assertEqual(self.run_repair(x)['audit']['repaired_fbs_games'],0)

    def test_malformed_nonnull_period_boundary_rejected(self):
        x=fixture();x[3][2020]['start_period']=x[3][2020].start_period.astype(object)
        x[3][2020].loc[8,'start_period']='unknown'
        self.assertEqual(self.run_repair(x)['audit']['repaired_fbs_games'],0)

    def test_unknown_regulation_outcome_stays_quarantined(self):
        x=fixture();x[3][2020].loc[0,'end_how']=None
        self.assertEqual(self.run_repair(x)['audit']['repaired_fbs_games'],0)

    def test_zero_play_ot_keeps_legacy_bookkeeping_path(self):
        x=fixture();x[3][2020].loc[8,['n_plays','end_period','end_how']]=[0,0,None]
        out=self.run_repair(x)
        self.assertEqual(out['audit']['repaired_fbs_games'],1)
        self.assertEqual(out['audit']['excluded_overtime_rows'],1)

    def test_minimum_two_team_evidence_not_relaxed(self):
        x=fixture();x[3][2020].loc[4:7,'n_plays']=1
        self.assertEqual(self.run_repair(x)['audit']['repaired_fbs_games'],0)

    def test_fcs_target_rejected(self):
        x=fixture();x[0].loc[0,'away_fbs']=0
        with self.assertRaises(GateError):self.run_repair(x)

    def test_source_hash_receipt_conflict_rejected(self):
        x=fixture();x[4][2020]=dict(x[4][2020],sha256='b'*64)
        with self.assertRaises(GateError):self.run_repair(x)

    def test_identity_context_conflict_rejected(self):
        x=fixture();x[2][0]['home_id']='3'
        with self.assertRaises(GateError):self.run_repair(x)

    def test_original_raw_count_preserved(self):
        x=fixture();x[2][0]['raw_rows']=9
        with self.assertRaises(GateError):self.run_repair(x)

    def test_scoped_context_separate_and_no_predictions(self):
        g=fixture()[0];r=g.iloc[0].copy();r['game_id']='1001';r['away_fbs']=0
        c=pd.concat([g,pd.DataFrame([r])],ignore_index=True)
        target,context,audit=prepare_fbs_scope(c)
        self.assertEqual(len(target),1);self.assertEqual(len(context),1)
        self.assertFalse(context.prediction_eligible.any())
        self.assertEqual(audit['standalone_fcs_games'],0)

    def test_new_final_bookkeeping_does_not_change_frozen_features(self):
        g=fixture()[0];f=g.copy();f.loc[0,'completed']=False
        f.loc[0,['home_points','away_points']]=np.nan;before=f.copy(deep=True)
        _,_,audit=prepare_fbs_scope(g,f)
        self.assertEqual(len(audit['newly_completed_since_frozen']),1)
        pd.testing.assert_frame_equal(before,f)

    def test_existing_completed_score_change_fails(self):
        g=fixture()[0];f=g.copy();f.loc[0,'home_points']=21.
        with self.assertRaises(GateError):prepare_fbs_scope(g,f)

    def test_pin_verification_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'file.bin';p.write_bytes(b'ab')
            pins=[dict(name='file.bin',bytes=2,sha256=hashlib.sha256(b'ab').hexdigest())]
            verify_local_inputs(d,pins);p.write_bytes(b'cd')
            with self.assertRaises(GateError):verify_local_inputs(d,pins)


if __name__=='__main__':unittest.main()
