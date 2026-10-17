# Football weekend refresh V049

One finite NFL official injury-report vintage refresh, using v046's tested capture/parser and exact cache reuse. This is not a repeat historical audit. Runtime calls only `validation.injuries`; no odds, CFBD, CBBD, or secrets retrieval path is invoked.

The full 107-test offline suite runs before any runtime AWS client or network request, and runs again in the Processing container. The weekend ledger is read and conditionally updated using its ETag; missing/ambiguous usage fails closed. Provider denials remain durable. One unique return ZIP and a hash manifest accompany the report. Raw player payloads remain private in the canonical bucket.

Reproduction (offline only):

```bash
python -m zipapp src -o sports_edge_lab_weekend_v049.pyz
python sports_edge_lab_weekend_v049.pyz --self-test
```

Do not launch this artifact again: its exact hourly job is `sports-edge-lab-weekend-20261017-01-v049`. Inspect existing job/results instead. The worker's internal run ledger also rejects a duplicate job record. No short application timer; only the finite two-URL NFL request queue (or a cache hit/source stop) executes. AWS defaults to an 86400-second safety maximum; the finite capture is expected to finish in seconds after provisioning.

The unchanged Big Ten Friday rows and eight unchanged public nflverse release assets were checked before launch. No changed release payload was queued. The six-hour current collector remains responsible for current odds. This pass does not claim a fresh CFBD game completion check, full conference coverage, or newly confirmed tracking/video rights.
