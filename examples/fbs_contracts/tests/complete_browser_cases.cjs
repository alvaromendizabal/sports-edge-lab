'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
exports.run=async({browser,root,screenshots})=>{
 const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))external.push(r.url());});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(root,'docs/fbs/complete.html'));
  assert.match(await page.locator('#result-status').innerText(),/^888 games · 629 observed complete · 622 retained replays$/);
  assert.equal(await page.locator('#game-rows tr').count(),30);assert.deepEqual(await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<0||r.right>innerWidth)&&getComputedStyle(e).position!=='absolute'&&!e.closest('.table-wrap')}).slice(0,15).map(e=>({tag:e.tagName,id:e.id,cls:e.className,right:e.getBoundingClientRect().right}))})),{width,scrollWidth:width,overflow:[]});
  assert.doesNotMatch(await page.locator('body').innerText(),/\bbetting\b|\bwagers?\b|\bstakes?\b|NO BET|\bpaper\b/i);
  for(const [period,count,complete,replays] of [['previous',56,56,56],['current',63,7,0],['all',888,629,622]]){
   await page.locator(`[data-period="${period}"]`).click();assert.equal(await page.locator('#result-status').innerText(),`${count} games · ${complete} observed complete · ${replays} retained replays`);
  }
  await page.selectOption('#model-filter','missing');assert.match(await page.locator('#result-status').innerText(),/^266 games/);
  await page.selectOption('#model-filter','all');await page.locator('#game-search').fill('401862817');assert.match(await page.locator('#game-rows').innerText(),/29 – 60/);assert.match(await page.locator('#game-rows').innerText(),/No retained replay/);
  await page.locator('#game-rows button').first().focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#game-dialog').isVisible(),true);assert.equal(await page.locator('#dialog-providers .provider-detail').count(),4);assert.match(await page.locator('#dialog-model').innerText(),/No qualified conditional distribution/);await page.keyboard.press('Escape');
  await page.locator('#game-search').fill('');await page.locator('[data-period="current"]').click();await page.selectOption('#provider-filter','Polymarket US');assert.match(await page.locator('#provider-coverage').innerText(),/Margin line or interval 52 \/ 63/);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-csv').click()]);const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split(/\r?\n/).length,64);assert.match(csv,/point_support/);assert.doesNotMatch(csv,/s3:\/\/|stake_usd|decision_reason/);
  await page.locator('[data-period="all"]').click();await page.selectOption('#model-filter','quarantine');assert.match(await page.locator('#result-status').innerText(),/^2 games/);assert.match(await page.locator('#game-rows').innerText(),/Identity quarantine/);
  for(const horizon of ['T120','T60','latest_pre_kickoff']){await page.selectOption('#comparison-horizon',horizon);assert.equal(await page.locator('#comparison-rows tr').count(),5);}
  for(const target of ['winner','margin','total','cover']){await page.selectOption('#target-filter',target);assert.equal(await page.locator('#registry-rows tr').count(),20);}
  assert.match(await page.locator('#registry-rows').innerText(),/No qualified cover forecast/);
  assert.deepEqual(await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left<0||r.right>innerWidth)&&getComputedStyle(e).position!=='absolute'&&!e.closest('.table-wrap')}).slice(0,15).map(e=>({tag:e.tagName,id:e.id,cls:e.className,right:e.getBoundingClientRect().right}))})),{width,scrollWidth:width,overflow:[]});
  if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.selectOption('#model-filter','all');await page.selectOption('#target-filter','winner');await page.evaluate(()=>{document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0);});await page.waitForFunction(()=>window.scrollY===0);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));assert.equal(await page.locator('.site-header').evaluate(e=>e.getBoundingClientRect().top),0);await page.screenshot({path:path.join(screenshots,`complete-${width}.png`)});await page.locator('#game-heading').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(screenshots,`complete-${width}-games.png`)});}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);await context.close();return{status:'PASS',games:888,complete:629,current_week:63,current_complete:7,retained_replays:622,viewports:[1440,390],external_requests:0,script_errors:0};
};
