# Sports Edge Lab

**Football forecasting · Data integrity · Reproducible ML systems**

NFL and FBS football research for **win probabilities, point margins and game totals**.
The project connects historical source acquisition, player identity, availability-aware
features, chronological evaluation and recoverable AWS execution. Football is the
modeling focus; NBA and NCAA basketball share the active data infrastructure.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Evidence scorecard](docs/demo/index.html) ·
[Maintained code and run paths](docs/PROJECT_SCOPE.md)

## What the evidence supports

| System | Accepted repository evidence | Important boundary |
|---|---|---|
| NFL reference | V047: 16 team-history features; regularized logistic/ridge models | Prospective forecast outcomes are not established by retrospective accuracy |
| College reference | V048R1: 60 team-history and opponent-adjusted drive features | Strict FBS use has source-readiness restrictions; the older accepted training cohort was mixed |
| Historical evaluation | Exact same-game comparisons, training-only preprocessing and paired uncertainty | 2024–2025 seasons were repeatedly examined, not untouched confirmation |
| Data operations | Hash-bound source inputs, quarantine, budgets, checkpoint reuse and scheduled current capture | A downloaded record is not automatically a model-ready observation |

**No profitable betting edge or live-model promotion is claimed.** The dated
[V065 evidence](docs/status/football_v065/README.md) records 386 completed real fits,
393 normalized independent-source games, 81 disagreements and 66 missing accepted
comparisons. The [V066 package](docs/status/football_v066/README.md) is a separately
prepared fallback experiment in that publication, not an outcome invented by this
cleanup. AWS work may advance beyond the repository's published snapshot.

## Inspect the engineering

| Question | Implementation and review |
|---|---|
| Are provider calls safe and bounded? | [Paid acquisition](tools/acquire_paid_data.py), [mocked integration tests](tools/test_paid_acquisition.py) |
| Can incomplete or conflicting observations enter a model? | [Data contracts](docs/DATA_READINESS.md), [V065 validation](modeling/football_v065/README.md) |
| Can accepted work be resumed unchanged? | [Current scheduled source](tools/current_snapshot_v043/README.md), content and lease guards |
| How were candidate models compared? | [Model card](docs/MODEL_CARD.md), [fixed-feature booster comparison](modeling/football_v060/README.md) |
| Can I run a real public example? | [Synthetic fitting and validation](modeling/football_v066/README.md), [earlier chronological example](modeling/football_v058/README.md) |

The [offline scorecard](docs/demo/index.html) opens as a self-contained HTML file.
Public synthetic demonstrations fit actual controls and exercise leakage, state and
recovery checks. Their scores are **not actual football performance**. The modeling
workflow runs all nine retained verification jobs for every pull request, including
changes to documentation and acquisition packaging.

## Deliberately narrow publication

Current acquisition utilities and the **deployed v043 scheduled collector** remain.
Superseded one-time collector bundles, duplicate history READMEs and an obsolete
schedule-construction script are removed from the current tree. Links in dated
receipts point to their exact original Git commit; source attribution, rejected
results, scientific controls and private S3 evidence are not erased.

All five tracks remain: [NFL](tracks/nfl/README.md), [NCAAF](tracks/ncaaf/README.md),
[NBA](tracks/nba/README.md), [NCAAM](tracks/ncaam/README.md), [NCAAW](tracks/ncaaw/README.md).
College headline forecasts target **FBS versus FBS**; historical FCS opponents may
supply explicitly declared context. ACB is excluded. Private/licensed raw records,
credentials, fitted assets and exact active recipes are not added to GitHub.

This is active research. Repository cleanup does not stop scheduled acquisition,
reset an AWS workspace, delete checkpoints, change a frozen forecast, or reclassify
an unpromoted candidate as a final deployed model.
