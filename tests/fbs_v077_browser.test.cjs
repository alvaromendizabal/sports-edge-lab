'use strict';
// Hosted real-browser verification of saved public data; no owner science.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/fbs/v077');
const live=process.env.FBS_V077_LIVE_URL,base=live||'http://fbs-v077.test/';
const out=process.env.FBS_SCREENSHOTS;
const data=JSON.parse(fs.readFileSync(path.join(site,'data/review.json'),'utf8'));
const census=JSON.parse(fs.readFileSync(path.join(site,'data/games.json'),'utf8')).games;
const percent=x=>(100*x).toFixed(3)+'%';
let browser,checks=0;
const check=(value,message)=>{assert.ok(value,message);checks++;};
(async()=>{
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const context=await browser.newContext(),errors=[],failed=[],httpErrors=[];
  if(!live)await context.route('http://fbs-v077.test/**',async route=>{
    const pathname=decodeURIComponent(new URL(route.request().url()).pathname);
    const file=path.resolve(site,'.'+(pathname==='/'?'/index.html':pathname));
    if(!file.startsWith(site+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Missing public asset'});
    const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json'};
    return route.fulfill({status:200,contentType:mime[path.extname(file)]||'text/plain',body:fs.readFileSync(file)});
  });
  for(const width of [1440,390]){
    const page=await context.newPage();await page.setViewportSize({width,height:1000});
    page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
    page.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()});});
    await page.goto(base,{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready="true"]');
    check(await page.locator('#stat-fits').innerText()==='201','Actual new research fits');
    check(await page.locator('#stat-reused').innerText()==='26','Prior states kept separate');
    check(await page.locator('#stat-fixtures').innerText()==='888','Current observed census');
    check(await page.locator('#stat-issues').innerText()==='0','No backdated new issues');
    check((await page.locator('#issued-evidence').innerText()).includes('0 / 3'),'Prior original archive retained');
    check((await page.locator('#issued-evidence').innerText()).includes('2 / 5'),'New older-issue outcomes retained');
    check((await page.locator('#issued-evidence').innerText()).includes('3,588'),'Separate shadow journal retained');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overview has no page overflow');
    if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`fbs-v077-result-${live?'live':'static'}-${width}.png`),fullPage:true});}
    await page.click('[data-tab="scores"]');
    for(const season of [2024,2025,2026])for(const target of ['winner','margin','total']){
      await page.selectOption('#score-season',String(season));await page.selectOption('#score-target',target);
      const options=await page.locator('#score-metric option').evaluateAll(xs=>xs.map(x=>x.value));
      for(const metric of options){
        await page.selectOption('#score-metric',metric);
        const expected=data.scores.filter(r=>r.season===season&&r.target===target);
        check(await page.locator('#score-body tr').count()===4,'Four policies in every saved season/target');
        for(const r of expected){
          const value=metric==='accuracy'||metric==='interval80_coverage'?percent(r[metric]):r[metric].toFixed(6);
          check(await page.locator(`#score-body tr[data-policy="${r.policy}"] td`).nth(1).innerText()===value,'Saved metric matches exact public aggregate');
        }
        check((await page.locator('#score-cohort').innerText()).includes(expected[0].n.toLocaleString('en-US')),'Same-cohort denominator shown');
      }
    }
    await page.click('[data-tab="weighted"]');
    for(const target of ['winner','margin','total'])for(const weight of ['primary','equal','current65'])for(const window of ['FULL_OBSERVED_SEASON','MATCHED_ELAPSED_SEASON_DAYS']){
      await page.selectOption('#weighted-target',target);await page.selectOption('#weighted-weight',weight);await page.selectOption('#weighted-window',window);
      const expected=data.comparisons.filter(r=>r.target===target&&r.weight_policy===weight&&r.comparison_window===window);
      check(await page.locator('#weighted-body tr').count()===3,'All challenger policies remain visible');
      for(const r of expected){
        const cells=page.locator(`#weighted-body tr[data-policy="${r.policy}"] td`);
        check(await cells.nth(1).innerText()===percent(r.weighted_relative_skill),'Saved weighted skill');
        check(await cells.nth(2).innerText()===`[${percent(r.adjusted95_interval[0])}, ${percent(r.adjusted95_interval[1])}]`,'Saved adjusted interval');
      }
      check(await page.locator('#interval-chart svg circle').count()===3,'Three saved interval points');
      check((await page.locator('#weighted-cohort').innerText()).includes(window==='FULL_OBSERVED_SEASON'?'918':'634'),'Window-specific cohort shown');
    }
    check((await page.locator('#weighted-limits').innerText()).includes('54 exploratory'),'Multiplicity limit remains visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Weighted view has no page overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v077-weighted-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="games"]');
    for(const season of [2024,2025,2026]){
      await page.selectOption('#game-season',String(season));
      check((await page.locator('#game-count').innerText()).startsWith(String(census.filter(g=>g.season===season).length)),'Every observed season retained');
    }
    check(await page.locator('#game-body tr').count()===25,'Game paging');
    const first=await page.locator('#game-body').innerText();await page.click('#game-next');
    check(await page.locator('#game-body').innerText()!==first,'Paging changes visible games');
    await page.selectOption('#game-status','final');check((await page.locator('#game-count').innerText()).startsWith('696'),'All current finals');
    await page.selectOption('#game-status','tbd');check((await page.locator('#game-count').innerText()).startsWith('53'),'Current TBD count excludes old-season TBD');
    await page.selectOption('#game-status','all');await page.selectOption('#game-coverage','prepared');
    check((await page.locator('#game-count').innerText()).startsWith('121'),'Prepared games remain unissued');
    check((await page.locator('#game-body').innerText()).includes('Prepared · not issued'),'Prepared label explicit');
    await page.selectOption('#game-coverage','missing');check((await page.locator('#game-count').innerText()).startsWith('71'),'All missing current preparations');
    await page.selectOption('#game-coverage','all');await page.fill('#game-search','Florida');
    check((await page.locator('#game-body').innerText()).includes('Florida'),'Team search works');await page.fill('#game-search','');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile game cards have no page overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v077-games-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="execution"]');check(await page.locator('#benchmark-body tr').count()===6,'All measured schedules retained');
    check((await page.locator('#panel-execution').innerText()).includes('14 parts'),'Multipart return explicit');
    check((await page.locator('#panel-execution').innerText()).includes('no manual upload'),'No manual return-upload requirement');
    check(await page.locator('#gate-body tr').count()===6,'All acceptance statuses shown');
    await page.locator('[data-tab="execution"]').focus();await page.keyboard.press('Home');
    check(await page.locator('[data-tab="result"]').getAttribute('aria-selected')==='true','Keyboard tab navigation');
    await page.close();
  }
  check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');check(httpErrors.length===0,'No HTTP failures');
  const receipt={status:'PASS',checks,viewports:[1440,390],live_url:live||null,source_as_of:data.source_as_of,
    owner_version:'V076',report_version:'V077',new_fits_by_publication:0,owner_new_research_fits:201,owner_new_issues:0,
    v077_owner_execution_claimed:false,errors,failed,httpErrors};
  if(out)fs.writeFileSync(path.join(out,`FBS_V077_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
