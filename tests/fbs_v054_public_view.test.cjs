'use strict';
// Credential-free view behavior checks against permitted rounded display data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const vm = require('node:vm');
const docs = path.resolve(__dirname, '../docs/fbs');
const data = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(docs, 'current-evidence-v054.json.gz'))));
const view = require(path.join(docs, 'current-evidence-v054.js'));
const all = view.select(data, {season: 'all', period: 'all'});
assert.equal(all.length, 2742);
assert.equal(view.select(data, {season: '2026', period: 'all'}).length, 888);
assert.equal(view.select(data, {season: '2026', period: 'tbd'}).length, 81);
assert.equal(view.select(data, {season: '2026', period: 'current_week'}).length, 67);
const example = all.find(g => g.mixture_gated.p_home !== null);
assert.equal(view.select(data, {season: 'all', period: 'all', search: example.id}).length, 1);
for (const layer of Object.keys(view.layers)) {
  const csv = view.csv([example], layer);
  assert.equal(csv.split('\r\n').length, 2);
  assert.ok(csv.includes('"' + layer + '"'));
  assert.ok(csv.includes('"issue_deadline_utc"'));
}
assert.throws(() => view.csv([], '__proto__'), /Unknown evidence layer/);
const invented = {...example, home: '=UNTRUSTED()', away: '-UNTRUSTED()'};
assert.ok(view.csv([invented], 'original').includes("'=UNTRUSTED()"));
assert.ok(view.csv([invented], 'original').includes("'-UNTRUSTED()"));
const nodes = new Map();
function element(id) {
  if (!nodes.has(id)) nodes.set(id, {id, value: '', innerHTML: '', textContent: '', disabled: false,
    options: [], addEventListener() {}, showModal() {this.open = true;}, close() {this.open = false;}});
  return nodes.get(id);
}
element('season').value = '2026';
element('period').value = 'current_week';
element('layer').value = 'original';
const context = {window: {FBS_CURRENT_EVIDENCE_V054_READY: Promise.resolve(data)},
  document: {getElementById: element}, Intl, Date, URLSearchParams, location: {search: ''},
  module: {exports: {}}, setTimeout, console};
vm.createContext(context);
(async () => {
  await vm.runInContext(fs.readFileSync(path.join(docs, 'current-evidence-v054.js'), 'utf8'), context);
  assert.match(element('game-summary').textContent, /^67 source games/);
  assert.match(element('execution-summary').textContent, /3 base fits and 6 mixture fits/);
  assert.equal((element('game-rows').innerHTML.match(/data-game=/g) || []).length, 40);
  assert.match(element('mixture-rows').innerHTML, /7\.774158/);
  element('game-rows').onclick({target: {closest() {return {dataset: {game: example.id}};}}});
  assert.equal(element('game-detail').open, true);
  assert.match(element('detail-content').innerHTML, /Saved issue context history/);
  assert.match(element('detail-content').innerHTML, /Global mixture issued shadow/);
  assert.match(element('detail-content').innerHTML, /Historical reconstruction/);
  element('close-detail').onclick();
  assert.equal(element('game-detail').open, false);
  console.log('PASS: saved evidence filters, seven layer exports, injection escaping, pagination, metrics and accessible detail behavior.');
})().catch(error => {console.error(error); process.exitCode = 1;});
