"""Validate a public NFL snapshot's numerical and presentation contracts."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.assets = []
        self.games = []
        self.ranks = []
        self.weights = []
        self.images = set()
        self.future_weeks = []
        self.market_games = []
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if "data-future-week" in attrs:
            self.future_weeks.append(attrs["data-future-week"])
        if "data-market-game" in attrs:
            self.market_games.append(attrs["data-market-game"])
        if tag == "details" and "game" in classes:
            self.games.append(attrs.get("data-search"))
        if tag == "article" and "contest-game" in classes:
            self.ranks.append(attrs.get("data-rank"))
        if tag == "tr" and "data-weight" in attrs:
            self.weights.append(attrs["data-weight"])
        if tag == "a" and attrs.get("href"):
            self.links.add(attrs["href"])
            if attrs["href"].endswith(".png"):
                self.images.add(attrs["href"])
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script" and "src" in attrs:
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.assets.append(attrs.get("href", ""))


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def validate(root: Path, allow_empty=False):
    errors = []
    data = json.loads((root / "data.json").read_text())
    games = data.get("games")
    performance = data.get("performance")
    if not isinstance(games, list) or not isinstance(performance, list):
        raise ValueError("games and performance must be arrays")
    if not games and not allow_empty:
        errors.append("Publication requires a populated slate; placeholder data remains pending.")
    seen = set()
    for game in games:
        identity = game.get("id")
        if not identity or identity in seen:
            errors.append(f"Missing or duplicate game identity: {identity!r}")
        seen.add(identity)
        for field in ("win_home", "win_away", "tie_probability", "probability_home", "probability_away", "probability_tie", "margin_home", "total"):
            value = game.get(field)
            if value is not None and not number(value):
                errors.append(f"{identity}: {field} is not finite or null")
        for field in ("win_home", "win_away", "tie_probability", "probability_home", "probability_away", "probability_tie"):
            value = game.get(field)
            if number(value) and not 0 <= value <= 1:
                errors.append(f"{identity}: {field} is outside [0,1]")
        home = game.get("win_home", game.get("probability_home"))
        away = game.get("win_away", game.get("probability_away"))
        tie = game.get("tie_probability", game.get("probability_tie"))
        if all(number(v) for v in (home, away, tie)) and abs(home + away + tie - 1) > 0.003:
            errors.append(f"{identity}: home + away + tie winner probabilities do not sum to 1")
        if all(number(v) for v in (home, away)) and tie in (None, 0) and abs(home + away - 1) > 0.003:
            errors.append(f"{identity}: binary home and away winner probabilities do not sum to 1")
        if game.get("total") is not None and number(game["total"]) and game["total"] < 0:
            errors.append(f"{identity}: projected total is negative")
        try:
            issued, kickoff = instant(game.get("issued_at")), instant(game.get("kickoff_utc"))
            if issued and kickoff and issued > kickoff:
                errors.append(f"{identity}: issue occurred after kickoff; do not present as a pregame issue")
        except (TypeError, ValueError):
            errors.append(f"{identity}: invalid or timezone-inconsistent issue/kickoff timestamp")
        circa = game.get("circa") or {}
        for field in ("cover_home", "cover_away", "push", "expected_home", "expected_away"):
            value = circa.get(field)
            if value is not None and (not number(value) or not 0 <= value <= 1):
                errors.append(f"{identity}: circa.{field} is not a probability or null")
        spread = circa.get("home_spread")
        if spread is not None and not number(spread):
            errors.append(f"{identity}: contest spread is not numeric or null")
        push = circa.get("push")
        if number(spread) and not float(spread).is_integer() and push is not None and push != 0:
            errors.append(f"{identity}: noninteger contest line cannot push")
        covers = [circa.get("cover_home"), circa.get("cover_away"), push]
        if all(number(v) for v in covers) and abs(sum(covers) - 1) > 0.003:
            errors.append(f"{identity}: cover_home + cover_away + push does not equal 1")
        for side in ("home", "away"):
            cover, expected = circa.get(f"cover_{side}"), circa.get(f"expected_{side}")
            if all(number(v) for v in (cover, push, expected)) and abs(expected - cover - 0.5 * push) > 0.001:
                errors.append(f"{identity}: {side} expected contest points do not equal cover + half push")
        for clock, forecast in (game.get("forecasts") or {}).items():
            for field in ("win_home", "win_away", "tie_probability", "margin_home", "total"):
                value = forecast.get(field)
                if value is not None and not number(value):
                    errors.append(f"{identity} {clock}: {field} is not finite or null")
            for field in ("win_home", "win_away", "tie_probability"):
                value = forecast.get(field)
                if number(value) and not 0 <= value <= 1:
                    errors.append(f"{identity} {clock}: {field} is outside [0,1]")
            values = [forecast.get(k) for k in ("win_home", "win_away", "tie_probability")]
            if all(number(v) for v in values) and abs(sum(values) - 1) > 0.003:
                errors.append(f"{identity} {clock}: winner probability mass does not sum to 1")
            try:
                issued, kickoff = instant(forecast.get("issued_at")), instant(game.get("kickoff_utc"))
                if issued and kickoff and issued > kickoff:
                    errors.append(f"{identity} {clock}: original forecast issue follows kickoff")
                for field in ("compiled_at", "as_of"):
                    if forecast.get(field):
                        instant(forecast[field])
            except (TypeError, ValueError):
                errors.append(f"{identity} {clock}: invalid or timezone-inconsistent timestamp")
    for i, row in enumerate(performance):
        for field in ("season_2024", "season_2025", "test_2026", "validation_score", "games_2024", "games_2025", "games_2026"):
            value = row.get(field)
            if value is not None and not number(value):
                errors.append(f"Performance row {i}: {field} is not finite or null")
    for i, row in enumerate((data.get("newest_model_comparison") or {}).get("rows", [])):
        incumbent, newest, change = [row.get(k) for k in ("incumbent_validation", "best_new_validation", "new_minus_incumbent")]
        if not all(number(v) for v in (incumbent, newest, change)):
            errors.append(f"Newest comparison row {i}: nonfinite comparison values")
        elif abs(newest - incumbent - change) > 1e-8:
            errors.append(f"Newest comparison row {i}: change does not match saved values")
        else:
            expected = change > 0 if "accuracy" in row.get("objective", "") else change < 0
            if row.get("new_fit_beats_incumbent") is not expected:
                errors.append(f"Newest comparison row {i}: improvement direction conflicts with objective")
    html = (root / "research-history.html").read_text()
    js = (root / "app.js").read_text()
    document = Document()
    document.feed(html)
    if len(set(document.ids)) != len(document.ids):
        errors.append("HTML contains duplicate element IDs")
    referenced = set(re.findall(r'\$\("([\w-]+)"\)', js))
    for missing in sorted(referenced - set(document.ids)):
        errors.append(f"JS control target absent from HTML: {missing}")
    for asset in document.assets:
        if "://" in asset or not (root / asset).is_file():
            errors.append(f"Required local asset missing or unexpectedly external: {asset}")
    if "Circa Million Picks &amp;" not in html or "Performance Dashboard" not in html:
        errors.append("Exact Circa dashboard title is missing")
    public_text = json.dumps(data, ensure_ascii=False) + html
    private_markers = ("s3://", "arn:aws:", "/home/sagemaker-user/", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "appgprj_")
    for marker in private_markers:
        if marker in public_text:
            errors.append(f"Public snapshot contains a private/internal marker: {marker}")
    current_html = (root / "index.html").read_text()
    current = Document()
    current.feed(current_html)
    if len(current.ids) != len(set(current.ids)):
        errors.append("Week 12 duplicate HTML anchors")
    if set(("gameday", "slate", "circa", "results", "cards")) - set(current.ids):
        errors.append("Week 12 game day, contest, results or share card navigation missing")
    if set(current.future_weeks) != set(map(str, range(12,19))) or len(set(current.market_games)) != 16:
        errors.append("Future-season and all-week market registration incomplete")
    if not (root / "archive/n186/index.html").is_file():
        errors.append("Prior issued Week 12 archive missing")
    if len(current.games) != 16 or len(set(current.games)) != 16:
        errors.append("Week 12 must present all sixteen distinct games")
    if sorted(int(x) for x in current.ranks) != list(range(1, 17)):
        errors.append("Contest decision requires all sixteen game ranks")
    if len(current.weights) != 35 or any(current.weights.count(w) != 7 for w in ("50", "40", "30", "20", "10")):
        errors.append("All seven league objectives need all five validation weightings")
    contest = (root / "circa/index.html").read_text()
    if "<h1>Circa Million Picks &amp; Performance Dashboard</h1>" not in contest or contest.count("data-card-season=") != 3:
        errors.append("Dedicated contest page or its season evidence is missing")
    if current_html.count("data-replay-week=") != 11 or not (root / "archive/n187/index.html").is_file():
        errors.append("Completed NFL weeks and prior issue archive are required")
    if current_html.count("data-joint-games=") != 7 or current_html.count("data-joint-ratio=") != 5:
        errors.append("Paired scores require the remaining scheduled weeks and all selection weights")
    if len({p for p in current.images if p.startswith("share/")}) != 18 or any(not (root / p).is_file() for p in current.images):
        errors.append("Seventeen downloadable public phone cards are required")
    if not any(p.startswith("research-history.html") for p in current.links):
        errors.append("The current release must link to historical research")
    for week in range(12, 19):
        if not (root / "weeks" / str(week) / "index.html").is_file():
            errors.append(f"Missing direct week {week} page")
    if (root / "thanksgiving/index.html").read_text().count('data-fixture=') != 3:
        errors.append("Thanksgiving requires its three distinct games")
    if current_html.count('data-current-ratio=') != 5:
        errors.append("N190 auxiliary decisions missing")
    for asset in current.assets:
        if "://" in asset or not (root / asset).is_file():
            errors.append(f"Current page requires missing or nonlocal asset {asset}")
    if current_html.count('data-interval-weight=') != 5 or current_html.count('data-range-game=') != 16 or contest.count('data-n191-card-rule=') != 5:
        errors.append("Interval decisions, game forecasts and matched contest comparisons required")
    if current_html.count('data-event-weight=') != 5 or current_html.count('data-event-game=') != 16 or contest.count('data-weekly-utility-weight=') != 5:
        errors.append("All five event and contest ratios and all Week 12 probabilities are required")
    if current_html.count('data-n193-game=') != 16 or current_html.count('data-n193-validation=') != 5 or contest.count('data-n193-sides=') != 3:
        errors.append("Nine score objectives and all three distinct official cards are required")
    if current_html.count('data-n194-game=') != 16 or current_html.count('data-n194-validation=') != 5 or contest.count('data-n194-sides=') != 5 or not (root / 'archive/n193/all-games/index.html').is_file():
        errors.append("Current and historical N194/N193 consumer routes and official model cards are incomplete")
    direct = (root / "against-the-spread/index.html").read_text()
    for key in ("official-games", "dk-games", "annual", "ratios", "source-coverage"):
        if f'data-n195="{key}"' not in direct:
            errors.append(f"Missing specialist evidence: {key}")
    if not (root / "archive/n194/circa/index.html").is_file() or "n195-specialist" not in current_html:
        errors.append("Missing specialist entrance or N194 archive")
    for role in ("all_points","top5_points","direct_brier"):
        if f'data-n195="alternatives-{role}"' not in direct:
            errors.append(f"Missing complete official alternatives for {role}")
    for marker in private_markers:
        if marker in current_html:
            errors.append(f"Week 12 contains an internal marker {marker}")
    return {"status": "FAIL" if errors else "PASS", "current_games": len(current.games),
            "contest_games": len(current.ranks), "objective_weights": len(current.weights),
            "games": len(games), "performance_rows": len(performance), "placeholder_allowed": allow_empty, "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()
    result = validate(Path(__file__).resolve().parent, args.allow_empty)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["errors"]))
