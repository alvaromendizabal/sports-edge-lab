"""Adversarial invented handoffs: no provider, cloud, credentials or model IO."""
import dataclasses
import hashlib
import unittest

from handoff import (Consumer, HandoffRejected, demo, execute_after_preflight,
                     invented_output, invented_registration, preflight)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.old = invented_registration(1)
        self.current = invented_registration(2)
        self.manifest, self.payload = invented_output(self.current)
        self.consumer = Consumer((self.old, self.current))

    def test_independent_component_success_does_not_admit_actual_handoff(self):
        report = demo()
        self.assertEqual(report["component_checks_passed"], 2)
        self.assertEqual(report["joined_handoff"], "UNREGISTERED_HANDOFF")
        self.assertEqual(report["actions_before_admission"], 0)
        self.assertFalse(report["real_owner_execution_claimed"])
        self.assertEqual(report["new_model_fit_credit"], 0)

    def test_exact_registered_identity_and_content_are_admitted(self):
        admitted = preflight(self.manifest, self.payload, self.consumer)
        self.assertEqual(admitted.producer, self.current)
        self.assertEqual(admitted.content_sha256, hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(admitted.content_bytes, len(self.payload))

    def test_identity_fields_cannot_be_mixed_from_individually_known_sources(self):
        for field in ("release", "run", "source_sha256", "artifact_prefix"):
            with self.subTest(field=field):
                identity = dataclasses.replace(self.current.identity,
                                               **{field: getattr(self.old.identity, field)})
                registration = dataclasses.replace(self.current, identity=identity)
                manifest = dataclasses.replace(self.manifest, producer=registration)
                with self.assertRaisesRegex(HandoffRejected, "UNREGISTERED_HANDOFF"):
                    preflight(manifest, self.payload, self.consumer)

    def test_other_project_is_rejected_even_with_all_other_fields_unchanged(self):
        identity = dataclasses.replace(self.current.identity, project="other_project")
        manifest = dataclasses.replace(self.manifest, producer=dataclasses.replace(self.current, identity=identity))
        with self.assertRaisesRegex(HandoffRejected, "UNREGISTERED_HANDOFF"):
            preflight(manifest, self.payload, self.consumer)

    def test_prefix_match_is_exact_and_not_a_startswith_allowance(self):
        identity = dataclasses.replace(self.current.identity,
                                       artifact_prefix=self.current.identity.artifact_prefix + "other/")
        manifest = dataclasses.replace(self.manifest, producer=dataclasses.replace(self.current, identity=identity))
        with self.assertRaisesRegex(HandoffRejected, "UNREGISTERED_HANDOFF"):
            preflight(manifest, self.payload, self.consumer)

    def test_prefix_traversal_ambiguous_and_external_forms_are_rejected(self):
        for prefix in ("/invented/", "invented//run/", "invented/../run/", "invented/./run/",
                       "invented\\run/", "https://example.test/", "invented/run", "invented/run /", ""):
            with self.subTest(prefix=prefix):
                identity = dataclasses.replace(self.current.identity, artifact_prefix=prefix)
                with self.assertRaisesRegex(HandoffRejected, "NONCANONICAL_PREFIX"):
                    identity.validate()

    def test_source_digest_must_be_canonical_full_hex(self):
        for digest in ("", "a" * 63, "g" * 64, "A" * 64, 123):
            with self.subTest(digest=digest):
                with self.assertRaisesRegex(HandoffRejected, "INVALID_SOURCE_DIGEST"):
                    dataclasses.replace(self.current.identity, source_sha256=digest).validate()

    def test_registered_identity_cannot_silently_change_format_or_artifact_kind(self):
        for fields in ({"wire_version": 3}, {"artifact_kind": "other_fixture"}):
            with self.subTest(fields=fields):
                manifest = dataclasses.replace(self.manifest, producer=dataclasses.replace(self.current, **fields))
                with self.assertRaisesRegex(HandoffRejected, "UNREGISTERED_HANDOFF"):
                    preflight(manifest, self.payload, self.consumer)

    def test_same_length_tamper_and_truncated_payload_are_rejected(self):
        for payload in (self.payload.replace(b"2", b"3"), self.payload[:-1]):
            with self.subTest(payload_length=len(payload)):
                with self.assertRaisesRegex(HandoffRejected, "CONTENT_PIN_MISMATCH"):
                    preflight(self.manifest, payload, self.consumer)

    def test_payload_pin_types_do_not_accept_boolean_counts(self):
        for count in (True, -1, float(len(self.payload))):
            with self.subTest(count=count):
                with self.assertRaisesRegex(HandoffRejected, "INVALID_CONTENT_PIN"):
                    preflight(dataclasses.replace(self.manifest, content_bytes=count), self.payload, self.consumer)

    def test_rehashing_modified_payload_does_not_reauthorize_the_receipt(self):
        payload = self.payload.replace(b"2", b"3")
        digest = hashlib.sha256(payload).hexdigest()
        manifest = dataclasses.replace(self.manifest, content_sha256=digest)
        with self.assertRaisesRegex(HandoffRejected, "MANIFEST_DISAGREES_WITH_REGISTERED_PIN"):
            preflight(manifest, payload, self.consumer)
        forged = dataclasses.replace(manifest, producer=dataclasses.replace(self.current, content_sha256=digest))
        forged.validate(payload)  # Self-consistency alone still passes.
        with self.assertRaisesRegex(HandoffRejected, "UNREGISTERED_HANDOFF"):
            preflight(forged, payload, self.consumer)

    def test_mutable_or_empty_registry_cannot_be_an_admission_anchor(self):
        for registry in ((), [self.current]):
            with self.subTest(registry=registry):
                with self.assertRaisesRegex(HandoffRejected, "EMPTY_OR_MUTABLE_REGISTRY"):
                    preflight(self.manifest, self.payload, Consumer(registry))

    def test_duplicate_or_conflicting_registration_has_no_last_writer_wins(self):
        changed = dataclasses.replace(self.current, identity=dataclasses.replace(
            self.current.identity, source_sha256=hashlib.sha256(b"conflicting invented source").hexdigest()))
        for second in (self.current, changed):
            with self.subTest(second=second):
                with self.assertRaisesRegex(HandoffRejected, "DUPLICATE_OR_CONFLICTING_REGISTRATION"):
                    preflight(self.manifest, self.payload, Consumer((self.current, second)))

    def test_no_action_begins_for_identity_or_content_rejection(self):
        calls = []
        for consumer, payload in ((Consumer((self.old,)), self.payload), (self.consumer, self.payload[:-1])):
            with self.assertRaises(HandoffRejected):
                execute_after_preflight(self.manifest, payload, consumer, lambda *_: calls.append("called"))
        self.assertEqual(calls, [])

    def test_exact_handoff_runs_once_with_the_validated_immutable_bytes(self):
        calls = []
        result = execute_after_preflight(self.manifest, self.payload, self.consumer,
            lambda admitted, payload: calls.append((admitted, payload)) or "finished")
        self.assertEqual(result, "finished")
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][1], self.payload)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            calls[0][0].content_bytes = 0

    def test_registry_order_does_not_change_the_admitted_identity(self):
        first = preflight(self.manifest, self.payload, self.consumer)
        second = preflight(self.manifest, self.payload, Consumer(tuple(reversed(self.consumer.registrations))))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
