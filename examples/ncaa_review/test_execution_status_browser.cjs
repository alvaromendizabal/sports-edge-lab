'use strict';
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
  let views = 0, cells = 0, downloads = 0;
  try {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(pathToFileURL(file).href);
      await page.locator('#attempt-rows tr').first().waitFor();
      assert.equal(await page.locator('#observed-release').innerText(), 'R30');
      assert.equal(await page.locator('#verified-release').innerText(), 'R30');
      assert.match(await page.locator('#observed-status').innerText(), /failed resumable/i);
      assert.equal(await page.locator('#current-execution-panel').isVisible(), true);
      assert.match(await page.locator('#current-work-facts').innerText(), /1,255 reused · 0 fresh/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Requested workers \/ scientific peak\s+24 \/ 0/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Not run · source stage blocked dispatch/);
      assert.match(await page.locator('#current-cost-facts').innerText(), /Succeeded · integrity verified/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Historical target checkpoint reuses\s+108/);
      assert.match(await page.locator('#current-work-facts').innerText(), /Current-consumer target reuses\s+0/);
      const costFacts = await page.locator('#current-cost-facts').innerText();
      assert.match(costFacts, /\$0\.67/);
      assert.doesNotMatch(costFacts, /\$0\.00/);
      assert.match(costFacts, /Budget exhaustion established\s+No · verified estimate below guard/);
      assert.match(await page.locator('#current-work-facts').innerText(), /823 \/ 32/);
      assert.match(await page.locator('#attempt-scope').innerText(), /11 audited attempts · 9 distinct run identities/);
      assert.match(await page.locator('#snapshot-time').innerText(), /Pacific.*not a live status feed/);
      assert.equal(await page.locator('#preserved-fits').innerText(), '11');
      assert.match(await page.locator('#throughput-facts').innerText(), /12–24-core science proven\s+No/);
      assert.equal(await page.locator('#recovery-evidence-panel').isVisible(), true);
      assert.match(await page.locator('#recovery-archive-facts').innerText(), /Historical target checkpoints authenticated\s+108/);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /Scientific occupancy gate executed\s+No/);
      assert.equal(await page.locator('#next-preparation-state').innerText(),
        `R31 · ${expected.next_preparation.status} · 0 owner executions`);
      assert.equal(await page.locator('#preparation-stages li').count(), 4);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /1\.23 cores/);
      assert.match(await page.locator('#recovery-clock-facts').innerText(), /1\.40 cores/);
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
    assert.match(await page.locator('#v12-current-evidence').innerText(), /latest observed R30.*published return and 220 payloads are verified/is);
    assert.equal(await page.locator('#v12-current-evidence a[href="execution.html"]').count(), 1);
    await page.locator('#v12-current-evidence a[href="execution.html"]').click();
    assert.equal(await page.locator('#observed-release').innerText(), 'R30');
    const raw = fs.readFileSync(file, 'utf8');
    const mutations = [d => {d.publication.new_fits = 1;}, d => {d.latest_verified_return.integrity = 'UNVERIFIED';},
    d => {d.science_contract.test_selection_weight = .1;}, d => {d.throughput.newer_12_to_24_core_science_proven = true;},
    d => {d.current_execution.new_target_fits = 1;}, d => {d.current_execution.scientific_gate_executed = true;},
    d => {d.latest_observed_attempt.return_published = false;}, d => {d.current_execution.cost_basis = 'INVOICE';},
    d => {d.current_execution.estimated_instance_wall_cost_usd = 0;}, d => {d.current_execution.estimated_instance_wall_cost_usd = 200;},
    d => {d.current_execution.failure.budget_exhaustion_proven = true;}, d => {d.current_execution.failure.recorded_error = 'V7_BOUNDED_IO_PRESSURE';},
    d => {d.current_execution.historical_checkpoint_reuses = 0;}, d => {d.clock_recovery_evidence.historical_checkpoints_verified = 0;},
    d => {d.current_execution.pressure_wait_seconds = 15.15;}, d => {d.audit_scope.audited_attempts = 7;},
    d => {d.next_preparation.owner_executions = 1;}, d => {d.clock_recovery_evidence.recorded_source_refresh_complete = true;},
    d => {d.current_execution.failure.pointer_status = 'COMPLETED';}, d => {d.next_preparation.engineering_evidence_sha256 = 'unverified';},
    d => {d.clock_recovery_evidence.useful_scientific_worker_cores = 12;}, d => {d.current_execution.peak_scientific_workers = 24;},
    d => {d.current_execution.reused_startup_tests = 1219;}, d => {d.clock_recovery_evidence.current_consumer_target_reuses = 108;}];
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
    assert.equal(await reopened.locator('#attempt-filter').inputValue(), 'all');
    assert.equal(await reopened.locator('#attempt-rows tr').count(), expected.attempts.length);
  } finally { await fresh.close(); }
  return { status: 'PASS', widths: [1440, 390], filter_views: views, checked_cells: cells,
    exact_downloads: downloads, corrupt_evidence_rejections: 24, actual_observed_release: expected.latest_observed_attempt.release, checked_cells_per_viewport: cells / 2, current_partial_return_verified: true, fresh_context_reopened: true,
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
