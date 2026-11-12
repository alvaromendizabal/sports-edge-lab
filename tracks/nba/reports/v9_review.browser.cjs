/* Independent V9 saved-data oracle; no fit, source request or rescoring. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const load=name=>JSON.parse(fs.readFileSync(path.join(__dirname,name)));
const hash=body=>crypto.createHash('sha256').update(body).digest('hex');
function verify(htmlBytes){
 const r=load('latest_v9_acceptance.json'),p=load('latest_research_outputs.json'),m=load('b078_recovered_b077_evidence.json');
 const embedded=htmlBytes.toString().match(/<script id="nba-v9-data" type="application\/json">([\s\S]*?)<\/script>/);
 assert.ok(embedded);assert.deepEqual(JSON.parse(embedded[1]),r);
 assert.equal(r.schema,'sports-edge-lab.nba.v9-publication.v1');
 assert.equal(r.selected_output_sha256,hash(fs.readFileSync(path.join(__dirname,'latest_research_outputs.json'))));
 assert.deepEqual(r.game_rows.map(g=>g.game_id).sort(),Object.keys(p.games).sort());
 assert.equal(r.coverage.observed_games,1274);assert.equal(r.coverage.unobserved_regular_slots,24);
 assert.equal(r.coverage.expected_current_role_cells,26532);assert.equal(r.coverage.available_current_role_cells,4245);
 assert.equal(r.coverage.missing_current_role_cells,22287);assert.equal(r.coverage.all_target_horizon_cells,7644);
 assert.equal(r.coverage.full_season_completion_claim,false);assert.equal(r.coverage.future_full_schedule_complete,false);
 let issueCells=0;
 for(const game of r.game_rows){const original=p.games[game.game_id],cov=p.game_coverage[game.game_id];
  assert.equal(game.last_confirmed_status,original.last_confirmed_status);assert.equal(game.scheduled_start_utc,original.scheduled_start_utc);
  assert.equal(game.schedule_source_asof_utc,original.schedule_source_asof_utc);assert.equal(game.last_confirmed_status_asof_utc,original.last_confirmed_status_asof_utc);
  assert.equal(game.available_current_roles,cov.current_role_ids_available.length);
  for(const c of game.target_horizon){const source=cov.target_horizon[c.target+'_T'+c.horizon_minutes];assert.equal(c.status,source.status);assert.equal(c.expected_roles,source.expected_roles);assert.equal(c.current_roles_available,source.current_roles_available);assert.equal(c.missing_roles,source.expected_roles-source.current_roles_available);}
  for(const ref of game.selected_original_issues){const source=p.issues[ref.issue_ref];assert.ok(source);for(const key of ['prediction','issued_at_utc','source_asof_utc','actual_lead_minutes','issue_horizon_class','source_age_seconds_at_issue']){assert.equal(ref[key],source[key]);issueCells++;}if(ref.prediction_intervals)assert.deepEqual(ref.prediction_intervals,source.prediction_intervals);}
  if(original.result_observation){assert.equal(game.actual.home_points,original.result_observation.home_points);assert.equal(game.actual.away_points,original.result_observation.away_points);assert.equal(game.actual.observed_at_utc,original.result_observation.observed_at_utc);}
  else{assert.equal(game.actual.home_points,null);assert.equal(game.actual.away_points,null);}
 }
 assert.equal(r.saved_metric_diagnostics.length,248);
 for(const d of r.saved_metric_diagnostics){const source=m.metric_rows[d.source_index];assert.equal(d.role_alias,source.role_alias);assert.equal(d.scored_games,source.scored_games);for(const [key,value]of Object.entries(d.metrics))assert.equal(value,source.metrics[key]);}
 assert.equal(r.runtime_receipts.length,5);assert.ok(r.runtime_receipts.every(x=>x.source_present===false&&x.verified_acceptance_claim===false));
 assert.equal(r.window_coverage.length,24);assert.ok(r.window_coverage.every(x=>x.saved_metric_rows===0&&x.full_current_season_best_claim===false));
 assert.equal(r.publication_lifecycle_scope,'CACHED_B077_SELECTED_OUTPUT_EVIDENCE');assert.equal(r.publication_lifecycle.merged.commit_sha,'9cd75587d769c68cd3a845bd6efa4400693f67f5');assert.equal(r.publication_lifecycle.deployed.verified,false);
 return{status:'PASS',games:r.game_rows.length,issue_source_cells_checked:issueCells,diagnostic_rows:248,real_fits:0,new_scores:0};
}
async function validatePage(page,name,exhaustive=false){const r=load('latest_v9_acceptance.json');
 assert.deepEqual(await page.locator('#nba-v9-data').evaluate(el=>JSON.parse(el.textContent)),r);
 assert.equal(await page.locator('#nba-v9-policy tbody tr').count(),r.model_policy_coverage.length);
 assert.equal(await page.locator('#nba-v9-windows tbody tr').count(),24);
 assert.equal(await page.locator('#nba-v9-diagnostics tbody tr').count(),248);
 const metrics=await page.locator('#nba-v9-diagnostics tbody tr').evaluateAll(rows=>rows.map(row=>[...row.cells].map(c=>c.textContent)));
 for(let i=0;i<metrics.length;i++){const source=r.saved_metric_diagnostics[i];assert.deepEqual(metrics[i].slice(2,6),['ece_10_bins','ece_10_fixed_bins','crps','weighted_interval_score'].map(key=>typeof source.metrics[key]==='number'?source.metrics[key].toFixed(6):'Unavailable'));}
 assert.equal(await page.locator('#nba-v9-runtime tbody tr').count(),5);
 assert.match(await page.locator('#nba-v9-denominator').textContent(),/1206 \/ 1230/);
 assert.match(await page.locator('#nba-v9-denominator').textContent(),/slots: 24/);
 assert.match(await page.locator('#nba-v9-publication-scope').textContent(),/CACHED B077 SELECTED OUTPUT EVIDENCE/);
 await page.locator('#nba-v9-game-details > summary').click();
 for(const filter of (exhaustive?['all','FINAL','SCHEDULED','TBD','missing','future']:['all','TBD'])){
  await page.selectOption('#nba-v9-game-state',filter);
  const expected=r.game_rows.filter(g=>filter==='all'||filter==='missing'&&g.missing_current_roles.length>0||filter==='future'&&g.tip_time_relation_at_report==='FUTURE_TIP'||g.last_confirmed_status===filter);
  const actual=await page.locator('#nba-v9-games tbody tr').evaluateAll(rows=>rows.map(row=>({id:row.dataset.gameId,cells:[...row.cells].map(c=>c.textContent)})));
  assert.deepEqual(actual.map(x=>x.id),expected.map(x=>x.game_id));
  for(let i=0;i<actual.length;i++){const e=expected[i];assert.equal(actual[i].cells[3],e.available_current_roles+' / '+e.expected_current_roles);assert.equal(actual[i].cells[4],(e.actual.home_points??'Unavailable')+' / '+(e.actual.away_points??'Unavailable'));}
 }
 await page.selectOption('#nba-v9-game-state','all');await page.locator('#nba-v9-game-details > summary').click();
 await page.locator('#nba-v9-title').scrollIntoViewIfNeeded();
 if(process.env.NBA_MONITOR_SCREENSHOTS)await page.screenshot({path:path.join(process.env.NBA_MONITOR_SCREENSHOTS,'nba-v9-'+name+'.png'),fullPage:false});
 assert.deepEqual(await page.evaluate(()=>window.NBA_V9_DISPLAY_STATE),{games:r.game_rows.length,filter:'all'});
 assert.equal(await page.locator('a[href="latest_v9_acceptance.json"]').count(),1);
 return{status:'PASS',name,games:r.game_rows.length};
}
module.exports={verify,validatePage};
