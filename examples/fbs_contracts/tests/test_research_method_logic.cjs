'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const M=require('../../../docs/fbs/research-method.js');
test('weekly windows use the dated Pacific capture including the DST boundary',()=>{
 const w=M.weekWindows('2026-11-08T19:34:42Z');
 assert.equal(w.current.start,'2026-11-02');assert.equal(w.current.end_exclusive,'2026-11-09');
 assert.equal(w.upcoming.start,'2026-11-09');assert.equal(w.upcoming.end_exclusive,'2026-11-16');
 assert.equal(M.periodFor({kickoff_exact:true,kickoff:'2026-11-09T07:59:59Z'},w.current.anchor),'current');
 assert.equal(M.periodFor({kickoff_exact:true,kickoff:'2026-11-09T08:00:00Z'},w.current.anchor),'upcoming');
 assert.equal(M.weekWindows('2026-11-02T07:59:59Z').current.start,'2026-10-26');
 assert.equal(M.periodFor({kickoff_exact:false,kickoff:'2026-11-14T00:00:00Z'},w.current.anchor),'unresolved');
 assert.equal(M.weekWindows('invalid'),null);
});
test('forecast ages distinguish long range, late computation and absent clocks without issuance',()=>{
 const game={kickoff_exact:true,kickoff:'2026-11-21T20:00:00Z'};
 const value={record:{cutoff:'2026-11-21T19:00:00Z'},model:{winner:{prediction:.6,computed_at_utc:'2026-11-07T20:00:00Z'}}};
 const c=M.clockReport(game,value,'2026-11-08T20:00:00Z');
 assert.equal(c.age_hours,24);assert.equal(c.horizon_hours,336);assert.equal(c.status,'LONG_RANGE_SNAPSHOT');assert.equal(c.forecast_issued,false);
 assert.equal(M.clockReport(game,value,'2026-11-06T20:00:00Z').status,'COMPUTED_AFTER_CAPTURE');
 assert.equal(M.clockReport(game,{model:{winner:{prediction:.6}}},'2026-11-08T20:00:00Z').status,'CLOCK_EVIDENCE_MISSING');
 assert.equal(M.clockReport(game,{model:{winner:{prediction:.6,computed_at_utc:game.kickoff}}},'2026-11-22T20:00:00Z').status,'AT_OR_AFTER_KICKOFF');
 assert.equal(M.clockReport({...game,kickoff_exact:false},value,'2026-11-08T20:00:00Z').status,'CLOCK_EVIDENCE_MISSING');
});
