"""Behavioral regressions, including execution of the exact invented zipapp."""
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
import warnings
import zipfile

import packaged_source


def pin(body):
    return hashlib.sha256(body).hexdigest()


@contextmanager
def fixture(*, zipped=False, source=b'value = 7\n', extra=()):
    name = 'invented_source_contract'
    previous = sys.modules.get(name)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / ('fixture.pyz' if zipped else name + '.py')
        if zipped:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(path, 'w') as z:
                    z.writestr(name + '.py', source)
                    for member, body in extra:
                        z.writestr(member, body)
            sys.path.insert(0, str(path))
            sys.modules.pop(name, None)
            module = importlib.import_module(name)
        else:
            path.write_bytes(source)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        try:
            yield module, path, source
        finally:
            if zipped:
                sys.path.remove(str(path))
                sys.path_importer_cache.pop(str(path), None)
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous


class PinnedSourceTests(unittest.TestCase):
    def test_plain_file_exact_bytes(self):
        with fixture() as (module, _, body):
            self.assertEqual(packaged_source.read_pinned_source(module, source_sha256=pin(body)).encode(), body)

    def test_crlf_source_is_not_normalized_before_hashing(self):
        with fixture(source=b'value = 7\r\n') as (module, _, body):
            self.assertEqual(packaged_source.read_pinned_source(module, source_sha256=pin(body)).encode(), body)

    def test_unicode_utf8_source(self):
        body = "value = 'équipe'\n".encode()
        with fixture(source=body) as (module, _, _):
            self.assertEqual(packaged_source.read_pinned_source(module, source_sha256=pin(body)).encode(), body)

    def test_old_path_failure_and_zip_source_success(self):
        with fixture(zipped=True) as (module, path, body):
            with self.assertRaises((NotADirectoryError, FileNotFoundError)):
                Path(module.__file__).read_text()
            self.assertEqual(packaged_source.read_pinned_source(module, source_sha256=pin(body),
                             archive_sha256=pin(path.read_bytes())).encode(), body)

    def test_wrong_source_pin(self):
        with fixture() as (module, _, _):
            with self.assertRaisesRegex(ValueError, 'Source hash'):
                packaged_source.read_pinned_source(module, source_sha256='0' * 64)

    def test_wrong_archive_pin(self):
        with fixture(zipped=True) as (module, _, body):
            with self.assertRaisesRegex(ValueError, 'Physical archive'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256='0' * 64)

    def test_zip_requires_separate_physical_pin(self):
        with fixture(zipped=True) as (module, _, body):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body))

    def test_plain_source_refuses_archive_identity(self):
        with fixture() as (module, _, body):
            with self.assertRaisesRegex(ValueError, 'normal source'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256='0' * 64)

    def test_malformed_source_digest(self):
        with fixture() as (module, _, _):
            for value in [None, '', 'x' * 64, 'A' * 64, '0' * 63]:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    packaged_source.read_pinned_source(module, source_sha256=value)

    def test_file_changed_after_import_is_not_silently_accepted(self):
        with fixture() as (module, path, body):
            path.write_bytes(b'value = 8\n')
            with self.assertRaisesRegex(ValueError, 'Source hash'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body))
            self.assertEqual(module.value, 7)  # No reexecution by the reader.

    def test_mismatched_module_origin(self):
        with fixture() as (module, _, body):
            module.__file__ += '.changed.py'
            with self.assertRaisesRegex(ValueError, 'origin'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body))

    def test_mismatched_spec_name(self):
        with fixture() as (module, _, body):
            module.__spec__.name = 'different'
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body))

    def test_unknown_loader_is_never_called(self):
        class Untrusted:
            def get_data(self, path):
                raise AssertionError('Must not call an unknown loader')
        with fixture() as (module, _, body):
            module.__loader__ = module.__spec__.loader = Untrusted()
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body))

    def test_nonmodule_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'module'):
            packaged_source.read_pinned_source(object(), source_sha256='0' * 64)

    def test_source_less_module_is_refused(self):
        with self.assertRaises(ValueError):
            packaged_source.read_pinned_source(types.ModuleType('source_less'), source_sha256='0' * 64)

    def test_unsafe_zip_members(self):
        for member in ['../outside.txt', '/outside.txt', 'a//b', 'C:/outside.txt', 'a\\b']:
            with self.subTest(member=member), fixture(zipped=True, extra=[(member, b'x')]) as (module, path, body):
                with self.assertRaisesRegex(ValueError, 'Unsafe ZIP'):
                    packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256=pin(path.read_bytes()))

    def test_duplicate_zip_members(self):
        with fixture(zipped=True, extra=[('extra', b'a'), ('extra', b'b')]) as (module, path, body):
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256=pin(path.read_bytes()))

    def test_case_ambiguous_zip_members(self):
        with fixture(zipped=True, extra=[('extra', b'a'), ('EXTRA', b'b')]) as (module, path, body):
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256=pin(path.read_bytes()))

    def test_symlink_zip_member(self):
        item = zipfile.ZipInfo('link'); item.create_system = 3; item.external_attr = 0o120777 << 16
        with fixture(zipped=True, extra=[(item, b'target')]) as (module, path, body):
            with self.assertRaisesRegex(ValueError, 'Unsafe ZIP'):
                packaged_source.read_pinned_source(module, source_sha256=pin(body), archive_sha256=pin(path.read_bytes()))

    def test_real_zipapp_subprocess_and_wrong_hash(self):
        helper = Path(packaged_source.__file__).read_bytes()
        source = b'value = 9\n'
        entry = ("import json,sys\nimport invented_packed_module as target\n"
                 "from packaged_source import read_pinned_source\n"
                 f"s=read_pinned_source(target,source_sha256='{pin(source)}',archive_sha256=sys.argv[1])\n"
                 "assert '.pyz/' in target.__file__\n"
                 "print(json.dumps({'exact_source':s,'value':target.value}))\n")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'actual_context.pyz'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('__main__.py', entry)
                z.writestr('packaged_source.py', helper)
                z.writestr('invented_packed_module.py', source)
            accepted = subprocess.run([sys.executable, str(path), pin(path.read_bytes())], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(accepted.stdout), {'exact_source': source.decode(), 'value': 9})
            refused = subprocess.run([sys.executable, str(path), '0' * 64], capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn('Physical archive hash mismatch', refused.stderr)

    def test_demo_declares_no_scientific_credit(self):
        result = packaged_source.demo()
        self.assertTrue(result['ordinary_path_read_failed'])
        self.assertTrue(result['pinned_zip_source_matched'])
        self.assertEqual(result['new_model_fits'], 0)
        self.assertFalse(result['owner_acceptance_claimed'])


if __name__ == '__main__':
    unittest.main()
