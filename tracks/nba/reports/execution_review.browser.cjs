/* Exact saved operational evidence and actual offline browser interactions. */
'use strict';
require('node:child_process').execFileSync('python',[require('node:path').join(__dirname,'restore_snapshot_assets.py')],{stdio:'pipe'});
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {expandHtml}=require('./standalone_payload.cjs');
const root=__dirname,read=n=>fs.readFileSync(path.join(root,n)),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const value=JSON.parse(read('latest_execution_review.json')),raw=read('latest_research_outputs.html'),body=expandHtml(raw);
const match=body.match(/<script id="nba-execution-data" type="application\/json">([\s\S]*?)<\/script>/);assert.ok(match);assert.deepEqual(JSON.parse(match[1]),value);
for(const [name,pin]of Object.entries(value.science_preservation.source_sha256))assert.equal(hash(read(name)),pin,name);
assert.equal(value.latest_owner_execution.new_confirmed_scientific_fits,318);assert.equal(value.observed_runtime.peak_concurrent_scientific_fits,6);
assert.equal(value.observed_runtime.twelve_core_scientific_utilization_proven,false);assert.equal(value.replacement_engineering.owner_execution_completed,false);
async function ready(page){await page.waitForFunction(()=>window.__SEL_OFFLINE_READY__||window.__SEL_OFFLINE_ERROR__,null,{timeout:120000});assert.equal(await page.evaluate(()=>window.__SEL_OFFLINE_ERROR__),null);}
async function check(page,viewport,name){
 const errors=[],external=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/*',route=>{if(/^https?:/.test(route.request().url())){external.push(route.request().url());return route.abort();}return route.continue();});
 await page.setViewportSize(viewport);await page.goto('file://'+path.join(root,'latest_research_outputs.html'),{waitUntil:'load'});await ready(page);
 assert.deepEqual(await page.locator('#nba-execution-data').evaluate(n=>JSON.parse(n.textContent)),value);
 assert.match(await page.locator('#nba-execution-outcome').textContent(),/318 native estimator fits and 13,860 new forecasts/);
 assert.match(await page.locator('#nba-execution-source-clock').textContent(),/2026-11-13T17:26:12\.502657\+00:00/);
 assert.match(await page.locator('#nba-execution-failures').textContent(),/B075_SCHEDULE_SOURCE_REPORT_BINDING_REQUIRED/);
 assert.match(await page.locator('#nba-execution-replacement-status').textContent(),/B083 has no completed owner-host sports run/);
 assert.equal(await page.locator('#nba-execution-evidence tbody tr').count(),12);
 const evidence=await page.locator('#nba-execution-evidence').textContent();
 assert.match(evidence,/570 heartbeats; maximum gap 10\.737294 seconds/);assert.match(evidence,/14,559,581 supplied compressed body bytes/);
 assert.match(evidence,/Peak 6 concurrent native fits/);assert.match(evidence,/Peak 10\.90101 was transport finalization/);
 assert.match(await page.locator('#nba-execution-budget-test').textContent(),/5,536 authentic issue-file pins/);
 assert.match(await page.locator('#nba-execution-budget-test').textContent(),/No scientific field was dropped/);
 assert.match(await page.locator('#nba-execution-projection-test').textContent(),/45\.21% less/);
 const packageText=await page.locator('#nba-execution-package-status').textContent();assert.match(packageText,value.replacement_engineering.package_verification.status==='PASS'?/PASS:/ : /verification is pending/);
 await page.locator('#nba-execution-repairs > summary').click();assert.equal(await page.locator('#nba-execution-repairs').evaluate(n=>n.open),true);
 assert.equal(await page.locator('#nba-execution-repairs li').count(),value.replacement_engineering.implemented_repairs.length);
 assert.equal(await page.locator('#nba-v9-data').evaluate(n=>JSON.parse(n.textContent).coverage.observed_games),1274);
 assert.equal(await page.evaluate(()=>Object.keys(window.NBA_PUBLIC_REPORT.issues).length),14054);
 if(name==='desktop'){const assets=JSON.parse(read('snapshot_asset_manifest.json'));for(const asset of assets.files){
  const downloadPromise=page.waitForEvent('download');await page.locator('#sel-complete-downloads [data-sel-json="'+asset.name+'"]').click();const download=await downloadPromise;
  assert.equal(download.suggestedFilename(),asset.name);const bytes=fs.readFileSync(await download.path());assert.equal(bytes.length,asset.original_pin.bytes);assert.equal(hash(bytes),asset.original_pin.sha256);
 }}
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'horizontal viewport overflow');
 const out=process.env.NBA_MONITOR_SCREENSHOTS;if(out){fs.mkdirSync(out,{recursive:true});await page.locator('#nba-execution-title').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'nba-b083-execution-'+name+'.png'),fullPage:false});}
 await page.reload({waitUntil:'load'});await ready(page);assert.deepEqual(await page.locator('#nba-execution-data').evaluate(n=>JSON.parse(n.textContent)),value);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);return{name,viewport,console_or_page_errors:0,external_requests:0,offline_reopen:true,verified_games:1274,verified_selected_issues:14054};
}
(async()=>{const browser=await require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright').chromium.launch({headless:true});const results=[];
 try{for(const [v,n]of[[{width:1440,height:1050},'desktop'],[{width:390,height:844},'mobile']]){const page=await browser.newPage();results.push(await check(page,v,n));await page.close();}
 const unsupported=await browser.newPage();await unsupported.addInitScript(()=>{window.DecompressionStream=undefined;});await unsupported.goto('file://'+path.join(root,'latest_research_outputs.html'));await unsupported.waitForFunction(()=>window.__SEL_OFFLINE_ERROR__);assert.equal(await unsupported.locator('#sel-offline-ready').getAttribute('data-state'),'error');assert.equal(await unsupported.locator('#sel-offline-ready a[href="latest_research_outputs.json.gz"]').count(),1);assert.equal(await unsupported.evaluate(()=>window.__SEL_OFFLINE_READY__),false);await unsupported.close();
 }finally{await browser.close();}
 const receipt={schema:'sports-edge-lab.nba.execution-review.browser.v2',status:'PASS',display_sha256:hash(raw),evidence_sha256:hash(read('latest_execution_review.json')),new_fits:0,new_forecasts:0,lossless_offline_restoration_verified:true,unsupported_browser_fallback_verified:true,exact_original_JSON_downloads_verified:2,results};
 if(process.env.NBA_MONITOR_SCREENSHOTS)fs.writeFileSync(path.join(process.env.NBA_MONITOR_SCREENSHOTS,'B083_EXECUTION_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;});
