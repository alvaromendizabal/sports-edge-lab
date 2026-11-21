'use strict';
// Actual offline page checks; no owner fits, provider calls or deployment.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const folder = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(__dirname, '.browser-review'));
const source = fs.readFileSync(path.join(__dirname, 'b105_execution_status.json'));
const data = JSON.parse(source);
const html = fs.readFileSync(path.join(__dirname, 'b105_execution_status.html'));
const url = pathToFileURL(path.join(__dirname, 'b105_execution_status.html')).href;
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
fs.mkdirSync(folder, {recursive:true});

async function content(page) {
  assert.match(await page.locator('h1').innerText(), /B104 stopped\.\s+Completed science is preserved\./);
  assert.deepEqual(JSON.parse(await page.locator('#aggregate-evidence').textContent()), data);
  assert.equal((await page.locator('#prepared-status').innerText()).trim(), data.B105_preparation.status);
  assert.deepEqual(await page.locator('.cards .number').allTextContents(), ['201 + 201','24 pairs','15','320']);
  assert.deepEqual(await page.locator('#cpu .policy strong').allTextContents(), ['12','36','1']);
  assert.deepEqual(await page.locator('progress').evaluateAll(xs=>xs.map(x=>[x.value,x.max])), [[225,240]]);
  const text = await page.locator('body').innerText();
  for (const phrase of [
    'No verified B104 final return was published',
    'The 240 task records are not 240 successful fits',
    '225 validation tasks · 450 scored variants',
    '402 new validation ledgers and 48 reused ledgers',
    'All 30 context tasks reused existing work',
    '320 original state pins unchanged',
    'Zero new residual-distribution fits were needed',
    '1,141,248,706-byte selection lock',
    '13 identified frozen-test workers terminated by SIGKILL',
    "The owner's exact exit status was not retained",
    'attributing the owner itself to an OOM kill remains an inference',
    'No fixed three-minute timeout or LightGBM training defect was established',
    '32.2775 cores','29.4468 cores',
    'Peak samples do not establish the sustained 180-second / 75%-occupancy gate',
    'explicit 36-worker maximum is a hard ceiling','USD 200 compute guard',
    'Zero B105 owner executions and zero new owner fits are credited',
    '5,808 preserved baseline variants and 450 box-feature variants',
    'Their 2026–27 test metrics remain pending',
    '24 negative-control variants from rankings, leaving 6,234 ranked variants',
    '46 verified base-model results and 92 prediction ledgers',
    'At most 179 original base-model test inferences remain',
    '24 earlier cached results and 22 new B104 inference results',
    '14,719,711 bytes',
    'All nine read-only native launch-readiness gates passed',
    '60 native archive regression tests passed',
    '12 existing-model tasks, with 12 overlapping native model calls',
    'zero repeated frozen-test calls on warm resume',
    '4,889,866,240 bytes','4.1753–4.6783 cores','0.1161–0.2669 seconds',
    'The sustained 180-second / 75%-occupancy gate was not evaluated',
    'Four separate engineering-fixture optimizer calls',
    '35 objects passed full GET and SHA-256 verification',
    '1,321 games in 2024–25','1,322 in 2025–26','210 in the frozen 2026–27 test snapshot',
    'Independent full-season qualification and the all-contender comparison remain unfinished',
    'No full-season champion is certified','DraftKings, Kalshi and Polymarket',
    'No website deployment, new public per-game forecast values or champion promotion is established']) {
    assert.ok(text.includes(phrase), 'Missing qualification: '+phrase);
  }
  const expected = data.comparison.rows.map(r=>[
    r.target[0].toUpperCase()+r.target.slice(1)+' · '+r.horizon_minutes+' min',
    r.family==='sklearn_linear'?'Linear + Gaussian':'Extra Trees + Gaussian',
    r.crps_2024.toFixed(4),r.crps_2025.toFixed(4),r.validation_50_50.toFixed(4),r.crps_2026.toFixed(4)]);
  assert.deepEqual(await page.locator('#comparison tbody tr').evaluateAll(rows=>rows.map(r=>
    [...r.querySelectorAll('td')].map(x=>x.textContent.trim()))),expected);
  const families={B095_FIXED_CONVEX_BLEND:'Preserved fixed blend',catboost:'CatBoost',sklearn_extra_trees:'Extra Trees'};
  const objectives={rmse:'RMSE ↓',mae:'MAE ↓',log_loss:'Log loss ↓',brier:'Brier ↓',accuracy:'Accuracy ↑'};
  const score=value=>value===null?'Pending':value.toFixed(6);
  const points=data.point_comparison.rows.map(r=>[
    r.target[0].toUpperCase()+r.target.slice(1)+' · '+r.horizon_minutes+' min',
    objectives[r.objective],families[r.family],score(r.metric_2024),score(r.metric_2025),
    score(r.validation_50_50),score(r.metric_2026)]);
  assert.deepEqual(await page.locator('#point-comparison tbody tr').evaluateAll(rows=>rows.map(r=>
    [...r.querySelectorAll('td')].map(x=>x.textContent.trim()))),points);
  assert.equal(points.filter(row=>row[6]==='Pending').length,4);
  const phaseNames={FROZEN_TEST_AUTHORIZED_INFERENCE:'Frozen-test application',
    HISTORICAL_CALIBRATION_SERIALIZATION_PARITY:'Saved calibration parity',
    VALIDATION_REPLAY_COMPARE_WITH_B104:'Validation replay'};
  const native=data.native_verification.phase_measurements.map(r=>[
    phaseNames[r.phase],'12 / 12','1',r.measured_average_cores_during_call_window.toFixed(4),
    r.native_call_window_seconds.toFixed(4),'12']);
  assert.deepEqual(await page.locator('#native-verification tbody tr').evaluateAll(rows=>rows.map(r=>
    [...r.querySelectorAll('td')].map(x=>x.textContent.trim()))),native);
  assert.equal(await page.locator('.requirements li').count(),6);
  assert.equal(await page.locator('.sources li').count(),data.evidence.length);
  const preparation = await page.locator('#delivery-qualification').innerText();
  if(data.B105_preparation.native_installation_verified) assert.match(preparation,/native installation passed complete-byte/);
  else if(data.B105_preparation.delivery_full_body_readback_verified) assert.match(preparation,/native installation remains pending/);
  else assert.ok(/in progress|delivery remains unverified/.test(preparation));
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal page overflow');
  assert.deepEqual(await page.locator('td,th,.policy,.sources,.identity').evaluateAll(xs=>xs.filter(x=>{
    const b=x.getBoundingClientRect();return b.left< -1||b.right>innerWidth+1;
  }).map(x=>x.tagName+': '+x.textContent.slice(0,70))),[]);
  if(page.viewportSize().width<650) {
    const boxes = await page.locator('.progress-head').evaluateAll(xs=>xs.map(x=>({
      complete:x.querySelector('strong').getBoundingClientRect().bottom,
      failed:x.querySelector('span').getBoundingClientRect().top})));
    assert.ok(boxes.every(x=>x.failed>=x.complete-1),'Progress labels stay separate on mobile');
  }
}

async function evidenceDownload(page) {
  await page.locator('#download-evidence').focus();
  const [download] = await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);
  assert.equal(download.suggestedFilename(),'nba-b105-recovery-evidence.json');
  assert.equal(fs.readFileSync(await download.path(),'utf8'),source.toString('utf8'));
}

async function main() {
  const launch={headless:true};
  if(process.env.NBA_CHROMIUM_EXECUTABLE) launch.executablePath=process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser=await chromium.launch(launch),views=[];
  try {
    for(const [width,javascript] of [[1440,true],[390,true],[390,false]]) {
      const context=await browser.newContext({viewport:{width,height:1000},javaScriptEnabled:javascript,acceptDownloads:true});
      await context.setOffline(true);
      const page=await context.newPage(),errors=[],remote=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
      await page.goto(url);await content(page);
      for(const [selector,phrase] of [['#receipt-detail','5,607 unique S3 payloads'],['#selection-detail','Previously inspected test outcomes remain exposed'],['#point-detail','Preserved fixed blend']]) {
        await page.locator(selector+' summary').focus();await page.keyboard.press('Enter');
        assert.notEqual(await page.locator(selector).getAttribute('open'),null);
        assert.ok((await page.locator(selector).innerText()).includes(phrase));
      }
      assert.ok((await page.locator('#receipt-detail').innerText()).includes('zero missing, unknown or mismatched objects'));
      await content(page); // Recheck geometry with every table and detail open.
      await evidenceDownload(page);
      await page.getByRole('link',{name:'Measured CPU',exact:true}).focus();await page.keyboard.press('Enter');
      assert.equal(new URL(page.url()).hash,'#cpu');
      if(javascript)await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:path.join(folder,`nba-b105-status-${width}-${javascript?'js':'nojs'}.png`),fullPage:true});
      assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
      views.push({width,javascript,offline:true,page_errors:0,remote_requests:0,page_overflow:false,
        keyboard_details:true,keyboard_section_navigation:true,exact_evidence_download:true,
        all_comparison_cells_fit:true});
      await context.close();
    }
  } finally {await browser.close();}
  const receipt={schema:'sel.nba.b105.public_browser_receipt.v1',status:'PASS',
    html_sha256:sha256(html),json_sha256:sha256(source),source_head:process.env.NBA_SOURCE_HEAD_SHA||null,
    views,owner_executions:0,new_owner_fits:0,provider_requests:0,deployment_performed:false};
  fs.writeFileSync(path.join(folder,'nba-b105-browser-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
