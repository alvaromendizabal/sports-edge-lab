"use strict";
(() => {
  let data;
  const $ = id => document.getElementById(id);
  const text = (tag, value) => { const element = document.createElement(tag); element.textContent = value; return element; };
  const format = (value, metric, signed = false) => typeof value !== "number" ? "Unavailable" :
    (signed && value > 0 ? "+" : "") + (metric === "accuracy" ? (value * 100).toFixed(2) + (signed ? " pp" : "%") : value.toFixed(5));
  const cell = (value, n, metric) => { const td = text("td", format(value, metric)); if (typeof n === "number") td.append(text("small", "n = " + n.toLocaleString())); return td; };
  function render() {
    const metric = $("metric").value, scope = $("scope").value;
    $("model-rows").replaceChildren();
    data.models.forEach(model => {
      const tr = document.createElement("tr"), name = text("td", model.alias + " · " + model.label);
      name.append(text("small", model.role.replaceAll("_", " "))); tr.append(name);
      const validation = scope === "full" ? model.validation_full : model.validation_matched_market;
      tr.append(cell(validation?.[metric], validation?.n, metric));
      [2024, 2025, 2026].forEach(year => { const card = model[scope]?.[year]; tr.append(cell(card?.metrics?.[metric], card?.metrics?.n, metric)); });
      $("model-rows").append(tr);
    });
    const counts = (scope === "full" ? data.cohorts.map(c => c.season + ": " + c.n) : data.provider_cohorts.map(c => c.season + ": " + c.matched_n)).join(" · ");
    $("cohort-note").textContent = (scope === "full" ? "Full observed final-game populations. " : "Fixed source-qualified market populations, selected without model scores. ") + counts;
    $("nomination").textContent = "Archived experiment: WM01, WM02 and WN01 are ineligible under the current comparison-only source policy. WB01 is a reference, not an owned-model nominee. No model has been promoted.";
    $("fallbacks").replaceChildren();
    data.models.filter(m => (m.original_study_role || m.role) === "candidate").forEach(model => {
      const p = document.createElement("p"); p.append(text("strong", model.alias + ": "));
      p.append(document.createTextNode([2024,2025,2026].map(year => { const counts = model[scope]?.[year]?.fallback_counts || {}; return year + " — " + (Object.entries(counts).map(([reason,n]) => n + " " + reason.toLowerCase()).join(", ") || "no fallback"); }).join("; ")));
      $("fallbacks").append(p);
    });
    $("uncertainty").replaceChildren();
    const period = $("period").value, comparator = $("comparator").value;
    const selected = data.paired_comparisons.filter(c => c.period === period && c.baseline === comparator && (comparator === "DraftKings" ? c.scope === "matched_market" : c.scope === scope));
    selected.forEach(row => {
      const m = row.metrics[metric], tr = document.createElement("tr");
      const interval = values => values && values.every(v => typeof v === "number") ? values.map(v => format(v, metric, true)).join(" to ") : "Unavailable";
      [row.alias, row.n + " / " + row.week_blocks, format(m.delta, metric, true), interval(m.interval95), interval(m.familywise_interval95)].forEach(v => tr.append(text("td", v)));
      $("uncertainty").append(tr);
    });
    if (!selected.length) { const tr = document.createElement("tr"), td = text("td", "Additional paired comparator intervals are not attached to this execution."); td.colSpan = 5; tr.append(td); $("uncertainty").append(tr); }
    $("weights").replaceChildren();
    const names = {predeclared_50_35_15:"2026 50% / 2025 35% / 2024 15%",equal:"Equal season weights",current65:"2026 65% / 2025 25% / 2024 10%"};
    data.descriptive_weight_sensitivity.forEach(row => {const tr = document.createElement("tr"); [row.alias,names[row.weight_policy],format(row.metrics[metric],metric)].forEach(v => tr.append(text("td",v))); $("weights").append(tr);});
  }
  fetch("data/market-study.json", {cache:"no-store"}).then(response => { if (!response.ok) throw new Error("Study aggregate response unavailable"); return response.json(); }).then(value => {
    if (value.schema !== "fbs.public.archived-market-study.v082") throw new Error("Study aggregate schema mismatch");
    data = value; $("execution").textContent = data.execution.environment;
    $("fit-count").textContent = data.execution.new_fits + " new fits · " + data.execution.reused_fits + " reused · " + data.execution.failed_fits + " failed · " + data.execution.worker_count + " observed workers";
    data.evidence_notes.forEach(note => $("notes").append(text("p", note)));
    data.cohorts.forEach(c => {const p = text("p", c.season + " full · n=" + c.n + " · "); p.append(text("code", c.cohort_sha256 || "Not attached")); $("hashes").append(p);});
    data.provider_cohorts.forEach(c => {const p = text("p", c.season + " qualified market · n=" + c.matched_n + " · "); p.append(text("code",c.cohort_sha256 || "Not attached")); $("hashes").append(p);});
    ["metric","scope","period","comparator"].forEach(id => $(id).addEventListener("change", render)); render();
  }).catch(() => {$("execution").textContent = "Study data unavailable"; $("load-error").hidden = false; $("load-error").textContent = "The verified market-study aggregate could not be loaded. Return to the main dashboard for the existing comparison.";});
})();