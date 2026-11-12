'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
exports.run=async({browser,root,screenshots})=>{
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage();
 const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!/^(file|blob|data):/.test(r.url()))external.push(r.url())});
 const url='file://'+path.join(root,'docs/fbs/latest-games-v063.html');
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);await page.evaluate(async()=>{await window.FBS_LATEST_READY;return true});
  assert.match(await page.locator('#game-summary').innerText(),/145 of 888 source games shown · 119 with retained probability · 26 explicit gaps/);
  assert.equal(await page.locator('#game-rows tr[data-game]').count(),30);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`overflow ${width}`);
  await page.locator('#game-rows button[data-detail]').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-detail').isVisible(),true);
  assert.match(await page.locator('#detail-content').innerText(),/Kalshi/);
  assert.match(await page.locator('#detail-content').innerText(),/None authorized by V062 champion check/);await page.keyboard.press('Escape');
  await page.selectOption('#period','refresh_gap');assert.match(await page.locator('#game-summary').innerText(),/145 of 888/);
  await page.selectOption('#period','omitted');assert.match(await page.locator('#game-summary').innerText(),/26 of 888.*0 with retained probability/);
  await page.selectOption('#layer','retained_v061');assert.match(await page.locator('#game-summary').innerText(),/26 of 888.*26 with retained probability/);
  await page.selectOption('#period','older');assert.match(await page.locator('#game-summary').innerText(),/14 of 888/);
  await page.selectOption('#period','all');assert.match(await page.locator('#game-summary').innerText(),/888 of 888/);
  await page.selectOption('#layer','replay');assert.match(await page.locator('#game-summary').innerText(),/790 with retained probability/);
  await page.selectOption('#period','tbd');assert.match(await page.locator('#game-summary').innerText(),/55 of 888/);
  await page.selectOption('#period','pending');assert.match(await page.locator('#game-summary').innerText(),/0 of 888/);
  await page.selectOption('#period','final');assert.match(await page.locator('#game-summary').innerText(),/688 of 888/);
  await page.selectOption('#period','upcoming');await page.selectOption('#layer','retained_v061');
  assert.match(await page.locator('#game-summary').innerText(),/145 of 888 source games shown · 145 with retained probability · 0 explicit gaps/);
  assert.match(await page.locator('#layer-note').innerText(),/not newly issued or reused by V062/);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-view').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.split('\r\n').length,146);
  assert.match(csv,/GENUINELY_FUTURE_ISSUED_ROLLING/);
  await page.locator('#search').fill('no such fixture');assert.equal(await page.locator('#download-view').isDisabled(),true);
  await page.locator('#search').fill('');await page.selectOption('#coverage','without');assert.match(await page.locator('#game-summary').innerText(),/0 of 888/);
  await page.selectOption('#coverage','all');assert.equal(await page.locator('#champion-rows tr').count(),9);
  assert.equal(await page.locator('#leader-rows tr').count(),49);
  assert.equal(await page.locator('#new-research-rows tr').count(),14);
  assert.equal(await page.locator('#native-monitor-rows tr').count(),4);
  assert.match(await page.locator('#native-monitor').innerText(),/387 completed games outside/);
  assert.match(await page.locator('#new-research').innerText(),/All 84/);
  if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,`fbs-latest-v063-${width}.png`),fullPage:true})}
 }
 const fallbackContext=await browser.newContext({javaScriptEnabled:false}),fallback=await fallbackContext.newPage();await fallback.goto(url);
 assert.match(await fallback.locator('noscript').innerText(),/all 888 games/);
 assert.match(await fallback.locator('#champions').innerText(),/V062 reached the champion stage and authorized zero/);
 await fallbackContext.close();assert.deepEqual(errors,[]);assert.deepEqual(external,[]);await context.close();
 return {status:'PASS',viewports:[1440,390],game_denominator:888,future_games:145,layer_csv_rows:145,actual_future_values:119,retained_archive_future_values:145,omitted_originals:26,older_selections:14,matched_research_rows:14,native_monitor_rows:4,keyboard_dialog:true,external_requests:0,script_errors:0};
};
