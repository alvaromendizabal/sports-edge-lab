"""Invented inputs only; passing tests confer no NFL performance credit."""
from pathlib import Path
import importlib.util
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / "examples" / "n064_frozen_champion_contract.py"
SPEC = importlib.util.spec_from_file_location("n064_public_contract", PATH)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.past = m.Label("invented-a", "2021-01-01T00:00:00Z", "2021-01-02T00:00:00Z", 1.0)
        self.cutoff = "2021-02-01T00:00:00Z"

    def key(self, labels, **kwargs):
        return m.training_key(labels, self.cutoff, kwargs.get("recipe", "invented-model"), "schema-a", "code-a")

    def test_future_labels_do_not_change_frozen_key(self):
        future = m.Label("invented-b", "2021-03-01T00:00:00Z", "2021-03-02T00:00:00Z", 0.0)
        self.assertEqual(self.key([self.past]), self.key([self.past, future]))

    def test_late_publication_is_excluded(self):
        late = m.Label("invented-b", "2021-01-01T00:00:00Z", "2021-03-02T00:00:00Z", 0.0)
        self.assertEqual(self.key([self.past]), self.key([self.past, late]))

    def test_recipe_changes_key(self):
        self.assertNotEqual(self.key([self.past]), self.key([self.past], recipe="different-model"))

    def test_only_selected_or_precommitted_components_refit(self):
        m.admit_forward_fit("a", {"metric": "a"})
        m.admit_forward_fit("b", {"metric": "a"}, ("b",))
        with self.assertRaises(ValueError):
            m.admit_forward_fit("other", {"metric": "a"})

    def test_issue_is_immutable_and_exact_duplicate_reused(self):
        ledger = {}
        self.assertEqual("new", m.preserve_issue(ledger, "i", {"value": 0.4}))
        self.assertEqual("reused", m.preserve_issue(ledger, "i", {"value": 0.4}))
        with self.assertRaises(ValueError):
            m.preserve_issue(ledger, "i", {"value": 0.5})

    def test_negative_feature_context_is_preserved(self):
        history = []
        m.retain_experiment(history, {"experiment_id": "old", "feature": "x", "context": "a", "result": "negative"})
        m.retain_experiment(history, {"experiment_id": "new", "feature": "x", "context": "b", "result": "pending"})
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["result"], "negative")


if __name__ == "__main__":
    unittest.main()
