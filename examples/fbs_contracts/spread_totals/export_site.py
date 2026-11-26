"""Export an exact Git commit's public FBS tree and Spread & Totals homepage.

All historical FBS routes remain. No other owner's files, private owner package,
provider cache, model state or credentials are read. This does not deploy a Site.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import posixpath
import re
import struct
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPO = "https://github.com/alvaromendizabal/sports-edge-lab"
ALLOWED = {".html", ".css", ".js", ".json", ".csv", ".md", ".gz", ".svg", ".png", ".jpg", ".webp"}
BOARD = "docs/fbs/spread-totals/"


def require(value, message):
    if not value:
        raise ValueError(message)


def committed(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def export(commit, output):
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "full exact source commit required")
    subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=ROOT, check=True)
    output = Path(output).resolve()
    require(not output.exists() or not any(output.iterdir()), "export destination must be empty")
    for name in ("build_board.py", "board.html.in", "export_site.py", "render_phone_cards.py"):
        rel = "examples/fbs_contracts/spread_totals/" + name
        require(committed(commit, rel) == (ROOT / rel).read_bytes(), "helper differs from exact commit: " + rel)
    spec = importlib.util.spec_from_file_location("fbs_spread_totals_exact_export", HERE / "build_board.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    data_raw = committed(commit, BOARD + "board.json")
    data = json.loads(data_raw)
    body = committed(commit, BOARD + "index.html")
    require(builder.build(data).encode() == body, "board differs from exact committed public data")
    science = {k: v for k, v in data.items() if k != "graphics"}
    digest = hashlib.sha256(json.dumps(science, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if data.get("graphics"):
        require(data["graphics"]["science_sha256"] == digest, "phone graphics refer to a different scientific snapshot")
        for item in data["graphics"]["pages"]:
            require(re.fullmatch(r"graphics/[a-z0-9_]+\.png", item["file"]), "invalid graphic path")
            raw = committed(commit, BOARD + item["file"])
            require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "graphic bytes changed")
            require(raw[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", raw[16:24]) == (1290, 2796),
                    "phone graphic dimensions changed")
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit, "docs/fbs"], cwd=ROOT, text=True).splitlines()
    require(names and all(n.startswith("docs/fbs/") for n in names), "FBS public tree missing")
    require(all(Path(n).suffix in ALLOWED or Path(n).name == ".nojekyll" for n in names), "unreviewed public file type")
    sources = set(names)

    def link(target, source):
        parsed = urlsplit(html.unescape(target))
        if parsed.scheme or parsed.netloc:
            return target.replace(REPO + "/tree/main/", REPO + "/tree/" + commit + "/")
        if not parsed.path:
            return target
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), parsed.path))
        if resolved in sources:
            return target
        require(not resolved.startswith(("../", "/")), "navigation escaped repository")
        subprocess.run(["git", "cat-file", "-e", f"{commit}:{resolved}"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        return REPO + "/blob/" + commit + "/" + resolved + ("#" + parsed.fragment if parsed.fragment else "")

    output.mkdir(parents=True, exist_ok=True)
    records = {}

    def write(name, raw, source):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        records[name] = {"name": name, "source_path": source, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    for source in names:
        name = source.removeprefix("docs/fbs/")
        raw = committed(commit, source)
        if name.endswith(".html") and source != BOARD + "index.html":
            raw = re.sub(r'href="([^"]+)"', lambda m: 'href="' + link(m.group(1), source) + '"', raw.decode()).encode()
        write(name, raw, source)
    previous = (output / "index.html").read_bytes()
    write("retained-index-before-spread-totals.html", previous, "docs/fbs/index.html")
    # Mirror only the exact new page's relative assets, avoiding source rewriting.
    for source in names:
        if source.startswith(BOARD) and (source.endswith("board.json") or "/graphics/" in source):
            relative = source.removeprefix(BOARD)
            raw = committed(commit, source)
            require(relative not in records or records[relative]["sha256"] == hashlib.sha256(raw).hexdigest(),
                    "homepage asset would overwrite an unrelated FBS asset")
            write(relative, raw, source)
    write("index.html", body, BOARD + "index.html")
    receipt = {"schema": "fbs.spread-totals.exact-commit-static-export.v1", "source_commit_sha": commit,
               "canonical_repository": REPO, "primary_dashboard_source": BOARD + "index.html",
               "previous_homepage_retained_at": "retained-index-before-spread-totals.html",
               "publication_status": "STATIC_EXPORT_VERIFIED_DEPLOYMENT_NOT_PERFORMED",
               "source_json_sha256": hashlib.sha256(data_raw).hexdigest(), "science_sha256": digest,
               "release": data["release"], "clocks": data["clocks"], "population": data["population"],
               "public_files": [records[n] for n in sorted(records)], "owner_runs_started": 0,
               "new_model_fits": 0, "new_provider_calls": 0, "production_model_promoted": False}
    (output / "published-snapshot.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    for item in records.values():
        raw = (output / item["name"]).read_bytes()
        require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "export readback mismatch")
    return {"status": "VERIFIED_STATIC_EXPORT_PREPARED", "source_commit": commit, "public_assets": len(records),
            "output": str(output), "new_model_fits": 0, "new_provider_calls": 0, "website_deployed": False,
            "other_owner_files_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.commit, args.output), sort_keys=True))
