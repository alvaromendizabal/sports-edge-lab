"""Render sanitized NCAA execution evidence without upgrading checkpoint status.

The public projection is deliberately separate from owner manifests and model
artifacts. A newer local failure can coexist with an older verified return.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
from html import escape
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "EXECUTION_STATUS_20261117.json"
SCHEMA = "sel.ncaa.public.execution_status.v1"
TOP_KEYS = {"schema", "owner", "observed_at", "publication", "latest_observed_attempt",
            "latest_verified_return", "attempts", "preserved_work", "throughput",
            "resume_contract", "science_contract", "source_coverage", "evidence"}
FORBIDDEN = re.compile(r"s3://|/home/|sagemaker-sports|arn:aws|AKIA[0-9A-Z]{16}|"
                       r"secret_access_key|api_key|access_token|\.pyz\b|circa", re.I)


def canonical(data):
    return json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"


def validate(data):
    """Fail closed on evidence-class confusion, inflated work, or private data."""
    if not isinstance(data, dict) or set(data) != TOP_KEYS:
        raise ValueError("Unexpected public execution fields")
    if data["schema"] != SCHEMA or data["owner"] != "NCAA basketball":
        raise ValueError("Wrong owner or schema")
    if FORBIDDEN.search(canonical(data)):
        raise ValueError("Private or out-of-owner content")
    datetime.fromisoformat(data["observed_at"])
    publication = data["publication"]
    if (publication["source_state"] not in {"PREPARED", "COMMITTED"}
            or publication["deployment_verified"] is not False
            or any(publication[k] != 0 for k in
                   ("owner_runs", "new_fits", "new_forecasts", "provider_requests"))):
        raise ValueError("Publication cannot claim owner research or deployment")
    observed = data["latest_observed_attempt"]
    verified = data["latest_verified_return"]
    if type(observed["return_published"]) is not bool:
        raise ValueError("Published state requires an explicit boolean")
    if (verified["integrity"] != "FULL_ARCHIVE_VERIFIED"
            or not re.fullmatch(r"[0-9a-f]{64}", verified["sha256"])
            or verified["payloads_verified"] <= 0):
        raise ValueError("Verified return needs full integrity evidence")
    if observed["return_published"] is False:
        if observed["evidence_class"] not in {"READ_ONLY_LOCAL_STATUS_CAPTURE", "VERIFIED_RECOVERY_EVIDENCE"}:
            raise ValueError("Unpublished attempt cannot be a verified owner return")
        if observed["release"] == verified["release"]:
            raise ValueError("Ambiguous published-versus-observed identity")
    elif (observed["release"] != verified["release"]
          or observed["evidence_class"] != "FULL_ARCHIVE_VERIFIED"):
        raise ValueError("Published state lacks matching verified return")
    rows = data["attempts"]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Missing or duplicate attempts")
    if rows[-1]["release"] != observed["release"]:
        raise ValueError("Latest attempt mismatch")
    for row in rows:
        if row["outcome"] not in {"FAILED_RESUMABLE", "RETURN_PACKAGING_FAILED_RESUMABLE"}:
            raise ValueError("Unexpected attempt outcome")
        for key in ("new_target_fits", "historical_checkpoint_reuses", "fresh_startup_tests", "reused_startup_tests"):
            value = row[key]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Work counters must be nonnegative or unobserved")
        if row["new_target_fits"] and row["phase"] != "RESEARCH":
            raise ValueError("Pre-fit failure cannot acquire fit credit")
    preserved = data["preserved_work"]
    if preserved["new_target_fits_in_audited_attempts"] != sum(r["new_target_fits"] or 0 for r in rows):
        raise ValueError("New-fit accounting does not reconcile")
    if preserved["duplicate_fits_proven"] is not False or preserved["all_repeated_work_eliminated"] is not False:
        raise ValueError("Unsupported repeat-work claim")
    t = data["throughput"]
    if (t["scientific_gate"] != "FAILED" or t["measurement_seconds"] < 180
            or t["reported_capacity_percent"] >= t["required_percent"]
            or t["newer_12_to_24_core_science_proven"] is not False):
        raise ValueError("Engineering cannot establish scientific throughput")
    s = data["science_contract"]
    if (s["validation_seasons"] != ["2024-25", "2025-26"]
            or s["test_season"] != "2026-27" or s["test_selection_weight"] != 0
            or s["primary_weights"] != [0.5, 0.5]
            or s["new_full_population_champion"] is not False
            or s["test_exposure_erased"] is not False):
        raise ValueError("Scientific selection contract changed")
    return deepcopy(data)


def load():
    return validate(json.loads(DATA.read_text()))


def render_current_banner(data=None):
    data = load() if data is None else validate(data)
    observed, verified = data["latest_observed_attempt"], data["latest_verified_return"]
    return (
        '<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" '
        'style="margin-bottom:28px;padding:20px;border:1px solid #ccd8ce;border-radius:12px;background:#eaf0e8">'
        '<p class="b063-eyebrow" style="margin-top:0">Execution and recovery · November 17, 2026 Pacific</p>'
        '<h2 id="v12-current-title">A newer failed attempt is separate from the last verified return</h2>'
        f'<p>The latest observed {escape(observed["release"])} attempt stopped with '
        f'<strong>{escape(observed["status_label"])}</strong>. The last fully verified published return remains '
        f'{escape(verified["release"])}. A failed package does not erase saved work, and an older pointer is not '
        'evidence that no newer execution occurred.</p>'
        '<p>The execution review separates new fits, recovered checkpoints, repeated startup checks, source work '
        'and unfinished tasks. No new full-population champion or successful 12–24-core NCAA science run is claimed.</p>'
        '<p><strong><a href="execution.html">Inspect the latest attempt and preserved work →</a></strong> · '
        '<a href="three_seasons.html">Preserved three-season comparison</a> · '
        '<a href="v12.html">Preserved V12 comparison</a></p></section>'
    )


def render(data=None):
    data = load() if data is None else validate(data)
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return (HERE / "execution_status.html.tmpl").read_text().replace("__EXECUTION_DATA__", encoded)


def status_outputs(existing=None):
    data = load()
    return {**(existing or {}), ROOT / "docs/ncaa/execution.html": render(data),
            ROOT / "docs/ncaa/execution_status.json": canonical(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = []
    for path, text in status_outputs().items():
        if args.check:
            if not path.is_file() or path.read_text() != text:
                raise SystemExit("Stale execution page: " + str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        results.append({"path": str(path.relative_to(ROOT)), "bytes": len(text.encode()),
                        "sha256": hashlib.sha256(text.encode()).hexdigest()})
    print(json.dumps({"status": "EXACT_GENERATION_VERIFIED" if args.check else "GENERATED", "files": results}))


if __name__ == "__main__":
    main()
