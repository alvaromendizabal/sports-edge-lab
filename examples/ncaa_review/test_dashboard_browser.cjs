// Real Chromium contract: all evidence selectors, clock scenarios and mobile layout.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { createHash } = require('node:crypto');
const { gzipSync } = require('node:zlib');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const { fixture: identityOverlayFixture } = require('./test_identity_overlay.cjs');
const { fixture: scheduleFixture, referenceFixture: scheduleReferenceFixture } = require('./test_schedule_viewer.cjs');
const { compactFixture: compactScheduleFixture } = require('./test_schedule_compact.cjs');
const { fixture: eligibilityFixture } = require('./test_eligibility_viewer.cjs');
const { fixture: v4Fixture } = require('./test_v4_review.cjs');

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}),
  });
  const failures = [], externalRequests = [];
  const page = await browser.newPage();
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => {
    if (!/^(file|data|blob):/.test(request.url())) externalRequests.push(request.url());
  });
  const root = path.resolve(__dirname, '../..');
  const objectiveMap = {
    probability: ['win', 'LogLoss'], accuracy: ['win', 'Accuracy'],
    margin: ['margin', 'MAE'], total: ['total', 'MAE'],
  };
  const counts = { viewports: 0, selectorStates: 0, scenarios: 0, progressScenarios: 0, preflightScenarios: 0, executionViews: 0, keyboardEvents: 0, privateViewerStates: 0, captureClockViews: 0, horizonMetricViews: 0, unclassifiedSourceViews: 0, providerComparisonViews: 0, boundedInventoryViews: 0, freshnessViews: 0, spreadScenarios: 0, atsRecordViews: 0 };
  try {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const league of ['ncaam', 'ncaaw']) {
        await page.goto(pathToFileURL(path.join(root, 'tracks', league, 'index.html')).href);
        await page.locator('#model-table tbody tr').first().waitFor();
        const evidence = JSON.parse(await page.locator('#evidence').textContent());
        assert.equal(evidence.league, league);
        assert.match(await page.locator('#b053-current-return').innerText(), /Current B053 owner result.*9\/16 stages completed.*one failed wrapper stage.*six not entered.*145 new target fits, 45 new scalar fits and 24 new empirical fits/s);
        assert.match(await page.locator('#b052-current-return').innerText(), /Dated B052 return.*5\/16 stages completed.*zero stages recorded failed.*11 not entered.*B048_SUMMARY_EXCEEDS_REPORT_PART_BOUND/s);
        assert.match(await page.locator('#b051-current-return').innerText(), /Dated B051 return.*1\/16 stages completed.*B035_REUSE_SCIENTIFIC_IMPLEMENTATION_CHANGED:b032_resume.py/s);
        assert.equal(await page.locator('#provider-table tr').count(), 3);
        assert.deepEqual(await page.locator('#provider-table tr td:first-child strong').allTextContents(), ['Kalshi', 'Polymarket', 'DraftKings']);
        const attempt = evidence.current_owner_attempt, inventory = evidence.observed_inventory;
        assert.equal(attempt.release, 'B046');
        const datedB045=evidence.owner_attempt_history.find(a=>a.release==='B045');
        const scientific = evidence.owner_attempt_history.find(a => a.release === 'B043');
        const earlier = evidence.owner_attempt_history.find(a => a.release === 'B044');
        assert.deepEqual([scientific.completed_scientific_stages, scientific.new_real_target_fits, scientific.new_calibration_fits, scientific.new_empirical_residual_fits], [9, 101, 45, 24]);
        assert.equal(attempt.status, 'RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED');
        assert.equal(datedB045.status,'WORKER_EXITED_WITHOUT_TERMINAL_RETURN');
        assert.equal(attempt.failure_class, 'AdmissionDeferred');
        assert.equal(datedB045.child_exit_code, -9);
        assert.equal(attempt.child_exit_code,null);
        assert.equal(attempt.external_shell_exit_code, null);
        assert.equal(datedB045.kill_cause, 'UNKNOWN');
        assert.equal(attempt.out_of_memory_proved, false);
        assert.deepEqual([attempt.completed_scientific_stages, attempt.attempted_scientific_stages, attempt.planned_scientific_stages], [9, 10, 16]);
        for (const key of ['new_real_target_fits','league_new_real_target_fits','new_calibration_fits','new_empirical_residual_fits','new_injury_fits','new_prediction_rows','new_prospective_issues','reused_target_fits','synthetic_tests_total','completed_at','total_wall_seconds','cpu_seconds','owner_peak_rss_bytes']) assert.equal(datedB045[key], null, key);
        assert.equal(datedB045.durable_return_verified, false);
        assert.equal(attempt.durable_return_verified,true);
        assert.deepEqual([attempt.new_real_target_fits,attempt.new_calibration_fits,attempt.new_empirical_residual_fits],[4033,701,24]);
        assert.match(await page.locator('#b046-panels').innerText(),/85,466.*47,127.*47,130.*1,499.*4,699/);
        assert.equal(await page.locator('#season-inventory tr').count(),5);
        assert.equal(await page.locator('#capability-table tr').count(),11);
        assert.match(await page.locator('#capability-caption').innerText(),/B047R1.*10 base estimator families \/ 26 target heads.*owner execution pending/);
        assert.match(await page.locator('#capability-table').innerText(),/Extra Trees.*Classification \/ margin and total regression/s);
        assert.match(await page.locator('#frontier-copy').innerText(),/actual B046.*not reached.*B047R1.*prepared/);
        assert.doesNotMatch(await page.locator('body').innerText(),/\b(?:bets?|betting|wagers?|wagering|stakes?|staking|ROI|profit|recommendations?|NO BET)\b/i);
        assert.match(await page.locator('#ats-repair-summary').innerText(),/1,793.*43,032.*Zero qualified/);
        assert.match(await page.locator('#latest-baseline-copy').innerText(), /87,003 target rows and 47,940 browser display rows.*1,223 metric panels.*4,147 checks with zero mismatches.*1,220 model metric panels.*417 season \/ 803 weekly; 4,132 checks.*3 provider panels \/ 15 checks/);
        assert.match(await page.locator('#latest-baseline-issues').innerText(), /255 returned immutable journal objects.*552 distinct verified B045-source issues across 8 games.*549 B045 prospective rows.*3 additional journal rows.*339 B042 issues across 5 games.*does not identify an owner run/);
        assert.equal(earlier.completed_scientific_stages, 0);
        assert.equal(earlier.storage_readback.new_full_storage_GETs, 182);
        assert.equal(earlier.new_real_target_fits, 0);
        assert.match(await page.locator('#time-legend').innerText(), /Injury stage.*Other recorded owner time/s);
        assert.equal(scientific.retained_prior_prospective_issues, 339);
        assert.equal(attempt.scientific_goal_complete, false);
        assert.equal(attempt.current_outcomes_used_for_selection, false);
        const currentText = await page.locator('#current').innerText();
        assert.match(currentText, /Original as-issued credit:\s*0/);
        assert.match(currentText, /3,816 target rows.*unchanged original weights/);
        assert.match(currentText, /69,600 current-monitor and 10,440 native-replay target rows/);
        assert.match(currentText, /Pre-study metrics:\s*Recovered/);
        const result = evidence.current_results_status;
        assert.equal(result.new_issues_created_by_recovery, 0);
        assert.equal(result.new_fits_created_by_recovery, 0);
        assert.equal(result.new_paired_metrics, 'PRE_STUDY_RETROSPECTIVE_AGGREGATES_AVAILABLE');
        assert.equal(result.new_model_winner, null);
        assert.match(await page.locator('#issue-recovery-copy').innerText(), league === 'ncaam'
          ? /132 existing B042 issue rows across 2 games/ : /207 existing B042 issue rows across 3 games/);
        assert.match(await page.locator('#issue-recovery-copy').innerText(), /339 rows across 5 games.*created no new issues or model fits/);
        const polymarketRow = page.locator('#provider-table tr').filter({hasText:'Polymarket'});
        assert.equal(await polymarketRow.locator('.provider-product').textContent(), 'International; US unacquired');
        assert.equal(await polymarketRow.locator('.provider-product').isHidden(), width === 390);
        assert.match(await polymarketRow.innerText(), /161,903 international observations.*US is separate and unacquired/s);
        assert.deepEqual(evidence.providers.find(p => p.name === 'Polymarket').products,
          [{name:'International',status:'PARTIAL_INTERNATIONAL_CAPTURE'}, {name:'US',status:'NOT_ACQUIRED_UNVERIFIED'}]);
        for (const provider of evidence.providers) {
          const expectedCoverage = league === 'ncaam' && provider.name === 'Polymarket'
            ? 'RECONSTRUCTED_PAIRED_POPULATION_ONLY' : 'NOT_ESTABLISHED';
          assert.equal(provider.eligible_comparison_coverage, expectedCoverage);
          assert.equal(provider.hypothetical_ROI, null);
          const providerRow = page.locator('#provider-table tr').filter({hasText:provider.name});
          assert.equal(await providerRow.locator('td').last().innerText(), expectedCoverage.replaceAll('_', ' '));
          assert.ok((await providerRow.innerText()).includes(provider.display_coverage));
        }
        const reconstructed = evidence.current_reconstructed_comparison;
        assert.equal(reconstructed.as_issued, false);
        assert.equal(reconstructed.current_outcomes_selected_model, false);
        assert.equal(reconstructed.qualified_settled_bets, 0);
        assert.equal(reconstructed.profit, null);
        assert.equal(reconstructed.latest_owner_result, false);
        if (league === 'ncaam') {
          assert.equal(reconstructed.status, 'RETROSPECTIVE_PAIRED_ORIGINAL_VERSUS_POLYMARKET');
          assert.equal(reconstructed.paired_games, 122);
          assert.equal(await page.locator('#current-paired-table tbody tr').count(), 5);
          assert.match(await page.locator('#current-paired-note').innerText(), /Preserved in B040; not a new B046 result.*122 identical supplied games.*T−60 reference/);
          assert.match(await page.locator('#current-paired-disagreements').innerText(), /7 model-right \/ provider-wrong disagreements; 2 in the reverse direction/);
          assert.match(await page.locator('#current-paired-disagreements').innerText(), /descriptive matched forecast comparison/);
        } else {
          assert.equal(reconstructed.status, 'NO_EXACT_PAIRED_COHORT_SUPPLIED');
          assert.equal(await page.locator('#current-paired-table table').count(), 0);
          assert.match(await page.locator('#current-paired-note').innerText(), /This earlier gap remains dated evidence/);
          assert.match(await page.locator('#current-paired-disagreements').innerText(), /authenticated B042 issues are reported separately/);
        }
        const latest = evidence.latest_reconstructed_comparison;
        assert.equal(latest.as_issued, false);
        assert.equal(latest.current_outcomes_selected_model, false);
        assert.equal(latest.qualified_settled_bets, 0);
        assert.equal(latest.profit, null);
        assert.equal(latest.latest_owner_result, false);
        assert.equal(latest.latest_scientific_result, true);
        assert.match(await page.locator('#durable-report-copy').innerText(), /84,195 target rows and 46,529 browser rows.*944 model metric panels with 0 mismatches/);
        if (league === 'ncaam') {
          assert.equal(latest.paired_games, 129);
          assert.equal(await page.locator('#latest-paired-table tbody tr').count(), 5);
          assert.match(await page.locator('#latest-paired-note').innerText(), /B043 pre-study report.*129 identical supplied games.*T−60 reference/);
          assert.match(await page.locator('#latest-paired-disagreements').innerText(), /7 model-right.*2 in the reverse direction.*worse log loss, Brier and AUC/);
          assert.match(await page.locator('#latest-paired-disagreements').innerText(), /earlier 122-game panel above keeps its original values/);
          const values = await page.locator('#latest-paired-table tbody tr').first().innerText();
          assert.match(values, /86.05%.*82.17%/s);
        } else {
          assert.equal(latest.paired_games, 0);
          assert.equal(await page.locator('#latest-paired-table table').count(), 0);
          assert.match(await page.locator('#latest-paired-note').innerText(), /No exact paired women’s provider cohort is admitted/);
        }
        assert.match(await page.locator('#attempt-summary').innerText(), /4,033 target \/ 701 scalar \/ 24 empirical committed fits/);
        assert.match(await page.locator('#attempt-summary').innerText(), /9 of 16 stages/);
        assert.match(await page.locator('#execution-intro').innerText(), /B046 recorded an injury-stage failure.*Nine of 16 stages completed/);
        assert.match(await page.locator('.status-strip strong').innerText(), /during injury research/);
        assert.doesNotMatch(await page.locator('.status-strip strong').innerText(), /stopped before science/);
        assert.match(await page.locator('#preserved-study-copy').innerText(), /108 committed target fits across both leagues; 54 in this track/);
        assert.equal(await page.locator('#phase-table tr').count(), 16);
        assert.equal(await page.locator('#phase-table .done').count(), 9);
        assert.equal(await page.locator('#phase-table tr').first().locator('td').last().innerText(), '23.3 min');
        assert.equal(await page.locator('#recent-phase-table .done').count(), 9);
        assert.match(await page.locator('#recent-study-copy').innerText(), /101 target \/ 45 scalar \/ 24 empirical fits/);
        assert.match(await page.locator('#readback-copy').innerText(), /90 chunks \/ 723,492 earlier observations \/ 1,504,058,360 logical bytes.*182 storage GETs/);
        assert.match(await page.locator('#prepared-copy').innerText(), /B047R1.*no owner-execution/);
        assert.deepEqual(await page.locator('#handoff-table tr td:last-child').allTextContents(), ['2 passed', 'Blocked before work', '0', 'ADMITTED', '0']);
        assert.equal(await page.locator('#phase-table .failed').count(), 1);
        assert.match(await page.locator('#phase-table tr').nth(5).innerText(), /Timestamped injury.*Completed/);
        assert.match(await page.locator('#phase-table tr').nth(9).innerText(), /paired injury.*Failed/);
        assert.equal(attempt.stages.filter(stage => stage.status === 'NOT_STARTED').length, 6);
        assert.match(await page.locator('#phase-table tr').nth(15).innerText(), /Final display.*secondary history\s+Not started/i);
        assert.equal(await page.locator('#history-phase-table .done').count(), 3);
        assert.equal(await page.locator('#history-phase-table .failed').count(), 1);
        assert.equal(inventory.snapshot_at, '2026-11-06T02:14:03.087794+00:00');
        const expectedPacificCapture = new Intl.DateTimeFormat('en-US', {timeZone:'America/Los_Angeles',
          year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(inventory.snapshot_at));
        assert.equal(await page.locator('#inventory-age').innerText(), 'Retained B043 source acquisition completed ' + expectedPacificCapture);
        assert.deepEqual([inventory.candidate_games, inventory.observed_finals], league === 'ncaam' ? [1439, 395] : [1379, 434]);
        assert.deepEqual(await page.locator('#coverage-counts strong').allTextContents(),
          [inventory.candidate_games.toLocaleString('en-US'), inventory.observed_finals.toLocaleString('en-US'), 'Unverified']);
        assert.equal(inventory.official_inventory_reconciled, false);
        assert.equal(inventory.all_official_games_covered, false);
        assert.equal(inventory.authenticated_current_issues, league === 'ncaam' ? 132 : 207);
        assert.match(await page.locator('#week-counts').innerText(), /Reporting weeks use America\/New_York; tipoffs display Pacific/);
        assert.match(await page.locator('#week-counts').innerText(), /recovery created zero new issues/);
        assert.match(await page.locator('#official-counts').innerText(), /1,797 accepted official contest records, 775 exact matches, 1,022 unmatched official candidates, 44 conflicts/);
        assert.equal(await page.locator('#freshness-table tr').count(), 8);
        assert.match(await page.locator('#freshness-note').innerText(), /publication does not refresh any provider/);
        assert.match(await page.locator('#resource-note').innerText(), /not the simultaneous process-tree peak/);
        assert.match(await page.locator('#injury-copy').innerText(), /All 1,320 historical snapshot versions remain unverified/);
        assert.match(await page.locator('#injury-clocks').innerText(), /1,246 lack one: 1,244 recovered image observations and two current PDF/);
        assert.match(await page.locator('#frontier-limit').innerText(), /no completed market-path study or performance gain is claimed/);
        const spreadExample = JSON.parse(await page.locator('#spread-ats-evidence').textContent());
        assert.equal(spreadExample.scope, 'INVENTED_EXAMPLE_NOT_NCAA_PERFORMANCE');
        for (const [name, values] of Object.entries(spreadExample.probabilities)) {
          await page.locator('[data-spread="' + name + '"]').click();
          assert.equal(await page.locator('[data-spread][aria-pressed="true"]').count(), 1);
          assert.deepEqual(await page.locator('#spread-probabilities strong').allTextContents(), ['cover','push','loss'].map(key => (values.home[key]*100).toFixed(2)+'%'));
          assert.ok((await page.locator('#spread-orientation').innerText()).includes('Away covers '+(values.away.cover*100).toFixed(2)+'%'));
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, league+' '+width+' spread overflow');
          counts.spreadScenarios++;
        }
        assert.deepEqual(await page.locator('#ats-record strong').allTextContents(), ['2','1','1']);
        assert.match(await page.locator('#ats-denominator').innerText(), /4 eligible settled games; 66.67% across 3 decisions, excluding pushes. 1 unknown-clock record excluded/);
        assert.match(await page.locator('#spread-clock-proof').innerText(), /Late capture is rejected.*17:01.*not captured before cutoff.*No additional scientific credit/s);
        assert.equal(evidence.ats_research.real_cover_probability_champion, null);
        assert.equal(evidence.ats_research.real_ats_record_published, false);
        await page.locator('[data-spread="favorite_half"]').focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.locator('[data-spread="favorite_half"]').getAttribute('aria-pressed'), 'true');
        counts.atsRecordViews++;
        counts.executionViews++;
        const preflightExamples = JSON.parse(await page.locator('#preflight-evidence').textContent());
        assert.equal(preflightExamples.length, 4);
        for (const scenario of preflightExamples) {
          await page.locator(`[data-preflight="${scenario.id}"]`).click();
          assert.equal(await page.locator('[data-preflight][aria-pressed="true"]').count(), 1);
          assert.match(await page.locator('#preflight-output').innerText(), scenario.result.gate_passed ? /Ready:/ : /Blocked:/);
          assert.equal(await page.locator('#preflight-output.blocked').count(), scenario.result.gate_passed ? 0 : 1);
          assert.deepEqual(await page.locator('#preflight-counts strong').allTextContents(), Object.values(scenario.result.counts).map(String));
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${league} ${width} ${scenario.id} preflight overflow`);
          counts.preflightScenarios++;
        }
        for (const [objective, [target, metric]] of Object.entries(objectiveMap)) {
          await page.selectOption('#objective', objective);
          for (const season of ['pooled', '2025', '2026']) {
            await page.selectOption('#season', season);
            const models = evidence.models.filter(m => m.target === target);
            const selected = models.find(m => m.selected_for.includes(metric));
            const selectedPanel = selected.panels[season];
            assert.equal(await page.locator('#model-table tbody tr').count(), models.length);
            assert.equal(await page.locator('#model-table tbody tr.active .table-id').textContent(), selected.id);
            assert.equal(await page.locator('.metric-value').last().innerText(), selectedPanel.N.toLocaleString('en-US'));
            const expected = metric === 'Accuracy'
              ? (selectedPanel.Accuracy * 100).toFixed(2) + '%'
              : selectedPanel[metric].toFixed(target === 'win' ? 4 : 3);
            assert.equal(await page.locator('.metric-value').first().innerText(), expected);
            assert.equal(await page.locator('#chart svg[role="img"]').count(), 1);
            assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${league} ${width} ${objective} page overflow`);
            counts.selectorStates++;
          }
        }
        for (const scenario of ['valid', 'late_quote', 'boundary_label', 'settlement']) {
          await page.locator(`[data-scenario="${scenario}"]`).click();
          assert.equal(await page.locator('[data-scenario][aria-pressed="true"]').count(), 1);
          assert.equal(await page.locator(`[data-scenario="${scenario}"]`).getAttribute('aria-pressed'), 'true');
          const output = await page.locator('#demo-output').innerText();
          assert.match(output, scenario === 'valid' ? /Eligible synthetic comparison/ : /Excluded:/);
          assert.equal(await page.locator('#demo-output.blocked').count(), scenario === 'valid' ? 0 : 1);
          counts.scenarios++;
        }
        const progressExamples = JSON.parse(await page.locator('#progress-evidence').textContent());
        assert.equal(progressExamples.length, 8);
        for (const scenario of progressExamples) {
          await page.locator(`[data-progress="${scenario.id}"]`).click();
          assert.equal(await page.locator('[data-progress][aria-pressed="true"]').count(), 1);
          const p = scenario.progress;
          assert.equal(await page.locator('#progress-count').innerText(), `${p.completed} / ${p.total === null ? 'unknown' : p.total}`);
          assert.match(await page.locator('#progress-components').innerText(), new RegExp(`${p.newly_committed} newly committed.*${p.reused} reused`));
          if (p.total === null) {
            assert.equal(await page.locator('#progress-track').getAttribute('aria-valuenow'), null);
            assert.match(await page.locator('#progress-eta').innerText(), /Unknown/);
          } else {
            assert.equal(await page.locator('#progress-track').getAttribute('aria-valuenow'), String(p.completed));
          }
          if (scenario.id === 'measured') assert.equal(await page.locator('#progress-eta').innerText(), '30.0 s');
          if (scenario.id === 'reused') assert.equal(await page.locator('#progress-eta').innerText(), '40.0 s');
          if (scenario.id === 'failed') assert.match(await page.locator('#progress-eta').innerText(), /Stopped/);
          if (scenario.id === 'complete') assert.equal(await page.locator('#progress-eta').innerText(), 'Complete');
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${league} ${width} ${scenario.id} progress overflow`);
          counts.progressScenarios++;
        }
        await page.selectOption('#objective', 'probability');
        await page.selectOption('#season', 'pooled');
        await page.locator('#objective').focus();
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        assert.equal(await page.locator('#objective').inputValue(), 'accuracy');
        counts.keyboardEvents++;
        await page.selectOption('#objective', 'probability');
        await page.locator('[data-scenario="valid"]').click();
        await page.locator('[data-progress="measured"]').click();
        await page.locator('body').click({ position: { x: 3, y: 3 } });
        await page.evaluate(() => window.scrollTo(0, 0));
        if (process.env.DASHBOARD_SCREENSHOTS) {
          fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS, { recursive: true });
          await page.screenshot({ path: path.join(process.env.DASHBOARD_SCREENSHOTS, `ncaa-${league}-${width}.png`), fullPage: true });
        }
        counts.viewports++;
      }
      await page.goto(pathToFileURL(path.join(root, 'docs/ncaa/index.html')).href);
      assert.equal(await page.locator('.cards a').count(), 2);
      assert.match(await page.locator('.status').innerText(), /B046: 9\/16 stages completed; partial work and final return preserved/);
      assert.match(await page.locator('.status').innerText(), /85,466 target rows, 47,127 game-model rows and 47,130 display rows/s);
      assert.match(await page.locator('.status').innerText(), /339 B042 immutable issues/);
      assert.doesNotMatch(await page.locator('.status').innerText(), /Latest owner stopped before science/);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `landing ${width} overflow`);
      if (process.env.DASHBOARD_SCREENSHOTS) {
        await page.screenshot({ path: path.join(process.env.DASHBOARD_SCREENSHOTS, `ncaa-landing-${width}.png`), fullPage: true });
      }
      counts.viewports++;
      // Only invented rows enter public browser tests. Private files are never fixtures.
      await page.goto(pathToFileURL(path.join(root, 'docs/ncaa/private-report/index.html')).href);
      assert.equal(await page.locator('#report').isHidden(), true);
      const rows = Array.from({ length: 27 }, (_, i) => ({ event_id: `invented-${i}`, league: i < 24 ? 'ncaam' : 'ncaaw',
        home_team: i === 0 ? '<img src=x onerror="window.privateLeak=true">' : `Home ${i}`, away_team: `Away ${i}`,
        source_date: '2026-11-04', time_precision: 'unknown', phase: 'unknown', completed: i === 0,
        ...(i === 0 ? { track: 'native_rolling_weekly_reconstruction', forecast_status: 'RETROSPECTIVE_NOT_AS_ISSUED',
          prediction_win: .6, prediction_margin: 3, prediction_total: 140, actual_home_points: 70, actual_away_points: 72,
          model_winner_pick: 'Home 0', model_winner_pick_correct: false } : {}) }));
      // Values deliberately disagree across clock references and with the strict
      // model pair. A display change must never rewrite the qualified pair.
      for(const [i,clock]of ['captured_t120','captured_t60','latest_pretip','latest_observed'].entries()){
        Object.assign(rows[0],{['kalshi_'+clock+'_win_value']:.4+i*.1,
          ['kalshi_'+clock+'_win_status']:'CAPTURED_INVENTED_'+clock,
          ['kalshi_'+clock+'_win_value_kind']:'Native home probability',
          ['kalshi_'+clock+'_win_quote_time']:'2026-11-04T'+(18+i)+':00:00Z',
          ['kalshi_'+clock+'_win_acquired_at']:'2026-11-05T01:00:00Z',
          ['kalshi_'+clock+'_win_observation_support_end_upper_bound']:'2026-11-04T'+(18+i)+':01:00Z',
          ['kalshi_'+clock+'_win_history_resolution_seconds']:60,
          ['kalshi_'+clock+'_win_clock_tier']:'recovered_display_observation'});
      }
      Object.assign(rows[0],{kalshi_win_prediction:.3456,kalshi_win_status:'INVENTED_QUALIFIED_PAIR',
        kalshi_quote_time:'2026-11-04T19:00:00Z',kalshi_quote_acquired_at:'2026-11-04T19:00:01Z',
        cutoff_time:'2026-11-04T19:00:00Z',issued_at:'2026-11-04T18:59:30Z',
        kalshi_hypothetical_selection:'NO BET',kalshi_no_bet_reason:'Execution and fees unverified',
        polymarket_latest_pretip_total_value:.2718,polymarket_latest_pretip_total_value_kind:'Binary threshold probability',
        polymarket_latest_pretip_total_status:'POINT_MEAN_UNSUPPORTED',polymarket_us_status:'NOT ACQUIRED / UNVERIFIED'});
      Object.assign(rows[1],{kalshi_latest_pretip_win_value:.8123,
        kalshi_latest_pretip_win_status:'CAPTURED_WITHOUT_MODEL',kalshi_latest_pretip_win_value_kind:'Native home probability'});
      rows[0].injury_display_views_json=JSON.stringify({strict_captured_t120:{injury_coverage_status:'UNKNOWN_NO_ELIGIBLE_REPORT',injury_feature_available_at:null},
        source_supported_reconstruction_t0:{injury_coverage_status:'PARTIAL_REPORTED_LOWER_BOUNDS',injury_feature_available_at:'2026-11-04T19:30:00Z'},undocumented_boundary:null});
      rows[1].injury_display_views_json='null';
      rows[0].b042_injury_display_views_json=JSON.stringify({strict_captured_t120:{injury_coverage_status:'UNKNOWN_NO_ELIGIBLE_REPORT',injury_feature_available_at:null},
        source_supported_reconstruction_t0:{injury_coverage_status:'PARTIAL_REPORTED_LOWER_BOUNDS',injury_feature_available_at:'2026-11-04T19:45:00Z'},undocumented_boundary:null});
      rows[0].b042_injury_display_asof='2026-11-05T23:00:00Z';
      const secondStream={...rows[0],track:'original_frozen',durable_issued_before_cutoff:true,
        forecast_status:'INVENTED_ORIGINAL_ISSUE',prediction_win:.4567,kalshi_win_prediction:.2345,
        kalshi_win_status:'INVENTED_OTHER_STREAM_PAIR'};
      const invented = { schema: 'sports-edge-lab.private.game-report.v1', evidence_release: 'INVENTED', asof_utc: '2026-11-04T20:00:00Z',
        records: [...rows,secondStream], market_observations: [{ provider: 'Kalshi', canonical_identity_verified: false, native_event_id: 'unresolved-fixture', binding_status: 'unknown_identity', quote_time: null, native_yes_probability: .37, value_kind: 'Native Yes probability' },
          { provider: 'DraftKings', league: 'ncaam', canonical_identity_verified: true, event_id: 'invented-0', target: 'win', prediction: .55 }],
        window_event_keys: { this_week: rows.slice(0, 5).map(r => [r.league, r.event_id]), season_to_date: rows.slice(0, 1).map(r => [r.league, r.event_id]), last_week: [] },
        audit_annotations: { 'invented-0': ['Exact time disputed; no replacement inferred.'] }, metrics: [{league:'ncaam',season_end_year:2027,target:'win',recipe:'invented original',track:'original_frozen',n:1,n_forecast_rows:2,accuracy:'0.5',log_loss:'0.7',brier:'0.2',horizon_minutes:60,model_evidence_mode:'invented',hypothetical_ROI:0.08},{league:'ncaam',season_end_year:2027,target:'margin',recipe:'invented original',track:'original_frozen',n:1,n_forecast_rows:2,mae:'3.25',rmse:'4.5',bias_prediction_minus_actual:'0.25'}], weekly_metrics: [],
        injury_display_latest_fields:{injury_display_views_json:'b042_injury_display_views_json',injury_display_asof:'b042_injury_display_asof'},
        injury_research:{schema:'sel.ncaa.b041.private_injury_display.v1',asof:'2026-11-05T20:00:00Z',
          observations:Array.from({length:27},(_,i)=>({observation_id:'invented-injury-'+i,league:i<24?'ncaam':'ncaaw',
            player_name:i===0?'<img src=x onerror="window.injuryLeak=true">':'Named Player '+i,team_name:'Availability Team '+i,
            status:i%2?'questionable':'out',scope:'single_game_date',season_end_year:2026,event_date:'2026-01-07',
            event_date_precision:'date_only_timezone_unknown',source_printed_report_date:'2026-01-07',
            source_publication_time:i===1?'2026-01-06T18:00:00Z':null,source_acquired_at:'2026-11-05T19:00:00Z',
            source_clock_precision:i===1?'exact_publication':'report_date_only_publication_unknown',source_id:'invented-source-'+i,
            source_url:i===0?'javascript:window.injuryLeak=true':'https://example.invalid/availability',binding_status:'UNRESOLVED_INVENTED'})),
          source_report:{unresolved_observations:[{observation_id:'unresolved-injury',player_name:'Unresolved Player',team_name:'Unresolved School',status:'out'}],gaps:[{source_id:'invented-source',status:'UNKNOWN_PUBLICATION_CLOCK',http_status:200}]},
          horizon_reports:[{evidence_tier:'source_supported_reconstruction',horizon_minutes:60,selected_observation_ids:['invented-injury-1']}]}};
      await page.locator('#report-file').setInputFiles({ name: 'invented-report.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(invented)) });
      await page.locator('#report:not([hidden])').waitFor();
      assert.match(await page.locator('#load-status').innerText(), /Loaded 27 source game records/);
      assert.equal(await page.locator('[data-season-game]').count(),25);
      assert.equal(await page.locator('[data-game]').count(),0);
      assert.match(await page.locator('#coverage-workspace').innerText(),/Supplied spread candidate/);
      assert.match(await page.locator('#results').innerText(),/Home probability|home/);
      await page.selectOption('#coverage-filter','cover');
      assert.equal(await page.locator('[data-season-game]').count(),25);
      await page.selectOption('#coverage-filter','all');
      await page.selectOption('#completion-filter','final');
      assert.equal(await page.locator('[data-season-game]').count(),1);
      await page.selectOption('#completion-filter','all');
      assert.match(await page.locator('#model-metrics').innerText(),/log_loss: 0.7000/);
      await page.selectOption('#metric-target','margin');
      assert.match(await page.locator('#model-metrics').innerText(),/mae: 3.2500.*rmse: 4.5000/s);
      assert.match(await page.locator('#metric-count').innerText(),/1–1 of 1/);
      await page.selectOption('#metric-target','all');
      await page.locator('#metric-details > summary').click();
      assert.doesNotMatch(await page.locator('#metric-details').innerText(),/hypothetical_ROI/);
      await page.locator('#metric-details > summary').click();
      counts.modelMetricViews=(counts.modelMetricViews||0)+3;
      // Generic fixture only: compare separate arms, inspect complete membership,
      // and download local inventory without invoking a provider or owner run.
      await page.locator('#show-comparison').click();
      assert.equal(await page.locator('[data-comparison-game]').count(),25);
      assert.match(await page.locator('#results').innerText(),/Original frozen record/);
      assert.match(await page.locator('#results').innerText(),/Per-game rolling record not supplied/);
      await page.selectOption('#completion-filter','final');
      assert.equal(await page.locator('[data-comparison-game]').count(),1);
      assert.match(await page.locator('#filter-scope').innerText(),/1.*27.*26/s);
      const inventoryDownloadEvent=page.waitForEvent('download');
      await page.locator('#export-game-inventory').click();
      const inventoryDownload=await inventoryDownloadEvent;
      assert.equal(inventoryDownload.suggestedFilename(),'ncaa_filtered_game_inventory.json');
      const inventoryExport=JSON.parse(fs.readFileSync(await inventoryDownload.path(),'utf8'));
      assert.equal(inventoryExport.schema,'sports-edge-lab.private.game-inventory-export.v1');
      assert.equal(inventoryExport.filtered_source_game_count,1);
      assert.equal(inventoryExport.loaded_source_game_count,27);
      assert.equal(inventoryExport.hidden_by_filters,26);
      assert.equal(inventoryExport.games.length,1);
      assert.equal(inventoryExport.games[0].event_id,'invented-0');
      assert.match(inventoryExport.report_physical_pin.sha256,/^[a-f0-9]{64}$/);
      await page.locator('#reset-game-filters').click();
      assert.equal(await page.locator('#completion-filter').inputValue(),'all');
      assert.match(await page.locator('#filter-scope').innerText(),/27.*27.*0/s);
      await page.locator('#report-file').setInputFiles({name:'wrong-archive.pyz',mimeType:'application/zip',buffer:Buffer.from([80,75,3,4,0,0])});
      await page.waitForFunction(()=>document.querySelector('#load-status').textContent.includes('ZIP or PYZ'));
      assert.match(await page.locator('#load-status').innerText(),/Existing report remains unchanged/);
      assert.equal(await page.locator('[data-comparison-game]').count(),25);
      counts.comparisonInventoryViews=(counts.comparisonInventoryViews||0)+5;
      await page.locator('#show-games').click();
      counts.seasonTableViews=(counts.seasonTableViews||0)+4;
      assert.equal(await page.locator('[data-game]').count(), 25);
      assert.match(await page.locator('#results').innerText(), /Original frozen as issued/);
      assert.match(await page.locator('#results').innerText(), /Wrong/);
      assert.match(await page.locator('#results').innerText(), /precision: unknown/);
      assert.match(await page.locator('#results').innerText(), /Exact time disputed/);
      assert.equal(await page.locator('#results img').count(), 0);
      assert.equal(await page.evaluate(() => window.privateLeak), undefined);
      assert.match(await page.locator('[data-game]').first().innerText(),/Two hours before tip.*Actually captured by boundary/s);
      assert.match(await page.locator('[data-game]').first().innerText(),/Strictly before tip.*Later recovered source assertion/s);
      assert.match(await page.locator('[data-game]').first().innerText(),/Unrecognized information boundary.*Unrecognized report view/s);
      assert.equal(await page.locator('[data-injury-source]').count(),25);
      assert.match(await page.locator('#injury-source-count').innerText(),/1–25 of 28/);
      assert.match(await page.locator('#injury-source-results').innerText(),/Publication clock unknown or unqualified/);
      assert.match(await page.locator('#injury-source-results').innerText(),/Not selected in the supplied horizon audits/);
      assert.match(await page.locator('[data-game]').first().innerText(),/2026-11-04T19:45:00Z/);
      assert.doesNotMatch(await page.locator('[data-game]').first().innerText(),/2026-11-04T19:30:00Z/);
      assert.match(await page.locator('#injury-source-gaps > summary').innerText(),/1 supplied/);
      assert.equal(await page.locator('#injury-source-results img').count(),0);
      assert.equal(await page.locator('#injury-source-results a[href^="javascript:"]').count(),0);
      assert.equal(await page.evaluate(()=>window.injuryLeak),undefined);
      await page.locator('#injury-source-next').click();assert.match(await page.locator('#injury-source-count').innerText(),/26–28 of 28/);
      await page.locator('#injury-source-league').selectOption('ncaaw');assert.equal(await page.locator('[data-injury-source]').count(),3);
      await page.locator('#injury-source-search').fill('Named Player 26');assert.equal(await page.locator('[data-injury-source]').count(),1);
      await page.locator('#injury-source-search').fill('');await page.locator('#injury-source-league').selectOption('all');
      await page.locator('#injury-source-clock').selectOption('unknown');assert.match(await page.locator('#injury-source-count').innerText(),/of 27/);
      await page.locator('#injury-source-clock').selectOption('supplied');assert.equal(await page.locator('[data-injury-source]').count(),1);
      assert.match(await page.locator('#injury-source-results').innerText(),/Source-supported reconstruction at T−60/);
      await page.locator('#injury-source-clock').selectOption('all');await page.locator('#injury-source-league').selectOption('unknown');
      assert.equal(await page.locator('[data-injury-source]').count(),1);assert.match(await page.locator('#injury-source-results').innerText(),/Unresolved Player/);
      await page.locator('#injury-source-league').selectOption('all');
      assert.match(await page.locator('[data-game]').first().innerText(),/INVENTED_QUALIFIED_PAIR/);
      const invalidInjuries={...invented,injury_research:{...invented.injury_research,observations:[null]}};
      await page.locator('#report-file').setInputFiles({name:'invalid-injuries.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalidInjuries))});
      await page.waitForFunction(()=>document.getElementById('load-status').textContent.includes('Invalid or oversized availability source inventory'));
      assert.equal(await page.locator('[data-injury-source]').count(),25);
      assert.match(await page.locator('[data-game]').first().innerText(),/INVENTED_QUALIFIED_PAIR/);
      await page.locator('#report-file').setInputFiles({name:'invented-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invented))});
      await page.waitForFunction(()=>document.getElementById('load-status').textContent.startsWith('Loaded 27'));

      assert.match(await page.locator('[data-game]').nth(1).innerText(),/unrecognized structure; raw evidence remains/);

      counts.privateViewerStates++;
      assert.equal(await page.locator('#market-clock').inputValue(),'latest_pretip');
      assert.deepEqual(await page.locator('#market-clock option').allTextContents(),
        ['Price supported by T−120','Price supported by T−60','Latest supported pre-tip',
          'Latest actually captured before tip','Latest observed']);
      const firstGame=page.locator('[data-game]').first();
      const pairedBefore=await firstGame.locator('[data-strict-value]').allTextContents();
      const forecastBefore=await firstGame.locator('table').first().innerText();
      for(const [clock,price]of [['captured_t120','0.4000'],['captured_t60','0.5000'],['latest_pretip','0.6000'],['latest_observed','0.7000']]){
        await page.selectOption('#market-clock',clock);
        assert.equal(await firstGame.locator('[data-captured-value]').first().innerText(),price);
        assert.equal(await firstGame.locator('.market-table tbody tr').first().locator('[data-captured-value]').count(),1,'identical captures shared by streams appear once');
        assert.deepEqual(await firstGame.locator('[data-strict-value]').allTextContents(),pairedBefore);
        assert.equal(await firstGame.locator('table').first().innerText(),forecastBefore);
        assert.match(await firstGame.locator('.market-table tbody tr').first().innerText(),/0.3456/);
        assert.match(await firstGame.locator('.market-table tbody tr').first().innerText(),/0.2345/);
        assert.match(await firstGame.locator('.market-table').innerText(),/Acquired: 2026-11-05T01:00:00Z/);
        assert.match(await firstGame.locator('.market-table').innerText(),/Support ends:/);
        assert.match(await firstGame.locator('.market-table').innerText(),/History resolution \(seconds\): 60/);
        assert.match(await firstGame.locator('.market-table').innerText(),/Model cutoff: 2026-11-04T19:00:00Z/);
        assert.match(await firstGame.innerText(),/Spread: recover an exact eligible line/);
        const overflow=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,
          elements:[...document.querySelectorAll('main,main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!e.closest('.data-scroll');}).slice(0,12).map(e=>({tag:e.tagName,id:e.id,cls:e.className,right:e.getBoundingClientRect().right,text:(e.textContent||'').slice(0,60)}))}));
        assert.equal(overflow.overflow,false,`private ${width} ${clock} overflow: ${JSON.stringify(overflow.elements)}`);
        counts.captureClockViews++;
      }
      assert.match(await page.locator('#market-clock-note').innerText(),/may be after tip or after settlement/);
      await page.selectOption('#market-clock','latest_pretip');
      assert.match(await firstGame.locator('.market-table').innerText(),/0.2718.*Binary threshold probability/s);
      assert.match(await firstGame.innerText(),/Polymarket US: NOT ACQUIRED \/ UNVERIFIED/);
      await page.selectOption('#model','original_frozen');
      assert.equal(await firstGame.locator('[data-strict-value]').first().innerText(),'0.2345');
      await page.selectOption('#model','native_rolling_weekly_reconstruction');
      assert.equal(await firstGame.locator('[data-strict-value]').first().innerText(),'0.3456');
      const missingModel=page.locator('[data-game]').nth(1);
      assert.match(await missingModel.innerText(),/No record for this game/);
      assert.equal(await missingModel.locator('[data-captured-value]').first().innerText(),'0.8123');
      assert.match(await missingModel.locator('.market-table').innerText(),/No model record for the selected stream/);
      await page.selectOption('#market-clock','captured_t120');
      assert.equal(await missingModel.locator('[data-captured-value]').first().innerText(),'Unavailable','missing horizon cannot fall back to a later quote');
      await page.locator('#market-clock').focus();
      await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
      assert.equal(await page.locator('#market-clock').inputValue(),'captured_t60');counts.keyboardEvents++;
      await page.locator('#horizon-details > summary').click();
      assert.match(await page.locator('#horizon-details').innerText(),/Not evaluated in this report/);
      assert.equal(await page.locator('#horizon-details table').count(),0);
      counts.horizonMetricViews++;
      assert.match(await page.locator('#unclassified-details > summary').innerText(),/not supplied/);
      await page.locator('#unclassified-details > summary').click();
      assert.match(await page.locator('#unclassified-details').innerText(),/absence is not a zero-coverage claim/);
      assert.equal(await page.locator('#unclassified-details table').count(),0);
      await page.locator('#unclassified-details > summary').click();counts.unclassifiedSourceViews++;
      await page.locator('#horizon-details > summary').click();
      await page.selectOption('#market-clock','latest_pretip');
      if(process.env.DASHBOARD_SCREENSHOTS)await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-private-clocks-${width}.png`),fullPage:true});
      await page.locator('#next').click();
      assert.equal(await page.locator('[data-game]').count(), 2);
      await page.selectOption('#page-size', '100');
      await page.selectOption('#model', 'native_rolling_weekly_reconstruction');
      assert.equal(await page.locator('[data-game]').count(), 27);
      assert.match(await page.locator('#results').innerText(), /No record for this game/);
      counts.privateViewerStates++;
      await page.selectOption('#window', 'this_week');
      assert.equal(await page.locator('[data-game]').count(), 5);
      await page.selectOption('#window', 'season_to_date');
      assert.equal(await page.locator('[data-game]').count(), 1);
      await page.selectOption('#window', 'last_week');
      assert.equal(await page.locator('[data-game]').count(), 0);
      await page.selectOption('#window', 'all_observed');
      await page.selectOption('#league', 'ncaaw');
      assert.equal(await page.locator('[data-game]').count(), 3);
      await page.locator('#search').fill('Away 26');
      assert.equal(await page.locator('[data-game]').count(), 1);
      counts.privateViewerStates++;
      await page.locator('#search').fill('');
      await page.selectOption('#league', 'all');
      await page.locator('#show-observations').click();
      assert.equal(await page.locator('.observation').count(), 2);
      assert.equal(await page.locator('#market-clock-control').isHidden(),true);
      assert.equal(await page.locator('#market-clock-note').isHidden(),true);
      await page.selectOption('#binding', 'unresolved');
      assert.equal(await page.locator('.observation').count(), 1);
      assert.match(await page.locator('#results').innerText(), /unresolved-fixture/);
      assert.match(await page.locator('#results').innerText(), /0.3700/);
      assert.match(await page.locator('#results').innerText(), /Native Yes probability/);
      await page.locator('#results summary').click();
      assert.match(await page.locator('#results pre').innerText(), /canonical_identity_verified/);
      counts.privateViewerStates++;
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `private report ${width} overflow`);
      await page.locator('#report-file').setInputFiles({ name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from('{"schema":"wrong"}') });
      await page.waitForFunction(() => document.getElementById('load-status').classList.contains('error'));
      assert.match(await page.locator('#load-status').innerText(), /not a supported/);
      assert.equal(await page.locator('.observation').count(), 1);
      // Optional horizon metrics are report-only, with exact paired populations.
      const horizonReport={...invented,unclassified_market_observations:Array.from({length:27},(_,i)=>({provider:'Polymarket',provider_product:'polymarket_international',
        native_market_id:'invented-unclassified-token-'+i,native_source_value:.4321,native_token_value:.4321,
        timestamp:1700000000,acquired_at:'2026-11-05T01:00:00Z',resolution:0,prediction:null,
        semantic_status:'UNVERIFIED_ZERO_RESOLUTION_POINT_OR_FRACTIONAL_SETTLEMENT',
        pretip_price_eligible:false,comparison_eligible:false})),comparison_horizons:{schema:'sel.ncaa.b038.horizon_report.v1',
        horizons:['T120','T60','LATEST_PRETIP'],rows:3,paired_settled:1,paired_unsettled:1,unavailable:1,
        paired_metrics:[{league:'ncaam',season_end_year:2027,target:'win',horizon:'T60',provider:'Kalshi',
          provider_product:'Kalshi',track:'native_rolling_weekly_reconstruction',model_evidence_mode:'retrospective',
          paired_n:1,paired_membership_sha256:'invented-membership',model_metrics:{n:1,log_loss:.51,brier:.16,accuracy:1,auc:null},
          provider_metrics:{n:1,log_loss:.61,brier:.21,accuracy:1,auc:null}}]}};
      await page.locator('#report-file').setInputFiles({name:'invented-horizon-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(horizonReport))});
      await page.waitForFunction(()=>document.getElementById('load-status').textContent.startsWith('Loaded'));
      if(!(await page.locator('#horizon-details').evaluate(el=>el.open)))await page.locator('#horizon-details > summary').click();
      assert.match(await page.locator('#horizon-details').innerText(),/paired settled: 1.*paired unsettled: 1.*unavailable: 1/);
      assert.match(await page.locator('#horizon-details').innerText(),/Model issue clocks, forecast values and selections remain unchanged/);
      assert.match(await page.locator('#horizon-details').innerText(),/Log loss: 0.5100/);
      assert.match(await page.locator('#horizon-details').innerText(),/Log loss: 0.6100/);
      assert.match(await page.locator('#horizon-details').innerText(),/AUC: Unavailable/);
      assert.match(await page.locator('#horizon-details').innerText(),/invented-membership/);
      counts.horizonMetricViews++;
      assert.match(await page.locator('#unclassified-details > summary').innerText(),/27 supplied.*may include settlement/);
      if(!(await page.locator('#unclassified-details').evaluate(el=>el.open)))await page.locator('#unclassified-details > summary').click();
      await page.locator('#unclassified-details table').waitFor();
      assert.match(await page.locator('#unclassified-details').innerText(),/Source: 0.432100/);
      assert.match(await page.locator('#unclassified-details').innerText(),/Token: 0.432100/);
      assert.match(await page.locator('#unclassified-details').innerText(),/UNVERIFIED_ZERO_RESOLUTION_POINT_OR_FRACTIONAL_SETTLEMENT/);
      assert.match(await page.locator('#unclassified-details').innerText(),/not eligible pre-tip prices/);
      assert.equal(await page.locator('#summary .stat').nth(2).locator('strong').innerText(),'2');
      assert.equal((await page.locator('#results [data-captured-value]').allTextContents()).some(v=>v==='0.4321'),false);
      assert.equal((await page.locator('#results [data-strict-value]').allTextContents()).some(v=>v==='0.4321'),false);
      assert.equal(await page.locator('#unclassified-details table tbody tr').count(),25);
      assert.match(await page.locator('#unclassified-count').innerText(),/1–25 of 27/);
      await page.locator('#unclassified-next').click();
      assert.equal(await page.locator('#unclassified-details table tbody tr').count(),2);
      assert.match(await page.locator('#unclassified-count').innerText(),/26–27 of 27/);
      await page.locator('#unclassified-previous').click();
      assert.equal(await page.locator('#unclassified-details table tbody tr').count(),25);
      counts.unclassifiedSourceViews++;
      // Three-provider panels preserve supplied populations rather than deriving rankings.
      const providers=['Kalshi','Polymarket','DraftKings'];
      assert.deepEqual(await page.locator('#provider-cards h3').allTextContents(),providers);
      assert.match(await page.locator('#provider-count').innerText(),/not supplied/);
      assert.match(await page.locator('#provider-cards').innerText(),/Paired performance: unavailable/);
      assert.equal(await page.locator('#provider-populations table').count(),0);
      counts.providerComparisonViews++;
      const comparisonBase={league:'ncaam',season_end_year:2027,recipe:'invented-public-fixture',track:'original_frozen',
        implementation_source_sha256:'invented-source',target:'win',horizon_minutes:60,model_evidence_mode:'invented',
        quote_evidence_mode:'invented-source-observation',cohort_scope:'pairwise_provider'};
      const pairRows=providers.map((provider,i)=>({...comparisonBase,provider,n_paired:[11,7,5][i],cohort_sha256:'invented-pair-'+i,
        model_log_loss:.51+i*.01,provider_log_loss:.61+i*.01,model_brier:.16,provider_brier:.21,
        model_accuracy:.6,provider_accuracy:.5,model_calibration_bias:-.02,provider_calibration_bias:.04,
        model_ece_10_fixed_bins:.07,provider_ece_10_fixed_bins:.09,model_auc:null,provider_auc:null,
        n_directional_disagreements:[4,3,0][i],n_model_right_provider_wrong:[3,1,0][i],n_provider_right_model_wrong:[1,2,0][i],
        model_win_rate_on_disagreements:[.75,1/3,null][i],raw_fields:{model_auc:'',authored_text:'<img src=x onerror="window.providerLeak=true">'}}));
      const tableSource=(name,data,scope='pairwise_provider')=>({availability:data===null?'NOT_SUPPLIED':data.length?'SUPPLIED':'SUPPLIED_EMPTY',
        source:data===null?null:{filename:'invented-'+name+'.csv',bytes:123,sha256:'invented-source-pin',columns:['provider','n_paired'],source_rows:data.length},
        rows:data,cohort_scope:scope,common_provider_set_verified:scope==='all_requested_providers_common'?false:null});
      const commonRows=pairRows.map(r=>({...r,cohort_scope:'all_requested_providers_common',common_cohort_evidence_mode:'invented-common',n_paired:3,cohort_sha256:'invented-common-membership'}));
      const exactDisagreements=Array.from({length:27},(_,i)=>({...comparisonBase,provider:providers[i%3],event_id:'invented-disagreement-'+i,
        week_start_local:'2026-11-02',model_prediction:.6,provider_prediction:.4,model_minus_provider_probability:.2,
        model_correct:i%2,provider_correct:1-i%2,disagreement_result:i%2?'model_right_provider_wrong':'provider_right_model_wrong',
        cutoff_time:'2026-11-04T19:00:00Z',quote_time:'2026-11-04T18:59:00Z',quote_acquired_at:'2026-11-04T18:59:01Z',raw_fields:{event_id:'invented-disagreement-'+i}}));
      const providerReport={...invented,provider_comparisons:{schema:'sel.ncaa.b038.three_provider_report.v1',providers,
        common_provider_set_verified:false,common_population_status:'UNVERIFIED_ACTIVE_THREE_PROVIDER_SET',polymarket_us:null,
        tables:{season_provider:tableSource('season-provider',[...pairRows,...Array.from({length:4},(_,i)=>({...pairRows[0],recipe:'invented-context-'+i})),
          {...pairRows[0],league:'ncaaw',track:'native_rolling_weekly_reconstruction'},
          {...pairRows[0],target:'margin',model_mae:9.2,provider_mae:10.3,model_rmse:12.2,provider_rmse:13.3,model_bias_prediction_minus_actual:-.2,provider_bias_prediction_minus_actual:.3}]),
          week_provider:tableSource('week-provider',pairRows.map(r=>({...r,n_paired:3,week_start_local:'2026-11-02'}))),
          season_common:tableSource('season-common',commonRows,'all_requested_providers_common'),
          week_common:tableSource('week-common',null,'all_requested_providers_common'),disagreements:tableSource('disagreements',exactDisagreements)},
        excluded_lineage:[{reason:'old-all-six-is-not-active-three',row:{provider:'MARKET',cohort_scope:'all_six_providers_common'}}]}};
      await page.locator('#report-file').setInputFiles({name:'invented-provider-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(providerReport))});
      await page.locator('#provider-populations table').first().waitFor();
      assert.deepEqual(await page.locator('#provider-cards h3').allTextContents(),providers);
      assert.match(await page.locator('#provider-count').innerText(),/1–4 of 6 separate population contexts/);
      const firstPopulation=page.locator('.comparison-population').first();
      assert.deepEqual(await firstPopulation.locator('tbody tr td:nth-child(2) > span').allTextContents(),['11Membership: invented-pair-0','7Membership: invented-pair-1','5Membership: invented-pair-2']);
      assert.match(await firstPopulation.innerText(),/Model right \/ provider wrong: 3/);
      assert.match(await firstPopulation.innerText(),/Provider right \/ model wrong: 2/);
      assert.match(await firstPopulation.innerText(),/AUC: Unavailable/);
      assert.match(await firstPopulation.innerText(),/Directional disagreements: 0/);
      assert.match(await firstPopulation.innerText(),/Product identity not supplied/);
      assert.match(await page.locator('#provider-cards').innerText(),/US status: not supplied \/ unverified/);
      assert.match(await page.locator('#provider-cards').innerText(),/Coverage, information time and comparable product semantics/);
      await firstPopulation.locator('summary').first().click();
      await firstPopulation.locator('pre').waitFor();
      assert.match(await firstPopulation.locator('pre').innerText(),/"model_auc": ""/);
      assert.equal(await firstPopulation.locator('img').count(),0);
      assert.equal(await page.evaluate(()=>window.providerLeak),undefined);
      await page.locator('#provider-next').click();
      assert.match(await page.locator('#provider-count').innerText(),/5–6 of 6/);
      await page.locator('#provider-previous').click();
      assert.equal(await page.locator('#provider-disagreements tbody tr').count(),25);
      assert.match(await page.locator('#provider-disagreements').innerText(),/model_right_provider_wrong/);
      assert.match(await page.locator('#provider-disagreements').innerText(),/provider_right_model_wrong/);
      assert.match(await page.locator('#provider-disagreements').innerText(),/Model: Correct/);
      assert.match(await page.locator('#provider-disagreements').innerText(),/Provider: Wrong/);
      await page.locator('#provider-disagreement-next').click();
      assert.equal(await page.locator('#provider-disagreements tbody tr').count(),2);
      assert.match(await page.locator('#provider-disagreement-count').innerText(),/26–27 of 27/);
      await page.locator('#provider-disagreement-previous').click();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`provider comparison ${width} overflow`);
      if(process.env.DASHBOARD_SCREENSHOTS)await page.locator('#provider-review').screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-three-providers-${width}.png`)});
      counts.providerComparisonViews++;
      await page.selectOption('#provider-cohort','common');
      assert.match(await page.locator('#provider-comparison-status').innerText(),/Active three-provider set unverified/);
      assert.match(await page.locator('#provider-populations').innerText(),/Three-way comparison remains unverified/);
      assert.equal(await page.locator('#provider-populations tbody tr').count(),3);
      counts.providerComparisonViews++;
      await page.selectOption('#provider-period','week');
      assert.match(await page.locator('#provider-count').innerText(),/not supplied/);
      await page.selectOption('#provider-cohort','provider');
      await page.selectOption('#provider-week','2026-11-02');
      assert.match(await page.locator('#provider-count').innerText(),/1–1 of 1 separate population contexts/);
      assert.match(await page.locator('#provider-populations').innerText(),/week: 2026-11-02/);
      await page.selectOption('#provider-league','ncaaw');
      assert.equal(await page.locator('#provider-populations table').count(),0);
      assert.match(await page.locator('#provider-disagreements').innerText(),/None in the supplied/);
      await page.selectOption('#provider-period','season');
      await page.selectOption('#provider-stream','native_rolling_weekly_reconstruction');
      assert.match(await page.locator('#provider-populations').innerText(),/Women/);
      assert.match(await page.locator('#provider-populations').innerText(),/No row supplied/);
      counts.providerComparisonViews++;
      await page.selectOption('#provider-stream','all');await page.selectOption('#provider-league','all');
      await page.locator('#provider-target').focus();await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
      assert.equal(await page.locator('#provider-target').inputValue(),'margin');counts.keyboardEvents++;
      assert.match(await page.locator('#provider-populations').innerText(),/MAE: 9.2000/);
      assert.match(await page.locator('#provider-populations').innerText(),/Bias: -0.2000/);
      assert.match(await page.locator('#provider-disagreements').innerText(),/No comparable point\/threshold disagreement records/);
      counts.providerComparisonViews++;
      const commonVerified=structuredClone(providerReport);commonVerified.provider_comparisons.common_provider_set_verified=true;
      commonVerified.evidence_release='INVENTED_COMMON_VERIFIED_FIXTURE';
      commonVerified.provider_comparisons.tables.season_common.common_provider_set_verified=true;
      commonVerified.provider_comparisons.tables.week_common=tableSource('week-common',[],'all_requested_providers_common');
      commonVerified.provider_comparisons.tables.disagreements=tableSource('disagreements',[]);
      await page.locator('#report-file').setInputFiles({name:'invented-common-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(commonVerified))});
      // The preceding margin view already displays zero disagreements. Wait for
      // the new fixture's own metadata, not a stale count from the prior report.
      await page.waitForFunction(()=>{
        try{return JSON.parse(document.getElementById('metadata').textContent).evidence_release==='INVENTED_COMMON_VERIFIED_FIXTURE'&&
          document.getElementById('load-status').textContent.startsWith('Loaded ')&&document.getElementById('provider-target').value==='win';}
        catch{return false;}
      });
      await page.selectOption('#provider-cohort','common');
      assert.match(await page.locator('#provider-populations').innerText(),/Supplied common-game membership and paired N match across all three/);
      await page.selectOption('#provider-period','week');
      assert.match(await page.locator('#provider-comparison-status').innerText(),/Supplied empty/);
      assert.match(await page.locator('#provider-cards').innerText(),/None in supplied disagreement rows/);
      assert.equal(await page.locator('#provider-populations table').count(),0);
      counts.providerComparisonViews++;
      const malformed=structuredClone(providerReport);malformed.provider_comparisons.tables.season_provider.rows='invalid';
      await page.locator('#report-file').setInputFiles({name:'invalid-provider-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(malformed))});
      await page.waitForFunction(()=>document.getElementById('load-status').classList.contains('error'));
      assert.match(await page.locator('#load-status').innerText(),/Invalid comparison row inventory/);
      assert.match(await page.locator('#provider-comparison-status').innerText(),/Supplied empty/);
      counts.providerComparisonViews++;
      // A large captured inventory is not an empty inventory merely because
      // the small report omits its rows. Source clocks remain independent.
      const sparseReport={...invented,market_observations:[],market_observation_count:500000,
        market_observations_inline_complete:false,freshness:{season_label:'2026–27',season_end_year:2027,
          report_generated_at_utc:'2026-11-05T02:00:00Z',report_asof_utc:'2026-11-04T20:00:00Z',
          data_acquisition_completed_at_utc:null,last_successful_refresh_at_utc:null,
          last_attempted_refresh_at_utc:'2026-11-04T21:00:00Z',last_attempt_status:'FAILED_PARTIAL'},
        unclassified_market_observations:[],unclassified_market_observation_count:3,
        unclassified_market_observation_dataset:{status:'REFERENCE_ONLY_FIXTURE'},
        window_event_keys:{...invented.window_event_keys,next_week:[[rows[26].league,rows[26].event_id]]}};
      sparseReport.records=structuredClone(invented.records);
      sparseReport.records[0].time_precision='exact';sparseReport.records[0].event_time='2026-11-04T20:30:00Z';
      sparseReport.records[1].time_precision='exact';sparseReport.records[1].event_time='2026-11-04T20:30:00Z';
      sparseReport.records[1].kalshi_latest_pretip_win_quote_time='2026-11-04T20:00:00Z';
      sparseReport.records[1].kalshi_latest_pretip_win_acquired_at='2026-11-04T20:00:01Z';
      await page.locator('#report-file').setInputFiles({name:'invented-sparse-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(sparseReport))});
      await page.waitForFunction(()=>document.querySelector('#summary .stat:nth-child(3) strong').textContent==='500,000');
      assert.equal(await page.locator('#summary .stat').nth(3).locator('strong').innerText(),'0');
      assert.match(await page.locator('#observation-scope').innerText(),/0 rows loaded; 500,000 captured observations/);
      assert.match(await page.locator('#freshness-grid').innerText(),/2026–27.*ends 2027/s);
      assert.equal(await page.locator('.clock-card').filter({hasText:'Last successful refresh'}).locator('strong').innerText(),'Unavailable');
      assert.equal(await page.locator('.clock-card').filter({hasText:'Data acquisition completed'}).locator('strong').innerText(),'Unavailable');
      assert.equal(await page.locator('.clock-card').filter({hasText:'Last attempted refresh'}).locator('strong').innerText(),'2026-11-04T21:00:00Z');
      assert.equal(await page.locator('.clock-card').filter({hasText:'Report generated'}).locator('strong').innerText(),'2026-11-05T02:00:00Z');
      assert.equal(await page.locator('#market-clock option:checked').innerText(),'Latest supported pre-tip');
      assert.match(await page.locator('[data-game]').first().innerText(),/Capture before tip: false.*recovered at or after tip/s);
      assert.match(await page.locator('[data-game]').nth(1).innerText(),/Capture before tip: true/);
      assert.match(await page.locator('[data-game]').nth(2).innerText(),/Capture before tip: unverified/);
      await page.selectOption('#window','next_week');assert.equal(await page.locator('[data-game]').count(),1);
      await page.selectOption('#window','all_observed');
      await page.locator('#show-observations').click();
      assert.match(await page.locator('#results').innerText(),/preserved observations but has no inline rows/);
      assert.match(await page.locator('#unclassified-details > summary').innerText(),/3 preserved.*0 loaded/);
      counts.freshnessViews++;counts.boundedInventoryViews++;
      // Local files are invented. One physical chunk is validated without
      // claiming that unselected chunks or the full logical archive were read.
      const digest=b=>createHash('sha256').update(b).digest('hex');
      const reference=(name,b)=>({key:'invented/'+name,bytes:b.length,sha256:digest(b)});
      const chunks=[Buffer.from(JSON.stringify({provider:'Kalshi',native_event_id:'invented-local-only',canonical_identity_verified:false,native_source_value:.4321})+'\n'+JSON.stringify({provider:'DraftKings',event_id:'invented-0',league:'ncaam',canonical_identity_verified:true})+'\n'),
        Buffer.from(JSON.stringify({provider:'Polymarket',provider_product:'polymarket_international',canonical_identity_verified:false})+'\n')];
      const meta=Buffer.from('{}\n');let byteStart=0,recordStart=0;
      const descriptors=chunks.map((body,i)=>{const value={schema:'sel.ncaa.b039.chunk_index.v1',ordinal:i,record_start:recordStart,records:i===0?2:1,
        logical_byte_start:byteStart,reference:reference('data-'+i,body),metadata_reference:reference('metadata-'+i,meta)};
        byteStart+=body.length;recordStart+=value.records;return value;});
      const indexBody=Buffer.from(descriptors.map(r=>JSON.stringify(r)).join('\n')+'\n');
      const manifest={schema:'sel.ncaa.b039.chunked_rows.v1',status:'COMMITTED',logical_encoding:'canonical_json_object_per_line_utf8',
        records:3,chunks:2,logical_bytes:byteStart,logical_sha256:digest(Buffer.concat(chunks)),chunk_sequence_sha256:digest(indexBody),
        parts:[{ordinal:0,reference:reference('index-part',indexBody),chunk_start:0,chunks:2,record_start:0,records:3,logical_byte_start:0,logical_bytes:byteStart}]};
      const chunkedReport={...sparseReport,market_observation_count:3,market_observation_dataset:{manifest},
        unclassified_market_observation_dataset:{manifest}};
      await page.locator('#report-file').setInputFiles({name:'invented-chunk-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(chunkedReport))});
      await page.waitForFunction(()=>document.querySelector('#summary .stat:nth-child(3) strong').textContent==='3');
      const forecastAfterImport=await page.locator('[data-game]').first().locator('table').first().innerText();
      if(!(await page.locator('#chunk-details').evaluate(el=>el.open)))await page.locator('#chunk-details > summary').click();
      await page.locator('#chunk-index-file').setInputFiles({name:'invented-index.jsonl',mimeType:'application/x-ndjson',buffer:indexBody});
      await page.waitForFunction(()=>document.getElementById('chunk-status').textContent.startsWith('Index part 1 / 1 verified'));
      assert.equal(await page.locator('#chunk-data-file').isDisabled(),false);
      await page.locator('#chunk-data-file').setInputFiles({name:'invented-data.jsonl',mimeType:'application/x-ndjson',buffer:chunks[0]});
      await page.waitForFunction(()=>document.getElementById('chunk-status').textContent.startsWith('Data chunk 1 / 2 verified'));
      assert.equal(await page.locator('.observation').count(),2);
      assert.match(await page.locator('#results').innerText(),/invented-local-only/);
      assert.equal(await page.locator('#summary .stat').nth(2).locator('strong').innerText(),'3');
      assert.equal(await page.locator('#summary .stat').nth(3).locator('strong').innerText(),'2');
      assert.match(await page.locator('#chunk-status').innerText(),/full logical archive have not been verified/);
      assert.match(await page.locator('#observation-scope').innerText(),/Verified bounded chunk 1 of 2/);
      const corrupt=Buffer.from(chunks[0]);corrupt[10]^=1;
      await page.locator('#chunk-data-file').setInputFiles({name:'invented-corrupt.jsonl',mimeType:'application/x-ndjson',buffer:corrupt});
      await page.waitForFunction(()=>document.getElementById('chunk-status').classList.contains('error'));
      assert.match(await page.locator('#chunk-status').innerText(),/SHA-256 do not match/);
      assert.equal(await page.locator('.observation').count(),2,'bad data must retain previous valid view');
      await page.locator('#show-games').click();
      assert.equal(await page.locator('[data-game]').first().locator('table').first().innerText(),forecastAfterImport);
      await page.locator('#restore-inline').click();
      assert.equal(await page.locator('#summary .stat').nth(3).locator('strong').innerText(),'0');
      // Unknown or wrong indexes cannot enable a data preview.
      await page.locator('#chunk-index-file').setInputFiles({name:'invented-wrong-index.jsonl',mimeType:'application/x-ndjson',buffer:Buffer.from('{}\n')});
      await page.waitForFunction(()=>document.getElementById('chunk-status').classList.contains('error'));
      assert.equal(await page.locator('#chunk-data-file').isDisabled(),true);
      await page.selectOption('#chunk-kind','unclassified');
      await page.locator('#chunk-index-file').setInputFiles({name:'invented-index.jsonl',mimeType:'application/x-ndjson',buffer:indexBody});
      await page.waitForFunction(()=>document.getElementById('chunk-status').textContent.startsWith('Index part 1 / 1 verified'));
      await page.locator('#chunk-data-file').setInputFiles({name:'invented-data.jsonl',mimeType:'application/x-ndjson',buffer:chunks[0]});
      await page.waitForFunction(()=>document.getElementById('chunk-status').textContent.startsWith('Data chunk 1 / 2 verified'));
      assert.match(await page.locator('#unclassified-details > summary').innerText(),/3 preserved.*2 loaded/);
      assert.match(await page.locator('#unclassified-details').innerText(),/Source: 0.432100/);
      assert.equal(await page.locator('[data-game]').first().locator('table').first().innerText(),forecastAfterImport);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'bounded preview must fit mobile viewport');
      counts.boundedInventoryViews+=5;
      // Shared-field rows and report-part indexes use only invented values.
      // The complete dense game/model universe is never constructed by the UI.
      const normalizedSchema='sports-edge-lab.private.game-report.normalized.v1';
      const canonical=value=>JSON.stringify(Object.fromEntries(Object.keys(value).sort().map(k=>[k,value[k]])))+'\n';
      const normalize=(sourceRows,metadata={})=>{
        const contexts=[],records=[],known=new Map(),flat=[];
        for(const input of sourceRows){const row=Object.fromEntries(Object.entries(input).filter(([k,v])=>v!==null&&v!=='')),shared={},own={};
          for(const [key,value]of Object.entries(row)){
            if(['league','event_id','home_team','away_team','source_date','time_precision','phase','event_time'].includes(key)||/^(kalshi|polymarket|draftkings)_/.test(key))shared[key]=value;
            else own[key]=value;
          }
          const encoded=canonical(shared);let id=known.get(encoded);if(id===undefined){id=contexts.length;contexts.push(shared);known.set(encoded,id);}
          records.push({...own,context_ids:[id]});flat.push(Buffer.from(canonical(row)));
        }
        const logical=Buffer.concat(flat);
        return {...metadata,schema:normalizedSchema,record_count:records.length,records,contexts,
          record_encoding:{schema:'sel.ncaa.b040.shared_fields.v1',context_field:'context_ids',merge_policy:'DISJOINT_CONTEXT_FIELDS_THEN_DISJOINT_RECORD_FIELDS',
            flat_encoding:'canonical_json_object_per_line_utf8',flat_logical_bytes:logical.length,flat_logical_sha256:digest(logical),fields_recomputed:false,new_forecasts:0,new_fits:0}};
      };
      const sourceRows=structuredClone(invented.records);sourceRows[0].prediction_margin=0;sourceRows[0].model_winner_pick_correct=false;
      sourceRows[0].kalshi_captured_before_tip_win_value=.1234;
      sourceRows[0].kalshi_captured_before_tip_win_quote_time='2026-11-04T18:00:00Z';
      sourceRows[0].kalshi_captured_before_tip_win_acquired_at='2026-11-04T18:00:01Z';
      const unresolved=Array.from({length:4},(_,i)=>({league:i%2?'ncaaw':'ncaam',date:'2026-11-04',row_index:i,
        reason:'INVENTED_TEAM_ID_MISSING',source_record_retention_status:'AUTHENTICATED_ORIGINAL_RAW_RECORD_RETAINED_REPORT_ONLY',
        canonical_identity_status:'UNRESOLVED',counted_as_new_physical_game:false,
        raw_source_record:{contestId:100+i,hasStartTime:false,teams:[{nativeTeamId:null,sourceLabel:'Unresolved invented source '+i,isHome:null}]}}));
      const normalized=normalize(sourceRows,{...invented,unresolved_official_records:unresolved});
      // Page size is an intentional user preference retained across imports.
      // Earlier cases selected 100; this case explicitly exercises 25-row paging.
      await page.selectOption('#page-size','25');
      await page.locator('#report-file').setInputFiles({name:'invented-normalized.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(normalized))});
      await page.waitForFunction(()=>{
        try{return JSON.parse(document.getElementById('metadata').textContent).schema==='sports-edge-lab.private.game-report.normalized.v1'&&
          document.getElementById('record-scope').textContent.includes('28 of 28 game/model rows loaded');}catch{return false;}
      });
      for(const [selector,expected]of [['#page-size','25'],['#league','all'],['#window','all_observed'],
        ['#model','all'],['#search',''],['#market-clock','latest_pretip']])assert.equal(await page.locator(selector).inputValue(),expected);
      assert.equal(await page.locator('#show-games').getAttribute('aria-pressed'),'true');
      assert.equal(await page.locator('[data-game]').count(),25);
      assert.equal(await page.locator('#summary .stat').nth(0).locator('strong').innerText(),'27');
      assert.equal(await page.locator('#summary .stat').nth(1).locator('strong').innerText(),'28');
      assert.match(await page.locator('[data-game]').first().locator('table').first().innerText(),/0\.00/);
      assert.match(await page.locator('[data-game]').first().locator('table').first().innerText(),/Wrong/);
      const sharedMetadata=JSON.parse(await page.locator('#metadata').textContent());
      assert.equal(sharedMetadata.contexts,undefined);assert.equal(sharedMetadata.records,undefined);
      assert.equal(sharedMetadata.shared_context_count,normalized.contexts.length);
      await page.selectOption('#market-clock','captured_before_tip');
      assert.equal(await page.locator('[data-game]').first().locator('[data-captured-value]').first().innerText(),'0.1234');
      assert.match(await page.locator('#market-clock-note').innerText(),/actual acquisition to precede/);
      assert.equal(await page.locator('[data-game]').nth(1).locator('[data-captured-value]').first().innerText(),'Unavailable','missing actual-capture evidence is never filled from historical support');
      await page.selectOption('#market-clock','latest_pretip');
      assert.equal(await page.locator('[data-game]').first().locator('[data-captured-value]').first().innerText(),'0.6000');
      await page.selectOption('#window','this_week');assert.equal(await page.locator('[data-game]').count(),5);
      await page.selectOption('#window','all_observed');await page.selectOption('#league','ncaaw');assert.equal(await page.locator('[data-game]').count(),3);
      await page.locator('#search').fill('Home 26');assert.equal(await page.locator('[data-game]').count(),1);
      await page.locator('#search').fill('');await page.selectOption('#league','all');
      await page.selectOption('#model','original_frozen');
      assert.match(await page.locator('[data-game]').first().locator('table').first().innerText(),/45\.7%/);
      assert.match(await page.locator('[data-game]').nth(1).locator('table').first().innerText(),/No record for this game/);
      await page.selectOption('#model','all');
      const rowDetails=page.locator('[data-game]').first().locator('details').filter({has:page.locator('summary', {hasText:'All source, issue, training and quote clocks'})});
      await rowDetails.locator('summary').click();
      await rowDetails.locator('pre').waitFor();
      const flatDetail=JSON.parse(await rowDetails.locator('pre').textContent());
      assert.equal(flatDetail[0].prediction_margin,0);assert.equal(flatDetail[0].model_winner_pick_correct,false);
      assert.equal(flatDetail[0].league,'ncaam');assert.equal(flatDetail[0].context_ids,undefined);
      assert.match(await page.locator('#unresolved-official-details > summary').innerText(),/4 supplied/);
      if(!(await page.locator('#unresolved-official-details').evaluate(el=>el.open)))await page.locator('#unresolved-official-details > summary').click();
      // Native <details> dispatches toggle asynchronously; its source cards
      // are intentionally constructed by that handler, after the click.
      await page.locator('[data-unresolved-official]').first().waitFor();
      assert.equal(await page.locator('[data-unresolved-official]').count(),4);
      assert.match(await page.locator('#unresolved-official-details').innerText(),/source row 0/);
      assert.equal(await page.locator('#summary .stat').nth(0).locator('strong').innerText(),'27','unresolved native rows never invent extra physical games');
      assert.equal(await page.evaluate(()=>window.privateLeak),undefined);
      const beforeInvalid=await page.locator('[data-game]').first().locator('table').first().innerText();
      const malformedNormalized=[];
      for(const ids of [[true],[-1],[normalized.contexts.length],[0,0]]){const bad=structuredClone(normalized);bad.records[0].context_ids=ids;malformedNormalized.push(bad);}
      const collision=structuredClone(normalized);collision.records[0].league='ncaam';malformedNormalized.push(collision);
      const sharedCollision=structuredClone(normalized);sharedCollision.contexts.push({league:'ncaam'});sharedCollision.records[0].context_ids.push(sharedCollision.contexts.length-1);malformedNormalized.push(sharedCollision);
      for(const bad of malformedNormalized){await page.locator('#report-file').setInputFiles({name:'invented-invalid-normalized.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
        await page.waitForFunction(()=>document.getElementById('load-status').classList.contains('error')&&
          document.getElementById('load-status').textContent.startsWith('Cannot open report:'));
        assert.equal(await page.locator('[data-game]').first().locator('table').first().innerText(),beforeInvalid);}
      counts.normalizedReportViews=(counts.normalizedReportViews||0)+12;

      const partRows=[sourceRows.slice(0,12),sourceRows.slice(12)];
      const parts=partRows.map((rs,i)=>normalize(rs,{...invented,part_ordinal:i,global_record_count:28,part_scope:'COMPLETE_ROWS_IN_THIS_PART_ONLY'}));
      const partBodies=parts.map(p=>Buffer.from(JSON.stringify(p)+'\n'));let start=0;
      const partRefs=parts.map((p,i)=>{const descriptor={ordinal:i,record_start:start,records:p.record_count,reference:reference('invented-report-part-'+i,partBodies[i]),flat_logical_bytes:p.record_encoding.flat_logical_bytes,flat_logical_sha256:p.record_encoding.flat_logical_sha256};start+=p.record_count;return descriptor;});
      const reportIndex={...invented,schema:'sports-edge-lab.private.game-report.index.v1',record_count:28,records:[],records_inline_complete:false,
        record_part_schema:normalizedSchema,record_parts:partRefs,max_part_bytes:64*1024*1024,
        flat_logical_bytes:partRefs.reduce((sum,p)=>sum+p.flat_logical_bytes,0),flat_logical_sha256:normalized.record_encoding.flat_logical_sha256,
        unloaded_rows:28,loaded_rows:0};
      await page.locator('#report-file').setInputFiles({name:'invented-report-index.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(reportIndex))});
      await page.waitForFunction(()=>document.getElementById('record-scope').textContent.includes('0 of 28 game/model rows loaded'));
      assert.equal(await page.locator('#summary .stat').nth(1).locator('strong').innerText(),'28');
      assert.equal(await page.locator('[data-game]').count(),0);assert.match(await page.locator('#results').innerText(),/preserved but unloaded/);
      if(!(await page.locator('#record-part-details').evaluate(el=>el.open)))await page.locator('#record-part-details > summary').click();
      await page.locator('#record-part-file').setInputFiles({name:'invented-part-0.json',mimeType:'application/json',buffer:partBodies[0]});
      await page.waitForFunction(()=>document.getElementById('record-part-status').textContent.startsWith('Part 1 / 2 verified'));
      assert.match(await page.locator('#record-scope').innerText(),/global rows 1–12.*12 of 28.*16 rows unloaded/);
      assert.equal(await page.locator('[data-game]').count(),12);
      const firstPartForecast=await page.locator('[data-game]').first().locator('table').first().innerText();
      await page.locator('#record-part-file').setInputFiles({name:'invented-wrong-part.json',mimeType:'application/json',buffer:partBodies[1]});
      await page.waitForFunction(()=>document.getElementById('record-part-status').classList.contains('error'));
      assert.match(await page.locator('#record-part-status').innerText(),/bytes or SHA-256/);
      assert.equal(await page.locator('[data-game]').first().locator('table').first().innerText(),firstPartForecast);
      await page.selectOption('#record-part-selection','1');
      await page.locator('#record-part-file').setInputFiles({name:'invented-part-1.json',mimeType:'application/json',buffer:partBodies[1]});
      await page.waitForFunction(()=>document.getElementById('record-part-status').textContent.startsWith('Part 2 / 2 verified'));
      assert.match(await page.locator('#record-scope').innerText(),/global rows 13–28.*16 of 28.*12 rows unloaded/);
      assert.equal(await page.locator('[data-game]').count(),16);
      await page.selectOption('#league','ncaaw');assert.equal(await page.locator('[data-game]').count(),3);
      await page.locator('#clear-record-part').click();assert.equal(await page.locator('[data-game]').count(),0);
      assert.match(await page.locator('#record-scope').innerText(),/0 of 28.*28 rows unloaded/);
      const reordered=structuredClone(reportIndex);reordered.record_parts.reverse();
      await page.locator('#report-file').setInputFiles({name:'invented-invalid-index.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(reordered))});
      await page.waitForFunction(()=>document.getElementById('load-status').classList.contains('error')&&
        document.getElementById('load-status').textContent.startsWith('Cannot open report:'));
      assert.match(await page.locator('#load-status').innerText(),/order/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'normalized report and local part chooser fit mobile');
      counts.reportPartViews=(counts.reportPartViews||0)+7;
      await page.locator('#clear').click();
      assert.equal(await page.locator('#freshness-grid').textContent(),'');
      assert.equal(await page.locator('#observation-scope').textContent(),'');
      assert.equal(await page.locator('#chunk-status').textContent(),'');
      assert.equal(await page.locator('#chunk-data-file').isDisabled(),true);
      assert.equal(await page.locator('#report').isHidden(), true);
      assert.equal(await page.locator('#results').textContent(), '');
      assert.equal(await page.locator('#asof').textContent(), '');
      assert.equal(await page.locator('#metadata').textContent(), '');
      assert.equal(await page.locator('#horizon-details').textContent(),'Paired metrics by market reference horizon');
      assert.equal(await page.locator('#unclassified-details').textContent(),'Unclassified source observations');
      assert.equal(await page.locator('#market-clock-note').textContent(),'');
      for(const id of ['provider-cards','provider-populations','provider-disagreements','provider-source-audit'])assert.equal(await page.locator('#'+id).textContent(),'');
      assert.equal(await page.locator('#model option').count(), 1);
      assert.match(await page.locator('#load-status').innerText(), /cleared/);
      counts.privateViewerStates++;
      {
      const researchRecords=[{league:'ncaam',event_id:'invented-frontier',family:'ridge',target:'margin',status:'DEFERRED_MISSING_LABEL_CLOCK',reason:'MISSING_LABEL_CLOCK',training_cutoff:'2026-11-04T18:00:00Z'},{league:'ncaaw',event_id:'invented-frontier-2',provider:'Kalshi',status:'UNAVAILABLE',reason:'EXACT_LINE_SEMANTICS_REQUIRED'}];
      const logical=Buffer.from(researchRecords.map(r=>JSON.stringify(r)).join('\n')+'\n'), compressed=gzipSync(logical);
      const manifest={schema:'sel.ncaa.b047.jsonl_parts.v1',name:'B047_frontier_inventory',records:2,logical_bytes:logical.length,logical_sha256:createHash('sha256').update(logical).digest('hex'),parts:[{filename:'B047_frontier_inventory.part00001.jsonl.gz',bytes:compressed.length,sha256:createHash('sha256').update(compressed).digest('hex'),records:2,logical_bytes:logical.length}]};
      const summary={schema:'sel.ncaa.b047.frontier.v1',model_registry:[{family:'ridge',targets:['margin','total'],library:'sklearn',dependency_status:'AVAILABLE',implementation_status:'IMPLEMENTED',calibration_status:'CANDIDATE'}],streams:{inventory:manifest}};
      await page.locator('#research-manifest-file').setInputFiles({name:'invented-frontier.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(summary))});
      await page.waitForFunction(()=>document.getElementById('research-load-status').textContent.startsWith('Manifest loaded'));
      assert.equal(await page.locator('[data-research-row]').count(),0);
      assert.match(await page.locator('#research-registry').innerText(),/ridge.*sklearn \/ AVAILABLE/s);
      await page.locator('#research-part-file').setInputFiles({name:manifest.parts[0].filename,mimeType:'application/gzip',buffer:compressed});
      await page.waitForFunction(()=>document.getElementById('research-load-status').textContent.startsWith('Verified selected part'));
      assert.equal(await page.locator('[data-research-row]').count(),2);
      assert.match(await page.locator('#research-records').innerText(),/Recover the missing original source, label or completion clock/);
      await page.locator('#research-search').fill('Kalshi');assert.equal(await page.locator('[data-research-row]').count(),1);await page.locator('#research-search').fill('');
      const corrupt=Buffer.from(compressed);corrupt[12]^=1;
      await page.locator('#research-part-file').setInputFiles({name:manifest.parts[0].filename,mimeType:'application/gzip',buffer:corrupt});
      await page.waitForFunction(()=>document.getElementById('research-load-status').textContent.includes('SHA256 mismatch'));
      assert.equal(await page.locator('[data-research-row]').count(),2);
      const bad=structuredClone(manifest);bad.parts.push({...bad.parts[0]});
      await page.locator('#research-manifest-file').setInputFiles({name:'invented-duplicate.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
      await page.waitForFunction(()=>document.getElementById('research-load-status').textContent.includes('duplicate research part'));
      assert.equal(await page.locator('[data-research-row]').count(),2);
      const empty={...manifest,records:0,parts:[],logical_bytes:0,logical_sha256:createHash('sha256').update('').digest('hex')};
      await page.locator('#research-manifest-file').setInputFiles({name:'invented-zero.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(empty))});
      await page.waitForFunction(()=>document.getElementById('research-records').textContent.includes('explicitly contains zero'));
      assert.equal(await page.locator('#research-part-file').isDisabled(),true);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'bounded research viewer fits mobile');
      counts.researchPartViews=(counts.researchPartViews||0)+6;
      }
      {
        const identityFixture=identityOverlayFixture();
        await page.locator('#report-file').setInputFiles({name:'invented-identity-baseline.json',mimeType:'application/json',buffer:identityFixture.body});
        await page.waitForFunction(()=>document.getElementById('load-status').textContent.startsWith('Loaded 3 source game records'));
        await page.locator('#show-games').click();
        const sourceIdsBefore=await page.locator('[data-game]').evaluateAll(nodes=>nodes.map(n=>n.dataset.game));
        const predictionsBefore=await page.locator('[data-game] table:first-of-type').allTextContents();
        const metricsBefore=await page.locator('#model-metrics').innerText();
        await page.locator('#identity-overlay-file').setInputFiles({name:'invented-identity-overlay.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(identityFixture.overlay))});
        await page.waitForFunction(()=>document.getElementById('identity-overlay-status').textContent.startsWith('Verified baseline binding'));
        assert.match(await page.locator('#identity-overlay-count').innerText(),/3 original source-game IDs → 2 groups.*1 supplied identity links.*4 original game\/model rows retained/);
        assert.equal(await page.locator('[data-identity-link]').count(),1);
        assert.deepEqual(await page.locator('[data-game]').evaluateAll(nodes=>nodes.map(n=>n.dataset.game)),sourceIdsBefore);
        assert.deepEqual(await page.locator('[data-game] table:first-of-type').allTextContents(),predictionsBefore);
        assert.equal(await page.locator('#model-metrics').innerText(),metricsBefore);
        for(const change of ['pin','duplicate','conflict','cycle']){
          const broken=structuredClone(identityFixture.overlay);
          if(change==='pin')broken.baseline.sha256='0'.repeat(64);
          if(change==='duplicate')broken.links.push({...broken.links[0]});
          if(change==='conflict')broken.links.push({...broken.links[0],canonical_event_id:'another-source'});
          if(change==='cycle')broken.links.push({...broken.links[0],source_event_id:'source-invented',canonical_event_id:'official-invented'});
          await page.locator('#identity-overlay-file').setInputFiles({name:'invented-invalid-'+change+'.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(broken))});
          await page.waitForFunction(()=>document.getElementById('identity-overlay-status').classList.contains('error'));
          assert.match(await page.locator('#identity-overlay-status').innerText(),/Existing report and prior valid overlay remain unchanged/);
          assert.equal(await page.locator('[data-identity-link]').count(),1);
          assert.deepEqual(await page.locator('[data-game] table:first-of-type').allTextContents(),predictionsBefore);
        }
        await page.getByRole('button',{name:'Inspect source-invented',exact:true}).click();
        assert.equal(await page.locator('[data-game]').count(),1);
        assert.match(await page.locator('#results').innerText(),/Linked official source: official-invented/);
        await page.locator('#clear-identity-overlay').click();
        assert.equal(await page.locator('[data-identity-link]').count(),0);
        assert.match(await page.locator('#identity-overlay-count').innerText(),/No identity links loaded/);
        assert.doesNotMatch(await page.locator('#results').innerText(),/Linked official source/);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'identity overlay fits mobile');
        await page.locator('#clear').click();
        counts.identityOverlayViews=(counts.identityOverlayViews||0)+8;
      }
      {
        // This schedule export contains only invented native source records.
        const schedule=scheduleFixture();
        schedule.value.records[0].home_team='<img src=x onerror="window.scheduleLeak=true">';
        const scheduleBytes=Buffer.from(JSON.stringify(schedule.value));
        const schedulePin=createHash('sha256').update(scheduleBytes).digest('hex');
        assert.equal(await page.locator('#report').isHidden(),true,'schedule works without a baseline');
        await page.locator('#schedule-file').setInputFiles({name:'invented-schedule.json',mimeType:'application/json',buffer:scheduleBytes});
        await page.waitForFunction(()=>document.getElementById('schedule-load-status').textContent.startsWith('Loaded 27 of 27 declared'));
        assert.equal(await page.locator('[data-schedule-record]').count(),25);
        assert.match(await page.locator('#schedule-summary').innerText(),/All 27 records.*does not certify a complete physical season/);
        assert.match(await page.locator('#schedule-provider-counts').innerText(),/ESPN.*Men/s);
        assert.match(await page.locator('#schedule-source-proof').innerText(),new RegExp(schedulePin));
        assert.equal(await page.locator('#schedule-records img').count(),0);
        assert.equal(await page.evaluate(()=>window.scheduleLeak),undefined);
        await page.locator('#schedule-next').click();
        assert.equal(await page.locator('[data-schedule-record]').count(),2);
        assert.match(await page.locator('#schedule-count').innerText(),/26–27 of 27 filtered.*27 loaded.*0 hidden/);
        await page.selectOption('#schedule-provider','espn');
        assert.equal(await page.locator('[data-schedule-record]').count(),14);
        await page.selectOption('#schedule-league','ncaaw');
        assert.equal(await page.locator('[data-schedule-record]').count(),7);
        await page.selectOption('#schedule-date','missing');
        assert.equal(await page.locator('[data-schedule-record]').count(),1);
        assert.match(await page.locator('#schedule-records').innerText(),/Exact tip time unavailable/);
        assert.match(await page.locator('#schedule-records').innerText(),/Winner: null · win probability: null/);
        assert.match(await page.locator('#schedule-records').innerText(),/NOT_JOINED_SCHEDULE_ONLY/);
        await page.locator('#reset-schedule-filters').click();
        await page.selectOption('#schedule-date','2027-02-01');
        assert.equal(await page.locator('[data-schedule-record]').count(),2);
        await page.locator('#reset-schedule-filters').click();
        await page.locator('#schedule-search').fill('SOURCE_IDENTITY_CHANGE_REQUIRES_REVIEW');
        assert.equal(await page.locator('[data-schedule-record]').count(),1);
        await page.locator('#reset-schedule-filters').click();
        assert.match(await page.locator('#schedule-count').innerText(),/27 loaded.*0 hidden/);
        const baseline=identityOverlayFixture();
        await page.locator('#report-file').setInputFiles({name:'invented-independent-baseline.json',mimeType:'application/json',buffer:baseline.body});
        await page.waitForFunction(()=>document.getElementById('load-status').textContent.startsWith('Loaded 3 source game records'));
        await page.locator('#show-games').click();
        await page.locator('#identity-overlay-file').setInputFiles({name:'invented-independent-overlay.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(baseline.overlay))});
        await page.waitForFunction(()=>document.getElementById('identity-overlay-status').textContent.startsWith('Verified baseline binding'));
        const baseForecasts=await page.locator('[data-game] table:first-of-type').allTextContents(),baseMetrics=await page.locator('#model-metrics').innerText(),baseOverlay=await page.locator('#identity-overlay-count').innerText();
        const invalid=structuredClone(schedule.value);invalid.records[0].win_probability=.9;
        await page.locator('#schedule-file').setInputFiles({name:'invented-forecast-not-schedule.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalid))});
        await page.waitForFunction(()=>document.getElementById('schedule-load-status').classList.contains('error'));
        assert.match(await page.locator('#schedule-load-status').innerText(),/Previous schedule, baseline and overlay remain unchanged/);
        assert.equal(await page.locator('[data-schedule-record]').count(),25);
        const references=scheduleReferenceFixture();
        await page.locator('#schedule-file').setInputFiles({name:'invented-reference-only-schedule.json',mimeType:'application/json',buffer:references.body});
        await page.waitForFunction(()=>document.getElementById('schedule-records').textContent.includes('This file contains references only'));
        assert.equal(await page.locator('[data-schedule-record]').count(),0);
        assert.match(await page.locator('#schedule-summary').innerText(),/27 provider-native IDs; zero rows/);
        assert.match(await page.locator('#schedule-records').innerText(),/not an empty season/);
        const sourceReferences=scheduleReferenceFixture('source');
        await page.locator('#schedule-file').setInputFiles({name:'invented-source-index-limit.json',mimeType:'application/json',buffer:sourceReferences.body});
        await page.waitForFunction(()=>document.getElementById('schedule-summary').textContent.includes('SOURCE_INDEX_BOUND_REACHED'));
        assert.equal(await page.locator('[data-schedule-record]').count(),0);
        assert.deepEqual(await page.locator('[data-game] table:first-of-type').allTextContents(),baseForecasts);
        assert.equal(await page.locator('#model-metrics').innerText(),baseMetrics);
        assert.equal(await page.locator('#identity-overlay-count').innerText(),baseOverlay);
        const compactSchedule=compactScheduleFixture();
        await page.locator('#schedule-file').setInputFiles({name:'invented-compact-schedule.json',mimeType:'application/json',buffer:compactSchedule.body});
        await page.waitForFunction(()=>document.getElementById('schedule-load-status').textContent.startsWith('Loaded 27 of 27 declared'));
        assert.equal(await page.locator('[data-schedule-record]').count(),25);
        assert.match(await page.locator('#schedule-source-proof').innerText(),new RegExp(compactSchedule.pin.sha256));
        assert.match(await page.locator('#schedule-source-proof').innerText(),/not a new owner execution/);
        assert.match(await page.locator('#schedule-source-proof').innerText(),/not reverified in this browser/);
        await page.locator('#schedule-next').click();
        assert.equal(await page.locator('[data-schedule-record]').count(),2);
        assert.deepEqual(await page.locator('[data-game] table:first-of-type').allTextContents(),baseForecasts);
        assert.equal(await page.locator('#model-metrics').innerText(),baseMetrics);
        assert.equal(await page.locator('#identity-overlay-count').innerText(),baseOverlay);
        await page.locator('#clear-schedule').click();
        assert.equal(await page.locator('#schedule-content').isHidden(),true);
        assert.deepEqual(await page.locator('[data-game] table:first-of-type').allTextContents(),baseForecasts);
        assert.equal(await page.locator('#identity-overlay-count').innerText(),baseOverlay);
        await page.locator('#schedule-file').setInputFiles({name:'invented-schedule-again.json',mimeType:'application/json',buffer:scheduleBytes});
        await page.waitForFunction(()=>document.getElementById('schedule-load-status').textContent.startsWith('Loaded 27 of 27 declared'));
        await page.locator('#clear').click();
        assert.equal(await page.locator('#report').isHidden(),true);
        assert.equal(await page.locator('[data-schedule-record]').count(),25,'clearing baseline leaves schedule independent');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'schedule panel fits mobile');
        await page.locator('#clear-schedule').click();
        counts.scheduleViews=(counts.scheduleViews||0)+21;
      }
      {
        // Every row here is invented; exact private owner data is never committed.
        const eligibility=eligibilityFixture();
        assert.match(await page.locator('#source-report-choice').innerText(),/B052_SOURCE_SNAPSHOT_DASHBOARD_DATA.json.*2,446 source game rows.*zero supplied model predictions.*58 missing event clocks/s);
        assert.equal(await page.locator('#report').isHidden(),true,'eligibility works without a baseline');
        await page.locator('#eligibility-file').setInputFiles({name:'invented-eligibility.json',mimeType:'application/json',buffer:eligibility.body});
        await page.waitForFunction(()=>document.getElementById('eligibility-load-status').textContent.startsWith('Loaded 29 exact'));
        assert.equal(await page.locator('[data-eligibility-record]').count(),25);
        assert.match(await page.locator('#eligibility-summary').innerText(),/29 source identities = 25 passed.*2 rejected.*2 without a feature row/);
        assert.match(await page.locator('#eligibility-source-proof').innerText(),/unrecognized owner provenance/);
        assert.match(await page.locator('#eligibility-source-proof').innerText(),new RegExp(eligibility.pin.sha256));
        await page.locator('#eligibility-next').click();
        assert.equal(await page.locator('[data-eligibility-record]').count(),4);
        assert.match(await page.locator('#eligibility-records').innerText(),/FEATURE_AVAILABILITY_KNOWN/);
        assert.match(await page.locator('#eligibility-records').innerText(),/FEATURE_STRICTLY_BEFORE_CUTOFF/);
        assert.match(await page.locator('#eligibility-records').innerText(),/Not supplied · null retained/);
        await page.selectOption('#eligibility-league','ncaaw');
        await page.selectOption('#eligibility-status','CURRENT_MODEL_GATE_REJECTED');
        assert.equal(await page.locator('[data-eligibility-record]').count(),1);
        assert.match(await page.locator('#eligibility-count').innerText(),/28 hidden by filters/);
        await page.locator('#reset-eligibility-filters').click();
        await page.selectOption('#eligibility-reason','NO_CURRENT_FEATURE_ROW');
        assert.equal(await page.locator('[data-eligibility-record]').count(),2);
        await page.locator('#reset-eligibility-filters').click();
        await page.locator('#eligibility-search').fill('outside_frozen_inclusion_cohort');
        assert.equal(await page.locator('[data-eligibility-record]').count(),2);
        const malformed=JSON.parse(JSON.stringify(eligibility.value));malformed.rows[0].win_probability=.8;
        await page.locator('#eligibility-file').setInputFiles({name:'rejected-eligibility.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(malformed))});
        await page.waitForFunction(()=>document.getElementById('eligibility-load-status').textContent.startsWith('Cannot open eligibility ledger:'));
        assert.equal(await page.locator('[data-eligibility-record]').count(),2,'invalid replacement preserves the previous ledger');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'eligibility panel fits mobile');
        await page.locator('#clear-eligibility').click();
        assert.equal(await page.locator('#eligibility-content').isHidden(),true);
        assert.equal(await page.locator('[data-eligibility-record]').count(),0);
        counts.eligibilityViews=(counts.eligibilityViews||0)+13;
      }
      {
        const v4=v4Fixture();
        await page.locator('#v4-summary-file').setInputFiles({name:'invented-v4.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(v4.value))});
        await page.waitForFunction(()=>document.getElementById('v4-status').textContent.startsWith('V4 review loaded.'));
        assert.equal(await page.locator('#v4-summary-cards .clock-card').count(),4);
        assert.equal(await page.locator('#v4-metric-rows tr').count(),1);
        assert.match(await page.locator('#v4-part-count').innerText(),/No evidence part loaded/);
        await page.selectOption('#v4-track','genuinely_future_issued_rolling');
        assert.equal(await page.locator('#v4-metric-rows tr').count(),0);
        assert.match(await page.locator('#v4-metric-count').innerText(),/No evaluated population/);
        await page.selectOption('#v4-track','all');
        await page.locator('#v4-part-file').setInputFiles({name:'invented-part.jsonl.gz',mimeType:'application/gzip',buffer:v4.body});
        await page.waitForFunction(()=>document.getElementById('v4-part-status').textContent.startsWith('Verified compressed'));
        assert.equal(await page.locator('[data-v4-record]').count(),25);
        await page.locator('[data-v4-record] details').first().locator('summary').click();
        await page.locator('[data-v4-record] details pre').first().waitFor({state:'visible'});
        assert.match(await page.locator('[data-v4-record]').first().innerText(),/<img src=x/);
        assert.equal(await page.locator('#v4-part-rows img').count(),0);
        await page.locator('#v4-part-next').click();
        assert.equal(await page.locator('[data-v4-record]').count(),2);
        assert.match(await page.locator('#v4-part-rows').innerText(),/Prediction: Unavailable/);
        const bad=JSON.parse(JSON.stringify(v4.value));bad.automatic_promotion=true;
        await page.locator('#v4-summary-file').setInputFiles({name:'rejected-v4.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
        await page.waitForFunction(()=>document.getElementById('v4-status').textContent.startsWith('Cannot open V4 review:'));
        assert.equal(await page.locator('[data-v4-record]').count(),2);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'V4 controls fit viewport');
        await page.locator('#clear-v4').click();
        assert.equal(await page.locator('#v4-content').isHidden(),true);
        counts.v4ReviewViews=(counts.v4ReviewViews||0)+12;
      }
      counts.viewports++;
    }
    assert.deepEqual(failures, []);
    assert.deepEqual(externalRequests, []);
    console.log(JSON.stringify({ status: 'PASS', ...counts, widths: [1440, 390], scriptErrors: 0, externalRequests: 0, realChromium: true }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

