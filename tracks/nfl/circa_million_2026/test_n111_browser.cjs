const {verifyHostedHtml}=require('./n111_current/verified_hosted_html.cjs');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');

const pagePath = process.env.NFL_N111_LOCAL_PATH || path.join(__dirname, 'n111_current', 'index.html');
const native = fs.readFileSync(pagePath);
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const pattern = /<script id="n111data" type="application\/json">([\s\S]*?)<\/script>/;
const data = JSON.parse(native.toString().match(pattern)[1]);
const parentSha = '2ed9b36184c5e68fcee872c40bba4f559a45ec9af0f098f6a13d4b4bc2c359f6';
const canonical = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/';
const url = process.env.NFL_N111_ONLINE_URL || pathToFileURL(pagePath).href;
const live = Boolean(process.env.NFL_N111_ONLINE_URL);

assert.equal(data.release, 'N111');
assert.equal(data.scope, 'public');
assert.equal(data.parent.games.length, 272);
assert.equal(new Set(data.market.fixtures.map(f => f.game)).size, 272);
assert.equal(data.market.fixtures.length, 272);
assert.deepEqual(data.market.fixtures.map(f=>f.game).sort(), data.parent.games.map(f=>f.game).sort());
assert(data.winner.scoreboard.length && data.frontier.by_season.length && data.market.panels.length);
assert(!/id="n111private"|s3:\/\/|\/home\/sagemaker-user|AKIA[A-Z0-9]{16}/i.test(native.toString()));
for (const f of data.market.fixtures) {
  for (const name of ['DraftKings','Kalshi','Polymarket']) {
    const v=f.providers[name];
    assert.equal(typeof v.n111_model_compared,'boolean');
    for (const r of [...v.n111_primary,...(v.n111_other_issued||[])]) {
      if (r.market_probability != null) {
        assert.equal(r.public_price_allowed, true);
        assert(['The Odds API','SportsBookISH'].includes(r.supplier));
      }
      for (const k of ['contract_id','rule_sha256','source_sha256','bid','ask','raw_legs']) assert(!Object.hasOwn(r,k));
    }
  }
}
async function fetchPublic(ref) {
  return fetch(ref,{credentials:'omit',redirect:'manual',headers:{'Cache-Control':'no-cache','User-Agent':'SportsEdgeLab N111 release readback'},signal:AbortSignal.timeout(50000)});
}
async function verifyRoutes() {
  const release=await fetchPublic(url), stable=await fetchPublic(canonical), pinned=await fetchPublic(canonical+'n110/'), m=await fetchPublic(canonical+'publication.json');
  for (const r of [release,stable,pinned,m]) assert.equal(r.status,200);
  verifyHostedHtml(Buffer.from(await release.arrayBuffer()),sha(native),'n111');
  verifyHostedHtml(Buffer.from(await pinned.arrayBuffer()),parentSha,'n110');
  const manifest=await m.json(), stableSha=verifyHostedHtml(Buffer.from(await stable.arrayBuffer()),manifest.assets['index.html'].sha256,'stable');
  assert.match(manifest.newest_review_path,/^n[0-9]+\/$/);
  assert.equal(manifest.assets['n111/index.html'].sha256,sha(native));
  assert.equal(manifest.assets['n110/index.html'].sha256,parentSha);
  assert.equal(manifest.assets[manifest.newest_review_path+'index.html'].sha256,stableSha);
  assert.equal(manifest.assets['index.html'].sha256,stableSha);
  for(const file of ['private.html','private_review.html']){
    const privateResult=await fetchPublic(new URL(file,url));
    assert([403,404,410].includes(privateResult.status));
  }
}
(async()=>{
  if(live) await verifyRoutes();
  const options={args:['--no-sandbox','--disable-dev-shm-usage']};
  if(process.env.TEST_CHROMIUM_EXECUTABLE) options.executablePath=process.env.TEST_CHROMIUM_EXECUTABLE;
  const browser=await chromium.launch(options);
  try {
    for (const width of [1440,390]) {
      const page=await browser.newPage({viewport:{width,height:910},ignoreHTTPSErrors:true});
      const errors=[];page.on('pageerror',e=>errors.push(String(e)));
      await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
      await page.waitForSelector('#leadersTable');
      assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
      assert.equal(sha(await page.locator('#n111data').textContent()),sha(native.toString().match(pattern)[1]));
      await page.locator('#metric').selectOption('margin CRPS');
      assert(await page.locator('#leadersTable table tbody tr').count());
      await page.getByRole('button',{name:'Games & venues',exact:true}).click();
      await page.waitForSelector('#caseRows button');
      assert.equal(await page.locator('#caseRows button').count(),272);
      await page.locator('#status').selectOption('Kickoff TBD');
      assert.equal(await page.locator('#caseRows button').count(),data.parent.games.filter(g=>g.status==='Kickoff TBD').length);
      await page.locator('#status').selectOption('');
      const game=data.market.fixtures.find(g=>g.providers.Kalshi.n111_primary.length)||data.market.fixtures[0];
      await page.locator('#gameq').fill(game.game);
      assert.equal(await page.locator('#caseRows button').count(),1);
      await page.locator('#caseRows button').click();
      assert.equal(await page.locator('#gameHeading').innerText(),game.away+' at '+game.home);
      await page.locator('#venue').selectOption('Kalshi');
      assert.equal(await page.locator('#caseDetail .venue-card').count(),1);
      await page.getByText('Qualified pregame checkpoints',{exact:true}).click();
      const ck=Object.keys(game.providers.Kalshi.qualified_checkpoints||{});
      assert.equal(await page.locator('#caseDetail .venue-card details tbody tr').count(),ck.length);
      await page.getByRole('button',{name:'Market comparisons',exact:true}).click();
      await page.locator('#marketVenue').selectOption('DraftKings');
      await page.getByText('Source coverage and settlement',{exact:true}).click();
      assert(await page.locator('#mk table tbody tr').count());
      await page.getByRole('button',{name:'Model features',exact:true}).click();
      assert(await page.getByText('Inherited named model feature groups',{exact:true}).isVisible());
      await page.getByRole('button',{name:'Circa cards',exact:true}).click();
      assert(await page.getByText('Week 10 · deadline passed',{exact:true}).isVisible());
      const size=await page.evaluate(()=>[document.documentElement.scrollWidth,innerWidth]);
      assert(size[0]<=size[1]+2);assert.deepEqual(errors,[]);
      console.log(JSON.stringify({source:live?'hosted':'repository',width,fixtures:272,sha256:sha(native),script_errors:errors.length}));
      await page.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
