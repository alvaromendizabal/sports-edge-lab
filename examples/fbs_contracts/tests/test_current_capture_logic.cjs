'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const {sameIdentity,indexRows,resultView} = require('../../../docs/fbs/current-capture.js');
const game = {id:'1',season:2026,home_id:'2',away_id:'3',home:'Home',away:'Away',kickoff_exact:true,
  kickoff:'2026-11-07T17:45:00Z',reported_kickoff:'2026-11-07T17:45:00Z',completed:false,
  home_score:null,away_score:null,cutoff:'2026-11-07T15:45:00Z',models:{fixed_equal_blend:{winner:{prediction:.52}}}};
const row = {...game,completed:true,home_score:26,away_score:23,observed_at:'2026-11-07T22:23:04Z'};
test('new results retain all immutable prediction and cutoff references',()=>{
 const next=resultView(game,row,'latest','old');
 assert.equal(next.home_margin,3);assert.equal(next.total_points,49);assert.equal(next.winner,'Home');
 assert.equal(next.newly_observed_final,true);assert.equal(next.result_snapshot,'latest');
 assert.equal(next.models,game.models);assert.equal(next.cutoff,game.cutoff);
 assert.equal(game.completed,false);assert.equal(game.home_score,null);
});
test('old snapshot remains available without overwriting prior scores',()=>{
 const old=resultView(game,row,'original','old');assert.equal(old.completed,false);assert.equal(old.result_observed_at,'old');
});
test('identity changes or swapped teams never rebind a prior prediction',()=>{
 for(const change of [{id:'9'},{home_id:'3',away_id:'2'},{kickoff:'2026-11-07T18:00:00Z'},{reported_kickoff:'2026-11-08T17:45:00Z'},{season:2025}]){
  assert.equal(sameIdentity(game,{...row,...change}),false);
  assert.equal(resultView(game,{...row,...change},'latest','old').completed,false);
 }
});
test('unchanged TBD placeholders are not kickoff revisions or exact times',()=>{
 const tbd={...game,kickoff_exact:false,kickoff:null}, observed={...row,kickoff_exact:false,kickoff:null,completed:false};
 assert.equal(sameIdentity(tbd,observed),true);
 const next=resultView(tbd,observed,'latest','old');assert.equal(next.kickoff,null);assert.equal(next.kickoff_exact,false);
 assert.equal(next.newly_observed_final,false);
 const final=resultView(tbd,{...observed,completed:true},'latest','old');
 assert.equal(final.completed,true);assert.equal(final.kickoff_exact,false);assert.equal(final.kickoff,null);
});
test('invalid final scores and duplicate official identities fail closed',()=>{
 for(const score of [null,NaN,-1,'26'])assert.equal(resultView(game,{...row,home_score:score},'latest','old').completed,false);
 assert.throws(()=>indexRows([row,row]),/Duplicate/);
});

test('separate prior snapshot and explicit newest-delta flags stay distinct',()=>{
 const prior=resultView(game,row,'prior','old');assert.equal(prior.result_snapshot,'prior');assert.equal(prior.newly_observed_final,true);
 const newest=resultView(game,{...row,newly_observed:false},'latest','old');assert.equal(newest.completed,true);assert.equal(newest.newly_observed_final,false);
 const addition=resultView(game,{...row,newly_observed:true},'latest','old');assert.equal(addition.newly_observed_final,true);assert.equal(addition.models,game.models);
 assert.equal(resultView(game,row,'unrecognized','old').result_snapshot,'original');
});

test('the intermediate late-Nov7 snapshot keeps its own scores, clock and delta',()=>{
 const prior=resultView(game,{...row,newly_observed:true},'nov7_late','old');
 assert.equal(prior.result_snapshot,'nov7_late');assert.equal(prior.result_observed_at,row.observed_at);
 assert.equal(prior.models,game.models);assert.equal(prior.newly_observed_final,true);
});

test('a verified TBD resolution creates a new empty forecast epoch without changing the old snapshot',()=>{
 const old={...game,kickoff_exact:false,kickoff:null,reported_kickoff:'2026-11-15T00:00:00Z',replay_p_home:.6};
 const resolved={...row,completed:false,kickoff:'2026-11-15T00:30:00Z',reported_kickoff:'2026-11-15T00:30:00Z',identity_status:'TBD_RESOLUTION_NEW_FIXTURE_EPOCH',owner_original_identity_status:'NEW_OBSERVED_FIXTURE_REVISION_OLD_PREDICTION_NOT_REBOUND'};
 const next=resultView(old,resolved,'latest','old');
 assert.equal(next.kickoff,resolved.kickoff);assert.equal(next.kickoff_exact,true);assert.equal(next.new_fixture_epoch,true);
 assert.deepEqual(next.models,{});assert.equal(next.replay_p_home,null);assert.equal(next.projection_status,'NEW_FIXTURE_EPOCH_PREDICTION_PENDING');
 assert.equal(old.kickoff,null);assert.equal(old.replay_p_home,.6);assert.equal(old.models,game.models);
 assert.equal(resultView(old,resolved,'original','old').kickoff,null);
 for(const change of [{home_id:'3',away_id:'2'},{id:'9'},{identity_status:'UNVERIFIED'},{kickoff:'invalid'}]){
  const rejected=resultView(old,{...resolved,...change},'latest','old');assert.equal(rejected.kickoff,null);assert.equal(rejected.new_fixture_epoch,undefined);
 }
});
