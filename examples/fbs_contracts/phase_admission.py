"""Invented demonstration: preserve the decision before admitting a phase.

This public example uses no project resource thresholds, live telemetry, source
requests or estimator code. The caller supplies its independently defined gate.
"""
from copy import deepcopy
import hashlib
import json


class AdmissionRefused(RuntimeError):
    def __init__(self, record):
        self.record = deepcopy(record)
        super().__init__(record['reason'])


def admission(observe, decide, persist, *, max_observations, retry_reasons=()):
    """Persist every immutable observation before work can be authorized.

    The bounded demonstration reobserves only explicitly designated transient
    reasons. Persistence failures propagate and never authorize a phase.
    """
    if type(max_observations) is not int or not 1 <= max_observations <= 100:
        raise ValueError('INVALID_OBSERVATION_BOUND')
    prior = None
    for number in range(1, max_observations + 1):
        snapshot = deepcopy(observe())
        decision = decide(deepcopy(snapshot))
        if (not isinstance(decision, dict) or type(decision.get('admitted')) is not bool
                or not isinstance(decision.get('reason'), str) or not decision['reason']):
            raise ValueError('INVALID_GATE_DECISION')
        record = {'observation': number, 'snapshot': snapshot,
                  'admitted': decision['admitted'], 'reason': decision['reason'],
                  'previous_record_sha256': prior, 'evidence_class': 'INVENTED_ENGINEERING_DEMONSTRATION'}
        raw = json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        record['sha256'] = hashlib.sha256(raw).hexdigest()
        persist(deepcopy(record))
        prior = record['sha256']
        if record['admitted']:
            return record
        if record['reason'] not in retry_reasons or number == max_observations:
            raise AdmissionRefused(record)
    raise AssertionError('Unreachable')
