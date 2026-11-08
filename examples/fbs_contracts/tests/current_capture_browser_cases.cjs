'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const X=require('../../../docs/fbs/current-capture-v045.json'),Y=require('../../../docs/fbs/observation-status-v046.json');
exports.run=async page=>{
 assert.equal(await page.locator('#capture-view').inputValue(),'latest');
 assert.equal(await page.locator('#result-status').innerText(),'888 games · 685 observed complete · 790 development projections');
 assert.equal(await page.locator('#stat-complete').innerText(),'685');
 assert.match(await page.locator('#capture-clock').innerText(),/2026-11-08T19:34:42/);
 assert.match(await page.locator('#capture-update-summary').innerText(),/2 new finals.*56 since November 6/);
 await page.locator('#show-new-finals').click();
 assert.equal(await page.locator('#result-status').innerText(),'2 games · 2 observed complete · 2 development projections');
 assert.equal(await page.locator('#game-rows tr').count(),2);
 const added=Y.rows.find(r=>r.newly_observed_since_prior_capture);
 await page.locator('#game-search').fill(added.id);
 assert.match(await page.locator('#game-rows').innerText(),new RegExp(`${added.away_points} – ${added.home_points}`));
 const originalPrediction=await page.evaluate(id=>{
  const g=window.FBSCompleteReview.games.find(r=>r.id===id);
  const p=window.FBSCompleteReview.projection(g);return[p.p,p.margin,p.total,p.record.cutoff];
 },added.id);
 await page.locator('#game-rows button').click();
 assert.match(await page.locator('#dialog-summary').innerText(),/Result source: latest/);
 assert.equal(await page.locator('#game-model-comparison tr').count(),26);
 await page.keyboard.press('Escape');
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-csv').click()]);
 const csv=fs.readFileSync(await download.path(),'utf8');
 assert.equal(csv.trim().split(/\r?\n/).length,2);assert.match(csv,/result_snapshot/);assert.match(csv,/result_observed_at/);assert.match(csv,/latest/);
 await page.selectOption('#result-filter','all');
 for(const snapshot of ['nov7_night','nov7_evening','nov7_late','prior','original']){
  await page.selectOption('#capture-view',snapshot);assert.match(await page.locator('#game-rows').innerText(),/No observed final/);
  assert.deepEqual(await page.evaluate(id=>{const g=window.FBSCompleteReview.games.find(r=>r.id===id);const p=window.FBSCompleteReview.projection(g);return[p.p,p.margin,p.total,p.record.cutoff];},added.id),originalPrediction);
 }
 await page.locator('#game-search').fill('');await page.locator('[data-period="current"]').click();
 for(const [snapshot,n] of [['original',7],['prior',25],['nov7_late',45],['nov7_evening',48],['nov7_night',61],['latest',63]]){
  await page.selectOption('#capture-view',snapshot);assert.equal(await page.locator('#result-status').innerText(),`63 games · ${n} observed complete · 63 development projections`);
 }
 for(const [study,cohorts] of [['v045',[['2026',683],['current_week',61],['previous_week',56],['newly_observed',13],['cumulative',2295]]],['v044',[['2026',670],['current_week',48],['previous_week',56],['newly_observed',3],['cumulative',2282]]],['v043',[['2026',667],['current_week',45],['previous_week',56],['newly_observed',20],['cumulative',2279]]],['v042',[['2026',647],['current_week',25],['previous_week',56],['newly_observed',18],['cumulative',2259]]]]){
  await page.selectOption('#development-study',study);
  for(const [cohort,n] of cohorts){
   await page.selectOption('#development-cohort',cohort);assert.equal(await page.locator('#development-rows tr').count(),11);
   const values=await page.locator('#development-rows tr').evaluateAll(rows=>rows.map(r=>Number(r.children[1].textContent)));
   assert.ok(values.includes(n));assert.ok(values.every(v=>v===n||['2026','cumulative'].includes(cohort)&&v===n-3));
  }
 }
 await page.selectOption('#development-study','v043');await page.selectOption('#development-cohort','2026');
 await page.selectOption('#comparison-scope','paired');
 const cat=page.locator('#metric-deltas tr').filter({hasText:/catboost/i});assert.match(await cat.innerText(),/664/);assert.doesNotMatch(await cat.innerText(),/Different or unverified/);
 await page.selectOption('#comparison-scope','displayed');
 await page.selectOption('#development-target','cover');assert.equal(await page.locator('#export-metrics').isDisabled(),true);
 assert.match(await page.locator('#latest-source-summary').innerText(),/DraftKings/);
 assert.match(await page.locator('#latest-source-counts').innerText(),new RegExp(X.draftkings.event_count+' captured events'));
 assert.equal(await page.locator('#latest-source-rows tr').count(),X.draftkings.event_count);
 // The retained browser cases exercise immutable original snapshots.
 await page.selectOption('#capture-view','original');await page.locator('[data-period="all"]').click();
 await page.selectOption('#development-study','v039');await page.selectOption('#development-cohort','2026');await page.selectOption('#development-target','winner');
};
