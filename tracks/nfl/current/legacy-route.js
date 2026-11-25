"use strict";
// Shared Week 11 links keep their original forecast clock, page, and view.
(() => {
  const query = new URLSearchParams(window.location.search);
  if (["slate", "circa", "performance", "cards"].includes(query.get("view"))) {
    const history = new URL("./research-history.html", window.location.href);
    history.search = query.toString();
    history.hash = window.location.hash;
    window.location.replace(history.href);
  }
})();
