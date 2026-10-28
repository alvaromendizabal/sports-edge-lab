# Portfolio evidence: decisions, prices and outcomes

A profitable-looking replay can fail for three independent reasons: its selections used future outcomes, its prices were not executable, or its accounting allocated the same capital more than once. The public [portfolio evidence example](../examples/review_lab/portfolio_evidence.py) makes these boundaries explicit using invented events. It extends the existing [decision ledger](../examples/review_lab/decision_replay.py); it does not introduce a second selector or expose the private staking recipe.

## Two evidence dimensions

| Decision origin | What the description establishes |
|---|---|
| Archived pregame prediction | An independently verified prediction existed before the event and its decision cutoff. |
| Reconstructed walk-forward prediction | A later reconstruction applies a chronological rule. It is not a historical prediction archive. |
| Forward paper portfolio | A frozen prospective decision records intended selections without claiming an execution. |
| Actual executed portfolio | Independently verified fills and settlements are required in addition to the decision record. |

| Price evidence | Permitted economic interpretation |
|---|---|
| Unavailable | Profit and ROI remain unknown. |
| Display price or midpoint only | A probability comparison may be possible; executable profit remains unknown. |
| Archived ask, depth, fees and contract terms | A disclosed hypothetical execution scenario may be computed. A fill is still not proved. |
| Execution receipts | Actual cost and fill quantities may support realized profit after verified settlement. This example does not implement a fill-receipt verifier. |

These dimensions must be reported separately. A genuine historical model forecast paired with a guessed price still cannot establish trading profit. Conversely, an excellent quote archive does not repair a selection made after inspecting winners.

## Commit before settlement

```bash
python -m examples.review_lab.portfolio_evidence
python -m unittest examples.review_lab.tests.test_portfolio_evidence -v
```

The example persists the outcome-free candidate selection, hashes its exact bytes and hands a separate commitment to settlement. Settlement reads the committed file and never invokes selection. Mutating outcomes changes settlement, while the selected positions and commitment remain identical. Unknown outcomes stay pending; display-only quotes return null profit and null ROI rather than fabricated zeros.

A local hash proves integrity against a separately retained expected hash. It does not prove historical existence, independent timestamping, truthful inputs, geographic eligibility or executable liquidity. Evidence class assignment is the responsibility of an external verifier. The demo's data is entirely invented and deliberately makes no archival or real-world performance claim.

## Venue alternatives share one capital allocation

The comparator treats venue A, venue B and best available venue as mutually exclusive scenarios for the same league, native season week and budget. The illustrative $100 allocation is reported once, even when three alternatives are displayed. Scenario profits must not be added. The demonstration is a capital-accounting boundary, not a venue router or an execution simulator.

The existing candidate ledger enforces quote age, fees, displayed depth and model availability. This extension preserves those checks and adds persisted commitment verification plus explicit price-evidence classification. There are no network requests, exchange orders, live forecasts or proprietary datasets in the example.

## Review questions

1. Was the complete eligible candidate universe recorded before outcomes were available?
2. Does independent evidence establish the claimed prediction and quote timestamps?
3. Do the price, contract target, fees and available depth support the reported execution scenario?
4. Is the same capital counted only once across alternative venues?
5. Are simulated profit, paper performance and actual execution kept distinct?

The answer to a missing evidence question is an explicit unavailable result, not a guessed number. Better probability scores may help discover useful opportunities, but fees, spreads, selection rules and risk determine whether a portfolio benefits.
