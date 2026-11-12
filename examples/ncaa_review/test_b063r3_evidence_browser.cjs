// Real Chromium checks for the preserved science and latest actual R2 status.
// Called by the established NCAA browser job; no workflow or source acquisition.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function verifyR3(browser, filename) {
  const page = await browser.newPage();
  const failures = [], external = [], viewports = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => {
    if (!/^(file|data|blob):/.test(request.url())) external.push(request.url());
  });
  try {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(pathToFileURL(filename).href);
      await page.locator('#season-leaders tbody tr').first().waitFor();
      const data = JSON.parse(await page.locator('#b063r2-data').textContent());
      assert.equal(data.execution.latest_actual_owner.release, 'B063R2');
      assert.equal(data.execution.continuation.release, 'B063R3');
      assert.equal(data.execution.latest_actual_owner.peak_scientific_workers, 0);
      assert.equal(data.execution.latest_actual_owner.probe_utilization_is_not_scientific_parallelism, true);
      assert.equal(await page.evaluate(() => window.__ncaaB063R2.ownerR2Executed), true);
      assert.match(await page.locator('#execution-actual').innerText(), /3,766 startup tests passed; 0 errored; 11 skipped/);
      for (const [selector, count] of [['#season-leaders',28],['#pooled-leaders',14],['#current-leaders',14],['#early-groups',6],['#late-groups',11],['#late-rows',46],['#outcome-sources',38]]) {
        assert.equal(await page.locator(selector+' tbody tr').count(), count, selector);
      }
      assert.match(await page.locator('#candidate-count').innerText(), /1–25 of 164/);
      await page.locator('#candidate-next').click();
      assert.match(await page.locator('#candidate-count').innerText(), /26–50 of 164/);
      await page.selectOption('#league', 'ncaaw');
      await page.selectOption('#season', '2026');
      await page.selectOption('#objective', 'win:log_loss');
      assert.equal(await page.locator('#season-leaders tbody tr').count(), 1);
      assert.equal(await page.locator('#current-leaders tbody tr').count(), 1);
      assert.equal(await page.locator('#candidate-table tbody tr').count(), 14);
      const downloadPromise = page.waitForEvent('download');
      await page.locator('#download-candidates').click();
      const download = await downloadPromise;
      const rows = fs.readFileSync(await download.path(),'utf8').trim().split(/\r?\n/);
      assert.equal(rows.length, 15);
      assert.ok(rows.slice(1).every(row => row.startsWith('ncaaw,2025–26,win,')));
      await page.locator('#query').fill('NO_MATCH_IN_SAVED_EVIDENCE');
      assert.match(await page.locator('#candidate-table').innerText(), /No rows match/);
      assert.equal(await page.locator('#candidate-next').isDisabled(), true);
      await page.locator('#reset').click();
      assert.equal(await page.locator('#season-leaders tbody tr').count(), 28);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      for (const href of await page.locator('a[download]').evaluateAll(nodes => nodes.map(n => n.getAttribute('href')))) {
        assert.ok(fs.existsSync(path.resolve(path.dirname(filename),href)), href);
      }
      viewports.push({ width, filterExportAndOverflowChecks: 'PASS' });
    }
    assert.deepEqual(failures, []);
    assert.deepEqual(external, []);
    return { viewports, originalRows:136, candidateSeasonRows:164, actualR2Fits:0, preparedContinuation:'B063R3', realChromium:true };
  } finally {
    await page.close();
  }
}
module.exports = { verifyR3 };
