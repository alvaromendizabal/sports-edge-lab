"""Invented installed-file evidence contract; stdlib only, no package execution.

This is an educational local-metadata verifier, not a Conda implementation,
upstream authenticity check, sandbox, installer, or private runtime export.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile


def digest(body):
    return hashlib.sha256(body).hexdigest()


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Expected an explicit lowercase SHA-256")
    return value


def _optional_size(item, key):
    if key not in item:
        return None
    value = item[key]
    if type(value) is not int or value < 0:
        raise ValueError("Invalid byte count: " + key)
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate metadata key")
        result[key] = value
    return result


def _relative(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError("Unsafe package path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or str(path) != name or name == ".":
        raise ValueError("Unsafe package path")
    return name


def _reject_symlink_components(path):
    # Inspect the supplied spelling before resolve() removes ancestor links.
    path = path.absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Symlink boundary is unsupported")


@dataclass(frozen=True)
class Receipt:
    metadata_sha256: str
    package: str
    # Keep original packaged-file identity separate from installed identity.
    # (path, measured bytes, installed SHA, original SHA, original bytes,
    #  optional declared installed bytes). Measured length is never omitted.
    files: tuple
    trust_boundary: str = "local installed metadata; upstream archive not authenticated"


def verify_tree(root, metadata_path, *, trusted_metadata_sha256):
    """Verify every file under a bounded root against already-pinned metadata.

    The caller supplies the metadata pin from its chosen trust boundary. This
    function never manufactures expected installed hashes from observed files.
    Metadata must live outside the bounded root to avoid a self-hash problem.
    Symlinks and special files are rejected. Returned evidence is a measurement,
    not a guarantee against mutation after verification.
    """
    _sha(trusted_metadata_sha256)
    root, metadata_path = Path(root), Path(metadata_path)
    _reject_symlink_components(root)
    _reject_symlink_components(metadata_path)
    if not root.is_dir() or not metadata_path.is_file():
        raise ValueError("Missing package root or metadata file")
    root = root.resolve()
    if metadata_path.resolve().is_relative_to(root):
        raise ValueError("Metadata must be outside the package root")
    raw = metadata_path.read_bytes()
    if digest(raw) != trusted_metadata_sha256:
        raise ValueError("Metadata changed or is not the pinned document")
    document = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(document, dict) or set(document) != {"schema", "package", "files"}:
        raise ValueError("Unexpected metadata fields")
    if document["schema"] != "invented.installed-files.v1":
        raise ValueError("Unsupported metadata schema")
    if not isinstance(document["package"], str) or not document["package"]:
        raise ValueError("Missing package identity")
    if not isinstance(document["files"], list) or not document["files"]:
        raise ValueError("No installed-file evidence")
    expected = {}
    folded = set()
    for item in document["files"]:
        if not isinstance(item, dict) or not {"path", "installed_sha256"} <= set(item) or set(item) - {"path", "installed_bytes", "installed_sha256", "original_sha256", "original_bytes"}:
            raise ValueError("An explicit installed digest is required")
        name = _relative(item["path"])
        if name.casefold() in folded:
            raise ValueError("Duplicate or case-colliding package path")
        folded.add(name.casefold())
        expected[name] = (
            _optional_size(item, "installed_bytes"),
            _sha(item["installed_sha256"]),
            _sha(item["original_sha256"]) if "original_sha256" in item else None,
            _optional_size(item, "original_bytes"),
        )
    observed = {}

    def scan_error(error):
        raise ValueError("Package inventory could not be completed") from error

    for directory, directories, files in os.walk(root, followlinks=False, onerror=scan_error):
        directories.sort()
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise ValueError("Symlink payload is unsupported")
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError("Symlink payload is unsupported")
            if not path.is_file():
                raise ValueError("Special payload is unsupported")
            name = path.relative_to(root).as_posix()
            body = path.read_bytes()
            observed[name] = (len(body), digest(body))
    if set(observed) != set(expected):
        raise ValueError("Package tree is not exactly covered by metadata")
    for name, actual in observed.items():
        declared_size, installed_sha, _, _ = expected[name]
        if actual[1] != installed_sha or (declared_size is not None and actual[0] != declared_size):
            raise ValueError("Installed payload mismatch: " + name)
    # An installed digest binds the complete observed byte string. An original
    # source-file length is provenance, never an installed-length constraint.
    return Receipt(trusted_metadata_sha256, document["package"], tuple(
        (name, *observed[name], expected[name][2], expected[name][3], expected[name][0])
        for name in sorted(expected)
    ))


def recheck_before_use(receipt, root, metadata_path):
    """Re-read metadata and the full tree; changing a receipt is not revalidation."""
    if not isinstance(receipt, Receipt):
        raise ValueError("A prior verification receipt is required")
    current = verify_tree(root, metadata_path, trusted_metadata_sha256=receipt.metadata_sha256)
    if current != receipt:
        raise ValueError("Package evidence changed")
    return current


def demo():
    # All data are invented; the expected pin is fixed before any verification.
    installed = b"INVENTED installed prefix\n"
    original = b"INVENTED archive placeholder\n"
    document = {"schema": "invented.installed-files.v1", "package": "invented-example", "files": [{"path": "example.py", "installed_sha256": digest(installed), "original_sha256": digest(original), "original_bytes": len(original)}]}
    raw = (json.dumps(document, sort_keys=True) + "\n").encode()
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder).resolve()
        root = base / "package"
        root.mkdir()
        (root / "example.py").write_bytes(installed)
        metadata = base / "metadata.json"
        metadata.write_bytes(raw)
        receipt = verify_tree(root, metadata, trusted_metadata_sha256=digest(raw))
        recheck_before_use(receipt, root, metadata)
        (root / "example.py").write_bytes(b"INVENTED changed payload\n")
        try:
            recheck_before_use(receipt, root, metadata)
        except ValueError:
            mutation_rejected = True
        else:
            mutation_rejected = False
        return {"invented_example": True, "verified_files": len(receipt.files), "original_equals_installed": receipt.files[0][2] == receipt.files[0][3], "measured_installed_bytes": receipt.files[0][1], "original_bytes": receipt.files[0][4], "declared_installed_bytes": receipt.files[0][5], "later_mutation_rejected": mutation_rejected, "package_code_executed": False, "owner_success_claimed": False, "trust_boundary": receipt.trust_boundary}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
