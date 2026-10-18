# V063 preparation: cached repairs and existing-model serving

**Prepared, not an executed V063 AWS result.** [Sanitized preparation receipt](preparation.json) and [public serving adapter](../../../modeling/football_v063/README.md).

Local replay of three already captured official sources repairs the LSU–Mississippi State, Boise State–San Diego State and Maryland–Rutgers secondary drive representations. Selected coverage becomes **28/29 games**: **15/15 current** and **13/14 historical**, including the 12 previously accepted historical cases. UConn–Temple remains unresolved after the persisted source-host denial; no retry or alternate access path was used.

The merged 17-source queue yields 325 accepted regulation drives and 32 paired team-feature rows. Its 16 accepted games are separate from the 12 earlier accepted historical cases. PDF score/drive tables are checked against exact game identity and published play-by-play evidence. Conflicting unused source fields remain quarantined. Source chart play counts retain their own semantics, including field-goal attempts where the publisher counts them; they are not relabeled as pure scrimmage-play counts. These repairs do not modify frozen model inputs, close the original ESPN gaps, or establish complete provider play coverage or historical point-in-time availability.

The local serving replay reproduces **1,247 cached predictions across six owned models**, with maximum absolute difference **1.43e-14 or less**, using zero refits and zero provider calls. This is numerical parity with earlier predictions, not new out-of-sample evidence. NFL uses the accepted model artifacts; the FBS-only matched linear artifacts remain shadow models. Accepted models are unchanged.

The prepared serving path uses runtime issue timestamps and records explicit abstentions for stale features, stale schedules, revised or missing released results, failed parity, missing inputs, or late issuance. A fresh acquisition timestamp cannot make an old feature snapshot current. New research fits, paid-provider calls and model promotions are all zero by design.

The public adapter has 36 offline tests with four tiny synthetic estimator fits. Local cache repair has 128 focused passing checks. These preparation checks do not replace the owner's full release gate or AWS runtime verification. Private raw source fixtures, model binaries and production source contracts are absent from this public release.

[Latest completed V062 evidence](../football_v062/README.md) · [Status index](../README.md)
