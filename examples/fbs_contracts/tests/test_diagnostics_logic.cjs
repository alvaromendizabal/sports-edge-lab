'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const D = require('../../../docs/fbs/diagnostics.js');

test('a score center needs both point targets and preserves negative model evidence', () => {
  assert.deepEqual(D.scoreCenters(-6, 50), {home:22, away:28, negative:false});
  assert.deepEqual(D.scoreCenters(80, 20), {home:50, away:-30, negative:true});
  for (const missing of [null, undefined, NaN, Infinity, '50']) assert.equal(D.scoreCenters(3, missing), null);
});
test('unobserved games never acquire errors or a winner verdict', () => {
  assert.equal(D.observedErrors({completed:false,home_score:0,away_score:0},{p:.8,margin:4,total:40}),null);
  assert.equal(D.observedErrors({completed:true,home_score:null,away_score:7},{p:.8,margin:4,total:40}),null);
});
test('signed display errors preserve direction and missing targets', () => {
  const g={completed:true,home_score:21,away_score:28};
  assert.deepEqual(D.observedErrors(g,{p:.2,margin:-4,total:44}),{winner_correct:true,margin_error:3,total_error:-5});
  assert.deepEqual(D.observedErrors(g,{margin:0}),{winner_correct:null,margin_error:7,total_error:null});
  assert.equal(D.observedErrors({...g,home_score:28},{p:.8}).winner_correct,null);
});
test('equal sample sizes alone do not admit a model metric comparison', () => {
  const base={target:'winner',games:20,exact_game_ids_sha256:'cohort-a',log_loss:.6};
  assert.equal(D.metricDelta({...base,exact_game_ids_sha256:'cohort-b'},base,'log_loss').value,null);
  assert.equal(D.metricDelta({...base,games:19},base,'log_loss').value,null);
  assert.equal(D.metricDelta({...base,target:'margin'},base,'log_loss').value,null);
  assert.equal(D.metricDelta({...base,exact_game_ids_sha256:null},base,'log_loss').value,null);
});
test('recorded metric differences preserve precision and nulls', () => {
  const base={target:'winner',games:629,exact_game_ids_sha256:'cohort-a',log_loss:0.5320529911487542};
  const row={...base,log_loss:0.5392646226339349};
  assert.equal(D.metricDelta(row,base,'log_loss').value,row.log_loss-base.log_loss);
  assert.equal(D.metricDelta({...row,log_loss:null},base,'log_loss').value,null);
});
test('target coverage does not turn one point estimate into winner or cover coverage', () => {
  const values=[{p:.6,margin:7,total:50},{margin:8,total:52},{p:.4},{}];
  assert.deepEqual(D.targetCoverage(values,x=>x),{games:4,winner:2,margin:2,total:2,intervals:0,cover:0});
});
test('residual intervals do not create an exact-line cover probability', () => {
  const model={margin:{prediction:4,interval80:[-15,22],interval95:[-30,40],cover_probability:.7,cover_status:'NO_AUTHENTICATED_CUTOFF_COMPATIBLE_HOME_SPREAD'}};
  assert.deepEqual(D.targetCoverage([{margin:4,model}],x=>x),{games:1,winner:0,margin:1,total:0,intervals:1,cover:0});
});
test('CSV preserves full-precision metrics, nullable values and formula-safe text', () => {
  const source=[{model:'=1+1',metric:0.5392646226339349,missing:null,bins:[{n:7}]}];
  const text=D.csv(source,['model','metric','missing','bins']);
  assert.match(text,/"'=1\+1"/);assert.match(text,/0\.5392646226339349/);assert.match(text,/,"",/);
  assert.match(text,/\[\{""n"":7\}\]/);
});
