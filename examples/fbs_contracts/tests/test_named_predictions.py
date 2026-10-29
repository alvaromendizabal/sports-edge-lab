"""Regression tests for named fit, cold prediction, and schema rejection."""
import importlib.util
import unittest

from examples.fbs_contracts.named_predictions import NamedFeatures, demonstrate, invented_data


AVAILABLE = all(importlib.util.find_spec(name) for name in ("pandas", "numpy", "lightgbm", "sklearn", "joblib"))


class SchemaDefinitionTests(unittest.TestCase):
    def test_input_name_list_cannot_mutate_saved_schema(self):
        columns = ["pace", "rest"]
        schema = NamedFeatures(columns)
        before = schema.sha256
        columns.reverse()
        self.assertEqual(schema.columns, ("pace", "rest"))
        self.assertEqual(schema.sha256, before)

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            NamedFeatures(("pace", "pace"))

    def test_empty_names_rejected(self):
        with self.assertRaises(ValueError):
            NamedFeatures(("",))

    def test_feature_order_is_part_of_identity(self):
        self.assertNotEqual(NamedFeatures(("pace", "rest")).sha256, NamedFeatures(("rest", "pace")).sha256)


@unittest.skipUnless(AVAILABLE, "Native compatibility workflow installs required packages")
class NativePredictionTests(unittest.TestCase):
    def test_classifier_regressor_cold_and_reordered_predictions(self):
        result = demonstrate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["feature_name_warnings"], 0)
        self.assertEqual(result["owner_fits"], 0)
        self.assertEqual(len(result["results"]), 2)

    def test_missing_feature_rejected(self):
        frame, _, _ = invented_data()
        with self.assertRaises(ValueError):
            NamedFeatures(tuple(frame.columns)).frame(frame.drop(columns="pace"))

    def test_duplicate_input_column_rejected(self):
        frame, _, _ = invented_data()
        with self.assertRaises(ValueError):
            NamedFeatures(tuple(frame.columns)).frame(frame[["pace", "pace", "rest"]])

    def test_nan_feature_rejected(self):
        frame, _, _ = invented_data()
        frame.loc[0, "pace"] = float("nan")
        with self.assertRaises(ValueError):
            NamedFeatures(tuple(frame.columns)).frame(frame)

    def test_ambiguous_array_rejected(self):
        frame, _, _ = invented_data()
        with self.assertRaises(TypeError):
            NamedFeatures(tuple(frame.columns)).frame(frame.to_numpy())

    def test_estimator_schema_mismatch_rejected(self):
        from lightgbm import LGBMClassifier
        frame, wins, _ = invented_data()
        estimator = LGBMClassifier(n_estimators=2, n_jobs=1, verbosity=-1).fit(frame, wins)
        with self.assertRaises(ValueError):
            NamedFeatures(tuple(reversed(frame.columns))).predict(estimator, frame, classification=True)


if __name__ == "__main__":
    unittest.main()
