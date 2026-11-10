"""Only invented bytes; no real source, fit, forecast or performance credit."""
import gzip
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'examples' / 'n066_transport_contract.py'
SPEC = importlib.util.spec_from_file_location('n066_public_contract', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class TransportTests(unittest.TestCase):
    def test_identical_wire_is_accepted(self):
        value = {'invented': 1}
        m.validate_wire(value, m.wire_identity(value))

    def test_other_serialization_not_silently_accepted(self):
        value = {'invented': 1}
        other = hashlib.sha256(m.wire_bytes(value).rstrip(b'\n')).hexdigest()
        with self.assertRaises(ValueError):
            m.validate_wire(value, other)

    def test_writable_spool_read_without_modification(self):
        raw = gzip.compress(b'invented,fixture\n1,2\n', mtime=0)
        with tempfile.SpooledTemporaryFile(max_size=1024, mode='w+b') as f:
            f.write(raw)
            f.seek(0)
            self.assertEqual(m.read_gzip_spool(f, 100), b'invented,fixture\n1,2\n')
            f.seek(0)
            self.assertEqual(f.read(), raw)

    def test_expansion_bound_is_enforced(self):
        with tempfile.SpooledTemporaryFile(mode='w+b') as f:
            f.write(gzip.compress(b'xxxxxxxxxx', mtime=0))
            f.seek(0)
            with self.assertRaises(ValueError):
                m.read_gzip_spool(f, 3)

    def test_embedded_clock_is_not_rewritten(self):
        receipt = {'captured_at': '2001-01-01T00:00:00Z', 'hash': 'invented'}
        self.assertIs(m.choose_receipt(receipt), receipt)
        self.assertEqual(m.choose_receipt(None, receipt), receipt)

    def test_conflicting_receipts_are_rejected(self):
        with self.assertRaises(ValueError):
            m.choose_receipt({'hash': 'a'}, {'hash': 'b'})


if __name__ == '__main__':
    unittest.main()
