"""Project an exact public Git commit to a self-contained static FBS site.

The allowlist contains presentation files and sanitized reports only. Repository
navigation is rewritten to the exact source commit. No private workspace or
provider archive is traversed, and this does not refresh any observation.
"""
from pathlib import Path
import argparse
import hashlib
import gzip
import html
from html.parser import HTMLParser
import json
import posixpath
import re
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'https://github.com/alvaromendizabal/sports-edge-lab'
ASSETS = ('index.html','research.html','recovery.html','season.js','source-progress.js','dashboard.js',
          'recovery.js','dashboard.css','season-2026.json','evidence.json',
          'official-inventory.json','source-progress.json',
          'V024_AGGREGATE_2026-11-03.json','V025_OPERATIONAL_REVIEW_2026-11-03.json',
          'v013-native-research-2026-10-31.json',
          'models.html','models.js','model-registry.json','recovery-review.json',
          'injury-association.json','common-game-review.json',
          'frontier.html','frontier.js','frontier-games.json','frontier-review.json',
          'complete.html','complete.js','coverage.js','diagnostics.js','complete.css','complete-season.json',
          'complete-data.js','complete-history.js','development-data.js','development-2026.json','season-archive.html','three-season.json','three-season-data.js','optional-study.json','optional-study-data.js','catboost-study.json','catboost-study-data.js','source-health-v040.json','owner-neural-study.json','owner-neural-study-data.js','current-capture.json','current-capture-data.js','current-capture.js','game-center.js','current-capture-v043.json','current-capture-v043-data.js','current-capture-v044.json','current-capture-v044-data.js','changed-input-study-v044.json','changed-input-study-v044-data.js','current-capture-v045.json','current-capture-v045-data.js','changed-input-evaluation-v045.json','changed-input-evaluation-v045-data.js','research-method.js','observation-status-v046.json','observation-status-v046-data.js','market-status-v046.json','market-status-v046-data.js','ranking-research.js','ranking-research-v047.json','ranking-research-v047-data.js','market-status-v047.json','market-status-v047-data.js','source-status.js','source-status-v048.json','source-status-v048-data.js','market-status-v048.json','market-status-v048-data.js','forecast-evidence.js','source-status-v049.json','source-status-v049-data.js','market-status-v049.json','market-status-v049-data.js','evaluation-v049.json','evaluation-v049-data.js','forward-outlooks.js','forecast-access.js','execution-status-v051.json','execution-status-v051-data.js','execution-status-v052.json','execution-status-v052-data.js','forward-outlooks-v050.json','forward-outlooks-v050-data.js','source-status-v050.json','source-status-v050-data.js','market-status-v050.json','market-status-v050-data.js')
ASSETS += ('current.html','current-evidence.css','current-evidence.js',
           'current-evidence-v053.json.gz','current-evidence-v053-data.js',
           'execution-status-v053.json','execution-status-v053-data.js')
ASSETS += ('current-v053.html','current-evidence-v054.json.gz','current-evidence-v054-data.js',
           'current-evidence-v054.js','current-evidence-v054.css','execution-status-v054.json',
           'execution-status-v054-data.js','learned-mixture-evaluation-v054.json','README-history-v053.md')
ASSETS += ('engineering-v055.html','engineering-status-v055.json')
ASSETS += ('actual-owner-v055.json','actual-owner-v055-data.js')
ASSETS += ('actual-owner-v056.json','historical-contenders-v057.json')
ASSETS += ('latest-v071.html','latest-v071.js','latest-v071.css','latest-v071.json',
           'issued-v070-selected.csv','season-inventory-v071.csv',
           'V071_ACTUAL_V070_REVIEW_2026-11-12.md')
SOURCE_FILES = {'index.html':'latest-v071.html','season-archive.html':'index.html'}


def committed(commit, path):
    return subprocess.check_output(['git','show',f'{commit}:{path}'], cwd=ROOT)


def navigation(target, commit):
    u = urlsplit(html.unescape(target))
    if u.scheme or u.netloc:
        return target.replace(REPOSITORY+'/tree/main/',REPOSITORY+'/tree/'+commit+'/')
    if not u.path or u.path in ASSETS:
        return target
    path = posixpath.normpath(posixpath.join('docs/fbs',u.path))
    if path.startswith('../') or path.startswith('/'):
        raise ValueError('Navigation escaped public repository')
    committed(commit,path)  # No guessed or stale source destination.
    return REPOSITORY+'/blob/'+commit+'/'+path+('#'+u.fragment if u.fragment else '')


def export(commit, output):
    if re.fullmatch('[0-9a-f]{40}',commit) is None:
        raise ValueError('Full exact public source commit required')
    subprocess.run(['git','cat-file','-e',commit+'^{commit}'],cwd=ROOT,check=True)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    files=[]
    for name in ASSETS:
        source_name=SOURCE_FILES.get(name,name)
        body=committed(commit,'docs/fbs/'+source_name)
        if name.endswith('.html'):
            text=body.decode()
            text=re.sub(r'href="([^"]+)"',lambda m:'href="'+navigation(m.group(1),commit)+'"',text)
            note=(f'<div style="padding:18px 24px;font:12px/1.6 system-ui;background:#eef3f6;color:#385268">'
                  f'Published source <a href="{REPOSITORY}/tree/{commit}">{commit[:12]}</a> · '
                  'Dated analytical snapshot; publication does not refresh source data or prices. '
                  '<a href="published-snapshot.json">Publication provenance</a></div>')
            text=text.replace('</body>',note+'</body>');body=text.encode()
        (output/name).write_bytes(body)
        files.append({'name':name,'source_path':'docs/fbs/'+source_name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
    report=json.loads(committed(commit,'docs/fbs/complete-season.json'))
    development=json.loads(committed(commit,'docs/fbs/development-2026.json'))
    three=json.loads(committed(commit,'docs/fbs/three-season.json'))
    optional=json.loads(committed(commit,'docs/fbs/optional-study.json'))
    catboost=json.loads(committed(commit,'docs/fbs/catboost-study.json'))
    health=json.loads(committed(commit,'docs/fbs/source-health-v040.json'))
    neural=json.loads(committed(commit,'docs/fbs/owner-neural-study.json'))
    prior=json.loads(committed(commit,'docs/fbs/current-capture.json'))
    late=json.loads(committed(commit,'docs/fbs/current-capture-v043.json'))
    evening=json.loads(committed(commit,'docs/fbs/current-capture-v044.json'))
    latest=json.loads(committed(commit,'docs/fbs/current-capture-v045.json'))
    refresh=json.loads(committed(commit,'docs/fbs/changed-input-study-v044.json'))
    refresh_evaluation=json.loads(committed(commit,'docs/fbs/changed-input-evaluation-v045.json'))
    observation_status=json.loads(committed(commit,'docs/fbs/observation-status-v046.json'))
    market_status=json.loads(committed(commit,'docs/fbs/market-status-v046.json'))
    ranking_status=json.loads(committed(commit,'docs/fbs/ranking-research-v047.json'))
    latest_market=json.loads(committed(commit,'docs/fbs/market-status-v047.json'))
    current_status=json.loads(committed(commit,'docs/fbs/source-status-v048.json'))
    current_market=json.loads(committed(commit,'docs/fbs/market-status-v048.json'))
    newest_status=json.loads(committed(commit,'docs/fbs/source-status-v049.json'))
    newest_market=json.loads(committed(commit,'docs/fbs/market-status-v049.json'))
    owner_evaluations=json.loads(committed(commit,'docs/fbs/evaluation-v049.json'))
    current_outlooks=json.loads(committed(commit,'docs/fbs/forward-outlooks-v050.json'))
    newest_v050=json.loads(committed(commit,'docs/fbs/source-status-v050.json'))
    market_v050=json.loads(committed(commit,'docs/fbs/market-status-v050.json'))
    current_v053=json.loads(gzip.decompress(committed(commit,'docs/fbs/current-evidence-v053.json.gz')))
    manifest={'schema':'sports-edge-lab.public-fbs-snapshot.v3',
              'canonical_repository':REPOSITORY,'source_commit_sha':commit,
              'evidence_prepared_at':report['projection_prepared_at'],
              'schedule_observed_at':report['source_observed_at'],
              'schedule_capture_completed_at':report['capture_completed_at'],
              'retained_model_report_at':report['retained_model_report_at'],
              'report_source_sha256':report['source_report_sha256'],
              'publication_operation_scope':'STATIC_PRESENTATION_ONLY_OWNER_SCIENCE_REPORTED_SEPARATELY','counts':report['counts'],'new_fits':0,'new_issues':0,'new_provider_requests':0,
              'development_reconstruction':{'counts':development['counts'],'computed_at':development['computed_at'],'evidence_class':development['evidence_class'],'resume_work':development['resume_work'],'cumulative_work':development['cumulative_work'],'season_coverage':development['season_coverage'],'scientific_results_generated_at':development['scientific_results_generated_at'],'sources':development['sources']},
              'v042_retained_capture':{k:prior[k] for k in ('capture','counts','sources','new_fits','new_predictions','new_provider_requests','forecast_issued','promotion_allowed')},
              'v043_retained_capture':{k:late[k] for k in ('capture','counts','sources','new_fits','new_predictions','new_provider_requests','forecast_issued','promotion_allowed')},
              'v044_retained_capture':{k:evening[k] for k in ('capture','counts','sources','new_fits','new_predictions','new_provider_requests','forecast_issued','promotion_allowed')},
              'v046_current_market_census':{k:market_status[k] for k in ('schema','source_capture_physical','source_observed_at','target_rows','event_count','exact_display_bound_events','exact_display_bound_target_rows','source_available_t120_exact_identity_rows','source_available_t60_exact_identity_rows','qualified_model_cover_rows','new_scientific_evaluations')},
              'v051_execution_attempt':json.loads(committed(commit,'docs/fbs/execution-status-v051.json')),
              'v052_execution_attempt':json.loads(committed(commit,'docs/fbs/execution-status-v052.json')),
              'v050_source_check':newest_v050,
              'v050_current_outlook_coverage':{key:current_outlooks[key] for key in ('schema','source_observed_at','counts','qualification_note','owner_work','ranking_research','local_scientific_calculations')},
              'v050_current_market_census':{key:market_v050[key] for key in ('schema','source_observed_at','target_rows','event_count','exact_display_bound_events','exact_display_bound_target_rows','source_available_t120_exact_identity_rows','source_available_t60_exact_identity_rows','qualified_model_cover_rows')},
              'v049_source_check':newest_status,
              'v049_current_market_census':{k:newest_market[k] for k in ('schema','source_capture_physical','source_observed_at','target_rows','event_count','exact_display_bound_events','exact_display_bound_target_rows','source_available_t120_exact_identity_rows','source_available_t60_exact_identity_rows','qualified_model_cover_rows','new_scientific_evaluations')},
              'v049_owner_evaluation':{'capture':owner_evaluations['capture'],'evaluated_at':owner_evaluations['evaluated_at'],'evidence_class':owner_evaluations['evidence_class'],'forecast_issued':False,'promotion_allowed':False,'local_scientific_calculations':0,'owner_metric_cohorts':{k:len(v['rows']) for k,v in owner_evaluations['scopes'].items()}},
              'v048_source_check':current_status,
              'v048_current_market_census':{k:current_market[k] for k in ('schema','source_capture_physical','source_observed_at','target_rows','event_count','exact_display_bound_events','exact_display_bound_target_rows','source_available_t120_exact_identity_rows','source_available_t60_exact_identity_rows','raw_source_available_t120_rows','raw_source_available_t60_rows','qualified_model_cover_rows','new_scientific_evaluations','original_selector_replay_status')},
              'v047_current_market_census':{k:latest_market[k] for k in ('schema','source_capture_physical','source_observed_at','target_rows','event_count','exact_display_bound_events','exact_display_bound_target_rows','source_available_t120_exact_identity_rows','source_available_t60_exact_identity_rows','raw_source_available_t120_rows','raw_source_available_t60_rows','qualified_model_cover_rows','new_scientific_evaluations','original_selector_replay_status')},
              'v047_ranking_source_census':{k:ranking_status[k] for k in ('schema','capture','counts','fixture_result_equivalence','feature_counts','ranking_request_count','owner_status','new_fit_count','new_prediction_count','no_new_metrics_computed','raw_rows_public')},
              'v046_latest_observation_status':{k:observation_status[k] for k in ('schema','counts','source_observed_at','original2026_source_observed_at','capture_completed_at','scientific_metrics','original_numeric_assets_modified','new_unissued_numeric_grids_public','actual_new_fits_in_this_export')},
              'v045_latest_evaluated_capture':{k:latest[k] for k in ('capture','counts','sources','new_fits','new_predictions','new_provider_requests','forecast_issued','promotion_allowed')},
              'v045_refresh_evaluation':{k:refresh_evaluation[k] for k in ('counts','sources','generated_at','evidence_class','forecast_issued','promotion_allowed')},
              'v044_recovered_changed_input_study':{k:refresh[k] for k in ('counts','sources','generated_at','evidence_class','forecast_issued','promotion_allowed')},
              'v041_original_owner_neural':{k:neural[k] for k in ('counts','sources','generated_at','evidence_class','forecast_issued','promotion_allowed')},
              'v040_catboost_study':{k:catboost[k] for k in ('counts','sources','generated_at','evidence_class','forecast_issued','promotion_allowed')},
              'v040_source_health':{k:health[k] for k in ('source_pin','return_pin','return_status','last_observed_at','provider_coverage_expansion_credited')},
              'v039_optional_study':{k:optional[k] for k in ('counts','sources','generated_at','evidence_class','forecast_issued','promotion_allowed')},
              'three_season_explorer':{k:three[k] for k in ('identified_games','predicted_games','seasons','sources','new_fits','new_provider_requests','new_issues')},
              'publication_is_not_source_refresh':True,'public_files':files}
    manifest['primary_dashboard_source']='docs/fbs/latest-v071.html'
    actual_v070=json.loads(committed(commit,'docs/fbs/latest-v071.json'))
    manifest['actual_v070_selected_report']={k:actual_v070[k] for k in (
        'schema','actual_owner_release','source_as_of_utc','source_capture_started_at',
        'source_capture_completed_at','source_owner_return_sha256','run_counts','refresh',
        'parallel_work','season_coverage','champions','publication')}
    manifest['earlier_current_dashboard_retained_at']='current.html'
    manifest['current_evidence_v053']={k:current_v053[k] for k in ('as_of','source_observed_at',
        'source_capture_completed_at','source_owner_delivery_accepted','source_authenticated',
        'official_games','season_counts','execution','provider_capture','saved_r12_comparison')}
    current_v054=json.loads(gzip.decompress(committed(commit,'docs/fbs/current-evidence-v054.json.gz')))
    manifest['current_evidence_v054']={k:current_v054[k] for k in ('as_of','source_observed_at',
        'source_capture_completed_at','official_games','season_counts','execution','provider_capture')}
    manifest['v056_actual_owner']=json.loads(committed(commit,'docs/fbs/actual-owner-v056.json'))
    manifest['v057_historical_contenders']=json.loads(committed(commit,'docs/fbs/historical-contenders-v057.json'))
    manifest['v055_actual_owner']=json.loads(committed(commit,'docs/fbs/actual-owner-v055.json'))
    manifest['v055_engineering_preparation']=json.loads(committed(commit,'docs/fbs/engineering-status-v055.json'))
    manifest['v053_preserved_interactive_view']='current-v053.html'
    manifest['earlier_dashboard_retained_at']='complete.html'
    (output/'published-snapshot.json').write_text(json.dumps(manifest,indent=2)+'\n')
    class Assets(HTMLParser):
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            for key in (['href'] if tag in ['a','link'] else ['src'] if tag in ['script','img'] else []):
                value=attrs.get(key)
                if not value:continue
                u=urlsplit(value)
                if not u.scheme and not u.netloc and u.path and not (output/u.path).is_file():
                    raise ValueError('Unpublished relative asset '+value)
    for name in ASSETS:
        if name.endswith('.html'):Assets().feed((output/name).read_text())
    return manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    result=export(args.commit,args.output)
    print(json.dumps({'source_commit':args.commit,'public_assets':len(result['public_files']),
                      'new_provider_calls':0,'owner_model_fits':0}))





