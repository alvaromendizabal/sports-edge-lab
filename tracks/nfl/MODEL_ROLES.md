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
