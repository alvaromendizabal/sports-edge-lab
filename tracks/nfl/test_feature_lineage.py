"""Invented fixture behavior; no real-model accuracy claims."""
import dataclasses
import unittest

from feature_lineage import FeatureNode, admit_features


class FeatureLineageTests(unittest.TestCase):
    cutoff = '2020-01-02T00:00:00Z'

    def node(self, key='a', **kwargs):
        return FeatureNode(key, 'a' * 64, kwargs.pop('kind', 'observed'),
                           kwargs.pop('available_at', '2020-01-01T00:00:00Z'), **kwargs)

    def run_graph(self, nodes, selected=('a',)):
        return admit_features(nodes, selected, cutoff=self.cutoff)

    def test_observed_source_admitted(self):
        self.assertTrue(self.run_graph([self.node()])[0].admitted)

    def test_cutoff_inclusive_source(self):
        self.assertTrue(self.run_graph([self.node(available_at=self.cutoff)])[0].admitted)

    def test_unknown_source_is_blocked(self):
        self.assertIn('a:unknown_availability', self.run_graph([self.node(available_at=None)])[0].reasons)

    def test_late_source_is_blocked(self):
        self.assertFalse(self.run_graph([self.node(available_at='2020-01-03T00:00:00Z')])[0].admitted)

    def test_timezone_equivalence(self):
        self.assertTrue(self.run_graph([self.node(available_at='2020-01-01T16:00:00-08:00')])[0].admitted)

    def test_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node(available_at='2020-01-01')])

    def test_bad_hash_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([dataclasses.replace(self.node(), sha256='not-a-hash')])

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node(), self.node()])

    def test_duplicate_selection_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node()], ('a', 'a'))

    def test_unknown_selected_feature_is_explicit(self):
        self.assertEqual(self.run_graph([], ('absent',))[0].reasons, ('absent:missing_dependency',))

    def test_dangling_parent_is_blocked(self):
        result = self.run_graph([self.node(kind='transform', parents=('missing',))])[0]
        self.assertIn('missing:missing_dependency', result.reasons)

    def test_cycle_is_blocked(self):
        nodes = [self.node('a', kind='transform', parents=('b',)), self.node('b', kind='transform', parents=('a',))]
        self.assertIn('a:dependency_cycle', self.run_graph(nodes)[0].reasons)

    def test_self_cycle_is_blocked(self):
        self.assertFalse(self.run_graph([self.node(kind='transform', parents=('a',))])[0].admitted)

    def test_unknown_teacher_training_blocks_descendant(self):
        nodes = [self.node('teacher', kind='fitted'), self.node(kind='transform', parents=('teacher',))]
        self.assertIn('teacher:unknown_training_lineage', self.run_graph(nodes)[0].reasons)

    def test_cutoff_training_label_is_not_prior(self):
        n = self.node(kind='fitted', available_at=self.cutoff, latest_training_label_available_at=self.cutoff)
        self.assertIn('a:training_label_not_strictly_prior', self.run_graph([n])[0].reasons)

    def test_valid_fitted_lineage(self):
        n = self.node(kind='fitted', latest_training_label_available_at='2019-12-31T00:00:00Z')
        self.assertTrue(self.run_graph([n])[0].admitted)

    def test_impossible_training_clock(self):
        n = self.node(kind='fitted', latest_training_label_available_at='2020-01-01T12:00:00Z')
        self.assertIn('a:training_label_after_artifact_availability', self.run_graph([n])[0].reasons)

    def test_unrelated_bad_family_does_not_block_counts(self):
        nodes = [self.node(), self.node('teacher', kind='fitted'),
                 self.node('derived', kind='transform', parents=('teacher',))]
        a, b = self.run_graph(nodes, ('a', 'derived'))
        self.assertTrue(a.admitted)
        self.assertFalse(b.admitted)

    def test_transitive_late_source_propagates(self):
        nodes = [self.node('source', available_at='2020-01-03T00:00:00Z'),
                 self.node('middle', kind='transform', parents=('source',)),
                 self.node(kind='transform', parents=('middle',))]
        self.assertIn('source:available_after_cutoff', self.run_graph(nodes)[0].reasons)

    def test_shared_dependency_deduplicated_and_pinned(self):
        nodes = [self.node('source'), self.node('b', kind='transform', parents=('source',)),
                 self.node(kind='transform', parents=('source', 'b'))]
        r = self.run_graph(nodes)[0]
        self.assertTrue(r.admitted)
        self.assertEqual(r.dependency_ids, ('a', 'b', 'source'))
        self.assertEqual(len(r.dependency_hashes), 3)

    def test_input_order_does_not_change_admission(self):
        nodes = [self.node('b'), self.node(kind='transform', parents=('b',))]
        self.assertEqual(self.run_graph(nodes), self.run_graph(reversed(nodes)))

    def test_parent_must_exist_before_child_artifact(self):
        nodes = [self.node('b', available_at='2020-01-01T12:00:00Z'),
                 self.node(kind='transform', parents=('b',))]
        self.assertIn('a:b:parent_available_after_child', self.run_graph(nodes)[0].reasons)

    def test_transitive_parent_artifact_chronology(self):
        nodes = [self.node('source', available_at='2020-01-01T12:00:00Z'),
                 self.node('b', kind='transform', parents=('source',)),
                 self.node(kind='transform', available_at=self.cutoff, parents=('b',))]
        self.assertIn('b:source:parent_available_after_child', self.run_graph(nodes)[0].reasons)

    def test_equal_parent_and_child_availability(self):
        nodes = [self.node('b'), self.node(kind='transform', parents=('b',))]
        self.assertTrue(self.run_graph(nodes)[0].admitted)

    def test_observed_with_hidden_parent_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node(parents=('b',))])

    def test_duplicate_parent_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node(kind='transform', parents=('b', 'b'))])

    def test_training_clock_on_unfitted_node_rejected(self):
        with self.assertRaises(ValueError):
            self.run_graph([self.node(latest_training_label_available_at=self.cutoff)])


if __name__ == '__main__':
    unittest.main()
