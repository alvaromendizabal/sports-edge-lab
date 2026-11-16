'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const {pathToFileURL} = require('node:url');
async function changeControls(page,pairs){
  await page.evaluate(values=>{for(const [id,value] of values){const element=document.getElementById(id);element.value=String(value);if(element.value!==String(value))throw new Error('Unavailable control value '+id);element.dispatchEvent(new Event('change',{bubbles:true}));}},pairs);
}

module.exports = async function checkSeasonComparison(browser, output) {
  require('node:child_process').execFileSync('python',[path.join(__dirname,'build_season_comparison.py'),'--check'],{stdio:'pipe'});
  for(const name of ['test_season_comparison.py','test_equal_population_public.py','test_draftkings_public.py','test_model_market_public.py'])require('node:child_process').execFileSync('python',['-m','unittest','discover','-s',__dirname,'-p',name],{stdio:'pipe'});
  const downloadSource = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname,'season_comparison.json.gz'))));
  const html=fs.readFileSync(path.join(__dirname,'season_comparison.html'),'utf8');
  const payload=html.match(/<script id="nba-comparison-payload" type="application\/octet-stream">([^<]+)<\/script>/);
  assert.ok(payload);
  const source=JSON.parse(zlib.gunzipSync(Buffer.from(payload[1],'base64')));
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
    const equal=source.equal_population_evaluation;
    assert.ok(equal);
    assert.deepEqual(equal.protocol.validation_seasons,['2024-25','2025-26']);
    assert.equal(equal.protocol.test_season,'2026-27');
    assert.equal(equal.protocol.test_exposure_status,'PREVIOUSLY_EXPOSED');
    assert.match(await page.locator('#equal-population-protocol').textContent(),/Selection population: 2024–25 and 2025–26.*prior analytical exposure/);
    for(const group of equal.groups){
      const metric=group.target==='winner'?'log_loss':'mae';
      await changeControls(page,[['equal-phase',group.phase],['equal-target',group.target],['equal-horizon',group.horizon_minutes],['equal-track',group.evidence_track],['equal-season',group.season],['equal-metric',metric]]);
      const observed=await page.evaluate(()=>({scope:document.getElementById('equal-population-scope').textContent,rows:[...document.querySelectorAll('#equal-population-rows tr')].map(r=>r.textContent),result:document.getElementById('equal-population-result').textContent,section:document.getElementById('equal-population').textContent}));
      assert.match(observed.scope,new RegExp('Required population: '+group.required_games+' games; '+group.required_candidate_count+' required candidates'));
      const display=observed.rows;assert.equal(display.length,group.models.length);
      group.models.forEach((m,i)=>{
        assert.ok(display[i].includes(m.label));
        assert.ok(display[i].includes(m.qualified_games+' / '+group.required_games));
        if(!m.full_population_complete)assert.ok(display[i].includes('Unavailable'));
        else if(typeof m.full_population_metrics?.[metric]==='number')assert.ok(display[i].includes(m.full_population_metrics[metric].toFixed(6)));
      });
      if(!group.all_required_candidates_complete)assert.match(observed.result,/No all-candidate full-population ranking/);
      assert.doesNotMatch(observed.section,/undefined|NaN/);
    }
    await page.selectOption('#equal-phase','regular');await page.selectOption('#equal-target','winner');await page.selectOption('#equal-horizon','120');await page.selectOption('#equal-season','2026-27');
    if(equal.groups.some(g=>g.evidence_track==='QUALIFIED_FIXED_REPLAY'&&g.target==='winner'&&g.horizon_minutes===120&&g.phase==='regular'))await page.selectOption('#equal-track','QUALIFIED_FIXED_REPLAY');
    await page.screenshot({path:path.join(output,`nba-full-population-${name}.png`),fullPage:false});

    const paired=source.model_market_comparison;
    if(paired){
      for(const group of paired.groups){
        await changeControls(page,[['paired-target',group.target],['paired-horizon',group.horizon_minutes],['paired-track',group.evidence_track]]);
        assert.match(await page.locator('#paired-market-scope').textContent(),new RegExp(group.required_games+' required 2026–27'));
        assert.equal(await page.locator('#paired-full-rows tr').count(),group.models.length);
        const cells=await page.locator('#paired-full-rows tr').allTextContents();
        group.models.forEach((m,i)=>{assert.ok(cells[i].includes(m.model_games+' / '+group.required_games));if(!m.full_population_complete)assert.ok(cells[i].includes('Unavailable'));});
        assert.match(await page.locator('#paired-diagnostic-scope').textContent(),new RegExp('Diagnostic only: '+group.common_diagnostic.games+' identical available games'));
        assert.doesNotMatch(await page.locator('#named-market-scoreboard').textContent(),/undefined|NaN/);
      }
      await page.selectOption('#paired-target','winner');await page.selectOption('#paired-horizon','120');await page.selectOption('#paired-track','QUALIFIED_FIXED_REPLAY');
    }
    if(source.draftkings_analytical){
      assert.equal(await page.locator('#draftkings-coverage-rows tr').count(),6);
      for(const group of source.draftkings_analytical.coverage)assert.equal(group.required_games,192);
      await page.selectOption('#market-availability','QUALIFIED_DRAFTKINGS');
      assert.match(await page.locator('#game-count').textContent(),/^185 matching/);
      await page.selectOption('#game-status','UPCOMING');await page.selectOption('#horizon','120');
      for(const target of ['winner','margin','total']){
        await page.selectOption('#target',target);assert.match(await page.locator('#game-rows').textContent(),/Current capture · reference only/);
        assert.match(await page.locator('#game-rows').textContent(),/official start retained/);
      }
      await page.selectOption('#game-status','ALL');await page.selectOption('#market-availability','ALL');await page.selectOption('#target','winner');
    }
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
        const missing=Object.entries(game.markets).filter(([provider,m])=>!m.bound_observations&&m.status!=='PREGAME_WINNER_REFERENCE_RETAINED_PRICE_NOT_PUBLIC'&&!(provider==='DRAFTKINGS'&&source.draftkings_analytical?.rows.some(r=>r.game_id===game.game_id&&r.target===target&&(r.horizon_minutes===120||r.horizon_minutes===null)))).length;
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
    const audit=source.b088_cached_science.paired_audit;
    assert.match(await page.locator('#latest-cached-audit-checkpoint').textContent(),/Cached-data audit update:.*no new fit, forecast or game quote.*Forecast foundation: B087-R3/);
    assert.equal(await page.locator('#owner-details summary').textContent(),'Forecast foundation: verified owner return');
    assert.match(await page.locator('#robust-clock').textContent(),/128 \/ 183.*55 missing/);
    assert.match(await page.locator('#robust-summary').textContent(),/reverse when week 44 is excluded/);
    for(const zone of ['UTC','America/Los_Angeles'])for(const metric of ['brier','log_loss','accuracy']){
      await page.selectOption('#robust-week-zone',zone);await page.selectOption('#robust-metric',metric);
      const view=audit.week_views[zone],expected=[['All 128 shared games',audit.overall],...Object.entries(view.weekly).map(([w,r])=>['Only '+w,r]),...Object.entries(view.leave_one_week_out).map(([w,r])=>['Exclude '+w,r])];
      assert.equal(await page.locator('#robust-rows tr').count(),7);
      for(const [label,row] of expected){
        const cells=await page.locator(`#robust-rows tr[data-cohort="${label}"] td`).allTextContents();
        assert.equal(cells.length,7);assert.equal(cells[1],String(row.games));
        ['HGB72','market_only9','ExtraTrees63'].forEach((alias,i)=>assert.equal(cells[i+2],metric==='accuracy'?(row.metrics[alias][metric]*100).toFixed(2)+'%':row.metrics[alias][metric].toFixed(6)));
        const delta=row.pairs.HGB72__minus__market_only9.mean_left_minus_right[metric==='accuracy'?'correctness':metric];
        assert.equal(cells[5],metric==='accuracy'?(delta*100).toFixed(2)+' percentage points':delta.toFixed(6));
      }
    }
    const tiedLead=await page.locator('#robust-rows tr[data-cohort="Exclude 2026-W44"] td').last().textContent();
    assert.match(tiedLead,/Shared lead:/);for(const label of ['Basketball + market','Market-only model','Basketball-only'])assert.ok(tiedLead.includes(label));
    await page.selectOption('#robust-metric','brier');
    assert.equal(await page.locator('#robust-rows tr[data-cohort="Exclude 2026-W44"] td').last().textContent(),'Market-only model');
    assert.match(await page.locator('#robust-limit').textContent(),/not 95% confidence intervals/);
    assert.match(await page.locator('#cached-work-details').textContent(),/830.*83.*166.*2,201/);
    assert.match(await page.locator('#cached-work-details').textContent(),/Nineteen tests passed/);
    assert.match(await page.locator('#cached-work-details').textContent(),/No predictive improvement established/);
    if(source.draftkings_analytical)assert.match(await page.locator('#source-inventory-rows').textContent(),/Earlier audit inventory retained/);else assert.match(await page.locator('#source-inventory-rows').textContent(),/Existing provider connection verified; no new game quotes collected/);
    assert.doesNotMatch(await page.locator('#robustness').textContent(),/undefined|NaN/);
    await page.selectOption('#robust-week-zone','UTC');
    assert.equal(await page.locator('#frontier-score-rows tr').count(),18);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/B087-R1/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/48 new frontier fits, 72 reused fits, 0 pending tasks and 0 failed tasks/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/120 of 120 registered tasks completed/);
    assert.match(await page.locator('#frontier-score-scope').textContent(),/not the required three-minute full-capacity pass/);
    assert.match(await page.locator('#latest-research-checkpoint').textContent(),/B087-R1.*120\/120 frontier tasks complete \(48 new, 72 reused\)/);
    assert.match(await page.locator('#latest-source-checkpoint').textContent(),/B087-R2.*32 source-qualified games and 64 eligible feature vectors/);
    assert.match(await page.locator('#upcoming-recovery-scope').textContent(),/3 official calendar requests \(1,081,438 downloaded bytes\) and performed 0 model fits/);
    assert.match(await page.locator('#warm-cache-scope').textContent(),/120 completed models and 66,432 evaluation rows reused in 3.975 seconds, with 0 new fits and 0 new prediction rows/);
    assert.match(await page.locator('#warm-cache-scope').textContent(),/does not measure a speedup/);
    assert.match(await page.locator('#latest-forecast-checkpoint').textContent(),/B087-R3.*448 new early-outlook rows for 32 games/);
    assert.match(await page.locator('#latest-forecast-checkpoint').textContent(),/1,012\/1,012 known scheduled regular games/);
    assert.match(await page.locator('#owner-status').textContent(),/B087-R3/);
    assert.match(await page.locator('#owner-status').textContent(),/3,773,418,232 bytes across 8 numbered byte-split pieces/);
    assert.equal(await page.locator('#earlier-frontier-rows tr').count(),36);
    const earlierRows=await page.locator('#earlier-frontier-rows tr').allTextContents();
    source.current_science_scores.new_frontier_earlier_season_ablations.forEach((row,i)=>{
      assert.ok(earlierRows[i].includes(row.phase));
      assert.ok(earlierRows[i].includes(row.baseline_metrics.games+' games'));
      for(const value of [row.baseline_metrics[row.primary_metric],row.candidate_metrics[row.primary_metric],row.paired_cluster_interval.lower,row.paired_cluster_interval.upper])assert.ok(earlierRows[i].includes(value.toFixed(6)));
    });
    assert.equal(await page.locator('#weighted-score-rows tr').count(),11);
    const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-json').click()]);
    assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),downloadSource);
    if(source.draftkings_analytical){assert.ok(source.draftkings_analytical.rows);assert.equal(downloadSource.draftkings_analytical.rows,undefined);assert.equal(downloadSource.draftkings_analytical.provider_quote_rows_excluded_from_download,true);}
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
