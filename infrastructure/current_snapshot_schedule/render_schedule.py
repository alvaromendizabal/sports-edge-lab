"""Bind reviewed v026 manifest to bounded AWS Scheduler API inputs; no AWS calls."""
import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACCOUNT = '560403859723'
REGION = 'us-west-2'
GROUP = 'sports-edge-lab-ingestion'
SCHEDULE = 'sports-edge-lab-current-6h-20261017-v026'
ROLE = 'SportsEdgeLabCurrentSchedulerRole'
BUCKET = 'sagemaker-sports-edge-lab-560403859723-us-west-2'
PROCESSING_ROLE = f'arn:aws:iam::{ACCOUNT}:role/SportsEdgeLabProcessingRole'
START = '2026-10-17T03:00:00Z'
END = '2026-11-16T03:04:59Z'

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--s3-key')
    a = parser.parse_args()
    m = json.loads(a.manifest.read_text())
    artifact = Path(m['artifact'])
    blob = artifact.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == m['sha256'], 'Artifact hash mismatch'
    assert len(blob) == m['bytes'], 'Artifact size mismatch'
    assert 'v026' in artifact.name, 'Expected reviewed current v026 artifact'
    key = a.s3_key or m.get('s3_key')
    assert isinstance(key,str), 'An exact uploaded S3 key is required'
    assert key.startswith('infrastructure/code/') and key.endswith('/' + artifact.name)
    args = m.get('container_arguments',m.get('arguments'))
    assert isinstance(args,list) and all(isinstance(x,str) for x in args)
    def arg(name):
        assert args.count(name) == 1, f'Expected one {name}'
        return args[args.index(name)+1]
    assert int(arg('--odds-credits')) <= 500
    assert int(arg('--stats-calls')) <= 100
    assert int(arg('--max-seconds')) <= 600
    assert int(arg('--workers')) <= 4
    assert int(arg('--props-per-track')) <= 12
    tags = [{'Key':'Project','Value':'sports-edge-lab'},
            {'Key':'Workstream','Value':'current-paid-data'},
            {'Key':'Environment','Value':'dev'},
            {'Key':'Schedule','Value':SCHEDULE}]
    job = {
        'ProcessingJobName':'sports-edge-lab-current-<aws.scheduler.execution-id>',
        'RoleArn':PROCESSING_ROLE,
        'AppSpecification':{
            'ImageUri':'246618743249.dkr.ecr.us-west-2.amazonaws.com/sagemaker-scikit-learn:1.9-0',
            'ContainerEntrypoint':['python3','-u',f'/opt/ml/processing/code/{artifact.name}'],
            'ContainerArguments':args},
        'Environment':{
            'SEL_SCHEDULED_TIME':'<aws.scheduler.scheduled-time>',
            'SEL_SCHEDULER_EXECUTION_ID':'<aws.scheduler.execution-id>',
            'SEL_SCHEDULE_ARN':'<aws.scheduler.schedule-arn>'},
        'ProcessingInputs':[{'InputName':'code','S3Input':{
            'S3Uri':f's3://{BUCKET}/{key.rsplit("/",1)[0]}/',
            'LocalPath':'/opt/ml/processing/code','S3DataType':'S3Prefix',
            'S3InputMode':'File','S3DataDistributionType':'FullyReplicated'}}],
        'ProcessingResources':{'ClusterConfig':{'InstanceCount':1,
            'InstanceType':'ml.m5.2xlarge','VolumeSizeInGB':30}},
        'StoppingCondition':{'MaxRuntimeInSeconds':900},
        'NetworkConfig':{'EnableNetworkIsolation':False},
        'Tags':tags}
    schedule = {
        'Name':SCHEDULE,'GroupName':GROUP,'ClientToken':SCHEDULE,
        'Description':'Current sports odds and statistics every 6 hours, 120 slots maximum, 500 odds credits and 100 statistics calls per run; expires 2026-11-16.',
        'ScheduleExpression':'cron(5 3,9,15,21 * * ? *)',
        'ScheduleExpressionTimezone':'UTC','StartDate':START,'EndDate':END,
        'FlexibleTimeWindow':{'Mode':'OFF'},'State':'ENABLED',
        'ActionAfterCompletion':'DELETE',
        'Target':{
            'Arn':'arn:aws:scheduler:::aws-sdk:sagemaker:createProcessingJob',
            'RoleArn':f'arn:aws:iam::{ACCOUNT}:role/{ROLE}',
            'Input':json.dumps(job,separators=(',',':')),
            'RetryPolicy':{'MaximumRetryAttempts':0,'MaximumEventAgeInSeconds':60}}}
    trust=json.loads((ROOT/'current_scheduler_trust.json').read_text())
    policy=json.loads((ROOT/'current_scheduler_permissions.json').read_text())
    slots=[]
    d=datetime(2026,10,17,3,5,tzinfo=timezone.utc)
    end=datetime.fromisoformat(END.replace('Z','+00:00'))
    while d < end:
        slots.append(d.isoformat())
        d+=timedelta(hours=6)
    assert len(slots)==120
    assert policy['Statement'][0]['Condition']['StringEquals']['aws:RequestTag/Schedule']==SCHEDULE
    assert all(x['Condition']['DateLessThan']['aws:CurrentTime']==END for x in policy['Statement'])
    write('create_current_role.json', {'RoleName':ROLE,
        'Description':'Launch only bounded current Sports Edge Lab acquisition jobs until 2026-11-16.',
        'AssumeRolePolicyDocument':json.dumps(trust,separators=(',',':')),
        'Tags':[{'Key':'Project','Value':'sports-edge-lab'},{'Key':'Environment','Value':'dev'}]})
    write('put_current_role_policy.json', {'RoleName':ROLE,'PolicyName':'LaunchBoundedCurrentJobsUntil20261116',
        'PolicyDocument':json.dumps(policy,separators=(',',':'))})
    write('create_current_schedule.json',schedule)
    write('current_processing_target.json',job)
    write('get_current_schedule.json',{'Name':SCHEDULE,'GroupName':GROUP})
    write('schedule_budget_and_artifact.json',{
        'manifest':str(a.manifest.resolve()),'artifact':artifact.name,
        'sha256':m['sha256'],'bytes':m['bytes'],'s3_bucket':BUCKET,'s3_key':key,
        'schedule_slots':len(slots),'first_trigger_utc':slots[0],'last_trigger_utc':slots[-1],
        'maximum_scheduled_odds_credits':len(slots)*int(arg('--odds-credits')),
        'maximum_scheduled_stats_calls':len(slots)*int(arg('--stats-calls')),
        'maximum_job_runtime_hours':len(slots)*900/3600,
        'reported_runtime_compute_estimate_usd':len(slots)*900/3600*0.461,
        'estimate_excludes':'Startup/billing differences, storage/requests, subscriptions, other jobs.',
        'prior_ncaa_schedule_changed':False,
        'aws_schedule_created':False})
    print(json.dumps({'schedule':SCHEDULE,'slots':len(slots),'sha256':m['sha256'],'output':str(ROOT)}))

if __name__=='__main__':
    main()
