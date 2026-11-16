'use strict';
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const {readFileSync,mkdirSync,writeFileSync}=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {createHash}=require('node:crypto');
(async()=>{
 const fs=path.join(__dirname,'n121_current','index.html'),html=readFileSync(fs,'utf8');
 const D=JSON.parse(html.match(/<script id="n121" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 const counts=Object.fromEntries([2024,2025,2026].map(y=>[y,D.calendar.filter(x=>x.season===y&&x.status==='PLAYED').length]));
 assert.deepEqual(counts,{2024:285,2025:285,2026:145});assert.equal(D.calendar.length,842);assert.equal(new Set(D.calendar.map(r=>r.game_id)).size,842);
 assert.equal(D.recipes.length,48);assert.equal(D.venues.fixtures.length,842);assert(D.forecasts.length>=2526);assert.equal(D.contest.cards.length,3);assert.equal(D.recommendations.filter(x=>x.winner==='n121_opponent_ridge_recent').length,3);for(const y of [2024,2025,2026])assert.equal(new Set(D.scores.filter(x=>Number(x.season)===y&&x.eligible_full_scope&&x.scored_n===counts[y]).map(x=>x.recipe)).size>=5,true);const futures=D.venues.fixture_coverage.filter(x=>x.season===2026&&x.status==='UPCOMING_TIMED');for(const [v,n] of [['DraftKings',94],['Polymarket',29],['Kalshi',2]])assert.equal(futures.find(x=>x.provider===v).exact,n);for(const v of D.contest.cards){assert.equal(v.picks.length,5);assert.equal(new Set(v.picks.map(p=>p.game_id)).size,5);assert(v.picks.every(p=>Math.abs(p.p_cover+.5*p.p_push-p.expected_points)<1e-6));}
 assert.equal(D.archive.rows.length,63);assert.equal(D.full_export.length,994);assert.equal(new Set(D.scores.filter(x=>x.season==='2026'&&x.scored_n===145&&x.eligible_full_scope).map(x=>x.recipe)).size,18);assert.equal(D.venues.public_panels.length,411);assert.equal(Object.keys(D.forward_market_cases).length,99);assert.equal(D.archive.rows.find(x=>x.id==='N025/margin/preserved_count_blend'&&x.season===2024).games,285);assert.equal(Object.values(D.market_cases).flat().length,7169);assert.equal(new Set(D.venues.public_panels.filter(x=>x.season===2026).map(x=>x.provider)).size>=3,true);assert.equal(D.venues.public_panels.filter(x=>x.season===2026).length,210);assert.equal(new Set(D.venues.public_panels.filter(x=>x.season===2026).map(x=>x.family)).size,3);assert.equal(D.openings.length,720);assert.equal(D.openings.filter(x=>D.calendar.some(g=>g.game_id===x.game_id&&g.status==='PLAYED')).length,715);const known=D.scores.find(x=>x.target==='margin'&&x.metric==='mae'&&x.recipe==='n116_opening_rating_margin_pool'&&x.season==='2026');assert.equal(known.scored_n,145);assert(known.score>9.65&&known.score<9.67);const signed=D.scores.find(x=>x.recipe==='n113_team_strength_margin'&&x.season==='2024'&&x.metric==='brier_3way');assert(signed.score>.447&&signed.score<.448);const restricted=/"(?:bid|ask|bid_size|ask_size|market_probability|contract_id|event_id|rule_sha256|bucket|private_path|source_blob|api_key)"\s*:/i;
 assert(!restricted.test(html));assert(!/s3:\/\/|[0-9]{12}\.dkr\.ecr|\/home\/sagemaker-user|private-handoff|x-amz-credential/i.test(html));
 const update=JSON.parse(html.match(/<script id="n121-followup" type="application\/json">([\s\S]*?)<\/script>/)[1]).current;
 assert.equal(update.rows.length,48*12);assert.equal(update.n,145+update.finals.length);
 for(const [name,count] of Object.entries({win:15,margin:14,total:11,ats:0}))assert.equal(update.complete[name],count);
 const facts={page_sha256:createHash('sha256').update(html).digest('hex'),population:counts,recipes:D.recipes.length,game_forecasts:D.forecasts.length};
 mkdirSync('artifacts',{recursive:true});const browser=await chromium.launch({headless:true});
 try{
 for(const [device,viewport] of [['desktop',{width:1440,height:980}],['mobile',{width:390,height:844}]]){
  const page=await browser.newPage({viewport,deviceScaleFactor:1});let errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(fs).href);await page.waitForSelector('#table121 tbody tr');
  assert.equal(await page.locator('#table121 tbody tr').count(),48);
  assert.match(await page.locator('#decision121').innerText(),/opponent ridge recent/i);
  await page.selectOption('#target121','win');await page.selectOption('#coverage121','complete');
  assert.equal(await page.locator('#table121 tbody tr').count(),4);assert.match(await page.locator('#table121').innerText(),/145\/145/);
  await page.selectOption('#target121','ats');assert.match(await page.locator('#decision121').innerText(),/named.market|spread coverage/i);
  await page.selectOption('#coverage121','all');await page.selectOption('#target121','margin');
  await page.screenshot({path:'artifacts/N121-'+device+'-models.png'});
  await page.click('[data-view=games]');await page.waitForSelector('#gameList121 button');
  assert.equal(await page.locator('#gameList121 button').count(),272);
  await page.selectOption('#year121g','2025');assert.equal(await page.locator('#gameList121 button').count(),285);
  assert.match(await page.locator('#gameDetail121').innerText(),/DraftKings/);assert.match(await page.locator('#gameDetail121').innerText(),/Archived opening comparison/);
  await page.click('[data-view=markets]');await page.waitForSelector('#cover121 table');assert.match(await page.locator('#cover121').innerText(),/Kalshi/);
  await page.screenshot({path:'artifacts/N121-'+device+'-markets.png'});await page.click('[data-view=future]');await page.getByRole('heading',{name:'Upcoming forecasts',exact:true}).waitFor();assert.equal(await page.locator('tbody tr').count(),124);
  await page.click('[data-view=circa]');await page.waitForSelector('#card121 table');assert.equal(await page.locator('#card121 table').first().locator('tbody tr').count(),5);assert.equal(await page.locator('#card121 details tbody tr').count(),28);assert.match(await page.locator('main').innerText(),/after deadline/i);
  await page.click('[data-view=study]');await page.getByRole('heading',{name:'Validation and test design',exact:true}).waitFor();assert.match(await page.locator('main').innerText(),/tool host/i);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  await page.click('[data-view=models]');await page.waitForSelector('#currentList tbody tr');
  assert.equal(await page.locator('#currentList tbody tr').count(),48);
  await page.selectOption('#currTarget','win');await page.fill('#currFilter','recent');assert.match(await page.locator('#currentList').innerText(),/140-day/);
  await page.getByRole('heading',{name:'N025 paper champions and the N121 validation leader',exact:true}).waitFor();
  await page.getByRole('heading',{name:'Weights and calibration fixed before each season',exact:true}).waitFor();
  await page.goto(pathToFileURL(fs).href+'#games/'+update.finals[0].game_id);await page.waitForSelector('#gameDetail121');assert.match(await page.locator('#gameDetail121').innerText(),/Graded pregame market comparisons/);
  await page.click('[data-view=markets]');await page.getByRole('heading',{name:'Identical three-venue settlement',exact:true}).waitFor();
  const download=await page.evaluate(async()=>{const bytes=Uint8Array.from(atob('YWJj'),c=>c.charCodeAt(0));const d=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),a=document.createElement('a');a.href=URL.createObjectURL(new Blob([bytes]));a.download='fixture.bin';const ok=a.download==='fixture.bin'&&a.href.startsWith('blob:');URL.revokeObjectURL(a.href);return [Array.from(d,x=>x.toString(16).padStart(2,'0')).join(''),ok];});assert.deepEqual(download,['ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',true]);assert.deepEqual(errors,[]);await page.close();facts[device]='PASS';
 }
 }finally{await browser.close();}
 writeFileSync('artifacts/N121-public-qa.json',JSON.stringify(facts,null,2)+'\n');console.log(facts);
})().catch(e=>{console.error(e);process.exit(1);});
