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
        self.data = status.validate(json.loads(status.RECOVERY_DATA.read_text()))

    def reject(self, mutate):
        value = deepcopy(self.data)
        mutate(value)
        with self.assertRaises(ValueError):
            status.validate(value)

    def test_latest_execution_is_verified_but_scientifically_partial(self):
        self.assertEqual(self.data["latest_observed_attempt"]["release"], "R28")
        self.assertEqual(self.data["latest_observed_attempt"]["status"], status.RESOURCE_DEFERRED)
        self.assertTrue(self.data["latest_observed_attempt"]["return_published"])
        self.assertEqual(self.data["latest_verified_return"]["release"], "R28")
        self.assertEqual(self.data["latest_verified_return"]["payloads_verified"], 132)
        self.assertEqual(self.data["latest_verified_return"]["sha256"],
                         "36c2b6fa93b4d01e24815ee47386e5c7a604756dfaf3560529ac51b13e84f780")
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
        price = status.validate(json.loads(status.PRICE_DATA.read_text()))
        self.assertEqual(self.data["attempts"][:-1], price["attempts"])
        self.assertEqual(price["attempts"][:-1], previous["attempts"])
        self.assertEqual(status.render_current_banner(price), status.PREVIOUS_PRICE_EXECUTION_BANNER)
        self.assertEqual(previous["attempts"][:-1], old["attempts"])
        self.assertEqual(status.render_current_banner(previous), status.PREVIOUS_VERIFIED_EXECUTION_BANNER)
        self.assertEqual(status.render_current_banner(old), status.PREVIOUS_EXECUTION_BANNER)
        self.assertIn("remains R24", status.PREVIOUS_EXECUTION_BANNER)
        self.assertIn("verified partial return", status.render_current_banner())

    def test_current_startup_reuse_is_actual_owner_evidence(self):
        c = self.data["current_execution"]
        self.assertEqual(c["reused_startup_tests"], 1102)
        self.assertEqual(c["fresh_startup_tests"], 0)
        self.assertAlmostEqual(c["startup_seconds"], 0.06631604299946048)
        self.assertEqual(c["parent_cpu_seconds"], 136.849758)
        self.assertAlmostEqual(c["owner_elapsed_seconds"], 203.60172191999936)
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

    def test_recovery_wait_is_not_wall_limit_or_continuous_pressure(self):
        reason = self.data['current_execution']['deferral']
        self.assertEqual(reason['configured_wait_minutes'], 2)
        self.assertEqual(reason['wait_budget_seconds'], 120)
        self.assertTrue(reason['wall_limit_disabled'])
        self.assertFalse(reason['continuous_pressure_duration_known'])
        self.assertIsNone(self.data['current_execution']['pressure_wait_seconds'])
        self.reject(lambda d: d['current_execution']['deferral'].update(wait_budget_seconds=0))
        self.reject(lambda d: d['current_execution']['deferral'].update(continuous_pressure_duration_known=True))
        self.reject(lambda d: d['current_execution'].update(pressure_wait_seconds=120))

    def test_durable_hits_are_not_recompression_or_model_fits(self):
        e = self.data['recovery_evidence']
        self.assertEqual(e['durable_predecessor_hits'], 50)
        self.assertEqual(e['predecessor_requests'], 50)
        self.assertEqual(e['predecessor_recompression_calls'], 0)
        self.assertEqual(e['durable_predecessor_evictions'], 0)
        self.assertEqual(e['in_memory_byte_cache_evictions'], 50)
        self.assertEqual(e['productive_cache_reads_after_wait_started'], 82)
        self.assertEqual(e['terminal_pressure_reasons'], [])
        self.reject(lambda d: d['recovery_evidence'].update(predecessor_recompression_calls=50))
        self.reject(lambda d: d['recovery_evidence'].update(durable_predecessor_evictions=50))
        self.reject(lambda d: d['recovery_evidence'].update(out_of_memory_or_external_kill_proven=True))

    def test_preparation_requires_receipt_but_never_acquires_owner_credit(self):
        self.assertEqual(self.data['next_preparation']['owner_executions'], 0)
        self.assertFalse(self.data['next_preparation']['science_completion_claimed'])
        self.assertEqual(self.data['audit_scope']['completed_campaigns'], 0)
        self.reject(lambda d: d['next_preparation'].update(owner_executions=1))
        self.reject(lambda d: d['next_preparation'].update(science_completion_claimed=True))
        self.reject(lambda d: d['audit_scope'].update(completed_campaigns=1))
        if self.data['next_preparation']['status'] == 'PREPARING':
            self.reject(lambda d: d['next_preparation'].update(status='PREPARED_VERIFIED'))
        else:
            self.reject(lambda d: d['next_preparation'].update(engineering_evidence_sha256=None))

    def test_estimate_keeps_its_own_measured_cost_interval_and_not_invoice(self):
        e = self.data['recovery_evidence']; c = self.data['current_execution']
        self.assertLess(e['estimated_cost_wall_seconds'], c['owner_elapsed_seconds'])
        self.assertAlmostEqual(c['estimated_instance_wall_cost_usd'], e['rate_usd_per_hour']*e['estimated_cost_wall_seconds']/3600, places=7)
        self.reject(lambda d: d['current_execution'].update(estimated_instance_wall_cost_usd=0))
        self.reject(lambda d: d['current_execution'].update(estimated_instance_wall_cost_usd=200))

    def test_cost_clock_and_unknown_measurement_guards(self):
        self.assertEqual(self.data["current_execution"]["cost_basis"], status.ESTIMATED_COST)
        self.assertAlmostEqual(self.data["current_execution"]["estimated_instance_wall_cost_usd"], 0.14515028062369395)
        self.reject(lambda d: d["current_execution"].update(cost_basis="BILLED_EXCLUSIVE_OWNER_COST"))
        self.reject(lambda d: d["current_execution"].update(parent_cpu_seconds=-1))
        self.reject(lambda d: d["current_execution"].update(cache_reads=True))
        self.reject(lambda d: d["current_execution"].update(parent_cpu_seconds=float("nan")))
        self.reject(lambda d: d["current_execution"].update(completed_at="2026-11-19T00:00:00Z"))
        self.reject(lambda d: d["current_execution"].update(started_at="2026-11-18T00:41:59"))
        self.reject(lambda d: d["current_execution"].update(unverified_science={}))

    def test_unknown_cost_cannot_be_zero_or_a_spent_budget(self):
        self.data = status.validate(json.loads(status.PRICE_DATA.read_text()))
        for cost in (0, 0.0, 200, -1, True):
            self.reject(lambda d, cost=cost: d["current_execution"].update(estimated_instance_wall_cost_usd=cost))
        self.reject(lambda d: d["current_execution"]["deferral"].update(budget_exhaustion_proven=True))
        self.reject(lambda d: d["current_execution"]["deferral"].update(root_cause="COMPUTE_BUDGET_SPENT"))
        self.assertEqual(self.data["current_execution"]["deferral"]["recorded_error"], "B057_WORK_BUDGET_EXHAUSTED")

    def test_unreported_storage_or_pressure_cannot_inherit_prior_measurements(self):
        self.data = status.validate(json.loads(status.PRICE_DATA.read_text()))
        for key in ("cache_reads", "cache_bytes", "fresh_storage_reads", "fresh_storage_bytes", "pressure_wait_seconds", "pressure_reason"):
            self.assertIsNone(self.data["current_execution"][key])
            self.reject(lambda d, key=key: d["current_execution"].update({key: 0}))
        previous = status.validate(json.loads(status.PREVIOUS_VERIFIED_DATA.read_text()))
        self.assertEqual(previous["current_execution"]["cache_reads"], 168)
        self.assertAlmostEqual(previous["current_execution"]["estimated_instance_wall_cost_usd"], 0.31758846043366623)

    def test_original_price_observation_and_expiry_must_precede_launch(self):
        self.data = status.validate(json.loads(status.PRICE_DATA.read_text()))
        for patch in ({"quote_expires_at": "2026-11-19T02:36:39.054419+00:00"},
                      {"quote_max_age_days": 8}, {"quote_observed_at": "2026-11-11T02:36:39.054419"}):
            self.reject(lambda d, patch=patch: d["current_execution"]["deferral"].update(patch))
        self.assertEqual(self.data["current_execution"]["deferral"]["compute_cost_guard_usd"], 200)

    def test_attempt_census_counts_invocations_separately_from_run_ids(self):
        self.assertEqual(self.data["audit_scope"]["audited_attempts"], 9)
        self.assertEqual(self.data["audit_scope"]["distinct_run_ids"], 7)
        self.reject(lambda d: d["audit_scope"].update(audited_attempts=7))
        self.reject(lambda d: d["audit_scope"].update(distinct_run_ids=10))

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
        self.assertGreaterEqual(report["corrupt_evidence_rejections"], 20)
        self.assertEqual(report["filter_views"], 5)
        self.assertTrue(report["current_partial_return_verified"])

    def test_attempt_identity_cannot_duplicate(self):
        self.reject(lambda d: d["attempts"].append(deepcopy(d["attempts"][-1])))
        self.reject(lambda d: d["attempts"][-1].update(release="R24"))

    def test_deterministic_public_page_and_exact_download(self):
        for path, text in status.status_outputs().items():
            self.assertEqual(path.read_text(), text, str(path))
        public = json.loads((status.ROOT / "docs/ncaa/execution_status.json").read_text())
        self.assertEqual(public, status.load())
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


class R29SourcePublicationTests(unittest.TestCase):
    def setUp(self):
        self.data = status.validate(json.loads(status.SOURCE_DATA.read_text()))

    def reject(self, mutate):
        value = deepcopy(self.data)
        mutate(value)
        with self.assertRaises(ValueError):
            status.validate(value)

    def test_latest_r29_return_has_full_integrity_but_incomplete_science(self):
        self.assertEqual(self.data['schema'], status.SCHEMA)
        self.assertEqual(self.data['latest_observed_attempt']['release'], 'R29')
        self.assertEqual(self.data['latest_verified_return']['payloads_verified'], 219)
        self.assertEqual(self.data['latest_verified_return']['sha256'],
            '2701766810d4b8e0409509a3796f694bd9d105180ec4b76c2a623bece6c6d792')
        self.assertEqual(self.data['audit_scope']['audited_attempts'], 10)
        self.assertEqual(self.data['audit_scope']['distinct_run_ids'], 8)
        self.assertEqual(self.data['audit_scope']['completed_campaigns'], 0)
        prior = status.validate(json.loads(status.RECOVERY_DATA.read_text()))
        self.assertEqual(self.data['attempts'][:-1], prior['attempts'])
        self.assertEqual(status.render_current_banner(prior), status.PREVIOUS_RECOVERY_EXECUTION_BANNER)

    def test_historical_reuse_does_not_become_new_or_current_consumer_fitting(self):
        c = self.data['current_execution']
        self.assertEqual(c['historical_checkpoint_reuses'], 108)
        self.assertEqual(c['verified_reused_target_fits'], 0)
        self.assertEqual(c['reused_startup_tests'], 1219)
        self.assertEqual(c['fresh_startup_tests'], 0)
        self.assertEqual(c['recorded_stages_completed'], 4)
        self.assertAlmostEqual(c['startup_seconds'], 0.04599206100101583)
        for key in ('new_target_fits','new_calibration_fits','new_residual_fits',
                    'peak_scientific_workers','verified_reused_target_fits'):
            self.reject(lambda d, key=key: d['current_execution'].update({key:108}))
        self.reject(lambda d: d['current_execution'].update(historical_checkpoint_reuses=0))
        self.reject(lambda d: d['source_publication_evidence'].update(historical_checkpoints_verified=0))

    def test_new_pressure_path_does_not_inherit_stale_r28_deadline(self):
        c = self.data['current_execution']; e = self.data['source_publication_evidence']
        self.assertEqual(c['deferral']['recorded_error'], 'V7_BOUNDED_IO_PRESSURE')
        self.assertEqual(e['pressure_reasons'], ['MEMORY_FULL_PRESSURE'])
        self.assertEqual(e['memory_full_avg10'], 42.37)
        self.assertEqual(e['io_full_avg10'], 42.72)
        self.assertEqual(e['available_memory_bytes'], 81163436032)
        self.assertAlmostEqual(c['pressure_wait_seconds'], 15.149872975001927)
        self.reject(lambda d: d['source_publication_evidence'].update(pressure_reasons=[]))
        self.reject(lambda d: d['source_publication_evidence'].update(memory_full_avg10=0))
        self.reject(lambda d: d['source_publication_evidence'].update(io_full_avg10=101))
        self.reject(lambda d: d['current_execution']['deferral'].update(
            root_cause='PRODUCTIVE_RECOVERY_EXHAUSTED_STALE_LAUNCH_WAIT'))
        self.reject(lambda d: d['current_execution']['deferral'].update(out_of_memory_or_external_kill_proven=True))

    def test_partial_source_counts_are_not_coverage_forecasts_or_fits(self):
        e = self.data['source_publication_evidence']
        self.assertEqual(e['recorded_source_chunks'], 294)
        self.assertEqual(e['recorded_chunk_rows'], 2821813)
        self.assertEqual(e['recorded_chunk_logical_bytes'], 4932251561)
        self.assertEqual(e['collector_outcome_rows'], 3187384)
        self.assertEqual(e['collector_completed_captures'], 510)
        self.assertEqual(e['collector_planned_captures'], 122177)
        for key in ('source_refresh_complete','source_rows_are_forecasts_or_fits','chunk_progress_is_complete_source_coverage'):
            self.reject(lambda d, key=key: d['source_publication_evidence'].update({key:True}))
        self.reject(lambda d: d['source_publication_evidence'].update(collector_completed_captures=122177))
        self.reject(lambda d: d['source_publication_evidence'].update(recorded_chunk_rows=3187385))

    def test_storage_readbacks_are_separate_from_provider_or_model_work(self):
        c = self.data['current_execution']
        self.assertEqual(c['cache_reads'], 2085)
        self.assertEqual(c['cache_bytes'], 2985729188)
        self.assertEqual(c['fresh_storage_reads'], 1513)
        self.assertEqual(c['fresh_storage_bytes'], 5393041268)
        self.assertEqual(self.data['publication']['provider_requests'], 0)
        self.reject(lambda d: d['publication'].update(provider_requests=1513))

    def test_two_owner_cpu_sampling_scopes_cannot_be_fit_occupancy(self):
        c = self.data['current_execution']; e = self.data['source_publication_evidence']
        self.assertAlmostEqual(e['owner_peak_cores_performance_ledger'], 1.3028224135576973)
        self.assertAlmostEqual(e['owner_peak_cores_independent_sampler'], 1.5904345375830122)
        self.assertEqual(e['useful_scientific_worker_cores'], 0)
        self.assertAlmostEqual(c['parent_cpu_seconds'], 1291.072474)
        self.assertEqual(c['completed_child_cpu_seconds'], 0)
        self.assertFalse(c['scientific_gate_executed'])
        self.reject(lambda d: d['source_publication_evidence'].update(useful_scientific_worker_cores=12))
        self.reject(lambda d: d['current_execution'].update(scientific_gate_executed=True))
        self.reject(lambda d: d['source_publication_evidence'].update(independent_measurement_seconds=99999))

    def test_observed_cost_stays_an_estimate_below_guard(self):
        c = self.data['current_execution']; e = self.data['source_publication_evidence']
        self.assertAlmostEqual(c['estimated_instance_wall_cost_usd'],1.2399884079552135)
        self.assertAlmostEqual(c['estimated_instance_wall_cost_usd'],
            e['rate_usd_per_hour']*e['estimated_cost_wall_seconds']/3600)
        self.assertFalse(c['deferral']['budget_exhaustion_proven'])
        self.reject(lambda d: d['current_execution'].update(estimated_instance_wall_cost_usd=0))
        self.reject(lambda d: d['current_execution']['deferral'].update(budget_exhaustion_proven=True))
        self.reject(lambda d: d['source_publication_evidence'].update(pressure_sample_at='2026-11-19T00:00:00Z'))

    def test_r30_preparation_needs_receipts_and_no_owner_credit(self):
        n = self.data['next_preparation']
        self.assertEqual(n['release'],'R30')
        self.assertEqual(n['owner_executions'],0)
        self.assertFalse(n['science_completion_claimed'])
        self.reject(lambda d: d['next_preparation'].update(owner_executions=1))
        self.reject(lambda d: d['next_preparation'].update(science_completion_claimed=True))
        if n['status']=='PREPARING':
            self.reject(lambda d: d['next_preparation'].update(status='PREPARED_VERIFIED'))
            self.reject(lambda d: d['next_preparation'].update(engineering_evidence_sha256='a'*64))
        else:
            self.reject(lambda d: d['next_preparation'].update(engineering_evidence_sha256=None))
            self.reject(lambda d: d['next_preparation']['verified_delivery'].update(owner_executions=1))
            self.reject(lambda d: d['next_preparation']['verified_delivery'].update(startup_cases_executed=1))
            self.reject(lambda d: d['next_preparation']['verified_delivery']['installation_receipt'].update(sha256='unverified'))

    def test_preparing_and_verified_preparation_render_without_new_owner_science(self):
        candidate=deepcopy(self.data)
        candidate['next_preparation'].update(status='PREPARING',canonical_gate_passed=False,
            upload_verified=False,engineering_tests=None,engineering_failures=None,
            engineering_evidence_sha256=None,verified_delivery=None)
        for row in candidate['next_preparation']['stages']:
            row['status']='PREPARING'
        self.assertIn('R30 is being prepared',status.render_current_banner(candidate))
        candidate['next_preparation'].update(status='PREPARED_VERIFIED',canonical_gate_passed=True,
            upload_verified=True,engineering_tests=1,engineering_failures=0,engineering_evidence_sha256='a'*64)
        candidate['next_preparation']['verified_delivery']={
            **{name:{'bytes':1,'sha256':'a'*64} for name in
               ('canonical_source','engineering_gate','installation_receipt','ready_receipt')},
            'installed_at':'2026-11-18T19:01:02.567660+00:00','startup_cases_reused':1,
            'startup_cases_executed':0,'owner_executions':0,'new_scientific_fits':0}
        for row in candidate['next_preparation']['stages']:
            row['status']='IMPLEMENTED_OWNER_EXECUTION_PENDING'
        # An isolated public-projection fixture exercises the verified rendering
        # path. These fabricated fixture pins never enter the published snapshot.
        self.assertIn('R30 preparation and staging are verified',status.render_current_banner(candidate))
        self.assertEqual(status.validate(json.loads(status.SOURCE_DATA.read_text()))['next_preparation'],self.data['next_preparation'])

    def test_current_banner_replaces_exact_old_wrapper_only(self):
        from v12_public_status import render_banner, strip_banner, CURRENT_BANNER
        body='<main><article data-original="keep">Preserved scientific rows</article></main>'
        previous=body.replace('<main>','<main>'+status.PREVIOUS_RECOVERY_EXECUTION_BANNER)
        current=render_banner(previous)
        self.assertEqual(strip_banner(current),body)
        self.assertEqual(current.count(CURRENT_BANNER),1)
        self.assertNotIn('stale launch-wide deadline',CURRENT_BANNER)
        self.assertNotIn('live memory pressure',CURRENT_BANNER)
        self.assertIn('original-clock check',CURRENT_BANNER)


class R30ClockRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.data = status.load()

    def reject(self, mutate):
        value = deepcopy(self.data)
        mutate(value)
        with self.assertRaises(ValueError):
            status.validate(value)

    def test_actual_failed_return_and_prior_attempts(self):
        self.assertEqual(self.data["schema"], status.CLOCK_SCHEMA)
        self.assertEqual(self.data["latest_observed_attempt"]["status"], "FAILED_RESUMABLE")
        self.assertEqual(self.data["latest_verified_return"]["payloads_verified"], 220)
        prior = status.validate(json.loads(status.SOURCE_DATA.read_text()))
        self.assertEqual(self.data["attempts"][:-1], prior["attempts"])
        self.assertEqual(self.data["audit_scope"]["audited_attempts"], 11)
        self.assertEqual(self.data["audit_scope"]["distinct_run_ids"], 9)
        self.reject(lambda d: d["attempts"][0].update(new_target_fits=100))
        self.reject(lambda d: d["latest_observed_attempt"].update(status="COMPLETED"))
        self.reject(lambda d: d["latest_verified_return"].update(sha256=prior["latest_verified_return"]["sha256"]))

    def test_historical_reuse_and_startup_are_not_new_science(self):
        c = self.data["current_execution"]
        self.assertEqual(c["historical_checkpoint_reuses"], 108)
        self.assertEqual(c["reused_startup_tests"], 1255)
        self.assertEqual(c["fresh_startup_tests"], 0)
        self.assertEqual(c["new_target_fits"], 0)
        self.assertEqual(c["verified_reused_target_fits"], 0)
        self.reject(lambda d: d["current_execution"].update(verified_reused_target_fits=108))
        self.reject(lambda d: d["current_execution"].update(new_target_fits=108))
        self.reject(lambda d: d["current_execution"].update(fresh_startup_tests=1255))
        self.reject(lambda d: d["current_execution"].update(historical_checkpoint_reuses=0))

    def test_clock_failure_never_inherits_pressure_or_budget(self):
        c = self.data["current_execution"]
        self.assertEqual(c["failure"]["recorded_error"], "B104_RESPONSE_HISTORICAL_ORIGINAL_CLOCKS")
        self.assertEqual(c["failure"]["recorded_status"], "FAILED_PARTIAL_WORK_PRESERVED")
        self.assertEqual(c["failure"]["pointer_status"], "FAILED_RESUMABLE")
        self.assertIsNone(c["pressure_wait_seconds"])
        self.assertIsNone(c["pressure_reason"])
        self.reject(lambda d: d["current_execution"].update(pressure_wait_seconds=15.15))
        self.reject(lambda d: d["current_execution"]["failure"].update(recorded_error="V7_BOUNDED_IO_PRESSURE"))
        self.reject(lambda d: d["current_execution"]["failure"].update(budget_exhaustion_proven=True))
        self.reject(lambda d: d["clock_recovery_evidence"].update(recorded_source_refresh_complete=True))

    def test_measured_parent_cpu_not_worker_occupancy(self):
        c, e = self.data["current_execution"], self.data["clock_recovery_evidence"]
        self.assertAlmostEqual(c["parent_cpu_seconds"], 632.602133)
        self.assertEqual(c["completed_child_cpu_seconds"], 0)
        self.assertEqual(c["peak_scientific_workers"], 0)
        self.assertEqual(c["requested_workers"], 24)
        self.assertAlmostEqual(e["owner_peak_cores_performance_ledger"], 1.226051398173781)
        self.assertAlmostEqual(e["owner_peak_cores_independent_sampler"], 1.3977839484346002)
        self.assertEqual(self.data["throughput"]["release"], "R22")
        self.reject(lambda d: d["current_execution"].update(scientific_gate_executed=True))
        self.reject(lambda d: d["current_execution"].update(peak_scientific_workers=24))
        self.reject(lambda d: d["clock_recovery_evidence"].update(useful_scientific_worker_cores=12))
        self.reject(lambda d: d["throughput"].update(release="R30"))

    def test_exact_shared_wall_estimate_separate_from_cpu_and_billing(self):
        c, e = self.data["current_execution"], self.data["clock_recovery_evidence"]
        self.assertAlmostEqual(c["estimated_instance_wall_cost_usd"], 0.670245610164624)
        self.assertAlmostEqual(c["estimated_instance_wall_cost_usd"],e["rate_usd_per_hour"]*e["estimated_cost_wall_seconds"]/3600)
        self.reject(lambda d: d["current_execution"].update(cost_basis="INVOICE"))
        self.reject(lambda d: d["current_execution"].update(estimated_instance_wall_cost_usd=0))
        self.reject(lambda d: d["clock_recovery_evidence"].update(rate_usd_per_hour=float("nan")))

    def test_r31_has_no_borrowed_r30_preparation_credit(self):
        n = self.data["next_preparation"]
        self.assertEqual(n["release"], "R31")
        self.assertEqual(n["owner_executions"], 0)
        self.reject(lambda d: d["next_preparation"].update(owner_executions=1))
        self.reject(lambda d: d["next_preparation"].update(science_completion_claimed=True))
        prior = status.validate(json.loads(status.SOURCE_DATA.read_text()))
        self.reject(lambda d: d.update(next_preparation=deepcopy(prior["next_preparation"])))
        if n["status"] == "IN_PROGRESS":
            self.assertIsNone(n["verified_delivery"])
            self.reject(lambda d: d["next_preparation"].update(status="PREPARED_VERIFIED"))
            self.reject(lambda d: d["next_preparation"].update(engineering_tests=1277))
        else:
            self.reject(lambda d: d["next_preparation"].update(verified_delivery=prior["next_preparation"]["verified_delivery"]))

    def test_v13_and_private_boundary_still_enforced(self):
        self.reject(lambda d: d["science_contract"].update(test_selection_weight=0.1))
        self.reject(lambda d: d["science_contract"].update(validation_seasons=["2025-26", "2026-27"]))
        self.reject(lambda d: d["science_contract"].update(new_full_population_champion=True))
        self.reject(lambda d: d["evidence"][-1].update(label="s3://private-owner/object"))
        self.reject(lambda d: d["publication"].update(deployment_verified=True))
        self.reject(lambda d: d["publication"].update(owner_runs=1))

    def test_previous_source_banner_replaced_without_changing_body(self):
        from v12_public_status import render_banner, strip_banner, CURRENT_BANNER
        body = '<main><article data-original="keep">Preserved scientific rows</article></main>'
        previous = body.replace('<main>', '<main>' + status.PREVIOUS_SOURCE_EXECUTION_BANNER)
        current = render_banner(previous)
        self.assertEqual(strip_banner(current), body)
        self.assertEqual(current.count(CURRENT_BANNER), 1)
        self.assertIn('latest observed R30', CURRENT_BANNER)
        self.assertIn('220 payloads', CURRENT_BANNER)
        self.assertIn('R31', CURRENT_BANNER)
        self.assertNotIn('R30 preparation and staging are verified', CURRENT_BANNER)


if __name__ == "__main__":
    unittest.main()
