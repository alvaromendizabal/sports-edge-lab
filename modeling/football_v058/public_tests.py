"""Additional offline scientific/data gates; no additional model fitting."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss,log_loss,mean_absolute_error,mean_squared_error
from common import Checkpoints,GateError
from data import build_features,normalize_nfl,split_rows
from efficiency import deduplicate
from experiments import prepare,columns
from fixtures import fixture_data,synthetic_games
from metrics import score,paired_interval,interval_score,residual_intervals


class PublicScientificTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=fixture_data();cls.frame=cls.fixture['frame']
    def test_fixture_is_explicitly_synthetic(self):
        self.assertTrue(self.fixture['readiness']['synthetic']);self.assertFalse(self.fixture['readiness']['core_modeling_ready'])
        self.assertTrue((self.frame.source=='synthetic fixture').all())
    def test_temporal_split_and_game_disjointness(self):
        for track in ['nfl','ncaaf']:
            tr,te=split_rows(self.frame,track,'total',2021,[2022])
            self.assertLess(tr.kickoff.max()+pd.Timedelta(hours=24),te.decision_at.min())
            self.assertFalse(set(tr.game_id)&set(te.game_id))
    def test_leaked_history_fails_closed(self):
        f=self.frame.copy();i=f.index[f.track=='nfl'][0];f.loc[i,'feature_max_available_at']=f.loc[i,'decision_at']
        with self.assertRaisesRegex(GateError,'at/after'):prepare(f)
    def test_duplicate_game_fails_closed(self):
        f=pd.concat([self.frame,self.frame.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(GateError,'Duplicate'):prepare(f)
    def test_nonfinite_model_input_fails_closed(self):
        f=self.frame.copy();i=f.index[f.track=='ncaaf'][0];f.loc[i,columns('ncaaf')[-1]]=np.inf
        with self.assertRaisesRegex(GateError,'Nonfinite'):prepare(f)
    def test_current_result_does_not_enter_current_features(self):
        games=synthetic_games();a=build_features(games);target=games.index[games.track=='nfl'][80]
        changed=games.copy();changed.loc[target,['home_points','away_points','margin','total','win']]=[70,0,70,70,1]
        b=build_features(changed);gid=games.loc[target,'game_id']
        for c in ['elo_diff','pf_diff','pa_diff','total_recent','margin_recent_diff']:
            self.assertEqual(a.loc[a.game_id==gid,c].iloc[0],b.loc[b.game_id==gid,c].iloc[0])
    def test_exact_nfl_identity_join(self):
        r=dict(season=2023,game_type='REG',game_id='2023_01_BUF_BAL',home_team='BAL',away_team='BUF',week=1,gametime='13:00',gameday='2023-09-10',home_score=21,away_score=14,location='Home')
        self.assertEqual(normalize_nfl(r,'synthetic source')['home_id'],'BAL')
        r['away_team']='KC'
        with self.assertRaisesRegex(GateError,'mismatch'):normalize_nfl(r,'synthetic source')
    def test_conflicting_source_duplicate_excludes_game(self):
        raw=pd.DataFrame([dict(game_id='g1',drive_id=1,yards=20),dict(game_id='g1',drive_id=1,yards=30),dict(game_id='g2',drive_id=2,yards=10)])
        audit={};quarantine=[];clean=deduplicate(raw,['game_id','drive_id'],audit,quarantine)
        self.assertEqual(clean.game_id.tolist(),['g2']);self.assertEqual(audit['conflicting_games'],1);self.assertEqual(len(quarantine),2)
    def test_probability_scores_match_sklearn(self):
        y=np.array([0,1,0,1]);p=np.array([.2,.7,.1,.9]);r=score(y,p,'win')
        self.assertAlmostEqual(r['value'],log_loss(y,p));self.assertAlmostEqual(r['brier'],brier_score_loss(y,p));self.assertEqual(sum(x['n'] for x in r['calibration']),4)
    def test_point_scores_match_sklearn(self):
        y=np.array([1.,5.,9.]);p=np.array([0.,7.,6.]);r=score(y,p,'total')
        self.assertAlmostEqual(r['value'],mean_absolute_error(y,p));self.assertAlmostEqual(r['rmse'],np.sqrt(mean_squared_error(y,p)));self.assertAlmostEqual(r['bias'],(p-y).mean())
    def test_interval_score_penalizes_missed_coverage(self):
        scores=interval_score(np.array([0.,5.,10.]),np.array([0.,0.,0.]),np.array([5.,5.,5.]),.2)
        np.testing.assert_array_equal(scores,np.array([5.,5.,55.]))
    def test_small_block_count_does_not_invent_ci(self):
        f=pd.DataFrame(dict(season=[2022]*4,week=[1,2,3,4],target=[1.,0.,1.,0.]))
        r=paired_interval(f,[.8,.2,.8,.2],[.5]*4,'win')
        self.assertIsNone(r['upper95']);self.assertEqual(r['status'],'insufficient_blocks')
    def test_interval_calibration_future_overlap_rejected(self):
        c=pd.DataFrame(dict(kickoff=pd.date_range('2022-01-01',periods=40,tz='UTC'),target=np.arange(40),candidate=np.arange(40)))
        e=pd.DataFrame(dict(snapshot_at=[pd.Timestamp('2022-01-20',tz='UTC')],target=[1.],candidate=[1.]))
        with self.assertRaisesRegex(GateError,'overlaps'):residual_intervals(c,e,'candidate')
    def test_checkpoint_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'toy.txt';p.write_text('synthetic');cp=Checkpoints(root,'fixture');cp.commit('stage',[p],{'status':'ok'});self.assertEqual(cp.lookup('stage')['status'],'ok');p.write_text('modified')
            with self.assertRaisesRegex(GateError,'changed'):cp.lookup('stage')
    def test_source_modules_have_no_network_sdk_dependencies(self):
        banned={'boto3','botocore','requests','httpx','urllib','socket'}
        for p in Path(__file__).parent.glob('*.py'):
            if p.name in {'run_demo.py','public_tests.py'}:continue
            tree=ast.parse(p.read_text())
            imported={n.name.split('.')[0] for node in ast.walk(tree) if isinstance(node,ast.Import) for n in node.names}|{(node.module or '').split('.')[0] for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
            self.assertFalse(imported&banned,(p.name,imported&banned))
    def test_fixture_and_prepare_work_with_network_blocked(self):
        with mock.patch('socket.socket.connect',side_effect=RuntimeError('Network forbidden')),mock.patch('socket.create_connection',side_effect=RuntimeError('Network forbidden')):
            frame,audit=prepare(fixture_data()['frame'])
        self.assertGreater(len(frame),0);self.assertEqual(audit['new_acquisition'],0)


if __name__=='__main__':unittest.main(verbosity=2)
