import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from examples.basketball_contracts.continuation import (
    Fold, active_floor, fixture_authority, inherit_authority, isolate_folds,
    remaining, validate_continuation, walkthrough,
)
from examples.basketball_contracts.recovery_plan import (
    Budget, Capability, Catalog, Need, Quota, QuotaJournal, SCHEMA, SnapshotRequest,
    digest, encoded, plan_recovery,
)


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.original, self.window = fixture_authority()
        self.source = digest({"invented_source": "B"})
        self.pins = {"authorization_pin": digest(self.original), "window_pin": digest(self.window)}
        self.receipt = inherit_authority(self.original, self.window, self.source, **self.pins)

    def test_exact_original_objects_and_limits_survive_release_change(self):
        self.assertEqual(self.receipt["original_authorization"], self.original)
        self.assertEqual(self.receipt["original_window"], self.window)
        self.assertEqual(self.receipt["absolute_limits"]["archive_pages"], 15)
        self.assertEqual(self.receipt["additional_allowance"], 0)
        self.assertEqual(validate_continuation(self.receipt, self.source, **self.pins), self.receipt)

    def test_independent_copy(self):
        self.receipt["original_window"]["counters_before_release"]["archive_pages"] = 11
        self.assertEqual(self.window["counters_before_release"]["archive_pages"], 3)

    def test_new_baseline_cannot_renew_allowance(self):
        self.receipt["original_window"]["counters_before_release"]["archive_pages"] = 11
        with self.assertRaises(ValueError):
            validate_continuation(self.receipt, self.source, **self.pins)

    def test_changed_source_caps_or_extra_authority_fail(self):
        for field, value in (("source_sha256", "0" * 64), ("additional_allowance", 1),
                ("absolute_limits", {"archive_pages": 99})):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt); receipt[field] = value
                with self.assertRaises(ValueError):
                    validate_continuation(receipt, self.source, **self.pins)

    def test_missing_original_paid_consent_cannot_be_inherited(self):
        self.original["paid_approved"] = False
        auth = digest(self.original); self.window["authorization_sha256"] = auth
        with self.assertRaises(ValueError):
            inherit_authority(self.original, self.window, self.source,
                authorization_pin=auth, window_pin=digest(self.window))

    def test_actual_counters_reduce_original_allowance(self):
        usage = {"active_seconds": 340, "public_requests": 7, "provider_requests": 1,
            "provider_credits": 10, "archive_pages": 11}
        result = remaining(self.receipt, usage, source_sha256=self.source, **self.pins)
        self.assertEqual(result["archive_pages"], 4)
        self.assertEqual(result["active_seconds"], 260)
        for value in (0, 16, True):
            usage["archive_pages"] = value
            with self.assertRaises(ValueError):
                remaining(self.receipt, usage, source_sha256=self.source, **self.pins)

    def test_missing_counter_is_not_zero(self):
        with self.assertRaises(ValueError):
            remaining(self.receipt, {}, source_sha256=self.source, **self.pins)

    def test_missing_closure_carries_reservation_without_calling_it_measured(self):
        self.assertEqual(active_floor(310, 340), 340)
        self.assertEqual(active_floor(310, 340, verified_closed_seconds=315), 315)

    def test_late_closure_cannot_refund_adopted_work(self):
        self.assertEqual(active_floor(310, 340, verified_closed_seconds=315, adopted_floor=340), 340)
        with self.assertRaises(ValueError):
            active_floor(310, 340, verified_closed_seconds=300)

    def test_support_failure_leaves_other_registered_folds_eligible(self):
        protocol = digest({"invented_fixed_threshold": 10})
        folds = [Fold(name, protocol, digest({"fold": name}), count, 10) for name, count in
            (("nba-A", 7), ("college-men-A", 25), ("college-women-A", 23))]
        results = isolate_folds(folds)
        self.assertEqual([row["status"] for row in results],
            ["BLOCKED_SUPPORT", "ELIGIBLE_PREFLIGHT", "ELIGIBLE_PREFLIGHT"])
        self.assertEqual([fold.minimum_calibration for fold in folds], [10, 10, 10])

    def test_identity_and_other_integrity_errors_do_not_become_support_skips(self):
        fold = Fold("nba-A", "1" * 64, "2" * 64, 11, 10)
        with self.assertRaisesRegex(ValueError, "cohort identity"):
            isolate_folds([fold], prepare=lambda _: {"eligible": True, "fold_sha256": "3" * 64})
        def broken(_):
            raise OSError("corrupt input")
        with self.assertRaises(OSError):
            isolate_folds([fold], prepare=broken)

    def test_walkthrough_separates_invented_journal_from_actual_execution(self):
        output = walkthrough()
        self.assertTrue(output["synthetic"])
        self.assertEqual(output["actual_model_fits"], 0)
        self.assertEqual(output["actual_requests"], 0)
        self.assertEqual(output["journal_after_lost_response"]["credits_charged_or_reserved"], 10)
        self.assertEqual(output["journal_after_zero_credit_receipt"]["credits_charged_or_reserved"], 0)
        self.assertEqual(output["journal_after_zero_credit_receipt"]["requests_used"], 1)


class RequestProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.now = "2026-10-28T20:00:00Z"
        self.at = "2025-01-01T19:00:00Z"
        self.request = SnapshotRequest("basketball_nba", self.at, ("h2h",), ("us",))
        self.budget = Budget(4, 0, 100, 0, "a" * 64)
        self.quota = Quota(100, self.now, "b" * 64)

    def test_lost_response_reentry_does_not_send_again_or_drop_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            first = QuotaJournal(path, self.budget)
            first.reserve("invented-attempt", self.request, self.quota, self.now)
            before = path.read_bytes()
            reopened = QuotaJournal(path, self.budget)
            repeat = reopened.reserve("invented-attempt", self.request, self.quota, self.now)
            self.assertFalse(repeat["new_reservation"])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(reopened.state()["pending_attempts"], 1)
            self.assertEqual(reopened.state()["credits_charged_or_reserved"], 10)

    def test_response_completion_is_immutable_and_zero_cost_still_counts_request(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            journal = QuotaJournal(path, self.budget)
            journal.reserve("invented-attempt", self.request, self.quota, self.now)
            journal.complete("invented-attempt", 0, "c" * 64, self.now)
            before = path.read_bytes()
            journal.complete("invented-attempt", 0, "c" * 64, self.now)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(journal.state()["requests_used"], 1)
            self.assertEqual(journal.state()["credits_charged_or_reserved"], 0)
            with self.assertRaises(ValueError):
                journal.complete("invented-attempt", 1, "d" * 64, self.now)
            with self.assertRaises(ValueError):
                QuotaJournal(path, Budget(8, 0, 200, 0, "a" * 64)).state()

    def test_empty_capture_keeps_original_response_provenance_and_no_duplicate_plan(self):
        need = Need("nba", "invented-game", "invented-provider", "invented-home", "invented-away",
            "2025-01-01T20:00:00Z", self.at, "e" * 64)
        payload = encoded({"schema": SCHEMA, "sport_key": "basketball_nba",
            "snapshot_at": self.at, "records": []})
        catalog = Catalog(); content = hashlib.sha256(payload).hexdigest()
        catalog.add("invented-cache", payload, content, self.request, self.now)
        catalog.seal("f" * 64)
        capability = Capability("basketball_nba", "2020-07-01T00:00:00Z", ("h2h",), ("us",), True,
            self.now, "2026-10-28T21:00:00Z", "1" * 64)
        plan = plan_recovery([need], catalog, [capability], self.budget, self.quota, self.now)
        cell = plan["cells"][0]
        self.assertEqual(cell["gap_provenance"], "captured_request_without_eligible_observation")
        self.assertEqual(cell["inventory_scope_sha256"], "f" * 64)
        self.assertEqual(cell["captured_request_receipts"][0]["content_sha256"], content)
        self.assertEqual(plan["planned_requests"], 0)
        self.assertEqual(plan["covered_cells"], 0)
        self.assertEqual(plan["expected_cells"], 1)


class ActualAggregateTests(unittest.TestCase):
    def test_actual_b008_outcome_and_preserved_dashboard(self):
        from examples.basketball_contracts.build_basketball_dashboard import load_evidence, validate
        data = load_evidence(); report = validate(data)
        self.assertEqual((report["scorecards"], report["populated_panels"], report["overlap_specifications"]), (235, 24, 120))
        outcome = data["execution_b008"]
        self.assertFalse(outcome["synthetic"])
        self.assertEqual(outcome["status"], "BLOCKED_DATA_CONTRACT")
        self.assertEqual(outcome["forecasts"]["archived_versions"], 440)
        self.assertEqual(outcome["forecasts"]["unique_games"], 61)
        self.assertEqual(outcome["new_real_fits"], 0)
        self.assertEqual(outcome["cumulative_real_estimator_units"], 238)

    def test_unsupported_owner_completion_and_settlement_fail(self):
        from examples.basketball_contracts.build_basketball_dashboard import load_evidence, validate
        for field, value in (("status", "SUCCESS"), ("new_real_fits", 30)):
            data = load_evidence(); data["execution_b008"][field] = value
            with self.assertRaises(ValueError):
                validate(data)
        data = load_evidence(); data["execution_b008"]["forecasts"]["settled_versions"] = 1
        with self.assertRaises(ValueError):
            validate(data)


if __name__ == "__main__":
    unittest.main()
