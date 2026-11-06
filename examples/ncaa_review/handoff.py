"""Invented producer/consumer handoff preflight; standard library, no external IO.

The reviewed registrations are the trust anchor in this example. A digest only
proves content equality; a self-declared identity is not independent provenance.
Real systems must authenticate their registry and source receipts separately.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Callable, TypeVar


class HandoffRejected(ValueError):
    """A bounded public reason, with no source payload or credential in errors."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _digest(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class ProducerIdentity:
    project: str
    release: str
    run: str
    source_sha256: str
    artifact_prefix: str

    def validate(self) -> None:
        tokens = (self.project, self.release, self.run)
        if any(not isinstance(x, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", x) is None for x in tokens):
            raise HandoffRejected("INVALID_IDENTITY")
        if not _digest(self.source_sha256):
            raise HandoffRejected("INVALID_SOURCE_DIGEST")
        prefix = self.artifact_prefix
        if (not isinstance(prefix, str) or not prefix.endswith("/")
                or prefix.startswith("/") or "\\" in prefix
                or any(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", p) is None for p in prefix[:-1].split("/"))):
            raise HandoffRejected("NONCANONICAL_PREFIX")


@dataclass(frozen=True)
class Registration:
    identity: ProducerIdentity
    wire_version: int
    artifact_kind: str
    content_sha256: str
    content_bytes: int

    def validate(self) -> None:
        self.identity.validate()
        if type(self.wire_version) is not int or self.wire_version < 1:
            raise HandoffRejected("INVALID_WIRE_VERSION")
        if not isinstance(self.artifact_kind, str) or re.fullmatch(r"[a-z][a-z_]*", self.artifact_kind) is None:
            raise HandoffRejected("INVALID_ARTIFACT_KIND")
        if type(self.content_bytes) is not int or self.content_bytes < 0 or not _digest(self.content_sha256):
            raise HandoffRejected("INVALID_REGISTERED_CONTENT_PIN")


@dataclass(frozen=True)
class Manifest:
    producer: Registration
    content_sha256: str
    content_bytes: int

    def validate(self, payload: bytes) -> None:
        self.producer.validate()
        if not isinstance(payload, bytes):
            raise HandoffRejected("PAYLOAD_MUST_BE_BYTES")
        if type(self.content_bytes) is not int or self.content_bytes < 0 or not _digest(self.content_sha256):
            raise HandoffRejected("INVALID_CONTENT_PIN")
        if (self.content_sha256, self.content_bytes) != (self.producer.content_sha256, self.producer.content_bytes):
            raise HandoffRejected("MANIFEST_DISAGREES_WITH_REGISTERED_PIN")
        if len(payload) != self.content_bytes or hashlib.sha256(payload).hexdigest() != self.content_sha256:
            raise HandoffRejected("CONTENT_PIN_MISMATCH")


@dataclass(frozen=True)
class Consumer:
    registrations: tuple[Registration, ...]

    def validate(self) -> None:
        if not isinstance(self.registrations, tuple) or not self.registrations:
            raise HandoffRejected("EMPTY_OR_MUTABLE_REGISTRY")
        keys = set()
        for entry in self.registrations:
            entry.validate()
            key = (entry.identity.project, entry.identity.release, entry.identity.run)
            if key in keys:
                raise HandoffRejected("DUPLICATE_OR_CONFLICTING_REGISTRATION")
            keys.add(key)


@dataclass(frozen=True)
class Admission:
    producer: Registration
    content_sha256: str
    content_bytes: int


def preflight(manifest: Manifest, payload: bytes, consumer: Consumer) -> Admission:
    """Validate the actual producer output against the actual next consumer.

    No field is rewritten to make it look like a supported release. Matching
    fields independently would admit a forged combination of valid identities;
    the complete reviewed registration must match exactly.
    """
    manifest.validate(payload)
    consumer.validate()
    if manifest.producer not in consumer.registrations:
        raise HandoffRejected("UNREGISTERED_HANDOFF")
    return Admission(manifest.producer, manifest.content_sha256, manifest.content_bytes)


T = TypeVar("T")


def execute_after_preflight(manifest: Manifest, payload: bytes, consumer: Consumer,
                            action: Callable[[Admission, bytes], T]) -> T:
    """Defer the real stage until all identity, format and content checks pass."""
    admitted = preflight(manifest, payload, consumer)
    return action(admitted, payload)


def invented_registration(version: int) -> Registration:
    """Only invented examples: neither a private producer nor a model recipe."""
    payload = invented_payload()
    return Registration(ProducerIdentity(
        project="invented_ncaa", release=f"demo_v{version}", run=f"sample_{version}",
        source_sha256=hashlib.sha256(f"invented-source-{version}".encode()).hexdigest(),
        artifact_prefix=f"invented/demo_v{version}/sample_{version}/",
    ), wire_version=version, artifact_kind="aggregate_fixture",
        content_sha256=hashlib.sha256(payload).hexdigest(), content_bytes=len(payload))


def invented_payload() -> bytes:
    return json.dumps({"invented": True, "items": [2, 5, 8]},
                      sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def invented_output(registration: Registration) -> tuple[Manifest, bytes]:
    payload = invented_payload()
    return Manifest(registration, hashlib.sha256(payload).hexdigest(), len(payload)), payload


def demo() -> dict:
    """Component fixtures pass; only a joined handoff exposes incompatibility."""
    legacy, current = invented_registration(1), invented_registration(2)
    old_manifest, old_payload = invented_output(legacy)
    manifest, payload = invented_output(current)
    legacy_consumer = Consumer((legacy,))
    manifest.validate(payload)  # The producer's own current fixture passes.
    preflight(old_manifest, old_payload, legacy_consumer)  # Old consumer fixture passes.
    calls = []
    try:
        execute_after_preflight(manifest, payload, legacy_consumer,
                                lambda *_: calls.append("started"))
    except HandoffRejected as exc:
        blocked = exc.code
    else:
        raise AssertionError("invented incompatible handoff unexpectedly admitted")
    repaired = Consumer((legacy, current))
    admission = preflight(manifest, payload, repaired)
    return {"fixture_scope": "INVENTED_ONLY", "component_checks_passed": 2,
            "joined_handoff": blocked, "actions_before_admission": len(calls),
            "reviewed_exact_registration": "ADMITTED",
            "admitted_content_bytes": admission.content_bytes,
            "real_owner_execution_claimed": False, "new_model_fit_credit": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run the invented joined-handoff fixture")
    parser.parse_args()
    print(json.dumps(demo(), sort_keys=True, indent=2, allow_nan=False))
