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
const report = { status: "RUNNING", method: "Anonymous deployed asset hashes and live Chromium interactions", checks: [], assets: [], viewports: [1440, 390], page_errors: [], console_errors: [] };
const digest = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const check = async (name, action) => { await action(); report.checks.push(name); };
const save = () => fs.writeFileSync(path.join(output, "live-browser.json"), JSON.stringify(report, null, 2) + "\n");
let browser;

(async () => {
  const receipt = JSON.parse(fs.readFileSync(path.join(root, "publication.json"), "utf8"));
  const data = JSON.parse(fs.readFileSync(path.join(root, "data.json"), "utf8"));
  const base = new URL(receipt.public_url);
  assert.equal(base.protocol, "https:");
  assert(base.hostname.endsWith(".alv-mendizabal.chatgpt.site"), "Publication must use the owner's public Site origin");
  assert(!base.username && !base.password && !base.search && !base.hash);
  assert.match(receipt.status, /^DEPLOYED/);
  assert.equal(receipt.verification.all_match, true);
  assert.equal(data.games.length, 12, "This Week 11 publication contains twelve remaining games");
  report.url = base.href;
  report.application_source_commit = receipt.github_application_source_commit;
  report.workflow_commit = process.env.GITHUB_SHA || null;
  report.pr_head = process.env.NFL_CURRENT_PR_HEAD || null;
  browser = await chromium.launch({ headless: true });
  const assetContext = await browser.newContext();
  const requiredAssets = ["index.html", "app.js", "styles.css", "data.json", "evidence.json", "circa_evidence.json", "newest_model_comparison.json"];
  await check("Seven deployed assets exactly match the committed publication and application bytes", async () => {
    assert.deepEqual(receipt.verification.assets.map(a => a.path).sort(), [...requiredAssets].sort());
    for (const asset of receipt.verification.assets) {
      assert.equal(asset.status, 200);
      assert.equal(asset.matches_pushed_source, true);
      const local = fs.readFileSync(path.join(root, asset.path));
      assert.equal(digest(local), asset.sha256, `${asset.path}: committed source differs from publication receipt`);
      assert.equal(local.length, asset.bytes);
      const url = new URL(asset.path === "index.html" ? "./" : asset.path, base);
      const response = await assetContext.request.get(url.href, { timeout: 30000 });
      const bytes = await response.body();
      const observed = { path: asset.path, url: response.url(), status: response.status(), bytes: bytes.length, sha256: digest(bytes) };
      report.assets.push(observed);
      assert.equal(response.status(), 200, `${asset.path}: live HTTP status`);
      assert.equal(new URL(response.url()).origin, base.origin, "Unexpected origin redirect");
      assert.equal(observed.sha256, asset.sha256, `${asset.path}: deployed bytes differ`);
      assert.equal(observed.bytes, asset.bytes);
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
    const go = async query => {
      const response = await page.goto(new URL(query, base).href, { waitUntil: "domcontentloaded" });
      assert.equal(response.status(), 200);
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
