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
const nodes = Object.fromEntries(['sport', 'campaign', 'metric', 'evidence-data', 'caption', 'framework-caption', 'count', 'tbody', 'framework-tbody', 'score-law-binary-tbody', 'score-law-distribution-tbody', 'score-law-binary-caption', 'score-law-distribution-caption', 'distribution-metric'].map(id => [id, new Element()]));
nodes['evidence-data'].textContent = JSON.stringify(data);
nodes.sport.value = 'all'; nodes.campaign.value = 'all'; nodes.metric.value = 'logloss'; nodes['distribution-metric'].value = 'joint_nll';
const document = {
  getElementById: id => nodes[id],
  querySelector: selector => { const mapping={'#scores tbody':'tbody','#framework-scores tbody':'framework-tbody','#score-law-binary tbody':'score-law-binary-tbody','#score-law-distribution tbody':'score-law-distribution-tbody'}; assert.ok(selector in mapping); return nodes[mapping[selector]]; },
  createElement: () => new Element(),
};
vm.runInNewContext(program, { document });
let states = 0;
for (const sport of ['all', 'NFL', 'FBS']) for (const campaign of ['all', '2024', '2025', '2026']) for (const metric of ['logloss', 'brier']) for (const distributionMetric of ['joint_nll','mean_marginal_crps']) {
  nodes.sport.value = sport; nodes.campaign.value = campaign; nodes.metric.value = metric; nodes['distribution-metric'].value=distributionMetric;
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
      assert.equal(cells[j + 3].className.includes('best'), !row.campaign.startsWith('2026') && value === Math.min(...scores));
    });
  });
  expected.forEach((row, i) => {
    const reference = metric === 'brier' ? 'retained_brier_reference' : 'retained_log_loss_reference';
    const scores = [...['LightGBM','XGBoost','PyTorch','TensorFlow','Equal-weight ensemble'].map(name=>row.new_frameworks[name][metric]),row[reference][metric]];
    const cells = nodes['framework-tbody'].children[i].children;
    scores.forEach((value,j)=>{assert.equal(cells[j+3].textContent,value.toFixed(6));assert.equal(cells[j+3].className.includes('best'),!row.campaign.startsWith('2026')&&value===Math.min(...scores));});
  });
  expected.forEach((row,i)=>{
    const reference=metric==='brier'?'retained_brier_reference':'retained_log_loss_reference';
    const binaries=[row.market,row[reference],...['Ensemble D0','Ensemble D1','Learned MARKET distribution','PyTorch D0','PyTorch D1','TensorFlow D0','TensorFlow D1'].map(name=>row.score_law_binary[name])];
    const distributions=['Learned MARKET distribution','Ensemble D0','Ensemble D1','PyTorch D0','PyTorch D1','TensorFlow D0','TensorFlow D1'].map(name=>row.score_law_distribution[name]);
    for(const [name,records,key] of [['score-law-binary-tbody',binaries,metric],['score-law-distribution-tbody',distributions,distributionMetric]]){
      const cells=nodes[name].children[i].children;const values=records.map(record=>record[key]);
      values.forEach((value,j)=>{assert.equal(cells[j+3].textContent,value.toFixed(6));assert.equal(cells[j+3].className.includes('best'),!row.campaign.startsWith('2026')&&value===Math.min(...values));});
    }
    assert.equal(nodes['score-law-distribution-tbody'].children[i].children[2].textContent,distributions[0].games);
  });
  states++;
}
console.log(JSON.stringify({ status: 'PASS', selector_states: states, tables_per_state: 4, method: 'minimal DOM fixture; no rendered browser' }));
