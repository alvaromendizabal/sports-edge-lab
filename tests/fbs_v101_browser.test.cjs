'use strict';
// Local public rendering only: this test cannot execute owner research or providers.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const moduleDir = process.env.PLAYWRIGHT_MODULE_DIR || (process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright') : 'playwright');
const { chromium } = require(moduleDir), root = path.resolve(__dirname, '..'), file = path.join(root, 'docs/fbs/v101/index.html');
const body = fs.readFileSync(file, 'utf8'), data = JSON.parse(fs.readFileSync(path.join(root, 'docs/fbs/v101/data/status.json'), 'utf8'));
const shots = process.env.FBS_SCREENSHOTS || path.join(root, 'tmp/fbs-v101-browser'); fs.mkdirSync(shots, { recursive: true });
const sha = x => crypto.createHash('sha256').update(x).digest('hex'); let assertions = 0;
const eq = (a, b, label) => { assertions++; assert.deepEqual(a, b, label); }, check = (a, label) => { assertions++; assert.ok(a, label); };
const receipt = { schema: 'fbs.v101.public-browser-review.v1', status: 'RUNNING', github_sha: process.env.GITHUB_SHA || null, github_head_sha: process.env.GITHUB_HEAD_SHA || null, source_html_sha256: sha(body), source_html_bytes: Buffer.byteLength(body), views: [], downloads: [], invalid_inputs: [], owner_executions_started_by_check: 0 };
const invalid = new Map(), server = http.createServer((req, res) => { const content = req.url === '/' ? body : invalid.get(req.url); res.writeHead(content ? 200 : 404, { 'content-type': 'text/html; charset=utf-8' }); res.end(content || 'Not found'); });
(async () => {
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ headless: true, executablePath: process.env.FBS_BROWSER_EXECUTABLE || undefined });
  try {
    for (const variant of ['served', 'offline']) for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, acceptDownloads: true });
      const page = await context.newPage(), errors = [], requests = [];
      page.on('pageerror', e => errors.push(e.message)); page.on('request', r => requests.push(r.url()));
      await page.goto(variant === 'served' ? origin + '/' : 'file://' + file);
      await page.waitForFunction(() => document.documentElement.dataset.reportReady === 'true');
      eq(await page.locator('#kpis strong').allTextContents(), ['2', '0', '1,125', '600'], 'Failed owner and preserved successful science');
      check((await page.locator('#failure-summary').innerText()).includes('28,513 / 44,841'), 'Failed recovery denominator');
      check((await page.locator('#return-facts').innerText()).includes('73,426,500'), 'Actual compact return bytes');
      check((await page.locator('#cohort-note').innerText()).includes('919 / 934 / 755'), 'Original evaluation population retained');
      check((await page.locator('#cohort-note').innerText()).includes('757 completed 2026 games'), 'New census is separately displayed');
      eq(await page.locator('#preserved tbody tr').count(), 2, 'Both successful predecessor campaigns');
      eq(await page.locator('#performance tbody tr').count(), 2, 'Recovery and custody separated');
      eq(await page.locator('#performance tbody tr td:nth-child(4)').allTextContents(), ['1.055', '1.293'], 'Measured CPU, not configured workers');
      check((await page.locator('#cpu-note').innerText()).includes('no scientific occupancy acceptance'), 'No invented occupancy pass');
      check((await page.locator('#plan-facts').innerText()).includes('12 / 24 / 36'), 'Explicit worker ceilings');
      eq(await page.locator('#preparation-status').innerText(), data.next_release.prepared_complete ? 'Prepared · awaiting owner execution' : 'Preparation in progress', 'Preparation status matches evidence');
      eq(await page.locator('#canonical').isVisible(), data.next_release.prepared_complete, 'No premature release identity');
      if (data.next_release.prepared_complete) check((await page.locator('#canonical-facts').innerText()).includes(data.next_release.canonical_sha256), 'Exact final prepared identity');
      eq(await page.locator('#remaining-work tbody tr').count(), data.remaining_work.length, 'Unfinished science visible');
      for (const state of ['all', 'Failed', 'Pending', 'Authenticated completed', 'Running']) {
        await page.locator('#stage-filter').selectOption(state);
        const expected = data.attempt_stages.filter(s => state === 'all' || s.status === state);
        eq(await page.locator('#stage-table tbody tr').count(), expected.length, 'Full state population ' + state);
        eq(await page.locator('#stage-table tbody tr td:first-child').allTextContents(), expected.map(s => s.number + ' of 21'), 'Authoritative stage numbering ' + state);
      }
      await page.locator('#stage-filter').focus(); await page.keyboard.press('Home'); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
      eq(await page.locator('#stage-filter').inputValue(), 'Failed', 'Keyboard stage navigation');
      await page.locator('#stage-filter').selectOption('all');
      const wait = page.waitForEvent('download'); await page.locator('#download').focus(); await page.keyboard.press('Enter');
      const download = await wait, destination = path.join(shots, 'FBS_V101_' + variant + '_' + width + '_download.json'); await download.saveAs(destination);
      const embedded = body.match(/<script id="report-data" type="application\/json">(.*?)<\/script>/s)[1];
      eq(fs.readFileSync(destination, 'utf8'), embedded, 'Exact source-byte JSON download');
      eq(JSON.parse(fs.readFileSync(destination, 'utf8')), data, 'Full bounded source data');
      receipt.downloads.push({ variant, width, sha256: sha(fs.readFileSync(destination)) });
      check(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'No viewport overflow');
      eq(errors, [], 'No page errors'); eq(requests.filter(u => !u.startsWith(origin) && !u.startsWith('file://')), [], 'No external runtime requests');
      await page.evaluate(() => window.scrollTo(0, 0));
      if (variant === 'served') await page.screenshot({ path: path.join(shots, 'FBS_V101_' + width + '.png'), fullPage: true });
      receipt.views.push({ variant, width, script_errors: 0, external_requests: 0 }); await context.close();
    }
    const raw = body.match(/<script id="report-data" type="application\/json">(.*?)<\/script>/s)[1], digest = sha(raw);
    const cases = [
      ['changed_bytes', d => d.latest_attempt.new_model_fits = 765, false],
      ['false_owner_success', d => d.latest_attempt.child_exit_code = 0, true],
      ['false_scientific_cpu', d => d.performance.sustained_scientific_capacity_pass = true, true],
      ['census_as_evaluation', d => d.model_evaluation.completed_cohorts[2] = 757, true],
      ['unexecuted_science', d => d.next_release.owner_execution_started = true, true],
      ['test_selection', d => d.model_evaluation.test_used_for_selection = true, true],
    ];
    for (const [name, mutate, rehash] of cases) {
      const changed = JSON.parse(JSON.stringify(data)); mutate(changed); const next = JSON.stringify(changed).replace(/</g, '\\u003c');
      let html = body.replace(raw, next); if (rehash) html = html.replace("expected='" + digest + "'", "expected='" + sha(next) + "'");
      invalid.set('/invalid-' + name, html); const page = await browser.newPage(); await page.goto(origin + '/invalid-' + name);
      await page.waitForFunction(() => document.documentElement.dataset.reportReady === 'error');
      check(await page.locator('#report').isHidden(), 'Invalid evidence hidden: ' + name); check(await page.locator('#error').isVisible(), 'Visible integrity failure: ' + name);
      receipt.invalid_inputs.push(name); await page.close();
    }
    receipt.status = 'PASS'; receipt.assertions = assertions;
    fs.writeFileSync(path.join(shots, 'FBS_V101_BROWSER_RECEIPT.json'), JSON.stringify(receipt, null, 2) + '\n'); console.log(JSON.stringify(receipt));
  } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
})().catch(error => { receipt.status = 'FAIL'; receipt.error = String(error.stack || error); fs.writeFileSync(path.join(shots, 'FBS_V101_BROWSER_RECEIPT.json'), JSON.stringify(receipt, null, 2) + '\n'); console.error(error); process.exitCode = 1; server.close(); });
