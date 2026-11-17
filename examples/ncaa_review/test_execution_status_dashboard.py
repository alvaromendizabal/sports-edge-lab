"""Protect recovery accounting and the distinction between run and return."""
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest

import execution_status_dashboard as status


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script" and "src" in attrs:
            self.scripts.append(attrs["src"])


class ExecutionStatusTests(unittest.TestCase):
    def setUp(self):
        self.data = status.load()

    def reject(self, mutate):
        value = deepcopy(self.data)
        mutate(value)
        with self.assertRaises(ValueError):
            status.validate(value)

    def test_latest_execution_is_separate_from_published_return(self):
        self.assertEqual(self.data["latest_observed_attempt"]["release"], "R25")
        self.assertEqual(self.data["latest_observed_attempt"]["status"], "RETURN_PACKAGING_FAILED_RESUMABLE")
        self.assertFalse(self.data["latest_observed_attempt"]["return_published"])
        self.assertEqual(self.data["latest_verified_return"]["release"], "R24")
        self.assertEqual(self.data["latest_verified_return"]["sha256"],
                         "9853bda9c8fe96e00cea2a6b23b13aa078747e90399fe4a2eb77a49fa5aa4e0e")
        self.reject(lambda d: d["latest_observed_attempt"].update(evidence_class="FULL_ARCHIVE_VERIFIED"))
        self.reject(lambda d: d["latest_observed_attempt"].update(return_published=True))
        self.reject(lambda d: d["latest_verified_return"].update(release="R25"))

    def test_new_fits_do_not_count_reuse(self):
        rows = {r["id"]: r for r in self.data["attempts"]}
        self.assertEqual(rows["r22-first"]["new_target_fits"], 11)
        self.assertEqual(rows["r23"]["historical_checkpoint_reuses"], 108)
        self.assertEqual(rows["r23"]["new_target_fits"], 0)
        self.assertEqual(rows["r24-retry"]["fresh_startup_tests"], 0)
        self.assertEqual(rows["r24-retry"]["reused_startup_tests"], 867)
        self.assertEqual(self.data["preserved_work"]["new_target_fits_in_audited_attempts"], 11)
        self.reject(lambda d: d["preserved_work"].update(new_target_fits_in_audited_attempts=119))
        self.reject(lambda d: d["attempts"][2].update(new_target_fits=108))

    def test_unknown_counts_are_not_manufactured_zero(self):
        self.assertIsNone(self.data["attempts"][0]["fresh_startup_tests"])
        self.assertIsNone(self.data["attempts"][1]["historical_checkpoint_reuses"])
        self.reject(lambda d: d["attempts"][0].update(new_target_fits=-1))
        self.reject(lambda d: d["attempts"][0].update(new_target_fits=True))

    def test_no_synthetic_scientific_utilization_or_improvement(self):
        self.assertEqual(self.data["throughput"]["scientific_gate"], "FAILED")
        self.assertFalse(self.data["throughput"]["newer_12_to_24_core_science_proven"])
        self.reject(lambda d: d["throughput"].update(newer_12_to_24_core_science_proven=True))
        self.reject(lambda d: d["throughput"].update(scientific_gate="PASS"))
        self.reject(lambda d: d["throughput"].update(measurement_seconds=30))
        self.reject(lambda d: d["science_contract"].update(new_full_population_champion=True))

    def test_test_season_cannot_select(self):
        self.reject(lambda d: d["science_contract"].update(test_selection_weight=0.1))
        self.reject(lambda d: d["science_contract"].update(validation_seasons=["2025-26", "2026-27"]))
        self.reject(lambda d: d["science_contract"].update(test_exposure_erased=True))

    def test_publication_does_not_execute_or_deploy(self):
        for key in ("owner_runs", "new_fits", "new_forecasts", "provider_requests"):
            self.reject(lambda d, key=key: d["publication"].update({key: 1}))
        self.reject(lambda d: d["publication"].update(deployment_verified=True))
        self.reject(lambda d: d["preserved_work"].update(all_repeated_work_eliminated=True))

    def test_public_boundary(self):
        self.assertIsNone(status.FORBIDDEN.search(status.canonical(self.data)))
        self.reject(lambda d: d.update(raw_private_manifest={}))
        for value in ("s3://private-bucket/object", "/home/owner/private.json", "secret_access_key", "runner.pyz"):
            self.reject(lambda d, value=value: d["evidence"][0].update(label=value))
        self.reject(lambda d: d.update(owner="NFL"))

    def test_actual_page_script_with_offline_dom(self):
        result = subprocess.run(["node", str(Path(__file__).with_name("test_execution_status_dom.cjs"))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["visual_browser_claim"])
        self.assertEqual(report["corrupt_evidence_rejections"], 4)

    def test_attempt_identity_cannot_duplicate(self):
        self.reject(lambda d: d["attempts"].append(deepcopy(d["attempts"][-1])))
        self.reject(lambda d: d["attempts"][-1].update(release="R24"))

    def test_deterministic_public_page_and_exact_download(self):
        for path, text in status.status_outputs().items():
            self.assertEqual(path.read_text(), text, str(path))
        public = json.loads((status.ROOT / "docs/ncaa/execution_status.json").read_text())
        self.assertEqual(public, self.data)
        embedded = status.render().split('<script id="execution-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(embedded), public)
        page = Page(); page.feed(status.render())
        self.assertEqual(len(page.ids), len(set(page.ids)))
        self.assertEqual(page.scripts, [])

    def test_only_landing_banner_changes_older_science(self):
        from v12_public_status import CURRENT_BANNER, R19_BANNER, render_banner, strip_banner
        current = (status.ROOT / "docs/ncaa/index.html").read_text()
        self.assertEqual(current.count(CURRENT_BANNER), 1)
        self.assertNotIn(R19_BANNER, current)
        self.assertEqual(render_banner(current), current)
        previous = current.replace(CURRENT_BANNER, R19_BANNER, 1).encode()
        git_blob = hashlib.sha1(b"blob " + str(len(previous)).encode() + b"\0" + previous).hexdigest()
        self.assertEqual(git_blob, "be0364eed03db2119cf5fe5c886f63c66ed606cf")
        self.assertNotIn('id="v12-current-evidence"', strip_banner(current))


if __name__ == "__main__":
    unittest.main()
