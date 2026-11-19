'use strict';
// Served/offline actual evidence rendering only. No research, providers or deployment.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const moduleDir=process.env.PLAYWRIGHT_MODULE_DIR||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleDir),root=path.resolve(__dirname,'..'),file=path.join(root,'docs/fbs/v099/completed/index.html');
const body=fs.readFileSync(file,'utf8'),data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/v099/completed/data/status.json'),'utf8'));
const shots=process.env.FBS_SCREENSHOTS||path.join(root,'tmp/fbs-v099-completed-browser');fs.mkdirSync(shots,{recursive:true});
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');let assertions=0;
const eq=(a,b,n)=>{assertions++;assert.deepEqual(a,b,n)},check=(a,n)=>{assertions++;assert.ok(a,n)};
const receipt={schema:'fbs.v099.completed-public-browser-review.v1',status:'RUNNING',github_sha:process.env.GITHUB_SHA||null,github_head_sha:process.env.GITHUB_HEAD_SHA||null,source_html_sha256:sha(body),source_html_bytes:Buffer.byteLength(body),views:[],downloads:[],invalid_inputs:[],owner_executions_started_by_check:0};
const invalid=new Map(),server=http.createServer((req,res)=>{const content=req.url==='/'?body:invalid.get(req.url);res.writeHead(content?200:404,{'content-type':'text/html; charset=utf-8'});res.end(content||'Not found')});
const fmt=(v,m)=>m==='accuracy'?(v*100).toFixed(2)+'%':v.toFixed(4);
(async()=>{await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.FBS_BROWSER_EXECUTABLE||undefined});
try{for(const variant of ['served','offline'])for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));await page.goto(variant==='served'?origin+'/':'file://'+file);
  await page.waitForFunction(()=>document.documentElement.dataset.reportReady==='true');
  eq(await page.locator('#kpis strong').allTextContents(),['600','1,125','934','0'],'Actual completed scope');
  check((await page.locator('#primary-change').innerText()).includes('0.0448 percentage points'),'Small descriptive accuracy change disclosed');
  check((await page.locator('#uncertainty-title').innerText()).includes('0 improved / 373 worse'),'Negative findings visible before expanding');
  check((await page.locator('#historical-tally').innerText()).includes('4 operational successes, 6 historical failed attempts, 1 separately refused duplicate launch'),'Scoped tally reconciled visibly');
  eq(await page.locator('#remaining-work tbody tr').count(),6,'All remaining branches disclosed');
  eq(await page.locator('#cpu tbody tr').count(),3,'All scientific phases');
  eq(await page.locator('#cpu tbody tr td:nth-child(5)').allTextContents(),['11.00','7.28','5.67'],'Actual CPU cores, not36configuredworkers');
  check((await page.locator('#time-facts').innerText()).includes('$0.8484'),'Final supervisor cost estimate');
  for(const profile of data.science.outcome.profiles)for(const target of ['all','winner','margin','total']){
    await page.locator('#profile').selectOption(profile);await page.locator('#target').selectOption(target);
    const expected=data.science.leaders.filter(r=>r.profile===profile&&(target==='all'||r.target===target)).sort((a,b)=>(a.target+'/'+a.objective).localeCompare(b.target+'/'+b.objective));
    const rows=await page.locator('#leaders tbody tr').evaluateAll(rs=>rs.map(r=>Array.from(r.querySelectorAll('td'),x=>x.textContent)));
    eq(rows.length,expected.length,'Complete target/profile objective count');
    rows.forEach((cells,i)=>{const r=expected[i];eq(cells.slice(2,5),r.annual.map(a=>fmt(a.metric,r.objective)),'Source-bound annual metrics');eq(cells[5],fmt(r.validation_score,r.objective),'Validation-only selection score');check(cells[6].includes('919 / 919')&&cells[6].includes('934 / 934')&&cells[6].includes('755 / 755'),'Full annual denominators');});
  }
  for(const season of ['all','2024','2025','2026']){await page.locator('#source-season').selectOption(season);eq(await page.locator('#sources tbody tr').count(),season==='all'?9:3,'Source filter preserves each target');}
  await page.locator('#profile').focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');eq(await page.locator('#profile').inputValue(),'40/60','Keyboard profile navigation');
  await page.locator('#profile').selectOption('50/50');await page.locator('#target').selectOption('all');await page.locator('#source-season').selectOption('all');
  const awaited=page.waitForEvent('download');await page.locator('#download').focus();await page.keyboard.press('Enter');const download=await awaited,destination=path.join(shots,'FBS_V099_COMPLETED_'+variant+'_'+width+'_download.json');await download.saveAs(destination);
  eq(JSON.parse(fs.readFileSync(destination,'utf8')),data,'Exact bounded projection download');receipt.downloads.push({variant,width,sha256:sha(fs.readFileSync(destination))});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'No viewport overflow');eq(errors,[],'No page errors');eq(requests.filter(u=>!u.startsWith(origin)&&!u.startsWith('file://')),[],'No external requests');
  await page.evaluate(()=>window.scrollTo(0,0));if(variant==='served')await page.screenshot({path:path.join(shots,'FBS_V099_COMPLETED_'+width+'.png'),fullPage:true});
  receipt.views.push({variant,width,script_errors:0,external_requests:0});await context.close();
}
const original=body.match(/<script id="report-data" type="application\/json">(.*?)<\/script>/s)[1],originalDigest=sha(original);
const cases=[['changed_content',d=>d.science.leaders[0].annual[0].metric=.1,false],['test_selection',d=>d.operations.science.test_outcomes_used_for_selection=true,true],['false_full_science',d=>d.operations.full_v13_program_complete=true,true],['false_cpu_pass',d=>d.operations.cpu.full_capacity_pass=true,true]];
for(const[name,change,rehash]of cases){const d=JSON.parse(JSON.stringify(data));change(d);const raw=JSON.stringify(d).replace(/</g,'\\u003c');let html=body.replace(original,raw);if(rehash)html=html.replace("expected='"+originalDigest+"'","expected='"+sha(raw)+"'");invalid.set('/invalid-'+name,html);const page=await browser.newPage();await page.goto(origin+'/invalid-'+name);await page.waitForFunction(()=>document.documentElement.dataset.reportReady==='error');check(await page.locator('#report').isHidden(),'Invalid scope or content never displayed');check(await page.locator('#error').isVisible(),'Visible integrity/scope failure');receipt.invalid_inputs.push(name);await page.close();}
receipt.status='PASS';receipt.assertions=assertions;fs.writeFileSync(path.join(shots,'FBS_V099_COMPLETED_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}})().catch(error=>{receipt.status='FAIL';receipt.error=String(error.stack||error);fs.writeFileSync(path.join(shots,'FBS_V099_COMPLETED_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.error(error);process.exitCode=1;server.close();});
