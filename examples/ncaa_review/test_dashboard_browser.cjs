// Real Chromium contract: all evidence selectors, clock scenarios and mobile layout.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
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
  const counts = { viewports: 0, selectorStates: 0, scenarios: 0, progressScenarios: 0, preflightScenarios: 0, executionViews: 0, keyboardEvents: 0, privateViewerStates: 0, captureClockViews: 0, horizonMetricViews: 0, unclassifiedSourceViews: 0 };
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
      await page.locator('#clear').click();
      assert.equal(await page.locator('#report').isHidden(), true);
      assert.equal(await page.locator('#results').textContent(), '');
      assert.equal(await page.locator('#asof').textContent(), '');
      assert.equal(await page.locator('#metadata').textContent(), '');
      assert.equal(await page.locator('#horizon-details').textContent(),'Paired metrics by market reference horizon');
      assert.equal(await page.locator('#unclassified-details').textContent(),'Unclassified source observations');
      assert.equal(await page.locator('#market-clock-note').textContent(),'');
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

