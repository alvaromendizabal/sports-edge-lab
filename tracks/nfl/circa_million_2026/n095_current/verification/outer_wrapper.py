"""Verify and run the embedded owner zipapp without a network dependency."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--overlay-self-test', action='store_true')
    args, other = parser.parse_known_args()
    executable = Path(sys.argv[0]).absolute()
    if executable.is_symlink() or hashlib.sha256(executable.read_bytes()).hexdigest() != args.expected_sha256:
        raise ValueError('N095_OUTER_DIGEST_MISMATCH')
    with ZipFile(executable) as z:
        if z.namelist() != ['__main__.py', 'owner.json']:
            raise ValueError('N095_OUTER_MEMBERSHIP_MISMATCH')
        meta = json.loads(z.read('owner.json'))
    data = base64.b64decode(meta['base64'], validate=True)
    digest = hashlib.sha256(data).hexdigest()
    if digest != meta['sha256'] or len(data) != meta['bytes']:
        raise ValueError('N095_INNER_DIGEST_MISMATCH')
    with ZipFile(io.BytesIO(data)) as z:
        manifest = json.loads(z.read('OVERLAY.json'))
        if set(z.namelist()) != set(manifest['files']) | {'__main__.py','OVERLAY.json'}:
            raise ValueError('N095_BAD_OVERLAY_MEMBERSHIP')
        for name, pin in manifest['files'].items():
            body = z.read(name)
            if hashlib.sha256(body).hexdigest() != pin['sha256'] or len(body) != pin['bytes']:
                raise ValueError('N095_OVERLAY_MEMBER_HASH_MISMATCH')
            if name.endswith('.py'):
                compile(body, name, 'exec')
        compile(z.read('__main__.py'), '__main__.py', 'exec')
    if args.overlay_self_test:
        print(json.dumps({'status':'PASS','external_sha256':args.expected_sha256,'inner_sha256':digest,
                          'proof':'CPython outer dispatch, inner CRC/SHA-256 and module compilation','owner_fits':0}))
        return 0
    home = args.fixture_root.absolute() if args.fixture_root else Path(meta['home'])
    if not args.fixture_root and not home.is_dir():
        raise ValueError('N095_EXISTING_OWNER_HOME_REQUIRED')
    cache = home.joinpath(*meta['cache_components'])
    if any(p.is_symlink() for p in (cache,*cache.parents)):
        raise ValueError('N095_UNSAFE_OWNER_PATH')
    cache.mkdir(parents=True, exist_ok=True)
    inner = cache / (digest + '.pyz')
    if inner.is_symlink():
        raise ValueError('N095_INNER_PATH_SYMLINK')
    if not inner.is_file() or hashlib.sha256(inner.read_bytes()).hexdigest() != digest:
        fd, stage = tempfile.mkstemp(dir=cache)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(stage, 0o444)
            os.replace(stage, inner)
        finally:
            Path(stage).unlink(missing_ok=True)
    if args.fixture_root:
        other += ['--fixture-root',str(home)]
    os.environ['N095_DELIVERY_PATH'] = str(executable)
    os.environ['N095_DELIVERY_SHA256'] = args.expected_sha256
    os.execv(sys.executable, [sys.executable,'-u',str(inner),'--expected-sha256',digest,*other])


if __name__ == '__main__':
    raise SystemExit(main())
