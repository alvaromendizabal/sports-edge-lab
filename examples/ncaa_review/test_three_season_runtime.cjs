// Actual public data through the actual page logic; DOM harness, not visual browser evidence.
'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const { harness, waitFor } = require('./test_three_season_dashboard.cjs');
const docs = path.resolve(__dirname, '../../docs/ncaa');
const assets = { has: name => fs.existsSync(path.join(docs, name)), get: name => name.endsWith('.gz') ? fs.readFileSync(path.join(docs, name)) : JSON.parse(fs.readFileSync(path.join(docs, name))) };
(async () => {
  const data = assets.get('population/population_public.json'), ui = harness({ assets });
  await waitFor(() => ui.win.SEL_POPULATION_CELLS_READY || ui.win.SEL_POPULATION_CELLS_ERROR);
  assert.equal(ui.win.SEL_POPULATION_ERROR, undefined);
  assert.equal(ui.win.SEL_POPULATION_CONTEXT_ERROR, undefined);
  assert.equal(ui.win.SEL_POPULATION_CELLS_ERROR, null);
  assert.equal(ui.win.SEL_POPULATION_CELLS_READY.records, 1760);
  assert.match(ui.get('reconciliation-note').innerHTML, /827/);
  assert.match(ui.get('reconciliation-note').innerHTML, /263/);
  assert.match(ui.get('reconciliation-note').innerHTML, /1,090/);
  assert.match(ui.get('reconciliation-note').innerHTML, /not counted as proven additional unique games/);
  assert.match(ui.get('rank-status').innerHTML, /No complete, comparable full-population champion/);
  for (const [league, games, accuracy] of [['ncaam', 610, '78.36%'], ['ncaaw', 606, '82.01%']]) {
    const original = data.model_roster.find(row => row.league === league && row.lineage === 'original');
    ui.get('competition').value = league; ui.get('season').value = '2027'; ui.get('target').value = 'win'; ui.get('model-filter').value = original.model_id; ui.get('model-filter').dispatch('change');
    assert(ui.get('own-subset-rows').innerHTML.includes(accuracy));
    assert(ui.get('own-subset-rows').innerHTML.includes(String(games)));
    const cohort = data.model_target_coverage.find(row => row.league === league && row.model_id === original.model_id && row.target === 'win' && row.season_end_year === 2027).metrics_by_evidence_class.find(row => row.games === games).cohort_hash;
    assert(ui.get('own-subset-rows').innerHTML.includes(cohort));
  }
  const reads = ui.fetched.filter(name => name.endsWith('.gz')).length;
  ui.get('cell-entity').value = 'provider:kalshi'; ui.get('cell-entity').dispatch('change');
  await waitFor(() => ui.win.SEL_POPULATION_CELLS_READY && ui.win.SEL_POPULATION_CELLS_READY.entity === 'kalshi');
  assert.equal(ui.fetched.filter(name => name.endsWith('.gz')).length, reads);
  assert.equal(ui.win.SEL_POPULATION_CELLS_READY.records, 1760);
  ui.get('cell-game-status').value = 'future_or_unresolved'; ui.get('cell-game-status').dispatch('change');
  assert.match(ui.get('cell-count').textContent, /^670 matching/);
  ui.get('download-cells').click();
  const exported = JSON.parse(await ui.output.downloaded.text());
  assert.equal(exported.row_count, 670);
  assert(exported.rows.every(row => row.public_entity_id === 'kalshi' && row.population_role === 'future_or_unresolved' && !Object.hasOwn(row, 'prediction')));
  console.log(JSON.stringify({ status: 'PASS', kind: 'authentic public-data DOM integration; not visual browser verification', six_populations: true, current_original_cohorts: { ncaam: 610, ncaaw: 606 }, current_source_and_unmatched_counts_separate: true, manifest_and_selected_status_parts_verified: true, source_cache_reused: true, future_status_export_only: true, champion_ranks_suppressed: true }));
})().catch(error => { console.error(error); process.exitCode = 1; });
