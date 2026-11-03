# FBS: preserve the failed attempt, certify the next step

[Interactive recovery review](recovery.html) · [Completed V024 study](index.html) · [Public aggregates](V025_OPERATIONAL_REVIEW_2026-11-03.json) · [Model card](../../tracks/ncaaf/MODEL_CARD.md)

## The owner result is partial

V025 attempted 198 forward learned fits. It committed 197, reused zero and failed one numerical optimizer attempt. Its 99 final learned states were not attempted. The process returned exit 2 with a preserved diagnostic archive. V024 remains the last completed owner study; there is no new owner-completed performance comparison, issued forecast, order or promotion.

This is an operational failure, not a completed experiment rejecting a modeling hypothesis. A local successful replay did not prove that the owner environment would follow the same solver termination path. The failure and all completed work remain part of the evidence. Private owner recovery requires authenticating the existing states and satisfying unchanged scientific definitions, not merely changing a success flag.

## Reuse the shared certificate, add real restart behavior

The [public checkpoint example](../../examples/fbs_contracts/certified_resume.py) imports the repository’s existing [numerical recovery module](../../examples/review_lab/numerical_recovery.py). It does not fork the certificate or modify another track’s scientific implementation. Its inputs are invented diagonal convex quadratic problems with nonnegative coordinates and a unit-budget constraint. This is not the private football objective.

For a feasible candidate x and the declared convex objective f, convexity gives

`f(x) − f(x*) ≤ ∇f(x) · (x − v)`,

where v minimizes the linear function `∇f(x) · v` over the stated domain. The existing certificate represents finite binary inputs exactly as rational numbers, then rounds the displayed bound upward. Its mathematical assumptions and domain are essential: an infeasible point has no such certificate, and a bound for this example does not certify a different or nonconvex objective.

A solver’s flag and a recomputed certificate are separate fields. The demonstration rejects a poor point even when the supplied solver flag says success. A valid certified point retains an unsuccessful original flag rather than rewriting history. Numerical acceptance does not establish calibration, source timing, predictive qualification or economic value.

The new local adapter binds a checkpoint to the exact job, source implementation, certificate implementation and interpreter. It writes immutable state bytes and a separate receipt, flushes and reads back those files, and recomputes the mathematical certificate during restoration. A stop after state persistence but before receipt publication has a tested recovery path that publishes the missing receipt without fitting the state again. Corrupt or conflicting files are rejected and preserved rather than silently replaced.

The example is serialized and uses a temporary local directory. It does not provide a multiprocess owner lock, remote durability, an object-store transaction or a general guarantee against filesystem/power failure. Real source authentication and owner-run acceptance remain separate requirements.

```bash
python -m examples.fbs_contracts.certified_resume
python -m unittest examples.fbs_contracts.tests.test_certified_resume -v
```

The first invented attempt commits two states and rejects one. Recovery computes one new state and reuses two. Successful reentry performs zero new solves and reuses all three. The test suite also covers changed inputs, altered environment identity, corrupted bytes, forged/rehashed bad numerical states, missing states, original solver-status retention and interruption between persistence stages. These are public software checks, not additional owner model fits.

## Explain source regressions without weakening the join

The V025 owner assessed sources at 1:38 p.m. PST on November 3 (21:38 UTC), but its consumed FBS capture was from 7:07 p.m. PST on November 1 (November 2, 03:07 UTC). A newer shared collector was NFL-only. The strict consumer correctly refused to treat that collector as FBS evidence, then fell back too far—to the old packaged FBS seed rather than a more recent, already authenticated FBS catalogue.

The prepared correction authenticates prior catalogue bytes, completion clocks, exact FBS selections and receipt counts before choosing the newest known completed FBS fallback. The original raw-response and standalone-receipt verification remains in place. It does not create a paid acquisition grant, claim complete shared-history coverage or turn a later read time into a new capture time.

The stale snapshot contains 63 game-market events. Fifty-five have unique exact-kickoff/ordered-school identity candidates; eight remain quarantined. Six have unresolved official kickoff placeholders and two have explicit kickoff disagreements. The new diagnostic history uses exact game IDs to expose schedule revisions. Ordered-school similarity is diagnostic only; no time-tolerance or guessed alias admits a gap. A name/time candidate still is not independent provider-ID proof or a certified executable quote.

Game-market and player-prop units are separate: 1,835 game-market observations comprise 1,603 mapped and 232 quarantined rows; 18 player-prop observations map separately. The source inventory has 888 FBS-involving games, 622 completed games and 500 completed FBS-versus-FBS games, but full official/latest coverage is unproved.

## Preserve current-season evidence without inventing a live record

The original nine-week replay contains 622 games and 465 correct winner predictions. Winner log loss is 0.513328, Brier score 0.173252, margin MAE 14.600 and total MAE 13.093. These are retrospective frozen-recipe results, not 622 proven pregame issues. The approximately 0.46 result belongs to a different 301-game monitor and is not a matched-cohort improvement claim over 622 games.

The rolling issued panel remains empty because full raw feature-value production and causal admission are incomplete. Upcoming numeric forecasts, executable opportunities, hypothetical settlements and realized return are not invented to fill that gap.

New active provider comparisons are restricted to DraftKings, Kalshi and Polymarket. DraftKings has 162 mapped game-market rows across 54 of 62 observed events in this stale snapshot; none is a certified current T−120/T−60 offer. Qualified Kalshi and Polymarket panels are unavailable in this evidence. US/global Polymarket products remain distinct. Older provider comparisons remain archived history; unavailable observations do not prove that a provider lacks the product.

The public report contains aggregates, generic engineering and invented fixtures. It excludes private rows, raw provider prices, active formulas/weights, cloud identifiers and personal communications. No new license or data redistribution entitlement is asserted.

## Same-game historical DraftKings comparison

The preserved original replay and DraftKings archive are joined to identical game and outcome identities. All 192 winner model values and 199 margin/total model values match the original 622-game replay to numerical tolerance. On the winner subset, the model has log loss 0.604359 and 132 correct selections (68.75%); DraftKings has log loss 0.553191 and 136 correct (70.83%). Of 40 disagreements, the model alone was right 18 times and DraftKings alone 22. Margin RMSE is 17.678192 versus 14.583325; total RMSE is 17.975532 versus 16.469517. Each target retains its exact denominator.

These are independently recomputed archived comparisons, not evidence of actual pregame possession, profitable execution or statistical significance. Cohort commitments and full-precision aggregate values are in the public JSON. Kalshi and Polymarket have no authenticated matched historical panels in this evidence. No fourth provider enters the active comparison.
