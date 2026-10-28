"""Adversarial checks for lineage, accounting semantics and public redaction."""
import copy
from dataclasses import FrozenInstanceError, replace
import json
import unittest

from examples.review_lab.serving_lineage import (
    SOURCE, Issue, Ledger, PolicyIdentity, Selection, demo, validate_public_receipt, verify_binding)


class ServingLineageTests(unittest.TestCase):
    def setUp(self):
        self.policy = (PolicyIdentity("nfl", "invented_reference", "a" * 64, "market_fallback", False),)
        self.selection = Selection("b" * 64, "2026-01-01T00:00:00Z", (2023, 2024, 2025), self.policy)
        self.issue = Issue("b" * 64, "2026-01-02T00:00:00Z", self.policy, 5, 0)
        self.ledger = Ledger("b" * 64, "2026-01-02T00:01:00Z", self.policy)

    def check(self, selection=None, issue=None, ledger=None):
        return verify_binding(selection or self.selection, issue or self.issue, ledger or self.ledger)

    def test_valid_binding_does_not_certify_a_market_edge(self):
        result = self.check()
        self.assertEqual(result["reference_rows"], 5)
        self.assertFalse(result["economic_readiness_assessed"])
        self.assertFalse(result["predictive_superiority_assessed"])

    def test_changed_model_same_display_name_is_rejected(self):
        changed = replace(self.policy[0], rule_sha256="c" * 64)
        with self.assertRaisesRegex(ValueError, "policies differ"):
            self.check(issue=replace(self.issue, identities=(changed,)))

    def test_ledger_cannot_resurrect_a_different_policy(self):
        changed = replace(self.policy[0], policy_id="invented_postselected_champion")
        with self.assertRaisesRegex(ValueError, "policies differ"):
            self.check(ledger=replace(self.ledger, identities=(changed,)))

    def test_forecast_bound_to_wrong_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "selection content identity"):
            self.check(issue=replace(self.issue, selection_sha256="c" * 64))

    def test_ledger_bound_to_wrong_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "selection content identity"):
            self.check(ledger=replace(self.ledger, selection_sha256="c" * 64))

    def test_current_outcomes_cannot_enter_selection(self):
        with self.assertRaisesRegex(ValueError, "forward outcomes"):
            self.check(selection=replace(self.selection, seasons=(2023, 2024, 2025, 2026)))

    def test_backdated_model_availability_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "out of order"):
            self.check(selection=replace(self.selection, available_at="2026-01-03T00:00:00Z"))

    def test_ledger_before_issue_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "out of order"):
            self.check(ledger=replace(self.ledger, created_at="2026-01-01T00:00:00Z"))

    def test_timezone_normalization(self):
        issue = replace(self.issue, issued_at="2026-01-01T19:00:00-05:00")
        self.assertEqual(self.check(issue=issue), self.check())

    def test_naive_clock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            self.check(issue=replace(self.issue, issued_at="2026-01-02T00:00:00"))

    def test_bad_clock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid clock"):
            self.check(issue=replace(self.issue, issued_at="not a date"))

    def test_ambiguous_rule_pin_is_rejected(self):
        invalid = (replace(self.policy[0], rule_sha256="A" * 64),)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.check(selection=replace(self.selection, identities=invalid))

    def test_duplicate_league_policy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate league"):
            self.check(selection=replace(self.selection, identities=self.policy * 2))

    def test_mutable_policy_identifier_is_rejected(self):
        invalid = (replace(self.policy[0], policy_id=["invented"]),)
        with self.assertRaisesRegex(ValueError, "policy identifier"):
            self.check(selection=replace(self.selection, identities=invalid))

    def test_reference_cannot_be_called_learned_prediction(self):
        with self.assertRaisesRegex(ValueError, "market references counted"):
            self.check(issue=replace(self.issue, learned_rows=5))

    def test_unqualified_learned_policy_is_rejected(self):
        invalid = (replace(self.policy[0], policy_kind="learned"),)
        with self.assertRaisesRegex(ValueError, "unqualified learned"):
            self.check(selection=replace(self.selection, identities=invalid))

    def test_reference_cannot_claim_learned_qualification(self):
        invalid = (replace(self.policy[0], learned_policy_qualified=True),)
        with self.assertRaisesRegex(ValueError, "market reference is not"):
            self.check(selection=replace(self.selection, identities=invalid))

    def test_retrospective_backfill_flag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "retrospective"):
            self.check(ledger=replace(self.ledger, historical_policy_backdated=True))

    def test_legacy_exposed_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "retrospective"):
            self.check(ledger=replace(self.ledger, legacy_exposed_forecasts_used=True))

    def test_bool_is_not_a_count(self):
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            self.check(issue=replace(self.issue, reference_rows=True))

    def test_dataclasses_and_nested_identities_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.selection.available_at = "forged"
        with self.assertRaises(FrozenInstanceError):
            self.selection.identities[0].rule_sha256 = "forged"

    def test_mutable_identity_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "immutable tuple"):
            self.check(selection=replace(self.selection, identities=list(self.policy)))

    def test_demo_is_explicitly_invented(self):
        self.assertEqual(demo()["input_kind"], "INVENTED")


class PublicServingReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(SOURCE.read_text())

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def test_owner_counts_remain_distinct(self):
        result = validate_public_receipt(self.data)
        self.assertEqual(result["owner_tests"], 2595)
        self.assertEqual(result["reference_rows"], 83)
        self.assertEqual(result["learned_rows"], 0)
        self.assertEqual(result["separate_research_forecast_rows"], 7908)
        self.assertFalse(result["private_artifacts_reproduced"])

    def test_missing_profit_is_not_zero(self):
        self.data["ledger"]["historical_profit"] = 0
        with self.assertRaisesRegex(ValueError, "unavailable executable profit"):
            validate_public_receipt(self.data)

    def test_current_predictions_cannot_enter_public_receipt(self):
        self.data["issue"]["individual_forecasts"] = []
        with self.assertRaisesRegex(ValueError, "public issue fields"):
            validate_public_receipt(self.data)

    def test_private_weight_payload_is_rejected(self):
        self.data["selection"]["identities"][0]["weights"] = [1.0]
        with self.assertRaisesRegex(ValueError, "public policy fields"):
            validate_public_receipt(self.data)

    def test_private_cloud_path_is_rejected(self):
        self.data["owner"]["cloud_path"] = "invented-private-path"
        with self.assertRaisesRegex(ValueError, "public owner fields"):
            validate_public_receipt(self.data)

    def test_forward_outcome_use_is_rejected(self):
        self.data["selection"]["current_outcomes_used"] = True
        with self.assertRaisesRegex(ValueError, "forward selection"):
            validate_public_receipt(self.data)

    def test_missing_identity_audit_is_rejected(self):
        self.data["issue"]["identity_matches_selection"] = False
        with self.assertRaisesRegex(ValueError, "identity audit"):
            validate_public_receipt(self.data)

    def test_issue_scope_cannot_drop_a_league(self):
        del self.data["issue"]["reference_rows_by_league"]["nfl"]
        with self.assertRaisesRegex(ValueError, "issue scope"):
            validate_public_receipt(self.data)

    def test_stage_clock_is_not_model_availability(self):
        self.data["selection"]["available_at"] = str(self.data["owner"]["worker_seconds"])
        with self.assertRaisesRegex(ValueError, "clock"):
            validate_public_receipt(self.data)

    def test_duplicate_stage_double_count_is_rejected(self):
        self.data["performance_stages"].append(self.data["performance_stages"][0])
        with self.assertRaisesRegex(ValueError, "duplicate or invalid stage"):
            validate_public_receipt(self.data)

    def test_nonfinite_resource_metric_is_rejected(self):
        self.data["owner"]["tests_seconds"] = float("nan")
        with self.assertRaisesRegex(ValueError, "duration"):
            validate_public_receipt(self.data)

    def test_untested_count_bool_is_rejected(self):
        self.data["owner"]["owner_tests"] = True
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            validate_public_receipt(self.data)

    def test_zero_tests_cannot_claim_verified_receipt(self):
        self.data["owner"]["owner_tests"] = 0
        with self.assertRaisesRegex(ValueError, "executed checks"):
            validate_public_receipt(self.data)

    def test_impossible_stage_duration_is_rejected(self):
        self.data["performance_stages"][0]["seconds"] = 10000
        with self.assertRaisesRegex(ValueError, "exceed worker"):
            validate_public_receipt(self.data)

    def test_run_stage_duration_nesting_is_checked(self):
        self.data["owner"]["tests_seconds"] = self.data["owner"]["supervised_seconds"] + 1
        with self.assertRaisesRegex(ValueError, "nesting"):
            validate_public_receipt(self.data)

    def test_new_fits_are_not_invented(self):
        self.data["owner"]["new_fits"] = 20
        with self.assertRaisesRegex(ValueError, "zero-fit"):
            validate_public_receipt(self.data)

    def test_actual_trade_claim_is_rejected(self):
        self.data["owner"]["actual_wagers"] = 1
        with self.assertRaisesRegex(ValueError, "orders or promotions"):
            validate_public_receipt(self.data)


if __name__ == "__main__":
    unittest.main()
