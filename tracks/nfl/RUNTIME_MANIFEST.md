# Verify the installed tree before consuming it

A file inside a package archive and its installed copy can have different hashes. Installation may replace a build-time prefix, while metadata may retain both the original file digest and an installed digest. A failed original-file digest comparison is therefore evidence to investigate. It is not permission to trust whichever bytes happen to be present.

The small [stdlib example](runtime_manifest.py) makes this distinction executable with invented data and temporary files. It verifies an explicitly pinned local metadata document, requires an installed digest and size for every file under a bounded package root, and rejects missing, extra, changed or ambiguously named files. The original digest remains a separate provenance field. It cannot substitute for an installed digest, and a failed check never updates expected hashes.

```bash
python tracks/nfl/runtime_manifest.py
python -m unittest discover -s tracks/nfl -p 'test_*.py'
```

The demonstration first accepts a tree whose original and installed digests differ. It then changes a file and shows that a phase-entry recheck rejects the mutation. The tests also cover rewritten metadata, equal file counts with different names, missing evidence, invalid hashes/sizes, duplicate JSON keys, traversal paths, symlinks and directory-scan failures. An incomplete scan is a failure, not an empty directory. Verification reads bytes; it does not import the candidate package, change an environment, make provider requests or fit a model.

## What the receipt means

| Evidence | What it establishes |
|---|---|
| Pinned metadata bytes | The verifier read the specific document chosen by the caller's trust policy |
| Original packaged-file digest | A separately recorded original identity; this example does not fetch or authenticate the containing archive |
| Installed digest and size | The measured installed bytes match the supplied local installed-file record |
| Complete tree inventory | No additional or missing regular files were observed inside this bounded root |
| Phase-entry recheck | Both metadata and the full tree still match the earlier receipt at the time of measurement |

The caller's metadata pin is a trust input. If an attacker can replace both the metadata and the trusted pin before first verification, this example cannot establish authenticity. Local installed metadata is not an independent upstream signature, and an original packaged-file hash is not proof of the installed bytes. Deliberately repinning changed metadata requires a separate trust decision, not automatic enrollment after a failure.

This is an educational contract, not a Conda parser or a production runtime admission implementation. It supports direct installed hashes only; it does not model prefix-replacement proofs, dependency resolution, imported-module origins or whole-environment isolation. All files under the selected root must be declared; no cache or binary exceptions are implicit. Metadata lives outside that root to avoid self-hashing. Symlinks, including ancestors of supplied root and metadata paths, and special files are outside this example's supported boundary.

Verification is a point-in-time measurement, not an atomic filesystem snapshot or sandbox. Rechecking immediately before use reduces stale-evidence errors but cannot stop concurrent mutation after the check. Production execution needs its own process, filesystem, dependency and ownership controls.

## Actual work versus preparation

The authenticated N016 owner attempt stopped at numerical runtime admission before its tests or research. Its aggregated diagnostics exposed additional installed-file evidence requirements. N017 local preparation adds and tests narrower installed-manifest verification and preserves useful reporting before numerical admission. **Owner execution of N017 remains pending.** These are engineering changes; they establish no new owner fits, forecast issues, scientific improvement or wagering returns. The public example publishes only invented files and evidence contracts, within the existing [publication boundary](../../docs/PUBLICATION_BOUNDARY.md).
