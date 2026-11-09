'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
exports.run=async page=>{
 await page.locator('#forecast-access-summary').filter({hasText:'203 remaining fixtures'}).waitFor();
 assert.equal(await page.locator('#forecast-readiness button').count(),8);
 assert.match(await page.locator('[data-readiness-gap="saved_intervals"]').innerText(),/108\s*\/ 203/);
 for(const [target,count]of [['saved_intervals',95],['coherent_scores',95],['empirical_calibration',203],['close_horizon',203]]){
  await page.locator(`[data-readiness-gap="${target}"]`).click();assert.equal(await page.locator('#forward-target').inputValue(),target);assert.equal(await page.locator('#forward-outlook-rows tr').count(),count);
 }
 await page.locator('#refresh-deadlines > summary').click();
 assert.equal(await page.locator('#deadline-rows tr').count(),53);assert.match(await page.locator('#deadline-summary').innerText(),/159 future horizon boundaries · 0 boundaries already reached/);
 await page.selectOption('#deadline-scope','all');assert.equal(await page.locator('#deadline-rows tr').count(),203);
 await page.selectOption('#deadline-scope','unresolved');assert.equal(await page.locator('#deadline-rows tr').count(),95);assert.match(await page.locator('#deadline-rows').innerText(),/Cannot assign a horizon/);
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#deadline-export').click()]);const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.split('\r\n').length,286);assert.match(csv,/EXACT_KICKOFF_UNRESOLVED/);
 await page.selectOption('#deadline-scope','upcoming');await page.locator('[data-deadline-game]').first().click();assert.equal(await page.locator('#game-dialog').isVisible(),true);assert.match(await page.locator('#dialog-current-outlook').innerText(),/Authenticated current-origin outlook/);await page.keyboard.press('Escape');
 await page.locator('#deadline-search').fill('no such game');assert.equal(await page.locator('#deadline-export').isDisabled(),true);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 const clean=new URL(page.url());clean.search='';clean.hash='';await page.goto(clean.href);await page.waitForFunction(()=>document.querySelectorAll('#game-cards .game-card').length===30);
 return {status:'PASS',remaining_fixtures:203,timing_rows:609,current_numeric_values_published:false};
};
