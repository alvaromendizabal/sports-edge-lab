/* Verify and expand exact standalone bytes for independent offline oracles. */
'use strict';
const zlib=require('node:zlib'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const BEGIN='<!-- SEL LOSSLESS SCRIPT TRANSPORT BEGIN -->',END='<!-- SEL LOSSLESS SCRIPT TRANSPORT END -->';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
function expandHtml(input){const html=input.toString();if(!html.includes(BEGIN))return html;
 assert.ok(html.endsWith(END));const split=html.split(BEGIN);assert.equal(split.length,2);
 const matches=[...split[1].matchAll(/<script id="sel-offline-payload-manifest" type="application\/json">(.*?)<\/script>/gs)];assert.equal(matches.length,1);
 const manifest=JSON.parse(matches[0][1]);assert.equal(manifest.schema,'sports-edge-lab.lossless-standalone-html.v1');assert.equal(manifest.lossy_projection,false);
 let count=0;const expanded=split[0].replace(/<script type="application\/octet-stream" data-sel-gzip="(\d+)">([A-Za-z0-9+/=]+)<\/script>/g,(_,index,encoded)=>{
 assert.equal(Number(index),count);const body=zlib.gunzipSync(Buffer.from(encoded,'base64')),entry=manifest.scripts[count++];assert.deepEqual(entry,{index:Number(index),bytes:body.length,sha256:hash(body)});return body.toString('utf8');});
 assert.equal(count,manifest.scripts.length);assert.equal(Buffer.byteLength(expanded),manifest.original_html_bytes);assert.equal(hash(expanded),manifest.original_html_sha256);return expanded;
}
module.exports={expandHtml};
