"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let data = [], page = 0;
  const size = 30;
  const columns = {
    winner: [["winner_logloss", "Log loss"], ["winner_brier", "Brier"], ["winner_accuracy", "Accuracy"], ["winner_ece", "ECE"]],
    margin: [["margin_mae", "MAE"], ["margin_rmse", "RMSE"], ["margin_bias", "Bias"]],
    total: [["total_mae", "MAE"], ["total_rmse", "RMSE"], ["total_bias", "Bias"]]
  };
  const el = (tag, value) => { const node = document.createElement(tag); if (value !== undefined) node.textContent = value; return node; };
  function selected() {
    const query = $("model-search").value.trim().toLowerCase(), season = $("eval-season").value, version = $("evidence-release").value;
    const target = $("score-target").value, primary = target === "winner" ? "winner_logloss" : target + "_rmse";
    const rows = data.filter(r => (season === "all" || String(r.evaluation_season) === season) && (version === "all" || r.evidence_release === version) && (!query || [r.model_id, r.family].some(v => String(v).toLowerCase().includes(query))));
    const mode = $("score-order").value;
    return rows.sort((a,b) => (mode === "primary" ? (a[primary] ?? Infinity) - (b[primary] ?? Infinity) : mode === "games" ? b.games - a.games : 0) || a.model_id.localeCompare(b.model_id) || a.evaluation_season-b.evaluation_season || a.evidence_release.localeCompare(b.evidence_release));
  }
  function render() {
    const rows = selected(), metrics = columns[$("score-target").value], pages = Math.max(1,Math.ceil(rows.length/size)); page=Math.min(page,pages-1);
    const head=el("tr"); for(const label of ["Model / family", "Evidence", "Season", "Games", ...metrics.map(v=>v[1]), "Provenance"]) { const th=el("th",label);th.scope="col";head.append(th); }
    $("registry-head").replaceChildren(head); const body=document.createDocumentFragment();
    for(const row of rows.slice(page*size,(page+1)*size)) {
      const tr=el("tr"), identity=el("td",row.model_id);identity.append(el("br"),el("small",row.family));tr.append(identity,el("td",row.evidence_release),el("td",row.evaluation_season),el("td",row.games));
      for(const [key] of metrics) { const value=row[key];tr.append(el("td",value === null || value === undefined ? "Unavailable" : key.endsWith("accuracy") ? (100*value).toFixed(2)+"%" : value.toFixed(6))); }
      const details=el("details"), summary=el("summary","Source record");details.append(summary,el("p","Authenticated inherited scorecard. Exposed historical evaluation; no promotion."),el("p","File SHA-256"),el("code",row.source_sha256));
      if(row.cohort_sha256) details.append(el("p","Cohort SHA-256"),el("code",row.cohort_sha256));
      details.append(el("p","Spread-cover metrics: not evaluated in this source."));const cell=el("td");cell.append(details);tr.append(cell);body.append(tr);
    }
    $("registry-body").replaceChildren(body);$("registry-status").textContent = rows.length.toLocaleString()+" scorecards for "+new Set(rows.map(r=>r.model_id)).size+" model identifiers. Missing values stay unavailable.";
    $("registry-page").textContent="Page "+(page+1)+" of "+pages;$("previous-models").disabled=page===0;$("next-models").disabled=page+1>=pages;
  }
  for(const id of ["eval-season","evidence-release","score-target","score-order"]) $(id).addEventListener("change",()=>{page=0;render();});
  $("model-search").addEventListener("input",()=>{page=0;render();});$("previous-models").addEventListener("click",()=>{page--;render();});$("next-models").addEventListener("click",()=>{page++;render();});
  $("download-models").addEventListener("click",()=>{const rows=selected(),keys=["model_id","family","evidence_release","evaluation_season","games",...columns[$("score-target").value].map(v=>v[0]),"cohort_sha256","source_sha256","status"];
    const quote=v=>'"'+String(v??"").replaceAll('"','""')+'"';const csv=[keys,...rows.map(r=>keys.map(k=>r[k]))].map(row=>row.map(quote).join(",")).join("\r\n");const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));const a=el("a");a.href=url;a.download="fbs-historical-model-metrics.csv";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  fetch("model-registry.json").then(r=>{if(!r.ok)throw new Error("Registry could not be loaded");return r.json();}).then(registry=>{
    if(!Array.isArray(registry.rows)||registry.rows.length!==registry.scorecard_rows||new Set(registry.rows.map(r=>r.model_id)).size!==registry.model_ids)throw new Error("Registry integrity counts do not match");
    for(const r of registry.rows)if(![2024,2025].includes(r.evaluation_season)||!Number.isInteger(r.games)||r.games<=0||r.status!=="EXPOSED_HISTORICAL_EVALUATION_NO_PROMOTION")throw new Error("Invalid scorecard identity");data=registry.rows;render();
  }).catch(error=>{$("registry-status").textContent=error.message+". The source JSON remains linked below.";$("download-models").disabled=true;});
})();
