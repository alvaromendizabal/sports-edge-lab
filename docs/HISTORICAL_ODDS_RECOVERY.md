# Recover missing odds without paying for duplicate evidence

[Project](../README.md) · [Executable contract](../examples/basketball_contracts/recovery_plan.py) · [Tests](../examples/basketball_contracts/tests/test_recovery_plan.py) · [Publication boundary](PUBLICATION_BOUNDARY.md)

Historical acquisition needs a precise answer to two separate questions: which observations are usable at the intended prediction cutoff, and which missing observations justify another request? A file inventory alone answers neither. Repeated copies can inflate coverage, a cached price can be too stale for the target, and an empty response can be downloaded repeatedly without filling any gap.

The public implementation joins a content-verified catalog, a deterministic recovery planner and an append-only quota journal. It is an executable engineering example with invented data. It makes zero requests, spends zero credits, trains no models, reads no credentials and provides no evidence of a predictive or trading advantage.

## Run the example

Python 3.11 or 3.12 on a POSIX system, with no third-party dependencies:

```bash
python -m unittest discover -s examples/basketball_contracts/tests -p test_recovery_plan.py -v
python -m examples.basketball_contracts.recovery_plan
```

The walkthrough creates three invented NBA games requiring moneyline and total observations: six event/market/region cells. Two archive aliases contain the same verified bytes, so the catalog counts one content object and preserves two retrieval receipts. That object supplies two eligible cells. The two remaining games share one exact snapshot request for two markets, with a preflight ceiling of 20 credits. This is a calculated proposal; the actual request count and actual credits spent remain zero.

The existing basketball CI suite discovers the new tests on both supported Python versions. The workflow also runs the walkthrough. No account, external data or private research package is needed.

## Catalog and request identity

`Catalog.add` hashes each supplied payload before indexing its normalized records. Identical bytes share a content object while retaining distinct retrieval receipts and storage aliases. Different bytes under an existing alias create a separate version. An alias is an opaque local identifier, never a signed URL or credential-bearing endpoint.

The envelope is deliberately named `public.normalized_historical_odds.v1`; it is **not** the provider's native response schema. A real ingestion adapter must preserve raw source bytes, validate provider identity, perform documented normalization and retain the relationship between those originals and the normalized payload. This example does not establish provider authenticity merely by computing a hash.

The caller seals a declared inventory scope only after classifying its relevant existing objects. Unresolved objects block planning. A seal does not assert that every object in a bucket or every possible source has been inspected. Existing manifests and selected prefixes can define the bounded inventory; a full bucket scan is unnecessary.

Request identity includes the exact sport, requested snapshot time, unique market set and unique region set. The planner combines missing games with the same sport, cutoff and region. It preserves missing-data status when an exact or broader query has already been captured without an eligible quote. It does not turn a stale or empty historical response into automatic permission to fetch the same query again.

## Information-time and identity checks

A reusable observation must match the league's provider sport, native event, ordered home/away identities and exact canonical tipoff. A changed commence time is not silently accepted as a schedule revision. Each need pins a separate binding receipt; the source adapter remains responsible for obtaining independent evidence for that binding.

The enforced clock ordering is:

`quote update <= archived snapshot <= model cutoff < canonical tipoff`

The quote update must also be within the specified freshness window. The default example uses 900 seconds. Retrieval can occur later when reading a genuine historical archive; that later download does not make the row an archived prospective forecast or prove historical executable liquidity. Paired moneyline, spread and total outcomes are validated, including opposing spread lines and equal total lines. A malformed, conflicting or after-cutoff record cannot repair apparent coverage.

The denominator is unique event/cutoff/market/region cells. Duplicate needs and multiple bookmaker observations do not become additional independent games. Uncovered cells are not evidence that no bookmaker offered the event.

## Supported provider contract

The implementation scopes cost arithmetic to The Odds API's **historical featured-market endpoint in explicit region mode**, covering `h2h`, `spreads` and `totals`. Its documented preflight ceiling is `10 × markets × regions`. The returned archive timestamp is at or before the requested date; actual response usage headers govern the observed charge. An empty result may cost zero provider credits while still consuming an HTTP request. [Official V4 documentation](https://the-odds-api.com/liveapi/guides/v4/).

The provider's historical coverage table, checked October 28, 2026, lists these earliest sport timestamps. They are product coverage bounds, not proof that any particular account is entitled or that every game/bookmaker/market exists. [Official historical coverage table](https://the-odds-api.com/historical-odds-data/).

| League | Sport identity | Earliest listed historical timestamp |
|---|---|---|
| NBA | `basketball_nba` | `2020-06-27T03:55:00Z` |
| NCAA men | `basketball_ncaab` | `2020-11-16T09:15:00Z` |
| NCAA women | `basketball_wncaab` | `2024-11-12T21:15:38Z` |

| Capability | Demonstrated behavior |
|---|---|
| Historical featured odds, region mode | Supported planning and bounded cost arithmetic |
| Existing normalized originals | Verified content reuse with retained source receipts |
| Missing or expired entitlement evidence | No request proposed as permitted |
| Unknown, stale or future-dated quota evidence | Dispatch gate remains closed |
| Existing project request and credit ceilings | Independently enforced without reset |
| Empty/stale already-captured requests | Remain explicitly uncovered; no identical automatic pull |
| Bookmaker-list cost mode | Deliberately outside this implementation |
| Historical event odds, player props and pagination | Require distinct endpoint adapters and cost contracts |
| Current odds and prospective capture | Require separate freshness and endpoint contracts |
| S3 listing, provider transport, credentials and orders | Not implemented by this public example |

A production adapter must verify the active account, entitlement, actual sport/market availability and current documentation. The demonstration uses invented capability and authorization receipts; it does not contact or verify the project owner's subscription. No key, account identifier or private object location appears in the example.

## Durable reservations and honest unknown spend

The quota journal uses a POSIX advisory lock, a hash-linked JSONL event stream and `fsync` before a reservation is returned. All workers must use the same journal file. Before a request could be sent, a reservation increments the cumulative request count and charges the maximum declared credits. A lost response keeps the reservation. A retry needs a new attempt identity and another allowance; replaying the same attempt returns its existing state.

A completed response supplies the actual nonnegative credit cost, response hash and observation time. That time cannot precede reservation. A confirmed zero-credit response releases its credit reservation while retaining the consumed request. A different completion cannot overwrite an accepted receipt. Unexpected actual cost above the declared contract is recorded in full and freezes subsequent reservations for investigation.

Fresh quota headers can still omit in-flight requests. The journal deducts unresolved reservations and completed charges whose response clocks are at or after the quota observation. Reusing an older still-fresh header therefore cannot refund intervening known spend. The constructor also verifies the original budget identity, so a restart cannot silently replace its limits or cumulative baseline. Truncated or edited journal data fails closed.

This local journal does **not** replace the shared account lease and quota commitments used by independently running collectors. A real dispatcher must acquire the existing account-wide coordination mechanism, reconcile other active jobs and reserve their commitments before passing an available quota to this contract. Different projects cannot use separate local journals to create independent claims on the same provider allowance. Secure runtime secret retrieval, authenticated response headers and provider delivery are intentionally outside the public example.

## What this contributes

The change adds reusable acquisition invariants and a working failure model: cached bytes are verified, missing observations are distinct from missing requests, pregame eligibility is explicit, costs are bounded before work, and ambiguous interruption cannot reset spending. It supplies engineering evidence for the recovery pipeline. Real recovery yield, modeling gains, forecast settlement and market superiority require their own authenticated owner-run evidence.

## Gap provenance and continuation after a blocked run

[B008 actually reached an incomplete-inventory gate](BASKETBALL_B008_EXECUTION.md), so it made zero paid requests and consumed zero provider credits. It did not verify the owner's current subscription quota. That outcome is distinct from the successful invented walkthrough.

Every planned cell now retains its cutoff, declared inventory-scope pin, binding receipt, required request identity and matching captured-response receipt pins. Its provenance distinguishes a usable archive observation, an already captured query with no eligible observation, and a query not found in the declared inventory. The last category describes the inspected scope; it does not prove universal absence. An empty captured response remains a gap and retains its original content pin, while the exact duplicate query remains deferred. Neither an inventory count nor a new download timestamp establishes historical eligibility.

The [continuation example](../examples/basketball_contracts/continuation.py) exercises the durable journal through a lost response, reopening and zero-credit completion. It preserves original authorization identity across code releases. Original approved limits and the original counter baseline remain pinned; prior spend, unresolved requests and adopted active-time floors do not reset. The caller must authenticate the original authority and exact live closing receipt before supplying those inputs. This public example does not implement that private archive verifier or the shared account lease.
