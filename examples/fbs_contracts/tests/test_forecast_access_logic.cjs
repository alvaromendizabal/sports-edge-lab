'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const A=require('../../../docs/fbs/forecast-access.js'),F=require('../../../docs/fbs/forward-outlooks.js');
const game={id:'invented',season:2026,home_id:'home',away_id:'away',home:'Home',away:'Away',kickoff:'2026-11-02T01:00:00Z',kickoff_exact:true,completed:false};
const record={id:game.id,season:2026,home_id:game.home_id,away_id:game.away_id,kickoff:game.kickoff,original_issue_verified:true,horizon:'CURRENT_ORIGIN_OUTLOOK',information_cutoff_utc:'2026-10-28T01:00:00Z',computed_at_utc:'2026-10-28T02:00:00Z',issued_at_utc:'2026-10-28T03:00:00Z',targets:{winner:{available:true},margin:{available:true},total:{available:true}},interval_status:'SAVED_MODEL_INTERVALS_CALIBRATION_UNPROVED',distribution_status:'JOINT_SCORE_COHERENCE_CHECKED'};
test('horizon arithmetic uses exact UTC elapsed time across Pacific DST',()=>{
 const result=A.deadlines(game,'2026-10-31T01:00:00Z');
 assert.deepEqual(result.map(x=>x.deadline_utc),['2026-11-01T01:00:00.000Z','2026-11-01T23:00:00.000Z','2026-11-02T00:00:00.000Z']);
 assert.ok(result.every(x=>x.status==='FUTURE_DEADLINE_AT_OBSERVATION'&&!x.qualified_issue));
 assert.equal(A.deadlines(game,'2026-11-01T01:00:00Z')[0].status,'DEADLINE_REACHED_AT_OBSERVATION');
 assert.equal(A.deadlines(game,'2026-11-01T23:30:00Z').filter(x=>x.status==='DEADLINE_REACHED_AT_OBSERVATION').length,2);
});
test('TBD fixtures and missing observation clocks never get fabricated due states',()=>{
 for(const changed of [{kickoff_exact:false},{kickoff:null},{kickoff:'invalid'}])assert.ok(A.deadlines({...game,...changed},'2026-11-01T01:00:00Z').every(x=>x.deadline_utc===null&&x.status==='EXACT_KICKOFF_UNRESOLVED'));
 assert.ok(A.deadlines(game,null).every(x=>x.status==='OBSERVATION_CLOCK_UNAVAILABLE'&&!x.qualified_issue));
});
test('saved intervals and coherent scores do not imply calibration, horizon issue or exact-line output',()=>{
 const row=F.coverage(game,{rows:[record]});assert.deepEqual(A.readiness(row),{winner:true,margin:true,total:true,saved_intervals:true,coherent_scores:true,empirical_calibration:false,close_horizon:false,cover:false});
 const mismatch=F.coverage({...game,home_id:'changed'},{rows:[record]});assert.equal(A.readiness(mismatch).saved_intervals,false);assert.equal(A.readiness(mismatch).coherent_scores,false);
});
test('every new gap filter uses the same remaining fixture population',()=>{
 const rows=F.inventory([game,{...game,id:'tbd',kickoff_exact:false,kickoff:null}],{rows:[record]});
 for(const target of ['saved_intervals','coherent_scores'])assert.deepEqual(F.select(rows,{scope:'all',target}).map(x=>x.id),['tbd']);
 for(const target of ['empirical_calibration','close_horizon','cover'])assert.equal(F.select(rows,{scope:'all',target}).length,2);
 const s=A.summary(rows);assert.equal(s.games,2);assert.equal(s.saved_intervals,1);assert.equal(s.empirical_calibration,0);
});
test('timing CSV retains all three horizons per fixture and explicit null deadlines',()=>{
 const rows=F.inventory([game,{...game,id:'tbd',kickoff:null,kickoff_exact:false}],{rows:[record]});
 const csv=A.csv(rows,'2026-10-31T01:00:00Z');assert.equal(csv.split('\r\n').length,7);assert.equal((csv.match(/EXACT_KICKOFF_UNRESOLVED/g)||[]).length,3);assert.doesNotMatch(csv,/prediction_value|undefined|NaN|private_recipe/);
});
