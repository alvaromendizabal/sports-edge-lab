"""Adversarial invented examples; no sports observations or production solver."""
import copy
import math
import unittest

from examples.review_lab.numerical_recovery import (
    certificate, digest, project_capped_simplex, recover, summarize_work, walkthrough,
)


class NumericalCertificateTests(unittest.TestCase):
    def test_success_status_cannot_override_bad_optimality(self):
        result = certificate((.7, .6, -.1), (1., 1., 1.), (0., 0., 0.), solver_success=True)
        self.assertFalse(result["numerically_certified"])
        self.assertTrue(result["solver_reported_success"])

    def test_infeasible_optimum_does_not_receive_feasible_domain_bound(self):
        result = certificate((.7, .6), (1., 1.), (.7, .6), solver_success=True)
        self.assertIsNone(result["convex_suboptimality_upper_bound"])
        self.assertFalse(result["numerically_certified"])

    def test_even_small_primal_violation_is_not_hidden(self):
        result = certificate((.5, .5), (1., 1.), (1., -1e-16), solver_success=True)
        self.assertFalse(result["numerically_certified"])

    def test_stopped_status_is_retained_after_independent_certificate(self):
        result = certificate((.7, .6, -.1), (1., 1., 1.), (.55, math.nextafter(.45, 0.), 0.), solver_success=False)
        self.assertTrue(result["numerically_certified"])
        self.assertFalse(result["solver_reported_success"])
        self.assertEqual(result["status"], "CERTIFIED_WITH_SOLVER_STOP_RETAINED")
        self.assertFalse(result["predictive_qualification"])

    def test_gap_bounds_known_analytic_optimality_error(self):
        # Unit curvature has known Euclidean-projection optimum.
        optimum = certificate((.7, .6, -.1), (1., 1., 1.), (.55, math.nextafter(.45, 0.), 0.), solver_success=True)
        for point in ((0., 0., 0.), (.375, .5, .125), (.1, .2, .3), (1., 0., 0.)):
            actual = certificate((.7, .6, -.1), (1., 1., 1.), point, solver_success=True)
            self.assertLessEqual(actual["objective"] - optimum["objective"], actual["convex_suboptimality_upper_bound"] + 1e-15)

    def test_nonconvex_problem_cannot_claim_convex_certificate(self):
        with self.assertRaises(ValueError):
            certificate((.5, .5), (1., -1.), (.5, .5), solver_success=True)

    def test_nonfinite_and_boolean_parameters_rejected(self):
        for value in (math.nan, math.inf, True):
            with self.assertRaises(ValueError):
                certificate((value, .5), (1., 1.), (.5, .5), solver_success=True)

    def test_solver_status_and_dimension_are_explicit(self):
        with self.assertRaises(ValueError):
            certificate((.5, .5), (1., 1.), (.5,), solver_success=True)
        with self.assertRaises(ValueError):
            certificate((.5,), (1.,), (.5,), solver_success=1)

    def test_tolerance_cannot_be_loosened_to_accept_anything(self):
        for value in (0, True, -1, math.nan, math.inf, 1.):
            with self.assertRaises(ValueError):
                certificate((.5,), (1.,), (.5,), solver_success=True, tolerance=value)

    def test_projection_is_feasible_and_idempotent(self):
        for point in ((.9, .8, .7), (-.1, .2, .4), (10., 11., 12.), (.7, .6, -.1)):
            result = project_capped_simplex(point)
            self.assertGreaterEqual(min(result), 0.)
            self.assertLessEqual(sum(result), 1.)
            self.assertEqual(result, project_capped_simplex(result))

    def test_recovery_converges_on_invented_conditioned_problem(self):
        result = recover((.7, .6, -.1), (1., 4., 10.))
        self.assertEqual(result["status"], "CERTIFIED_SYNTHETIC_RECOVERY")
        self.assertTrue(result["certificate"]["numerically_certified"])
        self.assertEqual(result["football_fits"], 0)
        self.assertEqual(result, recover((.7, .6, -.1), (1., 4., 10.)))

    def test_iteration_budget_exhaustion_is_not_success(self):
        result = recover((.7, .6, -.1), (1., 4., 10.), maximum_iterations=0)
        self.assertEqual(result["status"], "ITERATION_LIMIT_NO_ACCEPTED_RESULT")
        self.assertEqual(result["iterations"], 0)
        self.assertFalse(result["certificate"]["numerically_certified"])

    def test_iteration_budget_must_be_bounded_integer(self):
        for value in (-1, True, 100001, 1.5):
            with self.assertRaises(ValueError):
                recover((.5,), (1.,), maximum_iterations=value)

    def test_large_gradient_cancellation_cannot_create_zero_gap(self):
        result = certificate((1e16, 1e16), (1., 1.), (1., 0.), solver_success=True)
        self.assertFalse(result["numerically_certified"])
        self.assertEqual(result["convex_suboptimality_upper_bound"], 1.)

    def test_large_projection_is_bounded_and_correct(self):
        self.assertEqual(project_capped_simplex((1e16, 1e16)), (.5, .5))

    def test_subnormal_infeasibility_is_not_rounded_away(self):
        result = certificate((.5, .5), (1., 1.), (1., 1e-320), solver_success=True)
        self.assertFalse(result["numerically_certified"])
        self.assertIsNone(result["convex_suboptimality_upper_bound"])

    def test_high_dimension_is_explicitly_bounded(self):
        with self.assertRaises(ValueError):
            project_capped_simplex([.1] * 65)



class PartialWorkTests(unittest.TestCase):
    def setUp(self):
        self.prior = [{"unit_id": "previous", "input_sha256": digest("old input"),
                       "artifact_sha256": digest("old weights"), "origin_run": "earlier"}]
        self.attempts = [{"attempt_id": "a1", "unit_id": "new", "input_sha256": digest("new input"),
                          "status": "FAILED", "artifact_sha256": None},
                         {"attempt_id": "a2", "unit_id": "new", "input_sha256": digest("new input"),
                          "status": "COMPLETED", "artifact_sha256": digest("new weights")}]

    def test_import_is_not_new_work_and_failure_remains_counted(self):
        original = copy.deepcopy((self.prior, self.attempts))
        result = summarize_work(self.prior, self.attempts)
        self.assertEqual((result["new_attempts"], result["failed_attempts"], result["new_completed_units"]), (2, 1, 1))
        self.assertEqual(result["cumulative_unique_completed_units"], 2)
        self.assertEqual((self.prior, self.attempts), original)
        self.assertIsNone(result["owner_run_success"])

    def test_no_new_attempts_does_not_reset_prior_completed_count(self):
        result = summarize_work(self.prior, [])
        self.assertEqual(result["new_completed_units"], 0)
        self.assertEqual(result["cumulative_unique_completed_units"], 1)

    def test_imported_unit_cannot_be_refitted_or_double_counted(self):
        self.attempts[0]["unit_id"] = "previous"
        with self.assertRaisesRegex(ValueError, "refitted"):
            summarize_work(self.prior, self.attempts)

    def test_failed_artifact_is_not_an_accepted_checkpoint(self):
        self.attempts[0]["artifact_sha256"] = digest("partial")
        with self.assertRaisesRegex(ValueError, "failed attempt"):
            summarize_work(self.prior, self.attempts)

    def test_duplicate_attempt_and_completion_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate attempt"):
            summarize_work(self.prior, self.attempts + [self.attempts[0]])
        repeated = dict(self.attempts[1], attempt_id="a3")
        with self.assertRaisesRegex(ValueError, "completed unit"):
            summarize_work(self.prior, self.attempts + [repeated])

    def test_changed_input_cannot_retain_same_unit_identity(self):
        self.attempts[1]["input_sha256"] = digest("changed")
        with self.assertRaisesRegex(ValueError, "signature changed"):
            summarize_work(self.prior, self.attempts)

    def test_corrupt_completion_digest_rejected(self):
        self.prior[0]["artifact_sha256"] = "unverified"
        with self.assertRaisesRegex(ValueError, "digest"):
            summarize_work(self.prior, self.attempts)

    def test_duplicate_import_and_unknown_status_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate imported"):
            summarize_work(self.prior * 2, self.attempts)
        self.attempts[0]["status"] = "probably complete"
        with self.assertRaisesRegex(ValueError, "status"):
            summarize_work(self.prior, self.attempts)

    def test_no_attempt_after_completed_unit(self):
        later = dict(self.attempts[0], attempt_id="a3")
        with self.assertRaisesRegex(ValueError, "completed unit"):
            summarize_work(self.prior, self.attempts + [later])

    def test_walkthrough_does_not_claim_production_repair(self):
        result = walkthrough()
        self.assertTrue(result["synthetic_only"])
        self.assertFalse(result["production_repair_success_claimed"])
        self.assertEqual(result["actual_orders"], 0)


if __name__ == "__main__":
    unittest.main()
