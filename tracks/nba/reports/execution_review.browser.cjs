/* Saved aggregate oracle; no provider requests, fitting, forecasts or rescoring. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,read=name=>fs.readFileSync(path.join(root,name)),hash=body=>crypto.createHash('sha256').update(body).digest('hex');
const value=JSON.parse(read('latest_execution_review.json')),pageBody=read('latest_research_outputs.html').toString();
const match=pageBody.match(/<script id="nba-execution-data" type="application\/json">([\s\S]*?)<\/script>/);
assert.ok(match);assert.deepEqual(JSON.parse(match[1]),value);
for(const [name,pin]of Object.entries(value.science_preservation.source_sha256))assert.equal(hash(read(name)),pin,name);
assert.equal(value.latest_owner_execution.new_confirmed_scientific_fits,0);
assert.equal(value.observed_runtime.twelve_core_scientific_utilization_proven,false);
assert.equal(value.replacement_engineering.owner_execution_completed,false);
assert.equal(value.replacement_engineering.all_deployed_sports_retrofitted,false);

async function check(page,viewport,name){
 const errors=[],external=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',route=>{const url=route.request().url();if(/^https?:/.test(url)){external.push(url);return route.abort();}return route.continue();});
 await page.setViewportSize(viewport);await page.goto('file://'+path.join(root,'latest_research_outputs.html'),{waitUntil:'load'});
 const section=page.locator('#nba-execution-review');await section.waitFor();
 assert.deepEqual(await page.locator('#nba-execution-data').evaluate(n=>JSON.parse(n.textContent)),value);
 assert.match(await page.locator('#nba-execution-outcome').textContent(),/zero confirmed new scientific fits/);
 assert.match(await page.locator('#nba-execution-source-clock').textContent(),/2026-11-12T02:02:29\.830904\+00:00/);
 assert.match(await page.locator('#nba-execution-fatal').textContent(),/Both guards remain active/);
 assert.match(await page.locator('#nba-execution-replacement-status').textContent(),/No B079 owner execution/);
 assert.equal(await page.locator('#nba-execution-evidence tbody tr').count(),8);
 await page.locator('#nba-execution-repairs > summary').click();assert.equal(await page.locator('#nba-execution-repairs').evaluate(n=>n.open),true);
 assert.equal(await section.locator('li').count(),value.replacement_engineering.implemented_repairs.length+value.replacement_engineering.verification_summary.length);
 assert.equal(await page.locator('#nba-v9-data').evaluate(n=>JSON.parse(n.textContent).coverage.observed_games),1274);
 assert.ok(await page.locator('#forecast-rows').count());
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'horizontal viewport overflow');
 const screenshotDir=process.env.NBA_MONITOR_SCREENSHOTS;
 if(screenshotDir){fs.mkdirSync(screenshotDir,{recursive:true});await section.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(screenshotDir,'nba-b079-execution-'+name+'.png'),fullPage:false});}
 await page.locator('#nba-execution-repairs > summary').click();await page.reload({waitUntil:'load'});
 assert.deepEqual(await page.locator('#nba-execution-data').evaluate(n=>JSON.parse(n.textContent)),value);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);return{name,viewport,console_or_page_errors:errors.length,external_requests:external.length,offline_reopen:true};
}

(async()=>{
 const dependency=process.env.PLAYWRIGHT_MODULE_DIR||'playwright',browser=await require(dependency).chromium.launch({headless:true});
 const results=[];try{for(const[v,n]of[[{width:1440,height:1050},'desktop'],[{width:390,height:844},'mobile']]){const page=await browser.newPage();results.push(await check(page,v,n));await page.close();}}
 finally{await browser.close();}
 const receipt={schema:'sports-edge-lab.nba.execution-review.browser.v1',status:'PASS',display_sha256:hash(read('latest_research_outputs.html')),evidence_sha256:hash(read('latest_execution_review.json')),unchanged_research_sources:value.science_preservation.source_sha256,new_fits:0,new_forecasts:0,results};
 if(process.env.NBA_MONITOR_SCREENSHOTS)fs.writeFileSync(path.join(process.env.NBA_MONITOR_SCREENSHOTS,'B079_EXECUTION_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');
 console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;});
