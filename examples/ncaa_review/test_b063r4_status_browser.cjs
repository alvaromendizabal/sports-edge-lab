// Latest partial owner status; called from the established NCAA Chromium job.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
async function verifyR4(browser, filename) {
  const page = await browser.newPage({ acceptDownloads: true });
  const failures = [], external = [], viewports = [];
  const expected = JSON.parse(fs.readFileSync(path.join(path.dirname(filename), 'data/B063R4_PUBLIC_STATUS.json'), 'utf8'));
  page.on('pageerror', error => failures.push(error.message));
  page.on('request', request => { if (!/^(file|data|blob):/.test(request.url())) external.push(request.url()); });
  try {
    for (const width of [1440,390]) {
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(filename).href);
      assert.deepEqual(JSON.parse(await page.locator('#b063r4-data').textContent()), expected);
      assert.deepEqual(await page.locator('#r4-cards strong').allTextContents(), ['22','167 / 248','2.93 / 12','Pending']);
      assert.match(await page.locator('#r4-scope').innerText(),/zero new scientific fits/);
      assert.match(await page.locator('#r4-scope').innerText(),/November 12, 2026 at 23:34:23 UTC/);
      assert.equal(await page.locator('#r4-repairs tbody tr').count(), 6);
      assert.equal(await page.locator('#r4-remaining ol li').count(),4);
      await page.locator('#r4-engineering summary').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('#r4-engineering').getAttribute('open'),'');
      assert.match(await page.locator('#r4-engineering').innerText(),/38 runtime.*47-test/s);
      assert.match(await page.locator('#r4-engineering').innerText(),/10.0006 seconds and 9.9998 seconds/);
      const downloadPromise=page.waitForEvent('download');await page.locator('#r4-download').click();
      const download=await downloadPromise;
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),expected);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`R4 ${width}px overflow`);
      if (process.env.DASHBOARD_SCREENSHOTS) {
        fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});
        await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-b063r4-status-${width}.png`),fullPage:true});
      }
      await page.goto(pathToFileURL(path.join(path.dirname(filename),'index.html')).href);
      assert.equal(await page.locator('#b063r4-latest-status').count(),1);
      assert.match(await page.locator('#b063r4-latest-status').innerText(),/22 prior target fits recovered/);
      assert.match(await page.locator('#b063r4-latest-status').innerText(),/Twelve-core scientific acceptance remains unproven/);
      assert.equal(await page.locator('#b063r2-latest-evidence').count(),1);
      assert.equal(await page.locator('#b063r1-recovery').count(),1);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Landing ${width}px overflow`);
      viewports.push({width,downloadAndKeyboardAndPreservation:'PASS'});
    }
    assert.deepEqual(failures,[]);assert.deepEqual(external,[]);
    return {viewports,authenticatedPriorTargetFits:22,verifiedR4Owner:false,newPreparationFits:0,realChromium:true};
  } finally { await page.close(); }
}
module.exports={verifyR4};
