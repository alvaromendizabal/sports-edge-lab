/* Headless, dependency-free DOM harness for the self-contained Circa report. */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const data = html.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/);
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/);
assert(data && code, 'Missing embedded data or interactive script');
const parsed = JSON.parse(data[1]);
assert.equal(parsed.games.length, 136);
assert.equal(parsed.model_comparison.profiles.length, 23);

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      innerHTML: '', textContent: id === 'report-data' ? data[1] : '',
      value: '', disabled: false,
      classList: { toggle() {}, add() {}, remove() {} },
      querySelectorAll() { return []; }, addEventListener() {}, scrollIntoView() {},
    });
  }
  return elements.get(id);
}

const sandbox = vm.createContext({
  document: { getElementById: element, querySelectorAll() { return []; } },
  console, Intl, Date, Math, Number, Object, Array, String, JSON,
});
vm.runInContext(code[1], sandbox, { timeout: 2000 });
assert.match(element('ats-leaders').innerHTML, /tensorflow mlp/);
assert.match(element('card-leaders').innerHTML, /oof convex blend/);
assert.equal(element('model-choice').disabled, false, 'Circa card leader must be the default view');
assert.match(element('week-heading').textContent, /Week 8/);
assert.match(element('kpis').innerHTML, /23\.0 \/ 40/);
assert.match(element('kpis').innerHTML, /21–15–4/);
assert.match(element('kpis').innerHTML, /T-1,054/);
assert.equal(element('model-choice').value, parsed.model_comparison.by_card[0]);
assert.match(element('model-choice').innerHTML, /Circa #1T/);

for (const leader of parsed.model_comparison.by_card.slice(0, 4)) {
  vm.runInContext(`selectModel(${JSON.stringify(leader)})`, sandbox, { timeout: 2000 });
  assert.match(element('kpis').innerHTML, /23\.0 \/ 40/, leader);
  assert.equal(vm.runInContext('modelGames(1).filter(g=>g.top_five).length', sandbox), 5);
}

vm.runInContext('selectModel("tensorflow_mlp::football_support_control")', sandbox, { timeout: 2000 });
assert.equal(element('model-choice').disabled, false);
assert.match(element('kpis').innerHTML, /67–47–6/);
assert.match(element('kpis').innerHTML, /19\.0 \/ 40/);
assert.match(element('week-heading').textContent, /Week 8/);
assert.match(element('game-grid').innerHTML, /game/);
assert.equal(vm.runInContext('modelGames(1).filter(g=>g.top_five).length', sandbox), 5);

vm.runInContext('selectModel("torch_mlp::football_support_control")', sandbox, { timeout: 2000 });
assert.match(element('kpis').innerHTML, /63–51–6/);
vm.runInContext('selectModel("catboost::football_support_control")', sandbox, { timeout: 2000 });
assert.match(element('kpis').innerHTML, /23\.0 \/ 40/);

vm.runInContext('selectWeek(9)', sandbox, { timeout: 2000 });
assert.equal(element('model-choice').disabled, true);
assert.match(element('week-heading').textContent, /Week 9 · 6–4–0/);
assert.match(element('model-choice-hint').textContent, /original issues/);
console.log('PASS: Circa-first default, four tied card leaders, full-slate ATS comparator, 23 family selector, Week 9 original isolation');
