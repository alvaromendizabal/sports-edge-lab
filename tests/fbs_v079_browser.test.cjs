'use strict';
// Review public static evidence and controls. This test creates no owner science.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=process.env.FBS_V079_SITE||path.join(root,'docs/fbs/v079');
const live=process.env.FBS_V079_LIVE_URL,base=live||'http://fbs-v079.test/';
const data=JSON.parse(fs.readFileSync(path.join(site,'data/review.json'))),games=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(site,'data/games.json.gz')))).games;
const nomineeProjection=JSON.parse(fs.readFileSync(path.join(site,'data/validation-nominees.json')));
require(path.join(site,'app.js'));
const logic=globalThis.FBS079,out=process.env.FBS_SCREENSHOTS;
let browser,checks=0;const check=(value,message)=>{assert.ok(value,message);checks++;};
function parseCSV(text){const rows=[];let row=[],field='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(field);field='';}else if(c==='\n'&&!quoted){row.push(field.endsWith('\r')?field.slice(0,-1):field);rows.push(row);row=[];field='';}else field+=c;}if(field||row.length){row.push(field);rows.push(row);}return rows;}
(async()=>{
  browser=await chromium.launch({headless:true,args:['--no-sandbox'],executablePath:process.env.FBS_CHROMIUM_PATH||undefined});
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
    check((await page.locator('#market-summary').innerText()).includes('all 11 primary-comparison reconstructed winner candidates'),'Negative same-provider comparison finding remains visible');
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
    for(const target of ['all','winner','margin','total'])for(const role of ['all','challenger','negative_control']){
      await page.selectOption('#study-target',target);await page.selectOption('#study-role',role);
      const expected=data.current_study.rows.filter(r=>(target==='all'||r.target===target)&&(role==='all'||r.role===role));
      const aliases=await page.locator('#current-study-body tr[data-study-model]').evaluateAll(xs=>xs.map(x=>x.dataset.studyModel));
      assert.deepEqual(aliases,expected.map(r=>r.alias));checks++;
      for(const r of expected){const text=await page.locator(`#current-study-body tr[data-study-model="${r.alias}"]`).innerText();
        for(const c of r.season_cards)check(text.includes(c.n.toLocaleString('en-US')+' games'),'Study target retains identical annual population');
        check(text.includes(r.validation_n.toLocaleString('en-US')+' games'),'Study validation pool is visible');
        check(text.includes('No automatic promotion'),'Research role never claims promotion');
      }
    }
    await page.selectOption('#study-target','all');await page.selectOption('#study-role','all');
    check((await page.locator('#current-study-qualification').innerText()).includes('proxy'),'Corrected study retains availability qualification');
    await page.locator('#current-study-section details > summary').click();
    check((await page.locator('#current-study-original-note').innerText()).includes('24 games'),'Original timing-defect counts retained');
    check(await page.locator('#current-study-original-body tr[data-study-model]').count()===12,'All original study diagnostics preserved');
    await page.locator('#current-study-section details > summary').click();
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Model table scrolls inside viewport');
    await page.selectOption('#model-target','winner');await page.selectOption('#model-metric','log_loss');
    if(out){await page.screenshot({path:path.join(out,`fbs-v079-models-${live?'live':'static'}-${width}.png`),fullPage:true});await page.locator('#current-study-section').screenshot({path:path.join(out,`fbs-v080r1-study-${live?'live':'static'}-${width}.png`)});}
    await page.click('[data-tab="markets"]');
    for(const season of [2024,2025,2026])for(const metric of ['log_loss','brier','accuracy']){
      await page.selectOption('#research-market-season',String(season));await page.selectOption('#research-market-metric',metric);
      const expected=data.research_market_comparison.scorecards.filter(r=>r.season===season);
      const aliases=await page.locator('#research-market-body tr[data-research-market-model]').evaluateAll(xs=>xs.map(x=>x.dataset.researchMarketModel));
      assert.deepEqual(aliases,expected.map(r=>r.alias));checks++;
      for(const row of expected){const text=await page.locator(`#research-market-body tr[data-research-market-model="${row.alias}"]`).innerText();
        check(text.includes(row.paired_n.toLocaleString('en-US')+' / '+row.expected_n.toLocaleString('en-US')),'Research market comparison retains identical primary provider cohort');
        check(text.includes('no nomination'),'Research market comparison cannot nominate a champion');
      }
    }
    for(const season of [2024,2025,2026])for(const status of ['all','final','unfinished'])for(const target of ['winner','margin','total']){
      await page.selectOption('#market-season',String(season));await page.selectOption('#market-status',status);await page.selectOption('#market-target',target);
      const subset=logic.subsetGames(games,season,status);
      for(const provider of ['draftkings','kalshi','polymarket_global','polymarket_us']){
        const expected=logic.providerCoverage(subset,provider,target),row=page.locator(`#market-body tr[data-provider="${provider}"]`);
        for(const key of ['reference','display','qualified','missing','denominator'])check(await row.locator(`[data-coverage="${key}"]`).innerText()===expected[key].toLocaleString('en-US'),'Exact provider denominator and evidence state');
        for(const [prefix,state,fn] of [['current','CURRENT_SOURCE_PROJECTION_VERIFIED',logic.currentCoverage],['historical','HISTORICAL_SOURCE_PROJECTION_VERIFIED',logic.historicalCoverage]]){
          const projection=data[prefix+'_source_coverage'],attached=projection?.state===state&&(prefix==='historical'||season===2026),c=fn(subset,provider,target),sourceRow=page.locator(`#${prefix}-market-body tr[data-${prefix}-provider="${provider}"]`);
          for(const key of ['reference','qualified','denominator']){const expected=key==='denominator'?c[key].toLocaleString('en-US'):attached&&c.covered===subset.length?(key==='reference'?logic.referenceCoverageLabel(c,logic.referenceMeasurement(nomineeProjection,prefix,provider,data.current_source_coverage)):c[key].toLocaleString('en-US')):'Not attached';check(await sourceRow.locator(`[data-${prefix}-coverage="${key}"]`).innerText()===expected,'Capture coverage retains denominator and distinguishes unmeasured references from zero qualified');}
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
    const currentValueGames=games.filter(g=>g.season===2026&&g.status==='pending'&&g.current_provider_coverage?.draftkings?.winner?.display_eligible);
    check(currentValueGames.length===66,'All66 approved current probabilities exist outside the archived namespace');
    const currentExample=currentValueGames[0],currentCell=currentExample.current_provider_coverage.draftkings.winner;
    await page.selectOption('#game-season','2026');await page.fill('#game-search',currentExample.id);
    check((await page.locator('#game-body').innerText()).includes((100*currentCell.display_value).toFixed(2)+'%'),'Current provider probability is visibly rendered');
    await page.click('[data-open-game]');const currentDetail=await page.locator('#game-dialog-body').innerText();
    check(currentDetail.includes(currentCell.quote_time)&&currentDetail.includes(currentCell.observation_time),'Current quote and acquisition clocks are visible separately');
    await page.click('#dialog-close');await page.fill('#game-search','');
    check(await page.locator('#game-source option[value="nominees"]').count()===1,'Validation nominee source is selectable');
    await page.selectOption('#game-source','nominees');await page.fill('#game-search',currentExample.id);
    for(const [objective,role] of Object.entries(nomineeProjection.roles)){
      await page.selectOption('#game-target',role.target);await page.selectOption('#game-objective',objective);
      const cell=logic.selectGameModel(currentExample,'nominees',role.target,objective,nomineeProjection),text=await page.locator('#game-body').innerText(),value=role.target==='winner'?(100*cell.value).toFixed(1)+'%':cell.value.toFixed(1);
      check(text.includes(value)&&text.includes(role.model_alias),'Selected objective shows its actual rounded nominee output and public alias');
      await page.click('[data-open-game]');const detail=await page.locator('#game-dialog-body').innerText();
      for(const clock of ['issue_time','fit_completed_at','prepared_at','information_cutoff','nomination_report_completed_at'])check(detail.includes(cell[clock]),'Original issue and nomination-report clocks are visible separately');
      check(detail.includes('Exact original nomination-selection clock was not retained'),'Missing selection clock is never backdated');
      check(detail.includes('recipe and chronological protocol'),'Historical metrics do not validate the current fitted state');
      await page.click('#dialog-close');
    }
    await page.selectOption('#game-target','winner');await page.selectOption('#game-objective','winner_probability');
    const completedExample=games.find(g=>g.season===2026&&g.status==='final'),tbdExample=games.find(g=>g.season===2026&&g.status==='tbd');
    await page.fill('#game-search',completedExample.id);check((await page.locator('#game-body').innerText()).includes('not backfilled'),'Completed games do not receive a current-fit forecast');
    await page.fill('#game-search',tbdExample.id);check((await page.locator('#game-body').innerText()).includes('Kickoff is unresolved'),'Unissued unresolved fixtures retain an explicit missing reason');
    await page.fill('#game-search','');
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
    const stream=await download.createReadStream(),chunks=[];for await(const chunk of stream)chunks.push(chunk);const csv=parseCSV(Buffer.concat(chunks).toString('utf8')),headers=csv[0],exported=csv.slice(1).map(row=>Object.fromEntries(headers.map((name,i)=>[name,row[i]]))),byGame=new Map(exported.map(r=>[r.game_id,r]));
    check(exported.filter(r=>r.draftkings_current_display_value!=='').length===66,'CSV includes all66 current derived probabilities');
    check(exported.filter(r=>r.model_value!=='').length===96,'Nominee CSV has exactly96 current issues without historical backfill');
    check(exported.filter(r=>r.status==='final').every(r=>r.model_value===''),'Every completed game remains explicitly unforecast by the current-state view');
    for(const row of exported.filter(r=>r.model_value!=='')){check(row.model_alias==='W08'&&row.model_fit_completed_at&&row.model_information_cutoff&&row.model_nomination_report_completed_at,'CSV binds the selected alias and actual clocks');check(row.model_selection_time===''&&row.model_selection_time_basis.includes('not retained'),'CSV does not invent original selection time');}
    for(const [provider,expected] of [['kalshi',65],['polymarket_global',64],['polymarket_us',0]]){
      check(exported.filter(r=>r[provider+'_current_reference']==='true').length===expected,'CSV exports the measured current reference count for '+provider);
      check(exported.every(r=>['true','false'].includes(r[provider+'_current_reference'])&&r[provider+'_historical_reference']==='Not measured'&&r[provider+'_current_source_qualified']==='false'),'Current measurement never turns unknown history or unqualified settlement into a qualified comparison');
    }
    for(const game of currentValueGames){const row=byGame.get(game.id),cell=game.current_provider_coverage.draftkings.winner;check(Number(row.draftkings_current_display_value)===cell.display_value,'CSV current probability equals actual public cell');check(row.draftkings_current_quote_time===cell.quote_time&&row.draftkings_current_observed_at===cell.observation_time,'CSV keeps the actual current quote and acquisition clocks');}
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Game table contained on mobile');
    await page.click('[data-tab="diagnostics"]');check((await page.locator('#diagnostic-note').innerText()).includes('47-game'),'Narrow issued cohort is explicitly diagnostic');
    await page.click('[data-tab="execution"]');check((await page.locator('#new-execution').innerText()).includes('None'),'No promotion claimed');
    check((await page.locator('#current-execution').innerText()).includes(data.current_execution.verified_current_total_issue_records.toLocaleString('en-US')),'Current V080 execution is separate from predecessor accounting');
    check((await page.locator('#current-execution-note').innerText()).includes('do not establish novel models'),'Actual fit calls are not presented as novel learning');
    check((await page.locator('#prior-v080-audit').innerText()).includes('26 base fit calls'),'Earlier V080 avoidable fits remain dated history');
    check((await page.locator('#prior-v080-audit').innerText()).includes('separate from the current V080R1 execution'),'Earlier duplicate fits are not attributed to current execution');
    check((await page.locator('#feature-progress').innerText()).includes(data.current_execution.secondary_feature_milestone.team_context_rows+' team rows'),'Secondary progress uses actual V080 counts');
    check((await page.locator('#prior-execution-note').innerText()).startsWith('The V078 predecessor'),'Predecessor wording cannot imply current execution');
    check((await page.locator('#cpu-detail').innerText()).startsWith('Preserved V078 capacity measurement'),'Earlier CPU measurement remains explicitly dated');
    await page.focus('[data-tab="overview"]');await page.keyboard.press('ArrowRight');check(await page.locator('#panel-models').isVisible(),'Keyboard tabs work');
    await page.goto(new URL('data-policy.html',base).href,{waitUntil:'networkidle'});
    check((await page.locator('#execution').innerText()).includes('2987'),'Latest failed execution reuse count is visible');
    check((await page.locator('body').innerText()).includes('comparison-only'),'Named providers are comparison-only');
    check(await page.locator('#source-rows tr').count()>0,'Measured source audit is populated');
    const sourceRows=await page.locator('#source-rows tr').evaluateAll(rows=>rows.map(r=>Array.from(r.querySelectorAll('td')).map(c=>c.textContent)));
    const sourceCoverage=family=>sourceRows.find(row=>row[0]===family)?.[1]||'';
    check(/13,378.*15,450,173.*13,354,870/.test(sourceCoverage('Other bookmaker cache')),'Archive coverage renders actual shard and other-book row counts');
    check(/2,947 \/ 904,860.*554/.test(sourceCoverage('Other bookmaker features')),'Other-book feature coverage renders the measured numerator, denominator and excluded rows');
    check(/510 \/ 752.*242/.test(sourceCoverage('CFBD 2026 raw drives')),'Drive coverage renders the expanded inspected-source game counts');
    check(/890 \/ 27,420.*2,670/.test(sourceCoverage('CFBD F01')),'F01 renders qualified rows and values rather than a missing schema key');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Source policy fits viewport');
    if(out)await page.screenshot({path:path.join(out,`fbs-v082-policy-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.goto(new URL('market-study.html',base).href,{waitUntil:'networkidle'});
    check((await page.locator('#nomination').innerText()).includes('ineligible'),'Archived market policies cannot remain nominees');
    check((await page.locator('h1').innerText()).includes('Archived'),'Historical study has an archive heading');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Archived study fits viewport');
    await page.close();
  }
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  const receipt={status:'PASS',checks,site:live?'HOSTED_PUBLIC_URL':'EXACT_STATIC_PUBLIC_ASSETS',viewport_widths:[1440,390],execution_version:data.execution_version,source_as_of:data.source_as_of,fixture_source_as_of:data.fixture_source_as_of,scorecards:data.full_population.scorecards.length,research_target_rows:data.current_study.rows.length,research_season_cards:data.current_study.rows.reduce((n,r)=>n+r.season_cards.length,0),research_market_scorecards:data.research_market_comparison.scorecards.length,game_count:games.length,owner_fits:0,forecast_issues:0,promotion:false};
  if(out)fs.writeFileSync(path.join(out,`FBS_V079_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));await browser.close();
})().catch(async error=>{console.error(error);if(browser)await browser.close();process.exitCode=1;});

