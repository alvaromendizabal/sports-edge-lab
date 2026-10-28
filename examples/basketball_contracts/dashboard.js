/* Pure selectors are shared by the offline HTML and Node guard tests. */
(function (scope) {
  'use strict';
  function selectRows(data, state) {
    const rows = data.rows.filter(r => r.league === state.league && r.horizon_minutes === +state.horizon && r.year === +state.year && r.cohort === state.cohort);
    return rows.slice().sort((a, b) => +state.year === 2027 ? (a.recipe < b.recipe ? -1 : a.recipe > b.recipe ? 1 : 0) : a.log_loss - b.log_loss || a.recipe.localeCompare(b.recipe));
  }
  function numericalWinners(rows, year) {
    if (+year === 2027 || !rows.length) return [];
    const first = rows[0];
    if (rows.some(r => r.monitoring_only || r.year !== +year || r.n !== first.n || r.league !== first.league || r.horizon_minutes !== first.horizon_minutes || r.cohort !== first.cohort)) throw Error('Exact historical cohort required');
    const best = Math.min(...rows.map(r => r.log_loss));
    return rows.filter(r => Math.abs(r.log_loss - best) < 1e-12).map(r => r.recipe);
  }
  function overlapRows(data, league, year) {
    return data.overlap_sensitivities.filter(r => r.league === league && r.year === +year);
  }
  function presentation(data, state) {
    const rows = selectRows(data, state);
    const monitoring = +state.year === 2027;
    return {rows, monitoring, winnerRecipes: numericalWinners(rows, state.year),
      champion: data.frozen_champions[state.league + '/T' + state.horizon],
      status: rows.length ? (monitoring ? 'Retrospective monitoring only; stable recipe order; no selection.' : 'Historical numerical minima only; development-exposed, not promotion.') : 'No saved comparable scorecards for this panel. Missing is not zero.',
      games: rows.length ? rows[0].n : null};
  }
  const api = {selectRows, numericalWinners, overlapRows, presentation};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  scope.BasketballDashboard = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
