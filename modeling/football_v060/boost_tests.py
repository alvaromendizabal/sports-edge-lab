"""Offline V060 adapter checks: exactly twelve small synthetic training fits.

Four families x three targets are fitted once in setUpClass and reused. Each
booster win fixture exercises the full production 200-round ceiling. Regression
fixtures use an explicitly recorded 8-round override. No real data is loaded.
"""
import copy
import io
import unittest
from unittest import mock
import joblib
import numpy as np
import pandas as pd
if __package__:
    from boost_families import (FAMILIES, TASKS, MAX_ITERATIONS, SEED, config_for,
                                fit_model, predict_model, _training)
else:
    from boost_families import (FAMILIES, TASKS, MAX_ITERATIONS, SEED, config_for,
                               fit_model, predict_model, _training)


class BoostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(6001)
        cls.X = pd.DataFrame(rng.normal(size=(128, 16)), columns=[f'x{i}' for i in range(16)])
        cls.X['x0'] = np.linspace(-2., 2., 128)
        cls.y = {'win': ((cls.X.x0 + .4*cls.X.x1) > 0).astype(float).to_numpy(),
                 'margin': (7. + 5.*cls.X.x0 - 2.*cls.X.x1).to_numpy(),
                 'total': (45. + 5.*cls.X.x0 + 2.*cls.X.x1).to_numpy()}
        cls.bundles = {}; cls.events = {}; cls.fit_count = 0
        for family in FAMILIES:
            for task in TASKS:
                events = []
                override = None if task == 'win' or family == 'linear' else 8
                cls.bundles[(family, task)] = fit_model(cls.X, cls.y[task], task, family,
                    progress=lambda done, total: events.append((done, total)), iterations=override)
                cls.events[(family, task)] = events
                cls.fit_count += 1

    def test_exact_twelve_smoke_fits(self):
        self.assertEqual(self.fit_count, 12)
        self.assertEqual(set(self.bundles), {(f,t) for f in FAMILIES for t in TASKS})

    def test_finite_aligned_predictions_all_tasks(self):
        for bundle in self.bundles.values():
            pr = predict_model(bundle, self.X)
            self.assertEqual(pr.shape, (128,))
            self.assertTrue(np.isfinite(pr).all())

    def test_probabilities_clipped(self):
        extreme = self.X.copy()*10000.
        for family in FAMILIES:
            pr = predict_model(self.bundles[(family,'win')], extreme)
            self.assertTrue(((pr >= 1e-7) & (pr <= 1-1e-7)).all())

    def test_heldout_prediction_does_not_refit_scaler(self):
        for task in TASKS:
            bundle = self.bundles[('linear',task)]
            scaler = bundle['x_scaler']; before = scaler.mean_.copy()
            np.testing.assert_allclose(before, self.X.mean().to_numpy(), atol=1e-12)
            predict_model(bundle, self.X+1000.)
            np.testing.assert_array_equal(scaler.mean_, before)
            self.assertEqual(int(scaler.n_samples_seen_), len(self.X))

    def test_tree_inputs_and_targets_are_unscaled(self):
        for (family, task), bundle in self.bundles.items():
            self.assertIsNone(bundle['y_scaler'])
            self.assertFalse(bundle['target_scaling_used'])
            if family != 'linear': self.assertIsNone(bundle['x_scaler'])

    def test_regression_predictions_remain_in_points(self):
        for family in FAMILIES:
            pr = predict_model(self.bundles[(family,'total')], self.X)
            self.assertTrue(30. < pr.mean() < 60.)
            self.assertGreater(np.std(pr), 0.)

    def test_native_prediction_parity(self):
        for (family,task), bundle in self.bundles.items():
            x = self.X.to_numpy()
            if bundle['x_scaler'] is not None: x = bundle['x_scaler'].transform(x)
            estimator = bundle['estimator']
            native = estimator.predict_proba(x)[:,1] if task == 'win' else estimator.predict(x)
            if task == 'win': native = np.clip(native,1e-7,1-1e-7)
            np.testing.assert_allclose(predict_model(bundle,self.X),np.asarray(native).reshape(-1),atol=1e-12,rtol=1e-12)

    def test_repeated_prediction_is_identical(self):
        for bundle in self.bundles.values():
            np.testing.assert_array_equal(predict_model(bundle,self.X),predict_model(bundle,self.X))

    def test_serialization_round_trip_locally_trained_only(self):
        for bundle in self.bundles.values():
            memory = io.BytesIO(); joblib.dump(bundle,memory); memory.seek(0)
            restored = joblib.load(memory)
            np.testing.assert_allclose(predict_model(restored,self.X),predict_model(bundle,self.X),atol=1e-12,rtol=1e-12)

    def test_runtime_round_ceiling_and_fixture_override(self):
        for (family,task), bundle in self.bundles.items():
            if family == 'linear':
                self.assertIsNone(bundle['iterations_completed'])
                self.assertIsNone(bundle['fixture_iterations_override'])
            else:
                expected = MAX_ITERATIONS if task == 'win' else 8
                self.assertEqual(bundle['iterations_planned'],expected)
                self.assertTrue(1 <= bundle['iterations_completed'] <= expected)
                if family != 'lgbm': self.assertEqual(bundle['iterations_completed'],expected)
                self.assertEqual(bundle['fixture_iterations_override'],None if task == 'win' else 8)

    def test_progress_start_end(self):
        for key, bundle in self.bundles.items():
            total = bundle['iterations_planned']
            self.assertEqual(self.events[key],[(0,total),(total,total)])

    def test_no_validation_or_early_stopping(self):
        for bundle in self.bundles.values():
            self.assertFalse(bundle['validation_split_used']); self.assertFalse(bundle['early_stopping_used'])
            self.assertNotIn('early_stopping_rounds',bundle['config'])
            self.assertNotIn('eval_set',bundle['config'])

    def test_cpu_two_threads_and_frozen_seeds(self):
        for family in FAMILIES[:3]:
            conf = self.bundles[(family,'win')]['config']
            self.assertEqual(conf.get('random_state',conf.get('random_seed')),SEED)
            self.assertEqual(conf.get('n_jobs',conf.get('thread_count')),2)
        self.assertEqual(config_for('win','xgb')['device'],'cpu')
        self.assertEqual(config_for('win','lgbm')['device_type'],'cpu')
        self.assertEqual(config_for('win','catboost')['task_type'],'CPU')

    def test_catboost_ordered_no_external_files(self):
        conf = self.bundles[('catboost','win')]['estimator'].get_params()
        self.assertEqual(conf['boosting_type'],'Ordered'); self.assertTrue(conf['has_time'])
        self.assertFalse(conf['allow_writing_files']); self.assertFalse(conf['use_best_model'])
        self.assertEqual(conf['bootstrap_type'],'No'); self.assertEqual(conf['random_strength'],0.)

    def test_lightgbm_deterministic_histogram_and_no_bagging(self):
        conf = config_for('win','lgbm')
        self.assertTrue(conf['deterministic']); self.assertTrue(conf['force_col_wise'])
        self.assertEqual(conf['subsample_freq'],0); self.assertEqual(conf['colsample_bytree'],1.)

    def test_configs_are_independent_copies(self):
        conf = config_for('win','xgb'); conf['max_depth']=999
        self.assertEqual(config_for('win','xgb')['max_depth'],3)
        self.assertEqual(config_for('win','xgb')['min_child_weight'],7.5)
        self.assertEqual(config_for('margin','xgb')['min_child_weight'],30.)

    def test_linear_matches_requested_hyperparameters(self):
        self.assertEqual(config_for('win','linear')['C'],1.)
        self.assertEqual(config_for('win','linear')['max_iter'],1000)
        self.assertEqual(config_for('margin','linear')['alpha'],20.)
        self.assertEqual(config_for('total','linear')['alpha'],20.)

    def test_rejects_feature_order_width_and_duplicate_names(self):
        for bundle in self.bundles.values():
            with self.assertRaises(ValueError): predict_model(bundle,self.X.iloc[:,:-1])
            with self.assertRaises(ValueError): predict_model(bundle,self.X[self.X.columns[::-1]])
        bad = self.X.copy(); bad.columns = ['same']*16
        with self.assertRaises(ValueError): predict_model(self.bundles[('xgb','win')],bad)

    def test_rejects_nonfinite_and_malformed_inputs_before_fit(self):
        bad = self.X.copy(); bad.iloc[0,0]=np.nan
        cases=[(bad,self.y['win']), (self.X,np.full(128,np.nan)), (self.X,self.y['win'][:-1]),
               (self.X.iloc[:0],np.array([])), (self.X,np.ones(128)), (self.X,np.full(128,.5))]
        for x,y in cases:
            with self.assertRaises(ValueError): fit_model(x,y,'win','xgb')
        with self.assertRaises(ValueError): fit_model(self.X,self.y['win'],'bad','xgb')
        with self.assertRaises(ValueError): fit_model(self.X,self.y['win'],'win','bad')

    def test_rejects_invalid_fixture_iteration_override(self):
        for it in (True,0,201,1.5,'8'):
            with self.assertRaises(ValueError): fit_model(self.X,self.y['win'],'win','xgb',iterations=it)
        with self.assertRaises(ValueError): fit_model(self.X,self.y['win'],'win','linear',iterations=8)

    def test_callback_denial_prevents_native_fit(self):
        def denied(done,total): raise RuntimeError('synthetic budget denial')
        with mock.patch('sklearn.linear_model.Ridge.fit') as native:
            with self.assertRaisesRegex(RuntimeError,'synthetic budget denial'):
                fit_model(self.X,self.y['margin'],'margin','linear',progress=denied)
            native.assert_not_called()

    def test_input_rows_not_reordered_or_mutated(self):
        source = self.X.copy(deep=True); target = self.y['margin'].copy()
        x,y,names = _training(source,target,'margin','catboost',8)
        np.testing.assert_array_equal(x,source.to_numpy()); np.testing.assert_array_equal(y,target)
        x[0,0]=999.; y[0]=999.
        pd.testing.assert_frame_equal(source,self.X)
        np.testing.assert_array_equal(target,self.y['margin'])

if __name__ == '__main__': unittest.main()
