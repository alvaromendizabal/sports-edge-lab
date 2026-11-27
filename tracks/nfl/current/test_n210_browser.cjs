"use strict";
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const root = __dirname;
const data = JSON.parse(fs.readFileSync(path.join(root, 'week-12-field-notes/n210/week-12-picks.json'), 'utf8'));
const output = process.env.NFL_CURRENT_EVIDENCE || path.join(process.env.RUNNER_TEMP || '/tmp', 'nfl-n210-browser');
fs.mkdirSync(output, { recursive: true });
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0]);
  const file = path.resolve(root, '.' + rel + (rel.endsWith('/') ? 'index.html' : ''));
  if (!file.startsWith(root + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, content) => { if (err) { res.writeHead(404); return res.end(); } res.setHeader('Content-Type', file.endsWith('.png') ? 'image/png' : file.endsWith('.json') ? 'application/json' : 'text/html; charset=utf-8'); res.end(content); });
});
(async () => {
  assert.equal(data.games.length, 16);
  assert.equal(new Set(data.games.map(g => g.id)).size, 16);
  assert.equal(data.games.filter(g => g.score).length, 4);
  for (const row of data.champions) assert.equal(row.wins + row.losses + row.pushes, 166);
  const old = JSON.parse(fs.readFileSync(path.join(root, 'week-12-field-notes/n209/week-12-picks.json')));
  for (const game of data.games.filter(g => g.score)) {
    const prior = old.games.find(g => g.id === game.id);
    for (const [role, targets] of Object.entries(game.picks)) for (const [target, pick] of Object.entries(targets)) {
      const original = prior.pregame[role][target];
      assert.equal(pick.side, original.side); assert.equal(pick.line, original.line);
      assert.equal(pick.issued_utc, original.issued_utc);
      assert.equal(pick.probability, Math.round(original.probability * 10000) / 10000);
    }
  }
  assert.doesNotMatch(JSON.stringify(data), /s3:\/\/|\/home\/sagemaker|conditional_cdf|expanded_balanced|private-research/);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const origins = [{ label: 'local', url: `http://127.0.0.1:${server.address().port}/` }];
    if (process.env.NFL_N210_VERIFY_HOSTED === '1') {
      const receipt = JSON.parse(fs.readFileSync(path.join(root, 'publication.json'), 'utf8'));
      assert.match(receipt.status, /^DEPLOYED/);
      origins.push({ label: 'hosted', url: receipt.public_url });
    }
    for (const origin of origins) for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      page.on('pageerror', error => errors.push(error.message));
      await page.clock.install({ time: new Date('2026-11-27T19:00:00Z') });
      await page.goto(new URL('week-12-field-notes/n210/', origin.url).href);
      assert.equal(await page.locator('article[data-game]:visible').count(), 16);
      assert.match(await page.locator('.status').innerText(), /archived observations/);
      await page.getByRole('button', { name: 'Upcoming', exact: true }).click();
      assert.equal(await page.locator('article[data-game]:visible').count(), 12);
      await page.getByRole('button', { name: 'Final', exact: true }).click();
      assert.equal(await page.locator('article[data-game]:visible').count(), 4);
      await page.getByRole('button', { name: 'All games', exact: true }).click();
      await page.getByRole('textbox', { name: 'Search teams' }).fill('DEN');
      assert.equal(await page.locator('article[data-game]:visible').count(), 1);
      assert.match(await page.locator('article[data-game]:visible').innerText(), /DEN -4\.5/);
      await page.locator('article[data-game]:visible summary').click();
      assert.match(await page.locator('article[data-game]:visible').innerText(), /no separate historical validation/);
      await page.getByRole('textbox', { name: 'Search teams' }).fill('');
      assert.equal(await page.locator('#phone img').count(), 4);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: path.join(output, `n210-board-${origin.label}-${width}.png`), fullPage: true });
      await page.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'n210-browser.json'), JSON.stringify({ status: 'PASS', games: 16, originals: 4, saved_n210: 12, viewports: [1440, 390], origins: origins.map(item => item.label), scope: 'Saved issue identity, source rendering, filters, detail expansion and phone-card presence' }, null, 2));
    console.log('PASS N210 ' + origins.map(item => item.label).join(' and ') + ' rendering, saved issue identity, original preservation and desktop/mobile interactions');
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
