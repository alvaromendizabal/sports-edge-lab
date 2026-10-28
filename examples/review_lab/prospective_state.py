"""Transactional, append-only paper decisions using invented demonstration data.

The clock is injectable for deterministic tests. Evidence flags are supplied by
an external verifier; this example does not authenticate a venue or a model.
Hashes establish integrity, not independent historical timestamp attestation.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import Callable


REQUIRED_EVIDENCE = frozenset(('policy', 'orientation', 'fee', 'depth', 'settlement'))


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone-aware clock required')
    return result.astimezone(timezone.utc)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


@dataclass(frozen=True)
class Decision:
    decision_id: str
    league: str
    season: int
    week: int
    game_id: str
    kickoff: str
    window_open: str
    cutoff: str
    forecast_at: str
    quote_at: str
    model_id: str
    policy_sha256: str
    feature_sha256: str
    venue: str
    contract_id: str
    side: str
    probability: float
    stake_cents: int
    quantity: int
    price_cents: int
    fee_cents: int
    fee_version: str
    evidence_verified: tuple[str, ...]


class PaperLedger:
    """A single scenario's shared native-week budget; no execution capability."""

    def __init__(self, path: Path, *, clock: Callable[[], str], budget_cents: int = 10000):
        if type(budget_cents) is not int or budget_cents <= 0:
            raise ValueError('positive integer budget required')
        self.path, self.clock, self.budget = path, clock, budget_cents
        with self._connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY,
                    kind TEXT NOT NULL CHECK(kind IN ('decision','settlement')),
                    decision_id TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE,
                    UNIQUE(kind, decision_id)
                );
                CREATE TRIGGER IF NOT EXISTS immutable_event_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_event_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_config_update BEFORE UPDATE ON config
                    BEGIN SELECT RAISE(ABORT, 'immutable budget'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_config_delete BEFORE DELETE ON config
                    BEGIN SELECT RAISE(ABORT, 'immutable budget'); END;
            ''')
            old = db.execute("SELECT value FROM config WHERE key='budget_cents'").fetchone()
            if old and int(old[0]) != budget_cents:
                raise ValueError('resume cannot change the budget')
            db.execute("INSERT OR IGNORE INTO config VALUES ('budget_cents',?)", (str(budget_cents),))

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=3)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _events(db):
        events, previous = [], '0' * 64
        for row in db.execute('SELECT * FROM events ORDER BY sequence'):
            item = dict(row)
            material = {k: item[k] for k in ('sequence','kind','decision_id','recorded_at','payload','previous_hash')}
            expected = hashlib.sha256(canonical(material).encode()).hexdigest()
            if item['sequence'] != len(events)+1 or item['previous_hash'] != previous or item['event_hash'] != expected:
                raise ValueError('event chain integrity failure')
            item['payload'] = json.loads(item['payload'])
            events.append(item)
            previous = expected
        return events

    @staticmethod
    def _validate(d: dict, now: datetime):
        if not all(isinstance(d[k],str) and d[k] for k in ('decision_id','league','game_id','model_id','venue','contract_id','side','fee_version')):
            raise ValueError('explicit identity and provenance required')
        if d['side'] not in ('YES','NO') or not math.isfinite(d['probability']) or not 0 < d['probability'] < 1:
            raise ValueError('binary orientation and finite probability required')
        if type(d['season']) is not int or d['season'] <= 0 or type(d['week']) is not int or d['week'] <= 0:
            raise ValueError('native season/week required')
        if any(len(d[k]) != 64 or set(d[k])-set('0123456789abcdef') for k in ('policy_sha256','feature_sha256')):
            raise ValueError('content identities required')
        start, cutoff, kickoff = map(utc,(d['window_open'],d['cutoff'],d['kickoff']))
        if not start <= now <= cutoff < kickoff:
            raise ValueError('decision is not in its declared pregame window')
        if utc(d['forecast_at']) > now or not 0 <= (now-utc(d['quote_at'])).total_seconds() <= 900:
            raise ValueError('future forecast or nonfresh native quote')
        if set(d['evidence_verified']) != REQUIRED_EVIDENCE:
            raise ValueError('complete independent evidence review required')
        for key in ('stake_cents','quantity','price_cents','fee_cents'):
            if type(d[key]) is not int or d[key] < 0:
                raise ValueError('integer nonnegative financial units required')
        if not d['quantity'] or not 0 < d['price_cents'] < 100 or not d['stake_cents']:
            raise ValueError('positive quantity, stake and binary price required')
        if d['quantity']*d['price_cents']+d['fee_cents'] > d['stake_cents']:
            raise ValueError('purchase and fees exceed reserved stake')

    def _append(self, kind: str, identity: str, payload: dict):
        encoded, stamp = canonical(payload), self.clock()
        now = utc(stamp)
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            events = self._events(db)
            previous = next((e for e in events if e['kind']==kind and e['decision_id']==identity),None)
            if previous:
                if canonical(previous['payload']) != encoded:
                    raise ValueError('immutable event cannot be revised')
                return previous['event_hash']
            decisions = {e['decision_id']:e['payload'] for e in events if e['kind']=='decision'}
            if kind == 'decision':
                self._validate(payload,now)
                if decisions:
                    first = next(iter(decisions.values()))
                    if any(payload[k]!=first[k] for k in ('league','season','week')):
                        raise ValueError('one native league week per budget')
                    if any(payload['game_id']==d['game_id'] for d in decisions.values()):
                        raise ValueError('duplicate game exposure')
                if sum(d['stake_cents'] for d in decisions.values())+payload['stake_cents'] > self.budget:
                    raise ValueError('shared budget exceeded')
            else:
                d=decisions.get(identity)
                if not d or not utc(d['kickoff']) <= utc(payload['outcome_available_at']) <= now:
                    raise ValueError('settlement requires prior decision and an available post-kickoff outcome')
                if len(payload['source_sha256'])!=64 or set(payload['source_sha256'])-set('0123456789abcdef'):
                    raise ValueError('outcome source identity required')
                if type(payload['unit_payout_cents']) is not int or payload['unit_payout_cents'] not in (0,100):
                    raise ValueError('this invented example supports normal binary settlement only')
            record={'sequence':len(events)+1,'kind':kind,'decision_id':identity,'recorded_at':stamp,
                    'payload':encoded,'previous_hash':events[-1]['event_hash'] if events else '0'*64}
            digest=hashlib.sha256(canonical(record).encode()).hexdigest()
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',
                       tuple(record[k] for k in ('sequence','kind','decision_id','recorded_at','payload','previous_hash'))+(digest,))
            return digest

    def commit(self, decision: Decision):
        return self._append('decision',decision.decision_id,asdict(decision))

    def settle(self, decision_id: str, *, unit_payout_cents: int, outcome_available_at: str, source_sha256: str):
        return self._append('settlement',decision_id,dict(unit_payout_cents=unit_payout_cents,
            outcome_available_at=outcome_available_at,source_sha256=source_sha256))

    def snapshot(self):
        with self._connection() as db:
            events=self._events(db)
        decisions={e['decision_id']:e['payload'] for e in events if e['kind']=='decision'}
        outcomes={e['decision_id']:e['payload'] for e in events if e['kind']=='settlement'}
        reserved=sum(d['stake_cents'] for d in decisions.values())
        pending=sorted(set(decisions)-set(outcomes))
        profit=sum(decisions[k]['quantity']*(v['unit_payout_cents']-decisions[k]['price_cents'])-decisions[k]['fee_cents'] for k,v in outcomes.items())
        return {'events':len(events),'head':events[-1]['event_hash'] if events else '0'*64,
                'reserved_cents':reserved,'unallocated_cents':self.budget-reserved,
                'unsettled_exposure_cents':sum(decisions[k]['stake_cents'] for k in pending),
                'pending':pending,'complete_paper_profit_cents':None if pending else profit,
                'actual_profit':None,'orders':0,'independent_timestamp_attestation':False}


def fixture():
    return Decision('invented-a','SIM',2030,1,'invented-event-a','2030-01-02T20:00:00Z',
        '2030-01-02T18:45:00Z','2030-01-02T19:00:00Z','2030-01-02T18:40:00Z',
        '2030-01-02T18:49:00Z','invented-model','a'*64,'b'*64,'invented-venue',
        'invented-contract','YES',.6,2500,40,50,40,'invented-fee-v1',tuple(sorted(REQUIRED_EVIDENCE)))


def demonstration():
    clock=['2030-01-02T18:50:00Z']
    with TemporaryDirectory() as tmp:
        ledger=PaperLedger(Path(tmp)/'paper.sqlite',clock=lambda:clock[0])
        decision_hash=ledger.commit(fixture());pending=ledger.snapshot()
        clock[0]='2030-01-02T23:00:00Z'
        ledger.settle('invented-a',unit_payout_cents=100,outcome_available_at='2030-01-02T22:55:00Z',source_sha256='c'*64)
        return {'invented_only':True,'decision_hash':decision_hash,'pending':pending,'settled':ledger.snapshot()}


if __name__=='__main__':
    print(json.dumps(demonstration(),indent=2))
