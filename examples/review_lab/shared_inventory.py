"""Federate already-verified project catalogs without multiplying coverage.

All walkthrough data are invented. No transport, credentials, fitting, prices,
orders or quota spending. Raw-provider adapters and external attestations remain
outside this deliberately small content and scope contract.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable
from examples.basketball_contracts.recovery_plan import atomic_id, digest, encoded, instant, iso, pin


@dataclass(frozen=True)
class Request:
    provider: str
    sport: str
    endpoint: str
    snapshot_at: str
    markets: tuple[str, ...]
    regions: tuple[str, ...]

    def __post_init__(self):
        for value in (self.provider, self.sport, self.endpoint):
            atomic_id(value)
        object.__setattr__(self, 'snapshot_at', iso(self.snapshot_at))
        for field in ('markets', 'regions'):
            values = getattr(self, field)
            if not isinstance(values, tuple) or not values or len(set(values)) != len(values):
                raise ValueError('nonempty unique tuple required')
            for value in values:
                atomic_id(value)
            object.__setattr__(self, field, tuple(sorted(values)))

    @property
    def identity(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class Scope:
    project: str
    inventory_sha256: str
    object_hashes: tuple[str, ...]
    unresolved_objects: int = 0

    def __post_init__(self):
        atomic_id(self.project)
        pin(self.inventory_sha256)
        if not isinstance(self.object_hashes, tuple) or len(set(self.object_hashes)) != len(self.object_hashes):
            raise ValueError('unique declared object hashes required')
        for value in self.object_hashes:
            pin(value)
        if type(self.unresolved_objects) is not int or self.unresolved_objects < 0:
            raise ValueError('nonnegative unresolved object count required')


class Federation:
    """Immutable union of explicit project scopes and caller-held content pins.

    Scope manifests are trusted inputs, not proof of a complete bucket inventory.
    A content hash establishes equality; it does not attest source authenticity.
    An object contains request metadata and normalized quote identity receipts,
    not executable prices or a provider-specific API response.
    """
    def __init__(self, required_projects: Iterable[str], scopes: Iterable[Scope], objects: dict[str, bytes]):
        projects = tuple(required_projects)
        if not projects or len(set(projects)) != len(projects):
            raise ValueError('nonempty unique required project list required')
        for project in projects:
            atomic_id(project)
        scopes = tuple(scopes)
        if len(scopes) != len(projects) or {s.project for s in scopes} != set(projects):
            raise ValueError('every required project must supply exactly one scoped inventory')
        if any(s.unresolved_objects for s in scopes):
            raise ValueError('unclassified objects block an absence claim')
        required = {h for s in scopes for h in s.object_hashes}
        if set(objects) != required:
            raise ValueError('supplied content must exactly close all declared inventories')
        self._scopes = scopes
        self._objects = {}
        self._requests = {}
        self._request_specs = {}
        self._observations = {}
        quote_pins = {}
        for sha in sorted(required):
            raw = objects[sha]
            if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError('content hash mismatch')
            data = json.loads(raw)
            if set(data) != {'schema', 'request', 'captured_at', 'observations'} or data['schema'] != 'public.shared-inventory.v1':
                raise ValueError('unsupported normalized envelope')
            request_data = dict(data['request'])
            request_data['markets'] = tuple(request_data['markets'])
            request_data['regions'] = tuple(request_data['regions'])
            request = Request(**request_data)
            capture = instant(data['captured_at'])
            if instant(request.snapshot_at) > capture:
                raise ValueError('snapshot cannot follow receipt capture')
            if not isinstance(data['observations'], list):
                raise ValueError('observation list required')
            self._requests.setdefault(request.identity, set()).add(sha)
            self._request_specs[request.identity] = request
            self._objects[sha] = data
            seen = set()
            for observation in data['observations']:
                obs = dict(observation)
                if set(obs) != {'event', 'ordered_teams', 'kickoff', 'bookmaker', 'market', 'region', 'snapshot_at', 'quote_at', 'quote_sha256', 'binding_sha256', 'reuse_allowed'}:
                    raise ValueError('unsupported observation identity')
                for field in ('event', 'bookmaker', 'market', 'region'):
                    atomic_id(obs[field])
                if not isinstance(obs['ordered_teams'], list) or len(obs['ordered_teams']) != 2 or obs['ordered_teams'][0] == obs['ordered_teams'][1]:
                    raise ValueError('exact distinct ordered teams required')
                for team in obs['ordered_teams']:
                    atomic_id(team)
                for field in ('quote_sha256', 'binding_sha256'):
                    pin(obs[field])
                if type(obs['reuse_allowed']) is not bool:
                    raise ValueError('explicit reuse permission required')
                for field in ('kickoff', 'snapshot_at', 'quote_at'):
                    obs[field] = iso(obs[field])
                if obs['market'] not in request.markets or obs['region'] not in request.regions:
                    raise ValueError('observation outside request scope')
                if not instant(obs['quote_at']) <= instant(obs['snapshot_at']) <= instant(request.snapshot_at):
                    raise ValueError('quote and archive clocks must precede requested snapshot')
                # Independent catalog copies and formatting cannot create new observations.
                core = {'provider': request.provider, 'sport': request.sport, **{k:v for k,v in obs.items() if k not in {'binding_sha256', 'reuse_allowed'}}}
                coordinate = digest({k:v for k,v in core.items() if k != 'quote_sha256'})
                if coordinate in quote_pins and quote_pins[coordinate] != obs['quote_sha256']:
                    raise ValueError('conflicting quote content at one exact observation identity')
                quote_pins[coordinate] = obs['quote_sha256']
                identity = digest(core)
                if identity in seen:
                    raise ValueError('duplicate observation within one normalized object')
                seen.add(identity)
                entry = self._observations.setdefault(identity, {'provider': request.provider, 'sport': request.sport, **obs, 'objects': set(), 'reuse_objects': set(), 'bindings': set()})
                entry['objects'].add(sha)
                entry['bindings'].add(obs['binding_sha256'])
                if obs['reuse_allowed']:
                    entry['reuse_objects'].add(sha)

    def request_status(self, request: Request):
        matching_requests = [identity for identity, saved in self._request_specs.items()
            if (saved.provider, saved.sport, saved.endpoint, saved.snapshot_at) ==
               (request.provider, request.sport, request.endpoint, request.snapshot_at)
            and set(saved.markets) >= set(request.markets) and set(saved.regions) >= set(request.regions)]
        matches = sorted({sha for identity in matching_requests for sha in self._requests[identity]})
        return {'request_sha256': request.identity, 'status': 'CAPTURED' if matches else 'NOT_FOUND_IN_DECLARED_SCOPES',
                'content_sha256s': matches, 'original_request_sha256s': sorted(matching_requests), 'may_dispatch': False}

    def eligible(self, *, provider: str, sport: str, event: str, ordered_teams: tuple[str, str], kickoff: str,
                 cutoff: str, freshness_seconds: int):
        if type(freshness_seconds) is not int or freshness_seconds <= 0:
            raise ValueError('positive freshness required')
        lock, start = instant(cutoff), instant(kickoff)
        if lock >= start:
            raise ValueError('cutoff must precede kickoff')
        rows = []
        for identity, row in sorted(self._observations.items()):
            if (row['provider'], row['sport'], row['event'], tuple(row['ordered_teams']), instant(row['kickoff'])) != (provider, sport, event, ordered_teams, start):
                continue
            if not row['reuse_objects'] or instant(row['snapshot_at']) > lock or (lock - instant(row['quote_at'])).total_seconds() > freshness_seconds:
                continue
            rows.append({'observation_sha256': identity, 'market': row['market'], 'region': row['region'],
                         'bookmaker': row['bookmaker'], 'source_objects': sorted(row['objects']),
                         'reuse_permitted_objects': sorted(row['reuse_objects']), 'binding_sha256s': sorted(row['bindings'])})
        return rows

    def summary(self):
        aliases = sum(len(s.object_hashes) for s in self._scopes)
        occurrences = sum(len(data['observations']) for data in self._objects.values())
        return {'projects': sorted(s.project for s in self._scopes), 'scope_manifest_sha256s': sorted(s.inventory_sha256 for s in self._scopes),
                'object_references': aliases, 'unique_content_objects': len(self._objects),
                'duplicate_object_references': aliases - len(self._objects),
                'unique_requests': len(self._requests), 'observation_occurrences': occurrences,
                'unique_observations': len(self._observations), 'duplicate_observation_occurrences': occurrences - len(self._observations),
                'actual_requests': 0, 'actual_credits': 0, 'model_fits': 0}


def fixture():
    request = Request('invented-provider', 'invented-football', 'historical-featured', '2025-09-07T12:00:00Z', ('h2h',), ('us',))
    row = {'event': 'game-1', 'ordered_teams': ['home-1', 'away-1'], 'kickoff': '2025-09-07T18:00:00Z',
           'bookmaker': 'book-1', 'market': 'h2h', 'region': 'us', 'snapshot_at': request.snapshot_at,
           'quote_at': '2025-09-07T11:59:00Z', 'quote_sha256': digest('invented-paired-quote'),
           'binding_sha256': digest('invented-identity-binding'), 'reuse_allowed': True}
    data = {'schema': 'public.shared-inventory.v1', 'request': asdict(request),
            'captured_at': '2026-01-01T00:00:00Z', 'observations': [row]}
    raw = encoded(data)
    alternate = json.dumps(data, indent=2).encode()
    h1, h2 = hashlib.sha256(raw).hexdigest(), hashlib.sha256(alternate).hexdigest()
    scopes = (Scope('football', digest('football-scope'), (h1,)), Scope('basketball', digest('basketball-scope'), (h1,)),
              Scope('march', digest('march-scope'), (h2,)))
    return request, scopes, {h1: raw, h2: alternate}


def walkthrough():
    request, scopes, objects = fixture()
    catalog = Federation(('football', 'basketball', 'march'), scopes, objects)
    eligible = catalog.eligible(provider=request.provider, sport=request.sport, event='game-1', ordered_teams=('home-1', 'away-1'),
                                kickoff='2025-09-07T18:00:00Z', cutoff=request.snapshot_at, freshness_seconds=900)
    return {**catalog.summary(), 'already_captured': catalog.request_status(request), 'eligible_observations': len(eligible),
            'same_source_preserves_all_aliases': len(eligible[0]['source_objects']) == 2,
            'boundary': 'Invented scope receipts and normalized quote identities; no live provider or account verification.'}


if __name__ == '__main__':
    print(json.dumps(walkthrough(), indent=2))
