'use strict';
// Run against a served public FBS export; uses only the browser's local page.
const assert = require('node:assert/strict');

async function actualOwnerCases(page, baseUrl, screenshotDirectory) {
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  for (const viewport of [{width: 1440, height: 960}, {width: 390, height: 844}]) {
    await page.setViewportSize(viewport);
    await page.goto(baseUrl + '/current.html');
    await page.locator('#game-rows tr').first().waitFor();
    await page.locator('#actual-owner-v055-title').waitFor();
    assert.match(await page.locator('#actual-owner-v055').innerText(), /unknown \(null\)/);
    assert.match(await page.locator('#actual-owner-v055').innerText(), /33,336/);
    assert.match(await page.locator('#actual-owner-v055').innerText(), /5,822/);
    assert.match(await page.locator('#prepared-v056').innerText(), /No V056 owner results claimed/);
    assert.match(await page.locator('#game-summary').innerText(), /^67 source games/);
    assert.equal(await page.evaluate(() => window.FBS_ACTUAL_OWNER_V055.execution.new_genuine_forecasts), null);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    await page.locator('#layer').selectOption('mixture_gated');
    assert.match(await page.locator('#game-summary').innerText(), /67 source games/);
    await page.locator('#layer').selectOption('original');
    await page.locator('#actual-owner-v055').scrollIntoViewIfNeeded();
    if (screenshotDirectory) await page.screenshot({path: screenshotDirectory + '/v056-' + viewport.width + '.png'});
  }
  assert.deepEqual(errors, []);
}

module.exports = {actualOwnerCases};
