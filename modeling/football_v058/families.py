"""Fixed V058 tabular nonlinear families; chronological splits are caller-owned.

HGB: 100 histogram boosting iterations, at most 15 leaves/depth 5 per tree.
MLP: d -> 32 tanh -> 16 tanh -> one output (logistic for binary wins,
identity for regression); 32*d+577 trainable parameters. Adam sees only the
caller-provided training rows, for exactly 200 one-epoch partial_fit calls.
The test-only epochs override is explicit and recorded in the returned bundle.
No validation split, early stopping, parameter search or remote pickle loading.

These are small tabular research models, not evidence that nonlinear models
outperform accepted linear models or that learned football effects are causal.
Small effective seasonal samples make variance, calibration and chronological
validation central limitations. Repeatability is scoped to a pinned environment.
"""
import copy
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

FAMILIES=('hgb','mlp')
TASKS=('win','margin','total')
SEED=5801
MLP_EPOCHS=200
HGB_CONFIG=dict(learning_rate=.05,max_iter=100,max_leaf_nodes=15,max_depth=5,
                min_samples_leaf=30,l2_regularization=5.,max_bins=63,
                categorical_features=None,early_stopping=False,
                validation_fraction=None,random_state=SEED)
MLP_CONFIG=dict(hidden_layer_sizes=(32,16),activation='tanh',solver='adam',
                learning_rate_init=.001,learning_rate='constant',alpha=.01,
                batch_size=64,shuffle=True,random_state=SEED,
                early_stopping=False,max_iter=1,tol=0.,n_iter_no_change=201)


def _matrix(X):
    names=list(X.columns) if hasattr(X,'columns') else None
    if names is not None and len(set(names))!=len(names):
        raise ValueError('Duplicate input feature names')
    try:arr=np.array(X,dtype=np.float64,copy=True)
    except (ValueError,TypeError) as e:raise ValueError('X must be a finite numeric matrix') from e
    if arr.ndim!=2 or arr.shape[0]==0 or arr.shape[1]==0:
        raise ValueError('X must be a nonempty two-dimensional matrix')
    if not np.isfinite(arr).all():raise ValueError('X contains nonfinite values')
    return arr,names


def _training(X,y,task,family,epochs):
    if family not in FAMILIES:raise ValueError('Unsupported family')
    if task not in TASKS:raise ValueError('Unsupported task')
    if epochs is not None:
        if family!='mlp' or isinstance(epochs,(bool,np.bool_)) or not isinstance(epochs,(int,np.integer)) or not 1<=epochs<=MLP_EPOCHS:
            raise ValueError('epochs is an explicit MLP fixture-only integer override in [1,200]')
    arr,names=_matrix(X)
    try:target=np.array(y,dtype=np.float64,copy=True)
    except (TypeError,ValueError) as e:raise ValueError('y must be a finite vector') from e
    if target.ndim!=1 or len(target)!=len(arr) or len(target)<2 or not np.isfinite(target).all():
        raise ValueError('y must be a finite aligned vector with at least two rows')
    if task=='win' and set(np.unique(target))!={0.,1.}:
        raise ValueError('Binary win training requires both classes 0 and 1')
    return arr,target,names


def fit_model(X,y,task,family,progress=None,epochs=None):
    """Fit one fixed family to the supplied training partition only.

    ``progress(done,total)`` runs before training and at completion; for MLP it
    also runs every 20 epochs. HGB's public API provides no epoch callback here,
    so its single fit is bounded by the owner's independent runtime monitor.
    Callback exceptions propagate. No callback or runtime handle is serialized.
    """
    arr,target,names=_training(X,y,task,family,epochs)
    if progress is not None and not callable(progress):raise ValueError('progress must be callable')
    notify=progress if progress is not None else lambda done,total:None
    x_scaler=None;y_scaler=None
    if family=='hgb':
        config=copy.deepcopy(HGB_CONFIG);total=config['max_iter']
        estimator=(HistGradientBoostingClassifier if task=='win' else HistGradientBoostingRegressor)(**config)
        notify(0,total)
        with threadpool_limits(limits=2):estimator.fit(arr,target)
        notify(total,total)
        if estimator.n_iter_!=total:raise RuntimeError('HGB did not complete its fixed iteration count')
    else:
        total=MLP_EPOCHS if epochs is None else int(epochs)
        config=copy.deepcopy(MLP_CONFIG)
        x_scaler=StandardScaler().fit(arr);arr=x_scaler.transform(arr)
        if task!='win':
            y_scaler=StandardScaler().fit(target.reshape(-1,1));target=y_scaler.transform(target.reshape(-1,1)).ravel()
        estimator=(MLPClassifier if task=='win' else MLPRegressor)(**config)
        notify(0,total)
        with threadpool_limits(limits=2):
            for epoch in range(1,total+1):
                if task=='win':estimator.partial_fit(arr,target,classes=np.array([0,1]))
                else:estimator.partial_fit(arr,target)
                if epoch%20==0 or epoch==total:notify(epoch,total)
        if int(estimator.t_)!=total*len(arr):raise RuntimeError('MLP did not see exactly the fixed epochs of training rows')
    bundle={'family':family,'task':task,'estimator':estimator,'x_scaler':x_scaler,
            'y_scaler':y_scaler,'n_features':arr.shape[1],'feature_names':names,
            'training_rows':len(arr),'config':config,'epochs_completed':total if family=='mlp' else None,
            'fixture_epochs_override':epochs,'validation_split_used':False,
            'architecture':{'hidden_widths':[32,16],'activation':'tanh','output':'logistic' if task=='win' else 'identity','parameter_count':32*arr.shape[1]+577} if family=='mlp' else {'iterations':100,'max_leaves':15,'max_depth':5}}
    # Validate the returned interface without another fit or training mutation.
    predict_model(bundle,X)
    return bundle


def predict_model(bundle,X):
    """Predict without updating training scalers, weights or metadata."""
    arr,names=_matrix(X)
    if bundle.get('family') not in FAMILIES or bundle.get('task') not in TASKS:
        raise ValueError('Invalid family/task bundle')
    if arr.shape[1]!=bundle.get('n_features'):raise ValueError('Prediction feature width differs from training')
    if names is not None and bundle.get('feature_names') is not None and names!=bundle['feature_names']:
        raise ValueError('Prediction feature names/order differ from training')
    scaler=bundle.get('x_scaler')
    if scaler is not None:arr=scaler.transform(arr)
    with threadpool_limits(limits=2):
        if bundle['task']=='win':
            classes=np.asarray(bundle['estimator'].classes_)
            positive=np.flatnonzero(classes==1)
            if len(positive)!=1:raise ValueError('Missing unique positive win class')
            predictions=np.asarray(bundle['estimator'].predict_proba(arr),dtype=float)[:,positive[0]]
        else:
            predictions=np.asarray(bundle['estimator'].predict(arr),dtype=float)
            target_scaler=bundle.get('y_scaler')
            if target_scaler is not None:predictions=target_scaler.inverse_transform(predictions.reshape(-1,1)).ravel()
    if predictions.ndim!=1 or len(predictions)!=len(arr) or not np.isfinite(predictions).all():
        raise ValueError('Model returned nonfinite or misaligned predictions')
    if bundle['task']=='win':predictions=np.clip(predictions,1e-7,1-1e-7)
    return predictions
