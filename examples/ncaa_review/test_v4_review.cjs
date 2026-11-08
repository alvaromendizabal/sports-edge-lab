// Invented evidence tests for the public private-file inspector; no owner science.
const assert=require('node:assert/strict'),crypto=require('node:crypto'),{gzipSync}=require('node:zlib');
global.crypto=crypto.webcrypto;
const review=require('./v4_review.js');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function fixture(){
  const rows=Array.from({length:27},(_,i)=>({event_id:'invented-'+i,league:i%2?'ncaaw':'ncaam',season_end_year:2026,target:'win',evaluation_track:review.TRACKS[1],status:i===26?'SOURCE_GAP':'HISTORICAL_RECONSTRUCTION',prediction:i===26?null:.6,actual:i===26?null:1,note:i===0?'<img src=x onerror="window.bad=true">':'invented fixture'}));
  const logical=Buffer.from(rows.map(r=>JSON.stringify(r)+'\n').join('')),body=gzipSync(logical);
  const part={ordinal:0,rows:27,logical:{bytes:logical.length,sha256:sha(logical)},reference:{key:'invented/rows_part_00000.jsonl.gz',bytes:body.length,sha256:sha(body)},encoding:'gzip/canonical-json-lines'};
  const stream={schema:'sel.ncaa.b054.evidence_parts.v1',name:'invented',status:'PARTIAL_REGISTERED_STREAM',rows:27,logical_bytes:logical.length,logical_sha256:sha(logical),parts:[part],maximum_logical_part_bytes:8*1024*1024,all_parts_required_at_use:true,known_missing_parts_are_fatal:true,model_fit_credit_from_stream_rows:0};
  const value={schema:'sel.ncaa.b054.private_review.v1',project:'ncaa_basketball',release:'B054',source_sha256:'f'.repeat(64),run_id:'invented-fixture',created_at:'2026-11-08T12:00:00Z',audience:'private',status:'INVENTED_PARTIAL_FIXTURE',tracks:[...review.TRACKS],report:{status:'INVENTED_PARTIAL_FIXTURE',fit_and_prediction_counts:{new_target_fits:0,reused_target_fits:0},support:{missing_source:'INVENTED_SOURCE_GAP'}},metrics:{schema:'sel.ncaa.b054.metrics.v1',rows:[{league:'ncaam',season_end_year:2026,target:'win',selector:'invented-selector',evaluation_track:review.TRACKS[1],horizon_minutes:60,n:1,accuracy:1,log_loss:.5,brier:.16,mae:.4,rmse:.4,mean_error:-.4,ece_10_equal_width:.4}],dispositions:{INVENTED_SOURCE_GAP:1},source_only_rows_excluded_from_numeric_metrics:true,paired_gain_claim:false,no_cross_cohort_denominator_substitution:true},streams:{invented:stream},all_physical_season_games_complete:false,historical_reconstruction_is_not_as_issued:true,original_issue_mutation:false,automatic_promotion:false};
  return {value,body,logical,part,rows};
}
async function run(){const tests=[];async function check(name,f){await f();tests.push(name);}const copy=()=>JSON.parse(JSON.stringify(fixture().value));
  await check('four tracks and partial support remain separate',()=>assert.equal(review.validateV4(copy()).tracks.length,4));
  await check('empty metrics explicitly valid',()=>{const v=copy();v.metrics.rows=[];assert.equal(review.validateV4(v).metrics.rows.length,0);});
  await check('wrong sport rejected',()=>{const v=copy();v.project='nba';assert.throws(()=>review.validateV4(v),/separate V4/);});
  await check('missing or reordered evidence tracks rejected',()=>{const v=copy();v.tracks.reverse();assert.throws(()=>review.validateV4(v),/four evidence tracks/);});
  for(const [field,value] of [['automatic_promotion',true],['original_issue_mutation',true],['historical_reconstruction_is_not_as_issued',false],['all_physical_season_games_complete',true]])await check('unsupported qualification '+field,()=>{const v=copy();v[field]=value;assert.throws(()=>review.validateV4(v),/qualifications/);});
  await check('source-only reference cannot become scored model cohort',()=>{const v=copy();v.metrics.rows[0].evaluation_track=review.TRACKS[3];assert.throws(()=>review.validateV4(v),/population identity/);});
  await check('unknown evidence track cannot borrow a known one',()=>{const v=copy();v.metrics.rows[0].evaluation_track='weekly';assert.throws(()=>review.validateV4(v),/population identity/);});
  await check('population must have positive integral support',()=>{for(const n of [0,-1,1.5]){const v=copy();v.metrics.rows[0].n=n;assert.throws(()=>review.validateV4(v),/population identity/);}});
  await check('zero loss and unavailable optional metric are preserved',()=>{const v=copy();v.metrics.rows[0].log_loss=0;v.metrics.rows[0].mae=null;assert.equal(review.validateV4(v).metrics.rows[0].log_loss,0);});
  await check('probability metrics outside range rejected',()=>{const v=copy();v.metrics.rows[0].accuracy=1.1;assert.throws(()=>review.validateV4(v),/outside its range/);});
  await check('nonfinite metric rejected',()=>{const v=copy();v.metrics.rows[0].log_loss=Infinity;assert.throws(()=>review.validateV4(v),/metric value/);});
  await check('negative loss rejected',()=>{const v=copy();v.metrics.rows[0].rmse=-1;assert.throws(()=>review.validateV4(v),/nonnegative/);});
  await check('unproved comparison and source-only metric credits rejected',()=>{for(const field of ['source_only_rows_excluded_from_numeric_metrics','paired_gain_claim','no_cross_cohort_denominator_substitution']){const v=copy();v.metrics[field]=!v.metrics[field];assert.throws(()=>review.validateV4(v),/metric qualifications/);}});
  await check('stream inventory cannot claim model fits',()=>{const v=copy();v.streams.invented.model_fit_credit_from_stream_rows=1;assert.throws(()=>review.validateV4(v),/evidence stream/);});
  await check('stream row closure required',()=>{const v=copy();v.streams.invented.rows++;assert.throws(()=>review.validateV4(v),/part totals/);});
  await check('stream logical bytes closure required',()=>{const v=copy();v.streams.invented.logical_bytes++;assert.throws(()=>review.validateV4(v),/part totals/);});
  await check('part ordering cannot change',()=>{const v=copy();v.streams.invented.parts[0].ordinal=1;assert.throws(()=>review.validateV4(v),/part identity/);});
  await check('part bound cannot expand',()=>{const v=copy();v.streams.invented.parts[0].logical.bytes=9*1024*1024;assert.throws(()=>review.validateV4(v),/part identity/);});
  await check('known missing part may not become optional',()=>{const v=copy();v.streams.invented.known_missing_parts_are_fatal=false;assert.throws(()=>review.validateV4(v),/evidence stream/);});
  await check('strict JSON rejects duplicate decoded member names',()=>assert.throws(()=>review.strictJSON('{"a":1,"\\u0061":2}'),/Duplicate/));
  await check('strict JSON rejects duplicate nested keys',()=>assert.throws(()=>review.strictJSON('{"nested":{"k":0,"k":1}}'),/Duplicate/));
  await check('strict JSON preserves escaped strings and nullable numbers',()=>assert.deepEqual(review.strictJSON('{"s":"a\\\"b\\\\c","v":[null,0,-1.2e-3,true]}'),{s:'a"b\\c',v:[null,0,-.0012,true]}));
  await check('strict JSON rejects overflowing numbers',()=>assert.throws(()=>review.strictJSON('{"n":1e999}'),/Nonfinite/));
  await check('strict JSON rejects trailing content',()=>assert.throws(()=>review.strictJSON('{}{}'),/trailing/));
  await check('exact part restores every row and malicious-looking text literally',async()=>{const f=fixture(),rows=await review.decodePart(f.body,f.part);assert.equal(rows.length,27);assert.match(rows[0].note,/<img/);assert.equal(rows[26].prediction,null);});
  await check('wrong compressed hash rejects before decode',async()=>{const f=fixture();f.part.reference.sha256='0'.repeat(64);await assert.rejects(review.decodePart(f.body,f.part),/Compressed/);});
  await check('wrong logical hash rejects despite valid compression pin',async()=>{const f=fixture();f.part.logical.sha256='0'.repeat(64);await assert.rejects(review.decodePart(f.body,f.part),/logical SHA/);});
  await check('wrong logical length rejects bounded expansion',async()=>{const f=fixture();f.part.logical.bytes--;await assert.rejects(review.decodePart(f.body,f.part),/exact bound/);});
  await check('wrong part row count rejected',async()=>{const f=fixture();f.part.rows--;await assert.rejects(review.decodePart(f.body,f.part),/row inventory/);});
  await check('duplicate member in authenticated part still rejected',async()=>{const raw=Buffer.from('{"event_id":"a","event_id":"b"}\n'),body=gzipSync(raw),f=fixture();f.part={...f.part,rows:1,logical:{bytes:raw.length,sha256:sha(raw)},reference:{bytes:body.length,sha256:sha(body)}};await assert.rejects(review.decodePart(body,f.part),/Duplicate/);});
  console.log(JSON.stringify({status:'PASS',checks:tests.length,scope:'invented file and decode contracts; no owner science',tests}));
}
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={fixture};
