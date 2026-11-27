"""Create deterministic phone-sized NBA graphics from the public board only."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tracks/nba/current/board.json"
OUT = ROOT / "tracks/nba/current/graphics"
FONT = Path("/usr/share/fonts/truetype/dejavu")
TZ = ZoneInfo("America/Los_Angeles")
NAVY, INK, MUTED, PAPER, LINE, TEAL = "#101f31", "#172a40", "#627184", "#f4f6f7", "#dce3e7", "#007b72"


def font(size, bold=False):
    return ImageFont.truetype(str(FONT / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)


def text(d, xy, value, size=30, color=INK, bold=False):
    bounds = d.textbbox(xy, str(value), font=font(size, bold))
    if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > 1080 or bounds[3] > 1920:
        raise ValueError("Text would clip the phone graphic: " + str(value))
    d.text(xy, str(value), font=font(size, bold), fill=color)


def wrap(d, value, width, size=30):
    lines, line = [], ""
    for word in value.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=font(size)) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + ([line] if line else [])


def paragraph(d, xy, value, width, size=30, color=MUTED, line_height=None):
    x, y = xy
    line_height = line_height or int(size * 1.45)
    for line in wrap(d, value, width, size):
        text(d, (x, y), line, size, color)
        y += line_height
    return y


def clock(value, short=False):
    if not value:
        return "unverified"
    t = dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(TZ)
    return t.strftime("%b %-d, %-I:%M %p PST" if not short else "%-I:%M %p")


def publication_note(data):
    return "Local draft · updated snapshot not published" if data["publication_status"].startswith("Local draft") else "Published snapshot · forecast issue clocks retained"


def preparation_note(data):
    value = data.get("next_release_preparation", {})
    return value.get("release_label", "B120 R2") + " · " + value.get("status_label", "Prepared and verified").lower()


def canvas(subtitle, data, index=None):
    img = Image.new("RGB", (1080, 1920), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1080, 330), fill=NAVY)
    text(d, (60, 44), "SPORTS EDGE LAB  /  NBA", 29, "#9cd7c8", True)
    text(d, (60, 103), "Spread & Totals", 76, "#ffffff", True)
    text(d, (60, 210), subtitle, 35, "#e0e8ef", True)
    text(d, (60, 273), "B119 saved outlooks · " + preparation_note(data), 25, "#bbcad8")
    if index:
        text(d, (920, 46), index, 24, "#bbcad8")
    return img, d


def issue_summary(rows, target):
    values = sorted({r["horizons"]["120"][target]["issued_at_utc"] for r in rows if r["horizons"]["120"][target].get("issued_at_utc")})
    if not values:
        return "unavailable"
    return clock(values[0]) if len(values) == 1 else f"{clock(values[0])} to {clock(values[-1])}"


def draw_game(d, g, y, market_count=0):
    d.rounded_rectangle((50, y, 1030, y + 220), radius=16, fill="white", outline=LINE, width=2)
    tip = clock(g["tip_at_utc"], True)
    observation = g.get("calendar_observation", g)
    status = f"FINAL {observation['away_score']}–{observation['home_score']}" if observation["completed"] else observation.get("status", "SCHEDULED") + " AT CALENDAR CHECK"
    text(d, (74, y + 17), f"{tip} PT", 25, MUTED)
    sw = d.textlength(status, font=font(21, True))
    text(d, (1005 - sw, y + 20), status, 21, MUTED, True)
    text(d, (74, y + 55), f"{g['away_abbr']} at {g['home_abbr']}", 44, INK, True)
    rs = g["horizons"]["120"]
    w, m, t = (rs[k]["value"] for k in ("winner", "margin", "total"))
    pick = g["home_abbr"] if w is not None and w >= .5 else g["away_abbr"]
    win = f"{pick} {max(w, 1-w)*100:.1f}%" if w is not None else "Unavailable"
    margin = f"{g['home_abbr'] if m > 0 else g['away_abbr']} by {abs(m):.1f}" if m is not None and m != 0 else "Even" if m == 0 else "Unavailable"
    total = f"{t:.1f}" if t is not None else "Unavailable"
    for x, label, value in [(74, "WINNER PROBABILITY", win), (405, "EXPECTED MARGIN", margin), (754, "EXPECTED TOTAL", total)]:
        text(d, (x, y + 122), label, 20, MUTED, True)
        text(d, (x, y + 153), value, 34 if len(value) < 13 else 30, TEAL if x == 74 else INK, True)
    freshness = "SAVED PREGAME ISSUE" if observation["completed"] else "STALE SAVED OUTLOOK"
    text(d, (74, y + 192), freshness, 19, MUTED if observation["completed"] else "#9c641c", True)
    text(d, (405, y + 192), f"{market_count} captured contracts" if market_count else "No captured contracts", 18, MUTED)
    if t is None:
        text(d, (754, y + 192), "Fixture-time mismatch", 17, "#9c641c")


def main():
    data = json.loads(DATA.read_text())
    week = [g for g in data["games"] if g["in_week"]]
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = []
    market_counts = collections.Counter(row["game_id"] for row in data.get("observed_contracts", []))
    market = data["observed_contract_snapshot"]
    groups = collections.defaultdict(list)
    for g in week:
        groups[g["pacific_date"]].append(g)
    for date, rows in sorted(groups.items()):
        pages = math.ceil(len(rows) / 5)
        day = dt.date.fromisoformat(date).strftime("%A, %B %-d")
        for i in range(pages):
            selected = rows[i*5:(i+1)*5]
            img, d = canvas(day, data, f"{i+1}/{pages}")
            text(d, (60, 354), f"{len(rows)} observed games today · saved T−120 roles", 28, MUTED)
            y = 410
            for g in selected:
                draw_game(d, g, y, market_counts[g["game_id"]])
                y += 238
            footer_y = 1618
            d.line((60, footer_y - 22, 1020, footer_y - 22), fill=LINE, width=2)
            text(d, (60, footer_y), "Saved model issues / fresh calendar", 23, TEAL, True)
            text(d, (60, footer_y + 34), "Winner / margin issued: " + issue_summary(selected, "winner"), 22, MUTED)
            text(d, (60, footer_y + 66), "T−120 totals issued: " + issue_summary(selected, "total"), 22, MUTED)
            text(d, (60, footer_y + 98), "Kalshi capture: " + clock(market["captured_at_utc"]), 22, MUTED)
            text(d, (60, footer_y + 134), "Weekly calendar: " + clock(data["latest_week_calendar"]["checked_at_utc"]), 22, INK, True)
            text(d, (60, footer_y + 166), preparation_note(data) + "; latest owner result R1 partial.", 22, MUTED)
            text(d, (60, footer_y + 202), "Saved winner estimates · calibration incomplete.", 21, MUTED)
            text(d, (60, footer_y + 232), "Captured asks only · fees / model probabilities unavailable.", 21, MUTED)
            text(d, (60, footer_y + 262), publication_note(data), 21, MUTED)
            p = OUT / f"nba_{date}_page_{i+1:02d}.png"
            img.save(p, optimize=True)
            outputs.append({"file": p.name, "game_ids": [g["game_id"] for g in selected], "width": 1080, "height": 1920, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    img, d = canvas("Week of November 23–29, 2026", data)
    text(d, (60, 375), "The evidence at a glance", 44, INK, True)
    calendar = data["latest_week_calendar"]
    complete = sum(all(role["value"] is not None for role in g["horizons"]["120"].values()) for g in week)
    for x,y,n,label,detail in [(60,470,str(len(week)),"Observed week games",f"{calendar['final_games']} final · {calendar['scheduled_games']} scheduled at calendar check"),(560,470,f"{complete} / {len(week)}","Three saved point roles","T−120; fixture mismatch left visible"),(60,710,str(market['observed_contract_count']),"Observed Kalshi contracts",f"{market['games_with_observed_contracts']} games · no model sides or net returns"),(560,710,f"{data['completed_games']:,} / {data['declared_games']:,}","Saved season census","November 25; future calendar provisional")]:
        text(d,(x,y),n,64,TEAL,True);text(d,(x,y+90),label,29,INK,True);paragraph(d,(x,y+138),detail,450,23,MUTED,32)
    d.line((60,970,1020,970),fill=LINE,width=2)
    text(d,(60,1010),"Selected on 2024–25 and 2025–26",35,INK,True)
    paragraph(d,(60,1070),"Equal annual weights select the displayed log-loss winner and RMSE point roles. Calibration is incomplete. Previously inspected 2026–27 results are report-only; no promotion is claimed.",960,29,MUTED,43)
    text(d,(60,1275),"Stale saved model outlooks",35,INK,True)
    paragraph(d,(60,1330),"Upcoming winner and margin issues were saved Nov 25 at 11:40 AM PST. These T−120 pages retain Nov 19, 2:10 PM PST totals. Miami at Cleveland on Nov 29 has no matching saved total issue.",960,29,MUTED,43)
    text(d,(60,1555),"Latest verified owner result: R1 partial",27,INK,True)
    text(d,(60,1596),"Owner evidence checked: " + clock(data["owner_control_observation"]["observed_at_utc"]),23,MUTED)
    text(d,(60,1633),preparation_note(data),28,TEAL,True)
    paragraph(d,(60,1680),"No new model issue is verified. Kalshi captured 682 propositions across 11 games; side probabilities and net returns remain unavailable.",960,25,MUTED,35)
    text(d,(60,1762),"Forecast census: " + clock(data["source_observed_at_utc"]),22,MUTED)
    text(d,(60,1795),"Weekly calendar: " + clock(data["latest_week_calendar"]["checked_at_utc"]),22,MUTED)
    text(d,(60,1830),"Kalshi capture: " + clock(market["captured_at_utc"]),23,MUTED)
    text(d,(60,1870),publication_note(data),23,TEAL,True)
    p=OUT/'nba_2026-11-23_week_overview.png';img.save(p,optimize=True)
    outputs.insert(0,{"file":p.name,"game_ids":[],"width":1080,"height":1920,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    assert sorted(gid for r in outputs for gid in r["game_ids"]) == sorted(g["game_id"] for g in week)
    manifest = {"schema":"public.nba.phone_graphics.v1","source_projection_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"games":len(week),"images":outputs,"snapshot_label":"B119 stale saved outlooks · " + preparation_note(data),"owner_status_asof_utc":data["owner_execution_status_asof_utc"],"owner_status":"R1 partial after all 2,140 saved publication tasks recovered","owner_control_observation":data["owner_control_observation"],"prepared_execution_status":data["prepared_execution_status"],"prepared_execution_status_asof_utc":data["prepared_execution_status_asof_utc"],"next_release_preparation":data["next_release_preparation"],"R1_owner_results_included":False,"R1_operational_status_included":True,"R1_new_forecasts_included":False,"prior_publication_tasks_recovered":2140,"new_owner_campaign_fits":0,"new_provider_requests_by_graphics_generation":0,"calendar_provider_requests":calendar["official_requests"],"r2_preparation":data["r2_preparation"],"forecast_freshness":data["forecast_freshness"],"observed_contract_snapshot":market,"forecasts_changed_by_graphics_generation":False,"calendar_checked_at_utc":calendar["checked_at_utc"],"calendar_final_games":calendar["final_games"],"calendar_scheduled_games":calendar["scheduled_games"],"calendar_status_counts":calendar.get("status_counts",{}),"full_season_census_refreshed":False,"publication_status":data["publication_status"],"public_site_url":data["public_site_url"],"public_graphics_url":data["public_graphics_url"],"initial_hosting_verification":data["initial_hosting_verification"]}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({"images":len(outputs),"covered_games":len(week),"bytes":sum(p.stat().st_size for p in OUT.glob('*.png'))}))


if __name__ == "__main__":
    main()
