/* Independent saved-evidence display oracle. No fitting, inference or rescoring. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
function evidence(){return JSON.parse(fs.readFileSync(path.join(__dirname,'b078_recovered_b077_evidence.json')));}
function verify(htmlBytes){const r=evidence();assert.equal(r.schema,'sports-edge-lab.nba.recovered-b077-review.v1');
 const match=htmlBytes.toString('utf8').match(/<script id="b077-evidence" type="application\/json">([\s\S]*?)<\/script>/);
 assert.ok(match,'Saved aggregate evidence must be embedded for offline reopen');assert.deepEqual(JSON.parse(match[1]),r);
 assert.equal(r.metric_rows.length,248);assert.equal(r.provider_comparisons.length,24);
 assert.equal(r.publication_has_new_scoring,false);assert.equal(r.distinct_original_issue_monitor_games,6);
 assert.ok(r.metric_rows.every(x=>x.promotion_allowed===false));
 return {metric_rows:r.metric_rows.length,provider_rows:r.provider_comparisons.length};}
function filt(rows,options){return rows.filter(r=>Object.entries(options).every(([k,v])=>v==='all'||String(r[k])===String(v)));}
async function validatePage(page,name,exhaustive=false){const r=evidence();
 assert.equal(await page.locator('#b077-title').isVisible(),true);
 assert.deepEqual(await page.locator('#b077-evidence').evaluate(e=>JSON.parse(e.textContent)),r);
 const controls={season:'b077-season',evidence_track:'b077-track',target:'b077-target',phase:'b077-phase',horizon_minutes:'b077-horizon'};
 const base={season:'2026-27',evidence_track:'all',target:'winner',phase:'regular',horizon_minutes:'all'};
 const score=(v,m)=>typeof v!=='number'?'Unavailable':m==='accuracy'?(v*100).toFixed(2)+'%':v.toFixed(6);
 async function metricCheck(options){for(const [field,id] of Object.entries(controls))await page.selectOption('#'+id,String(options[field]));
   const expected=filt(r.metric_rows,options),actual=await page.locator('#b077-metrics tbody tr').evaluateAll(rows=>rows.map(row=>({section:row.dataset.source,index:row.dataset.sourceIndex,cells:[...row.cells].map(c=>c.textContent.trim())})));
   assert.equal(actual.length,expected.length,name+' filtered metric row count');
   for(let i=0;i<expected.length;i++){const e=expected[i],a=actual[i];assert.equal(a.section,e.source_section);assert.equal(a.index,String(e.source_index??e.source_role));
     assert.equal(a.cells[3],e.scored_games+' / '+e.completed_game_denominator);
     assert.deepEqual(a.cells.slice(4,9),['accuracy','log_loss','brier','mae','rmse'].map(k=>score(e.metrics[k],k)),name+' saved scores');}
   assert.equal(await page.locator('#b077-metric-empty').isHidden(),expected.length>0);
 }
 await metricCheck(base);
 if(exhaustive){for(const season of ['2024-25','2025-26','2026-27'])for(const target of ['winner','margin','total'])await metricCheck({...base,season,target,evidence_track:'all',phase:'all'});
  for(const track of new Set(r.metric_rows.map(x=>x.evidence_track)))await metricCheck({...base,season:'all',phase:'all',target:'all',evidence_track:track});
  await metricCheck({...base,season:'2024-25',evidence_track:'CURRENT_FIXED_STATE_REPLAY'});
  await metricCheck({season:'all',evidence_track:'all',target:'all',phase:'all',horizon_minutes:'all'});
  const downloadPromise=page.waitForEvent('download');await page.click('#b077-export');const download=await downloadPromise;
  assert.equal(download.suggestedFilename(),'nba-b077-saved-metrics.csv');
  const stream=await download.createReadStream(),chunks=[];for await(const chunk of stream)chunks.push(chunk);
  const csv=Buffer.concat(chunks).toString('utf8');
  function parseCSV(text){const rows=[];let row=[],cell='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];
   if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}
   else if(c===','&&!quoted){row.push(cell);cell='';}
   else if(c==='\r'&&!quoted&&text[i+1]==='\n'){row.push(cell);rows.push(row);row=[];cell='';i++;}
   else cell+=c;}assert.equal(quoted,false);row.push(cell);rows.push(row);return rows;}
  const exported=parseCSV(csv),headers=['season','evidence_track','role_alias','family','target','horizon_minutes','scored_games','completed_game_denominator','accuracy','log_loss','brier','mae','rmse','status'];
  assert.deepEqual(exported[0],headers);assert.equal(exported.length,r.metric_rows.length+1);
  for(let i=0;i<r.metric_rows.length;i++){const source=r.metric_rows[i];assert.deepEqual(exported[i+1],headers.map(k=>String((Object.hasOwn(source.metrics,k)?source.metrics[k]:source[k])??'')),name+' export row '+i);}
 }
 await metricCheck(base);
 const vbase={season:'2026-27',provider:'all',horizon_minutes:'all',issue_horizon_class:'all'};
 const vc={season:'b077-venue-season',provider:'b077-provider',horizon_minutes:'b077-venue-horizon',issue_horizon_class:'b077-venue-timing'};
 async function venueCheck(options){for(const [field,id]of Object.entries(vc))await page.selectOption('#'+id,String(options[field]));
  const expected=filt(r.provider_comparisons,options),actual=await page.locator('#b077-venues tbody tr').evaluateAll(rows=>rows.map(row=>({index:Number(row.dataset.sourceIndex),cells:[...row.cells].map(c=>c.textContent.trim())})));
  assert.equal(actual.length,expected.length);for(let i=0;i<expected.length;i++){const e=expected[i],a=actual[i];assert.equal(a.index,e.source_index);assert.equal(a.cells[3],e.model_on_same_reference_games.games+' / '+e.full_universe_games);assert.deepEqual(a.cells.slice(4,7),['accuracy','log_loss','brier'].map(m=>score(e.model_on_same_reference_games[m],m)+' / '+score(e.raw_bbo_midpoint_reference[m],m)));}
  assert.equal(await page.locator('#b077-venue-empty').isHidden(),expected.some(x=>x.model_on_same_reference_games.games>0));
 }
 await venueCheck(vbase);
 if(exhaustive){for(const provider of ['DRAFTKINGS','KALSHI','POLYMARKET_US','POLYMARKET_INTERNATIONAL'])await venueCheck({...vbase,provider});
  for(const season of ['2024-25','2025-26'])await venueCheck({...vbase,season});
  for(const timing of ['EARLY_OUTLOOK','NOMINAL','LATE'])await venueCheck({...vbase,issue_horizon_class:timing});
  await venueCheck({...vbase,horizon_minutes:'120'});
 }
 await venueCheck(vbase);
 return {status:'PASS',name,metric_rows:r.metric_rows.length,provider_rows:r.provider_comparisons.length};
}
module.exports={verify,validatePage};
