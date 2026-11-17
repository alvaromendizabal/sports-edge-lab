'use strict';
// Actual page script, simulated DOM: this is not a visual-browser result.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const html = fs.readFileSync(path.resolve(__dirname, '../../docs/ncaa/execution.html'), 'utf8');
const expected = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../docs/ncaa/execution_status.json')));
const script = html.match(/<script>\n([\s\S]*?)<\/script>/)[1];
function element(tag = '') { return { tag, textContent: '', value: '', hidden: false, children: [], attributes: {}, style: {}, listeners: {},
  appendChild(child) { this.children.push(child); }, replaceChildren(...children) { this.children = children; },
  setAttribute(name, value) { this.attributes[name] = value; }, addEventListener(name, handler) { this.listeners[name] = handler; }, click() {} }; }
function run(data) {
  const nodes = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(match => [match[1], element()]));
  nodes.get('execution-data').textContent = JSON.stringify(data); nodes.get('attempt-filter').value = 'all';
  nodes.get('data-error').hidden = true;
  let downloaded;
  vm.runInNewContext(script, { document: {getElementById: id => nodes.get(id), createElement: element}, Blob,
    URL: {createObjectURL(blob) { downloaded = blob; return 'blob:fixture'; }, revokeObjectURL() {}}, setTimeout() {} });
  return { nodes, download: () => downloaded };
}
(async () => {
  const ui = run(expected), nodes = ui.nodes; let cells = 0;
  assert.equal(nodes.get('observed-release').textContent, 'R25');
  assert.equal(nodes.get('verified-release').textContent, 'R24');
  assert.equal(nodes.get('preserved-fits').textContent, '11');
  for (const filter of ['all', 'RESEARCH', 'BEFORE_FIT', 'unpublished']) {
    nodes.get('attempt-filter').value = filter; nodes.get('attempt-filter').listeners.change();
    const rows = expected.attempts.filter(r => filter === 'all' || (filter === 'unpublished' ? !r.return_published : r.phase === filter));
    const actual = nodes.get('attempt-rows').children;
    assert.equal(actual.length, rows.length);
    for (let i = 0; i < rows.length; i++) {
      assert.equal(actual[i].children[0].textContent, rows[i].label);
      assert.equal(actual[i].children[1].textContent, rows[i].failure_label);
      assert.equal(actual[i].children[2].textContent, rows[i].new_target_fits === null ? 'Unobserved' : String(rows[i].new_target_fits));
      assert.equal(actual[i].children[3].textContent, rows[i].historical_checkpoint_reuses === null ? 'Unobserved' : String(rows[i].historical_checkpoint_reuses));
      assert.equal(actual[i].children[6].textContent, rows[i].note); cells += 5;
    }
  }
  nodes.get('download-report').listeners.click();
  assert.deepEqual(JSON.parse(await ui.download().text()), expected);
  for (const mutate of [d => {d.publication.new_fits = 1;}, d => {d.latest_verified_return.integrity = 'UNVERIFIED';},
    d => {d.science_contract.test_selection_weight = .1;}, d => {d.throughput.newer_12_to_24_core_science_proven = true;}]) {
    const data = JSON.parse(JSON.stringify(expected)); mutate(data); const bad = run(data).nodes;
    assert.equal(bad.get('data-error').hidden, false); assert.equal(bad.get('report').hidden, true);
  }
  console.log(JSON.stringify({status:'PASS', filter_views:4, checked_cells:cells, exact_downloads:1,
    corrupt_evidence_rejections:4, new_fits:0, visual_browser_claim:false}));
})().catch(error => { console.error(error); process.exitCode = 1; });
