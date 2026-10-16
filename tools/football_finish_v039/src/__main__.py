"""Finite football collection: run to queue completion, with no application timer."""
import argparse
import collections
import datetime as dt
import json
import signal
import sys
import threading
import time
import unittest
import urllib.error
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from acquire_paid_data import Archive, Budget, BudgetStop, SPORTS, blob, digest, emit, iso, parse, self_test
from continuation import Continuation, SOURCE_RUNS, SOURCE_EVENTS, request_id, continuation_tests
from current_capture import current_tests
from odds_resume import OddsOnly, resume_tests, validate_predecessor
import nfl_current

TRACKS = ('nfl', 'ncaaf')
VERSION = 'sports-edge-lab-football-finish-v039'
JOB = 'sports-edge-lab-football-finish-20261016-v039'
AWS_MAX_SECONDS = 432000
RESERVE_FLOOR = 100000
CREDIT_LIMIT = 200000
FROZEN_CUTOFF = '2026-10-16T18:10:06Z'


def scope_allowed(provider, track, endpoint, params):
    if provider != 'odds' or track not in TRACKS:
        return False
    if track == 'nfl' and endpoint == '/v4/sports/americanfootball_nfl/events':
        return params == {'dateFormat': 'iso'}
    expected = '/v4/historical/sports/' + SPORTS[track][0] + '/odds'
    return (endpoint == expected and set(params) == {'date', 'markets', 'regions', 'oddsFormat', 'dateFormat'}
            and params['markets'] == 'h2h,spreads,totals' and params['regions'] == 'us'
            and params['oddsFormat'] == 'decimal' and params['dateFormat'] == 'iso'
            and parse(params['date']) <= parse(FROZEN_CUTOFF))


def build_plan(events, missing, cutoff):
    tasks, counts = [], {}
    for track in TRACKS:
        first = parse(SPORTS[track][1] + 'T00:00:00Z')
        targets = set()
        for row in events.get(track, {}).values():
            kickoff = parse(row['commence_time'])
            targets.update(kickoff - dt.timedelta(minutes=m) for m in (15, 360, 1440, 4320)
                           if first <= kickoff - dt.timedelta(minutes=m) <= cutoff)
        endpoint = '/v4/historical/sports/' + SPORTS[track][0] + '/odds'
        selected = []
        for target in sorted(targets, reverse=True):
            params = {'date': iso(target), 'markets': 'h2h,spreads,totals', 'regions': 'us',
                      'oddsFormat': 'decimal', 'dateFormat': 'iso'}
            if missing('odds', track, endpoint, params):
                selected.append((track, target, 'football_historical_game_prices'))
        counts[track] = len(selected)
        tasks.extend(selected)
    return tasks, counts


class FootballFinish(OddsOnly):
    def __init__(self, args):
        super().__init__(args)
        self.deadline = float('inf')
        self.tasks = []
        self.task_ids = set()
        self.public_report = {}
        self.plan_counts = {}
        self.end = parse(FROZEN_CUTOFF)

    def time_left(self):
        if self.stop.is_set():
            raise BudgetStop('external_stop_requested')

    def capture(self, provider, track, endpoint, params, label, vintage='', need_data=True):
        if not scope_allowed(provider, track, endpoint, params):
            raise ValueError('outside_approved_football_scope')
        result = super().capture(provider, track, endpoint, params, label, vintage, need_data)
        if result is not None:
            self.completed_ids.add(request_id(provider, track, endpoint, params, vintage))
        # Check every available live header, not just the initial quota gate.
        remaining = self.budget.snapshot()['provider_headers'].get('odds', {}).get('x-requests-remaining')
        if isinstance(remaining, int) and remaining < RESERVE_FLOOR + 30:
            self.budget.disable('odds')
            raise BudgetStop('live_account_reserve_floor')
        return result

    def seed(self):
        with zipfile.ZipFile(sys.argv[0]) as z:
            proof = json.loads(z.read('predecessor_terminal.json'))
        validate_predecessor(proof)
        self.phase['predecessor'] = {'status': 'terminal_verified', 'evidence': proof}
        # Original successful receipts survive even though the stopped v011 had
        # no final summary. Its immutable successful indexes are authoritative.
        Continuation.seed(self)
        for track in TRACKS:
            prefix = 'tracks/' + track + '/raw/the-odds-api/request-index/'
            for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.args.bucket, Prefix=prefix):
                self.time_left()
                for row in page.get('Contents', []):
                    key = row['Key'].removeprefix(prefix)
                    if len(key) == 69 and key.endswith('.json'):
                        self.completed_ids.add(key[:-5])
        # Keep the same event universe and cutoff as v011 to avoid adding scope.
        self.tasks, self.plan_counts = build_plan(self.events, self.missing, self.end)
        self.seed_counts['existing_successful_football_indexes'] = len(self.completed_ids)
        self.phase['plan'] = {'status': 'frozen', 'missing_by_track': self.plan_counts,
                              'planned': len(self.tasks), 'planned_nominal_credits': len(self.tasks) * 30,
                              'cutoff': FROZEN_CUTOFF, 'markets': ['h2h', 'spreads', 'totals']}
        if len(self.tasks) * 30 + 30 > self.args.odds_credits:
            raise BudgetStop('finite_queue_exceeds_existing_credit_authorization')
        self.save_json('shared/acquisition/paid/' + self.run_id + '/plan.json', self.serialized_plan())
        self.checkpoint()
        emit('PLAN_FROZEN', run_id=self.run_id, **self.phase['plan'])

    def serialized_plan(self):
        return [{'track': track, 'target': iso(target), 'purpose': label} for track, target, label in self.tasks]

    def work(self):
        self.process(self.tasks, self.game_checkpoint, 'football_game_odds', 1)
        self.checkpoint()

    def refresh_availability(self):
        # NFL reports change during Friday. Only the current injury report is
        # requested; all 32 already captured roster pages and schedule are reused.
        report = {'run_id': self.run_id, 'capture_vintage': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:00Z'),
                  'captured': [], 'evidence': [], 'status': 'running', 'point_in_time_approved': False}
        self.public_report = report
        fetcher = nfl_current.Fetcher(2, 9000000, float('inf'))
        store = nfl_current.Store(self.args.bucket, self.args.region)
        try:
            _, receipt = nfl_current.capture(store, fetcher, nfl_current.SEEDS[0]['url'], 'injuries', report)
            report['captured'].append(receipt)
            report['status'] = 'current_report_captured_or_reused'
        except (nfl_current.BoundedStop, urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            report.update(status='source_unavailable', error_type=type(exc).__name__)
            if isinstance(exc, urllib.error.HTTPError):
                report['http_status'] = exc.code
        report.update(source_requests=fetcher.calls, source_bytes=fetcher.bytes)
        report['ncaa_note'] = 'Existing Big Ten capture retained; American Conference reports are acquired by the existing release-window schedule. No unpublished report assumed available.'
        self.phase['availability'] = {'status': report['status'], 'source_requests': fetcher.calls,
                                      'captured_pages': len(report['captured'])}
        self.save_json('shared/acquisition/paid/' + self.run_id + '/availability.json', report)
        emit('AVAILABILITY', run_id=self.run_id, **self.phase['availability'])

    def summary(self):
        r = super().summary()
        phase = r['phases'].get('football_game_odds', {})
        r.update(version=VERSION, scope='Missing NFL/NCAAF US game-price checkpoints and one current NFL injury report',
                 tracks=list(TRACKS), application_runtime_limit_seconds=None,
                 aws_service_runtime_max_seconds=AWS_MAX_SECONDS, frozen_cutoff=FROZEN_CUTOFF,
                 planned_missing_by_track=dict(self.plan_counts),
                 selected_queue_remaining=max(0, len(self.tasks) - phase.get('processed', 0)),
                 selected_queue_failed=phase.get('negative_responses', 0),
                 selected_queue_complete=(r['phases'].get('plan', {}).get('status') == 'frozen'
                     and phase.get('status') == 'planned_requests_processed'
                     and phase.get('processed', 0) == len(self.tasks) and phase.get('negative_responses', 0) == 0),
                 no_new_subscription_or_license=True,
                 not_completed_by_this_runner=['basketball_history', 'historical_player_props', 'unpublished_availability',
                                               'tracking_video', 'point_in_time_validation', 'model_training'])
        return r

    def finish(self):
        self.stop.set()
        summary = self.checkpoint()
        prefix = 'shared/acquisition/paid/' + self.run_id + '/'
        members = {'summary.json': summary, 'failures.json': self.failures, 'receipts.json': self.receipts,
                   'plan.json': self.serialized_plan(), 'availability.json': self.public_report,
                   'resume.json': {'reuse_successful_request_indexes': True, 'tracks': list(TRACKS),
                                   'frozen_cutoff': FROZEN_CUTOFF, 'remaining': summary['selected_queue_remaining']}}
        for name in ('summary.json', 'failures.json', 'receipts.json'):
            self.save_json(prefix + name, members[name])
        out = Path(self.args.output_dir); out.mkdir(parents=True, exist_ok=True)
        path = out / ('sports_edge_lab_football_return_' + self.run_id + '.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, value in members.items():
                z.writestr(name, blob(value))
        self.s3.upload_file(str(path), self.args.bucket, prefix + path.name, ExtraArgs={'ServerSideEncryption': 'AES256'})
        emit('COMPLETE', run_id=self.run_id, return_zip=path.name, summary_key=prefix + 'summary.json',
             queue_complete=summary['selected_queue_complete'], remaining=summary['selected_queue_remaining'],
             statistics=summary['statistics'], budget=summary['budget'])
        return 1 if any(x.get('status') == 'failed' for x in self.phase.values()) else 0


def focused_tests():
    class Tests(unittest.TestCase):
        def test_plan_excludes_basketball_and_future_and_deduplicates(self):
            r={'commence_time':'2026-10-10T18:00:00Z'}
            e={'nfl':{'a':r,'b':r},'ncaaf':{'a':r},'nba':{'a':r}}
            tasks, counts=build_plan(e,lambda *a:True,parse(FROZEN_CUTOFF))
            self.assertEqual(counts,{'nfl':4,'ncaaf':4});self.assertEqual(len(tasks),8)
            self.assertEqual({x[0] for x in tasks},set(TRACKS))
            self.assertTrue(all(x[1]<=parse(FROZEN_CUTOFF) for x in tasks))
        def test_plan_skips_successful_indexes(self):
            tasks,counts=build_plan({'ncaaf':{'a':{'commence_time':'2026-10-10T18:00:00Z'}}},lambda *a:False,parse(FROZEN_CUTOFF))
            self.assertEqual(tasks,[]);self.assertEqual(counts,{'nfl':0,'ncaaf':0})
        def test_old_application_timer_does_not_stop_queue(self):
            a=FootballFinish.__new__(FootballFinish);a.deadline=0;a.stop=threading.Event()
            a.time_left();a.stop.set()
            with self.assertRaises(BudgetStop):a.time_left()
        def test_scope_rejects_stats_props_and_non_us(self):
            p={'date':'2026-10-01T00:00:00Z','markets':'h2h,spreads,totals','regions':'us','oddsFormat':'decimal','dateFormat':'iso'}
            e='/v4/historical/sports/americanfootball_ncaaf/odds'
            self.assertTrue(scope_allowed('odds','ncaaf',e,p))
            for provider,track,path,params in [('cbbd','ncaam','/games',{}),('odds','nba',e,p),('odds','ncaaf',e,dict(p,regions='eu')),('odds','ncaaf',e,dict(p,markets='player_pass_yds')),('odds','ncaaf',e,dict(p,date='2027-01-01T00:00:00Z'))]:
                self.assertFalse(scope_allowed(provider,track,path,params))
        def test_scope_gate_runs_before_parent_capture(self):
            a=FootballFinish.__new__(FootballFinish)
            with mock.patch.object(OddsOnly,'capture') as parent:
                with self.assertRaises(ValueError):a.capture('cbbd','ncaam','/games',{},'bad')
                parent.assert_not_called()
        def test_live_reserve_stops_after_response(self):
            a=FootballFinish.__new__(FootballFinish);a.completed_ids=set();a.budget=Budget(200000,0)
            a.budget.providers={'odds':{'x-requests-remaining':100029}}
            with mock.patch.object(OddsOnly,'capture',return_value=True):
                with self.assertRaisesRegex(BudgetStop,'live_account_reserve_floor'):
                    a.capture('odds','nfl','/v4/sports/americanfootball_nfl/events',{'dateFormat':'iso'},'quota','test',False)
            self.assertIn('odds',a.budget.disabled)
        def test_one_unique_return_with_resume_state(self):
            import tempfile
            a=FootballFinish.__new__(FootballFinish);a.stop=threading.Event();a.run_id='test-unique';a.tasks=[]
            a.receipts=[];a.failures=[];a.public_report={};a.phase={};saved=[]
            a.checkpoint=lambda:{'selected_queue_remaining':0,'selected_queue_complete':True,'statistics':{},'budget':{}}
            a.save_json=lambda *args:None;a.s3=SimpleNamespace(upload_file=lambda *args,**kwargs:saved.append(args[2]))
            with tempfile.TemporaryDirectory() as folder:
                a.args=SimpleNamespace(output_dir=folder,bucket='test')
                with mock.patch('builtins.print'):self.assertEqual(a.finish(),0)
                paths=list(Path(folder).glob('*.zip'));self.assertEqual(len(paths),1);self.assertEqual(len(saved),1)
                with zipfile.ZipFile(paths[0]) as z:self.assertIn('resume.json',z.namelist());self.assertIn('availability.json',z.namelist())
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():raise RuntimeError('Focused football guard failed')
    return result.testsRun


def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    tests=self_test()+continuation_tests()+current_tests()+resume_tests()+focused_tests()
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(nfl_current.Tests))
    if not result.wasSuccessful():raise RuntimeError('NFL source tests failed')
    tests+=result.testsRun
    emit('SELF_TEST_PASS',tests=tests,workload=VERSION)
    if args.self_test:return 0
    # No AWS client, runtime credential or source network operation precedes tests.
    args.bucket='sagemaker-sports-edge-lab-560403859723-us-west-2';args.region='us-west-2'
    args.odds_parameter='/sports-edge-lab/shared/the-odds-api/key';args.mode='odds';args.until=FROZEN_CUTOFF
    args.odds_credits=CREDIT_LIMIT;args.stats_calls=0;args.max_seconds=float('inf');args.max_response_mb=64;args.odds_workers=1
    args.hourly_usd=.461;args.output_dir='/opt/ml/processing/output';args.source_runs=SOURCE_RUNS
    args.source_events_key='shared/acquisition/paid/20261016T182005Z-1999205e92/discovered-events.json'
    archive=FootballFinish(args)
    signal.signal(signal.SIGTERM,lambda *_:archive.stop.set())
    emit('START',run_id=archive.run_id,application_runtime_limit_seconds=None,credit_ceiling=CREDIT_LIMIT,tracks=list(TRACKS))
    beat=threading.Thread(target=archive.heartbeat,daemon=True);beat.start()
    archive.safe_work('seed',archive.seed)
    if archive.phase.get('plan',{}).get('status')=='frozen' and archive.phase.get('seed',{}).get('status')=='completed':
        archive.safe_work('availability',archive.refresh_availability)
        if archive.tasks:
            archive.safe_work('quota',archive.quota_gate)
            if archive.quota_check.get('passed') is True:archive.safe_work('odds',archive.work)
        else:archive.work()
    archive.stop.set();beat.join(timeout=10)
    return archive.finish()


if __name__=='__main__':raise SystemExit(main())
