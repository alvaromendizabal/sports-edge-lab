"""Run the unmodified ASCII-wrapper module using generated inner and outer zipapps."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(items):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as out:
        for name, data in items:
            out.writestr(name, data)
    return stream.getvalue()


def main():
    source = Path(sys.argv[1]).read_bytes()
    git_body = b'blob ' + str(len(source)).encode() + bytes([0]) + source
    assert hashlib.sha1(git_body).hexdigest() == 'b2e276280a503d63316f26043a9f41ff4ecb7912'
    result_fields = {'status':'PASS', 'owner_fits':0, 'source':'synthetic fixture'}
    cli = b"""import hashlib, json, os, sys
from pathlib import Path
args=sys.argv[1:]
assert args[0]=='--expected-sha256' and hashlib.sha256(Path(sys.argv[0]).read_bytes()).hexdigest()==args[1]
assert Path(args[args.index('--fixture-root')+1]).is_dir()
assert '--generated' in args
outer=Path(os.environ['N095_DELIVERY_PATH'])
assert hashlib.sha256(outer.read_bytes()).hexdigest()==os.environ['N095_DELIVERY_SHA256']
print(json.dumps({'status':'PASS','owner_fits':0,'source':'synthetic fixture'}))
"""
    member = b'value = 42\n'
    def inner_archive(pin=None, extra=False):
        manifest = {'files':{'sample.py':{'sha256':pin or digest(member),'bytes':len(member)}}}
        entries = [('__main__.py',cli),('OVERLAY.json',json.dumps(manifest)),('sample.py',member)]
        if extra:
            entries.append(('extra.py', b'x=0'))
        return archive(entries)
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        outer=root/'generated.pyz'
        inner=inner_archive()
        def pack(data, wrong=False, extra=False):
            meta={'base64':base64.b64encode(data).decode('ascii'),'bytes':len(data),'sha256':'f'*64 if wrong else digest(data),'home':'.','cache_components':['cache']}
            items=[('__main__.py',source),('owner.json',json.dumps(meta))]
            if extra:
                items.append(('extra.py',member))
            body=archive(items)
            outer.write_bytes(body)
            return digest(body)
        def run(pin,*args):
            return subprocess.run([sys.executable,str(outer),'--expected-sha256',pin,*args],
                                  capture_output=True,text=True,timeout=15)
        def rejects(pin,error):
            result=run(pin,'--overlay-self-test')
            assert result.returncode != 0 and error in result.stderr, result.stderr
        sha=pack(inner)
        selfcheck=run(sha,'--overlay-self-test')
        assert selfcheck.returncode==0, selfcheck.stderr
        result=json.loads(selfcheck.stdout)
        assert result['status']=='PASS' and result['inner_sha256']==digest(inner) and result['external_sha256']==sha and result['owner_fits']==0
        rejects('0'*64,'N095_OUTER_DIGEST_MISMATCH')
        cache=root/'cache'/(digest(inner)+'.pyz')
        def dispatch():
            result=run(sha,'--fixture-root',str(root),'--generated')
            assert result.returncode==0, result.stderr
            assert json.loads(result.stdout)==result_fields
            assert cache.read_bytes()==inner
        dispatch()
        previous=(cache.stat().st_ino,cache.stat().st_mtime_ns)
        dispatch()
        assert (cache.stat().st_ino,cache.stat().st_mtime_ns)==previous
        cache.chmod(0o600)
        cache.write_bytes(b'generated corruption')
        dispatch()
        rejects(pack(inner,wrong=True),'N095_INNER_DIGEST_MISMATCH')
        rejects(pack(inner_archive(pin='0'*64)),'N095_OVERLAY_MEMBER_HASH_MISMATCH')
        rejects(pack(inner_archive(extra=True)),'N095_BAD_OVERLAY_MEMBERSHIP')
        rejects(pack(inner,extra=True),'N095_OUTER_MEMBERSHIP_MISMATCH')
        print(json.dumps({'status':'PASS','runtime':sys.version.split()[0],'owner_fits':0,
                          'exact_wrapper_blob':'b2e276280a503d63316f26043a9f41ff4ecb7912',
                          'self_check':True,'cold_dispatch':True,'warm_cache_preserved':True,
                          'cache_repair':True,'digest_or_membership_rejections':5,'synthetic_inputs':True,
                          'full_private_distributable_executed':False},sort_keys=True))


if __name__=='__main__':
    main()
