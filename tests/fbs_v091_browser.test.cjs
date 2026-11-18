'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const moduleDir=process.env.PLAYWRIGHT_MODULE_DIR||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleDir);
const root=path.resolve(__dirname,'..'),file=path.join(root,'docs/fbs/v091/index.html'),body=fs.readFileSync(file,'utf8'),data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/v091/data/status.json'),'utf8'));
const shots=process.env.FBS_SCREENSHOTS||path.join(root,'tmp/fbs-v091-browser');fs.mkdirSync(shots,{recursive:true});
let checks=0;function check(condition,message){checks++;assert.ok(condition,message);}function eq(a,b,message){checks++;assert.deepEqual(a,b,message);}
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const receipt={schema:'fbs.v091.public-browser-review.v1',status:'RUNNING',github_sha:process.env.GITHUB_SHA||null,github_head_sha:process.env.GITHUB_HEAD_SHA||null,source_html_sha256:sha(body),source_html_bytes:Buffer.byteLength(body),views:[],downloads:[],invalid_inputs:[],research_executions:0};
const server=http.createServer((req,res)=>{if(req.url==='/'){res.writeHead(200,{'content-type':'text/html; charset=utf-8'});res.end(body);}else{res.writeHead(404);res.end('Not found');}});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,executablePath:process.env.FBS_BROWSER_EXECUTABLE||undefined});
 try{
  for(const variant of ['source','offline'])for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true}),page=await context.newPage();let errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
   await page.goto(variant==='source'?origin+'/':'file://'+file);await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
   eq(await page.locator('#new-fits').innerText(),'0','Saved V090 fit count stays zero');eq(await page.locator('#next-jobs').innerText(),'936','Prepared jobs are separate');
   check((await page.locator('#execution-facts').innerText()).includes('0 / 1'),'Actual failure count shown');check((await page.locator('#retained-facts').innerText()).includes('919 / 934 / 752'),'Retained equal cohorts shown');
   check((await page.locator('#count-note').innerText()).includes('completeness flag is false'),'Incomplete attempt ledger remains disclosed');
   check((await page.locator('#worker-facts').innerText()).includes('Pending owner execution'),'No invented optimizer CPU');
   const decimal=(data.storage.latest_return_bytes/1e9).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:3})+' GB';eq(await page.locator('#return-size').innerText(),decimal,'Decimal size matches bytes');
   await page.locator('#unit').selectOption('GiB');const binary=(data.storage.latest_return_bytes/1073741824).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:3})+' GiB';eq(await page.locator('#return-size').innerText(),binary,'Binary size matches same bytes');
   eq(await page.locator('.storage-row').count(),3,'Only three observed/prepared size rows');
   await page.locator('#unit').selectOption('GB');await page.locator('summary').click();eq(await page.locator('#evidence-list li').count(),data.evidence.length,'All approved evidence pins shown');
   for(const pin of data.evidence)check((await page.locator('#evidence-list').innerText()).includes(pin.sha256),'Exact evidence pin remains visible');
   const pendingDownload=page.waitForEvent('download');await page.locator('#download').focus();await page.keyboard.press('Enter');const download=await pendingDownload;const dl=path.join(shots,`FBS_V091_${variant}_${width}_download.json`);await download.saveAs(dl);eq(JSON.parse(fs.readFileSync(dl,'utf8')),data,'Keyboard-triggered download is the complete exact public evidence');receipt.downloads.push({variant,width,sha256:sha(fs.readFileSync(dl)),bytes:fs.statSync(dl).size});
   const dims=await page.evaluate(()=>({viewport:window.innerWidth,body:document.documentElement.scrollWidth}));check(dims.body<=dims.viewport+1,'No page-wide horizontal overflow');
   const metricBoxes=await page.locator('.metric').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return{x:r.x,right:r.right,top:r.top,bottom:r.bottom};}));
   for(const b of metricBoxes)check(b.x>=0&&b.right<=width+1&&b.bottom>b.top,'Metric cards fit the viewport');
   eq(errors,[],'No script errors');eq(requests.filter(x=>/^https?:/.test(x)&&!x.startsWith(origin)),[],'No external network requests');if(variant==='offline')eq(requests.filter(x=>/^https?:/.test(x)),[],'Standalone report makes zero HTTP requests');
   await page.locator('summary').click();await page.evaluate(()=>window.scrollTo(0,0));const screenshot=path.join(shots,`FBS_V091_${variant}_${width}.png`);await page.screenshot({path:screenshot,fullPage:true});
   receipt.views.push({variant,width,viewport_height:1000,page_errors:errors,network_requests:requests,full_page_screenshot:path.basename(screenshot),screenshot_sha256:sha(fs.readFileSync(screenshot)),page_overflow_pixels:dims.body-dims.viewport});await context.close();
  }
  for(const [label,edit] of [['wrong_owner',d=>d.owner='NBA'],['prepared_fit_claim',d=>d.prepared.new_scientific_fits=1],['test_selection',d=>d.selection.test_used_for_selection=true],['false_publication',d=>d.publication.website_deployed=true]]){
   const changed=structuredClone(data);edit(changed);const bad=body.replace(/(<script id="report-data" type="application\/json">)[\s\S]*?(<\/script>)/,(_,a,b)=>a+JSON.stringify(changed).replace(/</g,'\\u003c')+b);const context=await browser.newContext(),page=await context.newPage();await page.setContent(bad);await page.waitForFunction(()=>document.documentElement.dataset.ready==='error');check(await page.locator('#error').isVisible(),label+' error visible');check(!(await page.locator('#report').isVisible()),label+' stale report hidden');receipt.invalid_inputs.push({label,rejected:true});await context.close();
  }
  receipt.status='PASS';receipt.assertions=checks;fs.writeFileSync(path.join(shots,'FBS_V091_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');process.stdout.write(JSON.stringify({status:receipt.status,assertions:checks,views:receipt.views.length,source_html_sha256:receipt.source_html_sha256,receipt:'FBS_V091_BROWSER_RECEIPT.json'})+'\n');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(err=>{receipt.status='FAIL';receipt.error=String(err.stack||err);fs.writeFileSync(path.join(shots,'FBS_V091_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');server.close();console.error(err);process.exitCode=1;});
