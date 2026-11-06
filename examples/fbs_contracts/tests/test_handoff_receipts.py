"""Adversarial invented receipts; no owner execution or provider calls."""
from dataclasses import replace
import subprocess
import sys
import unittest

from examples.fbs_contracts.handoff_receipts import (
    Pin, Release, invented_fixture, registry, verify,
)


class HandoffReceiptTests(unittest.TestCase):
    def setUp(self):
        self.receipt, self.terminal, self.approved, self.source, self.archive = invented_fixture()

    def check(self, receipt=None, terminal=None, **changes):
        args = dict(approved=self.approved, expected_run=self.receipt.run,
                    source_bytes=self.source, archive_bytes=self.archive)
        args.update(changes)
        return verify(receipt or self.receipt, terminal or self.terminal, **args)

    def test_registry_cannot_replace_required_old_release_with_new(self):
        entries = (Release("example-one", Pin.of(b"one")), Release("example-three", Pin.of(b"three")))
        with self.assertRaisesRegex(ValueError, "Required predecessor missing"):
            registry(entries, ("example-one", "example-two"))
        entries += (Release("example-two", Pin.of(b"two")),)
        self.assertEqual(set(registry(entries, ("example-one", "example-two"))),
                         {"example-one", "example-two", "example-three"})

    def test_duplicate_source_registration_cannot_overwrite_an_earlier_commitment(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            registry((Release("example-two", Pin.of(b"one")),
                      Release("example-two", Pin.of(b"changed"))), ("example-two",))

    def test_unknown_release_is_not_inferred_from_version_order(self):
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            self.check(replace(self.receipt, release="example-four"))

    def test_changed_source_or_archive_is_rejected(self):
        for argument in ("source_bytes", "archive_bytes"):
            with self.subTest(argument=argument), self.assertRaises(ValueError):
                self.check(**{argument: b"different bytes"})

    def test_return_hash_cannot_substitute_for_run_identity(self):
        with self.assertRaisesRegex(ValueError, "Run identity"):
            self.check(terminal=replace(self.terminal, run="another-invented-run"))

    def test_matching_diagnostic_is_preserved_with_unknown_process_exit(self):
        result = self.check()
        self.assertEqual(result["classification"], "PARTIAL_BEFORE_ADMISSION")
        self.assertIsNone(result["process_exit"])
        self.assertFalse(result["process_exit_verified"])
        self.assertFalse(result["successful_collection_claimed"])
        self.assertFalse(result["next_writer_admitted"])

    def test_observed_conflicting_process_exit_is_not_silently_discarded(self):
        with self.assertRaisesRegex(ValueError, "Observed process exit differs"):
            self.check(terminal=replace(self.terminal, process_exit=0))
        self.assertTrue(self.check(terminal=replace(self.terminal, process_exit=2))["process_exit_verified"])

    def test_pre_admission_cannot_claim_work_or_writer_ownership(self):
        for change in ({"source_units": 1}, {"model_fits": 1}, {"forecast_issues": 1},
                       {"writer_lock_held": True}, {"phase": "COLLECTION"}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "Pre-admission"):
                self.check(replace(self.receipt, **change))

    def test_partial_collection_keeps_work_without_claiming_full_success(self):
        receipt = replace(self.receipt, phase="COLLECTION", owner_admitted=True,
                          writer_lock_held=True, source_units=3)
        result = self.check(receipt, replace(self.terminal, process_exit=2))
        self.assertEqual(result["preserved_source_units"], 3)
        self.assertFalse(result["successful_collection_claimed"])
        self.assertFalse(result["next_writer_admitted"])

    def test_complete_diagnostic_requires_observed_process_exit_for_success(self):
        receipt = replace(self.receipt, declared_exit=0, status="COMPLETE", phase="COLLECTION",
                          owner_admitted=True, writer_lock_held=True, source_units=3)
        terminal = replace(self.terminal, declared_exit=0)
        self.assertFalse(self.check(receipt, terminal)["successful_collection_claimed"])
        self.assertTrue(self.check(receipt, replace(terminal, process_exit=0))["successful_collection_claimed"])

    def test_terminal_marker_and_status_must_match(self):
        with self.assertRaisesRegex(ValueError, "Declared exit"):
            self.check(terminal=replace(self.terminal, declared_exit=0))
        with self.assertRaisesRegex(ValueError, "Status and declared exit"):
            self.check(replace(self.receipt, status="COMPLETE"))

    def test_external_completion_must_follow_archive_and_clocks_need_timezone(self):
        for timestamp in ("2020-01-01T00:00:02Z", "2020-01-01T00:00:01Z", "2020-01-01T00:00:03"):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                self.check(replace(self.receipt, completed_at=timestamp))

    def test_boolean_counts_are_not_integer_work(self):
        with self.assertRaisesRegex(ValueError, "Invalid work accounting"):
            self.check(replace(self.receipt, source_units=True))

    def test_returned_integer_is_not_an_interpreter_exit(self):
        invented = "def main():\n    return 2\n"
        dropped = subprocess.run([sys.executable, "-I", "-c", invented + "main()\n"],
                                 capture_output=True, check=False)
        propagated = subprocess.run([sys.executable, "-I", "-c", invented + "raise SystemExit(main())\n"],
                                    capture_output=True, check=False)
        self.assertEqual(dropped.returncode, 0)
        self.assertEqual(propagated.returncode, 2)


if __name__ == "__main__":
    unittest.main()
