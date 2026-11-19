'use strict';

// Verify the real offline dashboard; zero owner fits, providers or deployments.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(__dirname, '.browser-review'));
const source = fs.readFileSync(path.join(__dirname, 'b104_execution_status.json'));
const evidence = JSON.parse(source.toString('utf8'));
const html = fs.readFileSync(path.join(__dirname, 'b104_execution_status.html'));
const url = pathToFileURL(path.join(__dirname, 'b104_execution_status.html')).href;
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
fs.mkdirSync(output, {recursive: true});

async function checkContent(page) {
  assert.match(await page.locator('h1').innerText(), /Completed work preserved\.\s+The next campaign is prepared separately\./);
  assert.deepEqual(JSON.parse(await page.locator('#aggregate-evidence').textContent()), evidence);
  assert.equal((await page.locator('#prepared-status').innerText()).trim(), evidence.B104_preparation.status);
  assert.deepEqual(await page.locator('.cards .number').allTextContents(), ['12 + 12', '0', '320', '0']);
  assert.deepEqual(await page.locator('.policy strong').allTextContents(), ['12', '36', '1']);
  assert.deepEqual(await page.locator('progress').evaluateAll(items => items.map(x => [x.value, x.max])),
    [[evidence.cumulative_registered_work.preserved_validation_replay_groups_complete,
      evidence.cumulative_registered_work.preserved_validation_replay_groups_registered],
     [evidence.cumulative_registered_work.box_base_estimators_complete,
      evidence.cumulative_registered_work.box_base_recipes_registered]]);
  const body = await page.locator('body').innerText();
  for (const phrase of ['PARTIAL_RESUMABLE_BOUNDED_ACCEPTANCE', 'policy exit 2',
    '12 new estimators, 12 new calibrators and zero failed jobs',
    '846 / 2,429 replay groups complete', '1,583 still missing',
    '24 / 240 box-score base recipes complete', '216 still missing',
    '20,226 bytes and eight payloads', 'actual invoiced cost and NBA allocation are unknown',
    '12–36 cores', 'explicit 36-worker maximum is a hard ceiling',
    'USD 200 compute guard', 'after validation selection locks',
    '20.442 CPU equivalents', '4.6169 CPU equivalents', '50.10 seconds',
    'CONDITIONAL_SHORT_QUEUE_COMPLETION_NOT_FULL_CAPACITY_PASS',
    'Zero sustained 180-second / 75%-occupancy passes',
    'Frozen snapshot; fresh all-completed census unfinished',
    'No website deployment or champion promotion is established',
    'DraftKings, Kalshi and Polymarket']) {
    assert.ok(body.includes(phrase), `Missing or changed qualification: ${phrase}`);
  }
  const rows = await page.locator('#population tbody tr').evaluateAll(items =>
    items.map(row => Array.from(row.querySelectorAll('td')).slice(0, 2).map(cell => cell.textContent.trim())));
  assert.deepEqual(rows, [['1,314', '1,321'], ['1,315', '1,322'], ['210', '210']]);
  assert.equal(await page.locator('.requirements li').count(), 5);
  assert.equal(await page.locator('.sources li').count(), 4);
  const delivered = evidence.B104_preparation.delivery_full_body_readback_verified;
  const qualification = await page.locator('#delivery-qualification').innerText();
  if (delivered && evidence.B104_preparation.native_physical_installation_verified) {
    assert.match(qualification, /Prepared private delivery and native installation are verified/);
    assert.match(qualification, /full research campaign has not been launched/);
  } else if (delivered) {
    assert.match(qualification, /Complete-byte verification supports the prepared private delivery/);
    assert.match(qualification, /Native installation and the next owner execution remain pending/);
  } else {
    assert.match(qualification, /No completed private upload or native installation is certified/);
  }
  const readiness = await page.locator('#readiness-qualification').innerText();
  if (evidence.B104_preparation.native_readiness_verified) {
    assert.match(readiness, /Read-only native readiness passed/);
    assert.match(readiness, /zero research fits/);
  } else {
    assert.match(readiness, /readiness remains unverified/);
  }
  if (evidence.B104_preparation.canonical_executable) {
    assert.ok(body.includes(evidence.B104_preparation.canonical_executable.sha256));
  }
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
    'Current review must not require horizontal page scrolling');
  const overflow = await page.locator('#population td, #population th, .policy, .identity, .sources').evaluateAll(items =>
    items.filter(el => { const box = el.getBoundingClientRect(); return box.left < -1 || box.right > innerWidth + 1; })
      .map(el => ({tag: el.tagName, text: el.textContent.slice(0, 100)})));
  assert.deepEqual(overflow, [], 'Every population cell, policy and evidence identity must fit');
}

async function downloadEvidence(page) {
  await page.locator('#download-evidence').focus();
  const [download] = await Promise.all([page.waitForEvent('download'), page.keyboard.press('Enter')]);
  assert.equal(download.suggestedFilename(), 'nba-b104-current-status-evidence.json');
  assert.equal(fs.readFileSync(await download.path(), 'utf8'), source.toString('utf8'));
}

async function main() {
  const launch = {headless: true};
  if (process.env.NBA_CHROMIUM_EXECUTABLE) launch.executablePath = process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch(launch), views = [];
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({viewport: {width, height: 1000}, acceptDownloads: true});
      await context.setOffline(true);
      const page = await context.newPage(), errors = [], remoteRequests = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      page.on('request', request => { if (/^https?:/.test(request.url())) remoteRequests.push(request.url()); });
      await page.goto(url);
      await checkContent(page);
      const reuse = page.locator('#reuse-detail');
      await reuse.locator('summary').focus(); await page.keyboard.press('Enter');
      assert.notEqual(await reuse.getAttribute('open'), null);
      assert.match(await reuse.innerText(), /actual application counter remains unknown/);
      assert.match(await reuse.innerText(), /zero missing files required restoration/);
      const selection = page.locator('#selection-detail');
      await selection.locator('summary').focus(); await page.keyboard.press('Enter');
      assert.notEqual(await selection.getAttribute('open'), null);
      assert.match(await selection.innerText(), /must not refit estimators or reweight training seasons/);
      assert.match(await selection.innerText(), /Previously inspected test outcomes remain exposed/);
      await downloadEvidence(page);
      await page.getByRole('link', {name: 'Measured CPU', exact: true}).focus();
      await page.keyboard.press('Enter'); assert.equal(new URL(page.url()).hash, '#cpu');
      await page.evaluate(() => scrollTo(0, 0));
      await page.screenshot({path: path.join(output, `nba-b104-status-${width}.png`), fullPage: true});
      assert.deepEqual(errors, []); assert.deepEqual(remoteRequests, []);
      views.push({width, offline: true, page_errors: 0, remote_requests: 0,
        page_overflow: false, exact_evidence_download: true, keyboard_details: true,
        keyboard_section_link: true, all_population_cells_fit: true});
      await context.close();
    }
    const context = await browser.newContext({viewport: {width: 390, height: 1000},
      javaScriptEnabled: false, acceptDownloads: true});
    await context.setOffline(true);
    const page = await context.newPage(); await page.goto(url); await checkContent(page);
    await page.locator('#selection-detail summary').focus(); await page.keyboard.press('Enter');
    assert.notEqual(await page.locator('#selection-detail').getAttribute('open'), null);
    await downloadEvidence(page);
    views.push({width: 390, offline: true, javascript: false,
      complete_evidence_visible: true, native_details: true, exact_evidence_download: true});
    await context.close();
  } finally {
    await browser.close();
  }
  let checkout = null;
  try {
    checkout = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: __dirname,
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']}).trim();
  } catch {}
  const receipt = {schema: 'sel.nba.b104.public_browser_receipt.v1', status: 'PASS',
    html_sha256: sha256(html), json_sha256: sha256(source),
    source_head: process.env.NBA_SOURCE_HEAD_SHA || null, tested_checkout: checkout,
    views, owner_executions: 0, new_owner_fits: 0, provider_requests: 0,
    deployment_performed: false};
  fs.writeFileSync(path.join(output, 'nba-b104-browser-receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify(receipt));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
