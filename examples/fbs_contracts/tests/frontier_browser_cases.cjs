'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
async function run({browser,root,screenshots}){
 const directory=path.join(root,'docs/fbs'),errors=[],requests=[];
 const server=http.createServer((req,res)=>{try{const relative=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\/+/,''),file=path.resolve(directory,relative||'frontier.html');if(!file.startsWith(directory+path.sep))throw Error('outside public directory');const types={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'};res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.statusCode=404;res.end('Not found');}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const origin=`http://127.0.0.1:${server.address().port}`,context=await browser.newContext({acceptDownloads:true});
 let states=0;
 try{const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(origin)&&!r.url().startsWith('blob:'))requests.push(r.url());});
  for(const width of [1440,390]){await page.setViewportSize({width,height:1000});await page.goto(origin+'/frontier.html');await page.waitForFunction(()=>document.getElementById('game-status').textContent.startsWith('888 games'));
   assert.equal(await page.locator('h1').count(),1);assert.equal(await page.locator('#game-rows tr').count(),25);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   for(const [value,count]of [['previous',56],['current',63],['all',888]]){await page.selectOption('#game-window',value);assert.match(await page.locator('#game-status').innerText(),new RegExp(`^${count} games`));states++;}
   await page.selectOption('#game-window','current');for(const provider of ['DraftKings','Kalshi','Polymarket US','Polymarket Global']){await page.selectOption('#game-provider',provider);assert.match(await page.locator('#game-status').innerText(),/^63 games/);states++;}
   await page.locator('#game-query').fill('unobserved-team-token');assert.match(await page.locator('#game-status').innerText(),/^0 games/);assert.equal(await page.locator('#game-rows tr').count(),0);await page.locator('#game-query').fill('');
   await page.locator('#game-rows details summary').first().click();assert.match(await page.locator('#game-rows details').first().innerText(),/NO BET.*\$0 stake/);
   const pending=page.waitForEvent('download');await page.locator('#game-download').click();const download=await pending,content=fs.readFileSync(await download.path(),'utf8');assert.ok(content.startsWith('"game_id"'));assert.equal(content.trimEnd().split('\r\n').length,64);
   await page.locator('#game-query').focus();assert.equal(await page.locator('#game-query').evaluate(el=>el===document.activeElement),true);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(screenshots,`frontier-${width}-top.png`)});await page.locator('#games').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(screenshots,`frontier-${width}-games.png`)});}
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);return {status:'PASS',viewports:[1440,390],filter_provider_states:states,csv_rows_current_week:63,script_errors:0,external_requests:0};
 }finally{await context.close();await new Promise(resolve=>server.close(resolve));}
}
module.exports={run};
