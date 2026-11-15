// Exercise the actual page script with a small DOM harness; not a visual browser claim.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const docs=path.resolve(__dirname,'../../docs/ncaa');
const html=fs.readFileSync(path.join(docs,'v12.html'),'utf8'),data=JSON.parse(fs.readFileSync(path.join(docs,'v12_r14_public_evidence.json'),'utf8'));
const uncertainty=JSON.parse(fs.readFileSync(path.join(docs,'v12_r14_descriptive_uncertainty.json'),'utf8'));
const script=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].at(-1)[1];
class Element{constructor(id){this.id=id;this.value='';this.innerHTML='';this.textContent='';this.disabled=false;this.events={};this.classList={add(){}};}addEventListener(name,fn){this.events[name]=fn;}dispatch(name){this.events[name]();}click(){if(this.events.click)this.events.click();}}
async function main(){
 const elements=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element(m[1])])),get=id=>{assert(elements.has(id),'Undeclared DOM ID '+id);return elements.get(id);};
 for(const [id,value]of Object.entries({league:'all','historical-target':'all','historical-season':'pooled','game-status':'all','game-sort':'asc'}))get(id).value=value;
 let downloaded=null;
 const context={document:{getElementById:get,createElement:()=>new Element('download')},window:{},fetch:async url=>({ok:true,json:async()=>structuredClone(url.includes('descriptive_uncertainty')?uncertainty:data)}),Blob,URL:{createObjectURL:blob=>{downloaded=blob;return'blob:test';},revokeObjectURL(){}},setTimeout:fn=>fn(),Date,console};
 vm.runInNewContext(script,context,{timeout:10000});
 // Early interaction before fetch completion remains harmless.
 get('league').dispatch('change');
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(context.window.SEL_V12_ERROR,undefined);
 assert.equal(context.window.SEL_V12_READY.observedGames,2503);
 assert.equal(context.window.SEL_V12_UNCERTAINTY_READY,true);
 assert.equal((get('uncertainty-rows').innerHTML.match(/<tr>/g)||[]).length,7);
 assert.match(get('uncertainty-rows').innerHTML,/73\.33% – 83\.74%/);
 assert.match(get('uncertainty-rows').innerHTML,/78\.28% – 85\.08%/);
 assert.match(get('game-count').textContent,/2,503 matching observed games/);
 assert.equal((get('current-model-rows').innerHTML.match(/<tr>/g)||[]).length,6);
 assert.equal((get('provider-rows').innerHTML.match(/<tr>/g)||[]).length,8);
 assert.equal((get('historical-rows').innerHTML.match(/<tr>/g)||[]).length,14);
 assert.match(get('provider-rows').innerHTML,/Unavailable \/ Unavailable/);
 assert(!get('provider-rows').innerHTML.includes('0.000'));
 assert(get('game-rows').innerHTML.includes('74 – 72'));
 for(const [league,total,future]of [['ncaam',1255,438],['ncaaw',1248,455]]){
  get('league').value=league;get('league').dispatch('change');
  assert(get('game-count').textContent.startsWith(total.toLocaleString('en-US')+' matching'));
  assert.equal((get('current-model-rows').innerHTML.match(/<tr>/g)||[]).length,3);
  assert.equal((get('provider-rows').innerHTML.match(/<tr>/g)||[]).length,4);
  assert.equal((get('uncertainty-head').innerHTML.match(/<th>/g)||[]).length,2);
  get('game-status').value='future';get('game-status').dispatch('change');
  assert(get('game-count').textContent.startsWith(future+' matching'));
  get('game-status').value='all';get('game-status').dispatch('change');
 }
 get('league').value='all';get('league').dispatch('change');
 get('game-status').value='scheduled_start_passed';get('game-status').dispatch('change');
 assert.match(get('game-count').textContent,/^1 matching/);
 get('game-status').value='all';get('game-status').dispatch('change');
 get('next').click();assert.match(get('game-count').textContent,/page 2 of/);
 get('game-search').value='no-such-authentic-team';get('game-search').dispatch('input');assert.match(get('game-count').textContent,/^0 matching/);assert(get('download-games').disabled);
 get('game-search').value='Notre Dame';get('game-search').dispatch('input');assert(!get('download-games').disabled);get('download-games').click();
 const exported=JSON.parse(await downloaded.text());assert(exported.rows.length>0);assert.equal(exported.complete_official_season_universe,false);assert.equal(exported.report_asof,data.census_asof);assert(exported.rows.every(r=>(r.away_team+' '+r.home_team).includes('Notre Dame')));
 get('game-search').value='';get('game-search').dispatch('input');
 get('historical-target').value='win';get('historical-target').dispatch('change');get('historical-season').value='2025';get('historical-season').dispatch('change');
 assert.equal((get('historical-rows').innerHTML.match(/<tr>/g)||[]).length,6);assert(get('historical-rows').innerHTML.includes('5,758'));
 for(const e of elements.values()){assert(!e.innerHTML.includes('NaN'));assert(!e.innerHTML.includes('undefined'));}
 // A missing secondary audit must not suppress the established science tables.
 const fallback={...context,window:{},fetch:async url=>({ok:!url.includes('descriptive_uncertainty'),json:async()=>structuredClone(data)})};
 vm.runInNewContext(script,fallback,{timeout:10000});await new Promise(resolve=>setImmediate(resolve));
 assert.equal(fallback.window.SEL_V12_READY.observedGames,2503);
 assert.equal(fallback.window.SEL_V12_ERROR,undefined);
 assert.match(fallback.window.SEL_V12_UNCERTAINTY_ERROR,/unavailable/);
 console.log(JSON.stringify({status:'PASS',kind:'DOM harness, not visual browser verification',checks:['load','early interaction','competition filters','current and historical separation','null market losses','final scores','future-clock filter','passed-start filter','pagination','search','download scope','historical season filter']}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
