/* Hosted Playwright acceptance for the source-separated saved NBA schedule, schema v4.
 * Run only in the authorized GitHub Actions browser job using its pinned
 * Playwright installation. No local browser launch, NBA fit, or rescoring is
 * part of preparation. --data-only runs the independent JSON census without
 * importing Playwright or touching any browser API. The oracle below never
 * calls the page's expandedRows.
 */
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const METRICS = {
  winner: ["log_loss", "accuracy", "brier"],
  margin: ["mae", "rmse", "crps", "weighted_interval_score"],
  total: ["mae", "rmse", "crps", "weighted_interval_score"],
};
const CONTROLS = ["game-status", "phase", "target", "metric", "horizon", "date", "team", "availability", "issue-class"];
const PAGE_SIZE = 50;
const normalized = value => String(value ?? "").replace(/\s+/g, " ").trim();
const words = value => String(value ?? "Unavailable").split("_").join(" ");
function timestamp(value) {
  if (!value) return "Unavailable";
  const parsed = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:Z|\+00:00)$/.exec(value);
  assert.ok(parsed, "The public clock must retain an explicit UTC offset: " + value);
  return parsed[1] + " " + parsed[2] + " UTC";
}
const sorted = values => [...values].sort();
const sha256 = bytes => crypto.createHash("sha256").update(bytes).digest("hex");

function referenceInventory(data) {
  // Build the full six-cell coverage grid first, then associate registered
  // metric roles and sparse original issues. The UI instead expands games for
  // a selected role. Independent census checks make omitted games detectable.
  const gameIds = Object.keys(data.games);
  assert.deepEqual(sorted(Object.keys(data.game_coverage)), sorted(gameIds));
  assert.equal(gameIds.length, data.coverage.distinct_observed_games);
  const official = gameIds.filter(id => data.games[id].schedule_membership === "CANONICAL_OFFICIAL");
  assert.equal(official.length, data.coverage.official_schedule_games);
  assert.equal(Object.keys(data.champions).length, data.coverage.active_research_champion_roles);
  assert.equal(data.role_views.length, data.coverage.selected_champion_role_views);
  assert.equal(Object.keys(data.issues).length, data.coverage.distinct_public_selected_issues);
  assert.equal(Object.values(data.issues).filter(issue => issue.prediction_intervals).length,
    data.coverage.distinct_public_selected_issues_with_intervals);

  const views = new Map();
  const referencedIssues = new Set();
  for (const view of data.role_views) {
    const identity = view.game_id + "|" + view.champion_role;
    assert.equal(views.has(identity), false, "Duplicate saved role view: " + identity);
    assert.ok(data.games[view.game_id], "An original issue game disappeared: " + identity);
    const role = data.champions[view.champion_role];
    assert.ok(role, "Unknown saved champion role: " + identity);
    views.set(identity, view);
    for (const ref of [view.current_issue_ref, view.at_issue_ref].filter(Boolean)) {
      const issue = data.issues[ref];
      assert.ok(issue, "Missing immutable issued body: " + ref);
      assert.equal(issue.game_id, view.game_id);
      assert.equal(issue.target, role.target);
      assert.equal(issue.horizon_minutes, role.horizon_minutes);
      assert.equal(issue.original_pregame_issue, true);
      referencedIssues.add(ref);
    }
  }
  assert.deepEqual(sorted(referencedIssues), sorted(Object.keys(data.issues)), "No selected issue is orphaned");

  const statusGames = Object.fromEntries(["all", "upcoming", "completed", "unresolved", "pending"].map(key => [key, new Set()]));
  const gameFacts = new Map();
  for (const id of gameIds) {
    const game = data.games[id];
    statusGames.all.add(id);
    // The schedule fields retain their original source clock/status. The
    // optional final-result layer has an independent authenticated clock.
    const result = game.result_observation;
    const expectedStatus = result ? "FINAL" : game.source_status;
    assert.equal(game.last_confirmed_status, expectedStatus);
    assert.equal(game.last_confirmed_status_source, result ? "SAVED_RESULT_OBSERVATION" : "SAVED_SCHEDULE_OBSERVATION");
    assert.equal(game.last_confirmed_status_asof_utc, result ? result.observed_at_utc : game.schedule_source_asof_utc);
    if (game.schedule_membership === "CANONICAL_OFFICIAL") {
      assert.equal(game.official_status_at_source, game.source_status);
      assert.ok(Date.parse(game.schedule_source_asof_utc) <= Date.parse(data.schedule_observation.snapshot_finished_at_utc));
    }
    if (result) {
      assert.equal(result.status, "FINAL");
      assert.equal(result.original_historical_possession_claim, false);
      assert.equal(result.new_score_calculation, false);
      assert.ok(Number.isInteger(result.home_points) && result.home_points >= 0);
      assert.ok(Number.isInteger(result.away_points) && result.away_points >= 0);
      assert.ok(Date.parse(result.observed_at_utc) <= Date.parse(result.available_at_utc));
      assert.ok(Date.parse(result.available_at_utc) <= Date.parse(data.evidence_as_of_utc));
      if (result.ended_at_utc !== null) assert.ok(Date.parse(result.ended_at_utc) <= Date.parse(result.observed_at_utc));
    }

    if (game.last_confirmed_status === "FINAL") statusGames.completed.add(id);
    if (game.tip_time_relation_at_report === "FUTURE_TIP" && !new Set(["FINAL", "CANCELLED"]).has(game.last_confirmed_status)) statusGames.upcoming.add(id);
    if (game.identity_status !== "RESOLVED_MATCHUP") statusGames.unresolved.add(id);
    if (game.last_confirmed_status === "SCHEDULED" && game.tip_time_relation_at_report === "START_TIME_PASSED_STATUS_NOT_INFERRED") statusGames.pending.add(id);
    gameFacts.set(id, {
      date: game.scheduled_start_utc ? game.scheduled_start_utc.substring(0, 10) : "unknown",
      timestamp: game.scheduled_start_utc ? Date.parse(game.scheduled_start_utc) : Infinity,
      teamText: [game.home_team, game.away_team, game.home_team_name, game.away_team_name].filter(Boolean).join(" ").toLowerCase(),
    });
  }
  assert.equal(official.filter(id => statusGames.unresolved.has(id)).length, data.coverage.official_unresolved_matchups);
  assert.equal(official.filter(id => data.games[id].source_status === "SCHEDULED" && data.games[id].tip_time_relation_at_report === "START_TIME_PASSED_STATUS_NOT_INFERRED").length, data.coverage.official_scheduled_start_passed_without_final_observation);
  assert.equal(official.filter(id => data.games[id].tip_time_relation_at_report === "FUTURE_TIP").length, data.coverage.official_future_tips_at_report);
  assert.equal(official.filter(id => !data.games[id].original_issue_inventory_present).length, data.coverage.official_games_without_original_issues);
  for (const [phase, count] of Object.entries(data.coverage.official_games_by_phase)) {
    assert.equal(official.filter(id => data.games[id].phase === phase).length, count);
  }
  for (const [status, count] of Object.entries(data.coverage.official_games_by_saved_status)) {
    assert.equal(official.filter(id => data.games[id].source_status === status).length, count);
  }

  const latestCounts = {};
  for (const id of official) {
    const status = data.games[id].last_confirmed_status;
    latestCounts[status] = (latestCounts[status] || 0) + 1;
  }
  assert.deepEqual(latestCounts, data.coverage.official_games_by_latest_row_backed_status);
  const recovery = data.result_observation_recovery;
  const aggregate = recovery.source_reported_status_counts;
  const differences = {};
  if (aggregate) {
    assert.equal(Object.values(aggregate).reduce((a, b) => a + b, 0), recovery.source_reported_official_games);
    for (const key of new Set([...Object.keys(latestCounts), ...Object.keys(aggregate)])) {
      if ((latestCounts[key] || 0) !== (aggregate[key] || 0)) differences[key] = { row_backed: latestCounts[key] || 0, source_aggregate: aggregate[key] || 0 };
    }
  }
  assert.deepEqual(differences, data.coverage.latest_row_and_source_aggregate_difference);
  if (recovery.status !== "NO_SEPARATE_RESULT_OVERLAY_SUPPLIED") {
    assert.equal(recovery.full_B074_schedule_projection_reconstructed, false);
    assert.equal(recovery.source_clock_rewritten, false);
    assert.equal(recovery.original_forecast_values_or_clocks_changed, false);
    assert.equal(recovery.result_rows_attached, official.filter(id => data.games[id].result_observation).length);
    assert.deepEqual(sorted(recovery.newly_confirmed_final_game_ids), sorted(official.filter(id => data.games[id].result_observation && data.games[id].source_status !== "FINAL")));
  }

  let cellCount = 0;
  let opportunityCount = 0;
  let currentAvailable = 0;
  const cells = new Set();
  const rows = [];
  for (const [gameId, coverage] of Object.entries(data.game_coverage)) {
    const aliases = data.role_groups[coverage.applicable_role_group];
    assert.ok(Array.isArray(aliases), "Unknown compact role group: " + gameId);
    assert.equal(new Set(aliases).size, aliases.length);
    const availableRoles = aliases.filter(id => views.get(gameId + "|" + id)?.current_issue_ref);
    const atIssueRoles = aliases.filter(id => views.get(gameId + "|" + id)?.at_issue_ref);
    assert.ok(Array.isArray(coverage.current_role_ids_available));
    assert.ok(Array.isArray(coverage.at_issue_role_ids_available));
    assert.deepEqual(sorted(coverage.current_role_ids_available), sorted(availableRoles));
    assert.deepEqual(sorted(coverage.at_issue_role_ids_available), sorted(atIssueRoles));
    let declaredMissing = coverage.current_role_ids_missing;
    if (declaredMissing === "ALL_APPLICABLE_ROLES") {
      assert.equal(coverage.current_role_ids_available.length, 0,
        "ALL_APPLICABLE_ROLES contradicts a declared available issue: " + gameId);
      assert.equal(availableRoles.length, 0,
        "ALL_APPLICABLE_ROLES contradicts an authenticated saved issue: " + gameId);
      declaredMissing = aliases;
    } else {
      assert.ok(Array.isArray(declaredMissing), "Unknown compact missing-role representation: " + gameId);
    }
    assert.deepEqual(sorted(declaredMissing), sorted(aliases.filter(id => !availableRoles.includes(id))));
    opportunityCount += aliases.length;
    currentAvailable += availableRoles.length;
    assert.deepEqual(sorted(Object.keys(coverage.target_horizon)), sorted(
      Object.keys(METRICS).flatMap(target => [target + "_T60", target + "_T120"])));
    for (const [cellName, cell] of Object.entries(coverage.target_horizon)) {
      const match = /^(winner|margin|total)_T(60|120)$/.exec(cellName);
      assert.ok(match, "Unexpected target/horizon cell: " + cellName);
      const target = match[1], horizon = Number(match[2]);
      const cellRoles = aliases.filter(id => {
        const role = data.champions[id];
        assert.ok(role, "Unknown role group member: " + id);
        return role.target === target && role.horizon_minutes === horizon;
      });
      assert.equal(cell.expected_roles, cellRoles.length);
      assert.equal(cell.current_roles_available, cellRoles.filter(id => availableRoles.includes(id)).length);
      assert.equal(cell.at_issue_roles_available, cellRoles.filter(id => atIssueRoles.includes(id)).length);
      assert.ok(data.gap_reason_definitions[cell.status], "Undocumented coverage status: " + cell.status);
      cellCount += 1;
      cells.add(gameId + "|" + target + "|" + horizon);
      for (const metric of METRICS[target]) {
        const metricRoles = cellRoles.filter(id => data.champions[id].selected_metric === metric);
        assert.ok(metricRoles.length <= 1, "Metric-specific champion role is ambiguous");
        const roleId = metricRoles[0] || null;
        const view = roleId ? views.get(gameId + "|" + roleId) || null : null;
        const current = view?.current_issue_ref ? data.issues[view.current_issue_ref] : null;
        const atIssue = view?.at_issue_ref ? data.issues[view.at_issue_ref] : null;
        const clock = current || atIssue;
        rows.push({ gameId, game: data.games[gameId], facts: gameFacts.get(gameId), target, horizon, metric,
          roleId, role: roleId ? data.champions[roleId] : null, view, current, atIssue, clock,
          timingClass: clock ? clock.issue_horizon_class : "missing",
          gap: current ? null : !roleId ? "NO_ACTIVE_CHAMPION_FOR_TARGET_HORIZON" : view?.current_forecast_status || cell.status });
      }
    }
  }
  assert.equal(cellCount, data.coverage.all_game_target_horizon_cells);
  assert.equal(opportunityCount, data.coverage.all_game_applicable_role_opportunities);
  assert.equal(currentAvailable, data.coverage.all_game_current_role_forecasts_available);
  assert.equal(opportunityCount - currentAvailable, data.coverage.all_game_current_role_forecasts_missing);
  rows.sort((left, right) => (left.facts.timestamp - right.facts.timestamp || 0) ||
    left.gameId.localeCompare(right.gameId) || left.horizon - right.horizon ||
    String(left.roleId || "").localeCompare(String(right.roleId || "")));
  return { rows, cells, views, statusGames, gameIds, official,
    dates: sorted(new Set([...gameFacts.values()].map(value => value.date).filter(value => value !== "unknown"))) };
}

function criteria(overrides = {}) {
  const target = overrides.target || "winner";
  return { status: "all", phase: "all", target, metric: METRICS[target][0], horizon: "all", date: "all",
    team: "", availability: "all", issueClass: "all", ...overrides };
}
function matching(reference, input = {}) {
  const query = criteria(input);
  const allowedGames = reference.statusGames[query.status];
  assert.ok(allowedGames, "Unknown status query");
  const team = query.team.trim().toLowerCase();
  return reference.rows.filter(row => row.target === query.target && row.metric === query.metric &&
    allowedGames.has(row.gameId) && (query.phase === "all" || row.game.phase === query.phase) &&
    (query.horizon === "all" || row.horizon === Number(query.horizon)) &&
    (query.date === "all" || row.facts.date === query.date) && (!team || row.facts.teamText.includes(team)) &&
    (query.availability === "all" || Boolean(row.current) === (query.availability === "yes")) &&
    (query.issueClass === "all" || row.timingClass === query.issueClass));
}
function issueText(issue, target, current) {
  if (!issue) return "No original issue";
  const prediction = target === "winner" ? (issue.prediction * 100).toFixed(2) + "% home" : issue.prediction.toFixed(2) + " points";
  const parts = [prediction, issue.champion_at_issue_family,
    words(issue.issue_horizon_class) + " · " + (current ? "current champion" : "earlier champion"),
    "Issued " + timestamp(issue.issued_at_utc)];
  for (const [level, endpoints] of Object.entries(issue.prediction_intervals || {})) {
    parts.push(level + "% issued interval: " + endpoints[0].toFixed(2) + " to " + endpoints[1].toFixed(2) + " points");
  }
  return normalized(parts.join(" "));
}
function expectedRow(row, data) {
  const reason = data.gap_reason_definitions[row.gap] || words(row.gap);
  const clock = row.clock;
  return { gameId: row.gameId, roleId: row.roleId || "none", cells: [
    normalized([(row.game.away_team || "TBD") + " @ " + (row.game.home_team || "TBD"),
      timestamp(row.game.scheduled_start_utc), "NBA game " + row.gameId + " · " + words(row.game.phase),
      words(row.game.last_confirmed_status), ...(row.game.result_observation ? ["Saved final: " + row.game.result_observation.away_points + " – " + row.game.result_observation.home_points + " (away – home)", "Result observed " + timestamp(row.game.result_observation.observed_at_utc)] : []), "Schedule source " + timestamp(row.game.schedule_source_asof_utc)].join(" ")),
    normalized(words(row.metric) + " · T" + row.horizon + " " + (row.role?.family || "No registered role for this phase")),
    normalized(issueText(row.current, row.target, true) + (row.current ? "" : " " + reason)),
    issueText(row.atIssue, row.target, Boolean(row.view?.at_issue_matches_current_champion)),
    normalized("Forecast source " + timestamp(clock?.source_asof_utc) +
      " Source age at issue " + (clock?.source_age_seconds_at_issue ?? "Unavailable") + (clock ? "s" : "") +
      " Actual lead " + (clock?.actual_lead_minutes ?? "Unavailable") + (clock ? " min" : "")),
  ] };
}

(async () => {
  const started = new Date().toISOString(), startedClock = process.hrtime.bigint();
  const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || "nba-publication-browser-artifacts");
  fs.mkdirSync(output, { recursive: true });
  const jsonPath = path.join(__dirname, "latest_research_outputs.json");
  const htmlPath = path.join(__dirname, "latest_research_outputs.html");
  const jsonBytes = fs.readFileSync(jsonPath), htmlBytes = fs.readFileSync(htmlPath);
  const data = JSON.parse(jsonBytes), url = pathToFileURL(htmlPath).href;
  assert.equal(data.schema, "sports-edge-lab-nba-public-source-separated-research-outputs-v4");
  const reference = referenceInventory(data);
  const b077Review = require('./b077_review.browser.cjs');
  const b077Evidence = b077Review.verify(htmlBytes);
  if (process.argv.includes("--data-only")) {
    const combinations = [];
    const seenViews = new Set(), seenIssues = new Set();
    for (const [target, metrics] of Object.entries(METRICS)) {
      for (const metric of metrics) {
        const expected = matching(reference, { target, metric });
        assert.deepEqual(sorted(new Set(expected.map(row => row.gameId))), sorted(reference.gameIds));
        for (const row of expected) {
          const projected = expectedRow(row, data);
          assert.equal(projected.cells.length, 5);
          assert.ok(projected.cells.every(value => typeof value === "string" && value.length > 0));
          if (row.view) seenViews.add(row.gameId + "|" + row.roleId);
          for (const ref of [row.view?.current_issue_ref, row.view?.at_issue_ref].filter(Boolean)) seenIssues.add(ref);
        }
        combinations.push({ target, metric, expected_rows: expected.length,
          expected_pages: Math.max(1, Math.ceil(expected.length / PAGE_SIZE)) });
      }
    }
    assert.deepEqual(sorted(seenViews), sorted(reference.views.keys()));
    assert.deepEqual(sorted(seenIssues), sorted(Object.keys(data.issues)));
    assert.equal(Object.keys(require.cache).some(name => /(?:^|[\\/])playwright(?:-core)?(?:[\\/]|$)/.test(name)), false);
    const census = { status: "PASS_DATA_ONLY_ORACLE_CENSUS", browser_launched: false, playwright_imported: false,
      scope: "Independent JSON/reference census and expected-cell formatting only; no DOM or browser validation claimed",
      started_at_utc: started, finished_at_utc: new Date().toISOString(),
      elapsed_seconds: Number(process.hrtime.bigint() - startedClock) / 1e9,
      source_json_sha256: sha256(jsonBytes), source_html_sha256: sha256(htmlBytes),
      source_browser_test_sha256: sha256(fs.readFileSync(__filename)),
      observed_games: reference.gameIds.length, official_games: reference.official.length,
      target_horizon_cells: reference.cells.size, sparse_saved_role_views: seenViews.size,
      public_selected_issues: seenIssues.size,
      b077_saved_metrics_and_venue_evidence: b077Evidence,
      compact_all_missing_sentinels_verified: Object.values(data.game_coverage).filter(value => value.current_role_ids_missing === "ALL_APPLICABLE_ROLES").length,
      expected_metric_rows: reference.rows.length,
      expected_browser_pages: combinations.reduce((sum, value) => sum + value.expected_pages, 0),
      status_game_counts: Object.fromEntries(Object.entries(reference.statusGames).map(([key, value]) => [key, value.size])),
      target_metric_combinations: combinations };
    fs.writeFileSync(path.join(output, "nba-publication-data-census.json"), JSON.stringify(census, null, 2) + "\n");
    console.log(JSON.stringify(census, null, 2));
    return;
  }
  // Deliberately delayed: --data-only must work without any Playwright package
  // installed and cannot invoke a local browser as a side effect.
  const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || "playwright");
  const checks = [], snapshots = [], errors = [], consoleErrors = [], remoteRequests = [];
  const contexts = [], screenshots = [];
  const visitedCells = new Set(), visitedViews = new Set(), seenIssues = new Set();
  let exhaustiveRows = 0, exhaustivePages = 0;
  const browser = await chromium.launch({ headless: true });

  async function context(viewport) {
    const value = await browser.newContext({ viewport, reducedMotion: "reduce", serviceWorkers: "block" });
    await value.route(/^https?:\/\//, async route => {
      remoteRequests.push(route.request().url());
      await route.abort();
    });
    contexts.push(value);
    return value;
  }
  async function pageFor(owner) {
    const page = await owner.newPage();
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
    page.on("websocket", socket => remoteRequests.push(socket.url()));
    await page.goto(url, { waitUntil: "load" });
    await page.waitForFunction(() => window.NBA_RENDER_STATE && window.NBA_PUBLIC_REPORT);
    return page;
  }
  async function select(page, filter = {}) {
    const query = criteria(filter);
    await page.selectOption("#game-status", query.status);
    await page.selectOption("#phase", query.phase);
    await page.selectOption("#target", query.target);
    await page.selectOption("#metric", query.metric);
    await page.selectOption("#horizon", String(query.horizon));
    await page.selectOption("#date", query.date);
    await page.fill("#team", query.team);
    await page.selectOption("#availability", query.availability);
    await page.selectOption("#issue-class", query.issueClass);
  }
  async function assertPage(page, expected, pageIndex, name) {
    const slice = expected.slice(pageIndex * PAGE_SIZE, (pageIndex + 1) * PAGE_SIZE);
    const pages = Math.max(1, Math.ceil(expected.length / PAGE_SIZE));
    const gameCount = new Set(expected.map(row => row.gameId)).size;
    const state = await page.evaluate(() => window.NBA_RENDER_STATE);
    assert.equal(state.filtered_rows, expected.length, name + ": complete filtered denominator");
    assert.equal(state.filtered_games, gameCount, name + ": distinct game denominator");
    assert.equal(state.page, pageIndex + 1, name + ": page number");
    assert.equal(state.visible_rows, slice.length);
    assert.equal(state.official_games, data.coverage.official_schedule_games);
    assert.equal(state.total_target_horizon_cells, data.coverage.all_game_target_horizon_cells);
    assert.equal(state.preserved_original_role_views, data.role_views.length);
    assert.deepEqual(state.visible_game_ids, slice.map(row => row.gameId));
    const actual = await page.locator("#forecast-rows tr").evaluateAll(rows => rows.map(row => ({
      gameId: row.dataset.gameId, roleId: row.dataset.role,
      cells: [...row.querySelectorAll(":scope > td")].map(cell => cell.innerText.replace(/\s+/g, " ").trim()),
    })));
    assert.deepEqual(actual, slice.map(row => expectedRow(row, data)), name + ": exact rows, values, original intervals and source/issue clocks");
    const text = await page.locator("#denominator").innerText();
    assert.ok(text.includes("Showing " + slice.length + " of " + expected.length + " matching game/horizon rows across " + gameCount + " games."));
    assert.ok(text.includes(data.coverage.official_schedule_games + " official games; " + data.coverage.all_game_target_horizon_cells + " target/horizon coverage cells."));
    assert.equal(await page.locator("#page").innerText(), "Page " + (pageIndex + 1) + " of " + pages);
    assert.equal(await page.locator("#prev").isDisabled(), pageIndex === 0);
    assert.equal(await page.locator("#next").isDisabled(), pageIndex === pages - 1);
    return slice;
  }
  async function checkFilter(page, filter, name) {
    await select(page, filter);
    const expected = matching(reference, filter);
    await assertPage(page, expected, 0, name);
    snapshots.push({ check: name, filter: criteria(filter), matching_rows: expected.length,
      matching_games: new Set(expected.map(row => row.gameId)).size, checked_pages: 1 });
    checks.push(name);
    return expected;
  }
  async function walkInventory(page, filter, name) {
    await select(page, filter);
    const expected = matching(reference, filter);
    assert.deepEqual(sorted(new Set(expected.map(row => row.gameId))), sorted(reference.gameIds), name + ": every observed game included");
    const pages = Math.max(1, Math.ceil(expected.length / PAGE_SIZE));
    const seen = new Set();
    for (let index = 0; index < pages; index += 1) {
      const visible = await assertPage(page, expected, index, name + "/page-" + (index + 1));
      exhaustivePages += 1;
      for (const row of visible) {
        const identity = [row.gameId, row.target, row.metric, row.horizon, row.roleId || "none"].join("|");
        assert.equal(seen.has(identity), false, name + ": duplicate pagination row");
        seen.add(identity);
        visitedCells.add(row.gameId + "|" + row.target + "|" + row.horizon);
        if (row.view) visitedViews.add(row.gameId + "|" + row.roleId);
        if (row.view?.current_issue_ref) seenIssues.add(row.view.current_issue_ref);
        if (row.view?.at_issue_ref) seenIssues.add(row.view.at_issue_ref);
      }
      if (index + 1 < pages) await page.click("#next");
    }
    assert.equal(seen.size, expected.length, name + ": pagination omits no row");
    exhaustiveRows += seen.size;
    if (pages > 1) {
      await page.click("#prev");
      await assertPage(page, expected, pages - 2, name + "/previous-from-last");
      await page.click("#next");
      await assertPage(page, expected, pages - 1, name + "/next-to-last");
    }
    snapshots.push({ check: name, filter: criteria(filter), matching_rows: expected.length,
      matching_games: reference.gameIds.length, checked_pages: pages,
      every_row_compared: true, previous_and_next_from_last_checked: pages > 1 });
    checks.push(name);
  }
  async function noOverflow(page, name) {
    const result = await page.evaluate(() => ({
      page: document.documentElement.scrollWidth <= innerWidth + 1,
      main: document.querySelector("main").getBoundingClientRect().right <= innerWidth + 1,
      scrollContainers: [...document.querySelectorAll(".scroll")].every(element =>
        element.getBoundingClientRect().left >= -1 && element.getBoundingClientRect().right <= innerWidth + 1),
    }));
    assert.deepEqual(result, { page: true, main: true, scrollContainers: true }, name);
    checks.push(name);
  }
  async function screenshot(page, name) {
    await page.screenshot({ path: path.join(output, name), fullPage: true });
    screenshots.push(name);
  }
  async function checkChampionTable(page) {
    const score = (value, metric) => typeof value !== "number" ? "Unavailable" : metric === "accuracy" ?
      (100 * value).toFixed(4) + "%" : value.toFixed(6);
    const expected = Object.values(data.champions).map(role => [
      words(role.phase) + " · T" + role.horizon_minutes,
      role.target + " · " + words(role.selected_metric), role.family,
      Object.entries(role.per_season_metrics).map(([season, metrics]) => season + ": " + score(metrics[role.selected_metric], role.selected_metric)).join(" "),
      score(role.pooled_metrics[role.selected_metric], role.selected_metric),
      Object.entries(role.support_by_season).map(([season, count]) => season + ": " + count).join(" "),
    ].map(normalized));
    const actual = await page.locator("#champion-rows tr").evaluateAll(rows => rows.map(row =>
      [...row.querySelectorAll("td")].map(cell => cell.innerText.replace(/\s+/g, " ").trim())));
    assert.deepEqual(actual, expected, "Every champion role retains exact saved season and pooled metrics");
  }
  function isolate(row, extra = {}) {
    return { target: row.target, metric: row.metric, horizon: String(row.horizon),
      phase: row.game.phase, date: row.facts.date, team: row.game.home_team || row.game.away_team || "", ...extra };
  }

  try {
    const desktop = await context({ width: 1366, height: 1000 });
    const page = await pageFor(desktop);
    await b077Review.validatePage(page, 'desktop', true);
    assert.equal(await page.locator("h1").isVisible(), true);
    assert.equal(await page.locator("h1").innerText(), "Season coverage, issued forecasts and champion roles");
    for (const id of CONTROLS) {
      assert.equal(await page.locator("#" + id).isVisible(), true, "Visible control: " + id);
      assert.equal(await page.locator("#" + id).evaluate(element => Boolean(element.closest("label")?.textContent.trim())), true);
    }
    assert.deepEqual(await page.evaluate(() => window.NBA_PUBLIC_REPORT), data);
    checks.push("embedded_public_data_exactly_matches_adjacent_json", "all_nine_controls_visible_and_labelled",
      "b077_saved_metric_and_venue_filters_verified", "b077_metric_csv_all_248_rows_preserved",
      "b077_all_28_historical_peak_groups_and_filters_verified", "b077_nomination_and_production_gates_match_saved_registry");
    const cardValues = await page.locator("#cards .big").allTextContents();
    assert.deepEqual(cardValues, [data.coverage.official_schedule_games, data.coverage.games_in_original_issued_inventory,
      data.coverage.active_research_champion_roles, data.coverage.official_games_without_original_issues].map(value => value.toLocaleString("en-US")));
    assert.deepEqual(await page.locator("#date option").evaluateAll(options => options.map(option => option.value)), ["all", "unknown", ...reference.dates]);
    const optionExpectations = { "game-status": ["all", "upcoming", "completed", "unresolved", "pending"],
      phase: ["all", "regular", "postseason", "preseason", "ist_championship"], target: Object.keys(METRICS),
      horizon: ["all", "60", "120"], availability: ["all", "yes", "no"],
      "issue-class": ["all", "EARLY_OUTLOOK", "NOMINAL", "LATE", "missing"] };
    for (const [id, expected] of Object.entries(optionExpectations)) {
      assert.deepEqual(await page.locator("#" + id + " option").evaluateAll(options => options.map(option => option.value)), expected);
    }
    const resultNote = normalized(await page.locator("#result-status").innerText());
    assert.ok(resultNote.includes("Latest row-backed status counts: " + JSON.stringify(data.coverage.official_games_by_latest_row_backed_status)));
    assert.ok(resultNote.includes("Saved owner aggregate: " + JSON.stringify(data.result_observation_recovery.source_reported_status_counts || {})));
    checks.push("independent_result_status_clocks_and_aggregate_discrepancy_visible");
    await checkChampionTable(page);
    await checkFilter(page, {}, "desktop_default_complete_inventory");
    await noOverflow(page, "desktop_no_page_horizontal_overflow");
    await screenshot(page, "nba-publication-desktop.png");

    // Exhaustive displayed-row verification, including unsupported phases,
    // unresolved opponents and all games absent from the old issued inventory.
    for (const [target, metrics] of Object.entries(METRICS)) {
      await page.selectOption("#target", target);
      assert.deepEqual(await page.locator("#metric option").evaluateAll(options => options.map(option => option.value)), metrics);
      for (const metric of metrics) await walkInventory(page, { target, metric }, "all_observed_rows_" + target + "_" + metric);
    }
    assert.deepEqual(sorted(visitedCells), sorted(reference.cells));
    assert.deepEqual(sorted(visitedViews), sorted(reference.views.keys()));
    assert.deepEqual(sorted(seenIssues), sorted(Object.keys(data.issues)));
    checks.push("every_observed_target_horizon_cell_rendered", "every_sparse_saved_role_view_rendered",
      "every_public_issue_value_interval_and_clock_compared", "all_pages_next_previous_and_boundaries_verified");

    for (const status of ["completed", "upcoming", "unresolved", "pending"]) {
      const expected = await checkFilter(page, { status }, "status_control_" + status);
      assert.ok(expected.every(row => reference.statusGames[status].has(row.gameId)));
      if (status === "unresolved") {
        assert.equal(new Set(expected.map(row => row.gameId)).size, data.coverage.official_unresolved_matchups);
        assert.ok(expected.every(row => row.current === null && row.atIssue === null));
      }
      if (status === "pending") assert.ok(expected.every(row => row.game.source_status === "SCHEDULED"));
    }
    for (const phase of ["regular", "preseason", "postseason", "ist_championship"]) {
      const expected = await checkFilter(page, { phase }, "phase_control_" + phase);
      if (phase === "preseason" || phase === "ist_championship") {
        assert.ok(expected.every(row => row.role === null && row.current === null && row.atIssue === null));
      }
    }
    for (const horizon of ["60", "120"]) await checkFilter(page, { horizon }, "horizon_control_" + horizon);
    for (const availability of ["yes", "no"]) await checkFilter(page, { availability }, "availability_control_" + availability);
    for (const issueClass of ["EARLY_OUTLOOK", "NOMINAL", "LATE", "missing"]) {
      await checkFilter(page, { issueClass }, "issue_timing_control_" + issueClass);
    }
    const late = reference.rows.find(row => row.timingClass === "LATE");
    if (late) assert.ok((await checkFilter(page, { ...isolate(late), issueClass: "LATE" }, "actual_late_original_issue_remains_late")).length > 0);

    const currentInterval = reference.rows.find(row => row.current?.prediction_intervals && reference.statusGames.upcoming.has(row.gameId));
    const intervalRows = ["margin", "total"].map(target => reference.rows.find(row => row.target === target &&
      (row.current?.prediction_intervals || row.atIssue?.prediction_intervals))).filter(Boolean);
    for (const row of intervalRows) {
      const expected = await checkFilter(page, isolate(row), "desktop_original_intervals_" + row.target);
      assert.ok(expected.some(value => value.gameId === row.gameId && value.roleId === row.roleId));
      assert.ok(await page.locator("#forecast-rows .issued-intervals").count() > 0);
    }
    if (currentInterval) {
      const filter = { ...isolate(currentInterval), status: "upcoming", availability: "yes", issueClass: currentInterval.timingClass };
      assert.ok((await checkFilter(page, filter, "all_nine_controls_combined_on_actual_issue")).length > 0);
    }
    const older = reference.rows.find(row => row.current === null && row.atIssue && !row.view?.at_issue_matches_current_champion);
    if (older) {
      await checkFilter(page, { ...isolate(older), availability: "no" }, "earlier_champion_does_not_fill_current_champion_gap");
      const row = page.locator('#forecast-rows tr[data-game-id="' + older.gameId + '"][data-role="' + older.roleId + '"]');
      assert.equal(await row.locator("td").nth(2).locator(".value").count(), 0);
      assert.equal(await row.locator("td").nth(3).locator(".value").count(), 1);
    }
    const absent = reference.rows.find(row => !row.game.original_issue_inventory_present && row.game.home_team &&
      row.current === null && row.atIssue === null && row.role);
    if (absent) await checkFilter(page, { ...isolate(absent), availability: "no", issueClass: "missing" }, "official_game_absent_from_old_forecasts_stays_visible_and_missing");
    const example = reference.rows.find(row => row.current && row.game.home_team_name) || absent;
    const dates = new Set([reference.dates[0], reference.dates[reference.dates.length - 1], example?.facts.date, "unknown"].filter(Boolean));
    for (const date of dates) await checkFilter(page, { date }, "date_control_" + date);
    if (example) {
      await checkFilter(page, { team: "  " + example.game.home_team.toLowerCase() + "  " }, "team_code_case_and_whitespace_normalization");
      await checkFilter(page, { team: example.game.home_team_name.toUpperCase() }, "team_full_name_case_insensitive_filter");
    }
    await checkFilter(page, { team: "NO_MATCH_TEAM_000" }, "empty_selection_explicit_no_rows_and_disabled_paging");

    // Target-dependent metrics preserve only compatible selections.
    await select(page, { target: "winner", metric: "accuracy" });
    await page.selectOption("#target", "margin");
    assert.equal(await page.locator("#metric").inputValue(), "mae");
    await page.selectOption("#metric", "crps");
    await page.selectOption("#target", "total");
    assert.equal(await page.locator("#metric").inputValue(), "crps");
    await page.selectOption("#target", "winner");
    assert.equal(await page.locator("#metric").inputValue(), "log_loss");
    await assertPage(page, matching(reference), 0, "metric_resets_when_target_requires_different_metrics");
    checks.push("target_dependent_metric_options_and_resets");
    if (matching(reference).length > PAGE_SIZE && example) {
      await page.click("#next");
      await assertPage(page, matching(reference), 1, "page_two_before_input_change");
      await page.fill("#team", example.game.home_team);
      await assertPage(page, matching(reference, { team: example.game.home_team }), 0, "team_change_resets_pagination");
      checks.push("input_change_resets_pagination_to_first_page");
    }
    assert.deepEqual(await page.evaluate(() => window.NBA_PUBLIC_REPORT), data, "Controls never rewrite forecasts, original intervals, clocks, or outcomes");

    const mobile = await context({ width: 390, height: 844 });
    const small = await pageFor(mobile);
    await b077Review.validatePage(small, 'mobile', false);
    await checkFilter(small, {}, "mobile_default_all_observed_games");
    await checkChampionTable(small);
    await noOverflow(small, "mobile_390px_no_page_horizontal_overflow");
    await screenshot(small, "nba-publication-mobile.png");
    await checkFilter(small, { status: "unresolved" }, "mobile_unresolved_official_matchups_visible");
    await noOverflow(small, "mobile_unresolved_rows_do_not_overflow");
    await screenshot(small, "nba-publication-mobile-unresolved.png");
    if (intervalRows.length) {
      const row = intervalRows[intervalRows.length - 1];
      await checkFilter(small, isolate(row), "mobile_original_interval_endpoints_and_clocks");
      await noOverflow(small, "mobile_intervals_stay_inside_scroll_container");
      await screenshot(small, "nba-publication-mobile-intervals.png");
    }
    assert.deepEqual(await small.evaluate(() => window.NBA_PUBLIC_REPORT), data);

    // A brand-new context has no prior filter or tab state to rescue the page.
    const reopened = await context({ width: 1366, height: 1000 });
    const again = await pageFor(reopened);
    await b077Review.validatePage(again, 'offline_reopen', false);
    assert.deepEqual(await again.evaluate(() => window.NBA_PUBLIC_REPORT), data);
    await assertPage(again, matching(reference), 0, "fresh_context_reopen_default_without_prior_state");
    for (const [id, expected] of Object.entries({ "game-status": "all", phase: "all", target: "winner", metric: "log_loss",
      horizon: "all", date: "all", team: "", availability: "all", "issue-class": "all" })) {
      assert.equal(await again.locator("#" + id).inputValue(), expected);
    }
    await checkChampionTable(again);
    if (intervalRows.length) await checkFilter(again, isolate(intervalRows[0]), "fresh_reopen_preserves_original_intervals_and_clocks");
    checks.push("fresh_context_reopen_reconstructs_complete_saved_report", "all_controls_leave_public_data_immutable");

    assert.deepEqual(errors, []);
    assert.deepEqual(consoleErrors, []);
    assert.deepEqual(remoteRequests, []);
    assert.equal(sha256(fs.readFileSync(jsonPath)), sha256(jsonBytes));
    assert.equal(sha256(fs.readFileSync(htmlPath)), sha256(htmlBytes));
    checks.push("no_javascript_page_or_console_errors", "zero_remote_page_requests", "saved_artifact_bytes_unchanged");
    const result = { status: "PASS", scope: "Hosted browser verification of every public schedule/metric row against saved JSON; no fitting, rescoring or live refresh",
      browser_version: await browser.version(), started_at_utc: started, finished_at_utc: new Date().toISOString(),
      elapsed_seconds: Number(process.hrtime.bigint() - startedClock) / 1e9,
      source_json_sha256: sha256(jsonBytes), source_html_sha256: sha256(htmlBytes),
      oracle: "Independent target/horizon coverage grid joined to shared role groups and sparse original issues; no renderer functions invoked",
      observed_games_checked: reference.gameIds.length, target_horizon_cells_checked: visitedCells.size,
      b077_saved_metrics_and_venue_evidence: b077Evidence,
      saved_role_views_checked: visitedViews.size, distinct_issued_bodies_checked: seenIssues.size,
      exhaustive_displayed_rows_checked: exhaustiveRows, exhaustive_pages_checked: exhaustivePages,
      evidence_as_of_utc: data.evidence_as_of_utc, coverage: data.coverage, checks, rendered_cases: snapshots,
      page_errors: errors, console_errors: consoleErrors, remote_page_requests: remoteRequests.length,
      external_accessibility_audit: false, cross_browser_coverage: false, screenshots };
    fs.writeFileSync(path.join(output, "nba-publication-browser-result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    fs.writeFileSync(path.join(output, "nba-publication-browser-result.json"), JSON.stringify({
      status: "FAIL", started_at_utc: started, finished_at_utc: new Date().toISOString(),
      source_json_sha256: sha256(jsonBytes), source_html_sha256: sha256(htmlBytes),
      checks_completed: checks, exhaustive_displayed_rows_checked: exhaustiveRows, exhaustive_pages_checked: exhaustivePages,
      error: error.message, stack: error.stack, page_errors: errors, console_errors: consoleErrors,
      remote_page_requests: remoteRequests, rendered_cases: snapshots,
    }, null, 2) + "\n");
    throw error;
  } finally {
    for (const owner of contexts) await owner.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });

