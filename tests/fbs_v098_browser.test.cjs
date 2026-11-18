'use strict';
// Render and falsify the public report without invoking scientific owner work.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const crypto=require('node:crypto');
const moduleDir=process.env.PLAYWRIGHT_MODULE_DIR||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleDir);
const root=path.resolve(__dirname,'..');
const file=path.join(root,'docs/fbs/v098/index.html');
const body=fs.readFileSync(file,'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/v098/data/status.json'),'utf8'));
const shots=process.env.FBS_SCREENSHOTS||path.join(root,'tmp/fbs-v098-browser');
fs.mkdirSync(shots,{recursive:true});
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
let assertions=0;
function check(condition,label){assertions++;assert.ok(condition,label);}
function eq(actual,expected,label){assertions++;assert.deepEqual(actual,expected,label);}
const objective=x=>x.target[0].toUpperCase()+x.target.slice(1)+' '+({accuracy:'accuracy',brier:'Brier',log_loss:'log loss',mae:'MAE',rmse:'RMSE',crps:'CRPS'}[x.metric]);
const metric=(value,kind)=>kind==='accuracy'?(100*value).toFixed(4)+'%':value.toFixed(6);
const receipt={schema:'fbs.v098.public-browser-review.v1',status:'RUNNING',github_sha:process.env.GITHUB_SHA||null,github_head_sha:process.env.GITHUB_HEAD_SHA||null,source_html_sha256:sha(body),source_html_bytes:Buffer.byteLength(body),views:[],downloads:[],invalid_inputs:[],owner_executions_started_by_check:0};
const invalid=new Map();
const server=http.createServer((req,res)=>{const content=req.url==='/'?body:invalid.get(req.url);res.writeHead(content?200:404,{'content-type':'text/html; charset=utf-8'});res.end(content||'Not found');});

(async()=>{
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const origin='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:process.env.FBS_BROWSER_EXECUTABLE||undefined});
  try{
    for(const variant of ['source','offline'])for(const width of [1440,390]){
      const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});
      const page=await context.newPage(),errors=[],requests=[];
      page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>requests.push(request.url()));
      await page.goto(variant==='source'?origin+'/':'file://'+file);
      await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
      eq(await page.locator('#new-fits').innerText(),'294','Base fits remain separate from calibrators');
      eq(await page.locator('#complete-jobs').innerText(),'306 / 306','Full registered job denominator');
      eq(await page.locator('#fit-processes').innerText(),'22','Measured peak is not PID inventory');
      eq(await page.locator('#test-games').innerText(),'755','Known completed test population');
      const actual=await page.locator('#actual-facts').innerText();
      check(actual.includes('0 / 0')&&actual.includes('Incomplete'),'Operational closure and incomplete science remain separate');
      eq(await page.locator('#actual-facts div').filter({hasText:'Historical failed attempts'}).locator('dd').innerText(),'6','Historical failures preserved');
      eq(await page.locator('#actual-facts div').filter({hasText:'Operationally finished attempts'}).locator('dd').innerText(),'2','Current finish counted once');
      const gate=await page.locator('#gate-facts').innerText();
      check(gate.includes('Not established')&&gate.includes('48.162 s')&&gate.includes('30.366 s')&&gate.includes('180 seconds'),'Short phases cannot become sustained acceptance');
      check((await page.locator('#gate-limit').innerText()).includes('CONDITIONAL_INSUFFICIENT_INDEPENDENT_WORK'),'Conditional outcome is explicit');
      const phases=await page.locator('#phase-rows tr').allTextContents();
      eq(phases.length,2,'Two distinct scientific dispatch phases');
      check(phases[0].includes('19')&&phases[1].includes('22'),'Measured concurrency differs by phase');
      eq(await page.locator('#phase-bars .phase').count(),3,'Scientific phases and scoring plotted separately');
      const grading=await page.locator('#scoring-facts').innerText();
      check(grading.includes('612')&&grading.includes('79.264 CPU-s')&&grading.includes('22.700 s'),'Actual parallel scoring values');
      const cost=await page.locator('#queue-facts').innerText();
      check(cost.includes('$1.062090')&&cost.includes('$0.557423'),'Final and interim cost scopes stay visible');
      check((await page.locator('#queue-definition').innerText()).includes('not pure starvation'),'Queue definition is not silently changed');
      check((await page.locator('#population-facts').innerText()).includes('1,309 / 1,309'),'Full current known policy cohort');
      check((await page.locator('#next-facts').innerText()).includes('1,125'),'Finite separate T-60 plan is visible');
      const nextRuntime=await page.locator('#next-runtime').innerText();
      check(nextRuntime.includes('T60_CAMPAIGN_RUNTIME_ACCEPTANCE')&&nextRuntime.includes('UNVERIFIED')&&nextRuntime.includes('180 seconds')&&nextRuntime.includes('75%')&&nextRuntime.includes('shorter family waves cannot establish a pass'),'Finite T-60 job completion is separate from genuine campaign CPU acceptance');
      check((await page.locator('#next-status').innerText()).includes(data.next_preparation.status==='PREPARED_NOT_EXECUTED'?'native-verified':'under preparation'),'Installed claim follows sealed evidence');
      check((await page.locator('#summary-comparison').innerText()).includes('131,276,993')&&(await page.locator('#summary-comparison').innerText()).includes('138,960'),'Actual summary bytes, not total scientific storage');
      eq(await page.locator('#remaining-branches .branch').count(),data.remaining_work.length,'All unfinished branches retained');

      if(variant==='source'&&width===1440){
        for(const family of ['XGBoost','CatBoost']){
          await page.locator('#new-family').selectOption(family);
          eq(await page.locator('#new-family-rows tr').count(),9,'Nine new-family objective rows for '+family);
          for(const row of data.selection.new_family_best.filter(x=>x.family===family)){
            const cells=await page.locator('#new-family-rows tr').filter({hasText:objective(row)}).locator('td').allTextContents();
            eq(cells.slice(2),[String(row.primary_rank),metric(row.selection_score,row.metric),metric(row.all_source_absent_validation_score,row.metric),metric(row.annual_values[2],row.metric)],'Exact new-family rank and stress scope '+family+' '+objective(row));
          }
        }
        await page.locator('#new-family').selectOption('XGBoost');
        for(const profile of data.selection.profiles){
          await page.locator('#profile').selectOption(profile);
          eq(await page.locator('#leader-rows tr').count(),9,'Nine retained leaders for '+profile);
          for(const row of data.selection.leaders.filter(x=>x.profile===profile)){
            const cells=await page.locator('#leader-rows tr').filter({hasText:objective(row)}).locator('td').allTextContents();
            eq(cells.slice(2),[metric(row.annual_values[0],row.metric),metric(row.annual_values[1],row.metric),metric(row.selection_score,row.metric),metric(row.annual_values[2],row.metric)],'Exact annual validation and test metrics '+profile+' '+objective(row));
            check(cells[1].includes(row.family)&&cells[1].includes(row.policy_alias),'Coarse policy identity retained');
          }
        }
        await page.locator('#profile').selectOption('50/50');
        await page.locator('#leaders details summary').click();
        for(const row of data.selection.leaders.filter(x=>x.profile==='50/50')){
          const cells=await page.locator('#rank-rows tr').filter({hasText:objective(row)}).locator('td').allTextContents();
          eq(cells.slice(1),data.selection.profiles.map(profile=>String(data.selection.leaders.find(x=>x.profile===profile&&x.target===row.target&&x.metric===row.metric).primary_policy_rank)),'Exact saved sensitivity ranks '+objective(row));
        }
        await page.locator('#leaders details summary').click();
        for(const horizon of ['T60m','T2h'])for(const year of [2024,2025,2026])for(const target of ['winner','margin','total']){
          await page.locator('#coverage-horizon').selectOption(horizon);await page.locator('#coverage-season').selectOption(String(year));await page.locator('#coverage-target').selectOption(target);
          eq(await page.locator('#coverage-rows tr').count(),18,'All products '+horizon+' '+year+' '+target);
          for(const row of data.sources.completed_horizon_coverage.filter(x=>x.horizon===horizon&&x.season===year&&x.target===target)){
            const cells=await page.locator('#coverage-rows tr[data-bookmaker="'+row.bookmaker+'"]').locator('td').allTextContents();
            eq(cells.slice(1),[row.feature_qualified_n+' / '+row.expected_n,row.reference_n+' / '+row.expected_n,row.strict_original_availability_qualified_n+' / '+row.expected_n,row.predictive_baseline_qualified_n+' / '+row.expected_n],'Exact feature/reference/original/baseline coverage '+horizon+' '+year+' '+target+' '+row.bookmaker);
          }
        }
        await page.locator('#coverage-horizon').selectOption('T60m');await page.locator('#coverage-season').selectOption('2026');await page.locator('#coverage-target').selectOption('winner');
        await page.locator('#sources details summary').click();
        for(const row of data.sources.historical_t60){
          await page.locator('#source-season').selectOption(String(row.season));await page.locator('#source-target').selectOption(row.target);
          const actual=await page.locator('#historical-source-facts dd').allTextContents();
          eq(actual,[row.expected_n_values.join(' / '),String(row.bookmaker_rows),row.qualified_feature_cells.toLocaleString('en-US'),row.reference_cells.toLocaleString('en-US'),String(row.predictive_baseline_cells),String(row.strict_original_cells)],'Historical T-60 counts retain earlier-history scope');
        }
        await page.locator('#source-season').selectOption('2023');await page.locator('#source-target').selectOption('winner');await page.locator('#sources details summary').click();
      }
      await page.locator('#profile').focus();await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
      eq(await page.locator('#profile').inputValue(),'40/60','Keyboard changes validation ratio');
      check((await page.locator('#profile-note').innerText()).includes('zero sensitivity refits'),'Keyboard selection preserves frozen predictions');
      await page.locator('#profile').selectOption('50/50');
      const pending=page.waitForEvent('download');await page.locator('#download').focus();await page.keyboard.press('Enter');const download=await pending;
      const destination=path.join(shots,'FBS_V098_'+variant+'_'+width+'_evidence.json');await download.saveAs(destination);
      eq(JSON.parse(fs.readFileSync(destination,'utf8')),data,'Downloaded evidence matches exact embedded projection');
      receipt.downloads.push({variant,width,sha256:sha(fs.readFileSync(destination)),bytes:fs.statSync(destination).size});fs.unlinkSync(destination);
      const dims=await page.evaluate(()=>({viewport:innerWidth,body:document.documentElement.scrollWidth}));
      check(dims.body<=dims.viewport+1,'No page-wide horizontal overflow');eq(errors,[],'No script errors');
      eq(requests.filter(x=>/^https?:/.test(x)&&!x.startsWith(origin)),[],'No external requests');
      if(variant==='offline')eq(requests.filter(x=>/^https?:/.test(x)),[],'Offline report requires no network');
      const view={variant,width,viewport_height:1000,page_errors:errors,network_requests:requests,page_overflow_pixels:dims.body-dims.viewport};
      if(variant==='source'){
        await page.evaluate(()=>{document.activeElement.blur();window.scrollTo(0,0);});const shot=path.join(shots,'FBS_V098_'+width+'.png');await page.screenshot({path:shot,fullPage:true});view.full_page_screenshot=path.basename(shot);view.screenshot_sha256=sha(fs.readFileSync(shot));
      }
      receipt.views.push(view);await context.close();
    }
    const cases=[['changed_metric',d=>d.selection.leaders[0].annual_values[2]=0.99],['test_selection',d=>d.selection.test_used_for_selection=true],['partial_claimed_complete',d=>d.execution.scientific_complete=true],['false_sustained_pass',d=>d.cpu.current_sustained_pass=true],['t120_relabeled_t60',d=>d.selection.horizon_minutes=60],['new_private_field',d=>d.private_payload='/private/not-public']];
    for(const [label,edit]of cases){const changed=structuredClone(data);edit(changed);invalid.set('/'+label,body.replace(/(<script id="report-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(changed).replace(/</g,'\\u003c')+b));}
    invalid.set('/malformed_json',body.replace(/(<script id="report-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+'{"invalid":'+b));
    for(const url of invalid.keys()){
      const context=await browser.newContext(),page=await context.newPage();await page.goto(origin+url);await page.waitForFunction(()=>document.documentElement.dataset.ready==='error');
      check(await page.locator('#error').isVisible(),url+' visibly rejected');check(!(await page.locator('#report').isVisible()),url+' hides stale evidence');check((await page.locator('#error').innerText()).includes('does not match'),url+' failed expected digest check');receipt.invalid_inputs.push({label:url.slice(1),rejected:true});await context.close();
    }
    receipt.status='PASS';receipt.assertions=assertions;fs.writeFileSync(path.join(shots,'FBS_V098_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');
    process.stdout.write(JSON.stringify({status:'PASS',assertions,views:receipt.views.length,source_html_sha256:receipt.source_html_sha256,receipt:'FBS_V098_BROWSER_RECEIPT.json'})+'\n');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{receipt.status='FAIL';receipt.error=String(error.stack||error);fs.writeFileSync(path.join(shots,'FBS_V098_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');server.close();console.error(error);process.exitCode=1;});
