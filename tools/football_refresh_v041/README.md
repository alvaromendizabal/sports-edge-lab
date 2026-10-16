# Football refresh V041

Finite public 2026 NFL refresh plus cached NGS/FTN verification, ACC extraction
and exact identity joins. Deployed version and actual outcomes are in
[`docs/FOOTBALL_REFRESH_V041.md`](../../docs/FOOTBALL_REFRESH_V041.md).

The private deployed PYZ includes `src/config.json` and the original
`sec_seed.json` capture. Raw tables do not belong in Git. The exact deployed
artifact is retained at the S3 key recorded in the report and SHA manifest.
Retrieve that artifact for identical packaged tests:

```bash
python sports_edge_lab_football_refresh_v041_20261016.pyz --self-test
```

Source tests can also run without any credentials or provider calls:

```bash
python tools/football_refresh_v041/src/__main__.py --self-test
python tools/football_refresh_v041/verify_sec_export.py --self-test-only
```

The collector runs all 46 tests before creating runtime AWS clients. It uses
three finite, hash-pinned asset requests, concurrent independent work, source
pacing, existing successful caches, immutable captures, explicit join states,
20-second heartbeats and one return ZIP. It does not resume a paid collector.

`verify_sec_export.py` is a separate offline cached-export recovery utility.
Its eight tests and complete-table SHA parity gate must pass before outputs
can be uploaded. It does not perform network access, alter V041's original
report, infer unpublished statuses or certify historical point-in-time use.
