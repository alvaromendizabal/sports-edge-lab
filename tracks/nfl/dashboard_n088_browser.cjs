'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.join(__dirname,'dashboard_n088');
(async()=>{
 const server=http.createServer((req,res)=>{const route=new URL(req.url,'http://local').pathname;const filename=route==='/'?'index.html':route.replace(/^\//,'');if(!['index.html','historical.json','publication.json'].includes(filename)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',filename.endsWith('.json')?'application/json':'text/html');res.end(fs.readFileSync(path.join(root,filename)));});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base=process.env.NFL_N088_ONLINE_URL||'http://127.0.0.1:'+server.address().port+'/';
 const browser=await chromium.launch({headless:true,executablePath:process.env.NFL_BROWSER_EXECUTABLE||undefined});
 const output=process.env.NFL_N088_EVIDENCE||process.cwd(),errors=[],timings=[],loads=[];let checks=0;
 fs.mkdirSync(output,{recursive:true});
 try{
  const page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});const start=performance.now();const response=await page.goto(base,{waitUntil:'networkidle'});assert.equal(response.status(),200);await page.waitForFunction(()=>window.nflV10?.release==='N088');loads.push(performance.now()-start);checks++;
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await page.locator('#games tr').count(),24);assert.equal(await page.evaluate(()=>window.nflV10.data.games.length),272);checks+=3;
   for(const [status,count]of [['completed',137],['upcoming',111],['tbd',24],['',272]]){const now=performance.now();await page.selectOption('#status',status);assert.equal(await page.evaluate(()=>window.nflV10.visibleGameIds.length),count);timings.push(performance.now()-now);checks++;}
   await page.fill('#search','2026_10_WAS_NYG');assert.equal(await page.locator('#games tr').count(),1);assert.match(await page.locator('#games').innerText(),/WAS 24 \/ NYG 21/);await page.click('#games button');assert.equal(await page.locator('#detail').isVisible(),true);assert.match(await page.locator('#detail-body').innerText(),/LATER_FITTED_RECONSTRUCTION/);await page.keyboard.press('Escape');assert.equal(await page.locator('#detail').isVisible(),false);await page.fill('#search','');checks+=5;
   await page.selectOption('#timing','current_forecasts');assert.equal(await page.evaluate(()=>window.nflV10.visibleGameIds.length),111);await page.selectOption('#timing','');await page.click('#next');assert.match(await page.locator('#page-label').innerText(),/Page 2/);await page.click('#prev');checks+=2;
   for(const provider of ['DraftKings','Kalshi','Polymarket','Circa']){const now=performance.now();await page.selectOption('#provider',provider);assert.match(await page.locator('#provider-status').innerText(),new RegExp(provider+': 0 new qualified'));timings.push(performance.now()-now);checks++;}
   await page.click('#load-history');await page.waitForFunction(()=>!document.getElementById('history-controls').hidden);assert.equal(await page.locator('#history tr').count(),30);assert.match(await page.locator('#history-count').innerText(),/1530 matching/);await page.selectOption('#history-season','2024');assert.ok((await page.locator('#history tr').first().innerText()).includes('2024'));await page.selectOption('#history-season','');await page.click('#history-next');assert.match(await page.locator('#history-count').innerText(),/page 2/);checks+=4;
   await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(output,'nfl-n088-'+(process.env.NFL_N088_ONLINE_URL?'online':'local')+'-'+width+'.png')});
  }
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(base);assert.equal(await nojs.locator('noscript tbody tr').count(),272);checks++;await nojs.close();
  if(!process.env.NFL_N088_ONLINE_URL){const offline=await browser.newPage();await offline.route('**/*',r=>{if(r.request().url().startsWith('file:'))return r.continue();return r.abort()});await offline.goto('file://'+path.join(root,'index.html'));assert.equal(await offline.locator('#games tr').count(),24);await offline.fill('#search','SEA');assert.ok(await offline.locator('#games tr').count());await offline.close();checks+=2;}
  assert.deepEqual(errors,[]);timings.sort((a,b)=>a-b);const result={status:'PASS',release:'N088',url:base,online:!!process.env.NFL_N088_ONLINE_URL,checks,viewports:[1440,390],games:272,initial_game_DOM_rows:24,script_free_game_rows:272,load_wall_ms:loads,interaction_p95_ms:timings[Math.ceil(timings.length*.95)-1],console_errors:errors,commit:process.env.GITHUB_SHA||null,verified_at_utc:new Date().toISOString()};fs.writeFileSync(path.join(output,'nfl-n088-browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
