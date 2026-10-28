// Real Chromium smoke test. Install pinned Playwright in CI; no sports/network data.
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const failures=[],requests=[];
 const page=await browser.newPage();
 page.on('pageerror',e=>failures.push(e.message));
 page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))requests.push(r.url());});
 const file='file://'+path.resolve(__dirname,'../../../docs/dashboard/index.html');
 let checked=0;
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(file);
  await page.locator('#results table').waitFor();
  assert.equal(await page.locator('#results tbody tr').count(),5);
  assert.equal(await page.locator('#demo-output .lane').count(),3);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  assert.equal(overflow,false,'page must fit viewport '+width);
  await page.selectOption('#release','V129');await page.selectOption('#league','NFL');await page.selectOption('#season','2026');
  assert.match(await page.locator('#results').innerText(),/MONITORING ONLY/);
  assert.equal(await page.locator('#results .best').count(),0);
  assert.equal(await page.locator('#results tbody tr').count(),1);
  await page.selectOption('#release','V131');
  assert.match(await page.locator('#results').innerText(),/No saved panel/);
  await page.getByRole('button',{name:'Reference is stale',exact:true}).click();
  assert.match(await page.locator('#demo-output').innerText(),/BLOCKED/);
  assert.equal(await page.locator('#demo-output tbody tr').count(),0);
  await page.getByRole('button',{name:'Research rejects',exact:true}).click();
  assert.match(await page.locator('#demo-output').innerText(),/SERVED/);
  assert.equal(await page.locator('#demo-output tbody tr').count(),2);
  assert.equal(await page.locator('[data-scenario][aria-pressed="true"]').count(),1);
  await page.getByRole('button',{name:'2 · Resume failed research',exact:true}).click();
  assert.match(await page.locator('#recovery-output').innerText(),/REUSED/);
  assert.equal(await page.locator('#recovery-output tbody tr').count(),8);
  await page.getByRole('button',{name:'3 · Reenter unchanged',exact:true}).click();
  assert.equal(await page.locator('#recovery-output .score').first().innerText(),'0');
  await page.getByRole('button',{name:'1 · Sparse return',exact:true}).click();
  assert.match(await page.locator('#portable-output').innerText(),/BLOCKED/);
  assert.equal(await page.locator('#portable-output tbody tr').count(),4);
  await page.getByRole('button',{name:'2 · Complete export',exact:true}).click();
  assert.doesNotMatch(await page.locator('#portable-output').innerText(),/BLOCKED/);
  assert.match(await page.locator('.hero-note').innerText(),/V133 owner: FAILED/);
  await page.selectOption('#release','V132');await page.selectOption('#league','FBS');await page.selectOption('#season','2024');
  await page.locator('#metric').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#metric').inputValue(),'win_brier');
  const output=process.env.DASHBOARD_SCREENSHOTS;
  if(output){fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,`dashboard-${width}.png`),fullPage:true});}
  checked++;
 }
 assert.deepEqual(failures,[]);assert.deepEqual(requests,[]);
 console.log(JSON.stringify({status:'PASS',rendered_viewports:checked,widths:[1440,390],script_errors:failures.length,external_requests:requests.length,keyboard_control:true,real_UI_events:true}));
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
