'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const A=require('../../../docs/fbs/coverage.js');

test('partial point output never becomes a complete three-target forecast',()=>{
  const points={margin:0,total:0};
  assert.equal(A.completeness(points,'v040_catboost'),'partial');
  assert.equal(A.matches(points,'v040_catboost','winner','missing'),true);
  assert.equal(A.matches(points,'v040_catboost','margin','present'),true);
  assert.equal(A.matches(points,'v040_catboost','any','missing'),false);
});
test('family scope distinguishes unsupported targets from a failed expected target',()=>{
  assert.equal(A.completeness({p:0},'logistic'),'complete');
  assert.equal(A.completeness({margin:0,total:0},'linear'),'complete');
  assert.equal(A.completeness({margin:0},'ridge'),'partial');
  assert.equal(A.missingReason({kickoff_exact:true},{margin:0,total:0},'winner','linear'),'Not a target of this model family');
});
test('null, strings, infinity and invalid probabilities cannot count as outputs',()=>{
  for(const p of [null,undefined,NaN,Infinity,-.1,1.1,'0.5']) assert.equal(A.hasTarget({p},'winner'),false);
  assert.equal(A.hasTarget({p:0},'winner'),true);assert.equal(A.hasTarget({p:1},'winner'),true);
  assert.equal(A.hasTarget({margin:'0'},'margin'),false);
});
test('cover remains absent without its exact independent admission status',()=>{
  const value={p:.6,margin:4,total:50,model:{margin:{cover_probability:.8,interval80:[-20,30]}}};
  assert.equal(A.hasTarget(value,'cover'),false);
  value.model.margin.cover_status='AUTHENTICATED_EXACT_LINE_CUTOFF_QUALIFIED';
  assert.equal(A.hasTarget(value,'cover'),true);
  value.model.margin.cover_probability=2;assert.equal(A.hasTarget(value,'cover'),false);
});
test('fixture accounting is disjoint while per-target missingness retains reasons',()=>{
  const games=[{id:'a',kickoff_exact:true},{id:'b',kickoff_exact:true},{id:'c',kickoff_exact:false}];
  const values={a:{p:.5,margin:0,total:40},b:{margin:4,total:44,missing:{winner:'Saved winner state is absent'}},c:{}};
  const counts=A.reconcile(games,g=>values[g.id],'candidate','winner');
  assert.deepEqual([counts.complete,counts.partial,counts.missing,counts.target_present,counts.target_missing],[1,1,1,1,2]);
  assert.equal(counts.complete+counts.partial+counts.missing,counts.games);
  assert.deepEqual(counts.missing_reasons,[{reason:'Saved winner state is absent',games:1},{reason:'Exact kickoff unresolved',games:1}]);
});
test('the retained CatBoost three-winner gap is findable without hiding its point estimates',()=>{
  const root=path.join(__dirname,'../../../docs/fbs');
  const all=JSON.parse(fs.readFileSync(path.join(root,'three-season.json'))).rows.filter(g=>g.season===2026);
  const cat=new Map(JSON.parse(fs.readFileSync(path.join(root,'catboost-study.json'))).rows.map(g=>[g.id,g]));
  const project=g=>{const r=cat.get(g.id),m=r?.models.v040_catboost;return {p:m?.winner?.prediction,margin:m?.margin?.prediction,total:m?.total?.prediction,missing:r?.missing_targets};};
  const counts=A.reconcile(all,project,'v040_catboost','winner');
  assert.deepEqual([counts.games,counts.complete,counts.partial,counts.missing,counts.target_missing],[888,787,3,98,101]);
  assert.deepEqual(all.filter(g=>A.matches(project(g),'v040_catboost','winner','partial')).map(g=>g.id).sort(),['401856811','401858225','401858226']);
  for(const g of all.filter(g=>A.matches(project(g),'v040_catboost','winner','partial'))) assert.ok(A.hasTarget(project(g),'margin')&&A.hasTarget(project(g),'total'));
});
