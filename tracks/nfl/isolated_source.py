"""Load a declared flat source bundle without reusing foreign cached modules.

This is process-global import-state management for trusted Python source, not
a security sandbox. The demo and tests use invented source only.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.abc
import importlib.util
import io
import keyword
from pathlib import Path
import sys
import threading
import zipfile


_LOCK = threading.RLock()
_MISSING = object()


def _bundle(archive, expected_sha256, module_names, prefix):
    """Bind the complete archive and exact selected source membership."""
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha256)):
        raise ValueError('A lowercase SHA-256 identity is required')
    names = tuple(module_names)
    if not names or len(names) != len(set(names)):
        raise ValueError('Nonempty unique module declarations are required')
    reserved = set(sys.builtin_module_names) | set(getattr(sys, 'stdlib_module_names', ()))
    for name in names:
        if (not isinstance(name, str) or not name.isidentifier()
                or keyword.iskeyword(name) or name in reserved or name.startswith('__')):
            raise ValueError('Only nonstandard flat module names are supported')
    if not isinstance(prefix, str) or not prefix.isidentifier() or keyword.iskeyword(prefix):
        raise ValueError('A single source directory name is required')
    archive = Path(archive).resolve(strict=True)
    body = archive.read_bytes()
    actual = hashlib.sha256(body).hexdigest()
    if actual != expected_sha256:
        raise ValueError('Source archive SHA-256 mismatch')
    selected = {}
    with zipfile.ZipFile(io.BytesIO(body)) as bundle:
        infos = bundle.infolist()
        paths = [x.filename for x in infos]
        if len(paths) != len(set(paths)):
            raise ValueError('Duplicate archive member')
        for info in infos:
            name = info.filename
            parts = name.rstrip('/').split('/')
            if (not name or name.startswith('/') or '\\' in name
                    or any(p in ('', '.', '..') for p in parts)
                    or ((info.external_attr >> 16) & 0o170000) == 0o120000):
                raise ValueError('Unsafe archive member')
            if name == prefix + '/' and info.is_dir():
                continue
            if name.startswith(prefix + '/'):
                tail = name[len(prefix) + 1:]
                if '/' in tail or not tail.endswith('.py'):
                    raise ValueError('Only flat Python source is supported in the selected directory')
                module = tail[:-3]
                if module not in names:
                    raise ValueError('Undeclared selected source module')
                selected[module] = bundle.read(info)  # also checks the selected member CRC
        if set(selected) != set(names):
            raise ValueError('Missing declared source module')
    return archive, actual, selected


class _SelectedSource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, archive, prefix, sources):
        self.sources = sources
        self.origins = {n: str(archive) + '!/' + prefix + '/' + n + '.py' for n in sources}
        self.loaded = set()

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.sources:
            return importlib.util.spec_from_loader(fullname, self, origin=self.origins[fullname])
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        name = module.__name__
        module.__file__ = self.origins[name]
        code = compile(self.sources[name], self.origins[name], 'exec', dont_inherit=True)
        exec(code, module.__dict__)
        self.loaded.add(name)


@contextmanager
def isolated_source(archive, *, expected_sha256, module_names, prefix='source'):
    """Temporarily import only the exact declared modules from verified bytes.

    The caller must trust the source and supply its independently verified hash.
    Packages, native extensions and undeclared selected sources are unsupported.
    A reentrant lock serializes this helper's callers, not arbitrary imports in
    other threads. Use a dedicated process if other work may import these names.
    Ordinary dependency imports and arbitrary source side effects are not undone.
    """
    archive, digest, sources = _bundle(archive, expected_sha256, module_names, prefix)
    finder = _SelectedSource(archive, prefix, sources)
    with _LOCK:
        prior = {n: sys.modules.get(n, _MISSING) for n in sources}
        previous_finders = list(sys.meta_path)
        receipt = {'archive_sha256': digest, 'declared_modules': sorted(sources),
                   'source_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in sorted(sources.items())},
                   'previously_cached_modules': sorted(n for n, v in prior.items() if v is not _MISSING),
                   'loaded_modules': [], 'restored': False}
        try:
            for name in sources:
                sys.modules.pop(name, None)
            sys.meta_path.insert(0, finder)
            yield receipt
        finally:
            for name in sources:
                sys.modules.pop(name, None)
                if prior[name] is not _MISSING:
                    sys.modules[name] = prior[name]
            sys.meta_path[:] = previous_finders
            receipt['loaded_modules'] = sorted(finder.loaded)
            receipt['restored'] = True


def demo():
    """Reproduce foreign-cache reuse, then recover using invented source."""
    import importlib
    import json
    import tempfile
    import types

    name = 'invented_forecast_head'
    previous = sys.modules.get(name, _MISSING)
    foreign = types.ModuleType(name)
    foreign.value = 'foreign cached source'
    sys.modules[name] = foreign
    try:
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'invented.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('source/' + name + '.py', "value = 'verified selected source'\n")
            pin = hashlib.sha256(archive.read_bytes()).hexdigest()
            before = importlib.import_module(name).value
            with isolated_source(archive, expected_sha256=pin, module_names=[name]) as receipt:
                selected = importlib.import_module(name).value
            return {'evidence_class': 'INVENTED_ENGINEERING_DEMONSTRATION',
                    'before': before, 'inside': selected,
                    'original_object_restored': sys.modules[name] is foreign,
                    'import_receipt': receipt, 'new_fits': 0, 'scientific_acceptance_claimed': False}
    finally:
        sys.modules.pop(name, None)
        if previous is not _MISSING:
            sys.modules[name] = previous


if __name__ == '__main__':
    import json
    print(json.dumps(demo(), indent=2))
