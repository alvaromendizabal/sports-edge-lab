// Invented expected-score records; no owner predictions or source data.
const assert=require('node:assert/strict'),crypto=require('node:crypto'),{gzipSync}=require('node:zlib');
const projection=require('./projection_review.js'),review=require('./v4_review.js');
const {fixture:refreshFixture}=require('./test_refresh_review.cjs');
const sha=body=>crypto.createHash('sha256').update(body).digest('hex');
function fixture(){
  const value=refreshFixture().value;
  const rows=projection.STATES.map((status,index)=>({
    schema:'sel.ncaa.b055.score_projection.v1',projection_id:sha('invented-projection-'+index),
    event_key:'invented-score-event-'+index,event_id:'invented-score-'+index,
    league:index===4?'ncaaw':'ncaam',season_end_year:2027,home_id:'invented-home',away_id:'invented-away',
    event_time:'2026-11-09T01:00:00Z',cutoff_time:'2026-11-09T00:00:00Z',
    prediction_origin:'2026-11-08T12:00:00Z',horizon_minutes:60,
    evaluation_track:review.TRACKS[3],forecast_scope:'INVENTED_REFERENCE_ONLY',
    model_context:status==='DERIVED_EXPECTED_SCORES'||status==='INCOHERENT_NEGATIVE_EXPECTED_SCORE'
      ?{family:'invented-family',arm:'invented-arm',training_history:{mode:'invented-history',seasons:[2001,2002]}}:null,
    status,mean_home_score:status==='DERIVED_EXPECTED_SCORES'?80.25:null,
    mean_away_score:status==='DERIVED_EXPECTED_SCORES'?70.75:null,
    expected_home_minus_away:status==='DERIVED_EXPECTED_SCORES'?9.5:status==='INCOHERENT_NEGATIVE_EXPECTED_SCORE'?100:null,
    expected_total:status==='DERIVED_EXPECTED_SCORES'?151:status==='INCOHERENT_NEGATIVE_EXPECTED_SCORE'?50:null,
    margin_prediction_id:status==='DERIVED_EXPECTED_SCORES'?sha('invented-margin'):null,
    total_prediction_id:status==='DERIVED_EXPECTED_SCORES'?sha('invented-total'):null,
    new_fit_credit:0,new_immutable_issue_credit:0,joint_distribution_qualified:false,
    integer_pmf_qualified:false,cover_push_loss_qualified:false,
    derived_mean_not_a_separate_score_model:true,original_issue_mutation:false,automatic_promotion:false,
  }));
  Object.assign(rows[4],{league:null,event_id:null,home_id:null,away_id:null,
    season_end_year:null,event_time:null,cutoff_time:null,prediction_origin:null,
    horizon_minutes:null,input_target:'margin',input_disposition:'INVENTED_MISSING_SOURCE_INPUT',
    input_record_sha256:sha('invented-blocked-input-record')});
  const logical=Buffer.from(rows.map(row=>JSON.stringify(row)+'\n').join('')),body=gzipSync(logical);
  const part={ordinal:0,rows:rows.length,logical:{bytes:logical.length,sha256:sha(logical)},
    reference:{key:'invented/score_projections.jsonl.gz',bytes:body.length,sha256:sha(body)},
    encoding:'gzip/canonical-json-lines'};
  value.streams.score_projections={schema:'sel.ncaa.b054.evidence_parts.v1',name:'score_projections',
    status:'LOCAL_FIXTURE_ONLY',rows:rows.length,logical_bytes:logical.length,logical_sha256:sha(logical),
    parts:[part],maximum_logical_part_bytes:8*1024*1024,all_parts_required_at_use:true,
    known_missing_parts_are_fatal:true,model_fit_credit_from_stream_rows:0};
  value.report.score_projection_coverage={schema:'sel.ncaa.b055.score_projection_coverage.v1',
    input_rows:7,contexts:5,status_counts:Object.fromEntries(projection.STATES.map(s=>[s,1])),
    derived_pairs:1,missing_companion_heads:1,paired_contexts:2,
    count_closure:'contexts=2*paired_contexts+missing_companion_heads',
    all_physical_season_games_complete:false,new_fits:0,new_immutable_issues:0,
    joint_distribution_qualified:false,integer_pmf_qualified:false,cover_push_loss_qualified:false};
  return {value,rows,body,part};
}
function run(){
  const checks=[],check=(name,fn)=>{fn();checks.push(name);},copy=()=>JSON.parse(JSON.stringify(fixture()));
  check('B055 preserves separate score rows and individual head contexts',()=>{
    const f=copy();assert.equal(review.validateV4(f.value).report.score_projection_coverage.contexts,5);
    assert.equal(projection.validateRows(f.rows).length,5);
  });
  check('fractional supplied means and exact target IDs remain unchanged',()=>{
    const f=copy();projection.validateRows(f.rows);assert.equal(f.rows[0].mean_home_score,80.25);
    assert.equal(f.rows[0].mean_away_score,70.75);assert.notEqual(f.rows[0].margin_prediction_id,f.rows[0].total_prediction_id);
  });
  check('structured training history is retained without conversion or selection',()=>{
    const row=copy().rows[0],before=JSON.stringify(row.model_context.training_history);
    projection.validateRows([row]);assert.equal(JSON.stringify(row.model_context.training_history),before);
    row.model_context.training_history={};assert.throws(()=>projection.validateRows([row]),/supported means/);
  });
  check('pinned non-numeric source disposition preserves unknown identity',()=>{
    const row=copy().rows[4];projection.validateRows([row]);
    assert.equal(row.league,null);assert.equal(row.event_id,null);assert.equal(row.mean_home_score,null);
    assert.equal(row.input_target,'margin');
  });
  check('minimal source disposition requires its exact source pin reason and target',()=>{
    for(const [key,value] of [['input_record_sha256','unproved'],['input_disposition',null],
      ['input_target','win'],['event_key',null]]){
      const row=copy().rows[4];row[key]=value;
      assert.throws(()=>projection.validateRows([row]),/identity|non-numeric source disposition/);
    }
  });
  check('minimal source shape cannot invent numeric or partial canonical identity',()=>{
    for(const [key,value] of [['league','ncaam'],['event_id','guessed-id'],['expected_total',0],
      ['mean_home_score',0],['status','DERIVED_EXPECTED_SCORES'],['status','MISSING_COMPANION_HEAD']]){
      const row=copy().rows[4];row[key]=value;
      assert.throws(()=>projection.validateRows([row]),/identity|non-numeric source disposition|remain null/);
    }
  });
  check('unavailable-league filter retains the pinned disposition without guessing a league',()=>{
    const f=copy(),row=f.rows[4];
    assert.equal(projection.filterRows(f.rows,{state:'all',league:'unavailable',search:'missing_source'}).length,1);
    assert.equal(projection.filterRows([row],{state:'all',league:'ncaam',search:''}).length,0);
  });
  check('non-numeric source cannot carry numeric score inputs even with complete identity',()=>{
    const row=copy().rows[4];row.league='ncaam';row.event_id='invented-complete-id';row.expected_total=1;
    assert.throws(()=>projection.validateRows([row]),/non-numeric source disposition/);
  });
  check('finite but inconsistent supplied score means reject',()=>{
    for(const key of ['mean_home_score','mean_away_score']){
      const r=copy().rows[0];r[key]=90;
      assert.throws(()=>projection.validateRows([r]),/exact retained.*arithmetic/);
    }
  });
  check('binary64 round-trip means pass without decimal tolerance',()=>{
    const r=copy().rows[0];r.expected_total=0.2;r.expected_home_minus_away=0.1;
    r.mean_home_score=0.15000000000000002;r.mean_away_score=0.05;
    projection.validateRows([r]);r.mean_home_score=0.15;
    assert.throws(()=>projection.validateRows([r]),/exact retained.*arithmetic/);
  });
  check('signed zero preserves the supplied operation result',()=>{
    const r=copy().rows[0];r.expected_total=-0;r.expected_home_minus_away=-0;
    r.mean_home_score=-0;r.mean_away_score=0;projection.validateRows([r]);
    r.mean_home_score=0;assert.throws(()=>projection.validateRows([r]),/exact retained.*arithmetic/);
  });
  check('finite inputs with arithmetic overflow cannot claim derived scores',()=>{
    const r=copy().rows[0];r.expected_total=Number.MAX_VALUE;r.expected_home_minus_away=Number.MAX_VALUE;
    r.mean_home_score=Number.MAX_VALUE;r.mean_away_score=0;
    assert.throws(()=>projection.validateRows([r]),/exact retained.*arithmetic/);
  });
  check('incoherent pair keeps original inputs but has no scores',()=>{
    const r=copy().rows[2];projection.validateRows([r]);
    assert.equal(r.expected_home_minus_away,100);assert.equal(r.expected_total,50);assert.equal(r.mean_home_score,null);
  });
  check('missing head cannot be filled with zero',()=>{
    const r=copy().rows[1];r.mean_home_score=0;
    assert.throws(()=>projection.validateRows([r]),/remain null/);
  });
  check('derived score requires both original target identities',()=>{
    const r=copy().rows[0];r.total_prediction_id=null;
    assert.throws(()=>projection.validateRows([r]),/both exact target/);
  });
  check('unsupported scientific credits reject',()=>{
    for(const [key,value] of [['new_fit_credit',1],['new_immutable_issue_credit',1],
      ['cover_push_loss_qualified',true],['integer_pmf_qualified',true],
      ['joint_distribution_qualified',true],['automatic_promotion',true]]){
      const r=copy().rows[0];r[key]=value;assert.throws(()=>projection.validateRows([r]),/scientific credit/);
    }
  });
  check('nonfinite and negative score values reject',()=>{
    for(const value of [Infinity,NaN,-1]){const r=copy().rows[0];r.mean_home_score=value;
      assert.throws(()=>projection.validateRows([r]),/supported means/);}
  });
  check('new unsupported status rejects',()=>{
    const r=copy().rows[0];r.status='PROMOTED';assert.throws(()=>projection.validateRows([r]),/identity or status/);
  });
  check('duplicate projection identity rejects within the selected part',()=>{
    const f=copy();f.rows.push(f.rows[0]);assert.throws(()=>projection.validateRows(f.rows),/Duplicate/);
  });
  check('pair counts cannot be presented as head counts',()=>{
    const f=copy();f.value.report.score_projection_coverage.contexts=2;
    assert.throws(()=>review.validateV4(f.value),/context closure/);
  });
  check('stream rows must equal all emitted dispositions',()=>{
    const f=copy();f.value.report.score_projection_coverage.status_counts.NON_NUMERIC_OR_SOURCE_ONLY++;
    assert.throws(()=>review.validateV4(f.value),/emitted rows/);
  });
  check('missing coverage does not authorize the stream',()=>{
    const f=copy();delete f.value.report.score_projection_coverage;
    assert.throws(()=>review.validateV4(f.value),/coverage manifest/);
  });
  check('projection summary cannot claim a joint PMF or new issue',()=>{
    for(const [key,value] of [['new_immutable_issues',1],['integer_pmf_qualified',true]]){
      const f=copy();f.value.report.score_projection_coverage[key]=value;
      assert.throws(()=>review.validateV4(f.value),/qualification|create a fit or issue/);
    }
  });
  check('score filters retain exact supplied identity without falling back',()=>{
    const f=copy();const rows=projection.filterRows(f.rows,{state:'DERIVED_EXPECTED_SCORES',league:'all',search:'invented-family'});
    assert.equal(rows.length,1);assert.equal(rows[0],f.rows[0]);
    assert.equal(projection.filterRows(f.rows,{state:'all',league:'all',search:'absent'}).length,0);
  });
  console.log(JSON.stringify({status:'PASS',checks:checks.length,scope:'invented matched-head display contracts; no owner science',tests:checks}));
}
if(require.main===module)run();
module.exports={fixture};
