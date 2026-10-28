const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const api = require('../dashboard.js');
const root = path.resolve(__dirname, '../../..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'docs/evidence/2026-10-28-basketball-dashboard.json')));
const overlap = JSON.parse(fs.readFileSync(path.join(root, 'docs/evidence/2026-10-28-basketball-overlap.json')));
let panels = 0;
for (const league of ['nba', 'ncaam', 'ncaaw']) for (const horizon of [60, 1440]) for (const year of [2025, 2026, 2027]) for (const cohort of ['full_basketball', 'matched_MARKET']) {
  const view = api.presentation(data, {league, horizon, year, cohort});
  panels++;
  assert(view.rows.every(r => r.league === league && r.horizon_minutes === horizon && r.year === year && r.cohort === cohort));
  if (year === 2027) {
    assert.deepEqual(view.winnerRecipes, []);
    assert.deepEqual(view.rows.map(r => r.recipe), view.rows.map(r => r.recipe).sort());
  }
  if (!view.rows.length) assert.equal(view.games, null);
  else assert(view.rows.every(r => r.n === view.games));
}
assert.equal(data.frozen_champions['ncaam/T60'], 'basketball_rich_combined');
assert.equal(data.frozen_champions['ncaaw/T60'], 'basketball_rich_combined');
assert.equal(data.frozen_champions['nba/T60'], 'basketball_strength');
const historical = api.selectRows(data, {league:'nba',horizon:60,year:2026,cohort:'full_basketball'});
const market = api.selectRows(data, {league:'nba',horizon:60,year:2026,cohort:'matched_MARKET'});
assert.throws(() => api.numericalWinners([...historical, ...market], 2026), /Exact historical cohort/);
const current = api.selectRows(data, {league:'nba',horizon:60,year:2027,cohort:'full_basketball'});
const apparentWinner = current.map(r => ({...r,log_loss:r.recipe === 'Elo' ? 0 : r.log_loss}));
assert.deepEqual(api.numericalWinners(apparentWinner, 2027), []);
assert(current.every(r => r.n === 52));
assert.equal(api.overlapRows(overlap, 'ncaam', 2025).length, 20);
assert(api.overlapRows(overlap, 'ncaam', 2025).every(r => r.status !== 'estimated_on_common_support'));
assert.equal(overlap.overlap_sensitivities.length, 120);
const html = fs.readFileSync(path.join(root, 'docs/basketball/index.html'), 'utf8');
assert(!/<(?:script|link)[^>]+(?:src|href)=["']https?:/i.test(html));
assert(!/\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(/.test(html));
assert(html.includes('aria-live="polite"'));
assert(html.includes('id="dashboard-evidence"'));
console.log(JSON.stringify({status:'PASS',selector_panels:panels,monitoring_games:52,overlap_specs:120,network_requests:0}));
