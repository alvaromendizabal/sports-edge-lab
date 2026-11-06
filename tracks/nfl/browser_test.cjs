// Real offline Chromium checks; no AWS, provider data requests or external assets.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.NFL_BROWSER_EXECUTABLE||undefined});
 try {
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))network.push(r.url());});
 const widths=[1440,390];let states=0;
 for(const width of widths){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'review.html'));
  await page.locator('#results tbody tr').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'page overflow at '+width);
  // Current evidence is separately dated; old 316-panel controls remain intact.
  assert.equal(await page.locator('h1').count(),1);
  assert.match(await page.locator('#collection-clock-note').innerText(),/limits a two-hour evaluation, not data collection/);
  await page.locator('#clock-guide summary').click();
  assert.equal(await page.locator('#clock-guide table tbody tr').count(),5);
  assert.match(await page.locator('#clock-guide').innerText(),/T24 · 24 hours before kickoff/);
  assert.match(await page.locator('#clock-guide').innerText(),/a current postgame price cannot stand in/);
  await page.locator('#clock-guide summary').click();
  assert.match(await page.locator('#kalshi-horizon option[value="T2"]').innerText(),/2 hours before kickoff/);
  for(const id of ['kalshi-horizon','current-year','current-target','disagreement-model','disagreement-result'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.match(await page.locator('#current-headline').innerText(),/DraftKings.*Kalshi.*Polymarket/s);
  assert.equal(await page.locator('#three-provider-cards article').count(),3);
  for(const year of ['2026','week9','2025','2024']){await page.selectOption('#provider-review-period',year);assert.equal(await page.locator('#three-provider-cards article').count(),3);}
  await page.selectOption('#provider-review-period','2025');
  const latestHistoricalPoly=page.locator('[data-review-provider="Polymarket"]');
  assert.equal((await latestHistoricalPoly.innerText()).match(/279/g).length,2);
  assert.match(await latestHistoricalPoly.innerText(),/278/);
  assert.equal(await page.locator('#historical-source-delta-rows tbody tr').count(),17);
  assert.equal(await page.locator('#historical-source-delta-n041-rows tbody tr').count(),10);
  assert.equal(await page.locator('#historical-source-delta-n042-rows tbody tr').count(),11);
  assert.match(await page.locator('[data-review-provider="Kalshi"]').innerText(),/275[\s\S]*278[\s\S]*282/);
  await page.selectOption('#provider-review-period','2026');
  assert.equal(await page.locator('#three-provider-performance tbody tr').count(),3);
  assert.match(await page.locator('#three-provider-performance').innerText(),/77 \/ 77/);
  assert.match(await page.locator('#three-provider-performance').innerText(),/63 \/ 63/);
  assert.match(await page.locator('#current-comparison').innerText(),/119/);
  assert.match(await page.locator('#current-comparison').innerText(),/0\.644377/);
  await page.selectOption('#kalshi-horizon','T1');
  assert.match(await page.locator('#current-summary').innerText(),/not a same-horizon comparison/);
  assert.match(await page.locator('#current-comparison').innerText(),/0\.644579/);
  await page.selectOption('#kalshi-horizon','T2');
  assert.match(await page.locator('#current-comparison').innerText(),/0\.629080/);
  assert.equal(await page.locator('#current-provider-table tbody tr').count(),3);
  assert.match(await page.locator('#current-providers').innerText(),/incomplete/i);
  assert.match(await page.locator('#current-providers-heading').innerText(),/Archived provider coverage/);
  assert.equal(await page.locator('#current-providers').getAttribute('data-as-of'),'2026-11-03T21:24:00+00:00');
  assert.match(await page.locator('#archived-provider-notice').innerText(),/Superseded provider coverage/);
  assert.equal(await page.locator('#archived-provider-notice a').getAttribute('href'),'#latest-coverage');
  assert.match(await page.locator('#current-execution').innerText(),/Prior accepted N033 execution/);
  assert.match(await page.locator('#current-execution').innerText(),/That N033 execution added 192/);
  assert.doesNotMatch(await page.locator('#current-execution').innerText(),/This execution added/);
  assert.match(await page.locator('#current-snapshots').innerText(),/Week 8/);
  for(const year of ['2024','2025','2026']){
   await page.selectOption('#current-year',year);
   for(const target of ['winner','margin','total']){
    await page.selectOption('#current-target',target);
    assert.match(await page.locator('#current-selection').innerText(),new RegExp(year));
    assert((await page.locator('#current-season-table').innerText()).length>50,'current target has evidence or explicit missing state');
    states++;
   }
  }
  await page.selectOption('#current-target','winner');
  await page.selectOption('#disagreement-result','kalshi');
  assert((await page.locator('#disagreement-table tbody tr').count())>0,'lost disagreements stay visible');
  assert.equal(await page.locator('#disagreement-table [data-result="model"]').count(),0);
  await page.selectOption('#disagreement-result','model');
  assert((await page.locator('#disagreement-table [data-result="model"]').count())>0);
  assert.equal(await page.locator('#disagreement-table [data-result="kalshi"]').count(),0);
  await page.selectOption('#disagreement-result','all');
  await page.locator('#current-year').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#current-year').inputValue(),'2025');
  await page.selectOption('#current-year','2026');
  await page.evaluate(()=>window.scrollTo(0,0));
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-current-'+width+'.png')});}

  // N035 all-game evidence is separate from the retained N033 scorecard.
  for(const id of ['coverage-period','coverage-model','coverage-horizon','coverage-metric-season','coverage-metric-week','coverage-metric-model','coverage-metric-provider','coverage-metric-target','coverage-disagreement-result'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
  assert.equal(await page.locator('#coverage-games .forecast-readiness').count(),15);
  assert.equal(await page.locator('#coverage-games .injury-status').count(),15);
  assert.equal(await page.locator('#coverage-games .wager-status').count(),15);
  assert.match(await page.locator('#coverage-games').innerText(),/Early projection · betting assessment pending/);
  assert.match(await page.locator('#coverage-games').innerText(),/Raw and uncalibrated research/);
  assert.match(await page.locator('#coverage-games').innerText(),/Latest-issued display default; this is not model promotion/);
  assert.match(await page.locator('#coverage-games').innerText(),/Personal bets are not tracked/);
  assert.match(await page.locator('#coverage-games').innerText(),/early research forecast is not a qualified wagering recommendation/);
  assert.doesNotMatch(await page.locator('#coverage-games').innerText(),/NO BET|No wager placed/);
  assert.match(await page.locator('#ravens-qb-context').innerText(),/Joe Fagnano will start/);
  assert.match(await page.locator('#ravens-qb-context').innerText(),/no forecast that fully incorporates the quarterback situation is claimed/);
  // The experimental issue is an additional role, never a replacement stream.
  assert.equal(await page.locator('#coverage-model').inputValue(),'n048_fresh');
  assert.equal(await page.locator('#coverage-metric-model option[value="experimental_injury_issue"]').count(),0);
  await page.locator('#show-injury-challenger').click();
  assert.equal(await page.locator('#coverage-model').inputValue(),'experimental_injury_issue');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
  assert.equal(await page.locator('.experimental-injury-status').count(),15);
  const experimentalJax=page.locator('[data-coverage-game="2026_09_JAX_BAL"]');
  assert.match(await experimentalJax.innerText(),/JAX 64\.2%/);
  assert.match(await experimentalJax.innerText(),/-4\.5/);
  assert.match(await experimentalJax.innerText(),/46\.9/);
  assert.match(await experimentalJax.innerText(),/BAL 9 and JAX 5 admitted rows; 14 rows excluded/);
  assert.match(await experimentalJax.innerText(),/Tyler Huntley and Joe Fagnano were excluded/);
  assert.match(await experimentalJax.innerText(),/Announced starter, depth chart and injured-reserve status are not verified/);
  assert.match(await experimentalJax.innerText(),/Winner uses base features without direct injury fields/);
  assert.match(await experimentalJax.locator('.experimental-clocks').innerText(),/Nov 3, 5:52 PM PST/);
  assert.match(await experimentalJax.locator('.experimental-clocks').innerText(),/Nov 3, 9:35 PM PST/);
  assert.match(await experimentalJax.locator('.experimental-clocks').innerText(),/Nov 3, 10:10 PM PST/);
  assert.doesNotMatch(await experimentalJax.locator('.experimental-clocks').innerText(),/T06:/);
  await experimentalJax.locator('details summary').click();
  assert.match(await experimentalJax.locator('.experimental-exact-clocks').innerText(),/2026-11-04T06:10:07.939230/);
  assert.match(await experimentalJax.locator('.experimental-exact-clocks').innerText(),/2026-11-04T06:09:37.320475/);
  assert.match(await experimentalJax.locator('.experimental-exact-clocks').innerText(),/2026-11-04T05:35:54.789543/);
  await experimentalJax.locator('details summary').click();
  assert.match(await experimentalJax.innerText(),/Fixed pre-2024 residual quantiles; no coverage guarantee/);
  assert.match(await page.locator('[data-coverage-game="2026_09_TB_CHI"]').innerText(),/No current report rows were admitted/);
  await page.selectOption('#coverage-period','10');
  await page.selectOption('#coverage-model','experimental_injury_issue');
  assert.equal(await page.locator('.experimental-injury-status').count(),14);
  await page.locator('#show-injury-challenger').click();
  const originalPayload=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-latest-evidence').textContent));
  assert.equal(originalPayload.model_sets.some(m=>m.id==='experimental_injury_issue'),false);
  assert.equal(originalPayload.all_games.some(g=>g.forecasts.some(f=>f.model_id==='experimental_injury_issue')),false);
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await experimentalJax.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-experimental-jax-'+width+'.png')});}
  await page.locator('#show-injury-refresh').click();
  assert.equal(await page.locator('#coverage-model').inputValue(),'experimental_injury_refresh');
  assert.equal(await page.locator('#coverage-metric-model option[value="experimental_injury_refresh"]').count(),0);
  assert.equal(await page.locator('.experimental-injury-status').count(),15);
  const refreshedJax=page.locator('[data-coverage-game="2026_09_JAX_BAL"]');
  assert.match(await refreshedJax.innerText(),/JAX 64\.2%/);
  assert.match(await refreshedJax.innerText(),/-5\.2/);
  assert.match(await refreshedJax.innerText(),/46\.6/);
  assert.match(await refreshedJax.innerText(),/BAL 18 and JAX 10 admitted feature-report rows/);
  assert.match(await refreshedJax.innerText(),/Same fitted heads/);
  assert.match(await refreshedJax.textContent(),/2026-11-05T00:10:20\.334054/);
  assert.match(await refreshedJax.textContent(),/2026-11-04T01:52:35\.279297/);
  assert.equal((await page.locator('.experimental-injury-status').allTextContents()).filter(x=>x.includes('Partial listed reports:')).length,11);
  assert.match(await page.locator('[data-coverage-game="2026_09_ARI_SEA"]').innerText(),/Unknown reports do not mean healthy players/);
  const refreshPayload=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-injury-refresh').textContent));
  assert.equal(refreshPayload.cards.length,29);assert.equal(refreshPayload.new_selected_forward_fits,0);
  assert.equal(refreshPayload.new_issue_target_rows,87);assert.equal(refreshPayload.owner_pipeline_accepted,false);
  await page.selectOption('#coverage-period','10');
  await page.selectOption('#coverage-model','experimental_injury_refresh');
  assert.equal(await page.locator('.experimental-injury-status').count(),14);
  assert.equal((await page.locator('.experimental-injury-status').allTextContents()).filter(x=>x.includes('No current report rows')).length,14);
  await page.locator('#show-injury-n040').click();
  assert.equal(await page.locator('#coverage-model').inputValue(),'experimental_injury_n040');
  assert.equal(await page.locator('#coverage-metric-model option[value="experimental_injury_n040"]').count(),0);
  assert.equal(await page.locator('.experimental-injury-status').count(),15);
  const newestJax=page.locator('[data-coverage-game="2026_09_JAX_BAL"]');
  assert.match(await newestJax.innerText(),/JAX 64\.2%/);
  assert.match(await newestJax.innerText(),/BAL 18 and JAX 10 admitted feature-report rows/);
  assert.match(await newestJax.textContent(),/2026-11-05T01:21:02\.691700/);
  assert.match(await newestJax.textContent(),/2026-11-04T01:52:35\.279297/);
  assert.equal((await page.locator('.experimental-injury-status').allTextContents()).filter(x=>x.includes('Partial listed reports:')).length,13);
  assert.match(await page.locator('[data-coverage-game="2026_09_ARI_SEA"]').innerText(),/ARI 12 and SEA 0/);
  assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"]').innerText(),/Unknown reports do not mean healthy players/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .official-context-n046').innerText(),/not an input to those N045 outputs/);
  const newestPayload=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-injury-n040').textContent));
  assert.equal(newestPayload.cards.length,29);assert.equal(newestPayload.source_census.admitted_rows,258);
  assert.equal(newestPayload.source_census.full_roster_coverage,false);
  assert.match(await page.locator('#injury-model-readiness').innerText(),/2,304 historical native cells/);
  assert.match(await page.locator('#injury-model-readiness').innerText(),/More injury data has not established an overall gain/);
  await page.selectOption('#coverage-period','10');
  await page.selectOption('#coverage-model','experimental_injury_n040');
  assert.equal((await page.locator('.experimental-injury-status').allTextContents()).filter(x=>x.includes('No current report rows')).length,14);
  await page.locator('#show-injury-n041').click();
  assert.equal(await page.locator('#coverage-model').inputValue(),'experimental_injury_n041');
  assert.equal(await page.locator('#coverage-metric-model option[value="experimental_injury_n041"]').count(),0);
  assert.equal((await page.locator('.experimental-injury-status').allTextContents()).filter(x=>x.includes('Partial listed reports:')).length,14);
  assert.match(await page.locator('[data-coverage-game="2026_09_TB_CHI"]').innerText(),/CHI 0 and TB 8/);
  assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"]').innerText(),/Unknown reports do not mean healthy players/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .official-context-n046').innerText(),/not an input to those N045 outputs/);
  const latest41=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-injury-n041').textContent));
  assert.equal(latest41.source_census.admitted_rows,266);assert.equal(latest41.source_census.team_sections,26);
  assert.equal(latest41.changes_since_n040.winner,0);assert.equal(latest41.changes_since_n040.margin,1);
  assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').textContent(),/2026-11-05T02:26:17\.945056/);
  assert.match(await page.locator('#injury-source-inventory').innerText(),/54,966 normalized rows/);
  assert.match(await page.locator('#injury-source-inventory').innerText(),/Context only; not admitted/);
  await page.locator('#contribution-metric-details > summary').click();
  assert.equal(await page.locator('#contribution-metric-details table').count(),3);
  assert.match(await page.locator('#contribution-metric-details').innerText(),/76 \/ 119/);
  assert.match(await page.locator('#contribution-metric-details').innerText(),/Unknown-report treatment/);
  assert.match(await page.locator('#injury-contribution-study').innerText(),/had no new issued forecasts/);
  assert.match(await page.locator('#injury-contribution-study').innerText(),/later N042 raw shadow and current rolling streams above now preserve their actual issues separately/);
  await page.locator('#contribution-metric-details > summary').click();
  await page.locator('#show-injury-challenger').click();
  await page.selectOption('#coverage-model','original_frozen');
  assert.match(await page.locator('#coverage-games').innerText(),/Forecast unavailable · betting assessment unavailable/);
  assert.doesNotMatch(await page.locator('#coverage-games').innerText(),/Early projection · betting assessment pending/);
  await page.selectOption('#coverage-model','selected_latest_origin');

  assert.equal(await page.locator('#coverage-horizon').inputValue(),'LATEST_OBSERVED');
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/15 \/ 15/);
  assert.equal((await page.locator('#coverage-provider-counts').innerText()).match(/15 \/ 15/g).length,3);
  const providerCounts=page.locator('#coverage-provider-counts .mini-stat');
  assert.equal(await providerCounts.filter({hasText:'Kalshi'}).locator('strong').innerText(),'15 / 15');
  assert.equal(await providerCounts.filter({hasText:'DraftKings'}).locator('strong').innerText(),'15 / 15');
  const pointCounts=page.locator('#coverage-point-counts tbody tr');
  assert.match(await pointCounts.filter({hasText:'Kalshi'}).innerText(),/15 \/ 15[\s\S]*15 \/ 15 dated references[\s\S]*15 \/ 15 dated references/);
  assert.match(await pointCounts.filter({hasText:'DraftKings'}).innerText(),/15 \/ 15[\s\S]*15 \/ 15 dated references[\s\S]*15 \/ 15 dated references/);
  assert.match(await page.locator('#partial-source-status').innerText(),/fresh Kalshi and Polymarket references for all 15 games/);
  assert.match(await page.locator('#partial-source-status').innerText(),/dated early-week observations/);
  assert.match(await page.locator('#partial-source-status').innerText(),/alternate thresholds, not necessarily main lines/);
  const jaxCard=page.locator('[data-coverage-game="2026_09_JAX_BAL"]');
  assert.match(await jaxCard.innerText(),/JAX 67\.8%/);
  assert.match(await jaxCard.innerText(),/-4\.0/);
  assert.match(await jaxCard.innerText(),/45\.7/);
  const liveJaxSource=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n047-current-source').textContent));
  for(const r of liveJaxSource.point_rows.filter(r=>r.game_id==='2026_09_JAX_BAL'))assert((await jaxCard.innerText()).includes(r.predicate));
  assert.match(await jaxCard.innerText(),/Recovered observation/);
  const lvCard=page.locator('[data-coverage-game="2026_09_LV_SF"]');
  assert.match(await lvCard.innerText(),/Recovered schedule reference/);
  assert.match(await lvCard.innerText(),/Current quote/);
  assert.match(await lvCard.innerText(),/exact schedule revision recovered on the owner runtime/);
  assert.match(await lvCard.innerText(),/Separately verified event mapping/);
  assert.match(await lvCard.innerText(),/Home margin > 10 \(home handicap -10\)/);
  const currentLvTotal=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n047-current-source').textContent).point_rows.find(r=>r.game_id==='2026_09_LV_SF'&&r.provider==='DraftKings'&&r.target==='total'));
  assert.equal(typeof currentLvTotal.line,'number');
  assert((await lvCard.innerText()).includes(currentLvTotal.predicate),'Latest captured DraftKings total must be displayed');
  assert.match(await lvCard.locator('.schedule-mapping-note').innerText(),/2026-11-08T21:05:00Z[\s\S]*2026-11-08T21:25:00/);
  const mapping=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-reschedule-reference').textContent));
  assert.equal(mapping.winner_rows[0].quote_at,'2026-11-04T01:51:50Z');
  assert.equal(mapping.winner_rows[0].acquired_at,'2026-11-04T01:52:38Z');
  assert.equal(mapping.new_provider_requests,0);
  const recovery=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-source-recovery').textContent));
  assert.equal(recovery.winner_rows.length,5);
  assert.equal(recovery.point_rows.length,14);
  assert.equal(recovery.new_model_fits,0);
  assert.equal(recovery.owner_pipeline_accepted,false);
  assert.equal(await providerCounts.filter({hasText:'Polymarket'}).locator('strong').innerText(),'15 / 15');
  assert.match(await pointCounts.filter({hasText:'Polymarket'}).innerText(),/15 \/ 15[\s\S]*15 \/ 15 dated references[\s\S]*15 \/ 15 dated references/);
  const retainedSource=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n038-source').textContent));
  assert.equal(retainedSource.current_winner_rows.length,30);
  const priorSource=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n039-current-source').textContent));
  assert.equal(priorSource.winner_rows.length,58);
  const freshSource=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n041-current-source').textContent));
  assert.equal(freshSource.winner_rows.length,58);
  assert.equal(freshSource.point_rows.length,116);
  assert.equal(freshSource.n041_owner_fallback_available,false);
  assert.equal(freshSource.draftkings_fresh_games,15);
  assert.equal(freshSource.original_normalized_week9_games,14);
  assert.equal(freshSource.review_recovered_week9_games,1);
  for(const gid of ['2026_09_TB_CHI','2026_09_BUF_MIN']){
   const card=page.locator('[data-coverage-game="'+gid+'"]');
   const newestSource=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-n048-current-source').textContent));
   for(const r of newestSource.point_rows.filter(r=>r.game_id===gid))assert((await card.innerText()).includes(r.predicate));
   assert.match(await card.textContent(),/2026-11-06T0[12]:/);
   assert.equal(await card.locator('.alternate-threshold').count(),0);
  }
  const issue42=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n042').textContent));
  assert.equal(issue42.actual_target_rows,261);assert.equal(issue42.new_native_fits,7);assert.equal(issue42.owner_pipeline_accepted,false);
  for(const role of ['original','shadow','fresh']){
   await page.locator('#show-'+role+'-n042').click();
   assert.equal(await page.locator('#coverage-model').inputValue(),'n042_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   assert.equal(await page.locator('.n042-injury-status').count(),15);
   const currentJax=page.locator('[data-coverage-game="2026_09_JAX_BAL"]');
   assert.match(await currentJax.innerText(),role==='original'?/JAX 64\.2%/:/JAX 67\.6%/);
   assert.match(await currentJax.innerText(),role==='original'?/Preserved calibration/:/Raw and uncalibrated research/);
   assert.equal(await page.locator('#coverage-metric-model option[value="n042_'+role+'"]').count(),0);
   await page.selectOption('#coverage-period','10');await page.selectOption('#coverage-model','n042_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),14);
  }
  const study45=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-owner-study-n045').textContent));
  assert.equal(study45.new_total_fits,1038);assert.equal(study45.completed_historical_cells,1152);assert.equal(study45.new_designation_forecasts,0);assert.equal(study45.owner_research_acceptance,false);
  for(const origin of ['annual_injury_head','weekly_expanding','event_expanding'])for(const target of ['winner','margin','total']){
   await page.selectOption('#designation-origin',origin);await page.selectOption('#designation-target',target);
   assert.equal(await page.locator('#designation-metric-table tbody tr').count(),3);
   assert.match(await page.locator('#designation-metric-scope').innerText(),/not prospective issue performance/);
  }
  await page.selectOption('#designation-origin','annual_injury_head');await page.selectOption('#designation-target','winner');
  assert.match(await page.locator('#designation-metric-table').innerText(),/0\.663311/);
  await page.locator('#show-fresh-n045').click();
  const lvCurrent=page.locator('[data-coverage-game="2026_09_LV_SF"]');
  assert.match(await lvCurrent.innerText(),/exact schedule revision recovered on the owner runtime/);
  const issue45=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n045').textContent));
  assert.equal(issue45.actual_target_rows,261);assert.equal(issue45.source_census.team_sections,28);
  for(const role of ['fresh','original','shadow']){
   await page.locator('#show-'+role+'-n045').click();
   assert.equal(await page.locator('#coverage-model').inputValue(),'n045_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   assert.equal(await page.locator('#coverage-metric-model option[value="n045_'+role+'"]').count(),0);
   assert.match(await page.locator('[data-coverage-game="2026_09_ARI_SEA"]').innerText(),/SEA 15/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"]').innerText(),/Unknown reports do not mean healthy players/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .official-context-n046').innerText(),/not an input to those N045 outputs/);
  }
  if(process.env.NFL_SCREENSHOTS)await page.locator('#designation-study-n045').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-designation-study-n045-'+width+'.png')});
  assert.match(await page.locator('#latest-injury-source-n047').innerText(),/340 listed rows/);
  assert.match(await page.locator('#latest-injury-source-n047').innerText(),/not inputs to the N046 forecasts/);
  const issue46=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n046').textContent));
  assert.equal(issue46.actual_target_rows,348);assert.equal(issue46.new_native_fits,3);assert.equal(issue46.source_census.team_sections,29);
  assert.match(await page.locator('#owner-current-n046').innerText(),/28 other forecast games remain unknown/);
  const registry=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-model-registry').textContent));
  assert.equal(registry.models.length,39);
  assert.equal(await page.locator('#model-evidence-select option').count(),await page.locator('#coverage-model option').count()-1);
  for(const model of registry.models){
   await page.selectOption('#model-evidence-select',model.id);
   if(model.kind==='GENUINELY_ISSUED_EARLY_RESEARCH')assert.match(await page.locator('#model-evidence-status').innerText(),/AWAITING ISSUED OUTCOMES/);
   assert.match(await page.locator('#model-evidence-readiness').innerText(),['n047_designation','n048_designation'].includes(model.id)?/ISSUED UNVALIDATED DISTRIBUTION TRANSFER/:/NOT CALIBRATED FOR EXECUTABLE LINE/);
  }
  for(const role of ['designation','fresh','original','shadow']){
   await page.locator('#show-'+role+'-n046').click();
   assert.equal(await page.locator('#coverage-model').inputValue(),'n046_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   const actualCard=issue46.streams.find(s=>s.role===role).cards.find(c=>c.game_id==='2026_09_JAX_BAL');
   assert((await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').innerText()).includes('JAX '+(100*actualCard.pick_probability).toFixed(1)+'%'));
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"]').innerText(),/MIN 7/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .latest-injury-source-context').innerText(),/BUF 18 and MIN 9/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .cover-readiness').innerText(),/not a calibrated probability/);
   if(role==='designation'){
    assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"] .designation-coverage').innerText(),/Both teams have supported listed designations/);
    assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .designation-coverage').innerText(),/Unknown for this game/);
   }
  }
  await page.selectOption('#model-evidence-select','n046_designation');
  if(process.env.NFL_SCREENSHOTS){await page.locator('#owner-current-n046').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-current-n046-'+width+'.png')});await page.locator('#model-evidence-registry').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-model-evidence-'+width+'.png')});}
  const issue47=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n047').textContent));
  assert.equal(issue47.actual_target_rows,336);assert.equal(issue47.new_native_fits,0);assert.equal(issue47.source_census.team_slots,28);
  for(const role of ['designation','fresh','original','shadow']){
   await page.locator('#show-'+role+'-n047').click();
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   assert.match(await page.locator('#coverage-count').innerText(),/JAX–BAL had passed T1/);
   assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').innerText(),/Forecast unavailable/);
   assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"]').innerText(),/BUF 18 and MIN 9|MIN 9 and BUF 18/);
   assert.equal(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .latest-injury-source-context').count(),0);
   if(role==='designation')assert.equal(await page.locator('#coverage-games .designation-coverage').count(),14);
  }
  const cover47=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-cover-n047').textContent));
  assert.equal(cover47.cards.length,28);assert.equal(cover47.threshold_rows.length,82);assert.equal(cover47.historical_games.length,636);
  assert.match(await page.locator('#cover-provider-metrics').innerText(),/50 \/ 64/);
  assert.match(await page.locator('#cover-provider-metrics').innerText(),/0.7596 \/ 0.6861/);
  await page.locator('#cover-research-n047 details summary').click();
  for(const season of ['2024','2025']){await page.selectOption('#cover-season',season);assert.match(await page.locator('#cover-history-status').innerText(),/0 resolved contract comparisons/);assert.match(await page.locator('#cover-history-games').innerText(),/No qualified historical threshold cohort/);}
  await page.selectOption('#cover-season','2026');await page.selectOption('#cover-history-week','all');
  assert.equal(await page.locator('#cover-history-games tbody tr').count(),120);
  await page.selectOption('#cover-history-provider','polymarket');assert.equal(await page.locator('#cover-history-games tbody tr').count(),92);
  await page.selectOption('#cover-history-provider','draftkings');assert.match(await page.locator('#cover-history-games').innerText(),/No qualified historical threshold cohort/);
  assert.match(await page.locator('#cover-current-providers').innerText(),/Settlement unknown/);
  for(const policy of ['annual_injury_head','event_expanding','weekly_expanding']){await page.selectOption('#cover-policy',policy);assert.match(await page.locator('#cover-distribution-metrics').innerText(),/120/);}
  await page.selectOption('#cover-policy','annual_injury_head');await page.selectOption('#cover-history-provider','kalshi');await page.selectOption('#cover-history-week','8');
  if(process.env.NFL_SCREENSHOTS){await page.locator('#owner-current-n047').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-current-n047-'+width+'.png')});await page.locator('#cover-research-n047').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-cover-n047-'+width+'.png')});}
  const issue48=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n048').textContent));
  assert.equal(issue48.actual_target_rows,336);assert.equal(issue48.new_native_fits,0);assert.equal(issue48.source_census.team_sections,24);
  for(const role of ['original','shadow','fresh','designation']){await page.locator('#show-'+role+'-n048').click();assert.equal(await page.locator('#coverage-model').inputValue(),'n048_'+role);assert.match(await page.locator('#coverage-count').innerText(),/JAX–BAL had passed T1/);assert.match(await page.locator('[data-coverage-game="2026_09_BUF_MIN"] .n042-injury-status').innerText(),/Unknown reports do not mean healthy/);}
  assert.equal(await page.locator('#cover-current-issue').inputValue(),'n048');assert.match(await page.locator('#cover-current-clock').innerText(),/01:46:21/);
  await page.selectOption('#cover-current-issue','n047');assert.match(await page.locator('#cover-current-clock').innerText(),/2026-11-06T00:/);await page.selectOption('#cover-current-issue','n048');
  for(const season of ['2024','2025','2026'])for(const target of ['winner','margin','total']){await page.selectOption('#injury-only-season',season);await page.selectOption('#injury-only-target',target);assert.equal(await page.locator('#injury-only-metrics tbody tr').count(),16);}
  await page.selectOption('#injury-only-target','winner');assert.match(await page.locator('#injury-only-study').innerText(),/source|unavailable/);assert.match(await page.locator('#injury-only-metrics').innerText(),/0.693899/);
  assert.equal(await page.locator('#ledger-table [data-ledger-game]').count(),20);assert.match(await page.locator('#ledger-proof').innerText(),/2448 provider status cells/);assert.match(await page.locator('#ledger-proof').innerText(),/31824 model status cells/);
  await page.selectOption('#ledger-week','9');assert.equal(await page.locator('#ledger-table [data-ledger-game]').count(),15);await page.selectOption('#ledger-team','BAL');assert.equal(await page.locator('#ledger-table [data-ledger-game]').count(),1);assert.match(await page.locator('#ledger-table').innerText(),/NOT_PUBLISHED_IN_THIS_SNAPSHOT/);
  await page.selectOption('#ledger-team','all');await page.selectOption('#ledger-week','all');await page.locator('#ledger-next').click();assert.equal(await page.locator('#ledger-table [data-ledger-game]').count(),20);await page.locator('#ledger-prev').click();
  const closure=await page.evaluate(()=>{const E=window.NFL_EVIDENCE_VIEW,F=window.NFL_FULL_COVERAGE,rows=E.games.flatMap(g=>E.providers.flatMap(p=>['winner','margin','total'].map(t=>F.reference(g,p,t))));return{n:rows.length,unique:new Set(rows.map(r=>[r.game_id,r.provider,r.target].join('|'))).size,bad:rows.filter(r=>r.value!=null&&!(Date.parse(r.quote_at??r.acquired_at)<Date.parse(E.games.find(g=>g.game_id===r.game_id).kickoff_utc))).length};});assert.deepEqual(closure,{n:2448,unique:2448,bad:0});
  if(process.env.NFL_SCREENSHOTS){await page.locator('#injury-only-study').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-injury-only-n048-'+width+'.png')});await page.locator('#full-coverage').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-full-coverage-n049-'+width+'.png')});}
  const issue44=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-current-issues-n044').textContent));
  assert.equal(issue44.actual_target_rows,261);
  for(const role of ['fresh','original','shadow']){
   await page.locator('#show-'+role+'-n044').click();
   assert.equal(await page.locator('#coverage-model').inputValue(),'n044_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   assert.equal(await page.locator('#coverage-metric-model option[value="n044_'+role+'"]').count(),0);
  }
  for(const mid of ['selected_annual','selected_weekly','selected_event','selected_stack','descriptive_feedback','descriptive_accuracy']){
   await page.selectOption('#common-three-model',mid);
   assert.equal(await page.locator('#common-three-summary tbody tr').count(),3);
  }
  assert.equal(await page.locator('#common-three-probabilities tbody tr').count(),5);
  assert.equal(await page.locator('#common-three-probability-intervals tbody tr').count(),18);
  assert.match(await page.locator('#common-three-probabilities').innerText(),/0\.606083/);
  if(process.env.NFL_SCREENSHOTS)await page.locator('#owner-recovery-n044').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-owner-recovery-'+width+'.png')});
  if(process.env.NFL_SCREENSHOTS)await page.locator('#common-three-provider').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-common-three-'+width+'.png')});
  await page.selectOption('#coverage-period','completed');
  await page.selectOption('#coverage-horizon','T2');
  assert.match(await page.locator('#coverage-games').innerText(),/Restored original quote/);
  assert.match(await page.locator('#coverage-games').innerText(),/retrospectively acquired/);
  assert.match(await page.locator('#coverage-games').innerText(),/retained earlier reference, not demonstrated latest/);
  const study43=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-owner-study-n043').textContent));
  assert.equal(study43.new_total_fits,1614);assert.equal(study43.new_designation_forecasts,0);assert.equal(study43.owner_research_acceptance,false);
  for(const role of ['original','shadow']){
   await page.locator('#show-'+role+'-n043').click();
   assert.equal(await page.locator('#coverage-model').inputValue(),'n043_'+role);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
   assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').textContent(),/2026-11-04T01:52:35/);
   assert.equal(await page.locator('#coverage-metric-model option[value="n043_'+role+'"]').count(),0);
  }
  if(process.env.NFL_SCREENSHOTS)await page.locator('#designation-study-n043').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-designation-study-'+width+'.png')});
  await page.locator('#show-fresh-n042').click();
  assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').textContent(),/2026-11-05T04:36:42\.446281/);
  assert.match(await page.locator('[data-coverage-game="2026_09_JAX_BAL"]').innerText(),/121 earlier current-season training games/);
  if(process.env.NFL_SCREENSHOTS)await page.locator('#current-rolling-n042').screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-current-rolling-'+width+'.png')});
  await page.selectOption('#coverage-model','preserved_primary_refresh');
  assert.match(await jaxCard.innerText(),/JAX 67\.5%/);
  assert.match(await jaxCard.innerText(),/-5\.0/);
  assert.match(await jaxCard.innerText(),/45\.8/);
  assert.match(await jaxCard.textContent(),/2026-11-04T01:54:09/);
  assert.match(await jaxCard.innerText(),/Current injury\/QB information: Not verified/);
  await page.selectOption('#coverage-model','selected_latest_origin');
  assert.match(await jaxCard.innerText(),/JAX 67\.8%/);
  const sourceOverlay=await page.evaluate(()=>JSON.parse(document.getElementById('nfl-source-overlay').textContent));
  assert.equal(sourceOverlay.owner_pipeline_accepted,false);
  assert.equal(sourceOverlay.winner_rows.length,45);
  assert.equal(sourceOverlay.point_rows.length,90);
  assert(sourceOverlay.winner_rows.filter(r=>r.provider==='Kalshi'&&r.derived_pick).every(r=>r.quote_at===null&&r.quote_clock_kind==='OBSERVATION_TIME_ONLY_PROVIDER_QUOTE_CLOCK_UNKNOWN'));
  await page.selectOption('#coverage-horizon','T1');
  assert.match(await page.locator('#partial-source-status').innerText(),/not applied to the selected historical horizon/);
  assert.equal(await providerCounts.filter({hasText:'Kalshi'}).locator('strong').innerText(),'0 / 15');
  assert.doesNotMatch(await page.locator('#coverage-games').innerText(),/Recovered observation|Recovered schedule reference/);
  assert.equal(await page.locator('.schedule-mapping-note').count(),0);
  assert.match(await jaxCard.innerText(),/JAX 67\.8%/);
  await page.selectOption('#coverage-horizon','LATEST_OBSERVED');

  assert.match(await page.locator('#coverage-asof').innerText(),/Current N047 early research issues/);
  assert.match(await page.locator('#coverage-asof').innerText(),/Whole-pipeline acceptance is not claimed/);
  assert.doesNotMatch(await page.locator('#coverage-asof').innerText(),/FAILED/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/Current capture recovered: LV at SF/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/21:05 UTC/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/21:25 UTC/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/current references for all 15 Week 9 games/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/original owner normalizer's count remains 14/);
  assert.match(await page.locator('#unjoined-provider-note').innerText(),/No new provider request/);
  assert.match(await page.locator('#coverage-clock-note').innerText(),/Reaching T2 is not a requirement/);
  assert.match(await page.locator('#monday-game-summary').innerText(),/Chicago 34–17 Seattle/);
  assert.match(await page.locator('#monday-game-summary').innerText(),/Seattle lost/);
  assert.match(await page.locator('#monday-game-summary').innerText(),/source exists for T1, not T2/);
  assert.match(await page.locator('#monday-game-summary').innerText(),/updating view had not inherited/);
  assert.match(await page.locator('#monday-recovery-note').innerText(),/zero fits and zero forecasts/);
  assert.match(await page.locator('#monday-recovery-note').innerText(),/N042 current rolling branch has now trained/);
  assert.match(await page.locator('#monday-recovery-note').innerText(),/does not score this game using its own outcome/);
  assert.match(await page.locator('#coverage-point-counts').innerText(),/Margin reference/);
  assert.match(await page.locator('#coverage-point-counts').innerText(),/Total reference/);
  await page.locator('#show-monday-game').click();
  assert.equal(await page.locator('#coverage-period').inputValue(),'monday');
  assert.equal(await page.locator('#coverage-model').inputValue(),'preserved_selected_actual_T1');
  assert.equal(await page.locator('#coverage-horizon').inputValue(),'T1');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),1);
  assert.equal(await page.locator('#coverage-games .forecast-readiness').count(),0,'resolved games do not receive pending-future status');
  assert.match(await page.locator('#coverage-games').innerText(),/SEA 62\.9%/);
  assert.match(await page.locator('#coverage-games').innerText(),/Incorrect winner/);
  assert.match(await page.locator('#coverage-games').innerText(),/SEA margin > 3\.5/);
  assert.match(await page.locator('#coverage-games').innerText(),/Total points > 46\.5/);
  assert.match(await page.locator('#coverage-games').innerText(),/not a predicted final margin/);
  assert.match(await page.locator('#coverage-games').innerText(),/absolute error 22\.2/);
  await page.selectOption('#coverage-period','completed');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),121);
  assert.equal(await page.locator('#coverage-horizon').inputValue(),'T2');
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/121 \/ 121/);
  assert.match(await page.locator('#coverage-point-counts').innerText(),/121 \/ 121/);
  assert.match(await page.locator('#coverage-point-counts').innerText(),/92 \/ 121/);
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/92 \/ 121/);
  await page.selectOption('#coverage-model','original_frozen');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),121);
  assert.match(await page.locator('#coverage-count').innerText(),/0 with a selected model winner output/);
  await page.selectOption('#coverage-horizon','T1');
  assert.match(await page.locator('#coverage-clock-note').innerText(),/one hour before kickoff/);
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/92 \/ 121/);
  await page.selectOption('#coverage-horizon','LATEST_PREGAME');
  assert.equal((await page.locator('#coverage-provider-counts').innerText()).match(/0 \/ 121/g).length,1);
  assert.match(await providerCounts.filter({hasText:'Kalshi'}).innerText(),/121 \/ 121/);
  assert.equal((await page.locator('#coverage-point-counts').innerText()).match(/0 \/ 121/g).length,3);
  assert.match(await providerCounts.filter({hasText:'Polymarket'}).innerText(),/121 \/ 121/);
  const mondayLatest=page.locator('[data-coverage-game="2026_08_CHI_SEA"]');
  assert.match(await mondayLatest.innerText(),/Retrospective pregame reference/);
  assert.match(await mondayLatest.innerText(),/SEA margin > 3\.5/);
  assert.match(await mondayLatest.innerText(),/Total points > 46\.5/);
  assert.match(await mondayLatest.innerText(),/47\.5% observed probability/);
  assert.match(await mondayLatest.innerText(),/49\.5% observed probability/);
  assert.match(await mondayLatest.textContent(),/2026-11-03T01:14:00/);
  assert.match(await mondayLatest.textContent(),/2026-11-04T03:43/);
  assert.match(await mondayLatest.innerText(),/Incorrect winner/);
  assert.match(await page.locator('#coverage-clock-note').innerText(),/never replaced silently with a T2 quote/);
  assert.match(await page.locator('#coverage-games').innerText(),/No authenticated latest-pregame reference is published/);
  for(const week of ['1','2','3','4','5','6','7','8']){
   await page.selectOption('#coverage-period',week);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),Number(week)<5?16:week==='5'?15:14);
   states++;
  }
  await page.selectOption('#coverage-period','all');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),272);
  await page.selectOption('#coverage-period','9');
  await page.selectOption('#coverage-metric-provider','Polymarket');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/0\.606083/);
  assert.match(await page.locator('#coverage-paired-table').innerText(),/0\.615317/);
  assert.match(await page.locator('#coverage-paired-count').innerText(),/exactly the same games/);
  await page.selectOption('#coverage-disagreement-result','provider');
  assert((await page.locator('#coverage-disagreements tbody tr').count())>0,'new provider losses remain visible');
  assert.match(await page.locator('#coverage-disagreement-count').innerText(),/below 60%/);
  await page.selectOption('#coverage-metric-target','total');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/No equivalent authenticated comparison/);
  await page.selectOption('#coverage-metric-provider','DraftKings');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/MAE/);
  await page.selectOption('#coverage-metric-target','win');
  await page.selectOption('#coverage-metric-provider','all');
  await page.selectOption('#coverage-disagreement-result','all');
  if(process.env.NFL_SCREENSHOTS){await page.locator('#latest-coverage').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-all-games-'+width+'.png')});}
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'new all-game view overflow at '+width);
  states+=48;

  assert.equal(await page.locator('#historical-archive').getAttribute('open'),null,'dated archive starts closed');
  for(const id of ['weekly-period','weekly-model','inventory-week','inventory-status'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),14);
  assert.match(await page.locator('#weekly-count').innerText(),/13 with winner probabilities/);
  assert.match(await page.locator('[data-game="2026_08_CHI_SEA"]').innerText(),/Separate genuine T−1h issue/);
  await page.selectOption('#weekly-model','original_frozen');
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),14,'missing model coverage cannot drop games');
  assert.match(await page.locator('#weekly-count').innerText(),/0 with winner probabilities/);
  await page.selectOption('#weekly-model','selected_weekly');
  assert.match(await page.locator('#weekly-count').innerText(),/retrospective reconstruction/);
  await page.selectOption('#weekly-period','9');
  assert.equal(await page.locator('#weekly-model').inputValue(),'selected_latest_origin','future view uses historically selected series');
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),15);
  assert.equal(await page.locator('#weekly-game-cards .forecast-readiness').count(),15);
  assert.match(await page.locator('#weekly-game-cards').innerText(),/Early projection · betting assessment pending/);
  assert.match(await page.locator('#weekly-game-cards').innerText(),/Current injury\/QB information: Not verified in this forecast/);
  assert.match(await page.locator('#weekly-game-cards').innerText(),/Personal wager activity: Not tracked in this dashboard/);
  assert.doesNotMatch(await page.locator('#weekly-game-cards').innerText(),/NO BET|No wager placed/);
  assert.match(await page.locator('#weekly-count').innerText(),/DraftKings 14\/15/);
  assert.match(await page.locator('#weekly-policy').innerText(),/Full-pipeline promotion is false/);
  assert.match(await page.locator('[data-game="2026_09_JAX_BAL"]').innerText(),/JAX 67.8%/);
  assert.match(await page.locator('[data-game="2026_09_LV_SF"]').innerText(),/Unavailable/);
  await page.locator('[data-game="2026_09_JAX_BAL"] summary').click();
  assert.match(await page.locator('[data-game="2026_09_JAX_BAL"]').innerText(),/2026-11-03T21:20:14/);
  assert.equal(await page.locator('#inventory-table tbody tr').count(),272);
  await page.selectOption('#inventory-status','final');assert.equal(await page.locator('#inventory-table tbody tr').count(),121);
  await page.selectOption('#inventory-status','upcoming');assert.equal(await page.locator('#inventory-table tbody tr').count(),151);
  await page.selectOption('#inventory-week','9');assert.equal(await page.locator('#inventory-table tbody tr').count(),15);
  await page.selectOption('#inventory-status','final');assert.equal(await page.locator('#inventory-table tbody tr').count(),0,'no invented future results');
  await page.selectOption('#inventory-week','8');assert.equal(await page.locator('#inventory-table tbody tr').count(),14);
  if(process.env.NFL_SCREENSHOTS){await page.locator('#weekly-cards').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-weekly-'+width+'.png')});}
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'weekly view overflow at '+width);
  await page.selectOption('#weekly-model','all');assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),15);
  await page.selectOption('#weekly-period','8');
  await page.selectOption('#inventory-status','all');await page.selectOption('#inventory-week','all');
  states+=22;
  await page.locator('#historical-archive>summary').click();
  assert.match(await page.locator('#legacy').innerText(),/316 panels/);
  assert.match(await page.locator('#coverage').innerText(),/280 \/ 285/);
  assert.match(await page.locator('#coverage').innerText(),/272 regular · 13 postseason/);
  for(const id of ['season','target','policy','metric','family','model','week-season','week-provider','time-scenario','time-decision'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#weekly-results [data-week]').count(),22);
  assert.equal(await page.locator('#provider-summary tbody tr').count(),5);
  assert.match(await page.locator('#storage-evidence').innerText(),/14\.327 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/15,383,494,656 allocated bytes/);
  assert.match(await page.locator('#storage-evidence').innerText(),/0\.656 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/107\.962 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/global cleanup is not repeated/);
  assert.match(await page.locator('#storage-evidence').innerText(),/remaining budget are unknown/);
  assert.match(await page.locator('#storage-evidence').innerText(),/N011 and N012 owner execution are not verified/);
  assert.match(await page.locator('#time-detail [data-time-check="source_bound"]').innerText(),/Does not establish the earlier policy/);
  assert.match(await page.locator('#time-detail [data-time-check="model_availability"]').innerText(),/Not recorded \/ not inferred/);
  for(const scenario of ['origin_bound','complete','equal_boundary','late_input','late_fit','unknown_fit']){
   await page.selectOption('#time-scenario',scenario);
   for(const hours of ['1','48']){
    await page.selectOption('#time-decision',hours);
    const expected=scenario==='complete'&&hours==='1'?'DEMO_ADMISSIBLE':'NOT_ESTABLISHED_FOR_POLICY';
    assert.equal(await page.locator('#time-status [data-time-status]').getAttribute('data-time-status'),expected);
    assert.equal(await page.locator('#time-detail [data-time-check]').count(),4);
    if(scenario==='late_fit'&&hours==='1'){
     assert.match(await page.locator('#time-detail [data-time-check="inputs"]').innerText(),/Strictly before policy/);
     assert.match(await page.locator('#time-detail [data-time-check="model_availability"]').innerText(),/Model completed after policy/);
    }
    if(scenario==='origin_bound'&&hours==='1')assert.match(await page.locator('#time-status').innerText(),/No actual late input or label is established/);
    if(scenario==='late_input')assert.match(await page.locator('#time-status').innerText(),/recorded input or label is too late/);
    states++;
   }
  }
  await page.selectOption('#time-scenario','complete');await page.selectOption('#time-decision','1');
  await page.locator('#time-decision').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#time-decision').inputValue(),'48');
  assert.match(await page.locator('#time-status').innerText(),/2025-10-31T18:00:00\+00:00/);states++;
  await page.selectOption('#time-scenario','origin_bound');await page.selectOption('#time-decision','1');
  await page.selectOption('#week-season','2026');
  assert.equal(await page.locator('#weekly-results [data-future="true"]').count(),4);
  assert.match(await page.locator('#weekly-results').innerText(),/6 expected by format; no captured matchups/);
  await page.selectOption('#week-provider','Kalshi');
  await page.locator('#provider-details summary').click();
  assert.equal(await page.locator('#provider-results [data-provider="Kalshi"]').count(),22);
  assert.match(await page.locator('#provider-results').innerText(),/Not verified \/ Not verified/);
  await page.selectOption('#week-season','all');
  assert.equal(await page.locator('#weekly-results [data-week]').count(),66);
  assert.equal(await page.locator('#provider-results [data-provider="Kalshi"]').count(),66);
  assert.match(await page.locator('#weekly-summary').innerText(),/330 provider\/week evidence states/);
  await page.selectOption('#week-season','2024');await page.selectOption('#week-provider','DraftKings');
  await page.locator('#provider-details summary').click();
  await page.selectOption('#season','2025');assert.match(await page.locator('#coverage').innerText(),/277 \/ 285/);
  await page.selectOption('#policy','fixed');await page.selectOption('#target','margin');
  assert.match(await page.locator('#results').innerText(),/MAE/);
  await page.locator('#metric').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#metric').inputValue(),'rmse');
  await page.selectOption('#family','Constrained ensemble');
  assert((await page.locator('#results [data-model]').count())>0);
  const model=await page.locator('#model option').nth(1).getAttribute('value');
  await page.selectOption('#model',model);assert.equal(await page.locator('#results [data-model]').count(),1);
  await page.selectOption('#family','all');await page.selectOption('#season','2026');
  assert.match(await page.locator('#coverage').innerText(),/77 \/ 107/);
  assert.match(await page.locator('#coverage').innerText(),/165 unplayed/);
  assert.match(await page.locator('#result-boundary').innerText(),/EXPOSED MONITORING/);
  assert.equal(await page.locator('#results .best,#results [data-winner],#results .winner').count(),0);
  const ids=await page.locator('#results [data-model]').evaluateAll(nodes=>nodes.map(n=>n.dataset.model));
  assert.deepEqual(ids,[...ids].sort(),'monitoring stays in stable identifier order');
  await page.selectOption('#season','1999');
  assert.match(await page.locator('#results').innerText(),/No saved panel/);
  assert.match(await page.locator('#coverage').innerText(),/259 known game identities/);
  await page.selectOption('#season','2022');assert.match(await page.locator('#coverage').innerText(),/canceled game/);
  await page.selectOption('#season','2024');await page.selectOption('#target','win');await page.selectOption('#model','all');
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-review-'+width+'.png'),fullPage:true});}
  states+=13;
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
 console.log(JSON.stringify({status:'PASS',viewports:widths,selection_scenarios:states,current_source_recovery_scenarios:2*widths.length,information_time_scenarios:24,keyboard_control:true,label_checks:38,external_requests:0,script_errors:0,monitoring_ranking:false,complete_week_slots:66,provider_week_states:330,weekly_games:29,schedule_inventory:272,active_providers:3,archived_providers_preserved:true}));
 } finally {
  await browser.close();
 }
})().catch(error=>{console.error(error);process.exitCode=1});
