"""Invented-input cohort and complete-batch contracts, not the private predictor."""
import hashlib
import json


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def matched_rows(left, right):
    """A headline comparison needs the same event, target, cutoff and settlement."""
    fields = ('event', 'target', 'cutoff', 'settlement')
    def index(rows):
        result = {}
        for row in rows:
            key = tuple(row[k] for k in fields)
            if key in result:
                raise ValueError('duplicate cohort identity')
            result[key] = row
        return result
    a, b = index(left), index(right)
    if set(a) != set(b):
        raise ValueError('cohorts differ; no headline ranking')
    for key in sorted(a):
        if a[key]['truth'] != b[key]['truth']:
            raise ValueError('conflicting outcome')
    return [(a[key], b[key]) for key in sorted(a)]


def reuse_complete_batch(batch, expected_identity, expected_cases):
    """A partial batch is preserved but cannot masquerade as complete reuse."""
    if batch['identity'] != expected_identity:
        raise ValueError('batch identity differs')
    if batch.get('status') != 'complete' or set(batch['cases']) != set(expected_cases):
        raise ValueError('batch incomplete')
    if identity(batch['payload']) != batch['payload_sha256']:
        raise ValueError('batch payload changed')
    return batch['payload']
