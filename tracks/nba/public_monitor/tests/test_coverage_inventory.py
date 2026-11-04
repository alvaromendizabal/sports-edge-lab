"""Invented failures that distinguish calendar coverage from price eligibility."""
from copy import deepcopy
import unittest

from tracks.nba.public_monitor import coverage_inventory as coverage
from tracks.nba.public_monitor.history_panels import invented_quote


class CalendarFirst(unittest.TestCase):
    def test_missing_forecast_and_market_do_not_remove_a_game(self):
        games=[coverage.invented_event(),coverage.invented_event(event="invented-game-02")]
        board=coverage.build_board(games,[invented_quote()])
        self.assertEqual(len(board["games"]),2)
        self.assertEqual(board["games"][1]["references"],[])
        self.assertEqual({r["inventory_games"] for r in board["coverage"]},{2})

    def test_forecast_flag_never_changes_quote_or_coverage(self):
        a=coverage.build_board([coverage.invented_event(has_saved_forecast=False)],[invented_quote()])
        b=coverage.build_board([coverage.invented_event(has_saved_forecast=True)],[invented_quote()])
        self.assertEqual(a["coverage"],b["coverage"])
        self.assertEqual(a["games"][0]["references"],b["games"][0]["references"])

    def test_late_recovery_is_a_reference_without_original_possession(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote()])
        row=next(r for r in board["coverage"] if r["provider"]=="kalshi" and r["quote_policy"]=="T60")
        self.assertEqual((row["historical_reference_games"],row["original_possession_games"]),(1,0))

    def test_latest_quote_is_not_backfilled_into_t60(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote(quoted_at="2035-11-01T19:59:00Z")])
        counts={r["quote_policy"]:r["observed_reference_games"] for r in board["coverage"] if r["provider"]=="kalshi"}
        self.assertEqual(counts,{"LATEST_BEFORE_TIP":1,"T60":0,"T120":0})

    def test_several_contract_methods_do_not_inflate_game_count(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote(),invented_quote(method="last_trade")])
        row=next(r for r in board["coverage"] if r["provider"]=="kalshi" and r["quote_policy"]=="T60")
        self.assertEqual((row["observed_reference_games"],row["selected_contract_records"]),(1,2))

    def test_polymarket_products_are_never_merged(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote(provider="polymarket_us")])
        rows={r["provider"]:r for r in board["coverage"] if r["quote_policy"]=="T60"}
        self.assertEqual(rows["polymarket_us"]["observed_reference_games"],1)
        self.assertEqual(rows["polymarket_international"]["observed_reference_games"],0)

    def test_sampled_window_exhaustion_is_not_all_ticks(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote(tick_window_exhausted=True,sampling_resolution_seconds=60)])
        self.assertEqual({r["all_ticks_latest_proven_games"] for r in board["coverage"]},{0})

    def test_absent_game_is_retained_after_calendar_refresh(self):
        prior=[coverage.invented_event(),coverage.invented_event(event="invented-game-02")]
        current=[coverage.invented_event(schedule_observed_at="2035-11-01T12:00:00Z")]
        result,_=coverage.reconcile_schedule(prior,current)
        self.assertEqual(len(result),2)

    def test_schedule_refresh_does_not_erase_prior_saved_forecast_availability(self):
        result,_=coverage.reconcile_schedule([coverage.invented_event(has_saved_forecast=True)],
            [coverage.invented_event(has_saved_forecast=False,schedule_observed_at="2035-11-01T12:00:00Z")])
        self.assertTrue(result[0]["has_saved_forecast"])

    def test_reschedule_keeps_original_clocks_and_quarantines_old_tip_match(self):
        old=coverage.invented_event(); quote=invented_quote();before=deepcopy((old,quote))
        fresh=coverage.invented_event(tip_at="2035-11-02T20:00:00Z",schedule_observed_at="2035-11-01T12:00:00Z")
        games,changes=coverage.reconcile_schedule([old],[fresh]);board=coverage.build_board(games,[quote])
        self.assertEqual((old,quote),before)
        self.assertEqual(len(changes),1)
        self.assertEqual(len(board["games"]),1)
        self.assertEqual(board["unjoined"][0]["reason"],"TIP_CLOCK_CHANGED_REQUIRES_REQUALIFICATION")
        self.assertEqual(board["games"][0]["references"],[])

    def test_changed_ordered_teams_and_same_clock_conflict_reject(self):
        with self.assertRaisesRegex(ValueError,"ordered sides"):
            coverage.reconcile_schedule([coverage.invented_event()],[coverage.invented_event(home="Gold",away="Blue")])
        with self.assertRaisesRegex(ValueError,"same-clock"):
            coverage.reconcile_schedule([coverage.invented_event()],[coverage.invented_event(tip_at="2035-11-02T20:00:00Z")])

    def test_final_status_does_not_change_regular_phase(self):
        game=coverage.build_board([coverage.invented_event(status="final",phase="regular")],[])["games"][0]
        self.assertEqual(game["phase"],"regular")

    def test_successful_empty_day_is_not_a_failed_day(self):
        observed=dict(data_kind="INVENTED",date="2035-11-01",status="OBSERVED",reported_games=0)
        failed=dict(data_kind="INVENTED",date="2035-11-02",status="SOURCE_FAILED",reported_games=None)
        census=coverage.date_census(["2035-11-01","2035-11-02","2035-11-03"],[observed,failed])
        self.assertEqual(census["observed_dates"],1)
        self.assertFalse(census["complete_requested_date_census"])
        self.assertEqual(census["dates"][2]["status"],"NOT_OBSERVED")
        with self.assertRaisesRegex(ValueError,"failed date cannot claim zero"):
            coverage.date_census(["2035-11-02"],[dict(failed,reported_games=0)])

    def test_complete_requested_dates_do_not_prove_full_season(self):
        census=coverage.date_census(["2035-11-01"],[dict(data_kind="INVENTED",date="2035-11-01",status="OBSERVED",reported_games=0)])
        self.assertTrue(census["complete_requested_date_census"])
        self.assertFalse(census["complete_season_proven"])

    def test_pacific_monday_boundary_uses_local_date(self):
        self.assertEqual(coverage.pacific_week("2035-11-05T07:30:00Z"),"2035-10-29")
        self.assertEqual(coverage.pacific_week("2035-11-05T09:00:00Z"),"2035-11-05")

    def test_empty_census_does_not_prove_completion(self):
        self.assertFalse(coverage.date_census([],[])["complete_requested_date_census"])

    def test_unjoined_reference_retained_and_no_source_fit_or_financial_credit(self):
        board=coverage.build_board([coverage.invented_event()],[invented_quote(event="invented-outside")])
        self.assertEqual(len(board["unjoined"]),1)
        for field in ("provider_requests","new_fits","new_forecasts","new_orders","allocation"):self.assertEqual(board[field],0)
        self.assertIsNone(board["profit"]);self.assertIsNone(board["roi"])


if __name__=="__main__":unittest.main()
