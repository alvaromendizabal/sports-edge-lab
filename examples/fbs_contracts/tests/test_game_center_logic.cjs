'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const G=require('../../../docs/fbs/game-center.js'),A=require('../../../docs/fbs/coverage.js'),D=require('../../../docs/fbs/diagnostics.js');
const T=require('../../../docs/fbs/three-season.json'),C=require('../../../docs/fbs/catboost-study.json'),X=require('../../../docs/fbs/current-capture.json');
test('current week is first without discarding or mutating any fixture',()=>{
 const original=T.rows.filter(r=>r.season===2026),ids=original.map(r=>r.id),sorted=G.orderGames(original);
 assert.equal(sorted.length,888);assert.equal(new Set(sorted.map(r=>r.id)).size,888);
 assert.ok(sorted.slice(0,63).every(r=>r.period==='current'));
 assert.ok(sorted.slice(63,119).every(r=>r.period==='previous'));
 assert.deepEqual(original.map(r=>r.id),ids);
});
test('kickoff orders preserve TBD instead of substituting the raw placeholder',()=>{
 const original=T.rows.filter(r=>r.season===2026);
 for(const order of ['kickoff_asc','kickoff_desc']){
  const rows=G.orderGames(original,order);assert.ok(rows.slice(-98).every(r=>!r.kickoff_exact));
  const dates=rows.slice(0,-98).map(r=>Date.parse(r.kickoff));
  assert.ok(dates.every((v,i)=>i===0||(order==='kickoff_asc'?v>=dates[i-1]:v<=dates[i-1])));
 }
});
test('interval presentation preserves the original values and rejects invalid bounds',()=>{
 const bounds=[-5.14,12.75];const out=G.intervals({model:{margin:{interval80:bounds,interval95:[-10,20]}}},'margin');
 assert.deepEqual(out.interval80,bounds);assert.notEqual(out.interval80,bounds);
 for(const bad of [null,[],[1],[2,1],['1',2],[1,Infinity]])assert.equal(G.interval(bad),null);
 assert.deepEqual(G.intervals({margin:3,total:45},'margin'),{interval80:null,interval95:null});
});
test('computation clocks remain distinct from reconstructed cutoff and issuance',()=>{
 const p={record:{cutoff:'2026-11-01T15:00:00Z'},model:{winner:{computed_at_utc:'2026-11-07T01:00:00Z'},margin:{computed_at_utc:'2026-11-07T02:00:00Z'}}};
 assert.deepEqual(G.chronology(p),{cutoff:'2026-11-01T15:00:00Z',computed_first:'2026-11-07T01:00:00Z',computed_last:'2026-11-07T02:00:00Z'});
 assert.deepEqual(G.chronology({}),{cutoff:null,computed_first:null,computed_last:null});
});
test('all-family accounting retains the actual partial CatBoost target gap',()=>{
 const records=new Map(C.rows.map(r=>[r.id,r]));
 const project=g=>{const model=records.get(g.id)?.models.v040_catboost;return {p:model?.winner?.prediction,margin:model?.margin?.prediction,total:model?.total?.prediction,model};};
 const [r]=G.familyCoverage(T.rows.filter(g=>g.season===2026),[{id:'v040_catboost',label:'CatBoost'}],project,A);
 assert.deepEqual([r.games,r.winner,r.margin,r.total,r.complete,r.partial,r.missing,r.cover],[888,787,790,790,787,3,98,0]);
});
test('family completeness respects winner-only and points-only target scopes',()=>{
 const rows=[{p:.6},{margin:2,total:45},{}];
 const results=G.familyCoverage(rows,[{id:'logistic'},{id:'linear'}],r=>r,A);
 assert.deepEqual(results.map(r=>[r.complete,r.partial,r.missing]),[[1,0,2],[1,0,2]]);
});
test('recorded paired metrics expose the exact smaller common cohort without rescoring',()=>{
 const rows=X.metrics['2026'].filter(r=>r.target==='winner'),cat=rows.find(r=>r.family==='v040_catboost'),base=rows.find(r=>r.family==='v038_fixed_equal_blend');
 const before=JSON.stringify(cat);assert.equal(D.metricDelta(cat,base,'log_loss').value,null);
 const d=D.pairedMetricDelta(cat,base,'log_loss');
 assert.equal(d.games,644);assert.equal(d.cohort,cat.reference_common_game_ids_sha256);
 assert.equal(d.value,cat.paired_model_metrics.log_loss-cat.paired_reference_metrics.log_loss);
 assert.equal(base.games,647);assert.equal(JSON.stringify(cat),before);
});
test('paired comparison rejects wrong baseline, target, family, count and cohort',()=>{
 const rows=X.metrics['2026'].filter(r=>r.target==='winner'),cat=rows.find(r=>r.family==='v040_catboost'),base=rows.find(r=>r.family==='v038_fixed_equal_blend');
 assert.equal(D.pairedMetricDelta(cat,{...base,family:'another'},'log_loss').value,null);
 for(const change of [{family:'another'},{target:'total'},{reference_common_games:647},{reference_common_game_ids_sha256:'different'},{paired_reference_metrics:null}])
  assert.equal(D.pairedMetricDelta({...cat,...change},base,'log_loss').value,null);
 assert.equal(D.pairedMetricDelta({...cat,paired_reference_metrics:{...cat.paired_reference_metrics,exact_game_ids_sha256:'different'}},base,'log_loss').value,null);
});
