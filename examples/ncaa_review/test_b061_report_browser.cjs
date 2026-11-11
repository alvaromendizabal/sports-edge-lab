'use strict';

// Hosted CI only. This checks the exact self-contained public artifact, without
// provider calls, model fitting, cloud access or private notebook execution.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');

const htmlPath = path.join(__dirname, 'B061_EVIDENCE_REPORT.html');
const integrityPath = path.join(__dirname, 'B061_EVIDENCE_REPORT_integrity.json');
const screenshotRoot = process.env.DASHBOARD_SCREENSHOTS || path.join(process.cwd(), 'test-results');
const htmlBytes = fs.readFileSync(htmlPath);
const integrity = JSON.parse(fs.readFileSync(integrityPath, 'utf8'));
const digest = crypto.createHash('sha256').update(htmlBytes).digest('hex');
assert.equal(digest, integrity.artifact.sha256, 'Browser test must inspect the exact integrity-pinned public HTML');
assert.equal(htmlBytes.length, integrity.artifact.bytes);
fs.mkdirSync(screenshotRoot, {recursive: true});

const predictionFields = [
  'selected_original_home_win_probability', 'selected_original_margin', 'selected_original_total',
  'selected_issued_home_win_probability', 'selected_issued_margin', 'selected_issued_total',
];

async function awaitReady(page) {
  await page.waitForFunction(() => {
    const charts = Array.from(document.querySelectorAll('.plotly-graph-div'));
    return charts.length === 4 && charts.every(chart => chart._fullLayout && chart.querySelector('.main-svg') && chart.getBoundingClientRect().width > 0)
      && document.getElementById('game-explorer')?.dataset.ready === 'true';
  }, null, {timeout: 20000});
  await page.evaluate(() => document.fonts.ready);
}

async function dataset(page) {
  return page.locator('#game-explorer').evaluate(element => ({...element.dataset}));
}

async function expectedPayload(page) {
  return page.evaluate(() => {
    const data = JSON.parse(document.getElementById('evidence-data').textContent);
    const rows = data.public_games.records;
    const original = ['selected_original_home_win_probability', 'selected_original_margin', 'selected_original_total'];
    const issued = ['selected_issued_home_win_probability', 'selected_issued_margin', 'selected_issued_total'];
    const futures = rows.filter(row => row.original_replay_prediction_status === 'PRIVATE_UNISSUED_FUTURE_PREVIEW_NOT_PUBLISHED');
    return {
      scienceStatus: data.science_refresh.status,
      records: rows.length,
      replay: rows.filter(row => original.every(key => row[key] !== null && row[key] !== undefined)).length,
      issued: rows.filter(row => issued.every(key => row[key] !== null && row[key] !== undefined)).length,
      futurePreviews: futures.length,
      futureValues: futures.filter(row => [...original, ...issued].some(key => row[key] !== null && row[key] !== undefined)).length,
      invalidReplay: rows.filter(row => original.some(key => row[key] !== null && row[key] !== undefined) &&
        (row.completed !== true || row.original_replay_prediction_status !== 'EXPOSED_RETROSPECTIVE_RECONSTRUCTION_NOT_ORIGINAL_ISSUE')).length,
      invalidIssue: rows.filter(row => issued.some(key => row[key] !== null && row[key] !== undefined) &&
        row.forecast_status !== 'PRESERVED_ORIGINAL_ISSUE_NO_NEW_CREDIT').length,
      men: rows.filter(row => row.league === 'ncaam').length,
      women: rows.filter(row => row.league === 'ncaaw').length,
      completed: rows.filter(row => row.completed === true).length,
      uniqueSearchID: rows.find(row => row.selected_issued_home_win_probability !== null && row.selected_issued_home_win_probability !== undefined).event_id,
      externalAssets: Array.from(document.querySelectorAll('script[src],link[rel="stylesheet"]')).map(element => element.src || element.href),
      rawData: document.getElementById('evidence-data').textContent,
    };
  });
}

(async () => {
  let browser;
  const errors = [], externalRequests = [], screenshots = [];
  const began = Date.now();
  try {
    browser = await chromium.launch({headless: true});
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
    await context.setOffline(true);
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('request', request => { if (/^https?:/i.test(request.url())) externalRequests.push(request.url()); });
    await page.goto(pathToFileURL(htmlPath).href, {waitUntil: 'load', timeout: 30000});
    await awaitReady(page);
    const expected = await expectedPayload(page);
    assert.equal(expected.scienceStatus, 'AUTHENTICATED_SAVED_B003_OUTPUTS_REEVALUATED');
    assert.equal(expected.records, 3457);
    assert.equal(expected.replay, 814);
    assert.equal(expected.issued, 30);
    assert.equal(expected.futurePreviews, 1139);
    assert.equal(expected.futureValues, 0);
    assert.equal(expected.invalidReplay, 0);
    assert.equal(expected.invalidIssue, 0);
    assert.deepEqual(expected.externalAssets, []);
    for (const forbidden of ['s3://', 'arn:aws:', 'projects/ncaa_basketball/', 'errors_and_interactions', 'lagged_errors', 'legacy_all123', 'march_transfer_', 'B032_RETRAINED_', 'B031_hgb', '/workspace/']) {
      assert.ok(!expected.rawData.includes(forbidden), 'Public payload contains a prohibited private identifier: ' + forbidden);
    }
    delete expected.rawData;
    assert.equal((await dataset(page)).filteredRecords, String(expected.records));
    assert.equal(await page.locator('#game-ledger-body tr[data-game-id]').count(), 50);
    for (const field of [...predictionFields, 'original_replay_prediction_status', 'forecast_status', 'source_binding_status']) {
      assert.equal(await page.locator(`#game-ledger-table th[data-field="${field}"]`).count(), 1);
    }

    // Paging traverses the actual embedded census instead of a truncated view.
    await page.selectOption('#game-page-size', '25');
    const firstIDs = await page.locator('#game-ledger-body tr[data-game-id]').evaluateAll(rows => rows.map(row => row.dataset.gameId));
    await page.click('#game-next');
    const secondIDs = await page.locator('#game-ledger-body tr[data-game-id]').evaluateAll(rows => rows.map(row => row.dataset.gameId));
    assert.equal((await dataset(page)).page, '2');
    assert.equal(firstIDs.length, 25); assert.equal(secondIDs.length, 25);
    assert.ok(firstIDs.every(id => !secondIDs.includes(id)));
    await page.click('#game-prev');
    assert.deepEqual(await page.locator('#game-ledger-body tr[data-game-id]').evaluateAll(rows => rows.map(row => row.dataset.gameId)), firstIDs);

    for (const [value, count] of [['ncaam', expected.men], ['ncaaw', expected.women]]) {
      await page.selectOption('#game-league', value);
      assert.equal((await dataset(page)).filteredRecords, String(count));
      assert.equal((await dataset(page)).page, '1');
    }
    await page.click('#game-reset');
    for (const [value, count] of [['issued', expected.issued], ['replay', expected.replay], ['preview', expected.futurePreviews]]) {
      await page.selectOption('#game-evidence', value);
      assert.equal((await dataset(page)).filteredRecords, String(count));
      if (value === 'preview') {
        for (const field of predictionFields) {
          assert.equal(await page.locator(`#game-ledger-body td[data-field="${field}"][data-empty="false"]`).count(), 0);
          assert.ok((await page.locator(`#game-ledger-body td[data-field="${field}"]`).allTextContents()).every(text => text === '\u2014'));
        }
      }
    }
    await page.click('#game-reset');
    await page.selectOption('#game-completed', 'completed');
    assert.equal((await dataset(page)).filteredRecords, String(expected.completed));
    await page.selectOption('#game-completed', 'pending');
    assert.equal((await dataset(page)).filteredRecords, String(expected.records - expected.completed));
    await page.click('#game-reset');
    await page.fill('#game-search', String(expected.uniqueSearchID));
    assert.equal((await dataset(page)).filteredRecords, '1');
    assert.equal(await page.locator('#game-ledger-body tr[data-game-id]').getAttribute('data-game-id'), String(expected.uniqueSearchID));
    await page.fill('#game-search', '<script>not a team</script>');
    assert.equal((await dataset(page)).filteredRecords, '0');
    assert.equal(await page.locator('#game-ledger-body').innerText(), 'No records match these filters.');
    await page.click('#game-reset');

    // Downloaded data contains the same full census and does not add forecasts.
    const [download] = await Promise.all([page.waitForEvent('download'), page.click('#download-evidence')]);
    assert.equal(download.suggestedFilename(), 'NCAA_B061_PUBLIC_EVIDENCE_DATA.json');
    const downloaded = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
    assert.equal(downloaded.public_games.records.length, expected.records);
    assert.equal(downloaded.future_unissued_forecasts_published, 0);

    async function capture(name, locator) {
      const filename = 'ncaa-b061-' + name + '.png';
      const target = path.join(screenshotRoot, filename);
      if (locator) await locator.screenshot({path: target});
      else await page.screenshot({path: target, fullPage: false});
      screenshots.push(filename);
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await capture('report-desktop');
    for (let index = 0; index < 4; index++) await capture('report-chart-' + (index + 1), page.locator('.chart').nth(index));
    await page.locator('#game-explorer').evaluate(element => element.scrollIntoView({block: 'start'}));
    await capture('report-games-desktop');

    // Reopen the saved bytes offline and exercise responsive layout, separately
    // from the private in-process notebook's structural validation.
    await page.setViewportSize({width: 390, height: 844});
    await page.reload({waitUntil: 'load', timeout: 30000});
    await awaitReady(page);
    await page.waitForFunction(() => document.documentElement.scrollWidth <= window.innerWidth + 2);
    assert.equal((await dataset(page)).filteredRecords, String(expected.records));
    assert.equal(await page.locator('.plotly-graph-div').count(), 4);
    await page.evaluate(() => window.scrollTo(0, 0));
    await capture('report-mobile');
    await page.selectOption('#game-evidence', 'issued');
    assert.equal((await dataset(page)).filteredRecords, String(expected.issued));
    await page.locator('#game-explorer').evaluate(element => element.scrollIntoView({block: 'start'}));
    await capture('report-games-mobile');
    const fonts = await page.evaluate(() => ({status: document.fonts.status, bodyFamily: getComputedStyle(document.body).fontFamily}));
    assert.equal(fonts.status, 'loaded');
    assert.ok(fonts.bodyFamily.includes('sans-serif'));
    assert.deepEqual(externalRequests, [], 'Self-contained reopening must not request network assets');
    assert.deepEqual(errors, [], 'Browser execution must not emit JavaScript errors');
    const receipt = {
      schema: 'sel.ncaa.b061.hosted_public_report_browser.v1',
      status: 'PASS', completed_at_utc: new Date().toISOString(),
      artifact_sha256: digest, artifact_bytes: htmlBytes.length,
      git_commit: process.env.GITHUB_SHA || null,
      offline_reopen: true, charts_rendered: 4, javascript_errors: errors,
      external_requests: externalRequests, census: expected, screenshots,
      responsive_widths: [1440, 390], fonts,
      elapsed_seconds: (Date.now() - began) / 1000,
      private_notebook_visual_validation_implied: false,
      new_model_fits: 0, new_forecast_issues: 0, model_promotions: 0,
    };
    fs.writeFileSync(path.join(screenshotRoot, 'ncaa-b061-report-browser-validation.json'), JSON.stringify(receipt, null, 2) + '\n');
    console.log(JSON.stringify(receipt, null, 2));
  } finally {
    if (browser) await browser.close();
  }
})().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
