"use strict";
(() => {
  const $=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const date=t=>t?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(t)):'Not recorded';
  const day=t=>{if(!t)return '';const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(t));const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));return p.year+'-'+p.month+'-'+p.day;};
  let saved=null,page=0,current=[],perPage=25;
  function selectRows(data,q){
    const byGame=new Map();for(const r of data.rows){if(!byGame.has(r.game))byGame.set(r.game,[]);byGame.get(r.game).push(r);}
    const out=[];for(const g of data.games){
      if(q.search&&!(`${g.home} ${g.away} ${g.id}`).toLocaleLowerCase().includes(q.search.toLocaleLowerCase()))continue;
      if(q.date&&day(g.kickoff)!==q.date)continue;
      const records=(byGame.get(g.id)||[]).filter(r=>(q.family==='all'||r.family===q.family)&&(q.target==='all'||r.target===q.target));
      const prepared=records.reduce((a,r)=>a+r.prepared,0),issued=records.reduce((a,r)=>a+r.issued,0),missing=prepared+issued===0;
      if(q.status==='prepared'&&!prepared||q.status==='issued'&&!issued||q.status==='missing'&&!missing)continue;
      out.push({game:g,prepared,issued,missing,reason:missing?(g.missing_reason||'No verified record matches the selected family and target.'):null});
    }return out;
  }
  function query(){return {search:$('refit-search').value.trim(),family:$('refit-family').value,target:$('refit-target').value,status:$('refit-status').value,date:$('refit-date').value};}
  function render(){
    if(!saved)return;current=selectRows(saved,query());const pages=Math.max(1,Math.ceil(current.length/perPage));page=Math.min(page,pages-1);const shown=current.slice(page*perPage,(page+1)*perPage),c=saved.coverage;
    $('refit-coverage').textContent=`${c.games_with_refit_outputs} / ${c.pending_games} pending games covered · ${c.prepared_rows} prepared records · ${c.issued_rows} issued records · ${c.missing_games} games missing. This filter: ${current.length} games.`;
    $('refit-body').innerHTML=shown.length?shown.map(({game:g,prepared,issued,missing,reason})=>{
      const matchup=`<strong>${esc(g.away)} at ${esc(g.home)}</strong><span class="subline">${esc(g.kickoff?date(g.kickoff):'Kickoff TBD')} · ${esc(g.id)}</span>`;
      return `<tr><td>${matchup}</td><td class="number">${prepared}</td><td class="number">${issued}</td><td>${missing?esc(reason):'<span class="badge amber-label">Prepared values withheld</span><span class="subline">Unpromoted research; no public forecast issuance</span>'}</td><td>${esc(date(g.latest_prepared))}</td></tr>`;
    }).join(''):'<tr><td colspan="5">No games match these filters. An issued record requires a separate verified owner issue receipt.</td></tr>';
    $('refit-page').textContent=current.length?`${page*perPage+1}–${Math.min(current.length,(page+1)*perPage)} of ${current.length}`:'0 games';$('refit-prev').disabled=page===0;$('refit-next').disabled=page>=pages-1;
    document.documentElement.dataset.refitVisibleRows=String(current.length);
  }
  function csv(){const cols=['game','away','home','kickoff_utc','prepared_records','issued_records','latest_prepared_at','missing_reason'];const cell=v=>'"'+String(v??'').replace(/"/g,'""')+'"';return [cols,...current.map(({game:g,prepared,issued,reason})=>[g.id,g.away,g.home,g.kickoff,prepared,issued,g.latest_prepared,reason])].map(x=>x.map(cell).join(',')).join('\n');}
  for(const id of ['refit-search','refit-family','refit-target','refit-status','refit-date'])$(id).addEventListener(id==='refit-search'?'input':'change',()=>{page=0;render();});
  $('refit-prev').addEventListener('click',()=>{page--;render();});$('refit-next').addEventListener('click',()=>{page++;render();});
  $('refit-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([csv()],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='FBS_verified_refit_coverage.csv';a.click();URL.revokeObjectURL(url);});
  window.fbsRefitView={selectRows,day,query,render,csv};
  fetch('data/refits.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Verified refit coverage could not be loaded (HTTP '+r.status+').');return r.json();}).then(value=>{saved=value;$('refit-family').innerHTML='<option value="all">All families</option>'+saved.families.map(r=>r.family).sort().map(f=>'<option value="'+esc(f)+'">'+esc(f)+'</option>').join('');$('refit-limitations').innerHTML=saved.limitations.map(t=>'<li>'+esc(t)+'</li>').join('');render();document.documentElement.dataset.refitReady='true';}).catch(error=>{$('refit-error').hidden=false;$('refit-error').textContent=error.message;$('refit-coverage').textContent='Owner coverage could not be loaded; missing data are not treated as zero forecasts.';});
})();
