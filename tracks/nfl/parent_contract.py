"""Credential-free parent identity and reuse demonstration.

Only invented fixtures belong here. This generic contract illustrates why a
latest failed invocation and an older scientific carrier have separate identities.
It does not load models, access storage, fit data or issue forecasts.
"""
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import stat
from types import MappingProxyType
import zipfile

IDENTITY_FIELDS = frozenset(('schema', 'project', 'run_id', 'cycle', 'fixture',
                             'package_sha256', 'parent_package_sha256'))
ROLES = frozenset(('completed_study', 'fixed_forward', 'cover_conditional'))


def pin(body):
    return {'bytes': len(body), 'sha256': sha256(body).hexdigest()}


def check_pin(body, expected):
    if (set(expected) != {'bytes', 'sha256'} or type(expected['bytes']) is not int
            or expected['bytes'] < 0 or not isinstance(expected['sha256'], str)
            or not re.fullmatch('[0-9a-f]{64}', expected['sha256'])
            or pin(body) != expected):
        raise ValueError('Physical content identity mismatch')


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or path.is_absolute()
            or any(ord(c) < 32 for c in name)
            or any(p in ('', '.', '..') for p in name.split('/'))
            or path.as_posix() != name):
        raise ValueError('Unsafe or noncanonical member name')
    return name


def check_identity(identity):
    if set(identity) != IDENTITY_FIELDS:
        raise ValueError('Full identity fields required')
    if any(not isinstance(identity[k], str) or not identity[k] for k in IDENTITY_FIELDS - {'fixture'}):
        raise ValueError('Identity strings required')
    if type(identity['fixture']) is not bool:
        raise ValueError('Explicit fixture flag required')
    for k in ('package_sha256', 'parent_package_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', identity[k]):
            raise ValueError('Exact package digest required')


@dataclass(frozen=True)
class VerifiedCarrier:
    identity: object
    archive_pin: object
    manifest_pin: object
    members: object


def authenticate(archive, expected_identity, archive_pin, manifest_pin,
                 completion, completion_pin):
    """Verify all bytes and closure before admitting a carrier; never execute it."""
    check_identity(expected_identity)
    check_pin(archive, archive_pin)
    check_pin(completion, completion_pin)
    with zipfile.ZipFile(BytesIO(archive)) as zf:
        infos = zf.infolist()
        names = [safe_name(i.filename) for i in infos]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate member')
        if any(i.is_dir() or stat.S_IFMT(i.external_attr >> 16) != stat.S_IFREG for i in infos):
            raise ValueError('Only explicit regular members are admitted')
        if zf.testzip() is not None:
            raise ValueError('CRC mismatch')
        members = {n: zf.read(n) for n in names}
    if 'MANIFEST.json' not in members or 'IDENTITY.json' not in members:
        raise ValueError('Required metadata absent')
    check_pin(members['MANIFEST.json'], manifest_pin)
    manifest = json.loads(members['MANIFEST.json'])
    if set(manifest) != set(members) - {'MANIFEST.json'}:
        raise ValueError('Manifest closure mismatch')
    for name, expected in manifest.items():
        check_pin(members[name], expected)
    identity = json.loads(members['IDENTITY.json'])
    check_identity(identity)
    if identity != expected_identity:
        raise ValueError('Exact carrier identity mismatch')
    receipt = json.loads(completion)
    if (receipt['identity'] != identity or receipt['archive'] != archive_pin
            or receipt['manifest'] != manifest_pin):
        raise ValueError('External completion binding mismatch')
    packaged = datetime.fromisoformat(receipt['packaged_at'])
    completed = datetime.fromisoformat(receipt['completed_at'])
    if packaged.tzinfo is None or completed.tzinfo is None or completed <= packaged:
        raise ValueError('A genuinely later external completion is required')
    return VerifiedCarrier(MappingProxyType(identity), MappingProxyType(dict(archive_pin)),
                           MappingProxyType(dict(manifest_pin)), MappingProxyType(members))


def prepare_reuse(carrier, latest_invocation, selections, anchor_bytes):
    """Validate all three domains before returning any material to a hydrator.

    A failed later attempt is audit context. It cannot substitute its identity
    for the exact carrier. Original source/model/issue anchor bytes are returned
    unchanged; adapters may add a new binding but may not rewrite those anchors.
    """
    check_identity(latest_invocation)
    if set(selections) != ROLES:
        raise ValueError('All three reuse domains must be declared')
    pending = {}
    for role, selection in selections.items():
        if selection['carrier'] != dict(carrier.identity):
            raise ValueError('Selected member belongs to a different carrier')
        chosen = {}
        if not selection['members']:
            raise ValueError('An empty selection is not a completed domain')
        for name, expected in selection['members'].items():
            safe_name(name)
            if name not in carrier.members or name in ('IDENTITY.json', 'MANIFEST.json'):
                raise ValueError('Selected scientific member absent')
            check_pin(carrier.members[name], expected)
            chosen[name] = carrier.members[name]
        pending[role] = MappingProxyType(chosen)
    return MappingProxyType({'roles': MappingProxyType(pending),
                             'carrier': carrier.identity,
                             'latest_invocation': MappingProxyType(dict(latest_invocation)),
                             'original_anchors': bytes(anchor_bytes),
                             'new_native_fits': 0, 'new_forecasts': 0})


def write_source(namespace, payload):
    """Make the version, cycle and source role explicit at both ends."""
    if (set(namespace) != {'version', 'cycle', 'role'}
            or any(not isinstance(v, str) or not v for v in namespace.values())):
        raise ValueError('Explicit versioned namespace required')
    return {'namespace': dict(namespace), 'payload_pin': pin(payload), 'payload': bytes(payload)}


def read_source(envelope, expected_namespace):
    if envelope['namespace'] != expected_namespace:
        raise ValueError('Source reader and writer namespace mismatch')
    check_pin(envelope['payload'], envelope['payload_pin'])
    return envelope['payload']
