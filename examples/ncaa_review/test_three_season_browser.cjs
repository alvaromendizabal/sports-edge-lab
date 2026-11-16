// Invoked by the existing Chromium CI job. No production write or source acquisition.
'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), http = require('node:http');
module.exports = async function testThreeSeasonBrowser(browser) {
  const docs = path.resolve(__dirname, '../../docs/ncaa');
  const unpack = require('node:child_process').spawnSync('python', [path.join(__dirname, 'public_status_transport.py'), 'unpack'], { encoding: 'utf8', timeout: 120000 });
  assert.equal(unpack.status, 0, unpack.stdout + unpack.stderr);
  const data = JSON.parse(fs.readFileSync(path.join(docs, 'population/population_public.json')));
  const manifest = JSON.parse(fs.readFileSync(path.join(docs, 'population/status_manifest.json')));
  const allowed = new Set(['three_seasons.html', 'three_seasons.css', 'three_seasons.js', 'population/population_public.json', 'population/population_context.json', 'population/status_manifest.json', 'population/execution_public.json', ...manifest.parts.map(p => 'population/status/' + p.filename)]);
  const server = http.createServer((request, response) => {
    const name = request.url.split('?')[0].replace(/^\//, '');
    if (!allowed.has(name)) { response.writeHead(404); response.end(); return; }
    const type = name.endsWith('.gz') ? 'application/gzip' : name.endsWith('.json') ? 'application/json' : name.endsWith('.js') ? 'text/javascript' : name.endsWith('.css') ? 'text/css' : 'text/html';
    response.writeHead(200, { 'Content-Type': type }); fs.createReadStream(path.join(docs, name)).pipe(response);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`, receipts = [];
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } }), errors = [];
      page.on('pageerror', error => errors.push(error.message));
      try {
        await page.goto(origin + '/three_seasons.html', { waitUntil: 'load' });
        await page.waitForFunction(() => window.SEL_POPULATION_READY || window.SEL_POPULATION_ERROR, null, { timeout: 60000 });
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_ERROR), undefined);
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_READY.populations), 6);
        assert.equal(await page.locator('#population-rows tr').count(), 6);
        assert.match(await page.locator('#rank-status').innerText(), /No complete, comparable full-population champion/);
        assert.equal(await page.locator('#provider-summary article').count(), 4);
        for (const season of data.seasons) for (const league of ['ncaam', 'ncaaw']) {
          await page.selectOption('#season', String(season.season_end_year)); await page.selectOption('#competition', league);
          assert.equal(await page.locator('#population-rows tr').count(), 1);
          assert((await page.locator('#population-rows').innerText()).includes(season.leagues[league].declared_population_count.toLocaleString('en-US')));
          for (const target of ['win', 'margin', 'total']) {
            await page.selectOption('#target', target);
            const declaredModels = data.model_roster.filter(r => r.league === league);
            assert.match(await page.locator('#coverage-count').innerText(), new RegExp('^' + declaredModels.length.toLocaleString('en-US') + ' model'));
          }
        }
        await page.selectOption('#competition', 'all'); await page.selectOption('#season', 'all'); await page.selectOption('#target', 'win');
        await page.waitForFunction(() => window.SEL_POPULATION_CELLS_READY || window.SEL_POPULATION_CELLS_ERROR, null, { timeout: 90000 });
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_CELLS_ERROR), null);
        const current = data.seasons.find(s => s.season_end_year === 2027).leagues.ncaam;
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_CELLS_READY.records), current.declared_population_count + current.future_or_unresolved_count);
        await page.selectOption('#cell-entity', 'provider:kalshi');
        await page.waitForFunction(() => window.SEL_POPULATION_CELLS_READY && window.SEL_POPULATION_CELLS_READY.entity === 'kalshi', null, { timeout: 90000 });
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_CELLS_ERROR), null);
        await page.fill('#cell-search', '__no_authentic_game_matches__');
        assert.match(await page.locator('#cell-count').innerText(), /^0 matching/);
        assert(await page.locator('#download-cells').isDisabled());
        await page.fill('#cell-search', '');
        const [download] = await Promise.all([page.waitForEvent('download'), page.click('#download-cells')]);
        const exported = JSON.parse(fs.readFileSync(await download.path()));
        assert.equal(exported.row_count, current.declared_population_count + current.future_or_unresolved_count);
        assert(exported.rows.every(row => row.public_entity_id === 'kalshi' && !Object.hasOwn(row, 'prediction') && !Object.hasOwn(row, 'quote')));
        assert.equal(exported.complete_official_population_claimed, false);
        await page.selectOption('#cell-game-status', 'future_or_unresolved');
        assert.match(await page.locator('#cell-count').innerText(), new RegExp('^' + current.future_or_unresolved_count.toLocaleString('en-US') + ' matching'));
        await page.selectOption('#cell-game-status', 'all');
        const dimensions = await page.evaluate(() => ({ documentWidth: document.documentElement.scrollWidth, viewport: innerWidth }));
        assert(dimensions.documentWidth <= dimensions.viewport, JSON.stringify({ width, ...dimensions }));
        assert.deepEqual(errors, []);
        if (process.env.DASHBOARD_SCREENSHOTS) {
          fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS, { recursive: true });
          await page.screenshot({ path: path.join(process.env.DASHBOARD_SCREENSHOTS, `ncaa-three-seasons-source-${width}.png`), fullPage: true });
        }
        receipts.push({ version: 'three-season-population', width, source: true, allSixPopulations: true, allThreeTargets: true, rankSuppression: true, providerProducts: 4, explicitStatusIntegrity: true, filteredDownloadVerified: true, realChromium: true });
      } finally { await page.close(); }
    }
  } finally { await new Promise(resolve => server.close(resolve)); }
  return receipts;
};
