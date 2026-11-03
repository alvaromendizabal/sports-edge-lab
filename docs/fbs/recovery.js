'use strict';
(() => {
  const data=JSON.parse(document.getElementById('recovery-data').textContent);
  const byId=id=>document.getElementById(id);
  const display=value=>value===null?'Not available':String(value);
  document.querySelectorAll('[data-certificate]').forEach(button=>button.addEventListener('click',()=>{
    const example=data.certificate_cases.find(row=>row.id===button.dataset.certificate);
    const proof=example.certificate;
    document.querySelectorAll('[data-certificate]').forEach(node=>node.setAttribute('aria-pressed',String(node===button)));
    byId('case-status').textContent={REJECTED:'Rejected',CERTIFIED:'Certified',CERTIFIED_WITH_SOLVER_STOP_RETAINED:'Certified · original stop retained'}[proof.status];
    byId('case-status').dataset.certificateStatus=proof.status;
    byId('case-status').classList.toggle('certified',proof.numerically_certified);
    byId('case-explanation').textContent=example.explanation;
    byId('solver-status').textContent=display(proof.solver_reported_success);
    byId('primal-violation').textContent=display(proof.primal_violation);
    byId('gap-bound').textContent=display(proof.convex_suboptimality_upper_bound);
    byId('numerical-tolerance').textContent=display(proof.numerical_tolerance);
    byId('fixture-point').textContent=JSON.stringify(example.point);
  }));
  const selected=()=>data.actual.original_replay_2026.weekly.filter(row=>byId('week-filter').value==='all'||String(row.week)===byId('week-filter').value);
  byId('week-filter').addEventListener('change',()=>{
    document.querySelectorAll('#weekly-table tbody tr').forEach(row=>row.hidden=byId('week-filter').value!=='all'&&row.dataset.week!==byId('week-filter').value);
    const rows=selected();byId('week-status').textContent=`${rows.length} week${rows.length===1?'':'s'} · ${rows.reduce((total,row)=>total+row.games,0)} games · retrospective replay`;
  });
  byId('weekly-csv').addEventListener('click',()=>{
    const columns=['season','week','games','correct_winner','accuracy','logloss','brier','ece','mcc','margin_mae','margin_rmse','total_mae','total_rmse'];
    const quote=value=>'"'+String(value).replaceAll('"','""')+'"';
    const rows=[columns,...selected().map(row=>columns.map(key=>row[key]))];
    const url=URL.createObjectURL(new Blob([rows.map(row=>row.map(quote).join(',')).join('\n')+'\n'],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='fbs-2026-replay-weeks.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
})();
