"""Offline integration guards for FBS scope and frozen model artifacts."""
import unittest

import numpy as np
import pandas as pd

from common import GateError
from repair_tests import fixture
from scope_adapter import prepare_loaded_inputs


def inputs():
    canonical, queue, links, raw, sources = fixture()
    nfl = canonical.iloc[0].copy(); nfl['track']='nfl';nfl['game_id']='nfl-1000'
    # NFL division flags must never affect NFL retention.
    nfl['home_fbs']=0;nfl['away_fbs']=0
    context=canonical.iloc[0].copy();context['game_id']='1001';context['away_fbs']=0
    canonical=pd.concat([canonical,pd.DataFrame([nfl,context])],ignore_index=True)
    frame=canonical.copy();frame['test_existing_feature']=[1.,2.,3.]
    return frame,canonical,queue,links,raw,sources


class ScopeTests(unittest.TestCase):
    def run_scope(self,x):return prepare_loaded_inputs(*x,target_game_ids=('1000',))

    def test_nfl_preserved_and_fcs_context_removed_only_from_targets(self):
        out=self.run_scope(inputs())
        self.assertEqual(out['frame'].game_id.tolist(),['1000','nfl-1000'])
        self.assertEqual(out['fbs_history_context'].game_id.tolist(),['1001'])
        self.assertEqual(out['scope_audit']['excluded_context_model_rows'],1)
        self.assertEqual(out['scope_audit']['nfl_rows_preserved'],1)

    def test_existing_feature_values_preserved(self):
        x=inputs();before=x[0].copy(deep=True);out=self.run_scope(x)
        pd.testing.assert_frame_equal(before,x[0])
        self.assertEqual(out['frame'].test_existing_feature.tolist(),[1.,2.])
        self.assertFalse(out['scope_audit']['repaired_aggregates_inserted_into_model_features'])

    def test_new_final_labels_are_separate(self):
        x=inputs();x[0].loc[0,'completed']=False
        x[0].loc[0,['home_points','away_points']]=np.nan
        out=self.run_scope(x)
        self.assertFalse(out['frame'].iloc[0].completed)
        self.assertTrue(out['canonical_games'].iloc[0].completed)
        self.assertEqual(len(out['new_canonical_finals']),1)
        self.assertTrue(out['scope_audit']['canonical_final_updates_require_matched_baseline_cohort'])

    def test_unknown_track_rejected(self):
        x=inputs();x[0].loc[1,'track']='acb'
        with self.assertRaises(GateError):self.run_scope(x)

    def test_canonical_nfl_population_mismatch_rejected(self):
        x=list(inputs());x[1]=x[1][x[1].track.ne('nfl')]
        with self.assertRaises(GateError):self.run_scope(x)

    def test_repaired_rows_separate_from_model_frame(self):
        out=self.run_scope(inputs())
        self.assertEqual(len(out['regulation_efficiency_additions']),2)
        self.assertEqual(len(out['frame']),2)
        self.assertNotIn('drive_yards_per_play',out['frame'])


if __name__=='__main__':unittest.main()
