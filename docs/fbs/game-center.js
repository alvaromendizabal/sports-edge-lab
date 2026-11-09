'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const kickoff = game => game.kickoff_exact && Number.isFinite(Date.parse(game.kickoff)) ? Date.parse(game.kickoff) : null;
  function orderGames(rows, order = 'current_first') {
    const result = [...rows];
    const group = game => game.season === 2026 && game.period === 'current' ? 0 : game.season === 2026 && game.period === 'previous' ? 1 : 2;
    return result.sort((a,b) => {
      if (order === 'team') return `${a.away} ${a.home}`.localeCompare(`${b.away} ${b.home}`) || String(a.id).localeCompare(String(b.id));
      if (order === 'current_first' && group(a) !== group(b)) return group(a) - group(b);
      const left = kickoff(a), right = kickoff(b);
      if (left === null || right === null) return left === right ? String(a.id).localeCompare(String(b.id)) : left === null ? 1 : -1;
      return (order === 'kickoff_desc' ? right-left : left-right) || String(a.id).localeCompare(String(b.id));
    });
  }
  function interval(value) {
    return Array.isArray(value) && value.length === 2 && value.every(finite) && value[0] <= value[1] ? [...value] : null;
  }
  function intervals(value, target) {
    return {interval80:interval(value.model?.[target]?.interval80),interval95:interval(value.model?.[target]?.interval95)};
  }
  function chronology(value) {
    const clocks = [...new Set(['winner','margin','total'].map(t=>value.model?.[t]?.computed_at_utc).filter(Boolean))].sort();
    return {cutoff:value.record?.cutoff || null,computed_first:clocks[0] || null,computed_last:clocks.at(-1) || null};
  }
  // Compare the retained UTC clocks without discarding their fractional precision.
  // A reconstructed cutoff is not proof of historical input possession or issuance.
  function utcClock(value) {
    if(typeof value!=='string')return null;
    const match=/^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?Z$/.exec(value);
    if(!match)return null;
    const milliseconds=Date.parse(match[1]+'Z');
    if(!Number.isFinite(milliseconds)||new Date(milliseconds).toISOString().slice(0,19)!==match[1])return null;
    return BigInt(milliseconds)*1000000n+BigInt((match[2]||'').padEnd(9,'0'));
  }
  function timing(value) {
    const available={winner:finite(value.p)&&value.p>=0&&value.p<=1,margin:finite(value.margin),total:finite(value.total)};
    const cutoff=utcClock(value.record?.cutoff),counts={before:0,at_or_after:0,unverified:0},targets={};
    for(const target of ['winner','margin','total']){
      if(!available[target])continue;
      const saved=value.model?.[target],computed=utcClock(saved?.computed_at_utc);
      let status='unverified';
      if(cutoff!==null&&computed!==null){
        const before=computed<cutoff;
        if(typeof saved?.computed_before_cutoff!=='boolean'||saved.computed_before_cutoff===before)status=before?'before':'at_or_after';
      }
      targets[target]=status;counts[status]++;
    }
    const saved=Object.keys(targets).length,status=!saved?'none':counts.unverified?'unverified':counts.at_or_after?'at_or_after':'before';
    const labels={none:'No saved output',unverified:'Output timing unverified',at_or_after:'Output computed at or after cutoff',before:'All saved outputs computed before cutoff'};
    return {status,label:labels[status],saved,counts,targets};
  }
  function timingSummary(rows, project) {
    const counts={games:rows.length,before:0,at_or_after:0,unverified:0,none:0};
    for(const game of rows)counts[timing(project(game)).status]++;
    return counts;
  }
  // Weekly scopes are small enough to show every fixture without a page break.
  // Full-season and multi-season views retain a bounded 30-card page.
  function pageSize(season, period) {
    return String(season) === '2026' && ['current','previous','upcoming'].includes(period) ? 63 : 30;
  }
  function periodSummary(rows, project, family, contracts) {
    const output={games:rows.length,completed:0,without_final:0,winner:0,margin:0,total:0,cover:0,complete:0,partial:0,missing:0};
    for(const game of rows){
      output[game.completed?'completed':'without_final']++;
      const value=project(game,family);
      for(const target of ['winner','margin','total','cover'])output[target]+=Number(contracts.hasTarget(value,target));
      output[contracts.completeness(value,family)]++;
    }
    return output;
  }
  function comparisonRoute(season, period, snapshot, windows) {
    if(snapshot==='original'&&season==='all')return null;
    let cohort=season==='all'?'cumulative':String(season);
    if(String(season)==='2026'&&period!=='all'){
      // Relative names move on Monday; stored evaluation cohorts do not.
      // Compare their exact Pacific date boundaries before offering a route.
      if(windows){
        const selected=windows.selected?.[period];
        if(!selected)return null;
        const matched=Object.entries(windows.evaluated||{}).find(([name,range])=>
          ['previous','current'].includes(name)&&range.start===selected.start&&range.end_exclusive===selected.end_exclusive);
        if(!matched)return null;
        cohort=matched[0]+'_week';
      }else{
        if(period==='upcoming')return null;
        cohort=period+'_week';
      }
    }
    return {study:snapshot==='original'?'v041':snapshot==='prior'?'v042':snapshot==='nov7_late'?'v043':snapshot==='nov7_evening'?'v044':'v045',cohort};
  }
  function familyCoverage(rows, families, project, contracts) {
    return families.map(family => {
      const counts = {family:family.id,label:family.label,games:rows.length,winner:0,margin:0,total:0,margin_intervals:0,total_intervals:0,cover:0,complete:0,partial:0,missing:0};
      for (const game of rows) {
        const value=project(game,family.id);
        for(const target of ['winner','margin','total','cover'])counts[target]+=Number(contracts.hasTarget(value,target));
        for(const target of ['margin','total']){const pair=intervals(value,target);counts[target+'_intervals']+=Number(!!pair.interval80&&!!pair.interval95);}
        counts[contracts.completeness(value,family.id)]++;
      }
      return {...counts,expected_targets:contracts.expectedTargets(family.id)};
    });
  }
  const api = {orderGames, interval, intervals, chronology, timing, timingSummary, familyCoverage, pageSize, periodSummary, comparisonRoute};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window === 'undefined') return;
  window.FBSGameCenter = api;
  function init() {
    const G=window.FBSCompleteReview,A=window.FBSCoverage,$=id=>document.getElementById(id);
    if(!G||!A||!$('game-cards'))return;
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const percent=v=>finite(v)?(v*100).toFixed(1)+'%':'Unavailable';
    const number=v=>finite(v)?v.toFixed(1):'Unavailable';
    const signed=v=>finite(v)?(v>0?'+':'')+v.toFixed(1):'Unavailable';
    const date=v=>v?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(v)):'No retained clock';
    const small=v=>`<small>${esc(v)}</small>`;
    const pairText=pair=>pair?pair.map(number).join(' to '):'Not saved';
    const families=[...$('model-view').options].map(o=>({id:o.value,label:o.text}));
    const coverageCache=new Map();
    function renderCoverage() {
      const scope=G.filtered(true),key=scope.map(g=>g.id).sort().join(',');
      let records=coverageCache.get(key);
      if(!records){records=familyCoverage(scope,families,G.projection,A);coverageCache.set(key,records);if(coverageCache.size>16)coverageCache.delete(coverageCache.keys().next().value);}
      $('family-coverage-summary').textContent=`${scope.length.toLocaleString()} fixtures after the selected season, period, result, team, timing and retained-reference filters. Every family uses this same inventory before a model-coverage filter is applied.`;
      const show=(r,t)=>r.expected_targets.includes(t)?`${r[t]} / ${r.games}`:'Outside family scope';
      $('family-coverage-rows').innerHTML=records.map(r=>`<tr${r.family===$('model-view').value?' class="selected-model"':''}><td><button class="model-choice" data-model-choice="${esc(r.family)}">${esc(r.label)}</button>${small(r.family==='retained'?'Separate original replay':r.family.includes('_refresh_')?'Separate changed-input 119-game reconstruction':'Reconstructed development; original issuance unproved')}</td><td>${show(r,'winner')}</td><td>${show(r,'margin')}</td><td>${show(r,'total')}</td><td>${r.margin_intervals} / ${r.games}${small('margin · 80% + 95%')}</td><td>${r.total_intervals} / ${r.games}${small('total · 80% + 95%')}</td><td>${r.cover} qualified</td><td>${r.complete} complete${small(r.partial+' partial · '+r.missing+' absent')}</td></tr>`).join('');
    }
    function renderCards() {
      const list=G.filtered(),rows=list.slice(G.page*G.pageSize,(G.page+1)*G.pageSize),family=$('model-view').value,provider=$('provider-filter').value;
      $('visible-game-range').textContent=list.length?G.pageSize===63?`All ${list.length.toLocaleString()} matching weekly games are shown below · no hidden pages.`:`Showing ${G.page*G.pageSize+1}–${Math.min((G.page+1)*G.pageSize,list.length)} of ${list.length.toLocaleString()} selected games · every matching fixture remains in the page sequence.`:'No matching games in this selection';
      $('game-table-view').hidden=$('game-layout').value!=='table';$('game-cards').hidden=$('game-layout').value!=='cards';
      if(!$('game-cards').hidden)$('game-cards').innerHTML=rows.map(game=>{
        const value=G.projection(game),hasWinner=A.hasTarget(value,'winner'),clock=chronology(value),computed=timing(value),mi=intervals(value,'margin'),ti=intervals(value,'total'),age=window.FBSResearchMethod.clockReport(game,value,G.captureClock);
        const refs=['winner','margin','total'].map(t=>G.reference(game,provider,t));
        const why=target=>A.missingReason(game,value,target,family);
        return `<article class="game-card" data-card-game="${esc(game.id)}"><div class="game-card-meta"><span>${esc(game.season+' · Week '+game.week)}</span><span class="chip ${game.completed?'final-chip':''}">${game.completed?'Observed final':'No observed final'}</span></div><h3>${esc(game.away)} <span>at</span> ${esc(game.home)}</h3><p class="card-kickoff">${esc(game.kickoff_exact?date(game.kickoff):'Exact kickoff TBD')}${game.new_fixture_epoch?' · new fixture epoch; prediction pending':''}${game.newly_observed_final?' · newly observed final':''}</p><p class="card-result">${game.completed?esc(game.away_score+' – '+game.home_score+' · '+game.winner+' won'):esc('Result snapshot: '+game.result_snapshot)}${small('Official ID '+game.id)}</p><div class="card-pick"><span>${esc($('model-view').selectedOptions[0].text)}</span><strong>${hasWinner?esc(value.winner):'Winner unavailable'}</strong><div>${hasWinner?percent(Math.max(value.p,1-value.p))+small('Home '+percent(value.p)):small(why('winner'))}</div></div><div class="card-targets"><div><span>Home margin</span><b>${signed(value.margin)}</b>${!A.hasTarget(value,'margin')?small(why('margin')):''}</div><div><span>Total points</span><b>${number(value.total)}</b>${!A.hasTarget(value,'total')?small(why('total')):''}</div><div class="cover-cell"><span>Cover probability</span><b>${A.hasTarget(value,'cover')?percent(value.model.margin.cover_probability):'Unavailable'}</b>${small('Requires an admitted exact line and cutoff')}</div></div><div class="card-intervals"><div><span>Margin intervals</span><p><b>80%</b> ${pairText(mi.interval80)}<br><b>95%</b> ${pairText(mi.interval95)}</p></div><div><span>Total intervals</span><p><b>80%</b> ${pairText(ti.interval80)}<br><b>95%</b> ${pairText(ti.interval95)}</p></div></div><p class="card-reference"><b>${esc(provider)} · retained reference</b><span>Home ${esc(refs[0].value)} · Margin ${esc(refs[1].value)} · Total ${esc(refs[2].value)}</span></p><p class="output-timing" data-output-timing="${computed.status}">${esc(computed.label)}${small('Computation timing does not authenticate issuance')}</p><p class="private-refresh-status">${Object.keys(window.FBSResearchMethod.metadata(game.id)?.four_epoch_models||{}).length?'New private research metadata available · open details. Displayed numbers remain the legacy snapshot.':game.new_fixture_epoch?'Newly resolved kickoff requires a new forecast identity.':'No newer private-study output for this fixture.'}</p><p class="forecast-age" data-forecast-age="${esc(age.status)}"><b>${esc(age.label)}</b>${small("Age at dated capture: "+window.FBSResearchMethod.hoursLabel(age.age_hours))}${small("Original lead time: "+window.FBSResearchMethod.hoursLabel(age.horizon_hours))}</p><details class="card-clocks"><summary>Model and source clocks</summary><dl><dt>Reconstructed cutoff</dt><dd>${esc(clock.cutoff||'No retained reconstructed cutoff')}</dd><dt>Output computed</dt><dd>${esc(clock.computed_first||'No retained output clock')}${clock.computed_last&&clock.computed_last!==clock.computed_first?' through '+esc(clock.computed_last):''}</dd><dt>Reference quote</dt><dd>${esc(game[provider+'_winner_quote_at']||'No retained quote clock')}</dd><dt>Age measured at</dt><dd>${esc(age.age_as_of)}</dd><dt>Result observed</dt><dd>${esc(game.result_observed_at)}</dd></dl><p>Earlier-data reconstruction does not authenticate historical source possession or pregame issuance.</p></details><button class="secondary card-details" data-card-details="${esc(game.id)}">Inspect all models &amp; source evidence</button></article>`;
      }).join('')||'<p class="card-empty">No games match these filters. Clear game filters to restore the fixture list.</p>';
      $('active-result-snapshot').textContent=$('capture-view').selectedOptions[0].text.replace(/^/,'Results: ');
      renderCoverage();
    }
    $('game-layout').addEventListener('change',()=>G.renderGames());
    $('game-cards').addEventListener('click',event=>{const button=event.target.closest('[data-card-details]');if(button)G.openGame(button.dataset.cardDetails);});
    $('family-coverage-rows').addEventListener('click',event=>{const button=event.target.closest('[data-model-choice]');if(!button)return;$('model-view').value=button.dataset.modelChoice;$('model-filter').value='all';$('coverage-target').value='any';$('model-view').dispatchEvent(new Event('change'));$('game-heading').scrollIntoView({block:'start'});});
    document.addEventListener('fbs:games-rendered',renderCards);renderCards();
  }
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
