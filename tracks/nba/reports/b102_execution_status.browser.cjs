'use strict';

// Offline rendering of sanitized aggregate evidence. No owner fits or requests.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(__dirname,'.browser-review'));
const source = fs.readFileSync(path.join(__dirname,'b102_execution_status.json'));
const evidence = JSON.parse(source.toString('utf8'));
const html = fs.readFileSync(path.join(__dirname,'b102_execution_status.html'));
const url = pathToFileURL(path.join(__dirname,'b102_execution_status.html')).href;
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
fs.mkdirSync(output,{recursive:true});

async function checkContent(page) {
  assert.match(await page.locator('h1').innerText(),/Saved projections recovered\.\s+Scientific completion remains open\./);
  assert.deepEqual(JSON.parse(await page.locator('#aggregate-evidence').textContent()),evidence);
  const body=await page.locator('body').innerText();
  for(const phrase of ['PARTIAL_RESUMABLE','B101 · FAILED · EXIT 2',
    '2,374 of 5,808 projection tasks complete and 3,434 deferred',
    'zero individual projection failures','one worker','180.84 seconds','60.44 CPU-seconds',
    '33.42% of one admitted core','64 MiB interprocess message contract',
    '6,969,600 verified records','0 missing · 0 null · 0 regenerated',
    '210 completed test games and 990 upcoming games','zero newly generated projection outputs',
    '21 overlapping tasks','1.17 CPU equivalents','far below 12–24 busy cores',
    'slow publication filled the shared outstanding-work limit','22 targeted engineering tests passed',
    'These tests are not owner scientific utilization','75% occupancy / 180-second acceptance',
    'Failed measurements remain failures','Fourteen known validation omissions remain',
    'Previously inspected test results remain exposed','full-season cohort',
    'DraftKings, Kalshi and Polymarket','Scientific selection remains separate from production promotion']) {
    assert.ok(body.includes(phrase),`Missing or changed qualified evidence: ${phrase}`);
  }
  assert.equal(await page.locator('.cards .card').count(),4);
  assert.deepEqual(await page.locator('.cards .number').allTextContents(),['5,808 / 5,808','320','21','0']);
  assert.equal(await page.locator('.sources li').count(),7);
  assert.equal(await page.locator('.population').count(),3);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),
    'The recovery audit must remain readable without horizontal page scrolling');
}

async function main() {
  const launch={headless:true};
  if(process.env.NBA_CHROMIUM_EXECUTABLE)launch.executablePath=process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser=await chromium.launch(launch),views=[];
  try {
    for(const width of [1440,390]) {
      const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});
      await context.setOffline(true);
      const page=await context.newPage(),errors=[],remoteRequests=[];
      page.on('pageerror',error=>errors.push(error.message));
      page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
      page.on('request',request=>{if(/^https?:/.test(request.url()))remoteRequests.push(request.url());});
      await page.goto(url);
      await checkContent(page);
      // The native details control is keyboard-operable and keeps restoration
      // distinct from verification and application.
      const details=page.locator('#recovered details');
      assert.equal(await details.getAttribute('open'),null);
      await details.locator('summary').focus();
      await page.keyboard.press('Enter');
      assert.notEqual(await details.getAttribute('open'),null);
      assert.match(await details.innerText(),/Zero missing files required restoration/);
      assert.match(await details.innerText(),/not proof of renewed model application/);
      // Verify exact downloaded evidence, not merely the presence of a link.
      await page.locator('#download-evidence').focus();
      const [download]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);
      assert.equal(download.suggestedFilename(),'nba-b102-recovery-evidence.json');
      assert.equal(fs.readFileSync(await download.path(),'utf8'),JSON.stringify(evidence,null,2)+'\n');
      await page.getByRole('link',{name:'CPU evidence',exact:true}).focus();
      await page.keyboard.press('Enter');
      assert.equal(new URL(page.url()).hash,'#throughput');
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:path.join(output,`nba-b102-status-${width}.png`),fullPage:true});
      assert.deepEqual(errors,[]);assert.deepEqual(remoteRequests,[]);
      views.push({width,offline:true,page_errors:0,remote_requests:0,page_overflow:false,
        exact_evidence_download:true,keyboard_details:true,keyboard_section_link:true});
      await context.close();
    }
    const context=await browser.newContext({viewport:{width:390,height:1000},javaScriptEnabled:false,acceptDownloads:true});
    await context.setOffline(true);
    const page=await context.newPage();await page.goto(url);
    await checkContent(page);
    assert.ok(await page.locator('#download-evidence').isVisible());
    await page.locator('#recovered summary').focus();await page.keyboard.press('Enter');
    assert.notEqual(await page.locator('#recovered details').getAttribute('open'),null);
    views.push({width:390,offline:true,javascript:false,complete_evidence_visible:true,native_details:true,download_available:true});
    await context.close();
  } finally {await browser.close();}
  let checkout=null;
  try {checkout=execFileSync('git',['rev-parse','HEAD'],{cwd:__dirname,encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim();}catch{}
  const receipt={schema:'sel.nba.b102.public_browser_receipt.v1',status:'PASS',
    html_sha256:sha256(html),json_sha256:sha256(source),
    source_head:process.env.NBA_SOURCE_HEAD_SHA||null,tested_checkout:checkout,views,
    owner_executions:0,new_owner_fits:0,provider_requests:0};
  fs.writeFileSync(path.join(output,'nba-b102-browser-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
