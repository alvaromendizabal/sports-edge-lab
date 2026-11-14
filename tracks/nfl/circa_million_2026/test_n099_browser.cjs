const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

const sourcePath = path.join(__dirname, 'n099_current', 'index.html');
const source = fs.readFileSync(sourcePath, 'utf8');
const live = process.env.NFL_N099_ONLINE_URL;
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
  assert.equal(data.cards.length, 6);
  assert.equal(new Set(data.cards.map(c=>c.family)).size, 6);
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
      assert.equal(new URL(page.url()).pathname, '/circa/n099/');
    }
    assert.equal(await page.title(), 'Circa Million Picks & Performance Dashboard');
    const data=await page.locator('#data').evaluate(el=>JSON.parse(el.textContent));
    checkDataset(data);

    await page.locator('#bcard').click();
    await page.locator('#card').waitFor({state:'visible'});
    assert.equal(await page.locator('#family option').count(),6);
    for (let i=0; i<data.cards.length; i++) {
      await page.selectOption('#family',{index:i});
      await page.selectOption('#sideFilter','all');
      assert.equal(await page.locator('#cardTable tbody tr').count(), 26);
      await page.selectOption('#sideFilter','best');
      assert.equal(await page.locator('#cardTable tbody tr').count(), 5);
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
      assert.equal(await page.locator('#marginTable tbody tr').count(),data.margin.filter(r=>inYear(r)&&r.arm===arm).length);
      assert.equal(await page.locator('#frontierTable tbody tr').count(),data.frontier.filter(inYear).length);
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
    console.log(JSON.stringify({target:live || 'source',width,source_sha256:sha(source),served_sha256:responseHash,authored_blocks:assets.length,cards:data.cards.length,selected_sides:30,reviewed_sides:156,forecasts:111,team_filter_matches:teamRows.length,checks:'script/style/main, privacy, distinct games, ranking, probability arithmetic, filters, season scores, viewport and JS exceptions'}));
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
    const required=['family','sideFilter','team','year','cardTable','gamesTable','card','forecast','metric','market','bcard','bforecast','bmetric','bmarket'];
    for (const id of required) assert.ok(new RegExp('id=["\']'+id+'["\']').test(source),id);
    console.log(JSON.stringify({scope:'static source, no browser',sha256:sha(source),data_cards:dataset.cards.length,game_count:dataset.games.length,authored_blocks:assets.length}));
    return;
  }
  const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
  const executable=process.env.NFL_N099_CHROMIUM;
  const browser=await chromium.launch({headless:true, ...(executable ? {executablePath:executable} : {})});
  try {
    for (const width of [1440,390]) await exercise(width,browser,assets);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
