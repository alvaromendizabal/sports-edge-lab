'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const root = __dirname;
const load = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const data = load('week-12-field-notes/n211/week-12-picks.json');
const previous = load('week-12-field-notes/n210/week-12-picks.json');
const options = load('week-12-field-notes/n211/all-book-options.json');
const status = load('n211-execution-status.json');
const weather = load('week-12-field-notes/n211/weather.json');
const output = process.env.NFL_CURRENT_EVIDENCE || path.join(process.env.RUNNER_TEMP || '/tmp','nfl-n211-browser');
fs.mkdirSync(output,{recursive:true});
const server=http.createServer((req,res)=>{
  const rel=decodeURIComponent(req.url.split('?')[0]);
  const file=path.resolve(root,'.'+rel+(rel.endsWith('/')?'index.html':''));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  fs.readFile(file,(err,content)=>{if(err){res.writeHead(404);return res.end();}res.setHeader('Content-Type',({'.png':'image/png','.jpg':'image/jpeg','.json':'application/json','.js':'text/javascript','.css':'text/css','.ttf':'font/ttf','.woff':'font/woff','.woff2':'font/woff2','.svg':'image/svg+xml'})[path.extname(file)]||'text/html; charset=utf-8');res.end(content);});
});
(async()=>{
  assert.equal(data.games.length,16);assert.equal(new Set(data.games.map(g=>g.id)).size,16);
  assert.deepEqual(['final','started','upcoming'].map(s=>data.games.filter(g=>g.state===s).length),[4,1,11]);
  for(const game of data.games.filter(g=>g.retained_original)){
    const prior=previous.games.find(g=>g.id===game.id);assert(prior);
    for(const key of ['picks','winner','win_probability','margin','total','issue'])assert.deepEqual(game[key],prior[key],game.id+' '+key);
  }
  for(const game of data.games.filter(g=>!g.retained_original)){
    assert.equal(game.issue,data.forecast_issued_utc);assert(Date.parse(game.issue)<Date.parse(game.kickoff_utc));
    assert.deepEqual(Object.keys(game.picks).sort(),['points','probability','wins']);
    assert(game.total>=Math.abs(game.margin));
    for(const targets of Object.values(game.picks))for(const pick of Object.values(targets)){
      assert(pick.probability>=0&&pick.probability<=1);assert(pick.p_push>=0&&pick.p_push<=1);
      assert(Date.parse(pick.quote_utc)<=Date.parse(pick.issued_utc));
      assert(Math.abs(pick.p_win-pick.probability*(1-pick.p_push))<0.00015);
    }
  }
  for(const c of data.champions)assert.equal(c.wins+c.losses+c.settlement_pushes,c.completed_population);
  assert.equal(status.completed_population,167);assert.equal(status.v13_status,'INCOMPLETE');
  assert.equal(status.optimizer_completions,2560);assert.equal(status.new_fitting_units,160);
  assert.equal(status.forecast_issued_utc,data.forecast_issued_utc);
  assert.equal(options.options.length,128);assert.equal(data.research_option_rows,2314);
  assert.deepEqual(Object.fromEntries(['draftkings','kalshi','polymarket'].map(s=>[s,options.options.filter(r=>r.source===s).length])),{draftkings:44,kalshi:40,polymarket:44});
  assert(!options.options.some(r=>r.source==='kalshi'&&r.game_id==='2026_12_NE_LAC'));
  for(const row of options.options){
    assert(Math.abs(row.p_win+row.p_loss+row.p_push-1)<0.00015);
    assert(Math.abs(row.expected_profit_per_unit-(row.p_win*(row.decimal_price-1)-row.p_loss))<0.00025);
  }
  assert.equal(weather.model_application,'NOT_APPLIED_TO_N211_PICKS');
  assert.equal(weather.games.length,11);
  assert.equal(new Set(weather.games.map(g=>g.game_id)).size,11);
  for(const game of weather.games){
    assert(data.games.some(g=>g.id===game.game_id&&!g.retained_original));
    assert(Date.parse(game.captured_utc||weather.captured_utc)>Date.parse(data.forecast_issued_utc));
    for(const sample of game.samples||[])if(sample.precip_probability!==null&&sample.precip_probability!==undefined)assert(sample.precip_probability>=0&&sample.precip_probability<=1);
  }
  assert.doesNotMatch(JSON.stringify({data,options,status,weather}),/s3:\/\/|\/home\/sagemaker|conditional_cdf|expanded_balanced|private-research|N211X\//);
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true});const errors=[];
  try{
    const origins=[{label:'local',url:`http://127.0.0.1:${server.address().port}/`}];
    if(process.env.NFL_N211_VERIFY_HOSTED==='1'){
      const receipt=load('publication-n211.json');assert.match(receipt.status,/^DEPLOYED/);
      origins.push({label:'hosted',url:receipt.public_url});
    }
    for(const origin of origins)for(const width of [1440,390]){
      const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>errors.push(e.message));
      await page.clock.install({time:new Date('2026-11-28T12:00:00Z')});
      const response=await page.goto(new URL('week-12-field-notes/n211/',origin.url).href);assert.equal(response.status(),200);
      assert.equal(await page.locator('article[data-game]:visible').count(),16);
      await page.waitForFunction(()=>document.documentElement.dataset.weatherLoaded==='true');
      assert.equal(await page.locator('[data-weather-game]').count(),11);
      const weatherPanel=page.locator('[data-weather-game]').first();
      await weatherPanel.locator('summary').click();
      assert.match(await weatherPanel.innerText(),/not used in the frozen N211 picks/);
      assert.equal(await weatherPanel.locator('tbody tr').count(),3);
      assert.match(await weatherPanel.innerText(),/Enclosed stadium · fixed roof/);
      assert.match(await weatherPanel.locator('summary').innerText(),/Enclosed stadium · outdoor forecast/);
      assert.match(await page.locator('[data-weather-game="2026_12_BAL_HOU"] summary').innerText(),/Retractable roof · unknown · outdoor forecast/);
      assert.match(await page.locator('[data-weather-game="2026_12_NE_LAC"] summary').innerText(),/Open-air canopy forecast/);
      assert.match(await page.locator('[data-weather-game="2026_12_LV_CLE"] summary').innerText(),/Open-air stadium forecast/);
      assert.match(await weatherPanel.innerText(),/Forecast (captured|check)/);

      for(const [name,count] of [['Upcoming',11],['Started',1],['Final',4],['All games',16]]){
        await page.getByRole('button',{name,exact:true}).click();assert.equal(await page.locator('article[data-game]:visible').count(),count);
      }
      await page.getByRole('textbox',{name:'Search teams'}).fill('DEN');assert.equal(await page.locator('article[data-game]:visible').count(),1);
      assert.match(await page.locator('article[data-game]:visible').innerText(),/DEN -4\.5/);
      await page.getByRole('textbox',{name:'Search teams'}).fill('GB');const preserved=page.locator('article[data-game]:visible');
      await preserved.locator('summary').click();assert.match(await preserved.innerText(),/Point accuracy/);
      await page.getByRole('textbox',{name:'Search teams'}).fill('');
      for(const [source,count] of [['draftkings',44],['kalshi',40],['polymarket',44],['',128]]){
        await page.locator(`[data-source="${source}"]`).click();assert.equal(await page.locator('#market-count').innerText(),`${count} of 128 observed options`);
      }
      await page.locator('#market-next').click();assert.equal(await page.locator('#market-page').innerText(),'Page 2 / 6');
      await page.locator('#market-game').selectOption('2026_12_NE_LAC');assert.equal(await page.locator('#market-count').innerText(),'8 of 128 observed options');
      await page.locator('#market-source').selectOption('kalshi');assert.equal(await page.locator('#market-body tr').count(),0);
      await page.locator('#market-source').selectOption('draftkings');await page.locator('#market-target').selectOption('total');assert.equal(await page.locator('#market-body tr').count(),2);
      await page.locator('#market-sort').selectOption('probability');
      assert.equal(await page.locator('#phone img').count(),4);
      for(const image of await page.locator('#phone img').all()){
        await image.scrollIntoViewIfNeeded();assert.deepEqual(await image.evaluate(async e=>{await e.decode();return[e.naturalWidth,e.naturalHeight];}),[1170,2240]);
      }
      for(const link of await page.locator('#circa a[href$=".png"]').all()){
        const url=await link.getAttribute('href');assert.equal((await page.request.get(new URL(url,page.url()).href)).status(),200);
      }
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await page.screenshot({path:path.join(output,`n211-board-${origin.label}-${width}.png`),fullPage:true});
      await page.goto(origin.url,{waitUntil:'domcontentloaded'});
      assert.equal(await page.title(),'Week 12 · JMac’s Model Picks | Sports Edge Lab');
      const currentReader=load('publication.json');
      const currentLink=page.locator('#n214-reader-update > a[href="week-12-field-notes/n214/"]');
      assert.equal(await currentLink.count(),1);
      assert.equal(new URL(await currentLink.getAttribute('href'),page.url()).pathname,new URL(currentReader.field_notes_url).pathname);
      assert.match(await page.locator('meta[name="description"]').getAttribute('content'),/Exposed 2026 selection/);
      assert.match(await page.locator('meta[property="og:title"]').getAttribute('content'),/N211/);
      const originalN211=page.locator('#n214-reader-update nav a[href="week-12-field-notes/n211/"]');
      assert.equal(await originalN211.count(),1);
      assert.equal(await originalN211.innerText(),'Original N211');
      assert.match(await page.locator('meta[name="description"]').getAttribute('content'),/eleven new pregame issues and five preserved/i);
      assert.match(await page.locator('#n206-complete-population-notice').innerText(),/N206 completed/);
      assert.equal(await page.locator('#n206-complete-population-notice a[href="week-12-field-notes/n206/"]').count(),1);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await page.screenshot({path:path.join(output,`n211-entry-${origin.label}-${width}.png`),fullPage:false});
      await page.close();
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'n211-browser.json'),JSON.stringify({status:'PASS',games:16,retained_originals:5,new_issues:11,public_option_rows:128,viewports:[1440,390],origins:origins.map(o=>o.label)},null,2));
    console.log('PASS N211 data invariants, original preservation, options filters, pagination and desktop/mobile browser checks');
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});

