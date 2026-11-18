'use strict';
const { mutations } = require('./execution_status_invalid_fixtures.cjs');
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
  assert.equal(nodes.get('observed-release').textContent, 'R31');
  assert.equal(nodes.get('verified-release').textContent, 'R31');
  assert.equal(nodes.get('current-execution-panel').hidden, false);
  assert.match(nodes.get('current-execution-title').textContent, /R31 actual execution/);
  const currentFacts = nodes.get('current-work-facts').children.map(n => n.textContent).join(' ');
  assert.match(currentFacts, /1,284 reused · 0 fresh/);
  assert.match(currentFacts, /Requested workers \/ scientific peak 24 \/ 0/);
  assert.match(currentFacts, /Not run · source stage blocked dispatch/);
  assert.equal(nodes.get('preserved-fits').textContent, '11');
  assert.equal(nodes.get('bounded-acceptance-panel').hidden, false);
  assert.equal(nodes.get('bounded-fit-count').textContent, '36');
  assert.equal(nodes.get('bounded-overlap').textContent, '21');
  assert.match(nodes.get('bounded-cpu-facts').children.map(n=>n.textContent).join(' '), /180-second \/ 75% gate certified No/);
  assert.match(nodes.get('bounded-cpu-facts').children.map(n=>n.textContent).join(' '), /24 or 36 fitting kernels observed No/);
  assert.match(nodes.get('bounded-note').textContent, /21-kernel overlap.*does not establish 24 or 36/);
  assert.equal(nodes.get('stage-resumption-panel').hidden, false);
  assert.match(nodes.get('stage-restart-facts').children.map(n=>n.textContent).join(' '), /prior stages skipped 10/);
  assert.match(nodes.get('source-replay-facts').children.map(n=>n.textContent).join(' '), /Warm tasks reused \/ normalizer calls 6 \/ 0/);
  const costFacts = nodes.get('current-cost-facts').children.map(n => n.textContent).join(' ');
  assert.match(costFacts, /\$0\.42/);
  assert.doesNotMatch(costFacts, /\$0\.00/);
  assert.match(costFacts, /Budget exhaustion established No · verified estimate below guard/);
  assert.match(nodes.get('attempt-scope').textContent, /12 audited attempts · 10 distinct run identities/);
  assert.match(currentFacts, /822 \/ 36/);
  const source = run(JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R29_20261118.json')))).nodes;
  assert.equal(source.get('data-error').hidden, true);
  assert.equal(source.get('observed-release').textContent, 'R29');
  assert.match(source.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /Source chunks recorded 294/);
  const older = JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_20261118.json')));
  const prior = run(older).nodes;
  assert.equal(prior.get('data-error').hidden, true);
  assert.equal(prior.get('observed-release').textContent, 'R26');
  assert.match(prior.get('current-cost-facts').children.map(n => n.textContent).join(' '), /\$0\.32/);
  const recovery = run(JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R28_20261118.json')))).nodes;
  assert.equal(recovery.get('data-error').hidden, true);
  assert.equal(recovery.get('observed-release').textContent, 'R28');
  assert.match(recovery.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /50 \/ 50/);
  const price = run(JSON.parse(fs.readFileSync(path.join(__dirname, 'EXECUTION_STATUS_R27_20261118.json')))).nodes;
  assert.equal(price.get('data-error').hidden, true);
  assert.equal(price.get('observed-release').textContent, 'R27');
  assert.match(price.get('current-cost-facts').children.map(n => n.textContent).join(' '), /Unknown · no verified current rate/);
  assert.doesNotMatch(price.get('current-cost-facts').children.map(n => n.textContent).join(' '), /\$0\.00/);
  assert.equal(nodes.get('recovery-evidence-panel').hidden, false);
  assert.match(nodes.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /Historical target checkpoints authenticated 108/);
  assert.match(nodes.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /Displayed scoreboard completion 4 \/ 32/);
  assert.match(nodes.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /Authenticated committed responses 6/);
  assert.match(nodes.get('recovery-archive-facts').children.map(n => n.textContent).join(' '), /Additional authenticated pending capture 1/);
  assert.match(currentFacts, /Historical target checkpoint reuses 108/);
  assert.match(currentFacts, /Current-consumer target reuses 0/);
  assert.equal(nodes.get('next-preparation-state').textContent,
    `R32 · ${expected.next_preparation.status} · 0 owner executions`);
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
  for (const mutate of mutations) {
    const data = JSON.parse(JSON.stringify(expected)); mutate(data); const bad = run(data).nodes;
    assert.equal(bad.get('data-error').hidden, false); assert.equal(bad.get('report').hidden, true);
  }
  console.log(JSON.stringify({status:'PASS', filter_views:5, checked_cells:cells, exact_downloads:1,
    corrupt_evidence_rejections:mutations.length, current_partial_return_verified:true, new_fits:0, visual_browser_claim:false,
    next_preparation_status:expected.next_preparation.status,
    next_preparation_owner_executions:0,engineering_tests:expected.next_preparation.engineering_tests}));
})().catch(error => { console.error(error); process.exitCode = 1; });
