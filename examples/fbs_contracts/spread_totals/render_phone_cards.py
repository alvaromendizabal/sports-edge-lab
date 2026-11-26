"""Render exact FBS board data as paginated 1290 x 2796 phone PNGs.

No screenshot, remote font, network source, model fit or new probability is used.
Text comes from the checked public board. Pixel bounds are verified before save.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

from build_board import validate, probability_rank, return_rank, point_baseline_rows

W, H = 1290, 2796
BG, PANEL, LINE = "#08111f", "#111f31", "#31445b"
INK, MUTED, MINT, AMBER = "#f3f7fb", "#b2c2d4", "#a1ebcb", "#ffce8a"
FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")


def science_sha(data):
    base = {k: v for k, v in data.items() if k != "graphics"}
    return hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def stamp(value):
    if not value:
        return "Clock unavailable"
    d = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    return d.strftime("%b %-d · %-I:%M %p PT")


def number(value):
    return "Unavailable" if value is None else f"{value:.1f}"


def percentage(value):
    return "Unavailable" if value is None else f"{100*value:.1f}%"


class Page:
    def __init__(self):
        self.image = Image.new("RGB", (W, H), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.runs = []

    def text(self, xy, text, size=46, color=INK, bold=False, width=None, max_lines=1, line_gap=8):
        font = ImageFont.truetype(str(FONT_ROOT / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)
        text = str(text)
        words, lines, line = text.split(), [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if width is not None and self.draw.textlength(candidate, font=font) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        if not lines:
            lines = [""]
        if len(lines) > max_lines:
            raise ValueError(f"Text requires {len(lines)} lines; expected <= {max_lines}: {text}")
        x, y = xy
        step = size + line_gap
        for i, item in enumerate(lines):
            box = self.draw.textbbox((x, y + i * step), item, font=font, anchor="lt")
            if box[0] < 0 or box[1] < 0 or box[2] > W - 35 or box[3] > H - 25:
                raise ValueError(f"Text outside image: {item}, {box}")
            if width is not None and box[2] - box[0] > width + 1:
                raise ValueError(f"Text outside assigned column: {item}")
            self.draw.text((x, y + i * step), item, font=font, fill=color, anchor="lt")
            self.runs.append({"text": item, "font_pixels": size, "box": list(box)})
        return y + len(lines) * step

    def header(self, data, subtitle, page, count):
        self.text((50, 45), "SPORTS EDGE LAB · FBS", 43, MINT, True)
        self.text((47, 111), "Spread & Totals", 94, INK, True)
        self.text((52, 232), f"{subtitle} · {page}/{count}", 48, INK, True, width=1180)
        self.text((52, 302), f"{data['release']['label']} · Forecast {stamp(data['clocks']['forecast_as_of'])}", 42, MUTED, width=1180)
        self.draw.line((50, 367, 1240, 367), fill=LINE, width=2)

    def footer(self, data, population, qualification):
        self.draw.line((50, 2528, 1240, 2528), fill=LINE, width=2)
        self.text((52, 2563), population, 41, INK, width=1180)
        self.text((52, 2631), qualification, 36, AMBER, width=1180, max_lines=2, line_gap=9)
        state = data["publication"].get("graphics_status_label", "Dated research snapshot · deployment status on board")
        self.text((52, 2735), state, 36, MUTED, width=1180)

    def save(self, path, metadata):
        info = PngImagePlugin.PngInfo()
        for k, v in metadata.items():
            info.add_text(k, v if isinstance(v, str) else json.dumps(v, separators=(",", ":")))
        self.image.save(path, pnginfo=info, optimize=True)
        return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "width": W, "height": H, "text_runs": self.runs}


def game_card(page, game, y):
    page.draw.rounded_rectangle((48, y, 1242, y + 410), radius=22, fill=PANEL, outline=LINE, width=2)
    page.text((73, y + 20), stamp(game["kickoff_utc"]), 39, MUTED, width=820)
    status = game["status"].upper()
    page.text((950, y + 20), status, 36, MUTED, width=260)
    page.text((73, y + 74), game["away"] + " at", 47, INK, True, width=1120)
    page.text((73, y + 133), game["home"], 47, INK, True, width=1120)
    probability = game["winner"]["home_probability"]
    selected = game["home"] if probability is not None and probability >= .5 else game["away"]
    selected_p = None if probability is None else max(probability, 1 - probability)
    cal = game["winner"]["calibration_status"]
    cal_label = "calibrated" if cal in {"fitted", "fitted_component_blend"} else "raw" if cal == "identity" else "calibration unverified"
    page.text((73, y + 202), f"WINNER · {game['winner']['model']} · {cal_label}", 36, MUTED, width=820)
    page.text((73, y + 248), selected if probability is not None else "Unavailable", 45, MINT, True, width=820)
    page.text((950, y + 231), percentage(selected_p), 61 if selected_p is not None else 36, MINT, True, width=265)
    margin = game["margin"]["home_minus_away"]
    page.text((73, y + 310), "HOME − AWAY · " + game["margin"]["model"], 36, MUTED, width=780)
    page.text((73, y + 353), "Unavailable" if margin is None else f"{margin:+.1f}", 36 if margin is None else 45, INK, True, width=330)
    favorite = "Margin unavailable" if margin is None else "No point favorite" if margin == 0 else f"{game['home'] if margin > 0 else game['away']} by {abs(margin):.1f}"
    page.text((330, y + 358), favorite, 36, INK, width=575)
    page.text((976, y + 310), "TOTAL · " + game["total"]["model"], 32, MUTED, width=240)
    page.text((976, y + 353), number(game["total"]["points"]), 45 if game["total"]["points"] is not None else 34, INK, True, width=240)


def ranked_card(page, contract, game, rank, y, mode):
    # The exact native proposition is a complete sentence, often four lines.
    # Three cards per page preserve it without shortening contract wording.
    page.draw.rounded_rectangle((48, y, 1242, y + 680), radius=22, fill=PANEL, outline=LINE, width=2)
    name = f"{game['away']} at {game['home']}"
    page.text((73, y + 22), name if mode == "point_baseline" else f"#{rank} · {name}", 43, INK, True, width=1120, max_lines=2)
    page.text((73, y + 137), contract["proposition"], 43, INK, width=1120, max_lines=5)
    side = contract["point_baseline_side"] if mode == "point_baseline" else contract["best_return_side"] if mode == "return" else contract["most_probable_side"]
    p = contract.get("p_yes") if side == "YES" else contract.get("p_no")
    page.text((73, y + 412), side, 65, MINT, True, width=500)
    if mode == "point_baseline":
        page.text((850, y + 425), f"{contract['point_baseline_value']:.1f} pts", 48, MINT, True, width=365)
    else:
        page.text((887, y + 412), percentage(p), 65, MINT, True, width=330)
    q = contract.get("sides", {}).get(side, {})
    price = q.get("executable_price")
    net = q.get("expected_net_per_contract")
    price_label = "Executable price unavailable" if price is None else f"Price {price*100:.1f}¢ · {stamp(q.get('observed_at'))}"
    if price is None and q.get("observed_ask_price") is not None:
        price_label = (f"Observed {q['observed_ask_price']*100:.1f}¢ · {stamp(q.get('observed_ask_at'))}"
                       f" · {q['observed_ask_status'].lower()}")
    page.text((73, y + 510), price_label, 36, MUTED, width=1120)
    net_label = "Net return unavailable: price / fees not qualified" if net is None else f"Expected net {net:+.3f} USD / contract after fees"
    if mode == "point_baseline":
        net_label = "Point center only · binary probability unavailable"
    page.text((73, y + 565), net_label, 34, INK if net is not None else AMBER, width=1120)
    alias = contract["point_baseline_model"] if mode == "point_baseline" else contract["model"]
    page.text((73, y + 620), f"{alias} · Equality settles {contract['equality_settles']} · {contract['period']}", 32, MUTED, width=1120)


def release_status_page(data, directory, digest):
    """Explain a new research edition without issuing any new forecast."""
    research = data["release"].get("next_research")
    if not research:
        return None
    execution = data["release"].get("latest_owner_execution", {})
    page = Page()
    page.header(data, "RESEARCH STATUS", 1, 1)
    blocks = [
        ("LATEST VERIFIED RUN · " + execution.get("release", "UNAVAILABLE"),
         f"Recorded: {execution.get('new_model_fits', 'Unmeasured')} model fits · "
         f"{execution.get('new_calibrator_fits', 'Unmeasured')} calibrations",
         execution.get("summary", "See the verified owner return.")),
        ("NEXT CAMPAIGN · " + research["release"], "Prepared · awaiting owner launch",
         research["campaign_summary"]),
        ("EXPLICIT RESEARCH SPLIT", "2024–25 training · 2026 selection",
         "Late-2025 games are held out for calibration. Completed 2026 games select the new spread and total models and remain exposed validation. Prospective testing begins after the launch cutoff."),
        ("FORECASTS SHOWN NOW", "Prior frozen models · November 25 cutoff",
         "The inherited winner, margin and total forecasts retain their original identities, "
         "selection rules and source clocks. No new fit or fresh market quote is implied."),
    ]
    for index, (label, title, detail) in enumerate(blocks):
        y = 400 + index * 520
        page.draw.rounded_rectangle((48, y, 1242, y + 490), radius=22, fill=PANEL, outline=LINE, width=2)
        page.text((75, y + 30), label, 36, MUTED, True, width=1130)
        page.text((75, y + 97), title, 48, MINT, True, width=1130, max_lines=2)
        page.text((75, y + 242), detail, 40, INK, width=1110, max_lines=5, line_gap=11)
    page.footer(data, f"{data['population']['current_week_games']} weekly games · full forecasts retained",
                "70% is a research target. No new spread or total accuracy is claimed.")
    filename = "fbs_release_status.png"
    info = page.save(directory / filename, {"product": "Spread & Totals", "owner": "fbs",
                    "release": data["release"]["label"], "science_sha256": digest,
                    "forecast_as_of": data["clocks"]["forecast_as_of"], "new_fits": 0})
    return {"file": "graphics/" + filename, "title": "V118 research and execution status",
            "caption": "Verified prior failure, pending owner campaign and unchanged forecast cutoff",
            "alt": "V117 recorded zero new fits but global fit accounting is incomplete; V118 awaits owner launch. Existing forecasts retain their November 25 cutoff.",
            "kind": "release_status", **info}


def render(data, directory, scope="week"):
    validate(data)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = science_sha(data)
    games = sorted([g for g in data["games"] if scope == "season" or g["is_current_week"]],
                   key=lambda g: (g.get("kickoff_utc") or "9999", g["game_id"]))
    by_id = {g["game_id"]: g for g in data["games"]}
    records = []
    status_page = release_status_page(data, directory, digest)
    if status_page is not None:
        records.append(status_page)
    count = max(1, (len(games) + 4) // 5)
    for n in range(count):
        group = games[n * 5:(n + 1) * 5]
        page = Page()
        page.header(data, "ALL GAMES", n + 1, count)
        for i, game in enumerate(group):
            game_card(page, game, 390 + i * 426)
        page.footer(data, f"{len(games)} games in this view · {len(data['games'])} in season manifest",
                    "Early previews / reconstructions retain source clocks. No new original issue.")
        filename = f"fbs_all_games_{n+1:03d}.png"
        info = page.save(directory / filename, {"product": "Spread & Totals", "owner": "fbs",
                    "release": data["release"]["label"], "science_sha256": digest,
                    "forecast_as_of": data["clocks"]["forecast_as_of"], "game_ids": [g["game_id"] for g in group]})
        records.append({"file": "graphics/" + filename, "title": f"All games · page {n+1} of {count}",
                        "caption": f"{len(group)} games · forecast {stamp(data['clocks']['forecast_as_of'])}",
                        "alt": "; ".join(g["away"] + " at " + g["home"] for g in group),
                        "kind": "all_games", "game_ids": [g["game_id"] for g in group], **info})
    for market in ("spread", "total"):
        for mode, ranking in (("probability", probability_rank), ("return", return_rank), ("point_baseline", point_baseline_rows)):
            rows = ranking(data, market, weekly=scope != "season")
            if mode == "point_baseline":
                rows = [c for c in rows if not c.get("probability_qualified")]
            pages = (len(rows) + 2) // 3
            for n in range(pages):
                group = rows[n * 3:(n + 1) * 3]
                page = Page()
                title = ("SPREADS" if market == "spread" else "TOTALS") + (" · POINT BASELINES" if mode == "point_baseline" else " · PROBABILITY" if mode == "probability" else " · NET RETURN")
                page.header(data, title, n + 1, pages)
                for i, contract in enumerate(group):
                    ranked_card(page, contract, by_id[contract["game_id"]], n * 3 + i + 1, 390 + i * 695, mode)
                page.footer(data, f"{len(rows)} {'unranked point baselines' if mode == 'point_baseline' else 'qualified primary contracts'} · alternatives on board",
                            "Point rules are not probability-ranked. Exact terms apply." if mode == "point_baseline" else "Two sides: YES / NO. Actual contract terms determine equality and voids.")
                filename = f"fbs_{market}_{mode}_{n+1:03d}.png"
                info = page.save(directory / filename, {"product": "Spread & Totals", "owner": "fbs",
                                "release": data["release"]["label"], "science_sha256": digest,
                                "contract_ids": [c["contract_id"] for c in group]})
                records.append({"file": "graphics/" + filename, "title": f"{title.title()} · page {n+1} of {pages}",
                                "caption": "Unranked point-estimate sides; no binary probability" if mode == "point_baseline" else "Most probable side" if mode == "probability" else "Best observed net per contract after fees",
                                "alt": "; ".join(c["proposition"] for c in group), "kind": market + "_" + mode,
                                "contract_ids": [c["contract_id"] for c in group], **info})
    result = {"schema": "fbs.spread-totals.phone-graphics.v1", "science_sha256": digest, "scope": scope,
              "games_rendered": len(games), "pages": records, "new_fits": 0, "new_probabilities": 0,
              "text_bounds_checked": True, "render_function_modifies_input": False}
    (directory / "graphics_index.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--scope", choices=("week", "season"), default="week")
    p.add_argument("--attach-index", action="store_true", help="Attach only public graphic links to the input board")
    args = p.parse_args()
    data = json.loads(args.data.read_text())
    index = render(data, args.output, args.scope)
    if args.attach_index:
        data["graphics"] = {"science_sha256": index["science_sha256"], "scope": index["scope"],
                            "pages": [{k: v for k, v in p.items() if k != "text_runs"} for p in index["pages"]]}
        args.data.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "pages": len(index["pages"]), "games_rendered": index["games_rendered"],
                      "science_sha256": index["science_sha256"], "new_fits": 0, "new_probabilities": 0}))


if __name__ == "__main__":
    main()
