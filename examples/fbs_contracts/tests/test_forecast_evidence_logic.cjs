'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const api=require('../../../docs/fbs/forecast-evidence.js');
const sample={scopes:{baseline:{rows:[
 {period:'2026',target:'winner',family:'v038/fixed_equal_blend',games:685,metrics:{log_loss:.52},exact_game_ids_sha256:'own-a'},
 {period:'2026',target:'winner',family:'partial',games:682,metrics:{log_loss:.51},exact_game_ids_sha256:'own-b',paired_control:{exact_match:true,games:682,model_metrics:{log_loss:.51},reference_metrics:{log_loss:.53},exact_game_ids_sha256:'pair-b'}},
 {period:'2025',target:'winner',family:'old',games:934,metrics:{log_loss:.5}}
 ]},four_epoch:{rows:[]}}};
test('A missing metric is unavailable while genuine zero stays zero',()=>{assert.equal(api.value({},'brier'),null);assert.equal(api.value({brier:0},'brier'),0);assert.equal(api.value({brier:'0'},'brier'),null);assert.equal(api.value({brier:NaN},'brier'),null);});
test('Own family cohorts retain target, period and distinct denominators',()=>{const rows=api.selectRows(sample);assert.deepEqual(rows.map(r=>r.games),[685,682]);assert.equal(api.scoredGames(sample),685);assert.equal(api.selectRows(sample,{target:'cover'}).length,0);});
test('Only an explicitly authenticated matched cohort admits a paired control',()=>{const rows=api.selectRows(sample,{comparison:'matched'});assert.equal(rows.length,1);assert.equal(rows[0].games,682);assert.equal(rows[0].exact_game_ids_sha256,'pair-b');assert.equal(rows[0].control_metrics.log_loss,.53);assert.equal(api.selectRows(sample,{scope:'four_epoch'}).length,0);});
test('Clock parity follows exact boundaries rather than moving relative labels',()=>{const w={previous:{start_utc:'2026-11-02T08:00:00Z',end_utc:'2026-11-09T08:00:00Z'}};assert.equal(api.periodMatch(w,{current_week:w.previous},'previous'),'current_week');assert.equal(api.periodMatch(w,{current_week:{...w.previous,end_utc:'2026-11-09T07:00:00Z'}},'previous'),null);});
test('Upcoming queue retains every eligible game and ranks new identities before saved outlooks',()=>{const games=[{id:'a',season:2026,kickoff_exact:true,kickoff:'2026-11-10T00:30:00Z'},{id:'b',season:2026,kickoff_exact:true,kickoff:'2026-11-12T00:30:00Z',new_fixture_epoch:true},{id:'tbd',season:2026,kickoff_exact:false,kickoff:null},{id:'past',season:2026,kickoff_exact:true,kickoff:'2026-11-08T00:30:00Z'}];const queue=api.refreshQueue(games,{start_utc:'2026-11-09T08:00:00Z',end_utc:'2026-11-16T08:00:00Z'},g=>({available:g.id==='a'}));assert.deepEqual(queue.map(r=>r.id),['b','a']);assert.equal(queue[0].reason,'NEW_FIXTURE_EPOCH_PREDICTION_PENDING');assert.equal(queue[1].reason,'NEAR_TERM_MODEL_NOT_ISSUED');assert.equal(queue.every(r=>r.issue_status==='NO_AUTHENTICATED_NEAR_TERM_ISSUE'),true);});
test('Metric export preserves source values, missingness and cohort qualification',()=>{const rows=api.selectRows(sample);const csv=api.metricCsv(rows,['log_loss','brier']);assert.match(csv,/RECORDED_FAMILY_COHORT/);assert.match(csv,/"0.52",""/);assert.doesNotMatch(csv,/undefined|NaN/);assert.equal(csv.split('\r\n').length,3);});
test('Actual Pacific upcoming scope accounts for all 53 games and both new identities',()=>{
 const fs=require('node:fs'),path=require('node:path'),M=require('../../../docs/fbs/research-method.js');
 const directory=path.resolve(__dirname,'../../../docs/fbs');
 const status=JSON.parse(fs.readFileSync(path.join(directory,'observation-status-v046.json')));
 const current=JSON.parse(fs.readFileSync(path.join(directory,'source-status-v049.json')));
 const games=status.rows.map(row=>({...row,new_fixture_epoch:row.binding_status==='TBD_RESOLUTION_NEW_FIXTURE_EPOCH'}));
 const queue=api.refreshQueue(games,M.weekWindows(current.capture.official_current_season_observed_at).upcoming,g=>({available:!g.new_fixture_epoch}),M.pacificDate);
 assert.equal(queue.length,53);assert.deepEqual(queue.slice(0,2).map(row=>row.id),['401866463','401858519']);
 assert.equal(queue.filter(row=>row.baseline_saved).length,51);
});
