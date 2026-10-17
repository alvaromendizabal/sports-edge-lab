# Football V059 — dynamic score states and FBS data contracts

This public scientific core implements a fixed Gaussian team offense/defense model, its static control, exact FBS-versus-FBS scope selection and a conservative regulation-drive repair. It includes synthetic tests and a small offline demonstration. **V059 owner execution completed 16 real joint fits and eight FBS repairs; no task qualified. Public fixtures remain software checks, separate from those real results.**

## Reproduce the software behavior

From the repository root, with Python 3.12:

```bash
python -m venv .venv-state
. .venv-state/bin/activate
python -m pip install -r modeling/football_v059/requirements.txt
python -m unittest discover -s modeling/football_v059 -p '*_tests.py' -v
python modeling/football_v059/run_demo.py --output /tmp/football_v059_demo.json
```

Windows PowerShell activation is `.venv-state\Scripts\Activate.ps1`; select a suitable local output path. Package installation may contact the package index. Once installed, tests and the demo require no AWS account, credentials, subscription or network. The demonstration blocks outgoing socket creation.

The state test class performs **four tiny synthetic joint fits**, then checks the same results across mathematical and temporal cases. Repair/scope tests use invented local fixtures and perform no fits. The separate demo performs another **four synthetic joint fits**, with four training and four evaluation games per arm. Those counts are deliberately small software checks, not a model-quality evaluation.

The completed owner execution had **16 joint fits**: two tracks × static/dynamic × four chronological partitions. A joint fit produces three task outputs; it does not count as three independent fits.

## Method and control

The model jointly represents home and away scores using population scoring level, home advantage and separate team offense/defense states. Both arms have proper Gaussian priors and the same correlated observation likelihood. Predictions include means and covariance, margin/total transforms, a continuous win probability and a stated approximate tie/non-tie treatment.

The dynamic arm uses an Ornstein–Uhlenbeck transition with a fixed 365-day half-life and stationary team variance. The static arm sets process drift to zero. **Both arms still update from released earlier results**; static is not frozen posterior learning. Forecasts are constructed before consuming observations unavailable at their decision time, with no backward smoothing.

Settings are fixed heuristics, not an estimated paper reproduction: prior NFL/FBS population means are 22/27 points, observation score standard deviations 10/13, and residual score correlation 0.10. Complete settings and assumptions are embedded in `FIXED_CONFIG` and `METHOD_MEMO` in `state_model.py`. Proper priors yield a proper conditional posterior but do not make offense/defense parameters causal or uniquely identified by the likelihood alone.

The method is inspired by [Glickman and Stern's NFL dynamic linear model](https://www.glicko.net/research/nfl.pdf) and [their explanatory chapter](https://www.glicko.net/research/nfl-chapter.pdf). This implementation uses joint offense/defense Gaussian filtering with fixed hyperparameters; it does not reproduce their score-difference/MCMC procedure or inherit published performance.

## What is checked

| Contract | Examples |
| --- | --- |
| Forecast timing | Strict release-before-decision, no target/future observation, declared prequential updates, no backward smoothing. |
| Joint probability model | Positive covariance, exact margin/total transformations, noise inclusion, probability/tie arithmetic, Gaussian density and CRPS checks. |
| Model support | Negative-score probability mass is reported; continuous Gaussian scores are not silently truncated. |
| FBS scope | Both season-specific FBS flags required; NFL preserved; FCS history labeled separately and excluded from new target rows. |
| Regulation repair | Explicit noncontradictory overtime excluded before regulation validation; ambiguous periods and unknown positive-play results remain rejected. |
| Preservation | Accepted features and frozen labels remain unchanged; new finals are reported separately. |
| Public boundary | No owner pin manifest, cloud runtime, model weights or source payloads; explicit local pins are required for file-based integration. |

The release convention—result available 24 hours after kickoff—is an assumption, not verified historical publication time. NFL decisions precede kickoff by 24 hours and college decisions by one hour. The future college target is FBS versus FBS. Existing FCS archives remain historical context, without standalone FCS work.

## Distribution diagnostics

The implementation reports joint Gaussian negative log likelihood, marginal Gaussian NLL and CRPS for margin/total, and native 80%/95% interval coverage, width and interval score. It also reports marginal negative-team-score probability and a union bound, explicitly distinguished from an exact joint probability. These metrics describe the stated continuous model; football scores are discrete and future calibration is not guaranteed.

Point-only accepted baselines do not suddenly acquire an implied full predictive distribution. Their fair comparisons remain task metrics on identical games. The private experiment additionally checks log loss/Brier, MAE/RMSE, calibration, paired temporal uncertainty and frozen qualification gates.

## Data and code boundary

This directory contains no raw football records, credentials, private account configuration, asset pin files or trained weights. `scope_adapter.prepare_loaded_inputs` accepts caller-provided in-memory tables. Its file-based companion requires explicit local pins; the public copy never searches for a hidden owner configuration. Tests use synthetic sources and local temporary files only.

The original eight repair target IDs in `fbs_repair.py` identify the bounded historical hypothesis; identifiers do not supply the source data or permission to redistribute it. The public core does not download those games. Exact owner results require authorized source access, source hashes and the self-contained AWS handoff, which this demonstration does not replace.

Current actual evidence is the [V059 completed benchmark](../../docs/status/football_v059/summary.json), [metrics](../../docs/status/football_v059/metrics.json) and [accepted repair receipt](../../docs/status/football_v059/repair_completion.json). [Local V059 preparation](../../docs/status/football_v059/local_data_preparation.json) preserves its original pending status as dated history. CI configuration is not proof of a passing hosted run; inspect the actual workflow result.
