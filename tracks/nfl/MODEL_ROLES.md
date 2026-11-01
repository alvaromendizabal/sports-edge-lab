# Reading a model comparison without inventing a winner

A row with the smallest historical error answers, “Which saved candidate scored lowest on these games?” It does not establish that the candidate was selected before the outcomes, improves future predictions, or has profitable prices. A frozen selection requires its own authenticated historical decision record. When that record is absent, the selected champion remains unknown.

The small, credential-free [model_roles.py](model_roles.py) example makes three useful distinctions executable:

- Missing challenger results remain `None`; they never become a zero error score.
- Equal game counts are insufficient. Comparisons require identical game identifiers and per-game reference values. A shared average market value can still hide different inputs.
- A retrospective minimum is descriptive and cannot become a selected champion or promotion. The exposed 2026 season is monitoring only and generates no candidate ranking.

All example names and numbers are invented. This is an evidence contract, not a fitted model, real provider comparison, prediction, or betting recommendation. It uses no credentials or network, performs no fits, and places no orders. Matching reference numbers also does not prove a common original quote timestamp; source and availability clocks remain separate requirements.

Run the example and behavior tests from the repository root:

```bash
python tracks/nfl/model_roles.py
python -m unittest discover -s tracks/nfl -p 'test_*.py'
```

The tests cover unequal cohorts with equal counts, swapped per-game references with equal averages, unknown results, monitoring exclusions, tied descriptive minima, invalid numbers, and zero fit/order behavior. The example supplies no uncertainty interval: a confidence interval for a previously fixed candidate is not automatically adjusted for choosing the minimum after seeing outcomes.

## Check reporting coverage before comparing scores

A perfectly calculated report can still omit the model a reader wanted to see. `reporting_inventory(expected, reported)` requires a separate, explicit inventory of model-season identities. It accounts for each declaration before any scoring comparison:

| State | Meaning |
|---|---|
| `MISSING_REPORT_ROW` | An expected model is absent from the report; its score stays unknown. |
| `REPORTED_NO_AUTHENTICATED_SCORE` | The report contains the model, with a missing score explicitly recorded. |
| `REPORTED_SCORE` | A score is present; the inventory helper does not verify, rank or promote it. |

Duplicate identities and unlisted reported models raise an error. The caller must declare a MARKET reference, frozen candidate, weekly-updated model or unresolved role, together with its training policy. A current-season score from a policy using current-season labels remains visible and is marked ineligible under the frozen-season rule. Missing lineage stays unresolved; it is not converted into a frozen candidate.

Declared aliases group only when the season, target, prediction-vector digest, exact game-cohort digest and reference digest all match. Missing identity fields cannot establish alias independence; equal average scores or equal model names cannot do so either. This helper does not read the underlying bodies: digest declarations require independent source authentication. The full declared identity count is not a statistical count of independent hypotheses.

The command above prints an invented comparison and an invented inventory containing both kinds of missing result. The inventory never chooses a champion, ranks current-season scores, changes model weights or issues a forecast. An explicit expected list is a reporting contract, not proof that all private storage has been discovered. Use the existing matched-cohort comparison only after the inventory and source checks are complete.

The current public review remains a separately dated aggregate snapshot. This addition demonstrates reporting completeness using invented fixtures; it makes no claim of a new accepted owner study, improved forecast accuracy or wagering return.

