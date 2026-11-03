/* Progressive enhancement only: no requests, external data, or real forecasts. */
(function (root) {
  "use strict";
  const seasons = new Set(["all", "2024–25", "2025–26", "2026–27"]);
  const objectives = new Set(["all", "winner", "margin", "total"]);

  function selectedView(season, objective) {
    if (!seasons.has(season) || !objectives.has(objective)) {
      throw new Error("Unknown season or prediction objective");
    }
    return {
      showSeason: (value) => season === "all" || value === season,
      showObjective: (value) => objective === "all" || value === objective,
      status: (count) => `Showing ${count} dated cohort${count === 1 ? "" : "s"}; ${objective === "all" ? "all objectives" : objective}. No model ranking or refitting.`,
    };
  }

  function toySnapshot(mode) {
    if (!["union", "fresh"].includes(mode)) throw new Error("Unknown invented result mode");
    const outcomes = mode === "union" ? [0, 1] : [1];
    const probability = 0.7;
    const logLoss = outcomes.reduce((sum, y) => sum - (y ? Math.log(probability) : Math.log1p(-probability)), 0) / outcomes.length;
    return {
      dataKind: "INVENTED", admitted: mode === "union", games: outcomes.length,
      accuracy: outcomes.reduce((sum, y) => sum + y, 0) / outcomes.length,
      logLoss, brier: outcomes.reduce((sum, y) => sum + (probability - y) ** 2, 0) / outcomes.length,
      status: mode === "union" ? "Accepted toy union: the prior loss remains." : "REJECTED toy refresh: the earlier loss disappeared. This score is not admissible.",
    };
  }

  function toyVersion(mode) {
    if (!["issued", "reconstruction"].includes(mode)) throw new Error("Unknown invented version view");
    return { dataKind: "INVENTED", probability: mode === "issued" ? 0.7 : 0.62,
      originalProbability: 0.7, archivedVersions: 2, prospectiveCredit: 0,
      status: mode === "issued" ? "Original invented issue remains 70.0%; no source refresh can edit it."
        : "Later invented reconstruction: 62.0%. Not issued; original 70.0% remains unchanged.",
    };
  }

  function boot(document) {
    const season = document.getElementById("season-filter");
    const objective = document.getElementById("objective-filter");
    const table = document.getElementById("metrics-table");
    const status = document.getElementById("filter-status");
    const filters = document.getElementById("filters");
    const mode = document.getElementById("demo-mode");
    const versionMode = document.getElementById("version-mode");
    if (!season || !objective || !table || !status || !filters || !mode || !versionMode) return false;

    function updateTable() {
      const view = selectedView(season.value, objective.value);
      const rows = Array.from(table.querySelectorAll("tbody tr[data-season]"));
      for (const row of rows) row.hidden = !view.showSeason(row.dataset.season);
      for (const cell of table.querySelectorAll("[data-objective]")) {
        cell.hidden = !view.showObjective(cell.dataset.objective);
      }
      status.textContent = view.status(rows.filter((row) => !row.hidden).length);
    }

    function updateDemo() {
      const snapshot = toySnapshot(mode.value);
      document.getElementById("demo-accuracy").textContent = `${(100 * snapshot.accuracy).toFixed(1)}%`;
      document.getElementById("demo-log-loss").textContent = snapshot.logLoss.toFixed(4);
      document.getElementById("demo-games").textContent = String(snapshot.games);
      document.getElementById("demo-status").textContent = snapshot.status;
    }

    function updateVersion() {
      const version = toyVersion(versionMode.value);
      document.getElementById("version-probability").textContent = `${(version.probability * 100).toFixed(1)}%`;
      document.getElementById("version-status").textContent = version.status;
    }

    season.addEventListener("change", updateTable);
    objective.addEventListener("change", updateTable);
    mode.addEventListener("change", updateDemo);
    versionMode.addEventListener("change", updateVersion);
    filters.hidden = false;
    mode.disabled = false;
    versionMode.disabled = false;
    updateTable();
    updateDemo();
    updateVersion();
    return true;
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { selectedView, toySnapshot, toyVersion, boot };
  if (typeof document !== "undefined") boot(document);
})(typeof globalThis === "undefined" ? this : globalThis);
