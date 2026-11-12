// Dependency-free DOM contract for the exact inline recovery script.
// This tests behavior, not Chromium rendering or layout.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const template=fs.readFileSync(path.join(__dirname,'recovery_dashboard.html.tmpl'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'B063R1_PUBLIC_RECOVERY_DATA.json'),'utf8'));
const script=template.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
class Element {
  constructor(){this.value='';this.innerHTML='';this.textContent='';this.listeners={};this.disabled=false;this.body=null;}
  addEventListener(event,fn){this.listeners[event]=fn;}
  querySelector(selector){assert.equal(selector,'tbody');return this.body||(this.body=new Element());}
  fire(event){assert.ok(this.listeners[event]);this.listeners[event]();}
  click(){if(this.listeners.click)this.listeners.click();}
}
const elements=new Map([...template.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
elements.get('b063r1-data').textContent=JSON.stringify(data);
elements.get('r1-league').value=elements.get('r1-target').value='all';
let lastBlob=null;
vm.runInNewContext(script,{
 document:{getElementById:id=>{assert.ok(elements.has(id),id);return elements.get(id);},createElement:tag=>{assert.equal(tag,'a');return new Element();}},
 Blob:class {constructor(parts){this.text=parts.join('');}},
 URL:{createObjectURL:blob=>{lastBlob=blob;return 'blob:fixture';},revokeObjectURL:()=>{}},
 setTimeout:fn=>fn(),console
});
const el=id=>elements.get(id),rows=()=>[...el('r1-issues-table').body.innerHTML.matchAll(/<tr>/g)].length;
assert.match(el('r1-issue-count').textContent,/^90 selected original rows across 30 games/);assert.equal(rows(),15);
assert.equal([...el('r1-monitor-table').body.innerHTML.matchAll(/<tr>/g)].length,11);
assert.equal([...el('r1-outcome-cards').innerHTML.matchAll(/<p>/g)].length,8);
el('r1-league').value='ncaaw';el('r1-league').fire('change');
el('r1-target').value='win';el('r1-target').fire('change');
assert.match(el('r1-issue-count').textContent,/^26 selected original rows across 26 games/);
el('r1-next').click();assert.equal(rows(),11);assert.equal(el('r1-next').disabled,true);
el('r1-league').value='ncaam';el('r1-league').fire('change');assert.equal(rows(),4);
el('r1-download').click();assert.equal(lastBlob.text.split('\n').length,5);
assert.ok(lastBlob.text.includes('issued_at'));assert.ok(lastBlob.text.includes('issue_record_sha256'));
el('r1-search').value='NO_SUCH_TEAM';el('r1-search').fire('input');
assert.match(el('r1-issues-table').body.innerHTML,/No selected original rows/);
assert.equal(el('r1-prev').disabled,true);assert.equal(el('r1-next').disabled,true);
assert.match(el('r1-run-facts').innerHTML,/0 new fits/);
assert.match(el('r1-monitor-status').textContent,/full precision/);
console.log(JSON.stringify({status:'PASS',scope:'DEPENDENCY_FREE_DOM_SIMULATION_NOT_BROWSER_RENDER',selectedRows:90,monitorGroups:11,outcomes:8,filterCases:4,downloadRows:4}));
