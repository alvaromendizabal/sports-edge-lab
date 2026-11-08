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
test('weekly inventories fit one page while full seasons stay bounded',()=>{
 assert.equal(G.pageSize('2026','current'),63);assert.equal(G.pageSize('2026','previous'),63);
 for(const scope of [['2026','all'],['2024','all'],['all','all'],['2025','current']])assert.equal(G.pageSize(...scope),30);
});
test('period result and target counts retain missing outputs without excluding fixtures',()=>{
 const rows=[{completed:true,p:.7,margin:3,total:50},{completed:false,margin:2,total:42},{completed:false}];
 assert.deepEqual(G.periodSummary(rows,r=>r,'v040_catboost',A),{games:3,completed:1,without_final:2,winner:1,margin:2,total:2,cover:0,complete:1,partial:1,missing:1});
});
test('period comparison follows the selected dated snapshot without inventing cumulative original scores',()=>{
 assert.deepEqual(G.comparisonRoute('2026','current','latest'),{study:'v045',cohort:'current_week'});
 assert.deepEqual(G.comparisonRoute('2026','previous','nov7_late'),{study:'v043',cohort:'previous_week'});
 assert.deepEqual(G.comparisonRoute('2025','all','prior'),{study:'v042',cohort:'2025'});
 assert.deepEqual(G.comparisonRoute('2026','current','original'),{study:'v041',cohort:'current_week'});
 assert.deepEqual(G.comparisonRoute('2026','current','nov7_evening'),{study:'v044',cohort:'current_week'});
 assert.equal(G.comparisonRoute('all','all','original'),null);
});
test('saved output timing uses precise original clocks and treats the cutoff boundary as late',()=>{
 const make=computed=>({p:.6,record:{cutoff:'2026-11-08T01:00:00.000001Z'},model:{winner:{computed_at_utc:computed}}});
 assert.equal(G.timing(make('2026-11-08T01:00:00.000000Z')).status,'before');
 assert.equal(G.timing(make('2026-11-08T01:00:00.000001Z')).status,'at_or_after');
 assert.equal(G.timing(make('2026-11-08T01:00:00.000002Z')).status,'at_or_after');
});
test('missing, malformed or conflicting clocks remain unverified instead of implying availability',()=>{
 const value={p:.7,record:{cutoff:'2026-11-08T02:00:00Z'},model:{winner:{computed_at_utc:'2026-11-08T01:00:00Z',computed_before_cutoff:false}}};
 assert.equal(G.timing(value).status,'unverified');
 for(const clock of [null,'invalid','2026-02-30T01:00:00Z','2026-11-08T01:00:00','2026-11-08T01:00:00.1234567890Z'])assert.equal(G.timing({...value,model:{winner:{computed_at_utc:clock}}}).status,'unverified');
 assert.equal(G.timing({p:.6}).status,'unverified');
 assert.equal(G.timing({}).status,'none');
});
test('mixed targets are accounted individually and missing family targets are not counted as clocks',()=>{
 const value={margin:2,total:45,record:{cutoff:'2026-11-08T02:00:00Z'},model:{winner:{computed_at_utc:'2026-11-09T00:00:00Z'},margin:{computed_at_utc:'2026-11-08T01:00:00Z'},total:{computed_at_utc:'2026-11-08T03:00:00Z'}}};
 const result=G.timing(value);assert.equal(result.status,'at_or_after');assert.equal(result.saved,2);assert.deepEqual(result.counts,{before:1,at_or_after:1,unverified:0});
 assert.equal(G.timing({...value,model:{...value.model,total:{}}}).status,'unverified');
 assert.deepEqual(G.timingSummary([value,{p:.7},{}],v=>v),{games:3,before:0,at_or_after:1,unverified:1,none:1});
});
