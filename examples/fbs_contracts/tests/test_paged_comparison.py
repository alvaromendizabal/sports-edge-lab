"""Behavioral failures on invented pages; no real sports data or fits."""
from copy import deepcopy
import unittest

from examples.fbs_contracts.paged_comparison import (
    Sample, advance_comparison, close_pages, demo_pages, seal_page,
)


class PagedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.pages = demo_pages()
        self.names = tuple(page["body"]["page_id"] for page in self.pages)
        self.candidates = ("amber", "birch", "cedar")
        self.events = ("sample-a", "sample-b")

    def close(self, pages=None):
        return close_pages(self.names, self.pages if pages is None else pages,
                           self.candidates, self.events)

    def test_earliest_page_winner_survives_later_pages_and_resumes(self):
        inventory = self.close()
        first = advance_comparison(inventory)
        second = advance_comparison(inventory, first)
        third = advance_comparison(inventory, second)
        self.assertEqual((first["champion"], second["champion"]), (None, None))
        self.assertEqual(third["champion"], "amber")
        self.assertEqual(third["reused_comparisons"], 2)
        self.assertEqual(third["new_comparisons"], 1)
        self.assertEqual(first["completed"]["amber"], third["completed"]["amber"])

    def test_complete_reentry_performs_no_new_comparisons(self):
        inventory = self.close()
        done = advance_comparison(inventory, max_new_candidates=3)
        again = advance_comparison(inventory, done)
        self.assertEqual(again["new_comparisons"], 0)
        self.assertEqual(again["reused_comparisons"], 3)
        self.assertEqual(again["completed"], done["completed"])
        self.assertEqual(again["real_model_fits"], 0)

    def test_missing_page_cannot_select_from_only_latest_page(self):
        with self.assertRaisesRegex(ValueError, "Complete page closure"):
            self.close(self.pages[1:])

    def test_page_delivery_order_does_not_change_result(self):
        forward = advance_comparison(self.close(), max_new_candidates=3)
        backward = advance_comparison(self.close(tuple(reversed(self.pages))), max_new_candidates=3)
        self.assertEqual(forward, backward)

    def test_identical_page_redelivery_is_counted_only_as_delivery(self):
        inventory = self.close(self.pages + (self.pages[0],))
        self.assertEqual(inventory.page_count, 3)
        self.assertEqual(inventory.duplicate_page_deliveries, 1)
        self.assertEqual(len(inventory.rows), 6)

    def test_changed_page_bytes_fail_before_comparison(self):
        pages = deepcopy(self.pages)
        pages[0]["body"]["samples"][0]["loss"] = 999
        with self.assertRaisesRegex(ValueError, "changed after sealing"):
            self.close(pages)

    def test_conflicting_redelivery_is_rejected(self):
        changed = seal_page(self.names[0], [Sample("amber", "sample-a", 99.0), Sample("amber", "sample-b", 3.0)])
        with self.assertRaisesRegex(ValueError, "Conflicting delivery"):
            self.close(self.pages + (changed,))

    def test_missing_candidate_event_is_not_zero_filled(self):
        short = seal_page(self.names[0], [Sample("amber", "sample-a", 1.0)])
        with self.assertRaisesRegex(ValueError, "Every declared candidate"):
            self.close((short,) + self.pages[1:])

    def test_duplicate_candidate_event_is_not_double_counted(self):
        repeated = seal_page(self.names[0], [Sample("amber", "sample-a", 1.0), Sample("amber", "sample-a", 1.0)])
        with self.assertRaisesRegex(ValueError, "Duplicate candidate-event"):
            self.close((repeated,) + self.pages[1:])

    def test_changed_inventory_cannot_reuse_old_comparison(self):
        first = advance_comparison(self.close())
        changed = seal_page(self.names[0], [Sample("amber", "sample-a", 2.0), Sample("amber", "sample-b", 3.0)])
        other = self.close((changed,) + self.pages[1:])
        with self.assertRaisesRegex(ValueError, "changed input"):
            advance_comparison(other, first)

    def test_changed_completed_receipt_is_rejected(self):
        inventory = self.close()
        first = advance_comparison(inventory)
        first["completed"]["amber"]["body"]["mean_loss"] = -1
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            advance_comparison(inventory, first)

    def test_nonfinite_and_boolean_losses_are_rejected(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite numeric"):
                seal_page("fictional", [Sample("amber", "sample-a", value)])


if __name__ == "__main__":
    unittest.main()
