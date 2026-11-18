'use strict';

// Offline report verification only. No owner executable or scientific job is run.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');

const directory = __dirname;
const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(directory, '.browser-review'));
const source = fs.readFileSync(path.join(directory, 'b099_execution_status.json'));
const evidence = JSON.parse(source.toString('utf8'));
const pageBytes = fs.readFileSync(path.join(directory, 'b099_execution_status.html'));
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
fs.mkdirSync(output, {recursive:true});

async function main() {
  const options = {headless:true};
  if (process.env.NBA_CHROMIUM_EXECUTABLE) options.executablePath = process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch(options);
  const views = [];
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({viewport:{width, height:1000}, acceptDownloads:true});
      await context.setOffline(true);
      const page = await context.newPage();
      const errors = [], remoteRequests = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      page.on('request', request => { if (/^https?:/.test(request.url())) remoteRequests.push(request.url()); });
      await page.goto(pathToFileURL(path.join(directory, 'b099_execution_status.html')).href);
      await page.getByRole('heading', {level:1}).waitFor();
      assert.match(await page.locator('h1').innerText(), /Startup failed before\s+scientific work began/);
      for (const [key, expected] of [['failed-attempts','2'], ['new-fits','0'], ['cpu-samples','0'], ['return-parts','13']]) {
        assert.equal(await page.locator(`[data-metric="${key}"]`).innerText(), expected);
      }
      const text = await page.locator('body').innerText();
      for (const phrase of ['Measured scientific cores are unknown.', 'PARTIAL_RESUMABLE', '6,530,108,006',
                           '672 new estimator fits', '1,232 new calibration fits', '320 registered residual-distribution heads',
                           '92.12% over 183.01s', '3.62% over 182.33s', 'No qualified full-season champion',
                           'Zero B099 owner executions', 'main integration pending', 'website deployment pending']) {
        assert.ok(text.includes(phrase), `Missing qualified evidence: ${phrase}`);
      }
      const embedded = await page.locator('#aggregate-evidence').textContent();
      assert.deepEqual(JSON.parse(embedded), evidence);
      assert.equal(await page.locator('.attempts tbody tr').count(), evidence.attempts.length);
      for (const [index, attempt] of evidence.attempts.entries()) {
        const row = await page.locator('.attempts tbody tr').nth(index).innerText();
        assert.ok(row.includes(attempt.run_at_utc.replace('T',' ').replace('Z',' UTC')));
        assert.ok(row.includes('0 / 0'));
        assert.ok(row.includes('before scientific dispatch'));
      }
      const noOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
      assert.ok(noOverflow, `Page-level overflow at ${width}px`);
      await page.locator('#download-status').focus();
      const [download] = await Promise.all([
        page.waitForEvent('download'), page.keyboard.press('Enter')
      ]);
      assert.equal(download.suggestedFilename(), 'b099_execution_status.json');
      const downloadPath = await download.path();
      assert.deepEqual(JSON.parse(fs.readFileSync(downloadPath, 'utf8')), evidence);
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({path:path.join(output, `nba-b099-status-${width}.png`), fullPage:true});
      assert.deepEqual(errors, []);
      assert.deepEqual(remoteRequests, []);
      views.push({page:'b099', width, offline:true, page_errors:0, remote_requests:0,
                  page_overflow:false, exact_evidence_download:true, independent_context:true});

      // The previously unrendered B098 snapshot remains unchanged and is reviewed too.
      await page.goto(pathToFileURL(path.join(directory, 'b098_execution_status.html')).href);
      await page.getByRole('heading', {level:1}).waitFor();
      assert.match(await page.locator('h1').innerText(), /The fits finished\.\s+The delivery did not\./);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
      await page.screenshot({path:path.join(output, `nba-b098-status-${width}.png`), fullPage:true});
      assert.deepEqual(errors, []);
      assert.deepEqual(remoteRequests, []);
      views.push({page:'b098_preserved', width, offline:true, page_errors:0,
                  remote_requests:0, page_overflow:false});
      await context.close();
    }
  } finally {
    await browser.close();
  }
  let checkout = null;
  try { checkout = execFileSync('git', ['rev-parse','HEAD'], {cwd:directory, encoding:'utf8'}).trim(); } catch {}
  const receipt = {schema:'sel.nba.b099.public_browser_receipt.v1', status:'PASS',
    html_sha256:sha256(pageBytes), json_sha256:sha256(source),
    source_head:process.env.NBA_SOURCE_HEAD_SHA || null, tested_checkout:checkout,
    views, owner_executions:0, new_owner_fits:0};
  fs.writeFileSync(path.join(output, 'nba-b099-browser-receipt.json'), JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));
}

main().catch(error => {console.error(error); process.exitCode = 1;});
