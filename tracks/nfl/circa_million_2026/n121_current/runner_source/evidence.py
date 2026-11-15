"""Validate immutable evidence and independently recalculate held-out forecast losses."""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
from statistics import fmean
from tempfile import NamedTemporaryFile

def wire(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def file_sha(path):
    state=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):
            state.update(chunk)
    return state.hexdigest()

def checked_name(name):
    p=PurePosixPath(name)
    if not isinstance(name,str) or not name or p.is_absolute() or '..' in p.parts or '.' in p.parts or '\\' in name or name!=p.as_posix():
        raise ValueError('Unsafe relative payload path')
    return name

def pin(h):
    if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
        raise ValueError('Invalid SHA-256')
    return h

def catalog(doc):
    raw=doc['payloads']
    if isinstance(raw,dict):
        raw=[dict(v,path=k) for k,v in raw.items()]
    if not isinstance(raw,list) or not raw:raise ValueError('Empty evidence handoff')
    items={}
    for r in raw:
        p=checked_name(r['path'])
        pin(r['sha256'])
        if p in items or not isinstance(r['bytes'],int) or r['bytes']<0 or not isinstance(r['key'],str) or not r['key']:
            raise ValueError('Duplicate or invalid evidence entry')
        items[p]=r
    return items

def checked_file(path,h,size=None):
    p=Path(path)
    if not p.is_file() or p.is_symlink() or size is not None and p.stat().st_size!=size or file_sha(p)!=h:
        raise ValueError('File failed physical integrity: '+p.name)
    return p

def safe_output(root,relative):
    dest=Path(root)/checked_name(relative)
    for part in (dest,*dest.parents):
        if part.is_symlink():raise ValueError('Unexpected symbolic link in destination')
        if part==Path(root):break
    return dest

def restore_one(root,r,download):
    p=safe_output(root,r['path'])
    if p.exists():
        checked_file(p,r['sha256'],r['bytes'])
        return {'read_remote':0,'reused':1,'new_bytes':0}
    p.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile(dir=p.parent,delete=False) as f:
        temp=Path(f.name)
        try:
            download(r['key'],f)
            f.flush();os.fsync(f.fileno())
            checked_file(temp,r['sha256'],r['bytes'])
            try:os.link(temp,p)
            except FileExistsError:checked_file(p,r['sha256'],r['bytes'])
        finally:temp.unlink(missing_ok=True)
    return {'read_remote':1,'reused':0,'new_bytes':r['bytes']}

def read_cases(p):
    raw=Path(p).read_bytes()
    if raw[:2]==b'\x1f\x8b':raw=gzip.decompress(raw)
    try:d=json.loads(raw)
    except json.JSONDecodeError:d=[json.loads(l) for l in raw.splitlines() if l]
    if isinstance(d,dict):
        for key in ('rows','cases','laws','population'):
            if isinstance(d.get(key),list):return d[key]
        raise ValueError('Case table does not contain a flat list')
    if not isinstance(d,list):raise ValueError('Case table invalid')
    return d

def score_table(rows):
    sums={};seen=set();held=0
    for r in rows:
        actual=r.get('actual')
        if actual is None:held+=1;continue
        expected=r.get('point')
        if type(actual) not in (int,float) or type(expected) not in (int,float) or not math.isfinite(actual+expected):raise ValueError('Invalid margin case')
        ident=(str(r['family']),int(r['season']),str(r['game_id']))
        if ident in seen:raise ValueError('Duplicate model/game on held-out panel')
        seen.add(ident);group=sums.setdefault(ident[:2],{})
        def add(k,v):
            if not math.isfinite(v):raise ValueError('Nonfinite loss')
            group.setdefault(k,[]).append(v)
        add('margin_mae',abs(expected-actual));add('margin_rmse',(expected-actual)**2)
        if r.get('actual_total') is not None and r.get('total_point') is not None:
            d=r['total_point']-r['actual_total'];add('total_mae',abs(d));add('total_rmse',d*d)
        for field,lo,y,key in [('pmf',r.get('grid_min'),actual,'margin'),('total_pmf',r.get('total_grid_min'),r.get('actual_total'),'total')]:
            probs=r.get(field)
            if probs is None or y is None:continue
            if type(lo)!=int or not probs or not all(isinstance(x,(int,float)) and math.isfinite(x) and x>=0 for x in probs) or abs(sum(probs)-1)>1e-8:
                raise ValueError('Invalid count distribution')
            cdf=0.;crps=0.
            for i,pp in enumerate(probs):
                cdf+=pp;crps+=(cdf-int(i+lo>=y))**2
            crps+=max(0,lo-y)+max(0,y-(lo+len(probs)-1))
            add(key+'_crps',crps)
            if key=='margin':
                aw=sum(pp for i,pp in enumerate(probs,lo) if i>0);ti=(probs[-lo] if 0<=-lo<len(probs) else 0.);ho=1-aw-ti
                cats=[aw,ti,ho];obs=0 if y>0 else 1 if y==0 else 2
                add('winner_brier3',sum((v-(j==obs))**2 for j,v in enumerate(cats)));add('winner_logloss3',-math.log(max(1e-15,cats[obs])))
    table=[]
    for (family,season),metrics in sorted(sums.items()):
        row={'family':family,'season':season,'games':len(metrics['margin_mae'])}
        for k,vs in metrics.items():
            mean=fmean(vs);row[k]=math.sqrt(mean) if k.endswith('_rmse') else mean
        table.append(row)
    return {'scope':'Independent readback of supplied adjudicated numbers; prospective rows excluded','rows':table,'graded_case_count':len(seen),'ungraded_case_count':held}
