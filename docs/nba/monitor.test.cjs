/* Unit-level interaction checks; not a browser or external accessibility audit. */
const test = require("node:test");
const assert = require("node:assert/strict");
const { selectedView, toySnapshot, boot } = require("./monitor.js");

test("all seasons and objectives remain visible by default", () => {
  const view = selectedView("all", "all");
  for (const season of ["2024–25", "2025–26", "2026–27"]) assert.equal(view.showSeason(season), true);
  for (const objective of ["winner", "margin", "total"]) assert.equal(view.showObjective(objective), true);
});

for (const season of ["2024–25", "2025–26", "2026–27"]) {
  test(`season filter retains exactly ${season} without changing metrics`, () => {
    const view = selectedView(season, "all");
    assert.deepEqual(["2024–25", "2025–26", "2026–27"].filter(view.showSeason), [season]);
    assert.match(view.status(1), /No model ranking or refitting/);
  });
}
for (const objective of ["winner", "margin", "total"]) {
  test(`objective filter retains ${objective} columns`, () => {
    const view = selectedView("all", objective);
    assert.deepEqual(["winner", "margin", "total"].filter(view.showObjective), [objective]);
  });
}
test("unreviewed season and objective inputs are rejected", () => {
  assert.throws(() => selectedView("2027–28", "all"), /Unknown/);
  assert.throws(() => selectedView("all", "profit"), /Unknown/);
});
test("safe toy union preserves a loss and hand-calculated scores", () => {
  const result = toySnapshot("union");
  assert.equal(result.dataKind, "INVENTED");
  assert.equal(result.games, 2);
  assert.equal(result.accuracy, 0.5);
  assert.equal(result.admitted, true);
  assert.ok(Math.abs(result.logLoss - (-Math.log(0.3) - Math.log(0.7)) / 2) < 1e-12);
  assert.ok(Math.abs(result.brier - 0.29) < 1e-12);
});
test("apparently perfect fresh response is explicitly inadmissible", () => {
  const result = toySnapshot("fresh");
  assert.equal(result.games, 1);
  assert.equal(result.accuracy, 1);
  assert.equal(result.admitted, false);
  assert.match(result.status, /REJECTED/);
});
test("unknown result mode cannot choose an unregistered handling rule", () => {
  assert.throws(() => toySnapshot("best_score"), /Unknown/);
});
test("a page without the optional monitor UI is left alone", () => {
  assert.equal(boot({ getElementById: () => null }), false);
});

function fixtureDocument() {
  const rowNodes = ["2024–25", "2025–26", "2026–27"].map((season) => ({ dataset: { season }, hidden: false }));
  const columnNodes = ["winner", "margin", "total"].map((objective) => ({ dataset: { objective }, hidden: false }));
  const nodes = {};
  for (const id of ["season-filter", "objective-filter", "metrics-table", "filter-status", "filters", "demo-mode", "demo-accuracy", "demo-log-loss", "demo-games", "demo-status"]) {
    nodes[id] = { value: "all", hidden: true, disabled: true, textContent: "", handlers: {},
      addEventListener(kind, handler) { this.handlers[kind] = handler; } };
  }
  nodes["demo-mode"].value = "union";
  nodes["metrics-table"].querySelectorAll = (selector) => selector.startsWith("tbody") ? rowNodes : columnNodes;
  return { getElementById: (id) => nodes[id] || null, nodes, rowNodes, columnNodes };
}
test("progressive enhancement reveals controls and defaults to safe union", () => {
  const document = fixtureDocument();
  assert.equal(boot(document), true);
  assert.equal(document.nodes.filters.hidden, false);
  assert.equal(document.nodes["demo-mode"].disabled, false);
  assert.equal(document.nodes["demo-accuracy"].textContent, "50.0%");
  assert.equal(document.nodes["demo-log-loss"].textContent, "0.7803");
});
test("actual change handlers update rows, columns and live status", () => {
  const document = fixtureDocument();
  boot(document);
  document.nodes["season-filter"].value = "2026–27";
  document.nodes["season-filter"].handlers.change();
  assert.deepEqual(document.rowNodes.map((node) => node.hidden), [true, true, false]);
  document.nodes["objective-filter"].value = "margin";
  document.nodes["objective-filter"].handlers.change();
  assert.deepEqual(document.columnNodes.map((node) => node.hidden), [true, false, true]);
  assert.match(document.nodes["filter-status"].textContent, /1 dated cohort; margin/);
});
test("unsafe toy mode retains an explicit rejection in the rendered status", () => {
  const document = fixtureDocument();
  boot(document);
  document.nodes["demo-mode"].value = "fresh";
  document.nodes["demo-mode"].handlers.change();
  assert.equal(document.nodes["demo-accuracy"].textContent, "100.0%");
  assert.equal(document.nodes["demo-games"].textContent, "1");
  assert.match(document.nodes["demo-status"].textContent, /REJECTED/);
});
