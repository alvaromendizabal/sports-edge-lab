"""Keep the latest execution attempt separate from the retained dated science."""
import argparse,hashlib,json,pathlib
from build_review_n050 import validate as validate_retained
ROOT=pathlib.Path(__file__).resolve().parent


def retained():
    raw=(ROOT/'current_review_n050.json').read_bytes()
    return raw,validate_retained(json.loads(raw))


def validate(review):
    if review['schema']!='nfl.public.n050-actual-n051-readiness.v1':raise ValueError('schema')
    raw,data=retained();p=review['retained_snapshot']
    if p!={'file':'current_review_n050.json','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'evidence_as_of':data['as_of']}:raise ValueError('retained snapshot binding')
    actual=review['latest_owner_attempt']
    if actual['milestone']!='N050' or actual['status']!='FAILED' or actual['owner_research_accepted']:raise ValueError('actual execution state')
    for key in ['completed_scientific_stages','new_native_fits','new_target_forecasts','new_source_acquisitions','paid_provider_calls','protected_original_refits','actual_orders']:
        if actual[key]!=0:raise ValueError('unearned execution credit: '+key)
    archive=actual['return_archive'];completion=actual['later_external_completion']
    if archive!={'bytes':951839,'sha256':'173c84452261fda39d84433df7a7fab1c3d8c5ddb83835ecfd6c5f05c8beb0b5','safe_regular_members':346,'payload_members':345,'crc_and_manifest_closure':'PASS'}:raise ValueError('archive proof')
    if completion['bytes']!=1220 or completion['sha256']!='5adf28de10df8d4f6de1acb8552f116c200319a6b8baadfb35b5cb83effcfc6d':raise ValueError('external completion proof')
    if completion['final_return_readback_at']<=actual['finished_at']:raise ValueError('later completion required')
    upcoming=review['next']
    if upcoming['milestone']!='N051' or upcoming['status']!='PREPARED_NOT_OWNER_EXECUTED':raise ValueError('next state')
    if upcoming['owner_native_fits'] or upcoming['owner_forecasts']:raise ValueError('preparation cannot award owner execution')
    if (upcoming['annual_designation_cells_planned'],upcoming['paired_control_comparisons_if_complete'])!=(144,864):raise ValueError('registration counts')
    if any(upcoming[k] for k in ['automatic_promotion','repeated_completed_injury_study','unrestricted_history_acquisition']):raise ValueError('research scope')
    return review


def build(review):
    validate(review)
    envelope={'review':review,'retained_snapshot':retained()[1]}
    payload=json.dumps(envelope,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return (ROOT/'review_n051.template.html').read_text().replace('__SNAPSHOT_JSON__',payload)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    expected=build(json.loads((ROOT/'current_review_n051.json').read_text()));output=ROOT/'review_n051.html'
    if args.check:
        if output.read_text()!=expected:raise SystemExit('Current review differs from dated snapshot and template')
        print('N051 current review deterministic check: PASS')
    else:output.write_text(expected)
