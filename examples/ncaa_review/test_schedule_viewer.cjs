// Invented schedule-only records exercise the exact public viewer contract.
// They are not provider captures, forecasts, owner execution or scientific results.
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {createHash,webcrypto}=require('node:crypto');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const clone=value=>JSON.parse(JSON.stringify(value));
const fields=['winner_prediction','win_probability','point_margin','total_points','cover_probability','push_probability','loss_probability'];
function ref(name){const bytes=Buffer.from('INVENTED ONLY: '+name);return {bucket:'invented-private-fixture',key:'invented/'+name,bytes:bytes.length,sha256:sha(bytes)};}
function fixture(count=27){
  const records=Array.from({length:count},(_,i)=>{
    const provider=i%2?'ncaa_official':'espn',league=i%4<2?'ncaam':'ncaaw';
    const native=i<2?'invented-shared-native-id':'invented-native-'+i,prefix=league+(provider==='espn'?':espn:':':ncaa:');
    const day='2027-'+(i===3?'03':'02')+'-'+String(1+i%26).padStart(2,'0');
    const time=i===2?null:day+'T01:00:00+00:00';
    return {schema:'sel.ncaa.b050.full_season_schedule.v1.provider_game_index',provider,league,season_end_year:2027,
      event_id:prefix+(provider==='espn'?'event:':'contest:')+native,native_event_id:native,source_version_id:sha('invented-version-'+i),source_row_index:i,
      home_id:prefix+'team:home-'+i,away_id:prefix+'team:away-'+i,home_team:i<2?'Invented shared home':'Invented home '+i,away_team:i<2?'Invented shared away':'Invented away '+i,
      event_time:time,source_reported_event_time:i===2?'2027-02-03T00:00:00Z':time,time_precision:time===null?'unknown':'exact',status:'scheduled',source_phase:{phase:'unknown',verified:false},query_date:day,
      request_identity_sha256:sha('invented-request-identity-'+i),source_request_id:sha('invented-request-'+i),source_raw_reference:ref('raw-'+i),
      source_request_started_utc:'2026-11-07T20:00:00+00:00',acquired_at:'2026-11-07T20:00:01+00:00',source_publication_time:null,publication_time_status:'NOT_PROVEN_BY_CAPTURE_CLOCK',
      beyond_original_source_query_end:true,forecast_status:'NOT_JOINED_SCHEDULE_ONLY',forecast_gap_reason:'OUTSIDE_UNCHANGED_MODEL_ACQUISITION_WINDOW',prediction_eligibility:'NOT_EVALUATED_BY_SCHEDULE_INVENTORY',
      may_enter_fitting_feature_selection_or_promotion:false,model_inputs_changed:false,new_forecast_credit:0,...Object.fromEntries(fields.map(k=>[k,null])),
      source_version_count:i===3?2:1,source_binding_status:i===3?'SOURCE_IDENTITY_CHANGE_REQUIRES_REVIEW':'SOURCE_NATIVE_ID_OBSERVED',all_versions_retained_in_source_game_versions:true,cross_provider_match_claimed:false};
  });
  const streams=Object.fromEntries(['source_game_versions','request_dispositions','rejected_source_records','provider_game_index'].map(name=>[name,ref(name+'-root')]));
  const source_sha256=sha('invented-source'),owner_run_id='INVENTED_SCHEDULE_RUN',asof='2026-11-07T20:00:00+00:00';
  const summary={schema:'sel.ncaa.b050.full_season_schedule.v1',policy:'full_current_season_known_schedule_v1',owner_run_id,source_sha256,asof,
    completed_at:'2026-11-07T20:01:00+00:00',status:'FINITE_PLAN_ACCOUNTED_WITH_EXPLICIT_GAPS',original_calendar_scope_unchanged:{source_query_end:'2026-11-22'},
    source_query_start:'2026-07-01',source_query_end:'2027-06-30',planned_provider_league_dates:1460,accounted_provider_league_dates:1460,
    all_planned_dates_have_dispositions:true,all_provider_date_responses_validated:false,streams,
    stream_record_counts:{source_game_versions:records.reduce((n,r)=>n+r.source_version_count,0),request_dispositions:1460,rejected_source_records:1,provider_game_index:records.length},
    provider_native_game_ids:records.length,retained_display_index_ids:records.length,display_index_id_bound:100000,source_versions_beyond_display_index_bound:0,display_index_complete_for_observed_ids:true,
    source_game_ids_are_provider_specific_not_cross_source_game_count:true,full_season_complete:false,complete_official_denominator:false,model_inputs_changed:false,forecasts_joined_or_issued:0,new_model_fit_credit:0};
  const value={schema:'sel.ncaa.b050.schedule_display.v1',project:'ncaa_basketball',source_sha256,owner_run_id,asof,generated_at:'2026-11-07T20:01:01+00:00',model_inputs_changed:false,new_forecast_credit:0,full_season_complete:false,
    status:'FULL_PROVIDER_GAME_INDEX_INCLUDED',records,records_included:records.length,records_expected:records.length,maximum_utf8_bytes:26214400,reference_only_reason:null,summary,
    report_reference:ref('collector-report'),provider_game_index_reference:streams.provider_game_index,streams,
    proofs:{report_raw_pin_verified:true,provider_index_root_pin_verified:true,provider_index_complete_iteration_verified:true,snapshot_counts_match_report:true,display_rows_no_forecasts:true}};
  const body=Buffer.from(JSON.stringify(value));return {value,body,pin:{bytes:body.length,sha256:sha(body)}};
}
function referenceFixture(kind='byte',count=27){const value=clone(fixture(count).value);value.status=kind==='source'?'REFERENCE_ONLY_SOURCE_INDEX_BOUND':'REFERENCE_ONLY_DISPLAY_BYTE_BOUND';value.records=[];value.records_included=0;value.reference_only_reason=kind==='source'?'SOURCE_INDEX_BOUND_REACHED':'COMPLETE_DISPLAY_EXCEEDS_UTF8_BOUND';if(kind==='source'){value.summary.source_versions_beyond_display_index_bound=1;value.summary.display_index_complete_for_observed_ids=false;value.summary.provider_native_game_ids=null;}const body=Buffer.from(JSON.stringify(value));return {value,body,pin:{bytes:body.length,sha256:sha(body)}};}
module.exports={fixture,referenceFixture,createHarness};

function createHarness(input){
  const html=fs.readFileSync(input||path.join(__dirname,'private_report.html.tmpl'),'utf8');
  let script=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]).join('\n');
  assert(/\}\)\(\);\s*$/.test(script));
  script=script.replace(/\}\)\(\);\s*$/,`globalThis.api={decodeScheduleCompact,scheduleJsonBudget,validateScheduleDisplay,parseScheduleBytes,loadScheduleDisplay,clearScheduleDisplay,resetScheduleFilters,filteredScheduleRecords,renderScheduleRows,scheduleEventDate,state:()=>scheduleState,pin:()=>schedulePhysicalPin,setBaseline(value){report=value;recordRows=value.records;games=value.records;identityOverlay={value:{fixture:'baseline-overlay'}};},baseline:()=>({report,recordRows,games,identityOverlay})};})();`);
  class Element{
    constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.dataset={};this.value='all';this.hidden=false;this.disabled=false;this.own='';this.className='';this.files=[];}
    append(...items){this.children.push(...items);}
    replaceChildren(...items){this.children=items;this.own='';if(this.tagName==='select')this.value=items[0]?.value??'';}
    addEventListener(event,handler){this.events[event]=handler;}
    get textContent(){return this.own+this.children.map(x=>typeof x==='string'?x:x.textContent).join('\n');}
    set textContent(value){this.own=String(value);this.children=[];}
    get lastChild(){return this.children.at(-1);}
    get options(){return this.children;}
    querySelector(){return null;}
    setAttribute(name,value){this[name]=value;}
    get classList(){return {contains:name=>this.className.split(' ').includes(name)};}
  }
  const nodes=new Map(),get=id=>{if(!nodes.has(id)){const n=new Element(/(?:provider|league|date)$/.test(id)?'select':'div');if(id.endsWith('search'))n.value='';nodes.set(id,n);}return nodes.get(id);};
  const context={Node:Element,Option:function(label,value){this.textContent=label;this.value=value;},document:{getElementById:get,createElement:tag=>new Element(tag),createTextNode:text=>{const n=new Element('text');n.textContent=text;return n;}},TextDecoder,TextEncoder,Uint8Array,ArrayBuffer,crypto:webcrypto};
  vm.createContext(context);vm.runInContext(script,context);return {api:context.api,get,html};
}

async function run(){
  const {api,get,html}=createHarness(process.argv[2]);const tests=[];
  function check(name,test){test();tests.push(name);}
  const f=fixture(),before=JSON.stringify(f.value);const valid=x=>api.validateScheduleDisplay(x,f.pin);
  function reject(name,mutate,pattern){check(name,()=>{const x=clone(f.value);mutate(x);assert.throws(()=>valid(x),pattern);});}
  check('full schedule accepts all source-native records without mutating input',()=>{const x=valid(f.value);assert.equal(x.records.length,27);assert.equal(JSON.stringify(f.value),before);assert.equal(x.missingExactTimes,1);assert.equal(x.sourceConflicts,1);assert.equal(x.versionCount,28);});
  check('same native ID and matchup from two providers remains two records',()=>{const x=valid(f.value);assert.equal(x.records[0].native_event_id,x.records[1].native_event_id);assert.notEqual(x.records[0].event_id,x.records[1].event_id);assert.equal(x.records.length,27);});
  check('provider and gender denominators remain separate',()=>{const x=valid(f.value);assert.equal(x.counts.length,4);assert.equal(x.counts.reduce((n,g)=>n+g.records,0),27);assert.equal(x.counts.find(g=>g.provider==='espn'&&g.league==='ncaaw').missing_exact_times,1);});
  check('unknown tip time does not borrow query date or reported placeholder',()=>{assert.equal(api.scheduleEventDate(f.value.records[2]),null);assert(!valid(f.value).knownDates.includes('2027-02-03'));});
  reject('duplicate provider-native ID is rejected',x=>x.records[1]={...x.records[0]},/Duplicate/);
  reject('cross-provider event namespace is rejected',x=>x.records[0].event_id=x.records[1].event_id,/source-native/);
  reject('foreign league is rejected',x=>x.records[0].league='nba',/schema, provider or league/);
  reject('foreign provider is rejected',x=>x.records[0].provider='unapproved',/schema, provider or league/);
  reject('team identities cannot cross league/provider',x=>x.records[0].home_id='ncaaw:espn:team:other',/team IDs/);
  reject('duplicate source version is rejected',x=>x.records[1].source_version_id=x.records[0].source_version_id,/Duplicate/);
  for(const field of fields)reject('schedule forecast '+field+' must remain null',x=>x.records[0][field]=field==='winner_prediction'?'Invented home':.6,/cannot contain a forecast/);
  reject('unsupported forecast alias cannot bypass row schema',x=>x.records[0].prediction_win=.6,/row schema/);
  reject('cross-provider match claim is rejected',x=>x.records[0].cross_provider_match_claimed=true,/cannot contain a forecast/);
  reject('eligibility claim is rejected',x=>x.records[0].prediction_eligibility='ELIGIBLE',/cannot contain a forecast/);
  reject('missing forecast field is rejected rather than treated as null',x=>delete x.records[0].cover_probability,/row schema/);
  reject('model input mutation claim is rejected',x=>x.model_inputs_changed=true,/safeguards/);
  reject('complete-season claim is rejected',x=>x.full_season_complete=true,/safeguards/);
  reject('source run cannot change between root and summary',x=>x.owner_run_id='other-run',/summary does not agree/);
  reject('source hash cannot change between root and summary',x=>x.source_sha256='e'.repeat(64),/summary does not agree/);
  reject('included count cannot hide a record',x=>x.records_included--,/counts or bounds/);
  reject('declared source-ID count must match report index',x=>x.records_expected--,/index counts/);
  reject('known source reference conflict is rejected',x=>x.provider_game_index_reference={...x.provider_game_index_reference,sha256:'d'.repeat(64)},/reference bindings/);
  reject('summary stream cannot change source raw pin',x=>x.summary.streams.provider_game_index={...x.summary.streams.provider_game_index,bytes:999},/reference bindings/);
  reject('required supplied proof flag cannot be missing',x=>delete x.proofs.report_raw_pin_verified,/proof flags/);
  reject('invalid NaT event clock is rejected',x=>x.records[0].event_time='NaT',/clocks are invalid/);
  reject('invalid calendar day is rejected',x=>x.records[0].event_time='2027-02-30T01:00:00Z',/clocks are invalid/);
  reject('exact time cannot be claimed for null tip',x=>x.records[2].time_precision='exact',/clocks are invalid/);
  reject('capture order cannot be reversed',x=>x.records[0].source_request_started_utc='2026-11-08T20:00:00Z',/clocks are invalid/);
  reject('capture clock cannot become publication clock',x=>x.records[0].source_publication_time=x.records[0].acquired_at,/clocks are invalid/);
  reject('source raw pin must stay within response bound',x=>x.records[0].source_raw_reference.bytes=16*1024*1024+1,/raw-source references/);
  reject('source version accounting must match the full preserved stream',x=>x.records[0].source_version_count++,/source-version counts/);
  reject('outside-window reason must match its original flag',x=>x.records[0].forecast_gap_reason='PRESERVED_OLD_PIPELINE_NOT_JOINED_HERE',/gap reason/);
  check('explicit missing source clock stays null',()=>{const x=clone(f.value);x.records[0].acquired_at=null;x.records[0].source_request_started_utc=null;const r=valid(x);assert.equal(r.records[0].acquired_at,null);});
  check('unknown source hash remains null without authentication credit',()=>{const x=clone(f.value);x.source_sha256=null;x.summary.source_sha256=null;assert.equal(valid(x).value.source_sha256,null);});
  check('25 MiB physical bound applies before accepting records',()=>assert.throws(()=>api.validateScheduleDisplay(f.value,{bytes:26214401,sha256:f.pin.sha256}),/25 MiB bound/));
  check('100000-ID bound is enforced',()=>{const x=clone(f.value);x.records=new Array(100001).fill(x.records[0]);x.records_included=100001;assert.throws(()=>valid(x),/counts or bounds/);});
  check('reference-only byte-bound export has zero loaded versus expected records',()=>{const x=referenceFixture();const r=api.validateScheduleDisplay(x.value,x.pin);assert.equal(r.full,false);assert.equal(r.records.length,0);assert.equal(r.value.records_expected,27);});
  check('reference-only source-index bound retains explicit incomplete source inventory',()=>{const x=referenceFixture('source');const r=api.validateScheduleDisplay(x.value,x.pin);assert.equal(r.full,false);assert.equal(r.value.summary.provider_native_game_ids,null);assert.equal(r.value.summary.source_versions_beyond_display_index_bound,1);});
  check('reference-only cannot silently contain a partial row sample',()=>{const x=referenceFixture();x.value.records=[f.value.records[0]];x.value.records_included=1;assert.throws(()=>api.validateScheduleDisplay(x.value,x.pin),/reference-only states/);});
  check('source-index overflow cannot be mislabeled as full display',()=>{const x=referenceFixture('source');x.value.status='FULL_PROVIDER_GAME_INDEX_INCLUDED';assert.throws(()=>api.validateScheduleDisplay(x.value,x.pin),/reference-only states/);});
  const baseline={schema:'INVENTED_BASELINE',records:[{event_id:'invented-baseline',prediction_win:.5}],metrics:[{n:1,accuracy:.5}]};api.setBaseline(baseline);const baselineBefore=JSON.stringify(api.baseline());
  check('loading schedule leaves baseline rows, overlay and metrics unchanged',()=>{api.loadScheduleDisplay(f.value,f.pin);assert.equal(JSON.stringify(api.baseline()),baselineBefore);assert.equal(get('schedule-content').hidden,false);assert.match(get('schedule-summary').textContent,/does not certify a complete physical season/);});
  check('same-file physical pin is displayed independently of source claims',()=>{assert.match(get('schedule-source-proof').textContent,new RegExp(f.pin.sha256));assert.match(get('schedule-source-proof').textContent,/does not fetch or independently authenticate/);assert.equal(api.pin().sha256,f.pin.sha256);});
  check('provider filter keeps only that native source without joining',()=>{get('schedule-provider').value='espn';assert(api.filteredScheduleRecords().every(r=>r.provider==='espn'));assert.equal(api.filteredScheduleRecords().length,14);});
  check('gender filter composes with provider filter',()=>{get('schedule-league').value='ncaaw';assert(api.filteredScheduleRecords().every(r=>r.league==='ncaaw'&&r.provider==='espn'));assert.equal(api.filteredScheduleRecords().length,7);});
  check('missing-time filter uses null rather than query date',()=>{get('schedule-date').value='missing';const rs=api.filteredScheduleRecords();assert.equal(rs.length,1);assert.equal(rs[0].event_time,null);});
  check('exact event date filter does not promote placeholder time',()=>{api.resetScheduleFilters();get('schedule-date').value='2027-02-01';assert.equal(api.filteredScheduleRecords().length,2);assert(api.filteredScheduleRecords().every(r=>r.event_time!==null));});
  check('search can inspect an exact missing-data reason',()=>{api.resetScheduleFilters();get('schedule-search').value='SOURCE_IDENTITY_CHANGE_REQUIRES_REVIEW';assert.equal(api.filteredScheduleRecords().length,1);});
  check('reset returns every loaded provider-native record',()=>{api.resetScheduleFilters();assert.equal(api.filteredScheduleRecords().length,27);assert.match(get('schedule-count').textContent,/27 loaded.*0 hidden by filters/);});
  check('pagination renders only a bounded subset and can reach every row',()=>{const rows=get('schedule-records').children[0].children[0].children[1];assert.equal(rows.children.length,25);get('schedule-next').events.click();const later=get('schedule-records').children[0].children[0].children[1];assert.equal(later.children.length,2);assert.match(get('schedule-count').textContent,/26–27 of 27/);});
  check('invalid replacement keeps prior valid schedule and baseline intact',()=>{const prior=api.state(),oldPin=api.pin();const x=clone(f.value);x.records[0].win_probability=.7;assert.throws(()=>api.loadScheduleDisplay(x,f.pin),/cannot contain a forecast/);assert.equal(api.state(),prior);assert.equal(api.pin(),oldPin);assert.equal(JSON.stringify(api.baseline()),baselineBefore);});
  check('reference-only render makes unloaded records and reason explicit',()=>{const x=referenceFixture();api.loadScheduleDisplay(x.value,x.pin);assert.match(get('schedule-records').textContent,/No schedule rows are loaded.*not an empty season/);assert.match(get('schedule-summary').textContent,/27 provider-native IDs; zero rows/);});
  check('zero supplied records do not become complete-season certification',()=>{const x=fixture(0);api.loadScheduleDisplay(x.value,x.pin);assert.match(get('schedule-records').textContent,/zero accepted source IDs.*prevent a complete-season claim/);});
  check('clearing schedule leaves original baseline and overlay unchanged',()=>{api.clearScheduleDisplay();assert.equal(api.state(),null);assert.equal(get('schedule-content').hidden,true);assert.equal(JSON.stringify(api.baseline()),baselineBefore);});
  const bytes=s=>new TextEncoder().encode(s).buffer;
  check('archive error names the required schedule JSON',()=>assert.throws(()=>api.parseScheduleBytes(Uint8Array.from([80,75,3,4]).buffer),/B050_FULL_SEASON_SCHEDULE_DATA.json/));
  check('invalid UTF-8 is rejected before schedule JSON parsing',()=>assert.throws(()=>api.parseScheduleBytes(Uint8Array.from([255]).buffer),/UTF-8/));
  check('incomplete schedule JSON gets a specific byte/hash correction',()=>assert.throws(()=>api.parseScheduleBytes(bytes('{"records":')),/not complete, valid JSON.*byte\/hash/));
  check('nonfinite JSON numbers are rejected without coercing to null',()=>assert.throws(()=>api.parseScheduleBytes(bytes('{\"x\":1e9999}')),/not complete, valid JSON/));
  // Exercise the exact asynchronous input listener, not a replacement loader.
  const file={size:f.body.length,arrayBuffer:async()=>Uint8Array.from(f.body).buffer};get('schedule-file').files=[file];await get('schedule-file').events.change();
  check('file input computes SHA256 from the exact selected bytes',()=>{assert.equal(api.pin().sha256,f.pin.sha256);assert.equal(api.pin().bytes,f.body.length);});
  const previous=api.state();let readOversized=false;get('schedule-file').files=[{size:26214401,arrayBuffer:async()=>{readOversized=true;return new ArrayBuffer(0);}}];await get('schedule-file').events.change();
  check('oversized physical file is rejected before reading and preserves previous state',()=>{assert.equal(readOversized,false);assert.equal(api.state(),previous);assert.match(get('schedule-load-status').textContent,/Previous schedule, baseline and overlay remain unchanged/);});
  let resolveOld;const older=new Promise(resolve=>{resolveOld=resolve;});get('schedule-file').files=[{size:f.body.length,arrayBuffer:()=>older}];const pending=get('schedule-file').events.change();const replacement=fixture(4);get('schedule-file').files=[{size:replacement.body.length,arrayBuffer:async()=>Uint8Array.from(replacement.body).buffer}];await get('schedule-file').events.change();resolveOld(Uint8Array.from(f.body).buffer);await pending;
  check('late completion of an older file cannot overwrite a newer selection',()=>{assert.equal(api.state().records.length,4);assert.equal(api.pin().sha256,replacement.pin.sha256);assert.equal(JSON.stringify(api.baseline()),baselineBefore);});
  console.log(JSON.stringify({status:'PASS',kind:'invented_schedule_viewer_contract_not_owner_execution',checks:tests.length,tests,template_sha256:sha(html),browser_observation:'NOT_PERFORMED_BY_THIS_FUNCTION_TEST'}));
}
if(require.main===module)run().catch(error=>{console.error(error);process.exitCode=1;});
