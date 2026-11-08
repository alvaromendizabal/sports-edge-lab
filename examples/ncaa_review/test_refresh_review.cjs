// Invented refresh plans verify the generic viewer contract; no owner work or predictions.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {gzipSync} = require('node:zlib');
const refresh = require('./refresh_review.js');
const review = require('./v4_review.js');
const {fixture: legacyFixture} = require('./test_v4_review.cjs');
const sha = body => crypto.createHash('sha256').update(body).digest('hex');
function stream(name, rows) {
  const logical = Buffer.from(rows.map(row => JSON.stringify(row) + '\n').join(''));
  const body = gzipSync(logical);
  const part = {ordinal: 0, rows: rows.length,
    logical: {bytes: logical.length, sha256: sha(logical)},
    reference: {key: 'invented/' + name + '.jsonl.gz', bytes: body.length, sha256: sha(body)},
    encoding: 'gzip/canonical-json-lines'};
  const descriptor = {schema: 'sel.ncaa.b054.evidence_parts.v1', name,
    status: 'LOCAL_FIXTURE_ONLY', rows: rows.length, logical_bytes: logical.length,
    logical_sha256: sha(logical), parts: [part], maximum_logical_part_bytes: 8*1024*1024,
    all_parts_required_at_use: true, known_missing_parts_are_fatal: true,
    model_fit_credit_from_stream_rows: 0};
  return {descriptor, part, body, rows};
}
function fixture() {
  const value = legacyFixture().value;
  value.schema = 'sel.ncaa.b055.private_review.v1'; value.release = 'B055';
  value.status = 'LOCAL_FIXTURE_ONLY';
  const rows = refresh.STATES.flatMap((state, index) => refresh.TARGETS.map(target => ({
    event_key: 'invented-source-event-' + index, event_id: 'invented-refresh-' + index,
    source_namespace: 'invented', league: index%2 ? 'ncaaw' : 'ncaam',
    season_end_year: 2027, target, state, role: 'invented_candidate_baseline',
    event_time: '2026-11-09T01:00:00Z', window_open_at: null,
    cutoff_time: state === 'MISSED_WINDOW' ? '2026-11-08T11:00:00Z' : '2026-11-09T00:00:00Z',
    reason: state === 'SOURCE_BLOCKED' ? 'INVENTED_SOURCE_CLOCK_MISSING' : 'INVENTED_' + state,
    next_action: index === 0 ? '<img src=x onerror="window.bad=true"> inspect the invented fixture' : 'Inspect the supplied invented evidence',
    prediction_id: null, training_snapshot_id: null,asof:'2026-11-08T12:00:00Z',
    new_forecast_credit:0,previous_state_is_not_current_server_issue_proof:true,
    missed_window_is_evidence_gap_not_proof_no_legacy_issue:state==='MISSED_WINDOW',
  })));
  const plan = stream('refresh_plan', rows);
  const audit = stream('refresh_audit', [
    {kind: 'INVENTED_PLAN_OPERATION', disposition: 'PLANNED', new_owner_fits: 0},
    {kind: 'INVENTED_PLAN_OPERATION', disposition: 'SOURCE_GAP', new_owner_fits: 0},
  ]);
  value.streams.refresh_plan = plan.descriptor;
  value.streams.refresh_audit = audit.descriptor;
  value.report.refresh_coverage = {
    schema: 'sel.ncaa.b055.refresh_coverage.v1', asof: '2026-11-08T12:00:00Z',
    policy_id: 'invented-refresh-policy', schedule_rows: 11, unique_event_keys: 9,
    target_contexts: 27, counts_by_state: Object.fromEntries(refresh.STATES.map(s => [s, 3])),
    counts_by_target: Object.fromEntries(refresh.TARGETS.map(t =>
      [t, Object.fromEntries(refresh.STATES.map(s => [s, 1]))])),
    next_refresh_at: null, missed_contexts: 3, blocked_contexts: 6,
    new_fit_groups: 1, reused_fit_groups: 1, feature_only_refreshes: 1,
    full_physical_season_coverage:false,background_scheduler_created:false,original_issue_mutation:false,
    new_promotions:0,plan_counts_describe_registered_asof_not_wall_clock_at_report:true,
    unclassified_verified_fit_groups:0,execution_context_dispositions:{SOURCE_ONLY_NO_MODEL_CALLBACK:27},
    verified_issue_count: 0, streams: {plan: plan.descriptor, audit: audit.descriptor},
  };
  return {value, plan, audit, rows};
}
function run() {
  const checks = [];
  const check = (name, fn) => { fn(); checks.push(name); };
  const copy = () => JSON.parse(JSON.stringify(fixture().value));
  check('legacy B054 still accepted without refresh coverage', () =>
    assert.equal(review.validateV4(legacyFixture().value).release, 'B054'));
  check('explicit B055 review accepts a conserved refresh plan', () =>
    assert.equal(review.validateV4(copy()).report.refresh_coverage.target_contexts, 27));
  check('B055 absence is not a zero coverage manifest', () => {
    const value = copy(); delete value.report.refresh_coverage;
    delete value.streams.refresh_plan; delete value.streams.refresh_audit;
    assert.equal(review.validateV4(value).report.refresh_coverage, undefined);
  });
  check('schema and release cannot silently cross', () => {
    const value = copy(); value.release = 'B054';
    assert.throws(() => review.validateV4(value), /separate V4/);
  });
  check('future unreviewed schema is rejected', () => {
    const value = copy(); value.release = 'B056'; value.schema = 'sel.ncaa.b056.private_review.v1';
    assert.throws(() => review.validateV4(value), /separate V4/);
  });
  check('plan references without summary reject', () => {
    const value = copy(); delete value.report.refresh_coverage;
    assert.throws(() => review.validateV4(value), /coverage manifest/);
  });
  check('unknown state cannot silently become a known one', () => {
    const value = copy(); value.report.refresh_coverage.counts_by_state.CURRENT = 1;
    assert.throws(() => review.validateV4(value), /state counts/);
  });
  check('state totals must conserve contexts', () => {
    const value = copy(); value.report.refresh_coverage.target_contexts++;
    assert.throws(() => review.validateV4(value), /conserve/);
  });
  check('equal target sum cannot conceal different state cells', () => {
    const value = copy(), counts = value.report.refresh_coverage.counts_by_target.win;
    counts.DUE_MODEL_REFRESH++; counts.SOURCE_BLOCKED--;
    assert.throws(() => review.validateV4(value), /state and target cells/);
  });
  check('blocked subtotal includes missing recipe and source blocks', () => {
    const value = copy(); value.report.refresh_coverage.blocked_contexts = 3;
    assert.throws(() => review.validateV4(value), /subtotal/);
  });
  check('invalid and timezone-free declared clocks reject', () => {
    for (const asof of ['not a date', '2026-11-08T12:00:00']) {
      const value = copy(); value.report.refresh_coverage.asof = asof;
      assert.throws(() => review.validateV4(value), /declared clock/);
    }
  });
  check('missing next clock remains null and is not browser-now', () =>
    assert.equal(review.validateV4(copy()).report.refresh_coverage.next_refresh_at, null));
  check('fractional counts reject', () => {
    const value = copy(); value.report.refresh_coverage.new_fit_groups = 1.5;
    assert.throws(() => review.validateV4(value), /count/);
  });
  check('nested and top-level descriptors must agree beyond totals', () => {
    const value = copy();
    value.report.refresh_coverage.streams.plan.parts[0].reference.key = 'invented/different';
    assert.throws(() => review.validateV4(value), /descriptor differs/);
  });
  check('plan target count does not borrow operation rows', () => {
    const value = copy();
    value.report.refresh_coverage.streams.plan = value.streams.refresh_audit;
    value.streams.refresh_plan = value.streams.refresh_audit;
    assert.throws(() => review.validateV4(value), /plan rows/);
  });
  check('all exact invented plan rows pass without granting forecast credit', () =>
    assert.equal(refresh.validatePlanRows(fixture().rows).length, 27));
  check('duplicate source-event target fails within a loaded part', () => {
    const rows = fixture().rows; rows.push({...rows[0]});
    assert.throws(() => refresh.validatePlanRows(rows), /Duplicate/);
  });
  check('wrong target and unknown state reject at interpretation', () => {
    for (const [key, value] of [['target', 'cover'], ['state', 'PASSED']]) {
      const rows = fixture().rows; rows[0][key] = value;
      assert.throws(() => refresh.validatePlanRows(rows), /row identity/);
    }
  });
  check('missing recovery action cannot become a blank row', () => {
    const rows = fixture().rows; rows[0].next_action = '';
    assert.throws(() => refresh.validatePlanRows(rows), /recovery action/);
  });
  check('source keys and plan rows have explicit different denominators', () => {
    const value = review.validateV4(copy());
    assert.equal(value.report.refresh_coverage.unique_event_keys, 9);
    assert.equal(value.report.refresh_coverage.target_contexts, 27);
    assert.equal(value.report.refresh_coverage.streams.audit.rows, 2);
  });
  check('filters preserve exact rows and unavailable values', () => {
    const rows = fixture().rows;
    const filtered = refresh.filterRows(rows, {state: 'SOURCE_BLOCKED',
      league: 'ncaam', target: 'win', search: 'source_clock'});
    assert.equal(filtered.length, 1); assert.equal(filtered[0], rows[18]);
    assert.equal(filtered[0].prediction_id, null);
  });
  check('zero-match filter never falls back to all games', () =>
    assert.equal(refresh.filterRows(fixture().rows, {state: 'all', league: 'all',
      target: 'all', search: 'not-present'}).length, 0));
  check('plan asof cannot be replaced by another clock', () => {
    assert.throws(()=>refresh.validatePlanRows(fixture().rows,'2026-11-09T00:00:00Z'),/manifest clocks/);
  });
  check('plan rows cannot grant an issue or forecast', () => {
    const rows=fixture().rows;rows[0].new_forecast_credit=1;
    assert.throws(()=>refresh.validatePlanRows(rows),/forecast or issue credit/);
  });
  check('execution outcome counts cannot silently replace plan counts', () => {
    const value=copy();value.report.refresh_coverage.execution_context_dispositions.SOURCE_ONLY_NO_MODEL_CALLBACK--;
    assert.throws(()=>review.validateV4(value),/execution dispositions/);
  });
  check('exact clock strings are retained without wall-clock reclassification', () => {
    const rows = fixture().rows;
    assert.equal(refresh.filterRows(rows, {state: 'MISSED_WINDOW', league: 'all',
      target: 'all'}).length, 3);
    assert.equal(rows[15].cutoff_time, '2026-11-08T11:00:00Z');
  });
  console.log(JSON.stringify({status: 'PASS', checks: checks.length,
    scope: 'invented private refresh-file contracts; zero owner science', tests: checks}));
}
if (require.main === module) run();
module.exports = {fixture};
