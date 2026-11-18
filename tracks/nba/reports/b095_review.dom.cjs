'use strict';
// DOM-only interaction oracle. This is not a browser-rendering claim.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'b095_review.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'b095_review.json'),'utf8'));
class Element {
 constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.dataset={};this.listeners={};this._text='';this.value='';this.checked=false;this.hidden=false;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
 appendChild(child){this.children.push(child);return child;}
 append(...children){for(const child of children)this.appendChild(child);}
 replaceChildren(...children){this._text='';this.children=children;}
 addEventListener(type,handler){this.listeners[type]=handler;}
 dispatchEvent(event){if(this.listeners[event.type])this.listeners[event.type](event);}
 click(){this.dispatchEvent({type:'click'});}
}
const elements=new Map();for(const match of html.matchAll(/<([a-z][a-z0-9-]*)\b[^>]*\bid="([^"]+)"[^>]*>/gi))elements.set(match[2],new Element(match[1]));
for(const match of html.matchAll(/<select\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)){elements.get(match[1]).value=/<option value="([^"]+)"/.exec(match[2])[1];}
elements.get('book-covered').checked=true;
elements.get('b095-evidence').textContent=/<script id="b095-evidence" type="application\/json">([\s\S]*?)<\/script>/.exec(html)[1];
const document={getElementById:id=>{assert.ok(elements.has(id),'Unknown DOM id '+id);return elements.get(id);},createElement:tag=>new Element(tag),documentElement:new Element('html')};
let downloadBlob;
const context=vm.createContext({document,JSON,Number,String,Object,Math,console,Blob,setTimeout:()=>0,URL:{createObjectURL:blob=>{downloadBlob=blob;return 'blob:local-test';},revokeObjectURL:()=>{}}});
const script=/<script>\s*([\s\S]*?)<\/script>/.exec(html)[1];new vm.Script(script,{filename:'b095-inline.js'}).runInContext(context);
assert.equal(document.documentElement.dataset.reviewReady,'true');
const $=id=>elements.get(id),set=(id,value,event='change')=>{$(id).value=value;$(id).dispatchEvent({type:event});};
const rows=id=>$(id).children,show=(n,o)=>o==='winner_accuracy'?(n*100).toFixed(2)+'%':n.toFixed(4);
let leaderViews=0,weightViews=0,sourceViews=0,checkedMetricCells=0;
for(const horizon of ['all','60','120'])for(const target of ['all','winner','margin','total']){
 set('leader-horizon',horizon);set('leader-target',target);
 const expected=data.objective_leaders.filter(r=>(horizon==='all'||String(r.horizon_minutes)===horizon)&&(target==='all'||r.objective.startsWith(target+'_')));
 assert.equal(rows('leader-rows').length,expected.length);
 expected.forEach((r,i)=>{const cells=rows('leader-rows')[i].children;assert.ok(cells[1].textContent.includes(r.public_model_alias));
  for(const [j,idx] of [[2,0],[3,1],[5,2]]){assert.equal(cells[j].textContent,show(r.annual_metrics[idx].value,r.objective));checkedMetricCells++;}
  assert.ok(cells[4].textContent.startsWith(show(r.selection_score,r.objective)));assert.ok(cells[4].textContent.includes(r.saved_score_aggregation));checkedMetricCells++;
 });leaderViews++;
}
for(const objective of [...new Set(data.weight_sensitivity.map(r=>r.objective))])for(const horizon of ['60','120']){
 set('weight-objective',objective);set('weight-horizon',horizon);
 const expected=data.weight_sensitivity.filter(r=>r.objective===objective&&String(r.horizon_minutes)===horizon);
 assert.equal(rows('weight-rows').length,5);expected.forEach((r,i)=>{const cells=rows('weight-rows')[i].children;
  assert.ok(cells[0].textContent.startsWith(r.policy));assert.ok(cells[1].textContent.includes(r.public_model_alias));
  assert.ok(cells[2].textContent.startsWith(show(r.leader_score,r.objective)));assert.ok(cells[2].textContent.includes(r.saved_score_aggregation));
  assert.ok(cells[3].textContent.startsWith(String(r.primary_leader_rank)));assert.equal(cells[5].textContent,'0 / none');checkedMetricCells++;
 });weightViews++;
}
for(const season of ['2024-25','2025-26','2026-27','all'])for(const status of ['COMPLETED','UPCOMING','all'])for(const market of ['all','h2h','spreads','totals']){
 set('source-season',season);set('source-status',status);set('source-market',market);
 const expected=data.sources.named_provider_coverage.filter(r=>(season==='all'||r.season===season)&&(status==='all'||r.population_status===status)&&(market==='all'||r.market===market));
 assert.equal(rows('source-rows').length,Math.max(1,expected.length));expected.forEach((r,i)=>{const cells=rows('source-rows')[i].children;assert.equal(cells[3].textContent,r.qualified_n.toLocaleString('en-US')+' / '+r.population_n.toLocaleString('en-US'));assert.equal(cells[4].textContent,r.missing_n.toLocaleString('en-US'));checkedMetricCells+=2;});sourceViews++;
}
assert.equal(rows('book-rows').length,28);$('book-covered').checked=false;$('book-covered').dispatchEvent({type:'change'});assert.equal(rows('book-rows').length,122);
set('book-search','draftkings','input');assert.equal(rows('book-rows').length,1);assert.ok(rows('book-rows')[0].textContent.includes('7,848'));
assert.equal(rows('population-rows').length,3);assert.equal(rows('execution-rows').length,5);
assert.ok(rows('execution-rows')[2].textContent.includes('B095 · attempt 1'));
assert.ok(rows('execution-rows')[3].textContent.includes('B095 · attempt 2'));
assert.ok(rows('execution-rows')[4].textContent.includes('B096'));
for(const i of [2,3])assert.ok(rows('execution-rows')[i].textContent.includes('Exit 2; resumable'));
assert.ok($('latest-return-detail').textContent.includes('19,057,377'));
assert.ok($('failure-cost-detail').textContent.includes('invoiced cost remains unknown'));
assert.equal(rows('calibration-rows').length,7);
for(const e of elements.values())assert.doesNotMatch(e.textContent,/undefined|NaN/);
$('download-evidence').click();
(async()=>{assert.deepEqual(JSON.parse(await downloadBlob.text()),data);const summary={status:'PASS',kind:'DOM interaction oracle; not browser rendering',leader_views:leaderViews,weight_views:weightViews,source_views:sourceViews,book_filter_views:3,checked_metric_cells:checkedMetricCells,exact_public_download:true};console.log(JSON.stringify(summary));})().catch(e=>{console.error(e);process.exitCode=1;});
