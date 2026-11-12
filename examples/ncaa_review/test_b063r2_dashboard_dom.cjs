// Executes the exact generated inline script. This is DOM behavior, not browser layout proof.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../docs/ncaa/b063r2.html'),'utf8');
const payload=JSON.parse(html.match(/<script id="b063r2-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
class Element {
 constructor(){this.value='';this.innerHTML='';this.textContent='';this.listeners={};this.disabled=false;}
 addEventListener(event,fn){this.listeners[event]=fn;}
 fire(event){assert.ok(this.listeners[event]);this.listeners[event]();}
 click(){if(!this.disabled&&this.listeners.click)this.listeners.click();}
}
const elements=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
const el=id=>{assert.ok(elements.has(id),id);return elements.get(id);};
el('b063r2-data').textContent=JSON.stringify(payload);
for(const id of ['league','season','objective'])el(id).value='all';
let lastBlob=null;
class FixtureURL extends URL {
 static createObjectURL(blob){lastBlob=blob;return 'blob:fixture';}
 static revokeObjectURL(){}
}
const window={};
vm.runInNewContext(script,{document:{getElementById:el,createElement:tag=>{assert.equal(tag,'a');return new Element();}},
 Blob:class {constructor(parts){this.text=parts.join('');}},URL:FixtureURL,setTimeout:fn=>fn(),window,console});
const rowCount=id=>{const body=el(id).innerHTML.match(/<tbody>([\s\S]*?)<\/tbody>/);return body?[...body[1].matchAll(/<tr>/g)].length:0;};
assert.equal(rowCount('season-leaders'),28);assert.equal(rowCount('pooled-leaders'),14);assert.equal(rowCount('current-leaders'),14);
assert.equal(rowCount('candidate-table'),25);assert.equal(rowCount('early-groups'),6);assert.equal(rowCount('late-groups'),11);
assert.equal(rowCount('late-rows'),46);assert.equal(rowCount('outcome-sources'),38);
assert.match(el('candidate-count').textContent,/1–25 of 164/);assert.equal(window.__ncaaB063R2.ownerR2Executed,false);
el('candidate-next').click();assert.match(el('candidate-count').textContent,/26–50 of 164/);
el('league').value='ncaaw';el('league').fire('change');el('season').value='2026';el('season').fire('change');
el('objective').value='win:log_loss';el('objective').fire('change');
assert.equal(rowCount('season-leaders'),1);assert.equal(rowCount('current-leaders'),1);assert.equal(rowCount('candidate-table'),14);
assert.match(el('season-leaders').innerHTML,/Women/);assert.match(el('season-leaders').innerHTML,/2025–26/);
el('download-candidates').click();assert.equal(lastBlob.text.split('\r\n').length,15);assert.ok(lastBlob.text.includes('cohort_sha256'));
assert.ok(lastBlob.text.split('\r\n').slice(1).every(line=>line.startsWith('"ncaaw","2025–26","win"')));
el('query').value='NO_MATCH_IN_SAVED_EVIDENCE';el('query').fire('input');assert.equal(rowCount('candidate-table'),0);
assert.match(el('candidate-table').innerHTML,/No rows match/);assert.equal(el('candidate-next').disabled,true);
el('reset').click();assert.equal(rowCount('season-leaders'),28);
for(let i=0;i<6;i++)el('candidate-next').click();assert.equal(rowCount('candidate-table'),14);assert.equal(el('candidate-next').disabled,true);
assert.match(el('candidate-count').textContent,/151–164 of 164/);
assert.match(el('paired-market').innerHTML,/0\.389409/);assert.match(el('paired-market').innerHTML,/0\.342372/);
assert.match(el('execution-actual').innerHTML,/3,737 startup tests passed; 1 errored; 11 skipped/);
for(const name of Object.keys(payload.source_pins))assert.ok(fs.existsSync(path.join(__dirname,'../../docs/ncaa/data',name)),name);
console.log(JSON.stringify({status:'PASS',scope:'EXACT_INLINE_JAVASCRIPT_DOM_SIMULATION_NOT_BROWSER_LAYOUT',candidateRows:164,seasonLeaders:28,pooledLeaders:14,currentLeaders:14,earlyGroups:6,lateGroups:11,lateRows:46,officialOutcomeSources:38,filteredCsvRows:14,publicationPreservesOwnerExecutionPending:true}));
