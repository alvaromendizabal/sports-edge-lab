"""Invented test outcomes; these tests perform no research or network work."""
import unittest

from tracks.nba.public_monitor.selftest_evidence import inspect_suite


class NamedEvidenceTests(unittest.TestCase):
    def inspect(self, case):
        return inspect_suite(unittest.defaultTestLoader.loadTestsFromTestCase(case))

    def test_success_has_named_evidence_without_owner_completion(self):
        class Example(unittest.TestCase):
            def test_pass(self):
                self.assertEqual(1 + 1, 2)
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["tests_run"]), ("PASS", 1))
        self.assertEqual(report["records"][0]["status"], "PASS")
        self.assertFalse(report["owner_completion_asserted"])

    def test_class_setup_failure_is_named_before_any_test_starts(self):
        class Example(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("invented setup failure")
            def test_unreached(self):
                self.fail("must not run")
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["tests_run"], report["errors"]),
                         ("FAILED", 0, 1))
        self.assertTrue(report["records"][0]["without_startTest"])
        self.assertIn("setUpClass", report["failed_test_details"][0]["id"])
        self.assertIn("invented setup failure", report["log"])

    def test_class_teardown_error_preserves_prior_pass_record(self):
        class Example(unittest.TestCase):
            def test_pass(self):
                pass
            @classmethod
            def tearDownClass(cls):
                raise RuntimeError("invented teardown failure")
        report = self.inspect(Example)
        self.assertEqual([r["status"] for r in report["records"]], ["PASS", "ERROR"])
        self.assertEqual((report["tests_run"], report["errors"]), (1, 1))
        self.assertIn("tearDownClass", report["failed_test_details"][0]["id"])

    def test_subtest_failure_retains_parent_and_precise_failure_detail(self):
        class Example(unittest.TestCase):
            def test_parts(self):
                with self.subTest(part="invented"):
                    self.assertEqual(1, 2)
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["failures"]), ("FAILED", 1))
        self.assertEqual(report["records"][0]["status"], "FAIL")
        self.assertIn("part='invented'", report["failed_test_details"][0]["id"])

    def test_skip_does_not_satisfy_the_gate(self):
        class Example(unittest.TestCase):
            def test_skip(self):
                self.skipTest("invented unsupported condition")
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["skipped"]), ("FAILED", 1))

    def test_expected_failure_is_explicit_and_does_not_satisfy_the_gate(self):
        class Example(unittest.TestCase):
            @unittest.expectedFailure
            def test_expected(self):
                self.fail("invented expected failure")
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["expected_failures"]), ("FAILED", 1))
        self.assertEqual(report["records"][0]["status"], "EXPECTED_FAILURE")

    def test_unexpected_success_is_not_an_all_pass_gate(self):
        class Example(unittest.TestCase):
            @unittest.expectedFailure
            def test_unexpected(self):
                pass
        report = self.inspect(Example)
        self.assertEqual((report["status"], report["unexpected_successes"]), ("FAILED", 1))

    def test_empty_suite_is_not_success(self):
        report = inspect_suite(unittest.TestSuite())
        self.assertEqual((report["status"], report["tests_run"]), ("FAILED", 0))


if __name__ == "__main__":
    unittest.main()
