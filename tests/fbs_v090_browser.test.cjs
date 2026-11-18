'use strict';
// Real browser checks on public saved evidence. No remote services or owner research.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const site=path.resolve(__dirname,'../docs/fbs/v090'),standalone=process.env.FBS_V090_STANDALONE?path.resolve(process.env.FBS_V090_STANDALONE):null;
const data=JSON.parse(fs.readFileSync(path.join(site,'data/review.json'))),inventory=JSON.parse(fs.readFileSync(path.join(site,'data/games.json')));
require(path.join(site,'app.js'));const L=globalThis.FBS090;
const out=process.env.FBS_SCREENSHOTS?path.resolve(process.env.FBS_SCREENSHOTS):null,base='http://fbs-v090.test/';
let browser,checks=0;const check=(condition,message)=>{assert.ok(condition,message);checks++;};
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'fbs-v090-browser-'));
function rowsFor(target,metric,profile){return data.selection.ranks.filter(r=>r.target===target&&r.metric===metric&&r.profile===profile).sort((a,b)=>(a.rank??Infinity)-(b.rank??Infinity)||a.alias.localeCompare(b.alias));}
async function routeContext(context,mode,bad=false){
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());if(url.origin!==new URL(base).origin)return route.abort();
    if(mode==='standalone')return url.pathname==='/'?route.fulfill({status:200,contentType:'text/html',body:fs.readFileSync(standalone)}):route.fulfill({status:404,body:'No network asset exists for standalone report'});
    const file=path.resolve(site,'.'+(url.pathname==='/'?'/index.html':url.pathname));
    if(!file.startsWith(site+path.sep)||!fs.existsSync(file)||(bad&&url.pathname==='/data/review.json'))return route.fulfill({status:404,body:'Evidence unavailable'});
    const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};
    return route.fulfill({status:200,contentType:types[path.extname(file)]||'text/plain',body:fs.readFileSync(file)});
  });
}
(async()=>{
  browser=await chromium.launch({headless:true,args:['--no-sandbox'],executablePath:process.env.FBS_CHROMIUM_PATH||undefined});
  const modes=standalone?['source','standalone']:['source'];const receipts=[];
  for(const mode of modes)for(const width of [1440,390]){
    const context=await browser.newContext({acceptDownloads:true,viewport:{width,height:1000}});await routeContext(context,mode);
    const page=await context.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
    await page.goto(base,{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready="true"]');
    check((await page.locator('#stat-fits').innerText())==='90','Actual fit count visible');
    check((await page.locator('#stat-policies').innerText())==='397','Composite-policy count visible');
    check((await page.locator('#stat-games').innerText())==='2,605','Full completed population visible');
    check((await page.locator('#tranche-title').innerText()).includes('90 / 90'),'Actual finite tranche complete');
    check((await page.locator('#prepared-facts').innerText()).includes('936'),'Prepared campaign is separate');
    check((await page.locator('#prepared-facts').innerText()).includes('84'),'Fixed blends are separately counted');
    check((await page.locator('#publication-state').innerText()).includes('deployment pending'),'Publication status is truthful');
    check((await page.locator('.snapshot dt').first().innerText())==='Game manifest as of','Manifest cutoff is labelled separately from later cost and finalization');
    check((await page.locator('.qualification').innerText()).includes('cannot become an untouched test'),'Prior test exposure visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overview fits viewport');
    await page.keyboard.press('Tab');check((await page.evaluate(()=>document.activeElement.textContent)).includes('Skip to research'),'Keyboard skip link is first focus');
    if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`fbs-v090-${mode}-overview-${width}.png`)});}
    for(const profile of L.PROFILES){
      await page.selectOption('#profile',profile);
      const leaders=await page.locator('#leaders-body tr').evaluateAll(rows=>rows.map(r=>({objective:r.dataset.objective,alias:r.dataset.alias})));
      check(leaders.length===9,'Every objective leader rendered');
      for(const row of leaders){const [target,metric]=row.objective.split(':'),saved=data.selection.leaders.find(x=>x.profile===profile&&x.target===target&&x.metric===metric);check(saved.alias===row.alias,'Displayed leader matches saved validation lock');}
      for(const objective of L.OBJECTIVES){await page.selectOption('#objective',objective.id);const expected=rowsFor(objective.target,objective.metric,profile).slice(0,L.PAGE_SIZE).map(r=>r.alias);assert.deepEqual(await page.locator('#models-body tr[data-policy]').evaluateAll(rows=>rows.map(r=>r.dataset.policy)),expected);checks++;}
    }
    await page.selectOption('#profile','50/50');await page.selectOption('#objective','margin:crps');
    const allAliases=[];
    do{allAliases.push(...await page.locator('#models-body tr[data-policy]').evaluateAll(rs=>rs.map(r=>r.dataset.policy)));if(await page.locator('#model-next').isDisabled())break;await page.click('#model-next');}while(true);
    assert.deepEqual(allAliases,rowsFor('margin','crps','50/50').map(r=>r.alias));checks++;
    check((await page.locator('#models-body').innerText()).includes('Not available'),'Missing CRPS visible');
    check((await page.locator('#models-body').innerText()).includes('0 / 919 games'),'Missing CRPS keeps full denominator');
    await page.selectOption('#objective','winner:log_loss');await page.selectOption('#family','CatBoost');await page.selectOption('#input-mode','Market only');
    check(await page.locator('#models-body tr[data-policy]').count()>0,'Family and input controls are live');
    check((await page.locator('#models-body tr[data-policy]').first().innerText()).includes('CatBoost'),'Selected family rendered');
    await page.fill('#model-search','NO SUCH PUBLIC POLICY');check((await page.locator('#models-body').innerText()).includes('No saved policy'),'Empty-state honest');
    await page.fill('#model-search','');await page.selectOption('#family','all');await page.selectOption('#input-mode','all');await page.selectOption('#objective','total:crps');
    const downloadPromise=page.waitForEvent('download');await page.click('#download-models');const download=await downloadPromise;const dlPath=path.join(tmp,mode+'-'+width+'-models.csv');await download.saveAs(dlPath);
    assert.equal(fs.readFileSync(dlPath,'utf8'),L.csv(L.modelExport(L.rankedModels(data,'total:crps','50/50'),'crps','50/50')));checks++;
    if(out){await page.locator('#models').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`fbs-v090-${mode}-models-${width}.png`)});}
    check(await page.locator('#providers .provider').count()===4,'All four provider products remain separate');
    check((await page.locator('#findings').innerText()).includes('worse 2026 test results on 8 of 9'),'Negative finding visible');
    check(await page.locator('#book-list span').count()===17,'Actual admitted source count visible');
    if(out){await page.locator('#sources').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`fbs-v090-${mode}-sources-${width}.png`)});}
    await page.selectOption('#game-season','2026');await page.selectOption('#game-status','pending');
    check((await page.locator('#game-summary').innerText()).startsWith('136 games'),'All pending fixtures retained');
    await page.selectOption('#game-status','unresolved');check(await page.locator('#games-body tr[data-game]').count()===10,'Unresolved kickoffs retained');
    await page.selectOption('#game-season','2024');await page.selectOption('#game-status','pending');check(await page.locator('#games-body tr[data-game]').count()===1,'Older unconfirmed fixture remains separate');
    await page.selectOption('#game-season','all');await page.selectOption('#game-status','all');await page.fill('#game-search','Alabama');check(await page.locator('#games-body tr[data-game]').count()>0,'Team search is live');
    await page.fill('#game-search','');await page.selectOption('#game-season','2026');await page.selectOption('#game-status','pending');
    const gameDownload=page.waitForEvent('download');await page.click('#download-games');const gd=await gameDownload,gp=path.join(tmp,mode+'-'+width+'-games.csv');await gd.saveAs(gp);
    assert.equal(fs.readFileSync(gp,'utf8'),L.csv(L.gameExport(L.filteredGames(inventory.games,'2026','pending'))));checks++;
    if(mode==='standalone'){
      const jsonDownload=page.waitForEvent('download');await page.locator('a[download="FBS_V090_PUBLIC_AGGREGATE_REVIEW.json"]').click();const jd=await jsonDownload,jp=path.join(tmp,mode+'-'+width+'-review.json');await jd.saveAs(jp);assert.deepEqual(JSON.parse(fs.readFileSync(jp)),data);checks++;
      check(requests.every(url=>url===base||url.startsWith('blob:')),'Standalone report made no runtime network requests');
    }
    if(out){await page.locator('#execution').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`fbs-v090-${mode}-execution-${width}.png`)});}
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'All sections contain their horizontal overflow');check(errors.length===0,'No page errors');
    receipts.push({mode,width,page_errors:errors,runtime_request_count:requests.filter(x=>x!==base&&!x.startsWith('blob:')).length});await context.close();
  }
  const bad=await browser.newContext();await routeContext(bad,'source',true);const broken=await bad.newPage();await broken.goto(base,{waitUntil:'networkidle'});await broken.waitForSelector('html[data-ready="error"]');check((await broken.locator('#load-error').innerText()).includes('No stale replacement'),'Missing evidence fails closed');check((await broken.locator('#stat-fits').innerText())==='—','Missing evidence cannot display stale fit counts');await bad.close();
  const receipt={schema:'fbs.public.browser-review.v090',status:'PASS',checks,variants:receipts,owner_research_executed:0,website_deployed:false,browser_version:browser.version()};
  if(out)fs.writeFileSync(path.join(out,'FBS_V090_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();fs.rmSync(tmp,{recursive:true,force:true});});
