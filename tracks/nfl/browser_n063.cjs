/* Browser verification of the separately versioned N063 public review. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

module.exports=async function(browser){
 const results=[];
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:1000}});
  const page=await context.newPage(),errors=[],external=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{if(/^https?:/i.test(r.url()))external.push(r.url());});
  try{
   await page.goto(pathToFileURL(path.join(__dirname,'season_review_n063.html')).href);
   await page.waitForFunction(()=>document.body.dataset.ready==='true');
   assert.match(await page.locator('h1').innerText(),/Every game/);
   assert.match(await page.locator('#snapshot-clock').innerText(),/19:16:18/);
   assert.match(await page.locator('#snapshot-clock').innerText(),/21:47:52/);
   assert.equal(await page.locator('[data-selected-study]').count(),2);
   await page.selectOption('#week','all');
   const ids=[];
   while(true){
    ids.push(...await page.locator('#games-table tbody [data-game]').evaluateAll(rows=>rows.map(r=>r.dataset.game)));
    if(await page.locator('#games-next').isDisabled())break;
    await page.locator('#games-next').click();
   }
   assert.equal(ids.length,272);assert.equal(new Set(ids).size,272);
   assert.match(await page.locator('#game-count').innerText(),/272/);
   for(const team of ['LA','LAC']){
    await page.fill('#game-search',team);
    assert.match(await page.locator('#game-count').innerText(),/17 matching games/);
    const matched=await page.locator('#games-table tbody [data-game]').evaluateAll(rows=>rows.map(r=>r.dataset.game));
    assert(matched.every(g=>g.split('_').slice(2).includes(team)));
   }
   await page.fill('#game-search','BUF MIN');
   assert.equal(await page.locator('#games-table tbody [data-game]').count(),1);
   await page.locator('[data-open-game="2026_09_BUF_MIN"]').click();
   assert.equal(await page.locator('#detail-dialog').evaluate(d=>d.open),true);
   const details=await page.locator('#detail-body').innerText();
   assert.match(details,/42\.1%/);assert.match(details,/-1\.7/);assert.match(details,/49\.3/);
   assert.match(details,/19:35:03/);assert.match(details,/19:35:23/);assert.match(details,/19:35:29/);
   assert.match(details,/three separately issued targets/i);
   assert.equal(await page.locator('#game-provider-grid tbody tr').count(),9);
   for(const provider of ['DraftKings','Kalshi','Polymarket'])
    assert.equal(await page.locator('#game-provider-grid [data-provider="'+provider+'"]').count(),3);
   await page.keyboard.press('Escape');
   assert.equal(await page.locator('#detail-dialog').evaluate(d=>d.open),false);
   await page.fill('#game-search','2026_16_CAR_PIT');
   assert.match(await page.locator('#games-table tbody').innerText(),/Kickoff time TBD/);
   await page.locator('[data-open-game="2026_16_CAR_PIT"]').click();
   assert.match(await page.locator('#detail-body').innerText(),/no exact eligible registered cutoff/i);
   await page.locator('#detail-close').click();
   await page.fill('#game-search','');
   await page.locator('#current-week').click();
   assert.equal(await page.locator('#week').inputValue(),'9');
   await page.locator('#next-week').click();assert.equal(await page.locator('#week').inputValue(),'10');
   await page.locator('#prev-week').click();assert.equal(await page.locator('#week').inputValue(),'9');
   for(const year of ['2024','2025']){
    await page.selectOption('#season',year);
    assert.match(await page.locator('#game-count').innerText(),/285 matching games/);
   }
   await page.selectOption('#season','all');
   assert.match(await page.locator('#game-count').innerText(),/842 matching games/);
   assert.match(await page.locator('#metric-count').innerText(),/540 saved rows/);
   await page.locator('[data-dataset="paired"]').click();
   assert.match(await page.locator('#metric-count').innerText(),/252 saved rows/);
   assert.match(await page.locator('#metrics-head').innerText(),/Holm p/i);
   await page.selectOption('#metric-season','2026');
   const actual=await page.evaluate(()=>window.NFL_N063.data.current.paired_comparisons.filter(r=>r.season===2026).length);
   assert.match(await page.locator('#metric-count').innerText(),new RegExp(actual+' saved rows'));
   await page.selectOption('#metric-season','all');
   await page.locator('[data-dataset="retained"]').click();
   assert.match(await page.locator('#metric-count').innerText(),/1349 saved rows/);
   await page.locator('[data-open-metric]').first().click();
   assert.match(await page.locator('#detail-eyebrow').innerText(),/Separate dated archive/);
   assert.match(await page.locator('#detail-body').innerText(),/Retained exact matched provider cohort/);
   await page.locator('#detail-close').click();
   await page.locator('[data-dataset="season"]').focus();await page.keyboard.press('Enter');
   assert.equal(await page.locator('[data-dataset="season"]').getAttribute('aria-selected'),'true');
   await page.selectOption('#chosen-year','2025');
   assert.match(await page.locator('#chosen-policies').innerText(),/2025/);
   assert.match(await page.locator('#source-rows').innerText(),/32 rows/);
   assert.match(await page.locator('#source-rows').innerText(),/330/);
   assert.equal(await page.locator('#provider-cards .provider').count(),3);
   const bodyText=await page.locator('body').innerText();
   assert(!/\b(?:bet|bets|betting|wager|wagers|bankroll|parlay|staking)\b/i.test(bodyText));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,'Viewport has no horizontal overflow');
   assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
   if(process.env.NFL_SCREENSHOTS){
    fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});
    await page.selectOption('#season','2026');await page.locator('#current-week').click();
    await page.selectOption('#chosen-year','2026');
    await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n063-review-'+width+'.png'),fullPage:true});
   }
   results.push({width,current_games_paginated:ids.length,historical_games:570,original_cards:113,
                 provider_target_cells:2448,current_metrics:540,paired_comparisons:252,retained_scoreboards:1349,
                 source_clock_checks:true,distinct_la_and_lac:true,external_requests:0,script_errors:0});
  }finally{await context.close();}
 }
 console.log(JSON.stringify({schema:'nfl.n063.public-browser-verification.v1',status:'PASS',viewports:results}));
 return results;
};

