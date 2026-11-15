const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const sourcePath = path.join(__dirname, 'n108_current', 'index.html');
const source = fs.readFileSync(sourcePath, 'utf8');
const live = process.env.NFL_N108_ONLINE_URL;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const close = (a,b) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a-b)<=0.000005;

function checkPublicSource(html) {
  assert.doesNotMatch(html, /s3:\/\/|\/home\/(?:sagemaker-user|agent)\/|\/workspace\/scratch\/|-----BEGIN [^-]*PRIVATE KEY-----|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|[\w.+-]+@[\w.-]+\.(com|net|org|edu)\b/i);
  assert.match(html, /<main\b[^>]*>[\s\S]*?<\/main>/i);
  const assets = [...html.matchAll(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi)].map(m => m[0]);
  assert.ok(assets.some(a=>a.startsWith('<style')));
  assert.ok(assets.some(a=>/application\/json/i.test(a)));
  assert.ok(assets.some(a=>a.startsWith('<script') && !/type=["']application\/json["']/i.test(a)));
  return assets.concat(html.match(/<main\b[^>]*>[\s\S]*?<\/main>/i)[0]);
}

function checkCard(card) {
  assert.ok(Date.parse(card.issued) < Date.parse(card.deadline));
  assert.equal(card.rows.length, 26);
  assert.equal(new Set(card.rows.map(r => r.game)).size, 13);
  assert.equal(new Set(card.rows.map(r => r.game+' '+r.team)).size, 26);
  const selected = card.rows.filter(r => r.selected);
  assert.equal(selected.length, 5);
  assert.equal(new Set(selected.map(r => r.game)).size, 5);
  const gameBest = new Map();
  for (const row of card.rows) {
    for (const p of [row.cover, row.push, row.loss]) assert.ok(p >= 0 && p <= 1);
    assert.ok(close(row.cover + row.push + row.loss, 1), 'Cover/push/loss must total one');
    assert.ok(close(row.points, row.cover + 0.5*row.push), 'Expected contest points');
    gameBest.set(row.game, Math.max(gameBest.get(row.game) || 0, row.points));
  }
  const bestValues = [...gameBest.values()].sort((a,b)=>b-a).slice(0,5);
  const chosenValues = selected.map(r=>r.points).sort((a,b)=>b-a);
  bestValues.forEach((v,i)=>assert.ok(close(v,chosenValues[i]), 'The five selected games must maximize expected contest points'));
}

function checkDataset(data) {
  assert.equal(data.release,"N108");
  assert.equal(data.n108.rankings.length,4);assert.equal(data.n108.schedule.length,272);
  assert.ok(data.n108.strict_reference.every(r=>Date.parse(r.source)<=Date.parse(r.issue)&&Date.parse(r.issue)<=Date.parse(r.after_observed)));
  for(const c of data.n108.rankings){assert.ok(Date.parse(c.analysis_time)>Date.parse(c.contest_deadline));assert.equal(c.sides.length,26);assert.equal(new Set(c.sides.filter(r=>r.selected).map(r=>r.game_id)).size,5)}
  assert.deepEqual([...new Set(data.n108.boards.map(r=>r.source))].sort(),['DraftKings','Kalshi','Polymarket']); assert.ok(data.drives.length>0&&data.n101_margin.length>0&&data.n101_winner.length>0&&data.exchange.history.week===7);
  assert.equal(data.season_games.length,272);assert.equal(new Set(data.season_games.map(r=>r.game)).size,272);
  assert.deepEqual(data.season_counts,{Final:137,Confirmed:111,TBD:24});
  assert.equal(data.ties,1);
  const currentFinal=data.season_games.filter(g=>g.status==='Final');
  for(const g of currentFinal){
    if(g.p==null){assert.ok(g.winner_evidence&&g.q==null);continue;}
    assert.ok(g.p>=0&&g.p<=1&&g.q>=0&&g.q<=1);
    assert.equal(g.actual_margin,g.away_final-g.home_final);
    if(g.outcome==='Tie'){assert.equal(g.yb,null);assert.equal(g.qb,null);}
    else{assert.ok(close(g.yb,(g.p-Number(g.away_final>g.home_final))**2));}
  }
  if(data.strict?.complete){assert.equal(data.strict.promotion,false);assert.equal(data.strict.historical_new_strict_issue_credit,0);}

  assert.ok(Array.isArray(data.winner),'Winner evidence collection');
  assert.ok(data.margin.some(r=>r.arm==='market_joint'&&r.scope==='all_five_same_market_games'&&Number(r.season)===2026),'Common-cohort current margin evidence');
  for (const game of data.games) {
    assert.ok(close(game.away_score-game.home_score,game.margin),'Team-score margin sign');
    assert.ok(close(game.away_score+game.home_score,game.total),'Separate expected team-score total');
    assert.ok(Date.parse(game.issued)<Date.parse(game.kickoff),'Score issue before kickoff');
    if (game.winner) {
      assert.equal(game.winner.length,3);
      assert.ok(close(game.winner.reduce((a,b)=>a+b),1),'Away/tie/home partition');
      assert.ok(Date.parse(game.prob_issue)<Date.parse(game.kickoff),'Probability issue before kickoff');
    }
  }
  assert.equal(data.cards.filter(c=>c.release==='N107').length,4);assert.equal(data.cards.filter(c=>c.release==='N106').length,4);assert.equal(data.cards.filter(c=>c.release==='N105').length,6);assert.equal(data.cards.length, 14);
  assert.equal(new Set(data.cards.map(c=>c.release+' '+c.family)).size, 14);
  assert.equal(data.games.length,111);
  assert.equal(new Set(data.games.map(g=>g.game)).size,111);
  assert.ok(data.games.every(g=>g.away!==g.home && Number.isFinite(g.margin) && Number.isFinite(g.total)));
  for (const dataset of ['margin','frontier','history']) assert.ok(data[dataset].length > 0,dataset);
  assert.ok(data.exchange && Object.keys(data.exchange).length > 0);
  data.cards.forEach(checkCard);
}

async function exercise(width, browser, assets) {
  const page = await browser.newPage({viewport:{width,height:900}});
  try {
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    const response = await page.goto(live || pathToFileURL(sourcePath).href, {waitUntil:'domcontentloaded'});
    let responseHash=null;
    if (live) {
      assert.equal(response.status(), 200);
      const served=await response.body();
      responseHash=sha(served);
      for (const asset of assets) assert.ok(served.toString().includes(asset),'Deployed source asset or main layout differs');
      assert.equal(new URL(page.url()).pathname, '/circa/n108/');
    }
    assert.equal(await page.title(), 'Circa Million Picks & Performance Dashboard');
    const data=await page.locator('#data').evaluate(el=>JSON.parse(el.textContent));
    checkDataset(data);

    assert.equal(await page.locator('#n108').isVisible(),true);
    await page.selectOption('#mode108','late');
    for(const r of data.n108.rankings){await page.selectOption('#family108',r.family);await page.selectOption('#sides108','all');assert.equal(await page.locator('#late108table tbody tr').count(),26);await page.selectOption('#sides108','five');assert.equal(await page.locator('#late108table tbody tr').count(),5)}
    await page.selectOption('#mode108','season');for(const s of ['Final','Confirmed','TBD','All']){await page.selectOption('#status108',s);assert.equal(await page.locator('#schedule108table tbody tr').count(),data.n108.schedule.filter(r=>s==='All'||r.status===s).length)}
    await page.selectOption('#mode108','venues');for(const s of ['DraftKings','Kalshi','Polymarket']){await page.selectOption('#venue108',s);assert.equal(await page.locator('#venue108table tbody tr').count(),data.n108.boards.filter(r=>r.year===2026&&r.source===s).length)}
    await page.selectOption('#mode108','three');assert.equal(await page.locator('#three108table tbody tr').count(),data.n108.three.filter(r=>r.season===2026).length);
    await page.selectOption('#mode108','laws');assert.equal(await page.locator('#strict108table tbody tr').count(),data.n108.strict_reference.length);
    await page.locator('#bcard').click();
    assert.equal(await page.locator('#card').isVisible(),true);await page.selectOption('#issueRelease','N106');assert.equal(await page.locator('#family option').count(),4);assert.match(await page.locator('#cardStamp').textContent(),/N106/);await page.selectOption('#issueRelease','N107');assert.equal(await page.locator('#family option').count(),4);await page.selectOption('#issueRelease','N105');assert.equal(await page.locator('#family option').count(),6);await page.selectOption('#issueRelease','all');await page.locator('#bcontest').click();assert.equal(await page.locator('#contest').isVisible(),true);
    const contest=data.n107.contest;
    assert.ok(contest.season.length>0 && contest.weekly.length && !contest.evidence.verified_historical_entries);
    for(const year of ['2024','2025','2026']){
      await page.selectOption('#contestYear',year);
      for(const scope of ['week_open','saturday_remaining']){
        await page.selectOption('#contestScope',scope);
        const cohort=contest.season.filter(r=>r.season===+year&&r.scope===scope&&r.window==='through_week_9');
        assert.equal(await page.locator('#contestStandings tbody tr').count(),cohort.length);
        cohort.forEach(r=>assert.ok(close(r.observed_points,r.selected_wpl[0]+.5*r.selected_wpl[1])));
      }
    }
    await page.selectOption('#contestScope','week_open');await page.selectOption('#contestFamily','key_margin_calibration');
    await page.selectOption('#contestWeek','7');assert.equal(await page.locator('#contestPicks tbody tr').count(),5);
    await page.selectOption('#contestWeights','equal');assert.ok(await page.locator('#contestWeighted tbody tr').count()>0);
    await page.locator('#openCurrentCard').click();assert.equal(await page.locator('#card').isVisible(),true);
    await page.locator('#bn107').click();await page.locator('#n107').waitFor({state:'visible'});
    if(data.n107.margin_laws){
      assert.equal(await page.locator('#s3match option').count(),111);
      for(const [id,law] of Object.entries(data.n107.margin_laws)){
        assert.equal(law.cumulative.length,321);assert.equal(law.cumulative.at(-1),1000000);
        for(let i=1;i<law.cumulative.length;i++)assert.ok(law.cumulative[i]>=law.cumulative[i-1]);
      }
      await page.selectOption('#s3side','home');await page.fill('#s3min','3');await page.fill('#s3max','7');
      assert.equal(await page.locator('#s3law tbody tr').count(),6);
      await page.fill('#s3max','2');assert.equal(await page.locator('#s3law tbody tr').count(),0);
      await page.fill('#s3max','7');assert.equal(await page.locator('#s3law tbody tr').count(),6);
    }
    if(data.n107.totals.length){
      await page.fill('#s3tmin','44');assert.equal(await page.locator('#s3totlaw tbody tr').count(),1);
      assert.equal(await page.locator('#s3total option').count(),data.n107.totals.length);
      assert.ok(data.n107.totals.every(r=>r.cumulative.at(-1)===1000000));
    }
    const joint=data.n107.exchange.joint_model_replay;
    assert.equal(await page.locator('#jointlawrows tbody tr').count(),Object.values(joint).flat().length);
    assert.equal(await page.locator('#strictpointscores tbody tr').count(),data.n107.strict_scores.length);
    assert.equal(await page.locator('#totalpair tbody tr').count(),data.n107.exchange.matched_total_uncertainty.length);
    assert.equal(await page.locator('#bucketBoard tbody tr').count(),data.n107.exchange.bucket_study.boards.length);assert.equal(await page.locator('#clockChange tbody tr').count(),data.n107.exchange.decision_clock_study.length);assert.equal(await page.locator('#s3strict tbody tr').count(),data.n107.strict_new_rows.length);
    const uniqueSources=[...new Set(data.n107.providers.map(r=>r.source))];
    assert.ok(uniqueSources.includes('DraftKings')&&uniqueSources.includes('Kalshi')&&uniqueSources.includes('Polymarket'));
    for(const year of ['2024','2025','2026']){
      await page.selectOption('#s3year', year);await page.selectOption('#s3rel','');
      for(const source of uniqueSources){
        await page.selectOption('#s3source',source);const expected=data.n107.providers.filter(r=>r.year==year&&r.source===source);
        assert.equal(await page.locator('#s3prov tbody tr').count(),expected.length);
      }
    }
    await page.locator('#bn101').click();await page.locator('#n101').waitFor({state:'visible'});
    for(const year of ['2024','2025','2026']){
      await page.selectOption('#newYear',year);
      assert.equal(await page.locator('#driveRows tbody tr').count(),data.drives.filter(x=>x.season==year).length);
      for(const arm of [...new Set(data.n101_margin.map(x=>x.arm))]){
        await page.selectOption('#newArm',arm);
        const sc=await page.locator('#newScope').inputValue();
        assert.equal(await page.locator('#distRows tbody tr').count(),data.n101_margin.filter(x=>x.season==year&&x.scope===sc&&x.arm===arm).length);
      }
      for(const lead of [...new Set(data.n101_winner.map(x=>x.lead))]){
        await page.selectOption('#winnerLead',String(lead));
        assert.equal(await page.locator('#newWinner tbody tr').count(),data.n101_winner.filter(x=>x.season==year&&x.lead===lead&&x.baseline==='market').length);
      }
    }
    assert.equal(await page.locator('#providerRows tbody tr').count(),data.venue.length+data.named.length);
    assert.equal(await page.locator('#providerCurrent tbody tr').count(),data.named_current.length);
    assert.equal(await page.locator('#origMarket tbody tr').count(),data.original_contracts.scores.length);
    assert.equal(await page.locator('#totalRows tbody tr').count(),data.strict_total_forward.length);
    assert.ok(data.strict_total_forward.length&&data.total_contracts.pairs>0&&data.original_contracts.rows>0);
    assert.ok(data.named.some(r=>r.provider==='DraftKings')&&data.named.some(r=>r.provider==='Polymarket'));
    await page.locator('#bcard').click();
    await page.locator('#card').waitFor({state:'visible'});
    assert.equal(await page.locator('#family option').count(),14);
    for (let i=0; i<data.cards.length; i++) {
      await page.selectOption('#family',{index:i});
      await page.selectOption('#sideFilter','all');
      assert.equal(await page.locator('#cardTable tbody tr').count(), 26);
      await page.selectOption('#sideFilter','best');
      assert.equal(await page.locator('#cardTable tbody tr').count(), 5);
    }
    await page.locator('#bseason').click();
    await page.locator('#season').waitFor({state:'visible'});
    for(const [state,n] of Object.entries({all:272,Final:137,Confirmed:111,TBD:24})){
      await page.selectOption('#seasonStatus',state);assert.equal(await page.locator('#seasonTable tbody tr').count(),n);
    }
    await page.locator('#bforecast').click();
    await page.locator('#forecast').waitFor({state:'visible'});
    await page.fill('#team','');
    assert.equal(await page.locator('#gamesTable tbody tr').count(),111);
    const team = data.games[0].away;
    await page.fill('#team',team);
    const teamRows=await page.locator('#gamesTable tbody tr').allTextContents();
    const withTeam=data.games.filter(g=>g.away===team || g.home===team);
    assert.equal(teamRows.length,withTeam.length);
    assert.ok(teamRows.every(row=>row.includes(team)));
    await page.locator('#bmetric').click();
    await page.locator('#metric').waitFor({state:'visible'});
    for (const year of ['2024','2025','2026']) {
      await page.selectOption('#year',year);
      const arm=await page.locator('#arm').inputValue();
      const inYear=r=>String(r.season)===year;
      assert.equal(arm,'market_joint');
      for(const scope of await page.locator('#scope option').evaluateAll(items=>items.map(o=>o.value))) {
        await page.selectOption('#scope',scope);
        assert.equal(await page.locator('#marginTable tbody tr').count(),data.margin.filter(r=>inYear(r)&&r.arm===arm&&r.scope===scope).length);
      }
      assert.equal(await page.locator('#frontierTable tbody tr').count(),data.frontier.filter(inYear).length);
      assert.equal(await page.locator('#winnerTable tbody tr').count(),data.winner.filter(inYear).length);
    }
    await page.locator('#bmarket').click();
    await page.locator('#market').waitFor({state:'visible'});
    const scores=data.exchange.history.scores;
    for (const target of new Set(['all',...scores.map(r=>r.target)])) {
      await page.selectOption('#target',target);
      assert.equal(await page.locator('#marketTable tbody tr').count(),scores.filter(r=>target==='all'||r.target===target).length);
    }
    assert.equal(data.exchange.current.actual_trades,0);
    assert.ok(data.exchange.current.native_candle_equals_book<=data.exchange.current.paired);
    assert.ok(data.exchange.current.native_matches_distinct<=data.exchange.current.contracts);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1),false);
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({target:live || 'source',width,source_sha256:sha(source),served_sha256:responseHash,authored_blocks:assets.length,cards:data.cards.length,selected_sides:70,reviewed_sides:364,new_cards:0,retained_cards:14,late_rankings:4,late_sides:104,forecasts:111,team_filter_matches:teamRows.length,checks:'script/style/main, privacy, distinct games, ranking, probability arithmetic, filters, season scores, viewport and JS exceptions'}));
  } finally {
    await page.close();
  }
}

(async () => {
  const assets=checkPublicSource(source);
  if (process.argv.includes('--source-only')) {
    const dataBlock = assets.find(a=>/^<script\b[^>]*id=["']data["']/i.test(a));
    assert.ok(dataBlock,'Embedded public JSON');
    const dataset=JSON.parse(dataBlock.slice(dataBlock.indexOf('>')+1, dataBlock.lastIndexOf('</script>')));
    checkDataset(dataset);
    const required=['family','sideFilter','team','year','scope','cardTable','gamesTable','card','forecast','metric','market','bcard','bforecast','bmetric','bmarket'];
    for (const id of required) assert.ok(new RegExp('id=["\']'+id+'["\']').test(source),id);
    console.log(JSON.stringify({scope:'static source, no browser',sha256:sha(source),data_cards:dataset.cards.length,game_count:dataset.games.length,authored_blocks:assets.length}));
    return;
  }
  const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
  const executable=process.env.NFL_N108_CHROMIUM;
  const browser=await chromium.launch({headless:true, ...(executable ? {executablePath:executable} : {})});
  try {
    for (const width of [1440,390]) await exercise(width,browser,assets);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
