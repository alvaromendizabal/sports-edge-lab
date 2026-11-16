"""Verify every canonical N123 response anonymously and diagnose mismatched HTTP bodies."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from html import unescape
from pathlib import Path
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/'
HEADERS = {'User-Agent': 'SportsEdgeLab-PublicReleaseVerification/1.0', 'Cache-Control': 'no-cache'}


def observe(url, expected, expected_body):
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=35)
    except urllib.error.HTTPError as error:
        response = error
    except (OSError, ValueError) as error:
        return {'url': url, 'error': type(error).__name__, 'matches': False}
    with response:
        body = response.read()
        digest = sha256(body).hexdigest()
        head = body[:16000].decode('utf-8', errors='replace')
        title = re.search(r'<title[^>]*>\s*(.*?)\s*</title\s*>', head, re.I | re.S)
        dest = urllib.parse.urlsplit(response.geturl())
        record = {
            'url':url, 'status':response.status, 'final_host':dest.hostname, 'final_path':dest.path,
            'bytes':len(body), 'sha256':digest, 'expected_sha256':expected,
            'matches':response.status == 200 and digest == expected,
            'content_type':response.headers.get('Content-Type'),
            'cache':{key:response.headers.get(key) for key in ('Age','Cache-Control','CF-Cache-Status','Content-Encoding','Vary','Server') if key in response.headers},
        }
        if title:
            record['html_title']=unescape(' '.join(title.group(1).split()))[:180]
        if not record['matches']:
            fingerprints = ['<html','<meta','cloudflare','login','sign in','captcha','just a moment','<script','Circa Million Picks','N123']
            record['html_markers']=[m for m in fingerprints if m.lower() in head.lower()]
            common_prefix=next((i for i,(a,b) in enumerate(zip(body,expected_body)) if a!=b),min(len(body),len(expected_body)))
            common_suffix=next((i for i,(a,b) in enumerate(zip(reversed(body),reversed(expected_body))) if a!=b),min(len(body),len(expected_body)))
            record['common_prefix_bytes']=common_prefix
            record['common_suffix_bytes']=min(common_suffix,min(len(body),len(expected_body))-common_prefix)
            record['expected_bytes']=len(expected_body)
            if 'html' in (record['content_type'] or ''):
                html=body.decode('utf-8',errors='replace')
                record['script_paths']=[urllib.parse.urlsplit(src).path[:150] for src in re.findall(r'''<script\b[^>]*\bsrc=["']([^"']+)''',html,re.I)][:12]
                record['has_n123_text_anywhere']='N123' in html
                record['is_verbatim_embedded_asset']=expected_body in body
        return record


def main():
    here=Path(__file__).resolve().parent
    public=here/'n123_current' if (here/'n123_current').is_dir() else here/'public'
    pairs=[(BASE, public/'index.html')]
    pairs.extend((BASE+'n123/'+('' if f.name=='index.html' else f.name),f) for f in sorted(public.iterdir()) if f.name!='README.md')

    def probe(pair):
        url, asset=pair
        expected_body=asset.read_bytes()
        expected=sha256(expected_body).hexdigest()
        observations=[]
        for attempt in range(3):
            if attempt:
                time.sleep(2*attempt)
            observation=observe(url, expected, expected_body)
            observations.append(observation)
            if observation['matches']:
                break
        row={'url':url,'canonical':observations,'passed':observations[-1]['matches']}
        if not row['passed'] and asset.name=='index.html':
            row['cache_busted_diagnostic']=observe(url+'?release_sha256='+expected,expected,expected_body)
            row['explicit_index_diagnostic']=observe(url+'index.html',expected,expected_body)
        return row

    with ThreadPoolExecutor(max_workers=6) as pool:
        receipts=list(pool.map(probe,pairs))
    print(json.dumps({'canonical_responses':len(receipts), 'verified':sum(r['passed'] for r in receipts), 'receipts':receipts},indent=2),flush=True)
    failures=[r['url'] for r in receipts if not r['passed']]
    if failures:
        raise SystemExit('Canonical responses failed strict status/SHA-256 checks: '+', '.join(failures))


if __name__=='__main__':
    main()
