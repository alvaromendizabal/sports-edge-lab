# V061 — NFL neutral-situation feature method

**Prepared method, not an executed V061 model result.** This public package reproduces feature construction and 23 synthetic/mathematical tests, with **zero model fits and zero provider calls**. The latest completed experiment remains [V060](../../docs/status/football_v060/README.md); accepted predictions remain unchanged.

## Run the public checks

From the repository root with Python 3.12:

```bash
python -m venv .venv-v061
. .venv-v061/bin/activate
python -m pip install -r modeling/football_v061/requirements.txt
python -m unittest discover -s modeling/football_v061 -p '*_tests.py' -v
```

Only dependency installation uses the network. The suite needs no credentials, AWS account, football downloads or private configuration. [Local verification receipt](../../docs/status/football_v061/public_checks.json) records the checked source hashes. A local pass is not evidence that hosted CI ran or the owner workflow completed.

## Football hypothesis

A team's recent passing and designed-run performance may contain information hidden by whole-game averages. The proposed representation adds **36 columns to the 16 baseline columns**, for **52 total**:

| Added feature group | Definition | Columns |
| --- | --- | ---: |
| Early-down efficiency and success | Dropback yards/play and success; designed-run yards/play and success | 4 measures × home/away × offense/allowed = 16 |
| Neutral play mix and explosiveness | Dropback share; dropback gains at least 20 yards; run gains at least 10 yards | 3 measures × home/away × offense/allowed = 12 |
| Observation controls | Prior games, early-down dropbacks/runs and neutral plays, each scaled | 4 controls × home/away = 8 |

All seven measures use regulation quarters 1–3, absolute pre-play score differential at most eight points, and more than 120 seconds left in the half. Early-down measures use first/second downs; success requires at least 40%/60% of yards to go, respectively. Explosiveness and play mix use all eligible neutral downs. Dropbacks include sacks and scrambles; designed runs exclude identified dropbacks. Administrative/penalty plays are excluded explicitly. These fixed definitions are hypotheses, not estimated optimal parameters or causal effects.

Histories use at most eight prior completed team games within 365 days, with a fixed 100-opportunity prior. Additive opponent adjustment uses strictly earlier release groups: games released simultaneously do not inform each other. Adjusted rate indices may fall outside [0, 1]; they are not probabilities. Source absence remains visible in observation controls, and cold starts use fixed fallback values.

## Information-time boundary

The method assumes each game's data becomes available at kickoff +24 hours and permits it only **strictly before** the next game's kickoff −24 hours. This is a conservative retrospective release rule, **not proof of original publication time**. Unknown source publication stays null, and `strict_point_in_time_verified` remains false. No upcoming-starter certainty, vendor EPA/WP, causal player value or live wagering readiness is claimed.

`aggregate_pbp` validates exact canonical game/team identity and denominators, removes identical duplicates, and quarantines an entire game when duplicate play keys conflict. `build_features` preserves upstream columns and returns features, audit and provenance separately. Tests cover temporal boundaries, future-outcome mutation, same-release isolation, cold starts, row-order invariance, malformed inputs and missing sources.

## Owner work remains separate

The prepared owner V061 workflow plans 24 real NFL fits: linear and one fixed XGBoost arm × three targets × four chronological folds. It also validates four previously cached FBS parser cases and permits at most 40 public ESPN attempts for 15 newly final FBS games, with zero paid/CFBD/CBBD/odds calls. Two additional historical secondary representations are verified locally (12/14 including the prior ten); the accepted AWS outcome remains V060's 10/14 until an actual V061 return is reviewed. Current-source capture is pending owner execution, and preparation made zero new source calls.

Those collectors, private source payloads, source pins and the owner execution configuration are **not included here**. This package tests the scientific mechanism; it does not start a job, fit a model, fetch a game or establish current coverage. See [feature strategy](../../docs/FEATURE_STRATEGY.md), [data readiness](../../docs/DATA_READINESS.md) and [research roadmap](../../docs/RESEARCH_ROADMAP.md).
