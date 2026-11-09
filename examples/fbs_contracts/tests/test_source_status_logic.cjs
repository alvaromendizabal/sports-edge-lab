'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const S=require('../../../docs/fbs/source-status.js'),G=require('../../../docs/fbs/game-center.js'),M=require('../../../docs/fbs/research-method.js');
const target={observed_at:'2026-11-08T23:57:41Z',quote_time:'2026-11-08T23:57:30Z',source_available_by_t120:true,source_available_by_t60:true};
const bound={provider:'DraftKings',id:'123',home:'Home',away:'Away',kickoff:'2026-11-11T00:00:00Z',identity_status:'EXACT_REGISTERED_NAMES_ORDERED_IDS_AND_KICKOFF',targets:{h2h:{...target},spreads:{...target},totals:{...target}}};
const unbound={...bound,id:null,identity_status:'NO_UNIQUE_EXACT_REGISTERED_NAME_AND_KICKOFF_BINDING'};
test('raw timing counts never become exact identity counts or qualified model output',()=>{
 const rows=[bound,unbound],before=JSON.stringify(rows),s=S.sourceSummary(rows);
 assert.deepEqual(s,{events:2,targets:6,exact_events:1,exact_targets:3,raw_t120:6,raw_t60:6,exact_t120:3,exact_t60:3,qualified_cover:0});assert.equal(JSON.stringify(rows),before);
});
test('provider and association filters preserve unmatched events without guessing game IDs',()=>{
 const data={events:[bound,unbound]};assert.equal(S.sourceRows(data).length,2);
 assert.equal(S.sourceRows(data,{binding:'exact'}).length,1);assert.equal(S.sourceRows(data,{binding:'unmatched'}).length,1);
 assert.equal(S.sourceRows(data,{provider:'Kalshi'}).length,0);assert.equal(S.sourceRows(data,{query:'123'}).length,1);
 assert.equal(S.sourceRows(data,{query:'away'}).length,2);
});
test('a game detail requires the exact current epoch and never rebinds a revised or TBD time',()=>{
 const data={events:[bound,unbound]},game={id:'123',kickoff_exact:true,kickoff:'2026-11-11T00:00:00Z'};
 assert.equal(S.forGame(data,game).length,1);assert.equal(S.forGame(data,{...game,kickoff:'2026-11-11T01:00:00Z'}).length,0);
 assert.equal(S.forGame(data,{...game,kickoff_exact:false}).length,0);assert.equal(S.forGame(data,{...game,id:'different'}).length,0);
});
test('metadata CSV has target clocks and no price, probability, recipe, or eligibility invention',()=>{
 const csv=S.csv([{...bound,home:'=unsafe',targets:{h2h:{...target,prediction:.8,price:1.2,private_recipe:'secret'}}},unbound]);
 assert.match(csv,/"'=unsafe"/);assert.match(csv,/source_available_by_t120/);assert.match(csv,/historical_model_input_admitted/);
 assert.doesNotMatch(csv,/prediction|price|private_recipe|secret|0\.8|1\.2/);assert.equal(csv.split('\r\n').length,5);
});
test('observation gaps are metadata counts, never fabricated negative or missing metrics',()=>{
 assert.equal(S.resultGap(685,683),2);assert.equal(S.resultGap(683,685),null);assert.equal(S.resultGap(null,683),null);
});
test('a Monday transition maps the newly previous week to the stored current cohort by exact dates',()=>{
 const selected=M.weekWindows('2026-11-09T08:00:00Z'),evaluated=M.weekWindows('2026-11-08T06:27:42Z');
 assert.deepEqual(G.comparisonRoute('2026','previous','latest',{selected,evaluated}),{study:'v045',cohort:'current_week'});
 assert.equal(G.comparisonRoute('2026','current','latest',{selected,evaluated}),null);
 assert.equal(G.comparisonRoute('2026','upcoming','latest',{selected,evaluated}),null);
});
test('Sunday before the Pacific boundary retains current cohort and rejects an unmatched future week',()=>{
 const selected=M.weekWindows('2026-11-09T07:59:59Z'),evaluated=M.weekWindows('2026-11-08T06:27:42Z');
 assert.deepEqual(G.comparisonRoute('2026','current','latest',{selected,evaluated}),{study:'v045',cohort:'current_week'});
 assert.equal(G.comparisonRoute('2026','upcoming','latest',{selected,evaluated}),null);
 const wrong={...selected.current,end_exclusive:'2026-11-10'};
 assert.equal(G.comparisonRoute('2026','current','latest',{selected:{current:wrong},evaluated}),null);
});
test('missing date evidence fails closed and cumulative seasons retain their separate route',()=>{
 assert.equal(G.comparisonRoute('2026','current','latest',{}),null);
 assert.deepEqual(G.comparisonRoute('2025','all','latest',{}),{study:'v045',cohort:'2025'});
 assert.equal(G.comparisonRoute('all','all','original',{}),null);
});
test('deferred module waits for the game view while readyState is already interactive',()=>{
 const vm=require('node:vm'),fs=require('node:fs');let callback;
 const context={window:{},document:{readyState:'interactive',addEventListener:(name,fn)=>{assert.equal(name,'DOMContentLoaded');callback=fn;}}};
 vm.runInNewContext(fs.readFileSync(require.resolve('../../../docs/fbs/source-status.js'),'utf8'),context);
 assert.equal(typeof callback,'function');assert.equal(typeof context.window.FBSSourceStatus.sourceRows,'function');
});
