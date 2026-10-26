from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from examples.review_lab.provenance import (
    ProvenanceError, Reference, Registry, admit_parent, demonstration,
    sha256, synthetic_parent,
)


class ProvenanceTests(unittest.TestCase):
    decision = "2026-01-05T12:00:00Z"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "parent"
        self.pin, self.ref = synthetic_parent(self.bundle, "source-a")

    def admit(self, path=None, pin=None, parent_id="source-a"):
        return admit_parent(path or self.bundle, expected_parent_id=parent_id,
                            expected_manifest_sha256=pin or self.pin)

    def rewrite_manifest(self, update):
        path = self.bundle / "manifest.json"
        manifest = json.loads(path.read_bytes())
        update(manifest)
        body = json.dumps(manifest).encode()
        path.write_bytes(body)
        return sha256(body)

    def test_relocation_preserves_bytes_identity_and_clock(self):
        moved = self.root / "restored" / "parent"
        moved.parent.mkdir()
        shutil.move(str(self.bundle), moved)
        result = Registry([self.admit(path=moved)]).read(self.ref, decision_at=self.decision)
        self.assertFalse(self.bundle.exists())
        self.assertEqual(result.content, b'{"value": 7}\n')
        self.assertEqual(result.reference, self.ref)

    def test_two_parents_with_same_relative_key_remain_distinct(self):
        other = self.root / "other"
        pin, ref = synthetic_parent(other, "source-b", payload=b'{"value": 99}\n')
        registry = Registry([self.admit(), self.admit(other, pin, "source-b")])
        self.assertEqual(self.ref.key, ref.key)
        self.assertNotEqual(registry.read(self.ref, decision_at=self.decision).content,
                            registry.read(ref, decision_at=self.decision).content)

    def test_omitted_parent_does_not_search_nearby_valid_bundle(self):
        other = self.root / "other"
        _, ref = synthetic_parent(other, "source-b")
        with self.assertRaisesRegex(ProvenanceError, "not admitted"):
            Registry([self.admit()]).read(ref, decision_at=self.decision)

    def test_duplicate_parent_identity_is_rejected(self):
        admitted = self.admit()
        with self.assertRaisesRegex(ProvenanceError, "duplicate admitted parent"):
            Registry([admitted, admitted])

    def test_wrong_parent_manifest_is_rejected(self):
        with self.assertRaisesRegex(ProvenanceError, "parent identity"):
            self.admit(parent_id="other")

    def test_wrong_manifest_digest_is_rejected(self):
        with self.assertRaisesRegex(ProvenanceError, "manifest identity"):
            self.admit(pin="0" * 64)

    def test_manifest_change_after_admission_is_rejected(self):
        registry = Registry([self.admit()])
        (self.bundle / "manifest.json").write_bytes(b'{}')
        with self.assertRaisesRegex(ProvenanceError, "manifest changed"):
            registry.read(self.ref, decision_at=self.decision)

    def test_same_size_changed_content_is_rejected(self):
        registry = Registry([self.admit()])
        (self.bundle / self.ref.key).write_bytes(b'{"value": 8}\n')
        with self.assertRaisesRegex(ProvenanceError, "content identity"):
            registry.read(self.ref, decision_at=self.decision)

    def test_missing_artifact_is_not_replaced_with_same_named_neighbor(self):
        registry = Registry([self.admit()])
        (self.bundle / self.ref.key).unlink()
        neighbor = self.root / "sample.json"
        neighbor.write_bytes(b'{"value": 7}\n')
        with self.assertRaisesRegex(ProvenanceError, "missing"):
            registry.read(self.ref, decision_at=self.decision)

    def test_undeclared_member_is_rejected_even_when_content_matches(self):
        (self.bundle / "other.json").write_bytes(b'{"value": 7}\n')
        with self.assertRaisesRegex(ProvenanceError, "pinned manifest"):
            Registry([self.admit()]).read(replace(self.ref, key="other.json"), decision_at=self.decision)

    def test_forged_clock_does_not_override_manifest(self):
        with self.assertRaisesRegex(ProvenanceError, "pinned manifest"):
            Registry([self.admit()]).read(replace(self.ref, observed_at="2025-01-01T00:00:00Z"), decision_at=self.decision)

    def test_decision_must_be_strictly_after_observation(self):
        for decision in [self.ref.observed_at, "2026-01-03T00:00:00Z"]:
            with self.subTest(decision=decision), self.assertRaisesRegex(ProvenanceError, "before the decision"):
                Registry([self.admit()]).read(self.ref, decision_at=decision)

    def test_timezones_are_compared_by_instant(self):
        result = Registry([self.admit()]).read(self.ref, decision_at="2026-01-04T05:00:01-07:00")
        self.assertEqual(result.reference.observed_at, self.ref.observed_at)

    def test_naive_or_invalid_clock_is_rejected(self):
        for value in ["2026-01-01T00:00:00", "not-a-date", None]:
            with self.subTest(value=value), self.assertRaises(ProvenanceError):
                replace(self.ref, observed_at=value)

    def test_unsafe_reference_paths_are_rejected(self):
        for key in ["../sample.json", "/tmp/sample.json", "a/../b", "a//b", "./sample.json", "a\\b", "C:/sample.json", "", "a\x00b"]:
            with self.subTest(key=key), self.assertRaises(ProvenanceError):
                replace(self.ref, key=key)

    def test_unsafe_manifest_member_is_rejected(self):
        pin = self.rewrite_manifest(lambda m: m["entries"][0].update(key="../sample.json"))
        with self.assertRaises(ProvenanceError):
            self.admit(pin=pin)

    def test_manifest_duplicate_entries_are_rejected(self):
        pin = self.rewrite_manifest(lambda m: m["entries"].append(dict(m["entries"][0])))
        with self.assertRaisesRegex(ProvenanceError, "duplicate artifact"):
            self.admit(pin=pin)

    def test_manifest_duplicate_json_fields_are_rejected(self):
        body = b'{"schema":"public-synthetic-parent-v1","schema":"public-synthetic-parent-v1"}'
        (self.bundle / "manifest.json").write_bytes(body)
        with self.assertRaisesRegex(ProvenanceError, "duplicate manifest"):
            self.admit(pin=sha256(body))

    def test_invalid_size_and_hash_are_rejected(self):
        for field, value in [("size_bytes", -1), ("size_bytes", True), ("content_sha256", "x" * 64)]:
            with self.subTest(field=field), self.assertRaises(ProvenanceError):
                replace(self.ref, **{field: value})

    def test_final_symlink_is_rejected_even_to_matching_bytes(self):
        other = self.root / "outside.json"
        shutil.copyfile(self.bundle / self.ref.key, other)
        (self.bundle / self.ref.key).unlink()
        (self.bundle / self.ref.key).symlink_to(other)
        with self.assertRaisesRegex(ProvenanceError, "symbolic"):
            Registry([self.admit()]).read(self.ref, decision_at=self.decision)

    def test_directory_symlink_is_rejected(self):
        outside = self.root / "outside"
        shutil.move(str(self.bundle / "observations"), outside)
        (self.bundle / "observations").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ProvenanceError, "symbolic"):
            Registry([self.admit()]).read(self.ref, decision_at=self.decision)

    def test_verified_bytes_are_returned_not_a_mutable_path(self):
        result = Registry([self.admit()]).read(self.ref, decision_at=self.decision)
        (self.bundle / self.ref.key).write_bytes(b'changed after verified read')
        self.assertEqual(result.content, b'{"value": 7}\n')

    def test_demo_shows_failure_recovery_and_tamper_without_fits(self):
        result = demonstration()
        self.assertEqual(result["parents_recovered"], ["alpha", "beta"])
        self.assertEqual(result["values"], [7, 11])
        self.assertEqual(result["new_fits"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertTrue(result["observation_clocks_preserved"])
        self.assertIn("not admitted", result["omitted_parent"])
        self.assertIn("content identity", result["tampered_content"])


if __name__ == "__main__":
    unittest.main()
