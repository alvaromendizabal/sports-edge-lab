# Football modeling: executable scientific core

This directory provides a small, offline reproduction of the **modeling methods and validation contracts** used in Sports Edge Lab. It includes chronological feature construction, exact identity joins, quarterback-history definitions, opponent-adjusted efficiency definitions, fixed nonlinear model families and probability/point/interval metrics.

The demonstration uses **entirely synthetic data**. Its results are not NFL/NCAAF performance, a reproduction of private-run scores, evidence of betting profitability, or proof that the private AWS workflow succeeds. Synthetic QB/efficiency feature columns exercise model interfaces; they do not represent measured football skill.

## Run it

From the repository root, with Python 3.12:

```bash
python -m venv .venv-modeling
. .venv-modeling/bin/activate
python -m pip install -r modeling/football_v058/requirements.txt
python -m unittest discover -s modeling/football_v058 -p '*_tests.py' -v
python modeling/football_v058/run_demo.py --output /tmp/football_v058_demo.json
```

On Windows, activate the environment with `.venv-modeling\Scripts\Activate.ps1` in PowerShell and select an appropriate local output path. Installing dependencies may access the package index. Once installed, tests and the demonstration require no AWS account, credentials, provider subscriptions or network access. The demo explicitly blocks outgoing socket connections.

The unit suite includes **four small synthetic model fits**. The demonstration performs **nine synthetic fits**: HGB and MLP for NFL-shaped win/margin/total tasks, and MLP for college-shaped win/margin/total tasks. Training uses synthetic seasons through 2021 and evaluates synthetic 2022 events. Release-time and game-disjointness checks run before fitting. The JSON report contains split sizes, input widths, timestamps, metrics, dependency versions and explicit limitations.

## Model definitions

| Family | Fixed specification | Training controls |
|---|---|---|
| Histogram gradient boosting | 100 iterations, up to 15 leaves, depth 5, minimum 30 samples per leaf, learning rate 0.05, L2 5, 63 bins | No early stopping or random validation split; seed 5801 |
| Multilayer perceptron | Input → 32 tanh → 16 tanh → one logistic/identity output; Adam, learning rate 0.001, alpha 0.01, batch 64 | Input and regression-target scalers fitted on training rows only; no early stopping or random validation split; seed 5801 |

The MLP research default is **200 one-epoch `partial_fit` updates**. The demonstration explicitly uses **eight fixture epochs** to keep the smoke workflow small; the family tests use 41 classifier fixture epochs for progress callbacks and the full 200 regression epochs to exercise the runtime path. These overrides are recorded. The demo does not establish model convergence or real-data performance.

Small tabular samples can favor simple linear models. Nonlinear capacity is a testable hypothesis, not an automatic improvement. Random initialization is pinned; numerical reproducibility is scoped to the pinned environment and hardware, not promised bit-for-bit across arbitrary platforms.

## What is available

- `data.py`: exact schedule normalization, delayed prior-game features and chronological partitions.
- `efficiency.py`: raw football efficiency definitions and delayed opponent adjustment. NFL play-yardage and college drive-yardage definitions are intentionally distinct.
- `qb_features.py`: exact GSIS joins and last-observed dominant-passer history. This is **not an upcoming-starter detector**; ambiguous ties remain unknown.
- `families.py`: fixed HGB/MLP implementations, training-only scaling and checked prediction interfaces.
- `metrics.py`: log loss, Brier, ROC AUC, calibration bins, MAE/RMSE, bias, paired season-week uncertainty and chronological residual intervals.
- `experiments.py`: readable research comparison and promotion-gate definitions. Functions that consume frozen owner baseline files require the owner handoff and are **not exercised by the public demo**.
- `common.py`: atomic JSON output and fingerprint/hash-checked local checkpoints.
- `fixtures.py`, `family_tests.py`, `public_tests.py`, `run_demo.py`: synthetic reproducibility and safety checks.

Probability discrimination, calibration and point accuracy are separate questions. A low log loss is not a profitability claim. Empirical residual intervals carry no guaranteed coverage claim. Historical source publication dates remain unknown unless independently documented; lagging revised archives does not reconstruct original historical availability.

## Data and execution boundary

This directory contains no raw provider payloads, private account configuration, asset pins, subscription credentials, real prediction caches or trained model weights. It does not download football data or load remote pickled objects. Local joblib round-trip tests only deserialize objects generated within that same test process.

A full private AWS execution requires the owner’s self-contained handoff, authorized data access, hash-pinned caches and accepted baseline evidence. This public demonstration does not replace those controls. Provider availability is not permission to redistribute data; each source’s license and terms must be checked before independent acquisition, use or publication. No additional data or software license is granted by this directory.

## Primary references

- [Histogram gradient boosting](https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting)
- [Multilayer perceptrons](https://scikit-learn.org/stable/modules/neural_networks_supervised.html)
- [Model evaluation and scoring](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html)

CI runs the same tests and synthetic demonstration on Python 3.12. A configured workflow is not evidence of a successful hosted CI run; its actual run status must be inspected separately.
