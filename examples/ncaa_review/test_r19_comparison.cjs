'use strict';
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '../../docs/ncaa');
const source = fs.readFileSync(path.join(root, 'r19_comparison.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'r19_recovered_comparison.json')));
function element(value = '') { return {value, textContent: '', children: [], listeners: {},
  appendChild(child) { this.children.push(child); }, replaceChildren(...children) { this.children = children; },
  addEventListener(name, handler) { this.listeners[name] = handler; }}; }
async function run(input) {
  const nodes = new Map(['r19-recovered','r19-recovered-league','r19-recovered-target','r19-recovered-status',
    'r19-recovered-rows','r19-recovered-head','r19-recovered-gaps','r19-recovered-missing'].map(id => [id, element()]));
  nodes.get('r19-recovered-league').value = 'ncaam'; nodes.get('r19-recovered-target').value = 'win';
  vm.runInNewContext(source, {document: {getElementById: id => nodes.get(id), createElement: () => element()},
    fetch: async name => { assert.equal(name, 'r19_recovered_comparison.json'); return {ok: true, json: async () => input}; }});
  for (let i = 0; i < 10; i++) await Promise.resolve();
  return nodes;
}
(async () => {
  const ui = await run(data), roster = new Map(data.model_roster.map(row => [row.model_id,row]));
  let panels = 0;
  for (const league of ['ncaam','ncaaw']) for (const target of ['win','margin','total']) {
    ui.get('r19-recovered-league').value = league; ui.get('r19-recovered-target').value = target;
    ui.get('r19-recovered-target').listeners.change();
    const rows = ui.get('r19-recovered-rows').children;
    assert.equal(rows.length, target === 'win' ? 17 : 13);
    const expected = data.metrics.filter(row => row.league === league && row.target === target);
    assert.deepEqual(rows.map(row => row.children[0].textContent), expected.map(row => roster.get(row.public_model_id).public_label));
    assert(rows.every(row => row.children[1].textContent === (league === 'ncaam' ? '637' : '655')));
    assert.equal(ui.get('r19-recovered-missing').children.length, 8);
    assert.match(ui.get('r19-recovered-status').textContent, /selection: 0%/);
    panels++;
  }
  for (const mutate of [
    d => { d.metrics[0].games++; },
    d => { d.metrics[0].cohort_sha256 = '0'.repeat(64); },
    d => { d.metrics[0].qualified_games = 1; },
    d => { d.metrics[0].rank_permitted = true; },
    d => { d.missing_registered_target_policies.pop(); },
    d => { d.test_selection_weight = .5; }
  ]) {
    const changed = JSON.parse(JSON.stringify(data)); mutate(changed); const bad = await run(changed);
    assert.equal(bad.get('r19-recovered-rows').children.length,0);
    assert.match(bad.get('r19-recovered-status').textContent,/No older or differently scoped scores were substituted/);
  }
  console.log(JSON.stringify({status:'PASS',panels,metrics:86,missing_policies:8,corruptions_rejected:6,
    observed_test_scores_never_sorted_for_selection:true,new_fits:0,visual_browser_claim:false}));
})().catch(error => { console.error(error); process.exitCode = 1; });
