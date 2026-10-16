"""Bounded recent FBS detail capture; source dates and game joins are audited."""
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import logging
from pathlib import Path
import sys
import threading
import unittest
import zipfile

from acquire_paid_data import blob, emit, iso, now, parse, self_test
from current_capture import CurrentCapture, current_tests

VERSION = 'sports-edge-lab-football-current-v034'


def recent_weeks(calendar, observed):
    eligible = {}
    for row in calendar if isinstance(calendar, list) else []:
        try:
            start, end = parse(row['startDate']), parse(row['endDate'])
            week, kind = row['week'], row['seasonType']
            if isinstance(week, int) and kind in ('regular', 'postseason') and start <= observed and end >= observed-dt.timedelta(days=21):
                eligible[(week, kind)] = start
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return sorted(eligible, key=lambda k: eligible[k], reverse=True)[:3]


def game_audit(rows, games, observed, id_field):
    valid = [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
    ids = {str(r[id_field]) for r in valid if r.get(id_field) is not None}
    expected = {str(g['id']):g for g in games if g.get('completed') is True and parse(g['startDate']) <= observed}
    covered = set(expected) & ids
    all_games = {str(g['id']):g for g in games}
    dates = [all_games[k]['startDate'] for k in ids & set(all_games)]
    completed_dates = [expected[k]['startDate'] for k in covered]
    return {'rows':len(valid), 'returned_game_ids':len(ids), 'expected_completed_games':len(expected),
        'covered_completed_games':len(covered), 'missing_completed_game_ids':sorted(set(expected)-ids),
        'unmatched_game_ids':sorted(ids-set(all_games)), 'latest_game_kickoff':max(dates) if dates else None,
        'latest_completed_game_kickoff':max(completed_dates) if completed_dates else None,
        'missing_game_id_rows':sum(r.get(id_field) is None for r in valid),
        'all_expected_completed_games_have_rows':set(expected)<=ids,
        'row_completeness_verified':False, 'historical_point_in_time_approved':False}


def availability_rows(text, rejections=None):
    lines = [s for s in text.splitlines() if s.startswith('|')]
    if not lines or [x.strip() for x in lines[0].strip('|').split('|')] != ['Team','Date','Opponent','Number','Player','Initial Status','Update 1 Status','Update 2 Status','Game Day Status']:
        raise ValueError('Unexpected availability table schema')
    rows=[]
    for line in lines[2:]:
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)!=9:
            if rejections is None: raise ValueError('Availability column count changed')
            rejections.append({'cells':len(cells),'line':line,'reason':'ambiguous_missing_column'})
            continue
        date=dt.datetime.strptime(cells[1],'%m/%d/%y').date().isoformat()
        statuses={k:(None if v=='-' else v) for k,v in zip(('initial','update_1','update_2','game_day'),cells[5:])}
        rows.append({'team':cells[0], 'game_date':date, 'opponent':cells[2], 'jersey':cells[3],
            'player_name':cells[4], 'statuses':statuses, 'provider_player_id':None,
            'source_publication_time':None, 'historical_point_in_time_approved':False})
    return rows


class FootballCapture(CurrentCapture):
    def __init__(self,args):
        super().__init__(args)
        self.detail_audits={}
        self.availability={}

    def football(self):
        year=self.observed.year
        calendar=self.capture_current('cfbd','ncaaf','/calendar',{'year':year},'recent_calendar')
        games=self.capture_current('cfbd','ncaaf','/games',{'year':year,'seasonType':'both','classification':'fbs'},'fbs_schedule')
        if not isinstance(games,list): raise ValueError('FBS schedule unavailable')
        weeks=recent_weeks(calendar,self.observed)
        if not weeks: raise ValueError('Recent calendar windows unavailable')
        self.phase['recent_football']={'status':'running','weeks':weeks,'classification':'fbs'}
        for week,kind in weeks:
            subset=[g for g in games if (g.get('week'),g.get('seasonType'))==(week,kind)]
            for endpoint,id_field in [('/plays','gameId'),('/drives','gameId'),('/games/teams','id'),('/games/players','id'),('/stats/game/advanced','gameId')]:
                params={'year':year,'week':week,'seasonType':kind}
                if endpoint in ('/plays','/drives'):params['classification']='fbs'
                rows=self.capture_current('cfbd','ncaaf',endpoint,params,'recent_fbs'+endpoint)
                report=game_audit(rows,subset,self.observed,id_field)
                report.update(endpoint=endpoint,week=week,season_type=kind,http_capture_succeeded=rows is not None)
                with self.lock:self.detail_audits[str(week)+kind+endpoint]=report
            self.checkpoint()
        self.capture_current('cfbd','ncaaf','/player/usage',{'year':year},'current_player_usage')
        self.phase['recent_football']['status']='planned_requests_processed'
        # Optional entitlement-dependent endpoint comes after the core captures.
        for week,kind in weeks:
            self.capture_current('cfbd','ncaaf','/games/weather',{'year':year,'week':week,'seasonType':kind,'classification':'fbs'},'current_game_weather')

    def availability_capture(self):
        with zipfile.ZipFile(sys.argv[0]) as package:
            seed=json.loads(package.read('availability_seed.json'))
        extracted=seed['extracted_markdown'].encode()
        digest=hashlib.sha256(extracted).hexdigest()
        rejected=[]
        rows=availability_rows(seed['extracted_markdown'],rejected)
        if not rows:raise ValueError('Empty availability extraction')
        raw_key='tracks/ncaaf/raw/bigten-availability-rendered/objects/'+digest+'.md.gz'
        self.s3.put_object(Bucket=self.args.bucket,Key=raw_key,Body=gzip.compress(extracted,mtime=0),ServerSideEncryption='AES256',ContentType='application/gzip')
        derived='tracks/ncaaf/derived/bigten-availability/'+self.run_id+'/rows.jsonl.gz'
        normalized=b'\n'.join(blob(dict(r,source_url=seed['source_url'],observed_at=seed['observed_at'],source_key=raw_key)) for r in rows)+b'\n'
        self.s3.put_object(Bucket=self.args.bucket,Key=derived,Body=gzip.compress(normalized,mtime=0),ServerSideEncryption='AES256',ContentType='application/gzip')
        receipt={k:v for k,v in seed.items() if k!='extracted_markdown'}
        receipt.update(raw_key=raw_key,sha256=digest,raw_bytes=len(extracted),derived_key=derived)
        self.save_json('tracks/ncaaf/raw/bigten-availability-rendered/receipts/'+self.run_id+'.json',receipt)
        self.save_json('tracks/ncaaf/derived/bigten-availability/'+self.run_id+'/rejected-rows.json',rejected)
        current=[r for r in rows if self.observed.date().isoformat()<=r['game_date']<=(self.observed+dt.timedelta(days=2)).date().isoformat()]
        self.availability={**receipt,'rows':len(rows),'rejected_ambiguous_rows':len(rejected),'current_weekend_rows':len(current),
            'team_games':len({(r['team'],r['game_date'],r['opponent']) for r in rows}),
            'current_weekend_team_games':len({(r['team'],r['game_date'],r['opponent']) for r in current}),
            'teams':sorted({r['team'] for r in rows}), 'first_game_date':min(r['game_date'] for r in rows),
            'last_game_date':max(r['game_date'] for r in rows), 'missing_game_day_status_rows':sum(r['statuses']['game_day'] is None for r in rows),
            'scope':'Public Big Ten football archive rendered extraction, not an original versioned report PDF or all-conference feed',
            'historical_point_in_time_approved':False,'identity_join_validated':False}
        self.phase['bigten_availability']={'status':'completed','rows':len(rows)}

    def summary(self):
        r=super().summary()
        r.update(version=VERSION,scope='Recent three calendar windows of FBS plays/drives/game stats; current usage/weather; rendered Big Ten availability',
            recent_game_coverage=dict(self.detail_audits),bigten_availability=dict(self.availability),
            not_completed_by_this_runner=['all_NCAA_classifications','all_conference_availability','play_by_play_row_completeness','tracking_and_video','historical_point_in_time_approval'])
        return r


def detail_tests():
    class Tests(unittest.TestCase):
        def test_no_future_calendar_windows(self):
            at=parse('2026-10-16T20:00:00Z')
            c=[{'week':i,'seasonType':'regular','startDate':f'2026-10-{d:02}T00:00:00Z','endDate':f'2026-10-{d+6:02}T23:59:59Z'} for i,d in [(5,1),(6,8),(7,15),(8,22)]]
            self.assertEqual(recent_weeks(c,at),[(7,'regular'),(6,'regular'),(5,'regular')])
        def test_audit_distinguishes_rows_games_and_future(self):
            games=[{'id':1,'completed':True,'startDate':'2026-10-15T20:00:00Z'},{'id':2,'completed':True,'startDate':'2026-10-15T21:00:00Z'},{'id':3,'completed':False,'startDate':'2026-10-17T20:00:00Z'}]
            r=game_audit([{'gameId':1},{'gameId':1},{'gameId':9}],games,parse('2026-10-16T20:00:00Z'),'gameId')
            self.assertEqual((r['rows'],r['covered_completed_games']),(3,1));self.assertEqual(r['missing_completed_game_ids'],['2'])
            self.assertEqual(r['unmatched_game_ids'],['9']);self.assertFalse(r['row_completeness_verified'])
        def test_empty_response_is_missing_coverage(self):
            r=game_audit([], [{'id':1,'completed':True,'startDate':'2026-10-15T20:00:00Z'}],parse('2026-10-16T20:00:00Z'),'id')
            self.assertFalse(r['all_expected_completed_games_have_rows'])
        def test_availability_unknown_is_not_available(self):
            s='| Team | Date | Opponent | Number | Player | Initial Status | Update 1 Status | Update 2 Status | Game Day Status |\n|---|---|---|---|---|---|---|---|---|\n| A | 10/17/26 | at B | #1 | Test Player | Out | Out | - | - |'
            r=availability_rows(s)[0]
            self.assertIsNone(r['statuses']['game_day']);self.assertEqual(r['game_date'],'2026-10-17')
            self.assertFalse(r['historical_point_in_time_approved'])
        def test_changed_schema_rejected(self):
            with self.assertRaises(ValueError):availability_rows('| unexpected |')
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not r.wasSuccessful():raise RuntimeError('Football test gate failed')
    return r.testsRun


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--max-seconds',type=int,default=600)
    p.add_argument('--stats-calls',type=int,default=30)
    p.add_argument('--output-dir',default='/opt/ml/processing/output')
    a=p.parse_args()
    count=self_test()+current_tests()+detail_tests()
    emit('SELF_TEST_PASS',tests=count,workload=VERSION)
    if a.self_test:return 0
    if not (30<=a.max_seconds<=600 and 21<=a.stats_calls<=30):p.error('Bounded football envelope invalid')
    a.bucket='sagemaker-sports-edge-lab-560403859723-us-west-2';a.region='us-west-2'
    a.cfbd_parameter='/sports-edge-lab/shared/cfbd/key';a.mode='stats';a.until=None
    a.max_response_mb=64;a.odds_credits=0;a.hourly_usd=.461;a.workers=1;a.odds_workers=1
    logging.getLogger('botocore').setLevel(logging.ERROR)
    capture=FootballCapture(a)
    emit('START',run_id=capture.run_id,version=VERSION,max_stats_calls=a.stats_calls)
    beat=threading.Thread(target=capture.heartbeat,daemon=True);beat.start()
    capture.safe_work('bigten_availability',capture.availability_capture)
    capture.safe_work('recent_football',capture.football)
    capture.stop.set();beat.join(timeout=10)
    return capture.finish()


if __name__=='__main__':sys.exit(main())
