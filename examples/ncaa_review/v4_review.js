/* Generic private-file inspector. No model code, provider requests or embedded owner data. */
(() => {
  'use strict';
  const refresh = typeof module !== 'undefined' && module.exports ? require('./refresh_review.js') : window.NCAARefreshReview;
  const projection = typeof module !== 'undefined' && module.exports ? require('./projection_review.js') : window.NCAAProjectionReview;
  const TRACKS = Object.freeze([
    'original_frozen_issued', 'historically_reconstructed_rolling',
    'genuinely_future_issued_rolling', 'model_market_source_only_reference',
  ]);
  const LABELS = Object.freeze({
    original_frozen_issued: 'Original frozen issues',
    historically_reconstructed_rolling: 'Historical rolling reconstruction',
    genuinely_future_issued_rolling: 'Genuinely future rolling issues',
    model_market_source_only_reference: 'Model, market and source references',
  });
  const METRICS = ['accuracy','log_loss','brier','mae','rmse','mean_error','ece_10_equal_width'];
  const LIMIT = 16 * 1024 * 1024, PART = 8 * 1024 * 1024;
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const count = v => Number.isSafeInteger(v) && v >= 0;
  const hash = v => typeof v === 'string' && /^[0-9a-f]{64}$/.test(v);
  const pin = (v, bound) => object(v) && count(v.bytes) && v.bytes <= bound && hash(v.sha256);

  function strictJSON(text) {
    // Detect duplicate object members before JSON.parse discards them.
    let at=0;
    const ws=()=>{while(at<text.length && /\s/.test(text[at]))at++;};
    function string(){const start=at++;let escaped=false;for(;at<text.length;at++){const c=text[at];if(!escaped&&c==='"'){at++;return JSON.parse(text.slice(start,at));}if(!escaped&&c==='\\')escaped=true;else escaped=false;}throw Error('Unterminated JSON string.');}
    function value(depth){if(depth>80)throw Error('JSON nesting exceeds the review bound.');ws();const c=text[at];if(c==='{'){at++;ws();const keys=new Set();if(text[at]==='}'){at++;return;}while(true){ws();if(text[at]!=='"')throw Error('Invalid JSON object member.');const key=string();if(keys.has(key))throw Error('Duplicate JSON member: '+key);keys.add(key);ws();if(text[at++]!==':')throw Error('Missing JSON member separator.');value(depth+1);ws();if(text[at]==='}'){at++;return;}if(text[at++]!==',')throw Error('Invalid JSON object separator.');}}
      if(c==='['){at++;ws();if(text[at]===']'){at++;return;}while(true){value(depth+1);ws();if(text[at]===']'){at++;return;}if(text[at++]!==',')throw Error('Invalid JSON array separator.');}}
      if(c==='"'){string();return;}const token=/^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(at));if(!token)throw Error('Invalid JSON value.');if(/^-?\d/.test(token[0])&&!Number.isFinite(Number(token[0])))throw Error('Nonfinite JSON number.');at+=token[0].length;}
    value(0);ws();if(at!==text.length)throw Error('Unexpected trailing JSON content.');return JSON.parse(text);
  }
  function validateStream(value) {
    if(!object(value)||value.schema!=='sel.ncaa.b054.evidence_parts.v1'||!count(value.rows)||!count(value.logical_bytes)||!hash(value.logical_sha256)||value.maximum_logical_part_bytes!==PART||value.all_parts_required_at_use!==true||value.known_missing_parts_are_fatal!==true||value.model_fit_credit_from_stream_rows!==0||!Array.isArray(value.parts)||value.parts.length>100000)throw Error('Invalid V4 evidence stream.');
    let rows=0,bytes=0;
    for(const [ordinal,part] of value.parts.entries()){
      if(!object(part)||part.ordinal!==ordinal||!count(part.rows)||!pin(part.logical,PART)||!pin(part.reference,48*1024*1024)||part.encoding!=='gzip/canonical-json-lines')throw Error('Invalid V4 part identity or bound.');
      rows+=part.rows;bytes+=part.logical.bytes;
      if(!Number.isSafeInteger(rows)||!Number.isSafeInteger(bytes))throw Error('V4 inventory exceeds safe integer bounds.');
    }
    if(rows!==value.rows||bytes!==value.logical_bytes)throw Error('V4 part totals do not match the declared stream.');
    return value;
  }
  function validateV4(value) {
    if(!object(value)||!['B054','B055'].includes(value.release)||value.schema!=='sel.ncaa.'+value.release.toLowerCase()+'.private_review.v1'||value.project!=='ncaa_basketball'||value.audience!=='private')throw Error('Choose the separate V4 private review JSON for B054 or B055.');
    if(!Array.isArray(value.tracks)||JSON.stringify(value.tracks)!==JSON.stringify(TRACKS))throw Error('The four evidence tracks are incomplete or reordered.');
    if(value.historical_reconstruction_is_not_as_issued!==true||value.original_issue_mutation!==false||value.automatic_promotion!==false||value.all_physical_season_games_complete!==false)throw Error('V4 evidence qualifications are missing or changed.');
    if(!object(value.report)||!object(value.metrics)||value.metrics.schema!=='sel.ncaa.b054.metrics.v1'||!Array.isArray(value.metrics.rows)||value.metrics.rows.length>200000||!object(value.metrics.dispositions)||!object(value.streams))throw Error('V4 report inventories are missing.');
    if(value.metrics.source_only_rows_excluded_from_numeric_metrics!==true||value.metrics.paired_gain_claim!==false||value.metrics.no_cross_cohort_denominator_substitution!==true)throw Error('V4 metric qualifications are missing or changed.');
    for(const row of value.metrics.rows){
      if(!object(row)||!['ncaam','ncaaw'].includes(row.league)||!Number.isInteger(row.season_end_year)||!['win','margin','total'].includes(row.target)||!TRACKS.slice(0,3).includes(row.evaluation_track)||!count(row.n)||row.n===0)throw Error('Invalid V4 metric population identity.');
      for(const field of METRICS)if(row[field]!==undefined&&row[field]!==null&&(typeof row[field]!=='number'||!Number.isFinite(row[field])))throw Error('Invalid V4 metric value.');
      for(const field of ['accuracy','brier','ece_10_equal_width'])if(row[field]!==undefined&&row[field]!==null&&(row[field]<0||row[field]>1))throw Error('V4 probability metric outside its range.');
      for(const field of ['log_loss','mae','rmse'])if(row[field]!==undefined&&row[field]!==null&&row[field]<0)throw Error('V4 loss must be nonnegative.');
    }
    for(const stream of Object.values(value.streams))validateStream(stream);
    if(value.report.refresh_coverage!==undefined&&value.report.refresh_coverage!==null){
      if(value.release!=='B055')throw Error('Refresh coverage requires the B055 review contract.');
      refresh.validate(value.report.refresh_coverage,value.streams,validateStream);
    }else if(value.streams.refresh_plan||value.streams.refresh_audit){throw Error('Refresh streams require their coverage manifest.');}
    if(value.report.score_projection_coverage!==undefined&&value.report.score_projection_coverage!==null){
      if(value.release!=='B055')throw Error('Expected scores require the B055 review contract.');
      projection.validate(value.report.score_projection_coverage,value.streams,validateStream);
    }else if(value.streams.score_projections){throw Error('Expected-score stream requires its coverage manifest.');}
    return value;
  }
  async function digest(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
  async function decodePart(bytes, part) {
    if(bytes.byteLength!==part.reference.bytes||await digest(bytes)!==part.reference.sha256)throw Error('Compressed part bytes or SHA-256 differ from the selected manifest.');
    if(typeof DecompressionStream!=='function')throw Error('This browser cannot decode bounded gzip parts.');
    const reader=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')).getReader(),chunks=[];let total=0;
    while(true){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>part.logical.bytes||total>PART){await reader.cancel();throw Error('Decoded part exceeds its exact bound.');}chunks.push(value);}
    if(total!==part.logical.bytes)throw Error('Decoded part length differs from the selected manifest.');
    const body=new Uint8Array(total);let offset=0;for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.length;}
    if(await digest(body)!==part.logical.sha256)throw Error('Decoded logical SHA-256 mismatch.');
    const text=new TextDecoder('utf-8',{fatal:true}).decode(body);
    if(!text.endsWith('\n'))throw Error('V4 JSONL part lacks its terminating newline.');
    const rows=text.slice(0,-1).split('\n').map(strictJSON);
    if(rows.length!==part.rows||rows.some(row=>!object(row)))throw Error('Decoded V4 row inventory differs.');
    return rows;
  }
  if(typeof module!=='undefined'&&module.exports){module.exports={TRACKS,LABELS,strictJSON,validateV4,validateStream,decodePart};return;}
  window.NCAAReviewContracts=Object.freeze({strictJSON,validateStream});
  if(typeof document==='undefined')return;
  const $=id=>document.getElementById(id), node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;};
  let current=null,physical=null,generation=0,metricPage=0,partRows=[],partPage=0,partProof=null;
  const display=v=>v===undefined||v===null?'Unavailable':typeof v==='number'?Number.isInteger(v)?String(v):v.toFixed(6):String(v);
  function detail(label,value){const d=node('details'),p=node('pre');d.append(node('summary',label));d.addEventListener('toggle',()=>{if(d.open){p.textContent=JSON.stringify(value,null,2);if(!p.parentNode)d.append(p);}});return d;}
  function options(id,values,label){const previous=$(id).value;$(id).replaceChildren(new Option(label,'all'),...[...new Set(values)].sort().map(v=>new Option(v,v)));$(id).value=[...$(id).options].some(v=>v.value===previous)?previous:'all';}
  function filteredMetrics(){return current.metrics.rows.filter(r=>($('v4-track').value==='all'||r.evaluation_track===$('v4-track').value)&&($('v4-league').value==='all'||r.league===$('v4-league').value)&&($('v4-target').value==='all'||r.target===$('v4-target').value)&&($('v4-season').value==='all'||String(r.season_end_year)===$('v4-season').value));}
  function renderMetrics(){if(!current)return;const rows=filteredMetrics(),pages=Math.max(1,Math.ceil(rows.length/25));metricPage=Math.min(metricPage,pages-1);const shown=rows.slice(metricPage*25,metricPage*25+25),body=$('v4-metric-rows');body.replaceChildren();for(const r of shown){const tr=node('tr');for(const v of [r.league,r.season_end_year,r.target,LABELS[r.evaluation_track],r.selector,r.horizon_minutes,r.n,...METRICS.map(k=>r[k])])tr.append(node('td',display(v)));body.append(tr);}$('v4-metric-count').textContent=rows.length+' supplied metric populations; '+(current.metrics.rows.length-rows.length)+' hidden by filters. '+(rows.length?'Showing '+(metricPage*25+1)+'–'+(metricPage*25+shown.length)+'.':'No evaluated population was supplied for this selection.');$('v4-metric-previous').disabled=metricPage===0;$('v4-metric-next').disabled=metricPage+1>=pages;}
  function selectedStream(){return current?.streams[$('v4-stream').value];}
  function selectedPart(){return selectedStream()?.parts[Number($('v4-part').value)];}
  function renderParts(){
    const isPlan=$('v4-stream').value==='refresh_plan'&&refresh.active();
    const isScore=$('v4-stream').value==='score_projections'&&projection.active();
    const isOperational=['refresh_audit','refresh_state'].includes($('v4-stream').value);
    const trackRows=partRows.filter(r=>$('v4-track').value==='all'||r.evaluation_track===$('v4-track').value);
    const rows=isPlan?refresh.filtered(partRows):isOperational?partRows:isScore?projection.filtered(trackRows):trackRows;
    const pages=Math.max(1,Math.ceil(rows.length/25));partPage=Math.min(partPage,pages-1);
    $('v4-part-count').textContent=partProof?'Showing '+rows.length+' matching rows from '+partRows.length+' verified rows in one part; '+(partRows.length-rows.length)+' hidden by filters. Other parts remain unloaded; full stream closure is not claimed.':'No evidence part loaded. A manifest and its row count are references, not loaded game records.';
    const target=$('v4-part-rows');target.replaceChildren();
    for(const r of rows.slice(partPage*25,partPage*25+25)){
      const card=node('article');card.className='eligibility-card';card.dataset.v4Record='';
      const identity=r.event_id??r.target_game?.event_id??r.game?.event_id;
      card.append(node('h3',isOperational?'Refresh evidence · '+display(r.kind)+' · '+display(r.identity??r.event_key??r.recipe_id??r.snapshot_id??'See exact record'):[display(r.league??r.target_game?.league),display(identity),isScore?'Expected scores':display(r.target)].join(' · ')));
      if(isPlan){
        card.dataset.refreshState=r.state;
        card.append(node('p','Recorded plan state: '+refresh.LABELS[r.state]),
          node('p','Reason: '+r.reason),node('p','Next action: '+r.next_action),
          node('p','Window opens: '+display(r.window_open_at)+' · Cutoff: '+display(r.cutoff_time)),
          node('p','Declared role: '+display(r.role)+'. This row is a plan disposition, not a new forecast.'));
      }else if(isOperational){
        card.append(node('p','Record kind: '+display(r.kind)),node('p','Recorded disposition: '+display(r.disposition??r.last_execution_disposition??r.fit_reused_or_new??'No execution disposition supplied for this record kind')),
          node('p','Plan state: '+display(r.planned_state??'Not a per-context plan record')),
          node('p',$('v4-stream').value==='refresh_state'?'Persisted trigger-comparison state; it does not authenticate a current model or server-issued forecast.':'A separate execution record; it does not replace the immutable plan denominator.'));
      }else if(isScore){
        card.dataset.scoreStatus=r.status;
        if(r.status==='NON_NUMERIC_OR_SOURCE_ONLY'){
          card.append(node('p','Exact source event key: '+display(r.event_key)),
            node('p','Input disposition: '+display(r.input_disposition)+' · Input target: '+display(r.input_target)),
            node('p','Input record SHA-256: '+display(r.input_record_sha256)),
            node('p','Missing league, event ID or source clocks remain unavailable; this view never derives them from the source key.'));
        }
        card.append(node('p','Disposition: '+projection.LABELS[r.status]),
          node('p','Home: '+display(r.home_team??r.home_id)+' · Expected score: '+display(r.mean_home_score)),
          node('p','Away: '+display(r.away_team??r.away_id)+' · Expected score: '+display(r.mean_away_score)),
          node('p','Retained margin input: '+display(r.expected_home_minus_away)+' · Total input: '+display(r.expected_total)),
          node('p','Origin: '+display(r.prediction_origin)+' · Cutoff: '+display(r.cutoff_time)+' · Horizon minutes: '+display(r.horizon_minutes)),
          node('p','Margin prediction ID: '+display(r.margin_prediction_id)),
          node('p','Total prediction ID: '+display(r.total_prediction_id)),
          node('p','Supplied context: '+display(r.model_context?.family)+' / '+display(r.model_context?.arm)+' / '+(object(r.model_context?.training_history)?JSON.stringify(r.model_context.training_history):display(r.model_context?.training_history))),
          node('p','Fractional derived means only; no joint score distribution, line-result probability or new issue.'));
      }else{
        card.append(node('p','Track: '+(LABELS[r.evaluation_track]||display(r.evaluation_track))+' · State: '+display(r.status??r.disposition)),node('p','Prediction: '+display(r.prediction)+' · Outcome: '+display(r.actual)));
      }
      card.append(detail('Exact supplied record and clocks',r));target.append(card);
    }
    $('v4-part-previous').disabled=partPage===0;$('v4-part-next').disabled=partPage+1>=pages;
  }
  function resetPart(){generation++;partRows=[];partPage=0;partProof=null;refresh.setPart([],null,null);$('v4-part-file').value='';$('v4-part-status').textContent='';renderParts();}
  function resetStream(){resetPart();const stream=selectedStream();$('v4-part').replaceChildren(...(stream?.parts||[]).map((p,i)=>new Option('Part '+(i+1)+' · '+p.rows+' rows',String(i))));$('v4-part-file').disabled=!stream?.parts.length;$('v4-stream-proof').replaceChildren(...(stream?[detail('Declared full stream and exact part pins',stream)]:[]));}
  function load(value,pin){current=validateV4(value);physical=pin;refresh.render(current.report.refresh_coverage,physical);projection.render(current.report.score_projection_coverage);generation++;metricPage=0;$('v4-content').hidden=false;$('clear-v4').disabled=false;$('v4-track').value='all';$('v4-league').value='all';$('v4-target').value='all';options('v4-season',current.metrics.rows.map(r=>String(r.season_end_year)),'All supplied seasons');$('v4-summary-cards').replaceChildren(...TRACKS.map(track=>{const n=node('div');n.className='clock-card';n.append(node('strong',LABELS[track]),node('span',current.metrics.rows.filter(r=>r.evaluation_track===track).length+' metric populations supplied'));return n;}));$('v4-execution').replaceChildren(node('p','Recorded status: '+display(current.status)),detail('Execution, typed counts and remaining work',current.report),detail('Selected file identity and retained qualifications',{physical_pin:physical,source_sha256:current.source_sha256,run_id:current.run_id,created_at:current.created_at,automatic_promotion:current.automatic_promotion,all_physical_season_games_complete:current.all_physical_season_games_complete,metric_dispositions:current.metrics.dispositions}));$('v4-stream').replaceChildren(...Object.entries(current.streams).map(([name,stream])=>new Option(name+' · '+stream.rows+' declared rows',name)));resetStream();renderMetrics();$('v4-status').className='status';$('v4-status').textContent='V4 review loaded. Four evidence tracks remain separate; no game stream is automatically loaded and no promotion is implied.';}
  $('v4-summary-file').addEventListener('change',async()=>{const file=$('v4-summary-file').files[0],token=++generation;if(!file)return;try{if(file.size>LIMIT)throw Error('Review summary exceeds 16 MiB.');const bytes=await file.arrayBuffer(),value=strictJSON(new TextDecoder('utf-8',{fatal:true}).decode(bytes));validateV4(value);const sha=await digest(bytes);if(token!==generation)return;load(value,{bytes:bytes.byteLength,sha256:sha});}catch(e){if(token===generation){$('v4-status').className='status error';$('v4-status').textContent='Cannot open V4 review: '+e.message+' The previous valid view remains.';}}});
  $('v4-part-file').addEventListener('change',async()=>{const file=$('v4-part-file').files[0],part=selectedPart(),token=++generation;if(!file||!part)return;try{if(file.size!==part.reference.bytes)throw Error('Selected file size differs from the pinned part.');const rows=await decodePart(await file.arrayBuffer(),part);if($('v4-stream').value==='refresh_plan'&&refresh.active())refresh.validatePlanRows(rows,refresh.asof());if($('v4-stream').value==='score_projections'&&projection.active())projection.validateRows(rows);if(token!==generation)return;partRows=rows;partPage=0;partProof=part;refresh.setPart(rows,part,$('v4-stream').value);$('v4-part-status').className='status';$('v4-part-status').textContent='Verified compressed and decoded SHA-256, exact sizes and '+rows.length+' rows for this selected part.';renderParts();}catch(e){if(token===generation){$('v4-part-status').className='status error';$('v4-part-status').textContent='Cannot open V4 part: '+e.message+' Previous valid rows remain.';}}});
  const inspectionCallbacks={changed:()=>{partPage=0;renderParts();},inspect:name=>{if(!current?.streams[name])return;$('v4-stream').value=name;resetStream();$('v4-part-file').scrollIntoView({block:'center'});}};
  refresh.setup(inspectionCallbacks);projection.setup(inspectionCallbacks);
  for(const id of ['v4-track','v4-league','v4-target','v4-season'])$(id).addEventListener('change',()=>{metricPage=0;partPage=0;renderMetrics();renderParts();});
  $('v4-stream').addEventListener('change',resetStream);$('v4-part').addEventListener('change',resetPart);
  $('v4-metric-previous').addEventListener('click',()=>{metricPage--;renderMetrics();});$('v4-metric-next').addEventListener('click',()=>{metricPage++;renderMetrics();});$('v4-part-previous').addEventListener('click',()=>{partPage--;renderParts();});$('v4-part-next').addEventListener('click',()=>{partPage++;renderParts();});
  $('clear-v4').addEventListener('click',()=>{generation++;current=null;physical=null;partRows=[];partProof=null;refresh.render(null,null);projection.render(null);$('v4-content').hidden=true;$('clear-v4').disabled=true;for(const id of ['v4-summary-cards','v4-execution','v4-metric-rows','v4-part-rows','v4-stream-proof'])$(id).replaceChildren();$('v4-summary-file').value='';$('v4-part-file').value='';$('v4-status').textContent='V4 review cleared. The independent game, schedule and eligibility views are unchanged.';});
})();
