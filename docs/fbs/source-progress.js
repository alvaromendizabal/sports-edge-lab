/* Approved public source-inventory display only. No network, models or orders. */
(function(root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.document) {
    root.FbsSourceProgress = api;
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', () => api.hydrate(root.document), {once: true});
    } else api.hydrate(root.document);
  }
})(typeof window !== 'undefined' ? window : null, function() {
  'use strict';
  function normalized(value) {
    return String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  }
  function visibleIndices(rows, filters) {
    filters = filters || {};
    const season = String(filters.season || 'all');
    const result = filters.result || 'all';
    const query = normalized(filters.query).trim();
    return rows.reduce((found, row, index) => {
      if (season !== 'all' && String(row.season) !== season) return found;
      if (result === 'completed' && row.completed !== true) return found;
      if (result === 'not_completed' && row.completed !== false) return found;
      if (query && !normalized(row.home + ' ' + row.away).includes(query)) return found;
      found.push(index);
      return found;
    }, []);
  }
  function hydrate(doc) {
    const node = doc.getElementById('source-progress-data');
    const body = doc.getElementById('source-inventory-body');
    if (!node || !body || body.dataset.sourceHydrated === 'true') return false;
    const status = doc.getElementById('source-inventory-status');
    let payload;
    try {
      payload = JSON.parse(node.textContent);
      if (payload.inventory.schema !== 'fbs.public.official-source-inventory.v1' || !Array.isArray(payload.inventory.rows)) throw new Error('Source schema differs');
    } catch (error) {
      if (status) status.textContent = 'Interactive filters are unavailable. The complete static source table remains visible.';
      return false;
    }
    const elements = Array.from(body.querySelectorAll('[data-source-row]'));
    if (elements.length !== payload.inventory.rows.length || elements.some((row, i) => row.dataset.sourceRow !== String(i))) {
      if (status) status.textContent = 'Interactive row identity check failed. The static source inventory is preserved.';
      return false;
    }
    const season = doc.getElementById('source-season-filter');
    const result = doc.getElementById('source-result-filter');
    const query = doc.getElementById('source-team-filter');
    const reset = doc.getElementById('source-clear-filters');
    const empty = doc.getElementById('source-inventory-empty');
    if (![season, result, query, reset, empty, status].every(Boolean)) return false;
    function render() {
      const selected = new Set(visibleIndices(payload.inventory.rows, {season: season.value, result: result.value, query: query.value}));
      elements.forEach((row, i) => { row.hidden = !selected.has(i); });
      empty.hidden = selected.size !== 0;
      status.textContent = selected.size.toLocaleString() + ' of ' + elements.length.toLocaleString() + ' source rows shown. Filtering does not alter stored evidence.';
    }
    [season, result, query, reset].forEach(control => { control.disabled = false; });
    season.addEventListener('change', render);
    result.addEventListener('change', render);
    query.addEventListener('input', render);
    reset.addEventListener('click', () => { season.value = 'all'; result.value = 'all'; query.value = ''; render(); });
    body.dataset.sourceHydrated = 'true';
    render();
    return true;
  }
  return {visibleIndices, hydrate};
});
