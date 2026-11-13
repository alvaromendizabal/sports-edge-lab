// Real Chromium: actual failed-owner scope, retained metrics, export and mobile layout.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

async function verifyR9(browser, filename) {
  const page = await browser.newPage({acceptDownloads:true});
  const failures = [], external = [], viewports = [];
  const raw = fs.readFileSync(path.join(path.dirname(filename),'data/B063R9_PUBLIC_STATUS.json'),'utf8');
  const expected = JSON.parse(raw);
  page.on('pageerror',error=>failures.push(error.message));
  page.on('request',request=>{if(!/^(file|data|blob):/.test(request.url()))external.push(request.url());});
  try {
    for (const width of [1440,390]) {
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(filename).href);
      assert.deepEqual(JSON.parse(await page.locator('#b063r9-data').textContent()),expected);
      assert.deepEqual(await page.locator('#r9-cards strong').allTextContents(),['1 core','0 fits','1.397 GB','10.011s']);
      assert.match(await page.locator('#r9-failure').innerText(),/B051_SCHEDULE_EXACT_FULL_READBACK_REQUIRED/);
      assert.match(await page.locator('#r9-failure').innerText(),/1\.000436 cores/);
      assert.match(await page.locator('#r9-scope').innerText(),/no new forecasts, market quotes or metric scores/);
      assert.match(await page.locator('#r9-scope').innerText(),/not a certified complete season/);
      assert.match(await page.locator('#r9-cache').innerText(),/1,396,887,267/);
      assert.match(await page.locator('#r9-cache').innerText(),/119 hits and 1,396,887,736/);
      assert.match(await page.locator('#r9-cache').innerText(),/two verified full GETs totaling 24,079,252/);
      assert.match(await page.locator('#r9-logs').innerText(),/10\.010604 seconds/);
      assert.match(await page.locator('#r9-logs').innerText(),/Events after capture remain external/);
      assert.match(await page.locator('#r9-logs').innerText(),/estimate, not an invoice/);
      assert.equal(await page.locator('#r9-phases tbody tr').count(),6);
      assert.equal(await page.locator('#r9-coverage-table tbody tr').count(),7);
      assert.match(await page.locator('#r9-coverage-table').innerText(),/3,457.*not certified unique games/s);
      assert.match(await page.locator('#r9-coverage-table').innerText(),/Complete current-season and upcoming schedule.*Unverified/s);
      const rows = await page.locator('#r9-metric-table tbody tr').allInnerTexts();
      assert.equal(rows.length,14);
      assert.equal(rows.filter(text=>text.startsWith('Men')).length,7);
      assert.equal(rows.filter(text=>text.startsWith('Women')).length,7);
      for (const row of expected.preserved_science.current_observed_replay_leaders) {
        const label = row.league==='ncaam'?'Men':'Women';
        assert(rows.some(text=>text.startsWith(label)&&text.includes(row.public_model_ids[0])
          &&text.includes(row.metric_name_for_display.replaceAll('_',' '))
          &&text.includes(row.value.toFixed(6))&&text.includes(String(row.games))));
      }
      assert.equal(await page.locator('#r9-provider-table tbody tr').count(),4);
      assert.deepEqual(await page.locator('#r9-provider-table tbody td:nth-child(2)').allTextContents(),['0','0','0','338']);
      assert.match(await page.locator('#r9-repair').innerText(),/legacy adoption chain still runs/);
      assert.match(await page.locator('#r9-receipt-benchmark').innerText(),/112 captured JSON receipt\/metadata files/);
      assert.match(await page.locator('#r9-receipt-benchmark').innerText(),/2\.389× speedup for that subset only/);
      await page.locator('#r9-verification summary').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r9-verification').getAttribute('open'),'');
      assert.equal(await page.locator('#r9-source').textContent(),
        expected.prepared_continuation.source_sha256||'Final source fingerprint pending');
      assert.match(await page.locator('#r9-verification').innerText(),/Local engineering checks receive zero sports-fit credit/);
      assert.match(await page.locator('#r9-publication').innerText(),/does not establish a deployed website/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,
        `status page must fit ${width}px; tables may scroll inside their bounded wrappers`);
      const downloadPromise = page.waitForEvent('download');
      await page.locator('#r9-download').click();
      const download = await downloadPromise;
      const temporary = fs.mkdtempSync(path.join(os.tmpdir(),'sel-ncaa-r9-browser-'));
      try {
        const exportPath = path.join(temporary,'status.json');
        await download.saveAs(exportPath);
        assert.equal(fs.readFileSync(exportPath,'utf8'),raw);
        assert.deepEqual(JSON.parse(fs.readFileSync(exportPath,'utf8')),expected);
      } finally { fs.rmSync(temporary,{recursive:true,force:true}); }
      if (process.env.DASHBOARD_SCREENSHOTS) {
        fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});
        await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-r9-${width}.png`),fullPage:true});
      }
      await page.goto(pathToFileURL(path.join(path.dirname(filename),'index.html')).href);
      assert.equal(await page.locator('#b063r9-latest-status').count(),1);
      assert.match(await page.locator('#b063r9-latest-status').innerText(),/one peak reserved core, zero new scientific fits/);
      assert.match(await page.locator('#b063r9-latest-status').innerText(),/No complete current-season or upcoming-game refresh occurred/);
      assert.equal(await page.locator('#b063r9-latest-status a').getAttribute('href'),'b063r9.html');
      assert.equal(await page.locator('main > :first-child').getAttribute('id'),'b063r9-latest-status');
      assert.equal(await page.locator('#b063r1-data, #terminal-data, #b063-data').count(),3);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,
        `retained landing must fit ${width}px`);
      if (process.env.DASHBOARD_SCREENSHOTS) {
        await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-landing-r9-${width}.png`)});
      }
      viewports.push({width,metricRows:14,coverageRows:7,providerRows:4,exactDownload:true,keyboardDetails:true});
    }
    assert.deepEqual(failures,[]);
    assert.deepEqual(external,[]);
    return {viewports,actualOwnerRelease:'B063R8',actualOwnerStatus:'FAILED_PARTIAL_WORK_PRESERVED',
      actualPeakReservedCPUs:1,actualNewOwnerFits:0,actualVerifiedCacheReads:118,actualHeartbeatRows:26,
      completePostCaptureLogClaim:false,retainedMetricLeaders:14,realChromium:true,
      scriptErrors:0,externalRequests:0};
  } finally { await page.close(); }
}

module.exports = {verifyR9};
if (require.main===module) {
  (async()=>{
    const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
    const browser = await chromium.launch({headless:true,
      ...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
    try {
      const filename = path.resolve(__dirname,'../../docs/ncaa/b063r9.html');
      console.log(JSON.stringify({status:'PASS',...await verifyR9(browser,filename)}));
    } finally { await browser.close(); }
  })().catch(error=>{console.error(error);process.exitCode=1;});
}
