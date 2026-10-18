"""Synthetic feature reconstruction tests: no fitting, credentials or providers."""
import copy
import json
import pathlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from common import Checkpoints
from data import FEATURES,build_features
from efficiency import METRICS,augment_features,feature_columns
from fresh_features import (BASE_COLUMNS,STATS_COLUMNS,SEMANTIC_CONTRACT,_canonical,
                            replay_frozen_features,reconstruct_features,rebuild_serving)
from prospective import fixture_api,issue_forecasts


def synthetic_inputs():
    now=pd.Timestamp('2026-10-18T12:00:00Z');old='2026-10-16T12:00:00Z';rows=[]
    def game(track,gid,date,home,away,done,hs=24,aws=17,fbsaway=1):
        rows.append(dict(track=track,game_id=gid,season=2026,week=7,season_type='regular',kickoff=pd.Timestamp(date),
            home_id=home,away_id=away,home_name=home,away_name=away,completed=done,home_points=float(hs) if done else np.nan,
            away_points=float(aws) if done else np.nan,neutral=0,home_fbs=1,away_fbs=fbsaway,source='synthetic',source_snapshot_at=old))
    game('nfl','n0','2026-10-09T12:00:00Z','NA','NB',True)
    game('nfl','n1','2026-10-17T12:00:00Z','NA','NC',False)
    game('nfl','nt','2026-10-20T20:00:00Z','NA','NB',False)
    game('ncaaf','c0','2026-10-08T12:00:00Z','CA','CB',True,28,14)
    game('ncaaf','c1','2026-10-17T11:00:00Z','CA','CC',False)
    game('ncaaf','ct','2026-10-20T18:00:00Z','CA','CB',False)
    canonical=_canonical(pd.DataFrame(rows));stats=[]
    for team,opp in [('CA','CB'),('CB','CA')]:stats.append(dict(track='ncaaf',game_id='c0',team_id=team,opponent_id=opp,**METRICS['ncaaf']))
    stats=pd.DataFrame(stats,columns=STATS_COLUMNS)
    frozen,_=augment_features(build_features(canonical),stats)
    current=canonical.copy()
    for gid in ['n1','c1']:
        ix=current.game_id==gid;current.loc[ix,'completed']=True;current.loc[ix,'home_points']=35.;current.loc[ix,'away_points']=7.
    observations={t:dict(observed_at='2026-10-18T11:30:00Z',sha256='a'*64,complete_schedule=True,season=2026) for t in ['nfl','ncaaf']}
    observations['ncaaf_efficiency']=dict(observed_at='2026-10-18T11:00:00Z',sha256='e'*64,aggregate_sha256='f'*64,semantic_contract=SEMANTIC_CONTRACT,source='synthetic original primary metric capture')
    return dict(frozen_frame=frozen,historical_fbs_stats=stats,current_games=current,
                current_fbs_stats=pd.DataFrame(columns=STATS_COLUMNS),observations=observations,as_of=now)


def compatible_stats(gid='c1',home='CA',away='CC',observed='2026-10-18T11:40:00Z'):
    return pd.DataFrame([dict(track='ncaaf',game_id=gid,team_id=t,opponent_id=o,**METRICS['ncaaf'],
        source_observed_at=observed,source_sha256='b'*64,semantic_contract=SEMANTIC_CONTRACT) for t,o in [(home,away),(away,home)]])


class FreshFeatureTests(unittest.TestCase):
    def setUp(self):self.d=synthetic_inputs()
    def run_rebuild(self):return reconstruct_features(**self.d)
    def target(self,f,gid):return f.set_index('game_id').loc[gid]
    def test_frozen_replay_exact(self):
        a=replay_frozen_features(self.d['frozen_frame'],self.d['historical_fbs_stats'])
        self.assertEqual(a['status'],'PASS');self.assertTrue(all(x['max_absolute_difference']==0 for x in a['tracks']))
    def test_frozen_feature_tamper_rejected(self):
        self.d['frozen_frame'].loc[0,'elo_diff']+=1
        with self.assertRaisesRegex(ValueError,'definition parity'):replay_frozen_features(self.d['frozen_frame'],self.d['historical_fbs_stats'])
    def test_strict_release_boundary(self):
        f,_,_=self.run_rebuild();r=self.target(f,'nt');self.assertEqual(r.home_games,1)
        self.d['as_of']+=pd.Timedelta(seconds=1)
        f,_,_=self.run_rebuild();r=self.target(f,'nt');self.assertEqual(r.home_games,2)
        self.assertAlmostEqual(r.total_recent,29.5+17.)
    def test_result_changes_before_release_cannot_change_current_features(self):
        f,_,_=self.run_rebuild();self.d['current_games'].loc[self.d['current_games'].game_id=='n1','home_points']=100
        z,_,_=self.run_rebuild();np.testing.assert_array_equal(self.target(f,'nt')[FEATURES].to_numpy(),self.target(z,'nt')[FEATURES].to_numpy())
    def test_missing_current_drives_explicit(self):
        f,a,p=self.run_rebuild();r=self.target(f,'ct')
        self.assertFalse(r.reconstruction_ready);self.assertIn('released_history_missing_compatible_drive_statistics',r.reconstruction_reasons)
        self.assertEqual(json.loads(p.set_index('game_id').loc['ct'].missing_drive_game_ids),['c1'])
    def test_compatible_drive_updates_exact_definition(self):
        self.d['current_fbs_stats']=compatible_stats();f,a,_=self.run_rebuild();r=self.target(f,'ct')
        self.assertTrue(r.reconstruction_ready);self.assertEqual(r.eff_home_games,2);self.assertEqual(a['current_compatible_drive_games'],1)
        self.assertEqual(r.source_snapshot_at,'2026-10-18T11:30:00+00:00')
        self.assertEqual(r.fresh_feature_available_at,pd.Timestamp('2026-10-18T11:40:00Z'))
    def test_unapproved_secondary_stats_not_inserted(self):
        self.d['current_fbs_stats']=compatible_stats();self.d['current_fbs_stats']['semantic_contract']='official_rows_only'
        f,a,_=self.run_rebuild();self.assertEqual(a['current_compatible_drive_games'],0);self.assertFalse(self.target(f,'ct').reconstruction_ready)
        self.assertIn('semantics unverified',a['rejected_current_drive_games'][0]['reason'])
    def test_future_observed_drives_not_consumed(self):
        self.d['current_fbs_stats']=compatible_stats(observed='2026-10-18T13:00:00Z')
        f,a,_=self.run_rebuild();self.assertEqual(a['current_compatible_drive_games'],0);self.assertEqual(self.target(f,'ct').eff_home_games,1)
    def test_observation_clocks_not_reset_by_rebuild(self):
        self.d['observations']['nfl']['observed_at']='2026-10-16T12:00:00Z'
        # Earlier snapshot cannot truthfully carry a later final.
        ix=self.d['current_games'].game_id=='n1';self.d['current_games'].loc[ix,'completed']=False;self.d['current_games'].loc[ix,['home_points','away_points']]=np.nan
        f,_,_=self.run_rebuild();r=self.target(f,'nt');self.assertEqual(r.source_snapshot_at,'2026-10-16T12:00:00+00:00');self.assertFalse(r.reconstruction_ready)
        self.assertIn('snapshot_stale',r.reconstruction_reasons)
    def test_source_after_asof_cannot_modify_state(self):
        self.d['observations']['nfl']['observed_at']='2026-10-19T12:00:00Z';self.d['as_of']+=pd.Timedelta(seconds=1)
        f,_,_=self.run_rebuild();self.assertEqual(self.target(f,'nt').home_games,1);self.assertFalse(self.target(f,'nt').reconstruction_ready)
    def test_missing_scope_receipt_abstains(self):
        self.d['observations']['nfl']['complete_schedule']=False
        f,_,_=self.run_rebuild();self.assertFalse(self.target(f,'nt').reconstruction_ready)
    def test_missing_known_schedule_ids_abstains(self):
        self.d['current_games']=self.d['current_games'][self.d['current_games'].game_id!='n0']
        f,a,_=self.run_rebuild();self.assertFalse(self.target(f,'nt').reconstruction_ready);self.assertEqual(a['tracks']['nfl']['missing_known_game_ids'],['n0'])
    def test_existing_team_identity_change_rejected(self):
        self.d['current_games'].loc[self.d['current_games'].game_id=='n1','home_id']='OTHER'
        with self.assertRaisesRegex(ValueError,'identity changed'):self.run_rebuild()
    def test_duplicate_canonical_rejected(self):
        self.d['current_games']=pd.concat([self.d['current_games'],self.d['current_games'].iloc[[0]]])
        with self.assertRaisesRegex(ValueError,'Duplicate canonical'):self.run_rebuild()
    def test_revised_result_requires_drive_revalidation(self):
        self.d['current_games'].loc[self.d['current_games'].game_id=='c0','home_points']=40
        f,_,p=self.run_rebuild();self.assertFalse(self.target(f,'ct').reconstruction_ready)
        self.assertIn('c0',json.loads(p.set_index('game_id').loc['ct'].missing_drive_game_ids))
    def test_new_legacy_fcs_opponent_result_is_not_silently_ignored(self):
        # A previously declared FBS/FCS fixture is relevant opponent context,
        # while the only future target remains FBS-v-FBS.
        for k in ['frozen_frame','current_games']:self.d[k].loc[self.d[k].game_id=='c1','away_fbs']=0
        f,a,p=self.run_rebuild();self.assertEqual(self.target(f,'ct').home_games,2)
        self.assertFalse(self.target(f,'ct').reconstruction_ready)
        self.assertNotIn('c1',a['tracks']['ncaaf']['new_completed_fbs_vs_fbs_ids'])
        self.assertEqual(set(p[p.track=='ncaaf'].game_id),{'ct'})
    def test_taint_propagates_through_opponent_adjustment(self):
        # Missing CA/CC stats taint CC; a later valid CB/CC game propagates to CB.
        cur=self.d['current_games'];z=cur[cur.game_id=='c1'].copy();z['game_id']='c2';z['home_id']='CB';z['away_id']='CC';z['kickoff']=pd.Timestamp('2026-10-17T11:10:00Z')
        self.d['current_games']=pd.concat([cur,z],ignore_index=True)
        self.d['current_fbs_stats']=compatible_stats('c2','CB','CC')
        f,a,p=self.run_rebuild();self.assertTrue(any(x['game_id']=='c2' and 'c1' in x['missing_compatible_drive_game_ids'] for x in a['taint_events']))
    def test_old_declared_missing_drive_gap_does_not_newly_taint(self):
        # Original missing-game handling is part of the saved definition.
        self.d['historical_fbs_stats']=self.d['historical_fbs_stats'].iloc[0:0]
        self.d['current_fbs_stats']=compatible_stats()
        f,a,_=self.run_rebuild();self.assertTrue(self.target(f,'ct').reconstruction_ready)
    def test_future_target_outcome_is_not_used(self):
        f,_,_=self.run_rebuild();mask=self.d['current_games'].game_id=='nt';self.d['current_games'].loc[mask,['home_points','away_points']]=[120.,1.]
        z,_,_=self.run_rebuild();np.testing.assert_array_equal(self.target(f,'nt')[FEATURES].to_numpy(),self.target(z,'nt')[FEATURES].to_numpy())
    def test_release_clock_and_actual_observation_are_separate(self):
        self.d['current_fbs_stats']=compatible_stats();f,_,_=self.run_rebuild();r=self.target(f,'ct')
        self.assertEqual(r.efficiency_max_available_at,pd.Timestamp('2026-10-18T11:00:00Z'))
        self.assertEqual(r.fresh_feature_available_at,pd.Timestamp('2026-10-18T11:40:00Z'))
        self.assertIsNone(r.source_publication_at)
    def test_denied_nfl_observation_abstains_without_blocking_valid_fbs(self):
        self.d['observations']['nfl']={'observed_at':None,'input_usable':False,'complete_schedule':False}
        self.d['current_fbs_stats']=compatible_stats()
        frame,_,_=self.run_rebuild();frame['x']=1.
        serving=fixture_api(self.d['as_of']);snapshot=serving['snapshot'];snapshot['reconstructed']=True
        snapshot['tracks']={'ncaaf':{'feature_observed_at':'2026-10-18T11:30:00Z','canonical_observed_at':'2026-10-18T11:30:00Z'}}
        records,audit=issue_forecasts(frame,frame[BASE_COLUMNS],serving['contracts'],serving['models'],snapshot,self.d['as_of'])
        self.assertEqual(audit['forecasts'],3);self.assertEqual(audit['abstentions'],3)
        self.assertTrue(all(r['status']=='issued' for r in records if r['track']=='ncaaf'))
        self.assertTrue(all('inherited_feature_source_vintage_unknown' in r['reasons'] and r['prediction'] is None for r in records if r['track']=='nfl'))
    def test_fresh_schedule_cannot_renew_stale_efficiency_domain(self):
        self.d['current_fbs_stats']=compatible_stats()
        self.d['observations']['ncaaf_efficiency']['observed_at']='2026-10-16T18:15:25Z'
        f,a,_=self.run_rebuild();r=self.target(f,'ct')
        self.assertFalse(r.reconstruction_ready);self.assertIn('current_efficiency_source_stale',r.reconstruction_reasons)
        self.assertEqual(r.current_efficiency_observed_at,pd.Timestamp('2026-10-16T18:15:25Z'))
        self.assertEqual(a['current_efficiency_domain']['observed_at'],'2026-10-16T18:15:25+00:00')
        self.assertTrue(self.target(f,'nt').reconstruction_ready)
    def test_unknown_efficiency_observation_is_not_inferred_from_schedule(self):
        self.d['observations'].pop('ncaaf_efficiency');self.d['current_fbs_stats']=compatible_stats()
        f,a,_=self.run_rebuild();r=self.target(f,'ct')
        self.assertFalse(r.reconstruction_ready);self.assertTrue(pd.isna(r.current_efficiency_observed_at))
        self.assertIn('efficiency_observation_or_equivalence_unverified',r.reconstruction_reasons)
    def test_complete_actual_metric_reobservation_can_refresh_domain(self):
        self.d['observations']['ncaaf_efficiency']['observed_at']='2026-10-16T18:15:25Z'
        self.d['current_fbs_stats']=pd.concat([compatible_stats(),compatible_stats('c0','CA','CB')],ignore_index=True)
        f,a,_=self.run_rebuild();self.assertTrue(self.target(f,'ct').reconstruction_ready)
        self.assertTrue(a['current_efficiency_domain']['complete_current_season_reobservation'])
        self.assertEqual(a['current_efficiency_domain']['reobserved_current_season_metric_games'],2)

    def test_wrapper_real_reconstruction_in_fixture_without_fits(self):
        serving=fixture_api();current=serving['frame'].copy();current['neutral']=0
        sources=dict(current_games=current,current_fbs_stats=pd.DataFrame(columns=STATS_COLUMNS),observations={})
        with tempfile.TemporaryDirectory() as td:
            ctx=SimpleNamespace(root=pathlib.Path(td),fixture=True)
            with mock.patch('sklearn.linear_model.Ridge.fit',side_effect=AssertionError('no fit')):
                out=rebuild_serving(ctx,serving,sources)
            self.assertEqual(out['feature_replay_parity']['status'],'PASS');self.assertTrue((ctx.root/'fresh_features.parquet').is_file())
            self.assertTrue(out['snapshot']['reconstructed']);self.assertIn('nfl',out['snapshot']['tracks'])
    def test_resume_loads_saved_vintage_without_new_clock(self):
        serving=fixture_api();current=serving['frame'].copy();current['neutral']=0;sources=dict(current_games=current,current_fbs_stats=pd.DataFrame(columns=STATS_COLUMNS),observations={})
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);ctx=SimpleNamespace(root=root,fixture=True)
            first=rebuild_serving(ctx,serving,sources)
            (root/'snapshot_contract.json').write_text(json.dumps(first['snapshot']));(root/'serving_parity.json').write_text(json.dumps(serving.get('parity',[])))
            files=[p for p in root.iterdir() if p.is_file()]
            ctx.cp=Checkpoints(root,'synthetic-immutable-inputs')
            ctx.cp.commit('exact_feature_reconstruction_and_serving',files,{'verified':True})
            before={p.name:p.read_bytes() for p in files}
            ctx.fixture=False # exercise production resume with a later wall clock
            sources['observations']={'nfl':{'observed_at':'2030-01-10T00:00:00Z'}}
            with mock.patch('fresh_features.reconstruct_features',side_effect=AssertionError('resume must not rebuild')), mock.patch('fresh_features._runtime_utc_now',side_effect=AssertionError('resume must not read newer wall clock')):
                second=rebuild_serving(ctx,serving,sources)
            self.assertEqual(first['snapshot'],second['snapshot']);self.assertEqual(first['reconstruction_audit']['as_of'],second['reconstruction_audit']['as_of'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in files})

if __name__=='__main__':unittest.main()
