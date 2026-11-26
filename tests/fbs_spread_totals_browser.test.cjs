'use strict';
// Exact public board interaction checks; no research, credentials or provider calls.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const moduleDir=process.env.PLAYWRIGHT_MODULE_DIR||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleDir),root=path.resolve(__dirname,'..');
const file=path.join(root,'docs/fbs/spread-totals/index.html'),body=fs.readFileSync(file,'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/spread-totals/board.json'),'utf8'));
const shots=process.env.FBS_SCREENSHOTS||path.join(root,'tmp/fbs-spread-totals-browser');fs.mkdirSync(shots,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const receipt={schema:'fbs.spread-totals.public-browser-review.v1',status:'RUNNING',github_sha:process.env.GITHUB_SHA||null,github_head_sha:process.env.GITHUB_HEAD_SHA||null,html_sha256:sha(body),views:[],assertions:0,owner_runs_started:0,new_fits:0};
const eq=(a,b,label)=>{receipt.assertions++;assert.deepEqual(a,b,label);};
const check=(v,label)=>{receipt.assertions++;assert.ok(v,label);};
const weekly=data.games.filter(g=>g.is_current_week),allIds=new Set(data.games.map(g=>g.game_id));
const qualified=market=>data.contracts.filter(c=>c.market===market&&c.primary_for_game&&c.probability_qualified&&c.settlement_status==='pending'&&weekly.some(g=>g.game_id===c.game_id));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.FBS_BROWSER_EXECUTABLE||undefined});
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});const page=await context.newPage(),errors=[],external=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:')&&!r.url().startsWith('blob:'))external.push(r.url());});
   await page.goto('file://'+file);await page.waitForSelector('.game');
   eq(await page.title(),'Spread & Totals · FBS · Sports Edge Lab','Exact product and owner');
   eq(await page.locator('.game').count(),weekly.length,'Complete weekly game population');
   const initialIds=await page.locator('.game').evaluateAll(nodes=>nodes.map(n=>n.dataset.gameId));
   eq(new Set(initialIds),new Set(weekly.map(g=>g.game_id)),'Weekly IDs have no hidden omissions');
   const first=weekly.slice().sort((a,b)=>(a.kickoff_utc||'9999').localeCompare(b.kickoff_utc||'9999')||a.game_id.localeCompare(b.game_id))[0];
   const firstCard=page.locator(`[data-game-id="${first.game_id}"]`);check((await firstCard.innerText()).includes(first.away),'Real away team rendered');check((await firstCard.innerText()).includes(first.home),'Real home team rendered');
   check((await firstCard.innerText()).includes('Home − away:'),'Signed margin orientation visible');
   await firstCard.locator('summary').first().click();check(await firstCard.locator('details').first().evaluate(n=>n.open),'Game evidence opens by native disclosure');
   await page.locator('#scope').selectOption('season');eq(await page.locator('.game').count(),allIds.size,'Full season manifest');
   await page.locator('#scope').selectOption('week');await page.locator('#status').selectOption('scheduled');eq(await page.locator('.game').count(),weekly.filter(g=>g.status==='scheduled').length,'Upcoming filter');
   await page.locator('#status').selectOption('all');await page.locator('#search').fill(first.home);check(await page.locator('.game').count()>=1,'Team search retains matching game');await page.locator('#search').fill('');
   for(const market of ['spread','total']){
    await page.locator(`[data-tab="${market}"]`).click();eq(await page.locator('.rank-row').count(),qualified(market).length,'Only qualified pending primary probabilities rank');
    if(!qualified(market).length)check((await page.locator('#content').innerText()).includes('No contract-qualified ranking is available'),'Probability gap is visible');
    await page.locator('#rank-mode').selectOption('return');eq(await page.locator('.rank-row').count(),qualified(market).filter(c=>c.best_return_side).length,'Net return requires separate qualification');
    await page.locator('#rank-mode').selectOption('probability');
   }
   await page.locator('[data-tab="gaps"]').click();eq(await page.locator('#content tbody tr').count(),data.missing_inputs.filter(x=>weekly.some(g=>g.game_id===x.game_id)).length,'Full weekly input ledger');
   await page.locator('[data-tab="evidence"]').click();eq(await page.locator('.performance-table tbody tr').count(),data.performance.length,'Every reported metric and denominator retained');eq(await page.locator('details .source-coverage tbody tr').count(),data.source_coverage?.length||0,'Every source target cell retained separately');
   await page.locator('[data-tab="graphics"]').click();eq(await page.locator('.graphic-card').count(),data.graphics?.pages?.length||0,'All phone graphics exposed');
   await page.locator('[data-tab="games"]').click();
   const jsonWait=page.waitForEvent('download');await page.locator('#download-json').click();const jd=await jsonWait,jp=path.join(shots,`FBS_SPREAD_TOTALS_${width}_board.json`);await jd.saveAs(jp);eq(JSON.parse(fs.readFileSync(jp,'utf8')),data,'Complete public JSON download');
   const csvWait=page.waitForEvent('download');await page.locator('#download-csv').click();const cd=await csvWait,cp=path.join(shots,`FBS_SPREAD_TOTALS_${width}_games.csv`);await cd.saveAs(cp);eq(fs.readFileSync(cp,'utf8').trim().split('\r\n').length,weekly.length+1,'CSV includes every weekly game');
   check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No page overflow');eq(errors,[],'No script errors');eq(external,[],'No remote runtime dependencies');
   await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(shots,`FBS_SPREAD_TOTALS_${width}.png`),fullPage:false});
   receipt.views.push({width,script_errors:0,external_requests:0,weekly_games:weekly.length,season_games:allIds.size});await context.close();
  }
  receipt.status='PASS';fs.writeFileSync(path.join(shots,'FBS_SPREAD_TOTALS_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
 }finally{await browser.close();}
})().catch(e=>{receipt.status='FAIL';receipt.error=String(e.stack||e);fs.writeFileSync(path.join(shots,'FBS_SPREAD_TOTALS_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n');console.error(e);process.exitCode=1;});
