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


def canvas(subtitle, index=None):
    img = Image.new("RGB", (1080, 1920), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1080, 330), fill=NAVY)
    text(d, (60, 44), "SPORTS EDGE LAB  /  NBA", 29, "#9cd7c8", True)
    text(d, (60, 103), "Spread & Totals", 76, "#ffffff", True)
    text(d, (60, 210), subtitle, 35, "#e0e8ef", True)
    text(d, (60, 273), "B119 saved outlooks · R1 prepared for launch", 25, "#bbcad8")
    if index:
        text(d, (920, 46), index, 24, "#bbcad8")
    return img, d


def issue_summary(rows, target):
    values = sorted({r["horizons"]["120"][target]["issued_at_utc"] for r in rows if r["horizons"]["120"][target].get("issued_at_utc")})
    if not values:
        return "unavailable"
    return clock(values[0]) if len(values) == 1 else f"{clock(values[0])} to {clock(values[-1])}"


def draw_game(d, g, y):
    d.rounded_rectangle((50, y, 1030, y + 220), radius=16, fill="white", outline=LINE, width=2)
    tip = clock(g["tip_at_utc"], True)
    status = f"FINAL {g['away_score']}–{g['home_score']}" if g["completed"] else "UPCOMING AT SOURCE CUTOFF"
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
    if t is None:
        text(d, (754, y + 192), "Fixture-time mismatch", 17, "#9c641c")


def main():
    data = json.loads(DATA.read_text())
    week = [g for g in data["games"] if g["in_week"]]
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = []
    groups = collections.defaultdict(list)
    for g in week:
        groups[g["pacific_date"]].append(g)
    for date, rows in sorted(groups.items()):
        pages = math.ceil(len(rows) / 5)
        day = dt.date.fromisoformat(date).strftime("%A, %B %-d")
        for i in range(pages):
            selected = rows[i*5:(i+1)*5]
            img, d = canvas(day, f"{i+1}/{pages}")
            text(d, (60, 354), f"{len(rows)} observed games today · saved T−120 roles", 28, MUTED)
            y = 410
            for g in selected:
                draw_game(d, g, y)
                y += 238
            footer_y = 1618
            d.line((60, footer_y - 22, 1020, footer_y - 22), fill=LINE, width=2)
            text(d, (60, footer_y), "Saved issue clocks", 23, TEAL, True)
            text(d, (60, footer_y + 34), "Winner / margin: " + issue_summary(selected, "winner"), 22, MUTED)
            text(d, (60, footer_y + 66), "Totals: " + issue_summary(selected, "total"), 22, MUTED)
            text(d, (60, footer_y + 98), "Source census: " + clock(data["source_observed_at_utc"]), 22, MUTED)
            text(d, (60, footer_y + 134), "R1 preparation verified " + clock(data["prepared_execution_status_asof_utc"]), 22, INK, True)
            text(d, (60, footer_y + 166), "No R1 owner results; saved B119 outlooks remain.", 22, MUTED)
            text(d, (60, footer_y + 202), "0 qualified contracts; PIT / calibration incomplete.", 21, MUTED)
            text(d, (60, footer_y + 232), "Nominal horizon is not issue time. No source refresh.", 21, MUTED)
            text(d, (60, footer_y + 262), "Repository assets only · public hosting unverified.", 21, MUTED)
            p = OUT / f"nba_{date}_page_{i+1:02d}.png"
            img.save(p, optimize=True)
            outputs.append({"file": p.name, "game_ids": [g["game_id"] for g in selected], "width": 1080, "height": 1920, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    img, d = canvas("Week of November 23–29, 2026")
    text(d, (60, 375), "The evidence at a glance", 44, INK, True)
    for x,y,n,label,detail in [(60,470,"48","Observed week games","13 completed · 35 upcoming at cutoff"),(560,470,"47 / 48","Three saved point roles","T−120; fixture mismatch left visible"),(60,710,"0","Exact Kalshi contracts","No ranked YES/NO sides or prices"),(560,710,"261 / 1,200","Completed / declared","Current season; future calendar provisional")]:
        text(d,(x,y),n,64,TEAL,True);text(d,(x,y+90),label,29,INK,True);paragraph(d,(x,y+138),detail,450,23,MUTED,32)
    d.line((60,970,1020,970),fill=LINE,width=2)
    text(d,(60,1010),"Selected on 2024–25 and 2025–26",35,INK,True)
    paragraph(d,(60,1070),"Equal annual weights select the displayed log-loss winner and RMSE point roles. Previously inspected 2026–27 results are report-only; no production promotion is claimed.",960,29,MUTED,43)
    text(d,(60,1275),"Know the two clocks",35,INK,True)
    paragraph(d,(60,1330),"Nov 25 onward winner and margin issues were saved Nov 25 at 11:40 AM PST. Totals retain their Nov 19, 2:10 PM PST outlook. Miami at Cleveland on Nov 29 has no matching saved total issue.",960,29,MUTED,43)
    text(d,(60,1555),"B120 R1 prepared · owner execution separate",27,INK,True)
    text(d,(60,1596),"Preparation verified " + clock(data["prepared_execution_status_asof_utc"]),23,MUTED)
    text(d,(60,1633),"No R1 owner results; saved B119 outlooks remain.",25,TEAL,True)
    paragraph(d,(60,1680),"B119 partial: 2,140 publication-task failures (1,200 frontier + 940 legacy); 0 new fits. Saved forecasts remain unchanged.",960,25,MUTED,35)
    text(d,(60,1762),"Source census: " + clock(data["source_observed_at_utc"]),23,MUTED)
    text(d,(60,1806),"PIT / calibration incomplete; no admitted sides or prices.",23,MUTED)
    text(d,(60,1860),"Repository assets only · public hosting unverified.",23,TEAL,True)
    p=OUT/'nba_2026-11-23_week_overview.png';img.save(p,optimize=True)
    outputs.insert(0,{"file":p.name,"game_ids":[],"width":1080,"height":1920,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    assert sorted(gid for r in outputs for gid in r["game_ids"]) == sorted(g["game_id"] for g in week)
    (OUT/'manifest.json').write_text(json.dumps({"schema":"public.nba.phone_graphics.v1","source_projection_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"games":48,"images":outputs,"snapshot_label":"B119 saved outlooks · R1 prepared for launch","owner_status_asof_utc":data["owner_execution_status_asof_utc"],"owner_status":"Earlier B120 recovery blocked at recorded checkpoint","prepared_execution_status":data["prepared_execution_status"],"prepared_execution_status_asof_utc":data["prepared_execution_status_asof_utc"],"R1_owner_results_included":False,"forecasts_changed_by_graphics_generation":False,"publication_status":"Repository assets only; public hosting unverified"},indent=2)+'\n')
    print(json.dumps({"images":len(outputs),"covered_games":48,"bytes":sum(p.stat().st_size for p in OUT.glob('*.png'))}))


if __name__ == "__main__":
    main()
