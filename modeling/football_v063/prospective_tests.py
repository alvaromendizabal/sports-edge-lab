"""Offline prospective contracts: exactly four tiny synthetic fits, no providers."""
import copy
import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from prospective import (append_records,fixture_api,issue_forecasts,load_owned_model,
                         predict_existing,verify_serving_parity,prepare_serving)


class ProspectiveTests(unittest.TestCase):
    synthetic_smoke_fits=4

    @classmethod
    def setUpClass(cls):
        rng=np.random.default_rng(6301);x=rng.normal(size=(32,2));binary=(x[:,0]>0).astype(int);y=3*x[:,0]-x[:,1]
        cls.training_x=x;cls.smoke={}
        # Four fits total; regression objects cover both points targets by reuse.
        for fmt in ['sklearn_pipeline','linear_bundle']:
            for task,target in [('win',binary),('margin',y)]:
                est=LogisticRegression(C=1,max_iter=1000,random_state=6301) if task=='win' else Ridge(alpha=20)
                if fmt=='sklearn_pipeline':
                    m=make_pipeline(StandardScaler(),est).fit(x,target)
                else:
                    scaler=StandardScaler().fit(x);est.fit(scaler.transform(x),target)
                    m=dict(family='linear',task=task,estimator=est,x_scaler=scaler,y_scaler=None,n_features=2,
                           feature_names=['x0','x1'],fixture_iterations_override=None)
                cls.smoke[(fmt,task)]=m

    def setUp(self):self.d=fixture_api()
    def issue(self,d=None):
        z=self.d if d is None else d
        return issue_forecasts(z['frame'],z['canonical'],z['contracts'],z['models'],z['snapshot'],z['fixture_now'])
    def move(self,track,hours):
        t=pd.Timestamp(self.d['fixture_now'])+pd.Timedelta(hours=hours)
        for k in ['frame','canonical']:
            ix=(self.d[k].track==track)&~self.d[k].completed;self.d[k].loc[ix,'kickoff']=t

    def test_six_fixture_forecasts(self):
        r,a=self.issue();self.assertEqual(a['forecasts'],6);self.assertEqual(a['new_fits'],0)
        self.assertTrue(all(x['source_publication_at'] is None and not x['known_starting_qb_used'] for x in r))
    def test_horizons_and_leads(self):
        r,_=self.issue()
        for x in r:
            self.assertEqual(x['horizon_hours'],24 if x['track']=='nfl' else 1)
            self.assertEqual(x['actual_lead_hours'],48)
    def test_late_nfl_abstains(self):
        self.move('nfl',23);r,a=self.issue();self.assertEqual(a['abstentions'],3)
        self.assertTrue(all('issue_deadline_passed' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_exact_issue_boundary(self):
        self.move('nfl',24);_,a=self.issue();self.assertEqual(a['forecasts'],6)
    def test_fbs_deadline(self):
        self.move('ncaaf',.5);r,a=self.issue();self.assertEqual(a['abstentions'],3)
    def test_cannot_backdate_production(self):
        self.d['snapshot']['fixture']=False
        with self.assertRaisesRegex(ValueError,'cannot be supplied'):self.issue()
    def test_stale_snapshot_abstains(self):
        self.d['snapshot']['feature_observed_at']='2029-12-01T00:00:00Z';r,a=self.issue();self.assertEqual(a['abstentions'],6)
        self.assertTrue(all('frozen_feature_snapshot_stale' in x['reasons'] for x in r))
    def test_job_time_does_not_refresh_source(self):
        self.d['frame']['source_snapshot_at']='2029-12-01T00:00:00Z';r,a=self.issue();self.assertEqual(a['abstentions'],6)
        self.assertTrue(all('inherited_feature_source_stale' in x['reasons'] for x in r))
    def test_unknown_or_future_snapshot_clock(self):
        self.d['snapshot']['feature_observed_at']=None
        with self.assertRaises(ValueError):self.issue()
        self.d=fixture_api();self.d['snapshot']['feature_observed_at']='2030-01-03T01:00:00Z'
        r,a=self.issue();self.assertEqual(a['abstentions'],6)
    def test_source_at_cutoff_abstains(self):
        self.move('nfl',24);self.d['snapshot']['feature_observed_at']=self.d['fixture_now']
        r,_=self.issue();self.assertTrue(all('source_not_observed_before_cutoff' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_missing_newly_released_team_history(self):
        z=self.d['canonical'].iloc[[0]].copy();z['game_id']='new';z['kickoff']=pd.Timestamp(self.d['fixture_now'])-pd.Timedelta(days=2)
        self.d['canonical']=pd.concat([self.d['canonical'],z],ignore_index=True)
        r,_=self.issue();self.assertTrue(all('newly_released_team_result_missing_from_frozen_history' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_unreleased_result_not_consumed(self):
        z=self.d['canonical'].iloc[[0]].copy();z['game_id']='new';z['kickoff']=pd.Timestamp(self.d['fixture_now'])-pd.Timedelta(hours=12)
        self.d['canonical']=pd.concat([self.d['canonical'],z],ignore_index=True)
        _,a=self.issue();self.assertEqual(a['forecasts'],6)
    def test_known_result_revision_abstains(self):
        self.d['canonical'].loc[0,'home_points']=99
        r,_=self.issue();self.assertTrue(all('released_result_revised_since_frozen_features' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_schedule_change_abstains(self):
        self.d['canonical'].loc[1,'kickoff']+=pd.Timedelta(hours=1)
        r,_=self.issue();self.assertTrue(all('canonical_feature_identity_or_kickoff_changed' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_no_fcs_target_record(self):
        self.d['canonical'].loc[3,'away_fbs']=0
        r,a=self.issue();self.assertEqual(len(r),3);self.assertEqual(a['excluded_non_fbs_games'],1)
    def test_nonfinite_feature_abstains(self):
        self.d['frame'].loc[1,'x']=np.nan
        r,_=self.issue();self.assertTrue(all('nonfinite_or_missing_features' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_parity_required(self):
        self.d['snapshot']['parity_by_model']={};r,a=self.issue();self.assertEqual(a['abstentions'],6)
    def test_feature_release_strict(self):
        self.d['frame'].loc[1,'feature_max_available_at']=pd.Timestamp(self.d['fixture_now'])+pd.Timedelta(days=1)
        r,_=self.issue();self.assertTrue(all('feature_history_not_available' in x['reasons'] for x in r if x['track']=='nfl'))
    def test_positive_history_unknown_clock_abstains_but_cold_start_allowed(self):
        self.d['frame']['home_games']=1;self.d['frame']['away_games']=1;self.d['frame']['feature_max_available_at']=pd.NaT
        r,a=self.issue();self.assertEqual(a['abstentions'],6)
        self.assertTrue(all('positive_history_has_unknown_availability_clock' in x['reasons'] for x in r))
        self.d['frame']['home_games']=0;self.d['frame']['away_games']=0
        _,a=self.issue();self.assertEqual(a['forecasts'],6)
    def test_positive_efficiency_history_unknown_clock_abstains(self):
        self.d['frame']['eff_home_games']=1;self.d['frame']['eff_away_games']=0
        r,a=self.issue();self.assertEqual(a['abstentions'],3)
        self.assertTrue(all('positive_history_has_unknown_availability_clock' in x['reasons'] for x in r if x['track']=='ncaaf'))
    def test_model_release_strict(self):
        self.d['contracts'][0]['train_latest_release']='2030-01-04T00:00:00Z'
        r,_=self.issue();self.assertIn('training_label_not_available',next(x for x in r if x['model_id']=='nfl_win')['reasons'])
    def test_duplicate_identity_fails(self):
        self.d['frame']=pd.concat([self.d['frame'],self.d['frame'].iloc[[0]]])
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.issue()
    def test_missing_model_abstains(self):
        self.d['models']={};_,a=self.issue();self.assertEqual(a['abstentions'],6)
    def test_freshness_limit_cannot_expand(self):
        self.d['snapshot']['max_age_hours']=168
        with self.assertRaisesRegex(ValueError,'cannot be expanded'):self.issue()

    def contract(self,fmt,task):
        return dict(id='synthetic',track='nfl',task=task,format=fmt,features=['x0','x1'],
                    expected_parity_rows=8,reference_column='accepted',train_latest_release='2025-12-01T00:00:00Z',
                    sklearn_version=sklearn.__version__,owned_manifest_sha256='c'*64,model_pin={'sha256':'x','bytes':0})
    def test_four_tiny_model_inference_smokes(self):
        x=pd.DataFrame(self.training_x,columns=['x0','x1'])
        for (fmt,task),m in self.smoke.items():
            c=self.contract(fmt,task);p=predict_existing(m,x,c)
            self.assertTrue(np.isfinite(p).all())
            if task=='win':self.assertTrue(((p>0)&(p<1)).all())
    def test_owned_load_and_pin_before_deserialization(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'model.joblib';m=self.smoke[('sklearn_pipeline','margin')];joblib.dump(m,p)
            raw=p.read_bytes();c=self.contract('sklearn_pipeline','margin');c['model_pin']={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            loaded=load_owned_model(p,c);self.assertEqual(loaded.n_features_in_,2)
            p.write_bytes(raw+b'x')
            with mock.patch('prospective.joblib.load',side_effect=AssertionError('must not deserialize')):
                with self.assertRaisesRegex(ValueError,'byte-count'):load_owned_model(p,c)
    def test_same_size_tamper_before_deserialization(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'m';p.write_bytes(b'abcdefgh');c=self.contract('sklearn_pipeline','margin');c['model_pin']={'bytes':8,'sha256':'a'*64}
            with mock.patch('prospective.joblib.load',side_effect=AssertionError('must not deserialize')):
                with self.assertRaisesRegex(ValueError,'SHA'):load_owned_model(p,c)
    def test_version_mismatch_before_deserialization(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'m';p.write_bytes(b'abc');c=self.contract('sklearn_pipeline','margin');c['model_pin']={'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()};c['sklearn_version']='0.0'
            with mock.patch('prospective.joblib.load',side_effect=AssertionError('must not deserialize')):
                with self.assertRaisesRegex(ValueError,'version mismatch'):load_owned_model(p,c)
    def test_parity_replay_and_target_failure(self):
        x=pd.DataFrame(self.training_x[:8],columns=['x0','x1']);x['track']='nfl';x['game_id']=['g'+str(i) for i in range(8)];x['season']=2026;x['completed']=True;x['margin']=np.arange(8.)
        x['kickoff']=pd.date_range('2026-01-01',periods=8,freq='7D',tz='UTC')
        m=self.smoke[('sklearn_pipeline','margin')];c=self.contract('sklearn_pipeline','margin')
        p=x[['track','game_id','season','kickoff']].copy();p['task']='margin';p['target']=x.margin;p['accepted']=predict_existing(m,x,c);p['decision_at']=p.kickoff-pd.Timedelta(hours=24)
        a=verify_serving_parity(m,x,p,c);self.assertEqual(a['n'],8);self.assertEqual(a['max_absolute_difference'],0)
        x['home_games']=1
        with self.assertRaisesRegex(ValueError,'unknown availability clock'):verify_serving_parity(m,x,p,c)
        x['home_games']=0
        self.assertEqual(verify_serving_parity(m,x,p,c)['n'],8)
        p.loc[0,'target']=100
        with self.assertRaisesRegex(ValueError,'target mismatch'):verify_serving_parity(m,x,p,c)
    def test_no_fit_called_by_fixture_or_issuance(self):
        with mock.patch.object(Ridge,'fit',side_effect=AssertionError('no fit')),mock.patch.object(LogisticRegression,'fit',side_effect=AssertionError('no fit')):
            d=fixture_api();r,a=self.issue(d);self.assertEqual(a['forecasts'],6)
    def test_append_idempotent_and_conflict(self):
        r,_=self.issue()
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger.jsonl';a=append_records(p,r);self.assertEqual(a['appended'],6)
            b=append_records(p,r);self.assertEqual(b['reused'],6)
            bad=copy.deepcopy(r);bad[0]['prediction']=.7
            with self.assertRaisesRegex(ValueError,'Conflicting immutable'):append_records(p,bad)
            self.assertEqual(len(p.read_text().splitlines()),6)
    def test_hash_chain_detects_tamper(self):
        r,_=self.issue()
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger';append_records(p,r);rows=p.read_text().splitlines();x=json.loads(rows[0]);x['prediction']=.8;rows[0]=json.dumps(x);p.write_text('\n'.join(rows)+'\n')
            with self.assertRaisesRegex(ValueError,'Ledger integrity'):append_records(p,r)
    def test_empty_ledger_is_materialized_and_reusable(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger';a=append_records(p,[])
            self.assertTrue(p.is_file());self.assertEqual(p.read_bytes(),b'');self.assertEqual(a['total'],0)
            self.assertEqual(append_records(p,[])['appended'],0)
    def test_clock_advance_during_inference_abstains(self):
        self.move('nfl',24);self.d['snapshot']['fixture']=False
        first=pd.Timestamp(self.d['fixture_now']).to_pydatetime()
        after=(pd.Timestamp(self.d['fixture_now'])+pd.Timedelta(seconds=1)).to_pydatetime()
        with mock.patch('prospective.datetime') as clock:
            clock.now.side_effect=[first]+[after]*6
            r,a=issue_forecasts(self.d['frame'],self.d['canonical'],self.d['contracts'],self.d['models'],self.d['snapshot'])
        self.assertTrue(all(x['status']=='abstained' and 'issue_deadline_passed' in x['reasons'] and x['prediction'] is None for x in r if x['track']=='nfl'))
    def test_crash_recovery_replays_durable_batch(self):
        r,_=self.issue()
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger';pending=pathlib.Path(td)/'pending.json';pending.write_text(json.dumps(r))
            append_records(p,r) # crash before outer stage commit
            self.d['fixture_now']='2030-01-03T00:05:00Z'
            new,_=self.issue();self.assertNotEqual(new[0]['issued_at'],r[0]['issued_at'])
            recovered=json.loads(pending.read_text());a=append_records(p,recovered)
            self.assertEqual(a['appended'],0);self.assertEqual(a['reused'],6)
            with self.assertRaisesRegex(ValueError,'Conflicting immutable'):append_records(p,new)
    def test_interrupted_atomic_ledger_publish_preserves_prefix(self):
        r,_=self.issue()
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'ledger';append_records(p,r[:3]);before=p.read_bytes()
            with mock.patch('prospective.os.replace',side_effect=OSError('injected atomic publish failure')):
                with self.assertRaises(OSError):append_records(p,r[3:])
            self.assertEqual(p.read_bytes(),before)
            a=append_records(p,r);self.assertEqual(a['total'],6);self.assertEqual(a['reused'],3)

if __name__=='__main__':unittest.main()
