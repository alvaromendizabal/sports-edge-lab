# FBS Spread & Totals

[Open the board](index.html) · [Complete public dataset](board.json) · [69-game table](weekly_games.md) · [Games CSV](weekly_games.csv) · [Exact primary-contract baselines CSV](weekly_contract_point_baselines.csv) · [Phone graphic index](graphics/graphics_index.json) · [Earlier FBS evidence](../README.md)

This V118 release/status edition retains the verified frozen V116 forecasts and their November 25 source clocks. The owner ran V117; its verified return finished on **November 26 at 02:21:39.832795 UTC** with a resumable partial failure, **zero new model fits and zero new calibrator fits**. An input-identity guard rejected 588 raw-feature callbacks before fitting. The return separately records **9,932 new scoring-worker callbacks**: 1,008 retained-frontier, 4,462 current-report and 4,462 uncertainty callbacks. Its **31,766 reused scoring events** are not a count of unique tasks. Scoring, checkpoint recovery and preserved earlier work do not become new fits or a successful research run.

**V118 is prepared and awaiting the owner’s launch.** This public update starts no main research run and claims no V118 model result. The retained game rows, contract observations, model identities, original selection rules, annual metrics, source coverage and forecast timestamps are unchanged.

## New spread and total research protocol

The owner explicitly revised the next spread and total campaign: **2024 and 2025 supply training; completed 2026 games supply validation and selection.** The new branch is labeled `2026_EXPOSED_VALIDATION`. It does not replace the original registry or relabel the models displayed below. Previously inspected 2026 outcomes cannot become pristine test evidence; prospective testing for the new models begins only after the actual launch-time cutoff, with each forecast’s issue and source clocks retained.

The prepared campaign registers 1,344 base-fit slots, of which **1,176 are qualified** and **168 remain blocked by absent historical source columns**. It compares seven model families, point and threshold distributions, grouped feature ablations and calibration in a finite resumable queue. A **5,254-column candidate catalog** is available across the feature views; each fitted view reports its actual retained columns, so this count is not a claim that every model trains on every column. It retains full-population comparisons against the incumbent and reports missing inputs and negative findings. Runtime controls admit 4–42 safely available cores with a hard 42-core ceiling, bounded native threads and a USD 200 compute guard; no wall-time limit waives that guard. These are preparation and execution requirements, not completed fits or an achieved spread/total accuracy.

## What is available

The board retains all **895 observed 2026 games**, including 824 completed and 71 future games. Its **November 23–29 Pacific week has 69 games: two completed and 67 upcoming**. Missing market inputs never remove a game. The refreshed forecast snapshot is **November 25, 2026 at 23:30:00.818383 UTC**; the current game census is **23:29:48 UTC**. These are early previews and completed-game reconstructions, with no new original pregame issuance or early-horizon validation claim.

Every game displays the selected predicted winner and probability, a signed home-minus-away expected margin with a named point favorite, and expected combined total. Different objectives have different selected models:

| Public model | Displayed role | Saved validation-selected model |
| --- | --- | --- |
| P06 | Winner accuracy and displayed winner probability | Fixed equal blend of six pre-test sigmoid-calibrated components: linear, ExtraTrees, XGBoost, LightGBM, CatBoost and TensorFlow |
| P02 | Expected margin, selected by absolute error | CatBoost market control |
| P05 | Expected combined total, selected by absolute and squared error | PyTorch market control |

The independent P06 audit authenticated all six original fit receipts and their exact link to the current forecast rows. This establishes the saved calibration method; it does not establish new calibration performance at the current early horizon. The refresh completed 20 frozen-component inference tasks with **zero new model or calibrator fits**. All 6,592 completed-game policy outputs and the full manifest's labels are unchanged from the preceding diagnostic; 193 of 568 upcoming policy outputs changed with fresh inputs. The board exposes only the three selected public roles, while the earlier review preserves all objective leaders.

## Contract terms, primary strikes and missing probabilities

The native Kalshi capture finished at **23:05:33.334126 UTC**. It contains 3,535 observed contracts. **3,271 exact game-and-terms joins cover 68 FBS games**, including 66 upcoming and two completed games. The 264 unmatched observations remain outside game selections. All joined spread/total strike alternatives remain inspectable, including source clocks, exact propositions, observed asks, native record links and settlement-term links.

The registered primary-strike rule uses current two-sided quote midpoint distance to 0.50, then depth, spread and ticker. When no comparable current quote is eligible, it uses the lower median canonical integer boundary and ticker. Predictions and outcomes do not choose the primary. The current board's stale books therefore do not create an executable-price or net-return claim.

**The 66 spread and 66 total point-rule choices are unranked baselines.** They compare P02/P05 point centers with actual contract thresholds; they are not calibrated YES/NO probabilities. Validation-selected integer-distribution fits, monotone contract probabilities and fee-qualified rankings remain pending the owner's research run. Marshall at UL Monroe remains visible with missing authentic native contracts. No unavailable value is replaced with an invented line, price or probability.

The observed terms use strictly greater-than thresholds for the full game, including overtime. Equality settles NO under that wording. Exceptional cancellation, postponement and fair-price settlement are retained separately; tie or push is never an offered trading side. The source settlement ledger contains **80 NO and 23 YES**, which are contract resolution counts, not model accuracy. Historical pregame possession is not inferred from a current terms capture.

## Source coverage stays separate

The distinct **23:30:00 UTC** The Odds API snapshot contains 11,936 normalized references. The board exposes 339 target cells across 113 requested bookmaker labels, of which 83 have qualified observations. Raw provider bodies, licensed arrays and credentials are excluded.

| Source product via The Odds API | Weekly winner games / 69 | Weekly margin games / 69 | Weekly total games / 69 |
| --- | ---: | ---: | ---: |
| DraftKings | 67 | 67 | 67 |
| Kalshi | 66 | 62 | 66 |
| Polymarket | 65 | 65 | 65 |
| Polymarket US | 0 | 0 | 0 |

These current references are separate from the authentic native Kalshi contract capture. They establish neither historical fixed-horizon benchmark performance nor an executable continuous feed. All-source gaps and the full 895-game season denominator remain visible in the board's evidence tab.

## Selection, denominators and the 70% research target

The **displayed inherited models** use 2024 and 2025 selection, with 50/50 annual weights as the primary rule. The other four ratios reuse the same predictions. No 2026 outcome selected these displayed model identities, strike rule, blend, calibration or feature choices. Their 2026 results remain previously exposed test reporting. The separate pending V118 campaign follows the owner’s revised 2026-selection protocol described above.

| Selected role / metric | 2024 retained validation, n=919 | 2025 validation, n=934 | Current completed 2026 diagnostic, n=824 |
| --- | ---: | ---: | ---: |
| P06 winner accuracy | 73.4494% | 76.9807% | 74.3932%, 613/824 |
| P02 margin MAE | 12.59855 | 12.96061 | 13.02670 |
| P05 total MAE | 12.56040 | 12.43270 | 12.71514 |
| P05 total RMSE | 15.96130 | 15.46190 | 15.89489 |

The fresh census contains **920 observed fixtures / 919 completed games in 2024**, and **934 observed / 934 completed games in 2025**. The retained 2024 scorecards cover 919 completed games; the additional fixture is Liberty at App State on September 28, officially canceled after Hurricane Helene and not rescheduled. The [separate status ledger](schedule_status_ledger.json) cites [App State Athletics](https://appstatesports.com/news/2024/9/27/app-state-liberty-football-game-canceled.aspx) and [Liberty Athletics](https://libertyflames.com/news/2024/9/27/football-liberty-vs-appalachian-state-game-canceled), retains the immutable source manifest, and excludes that canceled fixture from completed-game grading. This denominator difference is not a missing completed-game prediction. The earlier 822-game 2026 cards remain separate from the updated 824-game diagnostic. Full-population rescores and contract comparisons belong to the pending owner research campaign.

The fixed [descriptive uncertainty diagnostic](uncertainty.json) resamples whole ISO weeks: 14 weeks, 2,000 draws and one preregistered seed (117). P06's 95% winner-accuracy interval is **68.66%–79.38%**, which crosses 70%. P02 margin MAE has a **11.932–14.200** interval; P05 total MAE has a **11.886–13.695** interval. These summarize observed-week variability in the exposed 824-game reconstruction; they do not quantify unobserved-season, source-reconstruction, selection or regime uncertainty. No fit, calibration or selection was changed.

The owner's 70% target is a spread/total research target. A 74.39% straight-up winner reconstruction does not demonstrate 70% contract accuracy. No contract-probability performance or fee-adjusted return is asserted by this snapshot.

## Phone pages and publication status

**59 deterministic 1290 × 2796 PNGs** cover the complete weekly display and current research status: one release-status page, 14 all-game pages, 22 spread point-baseline pages and 22 total point-baseline pages. They preserve exact propositions, selected model aliases, clocks and qualifications. The new status page makes the verified V117 zero-fit return and pending V118 campaign explicit. The PNG index binds every page to the complete public snapshot and records its hash, dimensions and checked text bounds.

GitHub source, hosted deployment and scientific production promotion are distinct. The last verified FBS Site remains **version 48 from November 16**, rechecked on November 26. This V118 update has not been deployed to that host. This public tree is prepared for review and static export; it does not establish a new hosted release or scientific promotion. The full prior FBS tree and all other sports remain preserved.

The presentation can be reproduced without a source subscription or model execution:

```sh
python -m pip install -r examples/fbs_contracts/spread_totals/requirements.txt
python examples/fbs_contracts/spread_totals/render_phone_cards.py --data docs/fbs/spread-totals/board.json --output docs/fbs/spread-totals/graphics --attach-index
python examples/fbs_contracts/spread_totals/build_board.py --data docs/fbs/spread-totals/board.json --check
python examples/fbs_contracts/spread_totals/export_week.py --data docs/fbs/spread-totals/board.json --output docs/fbs/spread-totals --check
python tests/test_fbs_spread_totals_public.py
```

The main owner executable, private source evidence, fitted states and exact active feature recipes remain outside this public repository.
