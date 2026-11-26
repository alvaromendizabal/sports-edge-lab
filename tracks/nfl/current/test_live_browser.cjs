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
  // The two byte-pinned documents without an explicit body tag receive this script after EOF.
  // The captured response must still recover every original source byte.
  const appendedAtEnd = ["current-archive-n186-research-history.html",
    "current-week-12-field-notes-n199-weekly-index.html"].includes(context);
  const change = appendedAtEnd
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
  const snapshot = JSON.parse(fs.readFileSync(path.join(root, "week-12-field-notes/n202/snapshot.json"), "utf8"));
  const currentSnapshot = JSON.parse(fs.readFileSync(path.join(root, "week-12-field-notes/n203/snapshot.json"), "utf8"));
  const currentCompleted = currentSnapshot.completed_population.completed;
  const currentIds = currentSnapshot.completed_population.games.map(g=>g.game_id).sort();
  assert(Number.isInteger(currentCompleted) && currentCompleted >= 163);
  assert.equal(currentIds.length,currentCompleted);assert.equal(new Set(currentIds).size,currentCompleted);
  assert.equal(digest(Buffer.from(currentIds.join("\n"))),currentSnapshot.completed_population.manifest_sha256);
  for(const row of currentSnapshot.ordinary_performance){
    for(const [score,field] of [[row.selected,row.target],[row.earlier_week_replay,row.target+"_replay"]]){
      const grades={WIN:0,LOSS:0,PUSH:0,UNRESOLVED:0};
      for(const game of currentSnapshot.completed_population.games){assert(game[field] in grades);grades[game[field]]++;}
      assert.equal(score.completed,currentCompleted);
      assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,currentCompleted);
      assert.deepEqual(grades,{WIN:score.wins,LOSS:score.losses,PUSH:score.settlement_pushes,UNRESOLVED:score.unresolved});
      if(score.full_population_champion)assert.equal(score.unresolved,0);
    }
  }
  assert.doesNotMatch(JSON.stringify(currentSnapshot),/"(?:pmf|calibrator|selected_features|calibration_parameters|configuration)"/);
  for(const g of currentSnapshot.games){
    if(g.n203)assert(Math.abs(g.n203.away_probability+g.n203.home_probability+g.n203.tie_probability-1)<1e-9);
    if(g.started_at_snapshot){assert.equal(g.n203,null);assert.equal(g.spread,null);assert.equal(g.total,null);}
  }
  for(const q of currentSnapshot.book_options){
    assert(Math.abs(q.p_win+q.p_push+q.p_loss-1)<1e-9);
    assert(Math.abs(q.expected_profit_per_unit-(q.p_win*(q.decimal_price-1)-q.p_loss))<1e-9);
  }
  assert.deepEqual(currentSnapshot.cards,snapshot.cards,"Preserve the V13/Circa issue and official deadline evidence");
  assert.deepEqual(currentSnapshot.circa,snapshot.circa);
  const n204Snapshot = JSON.parse(fs.readFileSync(path.join(root, "week-12-field-notes/n204/snapshot.json"), "utf8"));
  const n204Completed = n204Snapshot.completed_population.completed;
  const n204Ids = n204Snapshot.completed_population.games.map(g=>g.game_id).sort();
  assert(Number.isInteger(n204Completed) && n204Completed>=currentCompleted);
  assert.equal(n204Ids.length,n204Completed);assert.equal(new Set(n204Ids).size,n204Completed);
  assert.equal(digest(Buffer.from(n204Ids.join("\n"))),n204Snapshot.completed_population.manifest_sha256);
  for(const row of n204Snapshot.ordinary_performance){
    for(const [score,field] of [[row.selected,row.target],[row.earlier_week_replay,row.target+"_replay"]]){
      const grades={WIN:0,LOSS:0,PUSH:0,UNRESOLVED:0};
      for(const game of n204Snapshot.completed_population.games){assert(game[field] in grades);grades[game[field]]++;}
      assert.equal(score.completed,n204Completed);
      assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,n204Completed);
      assert.deepEqual(grades,{WIN:score.wins,LOSS:score.losses,PUSH:score.settlement_pushes,UNRESOLVED:score.unresolved});
      if(score.full_population_champion)assert.equal(score.unresolved,0);
    }
  }
  for(const score of [...n204Snapshot.objective_performance,...n204Snapshot.policy_replay,...n204Snapshot.annual_metrics])assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,score.completed);
  assert.doesNotMatch(JSON.stringify(n204Snapshot),/"(?:pmf|reference_pmf|calibrator|selected_features|calibration_parameters|configuration|learner)"/);
  for(const game of n204Snapshot.games){
    if(game.n204)assert(Math.abs(game.n204.away_probability+game.n204.home_probability+game.n204.tie_probability-1)<1e-9);
    if(game.started_at_snapshot){assert.equal(game.n204,null);assert.equal(game.spread,null);assert.equal(game.total,null);}
    const original=currentSnapshot.games.find(g=>g.id===game.id);
    assert.deepEqual(game.v13,original.v13);assert.deepEqual(game.roster,original.roster);assert.deepEqual(game.n203,original.n203);
  }
  for(const quote of n204Snapshot.book_options){
    assert(Math.abs(quote.p_win+quote.p_push+quote.p_loss-1)<1e-9);
    assert(Math.abs(quote.expected_profit_per_unit-(quote.p_win*(quote.decimal_price-1)-quote.p_loss))<1e-6);
  }
  assert.deepEqual(n204Snapshot.cards,currentSnapshot.cards);assert.deepEqual(n204Snapshot.circa,currentSnapshot.circa);
  assert.equal(n204Snapshot.independent_verification.status,"PASS");
  assert.equal(n204Snapshot.independent_verification.prediction_rows_checked,n204Completed*n204Snapshot.campaign.candidate_policies);
  const n205Snapshot = JSON.parse(fs.readFileSync(path.join(root, "week-12-field-notes/n205/snapshot.json"), "utf8"));
  const n205Completed = n205Snapshot.completed_population.completed;
  const n205Ids = n205Snapshot.completed_population.games.map(g=>g.game_id).sort();
  assert(Number.isInteger(n205Completed) && n205Completed>=n204Completed);
  assert.equal(n205Ids.length,n205Completed);assert.equal(new Set(n205Ids).size,n205Completed);
  assert.equal(digest(Buffer.from(n205Ids.join("\n"))),n205Snapshot.completed_population.manifest_sha256);
  for(const row of n205Snapshot.ordinary_performance){
    for(const [score,field] of [[row.selected,row.target],[row.earlier_week_replay,row.target+"_replay"]]){
      const grades={WIN:0,LOSS:0,PUSH:0,UNRESOLVED:0};
      for(const game of n205Snapshot.completed_population.games){assert(game[field] in grades);grades[game[field]]++;}
      assert.equal(score.completed,n205Completed);
      assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,n205Completed);
      assert.deepEqual(grades,{WIN:score.wins,LOSS:score.losses,PUSH:score.settlement_pushes,UNRESOLVED:score.unresolved});
      if(score.full_population_champion)assert.equal(score.unresolved,0);
    }
  }
  for(const score of [...n205Snapshot.objective_performance,...n205Snapshot.policy_replay,...n205Snapshot.annual_metrics])assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,score.completed);
  assert.doesNotMatch(JSON.stringify(n205Snapshot),/"(?:pmf|reference_pmf|calibrator|selected_features|calibration_parameters|configuration|learner)"/);
  for(const game of n205Snapshot.games){
    if(game.n205)assert(Math.abs(game.n205.away_probability+game.n205.home_probability+game.n205.tie_probability-1)<1e-9);
    if(game.started_at_snapshot){assert.equal(game.n205,null);assert.equal(game.spread,null);assert.equal(game.total,null);}
    const original=n204Snapshot.games.find(g=>g.id===game.id);
    assert.deepEqual(game.v13,original.v13);assert.deepEqual(game.roster,original.roster);assert.deepEqual(game.n203,original.n203);assert.deepEqual(game.n204,original.n204);
  }
  for(const quote of n205Snapshot.book_options){
    assert(Math.abs(quote.p_win+quote.p_push+quote.p_loss-1)<1e-9);
    assert(Math.abs(quote.expected_profit_per_unit-(quote.p_win*(quote.decimal_price-1)-quote.p_loss))<1e-6);
  }
  assert.deepEqual(n205Snapshot.cards,n204Snapshot.cards);assert.deepEqual(n205Snapshot.circa,n204Snapshot.circa);
  assert.equal(n205Snapshot.independent_verification.status,"PASS");
  assert.equal(n205Snapshot.independent_verification.prediction_rows_checked,n205Completed*n205Snapshot.campaign.candidate_policies);
  assert.equal(n205Snapshot.source_delivery.mode,"SEPARATE_ZERO_FIT_SOURCE_REFRESH");
  assert.equal(n205Snapshot.source_delivery.stale_priced_options,0);
  assert.equal(n205Snapshot.source_delivery.original_final_options,0);
  assert(n205Snapshot.source_delivery.original_issues.some(r=>r.priced_options>0&&r.forecast_rows_quotes_older_than_600_seconds>0));
  assert.equal(n205Snapshot.source_delivery.independent_refresh_verification.status,"PASS");
  for(const q of n205Snapshot.book_options){
    const observed=(Date.parse(q.issue_utc)-Date.parse(q.quote_clock_utc))/1000,native=(Date.parse(q.issue_utc)-Date.parse(q.native_clock_utc))/1000;
    assert(observed>=0&&observed<=600&&native>=0&&native<=600);assert(Math.abs(observed-q.quote_age_seconds_at_issue)<.001);assert(Math.abs(native-q.native_age_seconds_at_issue)<.001);
  }
  assert.equal(n205Snapshot.direct_source_options.length,3);
  const n206Snapshot = JSON.parse(fs.readFileSync(path.join(root, "week-12-field-notes/n206/snapshot.json"), "utf8"));
  const n206Completed = n206Snapshot.completed_population.completed;
  const n206Ids = n206Snapshot.completed_population.games.map(g=>g.game_id).sort();
  assert(Number.isInteger(n206Completed) && n206Completed>=n205Completed);
  assert.equal(n206Ids.length,n206Completed);assert.equal(new Set(n206Ids).size,n206Completed);
  assert.equal(digest(Buffer.from(n206Ids.join("\n"))),n206Snapshot.completed_population.manifest_sha256);
  for(const row of n206Snapshot.ordinary_performance){
    for(const [score,field] of [[row.selected,row.target],[row.earlier_week_replay,row.target+"_replay"]]){
      const grades={WIN:0,LOSS:0,PUSH:0,UNRESOLVED:0};
      for(const game of n206Snapshot.completed_population.games){assert(game[field] in grades);grades[game[field]]++;}
      assert.equal(score.completed,n206Completed);
      assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,n206Completed);
      assert.deepEqual(grades,{WIN:score.wins,LOSS:score.losses,PUSH:score.settlement_pushes,UNRESOLVED:score.unresolved});
      if(score.full_population_champion)assert.equal(score.unresolved,0);
    }
  }
  for(const score of [...n206Snapshot.objective_performance,...n206Snapshot.policy_replay,...n206Snapshot.annual_metrics])assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,score.completed);
  assert.doesNotMatch(JSON.stringify(n206Snapshot),/"(?:pmf|reference_pmf|calibrator|selected_features|calibration_parameters|configuration|learner)"/);
  for(const game of n206Snapshot.games){
    if(game.n206)assert(Math.abs(game.n206.away_probability+game.n206.home_probability+game.n206.tie_probability-1)<1e-9);
    if(game.started_at_snapshot){assert.equal(game.n206,null);assert.equal(game.spread,null);assert.equal(game.total,null);}
    const original=n205Snapshot.games.find(g=>g.id===game.id);
    assert.deepEqual(game.v13,original.v13);assert.deepEqual(game.roster,original.roster);assert.deepEqual(game.n203,original.n203);assert.deepEqual(game.n204,original.n204);assert.deepEqual(game.n205,original.n205);
  }
  for(const quote of n206Snapshot.book_options){
    assert(Math.abs(quote.p_win+quote.p_push+quote.p_loss-1)<1e-9);
    assert(Math.abs(quote.expected_profit_per_unit-(quote.p_win*(quote.decimal_price-1)-quote.p_loss))<1e-6);
  }
  assert.deepEqual(n206Snapshot.cards,n205Snapshot.cards);assert.deepEqual(n206Snapshot.circa,n205Snapshot.circa);
  assert.equal(n206Snapshot.independent_verification.status,"PASS");
  assert.equal(n206Snapshot.independent_verification.prediction_rows_checked,n206Completed*n206Snapshot.campaign.candidate_policies);
  assert.equal(n206Snapshot.source_delivery.mode,"VERIFIED_OWNER_FINAL_SOURCE_REFRESH");
  assert.equal(n206Snapshot.source_delivery.stale_priced_options,0);
  assert.equal(n206Snapshot.source_delivery.latest_forecasts_and_priced_options_same_issue,true);
  assert.equal(n206Snapshot.independent_current_verification.status,"PASS");
  assert.equal(n206Snapshot.source_delivery.quote_basis_counts.FRESH_OBSERVED_PREGAME_QUOTE,30);
  assert.equal(n206Snapshot.independent_verification.replay_game_rows_checked,n206Completed*n206Snapshot.policy_replay.length);
  for(const r of n206Snapshot.ordinary_performance){
    const prior=r.previous_policy_same_population;
    assert.equal(prior.completed,n206Completed);assert.equal(prior.wins+prior.losses+prior.settlement_pushes+prior.unresolved,n206Completed);
    assert.equal(r.same_population_extra_wins,r.selected.wins-prior.wins);
  }
  for(const g of n206Snapshot.games)if(g.n206){
    assert(g.n206.coherent_selected_score_law&&g.n206.total_coherent_selected_score_law);
    assert.equal(g.n206.away_margin,g.spread.model_point);assert.equal(g.n206.total,g.total.model_point);
  }
  assert(n206Snapshot.strict_probability_tradeoff.total_strict_brier>.25);
  assert(n206Snapshot.strict_probability_tradeoff.total_proper_brier<.25);
  for(const q of n206Snapshot.book_options){
    const observed=(Date.parse(q.issue_utc)-Date.parse(q.quote_clock_utc))/1000,native=(Date.parse(q.issue_utc)-Date.parse(q.native_clock_utc))/1000;
    assert(observed>=0&&observed<=600&&native>=0&&native<=600);assert(Math.abs(observed-q.quote_age_seconds_at_issue)<.001);assert(Math.abs(native-q.native_age_seconds_at_issue)<.001);
  }
  assert.equal(n206Snapshot.direct_source_options.length,3);
  const population = snapshot.completed_population;
  const completed = population.completed;
  assert(Number.isInteger(completed) && completed >= 163, "Completed census cannot fall below its verified baseline");
  const completedIds = population.games.map(g=>g.game_id).sort();
  assert.equal(completedIds.length,completed); assert.equal(new Set(completedIds).size,completed);
  assert.equal(digest(Buffer.from(JSON.stringify(completedIds))),population.manifest_sha256,"Immutable completed-game manifest changed");
  for(const row of snapshot.ordinary_performance){
    for(const [score,field] of [[row.selected,row.target],[row.earlier_week_replay,row.target+"_replay"]]){
      const grades={WIN:0,LOSS:0,PUSH:0,UNRESOLVED:0};
      for(const game of population.games){assert(game[field] in grades,"Missing completed-game grade");grades[game[field]]++;}
      assert.equal(score.completed,completed);
      assert.equal(score.wins+score.losses+score.settlement_pushes+score.unresolved,completed);
      assert.deepEqual(grades,{WIN:score.wins,LOSS:score.losses,PUSH:score.settlement_pushes,UNRESOLVED:score.unresolved});
      if(score.full_population_champion)assert.equal(score.unresolved,0);
    }
  }
  assert.equal(snapshot.circa.inherited_status_authoritative,false);
  for(const card of snapshot.cards){
    assert.equal(new Set(card.picks.map(p=>p.game_id)).size,5);
    const deadline=[snapshot.circa.weekly_deadline_utc,...card.picks.map(p=>snapshot.games.find(g=>g.id===p.game_id).kickoff_utc)].sort()[0];
    assert.equal(card.deadline_utc,deadline,"Circa deadline must use the earliest selected kickoff and weekly cap");
  }
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
    assert(verified || receipt.status === "DEPLOYED_AWAITING_HTTP_HASH_AUDIT", "Validate only a deployed release");
    report.current_assets = [];
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
      report.current_assets.push({path:asset.path, url:response.url(), status:response.status(), sha256:digest(local), bytes:local.length, received_sha256:digest(bytes), received_bytes:bytes.length, matches_pushed_source:true, verification:bytes.equals(local)?"EXACT_ORIGINAL_BYTES":"EXACT_SOURCE_AFTER_IDENTIFIED_EDGE_SCRIPT"});
    }
    console.log("Verified public asset manifest", JSON.stringify(report.current_assets));
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
    const noOverflow = async () => { const layout = await page.evaluate(() => ({ width: window.innerWidth, scroll: document.documentElement.scrollWidth, outside: [...document.querySelectorAll("main *, header *")].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest(".scroll, .table-scroll")).slice(0, 8).map(e => [e.tagName, e.id, e.className, e.getBoundingClientRect().right]) })); assert(layout.scroll <= layout.width + 1, JSON.stringify(layout)); };
    await check(`${width}px: retrospective NFL postseason results and complete annual denominators`,async()=>{
      await page.goto(new URL("week-12-field-notes/n208/",base).href,{waitUntil:"domcontentloaded"});
      await page.getByRole("link",{name:"How N208 performed in the 2024 and 2025 playoffs",exact:true}).click();
      await page.getByRole("heading",{name:"How the models graded in the playoffs",exact:true}).waitFor();
      await count("#results tbody tr",14);
      assert.match(await text("main"),/5–20–1/);
      await page.getByText("Each postseason separately · 13 games per year",{exact:true}).click();
      await page.getByText("Regular season and playoffs · 285 games per year",{exact:true}).click();
      await count("#annual details tbody tr:visible",56);
      const proof=await (await page.request.get(new URL("week-12-field-notes/n208/postseason/proof.json",base).href)).json();
      assert.deepEqual([proof.unique_games,proof.policy_target_components,proof.game_component_scores],[26,14,364]);
      assert.equal(proof.n209_qualification.status,"NATIVE_QUALIFICATION_UNDERWAY");
      assert.match(await text("#qualification"),/bounded native qualification/);
      assert(proof.pooled.every(r=>r.games===26 && r.wins+r.losses+r.pushes===26 && r.decisive===r.wins+r.losses));
      await page.getByText("Seven confidence thresholds for the original fixed policy",{exact:true}).click();
      await count("#confidence tbody tr:visible",14);
      await page.getByText("All 28 prices at 12:40 p.m. and their break-even points",{exact:true}).click();
      await count("#price tbody tr:visible",28);
      assert.deepEqual([proof.confidence_reconstruction.comparisons,proof.week12_quote_check.priced_targets],[252,28]);
      assert.deepEqual([proof.strict_point_integrity.issued_forecasts,proof.strict_point_integrity.incompatible_raw_point_pairs],[107,17]);
      await noOverflow();
      await page.goto(new URL("week-12-field-notes/n208/postseason/",base).href,{waitUntil:"domcontentloaded"});
      await page.screenshot({path:path.join(output,`n208-playoffs-${width}.png`)});
    });
    await check(`${width}px: N208 Thursday publication, specialist roles and full official Circa worksheet`, async () => {
      const res=await page.goto(new URL("week-12-field-notes/n208/",base).href,{waitUntil:"domcontentloaded"});
      assert.equal(res.status(),200);
      await page.getByRole("heading",{name:"Thanksgiving forecasts",exact:true}).waitFor();
      await count("[data-game]",16);
      await page.getByRole("button",{name:"Pregame",exact:true}).click();
      await count("[data-game]:visible",14);
      await page.locator("#team-search").fill("Eagles");
      await count("[data-game]:visible",1);
      const card=page.locator("[data-game]:visible");
      assert.match(await card.innerText(),/DAL by 5\.9/);
      assert.match(await card.innerText(),/PHI \+8\.5/);
      await card.getByText("Most-wins model diagnostics",{exact:true}).click();
      assert.match(await card.innerText(),/\+14\.6/);
      await page.locator("#team-search").fill("");
      await count(".caution:visible",4);
      await page.getByRole("button",{name:"Kickoff passed",exact:true}).click();
      await count("[data-game]:visible",2);
      await count("#latest-venue-prices details",14);
      const dk=page.locator("#latest-venue-prices details").filter({hasText:"PHI at DAL"}).first();
      await dk.locator("summary").click();
      await count("#latest-venue-prices tbody tr:visible",7);
      assert.match(await dk.innerText(),/Polymarket US/);
      await page.locator("#circa").getByText("All 32 authentic Circa sides",{exact:true}).click();
      await count("#circa details tbody tr:visible",32);
      await count("#circa > .tablewrap",2);
      assert.equal(await page.locator("#circa > .tablewrap").nth(0).locator("tbody tr").count(),5);
      assert.equal(await page.locator("#circa > .tablewrap").nth(1).locator("tbody tr").count(),5);
      await noOverflow();
      await count("#phone img",11);
      for(const img of await page.locator("#phone img").all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.querySelectorAll("#phone img")].every(img=>img.complete&&img.naturalWidth>0));
      await page.screenshot({path:path.join(output,`n208-gallery-${width}.png`)});
      await page.goto(new URL("week-12-field-notes/n208/",base).href,{waitUntil:"domcontentloaded"});
      await page.screenshot({path:path.join(output,`n208-board-${width}.png`)});
      const n208=await (await page.request.get(new URL("week-12-field-notes/n208/results.json",base).href)).json();
      assert.deepEqual([n208.census,n208.candidate_count,n208.issued_game_count,n208.execution.completed_units],[164,6506,14,256]);
      assert.deepEqual([n208.champions.length,n208.incompatible_raw_strict_point_pairs.length,n208.forward_lock.model_decisions],[6,4,56]);
    });
    await check(`${width}px: N207 Thanksgiving forecast coverage and phone navigation`, async () => {
      await page.goto(new URL("week-12-field-notes/n207/", base).href, { waitUntil: "domcontentloaded" });
      await count("[data-game]", 16);
      await page.getByRole("button", { name: "Pregame", exact: true }).click();
      await count("[data-game]:visible", 14);
      await page.locator("#team-search").fill("Eagles");
      await count("[data-game]:visible", 1);
      assert.match(await text("[data-game]:visible"), /PHI.*DAL/s);
      await page.locator("#team-search").fill("");
      await page.getByRole("button", { name: "Kickoff passed" }).click();
      await count("[data-game]:visible", 2);
      await count("#circa .circa article", 5);
      await count("#circa details tbody tr", 32);
      await count("#phone img", 8);
      for (const img of await page.locator("#phone img").all()) await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(() => [...document.querySelectorAll("#phone img")].every(img => img.complete && img.naturalWidth > 0));
      assert.doesNotMatch(await text("main"), /NaN|undefined|Invalid Date/);
      await noOverflow();
      await page.screenshot({path:path.join(output,`n207-gallery-${width}.png`)});
      await page.getByRole("link", { name: "Explore all 656 contracts by game, market and price" }).click();
      await count("tbody tr",656);
      await page.getByRole("combobox",{name:"Game",exact:true}).selectOption("PHI at DAL");
      await page.getByRole("combobox",{name:"Market",exact:true}).selectOption("Total");
      await count("tbody tr:visible",19);
      await page.getByRole("combobox",{name:"Sort by",exact:true}).selectOption("yes");
      const sorted=await page.locator("tbody tr:visible").evaluateAll(rows=>rows.map(row=>Number(row.dataset.yes)));
      assert.deepEqual(sorted,[...sorted].sort((a,b)=>b-a));
      await noOverflow();
      await page.screenshot({path:path.join(output,`n207-kalshi-${width}.png`)});
      await page.goto(new URL("week-12-field-notes/n207/",base).href,{waitUntil:"domcontentloaded"});
      await page.getByRole("link",{name:"Explore all 720 Polymarket Global markets",exact:true}).click();
      await count("tbody tr",720);
      await page.getByRole("combobox",{name:"Game",exact:true}).selectOption("PHI at DAL");
      await page.getByRole("combobox",{name:"Market",exact:true}).selectOption("Total");
      await count("tbody tr:visible",21);
      await page.getByRole("combobox",{name:"Sort by",exact:true}).selectOption("second");
      const sortedSecond=await page.locator("tbody tr:visible").evaluateAll(rows=>rows.map(row=>Number(row.dataset.second)));
      assert.deepEqual(sortedSecond,[...sortedSecond].sort((a,b)=>b-a));
      await noOverflow();
      await page.screenshot({path:path.join(output,`n207-polymarket-${width}.png`)});
      await page.getByRole("link",{name:"Return to game board",exact:true}).click();
      await page.getByRole("heading",{name:"Thanksgiving game board",exact:true}).waitFor();
      await page.screenshot({path:path.join(output,`n207-board-${width}.png`)});
      await page.getByRole("link",{name:"Standing V13 champions on all 164 games and the prospective scorecard"}).click();
      await page.getByRole("heading",{name:"Frozen champions, 164 games",exact:true}).waitFor();
      await count("#champions > .tablewrap tbody tr",9);
      await page.getByText("Champions under all five validation weights",{exact:true}).click();
      await count("#sensitivity tbody tr:visible",9);
      await count("#sensitivity tbody td:visible",54);
      await page.getByText("Compare all 56 locked model picks",{exact:true}).click();
      await count("#prospective tbody tr:visible",14);
      assert.match(await text("#prospective"),/dd6f9704a7ca3255cad11478b18c99bb752ad917fbaeb0a00debea25ad64bcb8/);
      const proof=await (await page.request.get(new URL("week-12-field-notes/n207/standing-results/proof.json",base).href)).json();
      assert.deepEqual([proof.objectives.length,proof.evaluation.completed,proof.evaluation.winner_correct],[9,164,108]);
      assert(proof.objectives.every(r=>r.scored_2026_games===164 && Object.keys(r.weights).length===5));
      assert.equal(proof.prospective_scorecard.rows.length,28);
      assert.equal(proof.playoff_price_reconstruction.covered_game_targets,52);
      await noOverflow();
      await page.goto(new URL("week-12-field-notes/n207/standing-results/",base).href, {waitUntil:"domcontentloaded"});
      await page.screenshot({path:path.join(output,`n207-standing-${width}.png`)});

    });
    await check(`${width}px: N206 current forecasts, full population, authentic prices and coherent score provenance`,async()=>{
      await page.goto(new URL("week-12-field-notes/n206/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();
      await count("#games .game",n206Snapshot.games.length);await count("#completed-games tr",n206Completed);
      assert.deepEqual(await page.evaluate(()=>data.completed_population.games.map(g=>g.game_id).sort()),n206Ids);
      assert.equal(await page.locator("#basis").inputValue(),"n206");assert.match(await text("#basis-note"),/new strict-win selections/);
      assert.match(await text("#games"),/Own coherent score law/);assert.match(await text("#games"),/Final: GB 13/);
      assert.match(await text("#source-status"),/VERIFIED FINAL SOURCE REFRESH/);assert.match(await text("#source-message"),/belong to that same issue/);
      for(const row of n206Snapshot.ordinary_performance){
        assert((await text("#performance")).includes(`${row.selected.wins} wins`));
        assert((await text("#performance")).includes(`${row.earlier_week_replay.wins} wins`));
        assert((await text("#performance")).includes(`of ${n206Completed} completed games`));
      }
      await page.selectOption("#scope","remaining");await count("#games .game",n206Snapshot.games.filter(g=>!g.started_at_snapshot).length);
      await page.selectOption("#scope","thanksgiving");await count("#games .game",3);
      await page.selectOption("#scope","all");await page.fill("#search","Bears");await count("#games .game",1);await page.fill("#search","");
      for(const basis of ["v13","roster","n203","n204","n205","n206"]){await page.selectOption("#basis",basis);assert.doesNotMatch(await text("#games"),/NaN|undefined|Invalid Date/);}
      for(const objective of ["brier","logloss","strict_wins"]){
        await page.selectOption("#pick-objective",objective);
        const actual=await page.locator('#games [data-game-id="2026_12_CHI_DET"]').count();
        assert.equal(actual,1);
        const body=await page.locator('#games [data-game-id="2026_12_CHI_DET"]').innerText();
        const expected=objective==="strict_wins"?n206Snapshot.games.find(g=>g.id==="2026_12_CHI_DET").total:n206Snapshot.games.find(g=>g.id==="2026_12_CHI_DET").total.objective_options.find(r=>r.objective===objective);
        assert(body.includes(expected.side+" "+expected.line));
        assert(body.includes(objective==="strict_wins"?"Own coherent score law":"Preserved coherent N205 score law"));
        await noOverflow();
      }
      for(const source of ["draftkings","kalshi","polymarket","all"]){
        await page.selectOption("#book-source",source);
        await count("#book-options tr",source==="all"?n206Snapshot.book_options.length:n206Snapshot.book_options.filter(q=>q.source===source).length);
      }
      await page.selectOption("#book-source","kalshi");await page.selectOption("#book-game","2026_12_NE_LAC");assert.match(await text("#book-options"),/No paired decimal offer/);
      await page.locator("#direct-source").locator("xpath=ancestor::details[1]").locator("summary").click();assert.match(await text("#direct-source"),/exact settlement, push treatment and fees/);
      await page.selectOption("#book-game","all");await page.selectOption("#book-source","draftkings");await page.selectOption("#book-target","total");
      await count("#book-options tr",n206Snapshot.book_options.filter(q=>q.source==="draftkings"&&q.target==="total").length);
      await page.selectOption("#book-target","all");await page.selectOption("#book-sort","value");
      await count("#objective-metrics tr",n206Snapshot.objective_performance.length);await count("#replay-metrics tr",n206Snapshot.policy_replay.length);await count("#annual-metrics tr",n206Snapshot.annual_metrics.length);
      await count("#distribution-metrics tr",n206Snapshot.score_distribution_performance.length);
      for(const card of n206Snapshot.cards){await page.selectOption("#circa-basis",card.id);await count("#circa-five .pick",5);await count("#alternatives tr",card.alternatives.length);}
      await page.selectOption("#circa-basis","circa_card_points");await count("#phone img",7);
      for(const img of await page.locator("#phone img").all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.querySelectorAll('#phone img')].every(img=>img.complete&&img.naturalWidth>0));
      await noOverflow();await page.screenshot({path:path.join(output,`n206-${width}.png`),fullPage:true});
    });
    await check(`${width}px: N205 current forecasts, full population, authentic prices and borrowed score provenance`,async()=>{
      await page.goto(new URL("week-12-field-notes/n205/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();
      await count("#games .game",n205Snapshot.games.length);await count("#completed-games tr",n205Completed);
      assert.deepEqual(await page.evaluate(()=>data.completed_population.games.map(g=>g.game_id).sort()),n205Ids);
      assert.equal(await page.locator("#basis").inputValue(),"n205");assert.match(await text("#basis-note"),/new N205 total score law/);
      assert.match(await text("#games"),/Direct probability/);assert.match(await text("#games"),/borrowed N203 push/);
      assert.match(await text("#source-status"),/SEPARATE VERIFIED REFRESH/);assert.match(await text("#source-message"),/original owner run’s final refresh failed/);
      for(const row of n205Snapshot.ordinary_performance){
        assert((await text("#performance")).includes(`${row.selected.wins} wins`));
        assert((await text("#performance")).includes(`${row.earlier_week_replay.wins} wins`));
        assert((await text("#performance")).includes(`of ${n205Completed} completed games`));
      }
      await page.selectOption("#scope","remaining");await count("#games .game",n205Snapshot.games.filter(g=>!g.started_at_snapshot).length);
      await page.selectOption("#scope","thanksgiving");await count("#games .game",3);
      await page.selectOption("#scope","all");await page.fill("#search","Bears");await count("#games .game",1);await page.fill("#search","");
      for(const basis of ["v13","roster","n203","n204","n205"]){await page.selectOption("#basis",basis);assert.doesNotMatch(await text("#games"),/NaN|undefined|Invalid Date/);}
      for(const objective of ["brier","logloss","strict_wins"]){
        await page.selectOption("#pick-objective",objective);
        const actual=await page.locator('#games [data-game-id="2026_12_CHI_DET"]').count();
        assert.equal(actual,1);
        const body=await page.locator('#games [data-game-id="2026_12_CHI_DET"]').innerText();
        const expected=objective==="strict_wins"?n205Snapshot.games.find(g=>g.id==="2026_12_CHI_DET").total:n205Snapshot.games.find(g=>g.id==="2026_12_CHI_DET").total.objective_options.find(r=>r.objective===objective);
        assert(body.includes(expected.side+" "+expected.line));
        if(objective!=="strict_wins")assert(body.includes("Own coherent N205 score law"));
        await noOverflow();
      }
      for(const source of ["draftkings","kalshi","polymarket","all"]){
        await page.selectOption("#book-source",source);
        await count("#book-options tr",source==="all"?n205Snapshot.book_options.length:n205Snapshot.book_options.filter(q=>q.source===source).length);
      }
      await page.selectOption("#book-source","kalshi");await page.selectOption("#book-game","2026_12_NE_LAC");assert.match(await text("#book-options"),/No paired decimal offer/);
      await page.locator("#direct-source").locator("xpath=ancestor::details[1]").locator("summary").click();assert.match(await text("#direct-source"),/exact settlement, push treatment and fees/);
      await page.selectOption("#book-game","all");await page.selectOption("#book-source","draftkings");await page.selectOption("#book-target","total");
      await count("#book-options tr",n205Snapshot.book_options.filter(q=>q.source==="draftkings"&&q.target==="total").length);
      await page.selectOption("#book-target","all");await page.selectOption("#book-sort","value");
      await count("#objective-metrics tr",n205Snapshot.objective_performance.length);await count("#replay-metrics tr",n205Snapshot.policy_replay.length);await count("#annual-metrics tr",n205Snapshot.annual_metrics.length);
      await count("#distribution-metrics tr",n205Snapshot.score_distribution_performance.length);
      for(const card of n205Snapshot.cards){await page.selectOption("#circa-basis",card.id);await count("#circa-five .pick",5);await count("#alternatives tr",card.alternatives.length);}
      await page.selectOption("#circa-basis","circa_card_points");await count("#phone img",7);
      for(const img of await page.locator("#phone img").all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.querySelectorAll('#phone img')].every(img=>img.complete&&img.naturalWidth>0));
      await noOverflow();await page.screenshot({path:path.join(output,`n205-${width}.png`),fullPage:true});
    });
    await check(`${width}px: N204 current forecasts, full population, authentic prices and borrowed score provenance`,async()=>{
      await page.goto(new URL("week-12-field-notes/n204/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();
      await count("#games .game",n204Snapshot.games.length);await count("#completed-games tr",n204Completed);
      assert.deepEqual(await page.evaluate(()=>data.completed_population.games.map(g=>g.game_id).sort()),n204Ids);
      assert.equal(await page.locator("#basis").inputValue(),"n204");assert.match(await text("#basis-note"),/directly estimates cover probability/);
      assert.match(await text("#games"),/Spread: direct estimate/);assert.match(await text("#games"),/borrowed from N203/);
      for(const row of n204Snapshot.ordinary_performance){
        assert((await text("#performance")).includes(`${row.selected.wins} wins`));
        assert((await text("#performance")).includes(`${row.earlier_week_replay.wins} wins`));
        assert((await text("#performance")).includes(`of ${n204Completed} completed games`));
      }
      await page.selectOption("#scope","remaining");await count("#games .game",n204Snapshot.games.filter(g=>!g.started_at_snapshot).length);
      await page.selectOption("#scope","thanksgiving");await count("#games .game",3);
      await page.selectOption("#scope","all");await page.fill("#search","Bears");await count("#games .game",1);await page.fill("#search","");
      for(const basis of ["v13","roster","n203","n204"]){await page.selectOption("#basis",basis);assert.doesNotMatch(await text("#games"),/NaN|undefined|Invalid Date/);}
      for(const source of ["draftkings","kalshi","polymarket","all"]){
        await page.selectOption("#book-source",source);
        await count("#book-options tr",source==="all"?n204Snapshot.book_options.length:n204Snapshot.book_options.filter(q=>q.source===source).length);
      }
      await page.selectOption("#book-source","kalshi");await page.selectOption("#book-game","2026_12_NE_LAC");assert.match(await text("#book-options"),/No paired decimal offer/);
      await page.locator("#direct-source").locator("xpath=ancestor::details[1]").locator("summary").click();assert.match(await text("#direct-source"),/Earlier N203 direct observation retained/);
      await page.selectOption("#book-game","all");await page.selectOption("#book-source","draftkings");await page.selectOption("#book-target","total");
      await count("#book-options tr",n204Snapshot.book_options.filter(q=>q.source==="draftkings"&&q.target==="total").length);
      await page.selectOption("#book-target","all");await page.selectOption("#book-sort","value");
      await count("#objective-metrics tr",n204Snapshot.objective_performance.length);await count("#replay-metrics tr",n204Snapshot.policy_replay.length);await count("#annual-metrics tr",n204Snapshot.annual_metrics.length);
      for(const card of n204Snapshot.cards){await page.selectOption("#circa-basis",card.id);await count("#circa-five .pick",5);await count("#alternatives tr",card.alternatives.length);}
      await page.selectOption("#circa-basis","circa_card_points");await count("#phone img",7);
      for(const img of await page.locator("#phone img").all())await img.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.querySelectorAll('#phone img')].every(img=>img.complete&&img.naturalWidth>0));
      await noOverflow();await page.screenshot({path:path.join(output,`n204-${width}.png`),fullPage:true});
    });
    await check(`${width}px: preserved N203 forecasts, full census, bookmaker terms and preserved Circa`,async()=>{
      await page.goto(new URL("week-12-field-notes/n203/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();
      await count("#games .game",currentSnapshot.games.length);
      await count("#completed-games tr",currentCompleted);
      assert.deepEqual(await page.evaluate(()=>data.completed_population.games.map(g=>g.game_id).sort()),currentIds);
      assert.equal(await page.locator("#basis").inputValue(),"n203");
      assert.match(await text("#basis-note"),/not a separately selected winner model/);
      for(const row of currentSnapshot.ordinary_performance){
        assert((await text("#performance")).includes(`${row.selected.wins} wins`));
        assert((await text("#performance")).includes(`${row.earlier_week_replay.wins} wins`));
        assert((await text("#performance")).includes(`of ${currentCompleted} completed games`));
      }
      await page.selectOption("#scope","remaining");await count("#games .game",currentSnapshot.games.filter(g=>!g.started_at_snapshot).length);
      await page.selectOption("#scope","thanksgiving");await count("#games .game",3);
      await page.selectOption("#scope","all");await page.fill("#search","Bears");await count("#games .game",1);
      await page.fill("#search","");
      for(const basis of ["v13","roster","n203"]){await page.selectOption("#basis",basis);assert.doesNotMatch(await text("#games"),/NaN|undefined|Invalid Date/);}
      for(const source of ["draftkings","kalshi","polymarket"]){
        await page.selectOption("#book-source",source);
        await count("#book-options tr",currentSnapshot.book_options.filter(q=>q.source===source).length);
      }
      await page.selectOption("#book-source","kalshi");await page.selectOption("#book-game","2026_12_NE_LAC");
      assert.match(await text("#book-options"),/No paired decimal offer/);
      await page.locator("#direct-source").locator("xpath=ancestor::details[1]").locator("summary").click();
      assert.match(await text("#direct-source"),/KXNFLSPREAD-26NOV29NELAC-NE2/);
      assert.match(await text("#direct-source"),/yes bid 0.48 \/ ask 0.5/);
      await page.selectOption("#book-game","all");await page.selectOption("#book-source","draftkings");
      await page.selectOption("#book-target","total");await count("#book-options tr",currentSnapshot.book_options.filter(q=>q.source==="draftkings"&&q.target==="total").length);
      await page.selectOption("#book-target","all");await page.selectOption("#book-sort","value");
      assert.equal(new Set(currentSnapshot.book_options.map(q=>q.source)).size,currentSnapshot.market_coverage.usable_spread_total_bookmakers);
      await count("#ablations tr",currentSnapshot.campaign.ablations.length);
      for(const card of currentSnapshot.cards){await page.selectOption("#circa-basis",card.id);await count("#circa-five .pick",5);await count("#alternatives tr",card.alternatives.length);}
      await page.selectOption("#circa-basis","circa_card_points");await count("#phone img",7);
      await noOverflow();await page.screenshot({path:path.join(output,`n203-${width}.png`),fullPage:true});
    });
    await check(`${width}px: full completed population, every current outlook, Circa rules and phone cards`, async () => {
      await page.goto(new URL("week-12-field-notes/n202/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();
      await count("#games .game",snapshot.games.length);
      await count("#completed-games tr",completed);
      const actualIds=await page.evaluate(()=>data.completed_population.games.map(g=>g.game_id).sort());
      assert.deepEqual(actualIds,completedIds,"Every completed identity must reach the rendered page");
      for(const row of snapshot.ordinary_performance){
        assert((await text("#performance")).includes(`${row.selected.wins} wins`));
        assert((await text("#performance")).includes(`of ${completed} completed games`));
        assert((await text("#performance")).includes(`${row.earlier_week_replay.wins} wins`));
      }
      assert.doesNotMatch(await text("#performance"), /150 decisive|152 decisive|full-population champion withheld/i);
      await page.selectOption("#basis","roster");
      assert.match(await text("#games"),/No new pregame roster issue after kickoff/);
      await page.selectOption("#scope","remaining");
      await count("#games .game",snapshot.games.filter(g=>!g.started_at_snapshot).length);
      await page.selectOption("#scope","thanksgiving");
      await count("#games .game",snapshot.games.filter(g=>g.kickoff_utc>="2026-11-26T08:00:00"&&g.kickoff_utc<"2026-11-27T08:00:00").length);
      await page.selectOption("#scope","all");await page.fill("#search","Bears");await count("#games .game",1);
      await page.fill("#search","");await page.selectOption("#sort","spread");await count("#games .game",snapshot.games.length);
      await page.selectOption("#sort","kickoff");
      const displayTime=x=>new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(x));
      for(const card of snapshot.cards){
        await page.selectOption("#circa-basis",card.id);
        await count("#circa-five .pick",5);await count("#alternatives tr",card.alternatives.length);
        assert((await text("#circa-description")).includes(displayTime(card.deadline_utc)));
        assert.match(await text("#circa-description"),/account activity was not queried/);
      }
      await page.selectOption("#circa-basis","circa_card_points");
      await count("#phone img",7);await noOverflow();
      await page.screenshot({path:path.join(output,`full163-${width}.png`),fullPage:true});
    });
    await check(`${width}px: retained fieldnotes, availability, venue controls and corrected ordinary record`,async()=>{
      await page.goto(new URL("week-12-field-notes/",base).href,{waitUntil:"domcontentloaded"});
      assert.match(await text(".dateline"),/N202/);
      assert.equal(await page.locator("#ordinary table").first().locator("tbody tr").count(),snapshot.games.length);
      assert((await text("#ordinary")).toLowerCase().includes(`all ${completed} completed games`));
      assert.match(await text("#ordinary"),/reconstructed.*saved N202/i);
      await count("#latest-forecasts tbody tr",snapshot.games.length);
      assert.match(await text("#latest-forecasts"),/N201 pregame archive/);
      assert.match(await text("#latest-circa"),/Official Circa Million VIII rules 7–8/);
      assert.match(await text("#latest-circa"),/Availability-family research policy/);
      assert.match(await text("#markets"),/1,598 pregame lines/);
      await count("#latest-circa details",3);await count("#latest-circa details:nth-of-type(2) tbody tr",30);
      await count("#phone img[src^='N202-public-']",11);
      await page.selectOption("#day","Thursday");await count("article.game:visible",3);
      await page.selectOption("#day","all");await count("article.game:visible",snapshot.games.length);
      for(const venue of ["draftkings","kalshi","polymarket"]){await page.selectOption("#venue",venue);await count("[data-venue]:visible tbody tr",snapshot.games.length);}
      await count("#availability details.health",16);await count("#availability .health-grid article",32);await noOverflow();
      await page.goto(new URL("week-12-field-notes/n202-weekly/",base).href,{waitUntil:"domcontentloaded"});
      await page.locator("#games .game").first().waitFor();await count("#games .game",snapshot.games.length);
      assert.match(await text("main"),/FULL-163 REVIEW/);await noOverflow();
    });
    await check(`${width}px: N195 official research choices and source-matched comparisons`, async () => {
      await page.goto(new URL('against-the-spread/', base).href, {waitUntil:'domcontentloaded'});
      await count('[data-n195="official-games"] tbody tr', 16);
      await count('[data-n195="dk-games"] tbody tr', 16);
      await count('[data-n195="annual"] tbody tr', 15);
      await count('[data-n195="ratios"] tbody tr', 15);
      await count('#five .cards li',15);
      for (const role of ['top5_points','all_points','direct_brier']) {
        const opts = page.locator('[data-n195="alternatives-'+role+'"]');
        const panel = opts.locator('xpath=ancestor::details[1]');
        await panel.locator('summary').click();
        assert.equal(await opts.locator('tbody tr').count(),32);
        assert.equal(await opts.locator('td').filter({hasText:/^Card #[1-5]$/}).count(),5);
        await noOverflow();
        await panel.locator('summary').click();
      }

      await count('#n195-week12-phone a img',4);
      assert.match(await text('#lines'), /55 adjacent strike checks, the specialist failed 52/);
      assert.match(await text('main'), /Zero contest entries/);
      await noOverflow();
    });
    await check(`${width}px: home opens the current release; older shared links still open the original dated slate`, async () => {
      await page.goto(base.href, { waitUntil: "domcontentloaded" });
      await noOverflow();
      assert.match(await text("#n206-complete-population-notice"),/N206 completed/);
      assert.equal(await page.locator('#n206-complete-population-notice a[href="week-12-field-notes/n206/"]').count(),1);
      assert.match(await page.locator("body").innerText(), /Week 12/i);
      assert(page.url().startsWith(base.href));
      assert.match(await text(".hero-stats"), /LAR by 4.66|Rams by 4.66/);
      assert.match(await text(".hero-footer"), /10:08 PM PT/);
      assert.match(await text("#results"), /N190 VS N189/i);
      await count("#completed-games tbody tr", 163);
      await count("[data-interval-weight] tbody tr", 40);
      await count("[data-interval-reliability] tbody tr", 18);
      await count("[data-interval-replay-week] tbody tr", 163);
      await count("[data-ats-horizons] tbody tr", 206);
      await count("#slate [data-range-game]", 16);
      await count("#slate [data-event-game]", 16);
      await count("#slate [data-n193-game]",16);
      await count("[data-n194-validation] tbody tr",45);
      await count("[data-n194-replay] tbody tr",163);
      await count("[data-n194-ats-live] tbody tr",16);
      await count("[data-n194-ats-history] tbody tr",3);
      await count("#slate [data-n194-game]",16);
      assert.match(await text("#situation-review"),/0 of 9/);
      await count("[data-n193-validation] tbody tr",45);
      await count("[data-n193-replay] tbody tr",163);
      assert.match(await text("#score-review"),/1 of 9/);
      await count("[data-event-weight] tbody tr",80);
      await count("[data-event-replay-week] tbody tr",163);
      await count("[data-event-calibration] tbody tr",240);
      assert.match(await text("#game-events"), /2\/16/);
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
      assert.match(await text("[data-market-game]:visible"), /Kalshi/);
      await page.locator("#market-matchup").selectOption("2026_12_GB_LA");
      assert.equal(await page.locator(".source-ledger summary").filter({hasText:receipt.scientific_scope.markets.sources + " sources"}).count(), 1);
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
    await check(`${width}px: all-games policy comparison, 18 annual records and 96 signed model sides`, async () => {
      await page.goto(new URL("circa/",base).href);
      await page.locator("#circa .contest-intro").getByRole("link",{name:"Compare all 16 games, the weekly five and the remaining sides"}).click();
      await page.waitForURL(u=>u.pathname.endsWith("/all-games/"));
      await count("section[data-policy]",6);
      await count(".season",18);
      await count("tr[data-game]",96);
      for (const key of ["standing","all","hybrid","law","edge","historic"]) {
        await page.locator("#policy").selectOption(key);
        await count("section[data-policy]:visible",1);
        const panel=page.locator("section[data-policy]:visible");
        assert.equal(await panel.getAttribute("data-policy"),key);
        assert.equal(await panel.locator("tr[data-game]").count(),16);
        assert.equal(await panel.locator(".season").count(),3);
        await noOverflow();
      }
      await page.goto(new URL("all-games/#policy-hybrid",base).href);
      await page.waitForFunction(()=>document.getElementById("policy").value==="hybrid");
      assert.equal(await page.locator("#policy").inputValue(),"hybrid");
      assert.match(await text("main"),/46,019/);
      assert.match(await text("section[data-policy]:visible"),/108.5 points/);
      await page.screenshot({path:path.join(output,`all-games-${width}.png`),fullPage:false});
    });
    await check(width + "px: dedicated Circa dashboard with all alternatives and 47 graded cards", async () => {
      await page.goto(new URL("circa/", base).href);
      assert.equal(await text("h1"), "Circa Million Picks & Performance Dashboard");
      await count("[data-card-season] tbody tr", 47);
      await count("[data-card-validation] tbody tr", 5);
      await count("[data-n191-card-rule] tbody tr", 15);
      await count("[data-card-vintages] tbody tr", 5);
      await count("[data-n191-cards-annual] tbody tr", 9);
      await count("[data-weekly-utility-weight] tbody tr",15);
      await count("[data-weekly-official] tbody tr",96);
      await count("[data-n194-sides] tbody tr",160);
      await count("[data-n194-card-weight] tbody tr",25);
      await count("[data-n194-current-cards] tbody tr",5);
      await count("[data-n193-sides] tbody tr",96);
      await count("[data-n193-contest-weight] tbody tr",25);
      await count("[data-n193-legacy] tbody tr",35);
      await count("[data-weekly-utility-five] tbody tr",5);
      assert.match(await text("main"), /Expected points across these five selections/);
      assert.match(await text("#historic-rules"), /28.5 out of 45/);
      assert.match(await text("#historic-rules"), /30.5\/55/);
      await count("#option-grid tbody tr", 32);
      await page.locator("#rank-filter").selectOption("top");
      await count(".contest-game:visible", 5);
      await page.locator("#contest-search").fill("does-not-match");
      await count(".contest-game:visible", 0);
      await noOverflow();
    });
    await check(width + "px: Thanksgiving and every scheduled week open on clean, shareable routes", async () => {
      await page.goto(new URL("thanksgiving/", base).href);
      await noOverflow();
      await count("[data-fixture]", 3);
      assert.deepEqual(await page.locator("[data-fixture]").evaluateAll(nodes => nodes.map(n => n.dataset.fixture)), ["2026_12_CHI_DET","2026_12_PHI_DAL","2026_12_KC_BUF"]);
      await count("a.gallery-card", 4);
      let scheduled = 0;
      for (let week = 12; week <= 18; week++) {
        await page.goto(new URL("weeks/" + week + "/", base).href);
        await noOverflow();
        const fixtures = await page.locator("[data-fixture]").count();
        await count("[data-range-game]", fixtures);
        await count("[data-event-game]", fixtures);
        await count("[data-n193-game]",fixtures);
        await count("[data-n194-game]",fixtures);
        scheduled += fixtures;
      }
      assert.equal(scheduled, 109);
      await page.goto(new URL("#current-objectives", base).href);
      await count("[data-current-ratio] tbody tr", 15);
      await count("#aux-replays tbody tr", 163);
      await count("#cards a.gallery-card", 18);
      await count("#cards a.gallery-card[href*=n194-circa]", 9);
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


