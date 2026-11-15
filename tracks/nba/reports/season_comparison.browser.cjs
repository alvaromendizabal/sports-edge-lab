'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const {pathToFileURL} = require('node:url');

module.exports = async function checkSeasonComparison(browser, output) {
  const source = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname,'season_comparison.json.gz'))));
  const uri = pathToFileURL(path.join(__dirname,'season_comparison.html')).href;
  const result = {schema:'sports-edge-lab.nba.season-comparison-browser.v1',status:'PASS',observed_games:source.games.length,viewports:[]};
  for (const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]) {
    const context = await browser.newContext({viewport:{width,height},acceptDownloads:true});
    const page = await context.newPage(), errors=[], external=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
    await page.route(/^https?:/,r=>{external.push(r.request().url());r.abort()});
    await page.goto(uri);await page.waitForSelector('html[data-nba-ready="true"]');
    assert.deepEqual(await page.evaluate(()=>window.NBA_COMPARISON_DATA),source);
    assert.equal(await page.locator('#game-rows tr').count(),Math.min(30,source.games.length));
    assert.equal(await page.locator('#provider-rows tr').count(),4);
    const visited = new Set();
    do {
      for(const id of await page.locator('#game-rows tr[data-game-id]').evaluateAll(rows=>rows.map(r=>r.dataset.gameId))) visited.add(id);
      if(await page.locator('#next').isDisabled())break;
      await page.locator('#next').click();
    } while(true);
    assert.deepEqual([...visited].sort(),source.games.map(g=>g.game_id).sort());
    await page.selectOption('#game-status','FINAL');
    assert.match(await page.locator('#game-count').textContent(),new RegExp('^'+source.games.filter(g=>g.status==='FINAL').length+' matching'));
    await page.selectOption('#game-status','UPCOMING');
    assert.match(await page.locator('#game-count').textContent(),new RegExp('^'+source.games.filter(g=>g.status!=='FINAL').length+' matching'));
    await page.selectOption('#game-status','ALL');
    await page.selectOption('#phase','regular');
    for(const target of ['winner','margin','total']){
      await page.selectOption('#target',target);await page.selectOption('#horizon','120');
      assert.match(await page.locator('#units').textContent(),target==='margin'?/home points minus away points/:target==='total'?/combined points/:/home team wins/);
      const rows=await page.locator('#game-rows tr[data-game-id]').evaluateAll(rs=>rs.map(r=>({id:r.dataset.gameId,text:r.textContent})));
      const objective=target==='winner'?'log_loss':'mae';
      for(const row of rows){
        const game=source.games.find(g=>g.game_id===row.id),forecast=game.forecasts[`regular_${target}_${objective}_t120`];
        if(forecast)assert.ok(row.text.includes(target==='winner'?(forecast.prediction*100).toFixed(2)+'%':forecast.prediction.toFixed(2)));
        else assert.ok(row.text.includes('No current-role original issue'));
        const missing=Object.values(game.markets).filter(m=>!m.bound_observations&&m.status!=='PREGAME_WINNER_REFERENCE_RETAINED_PRICE_NOT_PUBLIC').length;
        assert.equal((row.text.match(/No bound record in audited snapshot/g)||[]).length,missing);
      }
    }
    await page.fill('#game-search','LAL');
    assert.ok((await page.locator('#game-rows tr').allTextContents()).every(t=>t.includes('LAL')));
    await page.fill('#game-search','impossible-team-fixture');
    assert.match(await page.locator('#game-rows').textContent(),/No observed games/);
    await page.fill('#game-search','');await page.selectOption('#phase','ALL');await page.selectOption('#target','winner');await page.selectOption('#horizon','60');
    await page.selectOption('#market-availability','RETAINED');
    assert.match(await page.locator('#game-count').textContent(),/^68 matching/);
    assert.match(await page.locator('#game-rows').textContent(),/Winner reference retained/);
    assert.match(await page.locator('#game-rows').textContent(),/Provider quote time unknown/);
    await page.selectOption('#target','margin');
    assert.match(await page.locator('#game-rows').textContent(),/Winner only; no exact margin contract/);
    await page.selectOption('#target','winner');await page.selectOption('#market-availability','ALL');
    for(const provider of source.providers){
      await page.selectOption('#comparison-provider',provider);
      const expected=source.matched_comparisons.filter(r=>r.season==='2026-27'&&r.provider===provider&&r.model_on_same_reference_games?.games>0);
      assert.match(await page.locator('#comparison-count').textContent(),new RegExp('^'+expected.length+' saved'));
      if(!expected.length)assert.match(await page.locator('#comparison-rows').textContent(),/No saved scored comparison/);
    }
    await page.selectOption('#comparison-provider','ALL');
    for(const target of ['winner','margin','total']){
      await page.selectOption('#model-target',target);
      const expected=Object.values(source.champions).filter(r=>r.target===target&&r.phase==='regular'&&r.horizon_minutes===60);
      assert.equal(await page.locator('#model-rows tr').count(),expected.length);
    }
    await page.selectOption('#model-target','winner');
    assert.equal(await page.locator('#current-score-rows tr').count(),3);
    assert.match(await page.locator('#current-score-scope').textContent(),/128 identical/);
    assert.equal(await page.locator('#frontier-score-rows tr').count(),18);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/B087-R1/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/48 new frontier fits, 72 reused fits, 0 pending tasks and 0 failed tasks/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/120 of 120 registered tasks completed/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/not the required three-minute full-capacity pass/);
    assert.match(await page.locator('#latest-research-checkpoint').textContent(),/B087-R1.*120\/120 frontier tasks complete \(48 new, 72 reused\)/);
    assert.equal(await page.locator('#earlier-frontier-rows tr').count(),36);
    const earlierRows=await page.locator('#earlier-frontier-rows tr').allTextContents();
    source.current_science_scores.new_frontier_earlier_season_ablations.forEach((row,i)=>{
      assert.ok(earlierRows[i].includes(row.phase));
      assert.ok(earlierRows[i].includes(row.baseline_metrics.games+' games'));
      for(const value of [row.baseline_metrics[row.primary_metric],row.candidate_metrics[row.primary_metric],row.paired_cluster_interval.lower,row.paired_cluster_interval.upper])assert.ok(earlierRows[i].includes(value.toFixed(6)));
    });
    assert.equal(await page.locator('#weighted-score-rows tr').count(),11);
    const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-json').click()]);
    assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),source);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    assert.equal((await page.locator('body').innerText()).toLowerCase().includes('ci'+'rca'),false);
    await page.screenshot({path:path.join(output,`nba-season-comparison-${name}.png`),fullPage:true});
    await page.reload();await page.waitForSelector('html[data-nba-ready="true"]');
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    result.viewports.push({name,width,height,games_verified:visited.size,offline_reopen:true,download_roundtrip:true,page_errors:0,external_requests:0});
    await context.close();
  }
  fs.writeFileSync(path.join(output,'nba-season-comparison-browser.json'),JSON.stringify(result,null,2)+'\n');
  return result;
};
