# Verify the installed tree before consuming it

A file inside a package archive and its installed copy can have different hashes and byte lengths. Installation may replace a build-time prefix, while metadata retains an original file size alongside a digest of the installed bytes. Comparing the installed file to that original size can reject a valid installed-digest match. This does not justify ignoring an explicitly declared installed size or trusting a mismatched digest.

The small [stdlib example](runtime_manifest.py) makes this distinction executable with invented data and temporary files. It verifies an explicitly pinned local metadata document and requires an installed SHA-256 for every file under a bounded package root. An optional `installed_bytes` declaration is enforced when present. The actual full length and SHA-256 are always measured and bound into the receipt, including for empty files. Optional `original_bytes` and `original_sha256` describe the original packaged file; they never substitute for the installed digest or constrain the installed length. Present malformed sizes or hashes still fail, and a failed check never updates expected hashes.

```bash
python tracks/nfl/runtime_manifest.py
python -m unittest discover -s tracks/nfl -p 'test_*.py'
```

The demonstration accepts an exact installed digest with a different original size and no declared installed size. Its receipt retains the measured installed length. It then changes a file and shows that a phase-entry recheck rejects the mutation. Tests cover empty and nonempty files without declared installed sizes, incorrect supplied installed sizes, malformed optional values, wrong digests and appended bytes. All earlier guards for rewritten metadata, complete tree coverage, duplicate JSON keys, traversal paths, symlinks and directory-scan failures remain tested. An incomplete scan is a failure, not an empty directory. Verification reads bytes; it does not import the candidate package, change an environment, make provider requests or fit a model.

## What the receipt means

| Evidence | What it establishes |
|---|---|
| Pinned metadata bytes | The verifier read the specific document chosen by the caller's trust policy |
| Original packaged-file digest and size | Separately recorded provenance; neither field proves the installed content, and this example does not fetch or authenticate the containing archive |
| Required installed SHA-256 | The complete measured byte string matches the supplied local installed digest |
| Optional declared installed size | If present, it must be a nonnegative integer and must match the measured installed length; omission is not a zero |
| Measured installed length | Always retained in the receipt, including zero for an empty file; never replaced with an original source size |
| Complete tree inventory | No additional or missing regular files were observed inside this bounded root |
| Phase-entry recheck | Both metadata and the full tree still match the earlier receipt at the time of measurement |

The caller's metadata pin is a trust input. If an attacker can replace both the metadata and the trusted pin before first verification, this example cannot establish authenticity. Local installed metadata is not an independent upstream signature, and an original packaged-file hash is not proof of the installed bytes. Deliberately repinning changed metadata requires a separate trust decision, not automatic enrollment after a failure.

For example, an invented file can have `original_bytes=27`, measured installed length 25 and a matching installed SHA-256. It passes when `installed_bytes` is omitted or explicitly 25; it fails if `installed_bytes` is explicitly 27. Removing the installed digest also fails even if the original digest and original size happen to match. An appended byte changes the installed digest and is rejected with or without a size declaration.

This is an educational contract, not a Conda parser or a production runtime admission implementation. It supports direct installed hashes only; it does not model prefix-replacement proofs, dependency resolution, imported-module origins or whole-environment isolation. All files under the selected root must be declared; no cache or binary exceptions are implicit. Metadata lives outside that root to avoid self-hashing. Symlinks, including ancestors of supplied root and metadata paths, and special files are outside this example's supported boundary.

Verification is a point-in-time measurement, not an atomic filesystem snapshot or sandbox. Rechecking immediately before use reduces stale-evidence errors but cannot stop concurrent mutation after the check. Production execution needs its own process, filesystem, dependency and ownership controls.

## Actual work versus preparation

The authenticated N017 owner attempt completed standard-library reports and fresh capture, then failed scientific runtime admission. Its evidence contains 843 accepted installed-payload proofs, including 245 earlier RECORD differences with valid installed-manifest proofs, and six remaining size-related rejections across five packages. These diagnostic records are parts of one failed owner attempt, not additional runs or scientific successes.

A separate read-only replay compared 5,285 captured installed-hash observations with their declared installed digests: all agreed. Among those observations, 228 original/source size fields differed from observed installed length or were absent. These counts have different scopes from the 843 accepted proofs and must not be added together. The replay checks captured metadata and observation receipts; it is not 5,285 independent filesystem reads or new runtime admission. Original file sizes and optional size omissions explain why digest authority and byte-count provenance must be kept separate.

**N018 is tested local preparation; owner validation remains pending.** The actual N017 scientific result remains failed. The public contract improves an executable engineering example and establishes no new owner fits, learned forecast issues, scientific improvement or wagering returns. It publishes only invented files and qualified aggregates within the existing [publication boundary](../../docs/PUBLICATION_BOUNDARY.md).
