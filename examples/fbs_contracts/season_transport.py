"""Lossless public transport for repeated reference records; no data removal.

Column names occur once. Consumers expand the exact values before the existing
scientific, provenance and public-field validation. This is serialization only.
"""
from copy import deepcopy

SCHEMA='fbs.public.season-explorer.transport.v1'
REFERENCE_FIELDS=tuple(sorted(('target','value','picked_home','quote_at','captured_at',
    'reference_kind','product','evidence_kind','identity_basis','join_status',
    'event_url','executable','interval_end_at','price_status','clock_basis',
    'source_status','source_status_field','point_support','registered_cutoff_kind',
    'source_query_cutoff_kind')))


def pack(data):
    report=deepcopy(data)
    for game in report['games']:
        for provider,records in game['markets'].items():
            if any(set(row)!=set(REFERENCE_FIELDS) for row in records):
                raise ValueError('Unexpected field cannot enter reference transport')
            game['markets'][provider]=[[row[key] for key in REFERENCE_FIELDS] for row in records]
    return {'schema':SCHEMA,'reference_fields':list(REFERENCE_FIELDS),'report':report}


def unpack(data):
    if data.get('schema')=='fbs.public.season-explorer.v1':
        return data
    if set(data)!={'schema','reference_fields','report'} or data['schema']!=SCHEMA:
        raise ValueError('Unknown season transport')
    if data['reference_fields']!=list(REFERENCE_FIELDS):
        raise ValueError('Reference column identity differs')
    report=deepcopy(data['report'])
    for game in report['games']:
        for provider,records in game['markets'].items():
            if any(not isinstance(row,list) or len(row)!=len(REFERENCE_FIELDS) for row in records):
                raise ValueError('Reference column count differs')
            game['markets'][provider]=[dict(zip(REFERENCE_FIELDS,row,strict=True)) for row in records]
    return report
