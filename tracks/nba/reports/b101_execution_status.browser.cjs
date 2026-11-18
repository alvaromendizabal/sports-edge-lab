'use strict';

// Render sanitized aggregates only. No owner executable, source request or fit.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const directory = __dirname;
const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(directory,'.browser-review'));
const source = fs.readFileSync(path.join(directory,'b101_execution_status.json'));
const evidence = JSON.parse(source.toString('utf8'));
const pageBytes = fs.readFileSync(path.join(directory,'b101_execution_status.html'));
const url = pathToFileURL(path.join(directory,'b101_execution_status.html')).href;
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
fs.mkdirSync(output,{recursive:true});

function expectedCSV(horizon) {
  const fields=['objective','horizon_minutes','model_family','validation_2024_25_n','validation_2024_25_value',
    'validation_2025_26_n','validation_2025_26_value','test_2026_27_n','test_2026_27_value','primary_50_50_validation','test_selected'];
  const rows=evidence.selected_research_roles.filter(r=>String(r.horizon_minutes)===horizon).map(r=>[
    r.role,r.horizon_minutes,r.model_family,r.annual['2024-25'].n,r.annual['2024-25'].value,
    r.annual['2025-26'].n,r.annual['2025-26'].value,r.annual['2026-27'].n,r.annual['2026-27'].value,
    r.primary_validation_score,false]);
  const quote=v=>'"'+String(v).replaceAll('"','""')+'"';
  return [fields,...rows].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
}

async function main() {
  const launch={headless:true};
  if(process.env.NBA_CHROMIUM_EXECUTABLE)launch.executablePath=process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser=await chromium.launch(launch),views=[];
  try {
    for(const width of [1440,390]) {
      const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});
      await context.setOffline(true);
      const page=await context.newPage(),errors=[],requests=[];
      page.on('pageerror',error=>errors.push(error.message));
      page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
      page.on('request',request=>{if(/^https?:/.test(request.url()))requests.push(request.url());});
      await page.goto(url);
      assert.match(await page.locator('h1').innerText(),/B100 completed its campaign\.\s+B101 extends the research\./);
      for(const [metric,value] of [['distribution-fits','320'],['point-variants','5,808'],['completed-games','210'],['cpu-passes','0']]) {
        assert.equal(await page.locator(`[data-metric="${metric}"]`).innerText(),value);
      }
      const body=await page.locator('body').innerText();
      for(const phrase of ['V13 program incomplete','zero new base-estimator fits','zero new calibration fits',
        '210 completed games and 990 upcoming games','1,219,680 completed-game prediction rows',
        '5,749,920 upcoming-game prediction rows','1,321','1,322','14 newly identified validation games',
        'expanded population not yet rescored','no qualified full-season champion','previously exposed',
        '3,925 validation head-game zero-mass losses','zero new fits','6.13 cores','20.03 seconds','33.28 seconds',
        '49.10%','zero qualified exact-line comparison cells','Polymarket US','Polymarket International',
        'Every B101 branch below is planned and unexecuted','main integration pending','website deployment pending']) {
        assert.ok(body.includes(phrase),`Missing qualified evidence: ${phrase}`);
      }
      assert.equal(await page.locator('.plan tbody tr').count(),7);
      assert.equal(await page.locator('.metrics tbody tr:visible').count(),14);
      assert.deepEqual(JSON.parse(await page.locator('#aggregate-evidence').textContent()),evidence);
      // A real native keyboard radio interaction changes visible rows.
      await page.getByRole('radio',{name:'T60',exact:true}).focus();
      await page.keyboard.press('Space');
      assert.equal(await page.locator('.metrics tbody tr:visible').count(),7);
      assert.equal(await page.locator('#metric-summary').innerText(),'7 selected research roles · T60');
      assert.deepEqual(await page.locator('.metrics tbody tr:visible').evaluateAll(rows=>[...new Set(rows.map(r=>r.dataset.horizon))]),['60']);
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#metric-summary').innerText(),'7 selected research roles · T120');
      assert.deepEqual(await page.locator('.metrics tbody tr:visible').evaluateAll(rows=>[...new Set(rows.map(r=>r.dataset.horizon))]),['120']);
      await page.locator('#download-metrics').focus();
      const [csv]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);
      assert.equal(csv.suggestedFilename(),'b101_selected_roles_120.csv');
      assert.equal(fs.readFileSync(await csv.path(),'utf8'),expectedCSV('120'));
      await page.locator('#download-status').focus();
      const [download]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);
      assert.equal(download.suggestedFilename(),'b101_execution_status.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),evidence);
      if(width===390) {
        const cells=await page.locator('.mobile-cards tbody tr:visible td').evaluateAll(nodes=>nodes.map(node=>({
          label:node.dataset.label,generated:getComputedStyle(node,'::before').content,
          left:node.getBoundingClientRect().left,right:node.getBoundingClientRect().right,
          width:node.getBoundingClientRect().width,scroll:node.scrollWidth,client:node.clientWidth})));
        assert.ok(cells.length>60);
        for(const cell of cells) {
          assert.ok(cell.label);assert.equal(cell.generated,JSON.stringify(cell.label));
          assert.ok(cell.left>=0&&cell.right<=390&&cell.width>250&&cell.scroll<=cell.client+1,
            `Mobile field unreadable without horizontal scrolling: ${cell.label}`);
        }
      }
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Overflow at ${width}px`);
      await page.getByRole('radio',{name:'Both horizons',exact:true}).check();
      assert.equal(await page.locator('.metrics tbody tr:visible').count(),14);
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:path.join(output,`nba-b101-status-${width}.png`),fullPage:true});
      assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
      views.push({width,offline:true,page_errors:0,remote_requests:0,page_overflow:false,
        keyboard_horizon_filter:true,exact_visible_csv_download:true,exact_evidence_download:true});
      await context.close();
    }
    const context=await browser.newContext({viewport:{width:390,height:1000},javaScriptEnabled:false});
    await context.setOffline(true);
    const page=await context.newPage();await page.goto(url);
    assert.equal(await page.locator('.metrics tbody tr:visible').count(),14);
    assert.equal(await page.locator('#horizon-controls').isVisible(),false);
    assert.equal(await page.getByRole('link',{name:'Open aggregate JSON'}).getAttribute('href'),'b101_execution_status.json');
    assert.ok(await page.locator('noscript').isVisible());
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    views.push({width:390,offline:true,javascript:false,all_roles_visible:true,json_link_available:true});
    await context.close();
  } finally {await browser.close();}
  const receipt={schema:'sel.nba.b101.public_browser_receipt.v1',status:'PASS',
    html_sha256:sha256(pageBytes),json_sha256:sha256(source),
    source_head:process.env.NBA_SOURCE_HEAD_SHA||null,views,owner_executions:0,new_owner_fits:0};
  fs.writeFileSync(path.join(output,'nba-b101-browser-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
