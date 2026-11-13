/* Independent saved-cohort source binding and real-control oracle. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const read=n=>fs.readFileSync(path.join(__dirname,n)),load=n=>JSON.parse(read(n)),words=x=>String(x??'Unavailable').replaceAll('_',' ');
function verify(html){const value=load('current_saved_cohort_leaders.json'),model=load('latest_model_review.json'),rows=new Map(model.metric_rows.map(r=>[r.row_id,r]));
 const embedded=html.toString().match(/<script id="nba-cohort-data" type="application\/json">([\s\S]*?)<\/script>/);assert.ok(embedded);assert.deepEqual(JSON.parse(embedded[1]),value);
 assert.equal(crypto.createHash('sha256').update(read('latest_model_review.json')).digest('hex'),value.source_public_file_pin.sha256);
 assert.equal(value.rows.length,40);assert.equal(new Set(value.rows.map(r=>r.cohort_alias)).size,16);assert.equal(value.entire_current_season_best_claim,false);assert.equal(value.production_promotions,0);assert.equal(value.new_metric_scoring,0);
 let bindings=0;for(const row of value.rows){assert.equal(row.scored_games+row.missing_games,row.completed_game_denominator);assert.equal(row.selection_or_promotion_allowed,false);assert.equal(row.original_issue_claim,false);for(const ref of row.source_rows){const source=rows.get(ref.row_id);assert.ok(source);assert.equal(source.metrics[row.metric],row.saved_metric_value);for(const[k,v]of Object.entries(ref))assert.deepEqual(source[k],v);bindings++;}}
 assert.equal(bindings,71);return{saved_leaders:40,distinct_exact_cohorts:16,saved_source_bindings:bindings,new_scores:0};
}
async function validatePage(page,name,exhaustive=false){const value=load('current_saved_cohort_leaders.json');assert.deepEqual(await page.locator('#nba-cohort-data').evaluate(n=>JSON.parse(n.textContent)),value);
 const base={target:'all',horizon:'all',metric:'all',evidence_track:'all'};
 async function check(options){for(const key of Object.keys(base))await page.selectOption('#nba-cohort-'+key,options[key]);const expected=value.rows.filter(r=>(options.target==='all'||r.target===options.target)&&(options.evidence_track==='all'||r.evidence_track===options.evidence_track)&&(options.metric==='all'||r.metric===options.metric)&&(options.horizon==='all'||r.horizon_minutes===Number(options.horizon)));
 const actual=await page.locator('#nba-cohort-leaders tbody tr').evaluateAll(rows=>rows.map(row=>({cohort:row.dataset.cohort,metric:row.dataset.metric,cells:[...row.cells].map(c=>c.textContent)})));
 assert.equal(actual.length,expected.length,name+' saved leader filter count');for(let i=0;i<expected.length;i++){const r=expected[i];assert.equal(actual[i].cohort,r.cohort_alias);assert.equal(actual[i].metric,r.metric);assert.deepEqual(actual[i].cells,[r.cohort_alias+' / '+words(r.evidence_track),r.target+' / '+words(r.phase)+' / T'+r.horizon_minutes,words(r.metric),r.families.join('; ')+' / '+r.source_rows.map(x=>words(x.role_alias)).join('; '),r.metric==='accuracy'?(100*r.saved_metric_value).toFixed(2)+'%':r.saved_metric_value.toFixed(6),r.scored_games+' / '+r.completed_game_denominator+' / '+r.missing_games,r.distinct_saved_recipes+' / '+r.eligible_saved_role_views]);}}
 await check(base);if(exhaustive){for(const target of ['winner','margin','total'])for(const horizon of ['60','120'])await check({...base,target,horizon});for(const evidence_track of ['CURRENT_FIXED_STATE_REPLAY','NEW_SEASON_FROZEN_REFRESH'])await check({...base,evidence_track});for(const metric of ['accuracy','log_loss','brier','mae','rmse'])await check({...base,metric});await check({...base,target:'total',metric:'accuracy'});}await check(base);
 assert.match(await page.locator('#nba-current-cohorts').textContent(),/no full-season best-model claim/);return{status:'PASS',name,leaders:40,cohorts:16};
}
module.exports={verify,validatePage};
