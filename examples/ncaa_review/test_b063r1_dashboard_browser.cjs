// B063R1 public reporting contract: live filters, exact preserved data and mobile fit.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

async function verifyR1(browser, pagePath) {
  const page=await browser.newPage();
  const errors=[],external=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(!/^(file|data|blob):/.test(request.url()))external.push(request.url());});
  const results={viewports:0,filters:0,downloadRows:0,preservedTerminalRows:142,monitorGroups:11};
  try {
    for(const width of [1440,390]) {
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(pagePath).href);
      await page.waitForSelector('#r1-issues-table tbody tr');
      assert.equal(await page.locator('#r1-issues-table tbody tr').count(),15);
      assert.match(await page.locator('#r1-issue-count').innerText(),/^90 selected original rows across 30 games/);
      assert.equal(await page.locator('#r1-monitor-table tbody tr').count(),11);
      assert.equal(await page.locator('#r1-outcome-cards p').count(),8);
      assert.equal(await page.evaluate(()=>JSON.parse(document.getElementById('terminal-data').textContent).issues.length),142);
      assert.equal(await page.evaluate(()=>JSON.parse(document.getElementById('b063r1-data').textContent).actual_owner.science_started),false);
      await page.locator('#r1-league').selectOption('ncaaw');
      await page.locator('#r1-target').selectOption('win');
      assert.match(await page.locator('#r1-issue-count').innerText(),/^26 selected original rows across 26 games/);
      await page.locator('#r1-next').click();
      assert.equal(await page.locator('#r1-issues-table tbody tr').count(),11);
      await page.locator('#r1-search').fill('NO_SUCH_TEAM');
      assert.match(await page.locator('#r1-issues-table tbody').innerText(),/No selected original rows/);
      await page.locator('#r1-search').fill('');
      await page.locator('#r1-league').selectOption('ncaam');
      assert.match(await page.locator('#r1-issue-count').innerText(),/^4 selected original rows across 4 games/);
      const pending=page.waitForEvent('download');await page.locator('#r1-download').click();const download=await pending;
      const file=await download.path();const csv=fs.readFileSync(file,'utf8');assert.equal(csv.trim().split('\n').length,5);
      results.downloadRows+=4;results.filters+=4;
      await page.locator('#r1-league').selectOption('all');await page.locator('#r1-target').selectOption('all');
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'horizontal document overflow');
      if(process.env.DASHBOARD_SCREENSHOTS){fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`b063r1-${width}.png`),fullPage:false});}
      results.viewports++;
    }
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    return {status:'PASS',...results,scriptErrors:0,externalRequests:0};
  } finally {await page.close();}
}
module.exports={verifyR1};

if(require.main===module){
  const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
  (async()=>{const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
    try {console.log(JSON.stringify(await verifyR1(browser,path.resolve(__dirname,'../../docs/ncaa/index.html'))));}
    finally {await browser.close();}
  })().catch(error=>{console.error(error);process.exitCode=1;});
}
