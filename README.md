# NFL Edge Lab

**Probability forecasting · historical sports markets · reproducible ML engineering**

NFL Edge Lab is an applied machine learning research project for estimating NFL game outcome probabilities, point margins, and score distributions, then comparing forecast estimates against observable historical betting prices. The emphasis is on **calibration, temporal correctness, explainability, reproducible evaluation, and system design** rather than unsupported claims of profitable betting.

> **Status — Phase 0: data provenance and acquisition.** This starter contains a tested, dependency-free acquisition runner, a data-quality gate, and an explicit separation of permissible pregame metadata from postgame outcomes. The complete source archive is acquired only when the runner is executed in a network-enabled environment.

## Problem and design

NFL game forecasts are easy to overfit and hard to validate as actual wagering decisions. We are building a research pipeline that can answer three independently testable questions:

1. Can we reliably estimate out-of-time home-win probability, point-margin distribution, and total-points distribution?
2. Does football-only information add predictive value beyond a carefully reconstructed sportsbook consensus?
3. Would any apparent edge survive historically available prices, vig, pushes, bookmaker limits, timing, and uncertainty?

**Our standards:** strict week-by-week as-of timestamps, no label contamination, season-held-out evaluation, source-content hashing, and auditable acquisition ledgers.

## First acquisition

The Python acquisition runner uses only the standard library. It retrieves public nflverse source assets without requiring an odds subscription or cloud credentials. Start from this repository in a network-enabled AWS SageMaker terminal:

```bash
python3 -u tools/acquire_nfl_data.py --seasons 1999:2025 --data-root /home/sagemaker-user/nfl-edge-lab-data --return-dir /home/sagemaker-user --workers 4 --max-seconds 1500 --max-download-gb 5
```

For a smaller proof run use `--seasons 2023:2025`. The same runner is also packaged in the release as a `.pyz` ZIP application. Running again is safe: valid previously acquired source files are reused, and incomplete `.part` files are eligible for HTTP Range resumption.

Outputs are intentionally stored **outside this Git repository**:

```text
nfl-edge-lab-data/
├── raw/nfldata/                    # canonical all-season schedules + line archives
├── raw/nflverse/pbp/season=YYYY/    # detailed play-by-play, 1999+
├── raw/nflverse/team_stats/season=YYYY/
├── raw/nflverse/player_stats/season=YYYY/
├── raw/nflverse/rosters/season=YYYY/
├── raw/nflverse/injuries/season=YYYY/
├── curated/pregame_metadata.csv     # excludes postgame fields
├── curated/market_reference_NO_ASOF.csv  # quote time UNKNOWN
├── curated/POSTGAME_OUTCOMES.csv    # targets NEVER used as features
└── manifests/                     # hashes, source URLs, quality and coverage
```

Every execution produces exactly one uniquely named **return ZIP** in the specified return directory. It contains acquisition receipts, coverage, data quality, and test results, not bulky or potentially licensed raw datasets.

### Available CLI controls

| Flag | Purpose |
|---|---|
| `--seasons 1999:2025` | Inclusive season range, or explicit list `2021,2023,2025` |
| `--self-test` | Six local tests; no external network |
| `--plan` | Display source URL manifest; no downloads |
| `--workers 4` | Conservative concurrency; valid range 1–8 |
| `--max-seconds 1500` | Bounded run with graceful return report |
| `--max-download-gb 5` | Global download budget |
| `--data-root ...` | Resumable source archive outside Git |
| `--return-dir ...` | Directory for one unique return ZIP |

## Explicit leakage boundary

`games.csv` contains game results, actual quarterback starters, and observed weather **alongside** pregame schedule fields and archived market numbers. They are not interchangeable in a model input table. The runner splits them into distinct files and includes a strict results consistency test. Likewise, archived reference spreads do **not** become day-before betting quotes just because they were originally determined before kickoff.

The separate `closing_lines.csv` currently includes 2006–2018 games, while `initial_lines.csv` has 2021 data. These are **not** a continuous archive of bookmaker snapshots. The official paid The Odds API history can supply timestamped sports-book observations dating from 2020, but will be considered only after we audit the free source.

## Research roadmap

**Phase 0 — Acquisition:** audit NFL schedules and betting market coverage; archive PBP, player/team weekly statistics, rosters, injury history; produce source/field availability matrix.

**Phase 1 — Pregame features:** independent team-strength and Bayesian Elo ratings; rolling opponent-adjusted EPA and success rates; rest/travel and matchup factors. Every statistic uses only matches completed before prediction time.

**Phase 2 — Calibration:** logistic regression, LightGBM, XGBoost, CatBoost, Bayesian distributions, cross-fitted ensemble, out-of-time Brier and log loss; weekly and seasonal performance auditing.

**Phase 3 — Market evaluation:** reconstruct *specific* sportsbook prices available at T−72h, T−24h, T−6h and near kickoff; evaluate price availability, hold, no-vig probabilities, ROI, CLV, confidence intervals and uncertainty.

**Phase 4 — Product:** interactive matchup intelligence, interpretable feature explanations, simulated bet-slip audit, versioned reproducible weekly forecasts, and a public employer-facing demo.

## Rights, provenance, and limits

Published upstream sources are attributed to nflverse and underlying rights holders; own ingestion code does not grant permission to redistribute third-party datasets. Consult `docs/DATA_CATALOG.md` before sharing data or commercializing anything. Proprietary odds, private keys, large data, model artifacts, and local run returns must not be committed.

NFL Edge Lab is an analytical/research software project. It does not guarantee profitable bets or constitute financial advice. No wagering performance claim is made without genuinely out-of-sample, point-in-time evidence.