// Semantic DOM fixture: tests logic, not browser rendering or accessibility.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html=fs.readFileSync(path.resolve(__dirname,'../../../docs/current/index.html'),'utf8');
const evidence=JSON.parse(html.match(/<script type="application\/json" id="current-data">([\s\S]*?)<\/script>/)[1]);
const program=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
class Element {constructor(){this.children=[];this.textContent='';this.value='';this.listeners={};this.className='';}append(child){this.children.push(child);}replaceChildren(){this.children=[];}addEventListener(name,callback){this.listeners[name]=callback;}}
const nodes=Object.fromEntries(['current-data','role','league','panel','metric','search','scores','status','caption','fingerprint'].map(id=>[id,new Element()]));
nodes['current-data'].textContent=JSON.stringify(evidence);nodes.role.value='historical';nodes.league.value='nfl';nodes.metric.value='win_logloss';
const document={getElementById:id=>nodes[id],createElement:()=>new Element()};
vm.runInNewContext(program,{document});
const ids=['track','bank','protocol','scope','origin','season','cohort_sha256','games'];
const key=r=>JSON.stringify(ids.map(k=>r[k]??''));
const role=r=>r.purpose==='FORWARD_MONITORING_ONLY'?'monitor':r.protocol.startsWith('development')?'development':'historical';
const stable=(a,b)=>a.arm.localeCompare(b.arm)||String(a.label||'').localeCompare(String(b.label||''));
let states=0,monitorStates=0;
for(const mode of ['historical','monitor','development']) for(const league of ['nfl','ncaaf']){
 nodes.role.value=mode;nodes.league.value=league;nodes.league.listeners.change();
 const expectedPanels=new Set(evidence.rows.filter(r=>r.track===league&&role(r)===mode).map(key));
 assert.equal(nodes.panel.children.length,expectedPanels.size);
 for(const option of nodes.panel.children){
  nodes.panel.value=option.value;
  const full=evidence.rows.filter(r=>key(r)===option.value).sort(stable);
  for(const metric of ['win_logloss','win_brier','win_accuracy','ece10','home_score_mae','away_score_mae','margin_mae','total_mae','joint_nll','mean_marginal_crps']){
   nodes.metric.value=metric;
   for(const search of ['',full[0].arm,'a-query-with-no-match']){
    nodes.search.value=search;nodes.search.listeners.input();
    const visible=full.filter(r=>(r.arm+' '+(r.label||'')).toLowerCase().includes(search.toLowerCase()));
    assert.equal(nodes.scores.children.length,visible.length);
    const values=full.map(r=>r[metric]).filter(v=>typeof v==='number'&&Number.isFinite(v));
    const best=values.length>=2?(metric==='win_accuracy'?Math.max(...values):Math.min(...values)):null;
    visible.forEach((row,i)=>{const cells=nodes.scores.children[i].children;assert.equal(cells[0].textContent,row.label?row.arm+' · '+row.label:row.arm);assert.equal(cells[1].textContent,String(row.games));assert.equal(cells[2].className.includes('winner'),mode!=='monitor'&&best!==null&&row[metric]===best);});
    if(mode==='monitor'){assert.match(nodes.status.textContent,/MONITORING ONLY/);monitorStates++;}
    states++;
   }
  }
 }
}
console.log(JSON.stringify({status:'PASS',selector_states:states,monitor_only_states:monitorStates,exact_panels:57,method:'semantic DOM fixture; no rendered browser'}));
