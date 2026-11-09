'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const F=require('../../../docs/fbs/forward-outlooks.js');
const game={id:'invented-1',season:2026,home_id:'h',away_id:'a',home:'Home',away:'Away',kickoff:'2026-11-15T01:00:00Z',kickoff_exact:true,completed:false,period:'upcoming'};
const record={id:game.id,season:2026,home_id:'h',away_id:'a',kickoff:game.kickoff,original_issue_verified:true,horizon:'CURRENT_ORIGIN_OUTLOOK',information_cutoff_utc:'2026-11-09T01:00:00Z',computed_at_utc:'2026-11-09T02:00:00Z',issued_at_utc:'2026-11-09T02:01:00Z',targets:{winner:{available:true},margin:{available:true},total:{available:true}},interval_status:'SAVED_NOT_EMPIRICALLY_CALIBRATED',distribution_status:'JOINT_SCORE_DISTRIBUTION_SAVED'};
test('original issue requires exact ordered identity, original clocks and a declared horizon',()=>{
 assert.equal(F.coverage(game,{rows:[record]}).original_issue_verified,true);
 for(const change of [{home_id:'a',away_id:'h'},{kickoff:'2026-11-15T02:00:00Z'},{home_id:null},{season:2025}]){
  const r=F.coverage(game,{rows:[{...record,...change}]});assert.equal(r.original_issue_verified,false);assert.equal(r.reason,'CURRENT_OUTLOOK_FIXTURE_EPOCH_MISMATCH');
 }
 for(const change of [{information_cutoff_utc:'2026-11-09T03:00:00Z'},{computed_at_utc:null},{issued_at_utc:game.kickoff},{issued_at_utc:'2026-11-09T01:30:00Z'},{original_issue_verified:false},{horizon:'T60'}])assert.equal(F.coverage(game,{rows:[{...record,...change}]}).original_issue_verified,false);
});
test('duplicate identities never select a convenient row',()=>{
 const r=F.coverage(game,{rows:[record,{...record}]});assert.equal(r.reason,'AMBIGUOUS_CURRENT_OUTLOOK_IDENTITY');assert.equal(r.original_issue_verified,false);
});
test('all unplayed fixtures survive missing models and unresolved kickoff',()=>{
 const fixtures=[game,{...game,id:'invented-2',kickoff:null,kickoff_exact:false},{...game,id:'invented-3'},{...game,id:'invented-final',completed:true}];
 const rows=F.inventory(fixtures,{rows:[record]}),s=F.summarize(rows);assert.equal(rows.length,3);assert.deepEqual(s.targets,{winner:1,margin:1,total:1});assert.equal(s.issued,1);assert.equal(s.unresolved,1);assert.equal(s.qualified_cover,0);assert.equal(s.close_horizon_games,0);
 assert.equal(rows[1].targets.winner,'EXACT_KICKOFF_UNRESOLVED');assert.equal(rows[2].targets.winner,'CURRENT_OUTLOOK_NOT_RECORDED');
});
test('partial target coverage is never promoted to a complete family or fabricated cover',()=>{
 const r=F.coverage(game,{rows:[{...record,targets:{winner:{available:true},margin:{available:true},total:{available:false,reason:'SAVED_STATE_MISSING'}}}]});
 assert.equal(r.status,'PARTIAL_CURRENT_ORIGIN_OUTLOOK');assert.equal(r.targets.total,'SAVED_STATE_MISSING');assert.equal(r.targets.cover,'NO_QUALIFIED_EXACT_LINE_DISTRIBUTION');assert.equal(F.summarize([r]).complete,0);
});
test('scope and gap selectors retain exact denominators',()=>{
 const rows=F.inventory([game,{...game,id:'other',period:'other'},{...game,id:'tbd',kickoff:null,kickoff_exact:false,period:'unresolved'}],{rows:[record]});
 assert.equal(F.select(rows).length,1);assert.equal(F.select(rows,{scope:'all'}).length,3);assert.equal(F.select(rows,{scope:'exact'}).length,2);assert.equal(F.select(rows,{scope:'all',target:'winner'}).length,2);assert.equal(F.select(rows,{scope:'all',target:'cover'}).length,3);assert.equal(F.select(rows,{scope:'all',status:'missing'}).length,2);
});
test('metadata export preserves absent times and omits numeric forecasts',()=>{
 const rows=F.inventory([game,{...game,id:'tbd',kickoff:null,kickoff_exact:false}],{rows:[record]});const data=F.csv(rows);
 assert.equal(data.split('\r\n').length,3);assert.match(data,/original_issue_verified/);assert.match(data,/EXACT_KICKOFF_UNRESOLVED/);assert.doesNotMatch(data,/NaN|undefined|p_home|prediction_value/);
});
