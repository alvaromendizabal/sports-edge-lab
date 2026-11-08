'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const R=require('../../../docs/fbs/ranking-research.js');
const row={season:2026,source_key:'ap',source_label:'AP',source_kind:'poll',request_status:'VERIFIED_CAPTURE',source_observed_at:'2026-11-08T22:12:00Z',records:0,editions:0,teams:null,publication_clock_status:'ORIGINAL_PUBLICATION_UNPROVED',admitted_feature_values:0,evaluated_feature_values:0,reason_code:'ORIGINAL_PUBLICATION_UNPROVED',next_action:'Verify original edition and availability'};
const data={rows:[row,{...row,season:2025},{...row,source_key:'elo',source_label:'Elo',source_kind:'rating',records:null,editions:null}]};
const game={id:'invented-1',season:2026,kickoff_exact:true,kickoff:'2026-11-14T20:00:00Z'};
const projection={available:true,record:{cutoff:'2026-11-14T19:00:00Z'},model:{winner:{prediction:.6,computed_at_utc:'2026-11-07T01:00:00Z'},margin:{prediction:3,computed_at_utc:'2026-11-07T01:01:00Z'}}};
test('a newer capture before a future cutoff never enters an older saved model',()=>{
 const before=JSON.stringify({game,projection,data}),r=R.gameStatus(game,projection,data);
 assert.equal(r.length,2);assert.equal(r[0].versus_computation.code,'CAPTURE_AT_OR_AFTER_REFERENCE');
 assert.equal(r[0].versus_cutoff.code,'CAPTURE_BEFORE_REFERENCE');
 assert.equal(r[0].included_in_selected_model,false);assert.equal(r[0].qualified_feature_values,0);
 assert.equal(r[0].reason_code,'NOT_INCLUDED_IN_SELECTED_SAVED_MODEL');
 assert.equal(JSON.stringify({game,projection,data}),before);
});
test('missing target clocks cannot be replaced by another targets computation',()=>{
 const p={...projection,model:{...projection.model,total:{prediction:45}}};
 assert.equal(R.gameStatus(game,p,data)[0].versus_computation.code,'CLOCK_EVIDENCE_MISSING');
 assert.equal(R.gameStatus(game,{available:false},data)[0].reason_code,'NO_SAVED_MODEL_FOR_THIS_GAME_AND_FAMILY');
 assert.equal(R.relation('2026-01-01T00:00:00Z','2026-01-01T00:00:00Z').code,'CAPTURE_AT_OR_AFTER_REFERENCE');
 assert.equal(R.relation('invalid','2026-01-01T00:00:00Z').code,'CLOCK_EVIDENCE_MISSING');
});
test('new fixture epochs and unresolved kickoffs remain independent admission gaps',()=>{
 assert.equal(R.gameStatus({...game,new_fixture_epoch:true},projection,data)[0].reason_code,'NEW_FIXTURE_EPOCH_REQUIRES_NEW_MODEL');
 assert.equal(R.gameStatus({...game,kickoff_exact:false},projection,data)[0].reason_code,'EXACT_KICKOFF_UNRESOLVED');
});
test('source filtering preserves missing counts instead of filling them with zero',()=>{
 assert.equal(R.rowsFor(data).length,3);assert.equal(R.rowsFor(data,'2026','rating').length,1);
 assert.equal(R.rowsFor(data,'2026','rating')[0].records,null);
 assert.equal(R.sourceSummary([row]).admitted_feature_values,0);
 assert.equal(R.sourceSummary([{...row,admitted_feature_values:null}]).admitted_feature_values,null);
});
test('coverage export is whitelist-only and escapes spreadsheet formulas',()=>{
 const text=R.csv([{...row,source_label:'=SUM(1,2)',private_recipe:'private',raw_rank:7,cloud_locator:'private-storage'}]);
 assert.match(text,/"'=SUM\(1,2\)"/);assert.doesNotMatch(text,/private_recipe|raw_rank|cloud_locator|private-storage/);
 assert.equal(text.split('\r\n').length,2);
});
test('the captured census does not invent missing historical rating counts',()=>{
 const census=require('../../../docs/fbs/ranking-research-v047.json'),p=R.presentation(census);
 assert.equal(p.rows.length,21);assert.equal(p.selection_history.length,6);
 assert.equal(R.sourceSummary(p.rows).verified_source_season_cells,13);
 const absent=p.rows.filter(r=>r.request_status==='NOT_CAPTURED_THIS_RUN');
 assert.equal(absent.length,8);assert.ok(absent.every(r=>r.records===null&&r.editions===null&&r.teams===null));
 assert.equal(p.request_count,9);assert.deepEqual(p.feature_counts,{admitted:0,evaluated:0,promoted:0});
});
