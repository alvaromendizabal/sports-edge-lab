# Offline receipt closure

An archive may have several logical references to the same physical member. A
consumer that confuses those counts can reject an otherwise consistent receipt,
or silently lose aliases when adapting an older reference format. This example
makes those counts explicit and verifies the supplied archive before reporting a
complete result.

The [verifier](receipt_closure.py) and its [tests](tests/test_receipt_closure.py)
use the Python standard library. Every test archive is constructed from invented
bytes. The verifier performs no network requests, extraction or code execution.

## Count meanings

The principal fixture contains three payload files and one manifest. Two logical
aliases both refer to one of those payload files.

| Field | Fixture value | Meaning |
| --- | ---: | --- |
| `physical_members` | 4 | All entries exposed by the ZIP central directory, including the manifest |
| `payload_members` | 3 | Physical files covered by the manifest |
| `logical_descriptors` | 2 | All aliases in the caller's complete descriptor map |
| `unique_referenced_members` | 1 | Distinct physical payload paths named by those aliases |

`reference_members` means the logical descriptor count. Normalization validates
every alias before deriving that count. It does not deduplicate aliases, discard
member pins or substitute the manifest's payload count.

## Reference compatibility

A reference contains `object_id`, `bytes` and lowercase hexadecimal `sha256`.
Each descriptor contains the matching `object_id`, `object_bytes` and
`object_sha256`, plus its physical `member` path, `bytes` and `sha256`.

| Declared reference schema | Missing `reference_members` | Present count |
| --- | --- | --- |
| Absent, the documented legacy shape | Derive from the complete descriptor map | Require exact logical count |
| `receipt-reference.v1` | Derive from the complete descriptor map | Require exact logical count |
| `receipt-reference.v2` | Reject | Require exact logical count |
| Any other value, including null | Reject | Reject |

Only an absent field is eligible for the legacy adapter. An explicit null,
boolean, negative number, noninteger or conflicting count is an error. The
adapter returns a deep copy, preserving the original reference, its additional
metadata and the caller's descriptor map. Conflicting pins for aliases of one
physical member are rejected.

The expected whole-object pin and **complete** descriptor map must come from an
independently trusted parent. A verifier cannot infer omitted aliases from the
archive. An explicitly empty map can represent zero aliases only when that
trusted parent establishes that the inventory is complete.

## Archive admission

The manifest is `MANIFEST.json` with schema `receipt-payload-manifest.v1`. Its
`files` map gives byte and SHA-256 pins for every other physical entry. If present,
`payload_members` must equal the size of that physical file map. Duplicate JSON
keys, nonfinite JSON values and unknown schemas are rejected.

Admission requires the expected byte length and SHA-256 of the complete supplied
archive. It also requires safe relative POSIX paths, exact and casefold uniqueness,
no encryption, explicit Unix regular-file types, and an exact manifest-to-payload
closure. The verifier reads every payload to EOF and checks its CRC, byte length
and SHA-256. All referenced payload pins must agree with the manifest. Unreferenced
payloads are still verified.

The explicit type rule includes the manifest itself. Permission bits such as
`0600` without `S_IFREG` do not establish a regular-file type. Symbolic links,
directories, FIFOs and entries from another host-type convention fail this
contract. A producer needing another convention must define and review that
contract separately; the verifier does not silently relax its claim.

The default limits are 1,000 physical entries and 16 MiB of declared uncompressed
content. Callers can set explicit positive limits. This is a bounded demonstration,
not an extraction utility or a general archive format validator. Physical
membership is the ZIP central-directory view; the expected whole-object digest
also covers prefixes, trailers and other bytes in the supplied object.

## Running the example

From the repository root:

```bash
python -m unittest discover -s tracks/nba/public_monitor/tests -p test_receipt_closure.py -v
```

Application code can call `normalize_reference(reference, descriptors)` at a
legacy adapter boundary, or pass the original reference directly to
`verify_receipt_archive(blob, reference, descriptors)`. Verification returns an
immutable `ReceiptClosure` only after all checks succeed. An error never produces
an empty or partially successful closure receipt.

## Evidence limits

The result's scope is `SUPPLIED_BYTES_ONLY`. Matching an independently trusted pin
establishes consistency with that pinned object; a manifest alone does not
establish who produced it. Offline verification does not establish a fresh GET,
a completed owner computation, child retirement, a source-use grant, a paid-call
entitlement or a successful release. Those claims require their own evidence.

This addition changes no dated diagnostic capsule, generated dashboard or live
provider behavior. The repository's [publication boundary](../../../docs/PUBLICATION_BOUNDARY.md)
continues to apply.
