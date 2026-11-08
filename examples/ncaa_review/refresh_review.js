/* Generic inspection of a supplied refresh plan. No scheduling, fitting or network access. */
(() => {
  'use strict';
  const STATES = Object.freeze([
    'DUE_MODEL_REFRESH', 'DUE_FEATURE_REFRESH', 'DUE_ISSUE_REFRESH',
    'EARLY_OUTLOOK', 'CURRENT_VERIFIED', 'MISSED_WINDOW', 'SOURCE_BLOCKED',
    'NO_REGISTERED_RECIPE', 'TERMINAL_EVENT',
  ]);
  const TARGETS = Object.freeze(['win', 'margin', 'total']);
  const LABELS = Object.freeze({
    DUE_MODEL_REFRESH: 'Model refresh due',
    DUE_FEATURE_REFRESH: 'Feature refresh due',
    DUE_ISSUE_REFRESH: 'Issue refresh due',
    EARLY_OUTLOOK: 'Early outlook',
    CURRENT_VERIFIED: 'Current · owner classified',
    MISSED_WINDOW: 'Decision window missed',
    SOURCE_BLOCKED: 'Source evidence blocked',
    NO_REGISTERED_RECIPE: 'No registered recipe',
    TERMINAL_EVENT: 'Terminal event',
  });
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const count = v => Number.isSafeInteger(v) && v >= 0;
  const nonempty = v => typeof v === 'string' && v.length > 0;
  const clock = v => typeof v === 'string' &&
    /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(v) &&
    Number.isFinite(Date.parse(v));
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (object(value)) return '{' + Object.keys(value).sort().map(
      key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    return JSON.stringify(value);
  }
  function stateCounts(value) {
    if (!object(value) || Object.keys(value).some(k => !STATES.includes(k)) ||
        Object.values(value).some(v => !count(v))) throw Error('Invalid refresh state counts.');
    const total=STATES.reduce((n, state) => n+(value[state]||0),0);
    if(!Number.isSafeInteger(total))throw Error('Refresh totals exceed safe integer bounds.');
    return total;
  }
  function validate(value, streams, validateStream) {
    if (!object(value) || value.schema !== 'sel.ncaa.b055.refresh_coverage.v1' ||
        !clock(value.asof) || !nonempty(value.policy_id)) {
      throw Error('Invalid refresh coverage identity or declared clock.');
    }
    for (const key of ['schedule_rows', 'unique_event_keys', 'target_contexts',
      'missed_contexts', 'blocked_contexts', 'new_fit_groups', 'reused_fit_groups',
      'feature_only_refreshes', 'verified_issue_count']) {
      if (!count(value[key])) throw Error('Invalid refresh count: ' + key);
    }
    if(value.full_physical_season_coverage!==false||value.background_scheduler_created!==false||
        value.original_issue_mutation!==false||value.new_promotions!==0||
        value.plan_counts_describe_registered_asof_not_wall_clock_at_report!==true){
      throw Error('Refresh plan qualifications are missing or changed.');
    }
    if(value.unclassified_verified_fit_groups!==undefined&&!count(value.unclassified_verified_fit_groups))throw Error('Invalid unclassified execution-group count.');
    if(value.execution_context_dispositions!==undefined&&(!object(value.execution_context_dispositions)||
        Object.values(value.execution_context_dispositions).some(n=>!count(n))||
        Object.values(value.execution_context_dispositions).reduce((a,b)=>a+b,0)!==value.target_contexts)){
      throw Error('Refresh execution dispositions do not conserve target contexts.');
    }
    if (value.next_refresh_at !== null && !clock(value.next_refresh_at)) {
      throw Error('Invalid next refresh clock; missing is null.');
    }
    if (stateCounts(value.counts_by_state) !== value.target_contexts ||
        !object(value.counts_by_target) ||
        Object.keys(value.counts_by_target).sort().join(',') !== [...TARGETS].sort().join(',')) {
      throw Error('Refresh state totals do not conserve target contexts.');
    }
    const byTarget = TARGETS.reduce((total, target) =>
      total + stateCounts(value.counts_by_target[target]), 0);
    if (byTarget !== value.target_contexts) throw Error('Refresh target totals differ.');
    for (const state of STATES) {
      if (TARGETS.reduce((n, target) => n + (value.counts_by_target[target][state] || 0), 0) !==
          (value.counts_by_state[state] || 0)) throw Error('Refresh state and target cells differ.');
    }
    if (value.missed_contexts !== (value.counts_by_state.MISSED_WINDOW || 0) ||
        value.blocked_contexts !== (value.counts_by_state.SOURCE_BLOCKED || 0) +
          (value.counts_by_state.NO_REGISTERED_RECIPE || 0)) {
      throw Error('Refresh missed or blocked subtotal differs.');
    }
    if (!object(value.streams) || !object(streams)) throw Error('Refresh streams are missing.');
    for (const name of ['plan', 'audit']) {
      const stream = value.streams[name], top = streams['refresh_' + name];
      if (!object(stream) || !object(top) || canonical(stream) !== canonical(top)) {
        throw Error('Refresh ' + name + ' descriptor differs from the top-level stream.');
      }
      validateStream(stream);
    }
    if (value.streams.plan.rows !== value.target_contexts) {
      throw Error('Refresh plan rows differ from target contexts.');
    }
    return value;
  }
  function validatePlanRows(rows, expectedAsOf) {
    const seen = new Set();
    for (const row of rows) {
      if (!object(row) || !nonempty(row.event_key) || !nonempty(row.event_id) ||
          !['ncaam', 'ncaaw'].includes(row.league) || !TARGETS.includes(row.target) ||
          !STATES.includes(row.state) || !nonempty(row.reason) || !nonempty(row.next_action)) {
        throw Error('Invalid supplied refresh plan row identity, state or recovery action.');
      }
      if(row.new_forecast_credit!==0||row.previous_state_is_not_current_server_issue_proof!==true||
          row.missed_window_is_evidence_gap_not_proof_no_legacy_issue!==(row.state==='MISSED_WINDOW')){
        throw Error('Refresh plan row has unsupported forecast or issue credit.');
      }
      if(!clock(row.asof)||(expectedAsOf!==undefined&&row.asof!==expectedAsOf))throw Error('Refresh row and manifest clocks differ.');
      const key = canonical([row.event_key, row.target]);
      if (seen.has(key)) throw Error('Duplicate source-event/target in this refresh part.');
      seen.add(key);
      for (const field of ['event_time', 'window_open_at', 'cutoff_time']) {
        if (row[field] !== null && row[field] !== undefined && !clock(row[field])) {
          throw Error('Invalid supplied refresh row clock: ' + field);
        }
      }
    }
    return rows;
  }
  function filterRows(rows, filters) {
    const query = String(filters.search || '').trim().toLowerCase();
    return rows.filter(row =>
      (filters.state === 'all' || row.state === filters.state) &&
      (filters.league === 'all' || row.league === filters.league) &&
      (filters.target === 'all' || row.target === filters.target) &&
      (!query || ['event_key', 'event_id', 'league', 'target', 'state', 'reason', 'next_action']
        .some(key => String(row[key] ?? '').toLowerCase().includes(query))));
  }
  const api = {STATES, TARGETS, LABELS, validate, validatePlanRows, filterRows, canonical};
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
  window.NCAARefreshReview = api;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const node = (tag, text) => {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = String(text);
    return n;
  };
  let coverage = null, loadedRows = [], loadedPin = null, filePin = null;
  let changed = () => {}, inspect = () => {};
  function filters() {
    return {state: $('refresh-state').value, league: $('refresh-league').value,
      target: $('refresh-target').value, search: $('refresh-search').value};
  }
  api.filtered = rows => filterRows(rows, filters());
  api.active = () => coverage !== null;
  api.asof = () => coverage?.asof;
  api.setPart = (rows, pin, name) => {
    loadedRows = name === 'refresh_plan' ? rows : [];
    loadedPin = name === 'refresh_plan' ? pin : null;
    $('refresh-export').disabled = loadedPin === null;
  };
  api.render = (value, pin) => {
    coverage = value || null; filePin = pin || null;
    $('refresh-content').hidden = !coverage;
    $('refresh-status').textContent = coverage
      ? 'A dated refresh plan is loaded. Its classifications are supplied owner evidence, not browser decisions or new forecasts.'
      : 'No refresh-coverage manifest supplied. This does not mean that zero games need an update.';
    for (const id of ['refresh-state', 'refresh-league', 'refresh-target']) $(id).value = 'all';
    $('refresh-search').value = '';
    api.setPart([], null, null);
    if (!coverage) return;
    $('refresh-asof').textContent = 'Plan as of ' + coverage.asof +
      ' · Next recorded refresh: ' + (coverage.next_refresh_at ?? 'Not supplied') +
      '. This view never uses the browser clock to change a state.';
    const cards = [
      ['Supplied schedule rows', coverage.schedule_rows],
      ['Exact source event keys', coverage.unique_event_keys],
      ['Event × target contexts', coverage.target_contexts],
      ['Missed contexts', coverage.missed_contexts],
      ['Blocked contexts', coverage.blocked_contexts],
      ['Authored verified-issue count', coverage.verified_issue_count],
    ];
    $('refresh-cards').replaceChildren(...cards.map(([label, value]) => {
      const card = node('div'); card.className = 'clock-card';
      card.append(node('strong', label), node('span', value)); return card;
    }));
    $('refresh-counts').replaceChildren(...STATES.map(state => {
      const tr = node('tr');
      for (const cell of [LABELS[state], coverage.counts_by_state[state] || 0,
        ...TARGETS.map(target => coverage.counts_by_target[target][state] || 0)]) {
        tr.append(node('td', cell));
      }
      return tr;
    }));
    $('refresh-execution-counts').replaceChildren(...Object.entries(coverage.execution_context_dispositions||{}).map(([state,n])=>{
      const tr=node('tr');tr.append(node('td',state),node('td',n));return tr;
    }));
    $('refresh-execution-note').textContent=coverage.execution_context_dispositions===undefined?'No execution-disposition inventory was supplied. Missing is not zero.':'These are separately recorded execution outcomes; they do not rewrite the original plan states.';
    $('refresh-work').textContent = 'Recorded execution groups: ' +
      coverage.new_fit_groups + ' new-fit groups; ' + coverage.reused_fit_groups +
      ' reused groups; ' + coverage.feature_only_refreshes +
      ' feature-only refreshes; ' + (coverage.unclassified_verified_fit_groups??'unavailable') +
      ' verified groups with unclassified new/reuse status. Group counts are separate from the typed physical-fit ledger. No background scheduler is created by this report.';
    $('refresh-stream-counts').textContent = 'Plan: ' + coverage.streams.plan.rows +
      ' event/target rows in ' + coverage.streams.plan.parts.length + ' parts. Execution audit: ' +
      coverage.streams.audit.rows + ' separate operation records in ' +
      coverage.streams.audit.parts.length + ' parts. No part is loaded automatically.';
  };
  api.setup = callbacks => {
    changed = callbacks.changed; inspect = callbacks.inspect;
    $('refresh-state').replaceChildren(new Option('Every recorded state', 'all'),
      ...STATES.map(state => new Option(LABELS[state], state)));
    for (const id of ['refresh-state', 'refresh-league', 'refresh-target']) {
      $(id).addEventListener('change', changed);
    }
    $('refresh-search').addEventListener('input', changed);
    $('refresh-reset').addEventListener('click', () => {
      for (const id of ['refresh-state', 'refresh-league', 'refresh-target']) $(id).value = 'all';
      $('refresh-search').value = ''; changed();
    });
    $('refresh-inspect').addEventListener('click', () => inspect('refresh_plan'));
    $('refresh-export').addEventListener('click', () => {
      if (!coverage || !loadedPin) return;
      const value = {
        schema: 'sel.ncaa.review.loaded_refresh_part_export.v1',
        scope: 'FILTERED_ROWS_FROM_ONE_VERIFIED_PART_NOT_FULL_STREAM_OR_PHYSICAL_SEASON',
        plan_asof: coverage.asof, review_file_pin: filePin, part: loadedPin,
        filters: filters(), loaded_part_rows: loadedRows.length,
        rows: filterRows(loadedRows, filters()),
      };
      const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + '\n'],
        {type: 'application/json'}));
      const link = node('a'); link.href = url; link.download = 'ncaa_loaded_refresh_rows.json';
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 0);
    });
  };
})();
