"""Public evidence index: issued cards never inherit reconstruction scores."""
import hashlib,json
from pathlib import Path
from point_markets import require
HERE=Path(__file__).resolve().parent

def build_registry():
    d=json.loads((HERE/'current_coverage.json').read_text())
    models=[]
    for model in d['model_sets']:
        mid=model.get('id',model.get('model_id')); records=[r for r in d['season_metrics'] if r['model_id']==mid]
        models.append({'id':mid,'label':model.get('label',model.get('model_label')),'kind':'PRESERVED_PUBLIC_STREAM','record_source':'current_coverage.json','records':records,'issued_resolved_games':None,'performance_status':'VERIFIED_PUBLISHED_COHORTS' if records else 'PERFORMANCE_NOT_PUBLISHED','qualification':'Each row has its own exact event cohort, cutoff and provider. Counts cannot be pooled across provider rows. Missing metrics are unavailable, not zero.'})
    for version in ('042','043','044','045','046','047'):
        name=f'current_issues_n{version}.json';p=HERE/name
        if not p.exists():continue
        for stream in json.loads(p.read_text())['streams']:
            models.append({'id':stream['id'],'label':stream['label'],'kind':'GENUINELY_ISSUED_EARLY_RESEARCH','record_source':name,'records':[],'issued_resolved_games':0,'issued_games':len(stream['cards']),'issue_at':stream['actual_issue_at'],'performance_status':'AWAITING_ISSUED_OUTCOMES','qualification':'These specific forward issues have no scored outcomes in this snapshot. Related historical reconstructions are different evidence; their scores are not assigned to this stream.'})
    for mid,label,name in [('experimental_injury_issue','Experimental injury challenger · Nov 4','injury_issue_n037.json'),('experimental_injury_refresh','Prior injury refresh · Nov 5, 00:10 UTC','injury_refresh_n039.json'),('experimental_injury_n040','Prior injury refresh · Nov 5, 01:21 UTC','injury_refresh_n040.json'),('experimental_injury_n041','Prior injury refresh · Nov 5, 02:26 UTC','injury_refresh_n041.json')]:
        models.append({'id':mid,'label':label,'kind':'GENUINELY_ISSUED_EARLY_RESEARCH','record_source':name,'records':[],'issued_resolved_games':0,'performance_status':'AWAITING_ISSUED_OUTCOMES','qualification':'Historical selected-injury metrics are linked separately; no resolved outcome of these specific forward cards has been added.'})
    for m in models:
        m['target_readiness']={target:{'status':'VERIFIED_PUBLISHED_COHORTS' if any(r['target']==target for r in m['records']) else 'PENDING_OR_UNAVAILABLE','missing_metrics_are_zero':False}for target in ('winner','margin','total')}
        # Legacy winner target uses win in some contracts.
        if any(r['target']=='win' for r in m['records']):m['target_readiness']['winner']['status']='VERIFIED_PUBLISHED_COHORTS'
        m['target_readiness']['spread_cover']={'status':'NOT_CALIBRATED_FOR_EXECUTABLE_LINE','reason':'A point margin alone is not a cover probability. No verified line-specific cover distribution, settlement/fee evaluation or promoted cover strategy is attached to this stream.'}
    for m in models:
        if m['id']=='n047_designation':m['target_readiness']['spread_cover']={'status':'ISSUED_UNVALIDATED_DISTRIBUTION_TRANSFER','reason':'Separate actual N047 derived intervals and threshold probabilities are published in cover_research_n047.json. Historical study metrics are separate from these unresolved forward issues; no executable, calibration or promotion claim.'}
    return {'schema':'sports-edge-lab.nfl.model-performance-registry.v1','models':models,'related_historical_studies':[{'source':'cover_research_n047.json','scope':'Selected margin distribution: 2024–26 annual/event/weekly retrospective evaluation and exact 2026 T1 strict-contract comparison, separate from unresolved current issues'},{'source':'injury_selected_metrics_n037.json','scope':'Selected injury reconstruction, separate from later forward issues'},{'source':'designation_metrics_n045.json','scope':'Selected annual/weekly/event designation reconstructions, T1 designation boundary; base parents retain T2'}],'rules':['No metric is reconstructed from rounded cards.','2024/25 research is development-exposed; 2026 rankings are descriptive monitoring.','NO BET in older cards is a research eligibility state, not evidence of a personal transaction. Actual bets are not recorded here.','Provider thresholds are not expected margins or total points.','The N047 spread-cover study completed its registered research; transfer calibration and prospective promotion remain unvalidated.']}

def load_registry():
    p=HERE/'model_performance_registry.json';d=json.loads(p.read_text());expected=build_registry()
    require(d==expected,'Model registry differs from published source evidence')
    ids=[m['id'] for m in d['models']];require(len(ids)==len(set(ids)),'Duplicate public model identity')
    for m in d['models']:
        if m['kind']=='GENUINELY_ISSUED_EARLY_RESEARCH':require(not m['records'] and m['issued_resolved_games']==0,'Forward stream borrowed historical scores')
        require(m['target_readiness']['spread_cover']['status']==('ISSUED_UNVALIDATED_DISTRIBUTION_TRANSFER' if m['id']=='n047_designation' else 'NOT_CALIBRATED_FOR_EXECUTABLE_LINE'),'Unsupported cover readiness')
    return d,{'model_registry_validation':'PASS','public_model_count':len(ids),'registry_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

if __name__=='__main__':
    p=HERE/'model_performance_registry.json';p.write_text(json.dumps(build_registry(),indent=2)+'\n');print(load_registry()[1])
