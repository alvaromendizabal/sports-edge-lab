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

Current phase: controlled B003 historical experiments completed; source timing, MARKET training support and prospective confirmation remain incomplete.

## B003 basketball evidence

NCAA women added 22 new estimator units, including three changed final T−24h selection units. Rich combined logistic with 63 predictors improved both T−60 historical seasons and reduced pooled log loss from 0.465183 to 0.457143 across 10,901 games. Fixed-bin calibration worsened overall, and 2025 correct picks fell. The expanded T−60 MARKET cohorts contain 149 ending-2025 and 143 ending-2026 games; seasonal differences change sign and both paired intervals include zero. Twelve upcoming games retain early outlooks, no qualified current prices and no settled prospective scores at the snapshot.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. B004 owner execution is pending.
