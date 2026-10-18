"""V062 frozen LightGBM median point forecasts; no acquisition or evaluation fit.

The candidate differs from the V060 LightGBM regression control in one configured
value: ``objective='regression_l1'`` replaces ``'regression_l2'``. All V060 seeds,
tree settings, the native package version, and the 200-round ceiling are retained.
Neither inputs nor targets are standardized. The caller supplies chronological,
eligible training rows and owns cutoff checks, cached-control pairing and budgets.

An explicit ``iterations`` argument is a recorded synthetic-fixture-only override;
production callers must leave it null. No held-out data, early stopping, tuning,
network access or native dependency installation occurs here. Native LightGBM may
stop adding trees if there are no permitted splits; actual tree count is recorded.
L1 fitting targets a conditional median, not a mean, probability or full density.
"""
import copy
import importlib.metadata

import numpy as np
from threadpoolctl import threadpool_limits

TASKS = ('margin', 'total')
FAMILY = 'lgbm'
SEED = 6001
MAX_ITERATIONS = 200
PINNED_DEPENDENCIES = {'lightgbm': '4.7.0'}
LGBM_CONFIG = dict(n_estimators=MAX_ITERATIONS, learning_rate=.03, max_depth=3,
    num_leaves=7, min_child_samples=30, max_bin=63, reg_lambda=10., reg_alpha=0.,
    subsample=1., subsample_freq=0, colsample_bytree=1., deterministic=True,
    force_col_wise=True, device_type='cpu', random_state=SEED, n_jobs=2,
    verbosity=-1, data_random_seed=SEED, feature_fraction_seed=SEED,
    bagging_seed=SEED, drop_seed=SEED)
PRIMARY_REFERENCES = [
    'https://arxiv.org/html/0912.0902v2',
    'https://lightgbm.readthedocs.io/en/stable/Parameters.html',
]


def _options(task, iterations=None):
    if task not in TASKS:
        raise ValueError('V062 supports only margin and total point forecasts')
    if iterations is not None and (isinstance(iterations, (bool, np.bool_))
            or not isinstance(iterations, (int, np.integer))
            or not 1 <= iterations <= MAX_ITERATIONS):
        raise ValueError('iterations must be a synthetic fixture integer in [1,200]')
    return MAX_ITERATIONS if iterations is None else int(iterations)


def control_config(task):
    """Return the exact frozen V060 L2 configuration; never fit the control here."""
    _options(task)
    conf = copy.deepcopy(LGBM_CONFIG)
    conf['objective'] = 'regression_l2'
    return conf


def config_for(task, iterations=None):
    total = _options(task, iterations)
    conf = control_config(task)
    conf.update(n_estimators=total, objective='regression_l1')
    return conf


def _matrix(X):
    names = list(X.columns) if hasattr(X, 'columns') else None
    if names is not None and (len(set(names)) != len(names)
            or any(not isinstance(name, str) for name in names)):
        raise ValueError('Feature names must be unique strings')
    try:
        arr = np.asarray(X, dtype=np.float64).copy(order='C')
    except (ValueError, TypeError) as exc:
        raise ValueError('X must be a finite numeric matrix') from exc
    if arr.ndim != 2 or min(arr.shape) < 1 or not np.isfinite(arr).all():
        raise ValueError('X must be a nonempty finite two-dimensional matrix')
    return arr, names


def _training(X, y, task, iterations=None):
    _options(task, iterations)
    arr, names = _matrix(X)
    try:
        target = np.asarray(y, dtype=np.float64).copy()
    except (ValueError, TypeError) as exc:
        raise ValueError('y must be a finite aligned vector') from exc
    if target.ndim != 1 or len(target) != len(arr) or len(target) < 2 or not np.isfinite(target).all():
        raise ValueError('y must be a finite aligned vector with at least two rows')
    return arr, target, names


def _version():
    expected = PINNED_DEPENDENCIES['lightgbm']
    actual = importlib.metadata.version('lightgbm')
    if actual != expected:
        raise RuntimeError(f'LightGBM version mismatch: expected {expected}, found {actual}')
    import lightgbm
    if lightgbm.__version__ != expected:
        raise RuntimeError('Imported LightGBM differs from the pinned distribution version')
    return actual


def fit_model(X, y, task, progress=None, iterations=None):
    """Perform exactly one native fit with training data only and return its bundle.

    ``progress(done, planned)`` is called before and after the native fit. The
    callback is not retained; the caller maintains its own concurrent heartbeat.
    A callback denial before training prevents that fit.
    """
    arr, target, names = _training(X, y, task, iterations)
    if progress is not None and not callable(progress):
        raise ValueError('progress must be callable')
    version = _version()
    from lightgbm import LGBMRegressor
    conf = config_for(task, iterations)
    planned = conf['n_estimators']
    notify = progress if progress is not None else lambda done, total: None
    estimator = LGBMRegressor(**conf)
    notify(0, planned)
    with threadpool_limits(limits=2):
        estimator.fit(arr, target)
    actual = int(estimator.booster_.current_iteration())
    if not 1 <= actual <= planned:
        raise RuntimeError('Native tree count lies outside the fixed training budget')
    notify(planned, planned)
    bundle = dict(family=FAMILY, task=task, estimator=estimator, x_scaler=None,
        y_scaler=None, n_features=arr.shape[1], feature_names=names,
        training_rows=len(arr), config=conf, iterations_planned=planned,
        iterations_completed=actual, fixture_iterations_override=iterations,
        validation_split_used=False, early_stopping_used=False,
        training_order_preserved=True, target_scaling_used=False,
        package_version=version, target_functional='conditional_median',
        architecture={'kind': FAMILY, 'max_depth': 3, 'fixed_round_ceiling': planned},
        no_more_splits_stop=bool(actual < planned))
    predict_model(bundle, X)
    return bundle


def predict_model(bundle, X):
    """Return finite predictions in original point units and input row order."""
    arr, names = _matrix(X)
    if bundle.get('family') != FAMILY or bundle.get('task') not in TASKS:
        raise ValueError('Invalid V062 family/task bundle')
    if bundle.get('package_version') != PINNED_DEPENDENCIES['lightgbm']:
        raise ValueError('Bundle does not use the pinned LightGBM version')
    if bundle.get('config', {}).get('objective') != 'regression_l1':
        raise ValueError('Bundle does not use the frozen L1 objective')
    if bundle.get('x_scaler') is not None or bundle.get('y_scaler') is not None:
        raise ValueError('V062 does not permit input or target transformations')
    if arr.shape[1] != bundle.get('n_features'):
        raise ValueError('Prediction feature width differs from training')
    if names is not None and bundle.get('feature_names') is not None and names != bundle['feature_names']:
        raise ValueError('Prediction feature names/order differ from training')
    with threadpool_limits(limits=2):
        pr = np.asarray(bundle['estimator'].predict(arr), dtype=float)
    if pr.ndim != 1 or len(pr) != len(arr) or not np.isfinite(pr).all():
        raise ValueError('Model returned nonfinite or misaligned predictions')
    return pr
