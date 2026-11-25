/* Mandatory live verification of the current publication; historical receipts stay immutable. */
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || "playwright");

const root = __dirname;
const output = process.env.NFL_CURRENT_EVIDENCE || path.join(process.env.RUNNER_TEMP || "/tmp", "nfl-current-live-evidence");
fs.mkdirSync(output, { recursive: true });
const report = { status: "RUNNING", method: "Anonymous deployed asset hashes and live Chromium interactions", checks: [], assets: [], html_verifications: [], viewports: [1440, 390], page_errors: [], console_errors: [] };
const digest = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const check = async (name, action) => { await action(); report.checks.push(name); };
const save = () => fs.writeFileSync(path.join(output, "live-browser.json"), JSON.stringify(report, null, 2) + "\n");
let browser;

// This is the same narrowly anchored hosting exception used by the preserved N089
// live verifier. Every original HTML byte must still match; arbitrary changes fail.
function verifyHostedHtml(observed, source, context) {
  const bodyFile = `${context}-response.html`;
  fs.writeFileSync(path.join(output, bodyFile), observed);
  const record = { context, response_file: bodyFile, received_bytes: observed.length, received_sha256: digest(observed), original_bytes: source.length, original_sha256: digest(source), status: "UNVERIFIED" };
  report.html_verifications.push(record);
  if (observed.equals(source)) {
    record.status = "EXACT_ORIGINAL_BYTES";
    return record;
  }
  const text = observed.toString("utf8");
  // The archived redirect ends without an explicit body tag. On this one artifact Cloudflare appends
  // its known script at EOF. Exact recovery of all of the pinned original bytes still applies.
  const change = context === "current-archive-n186-research-history.html"
    ? /<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument[\s\S]*?<\/script>$/g
    : /<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument[\s\S]*?<\/script>(?=<\/body>\s*<\/html>\s*$)/g;
  const matches = [...text.matchAll(change)];
  assert.equal(matches.length, 1, `${context}: unexpected hosted HTML change; raw response retained`);
  const added = matches[0][0];
  record.fragment_file = `${context}-hosting-fragment.txt`;
  fs.writeFileSync(path.join(output, record.fragment_file), added);
  assert(added.length < 4096 && added.includes("/cdn-cgi/challenge-platform/scripts/jsd/main.js") && added.includes("window.__CF$cv$params"), `${context}: unknown host script`);
  const original = Buffer.from(text.slice(0, matches[0].index) + text.slice(matches[0].index + added.length));
  record.canonical_sha256 = digest(original);
  record.inserted_script_bytes = Buffer.byteLength(added);
  record.insertion_byte_offset = Buffer.byteLength(text.slice(0, matches[0].index));
  assert.equal(digest(original), digest(source), `${context}: original HTML/data/scripts changed`);
  assert(original.equals(source), `${context}: original bytes changed`);
  record.status = "ORIGINAL_BYTES_EQUAL_WITH_OBSERVED_CLOUDFLARE_APPEND";
  record.transformation = "SINGLE_OBSERVED_CLOUDFLARE_CHALLENGE_SCRIPT_APPENDED";
  return record;
}

(async () => {
  const receipt = JSON.parse(fs.readFileSync(path.join(root, "publication.json"), "utf8"));
  const historyReceipt = JSON.parse(fs.readFileSync(path.join(root, "publication-n175.json"), "utf8"));
  const data = JSON.parse(fs.readFileSync(path.join(root, "data.json"), "utf8"));
  const base = new URL(receipt.public_url);
  assert.equal(base.protocol, "https:");
  assert(base.hostname.endsWith(".alv-mendizabal.chatgpt.site"), "Publication must use the owner's public Site origin");
  assert(!base.username && !base.password && !base.search && !base.hash);
  assert.match(receipt.status, /^DEPLOYED/);
  const verified = receipt.status === "DEPLOYED_HTTP_VERIFIED";
  if (verified) assert.equal(receipt.verification.all_match, true);
  assert.equal(data.games.length, 12, "This Week 11 publication contains twelve remaining games");
  report.url = base.href;
  report.application_source_commit = receipt.github_application_source_commit;
  report.workflow_commit = process.env.GITHUB_SHA || null;
  report.pr_head = process.env.NFL_CURRENT_PR_HEAD || null;
  browser = await chromium.launch({ headless: true });
  const assetContext = await browser.newContext();
  const archivedFile = name => name === "index.html" ? "research-history.html" : name;
  const requiredAssets = ["index.html", "app.js", "styles.css", "data.json", "evidence.json", "circa_evidence.json", "newest_model_comparison.json", "execution_status.json"];
  await check("Eight canonical deployed assets match publication bytes; any Cloudflare HTML append is separately recorded", async () => {
    assert.deepEqual(historyReceipt.verification.assets.map(a => a.path).sort(), [...requiredAssets].sort());
    for (const asset of historyReceipt.verification.assets) {
      if (verified) {
        assert.equal(asset.status, 200);
        assert.equal(asset.matches_pushed_source, true);
      }
      const local = fs.readFileSync(path.join(root, archivedFile(asset.path)));
      const url = new URL(archivedFile(asset.path), base);
      const response = await assetContext.request.get(url.href, { timeout: 30000 });
      const bytes = await response.body();
      const observed = { path: asset.path, url: response.url(), status: response.status(), bytes: bytes.length, sha256: digest(bytes) };
      report.assets.push(observed);
      assert.equal(response.status(), 200, `${asset.path}: live HTTP status`);
      assert.equal(new URL(response.url()).origin, base.origin, "Unexpected origin redirect");
      if (asset.path === "index.html") {
        const canonical = verifyHostedHtml(bytes, local, "asset-index");
        observed.html_verification = canonical.status;
        console.log("Production HTML evidence", JSON.stringify(canonical));
      } else {
        assert.equal(observed.sha256, digest(local), `${asset.path}: live and committed bytes differ`);
        assert.equal(observed.bytes, local.length);
      }
    }
    console.log("Production asset evidence", JSON.stringify(report.assets));
    for (const asset of historyReceipt.verification.assets) {
      const local = fs.readFileSync(path.join(root, archivedFile(asset.path)));
      assert.equal(digest(local), asset.sha256, `${asset.path}: committed source differs from publication receipt`);
      assert.equal(local.length, asset.bytes);
    }
  });
  await check("Current anonymous release matches every declared published asset", async () => {
    assert(verified, "Current game day publication needs an anonymous HTTP receipt");
    const assets = receipt.verification.assets;
    assert(assets.some(a => a.path === "index.html"));
    assert(assets.filter(a => a.path.endsWith(".png")).length >= 4);
    for (const asset of assets) {
      const local = fs.readFileSync(path.join(root, asset.path));
      assert.equal(digest(local), asset.sha256);
      assert.equal(local.length, asset.bytes);
      const response = await assetContext.request.get(new URL(asset.path, base).href, { timeout: 30000 });
      assert.equal(response.status(), 200, asset.path);
      assert.equal(new URL(response.url()).origin, base.origin);
      const bytes = await response.body();
      if (asset.path.endsWith(".html")) {
        verifyHostedHtml(bytes, local, `current-${asset.path.replace(/[^a-zA-Z0-9_.-]/g, "-")}`);
      } else {
        assert(bytes.equals(local), asset.path);
      }
    }
  });
  await assetContext.close();

  for (const width of report.viewports) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, timezoneId: "America/Los_Angeles" });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on("pageerror", error => report.page_errors.push({ width, message: error.message }));
    page.on("console", message => { if (message.type() === "error") report.console_errors.push({ width, text: message.text(), location: message.location() }); });
    const text = selector => page.locator(selector).innerText();
    const count = (selector, expected) => page.locator(selector).count().then(actual => assert.equal(actual, expected, selector));
    const noOverflow = async () => assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${width}px layout overflows horizontally`);
    await check(`${width}px: home opens the current release; older shared links still open the original dated slate`, async () => {
      await page.goto(base.href, { waitUntil: "domcontentloaded" });
      await noOverflow();
      assert.match(await page.locator("body").innerText(), /Week 12/i);
      assert(page.url().startsWith(base.href));
      assert.match(await text(".hero-stats"), /LAR by 4.25|Rams by 4.25/);
      assert.match(await text(".hero-footer"), /10:08 PM PT/);
      assert.match(await text("#results"), /N189 VS N188/i);
      await count("#completed-games tbody tr", 163);
      await count("[data-joint-games] tbody tr", 109);
      await count("[data-recovered-ratio] tbody tr", 15);
      assert.match(await text("#recovered-validation"), /70.35%/);
      assert.match(await text("#recovered-validation"), /65.64%/);
      assert.match(await text("#recovered-validation"), /60.54%/);
      await count("[data-recovered-forecast-week] tbody tr", 109);
      await count("[data-joint-ratio] tbody tr", 15);
      assert.match(await text("#joint-scores"), /25.17/);
      await count("[data-secondary-ratio] tbody tr", 15);
      assert.match(await text("#secondary-nominees"), /74.04%/);
      assert.match(await text(".hero-stats"), /47.22/);
      await count("#season-outlook .source-table tbody tr", 109);
      await count("[data-market-game]", 16);
      await count("[data-market-game] tbody tr", 144);
      await page.locator("#market-matchup").selectOption("2026_12_NE_LAC");
      await count("[data-market-game]:visible tbody tr", 9);
      assert.match(await text("[data-market-game]:visible"), /Direct exchange observation/);
      await page.locator("#market-matchup").selectOption("2026_12_GB_LA");
      assert.equal(await page.locator(".source-ledger summary").filter({hasText:"79 sources"}).count(), 1);
      const archiveLink=page.locator('a[href="archive/n186/index.html"]');
      assert.equal(await archiveLink.count(),1);
      await count("#games details.game:visible", 16);
      await page.locator("#day").selectOption("Thu Nov 26");
      await count("#games details.game:visible", 3);
      await page.locator("#day").selectOption("");
      await page.locator("#game-search").fill("Packers");
      await count("#games details.game:visible", 1);
      await page.locator("#games details.game:visible > summary").click();
      assert.match(await text("#games details.game:visible .detail"), /58.0%/);
      await page.locator("#game-search").fill("");
      await count("#circa .contest-game", 16);
      await count("#circa .contest-game tbody tr", 32);
      await page.locator("#rank-filter").selectOption("top");
      await count("#circa .contest-game:visible", 5);
      await page.locator("#rank-filter").selectOption("all");
      for (const weight of ["50", "40", "30", "20", "10"]) {
        await page.locator("#weights").selectOption(weight);
        await count(`.score-table tr[data-weight="${weight}"]:visible`, 7);
        await count(".score-table tbody tr:visible", 7);
      }
      await noOverflow();
      await page.screenshot({ path: path.join(output, `week12-${width}.png`), fullPage: false });
      assert(await page.locator('a[href*="research-history.html"]').count());
      for (const [view, anchor] of Object.entries({slate:"slate", circa:"circa", performance:"results", cards:"cards"})) {
        await page.goto(new URL("?view=" + view, base).href);
        await page.waitForURL(u => u.hash === "#" + anchor && !u.searchParams.has("view"));
        assert(!/\/research-history(?:\.html)?$/.test(new URL(page.url()).pathname));
      }
      await page.goto(new URL("?view=cards&type=games&clock=T60&page=4", base).href);
      await page.waitForURL(u => /\/research-history(?:\.html)?$/.test(u.pathname) && u.searchParams.get("page") === "4");
      await page.waitForFunction(() => document.querySelector("#cards-page-label")?.textContent.trim() === "4 / 4");
    });
    await check(width + "px: dedicated Circa dashboard with all alternatives and 47 graded cards", async () => {
      await page.goto(new URL("circa/", base).href);
      assert.equal(await text("h1"), "Circa Million Picks & Performance Dashboard");
      await count("[data-card-season] tbody tr", 47);
      await count("[data-card-validation] tbody tr", 5);
      assert.match(await text("main"), /42.07%/);
      assert.match(await text("#historic-rules"), /28.5 out of 45/);
      assert.match(await text("#historic-rules"), /30.5\/55/);
      await count("#option-grid tbody tr", 32);
      await page.locator("#rank-filter").selectOption("top");
      await count(".contest-game:visible", 5);
      await page.locator("#contest-search").fill("does-not-match");
      await count(".contest-game:visible", 0);
      await noOverflow();
    });
    let navigation = 0;
    const go = async query => {
      const response = await page.goto(new URL("research-history.html" + query, base).href, { waitUntil: "domcontentloaded" });
      assert.equal(response.status(), 200);
      assert.equal(new URL(response.url()).origin, base.origin);
      verifyHostedHtml(await response.body(), fs.readFileSync(path.join(root, "research-history.html")), `navigation-${width}-${++navigation}`);
      await page.waitForFunction(() => document.querySelectorAll("#games-grid .game-card").length > 0);
    };
    await go("?view=slate&clock=T120");
    await check(`${width}px: dated usable snapshot, Sunday/Monday filters, all twelve game identities`, async () => {
      await count("#games-grid .game-card", 11);
      assert((await text("#forecast-clock-note")).includes(data.forecast_clock_meta.T120.description));
      assert.match(await text("#evidence-date"), /Nov 16/);
      await page.locator('[data-day="monday"]').click();
      await count("#games-grid .game-card", 1);
      await page.locator('[data-day="all"]').click();
      await count("#games-grid .game-card", 12);
      const ids = await page.locator("#games-grid .game-card").evaluateAll(nodes => nodes.map(n => n.dataset.gameId).sort());
      assert.deepEqual(ids, data.games.map(g => g.id).sort());
      for (const game of data.games) {
        const card = page.locator(`[data-game-id="${game.id}"]`);
        const forecast = game.forecasts.T120;
        const metrics = await card.locator(".metric-value").allTextContents();
        assert.equal(metrics[0], `${(100 * Math.max(forecast.win_home, forecast.win_away)).toFixed(1)}%`);
        assert.equal(metrics[1], `${Math.abs(forecast.margin_home).toFixed(1)} pts`);
        assert.equal(metrics[2], forecast.total.toFixed(1));
        assert.match(await card.locator(".forecast-foot").innerText(), /Compiled Nov 16/);
      }
      await noOverflow();
      await page.screenshot({ path: path.join(output, `slate-${width}.png`), fullPage: true });
    });
    await check(`${width}px: T60 stays unavailable without borrowing T120 matchup values`, async () => {
      await page.locator('#view-slate [data-forecast-clock="T60"]').click();
      assert.equal(new URL(page.url()).searchParams.get("clock"), "T60");
      const values = await page.locator("#games-grid .metric-value").allTextContents();
      assert.equal(values.length, 36);
      assert(values.every(value => value.trim() === "—"));
      assert((await text("#forecast-clock-note")).includes(data.forecast_clock_meta.T60.description));
      await page.locator('#view-slate [data-forecast-clock="T120"]').click();
      await page.locator("#team-search").fill("chiefs");
      await count("#games-grid .game-card", 1);
      await page.locator("#team-search").fill("");
    });
    await page.locator('.view-nav [data-view-link="circa"]').click();
    await check(`${width}px: twenty-four Circa sides and dated distribution notice`, async () => {
      await count("#circa-board .circa-game", 12);
      await count("#circa-board .circa-side", 24);
      await count("#circa-board [data-pick-game]:enabled", 24);
      assert.equal(await text("#circa-source-summary"), data.circa_source_summary);
      assert.equal(await text("#circa-deadline"), data.circa_deadline.label);
      await noOverflow();
    });
    await check(`${width}px: Week 11 retrospective primary card and original entry status`, async () => {
      const replay = page.locator("#week11-primary-replay");
      assert(await replay.isVisible());
      const complete = await replay.innerText();
      for (const phrase of ["3 wins, 2 losses", "26 sides across 13 games", "all 50 earlier selections", "zero original submission receipts"]) assert(complete.includes(phrase), phrase);
      const sides = await replay.locator("tbody tr").allInnerTexts();
      assert.deepEqual(sides.map(row => row.trim().split(/\s+/).slice(1).join(" ")), ["Kansas City Win", "Buffalo Win", "Houston Win", "Chicago Loss", "Carolina Loss"]);
      await replay.locator("summary").click();
      assert.equal(await replay.locator("tbody").isVisible(), false);
      await replay.locator("summary").click();
      assert.equal(await text("#pick-count"), "0 / 5");
      await noOverflow();
    });
    await check(`${width}px: five distinct games, replacement, sixth-game limit, clear`, async () => {
      await page.locator("#best-card").click();
      const selected = () => page.locator('#circa-board [data-pick-game][aria-pressed="true"]').evaluateAll(nodes => nodes.map(n => ({ id: n.dataset.pickGame, side: n.dataset.pickSide })));
      const picks = await selected();
      assert.equal(picks.length, 5);
      assert.equal(new Set(picks.map(p => p.id)).size, 5);
      const expected = data.games.map(g => Math.max(g.circa.cover_home, g.circa.cover_away) + g.circa.push / 2).sort((a,b) => b-a).slice(0,5).reduce((a,b) => a+b, 0);
      assert.equal(await text("#pick-expected"), expected.toFixed(3));
      const first = picks[0];
      const opposite = first.side === "home" ? "away" : "home";
      await page.locator(`[data-pick-game="${first.id}"][data-pick-side="${opposite}"]`).click();
      const replaced = await selected();
      assert.equal(replaced.length, 5);
      assert.equal(replaced.find(p => p.id === first.id).side, opposite);
      const sixth = data.games.find(g => !picks.some(p => p.id === g.id));
      await page.locator(`[data-pick-game="${sixth.id}"][data-pick-side="home"]`).click();
      assert.deepEqual(await selected(), replaced);
      await page.locator("#clear-card").click();
      assert.equal((await selected()).length, 0);
      assert.equal(await text("#pick-count"), "0 / 5");
    });
    await page.locator('.view-nav [data-view-link="performance"]').click();
    await check(`${width}px: N167 calibration, fitting and incomplete Circa stage are distinguished`, async () => {
      const results = await page.locator("#n167-results").innerText();
      for (const phrase of ["570 validation games", "103 win–tie–loss candidates", "68 score-distribution blends", "158 finals", "archived 151-final census", "224 score cells"]) assert(results.includes(phrase));
      const leaders = page.locator("#n167-results details").filter({ has: page.locator("summary", { hasText: "T120 outcome leaders by objective" }) });
      await leaders.locator("summary").click();
      const leadersText = await leaders.innerText();
      for (const phrase of ["62.92%", "56.67%", "150 / 157", "0.7223", "151 / 158"]) assert(leadersText.includes(phrase));
      await leaders.locator("summary").click();
      const improvements = page.locator("#n167-results details").filter({ has: page.locator("summary", { hasText: "T120 total-distribution improvements" }) });
      await improvements.locator("summary").click();
      const improvementsText = await improvements.innerText();
      for (const phrase of ["total pinball 10", "2.2006", "total pinball 50", "5.2121", "total pinball 90", "2.5501"]) assert(improvementsText.includes(phrase));
      await improvements.locator("summary").click();
    });
    await check(`${width}px: N168 selected leaders, scoring coverage and owner accounting`, async () => {
      const results = page.locator("#n168-results");
      const initial = await results.innerText();
      for (const phrase of ["672 raw and calibrated", "0.00175", "0.01281", "151 / 159", "113 unsettled games", "2,114 archived time-valid replays", "zero new original forecasts"]) assert(initial.includes(phrase));
      for (const horizon of [60, 120]) {
        const section = page.locator(`#n168-nominees-${horizon}`);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(), 14);
        assert((await section.innerText()).includes("150 / 158"));
        await section.locator("summary").click();
      }
      await noOverflow();
    });
    await check(`${width}px: N169 distribution and score-form metrics, separate market overlaps and owner disposition`, async () => {
      const results = page.locator("#n169-results");
      for (const phrase of ["46.8298", "47.2842", "2,352 residual distributions", "441 private forecasts across 110 games"]) assert((await results.innerText()).includes(phrase));
      for (const [key, rows, phrase] of [["distributions-120", 11, "151 / 161"], ["distributions-60", 11, "46.4667"], ["causal-60", 12, "157 / 160"], ["causal-120", 12, "157 / 160"], ["markets", 12, "141 / 159"]]) {
        const section = page.locator(`#n169-${key}`);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(), rows);
        assert((await section.innerText()).includes(phrase), key + " missing " + phrase);
        await section.locator("summary").click();
      }
      await noOverflow();
    });
    await check(`${width}px: N170 form and source ranks, historical report gaps and owner completion`, async () => {
      const results = page.locator("#n170-results");
      for (const phrase of ["66.32%", "62.42% on 157 of 160", "792 new fits", "4,057 of 12,240", "50 of 1,088", "24 points on 54 graded picks out of 55"]) assert((await results.innerText()).includes(phrase),phrase);
      for (const [key, size] of [["form-120",12],["form-60",12],["sources-120",10],["sources-60",14]]) {
        const section = page.locator(`#n170-${key}`);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(),size);
        await section.locator("summary").click();
      }
      const panel = page.locator("#execution-status");
      await panel.locator("summary").click();
      const body = await panel.innerText();
      for (const phrase of ["Three of three registered stages completed","272 new forests","69,632 new trees","36 simultaneous optimizers","$0.1269"]) assert(body.includes(phrase), phrase);
      await panel.locator("summary").click();
      await noOverflow();
    });
    await check(`${width}px: N175 primary winners, full and covered scores, clock and source evidence`, async () => {
      const published = JSON.parse(fs.readFileSync(path.join(root,"execution_status.json"))).n175_research;
      const panel = page.locator("#n175-results");
      for (const phrase of ["10,260 of 10,362", "Twelve of 64", "9,033 candidates", "Extra Trees"]) assert((await panel.innerText()).includes(phrase),phrase);
      for (const [key,count] of [["h120",32],["h60",32],["sensitivity",5],["coverage",4],["markets",24]]) {
        const section = page.locator("#n175-"+key);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(),count);
        if (key.startsWith("h")) {
          const expected = published.primary.filter(r=>r.horizon_minutes===Number(key.slice(1))).sort((a,b)=>a.metric.localeCompare(b.metric));
          const actual = await section.locator("tbody tr").allTextContents();
          for (let i=0;i<expected.length;i++) {
            const r=expected[i];
            assert(actual[i].includes(r.metric.replaceAll("_"," ")));
            assert.equal(await section.locator("tbody tr").nth(i).locator("td").last().textContent(),r.score_2026_full===null?"Unavailable":r.score_2026_full.toFixed(4));
          }
        }
        if (key==="markets") for (const venue of ["DraftKings","Kalshi","Polymarket","Polymarket US"]) assert((await section.innerText()).includes(venue));
        await noOverflow();
        await section.locator("summary").click();
      }
    });
    await check(`${width}px: N174 primary winners, full and covered scores, clock and source evidence`, async () => {
      const published = JSON.parse(fs.readFileSync(path.join(root,"execution_status.json"))).n174_research;
      const panel = page.locator("#n174-results");
      for (const phrase of ["10,236 of 10,362", "Twelve of 64", "8,737 candidates", "432 new blend recipes"]) assert((await panel.innerText()).includes(phrase),phrase);
      for (const [key,count] of [["h120",32],["h60",32],["sensitivity",5],["coverage",3],["markets",24]]) {
        const section = page.locator("#n174-"+key);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(),count);
        if (key.startsWith("h")) {
          const expected = published.primary.filter(r=>r.horizon_minutes===Number(key.slice(1))).sort((a,b)=>a.metric.localeCompare(b.metric));
          const actual = await section.locator("tbody tr").allTextContents();
          for (let i=0;i<expected.length;i++) {
            const r=expected[i];
            assert(actual[i].includes(r.metric.replaceAll("_"," ")));
            assert.equal(await section.locator("tbody tr").nth(i).locator("td").last().textContent(),r.score_2026_full===null?"Unavailable":r.score_2026_full.toFixed(4));
          }
        }
        if (key==="markets") for (const venue of ["DraftKings","Kalshi","Polymarket","Polymarket US"]) assert((await section.innerText()).includes(venue));
        await noOverflow();
        await section.locator("summary").click();
      }
    });
    await check(`${width}px: N173 completed grades, missing scores, sensitivities and paired benchmarks`, async () => {
      const panel = page.locator("#n173-results");
      for (const phrase of ["10,129 of 10,362", "151", "8,305 candidates", "162 completed games", "1,776 newly evaluated source candidates"])
        assert((await panel.innerText()).includes(phrase), phrase);
      for (const [key,count] of [["h120",32],["h60",32],["sensitivity",5],["coverage",5],["markets",24]]) {
        const section = page.locator("#n173-"+key);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(),count);
        if (key.startsWith("h")) assert.equal(await section.locator("tbody tr td:last-child").allTextContents().then(values => values.filter(v => v==="Unavailable").length),32);
        if (key==="coverage") assert((await section.innerText()).includes("1,160 explicit gaps"));
        if (key==="markets") for (const venue of ["DraftKings","Kalshi","Polymarket","Polymarket US"]) assert((await section.innerText()).includes(venue));
        await noOverflow();
        await section.locator("summary").click();
      }
    });
    await check(`${width}px: N172 owner grades, sensitivities and separate forecast evidence`, async () => {
      const p = page.locator("#n172-results");
      for (const phrase of ["9,978 of 10,298", "788 game-level grades", "6,529 candidates", "114 dispersion laws"]) assert((await p.innerText()).includes(phrase),phrase);
      for (const [id, count] of [["h120",32],["h60",32],["sensitivity",5],["coverage",4]]) {
        const detail = page.locator("#n172-"+id);
        await detail.locator("summary").click();
        assert.equal(await detail.locator("tbody tr").count(),count);
        if (id==="coverage") assert((await detail.innerText()).includes("2,540 explicit gaps"));
        await noOverflow();
        await detail.locator("summary").click();
      }
    });
    await check(`${width}px: N171 locked champions, replay gaps and separate market source populations`, async () => {
      const panel = page.locator("#n171-results");
      for (const phrase of ["6,415 candidates","9,190 grades for 10,298","59.87% on 157 of 160","12,274 have archived time-valid replays","5,134 have explicit gaps"]) assert((await panel.innerText()).includes(phrase),phrase);
      for (const [id,count] of [["h120",32],["h60",32],["sources",18]]) {
        const section = page.locator("#n171-"+id);
        await section.locator("summary").click();
        assert.equal(await section.locator("tbody tr").count(),count);
        if (id==="sources") for (const name of ["DraftKings","Kalshi","Polymarket"]) assert((await section.innerText()).includes(name));
        await noOverflow();
        await section.locator("summary").click();
      }
    });
    await check(`${width}px: N165 annual scores, complete market denominators and issue timing`, async () => {
      const newResults = page.locator("#n165-frontier");
      assert.match(await newResults.innerText(), /204 quantile fits/);
      assert.match(await newResults.innerText(), /58\.11%[\s\S]*148 \/ 150/);
      for (const minutes of [60, 120]) {
        const nominations = page.locator(`#n165-h${minutes}`);
        await nominations.locator("summary").click();
        assert.equal(await nominations.locator("tbody tr").count(), 24);
        assert.match(await nominations.innerText(), /149 \/ 151/);
      }
      await page.locator("#n165-issues summary").click();
      assert.match(await page.locator("#n165-issues").innerText(), /114 private forecasts/);
      const coverage = page.locator("#n165-books");
      await coverage.locator("summary").click();
      assert.equal(await coverage.locator("tbody tr").count(), 99);
      await page.locator("#n165-clock").selectOption("1");
      await page.locator("#n165-product").selectOption("1");
      await page.locator("#n165-scope").selectOption("1");
      assert.equal(await text("#n165-coverage-caption"), "Point spread · 1 hour · 121 upcoming games");
      const denominators = await coverage.locator("tbody td").allTextContents();
      assert(denominators.every(value => value === "0 / 121"));
      await noOverflow();
    });
    await check(`${width}px: locked results preserve eligibility and matched venue populations`, async () => {
      const grading = page.locator("#n164-grading");
      const leaders = grading.locator(":scope > .comparison-table-wrap tbody tr");
      assert.match(await leaders.nth(0).innerText(), /58\.78%[\s\S]*148 \/ 150/);
      assert.match(await leaders.nth(2).innerText(), /149 \/ 151/);
      assert.match(await grading.innerText(), /zero original forecasts/);
      const candidates = page.locator("#n164-candidates");
      if (await candidates.getAttribute("open") === null) {
        await candidates.locator("summary").click();
      }
      const rows = candidates.locator("[data-grade-metric]");
      assert.equal(await rows.count(), 112);
      await page.locator("#n164-metric").selectOption("margin_rmse");
      for (const horizon of ["60", "120"]) {
        await page.locator("#n164-horizon").selectOption(horizon);
        const expected = rows.and(page.locator(`[data-grade-metric="margin_rmse"][data-grade-horizon="${horizon}"]`));
        assert((await expected.count()) > 0);
        assert.equal(await candidates.locator("[data-grade-metric]:visible").count(), await expected.count());
        assert.equal(await expected.first().isVisible(), true);
        assert.match(await expected.first().innerText(), /149 \/ 151/);
      }
      const markets = page.locator("#n164-market-results");
      await markets.locator("summary").click();
      const paired = markets.locator("tbody tr");
      assert.equal(await paired.count(), 4);
      for (const [i, venue, graded] of [[0, "DraftKings", 148], [1, "Kalshi", 141], [2, "Polymarket", 139], [3, "Polymarket US", 69]]) {
        const row = paired.nth(i);
        assert.equal(await row.locator("th").innerText(), venue);
        assert.equal(await row.locator("td").last().innerText(), `${graded} / 151`);
      }
      await noOverflow();
    });
    await check(`${width}px: model clocks and latest-fit negative finding`, async () => {
      await count("#performance-grid .performance-card", data.performance.length);
      await page.locator("#performance-horizon").selectOption("T120");
      await count("#performance-grid .performance-card", 7);
      await page.locator("#performance-horizon").selectOption("T60");
      await count("#performance-grid .performance-card", data.performance.filter(p => p.horizon === "T60").length);
      assert.match(await text("#newest-summary"), /216/);
      assert.match(await text("#newest-summary"), /0\s+of 14 comparisons improved/);
      for (const horizon of ["60", "120"]) {
        await page.locator("#newest-horizon").selectOption(horizon);
        await count("#newest-table tbody tr", 7);
      }
      await noOverflow();
    });
    await go("?view=cards&type=games&clock=T120&page=1");
    await check(`${width}px: four forecast cards and two Circa cards retain direct-link pagination`, async () => {
      assert(await page.locator("#cards-prev").isDisabled());
      for (let number = 1; number <= 4; number++) {
        assert.equal(await text("#cards-page-label"), `${number} / 4`);
        await count("#phone-sheet .phone-game", 3);
        assert.equal(new URL(page.url()).searchParams.get("page"), String(number));
        assert.equal(new URL(page.url()).searchParams.get("clock"), "T120");
        assert.match(await text("#phone-sheet .phone-footer"), /Snapshot Nov 16/);
        await noOverflow();
        if (width === 390) await page.locator("#phone-sheet").screenshot({ path: path.join(output, `forecast-card-${number}.png`) });
        if (number < 4) await page.locator("#cards-next").click();
      }
      assert(await page.locator("#cards-next").isDisabled());
      await page.locator('[data-card-type="circa"]').click();
      assert(await page.locator("#cards-prev").isDisabled());
      for (let number = 1; number <= 2; number++) {
        assert.equal(await text("#cards-page-label"), `${number} / 2`);
        await count("#phone-sheet .phone-circa-game", 6);
        await count("#phone-sheet .phone-circa-side", 12);
        assert.equal(new URL(page.url()).searchParams.get("type"), "circa");
        assert.match(await text("#phone-sheet .phone-footer"), /Nov 16 distribution.*official Week 11 lines/);
        await noOverflow();
        if (width === 390) await page.locator("#phone-sheet").screenshot({ path: path.join(output, `circa-card-${number}.png`) });
        if (number < 2) await page.locator("#cards-next").click();
      }
      assert(await page.locator("#cards-next").isDisabled());
      await go("?view=cards&type=games&clock=T60&page=4");
      assert.equal(await text("#cards-page-label"), "4 / 4");
      const values = await page.locator("#phone-sheet .phone-metrics strong").allTextContents();
      assert.equal(values.length, 9);
      assert(values.every(value => value.trim() === "—"));
    });
    await context.close();
  }
  assert.deepEqual(report.page_errors, [], "Uncaught page errors on the published dashboard");
  assert(!report.console_errors.some(e => e.text.includes("NFL dashboard:")), "The published data loader failed");
  report.status = "PASS";
})().catch(error => {
  report.status = "FAIL";
  report.error = error.stack || String(error);
  process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  report.checked_at = new Date().toISOString();
  save();
  console.log(JSON.stringify(report));
});

