"""Resume only historical odds after v011 CBBD rate-limit stop; no college calls."""
import argparse
import threading
import unittest
from acquire_paid_data import BudgetStop, SPORTS, emit, self_test
from continuation import Continuation, SOURCE_RUNS, SOURCE_EVENTS, request_id, continuation_tests
from current_capture import CurrentOpener, current_tests


class OddsOnly(Continuation):
    def __init__(self,args):
        super().__init__(args)
        self.completed_ids=set()
        self.opener=CurrentOpener(self.opener,self,interval=1.0)
        self.resume_source='20261016T182005Z-1999205e92'
        self.quota_check={}

    def seed(self):
        # The old job must be terminal before any new provider request.
        import boto3
        sm=boto3.client('sagemaker',region_name=self.args.region)
        status=sm.describe_processing_job(ProcessingJobName='sports-edge-lab-gap-backfill-20261016-v011')['ProcessingJobStatus']
        if status not in ('Stopped','Completed','Failed'):raise BudgetStop('predecessor_not_terminal')
        super().seed()
        for track in SPORTS:
            prefix='tracks/'+track+'/raw/the-odds-api/request-index/'
            for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.args.bucket,Prefix=prefix):
                self.time_left()
                for row in page.get('Contents',[]):
                    key=row['Key'].removeprefix(prefix)
                    if len(key)==69 and key.endswith('.json'):
                        self.completed_ids.add(key[:-5])
        self.seed_counts['existing_successful_odds_indexes']=len(self.completed_ids)
        self.phase['seed']['existing_successful_odds_indexes']=len(self.completed_ids)

    def missing(self,provider,track,endpoint,params,vintage=''):
        return request_id(provider,track,endpoint,params,vintage) not in self.completed_ids and super().missing(provider,track,endpoint,params,vintage)

    def request_cost(self,provider,endpoint,params):
        return 1 if endpoint.endswith('/events') else super().request_cost(provider,endpoint,params)

    def quota_gate(self):
        self.capture('odds','nfl','/v4/sports/americanfootball_nfl/events',{'dateFormat':'iso'},'quota_preflight',self.run_id,need_data=False)
        remaining=self.budget.snapshot()['provider_headers'].get('odds',{}).get('x-requests-remaining')
        self.quota_check={'remaining':remaining,'required':self.args.odds_credits+100000,'reserve_floor':100000}
        if not isinstance(remaining,int) or remaining<self.quota_check['required']:
            self.budget.disable('odds');raise BudgetStop('account_reserve_gate')
        self.quota_check['passed']=True

    def summary(self):
        r=super().summary()
        r.update(version='sports-edge-lab-odds-only-v037',scope='Missing historical five-track US game odds; CBBD suspended after rate limit',
            predecessor_run=self.resume_source,quota_preflight=dict(self.quota_check),
            source_requests_per_second_limit=1,college_statistics_requests_permitted=0)
        return r


def resume_tests():
    from types import SimpleNamespace
    class Tests(unittest.TestCase):
        def test_success_index_suppresses_duplicate_request(self):
            a=OddsOnly.__new__(OddsOnly);a.cache={};a.negative=set()
            a.completed_ids={request_id('odds','nfl','/odds',{'date':'2026-01-01'})}
            self.assertFalse(a.missing('odds','nfl','/odds',{'date':'2026-01-01'}))
            self.assertTrue(a.missing('odds','nfl','/odds',{'date':'2026-01-02'}))
        def test_missing_quota_fails_closed(self):
            a=OddsOnly.__new__(OddsOnly);a.args=SimpleNamespace(odds_credits=200000);a.run_id='test'
            a.capture=lambda *args,**kwargs:None
            a.budget=SimpleNamespace(snapshot=lambda:{'provider_headers':{}},disable=lambda x:None)
            with self.assertRaises(BudgetStop):a.quota_gate()
            self.assertFalse(a.quota_check.get('passed',False))
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not r.wasSuccessful():raise RuntimeError('Odds resume gate failed')
    return r.testsRun


def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');a=p.parse_args()
    tests=self_test()+continuation_tests()+current_tests()+resume_tests()
    emit('SELF_TEST_PASS',tests=tests,workload='odds-only-v037')
    if a.self_test:return 0
    a.bucket='sagemaker-sports-edge-lab-560403859723-us-west-2';a.region='us-west-2'
    a.odds_parameter='/sports-edge-lab/shared/the-odds-api/key';a.mode='odds';a.until=None
    a.odds_credits=200000;a.stats_calls=0;a.max_seconds=1800;a.max_response_mb=64;a.odds_workers=1
    a.hourly_usd=.461;a.output_dir='/opt/ml/processing/output';a.source_runs=SOURCE_RUNS;a.source_events_key=SOURCE_EVENTS
    archive=OddsOnly(a);emit('START',run_id=archive.run_id,odds_credit_ceiling=a.odds_credits,stats_call_ceiling=0)
    beat=threading.Thread(target=archive.heartbeat,daemon=True);beat.start()
    archive.safe_work('seed',archive.seed)
    if archive.phase['seed'].get('status')=='completed':
        archive.safe_work('quota',archive.quota_gate)
        if archive.quota_check.get('passed') is True:
            archive.safe_work('odds',archive.odds_gap_work)
    archive.stop.set();beat.join(timeout=10)
    return archive.finish()


if __name__=='__main__':raise SystemExit(main())
