/* Independent saved aggregate and actual-control oracle. No fitting or scoring. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const load=name=>JSON.parse(fs.readFileSync(path.join(__dirname,name)));
const words=x=>String(x??'Unavailable').replaceAll('_',' ');
const score=(x,m)=>typeof x!=='number'?'Unavailable':m==='accuracy'?(100*x).toFixed(2)+'%':x.toFixed(6);
function verify(html){const m=load('latest_model_review.json'),p=load('latest_research_outputs.json');
 const embedded=html.toString().match(/<script id="nba-owner-review-data" type="application\/json">([\s\S]*?)<\/script>/);
 assert.ok(embedded);assert.deepEqual(JSON.parse(embedded[1]),m);
 assert.equal(m.release,'B082');assert.equal(m.exporter_release,'B082');assert.equal(m.latest_original_issue_at_utc,p.latest_forecast_issue_at_utc);
 assert.equal(m.evidence_as_of_utc,p.evidence_as_of_utc);assert.equal(m.metric_rows.length,392);assert.equal(m.historical_descriptive_peaks.length,28);
 assert.equal(m.publication_new_fits,0);assert.equal(m.publication_new_metric_scoring,0);assert.equal(m.production_promotions,0);
 assert.ok(m.metric_rows.every(row=>row.promotion_allowed===false));
 assert.ok(m.metric_rows.filter(row=>row.evidence_track!=='ORIGINAL_ISSUED_ROLLING').every(row=>row.original_issue_claim===false));
 assert.equal(m.model_pairs.length,66);assert.equal(m.venue_comparisons.length,105);assert.equal(m.venue_coverage.length,12);
 assert.equal(m.promotion_gates.registered_production.automatic_production_promotion,false);
 return {saved_metrics:m.metric_rows.length,descriptive_peaks:m.historical_descriptive_peaks.length,saved_current_pairs:66,current_venue_coverage_rows:m.venue_coverage.length,new_fits:0,new_scores:0};
}
async function validatePage(page,name,exhaustive=false){const m=load('latest_model_review.json');
 assert.deepEqual(await page.locator('#nba-owner-review-data').evaluate(n=>JSON.parse(n.textContent)),m);
 assert.equal(await page.locator('#nba-owner-review-title').isVisible(),true);
 const base={season:'all',track:'all',target:'all'};
 async function check(options){for(const key of Object.keys(base))await page.selectOption('#nba-owner-'+key,options[key]);
  const expected=m.metric_rows.filter(r=>(options.season==='all'||r.season===options.season)&&(options.track==='all'||r.evidence_track===options.track)&&(options.target==='all'||r.target===options.target));
  const actual=await page.locator('#nba-owner-metrics tbody tr').evaluateAll(rows=>rows.map(row=>[...row.cells].map(c=>c.textContent)));
  assert.equal(actual.length,expected.length,name+' metric filter census');
  for(let i=0;i<expected.length;i++){const r=expected[i];assert.deepEqual(actual[i],[r.season+' / '+words(r.evidence_track),words(r.role_alias)+' / '+r.family,r.target+' / '+words(r.phase)+' / T'+r.horizon_minutes,(r.scored_games??'Unavailable')+' / '+(r.completed_game_denominator??'Unavailable'),...['accuracy','log_loss','brier','mae','rmse'].map(k=>score(r.metrics[k],k)),Object.entries(r.missing_reasons||{}).map(([k,v])=>words(k)+': '+v).join('; ')+(r.state_origin?' / '+words(r.state_origin):'')],name+' saved metric exact display '+i);}
 }
 await check(base);
 if(exhaustive){for(const season of ['2024-25','2025-26','2026-27'])for(const target of ['winner','margin','total'])await check({...base,season,target});for(const track of new Set(m.metric_rows.map(r=>r.evidence_track)))await check({...base,track});await check({...base,season:'2024-25',track:'ORIGINAL_ISSUED_ROLLING'});}
 await check(base);
 const peaks=await page.locator('#nba-owner-peaks tbody tr').evaluateAll(rows=>rows.map(row=>[...row.cells].map(c=>c.textContent)));
 assert.equal(peaks.length,m.historical_descriptive_peaks.length);
 for(let i=0;i<peaks.length;i++){const r=m.historical_descriptive_peaks[i];assert.deepEqual(peaks[i],[r.season+' / T'+r.horizon_minutes,r.target+' / '+words(r.metric),r.families.join('; '),score(r.saved_metric_value,r.metric),r.games+' / '+r.tied_saved_rows]);}
 const venues=await page.locator('#nba-owner-coverage tbody tr').evaluateAll(rows=>rows.map(row=>[...row.cells].map(c=>c.textContent)));
 assert.deepEqual(venues,m.venue_coverage.map(r=>[r.season,words(r.provider),String(r.maximum_matched_games_in_one_saved_view),words(r.status)]));
 assert.equal(await page.locator('#nba-owner-pairs tbody tr').count(),m.model_pairs.length);assert.equal(await page.locator('#nba-owner-venues tbody tr').count(),m.venue_comparisons.length);
 assert.deepEqual(await page.locator('#nba-owner-review-data').evaluate(n=>JSON.parse(n.textContent)),m);
 return {status:'PASS',name,saved_metric_rows:m.metric_rows.length};
}
module.exports={verify,validatePage};
