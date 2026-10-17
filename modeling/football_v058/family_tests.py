"""Exactly four synthetic family smoke fits; all other tests reuse those fits."""
import copy,io,unittest
from unittest import mock
import joblib
import numpy as np
import pandas as pd
from families import fit_model,predict_model,HGB_CONFIG,MLP_CONFIG,MLP_EPOCHS,SEED


class FamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng=np.random.default_rng(9107)
        cls.X=rng.normal(size=(128,6))*np.array([1,2,3,4,5,6])+np.array([20,30,40,50,60,70])
        z=(cls.X-cls.X.mean(axis=0))/cls.X.std(axis=0)
        cls.y_win=(z[:,0]+.7*z[:,1]-.3*z[:,2]>0).astype(float)
        cls.y_reg=42+7*z[:,0]-4*z[:,1]+2*z[:,2]**2
        cls.X_test=cls.X[:15]+3.1
        cls.bundles={};cls.progress={}
        for family,task in [('hgb','win'),('hgb','margin'),('mlp','win'),('mlp','total')]:
            events=[]
            cls.bundles[(family,task)]=fit_model(cls.X,cls.y_win if task=='win' else cls.y_reg,task,family,progress=lambda a,b:events.append((a,b)),epochs=41 if family=='mlp' and task=='win' else None)
            cls.progress[(family,task)]=events
        cls.smoke_fits=4
    def test_exactly_four_smoke_fits(self):
        self.assertEqual(self.smoke_fits,4);self.assertEqual(len(self.bundles),4)
    def test_direct_estimator_prediction_parity(self):
        for b in self.bundles.values():
            X=b['x_scaler'].transform(self.X_test) if b['x_scaler'] is not None else self.X_test
            direct=b['estimator'].predict_proba(X)[:,1] if b['task']=='win' else b['estimator'].predict(X)
            if b['y_scaler'] is not None:direct=b['y_scaler'].inverse_transform(direct.reshape(-1,1)).ravel()
            if b['task']=='win':direct=np.clip(direct,1e-7,1-1e-7)
            np.testing.assert_allclose(predict_model(b,self.X_test),direct,rtol=1e-12,atol=1e-12)
    def test_pinned_seed_and_repeated_prediction(self):
        for b in self.bundles.values():
            self.assertEqual(b['estimator'].random_state,SEED)
            a=predict_model(b,self.X_test);c=predict_model(b,self.X_test)
            np.testing.assert_array_equal(a,c)
    def test_training_only_x_scaling(self):
        for key,b in self.bundles.items():
            if key[0]=='mlp':
                np.testing.assert_allclose(b['x_scaler'].mean_,self.X.mean(axis=0));self.assertEqual(b['x_scaler'].n_samples_seen_,128)
                before=b['x_scaler'].mean_.copy();predict_model(b,self.X_test+10000)
                np.testing.assert_array_equal(before,b['x_scaler'].mean_)
            else:self.assertIsNone(b['x_scaler'])
    def test_training_only_target_scaling_and_restore(self):
        b=self.bundles[('mlp','total')]
        self.assertAlmostEqual(b['y_scaler'].mean_[0],self.y_reg.mean());self.assertAlmostEqual(b['y_scaler'].scale_[0],self.y_reg.std())
        scaled=b['estimator'].predict(b['x_scaler'].transform(self.X_test))
        expected=scaled*self.y_reg.std()+self.y_reg.mean()
        np.testing.assert_allclose(predict_model(b,self.X_test),expected)
        self.assertIsNone(self.bundles[('mlp','win')]['y_scaler'])
    def test_probabilities_and_regression_finite(self):
        for b in self.bundles.values():
            p=predict_model(b,self.X_test);self.assertTrue(np.isfinite(p).all())
            if b['task']=='win':self.assertTrue(((p>=1e-7)&(p<=1-1e-7)).all())
    def test_fixed_hgb_parameters(self):
        for key,b in self.bundles.items():
            if key[0]=='hgb':
                for k,v in HGB_CONFIG.items():self.assertEqual(b['estimator'].get_params()[k],v)
                self.assertEqual(b['estimator'].n_iter_,100)
    def test_mlp_architecture_and_epoch_accounting(self):
        for key,b in self.bundles.items():
            if key[0]=='mlp':
                m=b['estimator'];self.assertEqual([w.shape for w in m.coefs_],[(6,32),(32,16),(16,1)])
                self.assertEqual(sum(w.size for w in m.coefs_)+sum(v.size for v in m.intercepts_),32*6+577)
                expected=41 if key[1]=='win' else 200
                self.assertEqual(m.t_,expected*128);self.assertEqual(b['epochs_completed'],expected)
                for k,v in MLP_CONFIG.items():self.assertEqual(m.get_params()[k],v)
    def test_no_random_validation_or_early_stop(self):
        for b in self.bundles.values():
            self.assertFalse(b['validation_split_used']);self.assertFalse(b['estimator'].early_stopping)
            if b['family']=='mlp':self.assertIsNone(b['estimator'].validation_scores_)
    def test_progress_boundaries(self):
        self.assertEqual(self.progress[('mlp','win')],[(0,41),(20,41),(40,41),(41,41)])
        self.assertEqual(self.progress[('hgb','win')],[(0,100),(100,100)])
    def test_runtime_default_200_epochs_without_fitting(self):
        # A recording estimator verifies the control loop, not a fifth model fit.
        class Recorder:
            def __init__(self,**kwargs):self.t_=0
            def partial_fit(self,X,y):self.t_+=len(X)
            def predict(self,X):return np.zeros(len(X))
        with mock.patch('families.MLPRegressor',Recorder):
            b=fit_model(self.X,self.y_reg,'total','mlp')
        self.assertEqual(MLP_EPOCHS,200);self.assertEqual(b['epochs_completed'],200);self.assertEqual(b['estimator'].t_,200*128);self.assertIsNone(b['fixture_epochs_override'])
    def test_expected_width_rejected(self):
        for b in self.bundles.values():
            with self.assertRaisesRegex(ValueError,'width'):predict_model(b,self.X_test[:,:5])
    def test_feature_names_and_order_rejected(self):
        b=dict(self.bundles[('hgb','win')],feature_names=list('abcdef'))
        np.testing.assert_array_equal(predict_model(b,pd.DataFrame(self.X_test,columns=list('abcdef'))),predict_model(b,self.X_test))
        with self.assertRaisesRegex(ValueError,'names/order'):predict_model(b,pd.DataFrame(self.X_test,columns=list('bacdef')))
    def test_invalid_training_data_rejected_before_fit(self):
        invalid=[(self.X,np.full(128,np.nan),'win','mlp',None),(self.X,np.ones(128),'win','mlp',None),(self.X,np.ones(127),'total','hgb',None),(np.full((128,6),np.inf),self.y_reg,'total','hgb',None),(self.X,self.y_reg,'wrong','hgb',None),(self.X,self.y_reg,'total','wrong',None),(self.X,self.y_reg,'total','hgb',2),(self.X,self.y_reg,'total','mlp',0),(self.X,self.y_reg,'total','mlp',True),(self.X,self.y_reg,'total','mlp',201)]
        for X,y,t,f,e in invalid:
            with self.assertRaises(ValueError):fit_model(X,y,t,f,epochs=e)
    def test_invalid_prediction_data_rejected(self):
        for X in [np.full((2,6),np.nan),np.ones(6),np.empty((0,6))]:
            with self.assertRaises(ValueError):predict_model(self.bundles[('mlp','win')],X)
    def test_progress_exception_propagates_before_fit(self):
        def stop(*args):raise RuntimeError('owner_budget_stop')
        with self.assertRaisesRegex(RuntimeError,'owner_budget_stop'):
            fit_model(self.X,self.y_reg,'total','hgb',progress=stop)
    def test_local_joblib_round_trip(self):
        for b in self.bundles.values():
            stream=io.BytesIO();joblib.dump(b,stream);stream.seek(0);loaded=joblib.load(stream)
            np.testing.assert_array_equal(predict_model(b,self.X_test),predict_model(loaded,self.X_test))
    def test_prediction_does_not_mutate_inputs(self):
        X=self.X_test.copy()
        for b in self.bundles.values():predict_model(b,X)
        np.testing.assert_array_equal(X,self.X_test)


if __name__=='__main__':unittest.main(verbosity=2)
