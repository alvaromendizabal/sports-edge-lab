"""Portable validation with explicit passed, failed, errored and skipped cases.

This dependency-free example runs invented checks only. It does not inspect or
signal processes, read provider data, fit models, or change a research gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable


@dataclass(frozen=True)
class Check:
    name: str
    run: Callable[[], None]
    needs: tuple[str, ...] = ()
    mandatory: bool = True


def capabilities(namespace, names):
    """Optional attributes can be absent or noncallable; neither is usable."""
    names = tuple(names)
    if not names or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError("unique nonempty capability names required")
    return {name: callable(getattr(namespace, name, None)) for name in names}


def run_checks(checks, available):
    """Complete the declared check inventory without treating skips as passes.

    An optional integration can skip on an unsupported runtime. A required
    capability or failed check still blocks the gate. Exceptions are classified
    without publishing their potentially sensitive messages or tracebacks.
    """
    checks = tuple(checks)
    if not checks or any(not isinstance(c, Check) for c in checks):
        raise ValueError("nonempty Check inventory required")
    names = [c.name for c in checks]
    if any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError("duplicate or empty check identity")
    if any(type(value) is not bool for value in available.values()):
        raise ValueError("capability observations must be boolean")
    for check in checks:
        if type(check.mandatory) is not bool or not callable(check.run):
            raise ValueError("explicit mandatory flag and callable check required")
        if any(name not in available for name in check.needs):
            raise ValueError("required capability was not observed")
    rows = []
    for check in checks:
        missing = [name for name in check.needs if not available[name]]
        row = {"name": check.name, "mandatory": check.mandatory,
               "missing_capabilities": missing, "exception_type": None}
        if missing:
            row["outcome"] = "SKIPPED"
        else:
            try:
                check.run()
            except AssertionError:
                row.update(outcome="FAILED", exception_type="AssertionError")
            except Exception as exc:
                row.update(outcome="ERROR", exception_type=type(exc).__name__)
            else:
                row["outcome"] = "PASSED"
        rows.append(row)
    counts = {key: sum(r["outcome"] == key for r in rows)
              for key in ("PASSED", "FAILED", "ERROR", "SKIPPED")}
    required_skips = sum(r["mandatory"] and r["outcome"] == "SKIPPED" for r in rows)
    mandatory_passes = sum(r["mandatory"] and r["outcome"] == "PASSED" for r in rows)
    admitted = not (counts["FAILED"] or counts["ERROR"] or required_skips) and mandatory_passes > 0
    return {"data_kind": "INVENTED", "total": len(checks), "completed": len(rows),
            "executed": len(rows) - counts["SKIPPED"], "counts": counts,
            "required_skips": required_skips, "gate_passed": admitted,
            "terminal": True, "status": "READY" if admitted else "BLOCKED",
            "rows": rows, "new_model_fits": 0, "provider_requests": 0,
            "process_signals": 0, "new_orders": 0}


def _pass():
    return None


def _error():
    raise AttributeError("invented optional integration assumption")


def demo_scenarios():
    base = Check("core-contract", _pass)
    optional = Check("optional-integration", _pass, ("optional_api",), False)
    required = Check("required-operation", _pass, ("optional_api",), True)
    specifications = [
        ("available", "Capability available", [base, optional], True,
         "Both checks execute. Two passed checks satisfy the gate; they are not model fits."),
        ("optional_absent", "Optional capability absent", [base, optional], False,
         "The core check passes and an unsupported optional integration skips. The skipped case does not become a pass."),
        ("required_absent", "Required capability absent", [base, required], False,
         "A required operation remains blocked when its capability is missing. A portable fixture does not weaken the operation's guard."),
        ("unexpected_error", "Unexpected check error", [base, Check("integration", _error)], False,
         "Completing the inventory is different from passing it. The unexpected error blocks the gate and the terminal state stays explicit."),
    ]
    return [{"id": name, "label": label, "explanation": explanation,
             "result": run_checks(checks, {"optional_api": available})}
            for name, label, checks, available, explanation in specifications]


if __name__ == "__main__":
    print(json.dumps(demo_scenarios(), indent=2, sort_keys=True))
