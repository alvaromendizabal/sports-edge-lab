# Reuse completed models with the intended source consumer

Putting a selected archive at the front of `sys.path` does not replace a module
that Python already has in `sys.modules`. A later stage can therefore receive
an earlier stage's same-named feature or model consumer. Both source trees may
be authentic; the consumer for this stage still has the wrong identity.

The [standard-library example](isolated_source.py) reproduces that failure
using **invented source only**, then imports the exact declared source bytes
and restores the previous module objects. It performs no model fitting,
provider acquisition, forecast issuance or order placement.

```bash
python tracks/nfl/isolated_source.py
python -m unittest discover -s tracks/nfl -p 'test_isolated_source.py' -v
```

## A bounded import contract

The caller supplies an independently authenticated archive SHA-256 and the
complete module names for one flat source directory. The helper:

1. Reads the selected archive, checks its exact SHA-256, rejects ambiguous or
   unsafe member paths, and requires exact declared source membership.
2. Retains the verified source bytes in memory. Imports compile those bytes,
   even if the archive pathname subsequently changes.
3. Temporarily removes only the declared names from Python's module cache and
   installs a finder that answers only for those names. Declared dependencies
   within the bundle use the same source identity.
4. Restores the exact prior module objects and finder list on normal exit,
   import failure, caller failure or nested use. A previously absent module
   remains absent; an explicit cached `None` is restored too.

The receipt binds the archive hash, each source hash and the declared names.
After exit it lists successfully executed module names and whether restoration
ran. It does not contain machine-specific paths. Actual loaded modules retain
their selected source origin for inspection. Merely entering the context does
not execute unused source. Neither `sys.path` nor its importer cache is changed.

```python
import importlib
from isolated_source import isolated_source

# expected_hash must come from an independently verified source receipt.
with isolated_source(
    archive_path,
    expected_sha256=expected_hash,
    module_names=['invented_feature', 'invented_head'],
) as receipt:
    consumer = importlib.import_module('invented_head')
    # Use the existing model only after its separate weight/input checks pass.
```

## Boundaries that remain necessary

This is **trusted-code import-state management, not a security sandbox**. A hash
establishes byte identity, not that code is safe or scientifically valid. Source
can still have arbitrary side effects. Ordinary dependency imports and effects
outside the declared module names are not rolled back. Native extensions,
packages and standard-library replacement names are deliberately unsupported.

The helper's reentrant lock serializes its own callers. It cannot coordinate
arbitrary imports in other threads. Use a dedicated process when another
workload may import the same names, or when callers change global import state.
References retained by earlier callers still point to their original modules;
this helper does not rewrite existing object graphs or invalidate fitted models.
The complete archive is read into memory, so the caller must choose a suitable
bounded source capsule. It is not a streaming bulk-data loader.

## What successful reuse would prove

A real model stage must separately verify model weights, preprocessing,
features, numerical source-consumer parity, dependency admission and output
receipts. If a prior fit finished and only import/report persistence failed,
repair that stage and reuse its exact completed fit. Do not count a source
repair, synthetic test or reused prediction as a new estimator fit.

The tests cover cached foreign consumers, nested contexts, exceptions, exact
origin and source hashes, pathname replacement, duplicate/unsafe members,
missing/extra declarations, unsupported layouts and unchanged unrelated import
state. These are engineering checks. They establish no market-beating model,
promotion, genuine historical issue or profitable betting result.
