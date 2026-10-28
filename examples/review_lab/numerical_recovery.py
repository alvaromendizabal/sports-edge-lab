"""Invented convex optimization and honest partial-work accounting.

This educational example has no sports data, production objective, model
promotion, exchange execution or network access. A solver's status and an
independent mathematical certificate are separate evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction


def _numbers(values, name):
    values = tuple(values)
    if not 1 <= len(values) <= 64 or any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError(name + " must contain 1 to 64 finite real numbers, excluding booleans")
    return values


def problem(target, curvature):
    """Strictly convex diagonal quadratic; all constants are invented inputs."""
    target, curvature = _numbers(target, "target"), _numbers(curvature, "curvature")
    if len(target) != len(curvature) or min(curvature) <= 0:
        raise ValueError("matching dimensions and positive curvature required")
    return target, curvature


def project_capped_simplex(point):
    """Euclidean projection onto nonnegative coordinates whose sum is <= 1."""
    point = tuple(Fraction(x) for x in _numbers(point, "point"))
    positive = tuple(max(Fraction(0), x) for x in point)
    if sum(positive) <= 1:
        projected = positive
    else:
        ordered = sorted(point, reverse=True)
        prefix, threshold = Fraction(0), Fraction(0)
        for index, value in enumerate(ordered, 1):
            prefix += value
            candidate = (prefix - 1) / index
            if value > candidate:
                threshold = candidate
        projected = tuple(max(Fraction(0), x - threshold) for x in point)
    result = []
    for value in projected:
        rounded = float(value)
        if Fraction(rounded) > value:
            rounded = math.nextafter(rounded, 0.0)
        result.append(rounded)
    # Outward rounding toward zero keeps the exact binary-float sum feasible.
    if sum(Fraction(v) for v in result) > 1:
        raise ValueError("projection feasibility check failed")
    return tuple(result)


def certificate(target, curvature, point, *, solver_success, tolerance=1e-9):
    """Bound suboptimality using the linear minimization gap of a convex law.

    For feasible x, convexity gives f(x)-f(x*) <= grad f(x).(x-v),
    where v minimizes grad f(x).v on the capped simplex. Its minimum is
    min(0, min(gradient)). The bound applies only to this explicit convex
    objective and domain; it is not a prediction-quality certificate.
    """
    target, curvature = problem(target, curvature)
    point = _numbers(point, "point")
    if len(point) != len(target) or type(solver_success) is not bool:
        raise ValueError("dimension mismatch or invalid solver status")
    if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or not 0 < tolerance <= 1e-3:
        raise ValueError("a finite declared numerical tolerance is required")
    # Fractions represent each finite binary input exactly. This avoids a
    # cancellation-created zero gap when large gradients differ by one unit.
    exact_target = tuple(Fraction(x) for x in target)
    exact_curve = tuple(Fraction(x) for x in curvature)
    exact_point = tuple(Fraction(x) for x in point)
    exact_objective = sum(c * (x-t)**2 for c, x, t in zip(exact_curve, exact_point, exact_target)) / 2
    gradient = tuple(c * (x-t) for c, x, t in zip(exact_curve, exact_point, exact_target))
    try:
        objective = float(exact_objective)
    except OverflowError as error:
        raise ValueError("objective exceeds finite display range") from error
    if not math.isfinite(objective):
        raise ValueError("objective exceeds finite display range")
    exact_violation = max(Fraction(0), -min(exact_point), sum(exact_point) - 1)
    feasible = exact_violation == 0
    violation = float(exact_violation)
    gap = None
    if feasible:
        exact_gap = sum(g*x for g, x in zip(gradient, exact_point)) - min(Fraction(0), min(gradient))
        if exact_gap < 0:
            raise ValueError("convex gap invariant failed")
        try:
            gap = float(exact_gap)
        except OverflowError as error:
            raise ValueError("certificate exceeds finite display range") from error
        if Fraction(gap) < exact_gap:
            gap = math.nextafter(gap, math.inf)
        if not math.isfinite(gap):
            raise ValueError("certificate exceeds finite display range")
    certified = feasible and gap <= tolerance
    return {"objective": objective, "primal_violation": violation,
            "convex_suboptimality_upper_bound": gap, "numerical_tolerance": tolerance,
            "numerically_certified": certified, "solver_reported_success": solver_success,
            "status": "CERTIFIED" if certified and solver_success else
                      "CERTIFIED_WITH_SOLVER_STOP_RETAINED" if certified else "REJECTED",
            "certificate_arithmetic": "EXACT_BINARY_INPUT_RATIONAL_WITH_OUTWARD_ROUNDED_GAP",
            "predictive_qualification": False, "automatic_promotion": False}


def recover(target, curvature, *, maximum_iterations=5000, tolerance=1e-9):
    """Bounded deterministic synthetic recovery with explicit iteration debt."""
    target, curvature = problem(target, curvature)
    if type(maximum_iterations) is not int or not 0 <= maximum_iterations <= 100000:
        raise ValueError("finite integer iteration budget required")
    point = tuple(0.0 for _ in target)
    step = 1.0 / max(curvature)
    if not math.isfinite(step) or step <= 0:
        raise ValueError("unsupported synthetic step scale")
    for iteration in range(maximum_iterations + 1):
        check = certificate(target, curvature, point, solver_success=False, tolerance=tolerance)
        if check["numerically_certified"]:
            return {"status": "CERTIFIED_SYNTHETIC_RECOVERY", "iterations": iteration,
                    "point": list(point), "certificate": check,
                    "origin": "INVENTED_FIXTURE", "football_fits": 0}
        if iteration < maximum_iterations:
            point = project_capped_simplex(x - step*c*(x-t) for x, c, t in zip(point, curvature, target))
    return {"status": "ITERATION_LIMIT_NO_ACCEPTED_RESULT", "iterations": maximum_iterations,
            "point": list(point), "certificate": check,
            "origin": "INVENTED_FIXTURE", "football_fits": 0}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def summarize_work(prior_completed, attempts):
    """Reconcile immutable prior work, current attempts and new completions.

    Inputs represent already authenticated receipts, not authentication itself.
    A different input signature is a different unit. A completed artifact may
    never change under one unit identity. Imported successes are never new fits.
    """
    prior_completed, attempts = list(prior_completed), list(attempts)
    required = {"unit_id", "input_sha256", "artifact_sha256", "origin_run"}
    prior = {}
    for row in prior_completed:
        if set(row) != required or any(not isinstance(row[k], str) or not row[k] for k in required):
            raise ValueError("invalid prior completion receipt")
        if row["unit_id"] in prior:
            raise ValueError("duplicate imported completion")
        for k in ("input_sha256", "artifact_sha256"):
            if len(row[k]) != 64 or any(c not in "0123456789abcdef" for c in row[k]):
                raise ValueError("invalid content digest")
        prior[row["unit_id"]] = row
    seen, complete, failed = set(), {}, 0
    signatures = {}
    for row in attempts:
        if set(row) != {"attempt_id", "unit_id", "input_sha256", "status", "artifact_sha256"}:
            raise ValueError("invalid attempt receipt")
        if any(not isinstance(row[k], str) or not row[k] for k in ("attempt_id", "unit_id", "input_sha256")):
            raise ValueError("attempt identity is missing")
        if row["attempt_id"] in seen:
            raise ValueError("duplicate attempt identity")
        seen.add(row["attempt_id"])
        if row["status"] not in {"FAILED", "COMPLETED"}:
            raise ValueError("unknown attempt status")
        if row["unit_id"] in prior:
            raise ValueError("imported completed unit must not be refitted or counted again")
        signature = row["input_sha256"]
        if len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
            raise ValueError("invalid attempt input digest")
        if row["unit_id"] in signatures and signatures[row["unit_id"]] != signature:
            raise ValueError("input signature changed under one unit identity")
        signatures[row["unit_id"]] = signature
        if row["unit_id"] in complete:
            raise ValueError("completed unit must not receive another attempt")
        if row["status"] == "FAILED":
            if row["artifact_sha256"] is not None:
                raise ValueError("failed attempt cannot publish an accepted artifact")
            failed += 1
        else:
            artifact = row["artifact_sha256"]
            if not isinstance(artifact, str) or len(artifact) != 64 or any(c not in "0123456789abcdef" for c in artifact):
                raise ValueError("completed attempt requires content identity")
            key = row["unit_id"]
            complete[key] = row
    return {"imported_completed_units": len(prior), "new_attempts": len(attempts),
            "new_completed_units": len(complete), "failed_attempts": failed,
            "cumulative_unique_completed_units": len(prior) + len(complete),
            "prior_receipts_sha256": digest(prior_completed),
            "attempt_receipts_sha256": digest(attempts),
            "source_authentication": "REQUIRED_EXTERNALLY", "owner_run_success": None}


def walkthrough():
    target, curvature = (.7, .6, -.1), (1., 1., 1.)
    misleading_success = certificate(target, curvature, (0., 0., 0.), solver_success=True)
    recovered = recover(target, curvature)
    prior = [{"unit_id": "prior-demo", "input_sha256": digest("prior-input"),
              "artifact_sha256": digest("prior-weights"), "origin_run": "invented-prior"}]
    attempts = [{"attempt_id": "new-a1", "unit_id": "new-demo", "input_sha256": digest("new-input"),
                 "status": "FAILED", "artifact_sha256": None},
                {"attempt_id": "new-a2", "unit_id": "new-demo", "input_sha256": digest("new-input"),
                 "status": "COMPLETED", "artifact_sha256": digest(recovered)}]
    return {"synthetic_only": True, "football_fits": 0, "misleading_solver_success": misleading_success,
            "recovery": recovered, "work": summarize_work(prior, attempts),
            "production_repair_success_claimed": False, "actual_orders": 0}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, allow_nan=False))
