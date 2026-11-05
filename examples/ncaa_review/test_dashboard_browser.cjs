// Real Chromium contract: all evidence selectors, clock scenarios and mobile layout.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { createHash } = require('node:crypto');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}),
  });
  const failures = [], externalRequests = [];
  const page = await browser.newPage();
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => {
    if (!/^(file|data):/.test(request.url())) externalRequests.push(request.url());
  });
  const root = path.resolve(__dirname, '../..');
  const objectiveMap = {
    probability: ['win', 'LogLoss'], accuracy: ['win', 'Accuracy'],
    margin: ['margin', 'MAE'], total: ['total', 'MAE'],
  };
  const counts = { viewports: 0, selectorStates: 0, scenarios: 0, progressScenarios: 0, preflightScenarios: 0, executionViews: 0, keyboardEvents: 0, privateViewerStates: 0, captureClockViews: 0, horizonMetricViews: 0, unclassifiedSourceViews: 0, providerComparisonViews: 0, boundedInventoryViews: 0, freshnessViews: 0 };
  try {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const league of ['ncaam', 'ncaaw']) {
        await page.goto(pathToFileURL(path.join(root, 'tracks', league, 'index.html')).href);
        await page.locator('#model-table tbody tr').first().waitFor();
        const evidence = JSON.parse(await page.locator('#evidence').textContent());
        assert.equal(evidence.league, league);
        assert.equal(await page.locator('#provider-table tr').count(), 3);
        assert.deepEqual(await page.locator('#provider-table tr td:first-child strong').allTextContents(), ['Kalshi', 'Polymarket', 'DraftKings']);
        assert.match(await page.locator('#current').innerText(), /Current metrics: unavailable/);
        assert.match(await page.locator('#provider-table').innerText(), /International: unverified/);
        assert.match(await page.locator('#provider-table').innerText(), /US: unacquired/);
        assert.match(await page.locator('#attempt-summary').innerText(), /536 passed.*0 errors.*1 skipped/);
        assert.match(await page.locator('#attempt-summary').innerText(), /12 of 12 workflow stages completed/);
        assert.match(await page.locator('#preserved-study-copy').innerText(), /108 committed target fits across both leagues; 54 in this track/);
        assert.equal(await page.locator('#phase-table tr').count(), 12);
        assert.equal(await page.locator('#phase-table .done').count(), 12);
        assert.equal(await page.locator('#phase-table .failed').count(), 0);
        assert.equal(await page.locator('#history-phase-table .done').count(), 3);
        assert.equal(await page.locator('#history-phase-table .failed').count(), 1);
        assert.match(await page.locator('#inventory-age').innerText(), /Nov 4, 2026/);
        assert.match(await page.locator('#coverage-counts').innerText(), /Unverified/);
        assert.match(await page.locator('#resource-note').innerText(), /simultaneous process-tree peak was not measured/);
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
      const secondStream={...rows[0],track:'original_frozen',durable_issued_before_cutoff:true,
        forecast_status:'INVENTED_ORIGINAL_ISSUE',prediction_win:.4567,kalshi_win_prediction:.2345,
        kalshi_win_status:'INVENTED_OTHER_STREAM_PAIR'};
      const invented = { schema: 'sports-edge-lab.private.game-report.v1', evidence_release: 'INVENTED', asof_utc: '2026-11-04T20:00:00Z',
        records: [...rows,secondStream], market_observations: [{ provider: 'Kalshi', canonical_identity_verified: false, native_event_id: 'unresolved-fixture', binding_status: 'unknown_identity', quote_time: null, native_yes_probability: .37, value_kind: 'Native Yes probability' },
          { provider: 'DraftKings', league: 'ncaam', canonical_identity_verified: true, event_id: 'invented-0', target: 'win', prediction: .55 }],
        window_event_keys: { this_week: rows.slice(0, 5).map(r => [r.league, r.event_id]), season_to_date: rows.slice(0, 1).map(r => [r.league, r.event_id]), last_week: [] },
        audit_annotations: { 'invented-0': ['Exact time disputed; no replacement inferred.'] }, metrics: [], weekly_metrics: [] };
      await page.locator('#report-file').setInputFiles({ name: 'invented-report.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(invented)) });
      await page.locator('#report:not([hidden])').waitFor();
      assert.match(await page.locator('#load-status').innerText(), /Loaded 27 source game records/);
      assert.equal(await page.locator('[data-game]').count(), 25);
      assert.match(await page.locator('#results').innerText(), /Original frozen as issued/);
      assert.match(await page.locator('#results').innerText(), /Wrong/);
      assert.match(await page.locator('#results').innerText(), /precision: unknown/);
      assert.match(await page.locator('#results').innerText(), /Exact time disputed/);
      assert.equal(await page.locator('#results img').count(), 0);
      assert.equal(await page.evaluate(() => window.privateLeak), undefined);
      counts.privateViewerStates++;
      assert.equal(await page.locator('#market-clock').inputValue(),'latest_pretip');
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
        assert.match(await firstGame.innerText(),/NO BET.*Execution and fees unverified/);
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
      assert.match(await page.locator('#provider-cards').innerText(),/ROI \/ hypothetical profit: not inferred/);
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
      commonVerified.provider_comparisons.tables.season_common.common_provider_set_verified=true;
      commonVerified.provider_comparisons.tables.week_common=tableSource('week-common',[],'all_requested_providers_common');
      commonVerified.provider_comparisons.tables.disagreements=tableSource('disagreements',[]);
      await page.locator('#report-file').setInputFiles({name:'invented-common-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(commonVerified))});
      await page.waitForFunction(()=>document.getElementById('provider-disagreement-count').textContent.startsWith('0 of 0'));
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
      counts.viewports++;
    }
    assert.deepEqual(failures, []);
    assert.deepEqual(externalRequests, []);
    console.log(JSON.stringify({ status: 'PASS', ...counts, widths: [1440, 390], scriptErrors: 0, externalRequests: 0, realChromium: true }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

