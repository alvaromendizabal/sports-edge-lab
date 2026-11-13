"""Lossless, deterministic standalone HTML transport; never change saved data.

Only script blocks are encoded. The browser restores the original scripts in
their original order after byte-length and SHA-256 verification. All source
JSON files remain available separately. This module performs no sports work.
"""
from __future__ import annotations
import base64
import gzip
import hashlib
import json
import re

SCHEMA='sports-edge-lab.lossless-standalone-html.v1'
START='<!-- SEL LOSSLESS SCRIPT TRANSPORT BEGIN -->'
END='<!-- SEL LOSSLESS SCRIPT TRANSPORT END -->'
SCRIPT=re.compile(r'<script\b[^>]*>.*?</script\s*>',re.S|re.I)
CARRIER=re.compile(r'<script type="application/octet-stream" data-sel-gzip="(\d+)">([A-Za-z0-9+/=]+)</script>')
MANIFEST=re.compile(r'<script id="sel-offline-payload-manifest" type="application/json">(.*?)</script>',re.S)

BOOT=r'''<aside id="sel-offline-ready" role="status" data-state="loading"><strong>Loading the complete saved research snapshot…</strong> All data is contained in this file. No network request is needed. If this browser does not support secure SHA-256 and gzip decompression, use a current browser or open <a href="latest_research_outputs.json">the complete selected-output JSON</a>, <a href="latest_model_review.json">saved model metrics</a> and <a href="latest_v9_acceptance.json">coverage evidence</a>.</aside>
<noscript>This saved dashboard requires JavaScript. The complete JSON downloads above retain all saved rows.</noscript>
<script id="sel-offline-loader">
(()=>{'use strict';const status=document.getElementById('sel-offline-ready');
window.__SEL_OFFLINE_READY__=false;window.__SEL_OFFLINE_ERROR__=null;
async function restore(){
 if(typeof DecompressionStream!=='function'||!globalThis.crypto?.subtle)throw Error('This browser does not support verified local decompression. Use the complete JSON links above.');
 const manifest=JSON.parse(document.getElementById('sel-offline-payload-manifest').textContent);
 const holders=[...document.querySelectorAll('script[data-sel-gzip]')];
 if(holders.length!==manifest.scripts.length)throw Error('Saved script count changed.');
 for(let i=0;i<holders.length;i++){
  const holder=holders[i],entry=manifest.scripts[i];
  if(Number(holder.dataset.selGzip)!==i||entry.index!==i)throw Error('Saved script order changed.');
  const zipped=Uint8Array.from(atob(holder.textContent),c=>c.charCodeAt(0));
  const bytes=new Uint8Array(await new Response(new Blob([zipped]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  if(bytes.byteLength!==entry.bytes)throw Error('Saved script length changed.');
  const sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(sha!==entry.sha256)throw Error('Saved script checksum changed.');
  const template=document.createElement('template');template.innerHTML=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
  const source=template.content.firstElementChild;
  if(!source||source.tagName!=='SCRIPT'||template.content.children.length!==1||source.hasAttribute('src'))throw Error('Unsupported saved script envelope.');
  const restored=document.createElement('script');for(const attr of source.attributes)restored.setAttribute(attr.name,attr.value);
  restored.textContent=source.textContent;holder.replaceWith(restored);
 }
 window.__SEL_OFFLINE_READY__=true;status.dataset.state='ready';status.textContent='Complete saved snapshot restored and verified locally. Data clocks shown below remain unchanged.';
}
restore().catch(error=>{window.__SEL_OFFLINE_ERROR__=String(error);status.dataset.state='error';const note=document.createElement('p');note.textContent='Unable to restore the interactive snapshot: '+String(error);status.append(note);});
})();</script>'''

def _sha(body):return hashlib.sha256(body).hexdigest()

def pack_html(body):
    if not isinstance(body,str):raise TypeError('HTML_TEXT_REQUIRED')
    if START in body or MANIFEST.search(body):
        expand_html(body)
        return body
    scripts=[]
    def replace(match):
        original=match.group().encode('utf-8');index=len(scripts)
        scripts.append({'index':index,'bytes':len(original),'sha256':_sha(original)})
        encoded=base64.b64encode(gzip.compress(original,compresslevel=9,mtime=0)).decode('ascii')
        return f'<script type="application/octet-stream" data-sel-gzip="{index}">{encoded}</script>'
    result=SCRIPT.sub(replace,body)
    manifest={'schema':SCHEMA,'original_html_bytes':len(body.encode()),'original_html_sha256':_sha(body.encode()),
              'scripts':scripts,'lossy_projection':False,'network_requests_required':0,'sports_computation':False}
    appendix=START+'\n<script id="sel-offline-payload-manifest" type="application/json">'+json.dumps(manifest,sort_keys=True,separators=(',',':'))+'</script>\n'+BOOT+'\n'+END
    # Appending after the preserved document keeps the exact original bytes
    # recoverable; HTML parsing places the status/loader in the document body.
    packed=result+appendix
    if expand_html(packed)!=body:raise ValueError('HTML_TRANSPORT_ROUNDTRIP_FAILED')
    return packed

def expand_html(body):
    if START not in body:
        if MANIFEST.search(body) or CARRIER.search(body):raise ValueError('HTML_TRANSPORT_ENVELOPE_MISSING')
        return body
    if body.count(START)!=1 or body.count(END)!=1 or not body.endswith(END):raise ValueError('HTML_TRANSPORT_ENVELOPE_CHANGED')
    original_part,appendix=body.split(START,1)
    matches=MANIFEST.findall(appendix)
    if len(matches)!=1:raise ValueError('HTML_TRANSPORT_MANIFEST_REQUIRED')
    manifest=json.loads(matches[0])
    if manifest.get('schema')!=SCHEMA or manifest.get('lossy_projection') is not False:raise ValueError('HTML_TRANSPORT_SCHEMA')
    seen=[]
    def replace(match):
        index=int(match.group(1))
        if index!=len(seen) or index>=len(manifest['scripts']):raise ValueError('HTML_TRANSPORT_SCRIPT_ORDER')
        entry=manifest['scripts'][index]
        original=gzip.decompress(base64.b64decode(match.group(2),validate=True))
        if entry!={'index':index,'bytes':len(original),'sha256':_sha(original)}:raise ValueError('HTML_TRANSPORT_SCRIPT_PIN_CHANGED')
        text=original.decode('utf-8')
        if SCRIPT.fullmatch(text) is None:raise ValueError('HTML_TRANSPORT_SCRIPT_ENVELOPE')
        seen.append(index);return text
    expanded=CARRIER.sub(replace,original_part)
    if len(seen)!=len(manifest['scripts']):raise ValueError('HTML_TRANSPORT_SCRIPT_COUNT')
    encoded=expanded.encode()
    if len(encoded)!=manifest['original_html_bytes'] or _sha(encoded)!=manifest['original_html_sha256']:
        raise ValueError('HTML_TRANSPORT_FULL_ORIGINAL_PIN_CHANGED')
    return expanded

def transport_receipt(packed):
    original=expand_html(packed);manifest=json.loads(MANIFEST.search(packed).group(1))
    return {'status':'LOSSLESS_ROUNDTRIP_VERIFIED','original_html_bytes':len(original.encode()),
        'packed_html_bytes':len(packed.encode()),'original_html_sha256':_sha(original.encode()),
        'packed_html_sha256':_sha(packed.encode()),'script_blocks':len(manifest['scripts']),
        'original_data_modified':False,'new_sports_fits':0,'network_requests_required':0}
