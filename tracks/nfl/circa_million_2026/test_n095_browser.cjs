'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const base = path.join(__dirname, 'n095_current');
const raw = fs.readFileSync(path.join(base,'public_science.json'));
const pageBody = fs.readFileSync(path.join(base,'index.html'));
const src = JSON.parse(raw);
let checks=0, server;
function check(ok,message){assert.ok(ok,message);checks++;}
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
async function main() {
  let url=process.env.NFL_N095_ONLINE_URL;
  if (!url) {
    server=http.createServer((req,res)=>{if(req.url==='/favicon.ico'){res.writeHead(204);return res.end();}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(pageBody);});
    await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';
  }
  const browser=await chromium.launch({headless:true}); const errors=[],viewports=[];
  for (const width of [1440,390]) {
    const p=await browser.newPage({viewport:{width,height:960}});
    p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    await p.goto(url,{waitUntil:'networkidle'});await p.waitForFunction(()=>Boolean(window.nflN095Review));
    const d=await p.evaluate(()=>window.nflN095Review);
    check(await p.title()==='Circa Million Picks & Performance Dashboard','title');
    check(JSON.stringify(d)===JSON.stringify(src),'exact embedded public data');
    check(d.source_owner_release==='N094'&&d.release==='N095','release provenance');
    check(d.owner_execution.new_base_weight_fits===0&&d.owner_execution.reused_fit_jobs===217&&d.owner_execution.failed_fit_jobs===0,'owner fit jobs');
    check(d.owner_execution.distinct_reused_weight_versions===199&&d.owner_execution.new_total_calibration_fits===9,'weights and separate calibrators');
    check(d.owner_execution.point_forecast_rows===2775&&d.owner_execution.dated_upcoming_games===111,'forecast coverage');
    check(d.cards.length===3&&d.owner_execution.production_accepted_total_calibrators===0,'issued cards and production acceptance');
    for(const c of d.cards){
      await p.selectOption('#n095-model',c.family);
      check(await p.locator('#n095-picks tbody tr').count()===5,'five rendered selections');
      check(await p.locator('#n095-all tbody tr').count()===26,'all alternatives rendered');
      check(new Set(c.selected.map(r=>r.game_id)).size===5,'five distinct games');
      check((await p.locator('#n095-card-summary').innerText()).includes(c.expected_points.toFixed(4)),'visible expected score');
      check(c.alternatives.every(r=>Math.abs(r.expected_points-r.p_cover-.5*r.p_push)<=.00011),'verified rounding and expected points');
      check(c.alternatives.every(r=>r.team_ats&&r.chosen_side_ats&&r.rationale&&r.uncertainty.length===2),'histories and uncertainty');
      check(new Date(c.probability_issue_utc)<=new Date(c.selection_utc)&&new Date(c.selection_utc)<new Date(d.official_board.official_deadline_utc),'chronology');
      check(c.actual_entry===false&&c.production_accepted===false&&c.automatic_promotion===false,'research qualification');
    }
    check(await p.locator('#n095-cutoff tbody tr').count()===3,'all cutoff comparisons');
    check(d.stability.fully_overlapping_side_intervals===26&&d.stability.preferred_same_side_all_models===8,'source-matched sensitivity results');
    check(await p.locator('#n095-pairs tbody tr').count()===3,'all card pairs');
    check(await p.locator('#n095-history tbody tr').count()===3&&d.common_week_cards.every(c=>c.possible===25&&c.points<c.expected),'same-week performance');
    check(await p.locator('#original-forecast tbody tr').count()===3,'three original comparable objectives');
    check(!await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),'responsive layout');
    viewports.push({width,models:d.cards.length,eligible_sides_per_model:26});await p.close();
  }
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(url);check(await nojs.locator('noscript tbody tr').count()===3,'script-free cards');
  check(errors.length===0,'console and page errors');await browser.close(); if(server)server.close();
  console.log(JSON.stringify({status:'PASS',release:'N095',online:!!process.env.NFL_N095_ONLINE_URL,url,checks,viewports,errors,public_payload_sha256:digest(raw),source_html_sha256:digest(pageBody),verified_at_utc:new Date().toISOString()}));
}
main().catch(e=>{console.error(e);if(server)server.close();process.exit(1);});