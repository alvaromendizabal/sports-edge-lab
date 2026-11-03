# Recovered market history without retrospective forecast credit

The acquisition question and the evaluation question are different:
"Can a historical observation be recovered?" and "What claim does that
observation support?" A late archive download must not erase a legitimate
pre-game quote. It also must not manufacture possession before a forecast.

This NBA-owned, credential-free example uses **invented games in 2035**.
It contains no real picks, prices, raw provider payloads or private methods.
The dated public aggregate capsule and public website remain unchanged.

## Two reference panels, three evidence levels

| View | Selection rule | Permitted interpretation |
|---|---|---|
| Latest before tip | Latest observed provider timestamp strictly before scheduled tip | Descriptive closing reference; not interchangeable with a T60 forecast benchmark |
| Cutoff matched | Latest observed timestamp at or before T60 or T120 | Historical comparison if event, side, target, line, product and settlement match |
| Prospective evidence | The same matched observation, actually possessed before cutoff | Evidence usable by a genuinely timestamped prospective pipeline |

Source time and acquisition time are separate columns. Retrieving a source's
authentic 2035-11-01 quote on 2035-11-03 is valid historical recovery, but it
does not establish that the model possessed it on November 1. Fees, depth,
executable price, access and settlement remain separate requirements for P&L.
Unknown P&L is null, not zero. This example always allocates zero.

US and international Polymarket products remain separate. Last trades,
midpoints, bid/ask sides and sampled candles do not become interchangeable
prices. Exhausting a one-minute candle window does not establish the last
available tick. Unknown settlement keeps the observation visible while its
comparison eligibility stays false.

## Run and inspect

```bash
python -m tracks.nba.public_monitor.history_panels
python -m unittest tracks.nba.public_monitor.tests.test_history_panels -v
```

The implementation uses only Python's standard library. The existing
NBA-scoped CI matrix automatically discovers the new negative tests. No
shared CI, other sport, provider account or environment setting is changed.

The walkthrough preserves two inventoried games even though only one has a
reference. It selects an invented 61% T60 quote and a later invented 58%
pre-tip reference into different panels. Same-clock conflicting observations
stop for resolution; exact duplicates are reuse. Outcomes are not accepted
by the selection schema.

## Private dashboard import contract

An owner-private dashboard can retain every inventoried game, include explicit
missing-data reasons, and import a compact derived snapshot locally in the
browser. Its SHA-256 envelope protects the exact bytes against accidental
change; it is **not** a signature or proof of data authenticity. Authentication
of the owner evidence must happen before presentation. An invalid import
should leave the previous view intact. A local import must not send the file
to a server, write durable browser storage, train a model or mutate archives.

This public example demonstrates that integrity envelope with invented JSON.
It does not publish or link a private dashboard, supply its private dataset,
or claim that current-season coverage is complete. Frozen reconstructions,
genuine issues and an inactive rolling protocol must retain separate labels.

## Review boundary

This change adds generic engineering behavior and meaningful tests, not a new
model, acquisition result, profitability result or promotion. It does not
change the [publication boundary](../../../docs/PUBLICATION_BOUNDARY.md), the
94-game public capsule, or any historical negative finding. Actual private
artifacts, credentials, licensed data and exact active methods remain outside
the public repository.
