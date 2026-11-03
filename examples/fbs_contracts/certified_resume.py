"""Immutable checkpoint recovery for invented convex problems; no network.

Reuse the existing shared rational certificate without changing its mathematics.
This serialized local example is not the private football objective or runner.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import tempfile
from examples.review_lab import numerical_recovery as numerical

SCHEMA='fbs.public.invented-certified-resume.v1'

def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def pin(body):
    return {'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}

def identity(job):
    if set(job)!={'name','target','curvature','tolerance'} or not isinstance(job['name'],str) or not job['name']:
        raise ValueError('Exact invented job contract required')
    numerical.problem(job['target'],job['curvature'])
    if type(job['tolerance']) not in (int,float) or not math.isfinite(job['tolerance']) or not 0<job['tolerance']<=1e-3:
        raise ValueError('Declared finite certificate tolerance required')
    return {'schema':SCHEMA,'job':job,'source_sha256':pin(Path(__file__).read_bytes())['sha256'],
        'certificate_source_sha256':pin(Path(numerical.__file__).read_bytes())['sha256'],
        'python':platform.python_version(),'implementation':platform.python_implementation()}

def _read(path):
    raw=path.read_bytes()
    def bad(value):raise ValueError('Nonfinite JSON value')
    return raw,json.loads(raw,parse_constant=bad)

def _write_once(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:handle=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if path.read_bytes()!=body:raise ValueError('Immutable content conflict')
        return
    with os.fdopen(handle,'wb') as stream:
        stream.write(body);stream.flush();os.fsync(stream.fileno())
    if path.read_bytes()!=body:raise ValueError('Local content readback failed')

def _paths(root,contract):
    key=pin(encode(contract))['sha256']
    return Path(root)/'states'/(key+'.json'),Path(root)/'receipts'/(key+'.json')

def validate_state(state,contract):
    if set(state)!={'schema','contract','point','solver_reported_success','certificate'} or state['schema']!=SCHEMA:
        raise ValueError('Unknown state schema')
    if state['contract']!=contract:raise ValueError('Checkpoint input, code or environment identity changed')
    job=contract['job']
    check=numerical.certificate(job['target'],job['curvature'],state['point'],
        solver_success=state['solver_reported_success'],tolerance=job['tolerance'])
    if check!=state['certificate'] or not check['numerically_certified']:
        raise ValueError('Recomputed mathematical certificate rejected checkpoint')
    return check

def commit_candidate(root,job,point,*,solver_success=False,before_receipt=None):
    contract=identity(job)
    check=numerical.certificate(job['target'],job['curvature'],point,solver_success=solver_success,tolerance=job['tolerance'])
    state={'schema':SCHEMA,'contract':contract,'point':list(point),'solver_reported_success':solver_success,'certificate':check}
    validate_state(state,contract)
    state_path,receipt_path=_paths(root,contract);body=encode(state)
    _write_once(state_path,body)
    if before_receipt:before_receipt()
    receipt={'schema':SCHEMA,'contract_sha256':pin(encode(contract))['sha256'],
        'state':pin(body),'mathematical_certificate_recomputed':True}
    _write_once(receipt_path,encode(receipt))
    return receipt

def restore(root,job):
    contract=identity(job);state_path,receipt_path=_paths(root,contract)
    if not state_path.exists() and not receipt_path.exists():return None
    if not state_path.exists():raise ValueError('Receipt exists without its state')
    body,state=_read(state_path);validate_state(state,contract)
    if not receipt_path.exists():
        commit_candidate(root,job,state['point'],solver_success=state['solver_reported_success'])
        return {'state':state,'reuse':'RECOVERED_UNCOMMITTED_LOCAL_STATE','new_fit':False}
    _,receipt=_read(receipt_path)
    expected={'schema':SCHEMA,'contract_sha256':pin(encode(contract))['sha256'],
        'state':pin(body),'mathematical_certificate_recomputed':True}
    if receipt!=expected:raise ValueError('Checkpoint receipt does not bind exact state bytes')
    return {'state':state,'reuse':'VERIFIED_COMMITTED_STATE','new_fit':False}

def jobs():
    return [{'name':n,'target':t,'curvature':c,'tolerance':1e-9} for n,t,c in [
        ('invented-a',[.7,.6,-.1],[1.,1.,1.]),('invented-b',[.2,.8,.4],[1.,2.,1.]),
        ('invented-c',[.6,.1,.7],[2.,1.,3.])]]

def run(root,*,simulate_failure=False):
    result={'fresh_synthetic_solves':0,'reused_committed_states':0,'recovered_uncommitted_states':0,
        'failed_attempts':0,'units':[],'owner_football_fits':0,'predictive_qualification':False}
    for index,job in enumerate(jobs()):
        try:
            saved=restore(root,job)
            if saved:
                field='reused_committed_states' if saved['reuse']=='VERIFIED_COMMITTED_STATE' else 'recovered_uncommitted_states'
                result[field]+=1;result['units'].append({'name':job['name'],'status':saved['reuse']});continue
            if simulate_failure and index==2:
                commit_candidate(root,job,[0.,0.,0.],solver_success=True)
                raise AssertionError('Uncertified invented candidate admitted')
            solved=numerical.recover(job['target'],job['curvature'],tolerance=job['tolerance'])
            if not solved['certificate']['numerically_certified']:raise ValueError('No accepted numerical certificate')
            commit_candidate(root,job,solved['point'],solver_success=False)
            result['fresh_synthetic_solves']+=1;result['units'].append({'name':job['name'],'status':'NEW_CERTIFIED_STATE'})
        except ValueError as error:
            result['failed_attempts']+=1;result['units'].append({'name':job['name'],'status':'REJECTED','reason':str(error)})
    result['status']='PARTIAL' if result['failed_attempts'] else 'COMPLETE_INVENTED_DEMO'
    return result

def walkthrough():
    with tempfile.TemporaryDirectory() as directory:
        first=run(directory,simulate_failure=True);second=run(directory);reentry=run(directory)
    return {'fixture':'INVENTED_CONVEX_PROBLEMS_NOT_PRIVATE_FOOTBALL_OBJECTIVE','first_attempt':first,
        'recovery':second,'completed_reentry':reentry,'private_owner_recovery_success_claimed':False,
        'source_authentication':'Local content checks; real owner source authentication is a separate requirement'}

if __name__=='__main__':print(json.dumps(walkthrough(),indent=2,allow_nan=False))
