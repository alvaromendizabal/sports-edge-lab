'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const names = {
    current_v067: 'New V067 issued foundation outlook',
    original: 'Prior preserved original selection',
    retained_v061: 'Dated V061 selected-original archive',
    calibrated: 'Separate calibrated shadow revision',
    mixture_global: 'Experimental global mixture',
    mixture_gated: 'Experimental gated mixture',
    replay: 'Retrospective reconstruction'
  };
  const providers = ['DraftKings', 'Kalshi', 'Polymarket Global', 'Polymarket US'];
  const targets = ['winner', 'margin', 'total', 'cover_probability'];
  const esc = value => String(value == null ? 'Unobserved' : value).replace(/[&<>"']/g,
    c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const human = value => String(value || 'Unobserved').toLowerCase().replaceAll('_', ' ');
  const fmt = (value, digits = 1) => value == null ? '—' : Number(value).toFixed(digits);
  const prob = value => value == null ? '—' : (value * 100).toFixed(2) + '%';
  const stamp = value => value ? value.replace('T', ' ').replace(/\.\d+(?=Z|[+-])/, '') : 'Unobserved';
  const pacific = value => value ? new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', hour: 'numeric',
    minute: '2-digit', timeZoneName: 'short'
  }).format(new Date(value)) : 'Exact kickoff unresolved';
  let data, page = 0, filtered = [];

  function selected(game) { return game.layers[$('layer').value]; }
  function filterGames() {
    const period = $('period').value, coverage = $('coverage').value;
    const query = $('search').value.trim().toLowerCase();
    return data.games.filter(game => {
      const timedFuture = game.schedule_status === 'CURRENT_ORIGIN_REFRESH_DUE';
      const originalPresent = game.layers.original.values.p_home !== null;
      if (period === 'upcoming' && !timedFuture) return false;
      if (period === 'missing_original' && (!timedFuture || originalPresent)) return false;
      if (period === 'refresh_gap' && (!game.current_owner_baseline_refresh.attempted || game.current_owner_baseline_refresh.status === 'CURRENT_ORIGIN_SHADOW_ISSUED')) return false;
      if (period === 'completed_original' && (!game.completed || !originalPresent)) return false;
      if (period === 'restored' && !game.archive_continuity.earlier_v062_missing_original_restored) return false;
      if (period === 'updated' && !game.archive_continuity.earlier_v062_older_selection_recovered) return false;
      if (period === 'tbd' && game.kickoff_utc !== null) return false;
      if (period === 'final' && !game.completed) return false;
      if (period === 'pending' && (game.completed || game.kickoff_utc === null || timedFuture)) return false;
      const hasValue = selected(game).values.p_home !== null;
      if ((coverage === 'with' && !hasValue) || (coverage === 'without' && hasValue)) return false;
      return !query || `${game.home} ${game.away} ${game.game_id}`.toLowerCase().includes(query);
    });
  }

  function render() {
    filtered = filterGames();
    const pages = Math.max(1, Math.ceil(filtered.length / 30));
    page = Math.min(page, pages - 1);
    const layer = $('layer').value;
    const withValues = filtered.filter(game => selected(game).values.p_home !== null).length;
    $('layer-note').textContent = data.layer_definitions[layer];
    $('game-summary').textContent = `${filtered.length} of 888 source games shown · ${withValues} with retained probability · ${filtered.length - withValues} explicit gaps`;
    $('game-rows').innerHTML = filtered.slice(page * 30, (page + 1) * 30).map(game => {
      const item = selected(game), values = item.values, hasValue = values.p_home !== null;
      const activity = game.current_owner_baseline_refresh.attempted ? 'V067 current outlook issued' : null;
      const evidence = item.information_cutoff_utc ? 'Information cutoff ' + stamp(item.information_cutoff_utc) :
        layer === 'replay' ? 'Historical availability unproved' : 'No authenticated issue in this layer';
      return `<tr data-game="${esc(game.game_id)}"><td><button class="game-link" data-detail="${esc(game.game_id)}">${esc(game.away)} at ${esc(game.home)}</button><span class="minor">${esc(pacific(game.kickoff_utc))}</span><span class="minor">${game.completed ? `Final: ${game.actual_away_points}–${game.actual_home_points}` : esc(human(game.schedule_status))}</span></td><td class="num" data-value="probability">${prob(values.p_home)}</td><td class="num" data-value="margin">${fmt(values.home_margin)}</td><td class="num" data-value="total">${fmt(values.total_points)}</td><td class="num" data-value="scores">${fmt(values.away_score)}–${fmt(values.home_score)}<span class="minor">away–home</span></td><td class="${hasValue ? 'ok' : 'gap'}">${esc(hasValue ? names[layer] : human(item.target_status.p_home))}${activity ? '<span class="minor">' + esc(activity) + '</span>' : ''}<span class="minor">${esc(evidence)}</span></td></tr>`;
    }).join('') || '<tr><td colspan="6">No games match these filters. Clear the search or choose all games.</td></tr>';
    $('page-status').textContent = `Page ${page + 1} of ${pages}`;
    $('previous').disabled = page === 0;
    $('next').disabled = page === pages - 1;
    $('download-view').disabled = filtered.length === 0;
  }

  function renderLeaders() {
    const season = $('leader-season').value;
    $('leader-rows').innerHTML = data.historical_cohort_leaders.filter(row => season === 'all' || String(row.season) === season)
      .map(row => `<tr><td>${esc(row.comparison_group)}</td><td>${row.season}</td><td>${esc(row.target)} / ${esc(row.metric)}</td><td>${row.games}</td><td class="num">${fmt(row.best_saved_value, 6)}</td><td>${row.compared_card_count}</td><td>Exposed descriptive leader<span class="minor">Not promoted; ${row.original_issued_games ?? 'unobserved'} proved original issues in saved card</span></td></tr>`).join('');
  }

  function interval(value) {
    if (value === null || value === undefined) return 'Unobserved';
    return JSON.stringify(value);
  }
  function openGame(id) {
    const game = data.games.find(item => item.game_id === id);
    if (!game) return;
    $('detail-title').textContent = `${game.away} at ${game.home}`;
    const layerRows = Object.entries(game.layers).map(([name, item]) => {
      const values = item.values;
      return `<tr data-layer="${esc(name)}"><td>${esc(names[name])}<span class="minor">${esc(human(item.status))}</span></td><td>${prob(values.p_home)}</td><td>${fmt(values.home_margin)}</td><td>${fmt(values.total_points)}</td><td>${fmt(values.away_score)}–${fmt(values.home_score)}<span class="minor">away–home</span></td><td>${esc(item.horizon || 'No issued horizon')}<span class="minor">Cutoff: ${esc(item.information_cutoff_utc || 'Unproved / absent')}</span><span class="minor">Durably observed: ${esc(item.original_durable_observed_at || 'Unproved / absent')}</span><span class="minor">Margin intervals: ${esc(interval(values.margin_intervals))}</span><span class="minor">Total intervals: ${esc(interval(values.total_intervals))}</span></td></tr>`;
    }).join('');
    const providerRows = providers.flatMap(provider => targets.map(target => {
      const item = data.provider_evidence[game.provider_reference_ids[provider][target]];
      return `<tr data-provider="${esc(provider)}" data-target="${esc(target)}"><td>${esc(provider)}</td><td>${esc(human(target))}</td><td>${target === 'winner' || target === 'cover_probability' ? prob(item.value) : fmt(item.value)}<span class="minor">${esc(human(item.interpretation))}</span></td><td>${esc(human(item.status))}<span class="minor">Quote: ${esc(item.quote_at || 'Missing')}</span><span class="minor">Acquired: ${esc(item.acquired_at || 'Missing')}</span><span class="minor">Age status: ${esc(human(item.age_status))}; seconds at saved view: ${fmt(item.age_seconds_at_view, 0)}</span><span class="minor">Product: ${esc(item.product || 'Unobserved')}</span><span class="minor">Qualified matched baseline: ${item.statistically_usable_baseline ? 'yes' : 'no'}</span></td></tr>`;
    })).join('');
    const continuity = game.archive_continuity;
    const recovery = continuity.earlier_v062_missing_original_restored ? ' The earlier original omitted from the prior ledger is restored with its original clock.' :
      continuity.earlier_v062_older_selection_recovered ? ' The newer original selection is recovered with its original clock.' : '';
    $('detail-content').innerHTML = `<p>${game.current_owner_baseline_refresh.attempted ? 'V067 issued a new foundation outlook after its registered current refit. This is a research baseline, not a promoted champion.' : 'No current-origin refresh task for this game.'} Earlier originals keep their true issue clocks; the new V067 layer is separate. Stored intervals have no calibrated-coverage claim.${recovery}</p><p>Game ${esc(id)} · ${esc(stamp(game.kickoff_utc))} · ${game.completed ? 'Final ' + game.actual_away_points + '–' + game.actual_home_points : 'Final not observed in this source capture'}</p><div class="clock-grid"><div>Fixture source observed<br><b>${esc(game.source_observed_at || 'Missing')}</b></div><div>Latest qualified champion issue<br><b class="gap">None authorized by V064 champion check</b></div></div><section class="detail-block"><h3>Separate saved forecast layers</h3><p>Home probability and signed home margin use the same venue orientation. All six older layers keep their original values. The seventh layer contains the new V067 issues. A calibrated or mixture revision remains separate from an original issue. Reconstructions are not issued forecasts. Displayed values are rounded from saved authenticated records.</p><div class="table-wrap"><table><thead><tr><th>Layer</th><th>Home win</th><th>Home margin</th><th>Total</th><th>Projected score</th><th>Clocks / horizon / saved intervals</th></tr></thead><tbody id="detail-layer-rows">${layerRows}</tbody></table></div></section><section class="detail-block"><h3>Provider references and source gaps</h3><p>Descriptive retained observations remain distinct from qualified matched pregame benchmarks. A threshold center or point line is not an expected score. Missing quote clocks or late acquisition remain explicit.</p><div class="table-wrap"><table><thead><tr><th>Provider</th><th>Target</th><th>Derived reference</th><th>Eligibility and clocks</th></tr></thead><tbody id="detail-provider-rows">${providerRows}</tbody></table></div></section>`;
    $('game-detail').showModal();
  }

  function download() {
    const layer = $('layer').value;
    const fields = ['game_id', 'home', 'away', 'kickoff_utc', 'completed', 'layer', 'evidence_class', 'information_cutoff_utc', 'durable_observed_at', 'p_home', 'home_margin', 'total_points', 'home_score', 'away_score', 'target_status', 'current_refresh_status'];
    const quote = value => '"' + String(value == null ? '' : value).replaceAll('"', '""') + '"';
    const rows = filtered.map(game => {
      const item = selected(game), values = item.values;
      return [game.game_id, game.home, game.away, game.kickoff_utc, game.completed, layer, item.evidence_class,
        item.information_cutoff_utc, item.original_durable_observed_at, values.p_home, values.home_margin,
        values.total_points, values.home_score, values.away_score, item.target_status.p_home,
        game.current_owner_baseline_refresh.status].map(quote).join(',');
    });
    const url = URL.createObjectURL(new Blob([[fields.map(quote).join(','), ...rows].join('\r\n')], {type: 'text/csv;charset=utf-8'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = `fbs-v068-2026-${layer}-${$('period').value}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  window.FBS_LATEST_READY = (async () => {
    if (typeof DecompressionStream === 'undefined') throw new Error('This browser cannot decode the compact inventory. Use the CSV or JSON.gz download.');
    const bytes = Uint8Array.from(atob(window.FBS_LATEST_V068_GZIP), char => char.charCodeAt(0));
    data = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
    if (data.schema !== 'fbs.public.v068.latest-authenticated-game-view.v1' || data.games.length !== 888) throw new Error('Inventory schema or denominator mismatch.');
    window.FBS_LATEST_V068 = data;
    for (const id of ['period', 'layer', 'coverage']) $(id).addEventListener('change', () => { page = 0; render(); });
    $('search').addEventListener('input', () => { page = 0; render(); });
    $('previous').addEventListener('click', () => { page--; render(); });
    $('next').addEventListener('click', () => { page++; render(); });
    $('game-rows').addEventListener('click', event => {
      const button = event.target.closest('[data-detail]');
      if (button) openGame(button.dataset.detail);
    });
    $('close-detail').addEventListener('click', () => $('game-detail').close());
    $('download-view').addEventListener('click', download);
    $('leader-season').addEventListener('change', renderLeaders);
    $('champion-rows').innerHTML = data.champion_status.roles.map(row => `<tr><td>${esc(row.objective)}</td><td class="gap">No authorized rolling champion</td></tr>`).join('');
    $('current-metric-rows').innerHTML = data.current_retained_metric_evidence.leader_roles.map(row => `<tr><td>${esc(human(row.target))} / ${esc(human(row.metric))}${row.tied_leader_count > 1 ? '<span class="minor">' + row.tied_leader_count + ' tied descriptive leaders</span>' : ''}</td><td>${row.games}</td><td>${row.candidate_family_count}</td><td class="num">${row.metric === 'accuracy' ? prob(row.value) : fmt(row.value, 6)}</td><td>Retained development evidence<span class="minor">Exposed; not an original-issued scorecard; not promoted</span></td></tr>`).join('');
    $('new-research-rows').innerHTML = data.new_research.new_vs_restored_metric_rows.map(row => `<tr><td>${row.season}</td><td>${esc(row.target)} / ${esc(row.metric)}</td><td>${row.games}</td><td class="num">${fmt(row.restored_selected_control, 6)}</td><td class="num">${fmt(row.best_new_value, 6)}</td><td>Restored reference leads</td></tr>`).join('');
    $('native-monitor-rows').innerHTML = data.native_latest_label_monitor.selected_descriptive_rows.map(row => `<tr><td>${esc(row.display_role)}</td><td>${row.games}</td><td>${row.correct}</td><td>${prob(row.accuracy)}</td><td class="num">${fmt(row.log_loss, 6)}</td><td class="num">${fmt(row.brier, 6)}</td></tr>`).join('');
    $('draftkings231-rows').innerHTML = data.saved_231_draftkings_comparison.rows.map(row => `<tr><td>${esc(row.role)}</td><td>${row.games}</td><td>${row.correct}</td><td>${fmt(row.accuracy_percent, 4)}%</td><td class="num">${fmt(row.log_loss, 6)}</td><td class="num">${fmt(row.brier, 6)}</td></tr>`).join('');
    $('annual-rows').innerHTML = data.annual_descriptive_leaders.map(row => `<tr><td>${row.season}</td><td>${esc(row.target)} / ${esc(row.metric)}</td><td>${row.games}</td><td class="num">${row.metric === 'accuracy' ? prob(row.value) : fmt(row.value, 6)}</td><td>${esc(row.family)}</td><td>${row.compared_candidates}</td></tr>`).join('');
    render();
    renderLeaders();
    return data;
  })();
  window.FBS_LATEST_READY.catch(error => {
    $('game-summary').textContent = error.message;
    $('game-summary').classList.add('gap');
  });
})();
