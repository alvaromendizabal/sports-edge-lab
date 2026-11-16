'use strict';
// Real sanitized metrics through the actual UI code. This is a DOM contract
// check, not a visual browser or owner-model execution claim.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../docs/ncaa');
const source = fs.readFileSync(path.join(root, 'validation_weights.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'validation_weight_sensitivity.json')));
function element(value = '') {
  return { value, textContent: '', children: [], listeners: {},
    appendChild(child) { this.children.push(child); },
    replaceChildren() { this.children = []; },
    addEventListener(name, fn) { this.listeners[name] = fn; } };
}
async function run(input) {
  const nodes = new Map();
  for (const id of ['validation-weights', 'validation-weight-status', 'validation-weight-rows',
    'validation-weight-league', 'validation-weight-policy', 'validation-weight-objective']) nodes.set(id, element());
  nodes.get('validation-weight-league').value = 'ncaam';
  nodes.get('validation-weight-policy').value = 'primary_50_50';
  nodes.get('validation-weight-objective').value = 'win:log_loss';
  vm.runInNewContext(source, { document: {getElementById: id => nodes.get(id), createElement: () => element()},
    fetch: async name => { assert.equal(name, 'validation_weight_sensitivity.json'); return {ok: true, json: async () => input}; } });
  for (let i = 0; i < 10; i++) await Promise.resolve();
  return nodes;
}
(async () => {
  const ui = await run(data);
  assert.equal(ui.get('validation-weight-rows').children.length, 12);
  let panels = 0;
  for (const league of ['ncaam', 'ncaaw']) for (const policy of Object.keys(data.weights)) {
    for (const objective of ['win:accuracy', 'win:log_loss', 'win:brier', 'margin:mae', 'margin:rmse', 'total:mae', 'total:rmse']) {
      ui.get('validation-weight-league').value = league;
      ui.get('validation-weight-policy').value = policy;
      ui.get('validation-weight-objective').value = objective;
      ui.get('validation-weight-objective').listeners.change();
      const rows = ui.get('validation-weight-rows').children;
      assert.equal(rows.length, 12);
      assert(rows.every(row => row.children[5].textContent === 'Research only · promotion withheld'));
      assert.match(ui.get('validation-weight-status').textContent, /2026–27 contributes zero selection weight/);
      const [target, metric] = objective.split(':');
      const expected = data.weighted_panels.filter(row => row.league === league && row.target === target && row.policy === policy)
        .sort((a,b) => (metric === 'accuracy' ? -1 : 1) * (a.metrics[metric] - b.metrics[metric]) || a.public_label.localeCompare(b.public_label));
      assert.deepEqual(rows.map(row => row.children[0].textContent), expected.map(row => row.public_label));
      panels++;
    }
  }
  for (const [caseIndex, mutate] of [
    value => { value.weighted_panels[0].cohort_sha256s[0] = '0'.repeat(64); },
    value => { value.season_cells[0].season_end_year = 2027; },
    value => { const row = value.weighted_panels[0]; row.metrics[row.target === 'win' ? 'log_loss' : 'mae'] += .01; },
    value => { value.test_rows_used = 1; },
    value => { value.weighted_panels.pop(); }
  ].entries()) {
    const input = JSON.parse(JSON.stringify(data)); mutate(input);
    const rejected = await run(input);
    assert.equal(rejected.get('validation-weight-rows').children.length, 0, 'corruption case ' + caseIndex);
    assert.match(rejected.get('validation-weight-status').textContent, /No ranking has been substituted/);
  }
  console.log(JSON.stringify({status: 'PASS', panels, candidates_per_panel: 12,
    corruption_cases_rejected: 5, source: 'actual sanitized retained validation results',
    new_model_fits: 0, visual_browser_claim: false}));
})().catch(error => { console.error(error); process.exitCode = 1; });
