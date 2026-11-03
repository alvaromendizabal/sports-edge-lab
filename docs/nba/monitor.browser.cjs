/* Hosted offline browser checks; all event-level demo inputs are invented. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_DIR || "playwright");

(async () => {
  const output = path.resolve(process.env.NBA_MONITOR_SCREENSHOTS || "nba-monitor-browser-artifacts");
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const checks = [];
  let remoteRequests = 0;
  const url = pathToFileURL(path.join(__dirname, "monitor.html")).href;
  try {
    const context = await browser.newContext({ viewport: { width: 1366, height: 1000 }, reducedMotion: "reduce" });
    await context.route(/^https?:\/\//, async route => { remoteRequests += 1; await route.abort(); });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(url);
    assert.equal(await page.locator("#filters").isVisible(), true);
    assert.equal(await page.locator("#metrics-table tbody tr:visible").count(), 3);
    await page.screenshot({ path: path.join(output, "nba-monitor-desktop.png"), fullPage: true });
    checks.push("desktop_all_three_dated_cohorts_visible");
    await page.selectOption("#season-filter", "2026–27");
    await page.selectOption("#objective-filter", "margin");
    assert.equal(await page.locator("#metrics-table tbody tr:visible").count(), 1);
    assert.equal(await page.locator("#metrics-table th[data-objective]:visible").count(), 2);
    assert.match(await page.locator("#filter-status").innerText(), /1 dated cohort; margin/);
    checks.push("actual_season_objective_controls_and_live_status");
    await page.selectOption("#demo-mode", "fresh");
    assert.equal(await page.locator("#demo-accuracy").innerText(), "100.0%");
    assert.match(await page.locator("#demo-status").innerText(), /REJECTED/);
    await page.selectOption("#demo-mode", "union");
    assert.equal(await page.locator("#demo-accuracy").innerText(), "50.0%");
    checks.push("rejected_fresh_only_view_and_safe_result_union");
    await page.goto(url);
    await page.keyboard.press("Tab");
    assert.equal(await page.evaluate(() => document.activeElement.textContent), "Skip to evidence");
    await page.keyboard.press("Enter");
    assert.equal(await page.evaluate(() => document.activeElement.id), "main");
    checks.push("keyboard_skip_link_focus");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    checks.push("desktop_no_page_horizontal_overflow");
    const contrast = await page.evaluate(() => {
      const rgb = text => text.match(/[\d.]+/g).slice(0, 3).map(Number);
      const luminance = values => values.map(value => value / 255).map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4).reduce((sum, value, i) => sum + value * [0.2126, 0.7152, 0.0722][i], 0);
      const selectors = [".lede", ".metric span", ".boundary p", ".muted", "select"];
      return selectors.map(selector => {
        const element = document.querySelector(selector);
        let parent = element, background;
        while (parent) {
          const color = getComputedStyle(parent).backgroundColor;
          if (color !== "rgba(0, 0, 0, 0)" && color !== "transparent") { background = color; break; }
          parent = parent.parentElement;
        }
        const foreground = getComputedStyle(element).color;
        const values = [luminance(rgb(foreground)), luminance(rgb(background || "rgb(255, 255, 255)"))].sort((a, b) => b - a);
        return { selector, ratio: (values[0] + 0.05) / (values[1] + 0.05) };
      });
    });
    assert.ok(contrast.every(sample => sample.ratio >= 4.5), JSON.stringify(contrast));
    checks.push("sampled_normal_text_contrast_at_least_4_5");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(url);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(output, "nba-monitor-mobile.png"), fullPage: true });
    checks.push("mobile_390px_no_page_horizontal_overflow");
    assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior), "auto");
    checks.push("reduced_motion_respected");
    assert.deepEqual(errors, []);
    checks.push("no_javascript_page_errors");
    const noJs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1366, height: 1000 } });
    await noJs.route(/^https?:\/\//, async route => { remoteRequests += 1; await route.abort(); });
    const plain = await noJs.newPage();
    await plain.goto(url);
    assert.equal(await plain.locator("#metrics-table tbody tr:visible").count(), 3);
    assert.equal(await plain.locator("#filters").isVisible(), false);
    assert.equal(await plain.locator("#demo-mode").isDisabled(), true);
    checks.push("no_javascript_complete_aggregate_content");
    assert.equal(remoteRequests, 0);
    checks.push("zero_remote_page_requests");
    const result = { status: "PASS", browser_version: await browser.version(), checks,
      contrast_samples: contrast, remote_page_requests: remoteRequests,
      external_accessibility_audit: false, cross_browser_coverage: false,
      screenshots: ["nba-monitor-desktop.png", "nba-monitor-mobile.png"] };
    fs.writeFileSync(path.join(output, "browser-result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify(result, null, 2));
    await context.close();
    await noJs.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
