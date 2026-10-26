"""Aggregate-export and generated-review checks, separate from synthetic metrics."""
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

from examples.review_lab.build_review import render, validate_evidence

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs/evidence/2026-10-25.json"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.selects = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "select":
            self.selects.append(attrs["id"])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SOURCE.read_text())

    def test_declared_cohorts_are_complete(self):
        validate_evidence(self.data)
        self.assertEqual({r["sport"] for r in self.data["rows"]}, {"NFL", "FBS"})

    def test_duplicate_cohort_rejected(self):
        self.data["rows"][1] = deepcopy(self.data["rows"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_evidence(self.data)

    def test_nonfinite_score_rejected(self):
        self.data["rows"][0]["challenger"]["logloss"] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_evidence(self.data)

    def test_committed_html_matches_exact_aggregate_source(self):
        expected = render(self.data, hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual((ROOT / "docs/review/index.html").read_text(), expected)

    def test_accessible_unique_selector_ids(self):
        parser = TableParser()
        parser.feed(render(self.data, "0" * 64))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertEqual(parser.selects, ["sport", "campaign", "metric"])

    def test_no_individual_prediction_export(self):
        self.assertEqual(self.data["data_kind"], "aggregate_private_run_export")
        serialized = json.dumps(self.data)
        for name in ('"game_id"', '"home_id"', '"away_id"', '"coefficients"', '"weights"'):
            self.assertNotIn(name, serialized)
        self.assertFalse(self.data["reproducibility"]["real_data_retraining_from_public_repo"])


if __name__ == "__main__":
    unittest.main()
