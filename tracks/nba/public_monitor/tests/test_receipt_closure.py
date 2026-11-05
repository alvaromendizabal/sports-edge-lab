"""Invented ZIP fixtures exercise the complete receipt boundary without mocks."""
import copy
import hashlib
import io
import json
import stat
import unittest
import warnings
import zipfile

from tracks.nba.public_monitor.receipt_closure import (
    MANIFEST_NAME, MANIFEST_SCHEMA, ReceiptError, normalize_reference,
    verify_receipt_archive,
)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def archive_bytes(payloads, *, manifest=None, extra=(), modes=None, systems=None):
    if manifest is None:
        manifest = {"schema": MANIFEST_SCHEMA, "payload_members": len(payloads),
                    "files": {name: pin(raw) for name, raw in payloads.items()}}
    raw_manifest = manifest if isinstance(manifest, bytes) else json.dumps(manifest).encode()
    result = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, raw in [*payloads.items(), (MANIFEST_NAME, raw_manifest), *extra]:
                info = zipfile.ZipInfo(name)
                info.create_system = (systems or {}).get(name, 3)
                info.external_attr = (modes or {}).get(name, stat.S_IFREG | 0o644) << 16
                archive.writestr(info, raw)
    return result.getvalue()


def fixture(**changes):
    payloads = {"data/toy.txt": b"entirely invented payload",
                "notes/empty.txt": b"", "notes/context.txt": b"invented context"}
    raw = archive_bytes(payloads, **changes)
    reference = {"object_id": "invented-archive-alpha", **pin(raw)}
    descriptor = {"object_id": reference["object_id"],
                  "object_bytes": reference["bytes"],
                  "object_sha256": reference["sha256"],
                  "member": "data/toy.txt", **pin(payloads["data/toy.txt"])}
    descriptors = {"first/toy.txt": copy.deepcopy(descriptor),
                   "retained/toy.txt": copy.deepcopy(descriptor)}
    return raw, reference, descriptors


def repin(raw, reference, descriptors):
    reference = {**reference, **pin(raw)}
    descriptors = {alias: {**value, "object_bytes": reference["bytes"],
                          "object_sha256": reference["sha256"]}
                   for alias, value in descriptors.items()}
    return reference, descriptors


class LogicalDescriptorContracts(unittest.TestCase):
    def test_legacy_reference_reaches_real_verifier_with_alias_count(self):
        raw, reference, descriptors = fixture()
        self.assertNotIn("reference_members", reference)
        receipt = verify_receipt_archive(raw, reference, descriptors)
        self.assertEqual((receipt.physical_members, receipt.payload_members,
                          receipt.logical_descriptors, receipt.unique_referenced_members),
                         (4, 3, 2, 1))
        self.assertEqual(receipt.verification_scope, "SUPPLIED_BYTES_ONLY")

    def test_adapter_preserves_identity_fields_and_complete_alias_map(self):
        _, reference, descriptors = fixture()
        reference["locator"] = {"partition": "invented", "labels": ["alpha"]}
        before_reference, before_descriptors = copy.deepcopy(reference), copy.deepcopy(descriptors)
        normalized = normalize_reference(reference, descriptors)
        self.assertEqual(normalized, {**before_reference, "reference_members": 2})
        normalized["locator"]["labels"].append("new")
        self.assertEqual(reference, before_reference)
        self.assertEqual(descriptors, before_descriptors)

    def test_v2_matching_explicit_count_and_v1_optional_count(self):
        raw, reference, descriptors = fixture()
        for schema in ("receipt-reference.v1", "receipt-reference.v2"):
            with self.subTest(schema=schema):
                receipt = verify_receipt_archive(raw, {**reference, "schema": schema,
                                                       "reference_members": 2}, descriptors)
                self.assertEqual(receipt.logical_descriptors, 2)

    def test_count_cannot_be_unique_members_or_physical_payloads(self):
        raw, reference, descriptors = fixture()
        for count in (1, 3, 4, 0, -1, True, 2.0, "2", None):
            with self.subTest(count=count):
                with self.assertRaisesRegex(ReceiptError, "LOGICAL_DESCRIPTOR_COUNT"):
                    verify_receipt_archive(raw, {**reference, "reference_members": count}, descriptors)

    def test_missing_v2_field_and_unknown_versions_fail_closed(self):
        _, reference, descriptors = fixture()
        for fields in ({"schema": "receipt-reference.v2"},
                       {"schema": "receipt-reference.v9"}, {"schema": None}):
            with self.subTest(fields=fields), self.assertRaises(ReceiptError):
                normalize_reference({**reference, **fields}, descriptors)

    def test_removing_an_alias_cannot_satisfy_a_pinned_logical_count(self):
        raw, reference, descriptors = fixture()
        descriptors.pop("retained/toy.txt")
        with self.assertRaisesRegex(ReceiptError, "LOGICAL_DESCRIPTOR_COUNT"):
            verify_receipt_archive(raw, {**reference, "reference_members": 2}, descriptors)

    def test_repeat_aliases_must_keep_the_same_member_pin(self):
        raw, reference, descriptors = fixture()
        descriptors["retained/toy.txt"]["sha256"] = "a" * 64
        with self.assertRaisesRegex(ReceiptError, "CONFLICTING_MEMBER_PIN"):
            verify_receipt_archive(raw, reference, descriptors)

    def test_each_alias_binds_the_object_identity_and_both_object_pins(self):
        raw, reference, descriptors = fixture()
        for key, wrong in (("object_id", "other-invented-object"),
                           ("object_bytes", len(raw) + 1), ("object_sha256", "0" * 64)):
            changed = copy.deepcopy(descriptors)
            changed["retained/toy.txt"][key] = wrong
            with self.subTest(key=key), self.assertRaisesRegex(ReceiptError, "DESCRIPTOR_OBJECT"):
                verify_receipt_archive(raw, reference, changed)

    def test_logical_paths_must_be_safe_and_casefold_unique(self):
        raw, reference, descriptors = fixture()
        descriptor = next(iter(descriptors.values()))
        for name in ("../escape", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "C:drive", "", "a\x00b"):
            with self.subTest(name=name), self.assertRaisesRegex(ReceiptError, "UNSAFE_LOGICAL"):
                verify_receipt_archive(raw, reference, {name: descriptor})
        with self.assertRaisesRegex(ReceiptError, "CASEFOLD_LOGICAL"):
            verify_receipt_archive(raw, reference, {"Alias": descriptor, "alias": descriptor})

    def test_zero_descriptors_is_explicit_not_an_exception_fallback(self):
        raw, reference, _ = fixture()
        result = verify_receipt_archive(raw, {**reference, "reference_members": 0}, {})
        self.assertEqual(result.logical_descriptors, 0)
        self.assertEqual(result.payload_members, 3)
        with self.assertRaisesRegex(ReceiptError, "DESCRIPTOR_MAP_REQUIRED"):
            verify_receipt_archive(raw, reference, None)


class PhysicalArchiveContracts(unittest.TestCase):
    def test_whole_object_byte_and_digest_pins_are_checked(self):
        raw, reference, descriptors = fixture()
        with self.assertRaisesRegex(ReceiptError, "ARCHIVE_BYTE_COUNT"):
            verify_receipt_archive(raw + b"x", reference, descriptors)
        changed = raw[:-1] + bytes([raw[-1] ^ 1])
        with self.assertRaisesRegex(ReceiptError, "ARCHIVE_SHA256"):
            verify_receipt_archive(changed, reference, descriptors)

    def test_payload_sha_and_byte_pins_remain_required_after_outer_repin(self):
        for wrong_pin in ({"bytes": 99, "sha256": hashlib.sha256(b"invented").hexdigest()},
                          {"bytes": 8, "sha256": "0" * 64}):
            raw = archive_bytes({"toy.txt": b"invented"}, manifest={
                "schema": MANIFEST_SCHEMA, "files": {"toy.txt": wrong_pin}})
            with self.subTest(pin=wrong_pin), self.assertRaisesRegex(ReceiptError, "MEMBER_"):
                verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_crc_corruption_is_rejected_even_with_matching_outer_pin(self):
        raw, reference, descriptors = fixture()
        damaged = raw.replace(b"entirely invented payload", b"entirely invented payloaD", 1)
        reference, descriptors = repin(damaged, reference, descriptors)
        with self.assertRaisesRegex(ReceiptError, "ZIP_READ_OR_INTEGRITY_ERROR"):
            verify_receipt_archive(damaged, reference, descriptors)

    def test_unmanifested_and_missing_payloads_fail_exact_closure(self):
        raw, reference, descriptors = fixture(extra=[("unlisted.txt", b"invented")])
        with self.assertRaisesRegex(ReceiptError, "EXACT_PAYLOAD_CLOSURE"):
            verify_receipt_archive(raw, reference, descriptors)
        raw = archive_bytes({}, manifest={"schema": MANIFEST_SCHEMA,
                                        "files": {"missing.txt": pin(b"invented")}})
        with self.assertRaisesRegex(ReceiptError, "EXACT_PAYLOAD_CLOSURE"):
            verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_reference_to_manifest_or_absent_member_is_rejected(self):
        raw, reference, descriptors = fixture()
        for target, reason in ((MANIFEST_NAME, "DESCRIPTOR_PAYLOAD_PATH"),
                               ("absent.txt", "REFERENCED_MEMBER_MISSING")):
            changed = {alias: {**d, "member": target} for alias, d in descriptors.items()}
            with self.subTest(target=target), self.assertRaisesRegex(ReceiptError, reason):
                verify_receipt_archive(raw, reference, changed)

    def test_descriptor_member_pins_must_match_manifest(self):
        raw, reference, descriptors = fixture()
        changed = {alias: {**d, "sha256": "b" * 64} for alias, d in descriptors.items()}
        with self.assertRaisesRegex(ReceiptError, "REFERENCED_MEMBER_PIN"):
            verify_receipt_archive(raw, reference, changed)

    def test_manifest_itself_requires_explicit_regular_type(self):
        raw, reference, descriptors = fixture(modes={MANIFEST_NAME: 0o600})
        with self.assertRaisesRegex(ReceiptError, "EXPLICIT_REGULAR_FILE_REQUIRED"):
            verify_receipt_archive(raw, reference, descriptors)

    def test_permissions_alone_symlinks_directories_and_unknown_origin_are_not_regular(self):
        for mode, system in ((0o644, 3), (stat.S_IFLNK | 0o777, 3),
                             (stat.S_IFDIR | 0o755, 3), (stat.S_IFIFO | 0o644, 3),
                             (stat.S_IFREG | 0o644, 0)):
            raw, reference, descriptors = fixture(modes={"data/toy.txt": mode},
                                                   systems={"data/toy.txt": system})
            with self.subTest(mode=oct(mode), system=system):
                with self.assertRaisesRegex(ReceiptError, "EXPLICIT_REGULAR_FILE_REQUIRED"):
                    verify_receipt_archive(raw, reference, descriptors)

    def test_explicit_read_only_regular_file_is_accepted(self):
        raw, reference, descriptors = fixture(modes={"data/toy.txt": stat.S_IFREG | 0o400})
        self.assertEqual(verify_receipt_archive(raw, reference, descriptors).payload_members, 3)

    def test_duplicate_and_casefold_colliding_zip_paths_are_rejected(self):
        for name, reason in (("data/toy.txt", "DUPLICATE_ZIP"),
                             ("DATA/TOY.TXT", "CASEFOLD_ZIP")):
            raw, reference, descriptors = fixture(extra=[(name, b"invented")])
            with self.subTest(name=name), self.assertRaisesRegex(ReceiptError, reason):
                verify_receipt_archive(raw, reference, descriptors)

    def test_unsafe_zip_paths_are_rejected_before_manifest_admission(self):
        for name in ("../escape", "/absolute", "a//b", "a\\b", "C:drive", "directory/"):
            raw, reference, descriptors = fixture(extra=[(name, b"invented")])
            with self.subTest(name=name), self.assertRaisesRegex(ReceiptError, "UNSAFE_ZIP"):
                verify_receipt_archive(raw, reference, descriptors)

    def test_nul_truncated_zip_name_is_rejected(self):
        raw, reference, descriptors = fixture()
        raw = raw.replace(b"data/toy.txt", b"data/toy\x00txt")
        reference, descriptors = repin(raw, reference, descriptors)
        with self.assertRaisesRegex(ReceiptError, "TRUNCATED_ZIP_NAME"):
            verify_receipt_archive(raw, reference, descriptors)

    def test_duplicate_manifest_keys_are_not_overwritten_by_json_decode(self):
        for raw_manifest in (b'{"schema":"receipt-payload-manifest.v1","files":{},"files":{}}',
                             b'{"schema":"receipt-payload-manifest.v1","files":{"x":{"bytes":0,"bytes":1}}}'):
            raw = archive_bytes({}, manifest=raw_manifest)
            with self.subTest(manifest=raw_manifest), self.assertRaisesRegex(ReceiptError, "DUPLICATE_JSON_KEY"):
                verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_unknown_manifest_schema_and_nonfinite_json_fail_closed(self):
        for manifest, reason in (({"schema": "receipt-payload-manifest.v9", "files": {}}, "UNSUPPORTED_MANIFEST_SCHEMA"),
                                 (b'{"schema":"receipt-payload-manifest.v1","files":{},"other":NaN}', "NONFINITE_JSON_NUMBER")):
            raw = archive_bytes({}, manifest=manifest)
            with self.subTest(manifest=manifest), self.assertRaisesRegex(ReceiptError, reason):
                verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_manifest_count_is_physical_payload_count(self):
        raw = archive_bytes({"toy.txt": b"invented"}, manifest={
            "schema": MANIFEST_SCHEMA, "payload_members": 2,
            "files": {"toy.txt": pin(b"invented")}})
        with self.assertRaisesRegex(ReceiptError, "PHYSICAL_PAYLOAD_COUNT"):
            verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_limits_fail_without_partial_success(self):
        raw, reference, descriptors = fixture()
        for limits, reason in (({"max_members": 3}, "ARCHIVE_MEMBER_LIMIT"),
                               ({"max_uncompressed_bytes": 1}, "ARCHIVE_UNCOMPRESSED_LIMIT"),
                               ({"max_members": True}, "INVALID_RESOURCE_LIMIT")):
            with self.subTest(limits=limits), self.assertRaisesRegex(ReceiptError, reason):
                verify_receipt_archive(raw, reference, descriptors, **limits)

    def test_invalid_zip_does_not_become_an_empty_receipt(self):
        raw = b"invented non-ZIP bytes"
        with self.assertRaisesRegex(ReceiptError, "ZIP_READ_OR_INTEGRITY_ERROR"):
            verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})

    def test_empty_regular_payload_is_verified(self):
        raw = archive_bytes({"empty.txt": b""})
        receipt = verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})
        self.assertEqual(receipt.payload_members, 1)

    def test_boolean_member_byte_count_is_not_integer_evidence(self):
        raw = archive_bytes({"empty.txt": b""}, manifest={"schema": MANIFEST_SCHEMA,
            "files": {"empty.txt": {"bytes": False, "sha256": hashlib.sha256(b"").hexdigest()}}})
        with self.assertRaisesRegex(ReceiptError, "MANIFEST_PIN_SCHEMA"):
            verify_receipt_archive(raw, {"object_id": "toy", **pin(raw)}, {})


if __name__ == "__main__":
    unittest.main()
