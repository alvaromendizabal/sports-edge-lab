/* Generic bounded-execution inspector. Imported declarations never create scientific credit. */
(() => {
  'use strict';
  const contracts = typeof module !== 'undefined' && module.exports
    ? require('./v4_review.js') : window.NCAAReviewContracts;
  const LIMIT = 16 * 1024 * 1024;
  const KINDS = Object.freeze(['ACTUAL_OWNER_RUNTIME', 'LOCAL_FIXTURE_ONLY', 'PREPARED_NOT_EXECUTED']);
  const STATUSES = Object.freeze(['PREPARED_NOT_EXECUTED', 'RUNNING',
    'REGISTERED_BATCH_REPORTED_WITH_EXPLICIT_GAPS', 'FAILED_PARTIAL_WORK_PRESERVED',
    'RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED']);
  const DISPOSITIONS = Object.freeze(['NEW', 'REUSED', 'SOURCE_BLOCKED', 'DEPENDENCY_UNAVAILABLE', 'FAILED']);
  const COUNT_LABELS = Object.freeze({
    new_target_fits: 'New target fits',
    reused_target_fit_accesses: 'Reused target-fit accesses',
    new_predictions: 'New prediction records',
    reused_prediction_accesses: 'Reused prediction accesses',
    new_immutable_issues: 'New immutable issues',
    new_promotions: 'New promotions',
  });
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const text = value => typeof value === 'string' && value.trim().length > 0 && value.length <= 2000;
  const measured = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
  function exactKeys(value, required, optional = []) {
    return object(value) && required.every(key => Object.hasOwn(value, key)) &&
      Object.keys(value).every(key => required.includes(key) || optional.includes(key));
  }
  function validate(value) {
    if (!exactKeys(value, ['kind', 'schema', 'status', 'execution_evidence_kind',
      'source_sha256', 'run_id', 'queue', 'counts', 'resources', 'limitations'], ['streams']) ||
      value.kind !== 'b056_execution_review' || value.schema !== 'sel.ncaa.b056.execution_review.v1' ||
      !KINDS.includes(value.execution_evidence_kind) || !STATUSES.includes(value.status) ||
      typeof value.source_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(value.source_sha256) ||
      !(value.run_id === null || text(value.run_id))) {
      throw Error('Invalid B056 execution-review identity or unsupported field.');
    }
    if (value.execution_evidence_kind === 'ACTUAL_OWNER_RUNTIME' && !text(value.run_id)) {
      throw Error('An actual-owner declaration needs its recorded run identity.');
    }
    if ((value.execution_evidence_kind === 'PREPARED_NOT_EXECUTED') !==
        (value.status === 'PREPARED_NOT_EXECUTED')) {
      throw Error('Prepared evidence and execution status disagree.');
    }
    const q = value.queue;
    if (!exactKeys(q, ['registered_contexts', 'admitted_contexts', 'completed_contexts',
      'remaining_contexts', 'dispositions', 'unit', 'physical_fit_credit_from_contexts']) ||
      q.unit !== 'event_target_recipe_contexts' || q.physical_fit_credit_from_contexts !== 0 ||
      ['registered_contexts', 'admitted_contexts', 'completed_contexts', 'remaining_contexts']
        .some(key => !count(q[key])) || !object(q.dispositions) ||
      Object.keys(q.dispositions).some(key => !DISPOSITIONS.includes(key)) ||
      Object.values(q.dispositions).some(value => !count(value))) {
      throw Error('Invalid bounded-queue counts, unit or context-to-fit credit.');
    }
    const total = q.completed_contexts + q.remaining_contexts;
    const classified = Object.values(q.dispositions).reduce((sum, value) => sum + value, 0);
    if (!Number.isSafeInteger(total) || !Number.isSafeInteger(classified) ||
      total !== q.admitted_contexts || q.admitted_contexts > q.registered_contexts ||
      classified !== q.completed_contexts) {
      throw Error('Queue closure failed: completed dispositions and remaining admitted work must reconcile.');
    }
    if (!exactKeys(value.counts, Object.keys(COUNT_LABELS)) ||
      Object.values(value.counts).some(value => !count(value)) || value.counts.new_promotions !== 0) {
      throw Error('Invalid execution ledger counts or unsupported promotion credit.');
    }
    if (value.status === 'PREPARED_NOT_EXECUTED' &&
      (q.completed_contexts !== 0 || Object.values(value.counts).some(value => value !== 0))) {
      throw Error('Prepared evidence cannot claim executed contexts or ledger work.');
    }
    const r = value.resources;
    if (!exactKeys(r, ['wall_seconds', 'process_cpu_seconds', 'process_peak_rss_bytes',
      'peak_scope', 'cost', 'eta_seconds', 'eta_reason']) ||
      !measured(r.wall_seconds) || !measured(r.process_cpu_seconds) ||
      !count(r.process_peak_rss_bytes) || !text(r.peak_scope) ||
      r.cost !== null || r.eta_seconds !== null || !text(r.eta_reason)) {
      throw Error('Invalid measured resources; this schema requires an explicit unknown cost and ETA.');
    }
    if (!Array.isArray(value.limitations) || value.limitations.length > 100 ||
      value.limitations.some(value => !text(value))) throw Error('Invalid execution limitations.');
    if (value.streams !== undefined) {
      if (!object(value.streams) || Object.keys(value.streams).length > 100 ||
        Object.keys(value.streams).some(key => !/^[A-Za-z][A-Za-z0-9_]{0,79}$/.test(key))) {
        throw Error('Invalid execution stream inventory.');
      }
      for (const stream of Object.values(value.streams)) contracts.validateStream(stream);
    }
    return value;
  }
  function parse(source) { return validate(contracts.strictJSON(source)); }
  function percent(value) {
    return value.queue.admitted_contexts === 0 ? null :
      100 * value.queue.completed_contexts / value.queue.admitted_contexts;
  }
  const api = {LIMIT, KINDS, STATUSES, DISPOSITIONS, COUNT_LABELS, validate, parse, percent};
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
  window.NCAAExecutionReview = api;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  if (!$('execution-file')) return;
  const node = (tag, value) => {
    const result = document.createElement(tag);
    if (value !== undefined) result.textContent = String(value);
    return result;
  };
  const integer = value => value.toLocaleString('en-US');
  const seconds = value => value.toLocaleString('en-US', {maximumFractionDigits: 3}) + ' seconds';
  let generation = 0;
  function row(target, label, value) {
    const tr = node('tr'); tr.append(node('th', label), node('td', value)); target.append(tr);
  }
  function render(value, physical) {
    $('execution-content').hidden = false;
    $('execution-clear').disabled = false;
    $('execution-kind').textContent = 'Declared evidence: ' + value.execution_evidence_kind +
      ' · Recorded status: ' + value.status;
    $('execution-identity').textContent = 'Recorded run: ' + (value.run_id ?? 'Not executed') +
      ' · Source SHA-256: ' + value.source_sha256;
    $('execution-file-pin').textContent = 'Loaded file: ' + integer(physical.bytes) +
      ' bytes · SHA-256 ' + physical.sha256 + '. This file pin does not authenticate an owner run by itself.';
    const q = value.queue, progress = percent(value);
    $('execution-progress').max = Math.max(1, q.admitted_contexts);
    $('execution-progress').value = q.completed_contexts;
    $('execution-progress').hidden = progress === null;
    $('execution-progress-copy').textContent = progress === null
      ? 'No batch admitted. Completion percentage is unavailable.'
      : integer(q.completed_contexts) + ' of ' + integer(q.admitted_contexts) +
        ' admitted contexts have a recorded disposition (' + progress.toFixed(1) + '%). ' +
        integer(q.remaining_contexts) + ' admitted contexts remain. Completed dispositions include explicit gaps and failures.';
    $('execution-registered').textContent = integer(q.registered_contexts) +
      ' registered event/target/recipe contexts. This broader inventory is not the batch completion denominator, a physical-fit count or a whole-project ETA.';
    const dispositions = $('execution-dispositions'); dispositions.replaceChildren();
    for (const key of DISPOSITIONS) row(dispositions, key.replaceAll('_', ' '), integer(q.dispositions[key] || 0));
    const ledger = $('execution-ledger'); ledger.replaceChildren();
    for (const [key, label] of Object.entries(COUNT_LABELS)) row(ledger, label, integer(value.counts[key]));
    const resources = $('execution-resources'); resources.replaceChildren();
    row(resources, 'Measured wall time', seconds(value.resources.wall_seconds));
    row(resources, 'Measured process CPU', seconds(value.resources.process_cpu_seconds));
    row(resources, 'Measured process peak RSS', integer(value.resources.process_peak_rss_bytes) + ' bytes');
    row(resources, 'Peak measurement scope', value.resources.peak_scope);
    row(resources, 'Attributable cost', 'Unknown');
    row(resources, 'Remaining-time estimate', 'Unknown · ' + value.resources.eta_reason);
    const limitations = $('execution-limitations'); limitations.replaceChildren();
    for (const item of value.limitations) limitations.append(node('li', item));
    if (!value.limitations.length) limitations.append(node('li', 'No additional limitations supplied; this is not proof of complete coverage.'));
    const streams = Object.values(value.streams || {});
    $('execution-streams').textContent = integer(streams.length) +
      ' declared bounded evidence streams. Descriptor structure was checked; no stream body was opened. Physical part bytes, logical hashes and full at-use closure remain unverified here.';
    $('execution-status').className = 'status';
    $('execution-status').textContent = value.execution_evidence_kind === 'ACTUAL_OWNER_RUNTIME'
      ? 'Owner-declared execution review loaded. Counters reconcile; scientific authority still requires the original authenticated owner evidence.'
      : 'Prepared or fixture review loaded. Its records receive no owner scientific credit.';
  }
  $('execution-file').addEventListener('change', async () => {
    const file = $('execution-file').files[0], token = ++generation;
    if (!file) return;
    try {
      if (file.size > LIMIT) throw Error('Execution review exceeds 16 MiB.');
      const bytes = await file.arrayBuffer();
      if (bytes.byteLength !== file.size) throw Error('Execution-review file size changed.');
      const value = parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
      const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
        .map(value => value.toString(16).padStart(2, '0')).join('');
      if (token !== generation) return;
      render(value, {bytes: bytes.byteLength, sha256});
    } catch (error) {
      if (token !== generation) return;
      $('execution-status').className = 'status error';
      $('execution-status').textContent = 'Cannot open execution review: ' + error.message + ' The previous valid view remains.';
    }
  });
  $('execution-clear').addEventListener('click', () => {
    generation++; $('execution-file').value = ''; $('execution-content').hidden = true;
    $('execution-clear').disabled = true; $('execution-status').className = 'status';
    $('execution-status').textContent = 'No execution review loaded. Missing evidence does not mean zero work.';
    for (const id of ['execution-kind', 'execution-identity', 'execution-file-pin',
      'execution-progress-copy', 'execution-registered', 'execution-dispositions',
      'execution-ledger', 'execution-resources', 'execution-limitations', 'execution-streams']) $(id).replaceChildren();
  });
})();
