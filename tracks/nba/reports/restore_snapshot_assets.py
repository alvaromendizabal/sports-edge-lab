"""Restore complete pinned JSON files from lossless repository gzip assets.

This is file transport only. No source acquisition, inference or scoring occurs.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import tempfile

ROOT=Path(__file__).resolve().parent
MANIFEST='snapshot_asset_manifest.json'
SCHEMA='sports-edge-lab.lossless-json-assets.v1'
def file_pin(path):
    h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
    return {'bytes':size,'sha256':h.hexdigest()}
def restore(root=ROOT):
    root=Path(root);manifest=json.loads((root/MANIFEST).read_bytes())
    if manifest.get('schema')!=SCHEMA or manifest.get('lossy_projection') is not False:raise ValueError('JSON_ASSET_SCHEMA')
    receipts=[]
    for row in manifest['files']:
        name=row['name']
        if Path(name).name!=name or not name.endswith('.json') or row['gzip_name']!=name+'.gz':raise ValueError('JSON_ASSET_NAME')
        source=root/row['gzip_name'];target=root/name
        if source.is_symlink() or target.is_symlink():raise ValueError('JSON_ASSET_SYMLINK')
        if file_pin(source)!=row['gzip_pin']:raise ValueError('JSON_ASSET_COMPRESSED_PIN_CHANGED')
        if target.exists():
            if file_pin(target)!=row['original_pin']:raise ValueError('JSON_ASSET_EXISTING_ORIGINAL_CHANGED')
            receipts.append({'name':name,'status':'EXACT_ORIGINAL_REUSED','pin':row['original_pin']});continue
        temp=None
        try:
            with tempfile.NamedTemporaryFile(prefix='verified-json-',suffix='.part',dir=root,delete=False) as output:
                temp=Path(output.name)
                with gzip.open(source,'rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):output.write(block)
                output.flush();os.fsync(output.fileno())
            if file_pin(temp)!=row['original_pin']:raise ValueError('JSON_ASSET_ORIGINAL_PIN_CHANGED')
            if target.exists():raise ValueError('JSON_ASSET_TARGET_APPEARED_DURING_RESTORE')
            os.replace(temp,target);temp=None
            receipts.append({'name':name,'status':'EXACT_ORIGINAL_RESTORED','pin':row['original_pin']})
        finally:
            if temp is not None:temp.unlink(missing_ok=True)
    return {'status':'PASS','schema':SCHEMA,'files':receipts,'new_sports_computation':False,'network_requests':0}
if __name__=='__main__':print(json.dumps(restore(),sort_keys=True))
