"""Credential-free transport demonstration; invented data, no sports model."""
import gzip
import hashlib
import json


def wire_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def wire_identity(value):
    return hashlib.sha256(wire_bytes(value)).hexdigest()


def validate_wire(value, expected):
    if wire_identity(value) != expected:
        raise ValueError('wire identity differs')


def read_gzip_spool(stream, maximum_bytes):
    """An input spool may be writable; the decompressor is explicitly read-only."""
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise ValueError('invalid read bound')
    with gzip.GzipFile(fileobj=stream, mode='rb') as reader:
        body = reader.read(maximum_bytes + 1)
    if len(body) > maximum_bytes:
        raise ValueError('expanded body exceeds bound')
    return body


def choose_receipt(embedded, legacy=None):
    """Two representations of the same source observation must agree."""
    if embedded is None:
        if legacy is None:
            raise ValueError('receipt missing')
        return legacy
    if legacy is not None and embedded != legacy:
        raise ValueError('conflicting receipts')
    return embedded
