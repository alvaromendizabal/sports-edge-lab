"""Public report contracts: full populations, typed missingness and safe exports."""
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(os.environ.get('FBS_REVIEW_ROOT', Path(__file__).resolve().parents[3]))
PUBLIC = Path(os.environ.get('FBS_PUBLIC_DIR', ROOT/'docs/fbs'))

class FrontierReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transport=json.loads((PUBLIC/'frontier-games.json').read_text())
        cls.rows=[dict(zip(cls.transport['columns'],r)) for r in cls.transport['rows']]

    def test_complete_unique_observed_population(self):
        self.assertEqual(len(self.rows),888)
        self.assertEqual(len({r['game_id'] for r in self.rows}),888)
        self.assertEqual(sum(r['completed'] for r in self.rows),627)
        self.assertEqual(sum(r['replay_p_home'] is not None for r in self.rows),622)

    def test_no_issuance_or_stake_is_invented(self):
        self.assertTrue(all(r['genuine_original_issue_at'] is None for r in self.rows))
        self.assertTrue(all(r['stake_usd']==0 and r['decision']=='NO BET' for r in self.rows))
        self.assertTrue(all(r['spread_cover_probability'] is None for r in self.rows))

    def test_two_source_revisions_preserved(self):
        revisions=self.transport['schedule_revisions']
        self.assertEqual({r['game_id'] for r in revisions},{'401866461','401862840'})
        by={r['game_id']:r for r in self.rows}
        for revision in revisions:
            r=by[revision['game_id']]
            self.assertEqual(r['previous_schedule_kickoff_utc'],revision['old_kickoff'])
            self.assertEqual(r['kickoff_utc'],revision['new_kickoff'])

    def test_midpoints_do_not_replace_point_bounds(self):
        seen=0
        for row in self.rows:
            for provider in ('Kalshi','Polymarket US','Polymarket Global'):
                for target in ('margin','total'):
                    text=row.get(f'{provider}_{target}_point_support')
                    if text:
                        point=json.loads(text)
                        if point.get('method')=='CAPTURED_BID_ASK_HALF_PROBABILITY_SUPPORT':
                            self.assertIsNone(row[f'{provider}_{target}_value'])
                            seen+=1
        self.assertGreater(seen,0)

    def test_latest_owner_and_local_work_remain_distinct(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        owner=review['owner']; local=review['new_local_source_review']
        self.assertEqual((owner['release'],owner['exit']),('V035',2))
        self.assertEqual((owner['provider_requests'],owner['model_fits'],owner['forecast_issues']),(0,0,0))
        self.assertEqual(owner['first_error_stage'],'QUEUED_PREDECESSOR_HANDOFF')
        self.assertIn('V034',owner['first_error'])
        self.assertIn('allowlist',owner['first_error'])
        self.assertEqual(owner['resource_phase_decision'],'NOT_REACHED')
        self.assertFalse(owner['owner_admission_attempted'])
        self.assertFalse(owner['collector_started'])
        self.assertFalse(owner['full_research_admitted'])
        self.assertFalse(owner['memory_s3_acquisition_admitted'])
        self.assertFalse(owner['writer_lock_held_during_finalization'])
        self.assertTrue(owner['queue_singleton_held_during_finalization'])
        self.assertEqual(owner['exit_evidence'],'RUNTIME_DECLARED_DIAGNOSTIC_STATUS')
        self.assertIsNone(owner['interpreter_exit_status'])
        self.assertFalse(owner['interpreter_exit_independently_observed'])
        self.assertFalse(review['prepared_successor_execution_observed'])
        self.assertFalse(review['next_handoff']['owner_execution_observed'])
        self.assertEqual((owner['return_bytes'],owner['source_bytes']),(84837823,84730490))
        self.assertEqual(local['new_predictive_fits'],0)
        self.assertFalse(local['prior_study_refitted'])
        self.assertEqual(local['prior_predictive_fits_preserved'],33)

    def test_prior_resource_failure_is_not_reassigned_to_latest_owner(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        prior=review['prior_owner']
        self.assertEqual(prior['release'],'V034')
        self.assertEqual(prior['research_disk_reserve_bytes']+prior['work_headroom_bytes']-prior['final_free_disk_bytes'],prior['disk_shortfall_bytes'])
        self.assertEqual(prior['disk_shortfall_bytes'],1770766336)
        self.assertEqual(prior['admission_attempts'],60)
        self.assertNotIn('final_free_disk_bytes',review['owner'])
        self.assertEqual([(o['release'],o['provider_requests']) for o in review['earlier_owners']],[('V033',669)])

    def test_owner_audit_is_distinct_from_new_local_source_reads(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        audit=review['new_independent_verification']
        self.assertEqual(audit['execution_class'],'LOCAL_READ_ONLY_EVIDENCE_AUDIT')
        self.assertEqual((audit['new_fits'],audit['new_forecast_issues']),(0,0))
        self.assertTrue(review['new_local_source_acquisition'])
        self.assertEqual(review['owner']['provider_requests'],0)
        self.assertFalse(audit['original_evidence_recomputed_by_fitting'])
        self.assertEqual(audit['retained_current_http_receipt_body_pairs'],16)
        for prefix in ('owner_return','exact_source','retained_market_seed','retained_current_evidence'):
            self.assertEqual(audit[prefix+'_members'],audit[prefix+'_manifested_members']+1)

    def test_fresh_local_capture_preserves_unchanged_reports_and_prior_changes(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        increment=review['new_local_science'];capture=increment['fresh_availability']
        self.assertEqual(increment['attribution'],'LOCAL_INDEPENDENT_AUDIT_AND_CURRENT_SOURCE_PREPARATION_NOT_SAGEMAKER')
        self.assertEqual((capture['fresh_official_requests'],capture['original_bodies_identical_to_prior_capture']),(4,4))
        self.assertEqual((capture['new_status_changes'],capture['prior_status_changes_preserved']),(0,108))
        self.assertEqual(capture['clock_qualified_team_cutoff_rows'],116)
        self.assertLess(capture['capture_start'],capture['capture_end'])
        self.assertLess(capture['capture_end'],capture['prepared_at'])
        for name in ('new_fits','new_scalers','new_model_states','new_predictions','genuine_forecast_issues','orders','stake'):
            self.assertEqual(increment[name],0)

    def test_recorded_state_candidates_are_not_promoted_to_strict_paths(self):
        increment=json.loads((PUBLIC/'frontier-review.json').read_text())['new_local_science']
        audit=increment['game_state_audit'];counts=audit['counts']
        self.assertEqual((audit['states_audited'],audit['retained_play_rows']),(905,157120))
        self.assertEqual((audit['independently_compared_projection_fields'],audit['projection_field_mismatches']),(1256960,0))
        self.assertEqual(counts['inherited_strict_flag'],audit['inherited_strict_conservative_support_pass']+audit['inherited_strict_needs_additional_state_review'])
        self.assertEqual(counts['conservative_complete_state_support_candidate'],22)
        self.assertEqual(audit['inherited_strict_issue_games']['score_decreases'],5)
        self.assertEqual(audit['inherited_strict_issue_games']['within_period_clock_increases'],4)
        self.assertIn('not a strict market-path cohort',' '.join(increment['game_state_limits']))

    def test_unbound_slots_do_not_inflate_game_population(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        schedule=review['new_local_source_review']['schedule']
        self.assertEqual(len(schedule['slots']),10)
        self.assertEqual(len(self.rows),888)
        self.assertTrue(all(s['home_team'] is None and s['away_team'] is None and not s['join_eligible'] for s in schedule['slots']))
        self.assertEqual(schedule['calendar_interval_conflicts_count'],1)

    def test_availability_unknowns_and_clocks_are_preserved(self):
        data=json.loads((PUBLIC/'frontier-review.json').read_text())['new_local_source_review']['availability']
        self.assertEqual(sum(data['identity_states'].values()),data['public_report_rows'])
        self.assertEqual(data['players_with_observed_usage']+data['players_without_observed_usage'],data['public_report_rows'])
        self.assertEqual(data['clock_qualified_team_rows_by_horizon'],{'120':58,'60':58})
        self.assertFalse(data['estimated_player_effects_available'])
        self.assertFalse(data['historical_pregame_certification'])
        self.assertEqual(data['new_predictive_fits'],0)

    def test_javascript_filtering_and_csv_failure_cases(self):
        code=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const path=process.argv[1],api=require(path+'/frontier.js'),t=JSON.parse(fs.readFileSync(path+'/frontier-games.json'));
const rows=api.unpack(t),state={query:'',week:'all',window:'all'};
assert.equal(api.filter(rows,state,t.windows).length,888);
assert.equal(api.filter(rows,{...state,window:'previous'},t.windows).length,56);
assert.equal(api.filter(rows,{...state,window:'current'},t.windows).length,63);
assert.equal(api.filter(rows,{...state,week:'14'},t.windows).length,0);
assert.equal(api.filter(rows,{...state,query:'unobserved-team-token'},t.windows).length,0);
assert.throws(()=>api.unpack({columns:['game_id'],rows:[['x'],['x']]}),/Duplicate/);
assert.throws(()=>api.unpack({columns:['game_id'],rows:[['x','extra']]}),/width/);
assert.throws(()=>api.unpack({columns:['game_id','game_id'],rows:[]}),/Invalid/);
assert.match(api.csv([{value:'=1+1'}],['value']),/'=1\+1/);
assert.match(api.csv([{value:null}],['value']),/\r\n""\r\n$/);
"""
        result=subprocess.run(['node','-e',code,str(PUBLIC)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
