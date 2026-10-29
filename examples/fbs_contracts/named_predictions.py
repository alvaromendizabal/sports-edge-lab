"""Small, invented-data reproducer for the FBS LightGBM compatibility repair.

This module owns feature order explicitly. It neither suppresses warnings nor
changes the installed estimator packages. It is not an owner research result.
"""
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class NamedFeatures:
    columns: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "columns", tuple(self.columns))
        if not self.columns or any(not isinstance(c, str) or not c for c in self.columns):
            raise ValueError("Feature names must be nonempty strings")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Duplicate feature names")

    @property
    def sha256(self):
        return hashlib.sha256(json.dumps(self.columns, separators=(",", ":")).encode()).hexdigest()

    def frame(self, data):
        import numpy as np
        import pandas as pd

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Expected named input columns, not an ambiguous array")
        if not data.columns.is_unique:
            raise ValueError("Duplicate input columns")
        missing = sorted(set(self.columns) - set(data.columns))
        if missing:
            raise ValueError("Missing features: " + ", ".join(missing))
        selected = data.loc[:, list(self.columns)].astype(float)
        if not np.isfinite(selected.to_numpy()).all():
            raise ValueError("This reproducer requires finite, already prepared features")
        return selected

    def predict(self, estimator, data, *, classification):
        selected = self.frame(data)
        if list(estimator.feature_name_) != list(self.columns):
            raise ValueError("Estimator feature order differs from the saved schema")
        if classification:
            return estimator.predict_proba(selected, validate_features=True)[:, 1]
        return estimator.predict(selected, validate_features=True)


def invented_data():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7421)
    frame = pd.DataFrame(rng.normal(size=(240, 3)), columns=["strength", "pace", "rest"])
    noise = rng.normal(scale=0.3, size=len(frame))
    margin = 4.0 * frame.strength - frame.pace + 0.2 * frame.rest + noise
    return frame, (margin > 0).astype(int), margin


def demonstrate():
    """Return observations from two invented fits; never an owner-fit count."""
    import io
    import joblib
    import lightgbm
    import numpy as np
    import sklearn
    import warnings

    frame, wins, margin = invented_data()
    schema = NamedFeatures(tuple(frame.columns))
    train, evaluation = frame.iloc[:180], frame.iloc[180:]
    records = []
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="X does not have valid feature names.*", category=UserWarning)
        for cls, target, classification in [(lightgbm.LGBMClassifier, wins, True), (lightgbm.LGBMRegressor, margin, False)]:
            estimator = cls(n_estimators=20, num_leaves=7, min_child_samples=8, n_jobs=1, random_state=7421, verbosity=-1)
            estimator.fit(schema.frame(train), target.iloc[:180])
            prediction = schema.predict(estimator, evaluation, classification=classification)
            buffer = io.BytesIO()
            joblib.dump((schema, estimator), buffer)
            buffer.seek(0)
            restored_schema, restored = joblib.load(buffer)
            cold = restored_schema.predict(restored, evaluation, classification=classification)
            assert np.array_equal(prediction, cold)
            reordered = schema.predict(estimator, evaluation[list(reversed(frame.columns))], classification=classification)
            assert np.array_equal(prediction, reordered)
            records.append({"kind": cls.__name__, "training_rows": 180, "evaluation_rows": 60, "cold_equal": True, "input_reorder_equal": True, "prediction_sum": float(np.sum(prediction))})
    return {"status": "PASS", "execution_mode": "LOCAL_INVENTED_DATA", "owner_fits": 0, "local_fits": 2, "feature_schema_sha256": schema.sha256, "feature_name_warnings": 0, "lightgbm": lightgbm.__version__, "scikit_learn": sklearn.__version__, "results": records}


if __name__ == "__main__":
    print(json.dumps(demonstrate(), sort_keys=True, indent=2), flush=True)
