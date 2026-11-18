'use strict';

// Render the aggregate status only. No owner executable or research job runs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const directory = __dirname;
const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || path.join(directory, '.browser-review'));
const source = fs.readFileSync(path.join(directory, 'b100_execution_status.json'));
const evidence = JSON.parse(source.toString('utf8'));
const pageBytes = fs.readFileSync(path.join(directory, 'b100_execution_status.html'));
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
fs.mkdirSync(output, {recursive:true});

async function main() {
  const launch = {headless:true};
  if (process.env.NBA_CHROMIUM_EXECUTABLE) launch.executablePath = process.env.NBA_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch(launch);
  const views = [];
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});
      await context.setOffline(true);
      const page = await context.newPage();
      const errors = [], requests = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {if(message.type()==='error')errors.push(message.text());});
      page.on('request', request => {if(/^https?:/.test(request.url()))requests.push(request.url());});
      await page.goto(pathToFileURL(path.join(directory,'b100_execution_status.html')).href);
      await page.getByRole('heading',{level:1}).waitFor();
      assert.match(await page.locator('h1').innerText(), /Retrieval and export finished\.\s+The scientific queues did not\./);
      for(const [metric, value] of [['new-projections','3,776'],['provider-requests','5'],['new-fits','0'],['completed-games','210']]) {
        assert.equal(await page.locator(`[data-metric="${metric}"]`).innerText(), value);
      }
      const text = await page.locator('body').innerText();
      for(const phrase of ['PARTIAL_RESUMABLE','6 tasks deferred','160 deferred','5,808 verified: 3,776 new + 2,032 reused',
        '5.63 average cores','23.47% of 24 admitted cores','80.45 seconds','zero full three-minute occupancy passes',
        '210 completed 2026–27 games','206 completed games','340,294,167 bytes','3,112 verified payloads','USD 0.4785',
        'Zero B100 owner executions, fits or inference rows','No qualified full-season champion','main integration pending',
        'website deployment pending']) {
        assert.ok(text.includes(phrase), `Missing qualified evidence: ${phrase}`);
      }
      assert.equal(await page.locator('.stages tbody tr').count(), 5);
      if(width === 390) {
        const cells = await page.locator('.stages tbody td').evaluateAll(nodes => nodes.map(node => ({
          label:node.dataset.label, generated:getComputedStyle(node,'::before').content,
          left:node.getBoundingClientRect().left, right:node.getBoundingClientRect().right,
          width:node.getBoundingClientRect().width, scroll:node.scrollWidth, client:node.clientWidth
        })));
        assert.equal(cells.length,10);
        for(const cell of cells) {
          assert.ok(['Completed','Unfinished or qualified'].includes(cell.label));
          assert.equal(cell.generated,JSON.stringify(cell.label));
          assert.ok(cell.left>=0 && cell.right<=390 && cell.width>250 && cell.scroll<=cell.client+1,
            'Each mobile stage cell must be readable without horizontal scrolling');
        }
      }
      assert.deepEqual(JSON.parse(await page.locator('#aggregate-evidence').textContent()), evidence);
      if(evidence.b100_preparation.status === 'PREPARED_VERIFIED') {
        assert.ok(text.includes('B100 replacement verified; owner execution pending'));
        assert.ok(text.includes(`${evidence.b100_preparation.canonical_engineering_tests} engineering tests`));
        assert.equal(evidence.b100_preparation.final_packaged_verification,'VERIFIED');
        assert.equal(evidence.b100_preparation.owner_cpu_acceptance,'NOT_RUN');
      } else {
        assert.ok(text.includes('B100 replacement in preparation'));
        assert.ok(text.includes('Final packaged verification and private staging are pending'));
      }
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth+1), `Page overflow at ${width}px`);
      await page.locator('#download-status').focus();
      const [download] = await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);
      assert.equal(download.suggestedFilename(),'b100_execution_status.json');
      assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),evidence);
      await page.evaluate(() => window.scrollTo(0,0));
      await page.screenshot({path:path.join(output,`nba-b100-status-${width}.png`),fullPage:true});
      assert.deepEqual(errors,[]);
      assert.deepEqual(requests,[]);
      views.push({page:'b100',width,offline:true,page_errors:0,remote_requests:0,page_overflow:false,exact_evidence_download:true,independent_context:true});
      await context.close();
    }
  } finally {await browser.close();}
  let checkout = null;
  try {checkout=execFileSync('git',['rev-parse','HEAD'],{cwd:directory,encoding:'utf8'}).trim();}catch{}
  const receipt = {schema:'sel.nba.b100.public_browser_receipt.v1',status:'PASS',
    html_sha256:sha256(pageBytes),json_sha256:sha256(source),source_head:process.env.NBA_SOURCE_HEAD_SHA||null,
    tested_checkout:checkout,views,owner_executions:0,new_owner_fits:0};
  fs.writeFileSync(path.join(output,'nba-b100-browser-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt));
}
main().catch(error => {console.error(error);process.exitCode=1;});
