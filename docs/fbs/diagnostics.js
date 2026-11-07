'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  function scoreCenters(margin, total) {
    if (!finite(margin) || !finite(total)) return null;
    const home = (total + margin) / 2, away = (total - margin) / 2;
    return {home, away, negative: home < 0 || away < 0};
  }
  function observedErrors(game, projection) {
    if (!game.completed || !finite(game.home_score) || !finite(game.away_score)) return null;
    const margin = game.home_score - game.away_score, total = game.home_score + game.away_score;
    return {
      winner_correct: finite(projection.p) && margin !== 0 ? (projection.p >= 0.5) === (margin > 0) : null,
      margin_error: finite(projection.margin) ? projection.margin - margin : null,
      total_error: finite(projection.total) ? projection.total - total : null,
    };
  }
  function metricDelta(row, baseline, key) {
    if (!row || !baseline || row.target !== baseline.target || !row.exact_game_ids_sha256 ||
        row.exact_game_ids_sha256 !== baseline.exact_game_ids_sha256 || row.games !== baseline.games) {
      return {value: null, reason: 'Different or unverified game cohort'};
    }
    if (!finite(row[key]) || !finite(baseline[key])) return {value: null, reason: 'Metric not recorded'};
    return {value: row[key] - baseline[key], reason: 'Exact cohort; descriptive comparison'};
  }
  function targetCoverage(games, project) {
    const counts = {games: games.length, winner: 0, margin: 0, total: 0, intervals: 0, cover: 0};
    for (const game of games) {
      const value = project(game);
      counts.winner += Number(finite(value.p));
      counts.margin += Number(finite(value.margin));
      counts.total += Number(finite(value.total));
      counts.intervals += Number(['margin', 'total'].some(target =>
        Array.isArray(value.model?.[target]?.interval80) && Array.isArray(value.model?.[target]?.interval95)));
      // Cover admission is deliberately independent of point forecasts and intervals.
      counts.cover += Number(value.model?.margin?.cover_status === 'AUTHENTICATED_EXACT_LINE_CUTOFF_QUALIFIED' &&
        finite(value.model.margin.cover_probability));
    }
    return counts;
  }
  function csv(records, columns) {
    const cell = value => '"' + String(value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : value)
      .replace(/^([=+@\t\r])/, "'$1").replaceAll('"', '""') + '"';
    return [columns.map(cell).join(','), ...records.map(row => columns.map(key => cell(row[key])).join(','))].join('\r\n');
  }
  const api = {scoreCenters, observedErrors, metricDelta, targetCoverage, csv};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window === 'undefined') return;
  window.FBSDiagnostics = api;
  const G = window.FBSCompleteReview, R = window.FBS_DEVELOPMENT_STUDY, O = window.FBS_OPTIONAL_STUDY, C = window.FBS_CATBOOST_STUDY, N = window.FBS_OWNER_NEURAL_STUDY;
  if (!G || !R || !O || !C || !N) return;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = (value, digits = 2) => finite(value) ? value.toFixed(digits) : 'Not recorded';
  const percent = value => finite(value) ? (value * 100).toFixed(1) + '%' : 'Not recorded';
  const signed = (value, digits = 2) => finite(value) ? (value > 0 ? '+' : '') + value.toFixed(digits) : 'Not recorded';
  const familyLabel = row => row.display_name || row.family.replaceAll('_', ' ');
  const option = (value, label) => `<option value="${esc(value)}">${esc(label)}</option>`;
  const small = value => `<span class="cell-sub">${esc(value)}</span>`;
  let openGameId = null;
  const metricColumns = ['study','evaluation_cohort','family','display_name','target','games','exact_game_ids_sha256','cohort_basis','matches_complete_neural_scored_cohort',
    'accuracy','correct_winners','log_loss','brier','ece_10_equal_width','roc_auc','mae','rmse','bias','empirical_crps',
    'interval80_coverage','interval95_coverage','interval80_mean_width','interval95_mean_width','calibration_bins',
    'cover_eligible_games','cover_evaluation_nonpush_games','cover_metric_status','comparison_baseline','primary_metric',
    'primary_delta','comparison_status','promotion_allowed'];
  function download(name, content) {
    const url = URL.createObjectURL(new Blob([content], {type:'text/csv;charset=utf-8'})), link = document.createElement('a');
    link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function rows() {
    return ((({v041:N,v040:C,v039:O,v038:R}[$('development-study').value])).metrics[$('development-cohort').value] || [])
      .filter(row => row.target === $('development-target').value);
  }
  function renderTargetCoverage() {
    const counts = targetCoverage(G.filtered(), G.projection);
    const titles = {winner:'Winner & probability',margin:'Point margin',total:'Total points',intervals:'Saved interval pair',cover:'Qualified cover probability'};
    $('target-coverage').innerHTML = Object.entries(titles).map(([key, title]) =>
      `<article><span>${title}</span><strong>${counts[key].toLocaleString()} <small>/ ${counts.games.toLocaleString()}</small></strong><small>${key === 'cover' ? 'Requires exact line and cutoff' : key === 'intervals' ? 'At least one point target · 80% + 95%' : (counts.games - counts[key]).toLocaleString() + ' without this target'}</small></article>`).join('');
  }
  function renderGameComparison(id) {
    const game = G.games.find(row => row.id === id); if (!game) return;
    openGameId = id;
    const selected = $('model-view').value;
    $('game-model-comparison').innerHTML = [...$('model-view').options].map(model => {
      const value = G.projection(game, model.value), score = scoreCenters(value.margin, value.total), errors = observedErrors(game, value);
      const winner = finite(value.p) ? (value.p >= 0.5 ? game.home : game.away) : 'Winner target unavailable';
      const result = errors?.winner_correct === true ? 'Correct' : errors?.winner_correct === false ? 'Incorrect' : game.completed ? 'No scored winner' : 'No observed final';
      const intervals = ['margin','total'].map(target => {
        const saved = value.model?.[target];
        return saved?.interval80 && saved?.interval95 ? `${target}: 80% ${saved.interval80.map(v => number(v,1)).join(' to ')}; 95% ${saved.interval95.map(v => number(v,1)).join(' to ')}` : `${target}: no saved intervals`;
      }).join(' · ');
      return `<tr${model.value === selected ? ' class="selected-model"' : ''}><td><strong>${esc(model.text)}</strong>${small(model.value === selected ? 'Selected in game center' : value.label)}</td><td>${esc(winner)}${small('Home ' + percent(value.p))}</td><td>${signed(value.margin)}</td><td>${number(value.total)}</td><td>${score ? `${number(score.away,1)} – ${number(score.home,1)}${small(score.negative ? 'Unconstrained center below zero; retained without clipping' : 'Away – home · derived from displayed point centers')}` : 'Both point targets required'}</td><td>${esc(result)}${small('Margin error ' + signed(errors?.margin_error))}${small('Total error ' + signed(errors?.total_error))}</td><td>${esc(intervals)}</td></tr>`;
    }).join('');
    $('game-comparison-note').textContent = 'Same official game identity across saved model families. Score centers are (total ± home margin) / 2 and may be fractional or unconstrained. Errors use the rounded displayed points and are not used to rescore headline metrics. Cover probability is not inferred from these outputs.';
  }
  function selectOptions(element, list, preferred) {
    const previous = element.value;
    element.innerHTML = list.map(row => option(row.family, familyLabel(row))).join('');
    element.value = list.some(row => row.family === previous) ? previous : list.some(row => row.family === preferred) ? preferred : list[0]?.family || '';
    element.disabled = list.length === 0;
  }
  function renderCalibration(list) {
    const selected = list.find(row => row.family === $('calibration-model').value);
    const bins = selected?.calibration_bins;
    $('calibration-title').textContent = selected ? familyLabel(selected) + ' · stored reliability bins' : 'No winner metrics in this cohort';
    const valid = Array.isArray(bins) && bins.length && bins.every(bin => finite(bin.mean_probability) && finite(bin.observed_rate) && Number.isInteger(bin.n) && bin.n > 0);
    if (!valid) {
      $('calibration-chart').innerHTML = '<p class="diagnostic-empty">No saved calibration bins for this family and cohort. ECE alone cannot reconstruct a reliability curve. The rounded per-game probabilities are not rescored to fill it.</p>';
      $('calibration-bins').innerHTML = '';
      $('calibration-status').textContent = selected ? 'Saved bins unavailable · probability metrics remain in their original table.' : 'Choose a study/cohort with recorded winner metrics.';
      return;
    }
    const ticks = [0,.25,.5,.75,1], x = p => 42 + 256 * p, y = p => 278 - 256 * p;
    $('calibration-chart').innerHTML = `<svg viewBox="0 0 340 330" role="img" aria-label="Stored calibration bins: forecast home-win probability versus observed home-win rate. The dashed diagonal marks equality."><title>Stored reliability curve, ${esc(familyLabel(selected))}</title>${ticks.map(t => `<line class="chart-grid" x1="42" y1="${y(t)}" x2="298" y2="${y(t)}"/><text x="34" y="${y(t)+4}" text-anchor="end">${Math.round(t*100)}%</text><text x="${x(t)}" y="298" text-anchor="middle">${Math.round(t*100)}%</text>`).join('')}<line class="chart-reference" x1="42" y1="278" x2="298" y2="22"/><polyline class="chart-line" points="${bins.map(bin => `${x(bin.mean_probability)},${y(bin.observed_rate)}`).join(' ')}"/>${bins.map(bin => `<circle class="chart-point" cx="${x(bin.mean_probability)}" cy="${y(bin.observed_rate)}" r="${Math.min(9,3+Math.sqrt(bin.n)/3)}"><title>Mean probability ${percent(bin.mean_probability)}; observed ${percent(bin.observed_rate)}; ${bin.n} games</title></circle>`).join('')}<text x="170" y="322" text-anchor="middle">Mean forecast home-win probability</text></svg>`;
    $('calibration-bins').innerHTML = bins.map(bin => `<tr><td>${esc(bin.bin)}</td><td>${bin.n}</td><td>${percent(bin.mean_probability)}</td><td>${percent(bin.observed_rate)}</td><td>${signed((bin.observed_rate-bin.mean_probability)*100,1)} pp</td></tr>`).join('');
    $('calibration-status').textContent = `${bins.reduce((sum,bin)=>sum+bin.n,0)} games in stored bins · observed home-win rate on the vertical axis · ECE ${number(selected.ece_10_equal_width,4)} · no uncertainty bands were recorded.`;
  }
  function renderMetricDiagnostics() {
    const list = rows(), target = $('development-target').value, cohort = $('development-cohort').value;
    const preferred = $('development-study').value !== 'v038' ? 'v038_fixed_equal_blend' : 'fixed_equal_blend';
    selectOptions($('diagnostic-baseline'),list,preferred);
    const baseline = list.find(row => row.family === $('diagnostic-baseline').value), key = target === 'winner' ? 'log_loss' : 'mae';
    $('delta-heading').textContent = target === 'winner' ? 'Log-loss difference from a fixed baseline' : target === 'cover' ? 'Cover evaluation requires an admitted line cohort' : 'Point-error difference from a fixed baseline';
    $('metric-deltas').innerHTML = list.map(row => {
      const delta = metricDelta(row,baseline,key);
      return `<tr><td>${esc(familyLabel(row))}</td><td>${row.games}</td><td>${number(row[key],4)}</td><td>${finite(delta.value)?signed(delta.value,4):esc(delta.reason)}</td><td>${esc(delta.value==null?delta.reason:delta.value===0?'Baseline / equal metric':delta.value<0?'Lower on this cohort':'Higher on this cohort')}</td></tr>`;
    }).join('') || '<tr><td colspan="5">No authenticated comparable cover cohort or recorded cover probabilities. No score is assigned.</td></tr>';
    $('delta-metric-name').textContent = key === 'log_loss' ? 'Log loss ↓' : 'MAE ↓';
    $('delta-note').textContent = baseline ? `Baseline: ${familyLabel(baseline)}. Negative differences mean lower ${key === 'log_loss' ? 'log loss' : 'MAE'}, with matching target, game count and exact game-ID hash required. Cohort ${baseline.exact_game_ids_sha256}. These stored reconstruction metrics cannot establish pregame issuance or select a champion.` : 'There is no valid baseline for this study, target and cohort. Unavailable scores are not zero.';
    $('export-metrics').disabled = list.length === 0;
    const winnerRows = ((({v041:N,v040:C,v039:O,v038:R}[$('development-study').value])).metrics[cohort] || []).filter(row => row.target === 'winner');
    selectOptions($('calibration-model'),winnerRows,preferred);
    renderCalibration(winnerRows);
  }
  $('diagnostic-baseline').addEventListener('change',renderMetricDiagnostics);
  $('calibration-model').addEventListener('change',() => {
    const source = ({v041:N,v040:C,v039:O,v038:R}[$('development-study').value]);
    renderCalibration((source.metrics[$('development-cohort').value] || []).filter(row => row.target === 'winner'));
  });
  ['development-study','development-cohort','development-target'].forEach(id => $(id).addEventListener('change',renderMetricDiagnostics));
  $('export-metrics').addEventListener('click',() => {
    const list = rows(), baseline = list.find(row => row.family === $('diagnostic-baseline').value), key = $('development-target').value === 'winner' ? 'log_loss' : 'mae';
    const records = list.map(row => {const d=metricDelta(row,baseline,key);return {...row,study:row.study || $('development-study').value,evaluation_cohort:$('development-cohort').value,comparison_baseline:baseline?.family,primary_metric:key,primary_delta:d.value,comparison_status:d.reason};});
    download(`fbs-${$('development-study').value}-${$('development-cohort').value}-${$('development-target').value}-stored-metrics.csv`,csv(records,metricColumns));
  });
  $('export-game-models').addEventListener('click',() => {
    const game = G.games.find(row => row.id === openGameId);if(!game)return;
    const records = [...$('model-view').options].map(model => {const p=G.projection(game,model.value),s=scoreCenters(p.margin,p.total),e=observedErrors(game,p);return {season:game.season,game_id:game.id,away:game.away,home:game.home,model:model.value,evidence:p.label,p_home:p.p,margin:p.margin,total:p.total,derived_away_score:s?.away,derived_home_score:s?.home,observed_winner_correct:e?.winner_correct,display_margin_error:e?.margin_error,display_total_error:e?.total_error,margin_interval80:p.model?.margin?.interval80,margin_interval95:p.model?.margin?.interval95,total_interval80:p.model?.total?.interval80,total_interval95:p.model?.total?.interval95,cover_status:p.model?.margin?.cover_status || 'NO_QUALIFIED_COVER_PROBABILITY',cutoff:p.record?.cutoff,computed_at:p.model?.winner?.computed_at_utc || p.model?.margin?.computed_at_utc};});
    download(`fbs-${game.id}-saved-model-comparison.csv`,csv(records,Object.keys(records[0])));
  });
  document.addEventListener('fbs:games-rendered',renderTargetCoverage);
  document.addEventListener('fbs:game-opened',event => renderGameComparison(event.detail.id));
  renderTargetCoverage();renderMetricDiagnostics();
})();
