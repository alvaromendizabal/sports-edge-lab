"""Invented release-registry and completion-receipt contract.

No production runner, cloud location, provider data or football model is used.
Hashes verify bytes against supplied commitments; they do not authenticate the
party that supplied them. Writer ownership must be independently established
by a real runtime. This example cannot grant a writer lease or resume a job.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@dataclass(frozen=True)
class Pin:
    size: int
    sha256: str

    @classmethod
    def of(cls, body: bytes) -> "Pin":
        require(isinstance(body, bytes), "Actual bytes required")
        return cls(len(body), hashlib.sha256(body).hexdigest())


@dataclass(frozen=True)
class Release:
    name: str
    source: Pin


@dataclass(frozen=True)
class Receipt:
    release: str
    run: str
    source: Pin
    archive: Pin
    declared_exit: int
    status: str
    phase: str
    owner_admitted: bool
    writer_lock_held: bool
    source_units: int
    model_fits: int
    forecast_issues: int
    started_at: str
    finished_at: str
    archived_at: str
    completed_at: str


@dataclass(frozen=True)
class Terminal:
    run: str
    archive: Pin
    declared_exit: int
    process_exit: int | None


def registry(releases: tuple[Release, ...], required: tuple[str, ...]) -> dict[str, Pin]:
    """Every required predecessor must have an independent source commitment.

    Callers use the resulting registry for receipt admission as well as seed
    validation. A new release cannot replace an older required entry merely
    because its version number is higher.
    """
    require(len(required) == len(set(required)), "Duplicate required release")
    result: dict[str, Pin] = {}
    for release in releases:
        require(bool(release.name) and release.name not in result, "Duplicate or empty release")
        require(type(release.source.size) is int and release.source.size > 0
                and len(release.source.sha256) == 64
                and all(c in "0123456789abcdef" for c in release.source.sha256),
                "Invalid independent source commitment")
        result[release.name] = release.source
    require(set(required) <= result.keys(), "Required predecessor missing from registry")
    return result


def clock(value: str) -> datetime:
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(instant.tzinfo is not None, "Clock requires an explicit timezone")
    return instant.astimezone(timezone.utc)


def verify(receipt: Receipt, terminal: Terminal, *, approved: dict[str, Pin],
           expected_run: str, source_bytes: bytes, archive_bytes: bytes) -> dict:
    """Keep failed work and unobserved process status explicit.

    A partial pre-admission diagnostic is valid evidence with zero work; it is
    not successful collection. A declared integer in a log is distinct from an
    independently captured child-process exit. Missing process status remains
    unknown, and a conflicting observed status fails verification.
    """
    require(receipt.release in approved, "Unapproved predecessor release")
    require(receipt.source == approved[receipt.release] == Pin.of(source_bytes),
            "Source differs from independent commitment")
    require(receipt.archive == terminal.archive == Pin.of(archive_bytes),
            "Archive bytes or terminal commitment differ")
    require(bool(expected_run) and receipt.run == terminal.run == expected_run,
            "Run identity differs")
    require(type(receipt.declared_exit) is int and receipt.declared_exit in (0, 2)
            and type(terminal.declared_exit) is int
            and terminal.declared_exit == receipt.declared_exit,
            "Declared exit differs")
    require(terminal.process_exit is None or type(terminal.process_exit) is int
            and terminal.process_exit == receipt.declared_exit,
            "Observed process exit differs from diagnostic status")
    require(receipt.status == ("COMPLETE" if receipt.declared_exit == 0 else "PARTIAL"),
            "Status and declared exit disagree")
    require(receipt.phase in {"HANDOFF", "RESOURCE_ADMISSION", "COLLECTION"},
            "Unknown execution phase")
    require(type(receipt.owner_admitted) is bool and type(receipt.writer_lock_held) is bool,
            "Ownership evidence requires explicit booleans")
    counts = (receipt.source_units, receipt.model_fits, receipt.forecast_issues)
    require(all(type(n) is int and n >= 0 for n in counts), "Invalid work accounting")
    if not receipt.owner_admitted:
        require(receipt.declared_exit == 2 and receipt.phase in {"HANDOFF", "RESOURCE_ADMISSION"}
                and not receipt.writer_lock_held and counts == (0, 0, 0),
                "Pre-admission evidence cannot claim acquired work")
        classification = "PARTIAL_BEFORE_ADMISSION"
    else:
        require(receipt.phase == "COLLECTION" and receipt.writer_lock_held,
                "Collection requires separately established ownership")
        classification = "PARTIAL_COLLECTION" if receipt.declared_exit == 2 else "COMPLETE_DIAGNOSTIC"
    clocks = tuple(clock(getattr(receipt, name)) for name in
                   ("started_at", "finished_at", "archived_at", "completed_at"))
    require(clocks[0] <= clocks[1] <= clocks[2] < clocks[3],
            "Completion must follow the archived result")
    return {
        "fixture_only": True,
        "run": receipt.run,
        "classification": classification,
        "declared_exit": receipt.declared_exit,
        "process_exit": terminal.process_exit,
        "process_exit_verified": terminal.process_exit is not None,
        "successful_collection_claimed": receipt.declared_exit == 0 and terminal.process_exit == 0,
        "preserved_source_units": receipt.source_units,
        "preserved_model_fits": receipt.model_fits,
        "preserved_forecast_issues": receipt.forecast_issues,
        "next_writer_admitted": False,
    }


def invented_fixture() -> tuple[Receipt, Terminal, dict[str, Pin], bytes, bytes]:
    source = b"invented-predecessor-source-two"
    archived = b"invented-pre-admission-diagnostic"
    approved = registry((Release("example-one", Pin.of(b"invented-source-one")),
                         Release("example-two", Pin.of(source)),
                         Release("example-three", Pin.of(b"invented-source-three"))),
                        ("example-one", "example-two"))
    receipt = Receipt("example-two", "invented-run-two", Pin.of(source), Pin.of(archived),
                      2, "PARTIAL", "HANDOFF", False, False, 0, 0, 0,
                      "2020-01-01T00:00:00Z", "2020-01-01T00:00:01Z",
                      "2020-01-01T00:00:02Z", "2020-01-01T00:00:03Z")
    terminal = Terminal(receipt.run, receipt.archive, 2, None)
    return receipt, terminal, approved, source, archived


def main() -> int:
    receipt, terminal, approved, source, archived = invented_fixture()
    report = verify(receipt, terminal, approved=approved, expected_run=receipt.run,
                    source_bytes=source, archive_bytes=archived)
    print(json.dumps(report, sort_keys=True, indent=2))
    # This demonstration completed successfully. The preserved receipt records
    # a different, invented invocation; its diagnostic is not our process exit.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
