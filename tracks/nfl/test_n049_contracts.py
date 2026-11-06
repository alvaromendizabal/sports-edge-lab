import copy
import hashlib
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

from continuation_contracts_n049 import (
    classify_event_reports, oriented_threshold_metadata, verify_completion_reentry,
)
from export_site_n049 import build_projection, validate_readiness

HERE = Path(__file__).resolve().parent


class EventTimingTests(unittest.TestCase):
    def setUp(self):
        self.events = [
            {"event_id": "INVENTED_STARTED", "kickoff_at": "2025-10-01T18:00:00Z",
             "decision_at": "2025-10-01T17:00:00Z", "published_at": "2025-10-01T16:00:00Z"},
            {"event_id": "INVENTED_FUTURE", "kickoff_at": "2025-10-01T22:00:00Z",
             "decision_at": "2025-10-01T21:00:00Z", "published_at": "2025-10-01T16:00:00Z"},
        ]

    def test_started_game_does_not_poison_future_game(self):
        original = copy.deepcopy(self.events)
        rows = classify_event_reports(self.events, "2025-10-01T19:00:00Z")
        self.assertEqual([r["status"] for r in rows], ["NON_PREGAME_TEMPORAL_EXCLUSION", "SOURCE_AVAILABLE_BY_DECISION"])
        self.assertEqual(self.events, original)
        self.assertEqual({r["event_id"] for r in rows}, {r["event_id"] for r in original})

    def test_capture_at_kickoff_is_not_pregame(self):
        self.assertEqual(classify_event_reports(self.events, "2025-10-01T18:00:00Z")[0]["status"], "NON_PREGAME_TEMPORAL_EXCLUSION")

    def test_late_capture_cannot_borrow_early_publication(self):
        self.assertEqual(classify_event_reports(self.events, "2025-10-01T21:30:00Z")[1]["status"], "AFTER_DECISION_EXCLUSION")

    def test_missing_clock_remains_unverified(self):
        self.events[1]["published_at"] = None
        self.assertEqual(classify_event_reports(self.events, "2025-10-01T19:00:00Z")[1]["status"], "UNVERIFIED_PUBLICATION_CLOCK")

    def test_malformed_clock_and_duplicate_identity_are_not_exclusions(self):
        for change in ({"kickoff_at": "2025-10-01T22:00:00"}, {"event_id": "INVENTED_STARTED"}):
            events = copy.deepcopy(self.events)
            events[1].update(change)
            with self.assertRaises(ValueError):
                classify_event_reports(events, "2025-10-01T19:00:00Z")


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.payload = b"invented completed calculation\n"
        self.identity = {"project": "nfl", "study": "invented-study", "input_version": "fixture-1", "algorithm": "toy-1"}
        self.receipt = {"schema": "public-completion-example.v1", "identity": self.identity.copy(), "status": "COMPLETE", "payload": {"bytes": len(self.payload), "sha256": hashlib.sha256(self.payload).hexdigest()}}

    def test_exact_reentry_is_zero_new_work_and_immutable(self):
        original = copy.deepcopy(self.receipt)
        result = verify_completion_reentry(self.receipt, self.identity, self.payload)
        self.assertEqual(result["new_work_units"], 0)
        self.assertEqual(self.receipt, original)

    def test_matching_payload_does_not_authorize_other_identity(self):
        for key in self.identity:
            expected = self.identity.copy()
            expected[key] = "different"
            with self.assertRaises(ValueError):
                verify_completion_reentry(self.receipt, expected, self.payload)

    def test_incomplete_or_corrupt_completion_is_rejected(self):
        with self.assertRaises(ValueError):
            verify_completion_reentry(self.receipt, self.identity, self.payload + b"!")
        self.receipt["status"] = "STARTED"
        with self.assertRaises(ValueError):
            verify_completion_reentry(self.receipt, self.identity, self.payload)

    def test_identity_types_are_not_interchangeable(self):
        self.identity["example_version"] = 1
        self.receipt["identity"]["example_version"] = True
        with self.assertRaises(ValueError):
            verify_completion_reentry(self.receipt, self.identity, self.payload)


class OrientationTests(unittest.TestCase):
    def metadata(self, orientation="LESS_THAN", settlement="VOID_EQUALITY", **mass):
        return oriented_threshold_metadata(above=mass.get("above", .2), equal=mass.get("equal", .1), below=mass.get("below", .7), orientation=orientation, settlement=settlement)

    def test_less_and_greater_use_opposite_oriented_numerators(self):
        less, greater = self.metadata(), self.metadata("GREATER_THAN")
        self.assertAlmostEqual(less["scoring_probability"], .7/.9)
        self.assertAlmostEqual(greater["scoring_probability"], .2/.9)
        self.assertAlmostEqual(less["scoring_probability"] + greater["scoring_probability"], 1)

    def test_strict_keeps_equality_as_loss(self):
        self.assertEqual(self.metadata(settlement="STRICT")["scoring_probability"], .7)

    def test_unknown_settlement_is_descriptive_only(self):
        result = self.metadata(settlement="UNKNOWN")
        self.assertIsNone(result["scoring_probability"])
        self.assertFalse(result["scoring_eligible"])
        self.assertFalse(result["executable_quote_claimed"])

    def test_all_mass_at_equality_has_no_conditional_probability(self):
        result = self.metadata(above=0, equal=1, below=0)
        self.assertIsNone(result["probability_conditional_on_non_equality"])
        self.assertFalse(result["scoring_eligible"])

    def test_unknown_orientation_and_invalid_mass_fail(self):
        for kwargs in ({"orientation": "OTHER"}, {"above": float("nan")}, {"above": .5}):
            with self.assertRaises(ValueError):
                self.metadata(**kwargs)


class PublicReadinessTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((HERE / "readiness_n049.json").read_text())

    def test_preparation_cannot_claim_completed_work(self):
        for field, value in (("new_owner_fits", 144), ("new_forecasts", 1), ("automatic_promotion", True), ("new_path_analysis_completed", True)):
            changed = copy.deepcopy(self.data)
            changed[field] = value
            with self.assertRaises(ValueError):
                validate_readiness(changed)

    def test_unknown_fields_do_not_expand_public_scope(self):
        self.data["private_source"] = "not permitted"
        with self.assertRaises(ValueError):
            validate_readiness(self.data)

    def test_projection_preserves_full_review_and_pins_links(self):
        source = (HERE / "review.html").read_text()
        commit = "a" * 40
        page, links = build_projection(source, self.data, commit)
        self.assertEqual(page.count('id="n049-readiness"'), 1)
        self.assertIn("PREPARED_NOT_OWNER_EXECUTED", page)
        self.assertIn('id="full-coverage"', page)
        self.assertIn('id="injury-only-study"', page)
        self.assertIn("/" + commit + "/tracks/nfl/N049_RESEARCH_UPDATE.md", page)
        self.assertTrue("/" + commit + "/tracks/nfl/" in page)
        self.assertTrue("n048_fresh" in page)
        self.assertGreater(len(links), 60)
        class Embedded(HTMLParser):
            def __init__(self):
                super().__init__()
                self.active = None
                self.payloads = {}
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "script" and attrs.get("type") == "application/json":
                    self.active = attrs["id"]
                    self.payloads[self.active] = ""
            def handle_data(self, data):
                if self.active is not None:
                    self.payloads[self.active] += data
            def handle_endtag(self, tag):
                if tag == "script":
                    self.active = None
        before, after = Embedded(), Embedded()
        before.feed(source)
        after.feed(page)
        self.assertGreater(len(before.payloads), 30)
        self.assertEqual(before.payloads, after.payloads)
        with self.assertRaises(ValueError):
            build_projection(page, self.data, commit)


if __name__ == "__main__":
    unittest.main()
