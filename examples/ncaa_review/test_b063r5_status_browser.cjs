// Authenticated failure, offline evidence download and cumulative history.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
async function verifyR5(browser, filename) {
  const page = await browser.newPage({acceptDownloads:true});
  const failures = [], external = [], viewports = [];
  const expected = JSON.parse(fs.readFileSync(path.join(path.dirname(filename), 'data/B063R5_PUBLIC_STATUS.json'), 'utf8'));
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => {if (!/^(file|data|blob):/.test(request.url())) external.push(request.url());});
  try {
    for (const width of [1440,390]) {
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(filename).href);
      assert.deepEqual(JSON.parse(await page.locator('#b063r5-data').textContent()), expected);
      assert.deepEqual(await page.locator('#r5-cards strong').allTextContents(), ['0','22','Failed','Unverified']);
      assert.match(await page.locator('#r5-scope').innerText(), /zero new owner fits/);
      assert.match(await page.locator('#r5-scope').innerText(), /referenced recovery diagnostic was not included/);
      assert.equal(await page.locator('#r5-remaining ol li').count(), 4);
      await page.locator('#r5-clocks summary').focus(); await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r5-clocks').getAttribute('open'), '');
      assert.match(await page.locator('#r5-clocks').innerText(), /filename timestamp, not a verified failure completion time/);
      await page.locator('#r5-engineering summary').focus(); await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r5-engineering').getAttribute('open'), '');
      assert.match(await page.locator('#r5-engineering').innerText(), /zero scientific-fit credit/);
      if (expected.prepared_continuation.source_sha256) assert.equal(await page.locator('#r5-source').innerText(), expected.prepared_continuation.source_sha256);
      const downloadPromise = page.waitForEvent('download'); await page.locator('#r5-download').click();
      const download = await downloadPromise;
      assert.equal(download.suggestedFilename(), 'B063R5_PUBLIC_STATUS.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(), 'utf8')), expected);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1), false, `R5 ${width}px overflow`);
      if (process.env.DASHBOARD_SCREENSHOTS) {
        fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});
        await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-b063r5-status-${width}.png`),fullPage:true});
      }
      await page.goto(pathToFileURL(path.join(path.dirname(filename), 'index.html')).href);
      for (const id of ['b063r5-latest-status','b063r4-latest-status','b063r2-latest-evidence','b063r1-recovery']) assert.equal(await page.locator('#'+id).count(), 1);
      assert.match(await page.locator('#b063r5-latest-status').innerText(), /zero new owner fits/);
      assert.match(await page.locator('#b063r5-latest-status').innerText(), /134 saved content objects/);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1), false, `Landing ${width}px overflow`);
      viewports.push({width,downloadAndKeyboardAndPreservation:'PASS'});
    }
    assert.deepEqual(failures, []); assert.deepEqual(external, []);
    return {viewports,latestOwnerStatus:'PREFLIGHT_FAILED',newOwnerFits:0,preservedPriorTargetFits:22,realChromium:true};
  } finally {await page.close();}
}
module.exports={verifyR5};
