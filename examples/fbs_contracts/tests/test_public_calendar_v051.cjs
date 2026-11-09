'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const M=require('../../../docs/fbs/research-method.js');
const B=require('../../../docs/fbs/game-center.js');
const F=require('../../../docs/fbs/forward-outlooks.js');
const status=require('../../../docs/fbs/execution-status-v051.json');
const source=require('../../../docs/fbs/observation-status-v046.json');
const report=require('../../../docs/fbs/forward-outlooks-v050.json');
const evaluation=require('../../../docs/fbs/evaluation-v049.json');

test('separate dated display calendar accounts for all latest fixtures without changing source data',()=>{
 const before=JSON.stringify(source),anchor=status.display_calendar.as_of_utc;
 const games=source.rows.map(row=>({...row,period:M.periodFor(row,anchor)}));
 const counts=Object.fromEntries(['previous','current','upcoming'].map(period=>[period,games.filter(g=>g.season===2026&&g.period===period).length]));
 assert.deepEqual(counts,{previous:63,current:53,upcoming:30});
 assert.equal(status.current_source_observed_at,'2026-11-09T03:22:14Z');
 assert.equal(M.pacificDate(anchor),'2026-11-09');
 assert.equal(JSON.stringify(source),before);
 const remaining=F.inventory(games,report);
 assert.equal(F.select(remaining).length,53);
 assert.equal(F.select(remaining,{scope:'upcoming'}).length,30);
 assert.deepEqual([remaining.length,F.summarize(remaining).issued,F.summarize(remaining).unresolved],[203,108,95]);
});

test('Monday rollover routes only the exact stored date cohort and never a same-named week',()=>{
 const windows={selected:M.weekWindows(status.display_calendar.as_of_utc),evaluated:M.weekWindows(evaluation.capture.source_observed_at)};
 assert.deepEqual(B.comparisonRoute('2026','previous','latest',windows),{study:'v045',cohort:'current_week'});
 assert.equal(B.comparisonRoute('2026','current','latest',windows),null);
 assert.equal(B.comparisonRoute('2026','upcoming','latest',windows),null);
 assert.equal(windows.evaluated.previous.start,'2026-10-26');
 assert.equal(windows.evaluated.current.start,'2026-11-02');
 assert.equal(windows.selected.current.start,'2026-11-09');
});
