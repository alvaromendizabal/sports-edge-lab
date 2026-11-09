'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
exports.run=async({browser,root,screenshots})=>{
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage();
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url())});
 const url='file://'+path.join(root,'docs/fbs/current.html');
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);await page.locator('#game-rows [data-game]').first().waitFor();
  assert.match(await page.locator('#game-summary').innerText(),/67 source games shown · 67 with saved issue values/);
  assert.equal(await page.locator('#game-rows tr').count(),40);
  assert.match(await page.locator('#execution-summary').innerText(),/46 base fits, 2 calibrators/);
  assert.match(await page.locator('#execution-summary').innerText(),/820,499 bytes/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`overflow ${width}`);
  await page.locator('#next-page').click();assert.equal(await page.locator('#game-rows tr').count(),27);
  await page.locator('#previous-page').click();await page.selectOption('#layer','calibrated');
  assert.match(await page.locator('#game-rows').innerText(),/Separate future-issued calibrated shadow/);
  await page.locator('#game-rows [data-game]').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-detail').isVisible(),true);
  assert.match(await page.locator('#detail-content').innerText(),/does not replace the original foundation issue/);
  assert.match(await page.locator('#detail-content').innerText(),/Polymarket Global/);await page.keyboard.press('Escape');
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.split('\r\n').length,68);assert.match(csv,/"calibrated"/);
  await page.selectOption('#period','tbd');assert.match(await page.locator('#game-summary').innerText(),/81 source games shown · 0 with saved issue values/);
  assert.match(await page.locator('#game-rows').innerText(),/Exact kickoff unresolved/);
  await page.selectOption('#period','all');await page.selectOption('#season','2024');await page.selectOption('#layer','historical');
  assert.match(await page.locator('#game-summary').innerText(),/920 source games shown/);
  await page.locator('#search').fill('no such game');assert.equal(await page.locator('#download-csv').isDisabled(),true);
  await page.goto(url);await page.locator('#game-rows [data-game]').first().waitFor();
  if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,`fbs-current-v053-${width}.png`),fullPage:true})}
 }
 const noScript=await browser.newContext({javaScriptEnabled:false}),fallback=await noScript.newPage();await fallback.goto(url);
 assert.match(await fallback.locator('#execution').innerText(),/46 base fits/);assert.equal(await fallback.locator('#comparison-rows tr').count(),5);
 assert.match(await fallback.locator('noscript').innerText(),/every game/);await noScript.close();
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);await context.close();
 return {status:'PASS',viewports:[1440,390],current_games:67,unresolved_current_season:81,all_source_games:2742,
  distinct_layers:3,keyboard_dialog:true,csv_rows:67,script_errors:0,external_requests:0};
};
