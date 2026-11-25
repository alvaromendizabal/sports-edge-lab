"use strict";
// Generic navigation opens current results. Clock, capture and dated bookmarks
// retain the historical cohort and original values they requested.
(() => {
  const query = new URLSearchParams(window.location.search);
  const sections = new Map([["slate", "slate"], ["circa", "circa"], ["performance", "results"], ["cards", "cards"]]);
  const view = query.get("view");
  if (!sections.has(view)) return;
  const archiveParameters = ["clock", "horizon", "page", "type", "capture", "week", "season", "date", "as_of", "snapshot", "vintage", "archive", "history"];
  const historical = archiveParameters.some(key => query.has(key));
  if (historical) {
    const url = new URL("./research-history.html", window.location.href);
    url.search = query;
    url.hash = window.location.hash;
    window.location.replace(url.href);
  } else {
    const url = new URL(window.location.href);
    url.searchParams.delete("view");
    url.hash = sections.get(view);
    window.location.replace(url.href);
  }
})();
