/* Render the committed public page and exercise its filters; no remote access. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');

(async () => {
  const launch = {headless: true, args: ['--no-sandbox']};
  if (process.env.CHROMIUM_PATH) launch.executablePath = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch(launch);
  const out = process.env.NFL_SCREENSHOTS;
  if (out) fs.mkdirSync(out, {recursive: true});
  const report = [];
  try {
    for (const [name, viewport] of [['desktop', {width: 1440, height: 1000}], ['mobile', {width: 390, height: 844}]]) {
      const page = await browser.newPage({viewport});
      const errors = [];
      const remoteRequests = [];
      page.on('pageerror', error => errors.push(String(error)));
      page.on('request', req => { if (/^https?:/.test(req.url())) remoteRequests.push(req.url()); });
      await page.goto(pathToFileURL(path.join(__dirname, 'index.html')).href, {waitUntil: 'load'});
      assert.match(await page.title(), /NFL N127R18/);
      assert.equal(await page.locator('h1').count(), 1);
      assert.match(await page.locator('h1').innerText(), /Research remains partial/);
      assert.equal(await page.locator('#weight-filter').inputValue(), '50/50');
      assert.equal(await page.locator('#clock-filter').inputValue(), 'All models available one hour before kickoff');
      const allRows = await page.locator('#metrics-body tr').count();
      assert.ok(allRows > 0, 'Saved nomination rows must exist');
      const initial = await page.locator('#metrics-body tr:not([hidden])').count();
      assert.ok(initial > 0, 'Primary default filter must show saved rows');
      const overflows = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
      assert.equal(overflows, false, 'The whole page must not overflow horizontally');
      if (out) await page.screenshot({path: path.join(out, `nfl-r18-${name}.png`)});
      if (out) {
        await page.locator('#metric-search').scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(out, `nfl-r18-${name}-metrics.png`)});
      }
      await page.locator('#metric-search').fill('__no_saved_nomination_matches_this__');
      assert.equal(await page.locator('#metrics-body tr:not([hidden])').count(), 0);
      assert.equal(await page.locator('#no-results').isVisible(), true);
      await page.locator('#metric-search').fill('');
      for (const id of ['weight-filter', 'clock-filter', 'objective-filter']) await page.locator('#' + id).selectOption('');
      assert.equal(await page.locator('#metrics-body tr:not([hidden])').count(), allRows);
      assert.equal(await page.locator('#no-results').isVisible(), false);
      const firstObjective = await page.locator('#metrics-body tr').first().getAttribute('data-objective');
      await page.locator('#objective-filter').selectOption(firstObjective);
      const objectives = await page.locator('#metrics-body tr:not([hidden])').evaluateAll(rs => rs.map(r => r.dataset.objective));
      assert.ok(objectives.length > 0 && objectives.every(v => v === firstObjective));
      await page.locator('#metric-search').focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.id), 'weight-filter');
      await page.locator('#sources details').first().locator('summary').click();
      assert.equal(await page.locator('#sources details').first().getAttribute('open'), '');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1), false);
      assert.equal(errors.length, 0, errors.join('\n'));
      assert.equal(remoteRequests.length, 0, 'The review must render without a network dependency');
      report.push({viewport: name, total_rows: allRows, initial_primary_rows: initial, script_errors: 0, external_requests: 0, horizontal_page_overflow: false, filters: 'PASS', keyboard: 'PASS'});
      await page.close();
    }
  } finally { await browser.close(); }
  console.log(JSON.stringify({status: 'PASS', local_render_only: true, hosted_deployment_verified: false, viewports: report}, null, 2));
})().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
