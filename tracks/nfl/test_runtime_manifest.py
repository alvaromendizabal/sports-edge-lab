"""File-system behavior tests using invented data; no numerical dependencies."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runtime_manifest import recheck_before_use, verify_tree


class InstalledManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name).resolve()
        self.root = base / "package"
        self.root.mkdir()
        self.metadata = base / "installed.json"
        self.body = b"invented installed bytes"
        (self.root / "sample.py").write_bytes(self.body)
        self.doc = {"schema": "invented.installed-files.v1", "package": "invented", "files": [{"path": "sample.py", "installed_bytes": len(self.body), "installed_sha256": hashlib.sha256(self.body).hexdigest(), "original_sha256": hashlib.sha256(b"different archive bytes").hexdigest()}]}
        self.write_metadata()

    def write_metadata(self):
        self.metadata.write_text(json.dumps(self.doc), encoding="utf-8")
        self.pin = hashlib.sha256(self.metadata.read_bytes()).hexdigest()

    def verify(self):
        return verify_tree(self.root, self.metadata, trusted_metadata_sha256=self.pin)

    def test_original_digest_is_separate_from_installed_digest(self):
        receipt = self.verify()
        self.assertNotEqual(receipt.files[0][2], receipt.files[0][3])
        self.assertEqual(receipt.files[0][2], hashlib.sha256(self.body).hexdigest())

    def test_unchanged_phase_recheck(self):
        receipt = self.verify()
        self.assertEqual(receipt, recheck_before_use(receipt, self.root, self.metadata))

    def test_changed_payload_same_size_rejected(self):
        (self.root / "sample.py").write_bytes(b"x" * len(self.body))
        with self.assertRaises(ValueError): self.verify()

    def test_wrong_size_rejected_even_with_correct_digest(self):
        self.doc["files"][0]["installed_bytes"] += 1
        self.write_metadata()
        with self.assertRaises(ValueError): self.verify()

    def test_changed_payload_does_not_enroll_new_expected_digest(self):
        receipt = self.verify()
        original_metadata = self.metadata.read_bytes()
        (self.root / "sample.py").write_bytes(b"changed")
        with self.assertRaises(ValueError): recheck_before_use(receipt, self.root, self.metadata)
        self.assertEqual(original_metadata, self.metadata.read_bytes())

    def test_rewriting_metadata_and_payload_cannot_reuse_receipt(self):
        receipt = self.verify()
        (self.root / "sample.py").write_bytes(b"changed")
        self.doc["files"][0].update(installed_bytes=7, installed_sha256=hashlib.sha256(b"changed").hexdigest())
        self.write_metadata()
        with self.assertRaises(ValueError): recheck_before_use(receipt, self.root, self.metadata)

    def test_added_file_rejected(self):
        (self.root / "extra.py").write_bytes(b"unlisted")
        with self.assertRaises(ValueError): self.verify()

    def test_failed_directory_scan_cannot_hide_an_unlisted_file(self):
        hidden = self.root / "unreadable"
        hidden.mkdir()
        (hidden / "unlisted.py").write_bytes(b"unlisted")
        scan = os.scandir

        def denied(path):
            if Path(path) == hidden:
                raise PermissionError("invented unreadable directory")
            return scan(path)

        with patch("os.scandir", side_effect=denied):
            with self.assertRaises(ValueError): self.verify()

    def test_removed_file_rejected(self):
        (self.root / "sample.py").unlink()
        with self.assertRaises(ValueError): self.verify()

    def test_equal_file_count_different_name_rejected(self):
        (self.root / "sample.py").rename(self.root / "other.py")
        with self.assertRaises(ValueError): self.verify()

    def test_added_file_after_receipt_rejected(self):
        receipt = self.verify()
        (self.root / "later.py").write_bytes(b"unlisted")
        with self.assertRaises(ValueError): recheck_before_use(receipt, self.root, self.metadata)

    def test_original_hash_cannot_substitute_for_missing_installed_hash(self):
        del self.doc["files"][0]["installed_sha256"]
        self.write_metadata()
        with self.assertRaises(ValueError): self.verify()

    def test_duplicate_or_case_colliding_paths_rejected(self):
        for name in ["sample.py", "SAMPLE.py"]:
            with self.subTest(name=name):
                self.doc["files"].append({**self.doc["files"][0], "path": name})
                self.write_metadata()
                with self.assertRaises(ValueError): self.verify()
                self.doc["files"].pop()

    def test_unsafe_paths_rejected(self):
        for name in ["../sample.py", "/sample.py", "a/../sample.py", "./sample.py", "a//sample.py", "a\\sample.py", "C:sample.py", ".", "", "a\x00b"]:
            with self.subTest(name=name):
                self.doc["files"][0]["path"] = name
                self.write_metadata()
                with self.assertRaises(ValueError): self.verify()

    def test_malformed_hashes_and_sizes_rejected(self):
        for field, value in [("installed_sha256", "0"), ("installed_sha256", "F" * 64), ("original_sha256", "unknown"), ("installed_bytes", True), ("installed_bytes", -1), ("installed_bytes", 1.0)]:
            with self.subTest(field=field, value=value):
                old = self.doc["files"][0][field]
                self.doc["files"][0][field] = value
                self.write_metadata()
                with self.assertRaises(ValueError): self.verify()
                self.doc["files"][0][field] = old

    def test_duplicate_json_keys_rejected(self):
        raw = self.metadata.read_bytes().replace(b'"package": "invented"', b'"package": "first", "package": "second"')
        self.metadata.write_bytes(raw)
        self.pin = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError): self.verify()

    def test_metadata_mutation_without_payload_mutation_rejected(self):
        receipt = self.verify()
        self.metadata.write_bytes(self.metadata.read_bytes() + b"\n")
        with self.assertRaises(ValueError): recheck_before_use(receipt, self.root, self.metadata)

    def test_unknown_metadata_fields_rejected(self):
        self.doc["trust_any_observed_hash"] = True
        self.write_metadata()
        with self.assertRaises(ValueError): self.verify()

    def test_missing_pin_is_not_implicit_trust(self):
        with self.assertRaises(TypeError): verify_tree(self.root, self.metadata)

    def test_empty_evidence_rejected(self):
        self.doc["files"] = []
        self.write_metadata()
        with self.assertRaises(ValueError): self.verify()

    def test_payload_symlink_rejected(self):
        target = self.root.parent / "external.py"
        target.write_bytes(self.body)
        (self.root / "sample.py").unlink()
        (self.root / "sample.py").symlink_to(target)
        with self.assertRaises(ValueError): self.verify()

    def test_metadata_symlink_rejected(self):
        original = self.metadata.with_name("real.json")
        self.metadata.rename(original)
        self.metadata.symlink_to(original)
        with self.assertRaises(ValueError): self.verify()

    def test_tree_symlink_rejected(self):
        alias = self.root.parent / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): verify_tree(alias, self.metadata, trusted_metadata_sha256=self.pin)

    def test_tree_ancestor_symlink_rejected(self):
        alias = self.root.parent / "parent_alias"
        alias.symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): verify_tree(alias / "package", self.metadata, trusted_metadata_sha256=self.pin)

    def test_metadata_ancestor_symlink_rejected(self):
        alias = self.root.parent / "parent_alias"
        alias.symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): verify_tree(self.root, alias / "installed.json", trusted_metadata_sha256=self.pin)

    def test_verification_does_not_import_payload(self):
        # If execution occurred this body would raise immediately.
        body = b'raise RuntimeError("must never execute")\n'
        (self.root / "sample.py").write_bytes(body)
        self.doc["files"][0].update(installed_bytes=len(body), installed_sha256=hashlib.sha256(body).hexdigest())
        self.write_metadata()
        self.assertEqual(len(self.verify().files), 1)


if __name__ == "__main__":
    unittest.main()
