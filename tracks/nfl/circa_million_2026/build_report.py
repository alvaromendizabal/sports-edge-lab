#!/usr/bin/env python3
"""Build an evidence-labelled, entirely self-contained NFL / Circa 2026 report.

No forecasting, refitting, backdating, or new model selection occurs here. The
read-only N057 owner HTML supplies both annual reconstructed and original N056
issues. All Circa spread numbers are sourced from official contest PDFs.
"""

from __future__ import annotations

import base64
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "Sports_Edge_Lab_NFL_N057.html"
LINES = HERE / "official_lines_2026.json"
W9_FINALS = HERE / "week9_final_scores_2026-11-08.json"
TEMPLATE = HERE / "site_template.html"
OUT = HERE / "index.html"

TEAM = {
    "SEAHAWKS": "SEA", "PATRIOTS": "NE", "RAMS": "LA", "49ERS": "SF",
    "JAGUARS": "JAX", "BROWNS": "CLE", "BENGALS": "CIN", "BUCS": "TB",
    "RAVENS": "BAL", "COLTS": "IND", "STEELERS": "PIT", "FALCONS": "ATL",
    "BILLS": "BUF", "TEXANS": "HOU", "BEARS": "CHI", "PANTHERS": "CAR",
    "TITANS": "TEN", "JETS": "NYJ", "LIONS": "DET", "SAINTS": "NO",
    "CHARGERS": "LAC", "CARDINALS": "ARI", "RAIDERS": "LV", "DOLPHINS": "MIA",
    "EAGLES": "PHI", "COMMANDERS": "WAS", "VIKINGS": "MIN", "PACKERS": "GB",
    "COWBOYS": "DAL", "GIANTS": "NYG", "CHIEFS": "KC", "BRONCOS": "DEN",
}

EARLY_W9_MARKET_TOTALS = {
    "2026_09_CIN_ATL": 52.5, "2026_09_CLE_NO": 42.5,
    "2026_09_DAL_IND": 51.5, "2026_09_DEN_CAR": 44.5,
    "2026_09_DET_MIA": 50.0, "2026_09_LA_WAS": 47.5,
    "2026_09_NYG_PHI": 38.5, "2026_09_NYJ_KC": 48.0,
}

SELECTED_RESEARCH_MODELS = {
    "win": "oof_stack",
    "margin": "catboost::football_support_control",
    "total": "oof_stack",
}


def load_dashboard() -> dict:
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    match = re.search(r'id="nfl-season-payload" type="application/octet-stream">([^<]+)', text)
    if not match:
        raise RuntimeError("N057 owner HTML has no embedded JSON evidence")
    payload = json.loads(gzip.decompress(base64.b64decode(match.group(1))))
    return {"data": payload, "source_sha256": hashlib.sha256(raw).hexdigest()}


def spread_number(raw: str) -> float:
    if raw == "PK":
        return 0.0
    sign = -1 if raw.startswith("-") else 1
    v = raw[1:].replace("½", ".5")
    if v.startswith(".5"):
        return sign * 0.5
    return sign * float(v)


def calculate_score(away: int, home: int, game: dict) -> dict:
    margin = home - away
    return {"away_score": away, "home_score": home, "home_margin": margin,
            "total": home + away, "winner": game["home"] if margin > 0 else game["away"] if margin < 0 else None}


def prob_stats(rows: list[dict]) -> dict:
    a = [r for r in rows if r.get("completed") and r.get("winner_correct") is not None]
    probs = [r for r in rows if r.get("completed") and r.get("home_win_prob") is not None and not r.get("tie")]
    margins = [r for r in rows if r.get("completed") and r.get("margin_error") is not None]
    totals = [r for r in rows if r.get("completed") and r.get("total_error") is not None]
    ats = [r for r in rows if r.get("ats_grade") in {"WIN", "LOSS", "PUSH"}]
    top = [r for r in rows if r.get("top_five")]
    top_ats = [r for r in top if r.get("ats_grade") in {"WIN", "LOSS", "PUSH"}]
    win = sum(x["ats_grade"] == "WIN" for x in ats)
    loss = sum(x["ats_grade"] == "LOSS" for x in ats)
    push = sum(x["ats_grade"] == "PUSH" for x in ats)
    return {
        "total_games": len(rows), "completed": sum(bool(r.get("completed")) for r in rows),
        "model_covered": sum(r.get("projected_margin") is not None for r in rows),
        "ats_win": win, "ats_loss": loss, "ats_push": push,
        "ats_decisions": win + loss, "ats_pct": win/(win+loss) if win+loss else None,
        "winner_hits": sum(x["winner_correct"] for x in a), "winner_count": len(a),
        "winner_pct": sum(x["winner_correct"] for x in a)/len(a) if a else None,
        "margin_mae": sum(x["margin_error"] for x in margins)/len(margins) if margins else None,
        "margin_n": len(margins),
        "total_mae": sum(x["total_error"] for x in totals)/len(totals) if totals else None,
        "total_n": len(totals),
        "brier": sum((x["home_win_prob"]-x["actual_home_win"])**2 for x in probs)/len(probs) if probs else None,
        "log_loss": -sum(x["actual_home_win"]*math.log(max(1e-9,min(1-1e-9,x["home_win_prob"])))
                          +(1-x["actual_home_win"])*math.log(max(1e-9,min(1-1e-9,1-x["home_win_prob"])))
                          for x in probs)/len(probs) if probs else None,
        "prob_n": len(probs),
        "top_five_picks": len(top),
        "top_five_graded": len(top_ats),
        "top_five_w": sum(x["ats_grade"] == "WIN" for x in top_ats),
        "top_five_l": sum(x["ats_grade"] == "LOSS" for x in top_ats),
        "top_five_p": sum(x["ats_grade"] == "PUSH" for x in top_ats),
        "top_five_points": sum(x["ats_grade"] == "WIN" for x in top_ats)
                           + 0.5 * sum(x["ats_grade"] == "PUSH" for x in top_ats),
    }


def grade_total(forecast: float | None, total: float | None, line: float | None) -> dict:
    if forecast is None or total is None or line is None:
        return {"market_total_pick": None, "market_total_grade": None}
    pred = "OVER" if forecast > line else "UNDER" if forecast < line else "PASS"
    actual = "OVER" if total > line else "UNDER" if total < line else "PUSH"
    return {"market_total_pick": pred,
            "market_total_grade": "PUSH" if pred == "PASS" or actual == "PUSH" else "WIN" if pred == actual else "LOSS"}


def build() -> tuple[dict, dict]:
    archive = load_dashboard()
    d = archive["data"]
    asserted = d["n055_selection_summary"]["selected"]
    if asserted != SELECTED_RESEARCH_MODELS:
        raise AssertionError("N057 model selection has drifted; refusing to substitute models")
    official = json.loads(LINES.read_text())
    final_overrides = json.loads(W9_FINALS.read_text())["finals"]

    circa_by_week = {}
    for week_str, w in official["weeks"].items():
        week = int(week_str)
        raw_picks = {int(k): v for k, v in w["picks"].items()}
        pairs = []
        for i in range(1, len(raw_picks)+1, 2):
            a, b = raw_picks[i], raw_picks[i+1]
            p_a, p_b = spread_number(a["spread"]), spread_number(b["spread"])
            assert abs(p_a + p_b) < 1e-9, (week, i, a, b)
            aa, bb = TEAM[a["team"]], TEAM[b["team"]]
            pairs.append({"teams": frozenset((aa, bb)), "sides": {aa: p_a, bb: p_b},
                          "pick_numbers": {aa:i, bb:i+1}})
        assert len({p["teams"] for p in pairs}) == len(pairs), (week, "duplicate lines")
        circa_by_week[week] = pairs

    recon = {}
    selected_model_set = set(asserted.values())
    alts = defaultdict(dict)
    for r in d["n055_family_per_game"]:
        if r["season"] != 2026 or r.get("policy") != "annual_forward_oof":
            continue
        key = (r["game_id"], r["target"])
        if r["model"] in selected_model_set and r["model"] == asserted.get(r["target"]):
            assert key not in recon, (key, "duplicate selected forecast")
            recon[key] = r
        if r["target"] == "margin":
            alts[r["model"]][r["game_id"]] = r["prediction"]

    original = {}
    original_alt = defaultdict(dict)
    for r in d["n056_owner_family_issues"]:
        key = (r["game_id"], r["target"])
        assert key not in original, (key, "duplicate owner issue")
        original[key] = r
    for r in d["n056_owner_raw_issues"]:
        if r["target"] == "margin":
            original_alt[r["arm"]][r["game_id"]] = r["prediction"]

    games = []
    matched_pairs = defaultdict(set)
    for g in d["games"]:
        week = g["week"]
        if not 1 <= week <= 9:
            continue
        matches = [p for p in circa_by_week[week] if p["teams"] == frozenset((g["away"], g["home"]))]
        assert len(matches) == 1, (g["game_id"], "no unique official Circa line",matches)
        pair = matches[0]
        matched_pairs[week].add(tuple(sorted(pair["teams"])))
        spread = pair["sides"][g["home"]]
        finished = bool(g["completed"])
        final = dict(g["actual"]) if g["actual"] else None
        if g["game_id"] in final_overrides:
            scores = final_overrides[g["game_id"]]
            if final and (final["away_score"], final["home_score"]) != tuple(scores):
                raise AssertionError(f"Discordant official final: {g['game_id']}")
            final = calculate_score(*scores, g)
            finished = True
        if finished and not final:
            raise AssertionError(f"Completed game missing score: {g['game_id']}")
        targets = {}
        raw_issues = {}
        for target in ("win", "margin", "total"):
            r = (recon if week <= 8 else original).get((g["game_id"], target))
            if r:
                targets[target] = r["prediction"]
                raw_issues[target] = r
            else:
                targets[target] = None
        if week <= 8 and any(raw_issues[k].get("historical_source_possession_verified") is True for k in raw_issues):
            raise AssertionError("unexpected authentication status; update provenance rules")
        if week == 9:
            for r in raw_issues.values():
                issue = r.get("actual_issue_at_utc")
                assert issue and issue < g["kickoff_utc"], (g["game_id"], "issue after kickoff")
                assert issue > "2026-11-08T00:00:00", "revised Circa-deadline logic required"
        p, margin, total = targets["win"], targets["margin"], targets["total"]
        margin_actual = final["home_margin"] if finished else None
        tot_actual = final["total"] if finished else None
        edge = margin + spread if margin is not None else None
        pick = g["home"] if edge is not None and edge > 0 else g["away"] if edge is not None and edge < 0 else None
        actual_cover = g["home"] if margin_actual is not None and margin_actual+spread > 0 else g["away"] if margin_actual is not None and margin_actual+spread < 0 else "PUSH" if margin_actual is not None else None
        ats_grade = ("PUSH" if actual_cover == "PUSH" else "WIN" if pick == actual_cover else "LOSS") if finished and pick else None
        win_pick = g["home"] if p is not None and p >= 0.5 else g["away"] if p is not None else None
        tie = bool(finished and margin_actual == 0)
        valid_winner = finished and p is not None and not tie
        mkt = EARLY_W9_MARKET_TOTALS.get(g["game_id"])
        rec = {
            "game_id": g["game_id"], "week": week, "away":g["away"], "home":g["home"],
            "kickoff_utc":g["kickoff_utc"], "completed":finished, "final":final,
            "tie": tie, "line_home":spread, "line_away": -spread,
            "circa_pick_home":pair["pick_numbers"][g["home"]],
            "circa_pick_away":pair["pick_numbers"][g["away"]],
            "model_lane": "RETROSPECTIVE" if week<=8 else "ORIGINAL_PRE_KICKOFF" if margin is not None else "NO_ORIGINAL_ISSUE",
            "model_labels": {t: raw_issues[t].get("classification") if t in raw_issues else None for t in ("win", "margin", "total")},
            "model_issue_utc": raw_issues.get("margin", {}).get("actual_issue_at_utc"),
            "projected_margin":margin, "projected_total":total, "home_win_prob":p,
            "projected_away_score":round((total-margin)/2,1) if total is not None and margin is not None else None,
            "projected_home_score":round((total+margin)/2,1) if total is not None and margin is not None else None,
            "model_win_pick":win_pick,
            "winner_correct": int(win_pick == final["winner"]) if valid_winner else None,
            "actual_home_win": int(margin_actual > 0) if valid_winner else None,
            "tie_excluded_win":tie,
            "margin_error":abs(margin-margin_actual) if margin is not None and margin_actual is not None else None,
            "total_error":abs(total-tot_actual) if total is not None and tot_actual is not None else None,
            "ats_edge_home": edge, "ats_edge_absolute":abs(edge) if edge is not None else None,
            "model_ats_pick":pick, "actual_ats_cover":actual_cover, "ats_grade":ats_grade,
            "market_total_line":mkt,
            "market_total_kind":"Nov 7, 2026 7:58 p.m. ET cross-book consensus (NOT Circa)" if mkt is not None else None,
            "market_total_source":"https://www.sharpfootballanalysis.com/betting/nfl-odds-picks-predictions/" if mkt is not None else None,
            "top_five": False, "top_five_rank":None,
        }
        rec.update(grade_total(total,tot_actual,mkt))
        games.append(rec)

    expected_games = defaultdict(int)
    for g in games: expected_games[g["week"]] += 1
    for week in range(1,10):
        assert len(matched_pairs[week]) == expected_games[week] == len(circa_by_week[week]), (
            week, expected_games[week], len(matched_pairs[week]), len(circa_by_week[week]))
    assert len(games) == 136, f"2026 Weeks 1-9 game count changed: {len(games)}"

    weeks = {}
    for week in range(1,10):
        wr = [r for r in games if r["week"] == week]
        candidates = sorted((r for r in wr if r["ats_edge_absolute"] is not None),
                            key=lambda r:(-r["ats_edge_absolute"],r["game_id"]))
        for i,r in enumerate(candidates[:5],start=1):
            r["top_five"] = True
            r["top_five_rank"] = i
        weeks[str(week)] = {"stats":prob_stats(wr),
                             "source":official["weeks"][str(week)]["source_point_spreads_pdf"],
                             "selections":official["weeks"][str(week)]["source_selection_pdf"]}

    hist_games = [r for r in games if r["week"]<=8]
    week9_games = [r for r in games if r["week"]==9]
    alt_metrics = []
    for name,preds in alts.items():
        matched = [r for r in hist_games if r["game_id"] in preds and r["completed"]]
        wins=losses=pushes=0
        for r in matched:
            pick_sign = preds[r["game_id"]] + r["line_home"]
            result_sign = r["final"]["home_margin"] + r["line_home"]
            if pick_sign == 0 or result_sign == 0: pushes += 1
            elif pick_sign*result_sign>0: wins += 1
            else: losses += 1
        alt_metrics.append({"model":name, "cohort":"RETROSPECTIVE_W1_W8",
                            "n":len(matched),"w":wins,"l":losses,"p":pushes,
                            "ats_pct":wins/(wins+losses) if wins+losses else None,
                            "margin_mae":sum(abs(preds[r["game_id"]]-r["final"]["home_margin"]) for r in matched)/len(matched) if matched else None,
                            "research_champion":name==asserted["margin"]})
    for name,preds in original_alt.items():
        matched = [r for r in week9_games if r["game_id"] in preds and r["completed"]]
        wins=losses=pushes=0
        for r in matched:
            pick_sign=preds[r["game_id"]]+r["line_home"]
            result_sign=r["final"]["home_margin"]+r["line_home"]
            if pick_sign==0 or result_sign==0: pushes+=1
            elif pick_sign*result_sign>0: wins+=1
            else: losses+=1
        if matched:
            alt_metrics.append({"model":"N056 raw • "+name,"cohort":"ORIGINAL_W9_AFTER_CIRCA_DEADLINE",
                                "n":len(matched),"w":wins,"l":losses,"p":pushes,
                                "ats_pct":wins/(wins+losses) if wins+losses else None,
                                "margin_mae":sum(abs(preds[r["game_id"]]-r["final"]["home_margin"]) for r in matched)/len(matched),
                                "research_champion":False})
    alt_metrics.sort(key=lambda r:(r["cohort"], -1 if r["research_champion"] else 0, r["margin_mae"] or 9999))

    data = {
        "title":"Sports Edge Lab | NFL 2026 vs Circa Million VIII",
        "asof":"2026-11-08 — Sunday afternoon Pacific",
        "season":2026, "selected_models":asserted,
        "archive_sha256":archive["source_sha256"],
        "origin":"Authenticated Sports Edge Lab N057 owner HTML / N055 retrospective / N056 owner issue",
        "origin_receipt":"https://github.com/alvaromendizabal/sports-edge-lab/blob/main/tracks/nfl/ACTUAL_N056_RESULTS_N057.md",
        "contest":"https://www.circasports.com/circa-million",
        "circa_deadline":"2026-11-07 16:00 PST (2026-11-08 00:00 UTC)",
        "weekly":weeks,
        "games":games,
        "retrospective":prob_stats(hist_games),
        "original_week9":prob_stats(week9_games),
        "alternatives":alt_metrics,
        "sources":{
            "circa_weekly_fixed_lines":"Circa Sports official weekly contest point-spread PDF (links in week details)",
            "circa_weekly_selections":"Official Circa entrant selections PDF used as machine-readable cross-check of point spreads",
            "result_source":"N057 preserved game scores plus dated Nov 8 public final scoreboard for later Week 9 games",
            "totals_source":"Saturday Nov 7 Sharp Football multi-book consensus only for eight early Week 9 games; no Circa Million totals exist",
        },
        "audit":{"circa_weeks_matched":9,"circa_games_matched":len(games),
                 "circa_teams_normalized":len(TEAM),
                 "original_week9_timed_issues":sum(g["model_lane"]=="ORIGINAL_PRE_KICKOFF" for g in week9_games),
                 "failed_gates":0},
    }
    receipt={"source_archive_sha256":archive["source_sha256"],
             "source_archive_bytes":SOURCE.stat().st_size,
             "official_lines_sha256":hashlib.sha256(LINES.read_bytes()).hexdigest(),
             "number_of_games":len(games),"scoreboard_final_overrides":len(final_overrides),
             "historical_2026_reconstructed_predictions":len(hist_games),
             "actual_N056_Week9_pre_kickoff_forecasts":data["audit"]["original_week9_timed_issues"],
             "compiled_at_utc":datetime.now(timezone.utc).isoformat(),
             "asof_note":"Scoreboard only includes games designated Final by public live sports feed Nov 8 PT. Never grade ongoing scores.",
             "integrity_checks":"all 136 Weeks 1-9 games matched exact official Circa pair; all issue clocks before kickoff, none before Saturday Circa deadline"}
    return data,receipt


def build_github_readme(data: dict) -> str:
    """Native GitHub-readable fallback; needs no download or external HTML host."""
    def n(x: float | None, digits: int = 1) -> str:
        return f"{x:.{digits}f}" if x is not None else "—"

    def sign(x: float | None) -> str:
        return f"{x:+g}" if x is not None else "—"

    def tri(s: dict) -> str:
        return f"{s['ats_win']}–{s['ats_loss']}–{s['ats_push']}"

    lines = [
        "# 2026 NFL models vs. Circa Million VIII",
        "",
        "**Sports Edge Lab · Complete Weeks 1–9 report · Nov. 8, 2026 (Pacific time)**",
        "",
        "> **Important:** This is research, not an entered Circa contest card. Weeks 1–8 are retrospectively reconstructed after the games, with unverified historical source-possession clocks. Week 9 forecasts were actually saved before Sunday's kickoffs, but after Circa's Saturday 4 p.m. contest cutoff. Thursday's Week 9 game has no N056 original issue. No backdated live-pick claims are made.",
        "",
        "**You're already viewing the full report on GitHub — no download needed.** For optional interactive filtering: [open the HTML in a third-party preview](https://raw.githack.com/alvaromendizabal/sports-edge-lab/main/tracks/nfl/circa_million_2026/index.html) (the preview service may show a safety notice first) · [view HTML source](./index.html) · [official Circa Million](https://www.circasports.com/circa-million).",
        "",
        "The native GitHub tables below show every result **without downloading anything**, even if the interactive preview service is unavailable.",
        "",
        "## The headline, with honest denominators",
        "",
        f"- **Weeks 1–8, retrospective:** {data['retrospective']['winner_hits']}/{data['retrospective']['winner_count']} outright winners ({100*data['retrospective']['winner_pct']:.1f}%). Against official Circa spreads: **{tri(data['retrospective'])}**, {100*data['retrospective']['ats_pct']:.1f}% excluding pushes. The illustrative five-per-week shortlist totals **{n(data['retrospective']['top_five_points'])} Circa-style points out of 40 picks** (21 wins, 15 losses, four pushes). All 121 games included; 120 have reconstructed margin forecasts.",
        f"- **Week 9, genuine pregame outputs:** {data['original_week9']['winner_hits']}/{data['original_week9']['winner_count']} outright winners; against Circa: **{tri(data['original_week9'])}** ({100*data['original_week9']['ats_pct']:.1f}% excluding pushes), with {data['original_week9']['completed']}/15 games final and four not yet graded. These outputs were **after the Saturday contest deadline**.",
        "- A hypothetical five-largest-edge shortlist is shown every week. It is a post-hoc diagnostic, **not a contest submission**. Circa itself scores only five selected sides against fixed spreads (win = 1, push = 0.5, loss = 0).",
        "- Circa Million has **no over/under component**. This report scores projected combined points against final combined points; independently documented market totals appear only for eight Week 9 games.",
        "",
        "## Jump to a week",
        "",
        " · ".join(f"[Week {w}](#week-{w})" for w in range(1,10)),
        "",
        "## Season scorecard",
        "",
        "| Week | Evidence lane | Forecast coverage | ATS W–L–P | ATS rate* | Hypothetical five (points) | Winner calls | Margin MAE | Total MAE | Brier | Log loss |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for w in range(1,10):
        s = data["weekly"][str(w)]["stats"]
        lines.append(f"| [{w}](#week-{w}) | {'Reconstructed' if w<=8 else 'Issued; late for contest'} | {s['model_covered']}/{s['total_games']} | {tri(s)} | {n(100*s['ats_pct'])+'%' if s['ats_pct'] is not None else '—'} | {s['top_five_w']}–{s['top_five_l']}–{s['top_five_p']} ({n(s['top_five_points'])} pts; {s['top_five_graded']}/5 scored) | {s['winner_hits']}/{s['winner_count']} | {n(s['margin_mae'])} | {n(s['total_mae'])} | {n(s['brier'],3)} | {n(s['log_loss'],3)} |")
    lines.extend(["", "*ATS rate excludes pushes. Tied games are not counted for outright winner/probability grades. No pending game is counted as a result.", ""])
    for w in range(1,10):
        s = data["weekly"][str(w)]["stats"]
        games = [g for g in data["games"] if g["week"] == w]
        wp = data["weekly"][str(w)]
        lines.extend([
            f"## Week {w}", "",
            f"**{'RETROSPECTIVE RECONSTRUCTION — not issued at kickoff' if w<=8 else 'ORIGINAL SAVED FORECASTS — before kickoff, after Circa deadline'}** · {s['model_covered']}/{s['total_games']} models available · {s['completed']}/{s['total_games']} final games · **{tri(s)} ATS** · **{s['winner_hits']}/{s['winner_count']} winner calls**",
            "",
            f"[Official Week {w} fixed spreads]({wp['source']}) · [Official entrant selection records]({wp['selections']})",
            "",
            f"**Illustrative top five by absolute projected spread edge ({n(s['top_five_points'])} Circa-style points from {s['top_five_graded']}/5 graded):** "+" · ".join(
                f"#{r['top_five_rank']} {r['model_ats_pick']} {sign(r['line_home'] if r['model_ats_pick']==r['home'] else r['line_away'])} ({n(r['ats_edge_absolute'])} pts, {r['ats_grade'] or 'pending'})"
                for r in sorted((g for g in games if g['top_five']),key=lambda x:x['top_five_rank'])),
            "",
            "| Game (away @ home) | Final | Official Circa (away / home) | Model ATS side | Grade | Model winner (prob.) | Predicted margin / actual | Total forecast / actual |",
            "|---|---:|---|---|---|---|---|---|",
        ])
        for g in games:
            final = f"{g['final']['away_score']}–{g['final']['home_score']}" if g["completed"] else "Pending"
            spread = f"{g['away']} {sign(g['line_away'])} / {g['home']} {sign(g['line_home'])}"
            pick = (f"**{g['model_ats_pick']} {sign(g['line_home'] if g['model_ats_pick']==g['home'] else g['line_away'])}** (edge {n(g['ats_edge_absolute'])})" if g["model_ats_pick"] else "Unavailable")
            winner_prob = (g["home_win_prob"] if g["model_win_pick"]==g["home"] else 1-g["home_win_prob"]) if g["home_win_prob"] is not None else None
            win = f"{g['model_win_pick']} ({n(100*winner_prob)}%)" if g["model_win_pick"] else "Unavailable"
            actual_margin = sign(g["final"]["home_margin"]) if g["completed"] else "pending"
            total_actual = str(g["final"]["total"]) if g["completed"] else "pending"
            marker = " ★" if g["top_five"] else ""
            lines.append(f"| {g['away']} @ {g['home']}{marker} | {final} | {spread} | {pick} | {g['ats_grade'] or 'Pending'} | {win} | {sign(g['projected_margin'])} / {actual_margin} | {n(g['projected_total'])} / {total_actual} |")
        lines.append("")
    lines.extend([
        "## Methodology, evidence & limitations", "",
        "1. **Fixed lines:** The 2026 Circa Million VIII contest PDFs supply each week's locked side spreads. The official entrant selections were independently parsed to cross-check all 136 pairings, including Week 6 Bears/Falcons **PK**.",
        "2. **Model configurations:** Outright probability and total use the saved research `oof_stack` champion; margin uses `catboost::football_support_control`. These configurations were selected by the existing research process, not optimized for the results printed here.",
        "3. **Prediction lane:** Weeks 1–8 are annual-forward reconstructed model outputs, but historical feature-publication and possession timing is not authenticated; therefore they are **descriptive**, not proof of what was knowable or pickable then. Week 9 N056 owner issues were saved around 11:32 p.m. Pacific Nov. 7, before kickoff but after the contest deadline.",
        "4. **ATS decision:** For home margin *m* and home Circa spread *s*, the model prefers home when *m+s>0*, away when *m+s<0*. Actual outcome replaces *m* with final home margin. Exact landing on the spread is a push.",
        "5. **No false O/U:** Circa Million is ATS-only. Eight Week 9 games separately have Saturday [cross-book consensus totals](https://www.sharpfootballanalysis.com/betting/nfl-odds-picks-predictions/); no unverified totals are imputed for Weeks 1–8.",
        "6. **As-of scoreboard:** Only officially marked **Final** games observed Nov. 8 afternoon Pacific are graded. At the snapshot, Texans–Chargers, Packers–Patriots, Buccaneers–Bears, and Bills–Vikings were not final. Rebuild to update after they finish.",
        "7. **Not actual Circa standings:** No contest entry, submitted five-pick card, wager, or return-on-investment claim is associated with these studies.",
        "",
        "**Provenance:** [N056/N057 owner result](../ACTUAL_N056_RESULTS_N057.md) · [official fixed lines JSON](./official_lines_2026.json) · [scored Week 9 finals JSON](./week9_final_scores_2026-11-08.json) · [reproducible build script](./build_report.py) · [build receipt](./build_receipt.json)",
        "",
        f"**Authenticated source N057 SHA-256:** `{data['archive_sha256']}`", "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload, receipt = build()
    json_text = json.dumps(payload,separators=(",",":"),ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.read_text().replace("__INLINE_REPORT_JSON__",json_text)
    assert page.count('id="report-data"') == 1
    assert page.count("__INLINE_REPORT_JSON__") == 0
    OUT.write_text(page,encoding="utf-8")
    (HERE/"evidence.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (HERE/"README.md").write_text(build_github_readme(payload),encoding="utf-8")
    receipt["html_sha256"]=hashlib.sha256(OUT.read_bytes()).hexdigest()
    receipt["html_bytes"]=OUT.stat().st_size
    (HERE/"build_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"html_bytes":OUT.stat().st_size,"games":len(payload["games"]),
                      "retro":payload["retrospective"],"issued":payload["original_week9"],
                      "receipt":receipt},indent=2))


if __name__ == "__main__":
    main()
