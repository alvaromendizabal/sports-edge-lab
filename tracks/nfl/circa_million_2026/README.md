# 2026 NFL models vs. Circa Million VIII

**Sports Edge Lab · Complete Weeks 1–9 report · Nov. 8, 2026 (Pacific time)**

> **Important:** This is research, not an entered Circa contest card. Weeks 1–8 are retrospectively reconstructed after the games, with unverified historical source-possession clocks. Week 9 forecasts were actually saved before Sunday's kickoffs, but after Circa's Saturday 4 p.m. contest cutoff. Thursday's Week 9 game has no N056 original issue. No backdated live-pick claims are made.

**You're already viewing the full report on GitHub — no download needed.** For optional interactive filtering: [open the HTML in a third-party preview](https://raw.githack.com/alvaromendizabal/sports-edge-lab/main/tracks/nfl/circa_million_2026/index.html) (the preview service may show a safety notice first) · [view HTML source](./index.html) · [official Circa Million](https://www.circasports.com/circa-million).

The native GitHub tables below show every result **without downloading anything**, even if the interactive preview service is unavailable.

## Circa-first headline · best available five-pick results

- **Circa's actual scoring objective:** Four of the 23 archived margin-model configurations are **tied for the best reconstructed five-pick result: 23.0 of 40 points**, each at **21 wins, 15 losses, 4 pushes** across Weeks 1–8. They are CatBoost · football support control, ExtraTrees · combined personnel interaction, ExtraTrees · football support control, and the OOF convex blend. There is **no unique first-place model** on this metric.
- **Next distinct Circa scores:** unchanged frozen201 mean at **22.5**; LightGBM · football support control and OOF stack tied at **22.0**. These are score tiers, not proof of predeadline predictive superiority.
- **Separate all-game evaluation:** TensorFlow MLP · football support control leads on spread sides at **67–47–6** (58.8% excluding pushes), but its own five-pick cards scored **19.0**, below the Circa leaders. The original research baseline had 73/119 outright winners (61.3%). All 121 historical games are listed; 120 have reconstructed margin forecasts.
- **Week 9, genuine pregame outputs:** 10/10 outright winners; against Circa: **6–4–0** (60.0% excluding pushes), with 11/15 games final and four not yet graded. These outputs were **after the Saturday contest deadline**.
- A hypothetical five-largest-edge shortlist is shown every week. It is a post-hoc diagnostic, **not a contest submission**. Circa itself scores only five selected sides against fixed spreads (win = 1, push = 0.5, loss = 0).
- Circa Million has **no over/under component**. This report scores projected combined points against final combined points; independently documented market totals appear only for eight Week 9 games.

## Best-performing Circa cards first · ATS accuracy second

**All 23 available reconstructed margin-model families were evaluated against the same 120 Circa-lined games in Weeks 1–8.** The rankings below deliberately use this season's known results and are therefore **post-hoc descriptions, not models known to be best before those games**. Week 9 original saved forecasts remain a separate evidence lane.

**Best in Circa's five-picks-per-week format:** **four model configurations tied at 23.0 points**, including, but not restricted to, the old CatBoost research baseline. **Best across all spreads:** TensorFlow MLP · football support control (67–47–6; 58.8% excluding pushes), but it scored only **19.0 five-pick points**. The all-game ATS winner and highest-scoring Circa cards are **different**. These cards choose the five biggest absolute projected spread edges *for each model*, without using outcomes to choose those five, but model ranking across the season is performed after outcomes are known.

**Official standings comparison:** [Circa's after-Week-8 leaderboard](https://www.circasports.com/wp-content/uploads/2026/11/Circa-Sports-Million-VIII-Full-Season-Standings-After-Week-8.pdf) shows **1054th place (tie)** at **23.0 points** and the leaders at **30.5**. A 23-point reconstructed card would have matched that score **only hypothetically**; these were not contest entries or authenticated pre-deadline selections.

### Ranking A · five-pick Circa-style points (after-the-fact)

| Card place* | Reconstructed margin model | Card W–L–P | Points / 40 | Full-slate ATS rate |
|---:|---|---:|---:|---:|
| 1T | catboost · football support control ★ research baseline | 21–15–4 | 23.0 | 51.8% |
| 1T | extratrees · combined personnel interaction | 21–15–4 | 23.0 | 49.1% |
| 1T | extratrees · football support control | 21–15–4 | 23.0 | 49.1% |
| 1T | oof convex blend | 21–15–4 | 23.0 | 49.1% |
| 5 | unchanged frozen201 mean | 21–16–3 | 22.5 | 46.5% |
| 6T | lightgbm · football support control | 20–16–4 | 22.0 | 48.2% |
| 6T | oof stack | 20–16–4 | 22.0 | 48.2% |
| 8T | xgboost · combined personnel interaction | 20–17–3 | 21.5 | 51.8% |
| 8T | histgb · combined personnel interaction | 20–17–3 | 21.5 | 47.4% |
| 10 | xgboost · football support control | 20–18–2 | 21.0 | 50.0% |
| 11 | histgb · football support control | 19–18–3 | 20.5 | 49.1% |
| 12T | linear · combined personnel interaction | 18–18–4 | 20.0 | 50.0% |
| 12T | ridge · combined personnel interaction | 18–18–4 | 20.0 | 50.0% |
| 12T | lightgbm · combined personnel interaction | 18–18–4 | 20.0 | 49.1% |
| 12T | oof calibration | 18–18–4 | 20.0 | 49.1% |
| 12T | fixed equal blend | 18–18–4 | 20.0 | 47.4% |
| 17T | torch mlp · combined personnel interaction | 19–20–1 | 19.5 | 51.8% |
| 17T | linear · football support control | 18–19–3 | 19.5 | 50.0% |
| 17T | ridge · football support control | 18–19–3 | 19.5 | 50.0% |
| 20T | tensorflow mlp · football support control | 18–20–2 | 19.0 | 58.8% |
| 20T | torch mlp · football support control | 18–20–2 | 19.0 | 55.3% |
| 20T | catboost · combined personnel interaction | 17–19–4 | 19.0 | 50.9% |
| 23 | tensorflow mlp · combined personnel interaction | 16–23–1 | 16.5 | 51.8% |

### Ranking B · every-game ATS accuracy (after-the-fact)

| ATS place* | Reconstructed margin model | ATS W–L–P | Rate excluding pushes | Five-pick card | Margin MAE |
|---:|---|---:|---:|---:|---:|
| 1 | tensorflow mlp · football support control | 67–47–6 | 58.8% | 19.0 / 40 | 10.03 |
| 2 | torch mlp · football support control | 63–51–6 | 55.3% | 19.0 / 40 | 10.04 |
| 3T | xgboost · combined personnel interaction | 59–55–6 | 51.8% | 21.5 / 40 | 9.84 |
| 3T | catboost · football support control ★ research baseline | 59–55–6 | 51.8% | 23.0 / 40 | 9.95 |
| 3T | torch mlp · combined personnel interaction | 59–55–6 | 51.8% | 19.5 / 40 | 10.21 |
| 3T | tensorflow mlp · combined personnel interaction | 59–55–6 | 51.8% | 16.5 / 40 | 10.29 |
| 7 | catboost · combined personnel interaction | 58–56–6 | 50.9% | 19.0 / 40 | 9.90 |
| 8T | ridge · football support control | 57–57–6 | 50.0% | 19.5 / 40 | 9.95 |
| 8T | linear · football support control | 57–57–6 | 50.0% | 19.5 / 40 | 9.95 |
| 8T | ridge · combined personnel interaction | 57–57–6 | 50.0% | 20.0 / 40 | 9.99 |
| 8T | xgboost · football support control | 57–57–6 | 50.0% | 21.0 / 40 | 10.00 |
| 8T | linear · combined personnel interaction | 57–57–6 | 50.0% | 20.0 / 40 | 10.00 |
| 13T | oof convex blend | 56–58–6 | 49.1% | 23.0 / 40 | 9.92 |
| 13T | extratrees · combined personnel interaction | 56–58–6 | 49.1% | 23.0 / 40 | 9.92 |
| 13T | oof calibration | 56–58–6 | 49.1% | 20.0 / 40 | 9.92 |
| 13T | extratrees · football support control | 56–58–6 | 49.1% | 23.0 / 40 | 9.92 |
| 13T | lightgbm · combined personnel interaction | 56–58–6 | 49.1% | 20.0 / 40 | 9.98 |
| 13T | histgb · football support control | 56–58–6 | 49.1% | 20.5 / 40 | 10.06 |
| 19T | oof stack | 55–59–6 | 48.2% | 22.0 / 40 | 10.14 |
| 19T | lightgbm · football support control | 55–59–6 | 48.2% | 22.0 / 40 | 10.14 |
| 21T | fixed equal blend | 54–60–6 | 47.4% | 20.0 / 40 | 9.92 |
| 21T | histgb · combined personnel interaction | 54–60–6 | 47.4% | 21.5 / 40 | 10.00 |
| 23 | unchanged frozen201 mean | 53–61–6 | 46.5% | 22.5 / 40 | 10.12 |

*Ranks use competition-style ties (four configurations can all be #1). Rankings cannot be used as an honest 'we picked the best in advance' claim. The historical source-publication/as-of archive is not verified.*

### Weekly five-pick comparisons · all four Circa leaders plus the ATS leader

| Week | CatBoost (card #1T) | ExtraTrees combined (card #1T) | ExtraTrees support (card #1T) | OOF convex blend (card #1T) | TensorFlow MLP (ATS #1) |
|---:|---:|---:|---:|---:|---:|
| [1](#week-1) | 2–2–1 (2.5 pts) | 1–3–1 (1.5 pts) | 2–2–1 (2.5 pts) | 2–2–1 (2.5 pts) | 1–3–1 (1.5 pts) |
| [2](#week-2) | 2–3–0 (2.0 pts) | 4–1–0 (4.0 pts) | 3–2–0 (3.0 pts) | 3–2–0 (3.0 pts) | 2–3–0 (2.0 pts) |
| [3](#week-3) | 4–1–0 (4.0 pts) | 4–1–0 (4.0 pts) | 4–1–0 (4.0 pts) | 4–1–0 (4.0 pts) | 3–2–0 (3.0 pts) |
| [4](#week-4) | 4–0–1 (4.5 pts) | 4–0–1 (4.5 pts) | 4–0–1 (4.5 pts) | 4–0–1 (4.5 pts) | 4–1–0 (4.0 pts) |
| [5](#week-5) | 3–1–1 (3.5 pts) | 3–1–1 (3.5 pts) | 3–1–1 (3.5 pts) | 3–1–1 (3.5 pts) | 3–2–0 (3.0 pts) |
| [6](#week-6) | 1–3–1 (1.5 pts) | 0–4–1 (0.5 pts) | 0–4–1 (0.5 pts) | 0–4–1 (0.5 pts) | 1–3–1 (1.5 pts) |
| [7](#week-7) | 1–4–0 (1.0 pts) | 2–3–0 (2.0 pts) | 2–3–0 (2.0 pts) | 2–3–0 (2.0 pts) | 1–4–0 (1.0 pts) |
| [8](#week-8) | 4–1–0 (4.0 pts) | 3–2–0 (3.0 pts) | 3–2–0 (3.0 pts) | 3–2–0 (3.0 pts) | 3–2–0 (3.0 pts) |

**Interactive HTML:** choose any of the 23 historical margin models to inspect its **individual game picks, edge sizes, grades, and five-pick cards**. On GitHub, the full native tables remain readable below without downloading or opening HTML source. The HTML preview is optional.

## Jump to a week

[Week 1](#week-1) · [Week 2](#week-2) · [Week 3](#week-3) · [Week 4](#week-4) · [Week 5](#week-5) · [Week 6](#week-6) · [Week 7](#week-7) · [Week 8](#week-8) · [Week 9](#week-9)

## Existing research baseline season scorecard · CatBoost margin

| Week | Evidence lane | Forecast coverage | ATS W–L–P | ATS rate* | Hypothetical five (points) | Winner calls | Margin MAE | Total MAE | Brier | Log loss |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [1](#week-1) | Reconstructed | 16/16 | 6–9–1 | 40.0% | 2–2–1 (2.5 pts; 5/5 scored) | 10/16 | 12.4 | 12.8 | 0.241 | 0.675 |
| [2](#week-2) | Reconstructed | 16/16 | 9–7–0 | 56.2% | 2–3–0 (2.0 pts; 5/5 scored) | 9/16 | 12.3 | 11.3 | 0.238 | 0.669 |
| [3](#week-3) | Reconstructed | 16/16 | 11–4–1 | 73.3% | 4–1–0 (4.0 pts; 5/5 scored) | 10/16 | 8.3 | 11.3 | 0.214 | 0.611 |
| [4](#week-4) | Reconstructed | 16/16 | 10–5–1 | 66.7% | 4–0–1 (4.5 pts; 5/5 scored) | 10/16 | 6.8 | 11.3 | 0.203 | 0.587 |
| [5](#week-5) | Reconstructed | 15/15 | 7–7–1 | 50.0% | 3–1–1 (3.5 pts; 5/5 scored) | 9/14 | 10.2 | 11.4 | 0.230 | 0.651 |
| [6](#week-6) | Reconstructed | 14/14 | 3–10–1 | 23.1% | 1–3–1 (1.5 pts; 5/5 scored) | 7/14 | 8.8 | 10.9 | 0.296 | 0.800 |
| [7](#week-7) | Reconstructed | 14/14 | 5–8–1 | 38.5% | 1–4–0 (1.0 pts; 5/5 scored) | 7/14 | 11.4 | 10.0 | 0.261 | 0.720 |
| [8](#week-8) | Reconstructed | 13/14 | 8–5–0 | 61.5% | 4–1–0 (4.0 pts; 5/5 scored) | 11/13 | 9.4 | 11.8 | 0.172 | 0.530 |
| [9](#week-9) | Issued; late for contest | 14/15 | 6–4–0 | 60.0% | 3–1–0 (3.0 pts; 4/5 scored) | 10/10 | 5.9 | 8.6 | 0.119 | 0.416 |

*ATS rate excludes pushes. Tied games are not counted for outright winner/probability grades. No pending game is counted as a result.

## Week 1

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 16/16 models available · 16/16 final games · **6–9–1 ATS** · **10/16 winner calls**

[Official Week 1 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-1.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Week-1-Selections.pdf)

**Research baseline top five by projected spread edge (2.5 Circa-style points from 5/5 graded):** #1 DEN +3 (5.6 pts, LOSS) · #2 MIA +3.5 (5.5 pts, LOSS) · #3 SEA -3 (5.3 pts, PUSH) · #4 NYG +3 (3.7 pts, WIN) · #5 JAX -8.5 (2.8 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 2.5 points:** #1 **DEN +3** (LOSS; edge 5.6) · #2 **MIA +3.5** (LOSS; edge 5.5) · #3 **SEA -3** (PUSH; edge 5.3) · #4 **NYG +3** (WIN; edge 3.7) · #5 **JAX -8.5** (WIN; edge 2.8)
- **Circa card #1T: extratrees · combined personnel interaction · 1.5 points:** #1 **DEN +3** (LOSS; edge 5.7) · #2 **NYG +3** (WIN; edge 5.0) · #3 **MIA +3.5** (LOSS; edge 5.0) · #4 **SEA -3** (PUSH; edge 4.5) · #5 **TEN -1.5** (LOSS; edge 2.8)
- **Circa card #1T: extratrees · football support control · 2.5 points:** #1 **MIA +3.5** (LOSS; edge 5.6) · #2 **NYG +3** (WIN; edge 5.2) · #3 **DEN +3** (LOSS; edge 4.9) · #4 **SEA -3** (PUSH; edge 4.2) · #5 **MIN -1.5** (WIN; edge 3.4)
- **Circa card #1T: oof convex blend · 2.5 points:** #1 **DEN +3** (LOSS; edge 5.4) · #2 **MIA +3.5** (LOSS; edge 5.3) · #3 **NYG +3** (WIN; edge 4.8) · #4 **SEA -3** (PUSH; edge 4.6) · #5 **JAX -8.5** (WIN; edge 2.7)
- **Full-slate ATS #1: tensorflow mlp · football support control · 1.5 points:** #1 **MIA +3.5** (LOSS; edge 13.1) · #2 **DEN +3** (LOSS; edge 7.5) · #3 **ATL +3.5** (LOSS; edge 7.1) · #4 **BUF -0.5** (WIN; edge 6.8) · #5 **SEA -3** (PUSH; edge 6.6)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| NE @ SEA ★ | 10–13 | NE +3 / SEA -3 | **SEA -3** (PUSH; edge 5.3) | **SEA -3** (PUSH; edge 4.5) | **SEA -3** (PUSH; edge 4.2) | **SEA -3** (PUSH; edge 4.6) | **SEA -3** (PUSH; edge 6.6) | SEA (74.0%) | +8.29581 / +3 | 42.0 / 23 |
| SF @ LA | 27–7 | SF +4 / LA -4 | **LA -4** (LOSS; edge 1.7) | **LA -4** (LOSS; edge 2.0) | **LA -4** (LOSS; edge 2.0) | **LA -4** (LOSS; edge 1.8) | **SF +4** (WIN; edge 2.9) | LA (71.7%) | +5.68185 / -20 | 47.0 / 34 |
| ATL @ PIT | 13–20 | ATL +3.5 / PIT -3.5 | **ATL +3.5** (LOSS; edge 0.8) | **ATL +3.5** (LOSS; edge 1.9) | **ATL +3.5** (LOSS; edge 1.7) | **ATL +3.5** (LOSS; edge 1.6) | **ATL +3.5** (LOSS; edge 7.1) | PIT (55.1%) | +2.68649 / +7 | 43.8 / 33 |
| BAL @ IND | 41–23 | BAL -3.5 / IND +3.5 | **BAL -3.5** (WIN; edge 0.6) | **IND +3.5** (LOSS; edge 1.7) | **IND +3.5** (LOSS; edge 1.3) | **IND +3.5** (LOSS; edge 1.3) | **BAL -3.5** (WIN; edge 2.5) | BAL (58.2%) | -4.13404 / -18 | 44.4 / 64 |
| BUF @ HOU | 36–31 | BUF -0.5 / HOU +0.5 | **HOU +0.5** (LOSS; edge 1.1) | **HOU +0.5** (LOSS; edge 1.3) | **HOU +0.5** (LOSS; edge 1.6) | **HOU +0.5** (LOSS; edge 1.0) | **BUF -0.5** (WIN; edge 6.8) | HOU (53.9%) | +0.551275 / -5 | 45.8 / 67 |
| CHI @ CAR | 59–37 | CHI -3 / CAR +3 | **CHI -3** (WIN; edge 1.0) | **CHI -3** (WIN; edge 0.2) | **CAR +3** (LOSS; edge 0.3) | **CAR +3** (LOSS; edge 0.0) | **CHI -3** (WIN; edge 2.6) | CHI (60.8%) | -3.98997 / -22 | 43.8 / 96 |
| CLE @ JAX ★ | 10–34 | CLE +8.5 / JAX -8.5 | **JAX -8.5** (WIN; edge 2.8) | **JAX -8.5** (WIN; edge 2.7) | **JAX -8.5** (WIN; edge 3.2) | **JAX -8.5** (WIN; edge 2.7) | **CLE +8.5** (LOSS; edge 4.7) | JAX (81.9%) | +11.2884 / +24 | 42.9 / 44 |
| NO @ DET | 30–31 | NO +7 / DET -7 | **NO +7** (WIN; edge 0.3) | **NO +7** (WIN; edge 2.6) | **NO +7** (WIN; edge 3.3) | **NO +7** (WIN; edge 2.4) | **NO +7** (WIN; edge 5.9) | DET (64.7%) | +6.73725 / +1 | 46.0 / 61 |
| NYJ @ TEN | 23–10 | NYJ +1.5 / TEN -1.5 | **TEN -1.5** (LOSS; edge 2.3) | **TEN -1.5** (LOSS; edge 2.8) | **TEN -1.5** (LOSS; edge 2.6) | **TEN -1.5** (LOSS; edge 2.6) | **NYJ +1.5** (WIN; edge 0.5) | TEN (68.8%) | +3.80236 / -13 | 43.2 / 33 |
| TB @ CIN | 27–33 | TB +3.5 / CIN -3.5 | **TB +3.5** (LOSS; edge 1.7) | **TB +3.5** (LOSS; edge 2.4) | **TB +3.5** (LOSS; edge 2.1) | **TB +3.5** (LOSS; edge 2.2) | **TB +3.5** (LOSS; edge 5.0) | CIN (57.1%) | +1.83536 / +6 | 45.9 / 60 |
| ARI @ LAC | 26–14 | ARI +8.5 / LAC -8.5 | **LAC -8.5** (LOSS; edge 0.0) | **ARI +8.5** (WIN; edge 0.8) | **ARI +8.5** (WIN; edge 0.3) | **ARI +8.5** (WIN; edge 0.8) | **ARI +8.5** (WIN; edge 6.3) | LAC (71.4%) | +8.53953 / -12 | 41.7 / 40 |
| GB @ MIN | 22–39 | GB +1.5 / MIN -1.5 | **MIN -1.5** (WIN; edge 2.0) | **MIN -1.5** (WIN; edge 2.7) | **MIN -1.5** (WIN; edge 3.4) | **MIN -1.5** (WIN; edge 2.5) | **MIN -1.5** (WIN; edge 1.6) | MIN (59.1%) | +3.48435 / +17 | 39.7 / 61 |
| MIA @ LV ★ | 13–27 | MIA +3.5 / LV -3.5 | **MIA +3.5** (LOSS; edge 5.5) | **MIA +3.5** (LOSS; edge 5.0) | **MIA +3.5** (LOSS; edge 5.6) | **MIA +3.5** (LOSS; edge 5.3) | **MIA +3.5** (LOSS; edge 13.1) | MIA (58.6%) | -2.04944 / +14 | 40.6 / 40 |
| WAS @ PHI | 22–24 | WAS +4.5 / PHI -4.5 | **PHI -4.5** (LOSS; edge 2.4) | **PHI -4.5** (LOSS; edge 1.3) | **WAS +4.5** (WIN; edge 0.0) | **PHI -4.5** (LOSS; edge 1.4) | **WAS +4.5** (WIN; edge 4.8) | PHI (67.5%) | +6.87754 / +2 | 43.3 / 46 |
| DAL @ NYG ★ | 20–28 | DAL -3 / NYG +3 | **NYG +3** (WIN; edge 3.7) | **NYG +3** (WIN; edge 5.0) | **NYG +3** (WIN; edge 5.2) | **NYG +3** (WIN; edge 4.8) | **NYG +3** (WIN; edge 0.5) | NYG (54.0%) | +0.652095 / +8 | 45.7 / 48 |
| DEN @ KC ★ | 10–31 | DEN +3 / KC -3 | **DEN +3** (LOSS; edge 5.6) | **DEN +3** (LOSS; edge 5.7) | **DEN +3** (LOSS; edge 4.9) | **DEN +3** (LOSS; edge 5.4) | **DEN +3** (LOSS; edge 7.5) | DEN (55.2%) | -2.58988 / +21 | 40.6 / 41 |

## Week 2

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 16/16 models available · 16/16 final games · **9–7–0 ATS** · **9/16 winner calls**

[Official Week 2 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-2.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Week-2-Selections.pdf)

**Research baseline top five by projected spread edge (2.0 Circa-style points from 5/5 graded):** #1 ATL +2.5 (7.1 pts, LOSS) · #2 JAX +2.5 (4.5 pts, LOSS) · #3 TEN +7 (3.7 pts, WIN) · #4 MIN +4.5 (3.1 pts, WIN) · #5 WAS +4 (3.1 pts, LOSS)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 2.0 points:** #1 **ATL +2.5** (LOSS; edge 7.1) · #2 **JAX +2.5** (LOSS; edge 4.5) · #3 **TEN +7** (WIN; edge 3.7) · #4 **MIN +4.5** (WIN; edge 3.1) · #5 **WAS +4** (LOSS; edge 3.1)
- **Circa card #1T: extratrees · combined personnel interaction · 4.0 points:** #1 **ATL +2.5** (LOSS; edge 6.7) · #2 **CLE +8.5** (WIN; edge 5.4) · #3 **LV +6.5** (WIN; edge 4.2) · #4 **TEN +7** (WIN; edge 4.1) · #5 **MIN +4.5** (WIN; edge 3.9)
- **Circa card #1T: extratrees · football support control · 3.0 points:** #1 **ATL +2.5** (LOSS; edge 7.9) · #2 **CLE +8.5** (WIN; edge 5.0) · #3 **NYG +7** (LOSS; edge 4.5) · #4 **LV +6.5** (WIN; edge 4.4) · #5 **MIN +4.5** (WIN; edge 4.3)
- **Circa card #1T: oof convex blend · 3.0 points:** #1 **ATL +2.5** (LOSS; edge 7.0) · #2 **CLE +8.5** (WIN; edge 4.7) · #3 **TEN +7** (WIN; edge 4.1) · #4 **LV +6.5** (WIN; edge 4.0) · #5 **NYG +7** (LOSS; edge 3.6)
- **Full-slate ATS #1: tensorflow mlp · football support control · 2.0 points:** #1 **ATL +2.5** (LOSS; edge 12.7) · #2 **JAX +2.5** (LOSS; edge 11.0) · #3 **NYJ +3.5** (WIN; edge 8.3) · #4 **SEA -4** (WIN; edge 4.9) · #5 **KC -6.5** (LOSS; edge 4.0)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| DET @ BUF | 31–41 | DET +5.5 / BUF -5.5 | **BUF -5.5** (WIN; edge 0.2) | **DET +5.5** (LOSS; edge 0.6) | **DET +5.5** (LOSS; edge 0.2) | **DET +5.5** (LOSS; edge 0.6) | **BUF -5.5** (WIN; edge 1.9) | BUF (70.5%) | +5.66843 / +10 | 47.6 / 72 |
| CAR @ ATL ★ | 34–3 | CAR -2.5 / ATL +2.5 | **ATL +2.5** (LOSS; edge 7.1) | **ATL +2.5** (LOSS; edge 6.7) | **ATL +2.5** (LOSS; edge 7.9) | **ATL +2.5** (LOSS; edge 7.0) | **ATL +2.5** (LOSS; edge 12.7) | ATL (65.5%) | +4.62927 / -31 | 44.3 / 37 |
| CIN @ HOU | 20–6 | CIN +2.5 / HOU -2.5 | **HOU -2.5** (LOSS; edge 0.7) | **HOU -2.5** (LOSS; edge 1.6) | **CIN +2.5** (WIN; edge 0.1) | **HOU -2.5** (LOSS; edge 1.3) | **CIN +2.5** (WIN; edge 3.7) | HOU (64.9%) | +3.23551 / -14 | 47.4 / 26 |
| CLE @ TB | 23–19 | CLE +8.5 / TB -8.5 | **CLE +8.5** (WIN; edge 2.0) | **CLE +8.5** (WIN; edge 5.4) | **CLE +8.5** (WIN; edge 5.0) | **CLE +8.5** (WIN; edge 4.7) | **CLE +8.5** (WIN; edge 1.2) | TB (61.2%) | +6.50812 / -4 | 41.6 / 42 |
| GB @ NYJ | 20–17 | GB -3.5 / NYJ +3.5 | **NYJ +3.5** (WIN; edge 0.0) | **GB -3.5** (LOSS; edge 0.3) | **GB -3.5** (LOSS; edge 1.2) | **GB -3.5** (LOSS; edge 0.2) | **NYJ +3.5** (WIN; edge 8.3) | GB (59.5%) | -3.46781 / -3 | 42.5 / 37 |
| MIN @ CHI ★ | 9–3 | MIN +4.5 / CHI -4.5 | **MIN +4.5** (WIN; edge 3.1) | **MIN +4.5** (WIN; edge 3.9) | **MIN +4.5** (WIN; edge 4.3) | **MIN +4.5** (WIN; edge 3.5) | **MIN +4.5** (WIN; edge 1.3) | CHI (51.2%) | +1.36764 / -6 | 45.0 / 12 |
| NO @ BAL | 24–17 | NO +8.5 / BAL -8.5 | **NO +8.5** (WIN; edge 0.3) | **NO +8.5** (WIN; edge 2.2) | **NO +8.5** (WIN; edge 2.0) | **NO +8.5** (WIN; edge 1.8) | **BAL -8.5** (LOSS; edge 0.3) | BAL (71.4%) | +8.18159 / -7 | 46.2 / 41 |
| PHI @ TEN ★ | 24–20 | PHI -7 / TEN +7 | **TEN +7** (WIN; edge 3.7) | **TEN +7** (WIN; edge 4.1) | **TEN +7** (WIN; edge 3.8) | **TEN +7** (WIN; edge 4.1) | **TEN +7** (WIN; edge 0.7) | PHI (57.9%) | -3.28238 / -4 | 41.4 / 44 |
| PIT @ NE | 3–20 | PIT +5.5 / NE -5.5 | **PIT +5.5** (LOSS; edge 1.0) | **NE -5.5** (WIN; edge 0.1) | **PIT +5.5** (LOSS; edge 0.9) | **NE -5.5** (WIN; edge 0.1) | **NE -5.5** (WIN; edge 1.9) | NE (65.9%) | +4.52586 / +17 | 41.7 / 23 |
| JAX @ DEN ★ | 13–20 | JAX +2.5 / DEN -2.5 | **JAX +2.5** (LOSS; edge 4.5) | **JAX +2.5** (LOSS; edge 3.2) | **JAX +2.5** (LOSS; edge 3.5) | **JAX +2.5** (LOSS; edge 3.4) | **JAX +2.5** (LOSS; edge 11.0) | JAX (51.7%) | -1.98223 / +7 | 44.6 / 33 |
| LV @ LAC | 26–14 | LV +6.5 / LAC -6.5 | **LV +6.5** (WIN; edge 2.1) | **LV +6.5** (WIN; edge 4.2) | **LV +6.5** (WIN; edge 4.4) | **LV +6.5** (WIN; edge 4.0) | **LV +6.5** (WIN; edge 0.7) | LAC (59.2%) | +4.3606 / -12 | 40.1 / 40 |
| MIA @ SF | 13–35 | MIA +13 / SF -13 | **MIA +13** (LOSS; edge 2.5) | **MIA +13** (LOSS; edge 1.7) | **MIA +13** (LOSS; edge 1.4) | **MIA +13** (LOSS; edge 1.7) | **SF -13** (WIN; edge 1.5) | SF (77.5%) | +10.4605 / +22 | 44.3 / 48 |
| SEA @ ARI | 31–7 | SEA -4 / ARI +4 | **SEA -4** (WIN; edge 0.2) | **SEA -4** (WIN; edge 0.7) | **SEA -4** (WIN; edge 0.4) | **SEA -4** (WIN; edge 0.8) | **SEA -4** (WIN; edge 4.9) | SEA (63.7%) | -4.19191 / -24 | 44.4 / 38 |
| WAS @ DAL ★ | 20–37 | WAS +4 / DAL -4 | **WAS +4** (LOSS; edge 3.1) | **WAS +4** (LOSS; edge 2.4) | **WAS +4** (LOSS; edge 2.6) | **WAS +4** (LOSS; edge 2.3) | **DAL -4** (WIN; edge 2.0) | DAL (53.9%) | +0.932333 / +17 | 48.0 / 57 |
| IND @ KC | 30–33 | IND +6.5 / KC -6.5 | **IND +6.5** (WIN; edge 1.2) | **IND +6.5** (WIN; edge 2.0) | **IND +6.5** (WIN; edge 0.6) | **IND +6.5** (WIN; edge 1.8) | **KC -6.5** (LOSS; edge 4.0) | KC (65.4%) | +5.32168 / +3 | 43.6 / 63 |
| NYG @ LA | 6–28 | NYG +7 / LA -7 | **NYG +7** (LOSS; edge 2.2) | **NYG +7** (LOSS; edge 3.9) | **NYG +7** (LOSS; edge 4.5) | **NYG +7** (LOSS; edge 3.6) | **LA -7** (WIN; edge 2.2) | LA (62.8%) | +4.84091 / +22 | 46.3 / 34 |

## Week 3

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 16/16 models available · 16/16 final games · **11–4–1 ATS** · **10/16 winner calls**

[Official Week 3 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-3.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/09/Circa-Sports-Million-VIII-Week-3-Selections.pdf)

**Research baseline top five by projected spread edge (4.0 Circa-style points from 5/5 graded):** #1 MIA +11.5 (7.7 pts, LOSS) · #2 CHI +4.5 (6.2 pts, WIN) · #3 NYG -2.5 (5.9 pts, WIN) · #4 WAS +7.5 (4.3 pts, WIN) · #5 BUF -7 (4.0 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 4.0 points:** #1 **MIA +11.5** (LOSS; edge 7.7) · #2 **CHI +4.5** (WIN; edge 6.2) · #3 **NYG -2.5** (WIN; edge 5.9) · #4 **WAS +7.5** (WIN; edge 4.3) · #5 **BUF -7** (WIN; edge 4.0)
- **Circa card #1T: extratrees · combined personnel interaction · 4.0 points:** #1 **MIA +11.5** (LOSS; edge 8.0) · #2 **CHI +4.5** (WIN; edge 5.5) · #3 **NYG -2.5** (WIN; edge 4.5) · #4 **PIT +3.5** (WIN; edge 3.9) · #5 **CLE +2.5** (WIN; edge 3.8)
- **Circa card #1T: extratrees · football support control · 4.0 points:** #1 **MIA +11.5** (LOSS; edge 8.2) · #2 **CHI +4.5** (WIN; edge 5.9) · #3 **NYG -2.5** (WIN; edge 5.3) · #4 **CLE +2.5** (WIN; edge 4.0) · #5 **BUF -7** (WIN; edge 3.7)
- **Circa card #1T: oof convex blend · 4.0 points:** #1 **MIA +11.5** (LOSS; edge 7.9) · #2 **CHI +4.5** (WIN; edge 5.6) · #3 **NYG -2.5** (WIN; edge 4.5) · #4 **CLE +2.5** (WIN; edge 4.0) · #5 **PIT +3.5** (WIN; edge 3.8)
- **Full-slate ATS #1: tensorflow mlp · football support control · 3.0 points:** #1 **MIA +11.5** (LOSS; edge 9.4) · #2 **NYG -2.5** (WIN; edge 9.3) · #3 **CHI +4.5** (WIN; edge 6.5) · #4 **JAX -3** (WIN; edge 5.5) · #5 **SF -8.5** (LOSS; edge 4.3)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| ATL @ GB | 35–14 | ATL +4.5 / GB -4.5 | **GB -4.5** (LOSS; edge 2.1) | **GB -4.5** (LOSS; edge 1.2) | **GB -4.5** (LOSS; edge 1.2) | **GB -4.5** (LOSS; edge 1.2) | **ATL +4.5** (WIN; edge 0.0) | GB (67.4%) | +6.62542 / -21 | 43.6 / 49 |
| CAR @ CLE | 18–21 | CAR -2.5 / CLE +2.5 | **CLE +2.5** (WIN; edge 2.9) | **CLE +2.5** (WIN; edge 3.8) | **CLE +2.5** (WIN; edge 4.0) | **CLE +2.5** (WIN; edge 4.0) | **CLE +2.5** (WIN; edge 3.2) | CAR (52.7%) | +0.419385 / +3 | 41.5 / 39 |
| CIN @ PIT | 27–30 | CIN -3.5 / PIT +3.5 | **PIT +3.5** (WIN; edge 2.5) | **PIT +3.5** (WIN; edge 3.9) | **PIT +3.5** (WIN; edge 3.4) | **PIT +3.5** (WIN; edge 3.8) | **CIN -3.5** (LOSS; edge 1.3) | CIN (52.2%) | -0.962667 / +3 | 42.7 / 57 |
| HOU @ IND | 17–19 | HOU -1.5 / IND +1.5 | **IND +1.5** (WIN; edge 0.1) | **IND +1.5** (WIN; edge 0.7) | **IND +1.5** (WIN; edge 0.5) | **IND +1.5** (WIN; edge 1.1) | **HOU -1.5** (LOSS; edge 3.1) | HOU (56.5%) | -1.35158 / +2 | 46.8 / 36 |
| KC @ MIA ★ | 24–10 | KC -11.5 / MIA +11.5 | **MIA +11.5** (LOSS; edge 7.7) | **MIA +11.5** (LOSS; edge 8.0) | **MIA +11.5** (LOSS; edge 8.2) | **MIA +11.5** (LOSS; edge 7.9) | **MIA +11.5** (LOSS; edge 9.4) | KC (63.3%) | -3.82957 / -14 | 41.6 / 34 |
| LAC @ BUF ★ | 16–24 | LAC +7 / BUF -7 | **BUF -7** (WIN; edge 4.0) | **BUF -7** (WIN; edge 3.4) | **BUF -7** (WIN; edge 3.7) | **BUF -7** (WIN; edge 3.1) | **BUF -7** (WIN; edge 2.5) | BUF (80.4%) | +11.0164 / +8 | 46.5 / 40 |
| NE @ JAX | 6–35 | NE +3 / JAX -3 | **JAX -3** (WIN; edge 0.7) | **NE +3** (LOSS; edge 1.6) | **NE +3** (LOSS; edge 1.3) | **NE +3** (LOSS; edge 1.3) | **JAX -3** (WIN; edge 5.5) | JAX (57.7%) | +3.66883 / +29 | 41.5 / 41 |
| NYJ @ DET | 24–31 | NYJ +6.5 / DET -6.5 | **DET -6.5** (WIN; edge 2.1) | **DET -6.5** (WIN; edge 3.0) | **DET -6.5** (WIN; edge 2.8) | **DET -6.5** (WIN; edge 3.0) | **NYJ +6.5** (LOSS; edge 0.7) | DET (78.1%) | +8.60491 / +7 | 46.8 / 55 |
| SEA @ WAS ★ | 31–33 | SEA -7.5 / WAS +7.5 | **WAS +7.5** (WIN; edge 4.3) | **WAS +7.5** (WIN; edge 3.1) | **WAS +7.5** (WIN; edge 3.6) | **WAS +7.5** (WIN; edge 3.3) | **WAS +7.5** (WIN; edge 1.0) | SEA (62.6%) | -3.20985 / +2 | 45.9 / 64 |
| TEN @ NYG ★ | 7–12 | TEN +2.5 / NYG -2.5 | **NYG -2.5** (WIN; edge 5.9) | **NYG -2.5** (WIN; edge 4.5) | **NYG -2.5** (WIN; edge 5.3) | **NYG -2.5** (WIN; edge 4.5) | **NYG -2.5** (WIN; edge 9.3) | NYG (70.5%) | +8.44005 / +5 | 44.2 / 19 |
| ARI @ SF | 30–36 | ARI +8.5 / SF -8.5 | **SF -8.5** (LOSS; edge 3.6) | **SF -8.5** (LOSS; edge 3.5) | **SF -8.5** (LOSS; edge 3.5) | **SF -8.5** (LOSS; edge 3.7) | **SF -8.5** (LOSS; edge 4.3) | SF (82.2%) | +12.0703 / +6 | 46.8 / 66 |
| MIN @ TB | 23–16 | MIN -1 / TB +1 | **MIN -1** (WIN; edge 1.2) | **MIN -1** (WIN; edge 1.2) | **MIN -1** (WIN; edge 0.9) | **MIN -1** (WIN; edge 0.7) | **TB +1** (LOSS; edge 0.0) | MIN (56.6%) | -2.15527 / -7 | 41.1 / 39 |
| BAL @ DAL | 34–31 | BAL -3 / DAL +3 | **BAL -3** (PUSH; edge 1.4) | **DAL +3** (PUSH; edge 1.0) | **DAL +3** (PUSH; edge 1.9) | **DAL +3** (PUSH; edge 0.7) | **DAL +3** (PUSH; edge 2.1) | BAL (59.6%) | -4.44939 / -3 | 46.2 / 65 |
| LV @ NO | 35–27 | LV +3 / NO -3 | **NO -3** (LOSS; edge 2.3) | **NO -3** (LOSS; edge 1.1) | **NO -3** (LOSS; edge 0.7) | **NO -3** (LOSS; edge 1.2) | **NO -3** (LOSS; edge 2.5) | NO (62.0%) | +5.32013 / -8 | 42.5 / 62 |
| LA @ DEN | 26–30 | LA -2.5 / DEN +2.5 | **DEN +2.5** (WIN; edge 4.0) | **DEN +2.5** (WIN; edge 3.3) | **DEN +2.5** (WIN; edge 3.4) | **DEN +2.5** (WIN; edge 3.2) | **LA -2.5** (LOSS; edge 1.0) | DEN (53.5%) | +1.50706 / +4 | 44.2 / 56 |
| PHI @ CHI ★ | 7–27 | PHI -4.5 / CHI +4.5 | **CHI +4.5** (WIN; edge 6.2) | **CHI +4.5** (WIN; edge 5.5) | **CHI +4.5** (WIN; edge 5.9) | **CHI +4.5** (WIN; edge 5.6) | **CHI +4.5** (WIN; edge 6.5) | CHI (51.7%) | +1.70123 / +20 | 44.7 / 34 |

## Week 4

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 16/16 models available · 16/16 final games · **10–5–1 ATS** · **10/16 winner calls**

[Official Week 4 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-4.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Week-4-Selections.pdf)

**Research baseline top five by projected spread edge (4.5 Circa-style points from 5/5 graded):** #1 CHI -3 (9.3 pts, WIN) · #2 JAX +2.5 (6.2 pts, WIN) · #3 NYG +2.5 (5.9 pts, WIN) · #4 SEA -7 (5.9 pts, PUSH) · #5 TB +3.5 (3.8 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 4.5 points:** #1 **CHI -3** (WIN; edge 9.3) · #2 **JAX +2.5** (WIN; edge 6.2) · #3 **NYG +2.5** (WIN; edge 5.9) · #4 **SEA -7** (PUSH; edge 5.9) · #5 **TB +3.5** (WIN; edge 3.8)
- **Circa card #1T: extratrees · combined personnel interaction · 4.5 points:** #1 **CHI -3** (WIN; edge 9.4) · #2 **NYG +2.5** (WIN; edge 6.0) · #3 **JAX +2.5** (WIN; edge 5.6) · #4 **SEA -7** (PUSH; edge 5.5) · #5 **TB +3.5** (WIN; edge 4.5)
- **Circa card #1T: extratrees · football support control · 4.5 points:** #1 **CHI -3** (WIN; edge 9.4) · #2 **NYG +2.5** (WIN; edge 6.4) · #3 **SEA -7** (PUSH; edge 5.8) · #4 **JAX +2.5** (WIN; edge 5.5) · #5 **TB +3.5** (WIN; edge 4.5)
- **Circa card #1T: oof convex blend · 4.5 points:** #1 **CHI -3** (WIN; edge 9.6) · #2 **NYG +2.5** (WIN; edge 6.1) · #3 **SEA -7** (PUSH; edge 5.4) · #4 **JAX +2.5** (WIN; edge 5.3) · #5 **TB +3.5** (WIN; edge 4.5)
- **Full-slate ATS #1: tensorflow mlp · football support control · 4.0 points:** #1 **NYG +2.5** (WIN; edge 13.6) · #2 **WAS +3.5** (LOSS; edge 9.8) · #3 **CLE +3** (WIN; edge 8.3) · #4 **TB +3.5** (WIN; edge 8.0) · #5 **SF -2.5** (WIN; edge 7.2)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| PIT @ CLE | 24–27 | PIT -3 / CLE +3 | **CLE +3** (WIN; edge 2.3) | **CLE +3** (WIN; edge 2.0) | **CLE +3** (WIN; edge 3.4) | **CLE +3** (WIN; edge 2.1) | **CLE +3** (WIN; edge 8.3) | PIT (53.4%) | -0.67907 / +3 | 40.4 / 51 |
| IND @ WAS | 30–13 | IND -3.5 / WAS +3.5 | **WAS +3.5** (LOSS; edge 3.8) | **WAS +3.5** (LOSS; edge 3.9) | **WAS +3.5** (LOSS; edge 4.4) | **WAS +3.5** (LOSS; edge 4.2) | **WAS +3.5** (LOSS; edge 9.8) | WAS (51.0%) | +0.256191 / -17 | 47.1 / 43 |
| ARI @ NYG ★ | 24–36 | ARI -2.5 / NYG +2.5 | **NYG +2.5** (WIN; edge 5.9) | **NYG +2.5** (WIN; edge 6.0) | **NYG +2.5** (WIN; edge 6.4) | **NYG +2.5** (WIN; edge 6.1) | **NYG +2.5** (WIN; edge 13.6) | NYG (57.6%) | +3.43925 / +12 | 43.2 / 60 |
| DAL @ HOU | 34–30 | DAL +3 / HOU -3 | **DAL +3** (WIN; edge 1.7) | **DAL +3** (WIN; edge 1.9) | **DAL +3** (WIN; edge 1.9) | **DAL +3** (WIN; edge 2.0) | **DAL +3** (WIN; edge 4.0) | HOU (56.0%) | +1.3013 / -4 | 46.1 / 64 |
| GB @ TB ★ | 17–14 | GB -3.5 / TB +3.5 | **TB +3.5** (WIN; edge 3.8) | **TB +3.5** (WIN; edge 4.5) | **TB +3.5** (WIN; edge 4.5) | **TB +3.5** (WIN; edge 4.5) | **TB +3.5** (WIN; edge 8.0) | GB (51.8%) | +0.309907 / -3 | 44.8 / 31 |
| JAX @ CIN ★ | 22–17 | JAX +2.5 / CIN -2.5 | **JAX +2.5** (WIN; edge 6.2) | **JAX +2.5** (WIN; edge 5.6) | **JAX +2.5** (WIN; edge 5.5) | **JAX +2.5** (WIN; edge 5.3) | **JAX +2.5** (WIN; edge 5.7) | JAX (59.1%) | -3.69515 / -5 | 47.4 / 39 |
| LA @ PHI | 24–20 | LA -3 / PHI +3 | **PHI +3** (LOSS; edge 1.4) | **PHI +3** (LOSS; edge 2.3) | **PHI +3** (LOSS; edge 1.6) | **PHI +3** (LOSS; edge 2.2) | **PHI +3** (LOSS; edge 1.6) | LA (52.1%) | -1.59407 / -4 | 44.7 / 44 |
| NE @ BUF | 29–26 | NE +6.5 / BUF -6.5 | **BUF -6.5** (LOSS; edge 0.9) | **NE +6.5** (WIN; edge 2.6) | **NE +6.5** (WIN; edge 1.2) | **NE +6.5** (WIN; edge 2.4) | **NE +6.5** (WIN; edge 0.3) | BUF (65.1%) | +7.42538 / -3 | 46.2 / 55 |
| NYJ @ CHI ★ | 12–23 | NYJ +3 / CHI -3 | **CHI -3** (WIN; edge 9.3) | **CHI -3** (WIN; edge 9.4) | **CHI -3** (WIN; edge 9.4) | **CHI -3** (WIN; edge 9.6) | **CHI -3** (WIN; edge 2.9) | CHI (81.9%) | +12.2844 / +11 | 46.3 / 35 |
| TEN @ BAL | 18–24 | TEN +11.5 / BAL -11.5 | **BAL -11.5** (LOSS; edge 1.0) | **BAL -11.5** (LOSS; edge 0.0) | **BAL -11.5** (LOSS; edge 0.7) | **TEN +11.5** (WIN; edge 0.1) | **BAL -11.5** (LOSS; edge 1.3) | BAL (81.8%) | +12.538 / +6 | 46.1 / 42 |
| MIA @ MIN | 10–15 | MIA +10.5 / MIN -10.5 | **MIN -10.5** (LOSS; edge 1.8) | **MIN -10.5** (LOSS; edge 1.2) | **MIN -10.5** (LOSS; edge 1.2) | **MIN -10.5** (LOSS; edge 1.0) | **MIN -10.5** (LOSS; edge 1.7) | MIN (80.0%) | +12.2719 / +5 | 41.0 / 25 |
| DEN @ SF | 14–24 | DEN +2.5 / SF -2.5 | **SF -2.5** (WIN; edge 2.9) | **SF -2.5** (WIN; edge 0.5) | **SF -2.5** (WIN; edge 1.0) | **SF -2.5** (WIN; edge 1.0) | **SF -2.5** (WIN; edge 7.2) | SF (59.1%) | +5.35152 / +10 | 47.5 / 38 |
| KC @ LV | 30–27 | KC -4.5 / LV +4.5 | **LV +4.5** (WIN; edge 1.8) | **LV +4.5** (WIN; edge 2.8) | **LV +4.5** (WIN; edge 2.8) | **LV +4.5** (WIN; edge 2.7) | **LV +4.5** (WIN; edge 1.6) | KC (57.0%) | -2.72971 / -3 | 43.1 / 57 |
| LAC @ SEA ★ | 23–30 | LAC +7 / SEA -7 | **SEA -7** (PUSH; edge 5.9) | **SEA -7** (PUSH; edge 5.5) | **SEA -7** (PUSH; edge 5.8) | **SEA -7** (PUSH; edge 5.4) | **SEA -7** (PUSH; edge 5.0) | SEA (78.4%) | +12.8644 / +7 | 43.8 / 53 |
| DET @ CAR | 26–32 | DET -3.5 / CAR +3.5 | **CAR +3.5** (WIN; edge 1.3) | **CAR +3.5** (WIN; edge 2.3) | **CAR +3.5** (WIN; edge 2.4) | **CAR +3.5** (WIN; edge 1.8) | **CAR +3.5** (WIN; edge 2.2) | DET (61.5%) | -2.1698 / +6 | 47.5 / 58 |
| ATL @ NO | 45–24 | ATL +2.5 / NO -2.5 | **ATL +2.5** (WIN; edge 1.2) | **ATL +2.5** (WIN; edge 2.1) | **ATL +2.5** (WIN; edge 2.2) | **ATL +2.5** (WIN; edge 2.1) | **ATL +2.5** (WIN; edge 1.9) | NO (52.3%) | +1.27272 / -21 | 43.6 / 69 |

## Week 5

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 15/15 models available · 15/15 final games · **7–7–1 ATS** · **9/14 winner calls**

[Official Week 5 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-5.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Week-5-Selections.pdf)

**Research baseline top five by projected spread edge (3.5 Circa-style points from 5/5 graded):** #1 BAL +3.5 (5.4 pts, WIN) · #2 TEN +7.5 (5.3 pts, LOSS) · #3 NE -3.5 (4.6 pts, WIN) · #4 MIA +7 (3.4 pts, PUSH) · #5 BUF +3 (3.3 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 3.5 points:** #1 **BAL +3.5** (WIN; edge 5.4) · #2 **TEN +7.5** (LOSS; edge 5.3) · #3 **NE -3.5** (WIN; edge 4.6) · #4 **MIA +7** (PUSH; edge 3.4) · #5 **BUF +3** (WIN; edge 3.3)
- **Circa card #1T: extratrees · combined personnel interaction · 3.5 points:** #1 **NYG +4** (WIN; edge 4.3) · #2 **BAL +3.5** (WIN; edge 4.1) · #3 **TEN +7.5** (LOSS; edge 4.1) · #4 **MIA +7** (PUSH; edge 3.5) · #5 **TB +8** (WIN; edge 3.4)
- **Circa card #1T: extratrees · football support control · 3.5 points:** #1 **TEN +7.5** (LOSS; edge 4.3) · #2 **NYG +4** (WIN; edge 4.2) · #3 **BAL +3.5** (WIN; edge 3.9) · #4 **TB +8** (WIN; edge 3.2) · #5 **MIA +7** (PUSH; edge 2.7)
- **Circa card #1T: oof convex blend · 3.5 points:** #1 **TEN +7.5** (LOSS; edge 4.4) · #2 **BAL +3.5** (WIN; edge 4.3) · #3 **NYG +4** (WIN; edge 4.2) · #4 **MIA +7** (PUSH; edge 3.5) · #5 **TB +8** (WIN; edge 3.2)
- **Full-slate ATS #1: tensorflow mlp · football support control · 3.0 points:** #1 **MIN -2** (WIN; edge 6.8) · #2 **CHI -1.5** (LOSS; edge 5.6) · #3 **NYG +4** (WIN; edge 4.5) · #4 **JAX -7.5** (LOSS; edge 4.3) · #5 **NE -3.5** (WIN; edge 4.2)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| TB @ DAL | 24–16 | TB +8 / DAL -8 | **TB +8** (WIN; edge 1.8) | **TB +8** (WIN; edge 3.4) | **TB +8** (WIN; edge 3.2) | **TB +8** (WIN; edge 3.2) | **TB +8** (WIN; edge 3.0) | DAL (68.4%) | +6.24114 / -8 | 47.1 / 40 |
| PHI @ JAX | 17–19 | PHI +7.5 / JAX -7.5 | **JAX -7.5** (LOSS; edge 0.7) | **JAX -7.5** (LOSS; edge 0.9) | **JAX -7.5** (LOSS; edge 0.7) | **JAX -7.5** (LOSS; edge 1.0) | **JAX -7.5** (LOSS; edge 4.3) | JAX (73.5%) | +8.24953 / +2 | 43.3 / 36 |
| CHI @ GB | 7–31 | CHI -1.5 / GB +1.5 | **CHI -1.5** (LOSS; edge 1.5) | **CHI -1.5** (LOSS; edge 1.2) | **CHI -1.5** (LOSS; edge 1.4) | **CHI -1.5** (LOSS; edge 1.1) | **CHI -1.5** (LOSS; edge 5.6) | CHI (63.7%) | -3.01833 / +24 | 46.7 / 38 |
| CIN @ MIA ★ | 31–24 | CIN -7 / MIA +7 | **MIA +7** (PUSH; edge 3.4) | **MIA +7** (PUSH; edge 3.5) | **MIA +7** (PUSH; edge 2.7) | **MIA +7** (PUSH; edge 3.5) | **MIA +7** (PUSH; edge 3.0) | CIN (68.6%) | -3.55517 / -7 | 44.2 / 55 |
| CLE @ NYJ | 12–17 | CLE +1.5 / NYJ -1.5 | **CLE +1.5** (LOSS; edge 2.6) | **CLE +1.5** (LOSS; edge 3.0) | **CLE +1.5** (LOSS; edge 2.4) | **CLE +1.5** (LOSS; edge 2.9) | **CLE +1.5** (LOSS; edge 2.3) | CLE (58.0%) | -1.12941 / +5 | 41.3 / 29 |
| HOU @ TEN ★ | 26–3 | HOU -7.5 / TEN +7.5 | **TEN +7.5** (LOSS; edge 5.3) | **TEN +7.5** (LOSS; edge 4.1) | **TEN +7.5** (LOSS; edge 4.3) | **TEN +7.5** (LOSS; edge 4.4) | **TEN +7.5** (LOSS; edge 4.1) | HOU (61.8%) | -2.17051 / -23 | 42.1 / 29 |
| IND @ PIT | 22–34 | IND +2.5 / PIT -2.5 | **IND +2.5** (LOSS; edge 1.6) | **IND +2.5** (LOSS; edge 1.5) | **IND +2.5** (LOSS; edge 1.5) | **IND +2.5** (LOSS; edge 1.6) | **PIT -2.5** (WIN; edge 0.7) | PIT (53.3%) | +0.915378 / +12 | 44.4 / 56 |
| LV @ NE ★ | 17–45 | LV +3.5 / NE -3.5 | **NE -3.5** (WIN; edge 4.6) | **NE -3.5** (WIN; edge 2.1) | **NE -3.5** (WIN; edge 0.8) | **NE -3.5** (WIN; edge 2.7) | **NE -3.5** (WIN; edge 4.2) | NE (67.3%) | +8.05778 / +28 | 42.6 / 62 |
| MIN @ NO | 23–13 | MIN -2 / NO +2 | **MIN -2** (WIN; edge 1.5) | **MIN -2** (WIN; edge 0.6) | **MIN -2** (WIN; edge 0.3) | **MIN -2** (WIN; edge 0.4) | **MIN -2** (WIN; edge 6.8) | MIN (58.4%) | -3.45343 / -10 | 43.0 / 36 |
| NYG @ WAS | 27–27 | NYG +4 / WAS -4 | **NYG +4** (WIN; edge 3.2) | **NYG +4** (WIN; edge 4.3) | **NYG +4** (WIN; edge 4.2) | **NYG +4** (WIN; edge 4.2) | **NYG +4** (WIN; edge 4.5) | Unavailable | +0.831673 / +0 | 43.9 / 54 |
| DEN @ LAC | 23–17 | DEN -3.5 / LAC +3.5 | **LAC +3.5** (LOSS; edge 1.0) | **LAC +3.5** (LOSS; edge 0.5) | **LAC +3.5** (LOSS; edge 0.9) | **LAC +3.5** (LOSS; edge 0.7) | **LAC +3.5** (LOSS; edge 3.8) | DEN (57.1%) | -2.46546 / -6 | 41.3 / 40 |
| DET @ ARI | 45–21 | DET -5.5 / ARI +5.5 | **ARI +5.5** (LOSS; edge 1.9) | **ARI +5.5** (LOSS; edge 1.3) | **ARI +5.5** (LOSS; edge 1.3) | **ARI +5.5** (LOSS; edge 1.4) | **ARI +5.5** (LOSS; edge 1.7) | DET (65.0%) | -3.59172 / -24 | 47.6 / 66 |
| SF @ SEA | 32–29 | SF +3 / SEA -3 | **SF +3** (WIN; edge 0.6) | **SEA -3** (LOSS; edge 0.6) | **SEA -3** (LOSS; edge 0.1) | **SEA -3** (LOSS; edge 0.5) | **SF +3** (WIN; edge 0.6) | SEA (63.4%) | +2.44963 / -3 | 47.8 / 61 |
| BAL @ ATL ★ | 30–23 | BAL +3.5 / ATL -3.5 | **BAL +3.5** (WIN; edge 5.4) | **BAL +3.5** (WIN; edge 4.1) | **BAL +3.5** (WIN; edge 3.9) | **BAL +3.5** (WIN; edge 4.3) | **BAL +3.5** (WIN; edge 4.1) | BAL (55.6%) | -1.89448 / -7 | 45.6 / 53 |
| BUF @ LA ★ | 37–34 | BUF +3 / LA -3 | **BUF +3** (WIN; edge 3.3) | **BUF +3** (WIN; edge 2.0) | **BUF +3** (WIN; edge 1.9) | **BUF +3** (WIN; edge 2.0) | **BUF +3** (WIN; edge 1.6) | LA (53.5%) | -0.271327 / -3 | 47.4 / 71 |

## Week 6

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 14/14 models available · 14/14 final games · **3–10–1 ATS** · **7/14 winner calls**

[Official Week 6 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-6.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Week-6-Selections.pdf)

**Research baseline top five by projected spread edge (1.5 Circa-style points from 5/5 graded):** #1 SF -7.5 (6.0 pts, LOSS) · #2 JAX -2.5 (5.7 pts, LOSS) · #3 PHI +1 (5.4 pts, LOSS) · #4 NE -7 (4.7 pts, PUSH) · #5 KC -8 (3.4 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 1.5 points:** #1 **SF -7.5** (LOSS; edge 6.0) · #2 **JAX -2.5** (LOSS; edge 5.7) · #3 **PHI +1** (LOSS; edge 5.4) · #4 **NE -7** (PUSH; edge 4.7) · #5 **KC -8** (WIN; edge 3.4)
- **Circa card #1T: extratrees · combined personnel interaction · 0.5 points:** #1 **JAX -2.5** (LOSS; edge 5.4) · #2 **NE -7** (PUSH; edge 5.2) · #3 **SF -7.5** (LOSS; edge 5.0) · #4 **NYG +1** (LOSS; edge 3.6) · #5 **IND -7** (LOSS; edge 3.3)
- **Circa card #1T: extratrees · football support control · 0.5 points:** #1 **NE -7** (PUSH; edge 5.8) · #2 **SF -7.5** (LOSS; edge 4.8) · #3 **JAX -2.5** (LOSS; edge 4.5) · #4 **NYG +1** (LOSS; edge 4.4) · #5 **PHI +1** (LOSS; edge 3.5)
- **Circa card #1T: oof convex blend · 0.5 points:** #1 **JAX -2.5** (LOSS; edge 5.5) · #2 **NE -7** (PUSH; edge 5.4) · #3 **SF -7.5** (LOSS; edge 5.0) · #4 **NYG +1** (LOSS; edge 3.7) · #5 **IND -7** (LOSS; edge 3.4)
- **Full-slate ATS #1: tensorflow mlp · football support control · 1.5 points:** #1 **NYG +1** (LOSS; edge 10.3) · #2 **KC -8** (WIN; edge 5.8) · #3 **ATL +0** (LOSS; edge 5.3) · #4 **TB +2.5** (LOSS; edge 4.9) · #5 **NE -7** (PUSH; edge 4.5)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| SEA @ DEN | 14–17 | SEA -2.5 / DEN +2.5 | **SEA -2.5** (LOSS; edge 0.8) | **DEN +2.5** (WIN; edge 1.3) | **DEN +2.5** (WIN; edge 0.6) | **DEN +2.5** (WIN; edge 1.4) | **DEN +2.5** (WIN; edge 3.3) | SEA (56.8%) | -3.30974 / +3 | 44.0 / 31 |
| HOU @ JAX ★ | 34–31 | HOU +2.5 / JAX -2.5 | **JAX -2.5** (LOSS; edge 5.7) | **JAX -2.5** (LOSS; edge 5.4) | **JAX -2.5** (LOSS; edge 4.5) | **JAX -2.5** (LOSS; edge 5.5) | **HOU +2.5** (WIN; edge 0.3) | JAX (74.7%) | +8.153 / -3 | 44.1 / 65 |
| BAL @ CLE | 10–13 | BAL -5.5 / CLE +5.5 | **CLE +5.5** (WIN; edge 0.8) | **CLE +5.5** (WIN; edge 0.7) | **CLE +5.5** (WIN; edge 0.4) | **CLE +5.5** (WIN; edge 0.5) | **CLE +5.5** (WIN; edge 2.1) | BAL (66.9%) | -4.67597 / +3 | 43.4 / 23 |
| CAR @ PHI ★ | 25–14 | CAR -1 / PHI +1 | **PHI +1** (LOSS; edge 5.4) | **PHI +1** (LOSS; edge 3.2) | **PHI +1** (LOSS; edge 3.5) | **PHI +1** (LOSS; edge 3.4) | **PHI +1** (LOSS; edge 3.1) | PHI (56.7%) | +4.44985 / -11 | 42.4 / 39 |
| CHI @ ATL | 31–23 | CHI -0 / ATL +0 | **ATL +0** (LOSS; edge 1.9) | **ATL +0** (LOSS; edge 1.0) | **ATL +0** (LOSS; edge 0.9) | **ATL +0** (LOSS; edge 1.0) | **ATL +0** (LOSS; edge 5.3) | CHI (50.7%) | +1.87141 / -8 | 45.6 / 54 |
| NO @ NYG | 34–27 | NO -1 / NYG +1 | **NYG +1** (LOSS; edge 3.1) | **NYG +1** (LOSS; edge 3.6) | **NYG +1** (LOSS; edge 4.4) | **NYG +1** (LOSS; edge 3.7) | **NYG +1** (LOSS; edge 10.3) | NYG (60.5%) | +2.05253 / -7 | 43.9 / 61 |
| NYJ @ NE ★ | 19–26 | NYJ +7 / NE -7 | **NE -7** (PUSH; edge 4.7) | **NE -7** (PUSH; edge 5.2) | **NE -7** (PUSH; edge 5.8) | **NE -7** (PUSH; edge 5.4) | **NE -7** (PUSH; edge 4.5) | NE (80.3%) | +11.6662 / +7 | 43.6 / 45 |
| PIT @ TB | 26–19 | PIT -2.5 / TB +2.5 | **TB +2.5** (LOSS; edge 1.5) | **TB +2.5** (LOSS; edge 2.3) | **TB +2.5** (LOSS; edge 2.0) | **TB +2.5** (LOSS; edge 2.5) | **TB +2.5** (LOSS; edge 4.9) | PIT (52.4%) | -1.01665 / -7 | 42.7 / 45 |
| TEN @ IND | 26–20 | TEN +7 / IND -7 | **IND -7** (LOSS; edge 3.2) | **IND -7** (LOSS; edge 3.3) | **IND -7** (LOSS; edge 3.4) | **IND -7** (LOSS; edge 3.4) | **TEN +7** (WIN; edge 2.8) | IND (78.1%) | +10.201 / -6 | 46.2 / 46 |
| ARI @ LA | 18–16 | ARI +12.5 / LA -12.5 | **LA -12.5** (LOSS; edge 0.7) | **ARI +12.5** (WIN; edge 0.2) | **ARI +12.5** (WIN; edge 0.5) | **LA -12.5** (LOSS; edge 0.1) | **LA -12.5** (LOSS; edge 1.7) | LA (83.1%) | +13.222 / -2 | 47.2 / 34 |
| BUF @ LV | 33–30 | BUF -4.5 / LV +4.5 | **BUF -4.5** (LOSS; edge 1.4) | **BUF -4.5** (LOSS; edge 2.5) | **BUF -4.5** (LOSS; edge 2.6) | **BUF -4.5** (LOSS; edge 2.6) | **LV +4.5** (WIN; edge 0.8) | BUF (70.2%) | -5.88808 / -3 | 46.7 / 63 |
| LAC @ KC ★ | 6–22 | LAC +8 / KC -8 | **KC -8** (WIN; edge 3.4) | **KC -8** (WIN; edge 1.8) | **KC -8** (WIN; edge 1.6) | **KC -8** (WIN; edge 2.0) | **KC -8** (WIN; edge 5.8) | KC (82.0%) | +11.4366 / +16 | 43.6 / 28 |
| DAL @ GB | 13–23 | DAL +1 / GB -1 | **GB -1** (WIN; edge 2.1) | **GB -1** (WIN; edge 2.1) | **GB -1** (WIN; edge 3.0) | **GB -1** (WIN; edge 2.2) | **GB -1** (WIN; edge 2.6) | GB (60.4%) | +3.11394 / +10 | 47.9 / 36 |
| WAS @ SF ★ | 17–23 | WAS +7.5 / SF -7.5 | **SF -7.5** (LOSS; edge 6.0) | **SF -7.5** (LOSS; edge 5.0) | **SF -7.5** (LOSS; edge 4.8) | **SF -7.5** (LOSS; edge 5.0) | **SF -7.5** (LOSS; edge 4.2) | SF (80.3%) | +13.461 / +6 | 48.3 / 40 |

## Week 7

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 14/14 models available · 14/14 final games · **5–8–1 ATS** · **7/14 winner calls**

[Official Week 7 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-7.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Week-7-Selections.pdf)

**Research baseline top five by projected spread edge (1.0 Circa-style points from 5/5 graded):** #1 CAR -3 (4.9 pts, LOSS) · #2 PHI +3.5 (4.3 pts, LOSS) · #3 NE +3 (3.7 pts, LOSS) · #4 MIA +4 (3.7 pts, WIN) · #5 BAL -1.5 (2.8 pts, LOSS)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 1.0 points:** #1 **CAR -3** (LOSS; edge 4.9) · #2 **PHI +3.5** (LOSS; edge 4.3) · #3 **NE +3** (LOSS; edge 3.7) · #4 **MIA +4** (WIN; edge 3.7) · #5 **BAL -1.5** (LOSS; edge 2.8)
- **Circa card #1T: extratrees · combined personnel interaction · 2.0 points:** #1 **CAR -3** (LOSS; edge 5.0) · #2 **PHI +3.5** (LOSS; edge 4.4) · #3 **MIA +4** (WIN; edge 3.1) · #4 **NE +3** (LOSS; edge 2.9) · #5 **NYG +10** (WIN; edge 2.5)
- **Circa card #1T: extratrees · football support control · 2.0 points:** #1 **PHI +3.5** (LOSS; edge 4.8) · #2 **CAR -3** (LOSS; edge 3.9) · #3 **MIA +4** (WIN; edge 3.1) · #4 **NE +3** (LOSS; edge 2.7) · #5 **NYG +10** (WIN; edge 2.5)
- **Circa card #1T: oof convex blend · 2.0 points:** #1 **CAR -3** (LOSS; edge 4.8) · #2 **PHI +3.5** (LOSS; edge 4.3) · #3 **MIA +4** (WIN; edge 3.4) · #4 **NE +3** (LOSS; edge 2.6) · #5 **NYG +10** (WIN; edge 2.5)
- **Full-slate ATS #1: tensorflow mlp · football support control · 1.0 points:** #1 **MIN -6.5** (LOSS; edge 6.5) · #2 **BAL -1.5** (LOSS; edge 4.9) · #3 **PHI +3.5** (LOSS; edge 3.0) · #4 **NE +3** (LOSS; edge 2.6) · #5 **ATL +2.5** (WIN; edge 2.3)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| NE @ CHI ★ | 24–30 | NE +3 / CHI -3 | **NE +3** (LOSS; edge 3.7) | **NE +3** (LOSS; edge 2.9) | **NE +3** (LOSS; edge 2.7) | **NE +3** (LOSS; edge 2.6) | **NE +3** (LOSS; edge 2.6) | NE (50.6%) | -0.68285 / +6 | 44.6 / 54 |
| PIT @ NO | 16–10 | PIT -3 / NO +3 | **PIT -3** (WIN; edge 0.9) | **NO +3** (LOSS; edge 1.1) | **NO +3** (LOSS; edge 0.7) | **NO +3** (LOSS; edge 1.1) | **PIT -3** (WIN; edge 0.4) | PIT (61.7%) | -3.94126 / -6 | 47.1 / 26 |
| CIN @ BAL ★ | 35–13 | CIN +1.5 / BAL -1.5 | **BAL -1.5** (LOSS; edge 2.8) | **BAL -1.5** (LOSS; edge 2.1) | **BAL -1.5** (LOSS; edge 2.2) | **BAL -1.5** (LOSS; edge 2.3) | **BAL -1.5** (LOSS; edge 4.9) | BAL (61.2%) | +4.33739 / -22 | 47.1 / 48 |
| CLE @ TEN | 27–24 | CLE -2.5 / TEN +2.5 | **CLE -2.5** (WIN; edge 0.1) | **TEN +2.5** (LOSS; edge 0.6) | **TEN +2.5** (LOSS; edge 1.0) | **TEN +2.5** (LOSS; edge 0.9) | **TEN +2.5** (LOSS; edge 1.7) | CLE (54.7%) | -2.64256 / -3 | 40.1 / 51 |
| IND @ MIN | 10–16 | IND +6.5 / MIN -6.5 | **MIN -6.5** (LOSS; edge 1.5) | **MIN -6.5** (LOSS; edge 0.7) | **MIN -6.5** (LOSS; edge 1.0) | **MIN -6.5** (LOSS; edge 1.0) | **MIN -6.5** (LOSS; edge 6.5) | MIN (71.9%) | +8.02337 / +6 | 42.5 / 26 |
| MIA @ NYJ ★ | 28–25 | MIA +4 / NYJ -4 | **MIA +4** (WIN; edge 3.7) | **MIA +4** (WIN; edge 3.1) | **MIA +4** (WIN; edge 3.1) | **MIA +4** (WIN; edge 3.4) | **MIA +4** (WIN; edge 1.6) | NYJ (51.1%) | +0.328489 / -3 | 40.7 / 53 |
| NYG @ HOU | 27–21 | NYG +10 / HOU -10 | **NYG +10** (WIN; edge 1.5) | **NYG +10** (WIN; edge 2.5) | **NYG +10** (WIN; edge 2.5) | **NYG +10** (WIN; edge 2.5) | **NYG +10** (WIN; edge 0.9) | HOU (73.1%) | +8.53891 / -6 | 45.4 / 48 |
| SF @ ATL | 20–29 | SF -2.5 / ATL +2.5 | **SF -2.5** (LOSS; edge 1.6) | **SF -2.5** (LOSS; edge 1.8) | **SF -2.5** (LOSS; edge 2.1) | **SF -2.5** (LOSS; edge 1.9) | **ATL +2.5** (WIN; edge 2.3) | SF (62.9%) | -4.10761 / +9 | 47.1 / 49 |
| TB @ CAR ★ | 43–13 | TB +3 / CAR -3 | **CAR -3** (LOSS; edge 4.9) | **CAR -3** (LOSS; edge 5.0) | **CAR -3** (LOSS; edge 3.9) | **CAR -3** (LOSS; edge 4.8) | **CAR -3** (LOSS; edge 2.0) | CAR (72.0%) | +7.90698 / -30 | 46.2 / 56 |
| DEN @ ARI | 30–16 | DEN -4.5 / ARI +4.5 | **ARI +4.5** (LOSS; edge 0.1) | **ARI +4.5** (LOSS; edge 1.4) | **ARI +4.5** (LOSS; edge 1.2) | **ARI +4.5** (LOSS; edge 1.6) | **DEN -4.5** (WIN; edge 1.4) | DEN (62.4%) | -4.38768 / -14 | 45.3 / 46 |
| GB @ DET | 17–20 | GB +3 / DET -3 | **DET -3** (PUSH; edge 1.3) | **GB +3** (PUSH; edge 0.3) | **GB +3** (PUSH; edge 0.2) | **GB +3** (PUSH; edge 0.2) | **GB +3** (PUSH; edge 1.4) | DET (56.4%) | +4.33694 / +3 | 47.7 / 37 |
| LA @ LV | 35–21 | LA -4 / LV +4 | **LA -4** (WIN; edge 0.4) | **LV +4** (LOSS; edge 0.4) | **LV +4** (LOSS; edge 0.3) | **LA -4** (WIN; edge 0.1) | **LA -4** (WIN; edge 1.4) | LA (67.6%) | -4.42342 / -14 | 48.7 / 56 |
| KC @ SEA | 3–20 | KC +2.5 / SEA -2.5 | **KC +2.5** (LOSS; edge 0.4) | **SEA -2.5** (WIN; edge 0.3) | **KC +2.5** (LOSS; edge 0.6) | **SEA -2.5** (WIN; edge 0.1) | **KC +2.5** (LOSS; edge 1.1) | SEA (62.9%) | +2.11784 / +17 | 44.4 / 23 |
| DAL @ PHI ★ | 38–21 | DAL -3.5 / PHI +3.5 | **PHI +3.5** (LOSS; edge 4.3) | **PHI +3.5** (LOSS; edge 4.4) | **PHI +3.5** (LOSS; edge 4.8) | **PHI +3.5** (LOSS; edge 4.3) | **PHI +3.5** (LOSS; edge 3.0) | PHI (55.8%) | +0.784658 / -17 | 44.1 / 59 |

## Week 8

**RETROSPECTIVE RECONSTRUCTION — not issued at kickoff** · 13/14 models available · 14/14 final games · **8–5–0 ATS** · **11/13 winner calls**

[Official Week 8 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/10/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-8.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/11/Circa-Sports-Million-VIII-Week-8-Selections.pdf)

**Research baseline top five by projected spread edge (4.0 Circa-style points from 5/5 graded):** #1 BUF -3 (7.0 pts, WIN) · #2 PHI +6 (4.6 pts, LOSS) · #3 DEN +1.5 (4.4 pts, WIN) · #4 LA -6.5 (4.3 pts, WIN) · #5 PIT -3 (2.9 pts, WIN)

**Separate five-pick cards for all four Circa leaders and the ATS leader:**

- **Circa card #1T: catboost · football support control · 4.0 points:** #1 **BUF -3** (WIN; edge 7.0) · #2 **PHI +6** (LOSS; edge 4.6) · #3 **DEN +1.5** (WIN; edge 4.4) · #4 **LA -6.5** (WIN; edge 4.3) · #5 **PIT -3** (WIN; edge 2.9)
- **Circa card #1T: extratrees · combined personnel interaction · 3.0 points:** #1 **PHI +6** (LOSS; edge 6.1) · #2 **LA -6.5** (WIN; edge 4.3) · #3 **BUF -3** (WIN; edge 4.3) · #4 **MIN +3.5** (LOSS; edge 3.7) · #5 **DEN +1.5** (WIN; edge 3.4)
- **Circa card #1T: extratrees · football support control · 3.0 points:** #1 **PHI +6** (LOSS; edge 5.4) · #2 **BUF -3** (WIN; edge 4.6) · #3 **LA -6.5** (WIN; edge 4.3) · #4 **MIN +3.5** (LOSS; edge 3.4) · #5 **DEN +1.5** (WIN; edge 3.3)
- **Circa card #1T: oof convex blend · 3.0 points:** #1 **PHI +6** (LOSS; edge 5.8) · #2 **BUF -3** (WIN; edge 4.4) · #3 **LA -6.5** (WIN; edge 4.4) · #4 **DEN +1.5** (WIN; edge 3.6) · #5 **MIN +3.5** (LOSS; edge 3.4)
- **Full-slate ATS #1: tensorflow mlp · football support control · 3.0 points:** #1 **BUF -3** (WIN; edge 9.4) · #2 **MIN +3.5** (LOSS; edge 6.2) · #3 **TB -2.5** (WIN; edge 5.1) · #4 **NYJ -1.5** (LOSS; edge 4.3) · #5 **TEN +12.5** (WIN; edge 3.8)

| Game (away @ home) | Final | Official Circa (away / home) | CatBoost card #1T | ExtraTrees combined #1T | ExtraTrees support #1T | OOF convex #1T | TensorFlow ATS #1 | Model winner (prob.) | Baseline margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|---|---|---|---|
| CAR @ GB | 19–27 | CAR +3.5 / GB -3.5 | **GB -3.5** (WIN; edge 0.8) | **GB -3.5** (WIN; edge 1.6) | **GB -3.5** (WIN; edge 1.8) | **GB -3.5** (WIN; edge 1.6) | **GB -3.5** (WIN; edge 3.4) | GB (69.1%) | +4.34046 / +8 | 44.4 / 46 |
| ARI @ DAL | 33–30 | ARI +7 / DAL -7 | **DAL -7** (LOSS; edge 2.7) | **DAL -7** (LOSS; edge 2.9) | **DAL -7** (LOSS; edge 2.1) | **DAL -7** (LOSS; edge 2.9) | **DAL -7** (LOSS; edge 0.8) | DAL (78.8%) | +9.70294 / -3 | 47.8 / 63 |
| ATL @ TB | 0–16 | ATL +2.5 / TB -2.5 | **TB -2.5** (WIN; edge 0.0) | **TB -2.5** (WIN; edge 0.6) | **TB -2.5** (WIN; edge 0.4) | **TB -2.5** (WIN; edge 0.9) | **TB -2.5** (WIN; edge 5.1) | TB (56.3%) | +2.52793 / +16 | 45.2 / 16 |
| BAL @ BUF ★ | 10–36 | BAL +3 / BUF -3 | **BUF -3** (WIN; edge 7.0) | **BUF -3** (WIN; edge 4.3) | **BUF -3** (WIN; edge 4.6) | **BUF -3** (WIN; edge 4.4) | **BUF -3** (WIN; edge 9.4) | BUF (73.6%) | +9.97797 / +26 | 47.1 / 46 |
| CLE @ PIT ★ | 6–27 | CLE +3 / PIT -3 | **PIT -3** (WIN; edge 2.9) | **PIT -3** (WIN; edge 1.5) | **PIT -3** (WIN; edge 1.7) | **PIT -3** (WIN; edge 1.6) | **CLE +3** (LOSS; edge 0.4) | PIT (67.3%) | +5.87315 / +21 | 42.7 / 33 |
| IND @ JAX | 7–42 | IND +10 / JAX -10 | **IND +10** (LOSS; edge 1.8) | **IND +10** (LOSS; edge 1.2) | **IND +10** (LOSS; edge 1.9) | **IND +10** (LOSS; edge 1.1) | **JAX -10** (WIN; edge 2.7) | JAX (77.6%) | +8.19788 / +35 | 47.8 / 49 |
| LV @ NYJ | 38–33 | LV +1.5 / NYJ -1.5 | **LV +1.5** (WIN; edge 1.0) | **NYJ -1.5** (LOSS; edge 0.1) | **LV +1.5** (WIN; edge 0.1) | **NYJ -1.5** (LOSS; edge 0.1) | **NYJ -1.5** (LOSS; edge 4.3) | LV (50.3%) | +0.523055 / -5 | 44.4 / 71 |
| MIN @ DET | 15–19 | MIN +3.5 / DET -3.5 | **MIN +3.5** (LOSS; edge 1.2) | **MIN +3.5** (LOSS; edge 3.7) | **MIN +3.5** (LOSS; edge 3.4) | **MIN +3.5** (LOSS; edge 3.4) | **MIN +3.5** (LOSS; edge 6.2) | DET (53.9%) | +2.30138 / +4 | 43.8 / 34 |
| TEN @ CIN | 36–43 | TEN +12.5 / CIN -12.5 | **CIN -12.5** (LOSS; edge 0.6) | **CIN -12.5** (LOSS; edge 0.6) | **CIN -12.5** (LOSS; edge 0.9) | **CIN -12.5** (LOSS; edge 0.6) | **TEN +12.5** (WIN; edge 3.8) | CIN (82.0%) | +13.0973 / +7 | 46.8 / 79 |
| LAC @ LA ★ | 9–24 | LAC +6.5 / LA -6.5 | **LA -6.5** (WIN; edge 4.3) | **LA -6.5** (WIN; edge 4.3) | **LA -6.5** (WIN; edge 4.3) | **LA -6.5** (WIN; edge 4.4) | **LA -6.5** (WIN; edge 2.6) | LA (79.9%) | +10.8185 / +15 | 43.1 / 33 |
| KC @ DEN ★ | 24–28 | KC -1.5 / DEN +1.5 | **DEN +1.5** (WIN; edge 4.4) | **DEN +1.5** (WIN; edge 3.4) | **DEN +1.5** (WIN; edge 3.3) | **DEN +1.5** (WIN; edge 3.6) | **KC -1.5** (LOSS; edge 1.6) | DEN (56.2%) | +2.86769 / +4 | 43.9 / 52 |
| NE @ MIA | 24–19 | NE -7 / MIA +7 | **MIA +7** (WIN; edge 2.5) | **MIA +7** (WIN; edge 1.3) | **MIA +7** (WIN; edge 1.3) | **MIA +7** (WIN; edge 1.3) | **NE -7** (LOSS; edge 3.5) | NE (68.3%) | -4.53708 / -5 | 44.9 / 43 |
| PHI @ WAS ★ | 10–27 | PHI +6 / WAS -6 | **PHI +6** (LOSS; edge 4.6) | **PHI +6** (LOSS; edge 6.1) | **PHI +6** (LOSS; edge 5.4) | **PHI +6** (LOSS; edge 5.8) | **PHI +6** (LOSS; edge 1.0) | PHI (53.1%) | +1.41173 / +17 | 44.0 / 37 |
| CHI @ SEA | 34–17 | CHI +3 / SEA -3 | — | — | — | — | — | Unavailable | — / -17 | — / 51 |

## Week 9

**ORIGINAL SAVED FORECASTS — before kickoff, after Circa deadline** · 14/15 models available · 11/15 final games · **6–4–0 ATS** · **10/10 winner calls**

[Official Week 9 fixed spreads](https://www.circasports.com/wp-content/uploads/2026/11/Circa-Sports-Million-VIII-Contest-Point-Spreads-Week-9.pdf) · [Official entrant selection records](https://www.circasports.com/wp-content/uploads/2026/11/Circa-Sports-Million-VIII-Week-9-Selections.pdf)

**Original issued model top five by projected spread edge (3.0 Circa-style points from 4/5 graded):** #1 MIN +3.5 (3.1 pts, pending) · #2 NYJ +10 (2.3 pts, LOSS) · #3 CIN -3 (2.1 pts, WIN) · #4 DEN -2.5 (1.9 pts, WIN) · #5 LA -4 (1.8 pts, WIN)

**Week 9 uses actual original N056 issues, not the historical model ranking.**

| Game (away @ home) | Final | Official Circa (away / home) | Original model ATS | Model winner (prob.) | Predicted margin / actual | Total forecast / actual |
|---|---:|---|---|---|---|---|
| JAX @ BAL | 33–10 | JAX -10 / BAL +10 | Unavailable (Pending) | Unavailable | — / -23 | — / 43 |
| CIN @ ATL ★ | 34–17 | CIN -3 / ATL +3 | **CIN -3** (edge 2.1) (WIN) | CIN (66.2%) | -5.09172 / -17 | 47.8 / 51 |
| CLE @ NO | 22–23 | CLE +3 / NO -3 | **CLE +3** (edge 0.3) (WIN) | NO (56.6%) | +2.65543 / +1 | 42.1 / 45 |
| DAL @ IND | 27–23 | DAL -4.5 / IND +4.5 | **IND +4.5** (edge 1.1) (WIN) | DAL (60.0%) | -3.41572 / -4 | 45.0 / 50 |
| DEN @ CAR ★ | 26–21 | DEN -2.5 / CAR +2.5 | **DEN -2.5** (edge 1.9) (WIN) | DEN (64.6%) | -4.38146 / -5 | 44.6 / 47 |
| DET @ MIA | 19–9 | DET -7 / MIA +7 | **MIA +7** (edge 1.6) (LOSS) | DET (69.3%) | -5.43639 / -10 | 46.2 / 28 |
| LA @ WAS ★ | 20–13 | LA -4 / WAS +4 | **LA -4** (edge 1.8) (WIN) | LA (67.3%) | -5.76037 / -7 | 45.5 / 33 |
| NYG @ PHI | 19–11 | NYG -3.5 / PHI +3.5 | **PHI +3.5** (edge 1.8) (LOSS) | NYG (54.3%) | -1.74479 / -8 | 38.6 / 30 |
| NYJ @ KC ★ | 12–35 | NYJ +10 / KC -10 | **NYJ +10** (edge 2.3) (LOSS) | KC (74.0%) | +7.72843 / +23 | 44.9 / 47 |
| HOU @ LAC | Pending | HOU -4.5 / LAC +4.5 | **HOU -4.5** (edge 0.2) (Pending) | HOU (63.0%) | -4.67224 / pending | 40.4 / pending |
| ARI @ SEA | 3–17 | ARI +8.5 / SEA -8.5 | **ARI +8.5** (edge 1.1) (LOSS) | SEA (72.1%) | +7.42656 / +14 | 43.2 / 20 |
| GB @ NE | Pending | GB +3 / NE -3 | **NE -3** (edge 1.5) (Pending) | NE (71.7%) | +4.54755 / pending | 45.6 / pending |
| LV @ SF | 17–38 | LV +10 / SF -10 | **SF -10** (edge 0.2) (WIN) | SF (79.3%) | +10.2456 / +21 | 47.3 / 55 |
| TB @ CHI | Pending | TB +6 / CHI -6 | **CHI -6** (edge 0.4) (Pending) | CHI (71.0%) | +6.41495 / pending | 41.2 / pending |
| BUF @ MIN ★ | Pending | BUF -3.5 / MIN +3.5 | **MIN +3.5** (edge 3.1) (Pending) | BUF (58.1%) | -0.436999 / pending | 42.2 / pending |

## Methodology, evidence & limitations

1. **Fixed lines:** The 2026 Circa Million VIII contest PDFs supply each week's locked side spreads. The official entrant selections were independently parsed to cross-check all 136 pairings, including Week 6 Bears/Falcons **PK**.
2. **Model configurations:** Outright probability and total use the saved research `oof_stack` champion. The original comparison margin is `catboost::football_support_control`; all 23 archived annual-forward margin families are now scored separately and ranked on both ATS accuracy and Circa-style five-game card points. The 2026-ranking leaders are post-hoc diagnostics, **not** historically selected champions. They are not substituted into original Week 9 issues.
3. **Prediction lane:** Weeks 1–8 are annual-forward reconstructed model outputs, but historical feature-publication and possession timing is not authenticated; therefore they are **descriptive**, not proof of what was knowable or pickable then. Week 9 N056 owner issues were saved around 11:32 p.m. Pacific Nov. 7, before kickoff but after the contest deadline.
4. **ATS decision:** For home margin *m* and home Circa spread *s*, the model prefers home when *m+s>0*, away when *m+s<0*. Actual outcome replaces *m* with final home margin. Exact landing on the spread is a push.
5. **No false O/U:** Circa Million is ATS-only. Eight Week 9 games separately have Saturday [cross-book consensus totals](https://www.sharpfootballanalysis.com/betting/nfl-odds-picks-predictions/); no unverified totals are imputed for Weeks 1–8.
6. **As-of scoreboard:** Only officially marked **Final** games observed Nov. 8 afternoon Pacific are graded. At the snapshot, Texans–Chargers, Packers–Patriots, Buccaneers–Bears, and Bills–Vikings were not final. Rebuild to update after they finish.
7. **Not actual Circa standings:** No contest entry, submitted five-pick card, wager, or return-on-investment claim is associated with these studies.

**Provenance:** [N056/N057 owner result](../ACTUAL_N056_RESULTS_N057.md) · [official fixed lines JSON](./official_lines_2026.json) · [scored Week 9 finals JSON](./week9_final_scores_2026-11-08.json) · [reproducible build script](./build_report.py) · [build receipt](./build_receipt.json)

**Authenticated source N057 SHA-256:** `a56262862f3c7f93d38e55533fdd0a5fb9fc4ab3d5b2b50534ebea48ed415812`
