'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'b095_review.json')));
const output=process.env.NBA_MONITOR_SCREENSHOTS||path.join(__dirname,'browser-output');
fs.mkdirSync(output,{recursive:true});
const display=(n,o)=>o==='winner_accuracy'?(n*100).toFixed(2)+'%':n.toFixed(4);
async function main(){
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE_PATH?{executablePath:process.env.BROWSER_EXECUTABLE_PATH}:{})});
 const result={schema:'sports-edge-lab.nba.b095-browser.v1',status:'PASS',viewports:[]};
 try{for(const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]){
  const context=await browser.newContext({viewport:{width,height}}),page=await context.newPage(),errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  await page.route(/^https?:/,r=>{external.push(r.request().url());r.abort()});
  const url=pathToFileURL(path.join(__dirname,'b095_review.html')).href;
  await page.goto(url);await page.waitForSelector('html[data-review-ready="true"]');
  assert.equal(await page.locator('#leader-rows tr').count(),14);
  assert.match(await page.locator('#evidence-clock').textContent(),/2026-11-17 22:58:57/);
  assert.match(await page.locator('#throughput-detail').textContent(),/did not establish/);
  assert.match(await page.locator('body').textContent(),/RMSE aggregation requires correction/);
  assert.doesNotMatch(await page.locator('body').textContent(),/circa|s3:\/\/|\/home\/|\/workspace\/|\.pyz|undefined|NaN/i);
  for(const r of data.objective_leaders){
   await page.selectOption('#leader-horizon',String(r.horizon_minutes));await page.selectOption('#leader-target',r.objective.split('_')[0]);
   const cells=await page.locator(`#leader-rows tr[data-objective="${r.objective}"][data-horizon="${r.horizon_minutes}"] td`).allTextContents();
   assert.ok(cells[1].includes(r.public_model_alias));
   for(const [j,idx] of [[2,0],[3,1],[5,2]])assert.equal(cells[j],display(r.annual_metrics[idx].value,r.objective));
   assert.ok(cells[4].includes(r.saved_score_aggregation));
  }
  for(const objective of [...new Set(data.weight_sensitivity.map(r=>r.objective))])for(const horizon of ['60','120']){
   await page.selectOption('#weight-objective',objective);await page.selectOption('#weight-horizon',horizon);
   const expected=data.weight_sensitivity.filter(r=>r.objective===objective&&String(r.horizon_minutes)===horizon);
   const rows=await page.locator('#weight-rows tr').allTextContents();assert.equal(rows.length,5);
   expected.forEach((r,i)=>{assert.ok(rows[i].includes(display(r.leader_score,r.objective)));assert.ok(rows[i].includes(r.public_model_alias));assert.ok(rows[i].includes(r.saved_score_aggregation));});
  }
  await page.selectOption('#source-season','all');await page.selectOption('#source-status','all');await page.selectOption('#source-market','all');assert.equal(await page.locator('#source-rows tr').count(),84);
  for(const status of ['COMPLETED','UPCOMING']){
   await page.selectOption('#source-season','2026-27');await page.selectOption('#source-status',status);
   const expected=data.sources.named_provider_coverage.filter(r=>r.season==='2026-27'&&r.population_status===status),rows=await page.locator('#source-rows tr').allTextContents();
   assert.equal(rows.length,expected.length);expected.forEach((r,i)=>assert.ok(rows[i].includes(r.qualified_n.toLocaleString('en-US')+' / '+r.population_n.toLocaleString('en-US'))));
  }
  await page.locator('#all-books summary').click();assert.equal(await page.locator('#book-rows tr').count(),28);await page.uncheck('#book-covered');assert.equal(await page.locator('#book-rows tr').count(),122);await page.fill('#book-search','draftkings');assert.equal(await page.locator('#book-rows tr').count(),1);
  const download=page.waitForEvent('download');await page.click('#download-evidence');const file=await download;assert.deepEqual(JSON.parse(fs.readFileSync(await file.path(),'utf8')),data);
  await page.selectOption('#leader-horizon','all');await page.selectOption('#leader-target','all');await page.evaluate(()=>window.scrollTo(0,0));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),true);
  await page.screenshot({path:path.join(output,`nba-b095-review-${name}.png`),fullPage:false});
  await page.locator('#leaders').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,`nba-b095-metrics-${name}.png`),fullPage:false});
  await context.close();const fresh=await browser.newContext({viewport:{width,height}}),reopened=await fresh.newPage();await reopened.goto(url);await reopened.waitForSelector('html[data-review-ready="true"]');assert.equal(await reopened.locator('#leader-rows tr').count(),14);await fresh.close();
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);result.viewports.push({name,leader_roles:14,sensitivity_rows:70,provider_rows:84,exact_download:true,reopen_verified:true,page_errors:0,external_requests:0});
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(output,'nba-b095-browser-review.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
