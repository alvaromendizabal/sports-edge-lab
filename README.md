<p align="center"><img src="docs/assets/masthead.svg" alt="Sports Edge Lab — probabilistic forecasting, scientific evaluation, reliable ML systems" width="1100"></p>

NFL and FBS forecasting built around a difficult engineering question: can a model add information beyond the market, and can every result survive an audit?

Designed and implemented by [Alvaro Mendizabal](https://github.com/alvaromendizabal). The project connects source acquisition, information-time contracts, four native ML frameworks, chronological experiments, immutable forecasts and recoverable AWS execution. NFL and FBS are the modeling focus; NBA and NCAA basketball share the data infrastructure.

[Start the review](docs/REVIEW_GUIDE.md) · [Current evidence](docs/CURRENT_EVIDENCE.md) · [Model card](docs/MODEL_CARD_CURRENT.md) · [System design](docs/SYSTEM_DESIGN.md) · [Run the example](examples/review_lab/README.md)

Latest execution, October 26: V119 stopped at a source-provenance gate after 1,058 owner checks passed. It made zero real fits and produced no new model result. The [recovery case study](docs/CASE_STUDY_PROVENANCE.md) explains the missed multi-parent integration case and provides a separate runnable synthetic demonstration. Prior accepted models and the scorecard below remain unchanged.

## A five-minute technical review

| Inspect | What it demonstrates |
|---|---|
| [Credential-free ML example](examples/review_lab/README.md) | Real fitting on invented data, chronological separation, exact-cohort scoring, leakage rejection and zero-fit reentry |
| [Executed review notebook](notebooks/engineering_review.ipynb) | Reproducible synthetic results beside clearly separated, sanitized real-run aggregate evidence |
| [Current evidence export](docs/evidence/2026-10-25.json) | Three campaigns, multiple training origins, raw MARKET, controls, all four frameworks and retained references |
| [System design](docs/SYSTEM_DESIGN.md) | Data/model/decision contracts, lineage, failure states and recovery |
| [Published scientific implementations](docs/PROJECT_SCOPE.md) | Preserved fitting, source-adjudication, uncertainty and interruption tests from earlier research stages |
| [Failure-to-recovery case study](docs/CASE_STUDY_PROVENANCE.md) | Multi-parent provenance, content-pinned relocation, rejection tests and honest incident classification |

<p align="center"><img src="docs/assets/evidence-overview.svg" alt="Current matched-cohort log loss: NFL MARKET 0.660022 and retained reference 0.624093; FBS MARKET 0.474843 and retained reference 0.465519. Exposed monitoring, not prospective profit." width="1100"></p>

The graphic above is generated from the same aggregate export as the [evidence explorer](docs/review/index.html). Download and open that self-contained HTML file locally; GitHub's file viewer displays its source. It has sport, campaign and proper-score selectors, responsive tables and no external requests.

## Current evidence, with the boundaries attached

The October 25, 2026 publication incorporates completed V117R1 modeling and V118 current serving. It preserves negative results and distinguishes predictive scores from economic outcomes.

| 2026–27 monitoring cohort | Games | MARKET log loss | New joint challenger | Strongest retained reference |
|---|---:|---:|---:|---:|
| NFL | 77 | 0.660022 | 0.647299 | **0.624093** |
| FBS | 301 | 0.474843 | 0.473819 | **0.465519** |

Lower is better. These are matched, non-tied games with included kickoffs through October 15, not complete seasons. Retained references were selected on exposed outcomes. The new challenger failed both historical qualification gates; the NFL monitoring panel has only six weekly blocks. These results do not establish prospective profitability.

[All 2024–25, 2025–26 and 2026–27 comparisons](docs/CURRENT_EVIDENCE.md) include Brier scores, different update policies and separate metric-specific references. MARKET means archived bookmaker consensus after paired de-vig—not an executable quote, a closing line, or Kalshi.

## What the latest completed serving run proved

| V118 owner result | Verified outcome |
|---|---|
| Verification | 927 tests passed |
| Current research issuance | 2,058 model rows across 39 games; rows are not independent games |
| Model reuse | Zero new real fits |
| Final source-read-to-issue interval | 6.282 seconds, versus 245.440 seconds in an earlier execution; an observational comparison, not a controlled benchmark |
| Action admission | Zero paper actions and zero actual wagers; all named sportsbook quotes were stale |
| Data integrity | 105/105 NFL PBP coverage; 549/566 detailed FBS summaries; 17 kickoff conflicts remain quarantined |

Reliable abstention is part of the system. A completed forecast pipeline does not turn a stale price or an incompatible settlement target into a valid decision.

## Engineering decisions worth inspecting

- Keep publication, observation, revision, label availability and decision clocks distinct.
- Fit preprocessing and learned representations inside their chronological training boundaries.
- Compare new systems with raw MARKET, matched controls and the strongest retained references on identical games.
- Preserve source bytes, model identity and accepted forecasts through recovery.
- Separate successful execution from positive science and deployment readiness.
- Validate source, environment, notebooks and resource guards before expensive owner work.

[Architecture and trade-offs](docs/SYSTEM_DESIGN.md) · [Research protocol](docs/RESEARCH_PROTOCOL.md) · [Current data gaps](docs/CURRENT_EVIDENCE.md#data-and-operational-readiness)

## Reproduce the public review

Python 3.11+; no credentials, cloud account or third-party packages are required for the core example. Run from the repository root:

```bash
python -m unittest discover -s examples/review_lab/tests -v
python -m examples.review_lab --output /tmp/sports-edge-review
python -m examples.review_lab --output /tmp/sports-edge-review
python -m examples.review_lab.build_review --check
python -m examples.review_lab.provenance
```

The second invocation verifies and reuses the accepted synthetic report with zero new fits. A different seed, changed implementation or corrupted artifact is rejected. The optional notebook uses Jupyter; see its [environment and reproduction instructions](examples/review_lab/README.md).

The public-review workflow runs the synthetic suite on Python 3.11/3.12, checks selector behavior, and executes the notebook in a separate kernel with saved-output validation. It complements the retained [scientific modeling](.github/workflows/modeling-quality.yml), [acquisition guards](.github/workflows/ingestion-guards.yml) and [repository hygiene](.github/workflows/repository-hygiene.yml) workflows. Consult the actual Actions result for the published commit. Earlier implementations and dated evidence remain intact.

## Public code, private research assets

Public material includes source contracts, evaluation mechanics, synthetic fitting, tests, notebooks, architecture and aggregate research results. Licensed/raw observations, individual forecasts, trained production weights, exact active feature transformations, tuning and live decision configuration remain private. The synthetic example verifies engineering behavior; it does not reproduce the private football scores.

[Publication boundary](docs/PUBLICATION_BOUNDARY.md) · [Historical evidence and maintained paths](docs/PROJECT_SCOPE.md) · [Evidence-based repository review](docs/REPOSITORY_REVIEW.md)
