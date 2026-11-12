# NCAA B063R1 dashboard recovery status

This dated public report separates the actual B063 startup failure, the local memory repair, recovered selected original issues, and later post-issue outcome monitoring. It preserves the prior NCAA dashboard and every frozen/current scientific table byte for byte beneath a separate recovery panel.

## Actual execution evidence

The authentic B063 inner return for run `20261112T050834Z_40dc9aa0` verifies all 180 manifest members and all 938 embedded source members. It reports 3,732 passed startup tests, one failed test and 11 skips. The failed test raised `PROBE_EXCEEDED_RESERVED_WORKER_MEMORY`; no owner scientific stage or actual 1/4/8/12 benchmark was reached. Configuration requested 12 CPUs; the recorded sequential-startup lease held one. This is not parallelism proof.

The owner recorded zero new sports-model fits, zero runtime-validated reused fits, zero new issued forecasts and zero promotions. Its dated whole-instance cost estimate is $0.457260 at a verified rate of $2.57/hour; it is neither an invoice nor project-attributed billing. The inner return is authenticated; this publication does not claim an independently reopened outer launcher receipt or current process state.

The local B063R1 repair measures the spawned process's current address-space resident high-water mark rather than inherited pre-exec `ru_maxrss`. It retains the 1 GiB synthetic-probe guard and rejects missing/invalid measurements. Real scientific worker memory and actual owner parallelism remain separate requirements.

## Selected original forecast recovery

Ninety additional original rows over 30 games (12 men's rows and 78 women's rows) match the authenticated preserved primary-role policy. Each is the latest original issue for its game/target. Their clocks, cutoffs and hashes were independently checked. Display probabilities are rounded to six decimals and points to three; full originals remain preserved separately. There are no duplicates with the existing 142 public originals, so the selected archive totals 232 rows. These earlier scheduled games are past, and this recovery did not refresh their finals or the upcoming schedule.

## Later monitoring

[B063R1_POSTISSUE_MONITORING.json](B063R1_POSTISSUE_MONITORING.json) contains 46 original rows and eight separate later official outcome observations. Eleven model/target metrics were calculated from original full precision and remain distinct. Six men's games and two women's games per applicable model are a small, selected sample; all eight were home wins. No models were blended or promoted, and no new provider-matched market comparison was acquired.

This report corrects draft PR #243's rounded-input metric headlines with full-precision calculations. The primary-source final observations and attribution remain preserved in [the monitoring addendum](B063_POSTISSUE_OUTCOME_MONITOR_20261112.md).

## Reproducible reporting checks

Run from the repository root:

```sh
python -m unittest discover -s examples/ncaa_review -p 'test_*dashboard.py' -v
node examples/ncaa_review/test_b063r1_dashboard_dom.cjs
python examples/ncaa_review/build_dashboard.py --check
node examples/ncaa_review/test_b063r1_dashboard_browser.cjs
```

The last command requires the repository's existing Playwright/Chromium setup. The recovery browser contract is also called by the existing NCAA browser suite. Local Python/DOM checks, real-browser checks and hosted exact-head CI are separate receipts. A local environment restriction on Chromium is not a passing browser test.

No other sport's data, shared navigation, provider rights, execution package or publication policy is changed.
