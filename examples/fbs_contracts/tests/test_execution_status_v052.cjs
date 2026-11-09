'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {executionReadout}=require('../../../docs/fbs/forecast-access.js');
const report=require('../../../docs/fbs/execution-status-v052.json');

test('latest attempt shows actual measured timing and zero new work',()=>{
  const row=executionReadout(report),cards=Object.fromEntries(row.cards);
  assert.equal(row.heading,'V051 stopped before research');
  assert.equal(cards['Worker before packaging'],'4.12 s');
  assert.equal(cards['Launch observer overall'],'20.10 s');
  assert.equal(cards['New base fits'],'0');
  assert.equal(cards['New original issues'],'0');
  assert.equal(cards['Retained fitted / calibrated records'],'7850');
  assert.equal(cards['Retained original outlooks'],'108');
  assert.match(row.note,/overlap/);
  assert.match(row.note,/does not monitor a live process/);
});

test('unobserved execution counters never turn into zero',()=>{
  const row=executionReadout({owner_release:'Invented',new_base_fits:null,new_genuine_issues:undefined});
  assert.equal(row.heading,'Invented execution evidence');
  assert.ok(row.cards.every(([,value])=>value==='Not recorded'));
});

test('malformed durations and fractional counters are not display evidence',()=>{
  const row=executionReadout({timing:{worker_before_packaging_seconds:NaN,launch_observer_seconds:-1},
    new_base_fits:1.5,new_genuine_issues:Infinity,retained_work:{successful_total:-5}});
  assert.ok(row.cards.every(([,value])=>value==='Not recorded'));
});

test('one reached scientific phase prevents a stopped-before-research claim',()=>{
  const row=executionReadout({owner_release:'Invented',scientific_stages:{first:'NOT_REACHED',second:'COMPLETED'}});
  assert.equal(row.heading,'Invented execution evidence');
});
