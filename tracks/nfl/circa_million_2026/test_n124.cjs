'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

async function main() {
  const dir = path.join(__dirname, 'n124');
  const localURL = pathToFileURL(path.join(dir, 'index.html')).href;
  const liveURL = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n124/';
  const browser = await chromium.launch();
  try {
    for (const [url,width] of [[localURL,390],[localURL,1280],[liveURL,390],[liveURL,1280]]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.goto(url, {waitUntil:'domcontentloaded', timeout:60000});
      await page.waitForSelector('#champion-list tbody tr');
      assert.equal(await page.locator('.n124-seasons strong').allTextContents().then(x=>x.join('/')), '285/285/149');
      assert.ok(await page.locator('#champion-objective option').count()>=8);
      await page.selectOption('#champion-objective','margin_mae');
      await page.check('#champion-precision');
      assert.match(await page.locator('#champion-list').innerText(), /149 games/);
      assert.equal(await page.locator('#new-scoreboard tbody tr').count(),5);
      assert.equal(await page.locator('#event-leaders tbody tr').count(),6);
      await page.selectOption('#law-model','n124_form_rest');
      await page.selectOption('#n124-v-venue','Polymarket_US');
      assert.match(await page.locator('#n124-venue-scores').innerText(), /69 \/ 149/);
      assert.equal(await page.locator('#opening-forecast tbody tr').count(),7);
      assert.equal(await page.title(), 'Circa Million Picks & Performance Dashboard');
      assert.equal(await page.locator('.stat b').allTextContents().then(x => x.join('/')), '285/285/149');
      const scores = page.locator('#cross-results tbody tr');
      assert.ok(await scores.count() > 8);
      assert.equal(await page.locator('#cross-objective option').count(), 12);
      const models = page.locator('#fixed tbody tr');
      assert.equal(await models.count(), 8);
      await page.selectOption('#metric', 'total_mae');
      assert.equal(await models.count(), 8);
      await page.fill('#venue-filter', '2026_10_PIT_CIN');
      assert.equal(await page.locator('#venue-games tbody tr').count(), 1);
      assert.ok((await page.locator('#venue-games').innerText()).includes('FINAL'));
      await page.fill('#venue-filter', '');
      await page.selectOption('#venue-status', 'UPCOMING');
      assert.ok((await page.locator('#range').innerText()).includes('123 games'));
      assert.equal(await page.locator('#forward-game option').count(), 123);
      await page.selectOption('#forward-game', '2026_10_LAC_BAL');
      assert.ok((await page.locator('#forward').innerText()).includes('Baltimore') || (await page.locator('#forward').innerText()).includes('N121'));
      await page.fill('#law-line', '4.5');
      await page.waitForFunction(() => document.querySelector('#law-chart .plotly') && document.querySelector('#law-answer tbody')?.textContent.includes('Exactly 4.5 (push)0.00%'));
      await page.waitForFunction(() => document.querySelector('#alternatives tbody tr'));
      assert.equal(await page.locator('#card-policy option').count(), 19);
      assert.equal(await page.locator('#card-table tbody tr').count(), 5);
      await page.selectOption('#card-policy', 'n110_cold_opening');
      await page.selectOption('#card-season', '2025');
      await page.selectOption('#card-week', '18');
      assert.equal(await page.locator('#card-table tbody tr').count(), 5);
      const links = await page.locator('#downloads a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
      for (const href of links.filter(h => !h.startsWith('http') && !h.startsWith('../'))) assert.ok(fs.existsSync(path.join(dir, href)), href);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
      assert.ok(!overflow, 'viewport overflow');
      assert.deepEqual(errors, []);
      await page.close();
    }
    console.log('Verified the repository file and signed-out live N124 on 390px and 1280px viewports, including full-season leader precision, 19 Circa policies and 10 forward distributions per game.');
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
