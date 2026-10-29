"""Generate a standalone NBA review from the sanitized aggregate receipt."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/evidence/2026-10-29-nba-b009-audit.json"
OUTPUT = ROOT / "docs/nba/index.html"


def validate(data):
    if data.get("schema") != "public.nba.audit.v1" or data.get("league") != "nba":
        raise ValueError("NBA aggregate evidence required")
    if data.get("evidence_kind") != "sanitized_authenticated_owner_aggregates":
        raise ValueError("actual aggregates and invented examples must remain separate")
    if data.get("owner_release") != "B009" or data.get("owner_execution_completed") is not True:
        raise ValueError("authenticated B009 execution required")
    if data.get("owner_status") != "SUCCESS_RESEARCH_WITH_REPORTED_GAPS":
        raise ValueError("B009 reported gaps must remain explicit")
    counts = [data["new_real_nba_units"], data["lifetime_nba_units"], data["combined_basketball_units"]]
    counts += [row["new_unique_units"] for row in data["nba_lineage"]]
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("nonnegative integer unit counts required")
    lineage = data["nba_lineage"]
    if len({row["release"] for row in lineage}) != len(lineage):
        raise ValueError("duplicate release would double-count native units")
    if sum(row["new_unique_units"] for row in lineage) != data["lifetime_nba_units"]:
        raise ValueError("NBA lifetime count differs from unique lineage")
    if [row["new_unique_units"] for row in lineage if row["release"] == "B009"] != [data["new_real_nba_units"]]:
        raise ValueError("B009 new count differs from its lineage contribution")
    if data["combined_basketball_units"] <= data["lifetime_nba_units"]:
        raise ValueError("combined basketball and NBA scopes must remain distinct")
    if data["nba_challenger_promoted"] is not False or data["qualified_market_advantage"] is not False:
        raise ValueError("no authenticated NBA promotion or MARKET edge")
    if data["B010_NBA_real_execution"] != "pending":
        raise ValueError("B010 preparation is not owner execution")
    if (data["current_season_selection_allowed"] is not False
            or data["historical_seasons_development_exposed"] is not True
            or data["historical_validation_seasons"] != [2025, 2026]):
        raise ValueError("historical exposure and current-season boundary changed")
    if data["original_B008_NBA_folds"] != "blocked_calibration_support_preserved":
        raise ValueError("B009 cannot retroactively complete the original B008 folds")
    if any(data[key] != 0 for key in ("new_paid_provider_requests", "new_paid_provider_credits",
                                    "public_example_real_model_fits", "public_example_network_requests")):
        raise ValueError("unestablished provider consumption or real public fitting")
    if data["portfolio_rating"] != {"before": 8.5, "after": 8.5,
        "kind": "editorial_assessment", "target_established": False}:
        raise ValueError("engineering publication does not establish a higher editorial rating")
    return data


def render(data):
    data = validate(data)
    segments = "".join(
        '<span class="segment s' + str(i) + '" style="flex:' + str(row["new_unique_units"]) + '" title="'
        + escape(row["release"]) + ': ' + str(row["new_unique_units"]) + ' unique units"></span>'
        for i, row in enumerate(data["nba_lineage"]))
    lineage_rows = "".join('<tr><th scope="row">' + escape(row["release"]) + '</th><td>'
                           + str(row["new_unique_units"]) + '</td></tr>' for row in data["nba_lineage"])
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Verified B009 NBA accounting and invented B010 branch contracts: controlled comparisons, information-time boundaries and exact checkpoint reuse.">
<title>NBA research and engineering | Sports Edge Lab</title>
<style>
:root{color-scheme:light;--ink:#172a3a;--muted:#526372;--line:#d6e0e7;--navy:#132e43;--teal:#007b77;--paper:#f5f8fa}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
a{color:#006b85;text-underline-offset:3px}a:focus-visible{outline:3px solid #db8a25;outline-offset:4px}
header{background:var(--navy);color:#fff}header>div,main,footer{max-width:1120px;margin:auto;padding:28px}
header a{color:#c9ecf0}nav{display:flex;flex-wrap:wrap;gap:20px;font-size:.9rem}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:.78rem;font-weight:750}
h1{font-size:clamp(2rem,4vw,3.1rem);line-height:1.15;max-width:850px;margin:18px 0}h2{font-size:1.5rem;line-height:1.3;margin-top:0}h3{font-size:1.05rem;margin:0 0 8px}
.lede{max-width:800px;color:#d7e5ee;font-size:1.08rem}.tag{display:inline-block;padding:3px 10px;border-radius:6px;background:#e7f5f1;color:#075e4b;font-size:.8rem;font-weight:700}.pending{background:#fff1d8;color:#775011}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 26px}.metric,.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px}.metric strong{display:block;font-size:2.1rem;line-height:1.2;margin:4px 0}.metric span{font-size:.86rem;color:var(--muted)}
.panel{margin-bottom:24px}.split{display:grid;grid-template-columns:1.2fr 1fr;gap:26px}.note{border-left:4px solid var(--teal);padding:10px 16px;background:#edf7f6}.muted{color:var(--muted)}
.matrix{border-collapse:separate;border-spacing:8px;width:100%;table-layout:fixed}.matrix th{text-align:left;font-size:.86rem}.matrix td{vertical-align:top;background:#edf5f8;border-radius:8px;padding:16px}.matrix strong{display:block}.matrix small{display:block;color:var(--muted);margin-top:8px}
.bar{display:flex;min-height:28px;border-radius:9px;overflow:hidden;margin:18px 0}.segment{min-width:0}.s0{background:#24465e}.s1{background:#367b94}.s2{background:#876329}.s3{background:#007b77}
.data{width:100%;border-collapse:collapse}.data th,.data td{padding:8px;border-bottom:1px solid var(--line);text-align:left}.data th{font-weight:650}.contracts{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.contract{border-top:3px solid var(--teal);padding-top:12px}.contract p{margin:0}.small{font-size:.86rem}
code{background:#eaf0f4;border-radius:4px;padding:2px 5px;overflow-wrap:anywhere}footer{color:var(--muted);font-size:.85rem;padding-top:0}
@media(max-width:760px){header>div,main,footer{padding:20px}.metrics{grid-template-columns:repeat(2,1fr)}.split,.contracts{grid-template-columns:1fr}.matrix{border-spacing:4px;font-size:.85rem}.matrix td{padding:10px}.matrix th{font-size:.77rem}.panel{padding:16px}}
</style></head><body>
<header><div><nav aria-label="Project navigation"><a href="../../README.md">Sports Edge Lab</a><a href="../NBA_RESEARCH_CARD.md">Experiment, model &amp; source card</a><a href="../../examples/nba_branch/README.md">Run the invented example</a><a href="../basketball/index.html">Preserved basketball evidence</a></nav>
<p class="eyebrow">NBA / Research &amp; engineering</p><h1>Controlled comparisons.<br>Verifiable progress.</h1>
<p class="lede">B009 completed a separately registered NBA experiment. The next NBA branch makes feature changes and training-window changes independently visible, preserves exact checkpoints, and keeps source timing attached to every admitted observation.</p>
<p><span class="tag">B009 completed with reported gaps</span> <span class="tag pending">B010 real execution pending</span></p></div></header>
<main><section class="metrics" aria-label="Verified accounting scopes">
<div class="metric"><span>B009 new NBA units</span><strong>''' + str(data["new_real_nba_units"]) + '''</strong><span>Completed native estimator units</span></div>
<div class="metric"><span>Lifetime NBA units</span><strong>''' + str(data["lifetime_nba_units"]) + '''</strong><span>Unique units; predecessor aliases excluded</span></div>
<div class="metric"><span>Combined basketball units</span><strong>''' + str(data["combined_basketball_units"]) + '''</strong><span>Includes NCAA; not an NBA-only total</span></div>
<div class="metric"><span>NBA challengers promoted</span><strong>0</strong><span>No qualified MARKET advantage</span></div></section>
<section class="panel" aria-labelledby="matrix-title"><div class="split"><div><p class="eyebrow">Registered comparison</p><h2 id="matrix-title">Separate the feature effect from the window effect</h2><p>Changing both at once leaves the source of a gain unresolved. Four arms, each evaluated in the same ending-2025 and ending-2026 population, expose that distinction.</p><p class="note"><strong>Four arms × two seasons = eight registered jobs.</strong> This is a comparison plan, not eight completed fits. A research job may contain multiple native estimator units.</p><p class="muted small">Historical seasons are development-exposed. Current 2026–2027 outcomes cannot choose features, windows, calibration, ensembles or a champion.</p></div>
<div><table class="matrix"><caption>Primary B010 NBA study — real execution pending</caption><thead><tr><th scope="col">Feature representation</th><th scope="col">Original window</th><th scope="col">Revised window</th></tr></thead><tbody>
<tr><th scope="row">Incumbent features</th><td><strong>Control</strong><small>2025 + 2026</small></td><td><strong>Window contrast</strong><small>2025 + 2026</small></td></tr>
<tr><th scope="row">Candidate features</th><td><strong>Feature contrast</strong><small>2025 + 2026</small></td><td><strong>Joint change</strong><small>2025 + 2026</small></td></tr>
</tbody></table></div></div></section>
<section class="panel" aria-labelledby="lineage-title"><div class="split"><div><p class="eyebrow">Authenticated historical accounting</p><h2 id="lineage-title">85 NBA units, counted once</h2><div class="bar" aria-hidden="true">''' + segments + '''</div><p class="muted">A reused artifact keeps its original identity. Reopening or importing it does not add a new fit. B009's ten NBA units belong to its separate experiment; the original B008 support failures remain recorded.</p></div>
<div><table class="data"><caption>Unique NBA additions by release</caption><thead><tr><th scope="col">Release</th><th scope="col">New NBA units</th></tr></thead><tbody>''' + lineage_rows + '''</tbody><tfoot><tr><th scope="row">Lifetime NBA total</th><td>85</td></tr></tfoot></table><p class="small">Zero new paid provider requests or credits in B009. Completed research did not establish a MARKET edge.</p></div></div></section>
<section class="panel" aria-labelledby="contracts-title"><p class="eyebrow">Executable engineering example</p><h2 id="contracts-title">Four boundaries that survive a restart</h2><div class="contracts">
<article class="contract"><h3>Exact NBA identity</h3><p>Provider, native event ID, league and season remain explicit. A similarly named event in another league is rejected.</p></article>
<article class="contract"><h3>Information available at cutoff</h3><p>The exact source version must have been published and observed by the decision time. A later download cannot turn a late revision into pregame knowledge.</p></article>
<article class="contract"><h3>Completed means verifiable</h3><p>Only a complete receipt with matching context and artifact bytes counts. Interrupted work remains pending; accepted reentry adds no new unit.</p></article>
<article class="contract"><h3>Shared sources remain read-only</h3><p>Content hashes qualify reuse. NBA writes its own derived outputs. Cached bytes do not grant source rights, provider credit or permission to alter another branch.</p></article></div>
<p class="note"><strong>Every example input is invented.</strong> The public walkthrough makes zero model fits, network requests and provider charges. It does not prove private owner execution or implement an account-wide acquisition lease.</p>
<p><a href="../../examples/nba_branch/README.md">Run the standard-library example and negative tests</a> · <a href="../evidence/2026-10-29-nba-b009-audit.json">Inspect the sanitized aggregate receipt</a></p></section>
<section class="panel"><h2>What still has to be established</h2><p>B010 needs real owner execution, historical source eligibility, matched MARKET support and the existing promotion gates. Increased coverage alone is not better forecasting, and predictive scores do not establish executable profit.</p><p>The existing <a href="../basketball/index.html">235 basketball scorecards and 120 overlap specifications</a> remain intact. The editorial portfolio assessment stays <strong>8.5 → 8.5</strong>; the 9.9 target is not established by this engineering publication.</p></section>
</main><footer>Sports Edge Lab · NBA-only public review · Published ''' + escape(data["published_on"]) + '''. No individual forecasts, raw records, private model implementations or infrastructure identifiers are published here.</footer>
</body></html>
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    content = render(json.loads(EVIDENCE.read_text()))
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != content:
            raise SystemExit("NBA review does not match the committed evidence")
        print("NBA review matches sanitized evidence; B010 owner execution remains pending.")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content)


if __name__ == "__main__":
    main()
