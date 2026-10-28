import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.review_lab.portable_recovery import (
    RecoveryError, admit_original, closure, digest, encoded, export, fixture,
    import_original, inspect, regular_bytes, relative, validate, walkthrough,
)


class PortableRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.owner = self.base / 'owner'
        self.manifest, self.pin = fixture(self.owner)

    def test_complete_transitive_closure_and_reopen(self):
        target = self.base / 'return'
        result = export(self.owner, self.manifest, self.pin, target)
        self.assertEqual(result['files'], 7)
        self.assertTrue(inspect(target, self.manifest, self.pin)['all_selected_stages_ready'])
        self.assertEqual((target / 'manifest.json').read_bytes(), encoded(self.manifest))
        self.assertEqual((target / 'outputs/forecast.json').read_bytes(), (self.owner / 'outputs/forecast.json').read_bytes())

    def test_context_loss_blocks_finance_but_not_research_or_forecasts(self):
        (self.owner / 'inputs/original-context.json').unlink()
        states = {r['stage']: r for r in inspect(self.owner, self.manifest, self.pin)['stages']}
        self.assertEqual(states['financial_evidence']['status'], 'BLOCKED')
        self.assertEqual(states['financial_evidence']['missing'], ['inputs/original-context.json'])
        self.assertEqual(states['forecasts']['status'], 'READY')
        self.assertEqual(states['research']['status'], 'READY')

    def test_unchanged_top_level_receipt_does_not_establish_portability(self):
        raw = (self.owner / 'outputs/forecast.json').read_bytes()
        (self.owner / 'inputs/source.json').unlink()
        result = inspect(self.owner, self.manifest, self.pin, ['forecasts'])
        self.assertEqual(digest(raw), self.manifest['artifacts']['outputs/forecast.json']['sha256'])
        self.assertFalse(result['all_selected_stages_ready'])

    def test_incomplete_export_never_publishes_destination(self):
        (self.owner / 'inputs/original-context.json').unlink()
        target = self.base / 'blocked'
        with self.assertRaises(RecoveryError):
            export(self.owner, self.manifest, self.pin, target)
        self.assertFalse(target.exists())

    def test_explicit_ready_subset_omits_unrelated_files(self):
        (self.owner / 'inputs/original-context.json').unlink()
        target = self.base / 'subset'
        result = export(self.owner, self.manifest, self.pin, target, stages=['research'])
        self.assertEqual(result['files'], 3)
        self.assertFalse((target / 'outputs/original-decision.json').exists())
        self.assertTrue(inspect(target, self.manifest, self.pin, ['research'])['all_selected_stages_ready'])
        self.assertFalse(inspect(target, self.manifest, self.pin)['all_selected_stages_ready'])

    def test_same_size_corruption_detected(self):
        path = self.owner / 'inputs/source.json'
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'true', b'null'))
        result = inspect(self.owner, self.manifest, self.pin)
        self.assertTrue(all('inputs/source.json' in s['corrupt'] for s in result['stages']))

    def test_manifest_edit_rejected_by_external_commitment(self):
        changed = copy.deepcopy(self.manifest)
        changed['artifacts']['inputs/source.json']['bytes'] += 1
        with self.assertRaisesRegex(RecoveryError, 'caller-held'):
            inspect(self.owner, changed, self.pin)

    def test_unknown_schema_rejected_even_with_matching_hash(self):
        changed = copy.deepcopy(self.manifest)
        changed['schema'] = 'unknown'
        with self.assertRaises(RecoveryError):
            validate(changed, digest(encoded(changed)))

    def test_cycles_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['artifacts']['inputs/source.json']['requires'] = ['outputs/forecast.json']
        with self.assertRaisesRegex(RecoveryError, 'cycle'):
            validate(changed, digest(encoded(changed)))

    def test_missing_graph_node_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['artifacts']['inputs/source.json']['requires'] = ['absent']
        with self.assertRaisesRegex(RecoveryError, 'explicitly pinned'):
            validate(changed, digest(encoded(changed)))

    def test_duplicate_dependencies_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['artifacts']['outputs/forecast.json']['requires'] *= 2
        with self.assertRaises(RecoveryError):
            validate(changed, digest(encoded(changed)))

    def test_duplicate_or_unknown_or_empty_stage_selection_rejected(self):
        for stages in ([], ['research', 'research'], ['unknown']):
            with self.subTest(stages=stages), self.assertRaises(RecoveryError):
                inspect(self.owner, self.manifest, self.pin, stages)

    def test_path_traversal_and_ambiguous_names_rejected(self):
        for name in ('../secret', '/tmp/secret', 'x/../secret', './secret', 'x//y', 'x\\y', '', 'manifest.json', 'export.json'):
            with self.subTest(name=name), self.assertRaises(RecoveryError):
                relative(name)

    def test_artifact_symlink_rejected_even_with_identical_bytes(self):
        path = self.owner / 'inputs/source.json'
        outside = self.base / 'outside.json'
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(RecoveryError, 'symlink'):
            regular_bytes(self.owner, 'inputs/source.json')
        self.assertFalse(inspect(self.owner, self.manifest, self.pin)['all_selected_stages_ready'])

    def test_parent_symlink_rejected(self):
        folder = self.owner / 'inputs'
        folder.rename(self.base / 'inputs')
        folder.symlink_to(self.base / 'inputs', target_is_directory=True)
        self.assertFalse(inspect(self.owner, self.manifest, self.pin)['all_selected_stages_ready'])

    def test_directory_instead_of_artifact_rejected(self):
        path = self.owner / 'inputs/source.json'
        path.unlink()
        path.mkdir()
        self.assertFalse(inspect(self.owner, self.manifest, self.pin)['all_selected_stages_ready'])

    def test_size_limit_is_checked_before_publication(self):
        target = self.base / 'limited'
        with self.assertRaisesRegex(RecoveryError, 'limit'):
            export(self.owner, self.manifest, self.pin, target, max_bytes=1)
        self.assertFalse(target.exists())

    def test_exact_size_limit_admits_all_bytes(self):
        one = export(self.owner, self.manifest, self.pin, self.base / 'one')
        two = export(self.owner, self.manifest, self.pin, self.base / 'two', max_bytes=one['bytes'])
        self.assertEqual(one, two)
        with self.assertRaises(RecoveryError):
            export(self.owner, self.manifest, self.pin, self.base / 'three', max_bytes=one['bytes'] - 1)

    def test_existing_destination_is_immutable(self):
        target = self.base / 'return'
        target.mkdir()
        (target / 'keep').write_text('existing')
        with self.assertRaises(RecoveryError):
            export(self.owner, self.manifest, self.pin, target)
        self.assertEqual((target / 'keep').read_text(), 'existing')

    def test_copy_failure_cleans_staging_and_does_not_publish(self):
        target = self.base / 'failed'
        with patch('examples.review_lab.portable_recovery.os.fsync', side_effect=OSError('invented disk failure')):
            with self.assertRaises(OSError):
                export(self.owner, self.manifest, self.pin, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(self.base.glob('.portable-*')), [])

    def test_original_decision_exact_across_release_and_relocation(self):
        name = 'outputs/original-decision.json'
        pin = self.manifest['artifacts'][name]['sha256']
        first = import_original(self.owner, name, pin, release='release-a')
        target = self.base / 'copied'
        export(self.owner, self.manifest, self.pin, target)
        second = import_original(target, name, pin, release='release-b')
        self.assertEqual(first['decision'], second['decision'])
        self.assertEqual(first['original_sha256'], second['original_sha256'])
        self.assertNotEqual(first['transport'], second['transport'])

    def test_missing_external_context_does_not_erase_embedded_original(self):
        name = 'outputs/original-decision.json'
        (self.owner / 'inputs/original-context.json').unlink()
        result = import_original(self.owner, name, self.manifest['artifacts'][name]['sha256'], release='next')
        self.assertTrue(result['decision']['week_locks'])
        self.assertFalse(inspect(self.owner, self.manifest, self.pin)['all_selected_stages_ready'])

    def test_original_lock_mutation_rejected(self):
        name = 'outputs/original-decision.json'
        decision = json.loads((self.owner / name).read_bytes())
        decision['week_locks'] = {}
        with self.assertRaisesRegex(RecoveryError, 'original decision changed'):
            admit_original(encoded(decision), self.manifest['artifacts'][name]['sha256'])

    def test_original_stake_or_policy_or_time_mutations_rejected(self):
        name = 'outputs/original-decision.json'
        for field, value in [('policy', 'changed'), ('issued_at', '2031-01-01T00:00:00Z'), ('allocations', [])]:
            decision = json.loads((self.owner / name).read_bytes())
            decision[field] = value
            with self.subTest(field=field), self.assertRaises(RecoveryError):
                admit_original(encoded(decision), self.manifest['artifacts'][name]['sha256'])

    def test_even_recommitted_empty_context_is_not_admitted(self):
        raw = (self.owner / 'outputs/original-decision.json').read_bytes()
        obj = json.loads(raw)
        obj['week_locks'] = {}
        raw = encoded(obj)
        with self.assertRaisesRegex(RecoveryError, 'whole-week context'):
            admit_original(raw, digest(raw))

    def test_workflow_counts_are_explicitly_invented(self):
        result = walkthrough()
        self.assertEqual(result['classification'], 'INVENTED_OFFLINE_EXAMPLE')
        self.assertEqual(result['actual_orders'], 0)
        self.assertEqual(result['real_fits'], 0)
        self.assertIsNone(result['profit'])
        self.assertTrue(result['changed_context_rejected'])
        self.assertTrue(result['original_decision_preserved'])
        self.assertTrue(result['forecast_issue_preserved'])
        self.assertTrue(result['independent_research_ready'])
        self.assertFalse(result['transport_changes_semantic_identity'])


if __name__ == '__main__':
    unittest.main()
