// Actual recovery, one errored fixture, exact offline data and retained history.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
async function verifyR6(browser,filename){
  const page=await browser.newPage({acceptDownloads:true});
  const failures=[],external=[],viewports=[];
  const expected=JSON.parse(fs.readFileSync(path.join(path.dirname(filename),'data/B063R6_PUBLIC_STATUS.json'),'utf8'));
  page.on('pageerror',error=>failures.push(error.message));
  page.on('request',request=>{if(!/^(file|data|blob):/.test(request.url()))external.push(request.url());});
  try{
    for(const width of [1440,390]){
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(filename).href);
      assert.deepEqual(JSON.parse(await page.locator('#b063r6-data').textContent()),expected);
      assert.deepEqual(await page.locator('#r6-cards strong').allTextContents(),['Recovered','1','0','22']);
      const wrapped=await page.locator('#r6-cards strong').evaluateAll(nodes=>nodes.filter(node=>node.getBoundingClientRect().height>parseFloat(getComputedStyle(node).lineHeight)+1).map(node=>node.textContent));
      assert.deepEqual(wrapped,[],`R6 ${width}px status labels must fit one line`);
      assert.match(await page.locator('#r6-scope').innerText(),/No foreign process was signaled/);
      assert.match(await page.locator('#r6-failure').innerText(),/115 of 116 unique cases/);
      assert.match(await page.locator('#r6-runtime').innerText(),/0.691 core equivalents/);
      assert.equal(await page.locator('#r6-remaining ol li').count(),4);
      await page.locator('#r6-clocks summary').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r6-clocks').getAttribute('open'),'');
      assert.match(await page.locator('#r6-clocks').innerText(),/excludes the preceding recovery/);
      await page.locator('#r6-engineering summary').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r6-engineering').getAttribute('open'),'');
      assert.match(await page.locator('#r6-engineering').innerText(),/zero scientific-fit credit/);
      if(expected.prepared_continuation.source_sha256)assert.equal(await page.locator('#r6-source').innerText(),expected.prepared_continuation.source_sha256);
      const pending=page.waitForEvent('download');await page.locator('#r6-download').click();
      const download=await pending;
      assert.equal(download.suggestedFilename(),'B063R6_PUBLIC_STATUS.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),expected);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`R6 ${width}px overflow`);
      if(process.env.DASHBOARD_SCREENSHOTS){
        fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});
        await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-b063r6-status-${width}.png`),fullPage:true});
      }
      await page.goto(pathToFileURL(path.join(path.dirname(filename),'index.html')).href);
      for(const id of ['b063r6-latest-status','b063r5-latest-status','b063r4-latest-status','b063r2-latest-evidence','b063r1-recovery'])assert.equal(await page.locator('#'+id).count(),1);
      assert.match(await page.locator('#b063r6-latest-status').innerText(),/zero new scientific fits/);
      assert.match(await page.locator('#b063r6-latest-status').innerText(),/22 prior target fits and 134 saved objects/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Landing ${width}px overflow`);
      viewports.push({width,downloadAndKeyboardAndPreservation:'PASS'});
    }
    assert.deepEqual(failures,[]);assert.deepEqual(external,[]);
    return {viewports,latestOwnerStatus:'FAILED_PARTIAL_WORK_PRESERVED',oldOwnerRecoveryVerified:true,newOwnerFits:0,preservedPriorTargetFits:22,realChromium:true};
  }finally{await page.close();}
}
module.exports={verifyR6};
