// Actual offline browser controls and reopen rendering of selected NFL outputs.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.NFL_BROWSER_EXECUTABLE||undefined});
 const source=JSON.parse(fs.readFileSync(path.join(__dirname,'selected_forecasts_n073.json'),'utf8'));
 let states=0;const errors=[],requests=[];
 try{
  const page=await browser.newPage({acceptDownloads:true});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url());});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   await page.goto('file://'+path.join(__dirname,'season_review_n073.html'));
   await page.locator('#games tr').first().waitFor();
   assert.equal(await page.locator('#games tr').count(),source.games.length);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'outer-page overflow');
   assert.equal(await page.locator('h1').count(),1);
   assert.match(await page.locator('#owner-status').innerText(),/verified minimum 21 native fits and 48 meta fits/);states++;
   assert.equal(await page.locator('#latest-sources tr').count(),4);states++;
   assert.match(await page.locator('#coverage-note').innerText(),new RegExp(String(source.counts.games_with_any_preserved_evidence)));
   await page.selectOption('#status','tbd');
   assert.equal(await page.locator('#games tr').count(),source.counts.official_time_tbd_games);
   assert.doesNotMatch(await page.locator('#games').innerText(),/05:00:00 UTC/);
   states++;
   await page.selectOption('#status','completed');
   assert.equal(await page.locator('#games tr').count(),source.counts.completed_games);states++;
   await page.selectOption('#status','future');
   assert.equal(await page.locator('#games tr').count(),source.counts.future_games);states++;
   await page.selectOption('#status','');
   for(const group of ['current_forecasts','earlier_saved_forward','prior_selected_reconstruction']){
    await page.selectOption('#evidence-filter',group);
    const expected=source.games.filter(g=>Object.values(g.targets).some(t=>t[group].length)).length;
    assert.equal(await page.locator('#games tr').count(),expected,group);states++;
   }
   await page.selectOption('#evidence-filter','missing');
   assert.equal(await page.locator('#games tr').count(),source.counts.games_without_prediction_evidence_in_this_projection);states++;
   await page.selectOption('#evidence-filter','');
   await page.getByLabel('Team or game').fill('SEA');
   assert.equal(await page.locator('#games tr').count(),source.games.filter(g=>[g.home_team,g.away_team,g.game_id].join(' ').toLowerCase().includes('sea')).length);states++;
   await page.getByLabel('Team or game').fill('NO_MATCH_EXPECTED');assert.equal(await page.locator('#empty').isVisible(),true);states++;
   await page.getByLabel('Team or game').fill('');
   await page.locator('#week').focus();await page.keyboard.press('ArrowDown');
   const week=await page.locator('#week').inputValue();assert.notEqual(week,'');
   assert.equal(await page.locator('#games tr').count(),source.games.filter(g=>String(g.week)===week).length);states++;
   await page.selectOption('#week','');
   for(const group of ['primary','fallback','all']){
    await page.selectOption('#role-group',group);
    assert.equal(await page.locator('#champions tr').count(),source.selected_historical_roles.filter(r=>group==='all'||r.role_id.startsWith(group+'_')).length);states++;
   }
   await page.selectOption('#role-group','all');
   for(const horizon of ['3600','7200']){
    await page.selectOption('#role-horizon',horizon);
    assert.equal(await page.locator('#champions tr').count(),source.selected_historical_roles.filter(r=>String(r.comparison_horizon_seconds)===horizon).length);states++;
   }
   await page.selectOption('#role-horizon','');
   await page.selectOption('#role-group','primary');
   await page.selectOption('#status','future');
   const downloadPromise=page.waitForEvent('download');await page.locator('#download').click();
   const download=await downloadPromise;const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
   assert.equal(exported.games.length,source.counts.future_games);assert.equal(exported.selection_filters.status,'future');states++;
   await page.reload();await page.locator('#games tr').first().waitFor();
   assert.equal(await page.locator('#games tr').count(),source.games.length);states++;
   if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-selected-season-n073-'+width+'.png'),fullPage:true});}
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  console.log(JSON.stringify({status:'PASS',viewport_widths:[1440,390],states,all_games:source.games.length,console_errors:errors,external_requests:requests,reopen_render_verified:true}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

