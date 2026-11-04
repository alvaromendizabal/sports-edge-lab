# Reading forecast status and market lines

[NFL overview](README.md) · [All-game dashboard](review.html#latest-coverage) · [Model card](CURRENT_MODEL_CARD.md)

## Three separate questions

| Question | What this snapshot establishes |
|---|---|
| What does the model predict? | The displayed winner probability, home margin and total, with the original issue and input clocks. |
| Has a particular bet been assessed? | **Betting assessment pending** for the early cards. A price, payoff, fees, liquidity and uncertainty comparison has not established an actionable recommendation. |
| Did anyone actually place a wager? | **Not tracked in this dashboard.** A zero model allocation or research status is not a personal transaction record. |

The current interface replaces the blanket **NO BET** badge with **Early projection · betting assessment pending**. A stream with no forecast says **Forecast unavailable · betting assessment unavailable**. This corrects the presentation; it does not approve a wager or establish that every offered bet has negative expected value. Earlier audit records and their `bet_decision` and stake values remain unchanged.

## Jacksonville at Baltimore: separate injury context

Baltimore's [November 3 team report](https://www.baltimoreravens.com/news/joe-fagnano-ravens-quarterbacks-practice-report-tyler-huntley) says Joe Fagnano will start against Jacksonville on Thursday. The [November 1 report](https://www.baltimoreravens.com/news/lamar-jackson-thumb-injured-ravens-bills-2026) described Lamar Jackson's right-thumb injury, planned surgery and intended injured-reserve move. Planned actions are not represented here as completed transactions.

The [official Week 9 practice report](https://www.baltimoreravens.com/team/injury-report/week/REG-9) is a separate changing source. Article publication dates above do not supply an invented precise UTC publication time. The source context is dated November 3, 2026; it is not proof of a continuous live feed.

**Current injury/QB information is not verified in the displayed model forecasts.** A team-news update does not demonstrate that an earlier model input contained it. The preserved forecast values and actual issue times remain intact. This update neither retrains a model nor manually adjusts its predicted points.

## A market line is not a model forecast

The saved November 3 DraftKings reference for Jacksonville–Baltimore is Jacksonville **−10**, equivalent to Baltimore **+10**, with a **40.5** total. Its provider quote time is **22:55:43 UTC**. The selected early model output displayed in the current view has Jacksonville by **4.0** and a total of **45.7**, issued at **22:58:32 UTC**. These are saved observations, not assertions about the current available price.

That is a six-point difference between the projected margin and the quoted handicap, and a 5.2-point difference between the total projection and quoted total. The two sources agree on the favored winner but differ on the margin. A sportsbook handicap is a contract threshold, not necessarily the provider's expected final margin. The gap alone does not establish a model probability of covering, a fee-adjusted advantage or an executable bet.

Upcoming quotes, final pregame references, model information time and source acquisition time stay separate. Later information may be displayed for comparison; it cannot be inserted into an earlier model forecast or used to backdate a prediction.
