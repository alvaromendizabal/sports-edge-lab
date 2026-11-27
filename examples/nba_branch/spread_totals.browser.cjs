/* Hosted offline browser checks for the public, dated NBA projection. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || "playwright");

(async () => {
  const root = path.resolve(__dirname, "../..");
  const board = JSON.parse(fs.readFileSync(path.join(root, "tracks/nba/current/board.json"), "utf8"));
  const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || "nba-spread-totals-browser-artifacts");
  fs.mkdirSync(output, { recursive: true });
  const url = pathToFileURL(path.join(root, "docs/nba/spread-totals/index.html")).href;
  const week = board.games.filter(game => game.in_week);
  const upcoming = week.filter(game => !(game.calendar_observation || game).completed);
  const observations = board.observed_contracts || [];
  const quoteGame = upcoming.find(game => observations.some(row => row.game_id === game.game_id));
  assert.ok(quoteGame, "A current public observation is required for the contract-card regression");
  const quotes = observations.filter(row => row.game_id === quoteGame.game_id);
  const browser = await chromium.launch({ headless: true });
  const checks = [];
  const errors = [];
  let remoteRequests = 0;
  try {
    const context = await browser.newContext({ viewport: { width: 1366, height: 1000 }, reducedMotion: "reduce" });
    await context.route(/^https?:\/\//, async route => { remoteRequests += 1; await route.abort(); });
    const page = await context.newPage();
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(url);
    assert.equal(await page.locator("#games .game").count(), upcoming.length);
    assert.equal(await page.locator("#stat-contracts").innerText(), String(observations.length));
    assert.equal(await page.locator(".contract-observations").count(), new Set(observations.map(row => row.game_id)).size);
    assert.match(await page.locator("#market-snapshot-summary").innerText(), /NO ask quantities remain unavailable/);
    checks.push("all_nonfinal_week_games_and_separate_current_contract_census");

    for (const game of upcoming) {
      const role = game.horizons["120"].winner;
      if (!Number.isFinite(role.value)) continue;
      const favorite = role.value >= 0.5 ? game.home_abbr : game.away_abbr;
      const probability = (Math.max(role.value, 1 - role.value) * 100).toFixed(1);
      const card = page.locator(`[data-game-id="${game.game_id}"]`);
      assert.match(await card.locator(".forecast > div").first().innerText(), new RegExp(`${favorite} ${probability.replace(".", "\\.")}%`));
      assert.match(await card.locator(".forecast > div").first().innerText(), /Stale saved outlook/);
    }
    checks.push("P_home_orientation_and_saved_issue_freshness_for_each_displayed_winner");

    const observedCard = page.locator(`[data-game-id="${quoteGame.game_id}"]`);
    const disclosure = observedCard.locator(".contract-observations");
    assert.equal(await disclosure.locator(".contract-item").count(), 0);
    await disclosure.locator(":scope > summary").click();
    await page.waitForFunction(id => document.querySelector(`[data-contract-game="${id}"]`).dataset.loaded === "true", quoteGame.game_id);
    assert.equal(await disclosure.locator(".contract-item").count(), quotes.length);
    const first = disclosure.locator(".contract-item").first();
    const firstSpread = quotes.find(row => row.market_kind === "spread");
    assert.equal(await first.locator("h4").textContent(), firstSpread.proposition);
    assert.equal(await first.locator("time").getAttribute("datetime"), firstSpread.observed_at_utc);
    assert.match(await first.locator(".quote-grid > div").nth(1).textContent(), /Quantity unavailable/);
    assert.match(await first.locator(".quote-unavailable").textContent(), /Chosen YES\/NO side and probability: unavailable/);
    assert.match(await first.locator(".quote-unavailable").textContent(), /Current execution size is unqualified/);
    assert.match(await disclosure.locator(".contract-content > p").textContent(), /no executable NO fill is established/);
    assert.match(await page.locator("#contracts").innerText(), /fee-adjusted returns are unavailable/);
    checks.push("all_exact_alternatives_lazy_rendered_with_capture_clock_missing_size_and_unavailable_model_side");

    assert.match(await observedCard.locator(".forecast > div").nth(2).innerText(), /Issued Nov 19/);
    await page.locator('[data-horizon="60"]').click();
    assert.match(await page.locator(`[data-game-id="${quoteGame.game_id}"] .forecast > div`).nth(2).innerText(), /Issued Nov 24/);
    const missing = upcoming.find(game => game.horizons["60"].total.value === null);
    assert.ok(missing, "The named missing-total fixture must remain visible");
    assert.match(await page.locator(`[data-game-id="${missing.game_id}"] .forecast > div`).nth(2).innerText(), /Unavailable/);
    await page.locator('[data-horizon="120"]').click();
    checks.push("distinct_T60_T120_total_issue_clocks_and_missing_total_retained");

    await page.selectOption("#window", "week");
    assert.equal(await page.locator("#games .game").count(), week.length);
    await page.selectOption("#window", "all");
    assert.equal(await page.locator("#games .game").count(), board.games.length);
    await page.selectOption("#window", "week_upcoming");
    await page.locator("#team-search").fill(quoteGame.home_abbr);
    assert.equal(await page.locator("#games .game").count(), upcoming.filter(game => [game.home, game.away, game.home_abbr, game.away_abbr, game.pacific_date].join(" ").toLowerCase().includes(quoteGame.home_abbr.toLowerCase())).length);
    await page.locator("#team-search").fill("");
    checks.push("week_season_and_team_controls_keep_full_observed_population");

    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.locator("#slate").scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(output, "nba-spread-totals-desktop.png") });
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(url);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const mobileDisclosure = page.locator(`[data-game-id="${quoteGame.game_id}"] .contract-observations`);
    await mobileDisclosure.locator(":scope > summary").click();
    await mobileDisclosure.locator(".contract-content > details > summary").first().click();
    await mobileDisclosure.locator(".contract-item").first().scrollIntoViewIfNeeded();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(output, "nba-spread-totals-mobile-contract.png") });
    checks.push("desktop_and_375px_mobile_contract_cards_do_not_overflow");

    assert.deepEqual(errors, []);
    assert.equal(remoteRequests, 0);
    checks.push("no_page_errors_or_remote_provider_requests");
    const result = { status: "PASS", browser_version: await browser.version(), checks,
      displayed_upcoming_games: upcoming.length, full_week_games: week.length,
      full_observed_season_games: board.games.length, captured_contracts: observations.length,
      remote_page_requests: remoteRequests, new_model_fits: 0,
      screenshots: ["nba-spread-totals-desktop.png", "nba-spread-totals-mobile-contract.png"] };
    fs.writeFileSync(path.join(output, "nba-spread-totals-browser-result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
    await context.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
