'use strict';
// Real desktop/mobile browser assertions for the new V065 public saved-result page.
// No models, source acquisition, training or metric rescoring are executed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const root = path.resolve(__dirname, '..');
const url = pathToFileURL(path.join(root, 'docs/fbs/latest-games-v065.html')).href;
let browser;

(async () => {
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({acceptDownloads: true});
  const page = await context.newPage();
  const errors = [], consoleErrors = [], external = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('request', request => { if (!/^(file|blob|data):/.test(request.url())) external.push(request.url()); });
  let selectorChecks = 0;
  const summary = async (count, present, gaps) => {
    assert.equal(await page.locator('#game-summary').innerText(),
      `${count} of 888 source games shown · ${present} with retained probability · ${gaps} explicit gaps`);
    selectorChecks++;
  };
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 1000});
    await page.goto(url);
    await page.evaluate(async () => { await window.FBS_LATEST_READY; return true; });
    const inventory = await page.evaluate(() => {
      const data = window.FBS_LATEST_V065;
      return {games: data.games.length, finals: data.games.filter(game => game.completed).length,
        timed: data.games.filter(game => game.schedule_status === 'CURRENT_ORIGIN_REFRESH_DUE').length,
        tbd: data.games.filter(game => game.kickoff_utc === null).length,
        originalFuture: data.games.filter(game => !game.completed && game.layers.original.values.p_home !== null).length,
        originalFinal: data.games.filter(game => game.completed && game.layers.original.values.p_home !== null).length,
        promoted: data.champion_status.roles.filter(role => role.selected_model !== null).length};
    });
    assert.deepEqual(inventory, {games: 888, finals: 688, timed: 146, tbd: 54, originalFuture: 145, originalFinal: 3, promoted: 0});
    await summary(146, 145, 1);
    assert.equal(await page.locator('#game-rows tr[data-game]').count(), 30);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `page overflow at ${width}`);
    await page.locator('#next').click();
    assert.equal(await page.locator('#page-status').innerText(), 'Page 2 of 5');
    await page.locator('#previous').click();

    // Keyboard access opens a real modal containing all six layers and 16 provider/target cells.
    await page.locator('#game-rows button[data-detail]').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#game-detail').isVisible(), true);
    assert.equal(await page.locator('#detail-layer-rows tr').count(), 6);
    assert.equal(await page.locator('#detail-provider-rows tr').count(), 16);
    assert.match(await page.locator('#detail-content').innerText(), /None authorized by V064 champion check/);
    assert.match(await page.locator('#detail-content').innerText(), /Kalshi/);
    assert.match(await page.locator('#detail-content').innerText(), /Quote:.*\n.*Acquired:/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#game-detail').isVisible(), false);

    await page.selectOption('#period', 'missing_original');
    await summary(1, 0, 1);
    const gap = page.locator('#game-rows tr[data-game="401858532"]');
    assert.match(await gap.innerText(), /Rutgers at Penn State/);
    for (const target of ['probability', 'margin', 'total']) {
      assert.equal(await gap.locator(`[data-value="${target}"]`).innerText(), '—', `${target} was zero-filled`);
    }
    assert.match(await gap.locator('[data-value="scores"]').innerText(), /^—–—/);
    assert.doesNotMatch(await gap.innerText(), /0\.00%/);
    const [missingDownload] = await Promise.all([page.waitForEvent('download'), page.locator('#download-view').click()]);
    const missingCSV = fs.readFileSync(await missingDownload.path(), 'utf8');
    assert.equal(missingCSV.split('\r\n').length, 2);
    assert.match(missingCSV, /401858532/);
    assert.match(missingCSV, /"","","","",""/);

    for (const [period, count, present] of [
      ['refresh_gap', 146, 145], ['completed_original', 3, 3], ['restored', 26, 26],
      ['updated', 14, 14], ['all', 888, 148], ['final', 688, 3], ['tbd', 54, 0], ['pending', 0, 0]
    ]) {
      await page.selectOption('#period', period);
      await summary(count, present, count - present);
    }
    await page.selectOption('#period', 'all');
    for (const [layer, present] of [['original', 148], ['retained_v061', 148], ['calibrated', 122],
      ['mixture_global', 114], ['mixture_gated', 114], ['replay', 790]]) {
      await page.selectOption('#layer', layer);
      await summary(888, present, 888 - present);
    }
    await page.selectOption('#period', 'upcoming');
    await page.selectOption('#layer', 'original');
    await page.selectOption('#coverage', 'with');
    await summary(145, 145, 0);
    const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#download-view').click()]);
    const csv = fs.readFileSync(await download.path(), 'utf8');
    assert.equal(csv.split('\r\n').length, 146);
    assert.match(csv, /GENUINELY_FUTURE_ISSUED_ROLLING/);
    assert.match(csv, /CURRENT_ORIGIN_REFRESH_BLOCKED/);
    await page.selectOption('#coverage', 'without');
    await summary(1, 0, 1);
    await page.selectOption('#coverage', 'all');
    await page.locator('#search').fill('no-such-fixture-065');
    await summary(0, 0, 0);
    assert.equal(await page.locator('#download-view').isDisabled(), true);
    await page.locator('#search').fill('401858532');
    await summary(1, 0, 1);
    await page.locator('#search').fill('');
    await summary(146, 145, 1);

    assert.equal(await page.locator('#champion-rows tr').count(), 9);
    assert.equal(await page.locator('#champion-rows td.gap').allTextContents().then(values => values.filter(value => value === 'No authorized rolling champion').length), 9);
    assert.equal(await page.locator('#current-metric-rows tr').count(), 7);
    assert.equal(await page.locator('#leader-rows tr').count(), 49);
    assert.equal(await page.locator('#new-research-rows tr').count(), 14);
    assert.equal(await page.locator('#native-monitor-rows tr').count(), 4);
    assert.match(await page.locator('#current-metrics').innerText(), /not an original-issued scorecard/);
    assert.match(await page.locator('#current-metrics').innerText(), /07:24:15 UTC/);
    assert.match(await page.locator('#current-metrics').innerText(), /19:38:28 UTC/);
    assert.match(await page.locator('#native-monitor').innerText(), /387 completed games outside/);
    assert.match(await page.locator('#new-research').innerText(), /All 84 primary comparisons/);
    assert.match(await page.locator('#champions').innerText(), /authorized zero rolling champions/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `page overflow after interaction at ${width}`);
    if (process.env.FBS_SCREENSHOTS) {
      fs.mkdirSync(process.env.FBS_SCREENSHOTS, {recursive: true});
      await page.screenshot({path: path.join(process.env.FBS_SCREENSHOTS, `fbs-latest-v065-${width}.png`), fullPage: true});
    }
  }
  const fallbackContext = await browser.newContext({javaScriptEnabled: false});
  const fallback = await fallbackContext.newPage();
  await fallback.goto(url);
  assert.match(await fallback.locator('noscript').innerText(), /all 888 games/);
  assert.match(await fallback.locator('#champions').innerText(), /V064 reached the champion stage and authorized zero/);
  await fallbackContext.close();
  assert.deepEqual(errors, []);
  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(external, []);
  await context.close();
  console.log(JSON.stringify({status: 'PASS', viewports: [1440, 390], selectorChecks, gameDenominator: 888,
    completedGames: 688, timedFutureGames: 146, unresolvedKickoffs: 54, selectedOriginalsFuture: 145,
    selectedOriginalsFinal: 3, currentRefreshGaps: 146, originalTimedGap: 1, restoredOriginalGames: 26,
    recoveredNewerOriginalGames: 14, forecastLayers: 6, currentMetricRows: 7, historicalLeaderRows: 49,
    originalMissingValuesRemainBlank: true, keyboardDialog: true, providerTargetDetailRows: 16,
    noScriptFallback: true, scriptErrors: 0, consoleErrors: 0, externalRequests: 0}));
})().catch(error => { console.error(error); process.exitCode = 1; })
  .finally(async () => { if (browser) await browser.close(); });
