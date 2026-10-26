// Semantic DOM fixture, not a rendered-browser or accessibility audit.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(path.resolve(__dirname, '../../../docs/review/index.html'), 'utf8');
const data = JSON.parse(html.match(/<script type="application\/json" id="evidence-data">([\s\S]*?)<\/script>/)[1]);
const program = html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
class Element {
  constructor() { this.children = []; this.textContent = ''; this.value = ''; this.listeners = {}; }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
}
const nodes = Object.fromEntries(['sport', 'campaign', 'metric', 'evidence-data', 'caption', 'framework-caption', 'count', 'tbody', 'framework-tbody'].map(id => [id, new Element()]));
nodes['evidence-data'].textContent = JSON.stringify(data);
nodes.sport.value = 'all'; nodes.campaign.value = 'all'; nodes.metric.value = 'logloss';
const document = {
  getElementById: id => nodes[id],
  querySelector: selector => { assert.ok(['#scores tbody','#framework-scores tbody'].includes(selector)); return nodes[selector === '#scores tbody' ? 'tbody' : 'framework-tbody']; },
  createElement: () => new Element(),
};
vm.runInNewContext(program, { document });
let states = 0;
for (const sport of ['all', 'NFL', 'FBS']) for (const campaign of ['all', '2024', '2025', '2026']) for (const metric of ['logloss', 'brier']) {
  nodes.sport.value = sport; nodes.campaign.value = campaign; nodes.metric.value = metric;
  nodes.metric.listeners.change();
  const expected = data.rows.filter(row => (sport === 'all' || row.sport === sport) && (campaign === 'all' || row.campaign.startsWith(campaign)));
  assert.equal(nodes.tbody.children.length, expected.length);
  assert.equal(nodes.count.textContent, `Showing ${expected.length} cohorts.`);
  expected.forEach((row, i) => {
    const reference = metric === 'brier' ? 'retained_brier_reference' : 'retained_log_loss_reference';
    const scores = ['market', 'matched_control', 'learned', 'direct', 'challenger', reference].map(key => row[key][metric]);
    const cells = nodes.tbody.children[i].children;
    assert.equal(cells[0].textContent, row.sport);
    assert.equal(cells[1].textContent, row.campaign);
    scores.forEach((value, j) => {
      assert.equal(cells[j + 3].textContent, value.toFixed(6));
      assert.equal(cells[j + 3].className.includes('best'), value === Math.min(...scores));
    });
  });
  expected.forEach((row, i) => {
    const reference = metric === 'brier' ? 'retained_brier_reference' : 'retained_log_loss_reference';
    const scores = [...['LightGBM','XGBoost','PyTorch','TensorFlow','Equal-weight ensemble'].map(name=>row.new_frameworks[name][metric]),row[reference][metric]];
    const cells = nodes['framework-tbody'].children[i].children;
    scores.forEach((value,j)=>{assert.equal(cells[j+3].textContent,value.toFixed(6));assert.equal(cells[j+3].className.includes('best'),value===Math.min(...scores));});
  });
  states++;
}
console.log(JSON.stringify({ status: 'PASS', selector_states: states, tables_per_state: 2, method: 'minimal DOM fixture; no rendered browser' }));
