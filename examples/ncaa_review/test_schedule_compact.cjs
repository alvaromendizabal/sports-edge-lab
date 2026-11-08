// Lossless display projection tests use invented data only.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {createHash}=require('node:crypto');
const {fixture,createHarness}=require('./test_schedule_viewer.cjs');
const clone=value=>JSON.parse(JSON.stringify(value));
const sha=value=>createHash('sha256').update(value).digest('hex');
function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
function compactFixture(count=27){
  const flat=fixture(count).value,metadata=clone(flat);delete metadata.records;
  const fields=count?Object.keys(flat.records[0]).sort():[],constant_fields={},record_columns=[];
  for(const key of fields){if(flat.records.every(row=>canonical(row[key])===canonical(flat.records[0][key])))constant_fields[key]=flat.records[0][key];else record_columns.push(key);}
  const value_dictionaries={};
  // Exercise dictionaries holding primitive and object values, and plain columns.
  for(const key of record_columns.filter(k=>['provider','league','home_team','event_time','source_binding_status','source_raw_reference'].includes(k))){const seen=new Map();for(const row of flat.records)seen.set(canonical(row[key]),row[key]);value_dictionaries[key]=[...seen.values()];}
  const record_values=flat.records.map(row=>record_columns.map(key=>Object.hasOwn(value_dictionaries,key)?value_dictionaries[key].findIndex(v=>canonical(v)===canonical(row[key])):row[key]));
  const decoded=Buffer.from(canonical(flat)),original=Buffer.from('INVENTED original reference-only export'),index=Buffer.from(flat.records.map(canonical).join('\n')+'\n');
  const value={schema:'sel.ncaa.b052.schedule_display.compact.v1',project:'ncaa_basketball',encoding:'COLUMN_DICTIONARIES_AND_CONSTANTS_V1',metadata,record_columns,constant_fields,value_dictionaries,record_values,records_included:count,decoded_canonical_pin:{bytes:decoded.length,sha256:sha(decoded)},provenance:{derivation_kind:'ASSISTANT_LOSSLESS_PROJECTION_OF_AUTHENTICATED_OWNER_INDEX',owner_source_sha256:flat.source_sha256,owner_run_id:flat.owner_run_id,report_reference:clone(flat.report_reference),provider_game_index_reference:clone(flat.provider_game_index_reference),original_display_export_pin:{bytes:original.length,sha256:sha(original)},source_index_logical_pin:{bytes:index.length,sha256:sha(index)}}};
  const body=Buffer.from(JSON.stringify(value));return {value,flat,body,pin:{bytes:body.length,sha256:sha(body)}};
}
module.exports={compactFixture};

async function run(){
  const {api,get,html}=createHarness(process.argv[2]),tests=[],f=compactFixture();
  const check=(name,fn)=>{fn();tests.push(name);};
  const reject=(name,change,pattern)=>check(name,()=>{const c=clone(f.value);change(c);assert.throws(()=>api.loadScheduleDisplay(c,f.pin),pattern);});
  const before=JSON.stringify(f.value);
  check('lossless columns constants and dictionaries restore every original field',()=>{const result=api.decodeScheduleCompact(f.value,f.pin);assert.equal(canonical(result.value),canonical(f.flat));assert.equal(result.projection.decoded_json_bytes_measured,f.value.decoded_canonical_pin.bytes);assert.equal(result.projection.decoded_sha256_validation,'DECLARED_NOT_REVERIFIED_IN_BROWSER');assert.equal(JSON.stringify(f.value),before);});
  check('compact file loads full index under unchanged exact row gates',()=>{api.loadScheduleDisplay(f.value,f.pin);assert.equal(api.state().records.length,27);assert.equal(api.state().full,true);assert.match(get('schedule-count').textContent,/27 loaded/);assert.match(get('schedule-source-proof').textContent,/not a new owner execution/);assert.match(get('schedule-source-proof').textContent,/not reverified in this browser/);});
  check('owner derivation keeps its recorded run without assistant relabeling',()=>{const c=clone(f.value);c.provenance.derivation_kind='OWNER_LOSSLESS_PROJECTION';api.loadScheduleDisplay(c,f.pin);assert.match(get('schedule-source-proof').textContent,/produced by the recorded owner run/);});
  reject('foreign envelope field is rejected',x=>x.extra=true,/envelope fields/);
  reject('wrong encoding is rejected',x=>x.encoding='LOSSY',/encoding/);
  reject('metadata cannot hide a competing records array',x=>x.metadata.records=[],/without records/);
  reject('reference-only metadata cannot claim loaded rows',x=>x.metadata.status='REFERENCE_ONLY_DISPLAY_BYTE_BOUND',/full original/);
  reject('duplicate column is rejected',x=>x.record_columns.push(x.record_columns[0]),/sorted and unique/);
  reject('unsorted columns are rejected',x=>x.record_columns.reverse(),/sorted and unique/);
  reject('constant and column overlap is rejected',x=>x.constant_fields[x.record_columns[0]]=null,/disjoint/);
  reject('missing exact field is rejected',x=>delete x.constant_fields.win_probability,/every exact/);
  reject('unknown row field is rejected',x=>x.constant_fields.future_prediction=.7,/every exact/);
  reject('dictionary cannot target a constant field',x=>x.value_dictionaries.win_probability=[null],/disjoint/);
  reject('duplicate dictionary values are rejected',x=>x.value_dictionaries.provider.push(x.value_dictionaries.provider[0]),/duplicate values/);
  reject('empty dictionary is rejected',x=>x.value_dictionaries.provider=[],/dictionary count/);
  reject('out-of-range dictionary index is rejected',x=>x.record_values[0][x.record_columns.indexOf('provider')]=1000,/dictionary index/);
  reject('fractional dictionary index is rejected',x=>x.record_values[0][x.record_columns.indexOf('provider')]=.5,/dictionary index/);
  reject('string dictionary index is not coerced',x=>x.record_values[0][x.record_columns.indexOf('provider')]='0',/dictionary index/);
  reject('negative dictionary index is rejected',x=>x.record_values[0][x.record_columns.indexOf('provider')]=-1,/dictionary index/);
  reject('row width cannot truncate a missing field',x=>x.record_values[0].pop(),/row width/);
  reject('row count cannot hide a source ID',x=>x.records_included--,/row counts/);
  reject('constant winner probability must remain null',x=>x.constant_fields.win_probability=.7,/cannot contain a forecast/);
  reject('duplicate decoded event identity is rejected',x=>x.record_values[1]=clone(x.record_values[0]),/Duplicate/);
  reject('provenance owner must match metadata',x=>x.provenance.owner_run_id='OTHER_OWNER',/provenance/);
  reject('provenance source must match metadata',x=>x.provenance.owner_source_sha256='f'.repeat(64),/provenance/);
  reject('provenance report pin cannot differ',x=>x.provenance.report_reference.bytes++,/provenance/);
  reject('provenance index pin cannot differ',x=>x.provenance.provider_game_index_reference.sha256='e'.repeat(64),/provenance/);
  reject('undeclared provenance field is rejected',x=>x.provenance.new_owner_fit_credit=1,/provenance/);
  reject('original display physical pin remains bounded',x=>x.provenance.original_display_export_pin.bytes=26214401,/provenance/);
  reject('source logical pin remains bounded',x=>x.provenance.source_index_logical_pin.bytes=800000001,/provenance/);
  reject('decoded canonical pin retains its independent object bound',x=>x.decoded_canonical_pin.bytes=800000001,/800000000/);
  reject('nonfinite literal numeric value is rejected',x=>x.metadata.summary.elapsed_seconds=Infinity,/nonfinite/);
  reject('unbounded constant string is rejected before display',x=>x.constant_fields.publication_time_status='x'.repeat(65537),/string exceeds/);
  check('physical compact input limit remains 25 MiB',()=>assert.throws(()=>api.decodeScheduleCompact(f.value,{bytes:26214401,sha256:f.pin.sha256}),/25 MiB/));
  check('token-by-token decoded budget stops without a giant string',()=>assert.throws(()=>api.scheduleJsonBudget({long:'x'.repeat(1000)},20),/byte budget/));
  check('empty compact index preserves zero supplied records without season claim',()=>{const c=compactFixture(0);api.loadScheduleDisplay(c.value,c.pin);assert.equal(api.state().records.length,0);assert.match(get('schedule-records').textContent,/zero accepted source IDs/);});
  const baseline={schema:'INVENTED_BASELINE',records:[{event_id:'invented-baseline',prediction_win:.5}],metrics:[{n:1,accuracy:.5}]};api.setBaseline(baseline);const baselineBefore=JSON.stringify(api.baseline());api.loadScheduleDisplay(f.value,f.pin);
  check('compact display preserves baseline forecasts metrics and identity overlay',()=>assert.equal(JSON.stringify(api.baseline()),baselineBefore));
  check('rejected compact replacement preserves prior valid schedule and baseline',()=>{const previous=api.state(),c=clone(f.value);c.provenance.owner_run_id='OTHER';assert.throws(()=>api.loadScheduleDisplay(c,f.pin),/provenance/);assert.equal(api.state(),previous);assert.equal(JSON.stringify(api.baseline()),baselineBefore);});
  const file={size:f.body.length,arrayBuffer:async()=>Uint8Array.from(f.body).buffer};get('schedule-file').files=[file];await get('schedule-file').events.change();
  check('actual file-input listener computes physical compact SHA and loads decoded rows',()=>{assert.equal(api.pin().sha256,f.pin.sha256);assert.equal(api.pin().bytes,f.body.length);assert.equal(api.state().records.length,27);assert.equal(api.state().projection.encoding,'COLUMN_DICTIONARIES_AND_CONSTANTS_V1');});
  console.log(JSON.stringify({status:'PASS',kind:'invented_compact_schedule_contract_not_owner_execution',checks:tests.length,tests,template_sha256:sha(html),browser_observation:'NOT_PERFORMED_BY_THIS_FUNCTION_TEST'}));
}
if(require.main===module)run().catch(error=>{console.error(error);process.exitCode=1;});
