# November 4 NFL source review

[Live dashboard](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/) · [Track overview](README.md) · [Sanitized source snapshot](source_review_n038.json)

The dashboard now gives DraftKings, Kalshi and Polymarket equal prominence. Choose a source cohort at the top, inspect an individual game, then use **Compare on the same games** for the preserved performance comparisons. Source coverage and model quality answer different questions.

## Current season and Week 9

| Provider | Latest-pregame winner / margin / total references, completed 2026 games | Current Week 9 references |
|---|---|---|
| DraftKings | Separate licensed-source archive; not supplied to this public-only historical exporter | 15 / 15 for each target; 14 direct joins plus one documented kickoff-revision recovery |
| Kalshi | 121 / 121 for each target | 15 / 15 for each target |
| Polymarket | 121 / 121 for each target | 15 / 15 for each target |

The newly published completed-game references include Chicago 34–17 Seattle. Their quote times precede kickoff; their acquisition times can be much later. This establishes a historical market observation, not proof of original possession, executable fills or an originally issued prediction.

DraftKings' November 4 capture listed LV–SF at 21:05 UTC; the independently documented revised kickoff is 21:25 UTC. Recovery binds the exact teams, event and source capture to that schedule revision. Its quote time remains November 4 at 17:31:26 UTC and acquisition remains 17:32:23 UTC. No timestamp is backdated. The earlier captured mapping remains unchanged in its original artifact.

Kalshi and Polymarket current references preserve November 4 capture clocks between 17:30 and 18:25 UTC. For point contracts, selection uses the latest complete two-sided book per captured contract, then the probability midpoint closest to 50%. This outcome-independent display choice is not a claim that the chosen threshold is a main line or expected score. Kalshi provider quote times remain explicitly unavailable where only observation time is supported.

## Latest-pregame historical source scope

| Season | Provider | Winner | Margin conditions | Total conditions | Completed games |
|---|---|---:|---:|---:|---:|
| 2024 | Kalshi | 0 | 0 | 0 | 285 |
| 2024 | Polymarket | 188 | 0 | 0 | 285 |
| 2025 | Kalshi | 257 | 260 | 264 | 285 |
| 2025 | Polymarket | 259 | 259 | 258 | 285 |
| 2026 | Kalshi | 121 | 121 | 121 | 121 |
| 2026 | Polymarket | 121 | 121 | 121 | 121 |

These counts describe the N038 public-source export only. Zero means no qualified reference in that export, not that a provider offered no market. DraftKings' existing authenticated saved-line evaluations remain available separately. Different target/provider counts cannot be used as a common-cohort performance ranking.

## What the observations support

- Winner references are rounded derived binary payout proxies with the declared tie caveats.
- Margin and total references are threshold conditions with observed probabilities. They are not conditional mean scores, full score distributions, model cover probabilities or verified executable prices.
- T1, T2 and T24 remain fixed evaluation checkpoints. Later observations can be displayed without changing the earlier model or its results.
- The source-only update changes no forecast, calibration, recipe, model ranking, hypothetical strategy or historical metric. Existing frozen, rolling and originally issued records keep their separate identities.

## Execution and reproducibility

The actual N038 return is authenticated at 47,824,710 bytes with SHA-256 `b52904f3fbdb1e0debb6db277c2ed72c6bfc06a8e8a3ec367044dd0c2cdb1919`. All 7,128 archive members, 7,127 manifest payloads and the later exact completion receipt passed the stated integrity checks. External omission proofs were structurally reconciled; this does not claim every omitted remote object was independently fetched again.

The run processed 691 completed games and exported 946 winner references and 1,525 point-condition references. Its scientific continuation failed during isolated runtime admission. The public update does not grant new fit or forecast credit and does not promote the failed run to owner research acceptance. Previously issued injury-study cards remain separately dated.

The public validator rejects postkickoff quotes, duplicate/missing cohort cells, private fields, relabelled horizons, threshold-to-score conversions and accidental research promotion. It also keeps direct DraftKings joins separate from the recovered schedule binding. Public checks verify this reporting boundary; they do not reproduce private training.

```bash
python -m unittest discover -s tracks/nfl -p 'test_*.py'
python tracks/nfl/contracts.py --check-review
```

The existing current-season advantage over Kalshi remains descriptive and uncertain. This new coverage does not establish an advantage over any provider. Matched performance comparisons and their limitations are visible for all three providers in the dashboard.
