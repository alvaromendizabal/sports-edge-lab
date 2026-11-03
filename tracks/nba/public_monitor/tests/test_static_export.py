"""The hosted projection stays bounded and makes no deployment claim itself."""
import json
from pathlib import Path
import tempfile
import unittest

from tracks.nba.public_monitor.build_site import ASSETS, Links, bundle, export, repository_links


class StaticExport(unittest.TestCase):
    commit = "1234567890abcdef" * 2 + "12345678"

    def test_exact_public_asset_allowlist(self):
        self.assertEqual(set(bundle(source_ref=self.commit)), ASSETS)

    def test_all_nonlocal_navigation_uses_public_source_pins(self):
        assets = bundle(source_ref=self.commit)
        parser = Links()
        parser.feed(assets["index.html"])
        self.assertIn("october-29.html", parser.links)
        self.assertTrue(any(self.commit in link for link in parser.links))
        self.assertFalse(any(link.startswith("../") for link in parser.links))

    def test_preserved_snapshot_links_back_to_hosted_monitor(self):
        parser = Links()
        parser.feed(bundle(source_ref=self.commit)["october-29.html"])
        self.assertIn("index.html", parser.links)

    def test_only_local_script_is_packaged(self):
        parser = Links()
        parser.feed(bundle(source_ref=self.commit)["index.html"])
        self.assertEqual(parser.scripts, ["monitor.js"])

    def test_export_cannot_claim_deployment(self):
        record = json.loads(bundle(source_ref=self.commit)["hosting-provenance.json"])
        self.assertEqual(record["deployment_status"], "DEFINED_BY_HOST_RECEIPT_NOT_THIS_FILE")
        self.assertEqual(record["live_provider_requests"], 0)
        self.assertFalse(record["private_runtime_artifacts"])

    def test_export_preserves_all_three_dated_cohorts(self):
        data = json.loads(bundle(source_ref=self.commit)["evidence.json"])
        self.assertEqual([row["n"] for row in data["metrics"]], [1164, 1164, 94])

    def test_export_needs_an_exact_public_commit_not_main_or_a_url(self):
        for source in ("main", "https://example.invalid", "a" * 39, "A" * 40):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "exact public source"):
                bundle(source_ref=source)

    def test_path_escaping_navigation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "escaped"):
            repository_links('<a href="../../../../private">x</a>', source_ref=self.commit)

    def test_anchors_are_local_and_external_links_not_rewritten(self):
        html = '<a href="#main">Skip</a><a href="https://example.invalid">Reference</a>'
        self.assertEqual(repository_links(html, source_ref=self.commit), html)

    def test_export_writes_exact_assets_once_without_deleting_existing_content(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "dist"
            receipt = export(destination, source_ref=self.commit)
            self.assertEqual(receipt["status"], "EXPORTED_NOT_DEPLOYED")
            self.assertEqual(set(p.name for p in destination.iterdir()), ASSETS)
            original = (destination / "index.html").read_bytes()
            with self.assertRaisesRegex(ValueError, "new or empty"):
                export(destination, source_ref=self.commit)
            self.assertEqual((destination / "index.html").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
