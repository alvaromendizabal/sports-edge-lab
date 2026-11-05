'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const {visibleIndices, hydrate} = require('../../../docs/fbs/source-progress.js');

const rows = [
  {season: 2024, home: 'Home A', away: 'Away A', completed: true},
  {season: 2025, home: 'San José State', away: 'Visitor', completed: true},
  {season: 2026, home: 'Home C', away: 'Away C', completed: false},
];

function domFixture(payload = {inventory: {schema: 'fbs.public.official-source-inventory.v1', rows}}) {
  const controls = {};
  for (const [id, value] of [
    ['source-season-filter', 'all'], ['source-result-filter', 'all'],
    ['source-team-filter', ''], ['source-clear-filters', ''],
    ['source-inventory-status', ''], ['source-inventory-empty', ''],
  ]) {
    controls[id] = {value, disabled: true, hidden: false, listeners: {}, textContent: '',
      addEventListener(event, listener) { this.listeners[event] = listener; }};
  }
  const tableRows = rows.map((row, index) => ({dataset: {sourceRow: String(index)}, hidden: false}));
  controls['source-progress-data'] = {textContent: JSON.stringify(payload)};
  controls['source-inventory-body'] = {dataset: {}, querySelectorAll: () => tableRows};
  return {controls, tableRows, getElementById: id => controls[id] || null};
}

test('all source rows are visible by default without mutation', () => {
  const before = JSON.stringify(rows);
  assert.deepEqual(visibleIndices(rows, {}), [0, 1, 2]);
  assert.equal(JSON.stringify(rows), before);
});
test('season and result filters remain separate', () => {
  assert.deepEqual(visibleIndices(rows, {season: '2026'}), [2]);
  assert.deepEqual(visibleIndices(rows, {result: 'completed'}), [0, 1]);
  assert.deepEqual(visibleIndices(rows, {result: 'not_completed'}), [2]);
  assert.deepEqual(visibleIndices(rows, {season: '2026', result: 'completed'}), []);
});
test('team search normalizes case and accents', () => {
  assert.deepEqual(visibleIndices(rows, {query: ' SAN JOSE '}), [1]);
  assert.deepEqual(visibleIndices(rows, {query: 'visitor'}), [1]);
});
test('hydration enables accessible controls and updates rows and polite count', () => {
  const doc = domFixture();
  assert.equal(hydrate(doc), true);
  assert.equal(doc.controls['source-season-filter'].disabled, false);
  assert.match(doc.controls['source-inventory-status'].textContent, /^3 of 3/);
  doc.controls['source-season-filter'].value = '2026';
  doc.controls['source-season-filter'].listeners.change();
  assert.deepEqual(doc.tableRows.map(row => row.hidden), [true, true, false]);
  assert.match(doc.controls['source-inventory-status'].textContent, /^1 of 3/);
  doc.controls['source-clear-filters'].listeners.click();
  assert.deepEqual(doc.tableRows.map(row => row.hidden), [false, false, false]);
  assert.equal(hydrate(doc), false);
});
test('empty result is a display state and reset restores every source row', () => {
  const doc = domFixture(); hydrate(doc);
  doc.controls['source-team-filter'].value = 'nonexistent fixture team';
  doc.controls['source-team-filter'].listeners.input();
  assert.equal(doc.controls['source-inventory-empty'].hidden, false);
  assert.equal(doc.tableRows.length, 3);
  doc.controls['source-clear-filters'].listeners.click();
  assert.equal(doc.controls['source-inventory-empty'].hidden, true);
  assert.deepEqual(doc.tableRows.map(row => row.hidden), [false, false, false]);
});
test('corrupt inline payload preserves complete static fallback', () => {
  const doc = domFixture(); doc.controls['source-progress-data'].textContent = '{broken';
  assert.equal(hydrate(doc), false);
  assert.deepEqual(doc.tableRows.map(row => row.hidden), [false, false, false]);
  assert.equal(doc.controls['source-season-filter'].disabled, true);
  assert.match(doc.controls['source-inventory-status'].textContent, /complete static source table remains visible/);
});
test('row identity mismatch preserves static table and refuses filtering', () => {
  const doc = domFixture(); doc.tableRows[1].dataset.sourceRow = '0';
  assert.equal(hydrate(doc), false);
  assert.deepEqual(doc.tableRows.map(row => row.hidden), [false, false, false]);
  assert.match(doc.controls['source-inventory-status'].textContent, /identity check failed/);
});
test('missing component does not alter other dashboard elements', () => {
  assert.equal(hydrate({getElementById() { return null; }}), false);
});
