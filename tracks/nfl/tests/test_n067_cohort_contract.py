"""Invented observations only. No sports performance credit."""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'examples' / 'n067_cohort_contract.py'
SPEC = importlib.util.spec_from_file_location('n067_public_contract', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class CohortTests(unittest.TestCase):
    def setUp(self):
        self.row = {'event': 'invented-a', 'target': 'winner', 'cutoff': '2001-01-01T00:00:00Z', 'settlement': 'binary', 'truth': 1, 'prediction': .6}

    def test_same_cohort_can_pair(self):
        other = dict(self.row, prediction=.7)
        self.assertEqual(len(m.matched_rows([self.row], [other])), 1)

    def test_different_horizon_is_not_ranked(self):
        with self.assertRaises(ValueError):
            m.matched_rows([self.row], [dict(self.row, cutoff='2001-01-02T00:00:00Z')])

    def test_conflicting_truth_rejected(self):
        with self.assertRaises(ValueError):
            m.matched_rows([self.row], [dict(self.row, truth=0)])

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            m.matched_rows([self.row, self.row], [self.row])

    def test_complete_batch_reused_without_modifying_payload(self):
        batch = {'identity': 'invented', 'status': 'complete', 'cases': ['a', 'b'], 'payload': [self.row]}
        batch['payload_sha256'] = m.identity(batch['payload'])
        before = copy.deepcopy(batch)
        self.assertEqual(m.reuse_complete_batch(batch, 'invented', ['a', 'b']), [self.row])
        self.assertEqual(batch, before)

    def test_incomplete_or_changed_batch_rejected(self):
        batch = {'identity': 'invented', 'status': 'partial', 'cases': ['a'], 'payload': []}
        batch['payload_sha256'] = m.identity([])
        with self.assertRaises(ValueError):
            m.reuse_complete_batch(batch, 'invented', ['a', 'b'])
        batch.update(status='complete', cases=['a', 'b'], payload=[self.row])
        with self.assertRaises(ValueError):
            m.reuse_complete_batch(batch, 'invented', ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
