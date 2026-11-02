"""Read pinned UTF-8 source from a normal module or a zipapp.

This verifies the captured source, not the historical execution of an already
imported module. The caller supplies trusted pins; it is not a security sandbox.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import io
from pathlib import Path
import types
import zipfile
import zipimport


def _digest(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in '0123456789abcdef' for c in value)):
        raise ValueError('A lowercase SHA-256 pin is required')
    return value


def read_pinned_source(module, *, source_sha256, archive_sha256=None):
    """Return exact pinned UTF-8 source, without importing or executing it.

    Standard source-file and ZIP import loaders are supported. A ZIP requires
    its own independently supplied physical archive pin. Whole archive bytes,
    names and CRCs are checked before reading the selected member. Native,
    bytecode-only and custom-loader modules are deliberately unsupported.
    """
    source_sha256 = _digest(source_sha256)
    if not isinstance(module, types.ModuleType):
        raise ValueError('An existing module is required')
    spec = getattr(module, '__spec__', None)
    loader = getattr(module, '__loader__', None)
    origin = getattr(module, '__file__', None)
    if (spec is None or spec.name != module.__name__ or spec.loader is not loader
            or not isinstance(origin, str) or spec.origin != origin
            or not origin.endswith('.py')):
        raise ValueError('Module/spec/source origin mismatch')
    if type(loader) is importlib.machinery.SourceFileLoader:
        if archive_sha256 is not None:
            raise ValueError('An archive pin cannot describe a normal source file')
        if loader.name != module.__name__ or loader.get_filename(module.__name__) != origin:
            raise ValueError('Source loader origin mismatch')
        body = loader.get_data(origin)
    elif type(loader) is zipimport.zipimporter:
        archive_sha256 = _digest(archive_sha256)
        if loader.get_filename(module.__name__) != origin:
            raise ValueError('ZIP loader origin mismatch')
        archive = Path(loader.archive)
        prefix = str(archive) + '/'
        portable_origin = origin.replace('\\', '/')
        prefix = prefix.replace('\\', '/')
        if not portable_origin.startswith(prefix):
            raise ValueError('Module is outside the declared archive')
        member = portable_origin[len(prefix):]
        captured = archive.read_bytes()
        if hashlib.sha256(captured).hexdigest() != archive_sha256:
            raise ValueError('Physical archive hash mismatch')
        with zipfile.ZipFile(io.BytesIO(captured)) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or len(names) != len({n.casefold() for n in names}):
                raise ValueError('Duplicate or ambiguous ZIP member')
            for item in z.infolist():
                name = item.filename
                parts = name.rstrip('/').split('/')
                if (not name or name.startswith('/') or '\\' in name
                        or any(p in ('', '.', '..') for p in parts)
                        or ':' in parts[0]
                        or ((item.external_attr >> 16) & 0o170000) == 0o120000):
                    raise ValueError('Unsafe ZIP member')
            if z.testzip() is not None:
                raise ValueError('ZIP CRC mismatch')
            body = z.read(member)
    else:
        raise ValueError('Unsupported source loader')
    if hashlib.sha256(body).hexdigest() != source_sha256:
        raise ValueError('Source hash mismatch')
    return body.decode('utf-8')


def demo():
    """Exercise the actual ZIP import context using an invented tiny module."""
    import importlib
    import sys
    import tempfile

    name = 'invented_zip_forecast'
    source = b"description = 'invented engineering fixture; no model fits'\n"
    previous = sys.modules.get(name)
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder) / 'invented.pyz'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr(name + '.py', source)
        sys.path.insert(0, str(archive))
        sys.modules.pop(name, None)
        try:
            module = importlib.import_module(name)
            try:
                Path(module.__file__).read_text()
            except (NotADirectoryError, FileNotFoundError):
                ordinary_path_failed = True
            else:
                ordinary_path_failed = False
            result = read_pinned_source(
                module, source_sha256=hashlib.sha256(source).hexdigest(),
                archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
            return {'evidence_class': 'INVENTED_ENGINEERING_DEMONSTRATION',
                    'ordinary_path_read_failed': ordinary_path_failed,
                    'pinned_zip_source_matched': result.encode('utf-8') == source,
                    'new_model_fits': 0, 'owner_acceptance_claimed': False}
        finally:
            sys.path.remove(str(archive))
            sys.modules.pop(name, None)
            if previous is not None:
                sys.modules[name] = previous
            sys.path_importer_cache.pop(str(archive), None)


if __name__ == '__main__':
    import json
    print(json.dumps(demo(), indent=2))
