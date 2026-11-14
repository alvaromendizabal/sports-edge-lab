"""N095 owner bootstrap. Reuse the verified local owner cache or recover two pinned S3 objects once."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import zipfile

from n095_bootstrap_config import (BUCKET, PREVIOUS, NEWEST, PARENT_NAME, RETURN_NAME, OBJECTS, BASELINES,
    STAMP, REGION, EXPECTED_OWNER, PROJECT_REL, HOME_PATH, CACHE_REL, AUTH_REL, OLD_RETURN_GUARD, NEW_RETURN_GUARD)

def pin(path):
    with open(path,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def identity(p):
    s=p.stat()
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode]

def safe(path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('N095_UNSAFE_SYMLINK:'+str(path))
    return path

def ensure_pinned(path,digest,size):
    before=identity(path)
    if before[2]!=size or pin(path)!=digest or before!=identity(path):
        raise ValueError('N095_PIN_MISMATCH:'+str(path))

def atomic(path,data):
    fd,n=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(n,path)
    finally:
        Path(n).unlink(missing_ok=True)

def recover(home,project,cache,spec,fixture):
    name,digest,size,key=spec
    choices=[home/name,project.joinpath(*AUTH_REL,digest,name),cache/name]
    for p in choices:
        safe(p)
        if p.is_file():
            ensure_pinned(p,digest,size)
            return p,0
    if fixture:
        raise FileNotFoundError('N095_FIXTURE_REQUIRES_LOCAL_PINNED_OBJECT:'+name)
    import boto3
    from botocore.config import Config
    client=boto3.Session(region_name=REGION).client('s3',config=Config(connect_timeout=5,read_timeout=60,retries={'total_max_attempts':3,'mode':'standard'}))
    stamp=time.monotonic()
    print('N095_RECOVERY_BEGIN '+name,flush=True)
    response=client.get_object(Bucket=BUCKET,Key=key,ExpectedBucketOwner=EXPECTED_OWNER)
    stream=response['Body'];fd,tmp=tempfile.mkstemp(dir=cache)
    try:
        with os.fdopen(fd,'wb') as dest:
            count=0
            while True:
                chunk=stream.read(4*1024**2)
                if not chunk:break
                count+=len(chunk)
                if count>size:raise ValueError('N095_RECOVERY_EXCESS_LENGTH')
                dest.write(chunk)
                if time.monotonic()-stamp>=10:
                    print('N095_RECOVERY '+name+' '+str(count)+'/'+str(size),flush=True);stamp=time.monotonic()
            dest.flush();os.fsync(dest.fileno())
        ensure_pinned(Path(tmp),digest,size);os.chmod(tmp,0o444);os.replace(tmp,cache/name)
        return cache/name,count
    finally:
        stream.close();Path(tmp).unlink(missing_ok=True)

def canon(v):
    return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()

def build(parent,latest,overlay,dest):
    # Copy already compressed parental members and append a new central directory.
    # Existing archived implementation bytes remain accessible under original names.
    shutil.copyfile(parent,dest)
    with zipfile.ZipFile(overlay) as patch,zipfile.ZipFile(latest) as ret,zipfile.ZipFile(dest,'a',allowZip64=True) as out:
        old=json.loads(out.read('N094_CODE_MANIFEST.json'))['files']
        prior=json.loads(out.read('N094_RECOVERY_MANIFEST.json'))
        newest=json.loads(ret.read('RETURN_MANIFEST.json'))
        if newest.get('release')!='N094' or newest.get('identity',{}).get('project')!='nfl' or newest.get('fixture') is not False:
            raise ValueError('N095_REQUIRES_ACTUAL_N094_RETURN')
        patches=json.loads(patch.read('OVERLAY.json'))['files']
        previous_roles=prior['files']
        replaced={'__main__.py','N094_CODE_MANIFEST.json','N094_RECOVERY_MANIFEST.json'}
        replaced.update(r['member'] for r in previous_roles if r['role'] in BASELINES)
        filtered=[i for i in out.filelist if i.filename not in replaced]
        out.filelist=filtered;out.NameToInfo={i.filename:i for i in filtered};out._didModify=True
        pins={n:q for n,q in old.items() if n not in replaced}
        roles=[{**r,'role':'return_prior_n093' if r['role']=='return_current' else r['role']} for r in previous_roles if r['role'] not in BASELINES]
        def append(name,stream,expected,stored=False):
            if name in out.NameToInfo:
                raise ValueError('N095_DUPLICATE_COMBINED_MEMBER:'+name)
            info=zipfile.ZipInfo(name,STAMP);info.compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            h=hashlib.sha256();length=0
            with out.open(info,'w',force_zip64=True) as f:
                for b in iter(lambda:stream.read(1024**2),b''):
                    length+=len(b);h.update(b);f.write(b)
            found={'sha256':h.hexdigest(),'bytes':length}
            if expected and found!=expected:raise ValueError('N095_MEMBER_MISMATCH:'+name)
            pins[name]=found
            return found
        import io
        def bytes_member(name,data):
            return append(name,io.BytesIO(data),None)
        name='recovery/return_current_n094/'+RETURN_NAME
        with latest.open('rb') as stream:
            q=append(name,stream,{'sha256':NEWEST,'bytes':OBJECTS[1][2]},True)
        roles.insert(0,{'role':'return_current','member':name,**q})
        for role,member in BASELINES.items():
            name='recovery/'+role+'/'+Path(member).name
            with ret.open(member) as stream:q=append(name,stream,newest['files'][member])
            roles.append({'role':role,'member':name,**q})
        for name,q in patches.items():
            with patch.open(name) as stream:append(name,stream,q)
        durable=out.read('n094_durable.py').decode('utf-8')
        old_guard="path.name.startswith("+repr(OLD_RETURN_GUARD)+")"
        if durable.count(old_guard)!=1:raise ValueError('N095_DURABILITY_PARENT_CONTRACT_CHANGED')
        durable=durable.replace(old_guard,"path.name.startswith("+repr(NEW_RETURN_GUARD)+")").replace("'release':'N094'","'release':'N095'")
        bytes_member('n095_durable.py',durable.encode('utf-8'))
        bytes_member('__main__.py',b"if __name__ == '__main__':\n    from n095_runner import main\n    raise SystemExit(main())\n")
        bytes_member('N095_RECOVERY_MANIFEST.json',canon({'release':'N095','owner':'nfl','files':roles,'newest_executed_return_sha256':NEWEST,'predecessor_package_sha256':PREVIOUS}))
        code=canon({'release':'N095','owner':'nfl','project':'nfl','active_policy':'V11.1','training_authorized':True,'automatic_promotion':False,'files':pins})
        bytes_member('N095_CODE_MANIFEST.json',code)
    with zipfile.ZipFile(dest) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(pins):
            raise ValueError('N095_COMBINED_MEMBERSHIP_MISMATCH')
        for name in ['__main__.py',*patches]:
            if name.endswith('.py'):compile(z.read(name),name,'exec')
        for name in ['N095_RECOVERY_MANIFEST.json','N095_CODE_MANIFEST.json',*patches]:
            if hashlib.sha256(z.read(name)).hexdigest()!=pins[name]['sha256']:
                raise ValueError('N095_COMBINED_READBACK_MISMATCH:'+name)
    return pin(dest)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--fixture-root',type=Path)
    parser.add_argument('--overlay-self-test',action='store_true')
    args,other=parser.parse_known_args()
    overlay=safe(Path(sys.argv[0]).absolute())
    if pin(overlay)!=args.expected_sha256:raise ValueError('N095_OVERLAY_SHA256_MISMATCH')
    with zipfile.ZipFile(overlay) as z:
        manifest=json.loads(z.read('OVERLAY.json'))
        if set(z.namelist())!=set(manifest['files'])|{'__main__.py','OVERLAY.json'}:raise ValueError('N095_OVERLAY_MEMBERSHIP')
        for n,v in manifest['files'].items():
            b=z.read(n)
            if len(b)!=v['bytes'] or hashlib.sha256(b).hexdigest()!=v['sha256']:raise ValueError('N095_OVERLAY_MEMBER:'+n)
            if n.endswith('.py'):compile(b,n,'exec')
    if args.overlay_self_test:
        print(json.dumps({'status':'PASS','test':'N095_OVERLAY_EXTERNAL_SHA_MEMBER_SHA_CRC_AND_PYTHON_COMPILE','owner_fits':0}));return 0
    home=safe(args.fixture_root.absolute() if args.fixture_root else Path(HOME_PATH))
    if not args.fixture_root and not home.is_dir():raise ValueError('N095_EXPECTED_EXISTING_OWNER_HOME')
    project=safe(home.joinpath(*PROJECT_REL))
    cache=safe(project.joinpath(*CACHE_REL));cache.mkdir(parents=True,exist_ok=True)
    key=args.expected_sha256;dest=safe(cache/('owner_'+key+'.pyz'));proof=safe(cache/(key+'.proof.json'))
    # Key and proof are external to the returned artifact and protected against
    # stale/corrupt substitution. Warm starts verify continuity without re-downloading.
    import hmac,secrets
    with safe(cache/'prepare.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        keyfile=safe(cache/'.proof_key')
        if not keyfile.exists():
            atomic(keyfile,secrets.token_bytes(32))
        if keyfile.stat().st_mode&0o077:raise ValueError('N095_BOOTSTRAP_KEY_PERMISSIONS')
        secret=keyfile.read_bytes();prev={}
        if proof.is_file():
            try:
                signed=json.loads(proof.read_bytes());payload=signed['payload']
                if hmac.compare_digest(signed['hmac_sha256'],hmac.new(secret,canon(payload),'sha256').hexdigest()):prev=payload
            except (ValueError,KeyError,TypeError):pass
        if dest.is_file() and prev.get('identity')==identity(dest) and prev.get('overlay')==key:
            combined=prev['sha256'];download=0;reused=True
        else:
            p,b1=recover(home,project,cache,OBJECTS[0],bool(args.fixture_root))
            r,b2=recover(home,project,cache,OBJECTS[1],bool(args.fixture_root))
            fd,tmp=tempfile.mkstemp(dir=cache);os.close(fd)
            try:
                combined=build(p,r,overlay,Path(tmp))
                os.chmod(tmp,0o444);os.replace(tmp,dest)
                value={'overlay':key,'sha256':combined,'identity':identity(dest)}
                atomic(proof,canon({'payload':value,'hmac_sha256':hmac.new(secret,canon(value),'sha256').hexdigest()}))
            finally:
                Path(tmp).unlink(missing_ok=True)
            download=b1+b2;reused=False
    print(json.dumps({'phase':'N095_VERIFIED_COMBINED_OWNER_EXECUTABLE','overlay_sha256':key,'combined_sha256':combined,'authenticated_warm_reuse':reused,'cold_s3_body_bytes':download}),flush=True)
    if args.fixture_root:other+=['--fixture-root',str(home)]
    os.environ['N095_BOOTSTRAP_PATH']=str(overlay)
    os.environ['N095_BOOTSTRAP_SHA256']=key
    os.environ['N095_BOOTSTRAP_DOWNLOADED_BYTES']=str(download)
    os.execv(sys.executable,[sys.executable,'-u',str(dest),'--expected-sha256',combined,*other])

if __name__=='__main__':
    raise SystemExit(main())
