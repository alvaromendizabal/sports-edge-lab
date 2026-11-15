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
    check(await page.locator('#stat-fits').innerText()===data.counts.new_fits.toLocaleString('en-US'),'Actual executed fit tasks');
    check((await page.locator('#fit-reuse-note').innerText()).includes(data.fit_reuse_caveat),'Current fit and reuse accounting visible');
    check(await page.locator('#stat-reused').innerText()===data.counts.reused_states.toLocaleString('en-US'),'Prior states kept separate');
    check(await page.locator('#stat-fixtures').innerText()==='888','Current observed census');
    check(await page.locator('#stat-issues').innerText()===data.counts.new_issue_records.toLocaleString('en-US'),'Updated genuine research issues');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overview has no page overflow');
    if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`fbs-v078-result-${live?'live':'static'}-${width}.png`),fullPage:true});}
    await page.click('[data-tab="models"]');
    for(const cohort of data.model_cohorts)for(const target of ['winner','margin','total']){
      await page.selectOption('#model-cohort',cohort.id);await page.selectOption('#model-target',target);
      const expected=data.models.filter(r=>r.cohort===cohort.id&&r.target===target);
      check(await page.locator('.model-card').count()===expected.length,'Exact separated model cohort cards');
      check((await page.locator('#model-cohort-note').innerText())===cohort.description,'Evidence caveat shown');
    }
    await page.selectOption('#model-cohort','issued');await page.selectOption('#model-target','winner');
    const winnerLeader=data.models.filter(r=>r.cohort==='issued'&&r.target==='winner').sort((a,b)=>a.metrics.log_loss-b.metrics.log_loss)[0];
    check((await page.locator('#model-cards').innerText()).includes(winnerLeader.metrics.log_loss.toFixed(6)),'Latest genuine probability leader metric');
    check((await page.locator('#model-cards').innerText()).includes('Conditional 95% accuracy interval'),'Conditional uncertainty visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Model cards do not overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-models-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="markets"]');
    for(const population of ['all','final','upcoming'])for(const target of ['winner','margin','total']){
      await page.selectOption('#provider-population',population);await page.selectOption('#provider-target',target);
      const cohort=census.filter(g=>g.season===2026&&(population==='all'||(population==='final'?g.status==='final':g.status!=='final')));
      check(await page.locator('#provider-body tr').count()===4,'Four distinct provider products');
      for(const provider of data.providers){
        const row=page.locator('#provider-body tr[data-provider="'+provider.id+'"]');
        const references=cohort.filter(g=>g.providers?.[provider.id]?.[target]?.observed_reference).length;
        const displayable=cohort.filter(g=>g.providers?.[provider.id]?.[target]?.value!=null&&g.providers?.[provider.id]?.[target]?.display_eligible===true).length;
        check((await row.locator('[data-coverage="reference"]').innerText())===references.toLocaleString('en-US'),'Correct archived reference count');
        check((await row.locator('[data-coverage="display"]').innerText())===displayable.toLocaleString('en-US'),'Displayable rounded references remain separate');
        check(await row.locator('[data-coverage="qualified"]').innerText()==='0','No invented qualified baseline');
        check(await row.locator('[data-coverage="denominator"]').innerText()===cohort.length.toLocaleString('en-US'),'Correct provider denominator');
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
    await page.selectOption('#game-status','final');check((await page.locator('#game-count').innerText()).startsWith(String(data.census.finals)),'All current finals');
    await page.selectOption('#game-status','unfinished');check((await page.locator('#game-count').innerText()).startsWith(String(data.census.pending)),'All pending includes unresolved kickoffs');
    await page.selectOption('#game-status','tbd');check((await page.locator('#game-count').innerText()).startsWith(String(census.filter(g=>g.season===2026&&g.status==='tbd').length)),'Current TBD count excludes old-season TBD');
    await page.selectOption('#game-status','all');await page.selectOption('#game-coverage','issued');
    check((await page.locator('#game-count').innerText()).startsWith(String(data.counts.new_issue_games)),'Updated issue game count');
    check((await page.locator('#game-body').innerText()).includes('research-grid issue rows updated'),'Issue coverage explicit');
    await page.selectOption('#game-coverage','missing');check((await page.locator('#game-count').innerText()).startsWith(String(data.census.fixtures-data.counts.new_issue_games)),'All games without an updated issue remain');
    await page.selectOption('#game-coverage','modelvalue');
    check((await page.locator('#game-count').innerText()).startsWith(String(census.filter(g=>g.season===2026&&g.model?.winner?.value!=null).length)),'Preserved foundation outputs can be located separately');
    await page.selectOption('#game-coverage','all');await page.fill('#game-search','Florida');
    check((await page.locator('#game-body').innerText()).includes('Florida'),'Team search works');await page.fill('#game-search','');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile game cards have no page overflow');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-games-${live?'live':'static'}-${width}.png`),fullPage:true});
    for(const provider of data.providers)for(const target of ['winner','margin','total']){
      await page.selectOption('#game-provider',provider.id);await page.selectOption('#game-target',target);
      for(const state of ['reference','display','qualified','missing','blocked']){
        await page.selectOption('#game-provider-state',state);
        const expected=census.filter(g=>{if(g.season!==2026)return false;const c=g.providers?.[provider.id]?.[target];const reference=c?.observed_reference===true,display=c?.value!=null&&c?.display_eligible===true;return state==='reference'?reference:state==='display'?display:state==='qualified'?c?.status==='qualified':state==='missing'?!reference:reference&&!display;});
        check((await page.locator('#game-count').innerText()).startsWith(String(expected.length)),`${provider.id} ${target} ${state} gap filter`);
      }
    }
    await page.click('[data-tab="markets"]');await page.selectOption('#provider-population','upcoming');await page.selectOption('#provider-target','winner');
    await page.click('[data-provider-open="kalshi"]');
    check(await page.locator('#tab-games').getAttribute('aria-selected')==='true','Provider drilldown opens the game table');
    check(await page.locator('#game-provider').inputValue()==='kalshi','Provider drilldown preserves product identity');
    check(await page.locator('#game-status').inputValue()==='unfinished','Provider drilldown includes all pending fixtures');
    check((await page.locator('#game-count').innerText()).startsWith(String(data.census.pending)),'Pending drilldown includes unresolved kickoffs');
    await page.selectOption('#game-status','all');await page.selectOption('#game-provider','all');await page.selectOption('#game-provider-state','all');
    await page.selectOption('#game-target','margin');
    await page.locator('[data-game-open]').first().click();
    check(await page.locator('#game-dialog').isVisible(),'Game detail opens');
    check((await page.locator('#game-dialog-body').innerText()).includes('Observed:'),'Observation clock separate from quote clock');
    check((await page.locator('#game-dialog-body').innerText()).includes('Preserved frozen foundation'),'Detail view names the per-game model source');
    check((await page.locator('#game-dialog-body').innerText()).includes('unqualified'),'Missingness and qualification remain explicit');
    await page.click('#dialog-close');check(!(await page.locator('#game-dialog').isVisible()),'Dialog closes');
    const downloadPromise=page.waitForEvent('download');await page.click('#download-games');const download=await downloadPromise;
    check(download.suggestedFilename()==='FBS_2026_FILTERED_COMPARISON.csv','Filtered CSV has current season');
    const downloaded=fs.readFileSync(await download.path(),'utf8');
    check(downloaded.split('\r\n').length===data.census.fixtures+2,'CSV contains every filtered game and header');
    for(const suffix of ['reference_present','rounded_value_displayable','identity_matched','clock_gate_passed','qualified_comparison'])check(downloaded.includes('draftkings_'+suffix),'CSV preserves '+suffix);
    check(downloaded.includes('draftkings_observation_time'),'CSV preserves provider observation clocks');
    check(downloaded.includes('model_source')&&downloaded.includes('preserved_frozen_foundation'),'CSV names the admitted foundation source, not current research leaders');
    check(!/circa|s3:\/\//i.test(downloaded),'CSV respects sport and public scope');
    await page.click('[data-tab="overview"]');await page.click('#open-audit-baseline');
    check(await page.locator('#game-model-source').inputValue()==='audit','Current audit action selects its explicit source');
    check(await page.locator('#game-model-heading').textContent()==='Current fixed audit baseline','Selected source is visible in the table heading');
    check((await page.locator('#game-count').innerText()).startsWith('84'),'Current fixed audit baseline covers 84 pending games');
    check((await page.locator('#game-model-source-note').innerText()).includes('not a promoted champion or the current aggregate leader'),'Audit baseline is not relabelled as a leaderboard winner');
    check((await page.locator('#audit-admission-note').innerText()).includes('252 admitted values'),'Current admitted scalar count is visible');
    check((await page.locator('#audit-admission-note').innerText()).includes(data.audit_baseline_selection.selection_time),'Actual selection clock is distinct from source observation');
    for(const target of ['winner','margin','total']){
      await page.selectOption('#game-target',target);
      const eligible=census.filter(g=>g.season===2026&&g.status!=='final'&&g.audit_model?.[target]?.value!=null);
      check((await page.locator('#game-count').innerText()).startsWith(String(eligible.length)),'Each fixed audit target retains its admitted cohort');
      const firstRow=page.locator('#game-body tr[data-game]').first(),id=await firstRow.getAttribute('data-game'),g=eligible.find(g=>g.id===id),c=g.audit_model[target];
      const shown=target==='winner'?(100*c.value).toFixed(1)+'%':c.value.toFixed(1);
      check((await firstRow.locator('td').nth(2).innerText()).includes(shown),'Displayed fixed audit value matches the authenticated rounded scalar');
      check((await firstRow.locator('td').nth(2).innerText()).includes(c.family),'Fixed audit family is visible');
      check((await firstRow.locator('td').nth(2).innerText()).includes(c.issue_time),'Original issue clock remains visible');
    }
    await page.locator('[data-game-open]').first().click();
    check((await page.locator('#game-dialog-body').innerText()).includes('Preserved frozen foundation'),'Details retain the independent original source');
    check((await page.locator('#game-dialog-body').innerText()).includes('Current fixed audit baseline'),'Details compare both admitted model sources');
    check((await page.locator('#game-dialog-body').innerText()).includes('Selected for audit display: '+data.audit_baseline_selection.selection_time),'Detailed selection clock is explicit');
    await page.click('#dialog-close');
    await page.selectOption('#game-status','final');check((await page.locator('#game-count').innerText()).startsWith('0 '),'No historical backfill of the current audit baseline');
    await page.selectOption('#game-status','unfinished');await page.selectOption('#game-coverage','all');
    check((await page.locator('#game-count').innerText()).startsWith('144'),'All pending games remain visible with audit gaps');
    await page.selectOption('#game-status','tbd');check((await page.locator('#game-count').innerText()).startsWith('53'),'Unresolved audit fixtures remain explicit');
    await page.selectOption('#game-status','unfinished');await page.selectOption('#game-coverage','modelvalue');
    const auditDownloadPromise=page.waitForEvent('download');await page.click('#download-games');const auditDownload=await auditDownloadPromise;
    const auditCSV=fs.readFileSync(await auditDownload.path(),'utf8');
    check(auditCSV.split('\r\n').length===86,'Selected audit CSV contains 84 rows and header');
    for(const field of ['current_fixed_audit_baseline','model_value_label','model_selection_time','model_fit_completed_at','model_prepared_at','model_requested_horizon_cutoff'])check(auditCSV.includes(field),'Audit CSV retains '+field);
    check(auditCSV.includes(data.audit_baseline_selection.selection_time),'Audit CSV preserves selection rather than re-dating issues');
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-audit-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="overview"]');await page.click('#open-research-leaders');
    check(await page.locator('#game-model-source').inputValue()==='leaders','Current leader action selects its explicit source');
    check((await page.locator('#game-model-heading').textContent()).includes('not promoted'),'Selected research roles retain non-promotion label');
    check((await page.locator('#game-count').innerText()).startsWith(String(data.research_leader_selection.admitted_games)),'Future research leader cohort matches independent admission');
    check((await page.locator('#leader-admission-note').innerText()).includes(data.research_leader_selection.selection_time),'Leader selection has its actual later clock');
    check((await page.locator('#leader-admission-note').innerText()).includes(data.research_leader_selection.exact_state_caveat),'Every newer state retains the exact-state performance caveat');
    check((await page.locator('#leader-admission-note').innerText()).includes(data.research_leader_selection.uncertainty_limitation),'Selected gain uncertainty remains visible');
    for(const target of ['winner','margin','total']){
      await page.selectOption('#game-target',target);
      const eligible=census.filter(g=>g.season===2026&&g.status!=='final'&&g.research_leader_model?.[target]?.value!=null);
      check((await page.locator('#game-count').innerText()).startsWith(String(eligible.length)),'Each selected research target preserves admitted coverage');
      const row=page.locator('#game-body tr[data-game]').first(),id=await row.getAttribute('data-game'),c=eligible.find(g=>g.id===id).research_leader_model[target];
      const shown=target==='winner'?(100*c.value).toFixed(1)+'%':c.value.toFixed(1);
      const text=await row.locator('td').nth(2).innerText();
      check(text.includes(shown),'Displayed selected research scalar matches admitted source');
      check(text.includes(c.family),'Selected family remains visible');
      check(text.includes(c.issue_time),'Original leader-family issue clock remains visible');
    }
    await page.locator('[data-game-open]').first().click();
    for(const name of ['Preserved frozen foundation','Current fixed audit baseline','Selected research leaders'])check((await page.locator('#game-dialog-body').innerText()).includes(name),'Details retain '+name);
    check((await page.locator('#game-dialog-body').innerText()).includes('Current issued states differ from the exact earlier-scored states'),'Details do not attribute old metrics to newer weights');
    await page.click('#dialog-close');
    await page.selectOption('#game-status','final');check((await page.locator('#game-count').innerText()).startsWith('0 '),'No retrospective selected-leader forecast backfill');
    await page.selectOption('#game-status','unfinished');await page.selectOption('#game-coverage','all');check((await page.locator('#game-count').innerText()).startsWith('144'),'Every pending game retains selected-leader gaps');
    await page.selectOption('#game-coverage','modelvalue');
    const leaderDownloadPromise=page.waitForEvent('download');await page.click('#download-games');const leaderDownload=await leaderDownloadPromise;
    const leaderCSV=fs.readFileSync(await leaderDownload.path(),'utf8');
    check(leaderCSV.split('\r\n').length===86,'Selected research CSV contains 84 pending rows and header');
    for(const field of ['selected_research_leaders_not_promoted','model_evidence','model_selection_time',data.research_leader_selection.selection_time,'Current issued states differ'])check(leaderCSV.includes(field),'Selected research CSV preserves '+field);
    if(out)await page.screenshot({path:path.join(out,`fbs-v078-leaders-${live?'live':'static'}-${width}.png`),fullPage:true});
    await page.click('[data-tab="execution"]');check((await page.locator('#cpu-detail').innerText())===data.cpu_detail,'Current measured CPU accounting');
    check((await page.locator('#finalization-note').innerText())===data.execution_note,'Current finalization is distinct from archived failures');
    check((await page.locator('#panel-execution').innerText()).includes(data.return.parts.toLocaleString('en-US')+' parts'),'Multipart return explicit');
    check((await page.locator('#panel-execution').innerText()).includes('Uploading the multi-gigabyte return in chat is unnecessary'),'No manual return-upload requirement');
    check(await page.locator('#gate-body tr').count()===data.gates.length,'All acceptance statuses shown');
    await page.locator('[data-tab="execution"]').focus();await page.keyboard.press('Home');
    check(await page.locator('[data-tab="overview"]').getAttribute('aria-selected')==='true','Keyboard tab navigation');
    check(!/circa/i.test(await page.locator('body').innerText()),'Current presentation has no out-of-sport content');
    await page.close();
  }
  check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');check(httpErrors.length===0,'No HTTP failures');
  const receipt={status:'PASS',checks,viewports:[1440,390],live_url:live||null,source_as_of:data.source_as_of,
    owner_version:data.owner_version,report_version:data.report_version,new_fits_by_publication:0,owner_executed_fit_tasks:data.counts.new_fits,owner_new_issues:data.counts.new_issue_records,
    publication_is_owner_execution:false,errors,failed,httpErrors};
  if(out)fs.writeFileSync(path.join(out,`FBS_V078_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
