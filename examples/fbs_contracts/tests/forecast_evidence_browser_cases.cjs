'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
exports.run=async page=>{
 await page.locator('#forecast-evidence-status').filter({hasText:/recorded target rows/}).waitFor();
 assert.equal(await page.locator('.evidence-lanes article').count(),4);
 assert.match(await page.locator('#evidence-lane-foundation').innerText(),/685 current-season outcomes/);
 assert.match(await page.locator('#forecast-evidence-issued').innerText(),/Original issued forecasts in these legacy evaluation banks: 0/);
 assert.match(await page.locator('#refresh-priority-summary').innerText(),/53 upcoming fixtures · 2 new kickoff identities.*51 with saved legacy outlooks.*0 authenticated near-term issues/);
 assert.equal(await page.locator('#refresh-priority-rows tr').count(),53);
 await page.locator('#refresh-priority details > summary').click();
 assert.match(await page.locator('#refresh-priority-rows tr').first().innerText(),/Massachusetts at Toledo/);
 await page.locator('[data-refresh-game="401866463"]').click();assert.match(await page.locator('#dialog-model').innerText(),/No winner projection/);await page.keyboard.press('Escape');
 await page.locator('#refresh-priority details > summary').click();
 for(const period of ['2024','2025','2026','previous_week','current_week']){
  await page.selectOption('#evidence-period',period);
  for(const target of ['winner','margin','total']){
   await page.selectOption('#evidence-target',target);
   const expected=await page.evaluate(({period,target})=>FBS_EVALUATION_V049.scopes.baseline.rows.filter(r=>r.period===period&&r.target===target).length,{period,target});
   assert.equal(await page.locator('#forecast-evidence-rows > tr').count(),expected);
  }
 }
 await page.selectOption('#evidence-period','2026');await page.selectOption('#evidence-target','winner');
 const cat=page.locator('#forecast-evidence-rows > tr').filter({has:page.locator('strong',{hasText:'CatBoost'})});
 assert.match(await cat.innerText(),/682/);assert.match(await page.locator('#forecast-evidence-rows').innerText(),/685/);
 await page.selectOption('#evidence-comparison','matched');assert.match(await cat.innerText(),/682/);
 await cat.locator('details summary').click();assert.match(await cat.innerText(),/multiplicity-adjusted.*Pacific week blocks/s);await cat.locator('details summary').click();
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#forecast-evidence-export').click()]);
 const csv=fs.readFileSync(await download.path(),'utf8');assert.match(csv,/EXACT_MATCHED_CONTROL_COHORT/);assert.match(csv,/original_computed_at_utc/);assert.doesNotMatch(csv,/undefined|NaN|s3:\/\//);
 await page.selectOption('#evidence-scope','two_epoch');await page.selectOption('#evidence-period','current_week');
 assert.match(await page.locator('#forecast-evidence-rows').innerText(),/14/);
 await page.locator('#forecast-evidence-rows details summary').first().click();assert.match(await page.locator('#forecast-evidence-rows').innerText(),/INSUFFICIENT_DISTINCT_WEEK_BLOCKS/);
 await page.selectOption('#evidence-target','margin');assert.match(await page.locator('#forecast-evidence-rows').innerText(),/mean width|without a saved score/);
 await page.selectOption('#evidence-scope','four_epoch');assert.match(await page.locator('#forecast-evidence-rows').innerText(),/OUTSIDE_REGISTERED_STUDY_SCOPE/);await page.selectOption('#evidence-period','2026');assert.match(await page.locator('#forecast-evidence-rows').innerText(),/GAME_NOT_YET_PLAYED/);assert.equal(await page.locator('#forecast-evidence-export').isDisabled(),true);
 await page.selectOption('#evidence-target','cover');assert.match(await page.locator('#forecast-evidence-rows').innerText(),/NO_COMPARABLE_LINE/);
 await page.selectOption('#evidence-scope','baseline');await page.selectOption('#evidence-period','2026');await page.selectOption('#evidence-target','winner');await page.selectOption('#evidence-comparison','own');
 return{status:'PASS',owner_rows:245,upcoming_games:53,pending_new_epochs:2,new_policy_issues:0,local_metric_calculations:0};
};
