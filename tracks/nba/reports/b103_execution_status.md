# NBA B103 bounded execution: completed tasks, incomplete campaign

**Evidence cutoff: November 19, 2026, 03:19 UTC. B103 completed its bounded real-work scope and remains PARTIAL_RESUMABLE_BOUNDED_ACCEPTANCE.**

[NBA track](../README.md) · [Sanitized aggregate evidence](b103_execution_status.json) · [Earlier dated B102 projection recovery](b102_execution_status.html)

## What changed since the preparation snapshot

B103 actually ran on the owner workspace from **03:12 to 03:19 UTC**. The authenticated record shows **one completed bounded execution, zero failed bounded executions, zero failed jobs, and zero full campaign executions**. Its invocation exited **2** under the partial-campaign policy after completing the selected bounded tasks; there was no observed execution exception. This is different from the earlier B102 full-run failure preserved below. It is also different from completing the whole owner campaign or passing full V13 acceptance.

| Work | Current B103 result | Cumulative registered progress |
|---|---|---|
| Base estimators | **12 new fits**, zero failed fits | **24 of 240** box-score base recipes, including the 12 distinct earlier B102 fits; **216 remain**. |
| Calibrators | **12 new fits** | **24 completed** across those distinct B102/B103 base recipes. |
| Preserved validation inference | **12 new replay groups**; **834 prior groups** authenticated and excluded from repeated work | **846 of 2,429** groups complete; **1,583 missing**. These produce **2,151 of 5,808** preserved variants; dependent blends remain incomplete. |
| Meta-models and residual heads | **Zero new fits** | The original **320 B100 residual-distribution states** remain preserved. |
| Original B100 states | **320 files verified; zero missing files restored** | **Zero renewed applications credited**. The actual application counter remains unknown; file verification is not application. |
| Private projections | Prior authenticated authority for **5,808** outputs reused | **Zero current projection tasks, rehashed projection files or new projection CPU credit**. |
| Provider retrieval | **Zero requests and zero credits** | No source freshness is inferred from fitting or checkpoint reuse. |
| Compact verified return | **20,226 bytes, eight payloads**, zero unchanged historical payloads repacked | Successful return verification does not establish full campaign completion. |

These cumulative counts are reconciled across distinct task identities. The current bounded run's policy-deferred counters include work deliberately excluded from the run, including some already completed prior work; they are not the number of scientifically missing tasks.

## Measured CPU and the acceptance limit

The context-preparation phase peaked at **20.442 sampled owner CPU equivalents**. The estimator phase peaked at **4.6169**, ran for **50.10 seconds**, and began with **12 ready estimator tasks** using **one native thread per fit**. Context preparation is useful real work, but its peak cannot be reported as estimator-fitting throughput. Neither a requested ceiling of 24 nor a short peak establishes 24 continuously busy cores.

The recorded fit acceptance is **CONDITIONAL_SHORT_QUEUE_COMPLETION_NOT_FULL_CAPACITY_PASS**, with **zero sustained 180-second / 75%-occupancy passes**. The bounded scope completed; sustained 12–24-core fitting and full-campaign acceptance remain unproven. The threshold was not lowered and synthetic CPU work received no credit.

The through-delivery whole-instance wall-time estimate was **USD 0.307878**. Actual invoiced cost and NBA allocation remain unknown. This estimate is separate from earlier executions and from the compute admission ceiling.

## Scientific boundaries and what remains

The expanded frozen evaluation snapshot contains **1,321 / 1,322 / 210** completed games for **2024–25 / 2025–26 / 2026–27**. The preserved B100 snapshot contains **1,314 / 1,315 / 210**. Their metrics cannot be mixed into a single all-model ranking. The expanded all-contender comparison remains incomplete, and an independently verified all-competition census remains open.

The **210 test games are a frozen snapshot**, not a verified fresh count of every completed 2026–27 game. B104 is being prepared to refresh descriptive test reporting **after the validation selection lock**, preserving completed fitted states and validation-task identities. It is also being prepared to repair the reader for the actual pinned storage-navigation bundle and current continuation. **This dated update does not certify a built, uploaded or executed B104 runner.**

Remaining registered work includes the missing preserved replay groups, **216 base-estimator recipes with their calibrators**, application of all **320 original heads without refitting them**, up to **162 meta-models**, **216 combination residual heads**, and **480 fixed mixtures requiring no new fits**. These are finite maxima and remaining tasks, not a promise that one run completes all V13 research. Existing negative findings, source-clock and coverage gaps, injury/replacement and other frontier work, complete forecasts and qualified dashboards remain visible requirements.

Only the two validation seasons select components and champions: **50/50** annual metrics are primary, with **40/60, 30/70, 20/80 and 10/90** sensitivity scores computed without refitting estimators or reweighting training seasons. Previously exposed test outcomes remain descriptive and cannot select or tune components. Original issues and reconstructed/replayed predictions remain separate; external-market overlap does not redefine the full evaluation population.

## Source and publication scope

This update changes only the NBA README notice and these two status documents. It adds no new forecast values, private model or feature recipes, runtime packages, raw provider records, cloud identifiers, owner commands, workflow changes or production changes. The earlier B102 full-run failure and B103 preparation facts remain preserved below and in explicitly historical JSON fields.

The aggregate JSON binds the latest B103 execution and invocation evidence by digest. Those private bodies are not public downloads. **This remains a draft, unmerged source review: no main integration, website deployment or automatic champion promotion.** Existing CI for the new exact source is tracked separately from both historical CI and scientific acceptance. No workflow rerun or timeout change is implied.

---

## Preserved earlier preparation and B102 failure record

**The following record was written before the B103 bounded invocation. Its statements about native access and zero B103 fits describe that earlier preparation snapshot. The actual execution above supersedes those statements for current activity; the B102 failure measurements and engineering history remain unchanged.**

# NBA B103 preparation and latest B102 full-run failure

**Dated status: November 19, 2026 UTC. B102 is PARTIAL_RESUMABLE; B103 is a prepared candidate awaiting native acceptance.**

[NBA track](../README.md) · [Sanitized aggregate evidence](b103_execution_status.json) · [Earlier dated B102 projection recovery](b102_execution_status.html)

## What the latest full execution actually did

The later B102 owner invocation exited **2** after a registered `preserved_point_replay` branch failed with `CurrentForecastsIncomplete`. This is one failed or partial full owner execution, zero successful full owner executions in this snapshot, and zero individual estimator or inference-task failures. The campaign entered scientific inference; it produced **zero new estimator, calibration, meta-model or residual-distribution fits** and made **zero provider requests**.

| Work | Actual outcome |
|---|---|
| Private projection recovery | All **5,808** saved outputs freshly verified against source/output hashes, schemas and identities; authenticated prior durability reused; zero regenerated, failed or deferred outputs. |
| Preserved validation inference | **834 of 2,429** base groups complete and checkpointed; **1,595** deferred. Those groups cover **2,127 of 5,808** variants, leaving **3,681**, including downstream blends. |
| B100 distribution states | All **320** files verified already present; zero missing states restored. New application remains blocked, so the application counter stays unknown and receives no credit. |
| Earlier bounded B102 fitting | **12 estimators + 12 calibrations** remain preserved prior work. They are not new fits from this later full invocation. |
| Verified compact return | **185,186 bytes**, nine authenticated payloads, zero historical payloads repacked. A verified partial return does not make the execution successful. |

## Exact failure and measured throughput

Shared memory-pressure admission drained worker grants to zero. The dispatcher exhausted a **180.04-second continuous no-capacity wait** with queued inference work and no active scientific workers. This differs from B101's old productive-projection occupancy defect. The later projection re-verification lasted **249.95 seconds**; there was no fixed three-minute productive-projection deadline in this execution.

Initial projection verification completed in **53.29 seconds**, with **24 real overlapping tasks** and **24.26 completed-task CPU seconds**. That ratio is about **0.46 CPU equivalents**, not 24 busy cores. Validation replay lasted **614.02 seconds** and accumulated **2,764.49 completed-task CPU seconds**. Its independent samples averaged **4.60 owner CPU equivalents**, peaked at **20.02**, and observed up to **24 active scoring processes**. Task CPU and whole-owner sampled CPU have different scopes. The recorded sustained three-minute/75% acceptance-pass count is **zero**.

After the branch failure, B102 unnecessarily repeated projection verification and spent another **162.38 seconds** generating private exports. That expensive work is separate from compact ZIP packaging. B103's incomplete-campaign path is prepared to retain prior references and emit compact diagnostics promptly.

The through-delivery whole-instance wall-time estimate was **USD 1.0635**. Actual invoiced cost and NBA allocation are unknown. A configured compute admission guard is not an absolute billed-cost guarantee.

## B103 preparation and its present limit

B103 preserves all **1,162** inherited release members byte-for-byte and retains the original numerical/checkpoint identities. It prepares current-pressure/owner-progress admission, bounded recovery, exact checkpoint reuse, separate independent research branches and compact incomplete-run finalization. Actual memory headroom, cgroup limits and fresh limit events, CPU saturation, low disk, cost/signal stops and other-owner reservations remain safeguards. Completed states are restored from authenticated bytes or blocked; they are not silently refitted.

The final combined engineering suite passed **96 tests, zero failures/errors/skips**. A prior combined attempt had **95 tests, two failures and 13 errors**; dependency resolution and isolated test hooks corrected that test-process failure, with a serialization-identity regression retained. The final **11 installer checks** separately passed with fake local storage and in-memory transfer fixtures. These are engineering checks, not native workload or scientific CPU measurements.

**Native installation, native readiness and representative B103 real-work acceptance remain pending because the authenticated workspace session was unavailable.** B103 has executed zero scientific fits and no full owner campaign. The next owner step is verified installation, read-only readiness and a bounded real-work acceptance run, requesting 24 cores with a hard ceiling of 24 workers, followed by evidence review. Full research is held; there is no automatic full-run chain. A configured worker ceiling does not promise safe admission or observed CPU throughput.

## Scientific work that remains

The declared completed-game populations are now **1,321 for 2024–25, 1,322 for 2025–26 and 210 for 2026–27**. B100's older validation metrics used **1,314 / 1,315**, so those scorecards cannot establish a winner against the expanded population. Complete preserved-contender replay, frozen test replay, application of the 320 existing distribution heads, missing registered estimator/calibration/blend work and unified identical-population scoring remain unfinished.

The independent full all-competition census is still unverified; an unknown missing count is not zero. Validation alone selects components and champions, using 50/50 annual weights by default and sensitivity policies without estimator refitting. Test results remain descriptive and previously exposed; they do not select or tune components. Market overlap remains separate. Source coverage, current forecasts, full V13 qualification and resulting qualified dashboards remain incomplete.

## Publication and provenance

This dated source update adds aggregates only. Prior reports and the previous NBA README content remain byte-identical after removing the new notice. It adds no forecast values, private recipes, runtime code, provider records, cloud identifiers or owner command. The aggregate JSON identifies the authenticated private execution, invocation and telemetry evidence by digest; those complete private bodies are not public downloads.

**Draft source review only: no merge, main integration, website deployment or automatic champion promotion.** Exact-head CI is tracked on the draft PR and is separate from both historical CI and native acceptance. The older B102 projection page remains historical evidence; its successful review does not certify the later failed full run or B103.
