"""Publish a dated NFL mirror with separate prepared-continuation evidence.

No provider calls, model execution or site creation. The caller supplies the
existing site's static directory after the canonical public commit is reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPOSITORY = "https://github.com/alvaromendizabal/sports-edge-lab"
FIELDS = {
    "schema", "status", "revision", "as_of_utc", "new_owner_fits", "new_forecasts",
    "planned_native_cells", "automatic_promotion", "actual_orders", "prior_revision",
    "prior_owner_status", "prior_new_native_fits", "prior_point_target_rows",
    "prior_threshold_rows", "prior_owner_return_sha256",
    "independently_verified_fit_receipts", "independently_verified_new_bundles",
    "independently_verified_new_bundle_payloads", "independently_verified_direct_omissions",
    "model_bodies_independently_replayed", "planned_path_intervals_minutes",
    "new_path_analysis_completed", "prior_path_observations", "prior_path_contracts",
    "next_study", "limits",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_readiness(data):
    require(isinstance(data, dict) and set(data) == FIELDS, "Unexpected public fields")
    require(data["schema"] == "sports-edge-lab.nfl.readiness.n049.v1", "Unknown schema")
    require(data["status"] == "PREPARED_NOT_OWNER_EXECUTED" and data["revision"] == "N049",
            "Prepared status changed without a new evidence contract")
    for key in ("new_owner_fits", "new_forecasts", "actual_orders"):
        require(type(data[key]) is int and data[key] == 0, "Preparation cannot claim execution")
    for key in ("automatic_promotion", "model_bodies_independently_replayed",
                "new_path_analysis_completed"):
        require(data[key] is False, "Unsupported completion or promotion claim")
    require(data["planned_native_cells"] == 144, "Prepared scope differs")
    require(data["prior_revision"] == "N048" and
            data["prior_owner_status"] == "PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED",
            "Prior partial status changed")
    require(data["prior_new_native_fits"] == data["independently_verified_fit_receipts"] == 288,
            "Prior receipt count differs")
    require((data["prior_point_target_rows"], data["prior_threshold_rows"]) == (336, 78),
            "Prior forecast accounting differs")
    require((data["independently_verified_new_bundles"],
             data["independently_verified_new_bundle_payloads"],
             data["independently_verified_direct_omissions"]) == (26, 15634, 6),
            "Independent audit scope differs")
    require(data["prior_owner_return_sha256"] ==
            "a1dfad6f9a466fb721e01d1d5904146e81708c5bcab7df25b69b1bb7718bfda4",
            "Prior owner identity differs")
    require((data["prior_path_observations"], data["prior_path_contracts"]) == (172373, 936),
            "Prior path acquisition differs")
    require(data["planned_path_intervals_minutes"] == [1, 3, 5, 10], "Path windows differ")
    require(isinstance(data["limits"], list) and len(data["limits"]) >= 6 and
            all(isinstance(x, str) and x for x in data["limits"]), "Limits are required")
    require(isinstance(data["next_study"], str) and data["next_study"], "Study scope is required")
    serialized = json.dumps(data)
    require(not re.search(r"s3://|arn:aws:|/home/|/workspace/|X-Amz-|AKIA[A-Z0-9]{16}", serialized),
            "Private locations or credentials are forbidden")
    return data


def render_readiness(data):
    validate_readiness(data)
    e = html.escape
    return f'''<section class="section" id="n049-readiness" aria-labelledby="n049-title">
<div class="section-head"><div><div class="eyebrow">Next continuation · N049</div>
<h2 id="n049-title">Prepared. Owner execution is pending.</h2></div>
<p class="fine">Readiness recorded {e(data['as_of_utc'])}. Latest verified owner evidence remains N048.</p></div>
<div class="facts compact-facts">
<article class="card fact"><div class="score">288</div><p>N048 fits verified</p></article>
<article class="card fact"><div class="score">144</div><p>N049 cells planned</p></article>
<article class="card fact"><div class="score">0</div><p>New N049 owner fits</p></article>
<article class="card fact"><div class="score">0</div><p>New N049 forecasts</p></article></div>
<p class="evidence-note"><strong>PREPARED_NOT_OWNER_EXECUTED.</strong> {e(data['next_study'])}
No improvement, forward injury-only issue, or promotion is claimed.</p>
<div class="snapshot-grid">
<article class="card"><h3>Keep timing local to each event</h3><p>A started game receives a temporal exclusion. Future games on the same official page retain their own source clocks and eligibility checks.</p></article>
<article class="card"><h3>Make missingness visible</h3><p>The historical injury-support gap and weak N048 result stay visible. Supported and unsupported cohorts need separate accounting before the next ablation is judged.</p></article>
<article class="card"><h3>Reuse exact completed work</h3><p>Identity and payload checks protect prior fits. Lower-oriented conditional probabilities must use the below-threshold mass; unknown settlement remains unscorable.</p></article>
</div>
<p class="scope-note" style="margin-top:16px">The next path study plans 1-, 3-, 5-, and 10-minute views of the retained {data['prior_path_observations']:,} observations across {data['prior_path_contracts']:,} contracts. Acquisition was retrospective; no new path result, contemporaneous possession, or executable fill is established.</p>
<p><a href="N049_RESEARCH_UPDATE.md">Read the N049 continuation review →</a> · <a href="readiness_n049.json">Inspect readiness evidence</a> · <a href="continuation_contracts_n049.py">Run the generic contracts</a></p>
</section>'''


def build_projection(source, readiness, commit, root=ROOT):
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "A full source commit is required")
    require('id="n049-readiness"' not in source, "Readiness was already inserted")
    marker = '<div class="reading-paths"'
    require(source.count(marker) == 1, "Expected canonical review marker is absent")
    page = source.replace(marker, render_readiness(readiness) + "\n" + marker, 1)
    rewritten = []

    def replace_link(match):
        target = match.group(1)
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith("#"):
            return match.group(0)
        if target == "'+esc(m.record_source)+'":
            destination = REPOSITORY + "/blob/" + commit + "/tracks/nfl/" + target
        elif parsed.path == "review.html":
            destination = "./" + ("#" + parsed.fragment if parsed.fragment else "")
        else:
            path = (root / "tracks/nfl" / unquote(parsed.path)).resolve()
            require(path.is_relative_to(root.resolve()) and path.is_file(),
                    "Unresolved public link: " + target)
            relative = path.relative_to(root.resolve()).as_posix()
            if path.suffix in {".json", ".csv"}:
                destination = "https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/" + commit + "/" + relative
            else:
                destination = REPOSITORY + "/blob/" + commit + "/" + relative
            if parsed.fragment:
                destination += "#" + parsed.fragment
        rewritten.append({"source": target, "destination": destination})
        return 'href="' + destination + '"'

    page = re.sub(r'href="([^"]+)"', replace_link, page)
    notice = f'''<section class="card" id="publication-provenance" aria-label="Publication provenance" style="margin:20px auto;max-width:1184px">
<h2 style="font-size:18px">A dated public evidence snapshot</h2>
<p class="fine">Canonical source: <a href="{REPOSITORY}/commit/{commit}">{commit}</a>.
This deployment preserves the N048 review and adds the separate prepared N049 continuation. Deployment does not refresh research, prices or forecasts. <a href="provenance.json">Inspect publication provenance</a>.</p></section>'''
    require(page.count("</footer>") == 1, "Expected canonical footer is absent")
    page = page.replace("</footer>", "</footer>" + notice, 1)
    return page, rewritten


def export(output, commit):
    source_path = HERE / "review.html"
    readiness_path = HERE / "readiness_n049.json"
    for path in (source_path, readiness_path, Path(__file__).resolve()):
        expected = subprocess.check_output(["git", "show", commit + ":" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        require(expected == path.read_bytes(), "Working tree differs from the pinned public commit")
    source = source_path.read_bytes()
    readiness_raw = readiness_path.read_bytes()
    readiness = json.loads(readiness_raw)
    page, rewritten = build_projection(source.decode(), readiness, commit)
    encoded = page.encode()
    provenance = {
        "role": "public_static_publication_mirror",
        "canonical_repository": REPOSITORY,
        "canonical_commit": commit,
        "canonical_path": "tracks/nfl/review.html",
        "canonical_source_sha256": sha(source), "canonical_source_bytes": len(source),
        "continuation_path": "tracks/nfl/readiness_n049.json",
        "continuation_sha256": sha(readiness_raw),
        "exporter_path": "tracks/nfl/export_site_n049.py",
        "hosted_html_sha256": sha(encoded), "hosted_html_bytes": len(encoded),
        "transformations": ["Add the separate prepared N049 readiness section", "Pin relative public links to the canonical commit", "Add dated source and deployment disclosure"],
        "research_state": "N048 partial; N049 prepared, not owner-executed",
        "licensed_raw_data": "not included", "private_model_bodies": "not included",
        "rewritten_links": rewritten,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_bytes(encoded)
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return {k: v for k, v in provenance.items() if k != "rewritten_links"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.output, args.commit), indent=2))
