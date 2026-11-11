"""Credential-free failure tests for saved report reconstruction only."""

import json
from pathlib import Path
import tempfile
import unittest

import build_b062_saved_reports as reports


class SavedReportReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plotly = "/* Invented runtime fixture; not real Plotly. */\nwindow.fixture = '<value>';"
        self.base = self.directory / "earlier.html"
        self.base.write_text("<html><script>" + self.plotly + "</script></html>", encoding="utf-8")
        self.census = self.directory / "census.json"
        records = [{"game": "Invented women's game — α", "value": None}]
        self.census.write_text(json.dumps({"records": records}, ensure_ascii=False) + "\n", encoding="utf-8")
        data = {"schema": "invented-fixture", "games": records, "display": "<tag> 'quote' \\ slash"}
        self.original_data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        data["games"] = reports.GAMES_TOKEN
        (self.directory / reports.DATA_FILE).write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
        template = "<!doctype html><script>" + reports.PLOTLY_TOKEN + "</script><script type='application/json'>" + reports.EVIDENCE_TOKEN + "</script>\n"
        (self.directory / reports.HTML_TEMPLATE).write_text(template, encoding="utf-8")
        self.original_html = template.replace(reports.PLOTLY_TOKEN, self.plotly).replace(
            reports.EVIDENCE_TOKEN, self.original_data.replace("<", "\\u003c")).encode("utf-8")
        original_notebook = {
            "cells": [{"cell_type": "code", "execution_count": 7,
                       "source": ["import json\n", "DATA = json.loads(" + repr(self.original_data) + ")\n",
                                  "raise RuntimeError('Saved report reconstruction must never run this cell')\n"],
                       "outputs": [{"output_type": "display_data", "data": {"text/html": (
                           "<style>body{color:black}</style><script>" + self.plotly + "</script>").splitlines(keepends=True)},
                                    "metadata": {}}], "metadata": {}}],
            "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"saved_evidence_only": True},
        }
        self.original_notebook = (json.dumps(original_notebook, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        original_notebook["cells"][0]["source"][1] = reports.ASSIGNMENT_TOKEN
        original_notebook["cells"][0]["outputs"][0]["data"]["text/html"] = [
            "<style>body{color:black}</style><script>" + reports.PLOTLY_TOKEN + "</script>"]
        (self.directory / reports.NOTEBOOK_TEMPLATE).write_bytes(reports.canonical_notebook(original_notebook))
        self.integrity = {
            "schema": reports.SCHEMA, "saved_evidence_created_at": "2026-11-11T00:00:00Z",
            "templates": {name: reports.fingerprint((self.directory / name).read_bytes()) for name in (
                reports.DATA_FILE, reports.HTML_TEMPLATE, reports.NOTEBOOK_TEMPLATE)},
            "upstream": {"census": {**reports.fingerprint(self.census.read_bytes()), "records": 1},
                         "plotly": {"javascript": reports.fingerprint(self.plotly.encode("utf-8"))}},
            "notebook_placeholders": {"cell": 0, "source_line": 1, "output": 0},
            "outputs": {"B062_EVIDENCE_REPORT.html": reports.fingerprint(self.original_html),
                        "B062_EVIDENCE_REPORT.ipynb": reports.fingerprint(self.original_notebook)},
        }
        self.write_integrity()

    def write_integrity(self):
        (self.directory / reports.INTEGRITY_FILE).write_text(json.dumps(self.integrity), encoding="utf-8")

    def rebuild(self):
        return reports.reconstruct(self.directory, self.base, self.census)[0]

    def test_restores_exact_unicode_bytes_saved_outputs_and_execution_metadata_without_execution(self):
        restored = self.rebuild()
        self.assertEqual(restored["B062_EVIDENCE_REPORT.html"], self.original_html)
        self.assertEqual(restored["B062_EVIDENCE_REPORT.ipynb"], self.original_notebook)
        notebook = json.loads(restored["B062_EVIDENCE_REPORT.ipynb"])
        self.assertEqual(notebook["cells"][0]["execution_count"], 7)
        self.assertIn("raise RuntimeError", notebook["cells"][0]["source"][2])
        self.assertEqual(notebook["metadata"], {"saved_evidence_only": True})

    def test_rejects_changed_census_even_with_same_record_count(self):
        self.census.write_text(self.census.read_text(encoding="utf-8").replace("women's", "men's"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Existing census"):
            self.rebuild()

    def test_rejects_changed_plotly_instead_of_substituting_another_runtime(self):
        self.base.write_text(self.base.read_text(encoding="utf-8").replace("fixture", "changed"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "pinned Plotly"):
            self.rebuild()

    def test_rejects_altered_template_before_emitting_a_report(self):
        path = self.directory / reports.HTML_TEMPLATE
        path.write_bytes(path.read_bytes() + b"<!-- changed -->")
        with self.assertRaisesRegex(ValueError, "template.html"):
            self.rebuild()

    def test_rejects_wrong_expected_output_even_when_inputs_are_valid(self):
        self.integrity["outputs"]["B062_EVIDENCE_REPORT.ipynb"]["sha256"] = "0" * 64
        self.write_integrity()
        with self.assertRaisesRegex(ValueError, "Reconstructed B062_EVIDENCE_REPORT.ipynb"):
            self.rebuild()

    def test_writes_and_reads_back_the_pinned_reports(self):
        restored = self.rebuild()
        destination = self.directory / "saved"
        receipt = reports.write_reports(restored, destination)
        self.assertEqual(receipt, self.integrity["outputs"])
        self.assertEqual((destination / "B062_EVIDENCE_REPORT.html").read_bytes(), self.original_html)
        self.assertEqual((destination / "B062_EVIDENCE_REPORT.ipynb").read_bytes(), self.original_notebook)
        self.assertEqual(set(path.name for path in destination.iterdir()), set(restored))


if __name__ == "__main__":
    unittest.main()
