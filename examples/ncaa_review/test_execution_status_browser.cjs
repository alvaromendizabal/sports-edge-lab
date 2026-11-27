'use strict';
const { mutations } = require('./execution_status_invalid_fixtures.cjs');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function verifyExecutionStatus(browser, file) {
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const errors = [], external = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (!/^(file|data|blob):/.test(request.url())) external.push(request.url());
  });
  const expected = JSON.parse(fs.readFileSync(path.join(path.dirname(file), 'execution_status.json')));
  const latest = JSON.parse(fs.readFileSync(path.join(path.dirname(file), 'execution_latest.json')));
  let views = 0, cells = 0, downloads = 0, latestDownloads = 0, latestCells = 0;
  try {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(pathToFileURL(file).href);
      await page.locator('#attempt-rows tr').first().waitFor();
      assert.equal(await page.locator('#latest-execution-tally').innerText(), '0 / 1');
      assert.equal(await page.locator('#latest-new-work').innerText(), '0 / 1');
      assert.equal(await page.locator('#latest-preserved-models').innerText(), '108');
      assert.match(await page.locator('#latest-execution-title').innerText(), /R33 stopped automatically before fitting/);
      assert.match(await page.locator('#latest-evidence-scope').innerText(), /internal execution defect, not a requested user stop/);
      assert.match(await page.locator('#latest-cpu-limit').innerText(), /do not establish 12–36-core fitting/);
      assert.match(await page.locator('#latest-cpu-limit').innerText(), /conditional 180-second, 75% scientific utilization gate/);
      assert.match(await page.locator('#latest-reuse-state').innerText(), /153 completed and nine reused/);
      assert.equal(await page.locator('#latest-preparation-state').innerText(), `R34 · ${latest.next_preparation.status} · 0 owner executions`);
      if (latest.next_preparation.status === 'PREPARED_VERIFIED') {
        const latestPanel = await page.locator('#latest-execution-panel').innerText();
        assert.ok(latestPanel.includes(latest.next_preparation.canonical_source.sha256));
        assert.ok(latestPanel.includes(latest.next_preparation.native_acceptance.report_sha256));
        assert.ok(latestPanel.includes(latest.next_preparation.installation_receipt_sha256));
        assert.match(latestPanel, /Owner execution remains pending/);
      }
      assert.match(await page.locator('#r34-native-engineering').innerText(), /1,572 native engineering tests/);
      assert.equal(await page.locator('#r34-bounded-new-fits').innerText(), '48 / 48');
      assert.equal(await page.locator('#r34-bounded-worker-overlap').innerText(), '28');
      assert.equal(await page.locator('#r34-bounded-capacity-limit').innerText(), 'The sustained 180-second capacity gate is not certified.');
      const expectedSourceRows = [
        ['Scoreboard requests','23','9','32 / 32','Source outputs; not fits'],
        ['Box requests','130','0','130 / 130','Source outputs; not fits'],
        ['Market snapshots','209','Separately tracked','1 additional partial','Full population incomplete']
      ];
      assert.equal(await page.locator('#latest-source-rows tr').count(), 3);
      for (let i = 0; i < expectedSourceRows.length; i++) {
        const values = await page.locator('#latest-source-rows tr').nth(i).locator('td').allTextContents();
        assert.deepEqual(values, expectedSourceRows[i]);
        latestCells += values.length;
      }
      const latestDownloadPromise = page.waitForEvent('download');
      await page.locator('#download-latest-execution').focus();
      await page.keyboard.press('Enter');
      const latestDownload = await latestDownloadPromise;
      assert.equal(latestDownload.suggestedFilename(), 'ncaa-latest-execution.json');
      const latestStream = await latestDownload.createReadStream(), latestChunks = [];
      for await (const chunk of latestStream) latestChunks.push(chunk);
      assert.deepEqual(JSON.parse(Buffer.concat(latestChunks).toString('utf8')), latest);
      latestDownloads++;
      assert.match(await page.locator('#earlier-evidence-title').innerText(), /Preserved earlier audit/);
      assert.equal(await page.locator('#observed-release').innerText(), 'R31');
      assert.equal(await page.locator('#verified-release').innerText(), 'R31');
      assert.match(await page.locator('#observed-status').innerText(), /failed resumable/i);
      assert.equal(await page.locator('#current-execution-panel').isVisible(), true);
      assert.match(await page.locator('#current-work-facts').innerText(), /1,284 reused · 0 fresh/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Requested workers \/ scientific peak\s+24 \/ 0/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Not run · source stage blocked dispatch/);
      assert.match(await page.locator('#current-cost-facts').innerText(), /Succeeded · integrity verified/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Historical target checkpoint reuses\s+108/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Current-consumer target reuses\s+0/);
      const costFacts = await page.locator('#current-cost-facts').innerText();
      assert.match(costFacts, /\$0\.42/);
      assert.doesNotMatch(costFacts, /\$0\.00/);
      assert.match(costFacts, /Budget exhaustion established\s+No · verified estimate below guard/);
      assert.match(await page.locator('#current-work-facts').innerText(), /822 \/ 36/);
      assert.match(await page.locator('#attempt-scope').innerText(), /12 audited attempts · 10 distinct run identities/);
      assert.match(await page.locator('#snapshot-time').innerText(), /Pacific.*not a live status feed/);
      assert.equal(await page.locator('#preserved-fits').innerText(), '11');
      assert.equal(await page.locator('#bounded-acceptance-panel').isVisible(), true);
      assert.equal(await page.locator('#bounded-fit-count').innerText(), '36');
      assert.equal(await page.locator('#bounded-overlap').innerText(), '21');
      assert.match(await page.locator('#bounded-cpu-facts').innerText(), /180-second \/ 75% gate certified\s+No/);
      assert.match(await page.locator('#bounded-cpu-facts').innerText(), /24 or 36 fitting kernels observed\s+No/);
      assert.match(await page.locator('#bounded-note').innerText(), /21-kernel overlap.*does not establish 24 or 36/);
      assert.equal(await page.locator('#stage-resumption-panel').isVisible(), true);
      assert.match(await page.locator('#stage-restart-facts').innerText(), /prior stages skipped\s+10/);
      assert.match(await page.locator('#source-replay-facts').innerText(), /Warm tasks reused \/ normalizer calls\s+6 \/ 0/);
      assert.match(await page.locator('#throughput-facts').innerText(), /Historical R22 sustained gate passed\s+No/);
      assert.equal(await page.locator('#recovery-evidence-panel').isVisible(), true);
      assert.match(await page.locator('#recovery-archive-facts').innerText(), /Historical target checkpoints authenticated\s+108/);
      assert.match(await page.locator('#recovery-archive-facts').innerText(), /Displayed scoreboard completion\s+4 \/ 32/);
      assert.match(await page.locator('#recovery-archive-facts').innerText(), /Authenticated committed responses\s+6/);
      assert.match(await page.locator('#recovery-archive-facts').innerText(), /Additional authenticated pending capture\s+1/);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /Scientific occupancy gate executed\s+No/);
      assert.equal(await page.locator('#next-preparation-state').innerText(),
        `R32 · ${expected.next_preparation.status} · 0 owner executions`);
      assert.equal(await page.locator('#preparation-stages li').count(), 4);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /1\.26 cores/);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /1\.41 cores/);
      if (expected.next_preparation.status === 'PREPARED_VERIFIED') {
        const note = await page.locator('#preparation-note').innerText();
        assert.ok(note.includes(`${expected.next_preparation.engineering_tests.toLocaleString('en-US')} engineering checks passed`));
        assert.match(note, /not owner fits or a scientific occupancy pass/);
      }
      for (const filter of ['all', 'RESEARCH', 'BEFORE_FIT', 'unpublished', 'published']) {
        await page.locator('#attempt-filter').selectOption(filter);
        const rows = expected.attempts.filter(r => filter === 'all' || (filter === 'unpublished' ? !r.return_published : filter === 'published' ? r.return_published : r.phase === filter));
        const actual = page.locator('#attempt-rows tr');
        assert.equal(await actual.count(), rows.length);
        for (let i = 0; i < rows.length; i++) {
          const row = rows[i], text = await actual.nth(i).locator('td').allTextContents();
          assert.equal(text[0], row.label);
          assert.equal(text[1], row.failure_label);
          assert.equal(text[2], row.new_target_fits === null ? 'Unobserved' : row.new_target_fits.toLocaleString('en-US'));
          assert.equal(text[3], row.historical_checkpoint_reuses === null ? 'Unobserved' : row.historical_checkpoint_reuses.toLocaleString('en-US'));
          assert.equal(text[6], row.note);
          cells += 5;
        }
        assert.equal(await page.locator('#attempt-count').innerText(), `${rows.length} of ${expected.attempts.length} audited attempts shown.`);
        views++;
      }
      await page.locator('#attempt-filter').selectOption('all');
      const downloadPromise = page.waitForEvent('download');
      await page.locator('#download-report').click();
      const download = await downloadPromise;
      assert.equal(download.suggestedFilename(), 'ncaa-execution-status.json');
      const stream = await download.createReadStream(), chunks = [];
      for await (const chunk of stream) chunks.push(chunk);
      assert.deepEqual(JSON.parse(Buffer.concat(chunks).toString('utf8')), expected);
      downloads++;
      await page.locator('#attempt-filter').focus();
      assert.equal(await page.locator('#attempt-filter').evaluate(node => node === document.activeElement), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, 'Unexpected page-level horizontal overflow');
      if (process.env.DASHBOARD_SCREENSHOTS) {
        fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS, { recursive: true });
        await page.screenshot({ path: path.join(process.env.DASHBOARD_SCREENSHOTS, `ncaa-execution-${width}.png`), fullPage: true });
      }
      await page.reload();
      assert.equal(await page.locator('#attempt-filter').inputValue(), 'all');
      assert.equal(await page.locator('#attempt-rows tr').count(), expected.attempts.length);
    }
    await page.goto(pathToFileURL(path.join(path.dirname(file), 'index.html')).href);
    assert.match(await page.locator('#v12-current-evidence').innerText(), /R33.*latest verified partial return contains 553 payloads/is);
    assert.equal(await page.locator('#v12-current-evidence a[href="execution.html"]').count(), 1);
    await page.locator('#v12-current-evidence a[href="execution.html"]').click();
    assert.equal(await page.locator('#latest-execution-tally').innerText(), '0 / 1');
    assert.equal(await page.locator('#observed-release').innerText(), 'R31');
    const raw = fs.readFileSync(file, 'utf8');
    for (const mutate of mutations) {
      const bad = JSON.parse(JSON.stringify(expected)); mutate(bad);
      const html = raw.replace(/(<script id="execution-data" type="application\/json">)[\s\S]*?(<\/script>)/, '$1' + JSON.stringify(bad).replace(/</g, '\\u003c') + '$2');
      await page.setContent(html);
      assert.equal(await page.locator('#data-error').isVisible(), true);
      assert.equal(await page.locator('#report').isVisible(), false);
    }
    const sourceData = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R29_20261118.json')));
    await page.setContent(raw.replace(/(<script id="execution-data" type="application\/json">)[\s\S]*?(<\/script>)/, '$1' + JSON.stringify(sourceData).replace(/</g, '\\u003c') + '$2'));
    assert.equal(await page.locator('#data-error').isVisible(), false);
    assert.equal(await page.locator('#observed-release').innerText(), 'R29');
    assert.match(await page.locator('#recovery-archive-facts').innerText(), /Source chunks recorded\s+294/);
    const older = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_20261118.json')));
    const legacy = raw.replace(/(<script id="execution-data" type="application\/json">)[\s\S]*?(<\/script>)/, '$1' + JSON.stringify(older).replace(/</g, '\\u003c') + '$2');
    await page.setContent(legacy);
    assert.equal(await page.locator('#data-error').isVisible(), false);
    assert.equal(await page.locator('#observed-release').innerText(), 'R26');
    assert.match(await page.locator('#current-cost-facts').innerText(), /\$0\.32/);
    const recoveryData = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R28_20261118.json')));
    await page.setContent(raw.replace(/(<script id="execution-data" type="application\/json">)[\s\S]*?(<\/script>)/, '$1' + JSON.stringify(recoveryData).replace(/</g, '\\u003c') + '$2'));
    assert.equal(await page.locator('#data-error').isVisible(), false);
    assert.equal(await page.locator('#observed-release').innerText(), 'R28');
    assert.match(await page.locator('#recovery-archive-facts').innerText(), /50 \/ 50/);
    const priceData = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R27_20261118.json')));
    await page.setContent(raw.replace(/(<script id="execution-data" type="application\/json">)[\s\S]*?(<\/script>)/, '$1' + JSON.stringify(priceData).replace(/</g, '\\u003c') + '$2'));
    assert.equal(await page.locator('#data-error').isVisible(), false);
    assert.equal(await page.locator('#observed-release').innerText(), 'R27');
    assert.match(await page.locator('#current-cost-facts').innerText(), /Unknown · no verified current rate/);
    assert.doesNotMatch(await page.locator('#current-cost-facts').innerText(), /\$0\.00/);
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
  } finally { await context.close(); }
  const fresh = await browser.newContext();
  try {
    const reopened = await fresh.newPage();
    await reopened.goto(pathToFileURL(file).href);
    assert.equal(await reopened.locator('#latest-execution-tally').innerText(), '0 / 1');
    assert.equal(await reopened.locator('#latest-preserved-models').innerText(), '108');
    assert.equal(await reopened.locator('#attempt-filter').inputValue(), 'all');
    assert.equal(await reopened.locator('#attempt-rows tr').count(), expected.attempts.length);
  } finally { await fresh.close(); }
  const staticContext = await browser.newContext({ javaScriptEnabled: false });
  try {
    const staticPage = await staticContext.newPage();
    await staticPage.goto(pathToFileURL(file).href);
    assert.equal(await staticPage.locator('#latest-execution-tally').innerText(), '0 / 1');
    assert.equal(await staticPage.locator('#latest-source-rows tr').count(), 3);
    assert.match(await staticPage.locator('#latest-cpu-limit').innerText(), /conditional 180-second, 75% scientific utilization gate/);
  } finally { await staticContext.close(); }
  return { status: 'PASS', widths: [1440, 390], filter_views: views, checked_cells: cells,
    latest_actual_release: 'R33', latest_unsuccessful_invocations: 1, latest_automatic_interruptions: 1, latest_checked_cells: latestCells,
    latest_exact_downloads: latestDownloads, latest_preparation_status: latest.next_preparation.status,
    latest_readable_without_javascript: true,
    exact_downloads: downloads, corrupt_evidence_rejections: mutations.length, actual_observed_release: expected.latest_observed_attempt.release, checked_cells_per_viewport: cells / 2, current_partial_return_verified: true, fresh_context_reopened: true,
    next_preparation_status: expected.next_preparation.status, next_preparation_owner_executions: 0,
    engineering_tests: expected.next_preparation.engineering_tests,
    script_errors: 0, external_requests: 0, real_chromium: true };
}

module.exports = { verifyExecutionStatus };
if (require.main === module) {
  const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
  (async () => {
    const browser = await chromium.launch({ headless: true,
      ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
    try { console.log(JSON.stringify(await verifyExecutionStatus(browser, path.resolve(__dirname, '../../docs/ncaa/execution.html')))); }
    finally { await browser.close(); }
  })().catch(error => { console.error(error); process.exitCode = 1; });
}
