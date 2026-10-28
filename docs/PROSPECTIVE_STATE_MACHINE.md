# Prospective decisions are events, not editable rows

[Project](../README.md) · [Example](../examples/review_lab/prospective_state.py) · [Tests](../examples/review_lab/tests/test_prospective_state.py) · [Evidence taxonomy](PORTFOLIO_EVIDENCE.md)

A forecast observed before a game is not necessarily a decision recorded at its declared horizon. The public example makes that distinction executable using invented events and a transactional SQLite journal.

## State and capital boundaries

An early outlook is outside this decision journal. A decision enters only inside its declared window, after its source clocks, contract orientation, price freshness, fee identity and external evidence-review flags pass validation. Settlement is a separate event after kickoff and outcome availability. It never changes the original decision.

The journal reserves a native league-week budget in integer cents, rejects duplicate game exposure, and records both reserved and unsettled capital. A transaction that exceeds the budget rolls back without leaving a partial decision. Settlement releases exposure but does not recycle the weekly allocation into another wager. Alternative venue scenarios require separate journals and remain mutually exclusive, following the existing portfolio-evidence contract.

Each event includes the previous event hash. SQL triggers reject ordinary updates and deletes; verification also detects changed hashes. Exact reentry returns the existing event identity. A changed payload under the same decision identity is rejected. The database uses immediate transactions and full synchronous writes; it is a single-file review example, not a hosted financial service.

## What is demonstrated—and what is not

The demonstration uses an injectable clock and invented probabilities, prices, contracts, fees and outcomes. It verifies software behavior. Evidence flags are inputs from an external verifier, not proof that this module independently authenticated an exchange or a trained model. A hash proves byte integrity, not historical existence; independent timestamp attestation and credentialed exchange verification remain separate operational responsibilities.

No network requests, credentials, orders or real wagers are involved. Actual trading profit remains unavailable. An unsettled paper position also has unavailable profit, not zero. Only normal binary payout examples are implemented here; refunds, ties and venue-specific resolution semantics require a separate qualified contract law.

The private football pipeline retains its own model, source and venue contracts. This sanitized mechanism does not disclose production features, live selections or proprietary datasets.

## Review checklist

- Early and late attempts must fail the declared decision window.
- Future forecasts and stale/future native quotes must fail admission.
- Incomplete external evidence flags must fail admission.
- A failed budget transaction must not leave an event behind.
- Same-input reentry must preserve the original event and timestamp.
- Settlement must append, never rerank or rewrite.
- Current outcomes cannot select a model, policy or stake.
- Local validation, hosted CI, remote publication and actual execution are distinct evidence.
