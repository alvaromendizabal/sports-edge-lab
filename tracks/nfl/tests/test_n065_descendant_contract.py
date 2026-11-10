"""Synthetic contract example only: no real sports or source performance credit."""
import importlib.util
from hashlib import sha256
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "examples/n065_descendant_contract.py"
SPEC = importlib.util.spec_from_file_location("n065_public_contract", PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class DescendantTests(unittest.TestCase):
    def setUp(self):
        self.bodies = {"old": b"invented original", "later": b"invented later"}
        self.old = {"old": sha256(self.bodies["old"]).hexdigest()}
        self.new = {"later": sha256(self.bodies["later"]).hexdigest()}

    def test_exact_declared_addition_has_zero_new_fit_credit(self):
        result = m.reconcile(self.old, self.new, self.bodies, self.new)
        self.assertEqual(result["verified_descendants"], 1)
        self.assertEqual(result["new_fit_credit"], 0)

    def test_unknown_extra_rejected_without_deleting_it(self):
        bodies = dict(self.bodies, unknown=b"unknown")
        with self.assertRaises(ValueError):
            m.reconcile(self.old, self.new, bodies, self.new)
        self.assertIn("unknown", bodies)

    def test_missing_original_rejected(self):
        with self.assertRaises(ValueError):
            m.reconcile(self.old, self.new, {"later": self.bodies["later"]}, self.new)

    def test_mutated_original_rejected(self):
        with self.assertRaises(ValueError):
            m.reconcile(self.old, self.new, dict(self.bodies, old=b"changed"), self.new)

    def test_missing_commit_rejected(self):
        with self.assertRaises(ValueError):
            m.reconcile(self.old, self.new, self.bodies, {})

    def test_conflicting_identity_rejected(self):
        with self.assertRaises(ValueError):
            m.reconcile(self.old, self.old, {"old": self.bodies["old"]}, self.old)


if __name__ == "__main__":
    unittest.main()
