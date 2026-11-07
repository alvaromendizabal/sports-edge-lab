"""Project an exact public Git commit to a self-contained static FBS site.

The allowlist contains presentation files and sanitized reports only. Repository
navigation is rewritten to the exact source commit. No private workspace or
provider archive is traversed, and this does not refresh any observation.
"""
from pathlib import Path
import argparse
import hashlib
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
          'complete.html','complete.js','complete.css','complete-season.json',
          'complete-data.js','complete-history.js','development-data.js','development-2026.json','season-archive.html')
SOURCE_FILES = {'index.html':'complete.html','season-archive.html':'index.html'}


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
    manifest={'schema':'sports-edge-lab.public-fbs-snapshot.v3',
              'canonical_repository':REPOSITORY,'source_commit_sha':commit,
              'evidence_prepared_at':report['projection_prepared_at'],
              'schedule_observed_at':report['source_observed_at'],
              'schedule_capture_completed_at':report['capture_completed_at'],
              'retained_model_report_at':report['retained_model_report_at'],
              'report_source_sha256':report['source_report_sha256'],
              'counts':report['counts'],'new_fits':0,'new_issues':0,'new_provider_requests':0,
              'development_reconstruction':{'counts':development['counts'],'computed_at':development['computed_at'],'evidence_class':development['evidence_class'],'resume_work':development['resume_work'],'cumulative_work':development['cumulative_work'],'season_coverage':development['season_coverage'],'scientific_results_generated_at':development['scientific_results_generated_at'],'sources':development['sources']},
              'publication_is_not_source_refresh':True,'public_files':files}
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

