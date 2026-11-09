#!/usr/bin/env python3
"""Deterministic contract tests for published Circa retrospective model lenses."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class CircaReportContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((ROOT / "evidence.json").read_text())
        cls.comp = cls.data["model_comparison"]
        cls.profiles = {p["model"]: p for p in cls.comp["profiles"]}
        cls.by_game = {g["game_id"]: g for g in cls.data["games"]}

    def test_official_games_and_week9_provenance(self) -> None:
        games = self.data["games"]
        self.assertEqual(len(games), 136)
        self.assertEqual(len({g["game_id"] for g in games}), 136)
        self.assertEqual(sorted(set(g["week"] for g in games)), list(range(1, 10)))
        self.assertEqual(sum(g["week"] <= 8 for g in games), 121)
        self.assertEqual(sum(g["week"] == 9 for g in games), 15)
        for g in games:
            self.assertEqual(g["line_home"], -g["line_away"])
            if g["week"] <= 8:
                self.assertEqual(g["model_lane"], "RETROSPECTIVE")
                self.assertIsNone(g["model_issue_utc"])
            elif g["model_lane"] == "ORIGINAL_PRE_KICKOFF":
                self.assertGreater(g["model_issue_utc"], "2026-11-08T00:00:00")
                self.assertLess(g["model_issue_utc"], g["kickoff_utc"])

    def test_common_retrospective_family_cohort(self) -> None:
        self.assertEqual(len(self.profiles), 23)
        self.assertEqual(set(self.profiles), set(self.comp["game_predictions"]))
        observed = None
        for model, rows in self.comp["game_predictions"].items():
            ids = set(rows)
            self.assertEqual(len(ids), 120, model)
            self.assertTrue(all(self.by_game[k]["week"] <= 8 for k in ids))
            if observed is None:
                observed = ids
            else:
                self.assertEqual(ids, observed, model)
            for game_id, r in rows.items():
                game = self.by_game[game_id]
                self.assertAlmostEqual(r["margin"]+game["line_home"], r["edge"])
                expected = ("PUSH" if game["actual_ats_cover"] == "PUSH" else
                            "WIN" if r["pick"] == game["actual_ats_cover"] else "LOSS")
                self.assertEqual(r["grade"], expected)
                self.assertAlmostEqual(r["margin_error"], abs(r["margin"]-game["final"]["home_margin"]))

    def test_five_picks_each_week_without_duplication(self) -> None:
        for model, rows in self.comp["game_predictions"].items():
            profile = self.profiles[model]
            total_points = 0
            for week in range(1, 9):
                card = [(key, r) for key, r in rows.items()
                        if self.by_game[key]["week"] == week and r["top_rank"] is not None]
                self.assertEqual(len(card), 5, (model, week))
                self.assertEqual({r["top_rank"] for _, r in card}, set(range(1, 6)))
                counts = Counter(r["grade"] for _, r in card)
                stats = profile["weekly"][str(week)]
                self.assertEqual((stats["top_five_w"], stats["top_five_l"], stats["top_five_p"]),
                                 (counts["WIN"], counts["LOSS"], counts["PUSH"]))
                total_points += counts["WIN"]+counts["PUSH"]*0.5
            self.assertAlmostEqual(profile["top_five_points"], total_points)
            self.assertEqual(profile["top_five_picks"], 40)

    def test_two_independent_rankings_and_ties(self) -> None:
        a = self.comp["by_ats"]
        c = self.comp["by_card"]
        self.assertEqual(set(a), set(c))
        self.assertEqual(a[:2], ["tensorflow_mlp::football_support_control",
                                  "torch_mlp::football_support_control"])
        tf = self.profiles[a[0]]
        self.assertEqual((tf["ats_win"], tf["ats_loss"], tf["ats_push"]), (67,47,6))
        self.assertEqual(tf["top_five_points"], 19.0)
        self.assertEqual(sum(self.profiles[m]["card_rank"] == 1 for m in c), 4)
        self.assertEqual({self.profiles[m]["top_five_points"] for m in c[:4]}, {23.0})
        self.assertEqual(self.profiles[a[2]]["ats_rank"], 3)
        self.assertGreater(sum(self.profiles[m]["ats_rank"] == 3 for m in a), 1)

    def test_baseline_preserved_and_original_week9_not_overwritten(self) -> None:
        champion = self.data["selected_models"]["margin"]
        self.assertEqual(champion, "catboost::football_support_control")
        for game_id, r in self.comp["game_predictions"][champion].items():
            game = self.by_game[game_id]
            self.assertAlmostEqual(game["projected_margin"], r["margin"])
            self.assertEqual(game["ats_grade"], r["grade"])
            self.assertEqual(game["top_five_rank"], r["top_rank"])
        self.assertTrue(all(g["week"]<=8 for rows in self.comp["game_predictions"].values() for g in
                            (self.by_game[k] for k in rows)))
        self.assertEqual(self.data["audit"]["original_week9_timed_issues"], 14)

    def test_official_leaderboard_benchmark_is_conditional(self) -> None:
        lb = self.data["leaderboard_benchmark"]
        self.assertEqual(lb["week"], 8)
        self.assertEqual(lb["rank_at_23_points"], 1054)
        self.assertTrue(lb["rank_tied"])
        self.assertEqual(lb["leader_points"], 30.5)
        self.assertIn("no Circa entry", lb["qualifier"])
        self.assertEqual(lb["entries_reported"], 5790)

    def test_build_receipt_matches_html_and_readme(self) -> None:
        receipt = json.loads((ROOT / "build_receipt.json").read_text())
        html = (ROOT / "index.html").read_bytes()
        readme = (ROOT / "README.md").read_text()
        self.assertEqual(receipt["html_sha256"], hashlib.sha256(html).hexdigest())
        self.assertEqual(receipt["html_bytes"], len(html))
        self.assertIn("id=\"model-choice\"", html.decode())
        self.assertIn("all 23 available margin configurations", html.decode())
        self.assertIn("# 2026 NFL models vs. Circa Million VIII", readme)
        self.assertIn("### Ranking A · five-pick Circa-style points", readme)
        self.assertIn("### Ranking B · every-game ATS accuracy", readme)
        self.assertIn("Four of the 23 archived margin-model configurations", readme)
        self.assertIn("**Week 9 uses actual original N056 issues", readme)
        self.assertIn("activeModel=FAMILIES.by_card[0]", html.decode())
        self.assertIn("Four models tied at", html.decode())


if __name__ == "__main__":
    unittest.main()
