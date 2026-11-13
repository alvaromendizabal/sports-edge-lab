#!/usr/bin/env python3
"""Build an honest Circa Million ATS board from genuine model margins and official lines.

This is a small standalone integration component. It does not acquire odds,
train a model, estimate a score distribution, call S3, or issue a forecast.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any


class InvalidBoard(ValueError):
    """A board or an input game fails integrity checks."""


def _instant(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise InvalidBoard(f"{field}: missing or invalid UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidBoard(f"{field}: ISO-8601 timestamp required") from exc
    if parsed.tzinfo is None:
        raise InvalidBoard(f"{field}: timezone must be explicit")
    return parsed.astimezone(timezone.utc)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidBoard(f"{field}: nonempty text required")
    return value.strip()


def _pmf(value: Any) -> dict[int, float]:
    if not isinstance(value, dict) or not value:
        raise InvalidBoard("margin_pmf: nonempty integer-margin distribution required")
    result: dict[int, float] = {}
    for raw_margin, raw_prob in value.items():
        if not isinstance(raw_margin, str) or not raw_margin.lstrip("-").isdigit():
            raise InvalidBoard("margin_pmf: integer margin keys required")
        margin = int(raw_margin)
        if str(margin) != raw_margin or margin in result:
            raise InvalidBoard(f"margin_pmf: noncanonical or duplicate margin {raw_margin}")
        if isinstance(raw_prob, bool) or not isinstance(raw_prob, (int, float)):
            raise InvalidBoard("margin_pmf: finite numeric probabilities required")
        probability = float(raw_prob)
        if not math.isfinite(probability) or probability < 0 or probability > 1:
            raise InvalidBoard("margin_pmf: each probability must be within [0,1]")
        result[margin] = probability
    if not math.isclose(math.fsum(result.values()), 1.0, abs_tol=1e-9):
        raise InvalidBoard("margin_pmf: probabilities must sum to 1")
    return result


def _score(game: dict[str, Any], asof: datetime) -> tuple[list[dict[str, Any]], str | None]:
    required = ("game_id", "home_team", "away_team", "forecast_id")
    identities = {key: _text(game.get(key), key) for key in required}
    if identities["home_team"] == identities["away_team"]:
        raise InvalidBoard("home_team and away_team are the same")

    kickoff = _instant(game.get("kickoff_utc"), "kickoff_utc")
    model_issued = _instant(game.get("model_issued_at_utc"), "model_issued_at_utc")
    line_captured = _instant(game.get("line_captured_at_utc"), "line_captured_at_utc")
    if model_issued >= kickoff:
        raise InvalidBoard("model issue must precede actual kickoff")
    if line_captured >= kickoff:
        raise InvalidBoard("official line capture must precede actual kickoff")
    if model_issued > asof or line_captured > asof:
        return [], "FUTURE_MODEL_OR_LINE_CAPTURE"
    if kickoff <= asof:
        return [], "GAME_ALREADY_STARTED"
    if game.get("official_circa_contest_line") is not True:
        return [], "NO_DECLARED_OFFICIAL_CIRCA_CONTEST_LINE"

    source = _text(game.get("contest_line_source"), "contest_line_source")
    if "circa" not in source.lower() or "contest" not in source.lower():
        raise InvalidBoard("contest_line_source must identify the official Circa contest line")
    spread = game.get("spread_home")
    if isinstance(spread, bool) or not isinstance(spread, (float, int)):
        raise InvalidBoard("spread_home: numeric home-team handicap required")
    spread = float(spread)
    if not math.isfinite(spread) or abs(spread) > 80 or not math.isclose(spread * 2, round(spread * 2)):
        raise InvalidBoard("spread_home: finite half-point increment within +/-80 required")

    probs = _pmf(game.get("margin_pmf"))
    choices = []
    for side in ("HOME", "AWAY"):
        cover = 0.0
        push = 0.0
        fail = 0.0
        for home_margin, probability in probs.items():
            edge = home_margin + spread
            adjusted = edge if side == "HOME" else -edge
            if adjusted > 0:
                cover += probability
            elif adjusted < 0:
                fail += probability
            else:
                push += probability
        expected = cover + 0.5 * push
        choices.append({
            "game_id": identities["game_id"],
            "pick_team": identities["home_team"] if side == "HOME" else identities["away_team"],
            "opponent": identities["away_team"] if side == "HOME" else identities["home_team"],
            "side": side,
            "contest_spread": spread if side == "HOME" else -spread,
            "p_cover": round(cover, 9),
            "p_push": round(push, 9),
            "p_fail": round(fail, 9),
            "expected_contest_points": round(expected, 9),
            "model_expected_home_margin": round(math.fsum(m * p for m, p in probs.items()), 4),
            "forecast_id": identities["forecast_id"],
            "model_issued_at_utc": model_issued.isoformat(),
            "contest_line_captured_at_utc": line_captured.isoformat(),
            "contest_line_source": source,
            "kickoff_utc": kickoff.isoformat(),
        })
    if not math.isclose(math.fsum(choice["expected_contest_points"] for choice in choices), 1.0, abs_tol=3e-9):
        raise InvalidBoard("two opposing Circa contest sides must sum to 1 expected point")
    return choices, None


def build_board(payload: dict[str, Any], asof_utc: str) -> dict[str, Any]:
    """Validate and rank every eligible side, then choose up to 5 distinct games."""
    if not isinstance(payload, dict):
        raise InvalidBoard("input: JSON object required")
    asof = _instant(asof_utc, "asof_utc")
    games = payload.get("games")
    if not isinstance(games, list):
        raise InvalidBoard("games: array required")

    all_sides: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for i, game in enumerate(games):
        if not isinstance(game, dict):
            raise InvalidBoard(f"games[{i}]: object required")
        gid = _text(game.get("game_id"), f"games[{i}].game_id")
        if gid in seen_ids:
            raise InvalidBoard(f"duplicate game_id: {gid}")
        seen_ids.add(gid)
        try:
            sides, reason = _score(game, asof)
            if reason:
                skipped.append({"game_id": gid, "reason": reason})
            else:
                all_sides.extend(sides)
        except InvalidBoard as exc:
            skipped.append({"game_id": gid, "reason": "INVALID_SOURCE_OR_DISTRIBUTION", "detail": str(exc)})

    all_sides.sort(key=lambda x: (-x["expected_contest_points"], x["game_id"], x["side"]))
    shortlist = []
    chosen_games: set[str] = set()
    for candidate in all_sides:
        if candidate["game_id"] not in chosen_games:
            shortlist.append(candidate)
            chosen_games.add(candidate["game_id"])
        if len(shortlist) == 5:
            break
    return {
        "board_asof_utc": asof.isoformat(),
        "contest": "2026 Circa Million VIII; static official contest spread",
        "scoring": "win=1,push=0.5,loss=0",
        "selection_objective": "maximum expected contest points; at most one side per game",
        "has_five_supplied_eligible_games": len(shortlist) == 5,
        "status": "FIVE_CANDIDATES_FROM_SUPPLIED_DATA" if len(shortlist) == 5 else "INSUFFICIENT_VALID_LINES_OR_FORECASTS",
        "games_received": len(games),
        "games_with_declared_official_lines": len(all_sides) // 2,
        "all_eligible_sides": all_sides,
        "top_five": shortlist,
        "skipped_games": skipped,
        "disclaimer": (
            "Model probabilities and official-line claims are taken from supplied artifacts; "
            "this tool does not independently verify line authenticity, issue forecasts, "
            "publish a betting recommendation or establish an advantage."
        ),
    }


def _write_atomic(destination: Path, obj: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".tmp", prefix=".circa.",
            dir=destination.parent, delete=False,
        ) as stream:
            name = stream.name
            json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, destination)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="private genuine JSON game/PMF/line source")
    parser.add_argument("--asof-utc", required=True, help="actual board decision timestamp, ISO-8601 with UTC offset")
    parser.add_argument("--output", type=Path, required=True, help="local output board JSON; does not publish")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        source = json.load(stream)
    result = build_board(source, args.asof_utc)
    _write_atomic(args.output, result)
    print(json.dumps({
        "status": result["status"],
        "games_received": result["games_received"],
        "eligible_games": result["games_with_declared_official_lines"],
        "top_five_count": len(result["top_five"]),
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
