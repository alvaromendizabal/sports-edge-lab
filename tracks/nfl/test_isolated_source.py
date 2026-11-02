import hashlib
import importlib
import sys
from pathlib import Path
import tempfile
import types
import unittest
import warnings
import zipfile

from isolated_source import demo, isolated_source


class IsolatedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.name = 'invented_selected_head'
        self.helper = 'invented_selected_feature'
        self.names = [self.name, self.helper]
        self.before = {n: sys.modules.get(n) for n in self.names}
        self.addCleanup(self.restore)

    def restore(self):
        for name, previous in self.before.items():
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous

    def archive(self, value=7, members=None, filename='selected.zip'):
        path = self.folder / filename
        if members is None:
            members = [('source/' + self.name + '.py',
                        'from ' + self.helper + ' import value\nresult = value + 1\n'),
                       ('source/' + self.helper + '.py', 'value = ' + repr(value) + '\n')]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(path, 'w') as bundle:
                for name, body in members:
                    bundle.writestr(name, body)
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def context(self, pair, names=None, **kwargs):
        path, pin = pair
        return isolated_source(path, expected_sha256=pin, module_names=names or self.names, **kwargs)

    def test_foreign_cached_head_and_dependency_are_replaced(self):
        prior = types.ModuleType(self.name); prior.result = -1
        foreign_helper = types.ModuleType(self.helper); foreign_helper.value = -20
        sys.modules.update({self.name: prior, self.helper: foreign_helper})
        with self.context(self.archive()) as receipt:
            self.assertEqual(importlib.import_module(self.name).result, 8)
            self.assertEqual(receipt['previously_cached_modules'], sorted(self.names))
        self.assertIs(sys.modules[self.name], prior)
        self.assertIs(sys.modules[self.helper], foreign_helper)
        self.assertEqual(receipt['loaded_modules'], sorted(self.names))
        self.assertTrue(receipt['restored'])

    def test_uncached_selected_modules_removed_on_exit(self):
        for name in self.names: sys.modules.pop(name, None)
        with self.context(self.archive()): importlib.import_module(self.name)
        self.assertTrue(all(n not in sys.modules for n in self.names))

    def test_exact_none_cache_entry_restored(self):
        sys.modules[self.name] = None
        with self.context(self.archive()): self.assertEqual(importlib.import_module(self.name).result, 8)
        self.assertIn(self.name, sys.modules); self.assertIsNone(sys.modules[self.name])

    def test_caller_exception_restores_import_state(self):
        prior = types.ModuleType(self.name); sys.modules[self.name] = prior
        finders = list(sys.meta_path)
        with self.assertRaisesRegex(RuntimeError, 'caller stopped'):
            with self.context(self.archive()) as receipt:
                importlib.import_module(self.name)
                raise RuntimeError('caller stopped')
        self.assertIs(sys.modules[self.name], prior)
        self.assertEqual(sys.meta_path, finders); self.assertTrue(receipt['restored'])

    def test_real_import_exception_preserved_and_state_restored(self):
        pair = self.archive(members=[('source/' + self.name + '.py', "raise LookupError('real import failure')\n")])
        prior = types.ModuleType(self.name); sys.modules[self.name] = prior
        with self.assertRaisesRegex(LookupError, 'real import failure'):
            with self.context(pair, [self.name]) as receipt:
                importlib.import_module(self.name)
        self.assertIs(sys.modules[self.name], prior)
        self.assertEqual(receipt['loaded_modules'], [])

    def test_nested_context_restores_outer_exact_objects(self):
        first = self.archive(7); second = self.archive(19, filename='other.zip')
        with self.context(first):
            outer = importlib.import_module(self.name)
            with self.context(second): self.assertEqual(importlib.import_module(self.name).result, 20)
            self.assertIs(importlib.import_module(self.name), outer)
            self.assertEqual(outer.result, 8)

    def test_source_origin_and_digests_are_exact(self):
        pair = self.archive()
        with self.context(pair) as receipt:
            mod = importlib.import_module(self.name)
            self.assertEqual(mod.__spec__.origin, str(pair[0].resolve()) + '!/source/' + self.name + '.py')
            self.assertEqual(mod.__file__, mod.__spec__.origin)
            self.assertEqual(receipt['archive_sha256'], pair[1])
            self.assertEqual(receipt['source_sha256'][self.helper], hashlib.sha256(b'value = 7\n').hexdigest())

    def test_verified_source_bytes_survive_archive_replacement(self):
        pair = self.archive(7)
        with self.context(pair):
            self.archive(999)
            self.assertEqual(importlib.import_module(self.name).result, 8)

    def test_sys_path_importer_cache_and_unrelated_modules_unchanged(self):
        import math
        paths = list(sys.path); cache = dict(sys.path_importer_cache)
        with self.context(self.archive()):
            importlib.import_module(self.name)
            self.assertIs(sys.modules['math'], math)
        self.assertEqual(sys.path, paths); self.assertEqual(sys.path_importer_cache, cache)

    def test_wrong_hash_rejected_before_global_mutation(self):
        pair = self.archive(); finders = list(sys.meta_path)
        prior = types.ModuleType(self.name); sys.modules[self.name] = prior
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            with self.context((pair[0], '0' * 64)): pass
        self.assertIs(sys.modules[self.name], prior); self.assertEqual(sys.meta_path, finders)

    def test_missing_declared_module_rejected(self):
        pair = self.archive(members=[('source/' + self.name + '.py', 'value=1')])
        with self.assertRaisesRegex(ValueError, 'Missing declared'):
            with self.context(pair): pass

    def test_undeclared_selected_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            with self.context(self.archive(), [self.name]): pass

    def test_duplicate_archive_member_rejected(self):
        pair = self.archive(members=[('source/' + self.name + '.py', 'value=1')] * 2)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            with self.context(pair, [self.name]): pass

    def test_nested_package_layout_rejected(self):
        pair = self.archive(members=[('source/pkg/__init__.py', 'value=1')])
        with self.assertRaisesRegex(ValueError, 'flat Python'):
            with self.context(pair, ['pkg']): pass

    def test_unsafe_path_rejected_even_outside_selected_prefix(self):
        for name in ('../outside.py', '/absolute.py', 'a\\b.py', 'a//b.py'):
            with self.subTest(name=name):
                pair = self.archive(members=[('source/' + self.name + '.py', 'value=1'), (name, '')])
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    with self.context(pair, [self.name]): pass

    def test_symlink_member_rejected(self):
        item = zipfile.ZipInfo('source/' + self.name + '.py'); item.external_attr = 0o120777 << 16
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            with self.context(self.archive(members=[(item, 'elsewhere')]), [self.name]): pass

    def test_non_source_file_in_selected_prefix_rejected(self):
        pair = self.archive(members=[('source/data.json', '{}')])
        with self.assertRaisesRegex(ValueError, 'flat Python'):
            with self.context(pair, [self.name]): pass

    def test_standard_library_and_invalid_names_rejected(self):
        pair = self.archive()
        for names in (['sys'], ['json'], ['for'], ['a.b'], ['__init__'], [self.name, self.name]):
            with self.subTest(names=names):
                with self.assertRaises(ValueError):
                    with self.context(pair, names): pass

    def test_invalid_pin_and_prefix_rejected(self):
        pair = self.archive()
        for pin in ('wrong', 'G' * 64, None):
            with self.subTest(pin=pin):
                with self.assertRaises(ValueError):
                    with self.context((pair[0], pin)): pass
        with self.assertRaises(ValueError):
            with self.context(pair, prefix='../source'): pass

    def test_unused_selected_module_is_not_executed(self):
        pair = self.archive(members=[('source/' + self.name + '.py', "raise AssertionError('not imported')")])
        with self.context(pair, [self.name]) as receipt: pass
        self.assertEqual(receipt['loaded_modules'], [])

    def test_demo_is_invented_zero_fit_and_restores_original(self):
        result = demo()
        self.assertEqual(result['inside'], 'verified selected source')
        self.assertTrue(result['original_object_restored'])
        self.assertEqual(result['new_fits'], 0)
        self.assertFalse(result['scientific_acceptance_claimed'])


if __name__ == '__main__': unittest.main()
