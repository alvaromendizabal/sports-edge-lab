// Real browser verification: actual wait, preserved leaders and exact offline export.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
async function verifyR8(browser,filename){
  const page=await browser.newPage({acceptDownloads:true});
  const failures=[],external=[],viewports=[];
  const expected=JSON.parse(fs.readFileSync(path.join(path.dirname(filename),'data/B063R8_PUBLIC_STATUS.json'),'utf8'));
  page.on('pageerror',error=>failures.push(error.message));
  page.on('request',request=>{if(!/^(file|data|blob):/.test(request.url()))external.push(request.url());});
  try{
    for(const width of [1440,390]){
      await page.setViewportSize({width,height:1000});await page.goto(pathToFileURL(filename).href);
      assert.deepEqual(JSON.parse(await page.locator('#b063r8-data').textContent()),expected);
      assert.deepEqual(await page.locator('#r8-cards strong').allTextContents(),['118','0','10.006s','R8']);
      assert.match(await page.locator('#r8-scope').innerText(),/sent no new signals/);
      assert.match(await page.locator('#r8-admission').innerText(),/45.7175–46.9802/);
      assert.match(await page.locator('#r8-admission').innerText(),/zero CPUs/);
      assert.match(await page.locator('#r8-logging').innerText(),/10.005856 seconds/);
      assert.match(await page.locator('#r8-logging').innerText(),/Events after capture remain external/);
      assert.equal(await page.locator('#r8-leaders tbody tr').count(),14);
      const renderedRows=await page.locator('#r8-leaders tbody tr').allInnerTexts();
      assert.equal(renderedRows.filter(x=>x.startsWith('Men')).length,7);
      assert.equal(renderedRows.filter(x=>x.startsWith('Women')).length,7);
      for(const row of expected.preserved_science.current_observed_replay_leaders){
        assert(renderedRows.some(text=>text.includes(row.public_model_ids[0])&&text.includes(row.value.toFixed(6))));
      }
      assert.match(await page.locator('#r8-preservation').innerText(),/retrospective reconstructions/);
      await page.locator('#r8-clocks summary').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r8-clocks').getAttribute('open'),'');
      assert.match(await page.locator('#r8-clocks').innerText(),/Dollar cost remains unavailable/);
      await page.locator('#r8-engineering summary').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r8-engineering').getAttribute('open'),'');
      assert.match(await page.locator('#r8-engineering').innerText(),/zero new sports-fit credit/);
      if(expected.prepared_continuation.source_sha256)assert.equal(await page.locator('#r8-source').innerText(),expected.prepared_continuation.source_sha256);
      const pending=page.waitForEvent('download');await page.locator('#r8-download').click();const download=await pending;
      assert.equal(download.suggestedFilename(),'B063R8_PUBLIC_STATUS.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),expected);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`R8 ${width}px overflow`);
      if(process.env.DASHBOARD_SCREENSHOTS){fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-b063r8-status-${width}.png`),fullPage:true});}
      await page.goto(pathToFileURL(path.join(path.dirname(filename),'index.html')).href);
      for(const id of ['b063r8-latest-status','b063r7-latest-status','b063r6-latest-status','b063r5-latest-status','b063r4-latest-status','b063r2-latest-evidence','b063r1-recovery'])assert.equal(await page.locator('#'+id).count(),1);
      assert.match(await page.locator('#b063r8-latest-status').innerText(),/zero new scientific fits/);
      assert.match(await page.locator('#b063r8-latest-status').innerText(),/15 heartbeats/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Landing ${width}px overflow`);
      viewports.push({width,downloadAndKeyboardAndPreservation:'PASS',retainedMetricRows:14});
    }
    assert.deepEqual(failures,[]);assert.deepEqual(external,[]);
    return {viewports,latestOwnerRelease:'B063R7',latestOwnerStatus:'RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED',
      actualNewOwnerFits:0,admissionDecisions:118,actualHeartbeatRows:15,
      completePostCaptureLogClaim:false,retainedMetricLeaders:14,realChromium:true};
  }finally{await page.close();}
}
module.exports={verifyR8};
