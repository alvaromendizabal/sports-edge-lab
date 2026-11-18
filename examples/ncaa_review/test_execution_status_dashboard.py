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

    def test_latest_execution_is_verified_but_scientifically_partial(self):
        self.assertEqual(self.data["latest_observed_attempt"]["release"], "R27")
        self.assertEqual(self.data["latest_observed_attempt"]["status"], status.BUDGET_DEFERRED)
        self.assertTrue(self.data["latest_observed_attempt"]["return_published"])
        self.assertEqual(self.data["latest_verified_return"]["release"], "R27")
        self.assertEqual(self.data["latest_verified_return"]["payloads_verified"], 52)
        self.assertEqual(self.data["latest_verified_return"]["sha256"],
                         "45ac375264849a50271db7778a9d1fa83ae04e4b77f9798d6cf2581f16489156")
        self.reject(lambda d: d["latest_observed_attempt"].update(evidence_class="VERIFIED_RECOVERY_EVIDENCE"))
        self.reject(lambda d: d["latest_observed_attempt"].update(return_published=False))
        self.reject(lambda d: d["latest_verified_return"].update(release="R24"))
        self.reject(lambda d: d["latest_observed_attempt"].update(status="COMPLETE"))

    def test_earlier_unpublished_recovery_snapshot_is_preserved(self):
        old = status.validate(json.loads(status.HISTORICAL_DATA.read_text()))
        self.assertEqual(old["latest_observed_attempt"]["release"], "R25")
        self.assertFalse(old["latest_observed_attempt"]["return_published"])
        self.assertEqual(old["latest_verified_return"]["release"], "R24")
        previous = status.validate(json.loads(status.PREVIOUS_VERIFIED_DATA.read_text()))
        self.assertEqual(previous["schema"], status.PREVIOUS_SCHEMA)
        self.assertEqual(previous["latest_verified_return"]["release"], "R26")
        self.assertEqual(self.data["attempts"][:-1], previous["attempts"])
        self.assertEqual(previous["attempts"][:-1], old["attempts"])
        self.assertEqual(status.render_current_banner(previous), status.PREVIOUS_VERIFIED_EXECUTION_BANNER)
        self.assertEqual(status.render_current_banner(old), status.PREVIOUS_EXECUTION_BANNER)
        self.assertIn("remains R24", status.PREVIOUS_EXECUTION_BANNER)
        self.assertIn("verified partial return", status.render_current_banner())

    def test_current_startup_reuse_is_actual_owner_evidence(self):
        c = self.data["current_execution"]
        self.assertEqual(c["reused_startup_tests"], 1074)
        self.assertEqual(c["fresh_startup_tests"], 0)
        self.assertAlmostEqual(c["startup_seconds"], 0.06511124499957077)
        self.assertEqual(c["parent_cpu_seconds"], 2.228032)
        self.assertAlmostEqual(c["owner_elapsed_seconds"], 2.6334098740044283)
        self.assertEqual(c["completed_child_cpu_seconds"], 0)
        self.reject(lambda d: d["current_execution"].update(reused_startup_tests=955))
        self.reject(lambda d: d["current_execution"].update(owner_elapsed_seconds=0))

    def test_current_recovery_cpu_cannot_establish_scientific_occupancy(self):
        c = self.data["current_execution"]
        self.assertEqual(c["requested_workers"], 24)
        self.assertEqual(c["maximum_ready_depth"], 0)
        self.assertEqual(c["peak_scientific_workers"], 0)
        self.assertFalse(c["scientific_gate_executed"])
        for key in ("new_target_fits", "new_calibration_fits", "new_residual_fits", "verified_reused_target_fits", "peak_scientific_workers"):
            self.reject(lambda d, key=key: d["current_execution"].update({key: 1}))
        self.reject(lambda d: d["current_execution"].update(scientific_gate_executed=True))
        self.reject(lambda d: d["current_execution"].update(scientific_gate="PASS"))

    def test_cost_clock_and_unknown_measurement_guards(self):
        self.assertEqual(self.data["current_execution"]["cost_basis"], status.UNKNOWN_COST)
        self.assertIsNone(self.data["current_execution"]["estimated_instance_wall_cost_usd"])
        self.reject(lambda d: d["current_execution"].update(cost_basis="BILLED_EXCLUSIVE_OWNER_COST"))
        self.reject(lambda d: d["current_execution"].update(parent_cpu_seconds=-1))
        self.reject(lambda d: d["current_execution"].update(cache_reads=True))
        self.reject(lambda d: d["current_execution"].update(parent_cpu_seconds=float("nan")))
        self.reject(lambda d: d["current_execution"].update(completed_at="2026-11-19T00:00:00Z"))
        self.reject(lambda d: d["current_execution"].update(started_at="2026-11-18T00:41:59"))
        self.reject(lambda d: d["current_execution"].update(unverified_science={}))

    def test_unknown_cost_cannot_be_zero_or_a_spent_budget(self):
        for cost in (0, 0.0, 200, -1, True):
            self.reject(lambda d, cost=cost: d["current_execution"].update(estimated_instance_wall_cost_usd=cost))
        self.reject(lambda d: d["current_execution"]["deferral"].update(budget_exhaustion_proven=True))
        self.reject(lambda d: d["current_execution"]["deferral"].update(root_cause="COMPUTE_BUDGET_SPENT"))
        self.assertEqual(self.data["current_execution"]["deferral"]["recorded_error"], "B057_WORK_BUDGET_EXHAUSTED")

    def test_unreported_storage_or_pressure_cannot_inherit_prior_measurements(self):
        for key in ("cache_reads", "cache_bytes", "fresh_storage_reads", "fresh_storage_bytes", "pressure_wait_seconds", "pressure_reason"):
            self.assertIsNone(self.data["current_execution"][key])
            self.reject(lambda d, key=key: d["current_execution"].update({key: 0}))
        previous = status.validate(json.loads(status.PREVIOUS_VERIFIED_DATA.read_text()))
        self.assertEqual(previous["current_execution"]["cache_reads"], 168)
        self.assertAlmostEqual(previous["current_execution"]["estimated_instance_wall_cost_usd"], 0.31758846043366623)

    def test_original_price_observation_and_expiry_must_precede_launch(self):
        for patch in ({"quote_expires_at": "2026-11-19T02:36:39.054419+00:00"},
                      {"quote_max_age_days": 8}, {"quote_observed_at": "2026-11-11T02:36:39.054419"}):
            self.reject(lambda d, patch=patch: d["current_execution"]["deferral"].update(patch))
        self.assertEqual(self.data["current_execution"]["deferral"]["compute_cost_guard_usd"], 200)

    def test_attempt_census_counts_invocations_separately_from_run_ids(self):
        self.assertEqual(self.data["audit_scope"]["audited_attempts"], 8)
        self.assertEqual(self.data["audit_scope"]["distinct_run_ids"], 6)
        self.reject(lambda d: d["audit_scope"].update(audited_attempts=7))
        self.reject(lambda d: d["audit_scope"].update(distinct_run_ids=9))

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
        self.assertEqual(report["corrupt_evidence_rejections"], 16)
        self.assertEqual(report["filter_views"], 5)
        self.assertTrue(report["current_partial_return_verified"])

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
