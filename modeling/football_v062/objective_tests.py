"""Offline V062 objective adapter checks: exactly four tiny synthetic fits.

One repeated margin pair uses the default 200-round ceiling; one repeated total
pair uses a recorded 8-round fixture override. All remaining fit calls are rejected
before native training or mock the native estimator. No real data is loaded.
"""
import copy
import io
import unittest
from unittest import mock

import joblib
import numpy as np
import pandas as pd

if __package__:
    from . import objective_model as model
else:
    import objective_model as model


# Deliberately declared independently of the candidate's configuration constant.
EXPECTED_V060_L2 = {
    'n_estimators': 200, 'learning_rate': .03, 'max_depth': 3, 'num_leaves': 7,
    'min_child_samples': 30, 'max_bin': 63, 'reg_lambda': 10., 'reg_alpha': 0.,
    'subsample': 1., 'subsample_freq': 0, 'colsample_bytree': 1.,
    'deterministic': True, 'force_col_wise': True, 'device_type': 'cpu',
    'random_state': 6001, 'n_jobs': 2, 'verbosity': -1,
    'data_random_seed': 6001, 'feature_fraction_seed': 6001,
    'bagging_seed': 6001, 'drop_seed': 6001, 'objective': 'regression_l2',
}


class ObjectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(6001)
        cls.X = pd.DataFrame(rng.normal(size=(160, 16)), columns=[f'x{i}' for i in range(16)])
        cls.X['x0'] = np.linspace(-2., 2., len(cls.X))
        cls.y = {
            'margin': (7. + 5.*cls.X.x0 - 2.*cls.X.x1).to_numpy(),
            'total': (45. + 5.*cls.X.x0 + 2.*cls.X.x1).to_numpy(),
        }
        cls.bundles = {}; cls.events = {}; cls.native_calls = []
        import lightgbm
        original_fit = lightgbm.LGBMRegressor.fit

        def observed_fit(estimator, *args, **kwargs):
            cls.native_calls.append((np.asarray(args[0]).copy(), np.asarray(args[1]).copy(), kwargs.copy()))
            return original_fit(estimator, *args, **kwargs)

        with mock.patch.object(lightgbm.LGBMRegressor, 'fit', new=observed_fit):
            for task in ('margin', 'total'):
                for repeat in (0, 1):
                    events = []
                    cls.bundles[(task, repeat)] = model.fit_model(
                        cls.X, cls.y[task], task,
                        progress=lambda done, total: events.append((done, total)),
                        iterations=None if task == 'margin' else 8)
                    cls.events[(task, repeat)] = events

    def test_exactly_four_synthetic_native_fits(self):
        self.assertEqual(len(self.native_calls), 4)
        self.assertEqual(set(self.bundles), {(task, rep) for task in ('margin', 'total') for rep in (0, 1)})

    def test_independent_v060_control_config(self):
        for task in model.TASKS:
            self.assertEqual(model.control_config(task), EXPECTED_V060_L2)

    def test_only_production_config_change_is_objective(self):
        for task in model.TASKS:
            candidate = model.config_for(task)
            self.assertEqual(set(candidate), set(EXPECTED_V060_L2))
            self.assertEqual({k for k in candidate if candidate[k] != EXPECTED_V060_L2[k]}, {'objective'})
            self.assertEqual(candidate['objective'], 'regression_l1')

    def test_frozen_all_seeds_cpu_threads_and_version(self):
        self.assertEqual(model.SEED, 6001)
        for bundle in self.bundles.values():
            self.assertEqual(bundle['package_version'], '4.7.0')
            for key in ('random_state', 'data_random_seed', 'feature_fraction_seed', 'bagging_seed', 'drop_seed'):
                self.assertEqual(bundle['config'][key], 6001)
            self.assertEqual(bundle['config']['n_jobs'], 2)
            self.assertEqual(bundle['config']['device_type'], 'cpu')

    def test_repeat_fits_are_identical(self):
        for task in model.TASKS:
            a, b = self.bundles[(task, 0)], self.bundles[(task, 1)]
            np.testing.assert_array_equal(model.predict_model(a, self.X), model.predict_model(b, self.X))
            self.assertEqual(a['estimator'].booster_.model_to_string(), b['estimator'].booster_.model_to_string())

    def test_two_full_round_and_two_fixture_fits(self):
        for (task, _), bundle in self.bundles.items():
            total = 200 if task == 'margin' else 8
            self.assertEqual(bundle['iterations_planned'], total)
            self.assertEqual(bundle['iterations_completed'], total)
            self.assertEqual(bundle['fixture_iterations_override'], None if task == 'margin' else 8)
            self.assertFalse(bundle['no_more_splits_stop'])

    def test_progress_start_end_not_retained(self):
        for key, bundle in self.bundles.items():
            planned = bundle['iterations_planned']
            self.assertEqual(self.events[key], [(0, planned), (planned, planned)])
            self.assertNotIn('progress', bundle)

    def test_native_fit_sees_training_only_no_extra_arguments(self):
        for i, (X, y, kwargs) in enumerate(self.native_calls):
            np.testing.assert_array_equal(X, self.X.to_numpy())
            np.testing.assert_array_equal(y, self.y['margin' if i < 2 else 'total'])
            self.assertEqual(kwargs, {})

    def test_no_transform_or_heldout_early_stop(self):
        for bundle in self.bundles.values():
            self.assertIsNone(bundle['x_scaler']); self.assertIsNone(bundle['y_scaler'])
            self.assertFalse(bundle['target_scaling_used'])
            self.assertFalse(bundle['validation_split_used']); self.assertFalse(bundle['early_stopping_used'])
            self.assertTrue(bundle['training_order_preserved'])
            self.assertNotIn('early_stopping_rounds', bundle['config'])
            self.assertNotIn('eval_set', bundle['config'])
            self.assertEqual(bundle['target_functional'], 'conditional_median')

    def test_finite_aligned_native_predictions_in_point_units(self):
        for (task, _), bundle in self.bundles.items():
            actual = model.predict_model(bundle, self.X)
            self.assertEqual(actual.shape, (160,)); self.assertTrue(np.isfinite(actual).all())
            expected = bundle['estimator'].predict(self.X.to_numpy())
            np.testing.assert_array_equal(actual, expected)
            self.assertGreater(np.std(actual), 0.)
            if task == 'total': self.assertTrue(30. < actual.mean() < 60.)
            else: self.assertGreater(actual.max(), 1.)

    def test_prediction_preserves_row_order_and_model_state(self):
        for bundle in self.bundles.values():
            before = bundle['estimator'].booster_.model_to_string()
            expected = model.predict_model(bundle, self.X)[::-1]
            np.testing.assert_array_equal(model.predict_model(bundle, self.X.iloc[::-1]), expected)
            model.predict_model(bundle, self.X + 1000.)
            self.assertEqual(bundle['estimator'].booster_.model_to_string(), before)

    def test_serialization_roundtrip_locally_trained_only(self):
        for bundle in self.bundles.values():
            stream = io.BytesIO(); joblib.dump(bundle, stream); stream.seek(0)
            restored = joblib.load(stream)
            np.testing.assert_array_equal(model.predict_model(restored, self.X), model.predict_model(bundle, self.X))

    def test_config_copies_are_independent(self):
        a = model.config_for('margin'); a['max_depth'] = 99
        b = model.control_config('total'); b['objective'] = 'changed'
        self.assertEqual(model.config_for('margin')['max_depth'], 3)
        self.assertEqual(model.control_config('total'), EXPECTED_V060_L2)

    def test_invalid_tasks_including_win_rejected_before_native_fit(self):
        with mock.patch('lightgbm.LGBMRegressor.fit') as native:
            for task in ('win', 'bad', None):
                with self.assertRaises(ValueError): model.fit_model(self.X, self.y['margin'], task)
                with self.assertRaises(ValueError): model.config_for(task)
                with self.assertRaises(ValueError): model.control_config(task)
            native.assert_not_called()

    def test_invalid_fixture_iteration_override_rejected_before_native_fit(self):
        with mock.patch('lightgbm.LGBMRegressor.fit') as native:
            for iterations in (True, np.bool_(True), 0, -1, 201, 1.5, '8'):
                with self.assertRaises(ValueError): model.config_for('margin', iterations)
                with self.assertRaises(ValueError): model.fit_model(self.X, self.y['margin'], 'margin', iterations=iterations)
            native.assert_not_called()

    def test_invalid_inputs_rejected_before_native_fit(self):
        bad = self.X.copy(); bad.iloc[0, 0] = np.nan
        infinite = self.X.copy(); infinite.iloc[0, 0] = np.inf
        cases = [(bad, self.y['margin']), (infinite, self.y['margin']),
                 (self.X, np.full(160, np.nan)), (self.X, np.full(160, np.inf)),
                 (self.X, self.y['margin'][:-1]), (self.X, self.y['margin'][:, None]),
                 (self.X.iloc[:0], np.array([])), (self.X.iloc[:1], np.array([1.])),
                 (self.X.iloc[:, :0], self.y['margin']), (np.ones(160), self.y['margin']),
                 ([['bad']] * 160, self.y['margin']), (self.X, ['bad'] * 160)]
        with mock.patch('lightgbm.LGBMRegressor.fit') as native:
            for X, y in cases:
                with self.assertRaises(ValueError): model.fit_model(X, y, 'margin')
            native.assert_not_called()

    def test_duplicate_nonstring_feature_names_rejected(self):
        for columns in (['same'] * 16, list(range(16))):
            bad = self.X.copy(); bad.columns = columns
            with self.assertRaises(ValueError): model.fit_model(bad, self.y['margin'], 'margin')
            with self.assertRaises(ValueError): model.predict_model(self.bundles[('margin', 0)], bad)

    def test_prediction_feature_width_order_rejected(self):
        bundle = self.bundles[('margin', 0)]
        with self.assertRaises(ValueError): model.predict_model(bundle, self.X.iloc[:, :-1])
        with self.assertRaises(ValueError): model.predict_model(bundle, self.X[self.X.columns[::-1]])

    def test_input_validation_copies_without_mutation_or_reordering(self):
        source, target = self.X.copy(deep=True), self.y['margin'].copy()
        arr, labels, names = model._training(source, target, 'margin')
        np.testing.assert_array_equal(arr, self.X.to_numpy())
        np.testing.assert_array_equal(labels, target)
        self.assertEqual(names, list(self.X.columns))
        arr[0, 0] = 999.; labels[0] = 999.
        pd.testing.assert_frame_equal(source, self.X)
        np.testing.assert_array_equal(target, self.y['margin'])

    def test_pinned_distribution_and_import_versions_enforced(self):
        with mock.patch('lightgbm.LGBMRegressor.fit') as native:
            with mock.patch.object(model.importlib.metadata, 'version', return_value='0.0'):
                with self.assertRaisesRegex(RuntimeError, 'version mismatch'):
                    model.fit_model(self.X, self.y['margin'], 'margin')
            with mock.patch('lightgbm.__version__', '0.0'):
                with self.assertRaisesRegex(RuntimeError, 'Imported LightGBM'):
                    model.fit_model(self.X, self.y['margin'], 'margin')
            native.assert_not_called()

    def test_callback_denial_and_noncallable_prevent_native_fit(self):
        def denied(done, total): raise RuntimeError('synthetic budget denial')
        with mock.patch('lightgbm.LGBMRegressor.fit') as native:
            with self.assertRaisesRegex(RuntimeError, 'synthetic budget denial'):
                model.fit_model(self.X, self.y['margin'], 'margin', progress=denied)
            with self.assertRaises(ValueError): model.fit_model(self.X, self.y['margin'], 'margin', progress='bad')
            native.assert_not_called()

    def test_bad_bundle_metadata_rejected(self):
        original = self.bundles[('margin', 0)]
        for key, value in (('family', 'xgb'), ('task', 'win'), ('package_version', '0.0'),
                           ('x_scaler', object()), ('y_scaler', object()),
                           ('config', {'objective': 'regression_l2'})):
            bundle = dict(original); bundle[key] = value
            with self.assertRaises(ValueError): model.predict_model(bundle, self.X)

    def test_bad_native_predictions_rejected(self):
        bundle = self.bundles[('margin', 0)]
        for output in (np.full(160, np.nan), np.full(160, np.inf), np.ones(159), np.ones((160, 1))):
            with mock.patch.object(bundle['estimator'], 'predict', return_value=output):
                with self.assertRaises(ValueError): model.predict_model(bundle, self.X)


if __name__ == '__main__':
    unittest.main()
