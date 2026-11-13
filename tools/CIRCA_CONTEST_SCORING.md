# Circa contest scoring adapter (offline)

This is a **small engineering component, not a prediction or wager recommendation**. It selects up to five independent NFL games from a supplied probability distribution over home-team scoring margins and a supplied official static Circa Million contest line. It does not train models, fetch market data, verify third-party authenticity, or publish forecasts.

## Inputs and validation

Pass JSON with a top-level "games" array. Each game must have:

- game_id, home_team, away_team, forecast_id
- kickoff_utc, model_issued_at_utc, line_captured_at_utc (timezone-aware ISO 8601)
- spread_home (signed contest handicap from home-team perspective; half-point increments)
- margin_pmf (integer home-minus-away margin mapped to probabilities summing to 1)
- official_circa_contest_line: true (declaration by the caller)
- contest_line_source (identify a real Circa contest document)

The script rejects game IDs repeated in the same input, forecast/line captures at or after kickoff, invalid PMFs, stale already-started events and missing declared contest lines. It separately records skipped games with reasons.

The caller must independently authenticate the original contest line sheet and forecast, confirm permissible publication, and check the appropriate contest entry deadline. A boolean flag alone does not prove a Circa line is authentic.

## Scoring and selection

For home margin M and actual published home spread S:

    home cover: M + S > 0
    home push:  M + S = 0
    away cover: M + S < 0

Expected contest points for a selection equal P(cover) + 0.5*P(push). The ranked list includes both sides of all eligible games; the top-five recommendation allows at most one side per game. The helper does not model correlated portfolio payout/tournament-winning probability.

Use:

    python3 tools/circa_pickboard.py --input PRIVATE_GENUINE_INPUT.json --asof-utc 2026-11-13T21:00:00Z --output PRIVATE_BOARD.json

Tests:

    python3 -m unittest discover -s tools -p 'test_circa_pickboard.py' -v

All supplied data remains local. No real picks or private source bytes are included in this repository. All games and probabilities must come from the owner's authenticated private issue ledger and source archive before any authorized selected rounded public export.

## Evidence

The 2026 Circa Million VIII official rules establish five picks against a static contest spread and scoring of 1/0.5/0 for cover/push/loss: https://www.circasports.com/wp-content/uploads/2026/05/CircaMillionVIIIContest.2026.pdf

The importance of distributional spread forecasts rather than point margins alone is explored in Dmochowski (2023): https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0287601
