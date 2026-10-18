# V065 — current FBS drives and immutable settlement

**Preparation only; owner execution has not occurred.** This is a zero-fit data and evaluation milestone, with no new forecast issuance or model promotion.

## Four workstreams

1. Reuse exact successful cached data, then capture at most **one** current CFBD drive response from the existing subscription under durable shared attempt accounting and provider-denial stops. The source request is 2026 regular-season FBS-involving drives, not a historical backfill or new subscription. Response cap: 10 MB.
2. Normalize exact game/team/drive identities and compare all five original drive metrics against the complete 455-game primary reference. Invalid eligible rows quarantine the whole game. The required inventory cannot shrink when canonical rows are missing. Independently normalized data remains separate; even complete equality is review evidence and never automatic FBS60 insertion.
3. Evaluate only immutable forecasts that were actually issued before their original deadlines, using observed final labels and conservative release. Append settlement records; retain earlier versions and resume idempotently. The current two-game NFL forecast batch has **no matured outcomes** at preparation. No new forecasts are generated.
4. Report the source dependency, complete/unequal/missing coverage, pending outcomes, cost and next decision in an executed notebook and one return.

V064's canonical snapshot is unchanged. CFBD rows for later games absent from that snapshot are retained in the immutable raw capture but excluded from normalization until a separately verified canonical refresh. Publication remains null where unknown. Declared FBS/FCS opponent context is reported separately; new forecast/training targets remain FBS versus FBS.

## Why another source is not a silent repair

The owned three-response overlap covers 2,888 drives and 124 games. Strict validation retains 110 games: 107 FBS-versus-FBS and three declared opponent-context games. Fourteen games are quarantined after 19 invalid eligible rows. Of the 110 retained games, **81 match all five primary metrics and 29 disagree**; 345 games are missing/quarantined against the 455-game reference. Neither matching drive IDs nor a fresh timestamp establishes equivalent inputs. [Sanitized owned-source diagnostic](owned_source_comparison.json).

The nine unresolved college availability rows represent three people and need exact dated identity corroboration. No fabricated join, tracking entitlement, new subscription, provider-denial bypass or source-semantic replacement is part of this milestone.

**Final preparation passed:** 495 packaged offline tests with four tiny synthetic fits, 89 public pure-method checks (39 compatibility + 50 settlement), and 144 independent focused checks. An injected failure after append resumed with six immutable files unchanged; accepted reentry reused the same ZIP. The fixture executed six notebook cells, saved/reopened Plotly evidence and verified return CRC. These are synthetic preparation tests, not an owner AWS execution. [Final artifact hash, bounds and test receipt](preparation.json).

[Actual predecessor V064](../football_v064/README.md) · [Public pure methods and fixtures](../../../modeling/football_v065/README.md) · [Model card](../../MODEL_CARD.md).
