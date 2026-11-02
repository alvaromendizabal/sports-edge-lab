"""Separate exact retained input identity from declared numerical replay.

The tiny schema and demo are invented engineering fixtures, not private feature
recipes. Trusted expected digests and replay policy must come from the caller.
This helper does not authenticate model execution, clocks or dependencies.
"""
from __future__ import annotations

import hashlib
import json
import math
import re


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('A finite number is required')
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Non-finite JSON constant: ' + value)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _validate(row):
    if type(row) is not dict or set(row) != {'identity', 'baseline', 'independent', 'derived'}:
        raise ValueError('Exact top-level schema required')
    identity = row['identity']
    if (type(identity) is not dict or set(identity) != {'event', 'source', 'model', 'cutoff'}
            or any(type(v) is not str or not v.strip() for v in identity.values())):
        raise ValueError('Complete identity declaration required')
    independent, derived = row['independent'], row['derived']
    if type(independent) is not dict or set(independent) != {'scale', 'offset'}:
        raise ValueError('Exact independent-field schema required')
    if type(derived) is not dict or set(derived) != {'shifted', 'scaled'}:
        raise ValueError('Exact derived-field schema required')
    baseline = _number(row['baseline'])
    scale, offset = (_number(independent[k]) for k in ('scale', 'offset'))
    expected = {'shifted': baseline + offset, 'scaled': baseline * scale}
    for key in expected:
        _number(derived[key]); _number(expected[key])
        if derived[key] != expected[key]:
            raise ValueError('Derived field violates its own baseline formula: ' + key)


def recover_original_inputs(original: bytes, *, expected_sha256: str,
                            recomputed: dict, baseline_abs_tolerance: float) -> tuple[bytes, dict]:
    """Validate replay, then return the unchanged authenticated original bytes.

    Identity and independent fields must match exactly, including numeric JSON
    representations. Each derived value must equal the declared formula applied
    to its own row's baseline. Only the baseline comparison uses the caller's
    predeclared absolute tolerance (exclusive); zero permits exact equality only.
    No numerical tolerance is applied to source bytes or downstream input hashes.
    """
    if type(original) is not bytes:
        raise ValueError('Original immutable bytes required')
    if type(expected_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('Trusted lowercase SHA-256 pin required')
    if hashlib.sha256(original).hexdigest() != expected_sha256:
        raise ValueError('Original input hash mismatch')
    tolerance = _number(baseline_abs_tolerance)
    if tolerance < 0:
        raise ValueError('Nonnegative predeclared tolerance required')
    saved = json.loads(original.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    _validate(saved); _validate(recomputed)
    for field in ('identity', 'independent'):
        if _canonical(saved[field]) != _canonical(recomputed[field]):
            raise ValueError('Exact field identity changed: ' + field)
    difference = abs(saved['baseline'] - recomputed['baseline'])
    if difference != 0 and not difference < tolerance:
        raise ValueError('Baseline numerical replay is outside the declared tolerance')
    return original, {
        'original_sha256': expected_sha256,
        'baseline_abs_difference': difference,
        'baseline_abs_tolerance_exclusive': tolerance,
        'independent_fields_compared_exactly': 2,
        'derived_formula_checks': 4,
        'original_bytes_changed': False,
        'training_hash_tolerance': 0,
        'new_fits': 0,
        'new_forecast_issues': 0,
        'owner_acceptance_claimed': False,
    }


def demo():
    """One floating-point ULP changes dependent values, not original inputs."""
    import copy
    original_row = {
        'identity': {'event': 'invented-event', 'source': 'invented-source',
                     'model': 'invented-model', 'cutoff': 'invented-clock-declaration'},
        'baseline': .5, 'independent': {'scale': 2., 'offset': .25},
        'derived': {'shifted': .75, 'scaled': 1.},
    }
    original = (json.dumps(original_row, indent=2) + '\n').encode()
    replay = copy.deepcopy(original_row)
    replay['baseline'] = math.nextafter(.5, 1.)
    replay['derived'] = {'shifted': replay['baseline'] + .25,
                         'scaled': replay['baseline'] * 2.}
    retained, receipt = recover_original_inputs(
        original, expected_sha256=hashlib.sha256(original).hexdigest(),
        recomputed=replay, baseline_abs_tolerance=1e-12)
    assert retained == original
    return {'evidence_class': 'INVENTED_ENGINEERING_FIXTURE',
            'ordinary_exact_derived_comparison': original_row['derived'] == replay['derived'],
            'receipt': receipt}


if __name__ == '__main__':
    print(json.dumps(demo(), indent=2))
