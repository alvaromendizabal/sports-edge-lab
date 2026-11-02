# Test the packaged execution context

A Python module imported from a zipapp can have a `__file__` such as
`example.pyz/forecast.py`. That is an import origin, not a normal directory.
Calling `Path(module.__file__).read_text()` can therefore fail even when the
same test passed against extracted files.

An authenticated NFL owner attempt reached exactly this boundary: its required
gate ran 934 tests, with 933 passing and one source-read error. Research had not
started. That failure does not disprove or erase completed models, and a
successful archive checksum alone would not exercise the failing test.

The [standard-library example](packaged_source.py) reads an existing module's
source through a supported source loader or a captured ZIP. It binds the module
name, spec, loader and origin, verifies the source digest, and requires a separate
physical archive digest for ZIP imports. ZIP membership and CRC checks remain
strict. Wrong hashes, unsafe or duplicate members, unknown loaders and changed
origins are rejected. It does not rewrite or execute the source it reads.

From the repository root:

```bash
python tracks/nfl/packaged_source.py
python -m unittest discover -s tracks/nfl -p 'test_packaged_source.py' -v
```

The demo reproduces the ordinary path failure using an invented module and then
reads its exact authenticated bytes. Tests also launch a real `.pyz` subprocess,
so the helper and inspected module are both imported from the package. The
negative package test refuses a changed physical digest. No provider, cloud
account, sports data, model fitting or betting operation is involved.

## Limits and acceptance

Trusted expected hashes must come from an independently authenticated caller;
computing a new hash from an untrusted file and accepting it establishes nothing.
The fixture generates its own pins only because it is an invented local test.
This example supports UTF-8 `.py` modules under standard file/ZIP loaders, not
native extensions, custom loaders or bytecode-only modules. It reads a small
archive into memory; a production reader must honor measured resource limits.

Source-byte verification does not prove which code an already-imported module
executed earlier, authenticate its dependencies, or establish scientific
acceptance. Production acceptance also needs exact package/runtime identities,
the full required test gate in the actual import context, source-consumer
numerical parity, completed-output receipts and the actual owner result.
These engineering fixtures supply no model fit, forecast or owner-run credit.
