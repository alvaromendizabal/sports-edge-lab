'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  function sameIdentity(game, row) {
    return !!row && String(game.id) === String(row.id) && game.season === row.season &&
      String(game.home_id) === String(row.home_id) && String(game.away_id) === String(row.away_id) &&
      game.kickoff_exact === row.kickoff_exact && game.kickoff === row.kickoff &&
      game.reported_kickoff === row.reported_kickoff;
  }
  function indexRows(rows) {
    const index = new Map();
    for (const row of rows) {
      if (index.has(row.id)) throw new Error('Duplicate latest-capture official identity');
      index.set(row.id, row);
    }
    return index;
  }
  function resultView(game, row, snapshot, originalClock) {
    const resolved = snapshot === 'latest' && !!row && row.identity_status === 'TBD_RESOLUTION_NEW_FIXTURE_EPOCH' &&
      String(game.id) === String(row.id) && game.season === row.season &&
      String(game.home_id) === String(row.home_id) && String(game.away_id) === String(row.away_id) &&
      game.kickoff_exact === false && game.kickoff === null && row.kickoff_exact === true &&
      typeof row.kickoff === 'string' && Number.isFinite(Date.parse(row.kickoff));
    if (resolved) {
      const next={...game,kickoff:row.kickoff,reported_kickoff:row.reported_kickoff,kickoff_exact:true,
        models:{},replay_p_home:null,replay_margin:null,replay_total:null,replay_winner:null,
        projection_status:'NEW_FIXTURE_EPOCH_PREDICTION_PENDING',schedule_join:'NEW_FIXTURE_EPOCH_PENDING',
        new_fixture_epoch:true,prior_kickoff_status:'Unresolved exact kickoff',
        owner_original_identity_status:row.owner_original_identity_status||null};
      return {...resultView(next,row,'latest',originalClock),latest_identity_status:'TBD resolution · new fixture epoch; new prediction pending'};
    }
    const out = {...game, result_snapshot: 'original', result_observed_at: originalClock,
      newly_observed_final: false, latest_identity_status: sameIdentity(game, row) ? 'Exact unchanged identity' : 'Current capture identity not admitted'};
    if (!['latest','nov7_night','nov7_evening','nov7_late','prior'].includes(snapshot) || !sameIdentity(game, row)) return out;
    if (row.completed && (!finite(row.home_score) || !finite(row.away_score) ||
        row.home_score < 0 || row.away_score < 0)) return out;
    // The overlay changes observed outcomes only. Forecasts, cutoff, kickoff and
    // the prior model/provider join remain the immutable original projection.
    const completed = row.completed === true;
    return {...out, result_snapshot: snapshot, result_observed_at: row.observed_at,
      completed, home_score: completed ? row.home_score : null, away_score: completed ? row.away_score : null,
      home_margin: completed ? row.home_score - row.away_score : null,
      total_points: completed ? row.home_score + row.away_score : null,
      winner: completed ? row.home_score === row.away_score ? 'Tie' : row.home_score > row.away_score ? game.home : game.away : null,
      newly_observed_final: completed && (typeof row.newly_observed === 'boolean' ? row.newly_observed : !game.completed)};
  }
  const api = {sameIdentity, indexRows, resultView};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.FBSCurrentCapture = api;
})();
