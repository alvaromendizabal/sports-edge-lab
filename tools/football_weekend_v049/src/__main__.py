"""Finite weekend NFL vintage refresh; zero paid-provider paths are invoked."""
import argparse, copy, datetime as dt, io, json, sys, threading, time, unittest, uuid, zipfile
from pathlib import Path
from unittest import mock
import validation as v

VERSION='sports-edge-lab-football-weekend-v049'
JOB='sports-edge-lab-weekend-20261017-01-v049'
OUTPUT='/opt/ml/processing/output'
pack,sha,stamp=v.pack,v.sha,v.stamp

def check_control(c):
    if c.get('series')!='football-weekend-20261016' or c.get('scope')!=['nfl','ncaaf']:
        raise ValueError('control_scope')
    for k in ('cfbd_charged_attempts','cfbd_outstanding_reservations','cfbd_total_limit','cfbd_per_run_limit','odds_credits_limit','cbbd_requests_limit'):
        if type(c.get(k)) is not int or c[k]<0:raise ValueError('ambiguous_budget:'+k)
    if c['cfbd_total_limit']!=160 or c['cfbd_per_run_limit']!=16 or c['cfbd_charged_attempts']+c['cfbd_outstanding_reservations']>160:
        raise ValueError('budget_scope')
    if c['odds_credits_limit'] or c['cbbd_requests_limit'] or not c.get('provider_blocks',{}).get('cbbd'):
        raise ValueError('disabled_provider_scope')
    if not isinstance(c.get('runs'),list):raise ValueError('missing_run_ledger')

def ledger(store,record,initial=False):
    # Conditional update fails closed on any concurrent writer; no usage reset.
    response=store.s3.get_object(Bucket=v.fr.BUCKET,Key=v.CONTROL)
    with response['Body'] as b:c=json.loads(b.read())
    check_control(c)
    matches=[x for x in c['runs'] if x.get('job_name')==JOB]
    if initial and matches:raise ValueError('exact_job_already_recorded')
    if initial and c['provider_blocks'].get('nfl_official'):raise ValueError('nfl_provider_previously_stopped')
    if initial and any(x.get('status')=='running' for x in c['runs']):raise ValueError('overlapping_weekend_run')
    if not initial and (len(matches)!=1 or matches[0]['run_id']!=record['run_id']):raise ValueError('run_lease_mismatch')
    c['runs']=[x for x in c['runs'] if x.get('job_name')!=JOB]+[record]
    store.s3.put_object(Bucket=v.fr.BUCKET,Key=v.CONTROL,Body=pack(c),IfMatch=response['ETag'],ContentType='application/json',ServerSideEncryption='AES256')

def run(store=None,output=OUTPUT):
    cfg=json.loads(v.rd.embedded('config.json'))
    observations=json.loads(v.rd.embedded('observations.json'))
    # Select the actual latest successful NFL source receipt, not the older v042 source.
    cfg['prior_nfl_injury']=json.loads(v.rd.embedded('prior_nfl.json'))
    cfg['job_name']=JOB
    store=store or v.rd.Store()
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    prefix='shared/acquisition/football-weekend/'+run_id+'/'
    report=dict(version=VERSION,job_name=JOB,run_id=run_id,started_at=stamp(),status='running',planned_stages=1,processed_stages=0,remaining_stages=1,cfbd_attempts=0,odds_credits=0,cbbd_requests=0,nfl_source_requests=0,failed_stages=[],observations=observations,application_runtime_limit_seconds=None,report_key=prefix+'report.json')
    ledger(store,copy.deepcopy(report),initial=True)
    stop=threading.Event();lock=threading.Lock();errors=[]
    def progress(x):
        with lock:report.update(x)
    def beat():
        while not stop.wait(20):
            try:
                with lock:r=copy.deepcopy(report)
                store.put(prefix+'progress.json',pack(r));print(pack(dict(event='HEARTBEAT',at=stamp(),remaining_stages=r['remaining_stages'])).decode(),flush=True)
            except Exception as e:errors.append(type(e).__name__)
    store.put(prefix+'progress.json',pack(report))
    thread=threading.Thread(target=beat,daemon=True);thread.start()
    try:
        report['result']=v.injuries(store,cfg,run_id,progress)
        report.update(processed_stages=1,remaining_stages=0)
    except Exception as e:
        report['failed_stages'].append(dict(stage='nfl_injuries',error_type=type(e).__name__,reason=str(e)[:200]))
    finally:
        stop.set();thread.join(timeout=60)
    report.update(finished_at=stamp(),status='partial_failure' if report['failed_stages'] else 'completed_with_explicit_gaps',heartbeat_errors=errors)
    # Captured request count includes robots. A stage failure is not equated with HTTP failure.
    report['http_successes']=report['nfl_source_requests'] if not report['failed_stages'] else None
    report['http_failures']=0 if not report['failed_stages'] else None
    try:ledger(store,copy.deepcopy(report))
    except Exception as e:
        report['failed_stages'].append(dict(stage='ledger',error_type=type(e).__name__,reason=str(e)[:200]));report['status']='partial_failure'
    store.put(prefix+'report.json',pack(report));store.put(prefix+'progress.json',pack(report))
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    name='sports_edge_lab_weekend_return_'+run_id+'.zip'
    with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json',pack(report));z.writestr('resume.json',pack(dict(job_name=JOB,relaunch=False,reuse_exact_successful_cache=True)))
    raw=(out/name).read_bytes();store.put(prefix+name,raw,'application/zip')
    receipt=dict(key=prefix+name,bytes=len(raw),sha256=sha(raw))
    store.put(prefix+'return_manifest.json',pack(receipt));print(pack(dict(event='FINISHED',report_key=prefix+'report.json',status=report['status'],return_zip=receipt)).decode(),flush=True)
    return int(bool(report['failed_stages']))

class Tests(unittest.TestCase):
    def base(self):return dict(series='football-weekend-20261016',scope=['nfl','ncaaf'],cfbd_charged_attempts=0,cfbd_outstanding_reservations=0,cfbd_total_limit=160,cfbd_per_run_limit=16,odds_credits_limit=0,cbbd_requests_limit=0,provider_blocks={'cbbd':'stopped'},runs=[])
    def test_valid_budget(self):check_control(self.base())
    def test_missing_budget_closed(self):
        c=self.base();del c['cfbd_charged_attempts']
        with self.assertRaises(ValueError):check_control(c)
    def test_overspent_closed(self):
        with self.assertRaises(ValueError):check_control(dict(self.base(),cfbd_charged_attempts=161))
    def test_ambiguous_bool_closed(self):
        with self.assertRaises(ValueError):check_control(dict(self.base(),cfbd_charged_attempts=False))
    def test_odds_disabled(self):
        with self.assertRaises(ValueError):check_control(dict(self.base(),odds_credits_limit=1))
    def test_cbbd_block_required(self):
        with self.assertRaises(ValueError):check_control(dict(self.base(),provider_blocks={}))
    def test_all_provider_denials(self):
        for code in (401,402,403,429):
            f=v.PublicFetch(2,10**7,float('inf'))
            with mock.patch.object(v.nfl_current.Fetcher,'raw',side_effect=v.urllib.error.HTTPError('x',code,'denied',{},None)):
                with self.assertRaises(v.urllib.error.HTTPError):f.raw('x')
            self.assertTrue(f.blocked)
    def test_conditional_ledger_preserves_budget(self):
        s=mock.Mock();c=self.base();c['cfbd_charged_attempts']=7
        s.s3.get_object.return_value={'Body':io.BytesIO(pack(c)),'ETag':'expected'}
        ledger(s,dict(job_name=JOB,run_id='r',status='running'),True)
        args=s.s3.put_object.call_args.kwargs
        self.assertEqual(args['IfMatch'],'expected');self.assertEqual(json.loads(args['Body'])['cfbd_charged_attempts'],7)
    def test_duplicate_record_closed(self):
        s=mock.Mock();c=self.base();c['runs']=[dict(job_name=JOB,run_id='r')]
        s.s3.get_object.return_value={'Body':io.BytesIO(pack(c)),'ETag':'e'}
        with self.assertRaises(ValueError):ledger(s,dict(job_name=JOB,run_id='r2'),True)
        s.s3.put_object.assert_not_called()
    def test_entrypoint_single_zip_no_odds_or_cfbd(self):
        import tempfile
        s=mock.Mock();data={};s.put.side_effect=lambda k,b,*a:data.update({k:b})
        mod=sys.modules[__name__]
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(mod,'ledger'),mock.patch.object(v,'injuries',return_value={'rows':1}),mock.patch.object(v,'cached_odds',side_effect=AssertionError('historical audit forbidden')),mock.patch.object(v.rd.Http,'get',side_effect=AssertionError('paid call forbidden')):
            self.assertEqual(run(s,tmp),0)
            files=list(Path(tmp).glob('*.zip'));self.assertEqual(len(files),1)
            with zipfile.ZipFile(files[0]) as z:
                self.assertIsNone(z.testzip());r=json.loads(z.read('report.json'))
            self.assertEqual(r['remaining_stages'],0);self.assertEqual(r['cfbd_attempts'],0)
    def test_failure_has_unique_return(self):
        import tempfile
        mod=sys.modules[__name__];s=mock.Mock()
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(mod,'ledger'),mock.patch.object(v,'injuries',side_effect=ValueError('fixture')):
            self.assertEqual(run(s,tmp),1);self.assertEqual(len(list(Path(tmp).glob('*.zip'))),1)
    def test_friday_hash_unchanged(self):
        obs=json.loads(v.rd.embedded('observations.json'));seed=json.loads(v.rd.embedded('friday_bigten.json'))
        self.assertEqual(sha(pack(seed['rows'])),obs['bigten']['subset_sha256'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (Tests,v.Tests,v.quality.Tests,v.rd.Tests,v.fr.Tests,v.ngs_avail.Tests,v.nfl_current.Tests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():return 1
    print(pack(dict(event='SELF_TEST_PASS',tests=result.testsRun,version=VERSION,at=stamp())).decode(),flush=True)
    return 0 if args.self_test else run()

if __name__=='__main__':sys.exit(main())
