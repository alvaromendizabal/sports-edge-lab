'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const names = {winner:'Winner & probability', margin:'Point margin', total:'Total points', cover:'Qualified cover probability'};
  function expectedTargets(family) {
    if (family === 'logistic' || /_refresh_logistic$/.test(family)) return ['winner'];
    if (family === 'linear' || family === 'ridge' || /_refresh_(linear|ridge)$/.test(family)) return ['margin','total'];
    return ['winner','margin','total'];
  }
  function hasTarget(value, target) {
    if (target === 'winner') return finite(value.p) && value.p >= 0 && value.p <= 1;
    if (target === 'margin' || target === 'total') return finite(value[target]);
    if (target === 'cover') return value.model?.margin?.cover_status === 'AUTHENTICATED_EXACT_LINE_CUTOFF_QUALIFIED' &&
      finite(value.model.margin.cover_probability) && value.model.margin.cover_probability >= 0 && value.model.margin.cover_probability <= 1;
    return expectedTargets('').some(key => hasTarget(value, key));
  }
  function completeness(value, family) {
    const required = expectedTargets(family), found = required.filter(key => hasTarget(value,key));
    return found.length === required.length ? 'complete' : found.length ? 'partial' : 'missing';
  }
  function missingReason(game, value, target, family) {
    if (target === 'cover') return 'No authenticated exact-line cover forecast';
    if (target !== 'any' && !expectedTargets(family).includes(target)) return 'Not a target of this model family';
    if (target !== 'any' && value.missing?.[target]) return value.missing[target];
    if (family === 'retained') return game.season !== 2026 ? 'Original replay is not projected for this season' : 'No original replay retained for this game';
    if (value.scope_reason) return value.scope_reason;
    if (!game.kickoff_exact) return 'Exact kickoff unresolved';
    if (game.projection_status === 'INSUFFICIENT_PRIOR_OUTCOMES') return 'Prior history or training/calibration separation not admitted';
    if (completeness(value,family) === 'partial') return 'One or more expected model targets are missing';
    return 'No authenticated saved output for this game and family';
  }
  function matches(value, family, target, filter, quarantined = false) {
    if (filter === 'quarantine') return quarantined;
    if (filter === 'partial' || filter === 'complete') return completeness(value,family) === filter;
    if (filter === 'present') return hasTarget(value,target);
    if (filter === 'missing') return !hasTarget(value,target);
    return true;
  }
  function reconcile(games, project, family, target = 'any') {
    const counts = {games:games.length,complete:0,partial:0,missing:0,target_present:0,target_missing:0};
    const reasons = new Map();
    for (const game of games) {
      const value = project(game);
      counts[completeness(value,family)]++;
      if (hasTarget(value,target)) counts.target_present++;
      else {
        counts.target_missing++;
        const reason = missingReason(game,value,target,family);
        reasons.set(reason,(reasons.get(reason)||0)+1);
      }
    }
    return {...counts, expected_targets:expectedTargets(family), missing_reasons:[...reasons].map(([reason,games])=>({reason,games}))};
  }
  const api = {names, expectedTargets, hasTarget, completeness, missingReason, matches, reconcile};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.FBSCoverage = api;
})();
