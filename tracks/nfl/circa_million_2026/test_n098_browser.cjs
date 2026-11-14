const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const dir=path.join(__dirname,'n098_current');
const file=path.join(dir,'index.html'), raw=fs.readFileSync(file);
const live = process.env.NFL_N098_ONLINE_URL;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const needle = Buffer.from([106,109,97,99]).toString();
const banned = [needle,needle[0]+'-'+needle.slice(1),'s3://','/home/','/workspace/','PRIVATE KEY-----','AKIA'];
for(const word of banned) assert.ok(!raw.toString().toLowerCase().includes(word.toLowerCase()));
(async()=>{
  const browser=await chromium.launch({headless:true});
  let checks=0;
  for(const width of [1440,390]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    const t=Date.now();
    const resp=await page.goto(live||pathToFileURL(file).href,{waitUntil:'domcontentloaded'});
    if(live){
      assert.equal(resp.status(),200);
      const served=await resp.body();
      const source=raw.toString(), returned=served.toString();
      const assets=[...source.matchAll(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/g)].map(match=>match[0]);
      assert.equal(assets.length,3);
      for(const authored of assets)assert.ok(returned.includes(authored),'Authored script, data, or style differs from source');
      const main=source.match(/<main>[\s\S]*?<\/main>/)[0];
      assert.ok(returned.includes(main),'Authored main layout or script-free fallback differs');
      console.log(JSON.stringify({source_sha256:sha(raw),response_sha256:sha(served),scripts_styles_and_evidence_data_exact:true,authored_main_and_fallback_exact:true}));
      checks+=6;
    }
    assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
    const d=await page.locator('#evidenceData').evaluate(n=>JSON.parse(n.textContent));
    assert.equal(d.release,'N098');assert.equal(d.games.length,272);
    assert.equal(new Set(d.games.map(g=>g.game)).size,d.games.length);
    assert.ok(d.kalshi.length>0&&d.totals.length>0&&d.margin.length>0);
    assert.equal(d.cards.length,5);assert.equal(d.cards.reduce((n,c)=>n+c.sides.length,0),130);assert.equal(d.games.reduce((n,g)=>n+(g.strict||[]).length,0),888);checks+=3;
    assert.ok(d.previous.new===0&&d.previous.reused===205);
    assert.equal(d.matched.current_executable_rows,0);checks+=7;
    assert.equal(d.historical_cards.length,84);
    await page.selectOption('#histFamily','frozen_2023_week_open_ridge');await page.selectOption('#histYear','2026');assert.equal(await page.locator('#histRows tbody tr').count(),9);
    assert.ok((await page.locator('#histScores').innerText()).includes('20.5 / 45'));
    await page.selectOption('#histFamily','week_open_ridge');assert.equal(await page.locator('#histRows tbody tr').count(),7);checks+=4;
    const timings=[];
    for(let i=0;i<d.cards.length+d.previous_cards.length;i++){
      await page.selectOption('#families',String(i));await page.selectOption('#sideView','all');
      const card=[...d.cards,...d.previous_cards][i];const rows=await page.locator('#cardRows tbody tr').count();
      assert.equal(rows,card.sides.length);
      const chosen=card.sides.filter(r=>r.selected);assert.equal(chosen.length,5);assert.equal(new Set(chosen.map(r=>r.game)).size,5);
      for(const r of card.sides){assert.ok(Math.abs(r.cover+r.push+r.loss-1)<4e-6);assert.ok(Math.abs((r.cover+0.5*r.push)-r.points)<2e-6)}
      await page.selectOption('#sideView','best');assert.equal(await page.locator('#cardRows tbody tr').count(),5);
      checks+=4+2*rows;
    }
    for(const id of ['season','models','exchange','evidence','card']){let before=Date.now();await page.locator('#b'+id).click();await page.locator('#'+id).waitFor({state:'visible'});timings.push(Date.now()-before);checks++}
    await page.locator('#bseason').click();await page.selectOption('#state','Final');assert.equal(await page.locator('#games tbody tr').count(),d.games.filter(r=>r.status==='Final').length);
    await page.fill('#team','DET');assert.ok((await page.locator('#games tbody tr').allTextContents()).every(row=>row.includes('DET')));
    await page.locator('#bmodels').click();await page.selectOption('#target','total');await page.selectOption('#year','2026');assert.ok(await page.locator('#performance tbody tr').count()>0);
    await page.locator('#bexchange').click();await page.selectOption('#settlement','total');assert.ok(await page.locator('#market tbody tr').count()>0);assert.equal(await page.locator('#estimate').isDisabled(),true);
    await page.selectOption('#settlement','win');await page.selectOption('#estimate','past_week_blend');assert.ok(await page.locator('#market tbody tr').count()>0);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);assert.deepEqual(errors,[]);checks+=8;
    console.log(JSON.stringify({url:live||'source',width,checks,load_and_test_ms:Date.now()-t,view_switch_p95_ms:timings.sort((a,b)=>a-b).at(-1),page_sha256:sha(raw)}));
    await page.close();
  }
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
