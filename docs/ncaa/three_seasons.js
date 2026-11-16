(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.document) api.start(root);
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const SCHEMA = 'sel.ncaa.b088.population_public.v1';
  const YEARS = [2025, 2026, 2027];
  const LEAGUES = ['ncaam', 'ncaaw'];
  const PROVIDERS = ['draftkings_sportsbook', 'kalshi', 'polymarket_international', 'polymarket_us'];
  const NAMES = { ncaam: 'Men', ncaaw: 'Women', draftkings_sportsbook: 'DraftKings', kalshi: 'Kalshi', polymarket_international: 'Polymarket · international', polymarket_us: 'Polymarket · US', win: 'Winner', margin: 'Margin', total: 'Total', ats: 'Against the spread' };
  const METRICS = { win: ['accuracy', 'log_loss', 'brier'], margin: ['mae', 'rmse', 'bias'], total: ['mae', 'rmse', 'bias'] };
  const METRIC_NAMES = { accuracy: 'Accuracy', log_loss: 'Log loss', brier: 'Brier', mae: 'MAE · points', rmse: 'RMSE · points', bias: 'Signed bias · points' };
  const CELL_KEYS = ['public_game_key', 'league', 'season_end_year', 'population_role', 'public_home_team', 'public_away_team', 'public_event_date', 'entity_type', 'public_entity_id', 'target', 'evidence_class', 'status', 'reason_codes', 'target_population_eligible'];
  const esc = value => String(value == null ? '' : value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const array = value => Array.isArray(value) ? value : [];
  const number = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
  const integer = value => Number.isInteger(value) && value >= 0 ? value : null;
  const count = value => integer(value) === null ? 'Not verified' : value.toLocaleString('en-US');
  const text = value => typeof value === 'string' ? value : '';
  const human = value => NAMES[value] || text(value).replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase()) || 'Not reported';
  const first = (...values) => values.find(v => v !== undefined && v !== null && v !== '');
  const seasonName = year => `${Number(year) - 1}–${String(year).slice(-2)}`;
  const hashValid = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
  const hashHTML = value => hashValid(value) ? `<details class="scope-hash"><summary>${esc(value.slice(0, 16))}…</summary><code>${value}</code></details>` : '<small>Not qualified</small>';
  const tag = (value, warn) => `<span class="tag${warn ? ' warn' : ''}">${esc(value)}</span>`;
  const empty = (columns, message) => `<tr><td class="empty" colspan="${columns}">${esc(message)}</td></tr>`;
  const reasons = value => array(value).map(v => typeof v === 'string' ? human(v) : human(v.code)).filter(Boolean).join('; ') || 'No qualification reason returned';
  const reasonCounts = value => Object.entries(value || {}).map(([key, n]) => `${human(key)}: ${count(n)}`).join('; ') || 'No reason counts returned';

  function pacific(value, dateOnly) {
    if (dateOnly && /^\d{4}-\d{2}-\d{2}$/.test(text(value))) return `${value} · date only`;
    if (!value || !/(?:Z|[+-]\d{2}:\d{2})$/.test(text(value))) return 'Timestamp not qualified';
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return 'Timestamp not qualified';
    return new Intl.DateTimeFormat('en-US', { timeZone: 'America/Los_Angeles', year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', second: '2-digit', timeZoneName: 'short' }).format(date);
  }

  function populations(data) {
    return YEARS.flatMap(year => {
      const season = array(data.seasons).find(s => s.season_end_year === year) || {};
      return LEAGUES.map(league => ({
        ...((season.leagues || {})[league] || {}),
        league,
        season_end_year: year,
        season_label: season.season_label || seasonName(year),
        population_role: season.population_role || (year === 2027 ? 'test' : 'validation'),
        test_already_exposed: season.test_already_exposed === true
      }));
    });
  }

  function normalizeB088(raw) {
    validatePublicData(raw);
    const modelRows = array(raw.model_roster);
    const sourceCoverage = array(raw.model_target_coverage);
    const sourceBoards = array(raw.same_game_scoreboards);
    const sourceProviders = array(raw.provider_target_coverage);
    const sourcePairs = array(raw.paired_model_provider_scoreboards);
    const same = (row, league, year) => row.league === league && row.season_end_year === year;
    const normalized = { ...raw, snapshot_asof: raw.asof, models: modelRows.map(m => ({ ...m, role: m.lineage })) };
    normalized.seasons = raw.seasons.map(season => ({ ...season, leagues: Object.fromEntries(LEAGUES.map(league => {
      const p = { ...((season.leagues || {})[league] || {}) };
      const rows = sourceCoverage.filter(r => same(r, league, season.season_end_year));
      const providers = sourceProviders.filter(r => same(r, league, season.season_end_year));
      const boards = sourceBoards.filter(r => same(r, league, season.season_end_year));
      const denominators = {};
      for (const target of ['win', 'margin', 'total']) {
        const values = [...new Set([...rows, ...providers, ...boards].filter(r => r.target === target).map(r => integer(r.target_eligible_count)).filter(v => v !== null))];
        denominators[target] = { count: values.length === 1 ? values[0] : null, reconciliation_status: values.length === 1 ? 'CONSISTENT_RETURNED_TARGET_DENOMINATOR' : values.length ? 'TARGET_DENOMINATOR_CONFLICT' : 'TARGET_DENOMINATOR_NOT_RETURNED' };
      }
      const completeness = p.official_completeness === true;
      p.declared_population_hash = p.population_game_set_sha256;
      p.official_completeness = { verified_complete: completeness, official_completed_count: completeness ? integer(p.declared_population_count) : null, status: completeness ? 'VERIFIED_COMPLETE_AND_RECONCILED' : 'OFFICIAL_DENOMINATOR_UNVERIFIED', reasons: array(p.official_completeness_reasons) };
      p.target_eligible_denominators = denominators;
      p.declared_model_roster = modelRows.filter(m => m.league === league).map(m => m.model_id);
      p.model_target_coverage = rows.map(row => ({ ...row, observed: row.prediction_available_count, descriptive: row.descriptive_scored_count, eligible: row.qualified_scored_count, missing: row.missing_prediction_count, invalid: row.invalid_or_ambiguous_count, evidence_class: null, rank_suppression_reasons: ['COVERAGE_TOTALS_ARE_NOT_MODEL_SELECTION'], metric_scope: 'COVERAGE_TOTALS_ALL_EVIDENCE_CLASSES' }));
      p.same_game_scoreboards = boards.map(board => ({ ...board, count: board.common_cohort_count, metrics_by_model: array(board.metrics_by_model).map(row => ({ ...row, n: row.games, cohort_hash: board.common_cohort_hash })) }));
      p.provider_coverage = providers.map(row => ({ ...row, provider: row.provider_product, observed: row.observed_quote_game_count, qualified: row.qualified_game_count, missing: row.missing_qualified_game_count, qualification_status: row.qualified_game_count > 0 ? 'QUALIFIED_GAMES_RETURNED' : 'NO_QUALIFIED_GAMES_RETURNED', qualification_blockers: Object.keys(row.reason_counts_overlapping || {}) }));
      p.provider_comparisons = sourcePairs.filter(r => same(r, league, season.season_end_year));
      return [league, p];
    })) }));
    return normalized;
  }

  function officialQualified(population) {
    const value = population.official_completeness;
    if (!value || typeof value !== 'object') return false;
    return value.verified_complete === true && integer(value.official_completed_count) !== null;
  }

  function targetDenominator(population, target) {
    const value = (population.target_eligible_denominators || {})[target];
    return integer(value && typeof value === 'object' ? first(value.count, value.eligible_count) : value);
  }

  function roster(data) {
    return array(data.models).filter(m => typeof m.model_id === 'string').map(m => ({ ...m, label: text(m.public_label) || text(m.label) || m.model_id }));
  }

  function coverageRows(data) {
    const models = roster(data);
    return populations(data).flatMap(pop => {
      const rows = array(pop.model_target_coverage).map(row => ({ ...row, population: pop, league: pop.league, season_end_year: pop.season_end_year }));
      const declared = array(pop.declared_model_roster).length ? pop.declared_model_roster.map(m => typeof m === 'string' ? m : m.model_id) : models.filter(m => m.league === pop.league).map(m => m.model_id);
      for (const modelId of declared) {
        const model = models.find(m => m.model_id === modelId) || {};
        const targets = ['win', 'margin', 'total'];
        for (const target of targets) {
          if (!rows.some(r => r.model_id === modelId && r.target === target)) {
            const supported = array(model.targets).includes(target);
            rows.push({ model_id: modelId, target, target_supported: supported, evidence_class: null, observed: null, descriptive: null, eligible: null, missing: null, invalid: null, rank_permitted: false, rank_suppression_reasons: [supported ? 'COVERAGE_ROW_NOT_REPORTED' : 'TARGET_NOT_SUPPORTED_BY_DECLARED_MODEL'], metric_scope: supported ? 'NOT_REPORTED' : 'UNSUPPORTED_TARGET', population: pop, league: pop.league, season_end_year: pop.season_end_year });
          }
        }
      }
      return rows;
    });
  }

  function metricRows(board) {
    if (Array.isArray(board.metrics_by_model)) return board.metrics_by_model;
    if (board.metrics_by_model && typeof board.metrics_by_model === 'object') return Object.entries(board.metrics_by_model).map(([model_id, value]) => ({ model_id, ...(value || {}) }));
    return [];
  }

  function boardQualification(board, pop) {
    const reasons = [];
    const scope = board.metric_scope || board.scope;
    const full = scope === 'FULL_DECLARED_POPULATION';
    if (!full) reasons.push('Secondary intersection or unqualified population scope');
    if (!officialQualified(pop)) reasons.push('Official completed denominator is not verified complete');
    if (!hashValid(board.common_cohort_hash)) reasons.push('Shared game cohort hash is not qualified');
    if (!hashValid(board.declared_model_roster_hash)) reasons.push('Declared model roster hash is not qualified');
    if (!hashValid(pop.declared_model_roster_hash)) reasons.push('Separate population roster hash is not supplied');
    else if (board.declared_model_roster_hash !== pop.declared_model_roster_hash) reasons.push('Scoreboard model roster does not match the declared population roster');
    const targetPopulation = (pop.target_eligible_denominators || {})[board.target] || {};
    if (!hashValid(targetPopulation.cohort_hash)) reasons.push('Separate eligible-target population hash is not supplied');
    else if (board.common_cohort_hash !== targetPopulation.cohort_hash) reasons.push('Scoreboard game cohort does not match the declared eligible target population');
    if (integer(board.count) === null || integer(board.full_population_count) === null || board.count !== board.full_population_count) reasons.push('Shared cohort does not cover the declared full population');
    if (!(board.count > 0)) reasons.push('An empty cohort cannot support a performance rank');
    if (board.full_population_count !== targetDenominator(pop, board.target)) reasons.push('Scoreboard denominator differs from target eligibility');
    if (board.all_declared_models_complete !== true) reasons.push('Not every declared model has complete eligible evidence');
    if (board.rank_permitted !== true) reasons.push('Producer has not qualified a full-population rank');
    if (!['original_issued', 'valid_replay', 'time_valid_replay'].includes(text(board.evidence_class).toLowerCase())) reasons.push('Evidence class is not qualified for a chronological performance rank');
    const rows = metricRows(board);
    if (!rows.length) reasons.push('No qualified metric rows were returned');
    if (rows.some(row => row.cohort_hash !== board.common_cohort_hash || row.n !== board.count)) reasons.push('Metric rows do not share the declared game cohort and count');
    return { permitted: reasons.length === 0, full, reasons };
  }

  function metricValue(value, name) {
    const raw = value && typeof value === 'object' ? value.value : value;
    const n = number(raw);
    if (n === null) return '<span class="muted">Unavailable</span>';
    if ((name !== 'bias' && n < 0) || (['accuracy', 'brier'].includes(name) && n > 1)) return '<span class="muted">Invalid metric</span>';
    const formatted = name === 'accuracy' ? `${(n * 100).toFixed(2)}%` : n.toFixed(['mae', 'rmse', 'bias'].includes(name) ? 3 : 5);
    const ci = value && typeof value === 'object' ? value.interval : null;
    if (!Array.isArray(ci) || ci.length !== 2 || ci.some(v => number(v) === null)) return esc(formatted);
    const scale = name === 'accuracy' ? 100 : 1;
    return `${esc(formatted)}<small>Interval: ${(ci[0] * scale).toFixed(3)} to ${(ci[1] * scale).toFixed(3)}${name === 'accuracy' ? '%' : ''}</small>`;
  }

  function relativeAsset(path) {
    if (typeof path !== 'string' || !/^(?:population(?:_r17)?\/[A-Za-z0-9_./-]+\.jsonl?(?:\.gz)?|status_objects\/[0-9a-f]{64}\.jsonl\.gz)$/.test(path) || path.split('/').includes('..')) throw new Error('Public status asset path is not qualified.');
    return path;
  }

  function cellState(cell) {
    if (['eligible', 'missing', 'invalid', 'not_applicable'].includes(cell.coverage_state)) return cell.coverage_state;
    const status = text(cell.status).toUpperCase();
    if (['ELIGIBLE', 'QUALIFIED', 'QUALIFIED_AVAILABLE', 'ORIGINAL_ISSUED', 'VALID_REPLAY'].includes(status)) return 'eligible';
    if (status.includes('NOT_APPLICABLE') || status.includes('OUTSIDE_POPULATION') || status.includes('UNSUPPORTED_TARGET') || status === 'TARGET_NOT_SUPPORTED_BY_DECLARED_MODEL') return 'not_applicable';
    if (status.includes('INVALID') || status.includes('UNQUALIFIED') || status.includes('REJECTED')) return 'invalid';
    if (status.includes('MISSING') || status.includes('UNAVAILABLE') || status.includes('NOT_OBSERVED') || status.includes('NOT_REPORTED')) return 'missing';
    return 'invalid';
  }

  function publicCell(row, descriptor) {
    if (!row || Object.keys(row).some(key => !CELL_KEYS.includes(key))) throw new Error('Status cell contains a field outside the public status contract.');
    if (row.league !== descriptor.league || row.season_end_year !== descriptor.season_end_year || row.target !== descriptor.target) throw new Error('Status cell population identity mismatch.');
    if (!text(row.public_game_key) || !text(row.public_entity_id) || !['model', 'provider'].includes(row.entity_type) || !['validation', 'test', 'future_or_unresolved'].includes(row.population_role) || !text(row.status) || !Array.isArray(row.reason_codes) || row.reason_codes.some(reason => typeof reason !== 'string') || typeof row.target_population_eligible !== 'boolean') throw new Error('Status cell is incomplete or malformed.');
    for (const key of ['public_home_team', 'public_away_team', 'public_event_date']) if (row[key] !== null && typeof row[key] !== 'string') throw new Error('Public game label is not qualified.');
    return Object.fromEntries(CELL_KEYS.map(key => [key, row[key]]));
  }

  function pairedQualified(board) {
    const rows = array(board.metrics_by_model);
    return board.all_models_and_provider_use_identical_games === true && hashValid(board.common_cohort_hash) && integer(board.common_cohort_count) !== null && board.common_cohort_count > 0 && rows.length > 0 && rows.every(row => row.games === board.common_cohort_count) && board.provider_metrics && board.provider_metrics.games === board.common_cohort_count;
  }

  function validateStatusManifest(data, manifest) {
    if (!manifest || manifest.schema !== SCHEMA + '.status_parts' || manifest.population_hash !== data.population_hash || manifest.complete !== true) throw new Error('Status manifest identity or completeness is not qualified.');
    const expected = array(data.status_partition_manifest), actual = array(manifest.parts);
    if (expected.length !== actual.length || new Set(actual.map(p => p.filename)).size !== actual.length) throw new Error('Status manifest omits or duplicates a declared partition.');
    const pinned = new Map(expected.map(p => [p.filename, p]));
    const keys = ['filename', 'bytes', 'sha256', 'league', 'season_end_year', 'target', 'part', 'rows', 'logical_bytes', 'logical_sha256', 'codec', 'population_hash', 'scope', 'physical_readback_verified'];
    for (const part of actual) {
      const original = pinned.get(part.filename);
      if (!original || keys.some(key => original[key] !== part[key])) throw new Error('Status manifest partition metadata differs from the declared snapshot.');
    }
    const rows = actual.reduce((total, part) => total + (integer(part.rows) || 0), 0);
    if (rows !== manifest.rows || (integer(data.status_ledger_rows) !== null && rows !== data.status_ledger_rows)) throw new Error('Status manifest row total does not reconcile.');
    return manifest;
  }

  function validatePublicData(data) {
    if (!data || data.schema !== SCHEMA) throw new Error('The public population schema is missing or incompatible.');
    if (!Array.isArray(data.seasons)) throw new Error('Season populations are not available.');
    const seen = new Set();
    for (const season of data.seasons) {
      if (!YEARS.includes(season.season_end_year) || seen.has(season.season_end_year)) throw new Error('Season population identity is invalid.');
      seen.add(season.season_end_year);
      if (season.population_role !== (season.season_end_year === 2027 ? 'test' : 'validation')) throw new Error('Validation and test population roles do not match the declared policy.');
    }
    if (seen.size !== 3) throw new Error('All three declared season populations must remain visible.');
    return data;
  }

  function start(win) {
    const document = win.document;
    const populationBase = document.body && document.body.dataset && document.body.dataset.populationBase === "population_r17" ? "population_r17" : "population";
    const sharedStatusObjects = document.body && document.body.dataset && document.body.dataset.statusObjectBase === "status_objects";
    const $ = id => document.getElementById(id);
    const state = { data: null, models: [], coverage: [], coveragePage: 0, ownPage: 0, cellsPage: 0, manifest: null, partition: null, cells: [], partitionCache: new Map(), cachedBytes: 0, loadToken: 0 };
    const filters = () => ({ league: $('competition').value, season: $('season').value, target: $('target').value, evidence: $('evidence').value });
    const matches = (row, f) => (f.league === 'all' || row.league === f.league) && (f.season === 'all' || Number(row.season_end_year) === Number(f.season)) && (!row.target || row.target === f.target) && (f.evidence === 'all' || !row.evidence_class || row.evidence_class === f.evidence);
    const modelName = id => (state.models.find(m => m.model_id === id) || {}).label || id || 'Model not reported';
    const modelInfo = id => state.models.find(m => m.model_id === id) || {};
    const chosenPops = () => populations(state.data).filter(p => matches(p, filters()));
    const safeExport = (name, payload) => {
      const blob = new win.Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = win.URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = name; link.click(); win.setTimeout(() => win.URL.revokeObjectURL(url), 1000);
    };
    const scopedDownload = rows => ({ schema: 'sel.ncaa.public.filtered_evidence_export.v1', snapshot_asof: state.data.snapshot_asof || null, filters: filters(), complete_official_population_claimed: false, row_count: rows.length, rows });

    function renderPopulations() {
      const ps = chosenPops();
      const f = filters();
      const known = ps.map(p => integer(p.declared_population_count));
      const sum = known.every(n => n !== null) ? known.reduce((a, b) => a + b, 0) : null;
      const complete = ps.filter(officialQualified).length;
      const fullBoards = ps.flatMap(p => array(p.same_game_scoreboards).filter(b => matches({ ...b, league: p.league, season_end_year: p.season_end_year }, f) && b.metric_scope === 'FULL_DECLARED_POPULATION'));
      $('population-cards').innerHTML = `<div class="card"><b>${ps.length}</b><span>separate selected populations</span></div><div class="card"><b>${count(sum)}</b><span>declared evaluation records; unresolved identities may overlap games</span></div><div class="card"><b>${complete} / ${ps.length}</b><span>official denominators verified complete</span></div><div class="card"><b>${fullBoards.length}</b><span>full declared-population tables returned; ranking remains separately gated</span></div>`;
      $('population-rows').innerHTML = ps.map(p => {
        const official = p.official_completeness || {};
        const qualified = officialQualified(p);
        return `<tr><td><strong>${NAMES[p.league]} · ${esc(p.season_label)}</strong></td><td>${tag(human(p.population_role))}</td><td>${count(p.declared_population_count)}<small>${count(p.future_or_unresolved_count)} future/unresolved outside evaluation</small></td><td>${count(official.official_completed_count)}</td><td>${count(targetDenominator(p, f.target))}</td><td>${tag(qualified ? 'Verified complete' : 'Completeness unverified', !qualified)}<small>${esc(reasons(official.reasons))}</small>${p.test_already_exposed ? '<small>Test population already examined</small>' : ''}</td><td>${hashHTML(p.declared_population_hash)}</td></tr>`;
      }).join('') || empty(7, 'No selected population records were returned.');
      $('population-scope-note').textContent = 'Declared evaluation records and unique official completed-game denominators are separate until identities and completeness are verified. Unmatched official records may overlap canonical-source games. Unknown counts remain unverified; status-cell totals are never game counts.';
      const context = state.data.population_context;
      const relevant = array(context && context.current_season_reconciliation).filter(row => ps.some(p => p.league === row.league && p.season_end_year === 2027));
      $('reconciliation-note').hidden = !relevant.length;
      $('reconciliation-note').innerHTML = relevant.length ? `<strong>Current-season records are an unresolved union, not a verified unique official game total.</strong><div class="scroll"><table><thead><tr><th>Competition</th><th>Canonical-source completed</th><th>Unmatched official completed records</th><th>Declared unresolved union</th><th>Additional unique games established</th></tr></thead><tbody>${relevant.map(row => `<tr><td>${NAMES[row.league]}</td><td>${count(row.canonical_source_completed_records)}</td><td>${count(row.unmatched_official_completed_records)}</td><td>${count(row.declared_unresolved_union_completed_records)}</td><td>Not established</td></tr>`).join('')}</tbody></table></div><p>Unmatched official records remain visible for reconciliation and can refer to games already represented in the canonical source. They are not counted as proven additional unique games. The current test population has already been examined.</p>` : '';
      const exposed = ps.some(p => p.test_already_exposed);
      $('test-exposure-note').hidden = !exposed;
      $('test-exposure-note').innerHTML = exposed ? '<strong>The current test population has already been examined.</strong><p>Evidence remains separated by original issuance, time-valid replay and later fitting. These current-season results do not represent an untouched test set.</p>' : '';
    }

    function filteredCoverage() {
      const f = filters(), model = $('model-filter').value, quality = $('coverage-filter').value;
      return state.coverage.filter(row => {
        if (!matches(row, f) || (model !== 'all' && row.model_id !== model)) return false;
        const denominator = targetDenominator(row.population, row.target);
        const complete = denominator !== null && integer(row.eligible) === denominator && integer(row.missing) === 0 && integer(row.invalid) === 0;
        return quality === 'all' || quality === 'complete' && complete || quality === 'gaps' && !complete;
      });
    }

    function renderCoverage() {
      const rows = filteredCoverage(), size = 30;
      state.coveragePage = Math.min(state.coveragePage, Math.max(0, Math.ceil(rows.length / size) - 1));
      const shown = rows.slice(state.coveragePage * size, (state.coveragePage + 1) * size);
      $('model-coverage-rows').innerHTML = shown.map(row => {
        const denominator = targetDenominator(row.population, row.target), eligible = integer(row.eligible), model = modelInfo(row.model_id);
        const pct = denominator !== null && denominator > 0 && eligible !== null && eligible <= denominator ? 100 * eligible / denominator : null;
        const showCount = value => row.target_supported === false ? 'Not supported' : count(value);
        return `<tr><td><strong>${esc(modelName(row.model_id))}</strong><small>${esc(human(model.role))}</small></td><td>${NAMES[row.league]} · ${seasonName(row.season_end_year)}</td><td>${esc(human(row.target))}<small>${row.target_supported === false ? 'Target not supported by this model' : 'Coverage across all evidence classes'}</small></td><td>${showCount(row.observed)}</td><td>${showCount(row.descriptive)}</td><td>${showCount(row.eligible)}</td><td>${showCount(row.missing)}</td><td>${showCount(row.invalid)}</td><td>${count(denominator)} target-eligible games${pct !== null ? `<small>${pct.toFixed(1)}% qualified scored evidence</small><div class="coverage-bar" aria-hidden="true"><span style="--coverage:${pct}%"></span></div>` : ''}</td><td>${tag('Rank withheld', true)}<small>${esc(reasons(row.rank_suppression_reasons))}</small></td></tr>`;
      }).join('') || empty(10, 'No declared coverage rows match these filters.');
      $('coverage-count').textContent = `${rows.length.toLocaleString('en-US')} model × season × target rows · page ${state.coveragePage + 1} of ${Math.max(1, Math.ceil(rows.length / size))}`;
      $('coverage-prev').disabled = state.coveragePage === 0; $('coverage-next').disabled = (state.coveragePage + 1) * size >= rows.length; $('download-model-coverage').disabled = !rows.length;
      $('model-catalog-rows').innerHTML = state.models.filter(m => filters().league === 'all' || m.league === filters().league).map(m => `<tr><td>${esc(m.label)}</td><td>${esc(NAMES[m.league] || human(m.league))}</td><td>${esc(human(m.role))}<small>${array(m.targets).map(human).map(esc).join(' · ') || 'Target not reported'}</small></td><td>${esc(m.family || 'Not publicly specified')}</td><td>${array(m.feature_families).length ? array(m.feature_families).map(esc).join(' · ') : 'Public feature-family evidence not returned'}</td></tr>`).join('') || empty(5, 'No public model catalog was returned.');
    }

    function renderBoard(board, pop, secondary) {
      const q = boardQualification(board, pop), names = METRICS[board.target] || [], rows = metricRows(board).slice().sort((a, b) => modelName(a.model_id).localeCompare(modelName(b.model_id)));
      const permitted = !secondary && q.permitted;
      const title = `${NAMES[pop.league]} · ${pop.season_label} · ${human(board.target)} · ${human(board.evidence_class)}`;
      const heading = `<div class="scoreboard-heading"><h3>${esc(title)}</h3><p>${secondary ? 'Secondary shared intersection · unranked descriptive' : 'Full declared population'} · ${count(board.count)} scored games / ${count(board.full_population_count)} declared evaluation records</p><p>${permitted ? 'Full-population rank qualified by the evidence producer.' : 'Champion rank withheld.'} ${esc(reasons(board.rank_suppression_reasons || q.reasons))}</p><div class="cohort-pins"><span>Shared game cohort</span>${hashHTML(board.common_cohort_hash)}<span>Declared model roster</span>${hashHTML(board.declared_model_roster_hash)}</div></div>`;
      const body = rows.map(row => {
        const matchesCohort = hashValid(board.common_cohort_hash) && row.cohort_hash === board.common_cohort_hash && row.n === board.count;
        const metrics = row.metrics || {};
        return `<tr><td>${esc(modelName(row.model_id))}</td><td>${count(row.n)}</td>${names.map(name => `<td>${matchesCohort ? metricValue(metrics[name], name) : '<span class="muted">Cohort mismatch</span>'}</td>`).join('')}<td>${permitted && integer(row.rank) !== null && row.rank > 0 ? row.rank : 'Withheld'}</td><td>${matchesCohort ? 'Same declared cohort' : 'Row cohort or count is not qualified'}</td></tr>`;
      }).join('') || empty(names.length + 4, 'No qualified metrics were returned for this population.');
      return `<article class="scoreboard">${heading}<div class="scroll"><table><thead><tr><th>Model</th><th>Games</th>${names.map(n => `<th>${METRIC_NAMES[n]}</th>`).join('')}<th>Full-population rank</th><th>Cohort check</th></tr></thead><tbody>${body}</tbody></table></div></article>`;
    }

    function renderComparisons() {
      const entries = chosenPops().flatMap(pop => array(pop.same_game_scoreboards).filter(board => matches({ ...board, league: pop.league, season_end_year: pop.season_end_year }, filters())).map(board => ({ board, pop })));
      const full = entries.filter(({ board }) => (board.metric_scope || board.scope) === 'FULL_DECLARED_POPULATION');
      const secondary = entries.filter(({ board }) => (board.metric_scope || board.scope) !== 'FULL_DECLARED_POPULATION');
      const eligible = full.filter(({ board, pop }) => boardQualification(board, pop).permitted).length;
      $('rank-status').innerHTML = eligible ? `<strong>${eligible} full-population comparison table${eligible === 1 ? '' : 's'} qualified for ranking.</strong><p>Ranks shown below come only from explicitly qualified full-population scoreboards. Other populations and intersections remain unranked.</p>` : '<strong>No complete, comparable full-population champion is established by this selection.</strong><p>Model coverage, official denominators, evidence classes or shared cohorts remain incomplete or unqualified. Descriptive subset scores cannot fill the missing games.</p>';
      $('full-scoreboards').innerHTML = full.map(({ board, pop }) => renderBoard(board, pop, false)).join('') || '<div class="notice"><strong>Full-population scores are not available for this selection.</strong><p>The model coverage table above shows the evidence that exists and the missing or unqualified counts. No sampled scorecard is substituted for the full population.</p></div>';
      const nonempty = secondary.filter(({ board }) => board.count > 0), zero = secondary.filter(({ board }) => !(board.count > 0));
      $('intersection-scoreboards').innerHTML = nonempty.map(({ board, pop }) => renderBoard(board, pop, true)).join('') + (zero.length ? `<div class="notice"><strong>${zero.length} declared shared cohorts have no scored games.</strong><p>The full model roster has no common evidence for these population/target/evidence combinations. Individual model observations are shown separately below.</p></div><details><summary>Inspect empty common-cohort identities</summary><div class="scroll"><table><thead><tr><th>Population</th><th>Evidence class</th><th>Common / declared games</th><th>Common cohort hash</th><th>Roster hash</th></tr></thead><tbody>${zero.map(({board, pop}) => `<tr><td>${NAMES[pop.league]} · ${esc(pop.season_label)}</td><td>${esc(human(board.evidence_class))}</td><td>${count(board.count)} / ${count(board.full_population_count)}</td><td>${hashHTML(board.common_cohort_hash)}</td><td>${hashHTML(board.declared_model_roster_hash)}</td></tr>`).join('')}</tbody></table></div></details>` : '') || '<p class="muted">No shared-intersection scoreboards were returned for this selection.</p>';
    }

    function renderOwnSubsets() {
      const f = filters(), selected = $('model-filter').value, names = METRICS[f.target] || [];
      const rows = state.coverage.filter(row => matches(row, { ...f, evidence: 'all' }) && (selected === 'all' || row.model_id === selected)).flatMap(row => array(row.metrics_by_evidence_class).filter(metric => (f.evidence === 'all' || metric.evidence_class === f.evidence) && ($('own-subset-include-empty').checked || metric.games > 0)).map(metric => ({ ...metric, model_id: row.model_id, league: row.league, season_end_year: row.season_end_year })));
      const size = 30;
      state.ownPage = Math.min(state.ownPage, Math.max(0, Math.ceil(rows.length / size) - 1));
      $('own-subset-head').innerHTML = `<tr><th>Model</th><th>Population</th><th>Evidence class</th><th>Games in own subset</th>${names.map(n => `<th>${METRIC_NAMES[n]}</th>`).join('')}<th>Own subset cohort hash</th><th>Comparison scope</th></tr>`;
      $('own-subset-rows').innerHTML = rows.slice(state.ownPage * size, (state.ownPage + 1) * size).map(row => `<tr><td>${esc(modelName(row.model_id))}</td><td>${NAMES[row.league]} · ${seasonName(row.season_end_year)}</td><td>${esc(human(row.evidence_class))}</td><td>${count(row.games)}</td>${names.map(name => `<td>${row.games > 0 ? metricValue((row.metrics || {})[name], name) : '<span class="muted">Unavailable</span>'}</td>`).join('')}<td>${hashHTML(row.cohort_hash)}</td><td>Own subset · unranked<small>Game sets may differ across models</small></td></tr>`).join('') || empty(names.length + 6, 'No individual-model metric rows match these filters.');
      $('own-subset-count').textContent = `${rows.length.toLocaleString('en-US')} individual evidence rows · page ${state.ownPage + 1} of ${Math.max(1, Math.ceil(rows.length / size))}`;
      $('own-subset-prev').disabled = state.ownPage === 0; $('own-subset-next').disabled = (state.ownPage + 1) * size >= rows.length;
    }

    function providerRows() {
      return chosenPops().flatMap(pop => PROVIDERS.map(provider => {
        const found = array(pop.provider_coverage).find(row => row.provider === provider && row.target === filters().target);
        return { ...(found || { provider, target: filters().target, observed: null, qualified: null, missing: null, invalid: null, qualification_status: 'NOT_REPORTED', qualification_blockers: ['PROVIDER_COVERAGE_NOT_REPORTED'] }), population: pop };
      }));
    }

    function renderMarkets() {
      const rows = providerRows();
      $('provider-summary').innerHTML = PROVIDERS.map(provider => {
        const selected = rows.filter(row => row.provider === provider), values = selected.map(row => integer(row.qualified));
        const total = values.every(v => v !== null) ? values.reduce((a, b) => a + b, 0) : null;
        return `<article><h3>${NAMES[provider]}</h3><strong>${count(total)} qualified games across selected populations</strong><p>Counts retain their competition, season and target denominators. Provider records alone do not establish a paired model comparison.</p></article>`;
      }).join('');
      $('provider-coverage-rows').innerHTML = rows.map(row => `<tr><td><strong>${NAMES[row.provider]}</strong></td><td>${NAMES[row.population.league]} · ${row.population.season_label}</td><td>${human(row.target)}</td><td>${count(row.declared_population_count)} / ${count(row.target_eligible_count)}</td><td>${count(row.observed)}</td><td>${count(row.qualified)}</td><td>${count(row.missing)}</td><td>${tag(human(row.qualification_status), !(row.qualified > 0))}<small>${esc(reasonCounts(row.reason_counts_overlapping))}</small></td><td>See matched cohorts below<small>Provider coverage is not a model-paired cohort</small></td></tr>`).join('') || empty(9, 'No provider coverage populations are selected.');
      const f = filters();
      const comparisons = chosenPops().flatMap(pop => array(pop.provider_comparisons).filter(row => row.target === f.target && (f.evidence === 'all' || row.model_evidence_class === f.evidence)).map(row => ({ row, pop })));
      const valid = comparisons.filter(({ row }) => pairedQualified(row)), withheld = comparisons.filter(({ row }) => !pairedQualified(row));
      const rendered = valid.map(({ row, pop }) => {
        const names = METRICS[row.target] || [];
        const entities = [...array(row.metrics_by_model).map(m => ({ label: modelName(m.model_id), ...m })), { label: NAMES[row.provider_product] || human(row.provider_product), ...row.provider_metrics }];
        return `<article class="scoreboard"><div class="scoreboard-heading"><h3>${esc(NAMES[row.provider_product] || human(row.provider_product))} and the declared model roster</h3><p>${NAMES[pop.league]} · ${pop.season_label} · ${human(row.target)} · ${count(row.common_cohort_count)} paired games / ${count(row.full_population_count)} declared</p><p>Model: ${esc(human(row.model_evidence_class))} · Provider: ${esc(human(row.provider_evidence_class))} · Secondary descriptive comparison; no rank</p>${hashHTML(row.common_cohort_hash)}</div><div class="scroll"><table><thead><tr><th>Entity</th><th>Same games</th>${names.map(n => `<th>${METRIC_NAMES[n]}</th>`).join('')}</tr></thead><tbody>${entities.map(entity => `<tr><td>${esc(entity.label)}</td><td>${count(entity.games)}</td>${names.map(n => `<td>${metricValue((entity.metrics || {})[n], n)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></article>`;
      }).join('');
      $('provider-scoreboards').innerHTML = rendered + (withheld.length ? `<div class="notice"><strong>${withheld.length} requested provider/model evidence cohorts have no displayable paired scores.</strong><p>Missing or unmatched games remain in the coverage table and status ledger. An empty common cohort produces no loss or accuracy score.</p></div><details><summary>Inspect unavailable paired-cohort counts</summary><div class="scroll"><table><thead><tr><th>Population</th><th>Provider product</th><th>Model / provider evidence</th><th>Common / declared games</th><th>Missing or unmatched</th><th>Cohort hash</th></tr></thead><tbody>${withheld.map(({row,pop}) => `<tr><td>${NAMES[pop.league]} · ${pop.season_label}</td><td>${esc(NAMES[row.provider_product] || row.provider_product)}</td><td>${esc(human(row.model_evidence_class))} / ${esc(human(row.provider_evidence_class))}</td><td>${count(row.common_cohort_count)} / ${count(row.full_population_count)}</td><td>${count(row.missing_or_unmatched_population_count)}</td><td>${hashHTML(row.common_cohort_hash)}</td></tr>`).join('')}</tbody></table></div></details>` : '') || '<div class="notice"><strong>No paired model/provider scorecards were returned for this selection.</strong><p>Missing provider cells remain in the coverage table and game-level status view.</p></div>';
    }

    function renderExecution() {
      const e = state.data.execution || {};
      $('execution-summary').innerHTML = `<strong>${esc(e.public_title || 'Verified execution summary not returned')}</strong><p>${esc(e.public_summary || 'No new execution result is inferred from this dashboard data.')}</p>`;
      const fields = array(e.public_counters);
      $('execution-cards').innerHTML = fields.map(row => `<div class="card"><b>${typeof row.value === 'number' ? count(row.value) : esc(row.value || 'Not verified')}</b><span>${esc(row.label)}</span></div>`).join('');
      $('execution-scope').textContent = [e.completed_at ? `Completed ${pacific(e.completed_at)}.` : '', e.count_scope || '', e.public_limitations || ''].filter(Boolean).join(' ');
    }

    function renderAll() {
      if (!state.data) return;
      renderPopulations(); renderCoverage(); renderComparisons(); renderOwnSubsets(); renderMarkets(); renderExecution();
      win.SEL_POPULATION_READY = { schema: state.data.schema, populations: populations(state.data).length, modelCoverageRows: state.coverage.length, publicGameValuesWithheld: true };
    }

    async function fetchJSON(path) {
      const response = await win.fetch(path);
      if (!response.ok) throw new Error(`Evidence asset unavailable (${response.status}).`);
      if (path.endsWith('.gz')) {
        if (!win.DecompressionStream) throw new Error('Compressed status partitions require browser decompression support; use the manifest download.');
        const bytes = await response.blob();
        return JSON.parse(await new win.Response(bytes.stream().pipeThrough(new win.DecompressionStream('gzip'))).text());
      }
      return response.json();
    }

    function publicGameLabel(game) {
      if (game.public_away_team && game.public_home_team) return `${game.public_away_team} at ${game.public_home_team}`;
      return `Game ${text(game.public_game_key).slice(0, 16)}`;
    }

    function projectedCells() {
      if (!state.partition) return [];
      const query = $('cell-search').value.trim().toLowerCase(), status = $('cell-state').value, gameStatus = $('cell-game-status').value, evidence = $('cell-evidence').value;
      return state.partition.cells.filter(cell => (status === 'all' || cellState(cell) === status) && (gameStatus === 'all' || (gameStatus === 'evaluation' ? cell.population_role !== 'future_or_unresolved' : cell.population_role === gameStatus)) && (evidence === 'all' || cell.evidence_class === evidence) && (!query || `${publicGameLabel(cell)} ${cell.public_game_key} ${cell.status} ${array(cell.reason_codes).join(' ')}`.toLowerCase().includes(query)));
    }

    function renderCells() {
      const rows = projectedCells(), size = 25;
      state.cells = rows;
      state.cellsPage = Math.min(state.cellsPage, Math.max(0, Math.ceil(rows.length / size) - 1));
      const shown = rows.slice(state.cellsPage * size, (state.cellsPage + 1) * size);
      $('cell-rows').innerHTML = shown.map(cell => `<tr><td><strong>${esc(publicGameLabel(cell))}</strong><small>${esc(cell.public_game_key)}</small></td><td>${esc(pacific(cell.public_event_date, true))}</td><td>${esc(human(cell.population_role))}<small>${cell.target_population_eligible ? 'Outcome eligible for target' : 'Target eligibility not established'}</small></td><td>${esc(cell.entity_type === 'provider' ? NAMES[cell.public_entity_id] || cell.public_entity_id : modelName(cell.public_entity_id))}<small>${esc(human(cell.target))}</small></td><td>${esc(human(cell.evidence_class))}</td><td>${tag(human(cell.status), cellState(cell) !== 'eligible')}</td><td>${esc(reasons(cell.reason_codes))}</td></tr>`).join('') || empty(7, state.partition ? 'No status cells match these filters.' : 'No qualified status partition has loaded.');
      $('cell-count').textContent = `${rows.length.toLocaleString('en-US')} matching game cells · page ${state.cellsPage + 1} of ${Math.max(1, Math.ceil(rows.length / size))}`;
      $('cell-prev').disabled = state.cellsPage === 0; $('cell-next').disabled = (state.cellsPage + 1) * size >= rows.length; $('download-cells').disabled = !rows.length;
    }

    async function loadPartition() {
      if (!state.manifest) return;
      const token = ++state.loadToken, year = Number($('cell-season').value), league = $('cell-competition').value, target = $('cell-target').value;
      const [kind, ...entityParts] = $('cell-entity').value.split(':'), entityId = entityParts.join(':');
      const descriptors = array(state.manifest.parts).filter(p => p.season_end_year === year && p.league === league && p.target === target).sort((a,b) => a.part - b.part);
      state.partition = null; state.cellsPage = 0; renderCells();
      win.SEL_POPULATION_CELLS_READY = null; win.SEL_POPULATION_CELLS_ERROR = null;
      if (!descriptors.length) { $('cell-load-status').textContent = 'No public status partition was returned for this competition, season and target. Full coverage is not established.'; return; }
      $('cell-load-status').textContent = `Loading ${descriptors.length} bounded public status partition${descriptors.length === 1 ? '' : 's'}…`;
      try {
        if (!win.crypto || !win.crypto.subtle || !win.DecompressionStream) throw new Error('Integrity-checked compressed cells require a secure browser with gzip support. The manifest remains available to download.');
        if (state.manifest.population_hash !== state.data.population_hash || state.manifest.complete !== true) throw new Error('Status manifest does not match the complete declared status projection.');
        const digest = async bytes => Array.from(new Uint8Array(await win.crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
        const cells = [], seen = new Set();
        let readRows = 0;
        for (const descriptor of descriptors) {
          if (token !== state.loadToken) return;
          const path = relativeAsset(sharedStatusObjects ? `status_objects/${descriptor.sha256}.jsonl.gz` : `${populationBase}/status/${descriptor.filename}`), cacheKey = `${path}:${descriptor.sha256}`;
          const pinned = array(state.data.status_partition_manifest).find(p => p.filename === descriptor.filename);
          if (!pinned || pinned.sha256 !== descriptor.sha256 || pinned.logical_sha256 !== descriptor.logical_sha256 || pinned.rows !== descriptor.rows || descriptor.population_hash !== state.data.population_hash || descriptor.codec !== 'jsonl_gzip' || descriptor.scope !== 'EXPLICIT_CELLS_NO_SPARSE_DEFAULTS' || descriptor.physical_readback_verified !== true || !hashValid(descriptor.sha256) || !hashValid(descriptor.logical_sha256) || !(descriptor.rows > 0 && descriptor.rows <= 4096) || !(descriptor.bytes > 0 && descriptor.bytes <= 8388608) || !(descriptor.logical_bytes > 0 && descriptor.logical_bytes <= 8388608)) throw new Error('Public status partition pin or bound is invalid.');
          let bytes = state.partitionCache.get(cacheKey);
          if (!bytes) {
            const response = await win.fetch(path);
            if (!response.ok) throw new Error(`Status partition unavailable (${response.status}).`);
            bytes = await response.arrayBuffer();
            if (bytes.byteLength !== descriptor.bytes || await digest(bytes) !== descriptor.sha256) throw new Error('Compressed status partition integrity check failed.');
            while (state.cachedBytes + bytes.byteLength > 33554432 && state.partitionCache.size) {
              const oldKey = state.partitionCache.keys().next().value;
              state.cachedBytes -= state.partitionCache.get(oldKey).byteLength; state.partitionCache.delete(oldKey);
            }
            state.partitionCache.set(cacheKey, bytes); state.cachedBytes += bytes.byteLength;
          }
          const logical = await new win.Response(new win.Blob([bytes]).stream().pipeThrough(new win.DecompressionStream('gzip'))).arrayBuffer();
          if (logical.byteLength !== descriptor.logical_bytes || await digest(logical) !== descriptor.logical_sha256) throw new Error('Logical status partition integrity check failed.');
          const body = new win.TextDecoder('utf-8', { fatal: true }).decode(logical), lines = body.split('\n');
          if (lines.pop() !== '' || lines.length !== descriptor.rows) throw new Error('Status partition row count or framing mismatch.');
          for (const line of lines) {
            const cell = publicCell(JSON.parse(line), descriptor);
            if (cell.entity_type !== kind || cell.public_entity_id !== entityId) continue;
            if (seen.has(cell.public_game_key)) throw new Error('Duplicate explicit game/entity/target status cell.');
            seen.add(cell.public_game_key); cells.push(cell);
          }
          readRows += lines.length;
          $('cell-load-status').textContent = `${readRows.toLocaleString('en-US')} status rows verified; selecting the requested entity…`;
          await new Promise(resolve => win.setTimeout(resolve, 0));
        }
        if (token !== state.loadToken) return;
        const pop = populations(state.data).find(p => p.league === league && p.season_end_year === year);
        if (integer(pop.declared_population_count) !== null && integer(pop.future_or_unresolved_count) !== null && seen.size !== pop.declared_population_count + pop.future_or_unresolved_count) throw new Error('Explicit selected-entity cells do not reconcile to the declared game inventory.');
        cells.sort((a,b) => text(a.public_event_date).localeCompare(text(b.public_event_date)) || a.public_game_key.localeCompare(b.public_game_key));
        state.partition = { season_end_year: year, league, cells };
        const classes = [...new Set(cells.map(c => c.evidence_class).filter(Boolean))].sort();
        $('cell-evidence').innerHTML = '<option value="all">All evidence classes</option>' + classes.map(c => `<option value="${esc(c)}">${esc(human(c))}</option>`).join('');
        $('cell-evidence').value = 'all';
        $('cell-load-status').textContent = `${seen.size.toLocaleString('en-US')} explicit status cells loaded for this entity and target; ${readRows.toLocaleString('en-US')} partition rows verified. Each cell describes a declared record, not an independently deduplicated official game.`;
        $('partition-scope').textContent = 'Every selected cell is explicit in the verified status projection. Compressed and logical hashes, sizes and row counts were checked. The declared inventory is not an assertion of complete official season coverage.';
        renderCells(); win.SEL_POPULATION_CELLS_READY = { season: year, league, target, entity: entityId, records: seen.size, verifiedRows: readRows };
      } catch (error) {
        if (token !== state.loadToken) return;
        $('cell-load-status').textContent = `Status partition unavailable: ${error.message}`;
        win.SEL_POPULATION_CELLS_ERROR = error.message; renderCells();
      }
    }

    function initializeChoices() {
      const evidence = [...new Set(state.coverage.flatMap(row => array(row.metrics_by_evidence_class).map(m => m.evidence_class)).filter(Boolean))].sort();
      $('evidence').innerHTML = '<option value="all">All evidence classes</option>' + evidence.map(value => `<option value="${esc(value)}">${esc(human(value))}</option>`).join('');
      $('model-filter').innerHTML = '<option value="all">All declared models</option>' + state.models.map(m => `<option value="${esc(m.model_id)}">${esc(m.label)} · ${esc(NAMES[m.league] || m.league)}</option>`).join('');
      initializeCellEntities();
    }

    function initializeCellEntities() {
      const previous = $('cell-entity').value, league = $('cell-competition').value;
      const models = state.models.filter(m => m.league === league);
      $('cell-entity').innerHTML = models.map(m => `<option value="model:${esc(m.model_id)}">${esc(m.label)}</option>`).join('') + PROVIDERS.map(p => `<option value="provider:${p}">${NAMES[p]}</option>`).join('');
      const choices = [...models.map(m => `model:${m.model_id}`), ...PROVIDERS.map(p => `provider:${p}`)];
      const supported = models.find(m => array(m.targets).includes($('cell-target').value));
      $('cell-entity').value = choices.includes(previous) ? previous : supported ? `model:${supported.model_id}` : choices[0];
    }

    for (const id of ['competition', 'season', 'target', 'evidence', 'model-filter', 'coverage-filter']) $(id).addEventListener('change', () => { state.coveragePage = 0; state.ownPage = 0; renderAll(); });
    $('coverage-prev').addEventListener('click', () => { state.coveragePage--; renderCoverage(); }); $('coverage-next').addEventListener('click', () => { state.coveragePage++; renderCoverage(); });
    $('own-subset-prev').addEventListener('click', () => { state.ownPage--; renderOwnSubsets(); }); $('own-subset-next').addEventListener('click', () => { state.ownPage++; renderOwnSubsets(); });
    $('own-subset-include-empty').addEventListener('change', () => { state.ownPage = 0; renderOwnSubsets(); });
    $('download-model-coverage').addEventListener('click', () => safeExport('ncaa_filtered_model_coverage.json', scopedDownload(filteredCoverage().map(({ population, ...row }) => row))));
    $('cell-competition').addEventListener('change', () => { initializeCellEntities(); loadPartition(); });
    for (const id of ['cell-season', 'cell-entity', 'cell-target']) $(id).addEventListener('change', loadPartition);
    for (const id of ['cell-game-status', 'cell-state', 'cell-evidence']) $(id).addEventListener('change', () => { state.cellsPage = 0; renderCells(); });
    $('cell-search').addEventListener('input', () => { state.cellsPage = 0; renderCells(); });
    $('cell-prev').addEventListener('click', () => { state.cellsPage--; renderCells(); }); $('cell-next').addEventListener('click', () => { state.cellsPage++; renderCells(); });
    $('download-cells').addEventListener('click', () => safeExport('ncaa_filtered_game_status_cells.json', { schema: 'sel.ncaa.public.filtered_status_cells.v1', population_snapshot_asof: state.data.snapshot_asof || null, season_end_year: Number($('cell-season').value), league: $('cell-competition').value, entity: $('cell-entity').value, target: $('cell-target').value, evidence_class_filter: $('cell-evidence').value, numerical_forecasts_and_quotes_excluded: true, complete_official_population_claimed: false, row_count: state.cells.length, rows: state.cells.map(cell => Object.fromEntries(CELL_KEYS.map(key => [key, cell[key]]))) }));
    (async () => {
      try {
        state.data = normalizeB088(await fetchJSON(`${populationBase}/population_public.json`)); state.models = roster(state.data); state.coverage = coverageRows(state.data);
        initializeChoices(); renderAll();
        $('publication-clock').textContent = `Population snapshot: ${pacific(state.data.snapshot_asof)}. Analysis/publication time does not replace a source-availability clock.`;
        $('load-status').innerHTML = '<strong>Three-season evidence loaded.</strong><p>Use the separate population, coverage and same-game tables below. Unknown counts and missing scores remain explicit.</p>';
        try {
          const context = await fetchJSON(`${populationBase}/population_context.json`);
          if (context.population_hash !== state.data.population_hash) throw new Error('Population context identity mismatch.');
          state.data.population_context = context; renderPopulations();
        } catch (error) { win.SEL_POPULATION_CONTEXT_ERROR = error.message; }
        try { state.data.execution = await fetchJSON(`${populationBase}/execution_public.json`); renderExecution(); } catch (error) { win.SEL_POPULATION_EXECUTION_ERROR = error.message; }
        if ($('collection-summary')) { try { const collection = await fetchJSON(`${populationBase}/collection_public.json`); $('collection-summary').hidden = false; $('collection-summary').innerHTML = `<strong>Latest recorded collection</strong><p>${esc(collection.public_summary)}</p><small>Captured ${pacific(collection.snapshot_completed_at)}. Quote-row counts are not game counts.</small>`; } catch (error) { win.SEL_POPULATION_COLLECTION_ERROR = error.message; } }
        try { state.manifest = validateStatusManifest(state.data, await fetchJSON(`${populationBase}/status_manifest.json`)); await loadPartition(); } catch (error) { $('cell-load-status').textContent = `Public status manifest unavailable: ${error.message}`; win.SEL_POPULATION_CELLS_ERROR = error.message; }
      } catch (error) {
        $('load-status').innerHTML = `<strong>Evidence could not be verified for display.</strong><p>${esc(error.message)}</p>`; $('load-status').classList.add('error'); win.SEL_POPULATION_ERROR = error.message;
      }
    })();
  }
  return { start, validatePublicData, normalizeB088, populations, roster, coverageRows, officialQualified, targetDenominator, boardQualification, metricRows, metricValue, relativeAsset, cellState, publicCell, pairedQualified, validateStatusManifest, pacific };
});
