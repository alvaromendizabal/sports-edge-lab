"""Public saved-output contracts: no fitting, rescoring, or provider requests."""
from pathlib import Path
import base64
import csv
import datetime
import gzip
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'docs/fbs'
DATA = json.loads(gzip.decompress((DOCS / 'latest-games-v063.json.gz').read_bytes()))


class LatestGamesV063Tests(unittest.TestCase):
    def test_denominator_and_identity(self):
        self.assertEqual(len(DATA['games']), 888)
        self.assertEqual(len({g['game_id'] for g in DATA['games']}), 888)
        self.assertTrue(all(g['season'] == 2026 for g in DATA['games']))

    def test_schedule_partition(self):
        self.assertEqual(sum(g['completed'] for g in DATA['games']), 688)
        self.assertEqual(sum(g['schedule_status'] == 'CURRENT_ORIGIN_REFRESH_DUE' for g in DATA['games']),145)
        self.assertEqual(sum(g['kickoff_utc'] is None for g in DATA['games']),55)
        self.assertEqual(sum(not g['completed'] and g['kickoff_utc'] is not None and
            g['schedule_status'] != 'CURRENT_ORIGIN_REFRESH_DUE' for g in DATA['games']),0)

    def test_layer_coverage_and_missingness(self):
        counts = {name: sum(g['layers'][name]['values']['p_home'] is not None for g in DATA['games'])
                  for name in DATA['layer_definitions']}
        self.assertEqual(counts, {'original':122,'retained_v061':148,'calibrated':122,'mixture_global':114,'mixture_gated':114,'replay':790})
        for g in DATA['games']:
            for layer in g['layers'].values():
                self.assertIsNone(layer['values']['exact_line_cover'])
                self.assertFalse(layer['new_issue_created_by_export'])

    def test_saved_issues_precede_target_kickoff(self):
        def timestamp(x): return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
        for g in DATA['games']:
            for name, layer in g['layers'].items():
                if name == 'replay' or layer['values']['p_home'] is None: continue
                self.assertLess(timestamp(layer['information_cutoff_utc']),timestamp(g['kickoff_utc']))
                self.assertLess(timestamp(layer['original_durable_observed_at']),timestamp(g['kickoff_utc']))
                self.assertEqual(layer['horizon'],'CURRENT_ORIGIN_OUTLOOK')
                self.assertFalse(layer['production_champion'])

    def test_replay_is_never_issued(self):
        for g in DATA['games']:
            replay = g['layers']['replay']
            self.assertFalse(replay['forecast_issued'])
            self.assertFalse(replay['historical_availability_proved'])
            self.assertIsNone(replay['information_cutoff_utc'])

    def test_failed_refresh_does_not_take_credit_for_retained_archive(self):
        future=[g for g in DATA['games'] if g['schedule_status']=='CURRENT_ORIGIN_REFRESH_DUE']
        self.assertEqual(len(future),145)
        self.assertEqual(sum(g['layers']['original']['values']['p_home'] is not None for g in future),119)
        self.assertTrue(all(g['layers']['retained_v061']['values']['p_home'] is not None for g in future))
        for g in future:
            refresh=g['current_owner_baseline_refresh']
            self.assertTrue(refresh['attempted'])
            self.assertEqual(refresh['reason_code'],'EXACT_REGISTERED_POOL_HAS_NO_EXISTING_STATE_NO_REFIT')
            self.assertEqual((refresh['new_issues'],refresh['reused_current_context_issues']),(0,0))
            self.assertTrue(refresh['earlier_archive_is_not_a_current_refresh'])
            self.assertFalse(g['layers']['retained_v061']['new_or_reused_issue_in_V062'])

    def test_archived_issues_and_older_selections_are_not_silently_replaced(self):
        missing=[g for g in DATA['games'] if g['archive_continuity']['prior_original_absent_from_current_ledger']]
        older=[g for g in DATA['games'] if g['archive_continuity']['current_ledger_selects_older_original_issue']]
        self.assertEqual((len(missing),len(older)),(26,14))
        self.assertEqual(len({g['game_id'] for g in missing+older}),40)
        for g in missing:
            self.assertIsNone(g['layers']['original']['values']['p_home'])
            self.assertIsNotNone(g['layers']['retained_v061']['values']['p_home'])
        for g in older:
            self.assertLess(g['layers']['original']['original_durable_observed_at'],
                g['layers']['retained_v061']['original_durable_observed_at'])
        for g in missing+older:
            self.assertEqual(g['schedule_status'],'CURRENT_ORIGIN_REFRESH_DUE')
            self.assertFalse(g['archive_continuity']['original_values_overwritten'])
            self.assertTrue(g['archive_continuity']['current_and_archived_fixture_identity_equal'])

    def test_no_invented_champion(self):
        self.assertEqual(DATA['champion_status']['authorized_metric_champions'],0)
        self.assertEqual(DATA['summary']['new_champion_forecasts'],0)
        self.assertTrue(DATA['summary']['metric_champion_phase_reached'])
        self.assertEqual(DATA['champion_status']['gap_count'],580)
        self.assertIsNone(DATA['summary']['new_genuine_forecasts_root_scope'])
        self.assertEqual(DATA['summary']['new_baseline_forecasts'],0)
        self.assertTrue(all(g['metric_champion_forecast'] is None for g in DATA['games']))
        self.assertTrue(all(r['selected_model'] is None for r in DATA['champion_status']['roles']))

    def test_every_provider_target_resolves_with_identity(self):
        names={'DraftKings','Kalshi','Polymarket Global','Polymarket US'}
        for g in DATA['games']:
            self.assertEqual(set(g['provider_reference_ids']),names)
            for provider, targets in g['provider_reference_ids'].items():
                self.assertEqual(set(targets),{'winner','margin','total','cover_probability'})
                for target,index in targets.items():
                    record=DATA['provider_evidence'][index]
                    self.assertEqual((record['provider'],record['target']),(provider,target))
                    self.assertIn('quote_at',record); self.assertIn('acquired_at',record)
                    self.assertFalse(record['reference_is_model_expected_score'])

    def test_probability_and_point_rounding(self):
        for g in DATA['games']:
            for layer in g['layers'].values():
                for key,value in layer['values'].items():
                    if value is None or isinstance(value,dict): continue
                    places=4 if key in ('p_home','exact_line_cover') else 1
                    self.assertEqual(value,round(value,places))
                    if key=='p_home': self.assertTrue(0<=value<=1)

    def test_csv_complete_six_layer_denominator(self):
        with (DOCS/'latest-games-v063.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),5328)
        self.assertEqual(len({(r['game_id'],r['layer']) for r in rows}),5328)
        self.assertEqual({r['game_id'] for r in rows},{g['game_id'] for g in DATA['games']})

    def test_browser_payload_exactly_matches_download(self):
        js=(DOCS/'latest-games-v063-data.js').read_text()
        encoded=re.fullmatch(r'window.FBS_LATEST_V063_GZIP="([A-Za-z0-9+/=]+)";\n',js).group(1)
        self.assertEqual(base64.b64decode(encoded),(DOCS/'latest-games-v063.json.gz').read_bytes())

    def test_public_boundary_no_private_cloud_or_recipe_keys(self):
        raw=json.dumps(DATA)
        for forbidden in ('s3://','/home/sagemaker-user','arn:aws:','recipe_policy_sha256',
                          'model_snapshot_sha256','candidate_id','raw_response','api_key','source_rows'):
            self.assertNotIn(forbidden,raw)

    def test_leaders_keep_support_and_exposed_status(self):
        self.assertEqual(len(DATA['historical_cohort_leaders']),49)
        for row in DATA['historical_cohort_leaders']:
            self.assertGreater(row['games'],0)
            self.assertEqual(len(row['cohort_sha256']),64)
            self.assertEqual(row['selection_status'],'EXPOSED_DESCRIPTIVE_COHORT_LEADER_NOT_PROMOTED')

    def test_recovered_narrow_cohort_remains_separate_and_unpromoted(self):
        r=DATA['previously_omitted_231_game_record']
        self.assertEqual(r['games'],231)
        self.assertEqual(r['best_saved_log_loss'],0.416199)
        self.assertEqual(r['best_loss_model_correct'],188)
        self.assertEqual(r['best_accuracy_model_correct'],191)
        self.assertEqual(r['complete_book_correct'],185)
        self.assertEqual(r['draftkings_correct'],186)
        self.assertTrue(r['full_precision_machine_evidence_authenticated'])
        self.assertFalse(r['promotion'])
        self.assertFalse(r['selection_permitted'])
        self.assertTrue(r['not_full_season'])
        self.assertTrue(r['not_same_as_301_game_panel'])
        self.assertTrue(r['not_kalshi_only'])
        self.assertEqual(DATA['current_low_logloss_evidence']['games'],301)

    def test_page_has_download_and_clock_fallback(self):
        text=(DOCS/'latest-games-v063.html').read_text()
        self.assertIn('<noscript>',text)
        self.assertIn('latest-games-v063.csv',text)
        self.assertIn('latest-games-v063.json.gz',text)
        self.assertIn('07:24:15',text)
        self.assertNotIn('https://cdn.',text)

    def test_actual_new_science_does_not_replace_stronger_restored_controls(self):
        r=DATA['new_research']
        self.assertEqual((r['new_frozen_base_fits'],r['new_frozen_scalar_outputs'],r['new_target_candidate_cards']),(36,33336,19))
        self.assertEqual(r['failed_fit_attempts'],0)
        self.assertFalse(r['new_candidates_were_promoted'])
        self.assertEqual(len(r['new_vs_restored_metric_rows']),14)
        for row in r['new_vs_restored_metric_rows']:
            self.assertEqual(row['games'],{2024:917,2025:933}[row['season']])
            if row['metric']=='accuracy':self.assertLess(row['best_new_value'],row['restored_selected_control'])
            else:self.assertGreater(row['best_new_value'],row['restored_selected_control'])
        self.assertEqual(sum(x['comparison_cells'] for x in r['matched_restored_control_tallies']),84)
        self.assertTrue(all(x['better']==x['tied']==0 and x['worse']==x['comparison_cells'] for x in r['matched_restored_control_tallies']))

    def test_latest_saved_monitor_retains_full_missingness_and_no_selection(self):
        m=DATA['native_latest_label_monitor']
        self.assertEqual((m['preserved_arms_evaluated'],m['new_saved_probability_metric_evaluations']),(250,250))
        self.assertEqual((m['games'],m['completed_games_outside_saved_bank'],m['pending_or_not_final_games']),(301,387,200))
        self.assertEqual(m['games']+m['completed_games_outside_saved_bank'],m['completed_season_games'])
        self.assertEqual(m['new_inference_rows'],0)
        self.assertEqual(m['new_model_fits'],0)
        self.assertFalse(m['selection_allowed']);self.assertFalse(m['promotion_authorized'])
        self.assertTrue(m['all_250_primary_metric_sets_unchanged_from_V061'])
        self.assertEqual(m['distinct_preserved_probability_vectors'],212)
        self.assertFalse(m['market_is_kalshi']);self.assertFalse(m['cohort_extended_beyond_original_panel'])
        self.assertEqual({x['correct'] for x in m['selected_descriptive_rows']},{234,235,237,238})

    def test_new_contexts_are_not_new_games_or_contiguous_cursor_credit(self):
        s=DATA['summary']
        self.assertEqual(s['newly_covered_baseline_games'],0)
        self.assertEqual(s['new_contexts_for_previously_covered_games'],0)
        self.assertEqual((s['new_contiguous_cases'],s['new_sparse_priority_cases'],s['reused_sparse_cases']),(12,24,36))
        self.assertEqual(s['frozen_case_cursor'],151)
        self.assertEqual(s['new_frozen_case_count'],36)
        self.assertTrue(s['priority_work_is_not_contiguous_cursor_credit'])


if __name__=='__main__': unittest.main()
