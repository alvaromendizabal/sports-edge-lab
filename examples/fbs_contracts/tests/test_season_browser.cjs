// CI browser verification of the actual rendered report, not synthetic owner fits.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'../../..');
const url='file://'+path.join(root,'docs/fbs/index.html');
let browser;
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({acceptDownloads:true});
 const page=await context.newPage();const errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url());});
 let states=0;
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);
  assert.equal(await page.locator('h1').count(),1);
  assert.match(await page.locator('#latest-owner-note').innerText(),/V035 failed before resource admission/);
  assert.match(await page.locator('#latest-owner-note').innerText(),/separate interpreter exit is unobserved/);
  assert.equal(await page.locator('#games-body tr').count(),25);
  assert.match(await page.locator('#result-status').innerText(),/^888 games/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  for(const [view,count] of [['completed',627],['last',56],['current',63],['all',888]]){
   await page.locator(`[data-view="${view}"]`).click();
   assert.match(await page.locator('#result-status').innerText(),new RegExp(`^${count} games`));
   assert.equal(await page.locator('[data-view][aria-pressed="true"]').count(),1);states++;
  }
  for(const provider of ['DraftKings','Kalshi','Polymarket US','Polymarket Global']){
   await page.selectOption('#provider-select',provider);
   assert.match(await page.locator('#result-status').innerText(),/^888 games/);
   assert.equal(await page.locator('#market-column').innerText(),(provider+' reference').toUpperCase());states++;
  }
  await page.selectOption('#provider-select','DraftKings');
  await page.locator('#game-search').fill('TCU');
  assert.ok((await page.locator('#games-body').innerText()).includes('TCU'));
  const matching=await page.locator('#games-body tr').count();assert.ok(matching>0&&matching<25);
  await page.locator('#games-body button').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-dialog').isVisible(),true);
  assert.equal(await page.locator('#dialog-markets .market-detail').count(),4);
  assert.match(await page.locator('#dialog-footer').innerText(),/Source timing, fees, depth and liquidity remain separate evidence requirements/);
  await page.keyboard.press('Escape');assert.equal(await page.locator('#game-dialog').isVisible(),false);
  await page.locator('#game-search').fill('');
  await page.locator('#view-disagreements').click();
  assert.match(await page.locator('#result-status').innerText(),/^122 games/);
  await page.locator('#next-page').click();assert.equal(await page.locator('#games-body tr').count(),25);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split('\n').length,123);
  assert.match(csv,/retrospective_original_replay/);assert.match(csv,/"not_issued"/);
  assert.doesNotMatch(csv,/s3:\/\/|api_key|raw_bid|model_weights/);
  await page.locator('#disagreements-only').uncheck();await page.locator('[data-view="current"]').click();
  await page.selectOption('#horizon-select','current');
  assert.match(await page.locator('#result-status').innerText(),/^63 games/);
  assert.match(await page.locator('#games-body').innerText(),/No recorded forecast/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.selectOption('#provider-select','Polymarket Global');
  assert.match(await page.locator('#reference-status').innerText(),/57 of 63/);
  await page.locator('#game-search').fill('401869936');
  const latestMissing=await page.locator('#games-body').innerText();
  assert.match(latestMissing,/Latest verified capture has no usable reference/);
  assert.doesNotMatch(latestMissing,/Home \+14\.5 to \+15\.5/);
  await page.selectOption('#horizon-select','latest_available_pregame');
  const repaired=await page.locator('#games-body').innerText();
  assert.match(repaired,/Home \+14\.5 to \+15\.5/);
  assert.match(repaired,/Total 51\.5 to 55\.5/);
  assert.doesNotMatch(repaired,/31\.5|39\.5/);
  await page.getByRole('button',{name:'Details for UL Monroe at Arkansas State',exact:true}).click();
  const globalDetail=page.locator('#dialog-markets .market-detail').nth(3);
  await globalDetail.locator('details summary').first().click();
  assert.match(await globalDetail.innerText(),/Earlier nearest-half threshold: 31\.5/);
  assert.match(await globalDetail.innerText(),/98\.0 percentage points/);
  await page.keyboard.press('Escape');
  await page.selectOption('#horizon-select','current');
  await page.locator('#game-search').fill('401858290');
  const newMedian=await page.locator('#games-body').innerText();
  assert.match(newMedian,/Home \+41\.5 to \+48\.5/);
  assert.match(newMedian,/Total 57\.5 to 59\.5/);
  assert.match(newMedian,/Captured median intervals/);
  assert.match(newMedian,/not expected scores/);
  await page.locator('#game-search').fill('');
  await page.selectOption('#provider-select','Polymarket US');
  assert.match(await page.locator('#result-status').innerText(),/^63 games/);
  const usCard=page.locator('#coverage-cards article').filter({has:page.getByRole('heading',{name:'Polymarket US',exact:true})});
  assert.match(await usCard.innerText(),/Winner 52 \/ 63/);
  assert.match(await usCard.innerText(),/Margin 50 \/ 63 · total 52 \/ 63/);
  assert.match(await usCard.innerText(),/Intervals are not expected scores/);
  await page.selectOption('#horizon-select','latest_available_pregame');
  assert.match(await page.locator('#result-status').innerText(),/^63 games/);
  await page.locator('#source-evidence details summary').click();
  assert.equal(await page.locator('#source-inventory-body [data-source-row]').count(),2742);
  await page.selectOption('#source-season-filter','2024');
  assert.match(await page.locator('#source-inventory-status').innerText(),/920/);
  await page.selectOption('#source-season-filter','2025');
  assert.match(await page.locator('#source-inventory-status').innerText(),/934/);
  await page.selectOption('#source-season-filter','2026');
  await page.selectOption('#source-result-filter','completed');
  assert.match(await page.locator('#source-inventory-status').innerText(),/627/);
  await page.locator('#source-clear-filters').click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.locator('#source-evidence details summary').click();
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});
   await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
   await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`season-${width}-top.png`)});
   await page.locator('#game-explorer').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
   await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`season-${width}-games.png`)});}
 }
 const noScript=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1000}});
 const fallback=await noScript.newPage();await fallback.goto(url);
 assert.equal(await fallback.locator('#games-body tr').count(),888);
 assert.match(await fallback.locator('#games-body tr').first().innerText(),/PDT/);
 assert.match(await fallback.locator('noscript').first().innerText(),/JavaScript is off/);
 assert.equal(await fallback.locator('#source-inventory-body [data-source-row]').count(),2742);
 assert.equal(await fallback.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const frontier=await require('./frontier_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({frontier}));
 const complete=await require('./complete_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({complete}));
 const latestGamesV060=await require('./latest_games_v060_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({latestGamesV060}));
 const latestGamesV061=await require('./latest_games_v061_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({latestGamesV061}));
 const latestGamesV062=await require('./latest_games_v062_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({latestGamesV062}));
 const currentEvidence=await require('./current_evidence_browser_cases.cjs').run({browser,root,screenshots:process.env.FBS_SCREENSHOTS});
 console.log(JSON.stringify({currentEvidence}));
 console.log(JSON.stringify({status:'PASS',viewports:[1440,390],inventory_provider_states:states,
   no_script_games:888,current_week:63,disagreement_csv_rows:122,keyboard_dialog:true,
   supported_current_bounds_verified:true,original_wide_book_diagnostic_preserved:true,
   current_only_native_grid:true,no_older_snapshot_fill_for_missing_latest:true,
   script_errors:0,external_requests:0}));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});


