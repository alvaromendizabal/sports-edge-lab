'use strict';

// Hosted CI reopens the exact reconstructed public artifacts. It neither runs
// notebook cells nor refreshes the source evidence. Install Chromium with the
// same Playwright package referenced by PLAYWRIGHT_MODULE_DIR before this test.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {pathToFileURL} = require('url');

const reportDir = path.resolve(process.env.B062_REPORT_DIR || __dirname);
const artifactDir = path.resolve(process.env.DASHBOARD_SCREENSHOTS ||
  path.join(__dirname, 'browser-artifacts', 'b062'));
const htmlPath = path.join(reportDir, 'B062_EVIDENCE_REPORT.html');
const notebookPath = path.join(reportDir, 'B062_EVIDENCE_REPORT.ipynb');
const integrityPath = path.join(reportDir, 'B062_REPORT_INTEGRITY.json');
const receiptPath = path.join(artifactDir, 'B062_REPORT_BROWSER_RECEIPT.json');
const visualLines = [];
const receipt = {
  schema: 'sel.ncaa.b062.hosted_report_render.v1',
  started_at: new Date().toISOString(),
  status: 'RUNNING',
  commit_sha: process.env.GITHUB_SHA || null,
  workflow_run_id: process.env.GITHUB_RUN_ID || null,
  source_evidence_refreshed: false,
  notebook_code_reexecuted: false,
  new_model_fits: 0,
  network_requests: [],
  errors: [],
  checks: [],
  screenshots: [],
};

function pinBytes(body) {
  return {bytes: body.length, sha256: crypto.createHash('sha256').update(body).digest('hex')};
}

function pinFile(file) {
  return {file: path.basename(file), ...pinBytes(fs.readFileSync(file))};
}

function requirePin(actual, expected, label) {
  if (!expected || actual.bytes !== expected.bytes || actual.sha256 !== expected.sha256) {
    throw new Error(label + ' differs from its committed byte count or SHA-256');
  }
}

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

async function isolatedContext(browser, viewport, label) {
  const context = await browser.newContext({viewport, offline: true, serviceWorkers: 'block'});
  await context.route('**/*', route => {
    const url = route.request().url();
    if (/^(?:https?|wss?):/i.test(url)) {
      receipt.network_requests.push({page: label, url});
      return route.abort();
    }
    return route.continue();
  });
  context.on('page', page => {
    page.on('pageerror', error => receipt.errors.push({page: label, message: error.message}));
    page.on('websocket', socket => receipt.network_requests.push({page: label, url: socket.url()}));
  });
  return context;
}

async function waitForPlots(page, requireInventory) {
  await page.waitForFunction(inventory => {
    const plots = [...document.querySelectorAll('.plotly-graph-div')];
    return plots.length === 4 && plots.every(node => node._fullLayout && node.querySelector('svg.main-svg')) &&
      (!inventory || window.B062_INVENTORY_STATE?.total === 3457 && window.B062_INVENTORY_STATE?.shown === 30);
  }, requireInventory, {timeout: 45000});
  await page.evaluate(() => document.fonts.ready);
}

async function saveFirstPage(page, name) {
  await page.evaluate(() => scrollTo(0, 0));
  const png = await page.screenshot({type: 'png', fullPage: false, animations: 'disabled'});
  await saveScreenshot(page, name, png, 'first_viewport');
}

async function saveScreenshot(page, name, png, region) {
  const pngName = name + '.png';
  fs.writeFileSync(path.join(artifactDir, pngName), png);
  // A bounded JPEG derivative makes the public visual recoverable from hosted
  // logs. The full-resolution PNG remains the authoritative screenshot artifact.
  const preview = await page.evaluate(async dataUrl => {
    const source = new Image();
    source.src = dataUrl;
    await source.decode();
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    for (const limit of [960, 800, 640, 480, 320]) {
      const scale = Math.min(1, limit / source.width);
      canvas.width = Math.max(1, Math.round(source.width * scale));
      canvas.height = Math.max(1, Math.round(source.height * scale));
      context.drawImage(source, 0, 0, canvas.width, canvas.height);
      for (const quality of [0.52, 0.42, 0.32, 0.24, 0.18, 0.12]) {
        const data = canvas.toDataURL('image/jpeg', quality).split(',')[1];
        // Leave room for the prefix, JSON keys, and filename within a 32 KiB
        // hosted log line as well as bounding the decoded JPEG to 24 KiB.
        if (Math.ceil(data.length * 3 / 4) <= 24 * 1024 && data.length <= 32 * 1024 - 256) {
          return {data, width: canvas.width, height: canvas.height, quality};
        }
      }
    }
    throw new Error('Could not produce the bounded public JPEG log preview');
  }, 'data:image/png;base64,' + png.toString('base64'));
  const jpegName = name + '_PREVIEW.jpg';
  const jpeg = Buffer.from(preview.data, 'base64');
  const visualLine = {name: jpegName, data: preview.data};
  requireValue(Buffer.byteLength('B062_VISUAL_SCREENSHOT_B64=' + JSON.stringify(visualLine)) <= 32 * 1024,
    'Public visual preview exceeded the hosted log line bound');
  fs.writeFileSync(path.join(artifactDir, jpegName), jpeg);
  receipt.screenshots.push({
    file: pngName, ...pinBytes(png), full_page: false, capture_region: region,
    log_preview: {file: jpegName, ...pinBytes(jpeg), width: preview.width,
      height: preview.height, quality: preview.quality, derived_from: pngName},
  });
  visualLines.push(visualLine);
}

async function checkInventory(page) {
  const first = await page.locator('#game-body tr:first-child').innerText();
  await page.locator('#game-next').click();
  const second = await page.locator('#game-body tr:first-child').innerText();
  requireValue(first !== second, 'Pagination did not change the visible records');
  await page.locator('#game-prev').click();
  requireValue(await page.locator('#game-body tr:first-child').innerText() === first,
    'Previous-page navigation did not restore the first page');

  // Follow the actual Next button across the entire saved source-record census;
  // duplicate identities remain records and are never silently deduplicated.
  const census = await page.evaluate(() => {
    const data = JSON.parse(document.getElementById('evidence-data').textContent);
    const expected = data.games.map(row => (row.league === 'ncaam' ? 'Men' : 'Women') + ' / ' + row.event_id);
    const rendered = [];
    let pages = 0;
    while (true) {
      pages++;
      for (const row of document.querySelectorAll('#game-body tr')) rendered.push(row.firstChild.textContent);
      const next = document.getElementById('game-next');
      if (next.disabled) break;
      if (pages > Math.ceil(expected.length / 30)) throw new Error('Inventory Next button did not stop');
      next.click();
    }
    const matched = rendered.length === expected.length && rendered.every((value, index) => value === expected[index]);
    return {total: expected.length, rendered_records: rendered.length, pages,
      order_and_identity_match: matched, last_page_shown: window.B062_INVENTORY_STATE.shown};
  });
  requireValue(census.total === 3457 && census.rendered_records === 3457 &&
    census.pages === 116 && census.last_page_shown === 7 && census.order_and_identity_match,
  'Full inventory pagination omitted or reordered saved records: ' + JSON.stringify(census));
  receipt.checks.push({name: 'all_saved_inventory_records_paginated', status: 'PASSED', ...census});

  const leagueCounts = {};
  for (const [league, label] of [['ncaaw', 'Women /'], ['ncaam', 'Men /']]) {
    await page.locator('#game-league').selectOption(league);
    const state = await page.evaluate(({league, label}) => {
      const data = JSON.parse(document.getElementById('evidence-data').textContent);
      const rows = [...document.querySelectorAll('#game-body tr')];
      return {expected: data.games.filter(row => row.league === league).length,
        matching: window.B062_INVENTORY_STATE.matching,
        shown: rows.length, every_row_matches: rows.every(row => row.firstChild.textContent.startsWith(label))};
    }, {league, label});
    requireValue(state.expected > 0 && state.expected === state.matching && state.shown > 0 && state.every_row_matches,
      'League filter failed for ' + league + ': ' + JSON.stringify(state));
    leagueCounts[league] = state.matching;
  }
  await page.locator('#game-search').fill('__definitely_no_ncaa_team__');
  requireValue(await page.locator('#game-body tr').count() === 0, 'No-match search filter failed');
  await page.locator('#game-search').fill('');
  await page.locator('#game-league').selectOption('');

  const predictionCounts = {};
  for (const [selection, expected, column] of [['replay', 814, 4], ['issued', 30, 5]]) {
    await page.locator('#game-prediction').selectOption(selection);
    const state = await page.evaluate(column => {
      const rows = [...document.querySelectorAll('#game-body tr')];
      return {matching: window.B062_INVENTORY_STATE.matching, page: window.B062_INVENTORY_STATE.page,
        shown: rows.length, every_row_has_triplet: rows.every(row => {
          const value = row.children[column]?.textContent || '';
          return !value.includes('Unavailable') && value.split(' / ').length === 3;
        })};
    }, column);
    requireValue(state.matching === expected && state.page === 0 && state.shown === 30 && state.every_row_has_triplet,
      'Saved prediction filter failed for ' + selection + ': ' + JSON.stringify(state));
    predictionCounts[selection] = state.matching;
  }
  await page.locator('#game-prediction').selectOption('');
  const reset = await page.evaluate(() => window.B062_INVENTORY_STATE);
  requireValue(reset.matching === 3457 && reset.page === 0 && reset.shown === 30,
    'Clearing the filters did not restore the complete inventory');
  receipt.checks.push({name: 'pagination_league_search', status: 'PASSED', league_records: leagueCounts});
  receipt.checks.push({name: 'saved_prediction_filters', status: 'PASSED',
    matching_records: predictionCounts, reset_to_all_records: reset.matching});
}

async function main() {
  fs.mkdirSync(artifactDir, {recursive: true});
  let browser;
  try {
    const integrity = JSON.parse(fs.readFileSync(integrityPath, 'utf8'));
    receipt.integrity_pin = pinFile(integrityPath);
    receipt.test_script_pin = pinFile(__filename);
    receipt.html_pin = pinFile(htmlPath);
    receipt.notebook_pin = pinFile(notebookPath);
    requirePin(receipt.html_pin, integrity.outputs?.[path.basename(htmlPath)], 'Reconstructed HTML');
    requirePin(receipt.notebook_pin, integrity.outputs?.[path.basename(notebookPath)], 'Reconstructed saved notebook');
    receipt.saved_evidence_created_at = integrity.saved_evidence_created_at;

    const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
    browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']});
    receipt.browser = {engine: 'chromium', version: browser.version(), executable_selection: 'playwright-installed-default'};
    const context = await isolatedContext(browser, {width: 1440, height: 1040}, 'report');
    const page = await context.newPage();
    await page.goto(pathToFileURL(htmlPath).href, {waitUntil: 'load'});
    await waitForPlots(page, true);
    const desktop = await page.evaluate(() => ({
      plots: document.querySelectorAll('.plotly-graph-div').length,
      visible_svg: document.querySelectorAll('.plotly-graph-div svg.main-svg').length,
      inventory: window.B062_INVENTORY_STATE,
      table_columns: document.querySelector('#game-body tr')?.children.length,
      title: document.querySelector('h1').innerText,
      width: innerWidth, document_width: document.documentElement.scrollWidth,
    }));
    requireValue(desktop.plots === 4 && desktop.inventory.total === 3457 && desktop.inventory.matching === 3457 &&
      desktop.table_columns === 7 && desktop.document_width <= desktop.width,
    'Desktop layout or inventory closure failed: ' + JSON.stringify(desktop));
    receipt.checks.push({name: 'desktop_reopen', status: 'PASSED', ...desktop});
    await saveFirstPage(page, 'B062_REPORT_DESKTOP');

    const predictions = await page.evaluate(() => {
      const data = JSON.parse(document.getElementById('evidence-data').textContent);
      const original = ['selected_original_home_win_probability', 'selected_original_margin', 'selected_original_total'];
      const issued = ['selected_issued_home_win_probability', 'selected_issued_margin', 'selected_issued_total'];
      const fields = [...original, ...issued];
      const complete = names => data.games.filter(row => names.every(field => row[field] != null)).length;
      return {saved_reconciliation_asof: data.prediction_reconciliation_asof,
        source_census_asof: data.census_asof,
        complete_original_triplets: complete(original), complete_issued_triplets: complete(issued),
        unfinished_records: data.games.filter(row => !row.completed).length,
        unfinished_records_with_any_forecast_value: data.games.filter(row => !row.completed && fields.some(field => row[field] != null)).length};
    });
    requireValue(typeof predictions.saved_reconciliation_asof === 'string' && predictions.saved_reconciliation_asof.length > 0 &&
      predictions.complete_original_triplets === 814 && predictions.complete_issued_triplets === 30 &&
      predictions.unfinished_records_with_any_forecast_value === 0,
    'Recovered prediction reconciliation or unfinished-game truth failed: ' + JSON.stringify(predictions));
    receipt.checks.push({name: 'saved_prediction_reconciliation', status: 'PASSED', ...predictions,
      new_forecasts_issued: 0, evidence_refreshed: false});
    await checkInventory(page);

    await page.locator('#confidence-loss').scrollIntoViewIfNeeded();
    await saveScreenshot(page, 'B062_REPORT_CONFIDENCE_CHART',
      await page.locator('#confidence-loss').screenshot({type: 'png', animations: 'disabled'}), '#confidence-loss');
    const before = await page.evaluate(() => document.querySelector('#confidence-loss').data.map(trace => trace.visible));
    await page.locator('#confidence-loss .legendtoggle').first().click();
    await page.waitForFunction(prior => JSON.stringify(document.querySelector('#confidence-loss').data.map(trace => trace.visible)) !== prior,
      JSON.stringify(before));
    receipt.checks.push({name: 'plotly_legend_interaction', status: 'PASSED'});

    await page.setViewportSize({width: 390, height: 844});
    await page.goto(pathToFileURL(htmlPath).href, {waitUntil: 'load'});
    await waitForPlots(page, true);
    const mobile = await page.evaluate(() => ({width: innerWidth, document_width: document.documentElement.scrollWidth,
      plots: document.querySelectorAll('.plotly-graph-div').length, records: window.B062_INVENTORY_STATE.total}));
    requireValue(mobile.document_width <= mobile.width + 1, 'Mobile horizontal page overflow: ' + JSON.stringify(mobile));
    await saveFirstPage(page, 'B062_REPORT_MOBILE');
    receipt.checks.push({name: 'mobile_reopen', status: 'PASSED', ...mobile});
    await context.close();

    // Build a fresh page solely from saved text/html outputs. No Python kernel,
    // notebook runner, or cell source is invoked, and no earlier DOM is reused.
    const notebook = JSON.parse(fs.readFileSync(notebookPath, 'utf8'));
    const codeCells = notebook.cells.filter(cell => cell.cell_type === 'code');
    const outputs = codeCells.flatMap(cell => cell.outputs || [])
      .filter(output => output.data && output.data['text/html'])
      .map(output => Array.isArray(output.data['text/html']) ? output.data['text/html'].join('') : output.data['text/html']);
    requireValue(outputs.length > 0, 'Notebook does not contain saved HTML outputs to reopen');
    const savedOutputPath = path.join(artifactDir, 'B062_REOPENED_NOTEBOOK_OUTPUTS.html');
    fs.writeFileSync(savedOutputPath, '<!doctype html><html><head><meta charset="utf-8"></head><body><main>' +
      outputs.join('\n') + '</main></body></html>');
    const notebookContext = await isolatedContext(browser, {width: 1440, height: 1040}, 'saved_notebook_outputs');
    const notebookPage = await notebookContext.newPage();
    await notebookPage.goto(pathToFileURL(savedOutputPath).href, {waitUntil: 'load'});
    await waitForPlots(notebookPage, false);
    receipt.checks.push({name: 'saved_notebook_outputs_reopen', status: 'PASSED',
      plotly_charts_rendered: await notebookPage.locator('.plotly-graph-div').count(),
      saved_html_output_count: outputs.length, saved_code_cell_count: codeCells.length,
      fresh_browser_context: true, fresh_page: true, code_reexecuted: false,
      reopened_output_pin: pinFile(savedOutputPath)});
    await notebookContext.close();

    requirePin(pinFile(htmlPath), receipt.html_pin, 'Rendered HTML after browser verification');
    requirePin(pinFile(notebookPath), receipt.notebook_pin, 'Saved notebook after browser verification');
    receipt.checks.push({name: 'exact_saved_artifacts_unchanged', status: 'PASSED',
      html_pin_matches_committed_integrity: true, notebook_pin_matches_committed_integrity: true});
    requireValue(receipt.errors.length === 0 && receipt.network_requests.length === 0,
      'Unexpected browser errors or attempted external requests');
    receipt.checks.push({name: 'offline_self_contained_render', status: 'PASSED', attempted_external_requests: 0});
    receipt.status = 'PASSED';
  } catch (error) {
    receipt.status = 'FAILED';
    receipt.failure = {name: error.name, message: error.message};
    process.exitCode = 1;
  } finally {
    if (browser) {
      try { await browser.close(); }
      catch (error) {
        receipt.status = 'FAILED';
        receipt.errors.push({page: 'browser_close', message: error.message});
        process.exitCode = 1;
      }
    }
    receipt.completed_at = new Date().toISOString();
    fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
    console.log('B062_HOSTED_REPORT_RENDER=' + JSON.stringify(receipt));
    for (const screenshot of visualLines) console.log('B062_VISUAL_SCREENSHOT_B64=' + JSON.stringify(screenshot));
  }
}

main().catch(error => { console.error(error.stack); process.exitCode = 1; });
