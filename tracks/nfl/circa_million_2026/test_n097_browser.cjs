'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const base = path.join(__dirname, 'n097_current');
const raw = fs.readFileSync(path.join(base,'public_science.json'));
const pageBody = fs.readFileSync(path.join(base,'index.html'));
const src = JSON.parse(fs.readFileSync(path.join(base,'research_review.json')));
const owner = JSON.parse(raw);
let checks=0, server;
function check(ok,message){assert.ok(ok,message);checks++;}
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
async function main() {
  let url=process.env.NFL_N097_ONLINE_URL;
  if (!url) {
    server=http.createServer((req,res)=>{if(req.url==='/favicon.ico'){res.writeHead(204);return res.end();}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(pageBody);});
    await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';
  }
  const browser=await chromium.launch({headless:true}); const errors=[],viewports=[];
  for (const width of [1440,390]) {
    const p=await browser.newPage({viewport:{width,height:960}});
    p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    await p.goto(url,{waitUntil:'networkidle'});await p.waitForFunction(()=>Boolean(window.nflN097Review));
    const d=await p.evaluate(()=>window.nflN097Review);
    check(await p.title()==='Circa Million Picks & Performance Dashboard','title');
    check(JSON.stringify(d)===JSON.stringify(src),'exact embedded research review');
    const original=await p.evaluate(()=>window.nflN094.data);
    check(JSON.stringify(original)===JSON.stringify(owner),'byte-pinned complete owner data');
    check(original.games.length===272&&original.records.length===444&&original.execution.current_models===26,'complete owner schedule and forecast streams');
    check(original.time_ordered_studies.length===27&&original.total_study.current_total_distributions===333&&original.total_study.exact_total_contract_model_pairs===42,'owner margin and total calibration');
    check(original.source_science_release==='N096'&&original.execution.qualified_current_rows_after_display_clock_gate===2886,'correct N096 owner vintage');
    check(original.execution.new_fits===1&&original.execution.reused_fits===217&&original.execution.failed_fits===0,'owner source results');
    check(await p.locator('#game-rows tr').count()===135,'upcoming full schedule');
    await p.selectOption('#game-scope','all');check(await p.locator('#game-rows tr').count()===272,'full-year census');
    await p.selectOption('#game-scope','upcoming');
    check(await p.locator('#common-models tbody tr').count()===12,'retained same-game champion leaderboard');
    check(await p.locator('#model-ats tbody tr').count()===3,'2026 ATS leaders');
    await p.selectOption('#study-policy','all');check(await p.locator('#model-ats tbody tr').count()===9,'alternate calibration policies');
    await p.selectOption('#study-policy','primary');
    check(await p.locator('#event-score-table tbody tr').count()===57,'scored margin events');
    check(await p.locator('#official-sides tbody tr').count()===78,'all model-specific board rows');
    check(new Set(await p.locator('#official-sides tbody tr td:first-child').allTextContents()).size===3,'distinct board model labels');
    check(d.source_owner_release==='N096'&&d.release==='N097','release provenance');
    check(d.owner_execution.new_base_weight_fits===1&&d.owner_execution.reused_fit_jobs===217&&d.owner_execution.failed_fit_jobs===0,'owner fit jobs');
    check(d.owner_execution.distinct_reused_weight_versions===199&&d.owner_execution.new_total_calibration_fits===0&&d.owner_execution.total_calibration_estimates_reused===9,'weights and separate calibrators');
    check(d.owner_execution.point_forecast_rows===2886&&d.owner_execution.dated_upcoming_games===111,'forecast coverage');
    check(d.cards.length===3&&d.owner_execution.production_accepted_total_calibrators===0,'issued cards and production acceptance');
    for(const c of d.cards){
      const i=original.current_model_card_review.cards.findIndex(x=>x.family===c.family.toLowerCase());
      check(i>=0,'owner family present');await p.selectOption('#model-card-select',String(i));
      check(await p.locator('#model-card-picked tbody tr').count()===5,'five rendered selections');
      check(await p.locator('#model-card-others tbody tr').count()===26,'all alternatives rendered');
      check(new Set(c.selected.map(r=>r.game_id)).size===5,'five distinct games');
      check((await p.locator('#model-card-status').innerText()).includes(c.expected_points.toFixed(4)),'visible expected score');
      check(c.alternatives.every(r=>Math.abs(r.expected_points-r.p_cover-.5*r.p_push)<=.00011),'verified rounding and expected points');
      check(c.alternatives.every(r=>r.team_ats&&r.chosen_side_ats&&r.rationale&&r.uncertainty.length===2),'histories and uncertainty');
      check(new Date(c.probability_issue_utc)<=new Date(c.selection_utc)&&new Date(c.selection_utc)<new Date(d.official_board.official_deadline_utc),'chronology');
      check(c.actual_entry===false&&c.production_accepted===false&&c.automatic_promotion===false,'research qualification');
    }
    check(await p.locator('#n096-cutoff tbody tr').count()===3,'all cutoff comparisons');
    check(d.stability.fully_overlapping_side_intervals===26&&d.stability.preferred_same_side_all_models===8,'source-matched sensitivity results');
    check(await p.locator('#n096-pairs tbody tr').count()===3,'all card pairs');
    check(await p.locator('#n096-history tbody tr').count()===3&&d.common_week_cards.every(c=>c.possible===25&&c.points<c.expected),'same-week performance');
    check(await p.locator('#original-scorecard tbody tr').count()===3,'three original comparable objectives');
    check(d.reissue_comparison.matched_selected_rows===444&&d.reissue_comparison.changed_selected_rows.length===6,'earlier vs current point issues');
    check(d.chronological_total_blend.rows===1371&&d.chronological_total_blend.estimates_reused===116&&d.chronological_total_blend.new_estimates===0,'total blend checkpoint and rows');
    check(await p.locator('#total-blend tbody tr').count()===9,'primary and alternative weights');
    check(d.new_research.total_tail.new_statistical_estimates===9&&d.new_research.total_tail.old_zero_mass===39&&d.new_research.total_tail.new_zero_mass===0,'tail coverage');
    check(await p.locator('#n096-totals tbody tr').count()===9,'paired model and exact total contracts');
    check(d.new_research.rolling_total.policies===47&&d.new_research.rolling_total.controls===47,'rolling policies and falsification controls');
    check(d.new_research.fixed_margin_pool.eligible_model_game_rows===1593&&d.new_research.fixed_margin_pool.settled_contract_model_pairs===666,'frozen margin comparison');
    check(await p.locator('#n096-margin-pool details').count()===4,'separate three pooled research cards');
    check(d.new_research.fixed_margin_pool.cards.every(a=>a.alternatives.length===26&&new Set(a.selected.map(b=>b.game_id)).size===5&&new Date(a.as_of)<new Date(a.deadline)),'current research card integrity');
    check(await p.locator('#n097-card-risk tbody tr').count()===6,'six audited research cards');
    check(d.card_risk.rows.every(c=>c.minimum<=c.independence+1e-9&&c.independence<=c.maximum+1e-9),'valid point probabilities and dependence bounds');
    check(d.card_risk.historical_weeks===530&&d.card_risk.new_fits===0,'historical card comparisons');
    check(d.owner_strict_update.family==='extratrees'&&d.owner_strict_update.training_games===1815&&d.owner_strict_update.eligible_recipes===8,'genuine new strict total fit');
    check(d.owner_execution.completed_fit_jobs===218&&d.owner_execution.worker_core_equivalents>1&&d.owner_execution.worker_core_equivalents<2,'actual useful work');
    check((await p.locator('#return-review').innerText()).includes('2,886'),'current owner attribution');
    check(d.n097_research.key_margin.new_statistical_fits===18&&d.n097_research.key_margin.historical_model_games===1593,'new registered distribution fitting and common data');
    check(d.n097_research.key_margin.common_year_scores.every(x=>x.n===75),'same annual cohort');
    for (const card of d.n097_research.key_margin.current_cards) {
      check(card.alternatives.length===26&&new Set(card.selected.map(s=>s.game_id)).size===5,'five selections and all alternatives');
      check(card.alternatives.every(x=>Math.abs(x.expected_points-x.p_cover-0.5*x.p_push)<1e-8),'exact push-aware ranking');
      check(!card.entry&&Date.parse(card.as_of)<Date.parse(card.deadline),'predeadline research');
    }
    check(await p.locator('.n097-challenger-card tbody tr').count()===78,'rendered all new alternatives');
    await p.locator('.n097-challenger-card summary').first().click();
    check(await p.locator('.n097-challenger-card').first().getAttribute('open')!==null,'new comparison accessible');
    check(d.n097_research.exchange_matched.distinct_settled_contracts===219&&await p.locator('#n097-exchange tbody tr').count()===6,'exact exchange comparisons');
    check(d.n097_research.personnel.parameters_fitted===225&&await p.locator('#n097-personnel tbody tr').count()===2,'reported personnel comparisons');
    check(d.n097_research.separate_total_exchange.distinct===73&&d.n097_research.separate_total_exchange.matched_pairs===219&&await p.locator('#n097-total-exchange tbody tr').count()===3,'separate historical totals quote and score comparison');
    check(Object.values(d.n097_research.separate_total_exchange.scores).every(row=>row.n===73&&row.week_cluster_95_market_minus_model[1]<0),'all three exchange total models with exact intervals');
    check(d.n097_research.legacy.new_statistical_estimates===264&&d.n097_research.legacy.graded_rows===183&&d.n097_research.legacy.original_games_graded===16&&await p.locator('#n097-legacy tbody tr').count()===3,'legacy chronology and controls');
    check(d.n097_research.native_legacy.changed_old_rows===0&&d.n097_research.native_legacy.additional_finals===17&&d.n097_research.native_legacy.new_fits===3&&d.n097_research.native_legacy.runtime_byte_identity===false,'original feature continuity and changed-system research qualification');
    check(await p.locator('#n097-native-legacy').isVisible(),'legacy native issue scope');
    check(!await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),'responsive layout');
    viewports.push({width,models:d.cards.length,eligible_sides_per_model:26});await p.close();
  }
  const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(url);check(await nojs.locator('noscript tbody tr').count()===272,'script-free full schedule');
  check(errors.length===0,'console and page errors');await browser.close(); if(server)server.close();
  console.log(JSON.stringify({status:'PASS',release:'N097',online:!!process.env.NFL_N097_ONLINE_URL,url,checks,viewports,errors,public_payload_sha256:digest(raw),source_html_sha256:digest(pageBody),verified_at_utc:new Date().toISOString()}));
}
main().catch(e=>{console.error(e);if(server)server.close();process.exit(1);});
