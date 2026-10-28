"""Portable dependency closure and immutable original decisions on invented data.

No provider calls, football features, fitting or orders. The expected manifest and
original-decision hashes are caller-held trust anchors, not self-authentication.
This is a trusted, quiescent local-filesystem example, not a hostile-process sandbox.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile

SCHEMA = "public.portable-recovery.v1"


class RecoveryError(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative(name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise RecoveryError("canonical relative path required")
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ("", ".", "..") for x in name.split("/")) or p.as_posix() != name:
        raise RecoveryError("canonical relative path required")
    if name in ("manifest.json", "export.json"):
        raise RecoveryError("reserved bundle path")
    return p


def regular_bytes(root, name):
    relative(name)
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise RecoveryError("regular root directory required")
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise RecoveryError("symlink artifacts or parents are not admitted")
    if not stat.S_ISREG(current.stat().st_mode):
        raise RecoveryError("regular artifact required")
    return current.read_bytes()


def validate(manifest, expected_sha256):
    if digest(encoded(manifest)) != expected_sha256:
        raise RecoveryError("manifest differs from caller-held commitment")
    if set(manifest) != {"schema", "artifacts", "stages"} or manifest["schema"] != SCHEMA:
        raise RecoveryError("unsupported manifest schema")
    artifacts, stages = manifest["artifacts"], manifest["stages"]
    if not isinstance(artifacts, dict) or not artifacts or not isinstance(stages, dict) or not stages:
        raise RecoveryError("nonempty artifact and stage maps required")
    for name, record in artifacts.items():
        relative(name)
        if not isinstance(record, dict) or set(record) != {"sha256", "bytes", "requires"}:
            raise RecoveryError("exact artifact contract required")
        h, size, deps = record["sha256"], record["bytes"], record["requires"]
        if not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
            raise RecoveryError("exact SHA-256 required")
        if type(size) is not int or size < 0:
            raise RecoveryError("nonnegative byte count required")
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps) or len(set(deps)) != len(deps) or not set(deps) <= set(artifacts):
            raise RecoveryError("every dependency must be unique and explicitly pinned")
    for stage, roots in stages.items():
        if not isinstance(stage, str) or not stage or not isinstance(roots, list) or not roots or any(not isinstance(x, str) for x in roots) or len(set(roots)) != len(roots) or not set(roots) <= set(artifacts):
            raise RecoveryError("nonempty unique stage roots required")
    for name in artifacts:
        closure(manifest, [name])


def closure(manifest, roots):
    visited, active = set(), set()
    def visit(name):
        if name in active:
            raise RecoveryError("dependency cycle")
        if name in visited:
            return
        if name not in manifest["artifacts"]:
            raise RecoveryError("undeclared dependency")
        active.add(name)
        for dependency in manifest["artifacts"][name]["requires"]:
            visit(dependency)
        active.remove(name)
        visited.add(name)
    for name in roots:
        visit(name)
    return sorted(visited)


def seal(root, dependencies, stages):
    """Pin declared inputs and outputs; declaration completeness is caller-owned."""
    artifacts = {}
    for name, requires in dependencies.items():
        raw = regular_bytes(root, name)
        artifacts[name] = {"sha256": digest(raw), "bytes": len(raw), "requires": list(requires)}
    manifest = {"schema": SCHEMA, "artifacts": artifacts, "stages": json.loads(encoded(stages))}
    pin = digest(encoded(manifest))
    validate(manifest, pin)
    return manifest, pin


def inspect(root, manifest, expected_sha256, stages=None):
    validate(manifest, expected_sha256)
    selected = list(manifest["stages"]) if stages is None else list(stages)
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(manifest["stages"]):
        raise RecoveryError("explicit unique registered stage selection required")
    results = []
    for stage in selected:
        required = closure(manifest, manifest["stages"][stage])
        missing, corrupt, verified = [], [], []
        for name in required:
            try:
                raw = regular_bytes(root, name)
            except FileNotFoundError:
                missing.append(name)
                continue
            except (OSError, RecoveryError):
                corrupt.append(name)
                continue
            record = manifest["artifacts"][name]
            (verified if len(raw) == record["bytes"] and digest(raw) == record["sha256"] else corrupt).append(name)
        results.append({"stage": stage, "status": "READY" if not missing and not corrupt else "BLOCKED",
                        "required": len(required), "verified": len(verified), "missing": missing, "corrupt": corrupt})
    return {"manifest_sha256": expected_sha256, "stages": results,
            "all_selected_stages_ready": all(r["status"] == "READY" for r in results)}


def export(root, manifest, expected_sha256, destination, *, stages=None, max_bytes=1_000_000):
    """Publish only after the complete selected transitive closure passes."""
    report = inspect(root, manifest, expected_sha256, stages)
    if not report["all_selected_stages_ready"]:
        raise RecoveryError("selected closure incomplete; no portable bundle published")
    if type(max_bytes) is not int or max_bytes < 0:
        raise RecoveryError("nonnegative export byte limit required")
    chosen = [r["stage"] for r in report["stages"]]
    paths = closure(manifest, [p for stage in chosen for p in manifest["stages"][stage]])
    metadata = {"manifest.json": encoded(manifest), "export.json": encoded({"stages": chosen, "manifest_sha256": expected_sha256})}
    total = sum(manifest["artifacts"][n]["bytes"] for n in paths) + sum(map(len, metadata.values()))
    if total > max_bytes:
        raise RecoveryError("complete closure exceeds export limit")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise RecoveryError("immutable destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".portable-", dir=destination.parent))
    try:
        for name in paths:
            raw = regular_bytes(root, name)
            pin = manifest["artifacts"][name]
            if len(raw) != pin["bytes"] or digest(raw) != pin["sha256"]:
                raise RecoveryError("artifact changed during export")
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        for name, raw in metadata.items():
            with (stage / name).open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        if not inspect(stage, manifest, expected_sha256, chosen)["all_selected_stages_ready"]:
            raise RecoveryError("copied closure failed verification")
        # A quiescent local destination is an explicit contract. No concurrent writers.
        os.rename(stage, destination)
        descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {"status": "PUBLISHED", "files": len(paths), "bytes": total,
            "stages": chosen, "manifest_sha256": expected_sha256}


def admit_original(raw, expected_sha256):
    """Validate original immutable bytes; absence never becomes empty context."""
    if digest(raw) != expected_sha256:
        raise RecoveryError("original decision changed")
    try:
        decision = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RecoveryError("invalid original decision") from exc
    if not isinstance(decision, dict) or set(decision) != {"schema", "issue", "issued_at", "policy", "week_locks", "allocations"}:
        raise RecoveryError("exact original-decision schema required")
    if decision["schema"] != "public.invented-decision.v1" or not isinstance(decision["week_locks"], dict) or not decision["week_locks"]:
        raise RecoveryError("authenticated original whole-week context required")
    return decision


def import_original(root, name, expected_sha256, *, release):
    raw = regular_bytes(root, name)
    decision = admit_original(raw, expected_sha256)
    return {"decision": decision, "original_sha256": expected_sha256,
            "transport": {"release": str(release), "local_member": name}}


def fixture(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    decision = {"schema": "public.invented-decision.v1", "issue": "invented-week-9",
                "issued_at": "2030-10-01T12:00:00Z", "policy": "invented-frozen-policy",
                "week_locks": {"invented-league:9": {"deadline": "2030-10-02T12:00:00Z", "universe": ["Amber-Indigo", "Cedar-Silver"]}},
                "allocations": [{"event": "Amber-Indigo", "stake": 25, "currency": "USD", "execution": "HYPOTHETICAL_UNQUALIFIED"}]}
    files = {"inputs/source.json": {"observed_at": "2030-10-01T11:00:00Z", "invented": True},
             "inputs/policy.json": {"identity": "invented-frozen-policy", "selection_season_max": 2029},
             "inputs/original-context.json": decision["week_locks"],
             "outputs/forecast.json": {"issued_at": decision["issued_at"], "probability": 0.57, "qualified": False},
             "outputs/quotes.json": {"observed_at": "2030-10-01T12:00:01Z", "fill_proven": False},
             "outputs/original-decision.json": decision,
             "outputs/research.json": {"accepted_invented_units": 1, "qualified": False}}
    for name, value in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded(value))
    dependencies = {"inputs/source.json": [], "inputs/policy.json": [], "inputs/original-context.json": [],
                    "outputs/forecast.json": ["inputs/source.json", "inputs/policy.json"],
                    "outputs/quotes.json": ["outputs/forecast.json"],
                    "outputs/original-decision.json": ["inputs/original-context.json", "outputs/forecast.json", "outputs/quotes.json"],
                    "outputs/research.json": ["inputs/source.json", "inputs/policy.json"]}
    stages = {"forecasts": ["outputs/forecast.json"], "venue_capture": ["outputs/quotes.json"],
              "financial_evidence": ["outputs/original-decision.json"], "research": ["outputs/research.json"]}
    return seal(root, dependencies, stages)


def walkthrough():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        owner, sparse, portable = root / "owner", root / "sparse", root / "portable"
        manifest, pin = fixture(owner)
        shutil.copytree(owner, sparse)
        (sparse / "inputs/original-context.json").unlink()
        incomplete = inspect(sparse, manifest, pin)
        proof = "outputs/original-decision.json"
        expected = manifest["artifacts"][proof]["sha256"]
        bad = json.loads(regular_bytes(sparse, proof))
        bad["week_locks"] = {}  # The historical defect: absent is not an empty universe.
        try:
            admit_original(encoded(bad), expected)
        except RecoveryError:
            changed_context_rejected = True
        else:
            raise AssertionError("changed original proof was accepted")
        original = import_original(sparse, proof, expected, release="invented-next-release")
        published = export(owner, manifest, pin, portable)
        reopened = inspect(portable, manifest, pin)
        relocated = import_original(portable, proof, expected, release="invented-relocated-release")
        assert original["decision"] == relocated["decision"]
        return {"classification": "INVENTED_OFFLINE_EXAMPLE", "actual_orders": 0,
                "real_fits": 0, "profit": None, "sparse": incomplete,
                "export": published, "portable": reopened,
                "changed_context_rejected": changed_context_rejected,
                "original_decision_preserved": original["original_sha256"] == relocated["original_sha256"],
                "forecast_issue_preserved": json.loads((portable / "outputs/forecast.json").read_bytes())["issued_at"] == "2030-10-01T12:00:00Z",
                "independent_research_ready": next(r["status"] for r in incomplete["stages"] if r["stage"] == "research") == "READY",
                "transport_changes_semantic_identity": False}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, sort_keys=True))
