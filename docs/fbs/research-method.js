'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const validTime = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
  const pacificFormatter = new Intl.DateTimeFormat('en-US', {timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'});
  const windowCache = new Map();
  function pacificDate(value) {
    if (validTime(value) === null) return null;
    const parts = pacificFormatter.formatToParts(new Date(value));
    const part = name => parts.find(p=>p.type===name).value;
    return `${part('year')}-${part('month')}-${part('day')}`;
  }
  function addDays(day, count) {
    const value = new Date(day+'T12:00:00Z'); value.setUTCDate(value.getUTCDate()+count);
    return value.toISOString().slice(0,10);
  }
  function weekWindows(observedAt) {
    if(windowCache.has(observedAt))return windowCache.get(observedAt);
    const observedDay = pacificDate(observedAt);
    if (!observedDay) return null;
    const weekday = new Date(observedDay+'T12:00:00Z').getUTCDay();
    const monday = addDays(observedDay,-((weekday+6)%7));
    const result=Object.fromEntries([['previous',-7],['current',0],['upcoming',7]].map(([name,offset])=>[name,{start:addDays(monday,offset),end_exclusive:addDays(monday,offset+7),label:addDays(monday,offset)+' to '+addDays(monday,offset+6),timezone:'America/Los_Angeles',anchor:observedAt}]));
    windowCache.set(observedAt,result);if(windowCache.size>8)windowCache.delete(windowCache.keys().next().value);return result;
  }
  function periodFor(game, observedAt) {
    if (!game.kickoff_exact) return 'unresolved';
    const day=pacificDate(game.kickoff), windows=weekWindows(observedAt);
    if (!day || !windows) return 'unresolved';
    return Object.entries(windows).find(([,range])=>day>=range.start&&day<range.end_exclusive)?.[0] || 'other';
  }
  function clockReport(game, value, observedAt) {
    const observed=validTime(observedAt), tip=game.kickoff_exact?validTime(game.kickoff):null;
    const clocks=['winner','margin','total'].filter(target=>finite(value.model?.[target]?.prediction)).map(target=>({target,computed_at:value.model[target].computed_at_utc||null}));
    const valid=clocks.map(row=>validTime(row.computed_at)).filter(time=>time!==null);
    const first=valid.length?Math.min(...valid):null,last=valid.length?Math.max(...valid):null;
    const complete=clocks.length>0&&valid.length===clocks.length;
    const age=observed!==null&&last!==null?(observed-last)/3600000:null;
    const horizon=tip!==null&&first!==null?(tip-first)/3600000:null;
    let status='CLOCK_EVIDENCE_MISSING',label='Forecast age not established';
    if (complete&&age!==null&&age<0) {status='COMPUTED_AFTER_CAPTURE';label='Computed after this dated capture';}
    else if (complete&&age!==null&&horizon!==null) {
      if(horizon<=0){status='AT_OR_AFTER_KICKOFF';label='Computed at or after kickoff';}
      else if(horizon>168){status='LONG_RANGE_SNAPSHOT';label='Long-range saved snapshot';}
      else {status='NEARER_ORIGIN_SNAPSHOT';label='Saved within seven days of kickoff';}
    }
    return {status,label,age_hours:age,horizon_hours:horizon,computed_first:first===null?null:new Date(first).toISOString(),computed_last:last===null?null:new Date(last).toISOString(),cutoff:value.record?.cutoff||null,age_as_of:observedAt,forecast_issued:false,clocks};
  }
  function hoursLabel(hours) {
    if (!finite(hours)) return 'Not established';
    if (hours<0) return 'After the dated observation';
    return hours>=48?`${(hours/24).toFixed(1)} days`:`${hours.toFixed(1)} hours`;
  }
  function captureProjection(source) {
    const rows=source.rows.map(row=>({id:row.id,season:row.season,home_id:row.home_id,away_id:row.away_id,
      kickoff:row.kickoff,kickoff_exact:row.kickoff_exact,reported_kickoff:row.reported_kickoff,
      completed:row.completed,home_score:row.home_points,away_score:row.away_points,
      observed_at:row.latest_result_observed_at||row.source_observed_at,
      source_observed_at:row.source_observed_at,newly_observed:row.newly_observed_since_prior_capture,
      identity_status:row.binding_status,owner_original_identity_status:row.owner_original_quarantine_reason}));
    return {capture:{observed_at:source.original2026_source_observed_at,started_at:source.source_observed_at,completed_at:source.capture_completed_at},rows,
      counts:{seasons:Object.fromEntries([2024,2025,2026].map(season=>[season,{identified:rows.filter(r=>r.season===season).length,completed:rows.filter(r=>r.season===season&&r.completed).length}])),periods:Object.fromEntries(Object.entries(source.periods).map(([key,value])=>[key,{identified:value.games,completed:value.observed_finals}])),newly_observed:source.counts.newly_observed_finals_since_prior_capture,newly_observed_since_original_snapshot:source.counts.current_season_observed_finals-629},
      scientific_metrics:source.scientific_metrics,source};
  }
  const api={pacificDate,weekWindows,periodFor,clockReport,hoursLabel,captureProjection};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window!=='undefined'){
    window.FBSResearchMethod=api;
    const source=window.FBS_OBSERVATION_STATUS_V046,index=new Map((source?.rows||[]).map(row=>[row.id,row]));
    api.metadata=id=>index.get(id)||null;
    const names={four_epoch_logistic:'Logistic',four_epoch_linear:'Linear',four_epoch_ridge:'Ridge',four_epoch_extra_trees:'Extra Trees',four_epoch_hist_gradient_boosting:'Histogram boosting',four_epoch_xgboost:'XGBoost',four_epoch_lightgbm:'LightGBM',four_epoch_pytorch:'PyTorch',four_epoch_tensorflow:'TensorFlow',four_epoch_blend_sklearn:'Fixed sklearn blend',four_epoch_blend_optional_trees:'Fixed optional-tree blend',four_epoch_blend_neural:'Fixed neural blend'};
    const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    function renderMetadata(id){
      const box=document.getElementById('dialog-latest-research');if(!box)return;
      const row=index.get(id);if(!row){box.textContent='No authenticated latest research metadata for this game.';return;}
      const models=Object.entries(row.four_epoch_models);
      if(!models.length){box.innerHTML='<h3>Latest private research status</h3><p>'+esc(row.new_fixture_prediction_status?'Exact kickoff newly resolved. This is a new fixture epoch; a new prediction remains pending.':!row.kickoff_exact?'Exact kickoff unresolved; new model target cannot yet be admitted.':'Outside the 105-game changed-input study. Earlier saved reconstructions remain separate.')+'</p>';return;}
      box.innerHTML='<h3>Latest private research status</h3><p>These are availability and clock records for the separate recovered owner study. Numerical values remain private; the legacy values above are unchanged. No authenticated issue is established.</p><div class="table-wrap"><table><thead><tr><th>Family</th><th>Saved targets</th><th>Original computation</th><th>Registered target cutoff</th><th>Original lead time</th><th>Training / calibration availability</th></tr></thead><tbody>'+models.map(([family,targets])=>{
        const values=Object.values(targets),first=values[0],clocks=values.map(v=>v.computed_at_utc).sort(),lead=values.map(v=>v.computed_horizon_minutes/60);
        return '<tr><td>'+esc(names[family]||family)+'</td><td>'+esc(Object.keys(targets).join(' / '))+'<small>Saved privately · not issued</small></td><td>'+esc(clocks[0])+(clocks.at(-1)!==clocks[0]?'<small>through '+esc(clocks.at(-1))+'</small>':'')+'</td><td>'+esc(first.registered_cutoff_utc)+'</td><td>'+esc(hoursLabel(Math.max(...lead)))+'</td><td>'+esc(first.training_max_available_at_utc||'Derived from saved constituents')+'<small>Calibration: '+esc(first.calibration_max_available_at_utc||'Not separately recorded for this derivation')+'</small></td></tr>';
      }).join('')+'</tbody></table></div><p class="footnote">Changed inputs produced a shared registered snapshot, then target-specific outputs; fixed blends derive from saved constituents. The future registered cutoff is not an assertion that future information was available. Original horizon and training/calibration clocks remain distinct. Long-range outlooks require a later admitted origin and independent issue.</p>';
    }
    document.addEventListener('fbs:game-opened',event=>renderMetadata(event.detail.id));
    document.addEventListener('DOMContentLoaded',()=>{
      const box=document.getElementById('latest-research-coverage');if(!box||!source)return;
      box.innerHTML='<strong>Recovered owner work: 105 future games · 3,360 private target outputs</strong><p>The authenticated owner completed 23 base fits and 7 calibrations. Across retained studies: '+source.counts.all_saved_base_fits.toLocaleString()+' base fits, '+source.counts.all_saved_calibration_fits.toLocaleString()+' calibrations and '+source.counts.all_saved_output_records.toLocaleString()+' saved outputs. This publication adds zero fits, forecasts or scientific evaluations.</p><p>All '+source.periods.current_week.games+' dated current-week games have observed finals. The upcoming week has '+source.periods.upcoming_week.games+' identified exact-kickoff games; two newly resolved fixtures require new prediction identities. Open a game for the latest private study’s availability and source clocks. The latest authenticated owner evaluation covers the 685-outcome baseline and 14 observed games from the separate 119-game study. The later 105-game outlook still has no observed outcomes. Earlier scorecards remain dated and unchanged.</p>';
    },{once:true});
  }
})();
