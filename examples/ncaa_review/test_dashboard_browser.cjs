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
  const counts = { viewports: 0, selectorStates: 0, scenarios: 0, progressScenarios: 0, preflightScenarios: 0, executionViews: 0, keyboardEvents: 0 };
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
        assert.match(await page.locator('#attempt-summary').innerText(), /510 passed.*3 errors.*1 skipped/);
        assert.match(await page.locator('#attempt-summary').innerText(), /0 of 12 scientific stages started/);
        assert.match(await page.locator('#preserved-study-copy').innerText(), /108 committed target fits across both leagues; 54 in this track/);
        assert.equal(await page.locator('#phase-table tr').count(), 3);
        assert.equal(await page.locator('#phase-table .done').count(), 0);
        assert.equal(await page.locator('#phase-table .failed').count(), 1);
        assert.equal(await page.locator('#history-phase-table .done').count(), 3);
        assert.equal(await page.locator('#history-phase-table .failed').count(), 1);
        assert.match(await page.locator('#inventory-age').innerText(), /Nov 2, 2026/);
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
    }
    assert.deepEqual(failures, []);
    assert.deepEqual(externalRequests, []);
    console.log(JSON.stringify({ status: 'PASS', ...counts, widths: [1440, 390], scriptErrors: 0, externalRequests: 0, realChromium: true }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
