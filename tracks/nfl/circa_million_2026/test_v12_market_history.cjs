'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const releaseDirectory = path.join(__dirname, 'market_history');
const publicURL = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/market-history/';
const horizonCSV = 'N124_V12_HORIZON_COVERAGE.csv';
const sampleCSV = 'N124_V12_OTHER_BOOKS_RAW_SAMPLE.csv';
const checkpoints = ['72h', '24h', '6h', '2h', '60m', '30m', '15m', '5m', '1m'].map(x => 't_minus_' + x);

// These two public files contain only identifiers, integer counts and unquoted product keys.
function readCoverage() {
  const csv = fs.readFileSync(path.join(releaseDirectory, horizonCSV), 'utf8').trim();
  assert.ok(!csv.includes('"'), 'Review the parser if the public schema adds quoted fields');
  const [header, ...lines] = csv.split(/\r?\n/);
  const columns = header.split(',');
  for (const name of ['season', 'venue', 'product', 'games', ...checkpoints]) assert.ok(columns.includes(name), name);
  return lines.map(line => {
    const fields = line.split(',');
    assert.equal(fields.length, columns.length);
    return Object.fromEntries(columns.map((name, i) => [name, fields[i]]));
  });
}

async function checkLadder(page, expected) {
  const key = [expected.season, expected.venue, expected.product].join(' / ');
  for (const field of ['season', 'venue', 'product']) {
    if (await page.locator('#' + field).inputValue() !== expected[field]) {
      await page.selectOption('#' + field, expected[field]);
    }
  }
  const rows = await page.locator('#ladder tbody tr[data-field]').evaluateAll(nodes =>
    nodes.map(node => ({
      field: node.dataset.field,
      count: node.dataset.count,
      text: node.innerText,
    }))
  );
  for (const field of checkpoints) {
    const matches = rows.filter(row => row.field === field);
    assert.equal(matches.length, 1, key + ' · ' + field);
    assert.equal(matches[0].count, expected[field], key + ' · ' + field);
    assert.match(matches[0].text, new RegExp('(?:^|[^0-9])' + expected[field] + '(?:[^0-9]|$)'), key + ' visible ' + field);
  }
  const strict = rows.find(row => row.field === 't_minus_1m_native_age_60s');
  if (strict) assert.equal(strict.count, expected.t_minus_1m_native_age_60s, key + ' · 60s native age');
}

async function checkSurface(browser, url, width, expected) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  try {
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (url === publicURL) assert.equal(response.status(), 200);
    await page.locator('#ladder tbody tr[data-field]').first().waitFor({ timeout: 30000 });
    assert.match(await page.title(), /Circa Million Picks & Performance Dashboard/i);
    assert.deepEqual(await page.locator('#season option').evaluateAll(nodes => nodes.map(n => n.value).sort()), ['2024', '2025', '2026']);
    for (const id of ['season', 'venue', 'product']) {
      assert.ok(await page.locator('#' + id).evaluate(n => n.labels.length > 0 || n.hasAttribute('aria-label') || n.hasAttribute('aria-labelledby')), id + ' accessible name');
    }
    const summary = page.locator('#result-summary');
    assert.ok(await summary.isVisible());
    assert.ok(await summary.evaluate(n => n.getAttribute('role') === 'status' || ['polite','assertive'].includes(n.getAttribute('aria-live'))));
    const checkpointScope = await page.locator('#checkpoints').innerText();
    assert.match(checkpointScope, /native quote/i);
    assert.match(checkpointScope, /five minutes|5 minutes/i);
    const broadSourceScope = await page.locator('#books').innerText();
    assert.match(broadSourceScope, /43 source responses/i);
    assert.match(broadSourceScope, /11 bookmakers/i);
    for (const name of [horizonCSV, sampleCSV]) {
      assert.ok(await page.locator('a[href$="' + name + '"]').count() > 0, 'source download ' + name);
    }
    for (const row of expected) await checkLadder(page, row);
    assert.ok((await summary.innerText()).trim(), 'status text after filters');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'outer viewport overflow');
    assert.deepEqual(errors, []);
    console.log(width + 'px ' + (url === publicURL ? 'signed-out public' : 'repository file') + ' verified ' + expected.length + ' season/venue/product combinations');
  } finally {
    await context.close();
  }
}

async function main() {
  const expected = readCoverage();
  assert.equal(expected.length, 42);
  assert.equal(new Set(expected.map(r => [r.season, r.venue, r.product].join('/'))).size, expected.length);
  const browser = await chromium.launch();
  try {
    for (const url of [pathToFileURL(path.join(releaseDirectory, 'index.html')).href, publicURL]) {
      for (const width of [390, 1280]) await checkSurface(browser, url, width, expected);
    }
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
