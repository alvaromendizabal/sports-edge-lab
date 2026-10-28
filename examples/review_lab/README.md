# A small, executable review of the engineering

[Project](../../README.md) · [Code](core.py) · [Tests](tests/test_core.py) · [Notebook](../../notebooks/engineering_review.ipynb) · [Recovery case study](../../docs/CASE_STUDY_PROVENANCE.md)

This example fits real models to invented data. It demonstrates chronological ML and recoverable execution without exposing the private football models, data or individual forecasts. It is intentionally small enough to inspect in one sitting.

## Run it

Use Python 3.11 or 3.12 from the repository root. The core example has no third-party dependencies and makes no network or provider calls.

```bash
python -m unittest discover -s examples/review_lab/tests -v
python -m examples.review_lab --output /tmp/sports-edge-review
python -m examples.review_lab --output /tmp/sports-edge-review
python -m examples.review_lab.build_review --check
python -m examples.review_lab.provenance
python -m examples.review_lab.factorial
node examples/review_lab/tests/test_selectors.cjs
```

The first run fits two regularized logistic models on 240 invented historical events, then evaluates the same 80 later events for a synthetic MARKET baseline, additive model and interaction model. The fixed educational settings are unrelated to the active research recipe. A synthetic interaction is present in the generator to make joint modeling inspectable; the example is not a test of whether real football features work.

The second invocation verifies the manifest and reuses the accepted result without fitting again. Changing the seed or implementation rejects incompatible reuse. Corrupting a file fails integrity validation. Choose a new output directory for a new experiment; the runner never repairs an accepted result by silently overwriting it.

## What the checks establish

- Canonical event identity and timezone-aware publication, observation, decision and label clocks.
- Training labels available before fitting and model availability before prediction.
- Exact cohort equality, with alignment by event ID rather than row position.
- Proper binary log loss and Brier scores, including boundary and invalid-probability cases.
- Deterministic training/evaluation and integrity-checked zero-fit reentry.
- Relocated bundles from two explicitly admitted parents; same-named artifacts retain distinct content identities.
- Rejection of omitted parents, changed manifests or bytes, forged clocks, path traversal and symlinks.
- Persisted notebook execution order, rich outputs and completion after the final figure.

The public example is not a production-grade artifact transaction protocol or a full sports pipeline. The broader historical [published implementations](../../docs/PROJECT_SCOPE.md) contain additional fitting, checkpoint and recovery mechanisms.

## Recovery under an explicit source contract

The [provenance example](provenance.py) creates two invented parent bundles, relocates them, reproduces an omitted-parent failure and recovers only after both pinned manifests are explicitly admitted. A later content change still fails. The code returns verified bytes and preserves observation timestamps; it does not search nearby folders or treat relocation as permission to widen access. This example makes no model fits or network calls.

This is an educational implementation for an immutable local cache, not a sandbox against concurrent hostile filesystem changes. It is separate from the private resolver. The [case study](../../docs/CASE_STUDY_PROVENANCE.md) explains the operational failure that motivated the exercise and why passing unit tests did not establish a completed experiment.

## Notebook

The committed [notebook](../../notebooks/engineering_review.ipynb) has fifteen executed code cells, recorded using in-process IPython. It discovers the repository root, trains only on synthetic events, renders the aggregate score table separately, displays an inline SVG, demonstrates two-parent recovery and inspects the sanitized owner-run status. The final cell verifies that these claims remain distinct. The runner records its execution mode and reopens the saved notebook to validate execution order, rich formats and completion.

```bash
python -m pip install -r examples/review_lab/notebook-requirements.txt
python -m examples.review_lab.execute_notebook --output /tmp/sports-edge-engineering-review.ipynb
```

A fresh independent environment is preferable for review. Package installation is optional; it is not needed by the core command or test suite.

The default runner executes cells in-process and captures their rich outputs. Use `--mode kernel` for a separate Jupyter kernel, or open the notebook and run all cells normally. Separate-kernel execution was reverified during the basketball extension: all fifteen cells completed, rich outputs persisted, and save/reopen plus final-cell checks passed. The public-review workflow also runs this mode independently on GitHub; its actual Actions result establishes hosted success.

## Rebuild the evidence page

```bash
python -m examples.review_lab.build_review
```

`docs/evidence/2026-10-25.json` is an aggregate export of audited owner results, not training data. The renderer checks its declared cohort inventory and produces `docs/review/index.html`. Open that self-contained file locally. It makes no external requests and discloses selected/exposed results, unresolved source gaps and zero admitted wagering actions.

## Evaluate feature families together

The [factorial evaluator](factorial.py) compares the complete base / A / B / AB system against MARKET and a retained reference on identical invented events. It includes paired weekly-block intervals and transparent complementary, redundant and harmful score fixtures. Read the [case study](../../docs/CASE_STUDY_JOINT_EVIDENCE.md) for why a favorable interaction alone does not establish market outperformance. The evaluator performs no fitting, network calls or wagering; its examples are separate from all real-football aggregate results.

## Generic finite-distribution mechanics

The `distribution` module accepts invented finite score laws. It does not fit a football model. It demonstrates normalized probability mass, authoritative log probabilities, conditional winner targets, mixtures before conditioning, marginal CRPS and explicit contract settlement. Twenty-two adversarial checks cover invalid supports, underflow, tied outcomes, impossible events and immutable inputs. These checks supplement the synthetic training and factorial examples.

The evidence explorer now separates conditional binary scores from joint distribution scores across all eight sport/origin panels. Its learned MARKET distribution baseline is labeled distinctly from raw MARKET consensus. All public example tests run in the same unittest discovery command above.
