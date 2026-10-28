"""Invented eight-stage workflow with recoverable, immutable local receipts.

Trusted single-host example, not a production scheduler or signed evidence store.
No sports observations, private formulas, network operations or order interface.
"""
from __future__ import annotations
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Callable


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def create(path, value):
    """Flush complete bytes, then publish without replacing any existing receipt."""
    data = encoded(value)
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


@dataclass(frozen=True)
class Stage:
    name: str
    dependencies: tuple[str, ...]
    recipe: str
    work: Callable


def validate_receipt(receipt, stage, identity):
    if set(receipt) != {"stage", "identity", "attempt", "status", "output", "output_sha256", "error_type"}:
        raise ValueError("invalid receipt schema")
    if receipt["stage"] != stage or receipt["identity"] != identity:
        raise ValueError("receipt belongs to different inputs")
    if type(receipt["attempt"]) is not int or receipt["attempt"] < 1:
        raise ValueError("invalid attempt")
    if receipt["status"] not in {"COMPLETED", "FAILED"}:
        raise ValueError("invalid terminal status")
    if receipt["status"] == "COMPLETED":
        if receipt["output_sha256"] != digest(receipt["output"]) or receipt["error_type"] is not None:
            raise ValueError("accepted output integrity failure")
    elif receipt["output"] is not None or receipt["output_sha256"] is not None or not isinstance(receipt["error_type"], str):
        raise ValueError("failed attempt cannot publish accepted output")
    return receipt


def run(directory, stages, context, *, max_attempts=2):
    """Execute independent stages in order, preserving accepted work across reentry.

    An exclusive writer lock fails closed if already held. A process-kill can leave
    a stale lock, which requires explicit operator inspection; it is never stolen.
    Recipe identifiers are declared contracts, not automatic code attestation.
    """
    if type(max_attempts) is not int or not 1 <= max_attempts <= 8:
        raise ValueError("invalid attempt bound")
    stages = list(stages)
    plan = []
    seen = set()
    for s in stages:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", s.name) or s.name in seen:
            raise ValueError("invalid or duplicate stage")
        if not isinstance(s.recipe, str) or not s.recipe or not set(s.dependencies) <= seen:
            raise ValueError("invalid recipe or dependency order")
        seen.add(s.name)
        plan.append({"name": s.name, "dependencies": list(s.dependencies), "recipe": s.recipe})
    frozen = json.loads(encoded(context))
    scope = {"context_sha256": digest(frozen), "plan": plan, "max_attempts": max_attempts}
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".writer-lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RuntimeError("writer lock exists; inspect before recovery") from error
    outputs, states = {}, []
    try:
        scope_path = root / "scope.json"
        if scope_path.exists():
            if read(scope_path) != scope:
                raise ValueError("scope, inputs or recipe changed; use a new decision directory")
        else:
            create(scope_path, scope)
        for stage in stages:
            if any(d not in outputs for d in stage.dependencies):
                states.append({"stage": stage.name, "status": "BLOCKED", "executed": False})
                continue
            dependencies = {d: outputs[d] for d in stage.dependencies}
            identity = digest({"scope": scope, "stage": stage.name, "dependencies": dependencies})
            reservations = sorted(root.glob(stage.name + ".attempt-*.json"))
            results = sorted(root.glob(stage.name + ".result-*.json"))
            if len(reservations) > max_attempts:
                raise ValueError("attempt budget exceeded")
            for index, path in enumerate(reservations, 1):
                if path.name != f"{stage.name}.attempt-{index}.json" or read(path) != {"stage": stage.name, "identity": identity, "attempt": index}:
                    raise ValueError("attempt reservation integrity failure")
            terminal = []
            for path in results:
                item = validate_receipt(read(path), stage.name, identity)
                if item["attempt"] > len(reservations) or path.name != f"{stage.name}.result-{item['attempt']}.json":
                    raise ValueError("result has no matching reservation")
                terminal.append(item)
            successes = [x for x in terminal if x["status"] == "COMPLETED"]
            if len(successes) > 1 or (successes and successes[0]["attempt"] != len(reservations)):
                raise ValueError("attempt recorded after completion")
            accepted_path = root / f"{stage.name}.accepted.json"
            if accepted_path.exists():
                accepted = validate_receipt(read(accepted_path), stage.name, identity)
                if accepted["status"] != "COMPLETED" or successes != [accepted]:
                    raise ValueError("accepted receipt lacks its successful terminal event")
            elif successes:
                # Recover a crash after the successful terminal event but before acceptance publication.
                accepted = successes[0]
                create(accepted_path, accepted)
            else:
                accepted = None
            if accepted:
                outputs[stage.name] = accepted["output"]
                states.append({"stage": stage.name, "status": "REUSED", "executed": False, "output_sha256": accepted["output_sha256"]})
                continue
            if len(reservations) == max_attempts:
                states.append({"stage": stage.name, "status": "EXHAUSTED", "executed": False})
                continue
            attempt = len(reservations) + 1
            create(root / f"{stage.name}.attempt-{attempt}.json", {"stage": stage.name, "identity": identity, "attempt": attempt})
            try:
                output = json.loads(encoded(stage.work(copy.deepcopy(dependencies), copy.deepcopy(frozen))))
                output_hash = digest(output)
                receipt = {"stage": stage.name, "identity": identity, "attempt": attempt, "status": "COMPLETED", "output": output, "output_sha256": output_hash, "error_type": None}
            except Exception as error:
                receipt = {"stage": stage.name, "identity": identity, "attempt": attempt, "status": "FAILED", "output": None, "output_sha256": None, "error_type": type(error).__name__}
            create(root / f"{stage.name}.result-{attempt}.json", receipt)
            if receipt["status"] == "COMPLETED":
                create(accepted_path, receipt)
                outputs[stage.name] = receipt["output"]
            states.append({"stage": stage.name, "status": receipt["status"], "executed": True, "output_sha256": receipt["output_sha256"]})
        return {"evidence": "INVENTED_OFFLINE_DEMONSTRATION", "stages": states, "outputs": outputs,
                "new_attempts": sum(x["executed"] for x in states), "reused_stages": sum(x["status"] == "REUSED" for x in states),
                "actual_orders": 0, "policy_changed_by_research": False}
    finally:
        lock.rmdir()


def fixture(fail_research=False):
    def research(dependencies, context):
        if fail_research:
            raise ArithmeticError("invented numerical rejection")
        return {"candidate": "invented_candidate", "numerically_accepted": True}
    return [
        Stage("refresh", (), "invented-v1", lambda d, c: {"source_version": "invented-observation-v1", "asof": c["decision_time"]}),
        Stage("integrity", ("refresh",), "invented-v1", lambda d, c: {"validated": True, "source_sha256": digest(d["refresh"])}),
        Stage("frozen_policy", ("integrity",), "invented-v1", lambda d, c: {"policy": "MARKET_REFERENCE", "learned_qualifier": False}),
        Stage("forecast", ("frozen_policy", "integrity"), "invented-v1", lambda d, c: {"classification": "SYNTHETIC_MARKET_REFERENCE", "fixture_probability": 0.57, "decision_time": c["decision_time"], "policy_sha256": digest(d["frozen_policy"])}),
        Stage("quotes", ("integrity",), "invented-v1", lambda d, c: {"executable_evidence": False, "reason": "invented fixture has no executable venue quote"}),
        Stage("finance", ("forecast", "quotes"), "invented-v1", lambda d, c: {"status": "NOT_ELIGIBLE", "paper_stake": 0, "profit": None}),
        Stage("research", ("integrity",), "invented-v1", research),
        Stage("qualification", ("research",), "invented-v1", lambda d, c: {"qualified": False, "reason": "numerical success supplies no predictive evidence", "promotion": False})]


def walkthrough():
    with tempfile.TemporaryDirectory(prefix="public-stages-") as directory:
        context = {"decision_time": "2030-01-01T12:00:00Z", "fixture": "invented-v1"}
        first = run(directory, fixture(True), context)
        second = run(directory, fixture(False), context)
        third = run(directory, fixture(False), context)
        return {"first": first, "resume": second, "reentry": third,
                "forecast_identity_preserved": first["outputs"]["forecast"] == second["outputs"]["forecast"] == third["outputs"]["forecast"],
                "finance_identity_preserved": first["outputs"]["finance"] == second["outputs"]["finance"] == third["outputs"]["finance"],
                "invented_only": True}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2))
