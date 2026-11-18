'use strict';
// Real rendering of the bounded public report. No scientific owner work runs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const moduleDir = process.env.PLAYWRIGHT_MODULE_DIR || (process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright') : 'playwright');
const { chromium } = require(moduleDir);
const root = path.resolve(__dirname, '..');
const file = path.join(root, 'docs/fbs/v097/index.html');
const body = fs.readFileSync(file, 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'docs/fbs/v097/data/status.json'), 'utf8'));
const shots = process.env.FBS_SCREENSHOTS || path.join(root, 'tmp/fbs-v097-browser');
fs.mkdirSync(shots, { recursive:true });
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
let assertions = 0;
function check(condition, label) { assertions++; assert.ok(condition, label); }
function eq(actual, expected, label) { assertions++; assert.deepEqual(actual, expected, label); }
const objective = x => x.target[0].toUpperCase() + x.target.slice(1) + ' ' + ({ accuracy:'accuracy', brier:'Brier', log_loss:'log loss', mae:'MAE', rmse:'RMSE', crps:'CRPS' }[x.metric]);
const metric = (value, kind) => kind === 'accuracy' ? (100*value).toFixed(4)+'%' : value.toFixed(6);
const receipt = { schema:'fbs.v097.public-browser-review.v1', status:'RUNNING', github_sha:process.env.GITHUB_SHA || null, github_head_sha:process.env.GITHUB_HEAD_SHA || null, source_html_sha256:sha(body), source_html_bytes:Buffer.byteLength(body), views:[], downloads:[], invalid_inputs:[], owner_executions_started_by_check:0 };
const invalid = new Map();
const server = http.createServer((req, res) => {
  const content = req.url === '/' ? body : invalid.get(req.url);
  res.writeHead(content ? 200 : 404, { 'content-type':'text/html; charset=utf-8' });
  res.end(content || 'Not found');
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ headless:true, executablePath:process.env.FBS_BROWSER_EXECUTABLE || undefined });
  try {
    for (const variant of ['source','offline']) for (const width of [1440,390]) {
      const context = await browser.newContext({ viewport:{ width,height:1000 }, acceptDownloads:true });
      const page = await context.newPage();
      const errors=[], requests=[];
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => requests.push(r.url()));
      await page.goto(variant === 'source' ? origin+'/' : 'file://'+file);
      await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
      eq(await page.locator('#new-fits').innerText(), '312', 'New base fits remain separate');
      eq(await page.locator('#complete-jobs').innerText(), '936 / 936', 'Completed registry denominator');
      eq(await page.locator('#fit-processes').innerText(), '17', 'Actual fit processes, not requested ceiling');
      eq(await page.locator('#test-games').innerText(), '755', 'Known test population');
      const facts = await page.locator('#actual-facts').innerText();
      check(facts.includes('0 / 0') && facts.includes('Incomplete'), 'Operational success and partial science are separate');
      eq(await page.locator('#actual-facts div').filter({hasText:'Historical failed attempts'}).locator('dd').innerText(), '6', 'Historical failure tally stays fixed');
      eq(await page.locator('#actual-facts div').filter({hasText:'Operationally finished attempts'}).locator('dd').innerText(), '1', 'Actual success counted once');
      const gate = await page.locator('#gate-facts').innerText();
      check(gate.includes('87.0095% of 17') && gate.includes('79.8297% of 17') && gate.includes('180.078 s'), 'Actual qualifying window retains both CPU measures');
      check((await page.locator('#gate-limit').innerText()).includes('include calibrators'), 'Gate completion count is not base-fit count');
      check((await page.locator('#phase-facts').innerText()).includes('267.657 s / 255.872 CPU-s'), 'Serial grading wall and CPU are visible');
      check((await page.locator('#queue-definition').innerText()).includes('not pure starvation'), 'Queue waiting definition stays explicit');
      eq(await page.locator('#phase-bars .phase').count(), 3, 'Independent phase CPU visualization');
      check((await page.locator('#queue-facts').innerText()).includes('$1.438130'), 'Whole-invocation estimate, not subset sum');
      check((await page.locator('#population-facts').innerText()).includes('123 / 133') && (await page.locator('#population-facts').innerText()).includes('93 / 133'), 'Pending forecast gaps remain visible');
      check((await page.locator('#next-status').innerText()).includes(data.next_preparation.status === 'PREPARED_NOT_EXECUTED' ? 'native-verified' : 'under preparation'), 'Preparation claim follows sealed evidence');
      check((await page.locator('#next-facts').innerText()).includes('306'), 'Finite next research tranche is explicit');
      check((await page.locator('#summary-comparison').innerText()).includes('131,276,993 → 137,541') && (await page.locator('#summary-comparison').innerText()).includes('does not predict'), 'Measured serialization reduction is not a future total size claim');
      check((await page.locator('#storage-facts').innerText()).includes('1.677 GB') && (await page.locator('#storage-facts').innerText()).includes('35.484 GB'), 'Control ZIP does not hide payload storage');
      eq(await page.locator('#remaining-branches .branch').count(), data.remaining_work.length, 'Incomplete scientific branches retained');

      // Exercise every data choice once; mobile and offline states retain default invariants.
      if (variant === 'source' && width === 1440) {
        for (const profile of data.selection.profiles) {
          await page.locator('#profile').selectOption(profile);
          const expected = data.selection.leaders.filter(x => x.profile === profile);
          eq(await page.locator('#leader-rows tr').count(), 9, 'Nine objectives for '+profile);
          for (const row of expected) {
            const cells = await page.locator('#leader-rows tr').filter({ hasText:objective(row) }).locator('td').allTextContents();
            eq(cells.slice(2), [metric(row.annual_values[0],row.metric), metric(row.annual_values[1],row.metric), metric(row.selection_score,row.metric), metric(row.annual_values[2],row.metric)], 'Exact annual and selection metrics for '+profile+' '+objective(row));
            check(cells[1].includes(row.family) && cells[1].includes(row.policy_alias), 'Coarse policy identity remains stable');
          }
        }
        await page.locator('#profile').selectOption('50/50');
        await page.locator('#leaders details summary').click();
        for (const row of data.selection.leaders.filter(x => x.profile === '50/50')) {
          const actual = await page.locator('#rank-rows tr').filter({ hasText:objective(row) }).locator('td').allTextContents();
          eq(actual.slice(1), data.selection.profiles.map(profile => String(data.selection.leaders.find(x => x.profile === profile && x.target === row.target && x.metric === row.metric).primary_policy_rank)), 'Saved sensitivity ranks for '+objective(row));
        }
        await page.locator('#leaders details summary').click();
        for (const season of [2024,2025,2026]) for (const target of ['winner','margin','total']) {
          await page.locator('#source-season').selectOption(String(season));
          await page.locator('#source-target').selectOption(target);
          eq(await page.locator('#source-rows tr').count(), 18, 'All recorded products for '+season+' '+target);
          for (const row of data.sources.t120_completed_coverage.filter(x => x.season === season && x.target === target)) {
            const tr = page.locator('#source-rows tr[data-bookmaker="'+row.bookmaker+'"]');
            const cells = await tr.locator('td').allTextContents();
            eq(cells.slice(1), [row.feature_qualified_n+' / '+row.expected_n, row.strict_original_availability_qualified_n+' / '+row.expected_n, row.predictive_baseline_qualified_n+' / '+row.expected_n], 'Exact qualified/reference scope for '+row.bookmaker+' '+season+' '+target);
          }
        }
        await page.locator('#source-season').selectOption('2026');
        await page.locator('#source-target').selectOption('winner');
      }
      await page.locator('#profile').focus();
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      eq(await page.locator('#profile').inputValue(), '40/60', 'Keyboard changes validation sensitivity');
      check((await page.locator('#profile-note').innerText()).includes('zero sensitivity refits'), 'Changing ratios does not refit');
      await page.locator('#profile').selectOption('50/50');
      const pending = page.waitForEvent('download');
      await page.locator('#download').focus();
      await page.keyboard.press('Enter');
      const download = await pending;
      const destination = path.join(shots, 'FBS_V097_'+variant+'_'+width+'_evidence.json');
      await download.saveAs(destination);
      eq(JSON.parse(fs.readFileSync(destination,'utf8')), data, 'Downloaded evidence exactly matches embedded record');
      receipt.downloads.push({ variant,width,sha256:sha(fs.readFileSync(destination)),bytes:fs.statSync(destination).size });
      fs.unlinkSync(destination); // The committed projection is the single retained copy.
      const dims = await page.evaluate(() => ({ viewport:innerWidth,body:document.documentElement.scrollWidth }));
      check(dims.body <= dims.viewport+1, 'No page-wide horizontal overflow');
      eq(errors, [], 'No script errors');
      eq(requests.filter(x => /^https?:/.test(x) && !x.startsWith(origin)), [], 'No external network requests');
      if (variant === 'offline') eq(requests.filter(x => /^https?:/.test(x)), [], 'Standalone report needs no network');
      const view = { variant,width,viewport_height:1000,page_errors:errors,network_requests:requests,page_overflow_pixels:dims.body-dims.viewport };
      if (variant === 'source') {
        await page.evaluate(() => { document.activeElement.blur(); window.scrollTo(0,0); });
        const screenshot = path.join(shots,'FBS_V097_'+width+'.png');
        await page.screenshot({ path:screenshot,fullPage:true });
        view.full_page_screenshot=path.basename(screenshot);
        view.screenshot_sha256=sha(fs.readFileSync(screenshot));
      }
      receipt.views.push(view);
      await context.close();
    }
    // Modified data is served over the same secure localhost origin so rejection
    // proves the digest guard, not a missing WebCrypto API on about:blank.
    const cases = [
      ['metric_changed', d => d.selection.leaders[0].annual_values[2]=0.99],
      ['test_selection', d => d.selection.test_used_for_selection=true],
      ['partial_claimed_complete', d => d.execution.scientific_complete=true],
      ['requested_cores_claimed_measured', d => d.cpu.observed_fit_processes=24],
      ['new_private_field', d => d.private_payload='/private/not-public'],
    ];
    for (const [label,edit] of cases) {
      const changed=structuredClone(data); edit(changed);
      invalid.set('/'+label, body.replace(/(<script id="report-data" type="application\/json">)[\s\S]*?(<\/script>)/, (_,a,b) => a+JSON.stringify(changed).replace(/</g,'\\u003c')+b));
    }
    invalid.set('/malformed_json',body.replace(/(<script id="report-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+'{"invalid":'+b));
    for (const url of invalid.keys()) {
      const context=await browser.newContext(),page=await context.newPage();
      await page.goto(origin+url);
      await page.waitForFunction(() => document.documentElement.dataset.ready==='error');
      check(await page.locator('#error').isVisible(), url+' is visibly rejected');
      check(!(await page.locator('#report').isVisible()),url+' hides stale evidence');
      check((await page.locator('#error').innerText()).includes('does not match'),url+' fails the expected integrity check');
      receipt.invalid_inputs.push({ label:url.slice(1),rejected:true });
      await context.close();
    }
    receipt.status='PASS';receipt.assertions=assertions;
    fs.writeFileSync(path.join(shots,'FBS_V097_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');
    process.stdout.write(JSON.stringify({ status:receipt.status,assertions,views:receipt.views.length,source_html_sha256:receipt.source_html_sha256,receipt:'FBS_V097_BROWSER_RECEIPT.json' })+'\n');
  } finally { await browser.close();await new Promise(resolve => server.close(resolve)); }
})().catch(error => {
  receipt.status='FAIL';receipt.error=String(error.stack||error);
  fs.writeFileSync(path.join(shots,'FBS_V097_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');
  server.close();console.error(error);process.exitCode=1;
});
