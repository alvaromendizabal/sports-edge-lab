# Football V060 — native boosting and strict source parsing

This public core exposes the prepared native XGBoost/LightGBM/CatBoost benchmark and its linear control, plus conservative official drive-chart parsing. **No V060 real-data result has executed or been accepted yet.** Public synthetic checks are separate from owner AWS execution and data rights.

## Run the public checks

From the repository root with Python 3.12:

```bash
python -m venv .venv-boost
. .venv-boost/bin/activate
python -m pip install -r modeling/football_v060/requirements.txt
python -m unittest discover -s modeling/football_v060 -p '*_tests.py' -v
```

The pinned `xgboost-cpu` distribution avoids requesting CUDA dependencies. Windows PowerShell uses `.venv-boost\Scripts\Activate.ps1`. Installation may contact the package index. The tests use invented in-memory inputs and do not load football archives, request provider data or require AWS credentials.

The booster test class performs **exactly 12 tiny synthetic fits** (four families × three targets) once, then reuses them across assertions. Classifier fixtures exercise the full 200-round ceiling; regression fixtures use an explicitly recorded eight-round override. The real planned experiment has **84 new fits**, not 12: 72 native boosters plus 12 fresh FBS linear controls. Public tests are not evidence of that real queue executing.

## What is controlled

| Contract | Implementation |
| --- | --- |
| Fixed CPU benchmark | Two threads, declared seeds, shallow trees, regularization and a 200-round ceiling. No sweep or evaluation-driven early stopping. |
| Equivalent representation | Caller supplies the same finite numerical features in exact name/order. This module neither chooses features nor invents labels. |
| Linear preprocessing | Training-only standardization; no target scaling. Tree inputs remain unscaled. |
| Chronological responsibility | The caller must supply already ordered, eligible partitions. CatBoost preserves order with `has_time=True`; that flag alone does not make data point-in-time valid. |
| LightGBM stopping | A permitted-split exhaustion may produce fewer trees; planned and completed iterations are recorded separately. |
| Source identity | Exact teams, date and final score; no guessed home/away identity or unknown positive-play outcomes. |
| Rendered evidence | Structured drives must agree with actual counted DOM rows and hashes. Source acquisition alone is not validated drive coverage. |
| Time provenance | Observation time does not become original publication time. Unknown source publication remains null. |

The prepared owner's college target rows are FBS-versus-FBS; inherited prior-opponent feature history may still include FCS context. Accepted college predictions retain older mixed-cohort training, so the new FBS linear control isolates that change. New captures are staged separately and do not alter frozen benchmark features.

## Public-suite boundary

This public subset retains booster checks, synthetic structured-HTML parser tests and classic-parser period arithmetic tests. Actual publisher HTML and the owner-only exact-source fixture tests are omitted. The full private artifact also tests source caches, finite capture budgets, provider stops, AWS persistence, notebook execution and real source receipts. A public subset passing does not imply those private checks ran.

No private account configuration, bucket names, object pins, source payloads, provider keys, trained weights or private executable archive is included. There is no collector or AWS launcher in this directory.

## Research status

[Current model card](../../docs/MODEL_CARD.md) · [Feature priorities / framework registry](../../docs/FEATURE_STRATEGY.md) · [V059 actual evidence](../../docs/status/football_v059/README.md).

Earlier completed methods include sklearn HGB, sklearn MLP and Gaussian score states. These are distinct from the prepared native boosters. PyTorch and TensorFlow have no verified project execution. Model frameworks provide capabilities; source quality, decision-time information and controlled evaluation determine whether forecasts improve.
