(function () {
  'use strict';
  const root = document.getElementById('validation-weights');
  if (!root) return;
  const el = id => document.getElementById(id);
  const message = el('validation-weight-status');
  const body = el('validation-weight-rows');
  const choices = ['primary_50_50', 'sensitivity_40_60', 'sensitivity_30_70', 'sensitivity_20_80', 'sensitivity_10_90'];
  const targets = {win: ['accuracy', 'log_loss', 'brier'], margin: ['mae', 'rmse'], total: ['mae', 'rmse']};
  const finite = x => typeof x === 'number' && Number.isFinite(x);
  function cell(row, text) { const c = document.createElement('td'); c.textContent = text; row.appendChild(c); }
  function show(value, metric) { return metric === 'accuracy' ? (100 * value).toFixed(3) + '%' : value.toFixed(6); }
  function fail(error) { body.replaceChildren(); message.textContent = 'Validation comparison unavailable: ' + error.message + '. No ranking has been substituted.'; }
  function validate(data) {
    if (data.schema !== 'sel.ncaa.public.validation_weight_sensitivity.v1' || data.test_rows_used !== 0 || data.automatic_promotions !== 0 || data.qualified_promotion_evidence !== false) throw new Error('policy evidence does not match');
    if (!Array.isArray(data.season_cells) || !Array.isArray(data.weighted_panels) || data.weighted_panels.length !== 360) throw new Error('candidate coverage is incomplete');
    const seen = new Set();
    for (const row of data.season_cells) {
      if (![2025, 2026].includes(row.season_end_year) || !['ncaam', 'ncaaw'].includes(row.league)) throw new Error('a season is outside validation');
      const id = [row.league, row.target, row.model_id, row.season_end_year].join('/');
      if (seen.has(id)) throw new Error('a candidate game cohort is duplicated');
      seen.add(id);
    }
    for (const policy of choices) for (const league of ['ncaam', 'ncaaw']) for (const target of Object.keys(targets)) {
      const rows = data.weighted_panels.filter(r => r.policy === policy && r.league === league && r.target === target);
      if (rows.length !== 12 || new Set(rows.map(r => r.model_id)).size !== 12) throw new Error('the declared twelve-candidate roster is incomplete');
      const first = rows[0];
      for (const row of rows) {
        if (row.promotion_permitted !== false || JSON.stringify(row.cohort_sha256s) !== JSON.stringify(first.cohort_sha256s) || JSON.stringify(row.scored_games) !== JSON.stringify(first.scored_games)) throw new Error('candidate game populations differ');
        if (!Array.isArray(row.cohort_sha256s) || row.cohort_sha256s.length !== 2 || row.cohort_sha256s.some(h => !/^[a-f0-9]{64}$/.test(h))) throw new Error('cohort hashes are missing');
        const weights = data.weights[policy];
        if (!weights || JSON.stringify(row.weights) !== JSON.stringify(weights)) throw new Error('season weights differ');
        for (const metric of targets[target]) {
          const cells = [2025, 2026].map(year => data.season_cells.find(c => c.league === league && c.target === target && c.model_id === row.model_id && c.season_end_year === year));
          if (cells.some((c, i) => !c || c.cohort_sha256 !== row.cohort_sha256s[i] || c.scored_games !== row.scored_games[i] || !finite(c.metrics[metric]))) throw new Error('season metric identity differs');
          const expected = weights.reduce((sum, weight, i) => sum + weight * cells[i].metrics[metric], 0);
          if (!finite(row.metrics[metric]) || Math.abs(expected - row.metrics[metric]) > 1e-10) throw new Error('weighted arithmetic differs');
        }
      }
    }
    return data;
  }
  function render(data) {
    const [target, metric] = el('validation-weight-objective').value.split(':');
    const league = el('validation-weight-league').value, policy = el('validation-weight-policy').value;
    const rows = data.weighted_panels.filter(r => r.league === league && r.target === target && r.policy === policy);
    rows.sort((a, b) => (metric === 'accuracy' ? -1 : 1) * (a.metrics[metric] - b.metrics[metric]) || a.public_label.localeCompare(b.public_label));
    body.replaceChildren();
    for (const row of rows) {
      const tr = document.createElement('tr');
      cell(tr, row.public_label);
      for (const year of [2025, 2026]) {
        const c = data.season_cells.find(c => c.league === league && c.target === target && c.model_id === row.model_id && c.season_end_year === year);
        cell(tr, show(c.metrics[metric], metric));
      }
      cell(tr, show(row.metrics[metric], metric));
      cell(tr, row.scored_games.map((n, i) => n.toLocaleString() + ' / ' + row.declared_games[i].toLocaleString()).join(' · '));
      cell(tr, 'Research only · promotion withheld');
      body.appendChild(tr);
    }
    const weights = data.weights[policy];
    message.textContent = rows.length + ' candidates on identical scored games in each year. Weights: ' + (weights[0] * 100) + '% for 2024–25, ' + (weights[1] * 100) + '% for 2025–26. ' + (policy === 'primary_50_50' ? 'Predeclared primary policy. ' : 'Sensitivity policy. ') + 'Sorted by the selected observed metric; 2026–27 contributes zero selection weight.';
  }
  fetch('validation_weight_sensitivity.json').then(r => { if (!r.ok) throw new Error('data request failed'); return r.json(); }).then(validate).then(data => {
    for (const id of ['validation-weight-league', 'validation-weight-policy', 'validation-weight-objective']) el(id).addEventListener('change', () => { try { render(data); } catch (error) { fail(error); } });
    render(data);
  }).catch(fail);
}());
