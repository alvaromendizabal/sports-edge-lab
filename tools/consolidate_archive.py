"""Consolidate existing Sports Edge Lab archives without downloading again."""
import concurrent.futures, datetime, hashlib, json, sys, urllib.request, urllib.error
import boto3
from botocore.config import Config

REGION = 'us-west-2'
DEST = 'sagemaker-sports-edge-lab-560403859723-us-west-2'
CFG = Config(retries={'mode':'standard','max_attempts':4}, connect_timeout=10, read_timeout=60, max_pool_connections=20)

def main():
    s3=boto3.client('s3',region_name=REGION,config=CFG)
    rows=[]
    sources={s:'sagemaker-sports-edge-lab-'+s+'-560403859723-us-west-2' for s in ['nfl','nba','ncaaf','ncaam','ncaaw']}
    sources['legacy-nfl']='sagemaker-nfl-edge-lab-560403859723-us-west-2'
    for sport,bucket in sources.items():
        for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket):
            for obj in page.get('Contents',[]):
                prefix='tracks/'+sport+'/' if sport!='legacy-nfl' else 'infrastructure/legacy-nfl-archive/'
                rows.append((bucket,obj['Key'],prefix+obj['Key'],obj['Size']))
    def copy(row):
        source,key,dest,size=row
        head=s3.head_object(Bucket=source,Key=key)
        try:
            current=s3.head_object(Bucket=DEST,Key=dest)
        except s3.exceptions.ClientError as exc:
            if exc.response['Error']['Code'] not in ('404','NoSuchKey','NotFound'):
                raise
            current={}
        if current.get('ETag')!=head['ETag'] or current.get('ContentLength')!=size:
            s3.copy_object(CopySource={'Bucket':source,'Key':key},Bucket=DEST,Key=dest)
        check=s3.head_object(Bucket=DEST,Key=dest)
        assert check['ContentLength']==head['ContentLength']==size
        assert check.get('Metadata',{})==head.get('Metadata',{})
        # Multipart source ETags can differ even for identical bytes.
        if check['ETag']!=head['ETag']:
            def digest(bucket,name):
                h=hashlib.sha256()
                with s3.get_object(Bucket=bucket,Key=name)['Body'] as body:
                    while True:
                        chunk=body.read(1024*1024)
                        if not chunk: break
                        h.update(chunk)
                return h.hexdigest()
            assert digest(source,key)==digest(DEST,dest)
        return {'source_bucket':source,'source_key':key,'key':dest,'bytes':size,'etag':check['ETag'],'verified':True}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for i,r in enumerate(pool.map(copy,rows),1):
            results.append(r)
            if i%100==0: print(json.dumps({'stage':'migration','completed':i,'remaining':len(rows)-i}),flush=True)
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'objects_verified':len(results),'bytes':sum(x['bytes'] for x in results),'sources_deleted':False,'objects':results}
    # Runtime credential use only; never serialize the key or request URL.
    ssm=boto3.client('ssm',region_name=REGION,config=CFG)
    key=ssm.get_parameter(Name='/sports-edge-lab/shared/cfbd/key',WithDecryption=True)['Parameter']['Value']
    url='https://api.collegebasketballdata.com/games?season=2026&startDateRange=2026-03-01T00%3A00%3A00Z&endDateRange=2026-03-02T00%3A00%3A00Z'
    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+key,'User-Agent':'SportsEdgeLab/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            body=response.read()
            data=json.loads(body)
            report['cbbd_canary']={'status':response.status,'rows':len(data) if isinstance(data,list) else None}
            s3.put_object(Bucket=DEST,Key='tracks/ncaam/raw/paid/cbbd/canary_20260301.json',Body=body,ContentType='application/json',Metadata={'sha256':hashlib.sha256(body).hexdigest()})
    except urllib.error.HTTPError as exc:
        report['cbbd_canary']={'status':exc.code}
    s3.put_object(Bucket=DEST,Key='infrastructure/migrations/consolidation_20261016.json',Body=json.dumps(report).encode(),ContentType='application/json')
    print(json.dumps({k:v for k,v in report.items() if k!='objects'}),flush=True)
    return 0

if __name__=='__main__':
    sys.exit(main())
