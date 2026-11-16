// Synthetic contract and DOM fixtures only. These are not scientific results.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const api = require('../../docs/ncaa/three_seasons.js');
const docs = path.resolve(__dirname, '../../docs/ncaa');
const html = fs.readFileSync(path.join(docs, 'three_seasons.html'), 'utf8');
const providers = ['draftkings_sportsbook', 'kalshi', 'polymarket_international', 'polymarket_us'];
const years = [2025, 2026, 2027], leagues = ['ncaam', 'ncaaw'], targets = ['win', 'margin', 'total'];
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const h = letter => letter.repeat(64);

function fixture() {
  const data = { schema: 'sel.ncaa.b088.population_public.v1', asof: '2026-11-15T21:27:26Z', population_hash: h('a'), seasons: [], model_roster: [], model_target_coverage: [], same_game_scoreboards: [], provider_target_coverage: [], paired_model_provider_scoreboards: [], status_partition_manifest: [] };
  const assets = new Map();
  for (const league of leagues) for (const role of ['original', 'unavailable']) data.model_roster.push({ model_id: `${league}-${role}`, public_label: `Fixture ${role}`, league, targets, lineage: role, availability_status: role === 'original' ? 'REGISTERED' : 'UNAVAILABLE' });
  for (const year of years) {
    const season = { season_end_year: year, season_label: `${year - 1}-${String(year).slice(-2)}`, population_role: year === 2027 ? 'test' : 'validation', test_already_exposed: year === 2027, leagues: {} };
    for (const league of leagues) {
      season.leagues[league] = { declared_population_count: 3, future_or_unresolved_count: 1, population_game_set_sha256: h('b'), official_completeness: false, official_completeness_reasons: ['OFFICIAL_UNIVERSE_NOT_VERIFIED'] };
      for (const target of targets) {
        for (const model of data.model_roster.filter(m => m.league === league)) {
          const available = model.lineage === 'original';
          data.model_target_coverage.push({ league, season_end_year: year, target, model_id: model.model_id, lineage: model.lineage, declared_population_count: 3, target_eligible_count: 3, prediction_available_count: available ? 3 : 0, descriptive_scored_count: available ? 3 : 0, qualified_scored_count: 0, missing_prediction_count: available ? 0 : 3, invalid_or_ambiguous_count: 0, rank_permitted: false, metrics_by_evidence_class: ['original_issued', 'valid_replay', 'later_fitted', 'unqualified_reconstruction'].map(evidence_class => ({ evidence_class, games: available && evidence_class === 'unqualified_reconstruction' ? 3 : 0, metrics: available && evidence_class === 'unqualified_reconstruction' ? target === 'win' ? { accuracy: 2 / 3, log_loss: 0.6, brier: 0.2 } : { mae: 4, rmse: 5, bias: -2 } : null, metric_scope: 'OWN_OBSERVED_SUBSET_NOT_A_RANKING' })) });
        }
        for (const evidence_class of ['original_issued', 'valid_replay', 'later_fitted', 'unqualified_reconstruction']) data.same_game_scoreboards.push({ league, season_end_year: year, target, evidence_class, declared_model_ids: data.model_roster.filter(m => m.league === league).map(m => m.model_id), declared_model_roster_hash: h('c'), common_cohort_hash: h('d'), common_cohort_count: 0, full_population_count: 3, target_eligible_count: 3, metric_scope: 'SECONDARY_COMMON_INTERSECTION', rank_permitted: false, rank_suppression_reasons: ['COMMON_COHORT_EMPTY'], metrics_by_model: data.model_roster.filter(m => m.league === league).map(m => ({ model_id: m.model_id, games: 0, metrics: null })) });
        for (const provider_product of providers) {
          data.provider_target_coverage.push({ league, season_end_year: year, target, provider_product, declared_population_count: 3, target_eligible_count: 3, observed_quote_game_count: 0, qualified_game_count: 0, missing_qualified_game_count: 3, reason_counts_overlapping: { PROVIDER_GAME_QUOTE_MISSING: 3 }, rank_permitted: false });
          data.paired_model_provider_scoreboards.push({ league, season_end_year: year, target, provider_product, model_evidence_class: 'original_issued', provider_evidence_class: 'original_issued', common_cohort_hash: h('d'), common_cohort_count: 0, full_population_count: 3, target_eligible_count: 3, rank_permitted: false, all_models_and_provider_use_identical_games: true, metrics_by_model: data.model_roster.filter(m => m.league === league).map(m => ({ model_id: m.model_id, games: 0, metrics: null })), provider_metrics: { games: 0, metrics: null }, missing_or_unmatched_population_count: 3 });
        }
        const cells = [];
        for (let i = 0; i < 4; i++) {
          const base = { public_game_key: `fixture-${league}-${year}-${i}`, league, season_end_year: year, population_role: i < 3 ? season.population_role : 'future_or_unresolved', public_home_team: i === 0 ? '<script>home</script>' : `Fixture Home ${i}`, public_away_team: `Fixture Away ${i}`, public_event_date: `${year - 1}-11-${String(i + 1).padStart(2, '0')}`, target, target_population_eligible: i < 3 };
          for (const model of data.model_roster.filter(m => m.league === league)) cells.push({ ...base, entity_type: 'model', public_entity_id: model.model_id, evidence_class: model.lineage === 'original' && i < 3 ? 'unqualified_reconstruction' : 'missing', status: model.lineage === 'original' && i < 3 ? 'DESCRIPTIVE_ONLY' : 'MISSING_PREDICTION', reason_codes: [i < 3 ? 'SOURCE_CLOCK_NOT_QUALIFIED' : 'FUTURE_OR_UNRESOLVED_NOT_TEST_MEMBER'] });
          for (const provider of providers) cells.push({ ...base, entity_type: 'provider', public_entity_id: provider, evidence_class: 'missing', status: 'MISSING_QUALIFIED_MARKET', reason_codes: ['PROVIDER_GAME_QUOTE_MISSING'] });
        }
        const logical = Buffer.from(cells.map(row => JSON.stringify(row) + '\n').join('')), body = zlib.gzipSync(logical);
        const filename = `fixture_${league}_${year}_${target}_part_00000.jsonl.gz`;
        const descriptor = { filename, bytes: body.length, sha256: sha(body), league, season_end_year: year, target, part: 0, rows: cells.length, logical_bytes: logical.length, logical_sha256: sha(logical), codec: 'jsonl_gzip', population_hash: data.population_hash, scope: 'EXPLICIT_CELLS_NO_SPARSE_DEFAULTS', physical_readback_verified: true };
        data.status_partition_manifest.push(descriptor); assets.set(`population/status/${filename}`, body);
      }
    }
    data.seasons.push(season);
  }
  const manifest = { schema: data.schema + '.status_parts', population_hash: data.population_hash, complete: true, rows: data.status_partition_manifest.reduce((n,p) => n + p.rows, 0), parts: structuredClone(data.status_partition_manifest) };
  assets.set('population/population_public.json', data);
  assets.set('population/status_manifest.json', manifest);
  assets.set('population/execution_public.json', { public_title: 'Fixture partial execution', public_summary: 'Contract fixture, not a production result.', public_counters: [], count_scope: 'Fixture' });
  return { data, manifest, assets };
}

class Element {
  constructor(id) { this.id = id; this.value = ''; this.innerHTML = ''; this.textContent = ''; this.disabled = false; this.hidden = false; this.events = {}; this.classList = { add() {} }; }
  addEventListener(name, fn) { this.events[name] = fn; }
  dispatch(name) { return this.events[name](); }
  click() { if (this.events.click) return this.events.click(); }
}
function harness(bundle) {
  const elements = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m => [m[1], new Element(m[1])]));
  const get = id => { assert(elements.has(id), `Missing DOM id ${id}`); return elements.get(id); };
  for (const [id, value] of Object.entries({ competition: 'all', season: 'all', target: 'win', evidence: 'all', 'model-filter': 'all', 'coverage-filter': 'all', 'cell-competition': 'ncaam', 'cell-season': '2027', 'cell-target': 'win', 'cell-evidence': 'all', 'cell-game-status': 'all', 'cell-state': 'all' })) get(id).value = value;
  const fetched = [], output = { downloaded: null };
  const win = { document: { body: { dataset: { populationBase: bundle.populationBase || 'population' } }, getElementById: get, createElement: () => new Element('download') }, Blob, Response, DecompressionStream, TextDecoder, crypto: crypto.webcrypto, setTimeout: fn => fn(), URL: { createObjectURL: blob => { output.downloaded = blob; return 'blob:fixture'; }, revokeObjectURL() {} }, fetch: async asset => {
    fetched.push(asset);
    if (!bundle.assets.has(asset)) return { ok: false, status: 404 };
    const value = bundle.assets.get(asset);
    return { ok: true, json: async () => structuredClone(value), arrayBuffer: async () => Uint8Array.from(value).buffer };
  } };
  api.start(win);
  return { win, get, elements, fetched, output };
}
async function waitFor(fn) {
  for (let i = 0; i < 1000; i++) { if (fn()) return; await new Promise(resolve => setTimeout(resolve, 5)); }
  throw new Error('Fixture async action timed out');
}

async function main() {
  const bundle = fixture(), normalized = api.normalizeB088(bundle.data);
  assert.equal(api.populations(normalized).length, 6);
  assert.equal(api.officialQualified(api.populations(normalized)[0]), false);
  assert.equal(api.populations(normalized)[0].official_completeness.official_completed_count, null);
  assert.equal(api.targetDenominator(api.populations(normalized)[0], 'win'), 3);
  const mismatch = structuredClone(bundle.data); mismatch.provider_target_coverage[0].target_eligible_count = 9;
  assert.equal(api.targetDenominator(api.populations(api.normalizeB088(mismatch))[0], 'win'), null);
  const board = api.populations(normalized)[0].same_game_scoreboards[0];
  assert.equal(api.boardQualification({ ...board, rank_permitted: true }, api.populations(normalized)[0]).permitted, false);
  assert.equal(api.pairedQualified(bundle.data.paired_model_provider_scoreboards[0]), false);
  const paired = { ...bundle.data.paired_model_provider_scoreboards[0], common_cohort_count: 3, metrics_by_model: [{ games: 3 }], provider_metrics: { games: 3 } };
  assert.equal(api.pairedQualified(paired), true);
  assert.equal(api.pairedQualified({ ...paired, provider_metrics: { games: 2 } }), false);
  assert.match(api.metricValue(null, 'log_loss'), /Unavailable/);
  assert.match(api.metricValue(-2, 'bias'), /-2\.000/);
  assert.equal(api.pacific('2026-11-15', true), '2026-11-15 · date only');
  assert.match(api.pacific('2026-11-15T21:27:26Z'), /PST/);
  assert.throws(() => api.relativeAsset('population/../private.json'), /not qualified/);
  assert.throws(() => api.relativeAsset('https://example.test/private.json'), /not qualified/);
  const descriptor = bundle.data.status_partition_manifest[0];
  const firstCell = JSON.parse(zlib.gunzipSync(bundle.assets.get('population/status/' + descriptor.filename)).toString().split('\n')[0]);
  assert.throws(() => api.publicCell({ ...firstCell, prediction: 0.9 }, descriptor), /outside the public status contract/);
  assert.throws(() => api.publicCell({ ...firstCell, league: 'ncaaw' }, descriptor), /identity mismatch/);
  const ui = harness(bundle);
  ui.get('competition').dispatch('change'); // early interactions before load
  await waitFor(() => ui.win.SEL_POPULATION_CELLS_READY || ui.win.SEL_POPULATION_CELLS_ERROR);
  assert.equal(ui.win.SEL_POPULATION_ERROR, undefined);
  assert.equal(ui.win.SEL_POPULATION_CELLS_ERROR, null);
  assert.equal(ui.win.SEL_POPULATION_READY.populations, 6);
  assert.equal(ui.win.SEL_POPULATION_CELLS_READY.records, 4);
  assert.match(ui.get('rank-status').innerHTML, /No complete, comparable full-population champion/);
  assert.match(ui.get('population-rows').innerHTML, /Completeness unverified/);
  assert.match(ui.get('own-subset-rows').innerHTML, /66\.67%/);
  assert(!ui.get('provider-scoreboards').innerHTML.includes('0.00000'));
  assert(!ui.get('cell-rows').innerHTML.includes('<script>home</script>'));
  assert(ui.get('cell-rows').innerHTML.includes('&lt;script&gt;home&lt;/script&gt;'));
  const gzFetches = () => ui.fetched.filter(name => name.endsWith('.gz')).length;
  const initialReads = gzFetches();
  ui.get('cell-entity').value = 'provider:kalshi'; ui.get('cell-entity').dispatch('change');
  await waitFor(() => ui.win.SEL_POPULATION_CELLS_READY && ui.win.SEL_POPULATION_CELLS_READY.entity === 'kalshi');
  assert.equal(gzFetches(), initialReads, 'Changing entity reuses verified compressed bytes');
  ui.get('cell-game-status').value = 'future_or_unresolved'; ui.get('cell-game-status').dispatch('change');
  assert.match(ui.get('cell-count').textContent, /^1 matching/);
  ui.get('download-cells').click();
  const exportData = JSON.parse(await ui.output.downloaded.text());
  assert.equal(exportData.rows.length, 1);
  assert.equal(exportData.rows[0].public_entity_id, 'kalshi');
  assert(!Object.hasOwn(exportData.rows[0], 'prediction'));
  assert.equal(exportData.complete_official_population_claimed, false);
  ui.get('cell-game-status').value = 'all'; ui.get('cell-game-status').dispatch('change');
  ui.get('cell-search').value = 'nonexistent-fixture'; ui.get('cell-search').dispatch('input');
  assert.match(ui.get('cell-count').textContent, /^0 matching/);
  assert(ui.get('download-cells').disabled);
  ui.get('evidence').value = 'original_issued'; ui.get('evidence').dispatch('change');
  assert.match(ui.get('model-coverage-rows').innerHTML, /Coverage across all evidence classes/);
  assert(!ui.get('own-subset-rows').innerHTML.includes('66.67%'));
  ui.get('competition').value = 'ncaaw'; ui.get('season').value = '2025'; ui.get('target').value = 'margin'; ui.get('evidence').value = 'all'; ui.get('target').dispatch('change');
  assert.match(ui.get('population-rows').innerHTML, /Women · 2024-25/);
  assert.match(ui.get('own-subset-rows').innerHTML, /-2\.000/);
  for (const element of ui.elements.values()) { assert(!element.innerHTML.includes('NaN')); assert(!element.innerHTML.includes('undefined')); }
  const corrupt = fixture();
  const first = corrupt.data.status_partition_manifest.find(p => p.season_end_year === 2027 && p.league === 'ncaam' && p.target === 'win');
  const bytes = Buffer.from(corrupt.assets.get('population/status/' + first.filename)); bytes[bytes.length - 1] ^= 1; corrupt.assets.set('population/status/' + first.filename, bytes);
  const broken = harness(corrupt); await waitFor(() => broken.win.SEL_POPULATION_CELLS_ERROR);
  assert.match(broken.win.SEL_POPULATION_CELLS_ERROR, /integrity check failed/);
  assert.equal(broken.win.SEL_POPULATION_CELLS_READY, null);
  assert(broken.get('download-cells').disabled);
  const missing = fixture(); missing.assets.delete('population/status/' + first.filename);
  const absent = harness(missing); await waitFor(() => absent.win.SEL_POPULATION_CELLS_ERROR);
  assert.match(absent.win.SEL_POPULATION_CELLS_ERROR, /unavailable \(404\)/);
  console.log(JSON.stringify({ status: 'PASS', kind: 'synthetic contract and DOM fixture, not scientific or visual-browser evidence', scenarios: ['six population roles', 'unknown official denominators', 'conflicting target denominator', 'suppressed incomplete ranks', 'same-game provider count gate', 'null and signed metrics', 'Pacific and date-only clocks', 'public field allowlist', 'XSS escaping', 'bounded hash-verified gzip loading', 'unchanged-byte cache reuse', 'explicit future and missing cells', 'filtered status export', 'separate own-subset evidence classes', 'missing and corrupted partition rejection'] }));
}
module.exports = { harness, waitFor };
if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });
