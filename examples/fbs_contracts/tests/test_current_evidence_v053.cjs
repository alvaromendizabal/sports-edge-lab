'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const view=require('../../../docs/fbs/current-evidence.js');
const data=JSON.parse(require('node:zlib').gunzipSync(require('node:fs').readFileSync(require('node:path').join(__dirname,'../../../docs/fbs/current-evidence-v053.json.gz'))));
test('current calendar has 67 exact games and all-source inventory has 2742',()=>{
 const rows=view.select(data);assert.equal(rows.length,67);assert.ok(rows.every(g=>g.kickoff_utc));
 assert.equal(view.select(data,{season:'all',period:'all'}).length,2742);
 assert.equal(view.select(data,{season:'2026',period:'tbd'}).length,81);
 assert.equal(view.select(data,{season:'2026',period:'previous_week'}).length,63);
 assert.equal(view.select(data,{season:'2026',period:'upcoming_week'}).length,70);
});
test('search never removes gaps by manufacturing a value',()=>{
 const gap=data.games.find(g=>g.season===2026&&!g.kickoff_utc),rows=view.select(data,{season:'2026',period:'all',search:gap.id});
 assert.equal(rows.length,1);assert.equal(rows[0].original.p_home,null);assert.equal(rows[0].calibrated.p_home,null);
});
test('CSV uses selected issue and clocks without rewriting original',()=>{
 const row=data.games.find(g=>g.original.p_home!==null),before=JSON.stringify(row);
 const original=view.csv([row],'original'),revised=view.csv([row],'calibrated'),historical=view.csv([row],'historical');
 assert.match(original,new RegExp(row.original.original_durable_observed_at.replaceAll('.','\\.')));
 assert.match(revised,new RegExp(row.calibrated.original_durable_observed_at.replaceAll('.','\\.')));
 assert.notEqual(original,revised);assert.match(historical,/"historical"/);assert.equal(JSON.stringify(row),before);
 assert.throws(()=>view.csv([row],'automatic'),/Unknown evidence layer/);
});
test('CSV protects spreadsheet formula input without replacing missing values with zero',()=>{
 const row=structuredClone(data.games.find(g=>g.original.p_home===null));row.home='=2+2';
 const csv=view.csv([row],'original');assert.match(csv,/'=2\+2/);assert.match(csv,/,"","","","","",/);
});
