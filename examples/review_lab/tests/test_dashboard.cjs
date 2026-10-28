// Tests all filter states and actual event callbacks; browser layout is checked separately.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const html=fs.readFileSync(path.resolve(__dirname,'../../../docs/dashboard/index.html'),'utf8');
const data=JSON.parse(html.match(/<script id="dashboard-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const script=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];
class Element{constructor(value=''){this.value=value;this.innerHTML='';this.listeners={};this.attributes={};}addEventListener(n,fn){this.listeners[n]=fn;}setAttribute(k,v){this.attributes[k]=v;}}
const nodes=Object.fromEntries(['release','league','season','policy','metric','results','demo-output','recovery-output','portable-output','dashboard-data'].map(x=>[x,new Element()]));
Object.assign(nodes['dashboard-data'],{textContent:JSON.stringify(data)});
const defaults={release:'V132',league:'FBS',season:'2024',policy:'annual',metric:'win_logloss'};for(const[k,v]of Object.entries(defaults))nodes[k].value=v;
const buttons=Object.keys(data.scenarios).map(s=>Object.assign(new Element(),{dataset:{scenario:s}}));
const recoveryButtons=['first','resume','reentry'].map(s=>Object.assign(new Element(),{dataset:{recovery:s}}));
const portableButtons=['sparse','portable'].map(s=>Object.assign(new Element(),{dataset:{portable:s}}));
const document={getElementById:id=>nodes[id],querySelectorAll:s=>s==='[data-recovery]'?recoveryButtons:s==='[data-portable]'?portableButtons:buttons};const context={document};vm.runInNewContext(script,context);const api=context.Dashboard;
let states=0,missing=0,monitoring=0;
for(const release of ['V129','V131','V132'])for(const league of ['NFL','FBS'])for(const season of ['2024','2025','2026'])for(const policy of ['annual','fixed'])for(const metric of ['win_logloss','win_brier']){
 const filter={release,league,season,policy,metric};for(const[k,v]of Object.entries(filter))nodes[k].value=v;nodes.metric.listeners.change();
 const expected=data.rows.filter(r=>r.release===release&&r.league===league&&r.season===+season&&r.policy===policy);
 assert.equal(api.selectedRows(data,filter).length,expected.length);
 const view=nodes.results.innerHTML;assert(!view.includes('NaN'));assert(!view.includes('undefined'));
 if(!expected.length){assert.match(view,/No saved panel/);assert(!view.includes('<table>'));missing++;}
 else {for(const row of expected)assert(view.includes(row[metric].toFixed(6)));}
 if(season==='2026'){assert.match(view,/MONITORING ONLY/);assert(!view.includes('num best'));monitoring++;}
 else if(expected.length){const min=Math.min(...expected.map(r=>r[metric]));assert.equal((view.match(/num best/g)||[]).length,expected.filter(r=>r[metric]===min).length);}
 states++;
}
for(const button of buttons){button.listeners.click();assert.equal(button.attributes['aria-pressed'],'true');assert.equal(buttons.filter(b=>b.attributes['aria-pressed']==='true').length,1);const view=nodes['demo-output'].innerHTML;assert(view.includes(data.scenarios[button.dataset.scenario].serving.status));assert(view.includes('profit → unavailable'));}
for(const button of recoveryButtons){button.listeners.click();assert.equal(button.attributes['aria-pressed'],'true');assert.equal(recoveryButtons.filter(b=>b.attributes['aria-pressed']==='true').length,1);const r=data.recovery[button.dataset.recovery];assert(nodes['recovery-output'].innerHTML.includes('>'+r.new_attempts+'</div>'));assert.equal((nodes['recovery-output'].innerHTML.match(/<tr>/g)||[]).length,9);}
for(const button of portableButtons){button.listeners.click();assert.equal(button.attributes['aria-pressed'],'true');assert.equal(portableButtons.filter(b=>b.attributes['aria-pressed']==='true').length,1);const view=nodes['portable-output'].innerHTML;assert.equal((view.match(/<tr>/g)||[]).length,5);assert.equal(view.includes('BLOCKED'),button.dataset.portable==='sparse');assert(view.includes('research'));}
assert.equal(data.owner.status,'FAILED');assert.equal(data.owner.extension_completed_units,0);assert.equal(data.owner.extension_status,'NOT_REACHED');
const malicious=structuredClone(data);malicious.rows[1].model='<img src=x onerror=alert(1)>';assert(!api.resultView(malicious,defaults).includes('<img src=x'));
console.log(JSON.stringify({status:'PASS',selector_states:states,missing_states:missing,monitoring_states:monitoring,scenario_events:buttons.length,recovery_events:recoveryButtons.length,portable_events:portableButtons.length}));
