// Invented contract fixtures only. No owner fits, forecasts or resource measurements.
const assert = require('node:assert/strict');
const execution = require('./execution_review.js');
const {fixture: legacyFixture} = require('./test_v4_review.cjs');

function fixture() {
  return {
    kind: 'b056_execution_review', schema: 'sel.ncaa.b056.execution_review.v1',
    execution_evidence_kind: 'LOCAL_FIXTURE_ONLY', status: 'REGISTERED_BATCH_REPORTED_WITH_EXPLICIT_GAPS',
    source_sha256: 'a'.repeat(64), run_id: 'invented-fixture-run',
    queue: {registered_contexts: 40000000, admitted_contexts: 20, completed_contexts: 12,
      remaining_contexts: 8, dispositions: {NEW: 4, REUSED: 3, SOURCE_BLOCKED: 2,
        DEPENDENCY_UNAVAILABLE: 1, FAILED: 2}, unit: 'event_target_recipe_contexts',
      physical_fit_credit_from_contexts: 0},
    counts: {new_target_fits: 2, reused_target_fit_accesses: 8, new_predictions: 4,
      reused_prediction_accesses: 11, new_immutable_issues: 0, new_promotions: 0},
    resources: {wall_seconds: 31.25, process_cpu_seconds: 50.5, process_peak_rss_bytes: 4096,
      peak_scope: 'Invented fixture process only', cost: null, eta_seconds: null,
      eta_reason: 'No calibrated remaining-work estimate in this invented fixture.'},
    limitations: ['Invented fixture values receive no scientific credit.'], streams: {},
  };
}
function run() {
  const checks = [];
  const check = (name, fn) => {fn(); checks.push(name);};
  const reject = (change, pattern) => {const value = fixture(); change(value); assert.throws(() => execution.validate(value), pattern);};
  check('bounded batch accepts a large separate registration universe', () =>
    assert.equal(execution.validate(fixture()).queue.admitted_contexts, 20));
  check('completion ratio uses admitted contexts rather than registered inventory', () =>
    assert.equal(execution.percent(fixture()), 60));
  check('completed dispositions include explicit failures and gaps', () =>
    assert.equal(Object.values(execution.validate(fixture()).queue.dispositions).reduce((a,b)=>a+b,0), 12));
  check('admitted closure cannot omit remaining contexts', () =>
    reject(value => value.queue.remaining_contexts--, /closure/));
  check('dispositions must sum to completed work and not admitted work', () =>
    reject(value => value.queue.dispositions.NEW += 8, /closure/));
  check('unknown dispositions do not silently disappear', () =>
    reject(value => value.queue.dispositions.UNKNOWN = 1, /bounded-queue/));
  check('admitted contexts cannot exceed registration', () =>
    reject(value => value.queue.registered_contexts = 19, /closure/));
  check('fractional, negative and unsafe queue counts reject', () => {
    for (const number of [1.5, -1, Number.MAX_SAFE_INTEGER + 1])
      reject(value => value.queue.admitted_contexts = number, /bounded-queue/);
  });
  check('overflowed queue addition cannot conceal closure', () =>
    reject(value => {value.queue.completed_contexts=Number.MAX_SAFE_INTEGER;value.queue.remaining_contexts=1;}, /closure/));
  check('a context is not a physical-fit credit', () =>
    reject(value => value.queue.physical_fit_credit_from_contexts = 1, /bounded-queue/));
  check('unsupported queue unit rejects', () =>
    reject(value => value.queue.unit = 'physical_fits', /bounded-queue/));
  check('reused accesses remain independent of physical-fit and context counts', () => {
    const value=fixture();value.counts.reused_target_fit_accesses=500;
    assert.equal(execution.validate(value).counts.new_target_fits, 2);
  });
  check('unknown ledger field cannot silently imply an extra result', () =>
    reject(value => value.counts.physical_games = 1, /ledger/));
  check('promotion credit is forbidden by this reporting contract', () =>
    reject(value => value.counts.new_promotions = 1, /promotion/));
  check('fractional and negative ledger counts reject', () => {
    for (const number of [0.5,-2]) reject(value => value.counts.new_predictions=number, /ledger/);
  });
  check('actual owner declaration needs an explicit recorded run', () =>
    reject(value => {value.execution_evidence_kind='ACTUAL_OWNER_RUNTIME';value.run_id=null;}, /run identity/));
  check('actual owner declaration can be inspected without upgrading it to proof', () => {
    const value=fixture();value.execution_evidence_kind='ACTUAL_OWNER_RUNTIME';
    assert.equal(execution.validate(value).execution_evidence_kind,'ACTUAL_OWNER_RUNTIME');
  });
  check('unknown evidence kind and status reject', () => {
    reject(value => value.execution_evidence_kind='CERTIFIED', /identity/);
    reject(value => value.status='COMPLETE_SEASON', /identity/);
  });
  check('prepared evidence cannot claim completed contexts or committed work', () =>
    reject(value => {value.execution_evidence_kind='PREPARED_NOT_EXECUTED';value.status='PREPARED_NOT_EXECUTED';}, /cannot claim/));
  check('prepared status and declared evidence kind agree', () =>
    reject(value => value.status='PREPARED_NOT_EXECUTED', /disagree/));
  check('empty prepared batch is explicitly unavailable rather than 100 percent', () => {
    const value=fixture();value.execution_evidence_kind='PREPARED_NOT_EXECUTED';value.status='PREPARED_NOT_EXECUTED';value.run_id=null;
    Object.keys(value.counts).forEach(key=>value.counts[key]=0);
    value.queue.admitted_contexts=value.queue.completed_contexts=value.queue.remaining_contexts=0;
    value.queue.dispositions={};assert.equal(execution.percent(execution.validate(value)),null);
  });
  check('missing resource values cannot become zeros', () =>
    reject(value => delete value.resources.process_cpu_seconds, /resources/));
  check('nonfinite and negative measurement values reject', () => {
    for (const number of [Infinity,NaN,-1]) reject(value => value.resources.wall_seconds=number, /resources/);
  });
  check('peak resource scope must be explicitly supplied', () =>
    reject(value => value.resources.peak_scope='', /resources/));
  check('an uncalibrated ETA must stay null with a reason', () => {
    reject(value => value.resources.eta_seconds=1, /unknown cost and ETA/);
    reject(value => value.resources.eta_reason='', /unknown cost and ETA/);
  });
  check('attributable cost is unknown in this initial contract', () =>
    reject(value => value.resources.cost=0, /unknown cost and ETA/));
  check('unknown top-level schema fields reject', () =>
    reject(value => value.secret_recipe = {}, /unsupported field/));
  check('source physical hash is mandatory', () =>
    reject(value => value.source_sha256='unbound', /identity/));
  check('hash validation does not coerce arrays into source identities', () =>
    reject(value => value.source_sha256=['a'.repeat(64)], /identity/));
  check('limitations remain explicit strings', () =>
    reject(value => value.limitations=[null], /limitations/));
  check('optional absent streams are accepted without stream credit', () => {
    const value=fixture();delete value.streams;assert.equal(execution.validate(value).streams,undefined);
  });
  check('existing bounded descriptors remain inspectable without loading parts', () => {
    const value=fixture();value.streams=legacyFixture().value.streams;
    assert.equal(execution.validate(value),value);
  });
  check('unbound or missing stream parts fail descriptor validation', () => {
    const value=fixture();value.streams=legacyFixture().value.streams;
    const stream=Object.values(value.streams)[0];stream.parts[0].reference.sha256='bad';
    assert.throws(()=>execution.validate(value),/part identity/);
  });
  check('a path cannot masquerade as a supported stream name', () =>
    reject(value => value.streams['private/cloud/path']={}, /stream inventory/));
  check('strict JSON rejects duplicate members before ordinary parsing discards them', () => {
    const source=JSON.stringify(fixture()).replace('"new_promotions":0','"new_promotions":0,"new_promotions":1');
    assert.throws(()=>execution.parse(source),/Duplicate/);
  });
  check('strict JSON rejects nonfinite literals and extra trailing material', () => {
    assert.throws(()=>execution.parse(JSON.stringify(fixture()).replace('31.25','1e999')),/Nonfinite/);
    assert.throws(()=>execution.parse(JSON.stringify(fixture())+'{}'),/trailing/);
  });
  check('ordinary valid JSON preserves exact declared values', () =>
    assert.deepEqual(execution.parse(JSON.stringify(fixture())),fixture()));
  return {status:'PASS', checks:checks.length, names:checks, evidence_kind:'LOCAL_FIXTURE_ONLY', new_owner_work:0};
}
module.exports={fixture,run};
if(require.main===module)process.stdout.write(JSON.stringify(run())+'\n');
