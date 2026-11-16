(function () {
  'use strict';
  const el = id => document.getElementById(id);
  if (!el('r19-recovered')) return;
  const status = el('r19-recovered-status'), body = el('r19-recovered-rows');
  function cell(row, text, header = false) { const node = document.createElement(header ? 'th' : 'td'); node.textContent = text; row.appendChild(node); }
  function validate(data) {
    if (data.schema !== 'sel.ncaa.public.r19.recovered_current_comparison.v1' || data.new_fits !== 0 || data.new_forecasts !== 0 || data.test_selection_weight !== 0 || data.promotion_permitted !== false || data.point_in_time_qualification_complete !== false || data.complete_all_seasons_claimed !== false) throw new Error('policy identity differs');
    if (data.metrics.length !== 86 || data.missing_registered_target_policies.length !== 8) throw new Error('declared policy coverage differs');
    const keys = new Set(), roster = new Map(data.model_roster.map(row => [row.model_id, row]));
    for (const league of ['ncaam', 'ncaaw']) for (const target of ['win', 'margin', 'total']) {
      const rows = data.metrics.filter(row => row.league === league && row.target === target);
      const cohort = data.cohorts.find(row => row.league === league && row.target === target);
      if (rows.length !== (target === 'win' ? 17 : 13) || !cohort || rows.length !== cohort.model_target_policy_count) throw new Error('fixed roster is incomplete');
      for (const row of rows) {
        const key = [row.league, row.target, row.public_model_id].join('/');
        if (keys.has(key) || !roster.has(row.public_model_id)) throw new Error('policy identity is missing or duplicated');
        keys.add(key);
        if (row.cohort_sha256 !== cohort.cohort_sha256 || row.games !== cohort.games || row.games !== (league === 'ncaam' ? 637 : 655) || row.qualified_games !== 0 || row.rank_permitted !== false || row.promotion_permitted !== false || row.test_selection_weight !== 0) throw new Error('shared cohort or qualification differs');
        for (const metric of (target === 'win' ? ['accuracy', 'log_loss', 'brier'] : ['mae', 'rmse'])) if (!Number.isFinite(row.metrics[metric])) throw new Error('a required metric is missing');
      }
    }
    return data;
  }
  function render(data) {
    const league = el('r19-recovered-league').value, target = el('r19-recovered-target').value;
    const roster = new Map(data.model_roster.map(row => [row.model_id, row]));
    const rows = data.metrics.filter(row => row.league === league && row.target === target);
    const metrics = target === 'win' ? ['accuracy', 'log_loss', 'brier'] : ['mae', 'rmse'];
    const labels = {accuracy: 'Accuracy', log_loss: 'Log loss', brier: 'Brier', mae: 'MAE (points)', rmse: 'RMSE (points)'};
    const header = document.createElement('tr');
    for (const label of ['Model policy', 'Shared games', ...metrics.map(m => labels[m]), 'Qualified games']) cell(header, label, true);
    el('r19-recovered-head').replaceChildren(header); body.replaceChildren();
    // Original fixed policy order, never a sort by the observed test metric.
    for (const row of rows) {
      const tr = document.createElement('tr'); cell(tr, roster.get(row.public_model_id).public_label); cell(tr, row.games.toLocaleString());
      for (const metric of metrics) cell(tr, metric === 'accuracy' ? (100 * row.metrics[metric]).toFixed(3) + '%' : row.metrics[metric].toFixed(6));
      cell(tr, '0 · descriptive only'); body.appendChild(tr);
    }
    const gaps = data.missing_registered_target_policies.filter(row => row.league === league && row.target === target);
    const full = data.full_registered_current_policy_intersections.find(row => row.league === league && row.target === target);
    status.textContent = rows.length + ' displayed policies · ' + rows[0].games + ' identical games each · R19 cutoff November 16, 1:35:28 p.m. Pacific. Current-season test weight for selection: 0%.';
    el('r19-recovered-gaps').textContent = 'The full declared target-policy roster contains ' + full.registered_target_policy_count + ' policies. ' + gaps.length + ' were not emitted; its full-policy shared-game intersection is ' + full.same_game_intersection_count + '. No full-population champion is asserted.';
    const list = el('r19-recovered-missing'); list.replaceChildren();
    for (const gap of data.missing_registered_target_policies) { const li = document.createElement('li'); li.textContent = (gap.league === 'ncaam' ? 'Men' : 'Women') + ' · ' + roster.get(gap.public_model_id).public_label + ' · ' + gap.target + ' · registered, no emitted predictions'; list.appendChild(li); }
  }
  function fail(error) { body.replaceChildren(); status.textContent = 'Recovered R19 comparison unavailable: ' + error.message + '. No older or differently scoped scores were substituted.'; }
  fetch('r19_recovered_comparison.json').then(r => { if (!r.ok) throw new Error('data request failed'); return r.json(); }).then(validate).then(data => {
    for (const id of ['r19-recovered-league', 'r19-recovered-target']) el(id).addEventListener('change', () => { try { render(data); } catch (error) { fail(error); } });
    render(data);
  }).catch(fail);
}());
