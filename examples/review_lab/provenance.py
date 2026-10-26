"""Synthetic, content-pinned recovery across explicitly admitted parent bundles.

This small educational component operates on immutable local caches. It is not
a security sandbox against concurrent hostile filesystem mutation, and contains
no active football transforms, model parameters, or production cache layout.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from types import MappingProxyType
from typing import Iterable, Mapping


class ProvenanceError(ValueError):
    """A source cannot be admitted under the declared identity or time contract."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ProvenanceError("invalid observation clock") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProvenanceError("observation clock must include a timezone")
    return parsed.astimezone(timezone.utc)


def _key(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or "\x00" in value or PurePosixPath(value).is_absolute()
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ProvenanceError("artifact key must be a normalized relative path")
    return value


def _digest(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ProvenanceError("invalid SHA-256 identity")
    return value


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProvenanceError("duplicate manifest field")
        result[key] = value
    return result


def _read(root: Path, key: str) -> bytes:
    relative = _key(key)
    path = root.joinpath(*relative.split("/"))
    for candidate in (path, *path.parents):
        if candidate == root:
            break
        if candidate.is_symlink():
            raise ProvenanceError("symbolic links are not admitted")
    if not path.resolve().is_relative_to(root):
        raise ProvenanceError("artifact escaped its admitted parent")
    if not path.is_file():
        raise ProvenanceError("declared artifact is missing")
    return path.read_bytes()


@dataclass(frozen=True)
class Reference:
    parent_id: str
    key: str
    content_sha256: str
    size_bytes: int
    observed_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.parent_id, str) or not self.parent_id.strip():
            raise ProvenanceError("parent identity is required")
        _key(self.key)
        _digest(self.content_sha256)
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ProvenanceError("invalid byte count")
        _utc(self.observed_at)


@dataclass(frozen=True)
class AdmittedParent:
    parent_id: str
    root: Path
    manifest_sha256: str
    references: Mapping[str, Reference]


@dataclass(frozen=True)
class Observation:
    reference: Reference
    content: bytes


def admit_parent(root: Path, *, expected_parent_id: str,
                 expected_manifest_sha256: str) -> AdmittedParent:
    """Verify the caller's pinned manifest before permitting any member lookup."""
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ProvenanceError("parent must be an existing non-symlink directory")
    root = root.resolve()
    _digest(expected_manifest_sha256)
    body = _read(root, "manifest.json")
    if sha256(body) != expected_manifest_sha256:
        raise ProvenanceError("manifest identity mismatch")
    try:
        manifest = json.loads(body, object_pairs_hook=_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ProvenanceError("invalid manifest JSON") from error
    if not isinstance(manifest, dict) or manifest.get("schema") != "public-synthetic-parent-v1":
        raise ProvenanceError("unsupported manifest")
    if manifest.get("parent_id") != expected_parent_id:
        raise ProvenanceError("manifest parent identity mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ProvenanceError("manifest needs a nonempty entry list")
    refs: dict[str, Reference] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"key", "content_sha256", "size_bytes", "observed_at"}:
            raise ProvenanceError("unexpected artifact fields")
        ref = Reference(parent_id=expected_parent_id, **entry)
        if ref.key in refs:
            raise ProvenanceError("duplicate artifact key")
        refs[ref.key] = ref
    return AdmittedParent(expected_parent_id, root, expected_manifest_sha256,
                          MappingProxyType(refs))


class Registry:
    """Resolve a logical parent/key pair without searching unrelated directories."""

    def __init__(self, parents: Iterable[AdmittedParent]):
        self.parents: dict[str, AdmittedParent] = {}
        for parent in parents:
            if parent.parent_id in self.parents:
                raise ProvenanceError("duplicate admitted parent identity")
            self.parents[parent.parent_id] = parent

    def read(self, reference: Reference, *, decision_at: str) -> Observation:
        parent = self.parents.get(reference.parent_id)
        if parent is None:
            raise ProvenanceError("referenced parent was not admitted")
        if parent.references.get(reference.key) != reference:
            raise ProvenanceError("reference differs from pinned manifest")
        if _utc(reference.observed_at) >= _utc(decision_at):
            raise ProvenanceError("source was not observed before the decision")
        if sha256(_read(parent.root, "manifest.json")) != parent.manifest_sha256:
            raise ProvenanceError("admitted manifest changed")
        body = _read(parent.root, reference.key)
        if len(body) != reference.size_bytes or sha256(body) != reference.content_sha256:
            raise ProvenanceError("artifact content identity mismatch")
        # Return the bytes that were verified, not a path that a caller reads again.
        return Observation(reference, body)


def synthetic_parent(root: Path, parent_id: str, *, payload: bytes = b'{"value": 7}\n',
                     observed_at: str = "2026-01-04T12:00:00Z") -> tuple[str, Reference]:
    """Write an invented example bundle; not a production acquisition interface."""
    root.mkdir(parents=True)
    key = "observations/sample.json"
    (root / "observations").mkdir()
    (root / key).write_bytes(payload)
    ref = Reference(parent_id, key, sha256(payload), len(payload), observed_at)
    manifest = {"schema": "public-synthetic-parent-v1", "parent_id": parent_id,
                "entries": [{k: getattr(ref, k) for k in
                             ("key", "content_sha256", "size_bytes", "observed_at")}]}
    body = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (root / "manifest.json").write_bytes(body)
    return sha256(body), ref


def demonstration() -> dict:
    """Reproduce an omitted-parent failure, then recover under explicit admission."""
    decision = "2026-01-05T12:00:00Z"
    with tempfile.TemporaryDirectory(prefix="sports-edge-provenance-") as directory:
        root = Path(directory)
        alpha_pin, alpha_ref = synthetic_parent(root / "original" / "alpha", "alpha")
        beta_pin, beta_ref = synthetic_parent(root / "original" / "beta", "beta",
                                              payload=b'{"value": 11}\n')
        restored = root / "restored"
        restored.mkdir()
        shutil.move(str(root / "original" / "alpha"), restored / "a")
        shutil.move(str(root / "original" / "beta"), restored / "b")
        alpha = admit_parent(restored / "a", expected_parent_id="alpha", expected_manifest_sha256=alpha_pin)
        beta = admit_parent(restored / "b", expected_parent_id="beta", expected_manifest_sha256=beta_pin)
        try:
            Registry([alpha]).read(beta_ref, decision_at=decision)
        except ProvenanceError as error:
            missing_parent = str(error)
        else:
            raise AssertionError("omitted parent was accepted")
        registry = Registry([alpha, beta])
        observations = [registry.read(ref, decision_at=decision) for ref in (alpha_ref, beta_ref)]
        (restored / "b" / beta_ref.key).write_bytes(b'{"value": 99}\n')
        try:
            registry.read(beta_ref, decision_at=decision)
        except ProvenanceError as error:
            tamper = str(error)
        else:
            raise AssertionError("changed content was accepted")
        return {"schema": "sports-edge-provenance-demo-v1", "data_kind": "synthetic",
                "new_fits": 0, "network_calls": 0, "omitted_parent": missing_parent,
                "parents_recovered": [o.reference.parent_id for o in observations],
                "same_relative_key_scoped_by_parent": alpha_ref.key == beta_ref.key,
                "observation_clocks_preserved": all(o.reference.observed_at == "2026-01-04T12:00:00Z" for o in observations),
                "values": [json.loads(o.content)["value"] for o in observations],
                "tampered_content": tamper,
                "claim": "Synthetic contract demonstration; private repair and owner execution remain separate."}


if __name__ == "__main__":
    print(json.dumps(demonstration(), indent=2))
