'use strict';
(() => {
  const $ = id => document.getElementById(id), fmt = n => Number(n).toLocaleString('en-US');
  const escape = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const percent = n => (100 * n).toFixed(3) + '%';
  let data, games, page = 0;
  const PAGE = 25;
  const metrics = {
    winner: [['log_loss','Log loss'],['brier','Brier score'],['accuracy','Winner accuracy']],
    margin: [['mae','Mean absolute error'],['rmse','Root mean squared error'],['crps','CRPS'],['bias','Mean signed error'],['interval80_coverage','80% interval coverage']],
    total: [['mae','Mean absolute error'],['rmse','Root mean squared error'],['crps','CRPS'],['bias','Mean signed error'],['interval80_coverage','80% interval coverage']]
  };
  const guides = {
    log_loss:'Lower is better. Log loss evaluates the probability assigned to the observed winner and penalizes confident wrong predictions.',
    brier:'Lower is better. Brier score is the mean squared error of the winner probabilities.',
    accuracy:'Higher is better. Winner accuracy uses a 50% probability threshold. It is not an ATS, profit or calibration measure.',
    mae:'Lower is better. Absolute error is measured in points. Margin uses home minus away; totals are a separate score model.',
    rmse:'Lower is better. Root mean squared error gives larger misses more weight, in points.',
    crps:'Lower is better. CRPS scores the saved own-model empirical predictive distribution. It is a retrospective research metric, not proof of future calibration.',
    bias:'Zero is the reference. A positive signed error indicates the model overestimated the saved outcome. Do not rank by the most negative value.',
    interval80_coverage:'80% is the nominal reference. The value is the share of saved outcomes inside the empirical held-out residual interval. Sample uncertainty and future validity remain unproved.'
  };
  const policyName = id => data.policies.find(x => x.id === id)?.label || id;
  function showTab(name, updateHash = true) {
    const selected = $('panel-' + name) ? name : 'result';
    document.querySelectorAll('[data-tab]').forEach(b => {
      const on = b.dataset.tab === selected; b.classList.toggle('active', on);
      b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1;
    });
    document.querySelectorAll('[role="tabpanel"]').forEach(p => p.hidden = p.id !== 'panel-' + selected);
    if (updateHash) history.replaceState(null, '', '#' + selected);
  }
  function updateMetricOptions() {
    const options = metrics[$('score-target').value], old = $('score-metric').value;
    $('score-metric').innerHTML = options.map(([id,label]) => `<option value="${id}">${label}</option>`).join('');
    if (options.some(([id]) => id === old)) $('score-metric').value = old;
    renderScores();
  }
  function renderScores() {
    if (!data) return;
    const target = $('score-target').value, season = Number($('score-season').value), metric = $('score-metric').value;
    const rows = data.scores.filter(r => r.target === target && r.season === season);
    const name = metrics[target].find(([id]) => id === metric)[1];
    $('score-metric-name').textContent = name;
    $('score-cohort').textContent = `${season}: ${fmt(rows[0].n)} identical games for every policy · ${rows.length} policy rows · later-fitted reconstruction`;
    $('score-body').innerHTML = rows.map(r => `<tr data-policy="${r.policy}"><td>${escape(policyName(r.policy))}</td><td class="number">${metric === 'accuracy' || metric === 'interval80_coverage' ? percent(r[metric]) : r[metric].toFixed(6)}</td><td>${fmt(r.n)}</td><td><span class="badge">${r.policy === 'control' ? 'Negative control' : 'Exposed reconstruction'}</span></td></tr>`).join('');
    $('score-guide-title').textContent = name;
    $('score-guide').textContent = guides[metric];
  }
  function renderIntervals(rows) {
    const W = 1000, H = 235, left = 245, right = 900, top = 41, step = 58;
    const min = Math.min(0, ...rows.map(r => r.adjusted95_interval[0])) * 1.12;
    const max = Math.max(.005, ...rows.map(r => r.adjusted95_interval[1])) * 1.4;
    const scale = x => left + (x - min) / (max - min) * (right - left);
    const axis = top + step * (rows.length - 1) + 37;
    let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Saved weighted relative skill with adjusted intervals; zero means equal to expanding baseline"><line x1="${scale(0)}" y1="18" x2="${scale(0)}" y2="${axis}" stroke="#8b9e93" stroke-dasharray="4 4"/><text x="${scale(0)}" y="${axis + 21}" text-anchor="middle" font-size="13" fill="#61736c">0%</text><text x="${left}" y="${axis + 21}" text-anchor="middle" font-size="13" fill="#61736c">${percent(min)}</text><text x="${right}" y="${axis + 21}" text-anchor="middle" font-size="13" fill="#61736c">${percent(max)}</text>`;
    rows.forEach((r,i) => {
      const y = top + i * step, [lo,hi] = r.adjusted95_interval, color = hi < 0 ? '#963e28' : '#416b58';
      svg += `<text x="5" y="${y + 5}" font-size="18" fill="#18342f">${escape(policyName(r.policy))}</text><line x1="${scale(lo)}" y1="${y}" x2="${scale(hi)}" y2="${y}" stroke="${color}" stroke-width="3"/><line x1="${scale(lo)}" y1="${y-7}" x2="${scale(lo)}" y2="${y+7}" stroke="${color}"/><line x1="${scale(hi)}" y1="${y-7}" x2="${scale(hi)}" y2="${y+7}" stroke="${color}"/><circle cx="${scale(r.weighted_relative_skill)}" cy="${y}" r="5" fill="${color}"/>`;
    });
    $('interval-chart').innerHTML = svg + '</svg>';
  }
  function renderWeighted() {
    if (!data) return;
    const target = $('weighted-target').value, weight = $('weighted-weight').value, window = $('weighted-window').value;
    const rows = data.comparisons.filter(r => r.target === target && r.weight_policy === weight && r.comparison_window === window);
    const seasons = rows[0].season_details;
    $('weighted-cohort').textContent = `Identical paired cohorts: 2026 ${fmt(seasons['2026'].n)} · 2025 ${fmt(seasons['2025'].n)} · 2024 ${fmt(seasons['2024'].n)} games. Baseline: expanding-history model. ${window === 'MATCHED_ELAPSED_SEASON_DAYS' ? 'Elapsed-day alignment is a proxy, not official week matching.' : 'Prior seasons extend beyond the current season span.'}`;
    $('weighted-body').innerHTML = rows.map(r => `<tr data-policy="${r.policy}"><td>${escape(policyName(r.policy))}</td><td class="number ${r.weighted_relative_skill < 0 ? 'negative' : ''}">${percent(r.weighted_relative_skill)}</td><td class="number">[${percent(r.adjusted95_interval[0])}, ${percent(r.adjusted95_interval[1])}]</td>${[2026,2025,2024].map(s => `<td class="number">${percent(r.season_details[s].relative_skill)}</td>`).join('')}</tr>`).join('');
    renderIntervals(rows);
  }
  function gameRows() {
    const season = Number($('game-season').value), status = $('game-status').value, coverage = $('game-coverage').value, query = $('game-search').value.trim().toLowerCase();
    return games.filter(g => g.season === season && (status === 'all' || g.status === status) &&
      (coverage === 'all' || g.coverage === coverage) && (!query || `${g.home} ${g.away} ${g.id}`.toLowerCase().includes(query)));
  }
  function renderGames() {
    if (!games) return;
    const rows = gameRows(); page = Math.min(page, Math.max(0, Math.ceil(rows.length / PAGE) - 1));
    $('game-count').textContent = `${fmt(rows.length)} games · ${$('game-season').value} season · saved coverage snapshot`;
    $('game-page').textContent = rows.length ? `${page * PAGE + 1}–${Math.min((page + 1) * PAGE, rows.length)} of ${fmt(rows.length)}` : '0 games';
    $('game-prev').disabled = page === 0; $('game-next').disabled = (page + 1) * PAGE >= rows.length;
    const reason = {KICKOFF_UNRESOLVED:'Kickoff unresolved',T120_ALREADY_PASSED:'T120 cutoff already passed'};
    $('game-body').innerHTML = rows.slice(page * PAGE, (page + 1) * PAGE).map(g => {
      const date = g.kickoff ? new Date(g.kickoff).toISOString().slice(0,16).replace('T',' ') + ' UTC' : 'Kickoff unresolved';
      const coverage = g.coverage === 'prepared' ? 'Prepared · not issued' : g.coverage === 'missing' ? 'Missing preparation' : g.coverage === 'final' ? 'Observed final' : 'Historical census';
      return `<tr data-game="${escape(g.id)}"><td data-label="Date / status">${escape(date)}<span class="small-line">${g.status === 'final' ? 'Final' : g.status === 'tbd' ? 'Pending · TBD' : 'Pending'}</span></td><td data-label="Matchup"><span class="matchup">${escape(g.away)} at ${escape(g.home)}</span><span class="small-line">Game ${escape(g.id)}</span></td><td data-label="Observed result" class="number">${g.status === 'final' ? `${g.away_score} – ${g.home_score}` : '—'}</td><td data-label="Coverage"><span class="badge ${g.coverage === 'missing' ? 'amber' : ''}">${coverage}</span>${g.missing_reason ? `<span class="small-line">${escape(reason[g.missing_reason] || g.missing_reason)}</span>` : ''}</td></tr>`;
    }).join('') || '<tr><td colspan="4" class="empty">No games match these filters.</td></tr>';
  }
  function renderExecution() {
    $('benchmark-body').innerHTML = data.cpu.score_benchmarks.map(r => `<tr><td>${escape(r.schedule.replace('x',' × '))}</td><td class="number">${r.wall_seconds.toFixed(4)}</td><td class="number">${r.wall_speedup_vs_one.toFixed(3)}×</td><td>${r.maximum_simultaneous_scoring_jobs}</td></tr>`).join('');
    $('gate-body').innerHTML = data.research_gate_status.map(r => `<tr><td>${escape(r.gate)}</td><td><span class="badge ${r.status === 'Verified' ? '' : 'amber'}">${escape(r.status)}</span></td><td>${escape(r.detail)}</td></tr>`).join('');
    $('archive-hash').textContent = 'Logical archive SHA-256: ' + data.return.logical_archive_sha256;
    $('manifest-hash').textContent = 'Manifest SHA-256: ' + data.return.manifest_sha256;
  }
  document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => showTab(b.dataset.tab)));
  document.querySelectorAll('[data-jump]').forEach(b => b.addEventListener('click', () => {showTab(b.dataset.jump); $('tab-' + b.dataset.jump).focus();}));
  document.querySelector('.tabs').addEventListener('keydown', e => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
    const tabs = [...document.querySelectorAll('[data-tab]')], current = tabs.indexOf(document.activeElement); if (current < 0) return;
    const next = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (current + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    e.preventDefault(); tabs[next].focus(); showTab(tabs[next].dataset.tab);
  });
  $('score-target').addEventListener('change', updateMetricOptions);
  ['score-season','score-metric'].forEach(id => $(id).addEventListener('change', renderScores));
  ['weighted-target','weighted-weight','weighted-window'].forEach(id => $(id).addEventListener('change', renderWeighted));
  ['game-season','game-status','game-coverage'].forEach(id => $(id).addEventListener('change', () => {page = 0; renderGames();}));
  $('game-search').addEventListener('input', () => {page = 0; renderGames();});
  $('game-prev').addEventListener('click', () => {page--; renderGames();});
  $('game-next').addEventListener('click', () => {page++; renderGames();});
  Promise.all(['data/review.json','data/games.json'].map(url => fetch(url).then(r => {if (!r.ok) throw new Error('Verified public data did not load.'); return r.json();})))
    .then(([review, census]) => {
      data = review; games = census.games; updateMetricOptions(); renderWeighted(); renderGames(); renderExecution();
      showTab(location.hash.slice(1), false); document.documentElement.dataset.ready = 'true';
      const publication = document.querySelector('meta[name="public-source-commit"]')?.content;
      if (publication && /^[a-f0-9]{40}$/.test(publication)) {
        $('source-link').href = `https://github.com/alvaromendizabal/sports-edge-lab/tree/${publication}/docs/fbs/v077`;
        $('source-version').textContent = 'Published from checked GitHub source ' + publication.slice(0,12) + '.';
      }
    }).catch(error => {$('load-error').textContent = error.message; $('load-error').hidden = false; document.documentElement.dataset.ready = 'error';});
})();
