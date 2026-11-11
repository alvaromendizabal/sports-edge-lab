/* Hosted offline browser regression for sanitized, actually issued NBA views.
 * Run in the authorized GitHub Actions browser job, not as a workaround for a
 * local browser access restriction. No private report or model source is read.
 */
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || "playwright");

(async () => {
  const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || "nba-publication-browser-artifacts");
  fs.mkdirSync(output, { recursive: true });
  const jsonPath = path.join(__dirname, "latest_research_outputs.json");
  const htmlPath = path.join(__dirname, "latest_research_outputs.html");
  const jsonBytes = fs.readFileSync(jsonPath);
  const data = JSON.parse(jsonBytes);
  const url = pathToFileURL(htmlPath).href;
  assert.equal(data.schema, "sports-edge-lab-nba-public-selected-research-outputs-v2");
  const checks = [];
  const errors = [];
  let remoteRequests = 0;
  const started = new Date().toISOString();
  const browser = await chromium.launch({ headless: true });
  const contexts = [];
  const snapshots = [];
  async function context(viewport) {
    const value = await browser.newContext({ viewport, reducedMotion: "reduce" });
    await value.route(/^https?:\/\//, async route => { remoteRequests += 1; await route.abort(); });
    contexts.push(value);
    return value;
  }
  async function pageFor(owner) {
    const page = await owner.newPage();
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(url, { waitUntil: "load" });
    await page.waitForFunction(() => window.NBA_RENDER_STATE && window.NBA_PUBLIC_REPORT);
    return page;
  }
  function matching({ target = "winner", metric = "log_loss", horizon = "all", date = "all", team = "", availability = "all" } = {}) {
    return data.role_views.filter(view => {
      const role = data.champions[view.champion_role];
      const game = data.games[view.game_id];
      return role.target === target && role.selected_metric === metric &&
        (horizon === "all" || String(role.horizon_minutes) === String(horizon)) &&
        (date === "all" || game.scheduled_start_utc.startsWith(date)) &&
        (!team || [game.home_team, game.away_team, game.home_team_name, game.away_team_name].join(" ").toLowerCase().includes(team.toLowerCase())) &&
        (availability === "all" || (availability === "yes") === Boolean(view.current_issue_ref));
    });
  }
  async function select(page, filter = {}) {
    await page.selectOption("#target", filter.target || "winner");
    await page.selectOption("#metric", filter.metric || (filter.target && filter.target !== "winner" ? "mae" : "log_loss"));
    await page.selectOption("#horizon", String(filter.horizon || "all"));
    await page.selectOption("#date", filter.date || "all");
    await page.fill("#team", filter.team || "");
    await page.selectOption("#availability", filter.availability || "all");
  }
  async function checkRows(page, filter, name) {
    const expected = matching(filter);
    const state = await page.evaluate(() => window.NBA_RENDER_STATE);
    assert.equal(state.filtered_rows, expected.length, name + ": filtered denominator");
    assert.equal(state.visible_rows, Math.min(50, expected.length), name + ": first page count");
    assert.equal(await page.locator("#forecast-rows tr").count(), Math.min(50, expected.length), name + ": rendered rows");
    assert.match(await page.locator("#denominator").innerText(), new RegExp("of " + expected.length + " matching role views"));
    snapshots.push({ check: name, expected_role_views: expected.length, visible_rows: state.visible_rows });
    checks.push(name);
    return expected;
  }
  try {
    const desktop = await context({ width: 1366, height: 1000 });
    const page = await pageFor(desktop);
    assert.equal(await page.locator("h1").isVisible(), true);
    assert.match(await page.locator("h1").innerText(), /Latest available issued forecasts/);
    assert.equal(await page.locator("#cards .card").count(), 4);
    for (const id of ["target", "metric", "horizon", "date", "team", "availability"]) {
      assert.equal(await page.locator("#" + id).isVisible(), true, "Visible control: " + id);
      assert.equal(await page.locator("#" + id).evaluate(element => Boolean(element.closest("label")?.textContent.trim())), true);
    }
    assert.deepEqual(await page.evaluate(() => window.NBA_PUBLIC_REPORT), data);
    checks.push("embedded_public_data_exactly_matches_adjacent_json");
    const state = await page.evaluate(() => window.NBA_RENDER_STATE);
    assert.equal(state.total_role_views, data.coverage.selected_champion_role_views);
    assert.equal(state.champion_rows, data.coverage.active_research_champion_roles);
    assert.equal(await page.locator("#champion-rows tr").count(), Object.keys(data.champions).length);
    assert.equal(Object.keys(data.champions).length, data.coverage.active_research_champion_roles);
    assert.equal(Object.keys(data.games).length, data.coverage.distinct_observed_games);
    checks.push("all_champion_roles_and_issued_game_denominators_render");
    await checkRows(page, {}, "desktop_default_winner_log_loss_cohort");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    await page.screenshot({ path: path.join(output, "nba-publication-desktop.png"), fullPage: true });
    checks.push("desktop_render_without_page_horizontal_overflow");

    // Pagination is exercised against actual source row counts, not a fixed
    // historical snapshot count that could become stale on the next owner run.
    if (matching().length > 50) {
      await page.click("#next");
      assert.match(await page.locator("#page").innerText(), /^Page 2 of /);
      assert.equal(await page.locator("#forecast-rows tr").count(), Math.min(50, matching().length - 50));
      await page.click("#prev");
      assert.match(await page.locator("#page").innerText(), /^Page 1 of /);
      checks.push("actual_pagination_next_and_previous");
    }
    for (const filter of [
      { target: "winner", metric: "accuracy", horizon: "60" },
      { target: "margin", metric: "mae", horizon: "120" },
      { target: "total", metric: "rmse", horizon: "all" },
    ]) {
      await select(page, filter);
      await checkRows(page, filter, "target_metric_horizon_" + filter.target + "_" + filter.metric);
    }
    const first = data.role_views[0];
    if (first) {
      const game = data.games[first.game_id], role = data.champions[first.champion_role];
      const filter = { target: role.target, metric: role.selected_metric, horizon: String(role.horizon_minutes),
        date: game.scheduled_start_utc.slice(0, 10), team: game.home_team };
      await select(page, filter);
      await checkRows(page, filter, "date_and_team_controls_use_actual_observed_inventory");
      assert.ok((await page.locator("#forecast-rows").innerText()).includes(game.home_team));
    }
    const missing = data.role_views.find(view => view.current_issue_ref === null);
    if (missing) {
      const role = data.champions[missing.champion_role];
      const filter = { target: role.target, metric: role.selected_metric, availability: "no" };
      await select(page, filter);
      const expected = await checkRows(page, filter, "missing_current_champion_filter_keeps_explicit_gaps");
      assert.ok(expected.length > 0);
      for (const text of await page.locator("#forecast-rows tr td:nth-child(3)").allTextContents()) {
        assert.match(text, /No original issue/);
      }
    }
    const present = data.role_views.find(view => view.current_issue_ref !== null);
    if (present) {
      const role = data.champions[present.champion_role];
      const filter = { target: role.target, metric: role.selected_metric, availability: "yes" };
      await select(page, filter);
      await checkRows(page, filter, "available_current_champion_filter");
      assert.equal(await page.locator("#forecast-rows tr td:nth-child(3) .missing").count(), 0);
    }
    await select(page, { team: "NO_MATCH_TEAM_000" });
    await checkRows(page, { team: "NO_MATCH_TEAM_000" }, "empty_filter_is_explicit_and_noncrashing");
    assert.equal(await page.locator("#next").isDisabled(), true);
    assert.equal(await page.locator("#prev").isDisabled(), true);
    assert.match(await page.locator("#page").innerText(), /^Page 1 of 1$/);

    const mobile = await context({ width: 390, height: 844 });
    const small = await pageFor(mobile);
    await checkRows(small, {}, "mobile_default_rows_render");
    assert.equal(await small.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    assert.equal(await small.locator("#champion-rows tr").count(), data.coverage.active_research_champion_roles);
    await small.screenshot({ path: path.join(output, "nba-publication-mobile.png"), fullPage: true });
    await select(small, { target: "total", metric: "mae", horizon: "60" });
    await checkRows(small, { target: "total", metric: "mae", horizon: "60" }, "mobile_actual_target_metric_horizon_controls");
    checks.push("mobile_390px_render_without_page_horizontal_overflow");

    // Reopen in a fresh context: the page must reconstruct its view entirely
    // from the saved artifact, without prior tab state or external resources.
    const reopened = await context({ width: 1366, height: 1000 });
    const again = await pageFor(reopened);
    assert.deepEqual(await again.evaluate(() => window.NBA_PUBLIC_REPORT), data);
    await checkRows(again, {}, "fresh_context_reopen_restores_complete_snapshot");
    assert.equal(await again.locator("#target").inputValue(), "winner");
    assert.equal(await again.locator("#metric").inputValue(), "log_loss");
    assert.equal(await again.locator("#champion-rows tr").count(), data.coverage.active_research_champion_roles);
    assert.deepEqual(errors, []);
    assert.equal(remoteRequests, 0);
    checks.push("no_javascript_page_errors", "zero_remote_page_requests");
    const result = { status: "PASS", scope: "Sanitized public outputs only; hosted browser checks, no NBA fitting or rescoring",
      browser_version: await browser.version(), started_at_utc: started, finished_at_utc: new Date().toISOString(),
      source_json_sha256: crypto.createHash("sha256").update(jsonBytes).digest("hex"),
      source_html_sha256: crypto.createHash("sha256").update(fs.readFileSync(htmlPath)).digest("hex"),
      evidence_as_of_utc: data.evidence_as_of_utc, coverage: data.coverage, checks, rendered_cases: snapshots,
      remote_page_requests: remoteRequests, external_accessibility_audit: false, cross_browser_coverage: false,
      screenshots: ["nba-publication-desktop.png", "nba-publication-mobile.png"] };
    fs.writeFileSync(path.join(output, "nba-publication-browser-result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    fs.writeFileSync(path.join(output, "nba-publication-browser-result.json"), JSON.stringify({
      status: "FAIL", started_at_utc: started, finished_at_utc: new Date().toISOString(),
      checks_completed: checks, error: error.message, page_errors: errors, remote_page_requests: remoteRequests,
    }, null, 2) + "\n");
    throw error;
  } finally {
    for (const value of contexts) await value.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
