// Invoked by the existing Chromium CI job. No production write or source acquisition.
'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), http = require('node:http');
module.exports = async function testThreeSeasonBrowser(browser) {
  const docs = path.resolve(__dirname, '../../docs/ncaa');
  for (const contract of ['test_validation_weights.cjs','test_r19_comparison.cjs']) {
    const result = require('node:child_process').spawnSync(process.execPath,
      [path.join(__dirname, contract)], {encoding: 'utf8', timeout: 30000});
    assert.equal(result.status, 0, result.stdout + result.stderr); console.log(result.stdout.trim());
  }
  const physical = require('node:child_process').spawnSync('python', ['-m', 'examples.ncaa_review.full_status_integrity_gate'], { cwd: path.resolve(__dirname, '../..'), encoding: 'utf8', timeout: 240000 });
  assert.equal(physical.status, 0, physical.stdout + physical.stderr);
  const physicalReceipt = JSON.parse(physical.stdout);
  assert.equal(physicalReceipt.status, 'PASS');
  console.log(JSON.stringify({ fullStatusIntegrity: physicalReceipt }));
  const data = JSON.parse(fs.readFileSync(path.join(docs, 'population/population_public.json')));
  const oldReassembly = require('node:child_process').spawnSync('python', ['-m', 'examples.ncaa_review.public_status_transport', 'unpack', '--population-directory', path.join(docs, 'population_r17')], { cwd: path.resolve(__dirname, '../..'), encoding: 'utf8', timeout: 60000 });
  assert.equal(oldReassembly.status, 0, oldReassembly.stdout + oldReassembly.stderr);
  const sharedBuild = require('node:child_process').spawnSync('python', ['-m', 'examples.ncaa_review.public_shared_status', '--already-reconstructed'], { cwd: path.resolve(__dirname, '../..'), encoding: 'utf8', timeout: 60000 });
  assert.equal(sharedBuild.status, 0, sharedBuild.stdout + sharedBuild.stderr);
  const sharedManifest = JSON.parse(fs.readFileSync(path.join(docs, 'status_objects_manifest.json')));
  assert.equal(sharedManifest.logical_partition_references, 3252);
  assert.equal(sharedManifest.physical_objects, 1899);
  const allowed = new Set(['status_objects_manifest.json', ...sharedManifest.objects.map(p => p.path), 'three_seasons.html', 'three_seasons_r17.html', 'three_seasons.css', 'three_seasons.js', 'validation_weights.js', 'validation_weight_sensitivity.json', 'r19_comparison.js', 'r19_recovered_comparison.json', 'population/collection_public.json', ...['population', 'population_r17'].flatMap(base => ['population_public.json', 'population_context.json', 'status_manifest.json', 'execution_public.json'].map(name => base + '/' + name))]);
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
        await page.waitForFunction(() => document.querySelectorAll('#r19-recovered-rows tr').length === 17);
        for (const league of ['ncaam','ncaaw']) for (const target of ['win','margin','total']) {
          await page.selectOption('#r19-recovered-league',league); await page.selectOption('#r19-recovered-target',target);
          assert.equal(await page.locator('#r19-recovered-rows tr').count(), target === 'win' ? 17 : 13);
          assert.equal(await page.locator('#r19-recovered-missing li').count(),8);
          assert.match(await page.locator('#r19-recovered-status').innerText(),/selection: 0%/);
        }
        await page.selectOption('#r19-recovered-league','ncaam'); await page.selectOption('#r19-recovered-target','win');
        await page.waitForFunction(() => document.querySelectorAll('#validation-weight-rows tr').length === 12);
        assert.match(await page.locator('#r19-execution-status').innerText(), /49 new target-model fits/);
        for (const league of ['ncaam', 'ncaaw']) {
          await page.selectOption('#validation-weight-league', league);
          for (const policy of ['primary_50_50', 'sensitivity_40_60', 'sensitivity_30_70', 'sensitivity_20_80', 'sensitivity_10_90']) {
            await page.selectOption('#validation-weight-policy', policy);
            for (const objective of ['win:accuracy', 'win:log_loss', 'win:brier', 'margin:mae', 'margin:rmse', 'total:mae', 'total:rmse']) {
              await page.selectOption('#validation-weight-objective', objective);
              assert.equal(await page.locator('#validation-weight-rows tr').count(), 12);
              assert.match(await page.locator('#validation-weight-status').innerText(), /2026–27 contributes zero selection weight/);
            }
          }
        }
        await page.selectOption('#validation-weight-league', 'ncaam');
        await page.selectOption('#validation-weight-policy', 'primary_50_50');
        await page.selectOption('#validation-weight-objective', 'win:log_loss');
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
        receipts.push({ version: 'three-season-population', width, source: true, allSixPopulations: true, allThreeTargets: true, rankSuppression: true, providerProducts: 4, explicitStatusIntegrity: true, fullPhysicalStatusIntegrity: true, filteredDownloadVerified: true, sharedImmutableObjectsOnly: true, realChromium: true });
        assert.match(await page.locator('#execution-summary').innerText(), /R18 stopped/);
        assert.match(await page.locator('#collection-summary').innerText(), /47 canonical/);
        await page.goto(origin + '/three_seasons_r17.html', { waitUntil: 'load' });
        await page.waitForFunction(() => window.SEL_POPULATION_CELLS_READY || window.SEL_POPULATION_CELLS_ERROR, null, { timeout: 90000 });
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_CELLS_ERROR), null);
        assert.equal(await page.evaluate(() => window.SEL_POPULATION_CELLS_READY.records), 1760);
        assert.match(await page.locator('#execution-summary').innerText(), /R17 produced/);
        assert.match(await page.locator('#reconciliation-note').innerText(), /827/);
        assert.deepEqual(errors, []);
        receipts.push({ version: 'preserved-r17', width, realChromium: true, statusRecords: 1760, snapshotDataNotMixed: true, sharedImmutableObjectsOnly: true });
      } finally { await page.close(); }
    }
  } finally { await new Promise(resolve => server.close(resolve)); }
  return receipts;
};
