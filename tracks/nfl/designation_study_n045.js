// Aggregate selected-origin results only; never convert reconstructions into issues.
(()=>{
 'use strict';
 const d=JSON.parse(document.getElementById('nfl-designation-metrics-n045').textContent);
 const get=id=>document.getElementById(id),fmt=(v,n=4)=>v==null?'Not applicable':Number(v).toFixed(n);
 function render(){
  const origin=get('designation-origin').value,target=get('designation-target').value;
  const rows=d.rows.filter(r=>r.origin===origin&&r.target===target);
  const headers=target==='winner'?['Season','Games','Correct','Accuracy','Log loss ↓','Brier ↓','AUC','ECE ↓']:['Season','Games','MAE ↓','RMSE ↓','Bias'];
  const cells=rows.map(r=>target==='winner'?[r.season,r.games,r.correct,fmt(100*r.accuracy,1)+'%',fmt(r.log_loss,6),fmt(r.brier,6),fmt(r.auc),fmt(r.ece)]:[r.season,r.games,fmt(r.mae),fmt(r.rmse),fmt(r.bias)]);
  get('designation-metric-scope').textContent='Pre-2024-selected ExtraTrees recipe; '+get('designation-origin').selectedOptions[0].textContent.toLowerCase()+'. 2024/25 are development-exposed retrospectives; 2026 is descriptive reconstruction, not prospective issue performance. No automatic promotion.';
  get('designation-metric-table').innerHTML='<div class="scroll table-wrap" tabindex="0" role="region" aria-label="Selected injury study metrics"><table><caption class="table-caption">Selected injury-designation '+target+' results</caption><thead><tr>'+headers.map(x=>'<th scope="col">'+x+'</th>').join('')+'</tr></thead><tbody>'+cells.map(row=>'<tr>'+row.map((x,i)=>i?'<td>'+x+'</td>':'<th scope="row">'+x+'</th>').join('')+'</tr>').join('')+'</tbody></table></div>';
 }
 for(const id of ['designation-origin','designation-target'])get(id).addEventListener('change',render);
 render();
})();
