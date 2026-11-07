"""Invented evidence tests; none of these timings measure a real provider."""
from dataclasses import replace
import unittest
from examples.fbs_contracts.acquisition_qualification import (
    Measurement, QualificationError, Window, full_run_decision, plan_batches,
    recovery_partition,
)


def window(item, **overrides):
    return Window(**dict(provider="Invented Provider", access_mode="fixture",
        route="fictional-history", item_id=item, lower=0, upper=120,
        period_seconds=60, supports_batch=True, **overrides))


def measured(**overrides):
    values=dict(environment="provider_and_canonical_storage", workers=8,
        elapsed_seconds=10, verified_contracts=120, requests=4,
        tickers_requested=120, s3_operations=16, http_429=0, http_5xx=0,
        integrity_failures=0, peak_requests_per_second=1,
        request_latencies_seconds=(.1,.2,.3,.4), attributed_cost_usd=None)
    values.update(overrides)
    return Measurement(**values)


def decision(sample=None, **overrides):
    values=dict(active_prior_owner=False, fresh_resource_admission=True,
        provider_mode_authorized=True, permitted_peak_requests_per_second=2,
        admitted_workers=8)
    values.update(overrides)
    return full_run_decision(sample or measured(), **values)


class CompatibleBatchTests(unittest.TestCase):
    def test_same_windows_combine_below_response_bound(self):
        result=plan_batches([window(str(i)) for i in range(8)], item_limit=8,
                            response_point_limit=20)
        self.assertEqual([len(batch) for batch in result],[5,3])
        self.assertEqual({w.item_id for b in result for w in b},{str(i) for i in range(8)})

    def test_different_cutoffs_and_access_modes_stay_separate(self):
        first=window("a")
        items=[first,replace(first,item_id="b",upper=180),
               replace(first,item_id="c",access_mode="another-mode"),
               replace(first,item_id="d",period_seconds=30)]
        result=plan_batches(items,item_limit=100,response_point_limit=10000)
        self.assertEqual([len(b) for b in result],[1,1,1,1])
        self.assertEqual({(w.lower,w.upper) for b in result for w in b},{(0,120),(0,180)})

    def test_single_routes_never_gain_batch_capability(self):
        items=[replace(window(str(i)),supports_batch=False) for i in range(3)]
        self.assertEqual([len(b) for b in plan_batches(items,item_limit=100,response_point_limit=1000)],[1,1,1])

    def test_oversized_window_and_duplicate_identity_fail(self):
        with self.assertRaisesRegex(QualificationError,"prior splitting"):
            plan_batches([window("a")],item_limit=2,response_point_limit=3)
        with self.assertRaisesRegex(QualificationError,"Duplicate"):
            plan_batches([window("a"),window("a")],item_limit=2,response_point_limit=100)

    def test_invalid_resource_bounds_and_windows_fail(self):
        for bad in (0,-1,True,1.2):
            with self.assertRaises(QualificationError):
                plan_batches([window("a")],item_limit=bad,response_point_limit=100)
        with self.assertRaises(QualificationError):
            replace(window("a"),upper=-1)


class SelectiveRecoveryTests(unittest.TestCase):
    def test_valid_members_do_not_repeat_when_another_is_missing(self):
        rows=[{"item_id":"a","body":"original-a"},{"item_id":"c","body":"invalid"}]
        result=recovery_partition(["a","b","c"],rows,
                                  validate=lambda row: row["body"].startswith("original"))
        self.assertEqual(set(result['verified_members']),{"a"})
        self.assertEqual(result['retry_ids'],("b","c"))
        self.assertTrue(result['original_batch_evidence_must_be_preserved'])

    def test_unexpected_and_duplicate_response_ids_quarantine_batch(self):
        for rows in ([{"item_id":"foreign"}], [{"item_id":"a"},{"item_id":"a"}]):
            with self.assertRaises(QualificationError):
                recovery_partition(["a"],rows,validate=lambda row:True)

    def test_truthy_validation_is_not_an_explicit_pass(self):
        result=recovery_partition(["a"],[{"item_id":"a"}],validate=lambda row:1)
        self.assertEqual(result['retry_ids'],("a",))

    def test_validator_failure_does_not_become_missing_or_success(self):
        def fail(_):raise ValueError("Original bytes differ")
        with self.assertRaisesRegex(ValueError,"Original bytes"):
            recovery_partition(["a"],[{"item_id":"a"}],validate=fail)


class PerformanceQualificationTests(unittest.TestCase):
    def test_denominators_and_unknown_cost_stay_distinct(self):
        result=measured().metrics()
        self.assertEqual(result['verified_contracts_per_second'],12)
        self.assertEqual(result['requests_per_second'],.4)
        self.assertEqual(result['tickers_per_request'],30)
        self.assertAlmostEqual(result['p50_request_seconds'],.25)
        self.assertAlmostEqual(result['p95_request_seconds'],.385)
        self.assertIsNone(result['cost_per_verified_contract_usd'])

    def test_valid_invented_sample_can_pass_without_speed_guarantee(self):
        result=decision()
        self.assertEqual(result['decision'],'GO')
        self.assertFalse(result['full_run_speed_guaranteed'])

    def test_active_owner_blocks_even_a_fast_sample(self):
        self.assertIn('ACTIVE_PRIOR_OWNER',decision(active_prior_owner=True)['reasons'])

    def test_missing_provider_authority_and_excess_peak_rate_block(self):
        self.assertIn('PROVIDER_MODE_OR_LIMIT_UNQUALIFIED',
                      decision(permitted_peak_requests_per_second=None)['reasons'])
        self.assertIn('PROVIDER_RATE_EXCEEDS_AUTHORIZED_BUDGET',
                      decision(measured(peak_requests_per_second=3))['reasons'])

    def test_more_workers_need_fresh_memory_and_cpu_admission(self):
        for workers in (16,24,32):
            self.assertIn('RESOURCE_ADMISSION_UNQUALIFIED',
                          decision(measured(workers=workers))['reasons'])
        self.assertIn('RESOURCE_ADMISSION_UNQUALIFIED',
                      decision(fresh_resource_admission=False)['reasons'])

    def test_synthetic_and_local_replay_rates_cannot_admit_full_provider_work(self):
        for environment in ('synthetic','local_replay'):
            self.assertIn('BENCHMARK_ENVIRONMENT_UNQUALIFIED',
                          decision(measured(environment=environment))['reasons'])

    def test_errors_and_integrity_failures_block(self):
        for change, reason in (({'http_429':1},'PROVIDER_ERRORS_REQUIRE_REASSESSMENT'),
                               ({'http_5xx':1},'PROVIDER_ERRORS_REQUIRE_REASSESSMENT'),
                               ({'integrity_failures':1},'INTEGRITY_FAILURES')):
            self.assertIn(reason,decision(measured(**change))['reasons'])

    def test_uncommitted_requests_cannot_satisfy_contract_target(self):
        result=decision(measured(verified_contracts=0))
        self.assertIn('VERIFIED_THROUGHPUT_TARGET_NOT_REACHED',result['reasons'])
        self.assertIsNone(result['metrics']['s3_operations_per_verified_contract'])

    def test_latency_accounting_and_nonfinite_values_fail(self):
        for change in ({'elapsed_seconds':0},{'elapsed_seconds':float('nan')},
                       {'request_latencies_seconds':(.1,)},{'http_429':5},
                       {'verified_contracts':True},{'attributed_cost_usd':-1}):
            with self.assertRaises(QualificationError):measured(**change)

    def test_known_allocated_cost_uses_verified_contracts(self):
        self.assertAlmostEqual(measured(attributed_cost_usd=.12).metrics()['cost_per_verified_contract_usd'],.001)


if __name__=='__main__':unittest.main()
