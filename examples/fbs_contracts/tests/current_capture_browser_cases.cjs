'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
exports.run=async page=>{
 assert.equal(await page.locator('#capture-view').inputValue(),'latest');
 assert.equal(await page.locator('#result-status').innerText(),'888 games · 647 observed complete · 790 development projections');
 assert.equal(await page.locator('#stat-complete').innerText(),'647');
 assert.match(await page.locator('#capture-clock').innerText(),/2026-11-07/);
 await page.locator('#show-new-finals').click();
 assert.equal(await page.locator('#result-status').innerText(),'18 games · 18 observed complete · 18 development projections');
 assert.equal(await page.locator('#game-rows tr').count(),18);
 await page.locator('#game-search').fill('401856738');
 assert.match(await page.locator('#game-rows').innerText(),/Arkansas at Auburn/);
 assert.match(await page.locator('#game-rows').innerText(),/23 – 26/);
 const originalPrediction=await page.evaluate(()=>{
  const g=window.FBSCompleteReview.games.find(r=>r.id==='401856738');
  const p=window.FBSCompleteReview.projection(g);return[p.p,p.margin,p.total,p.record.cutoff];
 });
 await page.locator('#game-rows button').click();
 assert.match(await page.locator('#dialog-summary').innerText(),/Result source: latest/);
 assert.equal(await page.locator('#game-model-comparison tr').count(),14);
 await page.keyboard.press('Escape');
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-csv').click()]);
 const csv=fs.readFileSync(await download.path(),'utf8');
 assert.equal(csv.trim().split(/\r?\n/).length,2);assert.match(csv,/result_snapshot/);assert.match(csv,/result_observed_at/);assert.match(csv,/latest/);
 await page.selectOption('#result-filter','all');await page.selectOption('#capture-view','original');
 assert.match(await page.locator('#game-rows').innerText(),/No observed final/);
 assert.deepEqual(await page.evaluate(()=>{const g=window.FBSCompleteReview.games.find(r=>r.id==='401856738');const p=window.FBSCompleteReview.projection(g);return[p.p,p.margin,p.total,p.record.cutoff];}),originalPrediction);
 await page.selectOption('#capture-view','latest');await page.locator('#game-search').fill('');await page.locator('[data-period="current"]').click();
 assert.equal(await page.locator('#result-status').innerText(),'63 games · 25 observed complete · 63 development projections');
 await page.selectOption('#development-study','v042');
 for(const [cohort,n] of [['2026',647],['current_week',25],['previous_week',56],['newly_observed',18],['cumulative',2259]]){
  await page.selectOption('#development-cohort',cohort);assert.equal(await page.locator('#development-rows tr').count(),11);
  const values=await page.locator('#development-rows tr').evaluateAll(rows=>rows.map(r=>Number(r.children[1].textContent)));
  assert.ok(values.includes(n));assert.ok(values.every(v=>v===n||cohort==='2026'&&v===644||cohort==='cumulative'&&v===2256));
 }
 await page.selectOption('#development-target','cover');assert.equal(await page.locator('#export-metrics').isDisabled(),true);
 assert.match(await page.locator('#latest-source-summary').innerText(),/DraftKings/);
 assert.match(await page.locator('#latest-source-counts').innerText(),/39 captured events/);
 assert.equal(await page.locator('#latest-source-rows tr').count(),39);
 // The retained browser cases exercise the immutable original snapshots.
 await page.selectOption('#capture-view','original');await page.locator('[data-period="all"]').click();
 await page.selectOption('#development-study','v039');await page.selectOption('#development-cohort','2026');await page.selectOption('#development-target','winner');
};
