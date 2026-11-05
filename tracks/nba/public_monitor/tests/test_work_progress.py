"""All examples are invented; these checks never acquire data or fit a model."""
from dataclasses import replace
import unittest
from tracks.nba.public_monitor.work_progress import Snapshot, compare, select_phase


class WorkProgressTests(unittest.TestCase):
    def setUp(self):
        self.first = Snapshot("priority", "2035-01-01T00:00:00Z", 2, 2, 0, 2, 8, 4, 1)

    def test_more_attempts_without_verified_rows_is_not_data_progress(self):
        later = replace(self.first, observed_at="2035-01-01T00:10:00Z", attempts=10, errors=8)
        result = compare(later, self.first)
        self.assertFalse(result["meaningful_interval_progress"])
        self.assertEqual(result["rows_per_second"], 0)
        self.assertIsNone(result["eta_seconds"])

    def test_new_phase_cannot_inherit_old_cooldown(self):
        old = replace(self.first, cooldown_until="2035-01-01T01:00:00Z")
        new = replace(self.first, phase="models", observed_at="2035-01-01T00:10:00Z")
        result = compare(new, old)
        self.assertIsNone(result["cooldown_until"])
        self.assertIsNone(result["meaningful_interval_progress"])

    def test_known_progress_without_complete_discovery_has_no_eta(self):
        later = replace(self.first, observed_at="2035-01-01T00:01:00Z", completed_items=4, verified_new_rows=7)
        result = compare(later, self.first)
        self.assertTrue(result["meaningful_interval_progress"])
        self.assertAlmostEqual(result["rows_per_second"], .05)
        self.assertIsNone(result["eta_seconds"])

    def test_eta_requires_comparable_enumerated_work(self):
        later = replace(self.first, observed_at="2035-01-01T00:01:00Z", completed_items=4,
                        remaining_items=6, discovery_exhausted=True, comparable_item_cost=True)
        self.assertEqual(compare(later, self.first)["eta_seconds"], 180)
        self.assertIsNone(compare(replace(later, cooldown_until="2035-01-01T01:00:00Z"), self.first)["eta_seconds"])

    def test_counters_cannot_go_backwards_under_same_phase(self):
        with self.assertRaisesRegex(ValueError, "backwards"):
            compare(replace(self.first, observed_at="2035-01-01T00:01:00Z", verified_new_rows=0), self.first)

    def test_invalid_response_accounting_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "accounting"):
            replace(self.first, errors=1)

    def test_naive_or_repeated_clocks_are_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.first, observed_at="2035-01-01T00:00:00")
        with self.assertRaises(ValueError):
            compare(self.first, self.first)

    def test_exhausted_priority_budget_releases_model_work(self):
        self.assertEqual(select_phase(current_inventory_disposed=True, priority_budget_exhausted=True,
            priority_work_remaining=True, model_report_finished=False), "MODEL_AND_REPORT")

    def test_history_remains_after_report_and_inventory_cannot_be_skipped(self):
        self.assertEqual(select_phase(current_inventory_disposed=False, priority_budget_exhausted=True,
            priority_work_remaining=True, model_report_finished=False), "CURRENT_INVENTORY_WITH_EXPLICIT_SOURCE_GAPS")
        self.assertEqual(select_phase(current_inventory_disposed=True, priority_budget_exhausted=True,
            priority_work_remaining=True, model_report_finished=True), "BOUNDED_HISTORY_WITH_RETAINED_BACKLOG")
