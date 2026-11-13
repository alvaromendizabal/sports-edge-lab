"""Embed exact original JSON download bytes and keep gzip fallbacks available."""
from pathlib import Path
import base64
import hashlib
import json
import re
from b083_html import pack_html,expand_html,START
from restore_snapshot_assets import restore,ROOT
BEGIN='<!-- SEL COMPLETE JSON DOWNLOADS BEGIN -->'
END='<!-- SEL COMPLETE JSON DOWNLOADS END -->'

def attach_downloads(body):
    body=expand_html(body)
    if body.count(BEGIN)!=body.count(END) or body.count(BEGIN)>1:raise ValueError('JSON_DOWNLOAD_SECTION_CHANGED')
    clean=re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+'\n?','',body,flags=re.S)
    restore(ROOT);manifest=json.loads((ROOT/'snapshot_asset_manifest.json').read_bytes())
    files=[]
    for row in manifest['files']:
        encoded=base64.b64encode((ROOT/row['gzip_name']).read_bytes()).decode()
        files.append({**row,'gzip_base64':encoded})
    data=json.dumps(files,sort_keys=True,separators=(',',':'))
    section=BEGIN+'''
<section id="sel-complete-downloads"><h2>Complete saved JSON downloads</h2>
<p>Download the exact original JSON bytes verified against their saved SHA-256. These files contain the full selected output and coverage exports. No field, row or source clock is removed by compression.</p>
<p><a href="latest_research_outputs.json.gz" data-sel-json="latest_research_outputs.json">Download complete selected-output JSON</a> · <a href="latest_v9_acceptance.json.gz" data-sel-json="latest_v9_acceptance.json">Download complete V9 coverage JSON</a></p>
<p>Compressed alternatives, including browsers without local decompression: <a href="latest_research_outputs.json.gz" download>Selected-output JSON.gz</a> · <a href="latest_v9_acceptance.json.gz" download>V9 coverage JSON.gz</a> · <a href="snapshot_asset_manifest.json">Exact original and compressed file checksums</a>.</p>
<p id="sel-json-download-status" role="status"></p>
<script id="sel-json-download-data" type="application/json">'''+data+'''</script>
<script>(()=>{'use strict';const files=JSON.parse(document.getElementById('sel-json-download-data').textContent),byName=new Map(files.map(row=>[row.name,row]));
async function bytes(row){const zipped=Uint8Array.from(atob(row.gzip_base64),c=>c.charCodeAt(0)),value=new Uint8Array(await new Response(new Blob([zipped]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
 const sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',value))].map(n=>n.toString(16).padStart(2,'0')).join('');if(value.length!==row.original_pin.bytes||sha!==row.original_pin.sha256)throw Error('Original JSON checksum changed.');return value;}
document.addEventListener('click',async event=>{const link=event.target.closest('a');if(!link)return;const name=link.dataset.selJson||link.getAttribute('href');const row=byName.get(name);if(!row)return;event.preventDefault();const status=document.getElementById('sel-json-download-status');status.textContent='Verifying complete '+name+'…';try{const value=await bytes(row),url=URL.createObjectURL(new Blob([value],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);status.textContent='Downloaded exact '+name+'; '+value.length+' bytes; SHA-256 '+row.original_pin.sha256+'.';}catch(error){status.textContent='Unable to create JSON download: '+String(error)+'. Use the complete gzip download links.';}});
})();</script>
</section>
'''+END+'\n'
    if clean.count('</body>')!=1:raise ValueError('JSON_DOWNLOAD_BODY_REQUIRED')
    return clean.replace('</body>',section+'</body>',1)

def pack_public_html(body):
    packed=pack_html(attach_downloads(body));before,appendix=packed.split(START,1)
    # Generic private exporters retain real raw JSON files. This public storage
    # adapter gives only its fallback links the corresponding committed gzip names.
    for name in ('latest_research_outputs.json','latest_v9_acceptance.json'):
        appendix=appendix.replace('href="'+name+'"','href="'+name+'.gz"')
    result=before+START+appendix
    if expand_html(result)!=expand_html(packed):raise ValueError('JSON_DOWNLOAD_ORIGINAL_HTML_CHANGED')
    return result
