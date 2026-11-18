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
  assert.equal(nodes.get('observed-release').textContent, 'R28');
  assert.equal(nodes.get('verified-release').textContent, 'R28');
  assert.equal(nodes.get('current-execution-panel').hidden, false);
  assert.match(nodes.get('current-execution-title').textContent, /R28 actual execution/);
  const currentFacts = nodes.get('current-work-facts').children.map(n => n.textContent).join(' ');
  assert.match(currentFacts, /1,102 reused · 0 fresh/);
  assert.match(currentFacts, /Requested workers \/ scientific peak 24 \/ 0/);
  assert.match(currentFacts, /Not run · no eligible work/);
  assert.equal(nodes.get('preserved-fits').textContent, '11');
  const costFacts = nodes.get('current-cost-facts').children.map(n => n.textContent).join(' ');
  assert.match(costFacts, /\$0\.15/);
  assert.doesNotMatch(costFacts, /\$0\.00/);
  assert.match(costFacts, /Budget exhaustion established No · price verification succeeded/);
  assert.match(nodes.get('attempt-scope').textContent, /9 audited attempts · 7 distinct run identities/);
  assert.match(currentFacts, /83 \/ 3/);
  const older = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_20261118.json')));
  const prior = run(older).nodes;
  assert.equal(prior.get('data-error').hidden, true);
  assert.equal(prior.get('observed-release').textContent, 'R26');
  assert.match(prior.get('current-cost-facts').children.map(n => n.textContent).join(' '), /\$0\.32/);
  const price = run(JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R27_20261118.json')))).nodes;
  assert.equal(price.get('data-error').hidden, true);
  assert.equal(price.get('observed-release').textContent, 'R27');
  assert.match(price.get('current-cost-facts').children.map(n => n.textContent).join(' '), /Unknown · no verified current rate/);
  assert.doesNotMatch(price.get('current-cost-facts').children.map(n => n.textContent).join(' '), /\$0\.00/);
  assert.equal(nodes.get('recovery-evidence-panel').hidden, false);
  assert.match(nodes.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /50 \/ 50/);
  assert.equal(nodes.get('next-preparation-state').textContent,
    `R29 · ${expected.next_preparation.status} · 0 owner executions`);
  assert.equal(nodes.get('preparation-stages').children.length, 4);
  if (expected.next_preparation.status === 'PREPARED_VERIFIED') {
    assert.ok(nodes.get('preparation-note').textContent.includes(
      `${expected.next_preparation.engineering_tests.toLocaleString('en-US')} engineering checks passed`));
    assert.match(nodes.get('preparation-note').textContent, /not owner fits or a scientific occupancy pass/);
  }
  for (const filter of ['all', 'RESEARCH', 'BEFORE_FIT', 'unpublished', 'published']) {
    nodes.get('attempt-filter').value = filter; nodes.get('attempt-filter').listeners.change();
    const rows = expected.attempts.filter(r => filter === 'all' || (filter === 'unpublished' ? !r.return_published : filter === 'published' ? r.return_published : r.phase === filter));
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
    d => {d.science_contract.test_selection_weight = .1;}, d => {d.throughput.newer_12_to_24_core_science_proven = true;},
    d => {d.current_execution.new_target_fits = 1;}, d => {d.current_execution.scientific_gate_executed = true;},
    d => {d.latest_observed_attempt.return_published = false;}, d => {d.current_execution.cost_basis = 'INVOICE';},
    d => {d.current_execution.estimated_instance_wall_cost_usd = 0;}, d => {d.current_execution.estimated_instance_wall_cost_usd = 200;}, d => {d.current_execution.deferral.budget_exhaustion_proven = true;}, d => {d.current_execution.deferral.root_cause = 'COMPUTE_BUDGET_SPENT';}, d => {d.current_execution.deferral.wait_budget_seconds = 0;}, d => {d.current_execution.cache_reads = 0;}, d => {d.current_execution.pressure_wait_seconds = 0;}, d => {d.audit_scope.audited_attempts = 7;}, d => {d.next_preparation.owner_executions = 1;}, d => {d.recovery_evidence.predecessor_recompression_calls = 1;}, d => {d.recovery_evidence.terminal_pressure_reasons = ['MEMORY_PRESSURE'];}, d => {d.next_preparation.engineering_evidence_sha256 = 'unverified';}]) {
    const data = JSON.parse(JSON.stringify(expected)); mutate(data); const bad = run(data).nodes;
    assert.equal(bad.get('data-error').hidden, false); assert.equal(bad.get('report').hidden, true);
  }
  console.log(JSON.stringify({status:'PASS', filter_views:5, checked_cells:cells, exact_downloads:1,
    corrupt_evidence_rejections:20, current_partial_return_verified:true, new_fits:0, visual_browser_claim:false,
    next_preparation_status:expected.next_preparation.status,
    next_preparation_owner_executions:0,engineering_tests:expected.next_preparation.engineering_tests}));
})().catch(error => { console.error(error); process.exitCode = 1; });
