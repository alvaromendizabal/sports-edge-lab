// Exercise the actual offline DOM in Chromium. No external sports/data requests.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const root = path.resolve(__dirname, '../../..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'docs/fbs/V024_AGGREGATE_2026-11-03.json'), 'utf8'));
const url = 'file://' + path.join(root, 'docs/fbs/index.html');
let browser;

(async () => {
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({acceptDownloads: true});
  const page = await context.newPage();
  const errors = [], requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (!/^(file|data|blob):/.test(request.url())) requests.push(request.url());
  });
  let states = 0;
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 1000});
    await page.goto(url);
    await page.locator('#comparison-table tbody tr').first().waitFor();
    assert.equal(await page.locator('#comparison-table tbody tr').count(), 7);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `horizontal page overflow at ${width}`);
    assert.match(await page.locator('#selection-status').innerText(), /934 paired games/);
    assert.match(await page.locator('.verdict').innerText(), /increased in both seasons/);
    assert.equal(await page.locator('h1').count(), 1);
    for (const select of ['study-season', 'target', 'metric', 'reference']) {
      assert.equal(await page.locator(`label[for="${select}"]`).count(), 1);
    }
    await page.getByRole('button', {name: 'Same count, other game', exact: true}).click();
    assert.equal(await page.locator('#demo-state').innerText(), 'BLOCKED');
    assert.match(await page.locator('#demo-reason').innerText(), /exact event identities/);
    assert.equal(await page.locator('#demo-table').isVisible(), false);
    await page.getByRole('button', {name: 'Label changed', exact: true}).click();
    assert.match(await page.locator('#demo-reason').innerText(), /paired labels/);
    await page.getByRole('button', {name: 'Late issue', exact: true}).click();
    assert.match(await page.locator('#demo-reason').innerText(), /before kickoff/);
    await page.getByRole('button', {name: 'Paired', exact: true}).click();
    assert.equal(await page.locator('#demo-table').isVisible(), true);
    assert.equal(await page.locator('[data-demo][aria-pressed="true"]').count(), 1);
    // A keyboard event must alter the same controls used by a mouse.
    await page.locator('#study-season').focus();
    await page.keyboard.press('ArrowUp');
    assert.equal(await page.locator('#study-season').inputValue(), '2024');
    assert.match(await page.locator('#selection-status').innerText(), /918 paired games/);
    await page.getByRole('button', {name: 'Reset view', exact: true}).click();
    const output = process.env.FBS_SCREENSHOTS;
    if (output) {
      fs.mkdirSync(output, {recursive: true});
      await page.screenshot({path: path.join(output, `fbs-${width}.png`), fullPage: true});
    }
  }
  // Every selectable state must preserve the exact registered cohort and numbers.
  for (const year of [2024, 2025]) {
    await page.selectOption('#study-season', String(year));
    for (const target of ['winner', 'margin', 'total']) {
      await page.selectOption('#target', target);
      const keys = await page.locator('#metric option').evaluateAll(options => options.map(o => o.value));
      for (const key of keys) {
        await page.selectOption('#metric', key);
        for (const model of data.models) {
          await page.selectOption('#reference', model.id);
          const actual = await page.locator('#comparison-table tbody tr').evaluateAll(rows => rows.map(r => ({
            model: r.dataset.model, cells: [...r.querySelectorAll('td')].map(c => c.textContent),
          })));
          const expected = data.panels.filter(r => r.season === year);
          const base = expected.find(r => r.model === model.id).metrics[key];
          assert.deepEqual(actual.map(r => r.model), data.models.map(m => m.id));
          for (const row of actual) {
            const e = expected.find(r => r.model === row.model);
            assert.equal(Number(row.cells[0]), e.games);
            assert.ok(Math.abs(Number(row.cells[1]) - e.metrics[key]) <= .00000051);
            if (row.model !== model.id) assert.ok(Math.abs(Number(row.cells[2]) - (e.metrics[key] - base)) <= .00000051);
          }
          assert.equal(await page.locator('#delta-chart .delta-row').count(), 7);
          states++;
        }
      }
    }
  }
  await page.getByRole('button', {name: 'Reset view', exact: true}).click();
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', {name: 'Download view · CSV', exact: true}).click(),
  ]);
  const csv = fs.readFileSync(await download.path(), 'utf8');
  assert.equal(csv.trim().split('\n').length, 8);
  assert.match(csv, /exposed historical aggregate/);
  assert.doesNotMatch(csv, /s3:\/\/|account_id|game_id|v024_full_|v024_combined_/);
  assert.equal(download.suggestedFilename(), 'fbs-v024-2025-winner_logloss.csv');
  // An initial seven-row comparison must remain meaningful without JavaScript.
  const noScript = await browser.newContext({javaScriptEnabled: false});
  const fallback = await noScript.newPage();
  await fallback.goto(url);
  assert.equal(await fallback.locator('#comparison-table tbody tr').count(), 7);
  assert.match(await fallback.locator('noscript').innerText(), /JavaScript is off/);
  assert.match(await fallback.locator('#comparison-table').innerText(), /0.488797/);
  assert.deepEqual(errors, []);
  assert.deepEqual(requests, []);
  console.log(JSON.stringify({status: 'PASS',viewports: [1440,390],comparison_states: states,
    real_keyboard_events: true,paired_failure_scenarios: 3,csv_rows: 7,no_script_rows: 7,
    script_errors: 0,external_requests: 0}));
  await browser.close();
})().catch(async error => {console.error(error);if (browser) await browser.close();process.exitCode = 1;});
