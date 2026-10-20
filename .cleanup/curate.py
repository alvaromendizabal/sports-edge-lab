"""Clean obsolete packaged collectors, never the active scheduled source or AWS data."""
from pathlib import Path
import hashlib,re,shutil,subprocess
from urllib.parse import unquote,urlsplit
R=Path.cwd();BASE='b247d233fee72734c868e07e24b4de67704e2a2a'
if subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()!=BASE:raise RuntimeError('Main advanced; reconcile first')
subprocess.run(['git','diff','--exit-code',BASE,'HEAD','--','.',':(exclude).cleanup',':(exclude).github/workflows/zz-sweep-snapshot.yml',':(exclude).github/workflows/zz-sweep-apply.yml'],check=True)
active={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'tools/current_snapshot_v043').rglob('*') if p.is_file()}
retired=['tools/current_snapshot_v026','tools/football_current_v034','tools/football_finish_v039','tools/football_quality_v044','tools/football_quality_v045','tools/football_readiness_v042','tools/football_refresh_v041','tools/football_validation_v046','tools/football_weekend_v049','tools/ngs_availability_v040','tools/odds_only_v037','tools/odds_only_v038','tools/shooting_continuation_v021','tools/shooting_continuation_v024','tools/history','docs/history','infrastructure/current_snapshot_schedule/render_schedule.py']
tracked=subprocess.check_output(['git','ls-files','-z'],text=True).split('\0')
removed={n for n in tracked if n and any(n==p or n.startswith(p+'/') for p in retired)}
for name in retired:
    p=R/name
    if p.is_dir():shutil.rmtree(p)
    elif p.is_file():p.unlink()
    else:raise ValueError('Inspected retirement path missing: '+name)
for p in R.rglob('*.md'):
    if '.git' in p.parts or '.cleanup' in p.parts:continue
    s=p.read_text()
    def replace(m):
        u=urlsplit(m.group(1))
        if u.scheme or u.netloc or not u.path:return m.group(0)
        try:name=str((p.parent/unquote(u.path)).resolve().relative_to(R))
        except ValueError:return m.group(0)
        if any(name==old or name.startswith(old+'/') for old in retired):
            kind='blob' if name in removed else 'tree'
            return ']('+f'https://github.com/alvaromendizabal/sports-edge-lab/{kind}/{BASE}/{name}'+('#'+u.fragment if u.fragment else '')+')'
        return m.group(0)
    s=re.sub(r'\]\(([^\s)]+)\)',replace,s)
    if p.name=='FOOTBALL_READINESS_V042.md':s=s.replace('](status/current_guard_v043/)','](../tools/current_snapshot_v043/README.md)')
    p.write_text(s)
(R/'README.md').write_text('''# Sports Edge Lab

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
''')
(R/'docs/PROJECT_SCOPE.md').write_text('''# Maintained source and reproducible review

This active project separates three surfaces: current acquisition, scientific
verification, and immutable records of earlier executions. Only the first two
require working launch code in the current checkout.

## Active components

| Path | Responsibility |
|---|---|
| `tools/*.py` | Provider clients, quotas, source validation, inventory and recovery; each client keeps its offline guards |
| `tools/current_snapshot_v043/` | Source snapshot corresponding to the currently scheduled AWS collector; preserved unchanged |
| `modeling/football_v058` through `modeling/football_v066` | Executable scientific controls, validation and recovery tests for the published modeling evidence |
| `docs/status/` | Original sanitized acceptance/rejection and preparation records; not a list of deployed models |
| `catalog/`, `config/`, `tracks/` | Source/identity catalog and five-track acquisition scope |

A model family's presence in verification code does not imply promotion. Consult
[the model card](MODEL_CARD.md) for accepted references and exact comparison scope.
Necessary comparison controls stay because the final decision depends on them.

## Run an isolated fitting demonstration

For the exact dependencies and supported Python version, follow the
[V066 README](../modeling/football_v066/README.md). That version's tests exercise
strict-FBS fallback, interruption, verified state reuse and publication identity.
The [V058 demonstration](../modeling/football_v058/README.md) provides a smaller
chronological fitting example. Both use synthetic input; no provider credentials,
private source data or running AWS space are needed.

All nine retained modeling jobs now run on each pull request. The acquisition gate
checks every surviving client and the active current-snapshot package offline.
Repository hygiene checks local document/notebook file links and rejects temporary
runtime/cache files. Scientific result gates have not been relaxed to achieve a
cleaner directory.

## Historical source and active AWS

Superseded packaged collector versions are available at the immutable commit links
in [execution provenance](EXECUTION_SOURCE_VERSIONS.md), not copied into new archive
folders. The original S3 source snapshots, scheduled processing configuration,
private data lake and experiment checkpoints are outside this GitHub pruning and
remain untouched. The obsolete v026 schedule-rendering helper is retired; this
publication does not recreate or update AWS infrastructure.

The repository's latest published modeling evidence may lag private AWS execution.
Dated results remain dated. Do not use an old README as permission to reopen a
rejected recipe, overwrite an accepted artifact or issue a new forecast.
''')
if not active or any(not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=digest for p,digest in active.items()):
    raise RuntimeError('Active v043 source changed')
print('Retired',len(removed),'legacy files; all',len(active),'active collector files unchanged')
