"""Restore the saved B062 report bytes from committed, pinned public inputs.

This is a standard-library artifact reconstruction. It does not execute notebook
cells, fit a model, request provider data, or refresh the evidence. The saved
notebook retains its original execution metadata and outputs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


SCHEMA = "sel.ncaa.b062.saved_report_reconstruction.v1"
INTEGRITY_FILE = "B062_REPORT_INTEGRITY.json"
DATA_FILE = "B062_REPORT_DATA.json"
HTML_TEMPLATE = "B062_EVIDENCE_REPORT.template.html"
NOTEBOOK_TEMPLATE = "B062_EVIDENCE_REPORT.template.ipynb"
PLOTLY_TOKEN = "@@B062_SAVED_PLOTLY_JS@@"
EVIDENCE_TOKEN = "@@B062_EVIDENCE_JSON@@"
GAMES_TOKEN = "@@B062_EXISTING_CENSUS_RECORDS@@"
ASSIGNMENT_TOKEN = "@@B062_NOTEBOOK_DATA_ASSIGNMENT@@\n"


def fingerprint(body):
    return {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def require_pin(body, expected, label):
    if fingerprint(body) != {key: expected[key] for key in ("bytes", "sha256")}:
        raise ValueError(label + ": byte count or SHA-256 differs from the saved report inputs")
    return body


def canonical_notebook(notebook):
    return (json.dumps(notebook, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def compact_data(data):
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def extract_plotly(report, expected):
    matches = []
    for match in re.finditer(r"<script(?:\s[^>]*)?>(.*?)</script>", report, re.S):
        script = match.group(1)
        if fingerprint(script.encode("utf-8")) == expected:
            matches.append(script)
    if len(matches) != 1:
        raise ValueError("The existing B061 report must contain exactly one pinned Plotly runtime")
    return matches[0]


def _replace_once(text, token, replacement, label):
    if text.count(token) != 1:
        raise ValueError(label + ": expected exactly one reconstruction placeholder")
    return text.replace(token, replacement, 1)


def reconstruct(template_dir, base_report, census_path):
    """Return pinned HTML/notebook bytes without executing their contents."""
    template_dir, base_report, census_path = map(Path, (template_dir, base_report, census_path))
    integrity = json.loads((template_dir / INTEGRITY_FILE).read_bytes())
    if integrity.get("schema") != SCHEMA:
        raise ValueError("Unrecognized saved-report reconstruction schema")
    templates = {}
    for name in (DATA_FILE, HTML_TEMPLATE, NOTEBOOK_TEMPLATE):
        templates[name] = require_pin((template_dir / name).read_bytes(), integrity["templates"][name], name)
    census_bytes = require_pin(census_path.read_bytes(), integrity["upstream"]["census"], "Existing census")
    census = json.loads(census_bytes)
    records = census.get("records")
    if not isinstance(records, list) or len(records) != integrity["upstream"]["census"]["records"]:
        raise ValueError("Existing census record count differs from the saved report")
    plotly = extract_plotly(base_report.read_text(encoding="utf-8"), integrity["upstream"]["plotly"]["javascript"])
    data = json.loads(templates[DATA_FILE])
    if data.get("games") != GAMES_TOKEN:
        raise ValueError("The report data must reference the existing census")
    data["games"] = records
    data_json = compact_data(data)
    html = _replace_once(templates[HTML_TEMPLATE].decode("utf-8"), PLOTLY_TOKEN, plotly, "HTML Plotly")
    html = _replace_once(html, EVIDENCE_TOKEN, data_json.replace("<", "\\u003c"), "HTML data").encode("utf-8")

    notebook = json.loads(templates[NOTEBOOK_TEMPLATE])
    location = integrity["notebook_placeholders"]
    source = notebook["cells"][location["cell"]]["source"]
    if not isinstance(source, list) or source[location["source_line"]] != ASSIGNMENT_TOKEN:
        raise ValueError("The notebook data assignment placeholder has changed")
    source[location["source_line"]] = "DATA = json.loads(" + repr(data_json) + ")\n"
    output = notebook["cells"][location["cell"]]["outputs"][location["output"]]["data"]["text/html"]
    if not isinstance(output, list):
        raise ValueError("The saved notebook HTML output must retain its line representation")
    output_text = _replace_once("".join(output), PLOTLY_TOKEN, plotly, "Notebook Plotly")
    notebook["cells"][location["cell"]]["outputs"][location["output"]]["data"]["text/html"] = output_text.splitlines(keepends=True)
    rebuilt = {"B062_EVIDENCE_REPORT.html": html, "B062_EVIDENCE_REPORT.ipynb": canonical_notebook(notebook)}
    for name, body in rebuilt.items():
        require_pin(body, integrity["outputs"][name], "Reconstructed " + name)
    return rebuilt, integrity


def write_reports(rebuilt, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, body in rebuilt.items():
        path = output_dir / name
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=output_dir, prefix="." + name + ".", delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(body)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, path)
            require_pin(path.read_bytes(), fingerprint(body), "Saved " + name)
            written[name] = fingerprint(body)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--template-dir", type=Path, default=here)
    parser.add_argument("--repo-root", type=Path, default=here.parent.parent)
    parser.add_argument("--base-report", type=Path)
    parser.add_argument("--census", type=Path)
    parser.add_argument("--output-dir", type=Path, default=here)
    parser.add_argument("--verify-only", action="store_true", help="Check exact reconstructed bytes without writing reports")
    args = parser.parse_args(argv)
    base_report = args.base_report or args.repo_root / "examples/ncaa_review/B061_EVIDENCE_REPORT.html"
    census = args.census or args.repo_root / "examples/ncaa_review/data/ncaa_observed_games_b060.json"
    rebuilt, integrity = reconstruct(args.template_dir, base_report, census)
    outputs = {name: fingerprint(body) for name, body in rebuilt.items()}
    if not args.verify_only:
        outputs = write_reports(rebuilt, args.output_dir)
    print(json.dumps({"status": "EXACT_SAVED_REPORT_BYTES_VERIFIED", "written": not args.verify_only,
                      "notebook_executed": False, "new_model_fits": 0, "provider_requests": 0,
                      "source_evidence_refreshed": False, "outputs": outputs,
                      "saved_evidence_created_at": integrity["saved_evidence_created_at"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
