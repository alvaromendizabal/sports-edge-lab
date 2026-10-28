# Sports Edge Lab · NCAA women's basketball

Player-adjusted team strength, possession efficiency, tempo and roster continuity with explicit separation between long statistical history and shorter odds history.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/ncaaw/` in the central data lake.

## Model sequence

1. Hierarchical team and player ratings.
2. Point-margin and total distributions.
3. Calibrated win-probability classifier.
4. Tournament simulations.

## Feature families

- Possession efficiency and tempo.
- Player role and availability.
- Roster continuity and matchup depth.
- Venue, rest and schedule strength.

## Source scope

- audited ESPN/NCAA interfaces and wehoop/sportsdataverse public archives.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Market evaluation begins only where timestamped quotes are actually present; the planned provider starting date is November 12, 2024. Older statistics do not create older market quotes.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

**Current phase:** first real reconstructed historical evaluation completed; prospective monitoring and MARKET coverage remain incomplete.

## B002 basketball evidence

NCAA women completed 59 native estimator units across the two horizons. The 53-predictor regularized combined model led the full basketball probability cohort; its separate point head uses shared Ridge. Matched T−60 MARKET comparisons contain 23 ending-2025 games and 13 ending-2026 games. No MARKET advantage is established. Twelve current games have early outlooks; no qualified current prices or settled prospective scores were present.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [separate league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures and remain separate from the real aggregate results. B001’s pre-modeling failure is preserved. B003 owner execution is pending.
