"""Small shared utilities. No credentials or network during import."""
import hashlib
import json
import os
import pathlib
import tempfile
from datetime import datetime, timezone


class GateError(RuntimeError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def require(ok, category, message):
    if not ok:
        raise GateError(category, message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def atomic_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, allow_nan=False, default=str) + '\n'
    tmp = path.with_name(path.name + '.partial')
    tmp.write_text(data)
    os.replace(tmp, path)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


class Checkpoints:
    def __init__(self, root, fingerprint):
        self.root = pathlib.Path(root)
        self.fingerprint = fingerprint
        self.folder = self.root / 'checkpoints'
        self.folder.mkdir(parents=True, exist_ok=True)

    def lookup(self, name):
        p = self.folder / (name + '.json')
        if not p.exists():
            return None
        m = read_json(p)
        require(m['fingerprint'] == self.fingerprint, 'SOURCE_STATE', 'Checkpoint source/environment changed: ' + name)
        for item in m['files']:
            f = self.root / item['path']
            require(f.is_file() and sha(f) == item['sha256'], 'SOURCE_STATE', 'Checkpoint file missing or changed: ' + item['path'])
        return m['result']

    def commit(self, name, files, result):
        rows = []
        for p in files:
            p = pathlib.Path(p)
            rows.append({'path': str(p.relative_to(self.root)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
        atomic_json(self.folder / (name + '.json'), {'fingerprint': self.fingerprint, 'completed_at': now(), 'files': rows, 'result': result})
        return result


def make_bundle(path, files):
    import zipfile
    path = pathlib.Path(path)
    tmp = path.with_name(path.name + '.partial')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, item in sorted(files.items()):
            item = pathlib.Path(item)
            if item.is_file():
                z.write(item, name)
    with zipfile.ZipFile(tmp) as z:
        require(z.testzip() is None, 'PACKAGING', 'Return ZIP CRC failure')
        require('summary.json' in z.namelist(), 'PACKAGING', 'Summary missing from ZIP')
    os.replace(tmp, path)
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}
