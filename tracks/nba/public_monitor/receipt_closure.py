"""Offline receipt closure contracts; the accompanying tests use invented bytes.

An expected whole-object pin and a complete descriptor map must come from an
independently trusted parent. Supplied-byte verification cannot establish origin,
a fresh network read, successful computation, or permission to use a source.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import io
import json
import re
import stat
import zipfile
import zlib


MANIFEST_NAME = "MANIFEST.json"
MANIFEST_SCHEMA = "receipt-payload-manifest.v1"
REFERENCE_SCHEMAS = {"receipt-reference.v1", "receipt-reference.v2"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ReceiptError(ValueError):
    """The supplied evidence does not satisfy the declared receipt contract."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReceiptError(reason)


def nonnegative_integer(value: object) -> bool:
    return type(value) is int and value >= 0


def valid_pin(value: object) -> bool:
    return (isinstance(value, dict) and nonnegative_integer(value.get("bytes"))
            and isinstance(value.get("sha256"), str)
            and SHA256.fullmatch(value["sha256"]) is not None)


def safe_path(name: object) -> bool:
    """Require a relative, unambiguous POSIX file path without control bytes."""
    return (isinstance(name, str) and bool(name)
            and not any(ord(char) < 32 or ord(char) == 127 for char in name)
            and "\\" not in name and ":" not in name
            and all(part not in {"", ".", ".."} for part in name.split("/")))


def unique_paths(names: list[str], label: str) -> None:
    require(all(safe_path(name) for name in names), f"UNSAFE_{label}_PATH")
    require(len(names) == len(set(names)), f"DUPLICATE_{label}_PATH")
    require(len(names) == len({name.casefold() for name in names}),
            f"CASEFOLD_{label}_COLLISION")


def strict_json(raw: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def reject_constant(value):
        raise ReceiptError("NONFINITE_JSON_NUMBER")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReceiptError("INVALID_MANIFEST_JSON") from error


def descriptor_pins(reference: dict, descriptors: dict) -> dict:
    """Validate every logical alias before forming a unique physical-pin view."""
    require(isinstance(descriptors, dict), "DESCRIPTOR_MAP_REQUIRED")
    unique_paths(list(descriptors), "LOGICAL")
    members = {}
    for descriptor in descriptors.values():
        require(isinstance(descriptor, dict) and valid_pin(descriptor),
                "DESCRIPTOR_PIN_SCHEMA")
        require(descriptor.get("object_id") == reference["object_id"],
                "DESCRIPTOR_OBJECT_ID")
        require(type(descriptor.get("object_bytes")) is int
                and descriptor["object_bytes"] == reference["bytes"]
                and descriptor.get("object_sha256") == reference["sha256"],
                "DESCRIPTOR_OBJECT_PIN")
        member = descriptor.get("member")
        require(safe_path(member) and member != MANIFEST_NAME,
                "DESCRIPTOR_PAYLOAD_PATH")
        pin = {key: descriptor[key] for key in ("bytes", "sha256")}
        require(member not in members or members[member] == pin,
                "CONFLICTING_MEMBER_PIN")
        members[member] = pin
    unique_paths(list(members), "REFERENCED_MEMBER")
    return members


def normalize_reference(reference: dict, descriptors: dict) -> dict:
    """Copy a legacy reference and supply its checked logical-alias count.

    An absent schema denotes the documented legacy shape. Version 1 permits a
    missing reference_members field; version 2 requires it. Neither an explicit
    null nor a conflicting count is a missing field. All caller fields and all
    original descriptors remain unchanged. Unknown schema versions fail closed.
    """
    require(isinstance(reference, dict) and valid_pin(reference),
            "REFERENCE_PIN_SCHEMA")
    require(isinstance(reference.get("object_id"), str)
            and bool(reference["object_id"]), "REFERENCE_OBJECT_ID")
    schema = reference.get("schema", "receipt-reference.v1")
    require(isinstance(schema, str) and schema in REFERENCE_SCHEMAS,
            "UNSUPPORTED_REFERENCE_SCHEMA")
    descriptor_pins(reference, descriptors)
    expected_count = len(descriptors)  # Preserve repeat aliases to one payload.
    if "reference_members" in reference:
        require(nonnegative_integer(reference["reference_members"])
                and reference["reference_members"] == expected_count,
                "LOGICAL_DESCRIPTOR_COUNT")
    else:
        require(schema != "receipt-reference.v2", "MISSING_V2_DESCRIPTOR_COUNT")
    normalized = deepcopy(reference)
    normalized["reference_members"] = expected_count
    return normalized


@dataclass(frozen=True)
class ReceiptClosure:
    archive_bytes: int
    archive_sha256: str
    physical_members: int
    payload_members: int
    logical_descriptors: int
    unique_referenced_members: int
    verification_scope: str = "SUPPLIED_BYTES_ONLY"


def _verify_archive(blob: bytes, reference: dict, descriptors: dict,
                    max_members: int, max_uncompressed_bytes: int) -> ReceiptClosure:
    reference = normalize_reference(reference, descriptors)
    require(isinstance(blob, bytes), "ARCHIVE_BYTES_REQUIRED")
    require(len(blob) == reference["bytes"], "ARCHIVE_BYTE_COUNT")
    require(hashlib.sha256(blob).hexdigest() == reference["sha256"],
            "ARCHIVE_SHA256")
    require(type(max_members) is int and max_members > 0
            and type(max_uncompressed_bytes) is int and max_uncompressed_bytes > 0,
            "INVALID_RESOURCE_LIMIT")

    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        entries = archive.infolist()
        require(len(entries) <= max_members, "ARCHIVE_MEMBER_LIMIT")
        require(sum(entry.file_size for entry in entries) <= max_uncompressed_bytes,
                "ARCHIVE_UNCOMPRESSED_LIMIT")
        names = [entry.filename for entry in entries]
        unique_paths(names, "ZIP")
        require(MANIFEST_NAME in names, "MISSING_MANIFEST")
        for entry in entries:
            require(entry.orig_filename == entry.filename, "TRUNCATED_ZIP_NAME")
            require(entry.create_system == 3
                    and stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFREG,
                    "EXPLICIT_REGULAR_FILE_REQUIRED")
            require(not entry.flag_bits & 1, "ENCRYPTED_ZIP_MEMBER")

        # Reading to EOF also invokes zipfile's CRC and local-name checks.
        manifest = strict_json(archive.read(MANIFEST_NAME))
        require(isinstance(manifest, dict)
                and manifest.get("schema") == MANIFEST_SCHEMA,
                "UNSUPPORTED_MANIFEST_SCHEMA")
        pins = manifest.get("files")
        require(isinstance(pins, dict), "MANIFEST_FILE_MAP_REQUIRED")
        unique_paths(list(pins), "MANIFEST")
        require(set(pins) == set(names) - {MANIFEST_NAME},
                "EXACT_PAYLOAD_CLOSURE")
        if "payload_members" in manifest:
            require(nonnegative_integer(manifest["payload_members"])
                    and manifest["payload_members"] == len(pins),
                    "PHYSICAL_PAYLOAD_COUNT")

        for name, expected in pins.items():
            require(valid_pin(expected), "MANIFEST_PIN_SCHEMA")
            size = crc = 0
            digest = hashlib.sha256()
            with archive.open(name) as stream:
                while block := stream.read(1 << 20):
                    size += len(block)
                    digest.update(block)
                    crc = zlib.crc32(block, crc)
            entry = archive.getinfo(name)
            require(size == expected["bytes"] == entry.file_size,
                    "MEMBER_BYTE_COUNT")
            require(digest.hexdigest() == expected["sha256"], "MEMBER_SHA256")
            require(crc & 0xFFFFFFFF == entry.CRC, "MEMBER_CRC32")

        members = descriptor_pins(reference, descriptors)
        for name, expected in members.items():
            require(name in pins, "REFERENCED_MEMBER_MISSING")
            require(all(pins[name][key] == expected[key] for key in ("bytes", "sha256")),
                    "REFERENCED_MEMBER_PIN")

        return ReceiptClosure(
            archive_bytes=len(blob), archive_sha256=reference["sha256"],
            physical_members=len(entries), payload_members=len(pins),
            logical_descriptors=reference["reference_members"],
            unique_referenced_members=len(members))


def verify_receipt_archive(blob: bytes, reference: dict, descriptors: dict, *,
                           max_members: int = 1000,
                           max_uncompressed_bytes: int = 16 << 20) -> ReceiptClosure:
    """Verify a bounded ZIP in memory without extraction, network, or execution.

    Physical membership means the entries exposed by the ZIP central directory.
    The expected whole-object pin covers the complete supplied byte string.
    Resource limits are explicit and can be tightened by the caller. An error
    never becomes an empty or partially successful closure receipt.
    """
    try:
        return _verify_archive(blob, reference, descriptors,
                               max_members, max_uncompressed_bytes)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error,
            EOFError) as error:
        raise ReceiptError("ZIP_READ_OR_INTEGRITY_ERROR") from error
