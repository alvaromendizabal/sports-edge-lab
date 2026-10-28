"""Invented-data feature snapshots with explicit availability and revision clocks.

This is a public engineering demonstration, not a basketball production recipe.
It fits no estimator, fetches no data, and changes no accepted research artifact.
Clock-verification flags are invented caller assertions, not external evidence.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math


def clock(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError('clock must be an explicit UTC string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError('an explicit UTC clock is required')
    return parsed


@dataclass(frozen=True)
class Observation:
    league: str
    event: str
    team: str
    completed_at: str
    observed_at: str
    published_at: str | None
    original_clock_verified: bool
    revision: int
    points_for: float
    points_against: float

    def validate(self):
        completed, observed = clock(self.completed_at), clock(self.observed_at)
        if any(not isinstance(x, str) or not x.strip() for x in (self.league, self.event, self.team)) or type(self.revision) is not int or self.revision < 1:
            raise ValueError('explicit identity and positive revision required')
        if type(self.original_clock_verified) is not bool:
            raise ValueError('clock verification must be an explicit boolean')
        if observed < completed:
            raise ValueError('outcome observed before completion')
        if self.published_at and clock(self.published_at) < completed:
            raise ValueError('outcome publication precedes completion')
        if self.original_clock_verified and not self.published_at:
            raise ValueError('verified publication requires its clock')
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (self.points_for, self.points_against)):
            raise ValueError('finite nonnegative invented points required')


@dataclass(frozen=True)
class Request:
    league: str
    event: str
    team: str
    opponent: str
    cutoff: str
    tipoff: str
    timing: str = 'strict'

    def validate(self):
        if clock(self.cutoff) >= clock(self.tipoff):
            raise ValueError('cutoff must precede tipoff')
        if self.team == self.opponent or any(not isinstance(x, str) or not x.strip() for x in (self.league, self.event, self.team, self.opponent)):
            raise ValueError('distinct explicit team identities required')
        if self.timing not in ('strict', 'reconstructed_24h'):
            raise ValueError('timing protocol must be explicit')


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def available_at(record: Observation, timing: str):
    observed = clock(record.observed_at)
    if timing == 'strict':
        if not record.original_clock_verified:
            return None
        return max(observed, clock(record.published_at))
    if timing == 'reconstructed_24h':
        return max(observed, clock(record.completed_at) + timedelta(hours=24))
    raise ValueError('unknown timing protocol')


def snapshot(records: list[Observation], request: Request):
    """Use only revisions available at cutoff, preserving absence as missing data."""
    request.validate()
    cutoff = clock(request.cutoff)
    identities = {}
    accepted = {}
    excluded = {'other_scope': 0, 'target_or_future_outcome': 0,
                'unverified_original_clock': 0, 'not_yet_available': 0}
    for record in records:
        record.validate()
        identity = (record.league, record.event, record.team, record.revision)
        content = asdict(record)
        if identity in identities:
            if identities[identity] != content:
                raise ValueError('conflicting duplicate source revision')
            continue
        identities[identity] = content
        if record.league != request.league or record.team not in (request.team, request.opponent):
            excluded['other_scope'] += 1
            continue
        if record.event == request.event or clock(record.completed_at) >= cutoff:
            excluded['target_or_future_outcome'] += 1
            continue
        release = available_at(record, request.timing)
        if release is None:
            excluded['unverified_original_clock'] += 1
            continue
        if release > cutoff:
            excluded['not_yet_available'] += 1
            continue
        key = (record.event, record.team)
        previous = accepted.get(key)
        if previous is None or record.revision > previous.revision:
            accepted[key] = record
    features = {}
    for team in (request.team, request.opponent):
        history = sorted((r for r in accepted.values() if r.team == team), key=lambda r: (clock(r.completed_at), r.event))
        recent = history[-3:]
        features[team] = {
            'prior_game_count': len(history),
            'rolling_points_for': sum(r.points_for for r in recent) / len(recent) if recent else None,
            'rolling_points_against': sum(r.points_against for r in recent) / len(recent) if recent else None,
            'rest_hours_from_last_completed_game': (clock(request.tipoff) - clock(history[-1].completed_at)).total_seconds() / 3600 if history else None,
            'latest_evidence_available_at': max(available_at(r, request.timing) for r in history).isoformat() if history else None,
            'missing_history': not bool(history),
        }
    used = sorted((asdict(r) for r in accepted.values()), key=lambda r: (r['team'], r['event'], r['revision']))
    payload = {'request': asdict(request), 'features': features, 'eligible_records': used,
               'excluded_counts': excluded, 'synthetic': True, 'real_fits': 0,
               'publication_qualification': 'original_clock_required' if request.timing == 'strict' else 'research_reconstruction_only'}
    # Audit counts may grow when a later archive contains more excluded records.
    # Bind the issued feature content only to its request and eligible evidence.
    identity_payload = {k: v for k, v in payload.items() if k != 'excluded_counts'}
    return {**payload, 'snapshot_sha256': digest(identity_payload)}


class IssuedSnapshots:
    """Append-only illustrative issue store; data revisions do not rewrite issuance."""
    def __init__(self):
        self._issued = {}

    def issue(self, value):
        payload = {k: v for k, v in value.items() if k not in ('snapshot_sha256', 'excluded_counts')}
        if digest(payload) != value['snapshot_sha256']:
            raise ValueError('snapshot content does not match its identity')
        request = value['request']
        key = tuple(request[k] for k in ('league', 'event', 'team', 'opponent', 'cutoff', 'timing'))
        if key in self._issued:
            if self._issued[key]['snapshot_sha256'] != value['snapshot_sha256']:
                raise ValueError('issued snapshot is immutable')
            return 'verified_reuse'
        self._issued[key] = json.loads(json.dumps(value))
        return 'issued'


def fixture():
    """All identities, clocks and scores below are invented."""
    r = Request('nba', 'invented-upcoming', 'Amber', 'Cobalt', '2024-01-08T20:00:00Z', '2024-01-08T21:00:00Z')
    records = [
        Observation('nba', 'invented-a', 'Amber', '2024-01-02T22:00:00Z', '2024-01-03T01:00:00Z', '2024-01-03T00:00:00Z', True, 1, 100, 98),
        Observation('nba', 'invented-b', 'Amber', '2024-01-06T22:00:00Z', '2024-01-07T01:00:00Z', '2024-01-07T00:00:00Z', True, 1, 108, 102),
        Observation('nba', 'invented-b', 'Amber', '2024-01-06T22:00:00Z', '2024-01-09T01:00:00Z', '2024-01-09T00:00:00Z', True, 2, 110, 101),
        Observation('nba', 'invented-c', 'Cobalt', '2024-01-04T22:00:00Z', '2024-01-05T01:00:00Z', '2024-01-05T00:00:00Z', True, 1, 95, 97),
        Observation('nba', 'invented-unclocked', 'Amber', '2024-01-05T22:00:00Z', '2024-01-06T01:00:00Z', None, False, 1, 120, 90),
        Observation('nba', 'invented-observed-late', 'Cobalt', '2024-01-07T22:00:00Z', '2024-01-09T01:00:00Z', '2024-01-08T00:00:00Z', True, 1, 101, 99),
        Observation('nba', 'invented-upcoming', 'Amber', '2024-01-08T23:00:00Z', '2024-01-09T01:00:00Z', '2024-01-09T00:00:00Z', True, 1, 130, 80),
    ]
    return records, r


def main():
    records, request = fixture()
    result = snapshot(records, request)
    issued = IssuedSnapshots()
    status = [issued.issue(result), issued.issue(result)]
    print(json.dumps({'fixture': 'invented_only', 'issue_status': status, 'snapshot': result}, indent=2))


if __name__ == '__main__':
    main()
