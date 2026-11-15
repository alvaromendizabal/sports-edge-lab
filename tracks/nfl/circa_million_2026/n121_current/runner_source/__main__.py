"""Restore an authorized immutable research handoff and seal an independently checked native return."""
import argparse
import base64
from contextlib import closing
import concurrent.futures
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import tempfile
import threading
import time
import zipfile
from evidence import catalog,checked_file,file_sha,pin,read_cases,restore_one,safe_output,score_table,sha,wire

def offline():
    from io import BytesIO
    row={'family':'baseline','season':1,'game_id':'a','actual':1,'point':0,'actual_total':2,'total_point':3,'pmf':[.25,.5,.25],'grid_min':-1}
    q=score_table([row,dict(row,game_id='b',actual=None)])
    if q['graded_case_count']!=1 or q['ungraded_case_count']!=1 or q['rows'][0]['margin_mae']!=1 or abs(q['rows'][0]['margin_crps']-.625)>1e-12:raise ValueError('Independent scoring failed')
    def reject(fn):
        try:fn()
        except (ValueError,KeyError):return
        raise AssertionError('Invalid fixture was accepted')
    reject(lambda:score_table([row,row]))
    reject(lambda:score_table([dict(row,pmf=[1.,2.])]))
    payload=b'actual test input';entry={'path':'input/data','key':'raw','sha256':sha(payload),'bytes':len(payload)}
    reject(lambda:catalog({'payloads':[entry,entry]}));reject(lambda:catalog({'payloads':[dict(entry,path='../bad')]}))
    with tempfile.TemporaryDirectory() as t:
        p=Path(t);calls=[]
        def obtain(k,f):calls.append(k);f.write(payload)
        if restore_one(p,entry,obtain)['read_remote']!=1 or restore_one(p,entry,obtain)['reused']!=1 or calls!=['raw']:raise ValueError('Verified warm readback failed')
        (p/entry['path']).write_bytes(b'X'*len(payload));reject(lambda:restore_one(p,entry,obtain))
        reject(lambda:restore_one(p,dict(entry,path='other',sha256='0'*64),obtain))
        if (p/'other').exists():raise ValueError('Interrupted verification committed')
        file=BytesIO()
        with zipfile.ZipFile(file,'w') as archive:
            archive.writestr('data',payload);archive.writestr('RETURN_MANIFEST.json',wire({'files':{'data':{'sha256':sha(payload),'bytes':len(payload)}}}))
        data=file.getvalue();pieces=[]
        for i,chunk in enumerate([data[:40],data[40:100],data[100:]]):
            fn='part'+str(i);(p/fn).write_bytes(chunk);pieces.append({'filename':fn,'bytes':len(chunk),'sha256':sha(chunk)})
        doc={'parts':pieces,'logical_zip':{'filename':'result.zip','sha256':sha(data),'bytes':len(data)}};save(p/'parts.json',doc)
        rr=assemble(p/'parts.json',None,file_sha(p/'parts.json'))
        if rr['payloads']!=1 or rr['parts']!=3:raise ValueError('Multipart assembly failure')
        (p/'part1').write_bytes(b'X'*pieces[1]['bytes']);reject(lambda:assemble(p/'parts.json',None,None))
        (p/'part1').unlink();reject(lambda:assemble(p/'parts.json',None,None))
    with zipfile.ZipFile(sys.argv[0]) as z:
        if z.testzip():raise ValueError('Executable integrity failed')
    print(json.dumps({'status':'PASS','checks':['python_zipapp_start','complete_zip_crc','reconstruct_case_losses','exclude_unsettled','duplicate_game_rejected','invalid_distribution_rejected','duplicate_evidence_rejected','path_traversal_rejected','warm_no_download','same_size_corruption_rejected','failed_download_no_commit','three_piece_assembly','missing_part_rejected','corrupt_part_rejected']}))
    return 0

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
        name=f.name;f.write(wire(data));f.flush();os.fsync(f.fileno())
    os.replace(name,path)

def read(path):
    return json.loads(path.read_bytes())

def run(a):
    from botocore.config import Config
    from botocore.exceptions import ClientError
    import boto3
    program=Path(sys.argv[0]).absolute();checked_file(program,pin(a.expected_sha256))
    for v in (a.owner,a.release,a.resume_run):
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,100}',v):raise ValueError('Invalid run, release or owner')
    home=Path(a.home).absolute();project=home/'sports-edge-lab-work'/a.owner
    if not project.is_dir():raise ValueError('Existing owner workspace is required')
    cache=project/'cache'/a.release.lower();state=project/'checkpoints'/a.release.lower()/a.resume_run
    out=project/'runs'/(a.release+'_'+a.resume_run);inputs=out/'verified_handoff'
    for p in (cache,state,out,inputs):p.mkdir(parents=True,exist_ok=True)
    client=boto3.client('s3',region_name=a.region,config=Config(retries={'total_max_attempts':3,'mode':'standard'}))
    aws={'get':0,'head':0,'put':0,'sent_bytes':0,'received_bytes':0};mu=threading.Lock()
    def plus(k,v=1):
        with mu:aws[k]+=v
    def get(k,file):
        q=client.get_object(Bucket=a.bucket,Key=k,ExpectedBucketOwner=a.owner_id);plus('get');plus('received_bytes',q['ContentLength'])
        with closing(q['Body']) as body:shutil.copyfileobj(body,file,1<<20)
    def fetch(k,dst,sha256):
        if dst.exists():return checked_file(dst,sha256)
        dst.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as f:
            tmp=Path(f.name)
            try:
                get(k,f);f.flush();os.fsync(f.fileno());checked_file(tmp,sha256)
                try:os.link(tmp,dst)
                except FileExistsError:checked_file(dst,sha256)
            finally:tmp.unlink(missing_ok=True)
        return dst
    def put(path,key,h):
        size=path.stat().st_size;ck=base64.b64encode(bytes.fromhex(h)).decode();kw=dict(Bucket=a.bucket,Key=key,ExpectedBucketOwner=a.owner_id)
        def head():
            plus('head')
            try:return client.head_object(**kw,ChecksumMode='ENABLED')
            except ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode']==404:return None
                raise
        q=head()
        if q is None:
            try:
                with path.open('rb') as f:
                    plus('put');client.put_object(**kw,Body=f,ContentLength=size,ChecksumSHA256=ck,IfNoneMatch='*');plus('sent_bytes',size)
            except ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode']!=412:raise
            q=head()
        if not q or q['ContentLength']!=size or q.get('ChecksumSHA256')!=ck:raise ValueError('S3 revalidation failed')
        return dict(key=key,bytes=size,sha256=h)
    runtime=fetch(a.runtime_key,cache/'runtime'/(pin(a.runtime_sha256)+'.pyz'),a.runtime_sha256)
    names=a.modules.split(',')
    if len(names)!=6 or any(not re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*',n) for n in names):raise ValueError('Supply the six authenticated runtime module names')
    sys.path.append(str(runtime))
    tr,cap,cost,helper,proofs,sig=[importlib.import_module(n) for n in names]
    identity={'program':a.expected_sha256,'runtime':a.runtime_sha256,'handoff':pin(a.manifest_sha256),'run':a.resume_run,'release':a.release}
    budget=cost.Budget(cost.current_basis(),a.max_compute_usd,time.monotonic()) if not (state/'COMPLETE.json').exists() else None
    stop=threading.Event()
    for s in (signal.SIGINT,signal.SIGTERM):signal.signal(s,lambda *_:stop.set())
    with helper.locked(cache/'ACTIVE_OWNER.lock',False):
        prior=proofs.read_proof(state/'COMPLETE.json',cache)
        if prior:
            if prior['identity']!=identity:raise ValueError('Immutable completion identity changed')
            for it in prior['archive']['parts']:checked_file(home/it['filename'],it['sha256'],it['bytes'])
            if prior['archive'].get('manifest_path'):checked_file(prior['archive']['manifest_path'],prior['archive']['manifest_sha256'])
            print(json.dumps({'status':'REUSED_NATIVE_RETURN','program_scope':prior['scope'],'logical_sha256':prior['archive']['logical_zip_sha256'],'path':prior['archive']['path'],'new_fits':0,'new_issues':0,'s3':aws}));return 0
        if (state/'COMPLETE.json').exists():raise ValueError('Cannot authenticate completion')
        if budget is None:raise ValueError('Prior completion disappeared')
        mf=fetch(a.manifest_key,cache/'handoffs'/(a.manifest_sha256+'.json'),a.manifest_sha256)
        doc=read(mf);items=catalog(doc)
        if doc.get('release',a.release)!=a.release or doc.get('owner',a.owner).lower()!=a.owner.lower():raise ValueError('Manifest owner or release differs')
        scope='Native materialization and independent evaluation of retained research; every original fit and issue retains its recorded time and host.'
        mon=helper.Monitor(project,a.resume_run);mon.io=project/'logs'/(a.release+'_'+a.resume_run);mon.io.mkdir(parents=True,exist_ok=True);mon.budget=budget;mon.begin()
        try:
            with cap.owner_lease(home,project=a.owner,run_id=a.resume_run,requested=a.cores,budget_gate=budget.check,stop_requested=stop.is_set,memory_bytes=(1024+180*a.cores)<<20) as lease:
                cpus,_,restore=cap.bind_owner_threads(lease.granted);lease.mark_launch_started();mon.lease=len(cpus)
                try:
                    pending=proofs.read_proof(state/'PENDING_DURABILITY.json',cache)
                    if pending:
                        if pending['identity']!=identity:raise ValueError('Pending release identity differs')
                        archive=pending['archive'];summary=pending['summary']
                        for it in archive['parts']:checked_file(home/it['filename'],it['sha256'],it['bytes'])
                    else:
                        tr.admit_work(project,sum(v['bytes'] for v in items.values() if not safe_output(inputs,v['path']).exists())+(8<<20))
                        mon.update('verification',remaining=len(items));records={}
                        def load_pair(pair):
                            name,entry=pair
                            if stop.is_set() or not budget.check()['admitted']:return name,None
                            return name,restore_one(inputs,entry,get)
                        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(len(cpus),8))) as pool:
                            for name,row in pool.map(load_pair,sorted(items.items())):
                                if row is not None:records[name]=row
                        missing=sorted(set(items)-set(records))
                        summary={'schema':'verified_research_native_readback.v1','execution_location':'SageMaker','scope':scope,'release':a.release,'run_id':a.resume_run,'parent_handoff_sha256':a.manifest_sha256,'upstream_scientific_status':doc.get('scientific_status',doc.get('status','UNSPECIFIED')),'observed_payloads':len(records),'files_reused':sum(r['reused'] for r in records.values()),'source_bytes_downloaded':sum(r['new_bytes'] for r in records.values()),'missing_payloads':missing,'evaluation_tables':[],'new_native_fits':0,'new_native_issues':0,'promotions':0,'orders':0,'official_entries':0}
                        save(out/'evidence_manifest.json',doc)
                        patterns=a.case_path or doc.get('native_case_tables',[]) or [n for n in sorted(records) if n.rsplit('/',1)[-1].endswith('_FULL_LAWS.json.gz')]
                        for i,name in enumerate(patterns):
                            if name not in records:continue
                            score=score_table(read_cases(safe_output(inputs,name)))
                            if score['graded_case_count']==0:continue
                            score.update(case_path=name,source_sha256=items[name]['sha256']);save(out/'native_audit'/('season_scores_'+str(i)+'.json'),score)
                            summary['evaluation_tables'].append({'path':name,'graded_cases':score['graded_case_count'],'prospective_excluded':score['ungraded_case_count']})
                        summary['native_status']='PARTIAL_RESUMABLE' if missing else 'NATIVE_EVIDENCE_READBACK_COMPLETE'
                        save(out/'NATIVE_RESEARCH_READBACK.json',summary)
                        mon.update('sealing',verified=len(records));shutil.copyfile(mon.io/'execution.jsonl',out/'NATIVE_HEARTBEATS.jsonl');key=a.resume_run if not missing else a.resume_run+'_partial_'+str(time.time_ns())
                        archive=tr.seal_logical_return(out,home,key,a.owner,metadata={'release':a.release,'scientific_status':summary['upstream_scientific_status'],'status':summary['native_status'],'execution_location':'SageMaker','research_origin_retained':True},extra_files={'executable/'+program.name:program},compression_workers=len(cpus),cache_dir=cache/'return_transport')
                        if not missing:sig.signed(state/'PENDING_DURABILITY.json',dict(identity=identity,archive=archive,summary=summary),cache)
                    objects=[]
                    for it in archive['parts']:
                        objects.append(put(home/it['filename'],a.output_prefix.rstrip('/')+'/objects/'+it['sha256'],it['sha256']))
                    if archive.get('manifest_path'):
                        path=Path(archive['manifest_path']);objects.append(put(path,a.output_prefix.rstrip('/')+'/objects/'+archive['manifest_sha256'],archive['manifest_sha256']))
                    rec=dict(identity=identity,scope=scope,archive=archive,summary=summary,objects=objects)
                    ix=state/(archive['logical_zip_sha256']+'.json');save(ix,rec);put(ix,a.output_prefix.rstrip('/')+'/native-readbacks/'+archive['logical_zip_sha256']+'.json',file_sha(ix))
                    if not summary['missing_payloads']:sig.signed(state/'COMPLETE.json',rec,cache)
                    print(json.dumps({'status':summary['native_status'],'logical_sha256':archive['logical_zip_sha256'],'path':archive['path'],'physical_parts':archive['parts'],'s3':aws,'new_native_fits':0,'new_native_issues':0}));return 3 if summary['missing_payloads'] else 0
                finally:restore()
        finally:mon.stop()

def assemble(manifest,target,pinned):
    from evidence import checked_name
    m=Path(manifest).absolute()
    if pinned:checked_file(m,pin(pinned))
    d=read(m);meta=d['logical_zip'];items=d['parts'];pins=[]
    for row in items:
        name=checked_name(row['filename'])
        if '/' in name:raise ValueError('Part outside manifest directory')
        part=checked_file(m.parent/name,pin(row['sha256']),row['bytes']);pins.append(part)
    dst=Path(target).absolute() if target else safe_output(m.parent,meta['filename'])
    if dst.exists():checked_file(dst,meta['sha256'],meta['bytes'])
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as f:
            t=Path(f.name)
            try:
                for part in pins:
                    with part.open('rb') as chunk:shutil.copyfileobj(chunk,f,1<<20)
                f.flush();os.fsync(f.fileno());checked_file(t,meta['sha256'],meta['bytes'])
                try:os.link(t,dst)
                except FileExistsError:checked_file(dst,meta['sha256'],meta['bytes'])
            finally:t.unlink(missing_ok=True)
    with zipfile.ZipFile(dst) as z:
        before=read_archive_manifest(z)
        if z.testzip():raise ValueError('Broken archive CRC')
        for name,r in before.items():
            with z.open(name) as source:
                import hashlib
                if hashlib.file_digest(source,'sha256').hexdigest()!=r['sha256'] or z.getinfo(name).file_size!=r['bytes']:raise ValueError('Bad payload '+name)
    return {'status':'ASSEMBLED_READBACK_OK','path':str(dst),'parts':len(items),'payloads':len(before),'sha256':meta['sha256']}

def read_archive_manifest(z):
    d=json.loads(z.read('RETURN_MANIFEST.json'))['files']
    if set(d)|{'RETURN_MANIFEST.json'}!=set(z.namelist()) or len(z.namelist())!=len(set(z.namelist())):raise ValueError('ZIP membership mismatch')
    return d

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true');p.add_argument('--cores',type=int,choices=range(1,13),default=12);p.add_argument('--max-compute-usd',type=float,default=200)
    p.add_argument('--assemble-return',type=Path);p.add_argument('--assemble-to','--output',type=Path);p.add_argument('--expected-manifest-sha256');p.add_argument('--home',default='/home/sagemaker-user');p.add_argument('--case-path',action='append')
    for n in ('bucket','owner-id','region','manifest-key','manifest-sha256','runtime-key','runtime-sha256','modules','resume-run','release','owner','expected-sha256','output-prefix'):p.add_argument('--'+n)
    a=p.parse_args()
    if a.self_test:return offline()
    if a.assemble_return:print(json.dumps(assemble(a.assemble_return,a.assemble_to,a.expected_manifest_sha256)));return 0
    if any(getattr(a,n) is None for n in ('bucket','owner_id','region','manifest_key','manifest_sha256','runtime_key','runtime_sha256','modules','resume_run','release','owner','expected_sha256','output_prefix')):p.error('Native execution requires all input identities, the owner, and a private output prefix')
    return run(a)
if __name__=='__main__':sys.exit(main())
