/* Sports Edge Lab NFL. Static, dependency-free presentation of saved evidence. */
"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (value) => value === null || value === undefined || value === "" || typeof value === "boolean" ? null : Number.isFinite(Number(value)) ? Number(value) : null;
  const probability = (value) => { const n = num(value); return n !== null && n >= 0 && n <= 1 ? n : null; };
  const pct = (value, digits = 1) => probability(value) === null ? "—" : `${(Number(value) * 100).toFixed(digits)}%`;
  const decimal = (value, digits = 1) => num(value) === null ? "—" : Number(value).toFixed(digits);
  const sign = (value) => num(value) === null ? "—" : Number(value) === 0 ? "PK" : `${Number(value) > 0 ? "+" : "−"}${Math.abs(Number(value)).toFixed(Number.isInteger(Number(value)) ? 0 : 1)}`;
  const urlOK = (value) => typeof value === "string" && (/^https?:\/\//i.test(value) || /^(?:\.\.?\/|\/|\?)/.test(value)) && !/[\u0000-\u0020]/.test(value) ? value : null;
  const dateValue = (value) => { if (!value) return null; const d = new Date(value); return Number.isNaN(d.getTime()) ? null : d; };
  const datePT = (value, options = {}) => { const d = dateValue(value); return d ? new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", ...options }).format(d) : null; };
  const longDate = (value) => datePT(/^\d{4}-\d{2}-\d{2}$/.test(value || "") ? `${value}T20:00:00Z` : value, { weekday: "long", month: "long", day: "numeric" });
  const shortDate = (value) => datePT(value, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  const plainText = (value, fallback = "") => typeof value === "string" ? value : fallback;
  const state = { data: null, view: "slate", day: "sunday", search: "", sort: "kickoff", circaSort: "kickoff", horizon: "all", newestHorizon: 60, forecastClock: "T120", cardType: "games", page: 1, picks: new Map(), toastTimer: null };
  const key = () => `sports-edge-nfl-card-${state.data?.season || ""}-${state.data?.week || state.data?.slate_date || ""}`;
  const forecastFields = ["win_home","win_away","tie_probability","probability_home","probability_away","probability_tie","margin_home","total","issued_at","forecast_issued_at","compiled_at","model_roles","forecast_status","forecast_label","forecast_note","card_note","evidence_label","winner_target","winner_target_label","as_of"];
  const selectedForecast = (g) => {
    const f=g.forecasts?.[state.forecastClock];
    const selected={...g};
    for(const field of forecastFields)selected[field]=null;
    if(f&&typeof f==="object")for(const field of forecastFields)if(Object.prototype.hasOwnProperty.call(f,field))selected[field]=f[field];
    if(!f){selected.forecast_label=`${state.forecastClock} unavailable`;selected.forecast_note="No qualified current forecast for this clock.";selected.evidence_label="No qualified current forecast. No value was borrowed from another clock.";}
    return selected;
  };
  const currentGames = () => (state.data?.games || []).filter((g) => g && typeof g === "object").map(selectedForecast);
  const forecastMeta = () => { const d=state.data||{},provided=d.forecast_clock_meta?.[state.forecastClock]||{},dates=[...new Set((d.games||[]).map(g=>g.forecasts?.[state.forecastClock]?.as_of).filter(Boolean))];return {label:provided.label || (state.forecastClock==="T120"?"T120 · best usable snapshot":"T60 audit · unavailable"),as_of:provided.as_of || (dates.length===1?dates[0]:null),description:provided.description || (state.forecastClock==="T120"?"Best usable saved outlook. Each model retains its original issue time and source conditions.":"Current selected T60 outputs are unavailable. Historical validation scores do not qualify missing current-game inputs.")}; };
  const gameId = (g) => String(g.id ?? `${g.away}-${g.home}-${g.kickoff_utc || g.date_pt || ""}`);
  const dayOf = (g) => { const d = dateValue(g.kickoff_utc); return d ? datePT(d, { weekday: "long" }).toLowerCase() : plainText(g.day).toLowerCase() || (/^\d{4}-\d{2}-\d{2}$/.test(g.date_pt || "") ? datePT(`${g.date_pt}T20:00:00Z`, { weekday: "long" }).toLowerCase() : "tbd"); };
  const kickoff = (g, showDay = true) => g.kickoff_pt || datePT(g.kickoff_utc, { ...(showDay ? { weekday: "short" } : {}), hour: "numeric", minute: "2-digit" })?.concat(" PT") || "Kickoff TBD";
  const teamCode = (g, side) => plainText(g[side], side === "home" ? "HOME" : "AWAY");
  const teamName = (g, side) => plainText(g[`${side}_name`], teamCode(g, side));
  const teamParts = (g, side) => { const full = teamName(g, side); const code = teamCode(g, side); const nickname = plainText(g[`${side}_nickname`]); if (nickname) return { city: full.endsWith(nickname) ? full.slice(0, -(nickname.length + 1)) : full, nickname }; const parts = full.split(" "); return parts.length > 1 ? { city: parts.slice(0, -1).join(" "), nickname: parts.at(-1) } : { city: full, nickname: code === full ? "" : code }; };
  const winProbabilities = (g) => { const home=probability(g.win_home ?? g.probability_home), explicitAway=probability(g.win_away ?? g.probability_away), tie=probability(g.tie_probability ?? g.probability_tie); const target=plainText(g.winner_target || state.data?.winner_target).toLowerCase(); const mayComplement=target.includes("binary") || tie===null || tie===0; const away=explicitAway!==null?explicitAway:home!==null&&mayComplement?1-home:null; return {home,away,tie}; };
  const winner = (g) => { const {home,away}=winProbabilities(g);if(home===null||away===null)return {code:"",chance:null,side:null};if(home===away)return {code:"Even",chance:home,side:"even"};return home>away?{code:teamCode(g,"home"),chance:home,side:"home"}:{code:teamCode(g,"away"),chance:away,side:"away"}; };
  const margin = (g) => { const m = num(g.margin_home); return m === null ? { code: "", points: null, text: "Unavailable" } : m === 0 ? { code: "Even", points: 0, text: "Even projection" } : { code: teamCode(g, m > 0 ? "home" : "away"), points: Math.abs(m), text: `${teamCode(g, m > 0 ? "home" : "away")} by ${Math.abs(m).toFixed(1)}` }; };
  const isComplete = (g) => winner(g).chance !== null && num(g.margin_home) !== null && num(g.total) !== null;
  const clock = (g) => g.issued_at || g.forecast_issued_at || null;
  const forecastTimeLabel = (g) => clock(g)?`Issued ${shortDate(clock(g))||clock(g)} PT`:g.compiled_at?`Compiled ${shortDate(g.compiled_at)||g.compiled_at} PT`:g.as_of?`Snapshot ${shortDate(g.as_of)||g.as_of} PT`:"Original issue time unavailable";
  const phoneSnapshotLabel = (g) => { const snapshot=g.as_of || forecastMeta().as_of;return snapshot?`Snapshot ${datePT(snapshot,{month:"short",day:"numeric"})||snapshot}`:g.compiled_at?`Compiled ${datePT(g.compiled_at,{month:"short",day:"numeric"})||g.compiled_at}`:"Snapshot date unavailable"; };
  const roleName = (role) => typeof role === "string" ? role : role && typeof role === "object" ? plainText(role.alias || role.name || role.label) : "";
  const roleClock = (role) => role && typeof role === "object" ? plainText(role.horizon || role.information_clock || role.clock || role.clock_group) : "";
  const roleDetail = (role) => { if(!role || typeof role!=="object")return roleName(role);return [roleName(role),roleClock(role),plainText(role.objective_label || role.objective).replaceAll("_"," ")].filter(Boolean).join(" · "); };
  const roleClockSummary = (g) => { const r=g.model_roles||{};return [["Win",r.winner],["Margin",r.margin],["Total",r.total]].filter(([,v])=>roleClock(v)).map(([k,v])=>`${k} ${roleClock(v)}`).join(" · "); };
  const winnerCaption = (g,w) => { if(!w.code)return "Unavailable";const target=plainText(g.winner_target || state.data?.winner_target).toLowerCase();const conditionalNonTie=target.includes("non_tie")||(target.startsWith("binary")&&target.includes("conditional"));return `${w.code}${conditionalNonTie?" · non-tie":" outright"}`; };
  const badge = (g) => {
    if (g.forecast_label) return { text: plainText(g.forecast_label), cls: isComplete(g) ? "" : "gap" };
    if (!isComplete(g)) return { text: probability(g.win_home) === null && num(g.margin_home) === null && num(g.total) === null ? "Forecast unavailable" : "Partial outlook", cls: "gap" };
    const status = plainText(g.forecast_status).toLowerCase();
    if (status.includes("early")) return { text: "Early outlook", cls: "" };
    if (status.includes("preserv") || status.includes("archiv")) return { text: "Saved outlook", cls: "neutral" };
    if (status.includes("reconstr")) return { text: "Reconstructed", cls: "neutral" };
    return { text: "Saved outlook", cls: "" };
  };
  const sortedGames = (games, mode) => [...games].sort((a, b) => {
    if (mode === "probability") { const diff = (winner(b).chance ?? -1) - (winner(a).chance ?? -1); if (diff) return diff; }
    if (mode === "expected") { const diff = Math.max(sideData(b, "home").expected ?? -1, sideData(b, "away").expected ?? -1) - Math.max(sideData(a, "home").expected ?? -1, sideData(a, "away").expected ?? -1); if (diff) return diff; }
    return (dateValue(a.kickoff_utc)?.getTime() ?? Infinity) - (dateValue(b.kickoff_utc)?.getTime() ?? Infinity) || gameId(a).localeCompare(gameId(b));
  });

  function gameCard(g) {
    const w = winner(g), m = margin(g), probs = winProbabilities(g), a = teamParts(g, "away"), h = teamParts(g, "home"), b = badge(g);
    const roles = g.model_roles || {};
    const evidenceRows = [["Win probability", roleDetail(roles.winner)], ["Winner target", g.winner_target_label || state.data?.winner_target_label], ["Point margin", roleDetail(roles.margin)], ["Game total", roleDetail(roles.total)], ["Original forecast issue", shortDate(clock(g)) ? `${shortDate(clock(g))} PT` : "Not established as an original issue"], ["Forecast compiled",g.compiled_at?`${shortDate(g.compiled_at)||g.compiled_at} PT`:null], ["Input snapshot",g.as_of?`${shortDate(g.as_of)||g.as_of} PT`:null], ...[["Win issue",roles.winner],["Margin issue",roles.margin],["Total issue",roles.total]].filter(([,r])=>r&&typeof r==="object"&&r.issued_at).map(([label,r])=>[label,`${shortDate(r.issued_at)||r.issued_at} PT`]), ["Evidence class", g.evidence_label || g.forecast_note || "Saved selected output"]].filter(([, v]) => v);
    const probabilityLabels=`<div class="win-labels"><span>${esc(g.away)} <strong>${pct(probs.away)}</strong></span>${probs.tie>0?`<span class="tie-label">Tie ${pct(probs.tie)}</span>`:""}<span><strong>${pct(probs.home)}</strong> ${esc(g.home)}</span></div>`;
    const probabilityLine = probs.home===null&&probs.away===null ? `<div class="win-labels"><span>Win probability</span><strong>Unavailable</strong></div><div class="probability-gap"></div>` : probs.home===null||probs.away===null ? `${probabilityLabels}<div class="probability-gap"></div>` : `${probabilityLabels}<div class="probability-track" role="img" aria-label="${esc(g.away)} ${pct(probs.away)}; ${esc(g.home)} ${pct(probs.home)}${probs.tie>0?`; tie ${pct(probs.tie)}`:""}"><span class="${probs.away>probs.home?"leader":""}" style="width:${(probs.away*100).toFixed(5)}%"></span>${probs.tie>0?`<span class="tie-segment" style="width:${(probs.tie*100).toFixed(5)}%"></span>`:""}<span class="${probs.home>=probs.away?"leader":""}" style="width:${(probs.home*100).toFixed(5)}%"></span></div>`;
    return `<article class="game-card" data-game-id="${esc(gameId(g))}" aria-label="${esc(teamName(g,"away"))} at ${esc(teamName(g,"home"))}"><div class="game-topline"><time${g.kickoff_utc ? ` datetime="${esc(g.kickoff_utc)}"` : ""}>${esc(kickoff(g))}</time><span class="status-badge ${b.cls}">${esc(b.text)}</span></div><div class="matchup"><div class="team-block"><span class="team-badge">${esc(teamCode(g,"away"))}</span><div class="team-city">${esc(a.city)}</div><div class="team-nickname">${esc(a.nickname)}</div></div><span class="matchup-at">${g.neutral ? "vs" : "at"}</span><div class="team-block home"><span class="team-badge">${esc(teamCode(g,"home"))}</span><div class="team-city">${esc(h.city)}</div><div class="team-nickname">${esc(h.nickname)}</div></div></div><div class="win-comparison">${probabilityLine}</div><div class="projection-grid"><div><span class="metric-label">Win probability</span><strong class="metric-value">${pct(w.chance)}<small></small></strong><span class="metric-sub">${esc(winnerCaption(g,w))}</span></div><div><span class="metric-label">Margin</span><strong class="metric-value">${decimal(m.points)}<small>${m.points !== null ? " pts" : ""}</small></strong><span class="metric-sub">${esc(m.code ? `${m.code}${m.points === 0 ? " projection" : " advantage"}` : "Unavailable")}</span></div><div><span class="metric-label">Total points</span><strong class="metric-value">${decimal(g.total)}</strong><span class="metric-sub">${num(g.total) !== null ? "Combined score" : "Unavailable"}</span></div></div><div class="forecast-foot"><span>${esc(forecastTimeLabel(g))}</span><details class="card-details"><summary>Model details</summary><div class="card-evidence"><dl>${evidenceRows.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>${g.note ? `<p>${esc(g.note)}</p>` : ""}</div></details></div></article>`;
  }

  function renderSlate() {
    const all = currentGames();
    const q = state.search.toLowerCase().trim();
    const games = sortedGames(all.filter(g => (state.day === "all" || dayOf(g) === state.day) && (!q || [g.away,g.home,g.away_name,g.home_name].some(t=>plainText(t).toLowerCase().includes(q)))), state.sort);
    $("games-grid").innerHTML = games.length ? games.map(gameCard).join("") : `<div class="empty-state"><h3>${all.length ? "No matchups in this view." : "The verified slate is being prepared."}</h3><p>${all.length ? "Try another day or a different team name." : "Game forecasts appear here when their saved model outputs and issue dates have been reconciled."}</p></div>`;
    $("game-count").textContent = `${games.length} ${games.length === 1 ? "game" : "games"}${q ? ` matching “${state.search.trim()}”` : ""} · ${state.day === "all" ? "Sunday + Monday" : state.day.charAt(0).toUpperCase()+state.day.slice(1)} · Pacific time`;
    document.querySelectorAll("[data-day]").forEach(b=>{const active=b.dataset.day===state.day;b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));});
  }

  function sideData(g, side) {
    const c = g.circa || {}, homeSpread = num(c.home_spread), spread = homeSpread === null ? null : side === "home" ? homeSpread : -homeSpread;
    const cover = probability(c[`cover_${side}`]);
    const push = probability(c[`push_${side}`] ?? c.push);
    const savedExpected = probability(c[`expected_${side}`]);
    const expected = cover !== null && push !== null ? cover + .5 * push : savedExpected;
    const expectedConsistent = savedExpected === null || expected === null || Math.abs(savedExpected - expected) <= .001;
    const outcomeMass = probability(c.cover_home) !== null && probability(c.cover_away) !== null && probability(c.push) !== null ? Number(c.cover_home)+Number(c.cover_away)+Number(c.push) : null;
    const distributionValid = outcomeMass === null || Math.abs(outcomeMass-1) <= .003;
    const halfPointValid = spread === null || Number.isInteger(spread) || push === 0;
    const upcoming = g.remaining !== false && g.status !== "final" && g.status !== "completed";
    const eligible = c.line_verified === true && spread !== null && cover !== null && push !== null && expected !== null && expected <= 1 && expectedConsistent && distributionValid && halfPointValid && upcoming;
    return { side, cover, push, expected, spread, eligible, code: teamCode(g,side), label: `${teamCode(g,side)} ${sign(spread)}` };
  }
  const circaGames = () => currentGames().filter(g => g.remaining !== false && g.status !== "final" && g.status !== "completed" && g.circa !== false);

  function circaSide(g, side) {
    const s = sideData(g, side), chosen = state.picks.get(gameId(g)) === side;
    const reason = !g.circa?.line_verified ? "Official line verification pending" : s.cover === null || s.push === null ? "Cover distribution unavailable" : !s.eligible ? "Evidence review pending" : chosen ? "Remove from research card" : "Add to research card";
    return `<div class="circa-side${chosen ? " selected" : ""}"><div class="side-team">${esc(s.label)}<small>${esc(teamParts(g,side).nickname || teamName(g,side))}</small></div><div class="side-stat${s.cover === null ? " missing" : ""}">${pct(s.cover)}</div><div class="side-stat${s.push === null ? " missing" : ""}">${pct(s.push)}</div><div class="side-stat expected${s.expected === null ? " missing" : ""}">${decimal(s.expected,3)}</div><button type="button" class="side-add" data-pick-game="${esc(gameId(g))}" data-pick-side="${side}" aria-pressed="${chosen}" aria-label="${esc(`${reason}: ${s.label}`)}" title="${esc(reason)}"${!s.eligible ? " disabled" : ""}>${chosen ? "✓" : "+"}</button></div>`;
  }
  function renderCirca() {
    const games = sortedGames(circaGames(), state.circaSort);
    $("circa-board").innerHTML = games.length ? games.map(g=>{
      const c=g.circa || {}, source=urlOK(c.source_url), h=sideData(g,"home"), a=sideData(g,"away");
      const note = c.note || (c.line_verified !== true ? "Official contest line not yet verified." : !h.eligible || !a.eligible ? "Official line verified. Complete cover and push probabilities are unavailable." : "Official line verified. Saved model distribution available.");
      return `<article class="circa-game" data-circa-game="${esc(gameId(g))}"><div class="circa-game-head"><h3>${esc(teamCode(g,"away"))} <span class="muted">at</span> ${esc(teamCode(g,"home"))}</h3><time>${esc(kickoff(g))}</time></div><div class="circa-columns" aria-hidden="true"><span>Contest side</span><span>Cover</span><span>Push</span><span>Exp. pts</span><span></span></div>${circaSide(g,"away")}${circaSide(g,"home")}<div class="circa-source"><span>${esc(note)}</span>${source ? `<a href="${esc(source)}" target="_blank" rel="noopener noreferrer">Official sheet</a>` : ""}</div></article>`;
    }).join("") : `<div class="empty-state"><h3>Contest board pending.</h3><p>The complete set of remaining games will appear with both sides and their verified contest spreads.</p></div>`;
    $("circa-coverage-label").textContent = `${games.filter(g=>g.circa?.line_verified===true).length} / ${games.length} lines verified`;
    renderPicks();
  }
  function persistPicks() { try { localStorage.setItem(key(), JSON.stringify([...state.picks])); } catch {} }
  function renderPicks() {
    const games = circaGames(), selected=[];
    for (const [id,side] of state.picks) { const g=games.find(g=>gameId(g)===id); if(g && sideData(g,side).eligible) selected.push({g,...sideData(g,side)}); else state.picks.delete(id); }
    $("pick-count").textContent = `${selected.length} / 5`;
    $("picked-sides").innerHTML = [...selected.map(s=>`<div class="picked-item"><div><strong>${esc(s.label)}</strong><small>${decimal(s.expected,3)} pts</small></div><button type="button" data-remove-pick="${esc(gameId(s.g))}" aria-label="Remove ${esc(s.label)}">×</button></div>`), ...Array.from({length:Math.max(0,5-selected.length)},(_,i)=>`<div class="pick-placeholder"><span>${selected.length+i+1}</span> Choose a game</div>`)].join("");
    $("pick-expected").textContent = selected.length ? `${selected.reduce((sum,s)=>sum+s.expected,0).toFixed(3)}` : "—";
    const eligibleGames = games.filter(g=>sideData(g,"home").eligible || sideData(g,"away").eligible).length;
    $("best-card").disabled = eligibleGames<5;
    $("best-card").title = eligibleGames<5 ? `${eligibleGames} games currently have complete verified contest evidence; five are required.` : "Choose the highest expected side from five different eligible games";
    $("pick-explainer").textContent = eligibleGames<5 ? `Only ${eligibleGames} ${eligibleGames===1?"game has":"games have"} complete verified line and cover evidence. The five-game selection becomes available when five are ready.` : "Choose one side from five different games with verified lines and available cover probabilities.";
    $("clear-card").disabled=selected.length===0;
  }
  function togglePick(id, side) {
    const g=circaGames().find(g=>gameId(g)===id);if(!g || !sideData(g,side).eligible)return;
    if(state.picks.get(id)===side)state.picks.delete(id);else{if(!state.picks.has(id)&&state.picks.size>=5){toast("Your card already has five games. Remove one to add another.");return;}state.picks.set(id,side);}
    persistPicks();renderCirca();
  }

  const objectiveLabels = { binary_accuracy:"Winner accuracy",binary_log_loss:"Probability log loss",binary_brier:"Probability Brier score",margin_mae:"Margin absolute error",margin_rmse:"Margin squared error",margin_crps:"Margin distribution",total_mae:"Total absolute error",total_rmse:"Total squared error",total_crps:"Total distribution",spread_accuracy:"Spread accuracy",spread_log_loss:"Spread log loss",spread_brier:"Spread Brier score",total_accuracy:"Over / under accuracy",total_log_loss:"Over / under log loss",total_brier:"Over / under Brier score" };
  const perfHorizon=(p)=>plainText(p.horizon || p.information_clock || p.clock_group,"Saved cohort");
  const perfValue=(p,value)=> /accuracy|percent/i.test(p.objective || p.format || "") || p.format==="percent" ? pct(value,1) : decimal(value,p.digits ?? (/loss|brier/i.test(p.objective || "")?3:2));
  function performanceCard(p) {
    const objective=p.objective || p.role || "",name=p.label || objectiveLabels[objective] || objective.replaceAll("_"," "),alias=p.alias || p.role_alias || p.model || "Selected model",higher= /accuracy/.test(objective) || p.lower_is_better===false;
    const descriptive=p.is_descriptive===true || /descriptive|new.fit|diagnostic/i.test(p.evaluation_class || p.evidence_class || "");
    const v=p.display_value ?? p.validation_score ?? p.validation ?? p.score ?? null;
    const scoreLabel=p.score_label || p.validation_label || (descriptive?"Descriptive saved score":"50 / 50 validation");
    const statusLabel=p.status_label || (descriptive?"Descriptive evaluation · no promotion established":"Validation nominee · acceptance remains partial");
    const co=Array.isArray(p.co_leaders) ? p.co_leaders : [];
    const aliasText=co.length ? `${alias} · ${co.length} tied nominees` : alias;
    const annuals = [{year:"2024",value:p.season_2024 ?? p.validation_2024,games:p.games_2024},{year:"2025",value:p.season_2025 ?? p.validation_2025,games:p.games_2025},{year:"2026",value:p.test_2026 ?? p.season_2026,games:p.games_2026}];
    const horizon=perfHorizon(p);
    return `<article class="performance-card"><div class="metric-category"><span>${esc(/margin/.test(objective)?"POINT MARGIN":/total/.test(objective)?"GAME TOTAL":"WINNER MODEL")}</span><span>${esc(horizon)}</span></div><h3>${esc(name)}</h3><p class="performance-alias">${esc(aliasText)}${p.model_family?` · ${esc(p.model_family)}`:""}</p><div class="performance-main"><strong class="performance-value">${perfValue(p,v)}</strong><small>${esc(scoreLabel)}<br>${higher?"Higher is better":"Lower is better"}</small></div><table class="annual-table"><caption class="sr-only">${esc(name)} performance by season</caption><thead><tr><th scope="col">Season</th><th scope="col">Score</th><th scope="col">Games</th></tr></thead><tbody>${annuals.map(a=>`<tr><td>${a.year}${a.year==="2026"?"*":""}</td><td>${perfValue(p,a.value)}</td><td>${num(a.games)===null?"—":Number(a.games).toLocaleString("en-US")}</td></tr>`).join("")}</tbody></table><p class="performance-note">${esc(p.note || (num(p.test_2026 ?? p.season_2026)===null?"2026 regrade unavailable. Missing values remain explicit.":"*2026 is a saved exposed evaluation, separate from the 2024–2025 selection."))}</p><div class="performance-foot">${esc(statusLabel)}${p.cohort ? `<br>${esc(p.cohort)}` : ""}</div></article>`;
  }
  function renderPerformance() {
    const rows=(state.data.performance||[]).filter(p=>state.horizon==="all" || perfHorizon(p)===state.horizon);
    $("performance-grid").innerHTML = rows.length ? rows.map(performanceCard).join("") : `<div class="empty-state"><h3>Performance evidence pending.</h3><p>Metric-specific leaders appear only after their saved annual scores, target definitions and game denominators have been reconciled.</p></div>`;
  }

  function renderNewestComparison() {
    const comparison=state.data?.newest_model_comparison,all=comparison?.rows;
    $("newest-comparison").hidden=!Array.isArray(all)||!all.length;
    if(!Array.isArray(all)||!all.length)return;
    const horizons=[...new Set(all.map(r=>num(r.horizon_minutes)).filter(v=>v!==null))].sort((a,b)=>a-b);
    if(!horizons.includes(state.newestHorizon))state.newestHorizon=horizons[0];
    $("newest-horizon").innerHTML=horizons.map(h=>`<option value="${h}"${h===state.newestHorizon?" selected":""}>T${h} comparison</option>`).join("");
    const rows=all.filter(r=>num(r.horizon_minutes)===state.newestHorizon),objectives=new Set(all.map(r=>r.objective)).size,improved=all.filter(r=>r.new_fit_beats_incumbent===true).length;
    $("newest-summary").innerHTML=`<div><strong>${esc(comparison.models_checked ?? "—")}</strong><span>newer models checked</span></div><div><strong>${objectives}</strong><span>objectives · ${horizons.length} clocks</span></div><div><strong>${improved}</strong><span>of ${all.length} comparisons improved</span></div><p>${improved===0?"The latest batch did not beat the retained validation nominees on any checked objective. No promotion was made.":"Saved validation comparisons are shown below. A numerical improvement does not establish a production promotion."}</p>`;
    const score=(r,v)=>/accuracy/.test(r.objective)?pct(v,2):decimal(v,/loss|brier/.test(r.objective)?3:2);
    const delta=(r)=>{const v=num(r.new_minus_incumbent);if(v===null)return "—";const sign=v>0?"+":v<0?"−":"";return /accuracy/.test(r.objective)?`${sign}${Math.abs(v*100).toFixed(2)} pp`:`${sign}${Math.abs(v).toFixed(/loss|brier/.test(r.objective)?3:2)}`;};
    $("newest-table").innerHTML=`<table class="comparison-table"><caption class="sr-only">Same-cohort validation comparison at T${state.newestHorizon}</caption><thead><tr><th scope="col">Objective</th><th scope="col">R18 leader</th><th scope="col">Best R20</th><th scope="col">Change</th></tr></thead><tbody>${rows.map(r=>`<tr><th scope="row">${esc(r.label || r.objective)}<small>${esc(r.games_2024 ?? "—")} / ${esc(r.games_2025 ?? "—")} games</small></th><td>${score(r,r.incumbent_validation)}</td><td>${score(r,r.best_new_validation)}</td><td class="${r.new_fit_beats_incumbent===true?"comparison-better":"comparison-worse"}">${delta(r)}</td></tr>`).join("")}</tbody></table>`;
    $("newest-test-table").innerHTML=`<table class="comparison-table"><caption class="sr-only">2026 scores for the validation-selected candidates at T${state.newestHorizon}</caption><thead><tr><th scope="col">2026 evaluation</th><th scope="col">R18 leader</th><th scope="col">Selected R20</th><th scope="col">Games</th></tr></thead><tbody>${rows.map(r=>`<tr><th scope="row">${esc(r.label || r.objective)}</th><td>${score(r,r.incumbent_2026)}</td><td>${score(r,r.validation_selected_new_2026)}</td><td>${esc(r.games_2026 ?? "—")}</td></tr>`).join("")}</tbody></table>`;
    $("newest-qualification").textContent=`Validation gives equal weight to the 2024 and 2025 annual scores; 2026 does not select the candidate. Row game counts show 2024 / 2025 support. ${plainText(comparison.comparison_qualification)} This comparison reads existing saved predictions and performs no new fits.`;
  }

  function phoneGame(g) {
    const w=winner(g),m=margin(g),b=badge(g),probs=winProbabilities(g);
    return `<section class="phone-game"><div class="phone-game-top"><span>${esc(kickoff(g))}</span><span>${esc(b.text)}</span></div><h3>${esc(teamCode(g,"away"))} <i>${g.neutral?"vs":"at"}</i> ${esc(teamCode(g,"home"))}</h3><p class="phone-teams">${esc(teamName(g,"away"))} · ${esc(teamName(g,"home"))}${probs.tie>0?` · Tie ${pct(probs.tie)}`:""}</p><div class="phone-metrics"><div><span>WIN CHANCE</span><strong>${pct(w.chance)}</strong><em>${esc(winnerCaption(g,w))}</em></div><div><span>MARGIN</span><strong>${decimal(m.points)}<small>${m.points===null?"":" pts"}</small></strong><em>${esc(m.code ? `${m.code} advantage` : "Unavailable")}</em></div><div><span>TOTAL</span><strong>${decimal(g.total)}</strong><em>${num(g.total)===null?"Unavailable":"Combined points"}</em></div></div><p class="phone-game-note">${esc(phoneSnapshotLabel(g))}${g.card_note?` · ${esc(g.card_note)}`:""}${roleClockSummary(g)?`<br>${esc(roleClockSummary(g))}`:""}</p></section>`;
  }
  function phoneCircaGame(g) {
    const sides=[sideData(g,"away"),sideData(g,"home")];
    return `<section class="phone-circa-game"><div class="phone-circa-heading"><h3>${esc(teamCode(g,"away"))} <i>at</i> ${esc(teamCode(g,"home"))}</h3><span>${esc(kickoff(g))}</span></div>${sides.map(s=>`<div class="phone-circa-side"><strong>${esc(s.label)}</strong><span>${pct(s.cover)}</span><span>${pct(s.push)}</span><span class="phone-circa-expected">${decimal(s.expected,3)}</span></div>`).join("")}</section>`;
  }
  function renderPhoneCirca() {
    const d=state.data,games=sortedGames(circaGames(),"kickoff"),count=Math.max(1,Math.ceil(games.length/6));state.page=Math.max(1,Math.min(count,state.page));
    const pageGames=games.slice((state.page-1)*6,state.page*6),sourceNote=d.circa_card_note || `${d.circa_distribution_as_of?`${datePT(d.circa_distribution_as_of,{month:"short",day:"numeric"})||d.circa_distribution_as_of} distribution`:"Saved margin distribution"} · official ${d.week?`Week ${d.week} `:""}lines`;
    $("phone-sheet").classList.add("phone-circa-sheet");
    $("phone-sheet").innerHTML=`<div class="phone-brand">SPORTS EDGE LAB <span>CIRCA${d.week?` · WEEK ${esc(d.week)}`:""}</span></div><h2>Every Circa <em>option.</em></h2><div class="phone-meta"><span>${esc(longDate(d.slate_date)||"Upcoming NFL slate")} + Monday</span><span>${state.page} / ${count}</span></div><div class="phone-circa-columns"><span>CONTEST SIDE</span><span>COVER</span><span>PUSH</span><span>EXP. PTS</span></div>${pageGames.length?pageGames.map(phoneCircaGame).join(""):`<div class="empty-state"><h3>Contest evidence pending.</h3><p>Missing distributions stay unavailable.</p></div>`}<div class="phone-footer"><div><strong>${esc(sourceNote)}</strong><br>Expected points = cover + ½ push.<br>Saved distribution · analytical comparison · all times Pacific.</div><span class="phone-page">${String(state.page).padStart(2,"0")} / ${String(count).padStart(2,"0")}</span></div>`;
    $("cards-page-label").textContent=`${state.page} / ${count}`;$("cards-prev").disabled=state.page<=1;$("cards-next").disabled=state.page>=count;
  }
  function renderPhone() {
    document.querySelectorAll("[data-card-type]").forEach(b=>{const active=b.dataset.cardType===state.cardType;b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));});
    $("phone-clock-bar").hidden=state.cardType==="circa";
    if(state.cardType==="circa"){renderPhoneCirca();return;}
    $("phone-sheet").classList.remove("phone-circa-sheet");
    const games=sortedGames(currentGames(),"kickoff"),count=Math.max(1,Math.ceil(games.length/3));state.page=Math.max(1,Math.min(count,state.page));const pageGames=games.slice((state.page-1)*3,state.page*3),d=state.data,meta=forecastMeta();
    $("phone-sheet").innerHTML = `<div class="phone-brand">SPORTS EDGE LAB <span>NFL${d.week?` · WK ${esc(d.week)}`:""} · ${state.forecastClock}</span></div><h2>The Sunday <em>outlook.</em></h2><div class="phone-meta"><span>${esc(d.card_date_label || `${longDate(d.slate_date) || "Upcoming slate"}${games.some(g=>dayOf(g)==="monday")?" + Monday":""}`)}</span><span>${state.page} / ${count}</span></div>${pageGames.length?pageGames.map(phoneGame).join(""):`<div class="empty-state"><h3>Verified outlook pending.</h3><p>No game probabilities, margins or totals have been filled with estimates.</p></div>`}<div class="phone-footer"><div><strong>${esc(meta.label)} · selected saved model outputs</strong><br>${meta.as_of?`Snapshot ${esc(shortDate(meta.as_of)||meta.as_of)} PT` : "Snapshot date unavailable"}<br>Win chance ≠ cover chance. All times Pacific.</div><span class="phone-page">${String(state.page).padStart(2,"0")} / ${String(count).padStart(2,"0")}</span></div>`;
    $("cards-page-label").textContent=`${state.page} / ${count}`;$("cards-prev").disabled=state.page<=1;$("cards-next").disabled=state.page>=count;
  }

  function paragraphList(value) { return (Array.isArray(value)?value:typeof value==="string"?[value]:[]).map(v=>`<p>${esc(typeof v==="string"?v:v.text || v.note || "")}</p>`).join(""); }
  function renderForecastMeta() {
    const games=currentGames(),complete=games.filter(isComplete).length,verified=circaGames().filter(g=>g.circa?.line_verified===true).length,meta=forecastMeta();
    $("evidence-date").textContent=meta.as_of?`${meta.label} · snapshot ${shortDate(meta.as_of)||meta.as_of} PT`:`${meta.label} · snapshot date unavailable`;
    const description=`${meta.description}${meta.as_of?` Snapshot: ${shortDate(meta.as_of)||meta.as_of} PT.`:""}`;
    $("forecast-clock-note").textContent=description;$("phone-clock-note").textContent=description;
    document.querySelectorAll("[data-forecast-clock]").forEach(b=>{const active=b.dataset.forecastClock===state.forecastClock;b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));});
    $("slate-summary").innerHTML=[{value:games.length,title:"Upcoming games",text:games.length?"Sunday + Monday":"Awaiting verified slate"},{value:`${complete}/${games.length}`,title:`${state.forecastClock} outlooks`,text:"Probability, margin & total"},{value:`${verified}/${circaGames().length}`,title:"Official contest lines",text:"Verified Circa spreads"}].map(x=>`<div class="summary-item"><div class="summary-value">${esc(x.value)}</div><div class="summary-copy"><strong>${esc(x.title)}</strong>${esc(x.text)}</div></div>`).join("");
  }
  function populate() {
    const d=state.data, games=currentGames(), complete=games.filter(isComplete).length, verified=circaGames().filter(g=>g.circa?.line_verified===true).length;
    $("edition-label").textContent=`${d.season||2026} NFL${d.week?` · WEEK ${d.week}`:""} · UPCOMING SLATE`;
    $("slate-intro").textContent=d.slate_intro || "Selected game forecasts for Sunday, November 22 and Monday, November 23. There are no NFL games on Saturday, November 21.";
    $("slate-date-label").textContent=longDate(d.slate_date)||"Upcoming slate";
    $("evidence-date").textContent=d.as_of?`Evidence ${shortDate(d.as_of)||d.as_of} PT`:"Evidence date pending";
    $("circa-date-label").textContent=`${d.week?`Week ${d.week} · `:""}${longDate(d.slate_date)||"Upcoming NFL slate"}`;
    $("slate-summary").innerHTML=[{value:games.length,title:"Upcoming games",text:games.length?"Sunday + Monday":"Awaiting verified slate"},{value:`${complete}/${games.length}`,title:"Complete outlooks",text:"Probability, margin & total"},{value:`${verified}/${circaGames().length}`,title:"Official contest lines",text:"Verified Circa spreads"}].map(x=>`<div class="summary-item"><div class="summary-value">${esc(x.value)}</div><div class="summary-copy"><strong>${esc(x.title)}</strong>${esc(x.text)}</div></div>`).join("");
    $("sunday-count").textContent=games.filter(g=>dayOf(g)==="sunday").length;$("monday-count").textContent=games.filter(g=>dayOf(g)==="monday").length;
    $("performance-context").innerHTML=paragraphList(d.performance_note || "These are saved objective-specific selections. Annual game cohorts and evaluation qualifications remain visible.");
    $("performance-method").innerHTML=paragraphList(d.performance_method);
    $("circa-method").innerHTML=paragraphList(d.circa_method);
    const circaSummary=d.circa_source_summary || d.circa?.source_summary || d.circa_note || d.circa?.note || "",deadline=d.circa_deadline;
    const deadlineLabel=typeof deadline==="string"?deadline:deadline?.label || (deadline?.utc?`${shortDate(deadline.utc)||deadline.utc} PT`:"");
    $("circa-source-summary").textContent=circaSummary;$("circa-deadline").textContent=deadlineLabel;$("circa-deadline-wrap").hidden=!deadlineLabel;$("circa-evidence-banner").hidden=!circaSummary&&!deadlineLabel;
    $("performance-asof").textContent=d.performance_as_of?`Evaluation evidence ${shortDate(d.performance_as_of)||d.performance_as_of} PT`:d.as_of?`Saved evidence ${shortDate(d.as_of)||d.as_of} PT`:"Latest verified saved results";
    const horizons=[...new Set((d.performance||[]).map(perfHorizon))];$("performance-horizon").innerHTML=`<option value="all">All horizons</option>${horizons.map(h=>`<option value="${esc(h)}">${esc(h)}</option>`).join("")}`;
    $("source-list").innerHTML=(d.sources||[]).map(s=>{const name=typeof s==="string"?s:s.label || s.title || "Evidence source",href=urlOK(typeof s==="object"?s.url:null);return `<li>${href?`<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(name)}</a>`:esc(name)}${s.as_of?` · ${esc(shortDate(s.as_of)||s.as_of)}`:""}${s.note?` — ${esc(s.note)}`:""}</li>`;}).join("") || "<li>Source references will appear with the verified snapshot.</li>";
    $("source-notes").innerHTML=paragraphList(d.notes);
    $("source-summary").textContent=d.source_summary || "The forecast issue time, the saved evaluation date and the publication time describe different events.";
    $("published-at").textContent=d.published_at?`Dashboard published ${shortDate(d.published_at)||d.published_at} PT. Publication does not refresh the underlying forecasts.`:"Publication time pending.";
    if(urlOK(d.archive_links?.r18))$("archive-r18").href=d.archive_links.r18;
    if(urlOK(d.archive_links?.v10))$("archive-v10").href=d.archive_links.v10;
    try { const saved=JSON.parse(localStorage.getItem(key())||"[]");if(Array.isArray(saved))for(const row of saved.slice(0,5))if(Array.isArray(row)&&row.length===2&&["home","away"].includes(row[1]))state.picks.set(String(row[0]),row[1]); } catch {}
    renderForecastMeta();renderSlate();renderCirca();renderPerformance();renderNewestComparison();renderPhone();
  }

  function route(view, page, replace = false, forecastClock = state.forecastClock, cardType = state.cardType) {
    const previousClock=state.forecastClock;state.forecastClock=forecastClock==="T60"?"T60":"T120";
    state.cardType=cardType==="circa"?"circa":"games";
    state.view=["slate","circa","performance","cards"].includes(view)?view:"slate";if(page)state.page=Math.max(1,Number.parseInt(page,10)||1);
    const capture=new URLSearchParams(location.search).get("capture");
    document.body.classList.toggle("capture-mode",state.view==="cards"&&["1","2"].includes(capture));
    document.body.classList.toggle("capture-hires",state.view==="cards"&&capture==="2");
    document.querySelectorAll(".view").forEach(v=>v.hidden=v.id!==`view-${state.view}`);
    document.querySelectorAll("[data-view-link]").forEach(a=>{if(a.dataset.viewLink===state.view)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});
    document.title=state.view==="circa"?"Circa Million Picks & Performance Dashboard · Sports Edge Lab":state.view==="cards"?"NFL Phone Cards · Sports Edge Lab":"Sports Edge Lab · NFL";
    if(state.data&&previousClock!==state.forecastClock){renderForecastMeta();renderSlate();renderCirca();}
    if(state.data && state.view==="cards")renderPhone();
    const u=new URL(location.href);u.searchParams.set("view",state.view);u.searchParams.set("clock",state.forecastClock);if(state.view==="cards"){u.searchParams.set("page",String(state.page));u.searchParams.set("type",state.cardType);}else{u.searchParams.delete("page");u.searchParams.delete("type");}
    if(replace)history.replaceState(null,"",u);else history.pushState(null,"",u);
  }
  function toast(message) { $("toast").textContent=message;$("toast").classList.add("visible");clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>$("toast").classList.remove("visible"),3500); }
  async function share() {
    const data={title:document.title,text:state.view==="cards"?(state.cardType==="circa"?"Sports Edge Lab NFL — all Circa sides, cover and push probabilities.":"Sports Edge Lab NFL — selected model game outlooks."):"Sports Edge Lab NFL — game outlooks, model performance and the Circa board.",url:location.href};
    if(navigator.share){try{await navigator.share(data);return;}catch(e){if(e.name==="AbortError")return;}}
    try { await navigator.clipboard.writeText(location.href);toast("Link copied. It opens directly in a browser."); }
    catch { const ta=document.createElement("textarea");ta.value=location.href;ta.setAttribute("readonly","");ta.style.position="fixed";ta.style.opacity="0";document.body.append(ta);ta.select();const ok=document.execCommand("copy");ta.remove();toast(ok?"Link copied.":"Copy the page address from your browser to share it."); }
  }
  function validateData(data) {
    if(!data || typeof data!=="object" || !Array.isArray(data.games) || !Array.isArray(data.performance))throw new Error("The saved snapshot does not have the expected game and performance tables.");
    const ids=new Set();for(const g of data.games){const id=gameId(g);if(ids.has(id))throw new Error("The saved snapshot contains a duplicate game identity.");ids.add(id);for(const p of [g.win_home,g.win_away,g.tie_probability,g.probability_home,g.probability_away,g.probability_tie,g.circa?.cover_home,g.circa?.cover_away,g.circa?.push])if(p!==null&&p!==undefined&&probability(p)===null)throw new Error("The saved snapshot contains an invalid probability.");}
    return data;
  }
  document.addEventListener("click",e=>{
    const link=e.target.closest("a[data-view-link]");if(link && !e.metaKey && !e.ctrlKey && !e.shiftKey && e.button===0){e.preventDefault();const page=new URL(link.href).searchParams.get("page");route(link.dataset.viewLink,page);window.scrollTo({top:0,behavior:"auto"});return;}
    const day=e.target.closest("[data-day]");if(day){state.day=day.dataset.day;renderSlate();return;}
    const forecastClock=e.target.closest("[data-forecast-clock]");if(forecastClock){route(state.view,state.page,false,forecastClock.dataset.forecastClock);return;}
    const cardType=e.target.closest("[data-card-type]");if(cardType){route("cards",1,false,state.forecastClock,cardType.dataset.cardType);return;}
    const pick=e.target.closest("[data-pick-game]");if(pick&&!pick.disabled){togglePick(pick.dataset.pickGame,pick.dataset.pickSide);return;}
    const remove=e.target.closest("[data-remove-pick]");if(remove){state.picks.delete(remove.dataset.removePick);persistPicks();renderCirca();}
  });
  $("team-search").addEventListener("input",e=>{state.search=e.target.value;renderSlate();});
  $("game-sort").addEventListener("change",e=>{state.sort=e.target.value;renderSlate();});
  $("circa-sort").addEventListener("change",e=>{state.circaSort=e.target.value;renderCirca();});
  $("performance-horizon").addEventListener("change",e=>{state.horizon=e.target.value;renderPerformance();});
  $("newest-horizon").addEventListener("change",e=>{state.newestHorizon=Number(e.target.value);renderNewestComparison();});
  $("clear-card").addEventListener("click",()=>{state.picks.clear();persistPicks();renderCirca();});
  $("best-card").addEventListener("click",()=>{const candidates=circaGames().map(g=>({g,s:[sideData(g,"home"),sideData(g,"away")].filter(s=>s.eligible).sort((a,b)=>b.expected-a.expected)[0]})).filter(x=>x.s).sort((a,b)=>b.s.expected-a.s.expected);if(candidates.length<5)return;state.picks.clear();candidates.slice(0,5).forEach(x=>state.picks.set(gameId(x.g),x.s.side));persistPicks();renderCirca();toast("Five distinct games selected by expected contest points.");});
  $("cards-prev").addEventListener("click",()=>route("cards",state.page-1,true));$("cards-next").addEventListener("click",()=>route("cards",state.page+1,true));
  $("share-button").addEventListener("click",share);$("share-card-button").addEventListener("click",share);
  let touchX=null;$("phone-sheet").addEventListener("touchstart",e=>{touchX=e.changedTouches[0].clientX;},{passive:true});$("phone-sheet").addEventListener("touchend",e=>{if(touchX===null)return;const dx=e.changedTouches[0].clientX-touchX;touchX=null;if(Math.abs(dx)>65)route("cards",state.page+(dx<0?1:-1),true);},{passive:true});
  window.addEventListener("popstate",()=>{const q=new URLSearchParams(location.search);route(q.get("view"),q.get("page"),true,q.get("clock"),q.get("type"));});
  const initial=new URLSearchParams(location.search),requestedClock=["T60","T120"].includes(initial.get("clock"))?initial.get("clock"):null;route(initial.get("view"),initial.get("page"),true,requestedClock||"T120",initial.get("type"));
  fetch("data.json",{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error(`Snapshot request returned ${r.status}.`);return r.json();}).then(validateData).then(data=>{state.data=data;state.forecastClock=requestedClock || (data.forecast_clock_default==="T60"?"T60":"T120");populate();route(state.view,state.page,true);}).catch(error=>{
    const message="The saved data snapshot could not be loaded. Please refresh, or open the evidence archive below.";
    ["games-grid","circa-board","performance-grid"].forEach(id=>$(id).innerHTML=`<div class="empty-state"><h3>Snapshot unavailable.</h3><p>${message}</p></div>`);
    $("phone-sheet").innerHTML=`<div class="phone-brand">SPORTS EDGE LAB <span>NFL</span></div><div class="empty-state"><h3>Snapshot unavailable.</h3><p>${message}</p></div>`;$("evidence-date").textContent="Data unavailable";console.error("NFL dashboard:",error);
  });
})();
