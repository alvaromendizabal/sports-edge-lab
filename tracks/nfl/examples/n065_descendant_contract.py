"""Invented-input demonstration: declared descendants are not arbitrary extras.

No private model, account, provider source, runtime package or active recipe.
"""
from hashlib import sha256
from typing import Mapping


def reconcile(original: Mapping[str, str], declared: Mapping[str, str],
              actual: Mapping[str, bytes], committed: Mapping[str, str]) -> dict:
    """Retain original state hashes and require exact authorized additions."""
    if set(original) & set(declared):
        raise ValueError("descendant identity collides with immutable original")
    expected = dict(original) | dict(declared)
    if set(actual) != set(expected):
        raise ValueError("missing state or undeclared addition")
    for key, digest in expected.items():
        if sha256(actual[key]).hexdigest() != digest:
            raise ValueError("state body differs from its declared identity")
    if set(committed) != set(declared):
        raise ValueError("descendant commit inventory differs")
    for key, digest in declared.items():
        if committed[key] != digest:
            raise ValueError("descendant lacks the exact durable commit")
    return {"original_states": len(original), "verified_descendants": len(declared),
            "new_fit_credit": 0, "deleted_files": 0}
