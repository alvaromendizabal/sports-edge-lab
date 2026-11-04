"""Counterexamples for optional runtime capabilities and honest gate outcomes."""
from types import SimpleNamespace
import unittest

from preflight import Check, capabilities, run_checks, demo_scenarios


class PortableGateTests(unittest.TestCase):
    def test_missing_attribute_is_an_observation_not_an_exception(self):
        self.assertEqual(capabilities(SimpleNamespace(), ["operation"]), {"operation": False})

    def test_noncallable_attribute_does_not_admit_an_operation(self):
        self.assertFalse(capabilities(SimpleNamespace(operation=True), ["operation"])["operation"])
        self.assertTrue(capabilities(SimpleNamespace(operation=lambda: None), ["operation"])["operation"])

    def test_optional_skip_never_invokes_missing_operation_or_counts_as_pass(self):
        calls = []
        result = run_checks([Check("core", lambda: calls.append("core")),
            Check("optional", lambda: calls.append("optional"), ("api",), False)], {"api": False})
        self.assertEqual(calls, ["core"])
        self.assertEqual(result["counts"], {"PASSED": 1, "FAILED": 0, "ERROR": 0, "SKIPPED": 1})
        self.assertEqual((result["completed"], result["executed"]), (2, 1))
        self.assertTrue(result["gate_passed"])

    def test_required_skip_blocks_even_when_other_checks_pass(self):
        result = run_checks([Check("core", lambda: None), Check("required", lambda: None, ("api",))], {"api": False})
        self.assertFalse(result["gate_passed"])
        self.assertEqual(result["required_skips"], 1)

    def test_no_required_pass_cannot_qualify_science(self):
        result = run_checks([Check("optional", lambda: None, (), False)], {})
        self.assertFalse(result["gate_passed"])

    def test_failure_and_error_are_distinct_and_do_not_hide_later_checks(self):
        def fail(): raise AssertionError("invented failure")
        def error(): raise RuntimeError("private-message-must-not-escape")
        result = run_checks([Check("failure", fail), Check("error", error), Check("later", lambda: None)], {})
        self.assertEqual(result["counts"], {"PASSED": 1, "FAILED": 1, "ERROR": 1, "SKIPPED": 0})
        self.assertFalse(result["gate_passed"])
        self.assertNotIn("private-message", str(result))
        self.assertTrue(result["terminal"])

    def test_duplicate_identity_rejects_before_side_effects(self):
        calls=[]
        with self.assertRaises(ValueError):
            run_checks([Check("same", lambda: calls.append(1)), Check("same", lambda: calls.append(2))], {})
        self.assertEqual(calls, [])

    def test_unknown_capability_does_not_become_a_skip_or_false_measurement(self):
        with self.assertRaisesRegex(ValueError, "not observed"):
            run_checks([Check("required", lambda: None, ("unknown",))], {})

    def test_stop_signal_is_not_swallowed_as_a_completed_check(self):
        def stop(): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): run_checks([Check("stop", stop)], {})

    def test_empty_or_nonboolean_inventory_is_rejected(self):
        with self.assertRaises(ValueError): run_checks([], {})
        with self.assertRaises(ValueError): run_checks([Check("core", lambda: None)], {"api": 1})
        with self.assertRaises(ValueError): capabilities(SimpleNamespace(), ["same", "same"])

    def test_every_demo_is_terminal_and_has_no_science_or_external_credit(self):
        cases=demo_scenarios()
        self.assertEqual([c["result"]["gate_passed"] for c in cases], [True, True, False, False])
        for case in cases:
            result=case["result"]
            self.assertEqual(result["completed"], sum(result["counts"].values()))
            self.assertTrue(result["terminal"])
            for field in ("new_model_fits", "provider_requests", "process_signals", "new_orders"):
                self.assertEqual(result[field], 0)


if __name__ == "__main__": unittest.main()
