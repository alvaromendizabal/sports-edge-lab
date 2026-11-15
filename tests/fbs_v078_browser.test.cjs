'use strict';
// Hosted real-browser verification of saved public data; no owner science.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/fbs/v078');
const live=process.env.FBS_V078_LIVE_URL,base=live||'http://fbs-v078.test/';
const out=process.env.FBS_SCREENSHOTS;
const data=JSON.parse(fs.readFileSync(path.join(site,'data/review.json'),'utf8'));
const census=JSON.parse(require('node:zlib').gunzipSync(fs.readFileSync(path.join(site,'data/games.json.gz'))).toString()).games;
const percent=x=>(100*x).toFixed(3)+'%';
let browser,checks=0;
const check=(value,message)=>{assert.ok(value,message);checks++;};
(async()=>{
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const context=await browser.newContext(),errors=[],failed=[],httpErrors=[];
  if(!live)await context.route('http://fbs-v078.test/**',async route=>{
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
    check(await page.locator('#stat-fits').innerText()==='35','Actual new model fits');
    check(await page.locator('#stat-reused').innerText()==='192','Prior states kept separate');
    check(await page.locator('#stat-fixtures').innerText()==='888','Current observed census');
    check(await page.locator('#stat-issues').innerText()==='2,210','New genuine research issues');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overview has no page overflow');
    if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`fbs-v078-result-${live?'live':'static'}-${width}.png`),fullPage:true});}
    await page.click('[data-tab="models"]');
    for(const cohort of data.model_cohorts)for(const target of ['winner','margin','total']){
      await page.selectOption('#model-cohort',cohort.id);await page.selectOption('#model-target',target);
      const expected=data.models.filter(r=>r.cohort===cohort.id&&r.target===target);
      check(await page.locator('.model-card').count()===expected.length,'Exact separated model cohort cards');
      check((await page.locator('#model-cohort-note').innerText())===cohort.description,'Evidence caveat shown');
    }
    await page.selectOption('#model-cohort','issued29');await page.selectOption('#model-target','winner');
    check((await page.locator('#model-cards').innerText()).includes('0.500763'),'Genuine LightGBM metric');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Model cards do not overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-models-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="markets"]');
    for(const population of ['all','final','upcoming'])for(const target of ['winner','margin','total']){
      await page.selectOption('#provider-population',population);await page.selectOption('#provider-target',target);
      const cohort=census.filter(g=>g.season===2026&&(population==='all'||(population==='final'?g.status==='final':g.status!=='final')));
      check(await page.locator('#provider-body tr').count()===4,'Four distinct provider products');
      for(const provider of data.providers){
        const row=page.locator('#provider-body tr[data-provider="'+provider.id+'"] td');
        const references=cohort.filter(g=>g.providers?.[provider.id]?.[target]?.observed_reference).length;
        check((await row.nth(1).innerText())===(references?references.toLocaleString('en-US')+' archived references':'Not proved for this cohort'),'Correct provider schema and coverage');
        check(await row.nth(2).innerText()==='0','No invented qualified baseline');
        check(await row.nth(3).innerText()===cohort.length.toLocaleString('en-US'),'Correct provider denominator');
      }
    }
    check((await page.locator('#archive-comparison-body').innerText()).includes('Unresolved saved market reference'),'Composite reference not misattributed');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-markets-${live?'live':'static'}-${width}.png`),fullPage:true});
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
      check((await page.locator('#weighted-cohort').innerText()).includes(expected[0].season_details['2024'].n.toLocaleString('en-US')),'Window-specific cohort shown');
    }
    check((await page.locator('#weighted-limits').innerText()).includes('54 exploratory'),'Multiplicity limit remains visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Weighted view has no page overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-weighted-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="games"]');
    for(const season of [2024,2025,2026]){
      await page.selectOption('#game-season',String(season));
      check((await page.locator('#game-count').innerText()).startsWith(String(census.filter(g=>g.season===season).length)),'Every observed season retained');
    }
    check(await page.locator('#game-body tr').count()===25,'Game paging');
    const first=await page.locator('#game-body').innerText();await page.click('#game-next');
    check(await page.locator('#game-body').innerText()!==first,'Paging changes visible games');
    await page.selectOption('#game-status','final');check((await page.locator('#game-count').innerText()).startsWith('728'),'All current finals');
    await page.selectOption('#game-status','tbd');check((await page.locator('#game-count').innerText()).startsWith('53'),'Current TBD count excludes old-season TBD');
    await page.selectOption('#game-status','all');await page.selectOption('#game-coverage','issued');
    check((await page.locator('#game-count').innerText()).startsWith('85'),'New issues cover 85 games');
    check((await page.locator('#game-body').innerText()).includes('new issue rows retained'),'Issue coverage explicit');
    await page.selectOption('#game-coverage','missing');check((await page.locator('#game-count').innerText()).startsWith('803'),'All games without new issue remain');
    await page.selectOption('#game-coverage','all');await page.fill('#game-search','Florida');
    check((await page.locator('#game-body').innerText()).includes('Florida'),'Team search works');await page.fill('#game-search','');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile game cards have no page overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-games-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.selectOption('#game-target','margin');
    await page.locator('[data-game-open]').first().click();
    check(await page.locator('#game-dialog').isVisible(),'Game detail opens');
    check((await page.locator('#game-dialog-body').innerText()).includes('Observed:'),'Observation clock separate from quote clock');
    check((await page.locator('#game-dialog-body').innerText()).includes('unqualified'),'Missingness and qualification remain explicit');
    await page.click('#dialog-close');check(!(await page.locator('#game-dialog').isVisible()),'Dialog closes');
    const downloadPromise=page.waitForEvent('download');await page.click('#download-games');const download=await downloadPromise;
    check(download.suggestedFilename()==='FBS_2026_FILTERED_COMPARISON.csv','Filtered CSV has current season');
    const downloaded=fs.readFileSync(await download.path(),'utf8');
    check(downloaded.split('\r\n').length===890,'CSV contains all 888 filtered games and header');
    check(downloaded.includes('draftkings_observation_time'),'CSV preserves provider observation clocks');
    check(!/circa|s3:\/\//i.test(downloaded),'CSV respects sport and public scope');
    await page.click('[data-tab="execution"]');check((await page.locator('#cpu-detail').innerText()).includes('11.607945'),'Actual study CPU seconds');
    check((await page.locator('#panel-execution').innerText()).includes('10 parts'),'Multipart return explicit');
    check((await page.locator('#panel-execution').innerText()).includes('Uploading the multi-gigabyte return in chat is unnecessary'),'No manual return-upload requirement');
    check(await page.locator('#gate-body tr').count()===6,'All acceptance statuses shown');
    await page.locator('[data-tab="execution"]').focus();await page.keyboard.press('Home');
    check(await page.locator('[data-tab="overview"]').getAttribute('aria-selected')==='true','Keyboard tab navigation');
    check(!/circa/i.test(await page.locator('body').innerText()),'Current presentation has no out-of-sport content');
    await page.close();
  }
  check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');check(httpErrors.length===0,'No HTTP failures');
  const receipt={status:'PASS',checks,viewports:[1440,390],live_url:live||null,source_as_of:data.source_as_of,
    owner_version:'V077',report_version:'V078',new_fits_by_publication:0,owner_new_model_fits:35,owner_new_issues:2210,
    publication_is_owner_execution:false,errors,failed,httpErrors};
  if(out)fs.writeFileSync(path.join(out,`FBS_V078_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
