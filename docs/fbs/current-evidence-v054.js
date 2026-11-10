'use strict';
(async () => {
  const layers = {
    original: 'Original foundation issue',
    latest_foundation: 'Latest foundation issue or revision',
    first_calibrated: 'Earlier calibrated revision',
    calibrated: 'Latest calibrated revision',
    mixture_global: 'Global mixture issued shadow',
    mixture_gated: 'Conditional mixture issued shadow',
    historical: 'Historical reconstruction'
  };
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const number = (value, digits = 2) => finite(value) ? value.toFixed(digits) : '—';
  const percentage = value => finite(value) ? (value * 100).toFixed(2) + '%' : '—';
  const shortStatus = value => ({
    AUTHENTICATED_SAVED_FUTURE_SHADOW_ISSUE: 'Saved future-issued shadow',
    AUTHENTICATED_SAVED_CALIBRATED_SHADOW_REVISION: 'Separate future-issued calibration',
    NO_SAVED_ORIGINAL_ISSUE: 'No original issue proved',
    NO_SAVED_CALIBRATED_REVISION: 'No saved calibrated revision',
    NO_SAVED_MIXTURE_ISSUE: 'No saved mixture issue',
    INSUFFICIENT_PRIOR_OUTCOMES: 'Insufficient earlier outcomes',
    EXACT_KICKOFF_UNRESOLVED: 'Exact kickoff unresolved'
  }[value] || String(value || 'No saved output').replaceAll('_', ' ').toLowerCase());
  function select(data, {season = '2026', period = 'current_week', search = ''} = {}) {
    const term = search.trim().toLowerCase();
    return data.games.filter(g => (season === 'all' || String(g.season) === season)
      && (period === 'all' || period === 'tbd' && !g.kickoff_utc || g.period === period
          || !g.kickoff_utc && g.nominal_tbd_period === period)
      && (!term || `${g.id} ${g.home} ${g.away}`.toLowerCase().includes(term)));
  }
  const cell = value => '"' + String(value ?? '')
    .replace(typeof value === 'string' ? /^[=+@\-\t\r\n]/ : /$^/, "'$&")
    .replaceAll('"', '""') + '"';
  function csv(rows, layer) {
    if (!Object.hasOwn(layers, layer)) throw new Error('Unknown evidence layer');
    const head = ['official_game_id', 'season', 'home', 'away', 'exact_kickoff_utc', 'source_observed_at',
      'forecast_layer', 'evidence_status', 'home_win_probability', 'home_margin', 'total_points',
      'home_score', 'away_score', 'information_cutoff_utc', 'computed_at_utc', 'published_at_utc',
      'original_durable_observed_at', 'issue_deadline_utc'];
    return [head, ...rows.map(g => {
      const v = g[layer];
      return [g.id, g.season, g.home, g.away, g.kickoff_utc, g.source_observed_at, layer, v.status,
        v.p_home, v.home_margin, v.total_points, v.home_score, v.away_score, v.information_cutoff_utc,
        v.computed_at_utc, v.published_at_utc, v.original_durable_observed_at, v.issue_deadline_utc];
    })].map(row => row.map(cell).join(',')).join('\r\n');
  }
  const api = {select, csv, shortStatus, layers};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window === 'undefined') return;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  let data;
  try { data = await window.FBS_CURRENT_EVIDENCE_V054_READY; }
  catch (_) {
    $('game-summary').textContent = 'The saved game file could not be decoded in this browser. Execution and evaluation evidence remains visible; the compressed JSON export is available above.';
    return;
  }
  if (!data) return;
  window.FBSCurrentEvidence = api;
  const execution = window.FBS_EXECUTION_STATUS_V054 || data.execution;
  const date = value => value && Number.isFinite(Date.parse(value))
    ? new Intl.DateTimeFormat('en-US', {timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric',
        year: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short'}).format(new Date(value))
    : 'Exact time not established';
  let page = 0, filtered = [];
  const size = 40;
  $('source-clock').textContent = `Source observed ${date(data.source_observed_at)}; capture completed ${date(data.source_capture_completed_at)}. Owner evidence ended ${date(data.as_of)}. This is a saved snapshot.`;
  $('execution-summary').textContent = execution.public_summary;
  const cards = [['New base fits', execution.new_base_fits], ['New mixture fits', execution.new_mixture_fits],
    ['New issue records', execution.new_issue_records], ['Current scalar outputs', execution.new_current_scalar_outputs],
    ['Provider requests', execution.provider_requests], ['Failed optimizers', execution.failed_optimizer_attempts]];
  $('execution-grid').innerHTML = cards.map(([label, value]) => `<article><span>${esc(label)}</span><strong>${finite(value) ? value.toLocaleString() : 'Not measured'}</strong></article>`).join('');
  const study = data.saved_r15_comparison;
  const metricRows = [['joint_log_loss', 'Joint score log loss'], ['winner_log_loss', 'Winner log loss'],
    ['winner_brier', 'Winner Brier score'], ['winner_accuracy', 'Winner accuracy'],
    ['margin_mae', 'Point-margin MAE'], ['total_mae', 'Total-points MAE'],
    ['margin_rmse', 'Margin RMSE'], ['total_rmse', 'Total RMSE'],
    ['margin_crps', 'Margin CRPS'], ['total_crps', 'Total CRPS'], ['winner_ece10', 'Winner calibration gap (ECE)']];
  $('mixture-rows').innerHTML = metricRows.map(([key, label]) => `<tr><td>${esc(label)}</td>${['foundation', 'global', 'gated', 'equal'].map(arm => `<td>${key === 'winner_accuracy' ? percentage(study.metrics[arm][key]) : number(study.metrics[arm][key], 6)}</td>`).join('')}</tr>`).join('');
  $('ablation-rows').innerHTML = [['gated', 'Conditional mixture'], ['without_uncertainty', 'Uncertainty group removed'], ['without_disagreement', 'Disagreement group removed']].map(([key, label]) => {
    const uncertainty = study.uncertainty[key];
    return `<tr><td>${esc(label)}</td><td>${number(study.metrics[key].joint_log_loss, 6)}</td><td>+${number(uncertainty.paired_joint_log_loss_delta, 6)}</td><td>[${uncertainty.week_block_bootstrap_interval95.map(v => number(v, 6)).join(', ')}]</td></tr>`;
  }).join('');
  $('mixture-qualification').textContent = `${study.qualification} Evaluation computed ${date(study.computed_at_utc)}. Current mixture issues remain a separate unscored cohort.`;
  const calibration = data.saved_r12_comparison;
  $('calibration-rows').innerHTML = [['joint_log_loss', 'Joint score log loss'], ['winner_log_loss', 'Winner log loss'],
    ['winner_brier', 'Winner Brier score'], ['margin_absolute_error', 'Point-margin MAE'], ['total_absolute_error', 'Total-points MAE']].map(([key, label]) => {
      const delta = calibration.uncertainty.metrics[key]?.mean_difference;
      return `<tr><td>${esc(label)}</td><td>${number(calibration.aggregate.control[key], 6)}</td><td>${number(calibration.aggregate.calibrated[key], 6)}</td><td>${finite(delta) ? (delta > 0 ? '+' : '') + number(delta, 6) : 'Unchanged'}</td></tr>`;
    }).join('');
  function render() {
    filtered = select(data, {season: $('season').value, period: $('period').value, search: $('search').value});
    page = Math.min(page, Math.max(0, Math.ceil(filtered.length / size) - 1));
    const layer = $('layer').value, available = filtered.filter(g => finite(g[layer].p_home)).length;
    const tbd = filtered.filter(g => !g.kickoff_utc).length;
    $('game-summary').textContent = `${filtered.length.toLocaleString()} source games · ${available.toLocaleString()} with saved values in this layer · ${(filtered.length - available).toLocaleString()} explicit gaps · ${tbd} unresolved exact kickoffs. A later revision never replaces its original issue.`;
    $('game-rows').innerHTML = filtered.slice(page * size, (page + 1) * size).map(g => {
      const v = g[layer];
      return `<tr><td>${esc(g.away)} at ${esc(g.home)}<small>${esc(g.id)} · ${g.completed ? `Final ${esc(g.actual_away_points)}–${esc(g.actual_home_points)}` : 'No observed final'}</small></td><td>${esc(date(g.kickoff_utc))}${!g.kickoff_utc && g.nominal_source_date ? `<small>Source date ${esc(g.nominal_source_date.slice(0, 10))} · time unconfirmed</small>` : ''}</td><td><span class="status ${finite(v.p_home) ? 'available' : 'gap'}">${esc(shortStatus(v.status))}</span></td><td>${percentage(v.p_home)}</td><td>${number(v.home_margin)}</td><td>${number(v.total_points)}</td><td>${number(v.away_score)} / ${number(v.home_score)}</td><td><button data-game="${esc(g.id)}" aria-label="Inspect ${esc(g.away)} at ${esc(g.home)}">Inspect</button></td></tr>`;
    }).join('') || '<tr><td colspan="8">No games match these filters.</td></tr>';
    $('page-status').textContent = `Page ${filtered.length ? page + 1 : 0} of ${Math.ceil(filtered.length / size)}`;
    $('previous-page').disabled = page === 0;
    $('next-page').disabled = (page + 1) * size >= filtered.length;
    $('download-csv').disabled = filtered.length === 0;
  }
  function details(id) {
    const g = data.games.find(row => row.id === id);
    if (!g) return;
    $('detail-title').textContent = `${g.away} at ${g.home}`;
    let text = `<p class="note">Official game ${esc(g.id)} · ${esc(date(g.kickoff_utc))}<br>Source observed ${esc(date(g.source_observed_at))}. ${g.completed ? 'Final score: ' + esc(g.actual_away_points) + '–' + esc(g.actual_home_points) : 'No observed final.'}</p>`;
    for (const [key, label] of Object.entries(layers)) {
      const v = g[key];
      text += `<details class="detail-layer" ${key === $('layer').value ? 'open' : ''}><summary>${esc(label)} · ${esc(shortStatus(v.status))}</summary><dl><dt>Home win probability</dt><dd>${percentage(v.p_home)}</dd><dt>Home margin / total</dt><dd>${number(v.home_margin)} / ${number(v.total_points)}</dd><dt>Away / home score</dt><dd>${number(v.away_score)} / ${number(v.home_score)}</dd><dt>Information cutoff</dt><dd>${esc(v.information_cutoff_utc || 'Not an original issue clock')}</dd><dt>Computed</dt><dd>${esc(v.computed_at_utc || 'Not in this rounded layer')}</dd><dt>Published</dt><dd>${esc(v.published_at_utc || 'Not in this rounded layer')}</dd><dt>Durable issue observed</dt><dd>${esc(v.original_durable_observed_at || 'No original issue proved')}</dd><dt>Issue deadline</dt><dd>${esc(v.issue_deadline_utc || 'No separate deadline in this layer')}</dd><dt>Saved margin intervals</dt><dd>${esc(v.margin_intervals ? JSON.stringify(v.margin_intervals) : 'Not in this saved layer')}</dd><dt>Saved total intervals</dt><dd>${esc(v.total_intervals ? JSON.stringify(v.total_intervals) : 'Not in this saved layer')}</dd></dl><p>${key === 'historical' ? 'Exposed retrospective development. These values do not establish an original publication before the game.' : 'This saved issue keeps its own information and publication clocks. It is a research shadow, with no automatic promotion or prospective performance confirmation.'}</p></details>`;
    }
    if (g.saved_issue_contexts.length) {
      text += '<h3>Saved issue context history</h3><p class="note">Repeated issue records can concern the same game. The table preserves their clocks without republishing private record bodies or active recipes.</p><div class="table-scroll"><table><thead><tr><th>Layer</th><th>Information cutoff · UTC</th><th>Durably observed · UTC</th><th>New in V053</th></tr></thead><tbody>';
      text += g.saved_issue_contexts.map(row => `<tr><td>${esc(row.layer)}</td><td>${esc(row.information_cutoff_utc)}</td><td>${esc(row.durably_observed_at_utc)}</td><td>${row.new_in_v053 ? 'Yes' : 'Retained'}</td></tr>`).join('') + '</tbody></table></div>';
    }
    text += '<h3>Dated provider references</h3><p class="note">Each source keeps its own capture and quote qualification. Missing values remain explicit. No qualified four-provider baseline is established.</p><div class="table-scroll"><table><thead><tr><th>Provider / target</th><th>Saved reference</th><th>Status</th><th>Quote / capture · UTC</th></tr></thead><tbody>';
    for (const [provider, targets] of Object.entries(g.providers)) for (const [target, v] of Object.entries(targets)) {
      text += `<tr><td>${esc(provider)}<small>${esc(target)}</small></td><td>${number(v.value, 3)}</td><td><span class="status">${esc(shortStatus(v.status))}</span></td><td>${esc(v.quote_at || 'Quote clock absent')}<small>${esc(v.acquired_at || 'Capture clock absent in this reference')}</small></td></tr>`;
    }
    $('detail-content').innerHTML = text + '</tbody></table></div>';
    $('game-detail').showModal();
  }
  for (const id of ['season', 'period', 'layer', 'search']) $(id).addEventListener(id === 'search' ? 'input' : 'change', () => {page = 0; render();});
  $('previous-page').onclick = () => {page--; render();};
  $('next-page').onclick = () => {page++; render();};
  $('game-rows').onclick = event => {const button = event.target.closest('[data-game]'); if (button) details(button.dataset.game);};
  $('close-detail').onclick = () => $('game-detail').close();
  $('download-csv').onclick = () => {
    const url = URL.createObjectURL(new Blob([csv(filtered, $('layer').value)], {type: 'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = `fbs-${$('layer').value}-rounded-evidence.csv`;
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const query = new URLSearchParams(location.search);
  for (const key of ['season', 'period', 'layer']) if ([...$(key).options].some(o => o.value === query.get(key))) $(key).value = query.get(key);
  render();
})();
