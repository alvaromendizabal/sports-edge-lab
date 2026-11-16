'use strict';
// Review public static evidence and controls. This test creates no owner science.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=process.env.FBS_V079_SITE||path.join(root,'docs/fbs/v079');
const live=process.env.FBS_V079_LIVE_URL,base=live||'http://fbs-v079.test/';
const data=JSON.parse(fs.readFileSync(path.join(site,'data/review.json'))),games=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(site,'data/games.json.gz')))).games;
require(path.join(site,'app.js'));
const logic=globalThis.FBS079,out=process.env.FBS_SCREENSHOTS;
let browser,checks=0;const check=(value,message)=>{assert.ok(value,message);checks++;};
(async()=>{
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const context=await browser.newContext(),errors=[],failed=[];
  if(!live)await context.route('http://fbs-v079.test/**',async route=>{
    const pathname=decodeURIComponent(new URL(route.request().url()).pathname),file=path.resolve(site,'.'+(pathname==='/'?'/index.html':pathname));
    if(!file.startsWith(site+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Public asset missing'});
    const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json'};
    return route.fulfill({status:200,contentType:types[path.extname(file)]||'application/octet-stream',body:fs.readFileSync(file)});
  });
  for(const width of [1440,390]){
    const page=await context.newPage();await page.setViewportSize({width,height:1000});
    page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
    await page.goto(base,{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready="true"]');
    check(await page.locator('#census-body tr').count()===3,'All three season populations visible');
    for(const c of data.census)check((await page.locator('#census-body').innerText()).includes(c.finals.toLocaleString('en-US')),'Exact final census');
    check((await page.locator('body').innerText()).includes('already been exposed'),'Prior test exposure remains visible');
    check((await page.locator('.report-label').innerText()).includes(data.execution_version),'V080 execution label is visible on the existing route');
    check((await page.locator('#upcoming-summary').innerText()).includes(data.current_execution.verified_current_total_issue_records.toLocaleString('en-US')),'All actual base and derived forecasts are accounted for');
    check((await page.locator('#upcoming-summary').innerText()).includes(data.current_execution.verified_current_derived_issue_records.toLocaleString('en-US')),'Derived fixed-blend count is visible');
    check((await page.locator('#market-summary').innerText()).includes('all 11 reconstructed winner candidates'),'Negative same-provider comparison finding remains visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overview fits viewport');
    if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`fbs-v079-overview-${live?'live':'static'}-${width}.png`),fullPage:true});}
    await page.click('[data-tab="models"]');
    const lanes=await page.locator('#model-lane option').evaluateAll(xs=>xs.map(x=>x.value));
    for(const target of ['winner','margin','total'])for(const lane of lanes){
      await page.selectOption('#model-target',target);await page.selectOption('#model-lane',lane);
      const metrics=await page.locator('#model-metric option').evaluateAll(xs=>xs.map(x=>x.value));
      for(const metric of metrics){await page.selectOption('#model-metric',metric);const expected=logic.groupModels(data.full_population.scorecards,target,lane,metric);
        check(await page.locator('#model-body tr[data-model]').count()===expected.length,'Every fixed-population recipe visible');
        const aliases=await page.locator('#model-body tr[data-model]').evaluateAll(xs=>xs.map(x=>x.dataset.model));
        assert.deepEqual(aliases,expected.map(x=>x.alias));checks++;
      }
    }
    check((await page.locator('#nomination-note').innerText()).includes('never used to order'),'2026 cannot set table order');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Model table scrolls inside viewport');
    if(out)await page.screenshot({path:path.join(out,`fbs-v079-models-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="markets"]');
    for(const season of [2024,2025,2026])for(const status of ['all','final','unfinished'])for(const target of ['winner','margin','total']){
      await page.selectOption('#market-season',String(season));await page.selectOption('#market-status',status);await page.selectOption('#market-target',target);
      const subset=logic.subsetGames(games,season,status);
      for(const provider of ['draftkings','kalshi','polymarket_global','polymarket_us']){
        const expected=logic.providerCoverage(subset,provider,target),row=page.locator(`#market-body tr[data-provider="${provider}"]`);
        for(const key of ['reference','display','qualified','missing','denominator'])check(await row.locator(`[data-coverage="${key}"]`).innerText()===expected[key].toLocaleString('en-US'),'Exact provider denominator and evidence state');
        for(const [prefix,state,fn] of [['current','CURRENT_SOURCE_PROJECTION_VERIFIED',logic.currentCoverage],['historical','HISTORICAL_SOURCE_PROJECTION_VERIFIED',logic.historicalCoverage]]){
          const projection=data[prefix+'_source_coverage'],attached=projection?.state===state&&(prefix==='historical'||season===2026),c=fn(subset,provider,target),sourceRow=page.locator(`#${prefix}-market-body tr[data-${prefix}-provider="${provider}"]`);
          for(const key of ['reference','qualified','denominator'])check(await sourceRow.locator(`[data-${prefix}-coverage="${key}"]`).innerText()===(key==='denominator'||attached&&c.covered===subset.length?c[key].toLocaleString('en-US'):'Not attached'),'Capture coverage retains exact denominator and missing projection');
        }
        if(status==='final'){
          await page.selectOption('#comparison-provider',provider);
          const cards=(data.market_comparison?.scorecards||[]).filter(r=>r.season===season&&r.target===target&&r.provider===provider);
          check(await page.locator('#market-comparison-body tr[data-market-model]').count()===cards.length,'All model rows use fixed provider cohort');
          for(const metric of await page.locator('#comparison-metric option').evaluateAll(xs=>xs.map(x=>x.value))){await page.selectOption('#comparison-metric',metric);check(await page.locator('#market-comparison-body tr[data-market-model]').count()===cards.length,'Metric control preserves provider population');}
        }

      }
    }
    await page.click('[data-tab="games"]');
    for(const season of [2024,2025,2026]){await page.selectOption('#game-season',String(season));check((await page.locator('#game-count').innerText()).startsWith(games.filter(g=>g.season===season).length.toLocaleString('en-US')),'All observed games remain in each season');}
    await page.selectOption('#game-status','unfinished');check((await page.locator('#game-count').innerText()).startsWith(games.filter(g=>g.season===2026&&g.status!=='final').length.toLocaleString('en-US')),'Pending and unresolved retained');
    const first=await page.locator('#game-body').innerText();if(await page.locator('#game-next').isEnabled()){await page.click('#game-next');check(await page.locator('#game-body').innerText()!==first,'Next page changes games');}
    await page.selectOption('#game-provider','draftkings');await page.selectOption('#game-provider-state','qualified');
    const qualified=games.filter(g=>g.season===2026&&g.status!=='final'&&logic.combinedProviderFlags(g,'draftkings','winner').qualified).length;
    check((await page.locator('#game-count').innerText()).startsWith(qualified.toLocaleString('en-US')),'Qualified filter does not include mere references');
    await page.selectOption('#game-provider-state','all');await page.selectOption('#game-status','all');
    const game=games.find(g=>g.season===2026);await page.fill('#game-search',game.id);await page.click('[data-open-game]');
    check(await page.locator('#game-dialog').isVisible(),'Per-game evidence opens');check((await page.locator('#game-dialog-body').innerText()).includes('Quote')||(await page.locator('#game-dialog-body').innerText()).includes('Not retained'),'Source clocks or absence visible');await page.click('#dialog-close');
    await page.fill('#game-search','');
    const downloadPromise=page.waitForEvent('download');await page.click('#download-games');const download=await downloadPromise;check(download.suggestedFilename()==='FBS_2026_COMPARISON.csv','Filtered comparison downloadable');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Game table contained on mobile');
    await page.click('[data-tab="diagnostics"]');check((await page.locator('#diagnostic-note').innerText()).includes('47-game'),'Narrow issued cohort is explicitly diagnostic');
    await page.click('[data-tab="execution"]');check((await page.locator('#new-execution').innerText()).includes('None'),'No promotion claimed');
    check((await page.locator('#current-execution').innerText()).includes(data.current_execution.verified_current_total_issue_records.toLocaleString('en-US')),'Current V080 execution is separate from predecessor accounting');
    check((await page.locator('#current-execution-note').innerText()).includes('do not establish novel models'),'Actual fit calls are not presented as novel learning');
    await page.focus('[data-tab="overview"]');await page.keyboard.press('ArrowRight');check(await page.locator('#panel-models').isVisible(),'Keyboard tabs work');
    await page.close();
  }
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  const receipt={status:'PASS',checks,site:live?'HOSTED_PUBLIC_URL':'EXACT_STATIC_PUBLIC_ASSETS',viewport_widths:[1440,390],source_as_of:data.source_as_of,fixture_source_as_of:data.fixture_source_as_of,scorecards:data.full_population.scorecards.length,game_count:games.length,owner_fits:0,forecast_issues:0,promotion:false};
  if(out)fs.writeFileSync(path.join(out,`FBS_V079_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));await browser.close();
})().catch(async error=>{console.error(error);if(browser)await browser.close();process.exitCode=1;});
