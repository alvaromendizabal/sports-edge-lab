# Numerical certification and partial-work accounting

The [invented numerical-recovery example](numerical_recovery.py) keeps solver termination, primal feasibility, an explicit convex optimality certificate and predictive qualification separate. It rejects counting imported completed units as new work and preserves failed attempts. Run `python -m examples.review_lab.numerical_recovery`; read the [actual V130 incident](../../docs/NUMERICAL_RECOVERY_INCIDENT.md) for the boundary between this example and the actual failed V130/V131 owner executions. No football data, private objective, network call or actual order is used.

# Transactional prospective state

The [prospective-state example](prospective_state.py) adds an append-only SQLite journal with atomic native-week capital reservation, immutable decision reentry and separate settlement events. Run `python -m examples.review_lab.prospective_state`. Its 22 targeted tests cover cutoff timing, native quote age, budget rollback, duplicate exposure, pre-kickoff outcome rejection and tamper detection. Read the [limitations and operational boundary](../../docs/PROSPECTIVE_STATE_MACHINE.md): injected clocks and external evidence flags are test inputs, not independent historical attestation or venue verification. Every event and financial result is invented.

# Persisted portfolio evidence

The [portfolio evidence example](portfolio_evidence.py) extends the existing decision ledger with a persisted byte commitment, explicit unavailable/display/executable-price classes and same-budget venue alternatives. Run `python -m examples.review_lab.portfolio_evidence`. The [review guide](../../docs/PORTFOLIO_EVIDENCE.md) explains why a local hash is not a historical timestamp attestation and why a displayed price cannot establish realized profit. All events and monetary results in this example are invented.

# V126 serving-lineage review

The new [serving-lineage mechanism](serving_lineage.py) binds immutable selected, served and recorded policy identities. It rejects hash substitutions, forward-season selection, backdated availability, duplicate league policies and reference/model count confusion. Its invented-data demonstration is separate from the sanitized actual [V126 owner receipt](../../docs/evidence/2026-10-27-v126-execution.json).

The [case study](../../docs/CASE_STUDY_SERVING_LINEAGE.md) explains what the owner correction established and what remains unproved. Reconcile the receipt and run the demonstration with `python -m examples.review_lab.serving_lineage` from the repository root. All lineage tests run in the existing unittest discovery command. No network calls, real football fitting or actual orders occur in these examples.

The current notebook now extends the retained research narrative with selection-to-serving verification and a separate V126 owner-status section. Older counts below describe earlier notebook stages; the saved execution receipt reports the current cell count.

# Public review — new historical-selection and decision mechanisms

Two additional standard-library examples connect the existing chronological training, provenance, factorial and distribution demonstrations:

```bash
python -m examples.review_lab.historical_selection
python -m examples.review_lab.decision_replay
python -m examples.review_lab.build_current_review --check
node examples/review_lab/tests/test_current_selectors.cjs
```

The historical example rejects forward outcomes and preserves the frozen choice even when another model appears better in monitoring. The paper ledger accepts a complete outcome-free candidate universe, native league week and evidence clocks; settlement is a separate operation. Both use invented data and illustrative rules, not the private football selection or staking recipe.

The [current explorer](../../docs/current/index.html) exposes 57 exact panels and 9,756 sanitized V125 scorecards. Its 2026 panels use stable identifiers with no winner emphasis. Historical comparison emphasis is computed over the full exact panel before a search filter is applied. No individual forecasts or execution-quality historical profit are provided.

The reproducibility instructions below remain valid for the preserved mechanisms. The executed notebook extends them with selection, ledger and current evidence validation cells.

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

The committed [notebook](../../notebooks/engineering_review.ipynb) has twenty-two code cells, preserving the earlier research narrative and subsequent executed sections, recorded using in-process IPython. It discovers the repository root, trains only on synthetic events, renders the aggregate score table separately, displays an inline SVG, demonstrates two-parent recovery and inspects the sanitized owner-run status. The final cell verifies that these claims remain distinct. The runner records its execution mode and reopens the saved notebook to validate execution order, rich formats and completion.

```bash
python -m pip install -r examples/review_lab/notebook-requirements.txt
python -m examples.review_lab.execute_notebook --output /tmp/sports-edge-engineering-review.ipynb
```

A fresh independent environment is preferable for review. Package installation is optional; it is not needed by the core command or test suite.

The default runner executes cells in-process and captures their rich outputs. Use `--mode kernel` for a separate Jupyter kernel, or open the notebook and run all cells normally. The earlier fifteen-cell version passed separate-kernel execution during the basketball extension. The current twenty-two-cell notebook is reexecuted in-process for this release; local separate-kernel startup is blocked by the authoring environment IPC restriction. The public-review workflow also runs this mode independently on GitHub; its actual Actions result establishes hosted success.

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

## Results dashboard and independent stage outcomes

Open [the self-contained dashboard](../../docs/dashboard/index.html) in a browser. It renders sanitized V131 owner facts, matched FBS historical comparisons, prior V129 historical scores and clearly dated monitoring. Its four invented workflow scenarios are generated by executable Python, not hard-coded success claims.

```bash
python -m examples.review_lab.fault_isolation
python -m examples.review_lab.build_status_dashboard --check
node examples/review_lab/tests/test_dashboard.cjs
```

The [workflow contract](../../docs/FAULT_ISOLATION.md) documents snapshot isolation, failure boundaries, public-data limits and reproduction. Hosted CI additionally exercises the dashboard in Chromium at desktop/mobile widths. Research completion never changes the frozen fixture policy; successful reference serving never grants paper eligibility.

## Persistent recovery across invocations

The [eight-stage journal](recoverable_stages.py) uses immutable local receipts on invented inputs. It preserves forecast/finance identities after research failure, executes only unfinished stages on resume, and reenters with zero work. Run `python -m examples.review_lab.recoverable_stages`; see [contracts and limits](../../docs/RECOVERABLE_OPERATIONS.md). The latest dashboard separately records actual V132 completion, failed predictive qualification, 83 issued MARKET references and zero qualified financial executions.
