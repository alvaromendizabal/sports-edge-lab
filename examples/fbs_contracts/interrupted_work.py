"""Credential-free, invented interrupted-work recovery contract.

This is a teaching example, not the private collector or a football model. It
opens no files, creates no processes and makes no network calls. Hashes prove
unchanged bytes relative to an independently supplied commitment, not provider
authenticity or historical possession. Production requires separately verified
source identities, storage access controls, writer ownership and source rights.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Callable


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(body: bytes) -> str:
    if not isinstance(body, bytes):
        raise ValueError("Actual bytes are required")
    return hashlib.sha256(body).hexdigest()


def clock(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("An explicit time zone is required")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class ProcessIdentity:
    boot: str
    pid: int
    started: int
    run: str


@dataclass(frozen=True)
class Checkpoint:
    unit: str
    request: str
    run: str
    source_sha256: str
    observed_at: str
    payload_sha256: str
    dependencies: tuple[tuple[str, str], ...]
    result: object
    committed: bool = True

    def identity(self) -> bytes:
        return canonical(self.__dict__)


def classify(expected: ProcessIdentity, current: tuple[ProcessIdentity, ...],
             *, completion_exit: int | None = None) -> str:
    """A completed marker never authorizes takeover of the same active owner.

    completion_exit is accepted only after a caller's external completion
    authentication. This toy function does not authenticate a real completion.
    """
    if expected in current:
        return "ACTIVE_OWNER_PRESERVED"
    if completion_exit is None:
        return "INTERRUPTED_OR_ORPHANED_WITHOUT_NORMAL_COMPLETION"
    if type(completion_exit) is not int or completion_exit not in (0, 2):
        raise ValueError("Unrecognized authenticated completion status")
    return "NORMAL_COMPLETION" if completion_exit == 0 else "FAILED_DIAGNOSTIC_COMPLETION"


def recover(*, run: str, source: bytes, independently_expected_source: str,
            checkpoints: tuple[Checkpoint, ...], catalog_complete: bool,
            originals: dict[str, bytes], replay: Callable[[bytes], object],
            assessed_at: str) -> dict:
    """Check the complete metadata inventory, then replay each exact dependency.

    No normal completion is required to recover independent complete units.
    A partial inventory cannot resolve unseen duplicate/conflict candidates.
    Every rejected unit is retained with a reason; source clocks never change.
    Replay is an explicit pure function and is not a substitute model fit.
    """
    if digest(source) != independently_expected_source:
        raise ValueError("Source differs from independent source commitment")
    assessment = clock(assessed_at)
    report = {
        "fixture_only": True,
        "status": "PARTIAL_INVENTORY_PENDING" if catalog_complete is not True else "RECOVERY_CHECKED",
        "normal_owner_completion_claimed": False,
        "new_fits": 0,
        "new_forecasts": 0,
        "orders": 0,
        "recovered": [],
        "rejected": [],
        "exact_duplicates": 0,
    }
    if catalog_complete is not True:
        report["rejected"] = [{"unit": c.unit, "reason": "INVENTORY_CLOSURE_UNPROVED"} for c in checkpoints]
        return report
    groups: dict[str, list[Checkpoint]] = {}
    seen: set[bytes] = set()
    for checkpoint in checkpoints:
        identity = checkpoint.identity()
        if identity in seen:
            report["exact_duplicates"] += 1
            continue
        seen.add(identity)
        groups.setdefault(checkpoint.request, []).append(checkpoint)
    for request, candidates in sorted(groups.items()):
        complete = [c for c in candidates if c.committed is True]
        if len(complete) > 1:
            report["rejected"].extend({"unit": c.unit, "reason": "CONFLICTING_COMPLETE_OBSERVATIONS"} for c in candidates)
            continue
        for c in candidates:
            try:
                if c.committed is not True:
                    raise ValueError("INCOMPLETE_UNIT")
                if c.run != run or c.source_sha256 != independently_expected_source:
                    raise ValueError("RUN_OR_SOURCE_IDENTITY_DIFFERS")
                if clock(c.observed_at) > assessment:
                    raise ValueError("CAPTURE_AFTER_ASSESSMENT")
                if not c.dependencies or len({name for name, _ in c.dependencies}) != len(c.dependencies):
                    raise ValueError("DEPENDENCY_CLOSURE_INVALID")
                for name, expected in c.dependencies:
                    if name not in originals:
                        raise ValueError("DEPENDENCY_ABSENT")
                    if digest(originals[name]) != expected:
                        raise ValueError("DEPENDENCY_BYTES_CHANGED")
                payload = originals.get(c.payload_sha256)
                if payload is None or digest(payload) != c.payload_sha256:
                    raise ValueError("ORIGINAL_PAYLOAD_ABSENT_OR_CHANGED")
                if c.payload_sha256 not in dict(c.dependencies):
                    raise ValueError("PAYLOAD_NOT_IN_EXACT_DEPENDENCY_CLOSURE")
                recalculated = replay(payload)
                if canonical(recalculated) != canonical(c.result):
                    raise ValueError("NUMERICAL_REPLAY_DIFFERS")
                report["recovered"].append({"unit": c.unit, "request": request,
                    "observed_at": c.observed_at, "payload_sha256": c.payload_sha256,
                    "dependencies": list(c.dependencies), "replayed_result": recalculated})
            except (ValueError, TypeError, KeyError) as error:
                report["rejected"].append({"unit": c.unit, "reason": str(error)})
    report["recovered_units"] = len(report["recovered"])
    report["rejected_units"] = len(report["rejected"])
    return report


def invented_demo() -> dict:
    source = b"invented-count-reduction-v1"
    payload = canonical(["invented-a", "invented-b"])
    key = digest(payload)
    c = Checkpoint("fixture-unit", "fixture-request", "fixture-run", digest(source),
                   "2020-01-01T00:00:00Z", key, ((key, key),), 2)
    return recover(run="fixture-run", source=source, independently_expected_source=digest(source),
        checkpoints=(c,), catalog_complete=True, originals={key: payload},
        replay=lambda raw: len(json.loads(raw)), assessed_at="2020-01-02T00:00:00Z")


def main() -> None:
    print(json.dumps(invented_demo(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
