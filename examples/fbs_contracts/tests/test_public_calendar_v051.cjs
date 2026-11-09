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

test('source-dated unresolved fixtures remain visible without becoming exact-kickoff weekly forecasts',()=>{
 const windows=M.weekWindows(status.display_calendar.as_of_utc);
 for(const [period,expected] of [['previous',0],['current',14],['upcoming',40]]){
  const range=windows[period];
  const rows=source.rows.filter(row=>row.season===2026&&!row.kickoff_exact&&
   M.pacificDate(row.reported_kickoff)>=range.start&&M.pacificDate(row.reported_kickoff)<range.end_exclusive);
  assert.equal(rows.length,expected);
  assert.equal(status.display_calendar.periods[period].source_dated_unresolved_games,expected);
  for(const row of rows){
   assert.equal(M.periodFor(row,status.display_calendar.as_of_utc),'unresolved');
   assert.equal(F.coverage(row,report).original_issue_verified,false);
  }
 }
 assert.equal(status.display_calendar.periods.current.schedule_associated_games,67);
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
