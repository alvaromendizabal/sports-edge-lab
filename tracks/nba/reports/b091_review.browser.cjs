'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'B091_CHAMPION_AUDIT_PUBLIC.json')));
const output=process.env.NBA_MONITOR_SCREENSHOTS||path.join(__dirname,'browser-output');
fs.mkdirSync(output,{recursive:true});
const display=(v,m)=>m==='accuracy'?(100*v).toFixed(4)+'%':v.toFixed(6);
const lanes=['QUALIFIED_FIXED_REPLAY','LATER_FITTED_RECONSTRUCTION','STRICT_POINT_IN_TIME','ORIGINAL_ISSUED'];
async function main(){
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE_PATH?{executablePath:process.env.BROWSER_EXECUTABLE_PATH}:{})});
  const summary={status:'PASS',schema:'sports-edge-lab.nba.b091-browser.v1',current_cells:data.current_descriptive_cell_count,viewports:[]};
  try{
    for(const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]){
      const context=await browser.newContext({viewport:{width,height}}),page=await context.newPage(),errors=[],external=[];
      page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
      await page.route(/^https?:/,r=>{external.push(r.request().url());r.abort()});
      const url=pathToFileURL(path.join(__dirname,'b091_review.html')).href;
      await page.goto(url);await page.waitForSelector('html[data-b091-ready="true"]');
      assert.equal(await page.locator('#current-cell-count').textContent(),String(data.current_descriptive_cell_count));
      assert.equal(await page.locator('#all-role-rows tr').count(),data.roles.reduce((n,r)=>n+r.leader_model_ids.length,0));
      assert.match(await page.locator('#source-policy').textContent(),/DraftKings, Kalshi and Polymarket are comparison-only/);
      assert.match(await page.locator('#snapshot-clock').textContent(),/Pacific.*current test has zero selection weight/);
      let cases=0;
      for(const role of data.roles)for(const lane of lanes){
        await page.evaluate(s=>{
          for(const [id,value] of [['phase',s.phase],['target',s.objective],['metric',s.metric],['horizon',s.horizon_minutes],['track',s.lane]]){
            const e=document.getElementById(id);e.value=String(value);e.dispatchEvent(new Event('change',{bubbles:true}));
          }
        },{...role,lane});
        const expected=data.models.filter(m=>m.phase===role.phase&&m.objective===role.objective&&m.horizon_minutes===role.horizon_minutes)
          .sort((a,b)=>(role.metric==='accuracy'?b.pooled_validation_metrics[role.metric]-a.pooled_validation_metrics[role.metric]:a.pooled_validation_metrics[role.metric]-b.pooled_validation_metrics[role.metric])||a.model_id.localeCompare(b.model_id));
        const rows=await page.locator('#leader-rows tr').allTextContents();assert.equal(rows.length,expected.length);
        expected.forEach((m,i)=>{assert.ok(rows[i].includes(m.label));assert.ok(rows[i].includes(display(m.pooled_validation_metrics[role.metric],role.metric)));assert.ok(rows[i].includes('Current test weight: 0'));});
        const current=data.current_descriptive_cells.filter(c=>role.phase==='regular'&&c.objective===role.objective&&c.horizon_minutes===role.horizon_minutes&&c.evidence_class===lane).sort((a,b)=>a.model_id.localeCompare(b.model_id));
        const shown=await page.locator('#current-rows tr').allTextContents();assert.equal(shown.length,Math.max(1,current.length));
        current.forEach((c,i)=>{assert.ok(shown[i].includes('197 / 197'));assert.ok(shown[i].includes(display(c.metrics[role.metric],role.metric)));assert.ok(shown[i].includes('Strict point-in-time score: unavailable'));});
        if(lane==='STRICT_POINT_IN_TIME'&&role.phase==='regular')assert.match(await page.locator('#current-scope').textContent(),/Zero complete current cells/);
        assert.doesNotMatch((await page.locator('#leader-rows').textContent())+(await page.locator('#current-rows').textContent()),/undefined|NaN/);
        cases++;
      }
      await page.selectOption('#phase','regular');await page.selectOption('#target','winner');await page.selectOption('#metric','brier');await page.selectOption('#horizon','60');await page.selectOption('#track','QUALIFIED_FIXED_REPLAY');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),true);
      await page.screenshot({path:path.join(output,`nba-b091-review-${name}.png`),fullPage:false});
      await context.close();
      const fresh=await browser.newContext({viewport:{width,height}}),reopened=await fresh.newPage();await reopened.goto(url);await reopened.waitForSelector('html[data-b091-ready="true"]');assert.equal(await reopened.locator('#phase').inputValue(),'regular');await fresh.close();
      assert.deepEqual(errors,[]);assert.deepEqual(external,[]);summary.viewports.push({name,cases,page_errors:0,external_requests:0});
    }
    fs.writeFileSync(path.join(output,'nba-b091-browser-review.json'),JSON.stringify(summary,null,2)+'\n');console.log(JSON.stringify(summary));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
