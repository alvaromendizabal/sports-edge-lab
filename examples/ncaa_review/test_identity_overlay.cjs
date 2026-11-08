// Invented records exercise the exact shipped identity validator without a network.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createHash } = require('node:crypto');

function shippedIdentityValidator() {
  const html = fs.readFileSync(path.join(__dirname, 'private_report.html.tmpl'), 'utf8');
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x => x[1]).filter(source => source.includes('function validateIdentityOverlay('));
  assert.equal(scripts.length, 1, 'Exactly one main identity script is exercised; the independent V4 script has its own contract.');
  let source = scripts[0];
  source = source.replace(/\}\)\(\);\s*$/, 'globalThis.identityAudit={validateIdentityOverlay,validate,recordAdapter};})();');
  const stub = { addEventListener() {}, value: 'all' };
  const context = { document: { getElementById() { return stub; } } };
  vm.createContext(context); vm.runInContext(source, context);
  return context.identityAudit;
}

function fixture() {
  const base = { league: 'ncaam', home_team: 'Invented North', away_team: 'Invented South', event_time: '2026-11-04T20:00:00Z', season_end_year: 2027 };
  const rows = [
    { ...base, event_id: 'official-invented', source_binding_status: 'UNMATCHED_OFFICIAL_CANDIDATE_RECORD', prediction_win: null, prediction_margin: null, prediction_total: null, training_cutoff: null, durable_issued_before_cutoff: false },
    { ...base, event_id: 'source-invented', source_binding_status: 'EXACT_SOURCE_BINDING', prediction_win: 0.64, prediction_margin: 4.5, prediction_total: 140, training_cutoff: '2026-11-04T18:00:00Z', durable_issued_before_cutoff: false },
    { ...base, event_id: 'source-invented', source_binding_status: 'EXACT_SOURCE_BINDING', prediction_win: 0.61, prediction_margin: 3.1, prediction_total: 138, training_cutoff: '2026-11-03T18:00:00Z', durable_issued_before_cutoff: true },
    { ...base, event_id: 'another-source', source_binding_status: 'EXACT_SOURCE_BINDING', prediction_win: 0.53, prediction_margin: 1.1, prediction_total: 132, training_cutoff: '2026-11-04T18:00:00Z', durable_issued_before_cutoff: false },
  ];
  const report = { schema: 'sports-edge-lab.private.game-report.v1', records: rows, market_observations: [], metrics: [{ n: 2, accuracy: 0.5 }], weekly_metrics: [] };
  const body = Buffer.from(JSON.stringify(report)), pin = { bytes: body.length, sha256: createHash('sha256').update(body).digest('hex') };
  const overlay = { schema: 'sel.ncaa.b047r1.identity_overlay.v1', baseline: { ...pin, record_count: rows.length, source_game_count: 3 }, links: [{ league: 'ncaam', source_event_id: 'official-invented', canonical_event_id: 'source-invented', status: 'VERIFIED_SOURCE_IDENTITY_LINK', proof: { scope: 'INVENTED_FIXTURE', raw_body_sha256: '1'.repeat(64), original_clock: '2026-11-03T19:00:00Z' } }] };
  return { rows, report, body, pin, overlay };
}

const validator = shippedIdentityValidator(), original = fixture();
const snapshot = JSON.stringify(original.report), overlaySnapshot = JSON.stringify(original.overlay);
const accepted = validator.validateIdentityOverlay(original.overlay, original.pin, original.rows);
assert.equal(accepted.rawSourceCount, 3); assert.equal(accepted.canonicalGroupCount, 2); assert.equal(accepted.recordCount, 4);
assert.equal(accepted.outgoing.size, 1); assert.equal(accepted.incoming.size, 1);
assert.equal(JSON.stringify(original.report), snapshot);
assert.equal(JSON.stringify(original.overlay), overlaySnapshot);
assert.equal(original.rows[0].prediction_win, null); // A link never borrows a forecast.
assert.equal(original.rows[1].prediction_win, 0.64); assert.equal(original.rows[2].durable_issued_before_cutoff, true);
const cases = [
  ['wrong baseline hash', f => { f.overlay.baseline.sha256 = '0'.repeat(64); }],
  ['wrong baseline bytes', f => { f.overlay.baseline.bytes++; }],
  ['wrong row count', f => { f.overlay.baseline.record_count--; }],
  ['wrong source count', f => { f.overlay.baseline.source_game_count--; }],
  ['duplicate link', f => { f.overlay.links.push(structuredClone(f.overlay.links[0])); }],
  ['conflicting target', f => { f.overlay.links.push({ ...f.overlay.links[0], canonical_event_id: 'another-source' }); }],
  ['cycle', f => { f.overlay.links.push({ ...f.overlay.links[0], source_event_id: 'source-invented', canonical_event_id: 'official-invented' }); }],
  ['chain', f => { f.overlay.links.push({ ...f.overlay.links[0], source_event_id: 'source-invented', canonical_event_id: 'another-source' }); }],
  ['missing source', f => { f.overlay.links[0].source_event_id = 'not-in-baseline'; }],
  ['wrong league', f => { f.overlay.links[0].league = 'ncaaw'; }],
  ['self link', f => { f.overlay.links[0].canonical_event_id = 'official-invented'; }],
  ['unsupported status', f => { f.overlay.links[0].status = 'CANDIDATE'; }],
  ['missing proof', f => { f.overlay.links[0].proof = {}; }],
  ['forecast replacement', f => { f.overlay.links[0].prediction_win = 0.99; }],
  ['source is not official candidate', f => { f.rows[0].source_binding_status = 'EXACT_SOURCE_BINDING'; }],
  ['canonical is still unmatched', f => { f.rows[1].source_binding_status = 'UNMATCHED_OFFICIAL_CANDIDATE_RECORD'; }],
];
for (const [name, mutate] of cases) {
  const f = fixture(); mutate(f); const before = JSON.stringify(f.report);
  assert.throws(() => validator.validateIdentityOverlay(f.overlay, f.pin, f.rows), undefined, name);
  assert.equal(JSON.stringify(f.report), before, name + ' must preserve original records');
}
console.log(JSON.stringify({ identity_overlay_unit_tests: 'PASS', accepted: 1, rejected: cases.length, unchanged_original_rows: true, fixture_only: true }));

module.exports = { shippedIdentityValidator, fixture };
