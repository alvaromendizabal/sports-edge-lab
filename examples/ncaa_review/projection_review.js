/* Read-only display of supplied matched-head score means; never derives or fits a model. */
(() => {
  'use strict';
  const STATES = Object.freeze(['DERIVED_EXPECTED_SCORES', 'MISSING_COMPANION_HEAD',
    'INCOHERENT_NEGATIVE_EXPECTED_SCORE', 'UNSUPPORTED_SELECTOR_PAIRING', 'NON_NUMERIC_OR_SOURCE_ONLY']);
  const LABELS = Object.freeze({
    DERIVED_EXPECTED_SCORES: 'Derived expected scores',
    MISSING_COMPANION_HEAD: 'Matching margin or total head missing',
    INCOHERENT_NEGATIVE_EXPECTED_SCORE: 'Paired inputs imply a negative score',
    UNSUPPORTED_SELECTOR_PAIRING: 'Selector pairing is unsupported',
    NON_NUMERIC_OR_SOURCE_ONLY: 'No numerical companion input',
  });
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const count = v => Number.isSafeInteger(v) && v >= 0;
  const finite = v => typeof v === 'number' && Number.isFinite(v);
  const id = v => typeof v === 'string' && v.length > 0;
  function validate(value, streams, validateStream) {
    if (!object(value) || value.schema !== 'sel.ncaa.b055.score_projection_coverage.v1' ||
        !object(value.status_counts) || Object.keys(value.status_counts).some(s => !STATES.includes(s)) ||
        Object.values(value.status_counts).some(n => !count(n))) {
      throw Error('Invalid expected-score coverage or status inventory.');
    }
    for (const key of ['input_rows', 'contexts', 'derived_pairs', 'missing_companion_heads', 'paired_contexts']) {
      if (!count(value[key])) throw Error('Invalid expected-score count: ' + key);
    }
    const c = value.status_counts, n = state => c[state] || 0;
    if (value.derived_pairs !== n('DERIVED_EXPECTED_SCORES') ||
        value.missing_companion_heads !== n('MISSING_COMPANION_HEAD') ||
        value.paired_contexts !== n('DERIVED_EXPECTED_SCORES') + n('INCOHERENT_NEGATIVE_EXPECTED_SCORE') ||
        value.contexts !== 2*value.paired_contexts + value.missing_companion_heads ||
        value.count_closure !== 'contexts=2*paired_contexts+missing_companion_heads') {
      throw Error('Expected-score head/context closure differs.');
    }
    for (const key of ['all_physical_season_games_complete', 'joint_distribution_qualified',
      'integer_pmf_qualified', 'cover_push_loss_qualified']) {
      if (value[key] !== false) throw Error('Unsupported expected-score qualification.');
    }
    if (value.new_fits !== 0 || value.new_immutable_issues !== 0) {
      throw Error('A derived expected score cannot create a fit or issue.');
    }
    const stream = streams?.score_projections;
    validateStream(stream);
    if (stream.rows !== Object.values(c).reduce((a, b) => a+b, 0)) {
      throw Error('Expected-score emitted rows differ from the stream.');
    }
    return value;
  }
  function validateRows(rows) {
    const seen = new Set();
    for (const row of rows) {
      if (!object(row) || row.schema !== 'sel.ncaa.b055.score_projection.v1' ||
          !id(row.projection_id) || !STATES.includes(row.status) ||
          !['ncaam', 'ncaaw'].includes(row.league) || !id(row.event_key) || !id(row.event_id)) {
        throw Error('Invalid expected-score row identity or status.');
      }
      if (seen.has(row.projection_id)) throw Error('Duplicate expected-score record in this part.');
      seen.add(row.projection_id);
      if (row.new_fit_credit !== 0 || row.new_immutable_issue_credit !== 0 ||
          row.joint_distribution_qualified !== false || row.integer_pmf_qualified !== false ||
          row.cover_push_loss_qualified !== false || row.derived_mean_not_a_separate_score_model !== true ||
          row.original_issue_mutation !== false || row.automatic_promotion !== false) {
        throw Error('Expected-score record has unsupported scientific credit.');
      }
      if (row.status === 'DERIVED_EXPECTED_SCORES') {
        if (![row.mean_home_score, row.mean_away_score, row.expected_home_minus_away,
          row.expected_total].every(finite) || row.mean_home_score < 0 ||
          row.mean_away_score < 0 || row.expected_total < 0 ||
          !id(row.margin_prediction_id) || !id(row.total_prediction_id) ||
          !object(row.model_context) ||
          ['family', 'arm', 'training_history'].some(k => !id(row.model_context[k]))) {
          throw Error('Derived scores require both exact target identities and finite supported means.');
        }
      } else if (row.mean_home_score !== null || row.mean_away_score !== null) {
        throw Error('Blocked expected scores must remain null.');
      }
      for (const field of ['expected_home_minus_away', 'expected_total']) {
        if (row[field] !== null && !finite(row[field])) throw Error('Invalid retained expected-score input.');
      }
    }
    return rows;
  }
  function filterRows(rows, filters) {
    const query = String(filters.search || '').trim().toLowerCase();
    return rows.filter(row => (filters.state === 'all' || row.status === filters.state) &&
      (filters.league === 'all' || row.league === filters.league) &&
      (!query || [row.event_id, row.event_key, row.home_team, row.away_team,
        row.home_id, row.away_id, row.model_context?.family, row.status]
        .some(value => String(value ?? '').toLowerCase().includes(query))));
  }
  const api = {STATES, LABELS, validate, validateRows, filterRows};
  if (typeof module !== 'undefined' && module.exports) {module.exports = api; return;}
  window.NCAAProjectionReview = api;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const node = (tag, text) => {const n=document.createElement(tag);n.textContent=String(text);return n;};
  let current = null;
  api.active = () => current !== null;
  api.filtered = rows => filterRows(rows, {state:$('score-state').value,
    league:$('score-league').value, search:$('score-search').value});
  api.render = value => {
    current = value || null; $('score-content').hidden = !current;
    $('score-status').textContent = current
      ? 'The supplied expected-score inventory is loaded. Select its exact part to inspect pairs and blocked contexts.'
      : 'No expected-score projection inventory supplied. Missing pairs are not filled from other model rows.';
    $('score-state').value='all';$('score-league').value='all';$('score-search').value='';
    if (!current) return;
    $('score-counts').replaceChildren(...STATES.map(state => {
      const tr=document.createElement('tr');tr.append(node('td',LABELS[state]),
        node('td',current.status_counts[state]||0));return tr;
    }));
    $('score-contexts').textContent = current.input_rows + ' supplied input rows; ' +
      current.contexts + ' admitted head contexts = twice ' + current.paired_contexts +
      ' matched pair contexts + ' + current.missing_companion_heads +
      ' missing companion heads. Emitted dispositions and input/head counts are different denominators.';
  };
  api.setup = callbacks => {
    $('score-state').replaceChildren(new Option('Every supplied disposition','all'),
      ...STATES.map(state=>new Option(LABELS[state],state)));
    for(const key of ['score-state','score-league'])$(key).addEventListener('change',callbacks.changed);
    $('score-search').addEventListener('input',callbacks.changed);
    $('score-inspect').addEventListener('click',()=>callbacks.inspect('score_projections'));
    $('score-reset').addEventListener('click',()=>{
      $('score-state').value='all';$('score-league').value='all';$('score-search').value='';
      callbacks.changed();
    });
  };
})();
