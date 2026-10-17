"""Frozen V060 CPU boosting benchmark and its same-feature linear control.

All input rows must already be in chronological order; CatBoost preserves their
order with has_time=True. The caller owns train/evaluation separation, FBS-only
row eligibility, availability checks, and any exclusion of ties from win targets.
This module never chooses columns, derives labels, accesses network/data, or tunes
on evaluation data. Tree objectives are binary log loss and squared error.
The 200-round ceiling is predeclared, not chosen using a held-out set. LightGBM
may stop adding trees when no permitted split exists; that is recorded explicitly.

Numeric inputs are finite and preserve exact feature names/order. Only the linear
control standardizes X, using training rows alone. No model standardizes targets.
The packages implement different tree-growing mechanisms, not different signals;
there is no claim these fixed heuristic settings are optimal or profitable.
"""
import copy
import importlib.metadata
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

FAMILIES = ('xgb', 'lgbm', 'catboost', 'linear')
TASKS = ('win', 'margin', 'total')
SEED = 6001
MAX_ITERATIONS = 200
PINNED_DEPENDENCIES = {'xgboost-cpu': '3.4.1', 'lightgbm': '4.7.0', 'catboost': '1.2.10'}
XGB_CONFIG = dict(n_estimators=MAX_ITERATIONS, learning_rate=.03, max_depth=3,
    max_bin=63, reg_lambda=10., reg_alpha=0., subsample=1., colsample_bytree=1.,
    colsample_bylevel=1., colsample_bynode=1., tree_method='hist', device='cpu',
    random_state=SEED, n_jobs=2, verbosity=0, validate_parameters=True)
LGBM_CONFIG = dict(n_estimators=MAX_ITERATIONS, learning_rate=.03, max_depth=3,
    num_leaves=7, min_child_samples=30, max_bin=63, reg_lambda=10., reg_alpha=0.,
    subsample=1., subsample_freq=0, colsample_bytree=1., deterministic=True,
    force_col_wise=True, device_type='cpu', random_state=SEED, n_jobs=2,
    verbosity=-1, data_random_seed=SEED, feature_fraction_seed=SEED,
    bagging_seed=SEED, drop_seed=SEED)
CATBOOST_CONFIG = dict(iterations=MAX_ITERATIONS, learning_rate=.03, depth=3,
    border_count=63, l2_leaf_reg=10., boosting_type='Ordered', has_time=True,
    bootstrap_type='No', random_strength=0., leaf_estimation_iterations=1,
    use_best_model=False, allow_writing_files=False, random_seed=SEED,
    task_type='CPU', thread_count=2, verbose=False, nan_mode='Forbidden',
    grow_policy='SymmetricTree')
LINEAR_CONFIG = {'win': dict(C=1., max_iter=1000, solver='lbfgs', random_state=SEED),
                 'margin': dict(alpha=20.), 'total': dict(alpha=20.)}
PRIMARY_REFERENCES = [
    'https://xgboost.readthedocs.io/en/stable/parameter.html',
    'https://xgboost.readthedocs.io/en/stable/install.html',
    'https://lightgbm.readthedocs.io/en/stable/Parameters.html',
    'https://github.com/catboost/catboost/blob/master/catboost/docs/en/references/training-parameters/common.md',
]


def _matrix(X):
    names = list(X.columns) if hasattr(X, 'columns') else None
    if names is not None and (len(set(names)) != len(names) or any(not isinstance(x, str) for x in names)):
        raise ValueError('Feature names must be unique strings')
    try:
        arr = np.asarray(X, dtype=np.float64).copy(order='C')
    except (ValueError, TypeError) as exc:
        raise ValueError('X must be a finite numeric matrix') from exc
    if arr.ndim != 2 or min(arr.shape) < 1 or not np.isfinite(arr).all():
        raise ValueError('X must be a nonempty finite two-dimensional matrix')
    return arr, names


def _training(X, y, task, family, iterations):
    if task not in TASKS or family not in FAMILIES:
        raise ValueError('Unsupported task or family')
    if iterations is not None and (family == 'linear' or isinstance(iterations, (bool, np.bool_))
            or not isinstance(iterations, (int, np.integer)) or not 1 <= iterations <= MAX_ITERATIONS):
        raise ValueError('iterations must be an explicit booster fixture integer in [1,200]')
    arr, names = _matrix(X)
    try:
        target = np.asarray(y, dtype=np.float64).copy()
    except (ValueError, TypeError) as exc:
        raise ValueError('y must be a finite aligned vector') from exc
    if target.ndim != 1 or len(target) != len(arr) or len(target) < 2 or not np.isfinite(target).all():
        raise ValueError('y must be a finite aligned vector with at least two rows')
    if task == 'win' and set(np.unique(target)) != {0., 1.}:
        raise ValueError('Win training requires both classes 0 and 1; ties must be excluded by caller')
    return arr, target, names


def config_for(task, family, iterations=None):
    if task not in TASKS or family not in FAMILIES:
        raise ValueError('Unsupported task or family')
    total = MAX_ITERATIONS if iterations is None else int(iterations)
    if family == 'xgb':
        conf = copy.deepcopy(XGB_CONFIG)
        conf.update(n_estimators=total, objective='binary:logistic' if task == 'win' else 'reg:squarederror',
                    min_child_weight=7.5 if task == 'win' else 30.)
    elif family == 'lgbm':
        conf = copy.deepcopy(LGBM_CONFIG)
        conf.update(n_estimators=total, objective='binary' if task == 'win' else 'regression_l2')
    elif family == 'catboost':
        conf = copy.deepcopy(CATBOOST_CONFIG)
        conf.update(iterations=total, loss_function='Logloss' if task == 'win' else 'RMSE')
    else:
        conf = copy.deepcopy(LINEAR_CONFIG[task])
    return conf


def fit_model(X, y, task, family, progress=None, iterations=None):
    """Fit one frozen candidate on caller-supplied chronological training data.

    No evaluation set or early-stopping callback is supplied. ``iterations`` is
    a recorded fixture-only override; production callers must leave it null.
    Progress is emitted before and after one native fit; caller's independent
    heartbeat/budget monitor remains responsible while the native call runs.
    No user callback is retained in the returned serializable model bundle.
    """
    arr, target, names = _training(X, y, task, family, iterations)
    if progress is not None and not callable(progress):
        raise ValueError('progress must be callable')
    notify = progress if progress is not None else lambda done, total: None
    conf = config_for(task, family, iterations)
    scaler = None
    if family == 'xgb':
        from xgboost import XGBClassifier, XGBRegressor
        estimator = (XGBClassifier if task == 'win' else XGBRegressor)(**conf)
        package = 'xgboost-cpu'
    elif family == 'lgbm':
        from lightgbm import LGBMClassifier, LGBMRegressor
        estimator = (LGBMClassifier if task == 'win' else LGBMRegressor)(**conf)
        package = 'lightgbm'
    elif family == 'catboost':
        from catboost import CatBoostClassifier, CatBoostRegressor
        estimator = (CatBoostClassifier if task == 'win' else CatBoostRegressor)(**conf)
        package = 'catboost'
    else:
        estimator = (LogisticRegression if task == 'win' else Ridge)(**conf)
        package = 'scikit-learn'
        scaler = StandardScaler().fit(arr)
        arr = scaler.transform(arr)
    planned = 1 if family == 'linear' else (MAX_ITERATIONS if iterations is None else int(iterations))
    notify(0, planned)
    with threadpool_limits(limits=2):
        estimator.fit(arr, target)
    if family == 'xgb':
        actual = int(estimator.get_booster().num_boosted_rounds())
    elif family == 'lgbm':
        actual = int(estimator.booster_.current_iteration())
    elif family == 'catboost':
        actual = int(estimator.tree_count_)
    else:
        actual = None
    if actual is not None and not 1 <= actual <= planned:
        raise RuntimeError('Native tree count exceeds the fixed training budget')
    if family in ('xgb', 'catboost') and actual != planned:
        raise RuntimeError('Unexpected native truncation without an evaluation set')
    notify(planned, planned)
    bundle = dict(family=family, task=task, estimator=estimator, x_scaler=scaler,
        y_scaler=None, n_features=arr.shape[1], feature_names=names,
        training_rows=len(arr), config=conf, iterations_planned=planned,
        iterations_completed=actual, fixture_iterations_override=iterations,
        validation_split_used=False, early_stopping_used=False,
        training_order_preserved=True, target_scaling_used=False,
        package_version=importlib.metadata.version(package),
        architecture={'kind': family, 'max_depth': 3 if family != 'linear' else None,
                      'fixed_round_ceiling': planned if family != 'linear' else None},
        no_more_splits_stop=bool(family == 'lgbm' and actual < planned))
    predict_model(bundle, X)
    return bundle


def predict_model(bundle, X):
    """Predict without changing scaler state, weights, or input order."""
    arr, names = _matrix(X)
    if bundle.get('family') not in FAMILIES or bundle.get('task') not in TASKS:
        raise ValueError('Invalid family/task bundle')
    if arr.shape[1] != bundle.get('n_features'):
        raise ValueError('Prediction feature width differs from training')
    if names is not None and bundle.get('feature_names') is not None and names != bundle['feature_names']:
        raise ValueError('Prediction feature names/order differ from training')
    if bundle.get('x_scaler') is not None:
        arr = bundle['x_scaler'].transform(arr)
    with threadpool_limits(limits=2):
        if bundle['task'] == 'win':
            classes = np.asarray(bundle['estimator'].classes_)
            positive = np.flatnonzero(classes == 1)
            if len(positive) != 1:
                raise ValueError('Model has no unique positive win class')
            pr = np.asarray(bundle['estimator'].predict_proba(arr), dtype=float)[:, positive[0]]
        else:
            pr = np.asarray(bundle['estimator'].predict(arr), dtype=float).reshape(-1)
    if pr.ndim != 1 or len(pr) != len(arr) or not np.isfinite(pr).all():
        raise ValueError('Model returned nonfinite or misaligned predictions')
    return np.clip(pr, 1e-7, 1.-1e-7) if bundle['task'] == 'win' else pr
