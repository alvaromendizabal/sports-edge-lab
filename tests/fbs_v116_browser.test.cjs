'use strict';
// Public presentation checks only. No owner research, credentials or providers.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const moduleDir=process.env.PLAYWRIGHT_MODULE_DIR||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleDir),root=path.resolve(__dirname,'..');
const file=path.join(root,'docs/fbs/v116/index.html'),body=fs.readFileSync(file,'utf8'),data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/v116/data/review.json'),'utf8'));
const shots=process.env.FBS_SCREENSHOTS||path.join(root,'tmp/fbs-v116-browser');fs.mkdirSync(shots,{recursive:true});
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');let assertions=0;
const eq=(a,b,label)=>{assertions++;assert.deepEqual(a,b,label);},check=(value,label)=>{assertions++;assert.ok(value,label);};
const receipt={schema:'fbs.v116.public-browser-review.v1',status:'RUNNING',github_sha:process.env.GITHUB_SHA||null,github_head_sha:process.env.GITHUB_HEAD_SHA||null,html_sha256:sha(body),html_bytes:Buffer.byteLength(body),views:[],invalid_inputs:[],owner_runs_started:0,new_fits:0};
const invalid=new Map();const server=http.createServer((req,res)=>{const content=req.url==='/'?body:invalid.get(req.url);res.writeHead(content?200:404,{'content-type':'text/html;charset=utf-8'});res.end(content||'Not found');});
(async()=>{
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const origin='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:process.env.FBS_BROWSER_EXECUTABLE||undefined});
  try{
    for(const mode of ['served','offline'])for(const width of [1440,390]){
      const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});const page=await context.newPage(),errors=[],requests=[];
      page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>requests.push(request.url()));
      await page.goto(mode==='served'?origin+'/':'file://'+file);await page.waitForFunction(()=>document.documentElement.dataset.reportReady==='true');
      const current=data.current_diagnostic,initial=current?.status==='FRESH_SOURCE_AND_SELECTED_INFERENCE'?current:data.snapshot;
      eq(await page.locator('#game-rows tr').count(),initial.weekly_games,'Complete weekly population');
      eq(await page.locator('#gap-count').innerText(),String(initial.weekly_missing_policy_games),'All missing weekly outputs disclosed');
      if(current){
        eq(await page.locator('#current-provider-cards article').count(),3,'Named-provider observations remain separate');
        eq(await page.locator('#current-all-coverage tr').count(),current.market_coverage.length,'Every bookmaker-target coverage row retained');
        check((await page.locator('#metric-clock').innerText()).includes('n=822'),'Historical metric denominator is unchanged');
        if(current.status==='FRESH_SOURCE_AND_SELECTED_INFERENCE')eq(await page.evaluate(()=>FBS_REVIEW.evidence()),'fresh','Fresh inference is initial view');
        await page.locator('#evidence-view').selectOption('retained');
        eq(await page.locator('#gap-count').innerText(),String(data.snapshot.weekly_missing_policy_games),'Retained old gaps are separately reviewable');
      }
      eq(await page.locator('#metric-rows tr').count(),9,'All objective-specific annual metrics');
      if(data.current_test_diagnostic){eq(await page.locator('#current-test-rows tr').count(),9,'All separately updated824-game objectives');check((await page.locator('#current-test-summary').innerText()).includes('824'),'Updated diagnostic full denominator');}
      check((await page.locator('#snapshot-clock').innerText()).includes('V114'),'Scientific snapshot remains dated');
      await page.locator('#gap-filter').click();eq(await page.locator('#game-rows tr').count(),data.snapshot.weekly_missing_policy_games,'Gap filter never imputes missing games');
      await page.locator('#search').fill('Kentucky');eq(await page.locator('#game-rows tr').count(),1,'Missing Kentucky game remains searchable');
      await page.locator('#reset').click();eq(await page.locator('#game-rows tr').count(),data.snapshot.weekly_games,'Reset restores full weekly population');
      const cellsBefore=await page.locator('#game-rows tr:first-child td:nth-child(3)').innerText();
      await page.locator('#winner-role').selectOption('P07');const cellsAfter=await page.locator('#game-rows tr:first-child td:nth-child(3)').innerText();check(cellsBefore!==cellsAfter,'Winner objective changes selected values');
      await page.locator('#margin-role').selectOption('P02');check((await page.locator('#game-rows tr:first-child td:nth-child(4)').innerText()).includes('Prior fallback'),'Market-only margin fallback is visible');
      await page.locator('[data-detail]').first().click();check(await page.locator('#game-dialog').isVisible(),'All-policy dialog opens');eq(await page.locator('.detail-policy').count(),8,'Eight exact selected roles in detail');check((await page.locator('#game-dialog-body').innerText()).includes('Not recorded'),'Unknown composite flags remain unknown');await page.keyboard.press('Escape');check(!await page.locator('#game-dialog').isVisible(),'Escape closes detail');
      await page.locator('#population').selectOption('season');eq(await page.evaluate(()=>FBS_REVIEW.filtered().length),data.snapshot.game_count,'Full observed season retained');
      await page.locator('#gap-filter').click();eq(await page.evaluate(()=>FBS_REVIEW.filtered().length),data.games.filter(g=>g.covered_policies<8).length,'All-season gaps retained');
      await page.locator('#reset').click();
      for(const profile of ['50/50','40/60','30/70','20/80','10/90']){await page.locator(`[data-profile="${profile}"]`).click();eq(await page.locator('#sensitivity-rows tr').count(),9,'Every saved sensitivity role');eq(await page.evaluate(()=>FBS_REVIEW.profile()),profile,'Requested evaluation profile selected');}
      const downloadWait=page.waitForEvent('download');await page.locator('#download-json').evaluate(button=>button.closest('details').open=true);
      await page.locator('#download-json').scrollIntoViewIfNeeded();await page.locator('#download-json').click();
      const download=await downloadWait,destination=path.join(shots,`FBS_V116_${mode}_${width}_evidence.json`);await download.saveAs(destination);eq(JSON.parse(fs.readFileSync(destination,'utf8')),data,'Complete allowlisted JSON download');
      const csvWait=page.waitForEvent('download');await page.locator('#download-csv').click();const csv=await csvWait,csvFile=path.join(shots,`FBS_V116_${mode}_${width}_games.csv`);await csv.saveAs(csvFile);eq(fs.readFileSync(csvFile,'utf8').trim().split('\r\n').length,data.snapshot.weekly_games+1,'Visible CSV includes every weekly game');
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No viewport overflow');eq(errors,[],'No page script errors');eq(requests.filter(url=>!url.startsWith(origin)&&!url.startsWith('file://')),[],'No external runtime dependencies');
      if(current?.status==='FRESH_SOURCE_AND_SELECTED_INFERENCE')await page.locator('#evidence-view').selectOption('fresh');
      await page.evaluate(()=>scrollTo(0,0));if(mode==='served')await page.screenshot({path:path.join(shots,`FBS_V116_${width}.png`),fullPage:true});
      receipt.views.push({mode,width,script_errors:0,external_requests:0});await context.close();
    }
    const raw=body.match(/<script id="fbs-evidence" type="application\/json">(.*?)<\/script>/s)[1],digest=sha(raw);
    const cases=[['changed_bytes',d=>d.execution.new_model_fits=1,false],['false_success',d=>d.execution.owner_executions_successful=1,true],['test_selection',d=>d.selection.test_used_for_selection=true,true],['fake_source_refresh',d=>d.snapshot.market_snapshot_refreshed=true,true],['shrunk_population',d=>d.games.pop(),true],['fake_current_quotes',d=>d.providers.current_week_qualified_quotes=1,true]];
    if(data.current_diagnostic)cases.push(['fresh_fit_claim',d=>d.current_diagnostic.new_model_fits=1,true],['false_t60_market',d=>d.current_diagnostic.market_rows[0].strict_t60_model_input_qualified=true,true]);
    for(const [name,mutate,rehash] of cases){const changed=JSON.parse(JSON.stringify(data));mutate(changed);const payload=JSON.stringify(changed).replace(/</g,'\\u003c');let html=body.replace(raw,payload);if(rehash)html=html.replaceAll(digest,sha(payload));invalid.set('/'+name,html);const page=await browser.newPage();await page.goto(origin+'/'+name);await page.waitForFunction(()=>document.documentElement.dataset.reportReady==='error');check(await page.locator('#report').isHidden(),'Invalid report is hidden');check(await page.locator('#evidence-error').isVisible(),'Integrity failure is visible');receipt.invalid_inputs.push(name);await page.close();}
    receipt.status='PASS';receipt.assertions=assertions;fs.writeFileSync(path.join(shots,'FBS_V116_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{receipt.status='FAIL';receipt.error=String(error.stack||error);fs.writeFileSync(path.join(shots,'FBS_V116_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.error(error);process.exitCode=1;server.close();});
