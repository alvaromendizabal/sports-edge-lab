"""Render an additive, pinned NCAA evidence review. No training or source acquisition."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_PINS = {
    "NCAA_B063R2_PUBLIC_SCIENTIFIC_TABLES.json": "afd11df371e7886d6ed0adc97802fee565259cc9c95701f7cf8d133559f7f766",
    "B063_PUBLIC_EARLY_ORIGINAL_POSTISSUE_MONITORING.json": "af4813490e536bbb32b9c38e44af5e4504a45859bbbf8951e063003dc43ece35",
    "B063_PUBLIC_LATE_ORIGINAL_POSTISSUE_MONITORING.json": "918e8951f0972429c6a226d8347d53f07c746fb7c3beae0b904a5fbdaa2ddd58",
    "B063R2_PUBLIC_EXECUTION_STATUS.json": "a05d58f11f30ff4b422d85940a2ca89d82c34c57389e3fa95d242b4e4c7c0825",
}
KEYS = ("science", "early", "late", "execution")
START = "<!-- B063R2_EVIDENCE_LINK_START -->"
END = "<!-- B063R2_EVIDENCE_LINK_END -->"
BANNER = START + '''
<section id="b063r2-latest-evidence" aria-labelledby="b063r2-latest-title" style="margin:0 0 28px;padding:24px;border:1px solid #a4bcae;border-top:5px solid #17684f;border-radius:12px;background:#fffdf7;color:#193e31">
  <p style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;font-weight:750;margin:0 0 9px">November 12 · Latest NCAA evidence review</p>
  <h2 id="b063r2-latest-title" style="font-size:28px;line-height:1.2;margin:0 0 12px">Legacy models, season leaders and original forecasts—reconciled.</h2>
  <p>Open the complete 2024–25 and 2025–26 tables: <strong>164 candidate-season results, 28 season leaders and 14 pooled leaders</strong>. The separate current-season view includes 14 replay leaders, qualified market comparisons, and two preserved original-forecast cohorts with later final scores.</p>
  <p><strong>Latest actual owner: B063R2 passed startup tests, then failed prior-source compatibility; no new owner science ran.</strong> B064 is prepared for owner execution. The measured 12-worker activity was an engineering probe; scientific concurrency was zero. The 115 recovered model artifacts are distinct from new fits or runtime reuse.</p>
  <p><a href="b063r2.html" style="display:inline-block;padding:10px 15px;border-radius:7px;background:#17684f;color:white;font-weight:750;text-decoration:none">Open the latest comparisons and recovery status →</a></p>
  <p style="font-size:12px;color:#52675c;margin-bottom:0">The dated panels below remain preserved. Their earlier counts and execution labels do not supersede this latest review. Saved source cutoffs are shown throughout; this page makes no live-schedule or new-forecast claim.</p>
</section>
''' + END

def validate(payload):
    science, early, late, execution = (payload[k] for k in KEYS)
    if any(science[k] != 0 for k in ("new_fits", "new_issues", "promotions")):
        raise ValueError("Saved evidence review cannot acquire new science credit")
    if science["status"] != "SAVED_EVIDENCE_VERIFIED_NO_NEW_FITS_OR_ISSUES":
        raise ValueError("Unexpected scientific evidence status")
    expected = {(league, year, metric, target)
        for league in ("ncaam", "ncaaw") for year in (2025, 2026)
        for target, metrics in (("win", ("accuracy", "log_loss", "brier")), ("margin", ("mae", "rmse")), ("total", ("mae", "rmse")))
        for metric in metrics}
    actual = {(r["league"], r["season_end_year"], r["metric"], r["target"]) for r in science["historical_per_season_leaders"]}
    if actual != expected or len(science["historical_per_season_leaders"]) != len(expected):
        raise ValueError("Incomplete or duplicate historical season/target/metric coverage")
    if any(r.get("automatic_promotion") is not False for r in science["historical_per_season_leaders"]):
        raise ValueError("Historical research must not claim automatic promotion")
    if any(r.get("evaluation_mode") != "retrospective_reconstructed" or r.get("selection_or_promotion_authority") is not False for r in science["current_observed_replay_leaders"]):
        raise ValueError("Current replay cannot be relabeled original issuance or promotion")
    candidates = {(r["league"], r["season_end_year"], r["target"], r["public_model_id"]): r for r in science["historical_per_season_candidate_metrics"]}
    if len(candidates) != len(science["historical_per_season_candidate_metrics"]):
        raise ValueError("Duplicate candidate-season rows")
    for row in science["historical_per_season_leaders"]:
        for model in row["public_model_ids"]:
            candidate = candidates[(row["league"], row["season_end_year"], row["target"], model)]
            if candidate["games"] != row["games"] or abs(candidate["metrics"][row["metric"]] - row["value"]) > 1e-10:
                raise ValueError("Leader does not match an exact candidate-season result")
    if early["summary"]["selected_original_rows"] != 90 or early["summary"]["selected_original_games"] != 30:
        raise ValueError("Early original forecast population changed")
    if len(late["rows"]) != 46 or len(late["outcomes"]) != 8:
        raise ValueError("Late original forecast population changed")
    if {r["event_id"] for r in early["outcomes"]} & {r["event_id"] for r in late["outcomes"]}:
        raise ValueError("Original issue cohorts unexpectedly overlap")
    for row in late["rows"]:
        if row["original_actual"] is not None or not row["original_issued_at"] < row["original_cutoff_time"]:
            raise ValueError("Original issue chronology or actual field changed")
    owner = execution["latest_actual_owner"]
    if owner["release"] != "B063R2" or execution["continuation"]["release"] != "B064":
        raise ValueError("Latest actual R2 and prepared B064 must remain separate")
    if (owner["peak_observed_cpu_cores"] > 0 and owner["peak_scientific_workers"] == 0
            and not owner.get("probe_utilization_is_not_scientific_parallelism")):
        raise ValueError("Probe utilization cannot establish scientific parallelism")
    if owner["status"] != "FAILED_PARTIAL_WORK_PRESERVED" or owner["new_verified_scientific_fits"] != 0 or owner["peak_scientific_workers"] != 0:
        raise ValueError("B063R2 actual return is misrepresented")
    if execution["continuation"]["status"] != "PREPARED_OWNER_EXECUTION_PENDING" or execution["continuation"]["owner_parallelism_proven"]:
        raise ValueError("Prepared B064 must not be presented as executed")
    return payload

def load_payload():
    payload = {}
    for key, (name, expected) in zip(KEYS, SOURCE_PINS.items()):
        body = (HERE / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Public source identity mismatch: " + name)
        payload[key] = json.loads(body)
    payload["source_pins"] = SOURCE_PINS
    return validate(payload)

def render_banner(html):
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)
    marker = "<main>"
    if html.count(marker) != 1:
        raise ValueError("Expected one NCAA main element")
    return html.replace(marker, marker + BANNER, 1)

def render_page():
    payload = load_payload()
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    return (HERE / "b063r2_dashboard.html.tmpl").read_text().replace("__B063R2_DATA__", raw)

def evidence_outputs():
    result = {ROOT / "docs/ncaa/b063r2.html": render_page()}
    for name in SOURCE_PINS:
        result[ROOT / "docs/ncaa/data" / name] = (HERE / name).read_text()
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = evidence_outputs()
    landing = ROOT / "docs/ncaa/index.html"
    output[landing] = render_banner(landing.read_text())
    receipts = []
    for path, rendered in output.items():
        if args.check:
            if path.read_text() != rendered:
                raise ValueError("Stale NCAA R2 generated page: " + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered)
        receipts.append({"path": str(path.relative_to(ROOT)), "bytes": len(rendered.encode()), "sha256": hashlib.sha256(rendered.encode()).hexdigest()})
    print(json.dumps({"status": "EXACT_GENERATION_VERIFIED" if args.check else "GENERATED", "outputs": receipts}, indent=2))

if __name__ == "__main__":
    main()

