"""Render the public NFL R18 aggregate review; never fit or rescore a model."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def number(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return "Gap"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite public number")
        return f"{value:,.{digits}f}".rstrip("0").rstrip(".")
    return esc(value)


def safe_json(value: Any) -> str:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


CSS = """
:root{color-scheme:light;--paper:#f5f5f0;--ink:#152629;--muted:#536469;--line:#d6dfda;--card:#fff;--green:#076953;--amber:#8a4e0c;--amber-bg:#fff2d9;--navy:#16383d}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--green);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}a:focus-visible,input:focus-visible,select:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #bd6f00;outline-offset:3px}
.skip{position:absolute;left:1rem;top:-5rem;background:white;padding:.6rem;z-index:9}.skip:focus{top:1rem}.shell{max-width:1420px;margin:auto;padding:0 3rem}header{background:var(--navy);color:white;padding:2rem 0 2.6rem}header a{color:#bce6d7}.topline{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-weight:650;font-size:.75rem;margin:2.5rem 0 .7rem;color:#bce6d7}h1{font-size:clamp(2rem,4vw,3.5rem);line-height:1.12;letter-spacing:-.035em;max-width:950px;margin:.6rem 0 1rem}header .intro{max-width:900px;color:#deebe8;font-size:1.05rem}.badge{display:inline-block;border:1px solid #b9d5cb;border-radius:2rem;padding:.25rem .8rem;font-size:.76rem;font-weight:700;letter-spacing:.04em}.stamp{font-size:.8rem;color:#c7d9d5}.summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;margin:1.7rem 0 2rem}.stat{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--green);padding:1rem 1.2rem;border-radius:5px}.stat strong{display:block;font-size:1.8rem;font-weight:650;line-height:1.3;font-variant-numeric:tabular-nums}.stat span{font-size:.82rem;color:var(--muted)}.notice{border-left:4px solid #b87923;background:var(--amber-bg);padding:1rem 1.25rem;margin:1.5rem 0;color:#633a0e}.notice p{margin:.2rem 0}.section{margin:2.4rem 0;background:var(--card);border:1px solid var(--line);padding:1.5rem;border-radius:6px}.section h2{font-size:1.45rem;margin:0 0 .5rem;letter-spacing:-.015em}.section h3{font-size:1rem;margin:1.5rem 0 .5rem}.sub{color:var(--muted);margin:.3rem 0 1.2rem;font-size:.9rem}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.3rem}.table-wrap{overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:4px}table{width:100%;border-collapse:collapse;font-size:.85rem;text-align:left}caption{text-align:left;padding:.7rem 1rem;font-weight:650;background:#f3f7f4}th{background:#eaf1ed;font-size:.74rem;letter-spacing:.035em;font-weight:700;white-space:nowrap}th,td{padding:.65rem .8rem;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fbfcfa}td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}td small{display:block;color:var(--muted);font-size:.73rem}.gap{color:var(--amber);font-weight:650}.filters{display:flex;gap:.8rem;flex-wrap:wrap;align-items:end;margin:1rem 0}.filters label{display:flex;flex-direction:column;gap:.25rem;font-size:.78rem;color:var(--muted)}input,select,button{font:inherit;color:var(--ink);border:1px solid #a8b9b0;border-radius:4px;background:#fff;padding:.5rem .65rem;min-height:40px;max-width:100%}.filters input{min-width:220px}.rowcount{font-size:.82rem;color:var(--muted);margin:.5rem 0}.metric-table{min-width:1080px}.metric-table td:first-child{font-weight:650}.metric-table td{max-width:250px}.muted{color:var(--muted)}.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere;font-size:.75rem}details{margin:1rem 0}summary{font-weight:650;cursor:pointer}ul{padding-left:1.25rem}li{margin:.5rem 0}.evidence-list{display:grid;grid-template-columns:1fr 1fr;gap:.8rem}.evidence-item{background:#f3f7f4;padding:.8rem;border:1px solid var(--line);border-radius:4px}.evidence-item strong{display:block;font-size:.82rem}footer{border-top:1px solid var(--line);padding:1.5rem 0 3rem;color:var(--muted);font-size:.8rem}.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}[hidden]{display:none!important}
.grid,.evidence-list{grid-template-columns:repeat(2,minmax(0,1fr))}.grid>*,.evidence-list>*,.filters label{min-width:0}.filters label{max-width:100%}.filters input,.filters select{min-width:0}h1,h2,h3,p,li,summary{overflow-wrap:anywhere}
@media(max-width:900px){.shell{padding:0 1.2rem}.summary{grid-template-columns:repeat(2,minmax(0,1fr))}.grid,.evidence-list{grid-template-columns:minmax(0,1fr)}.section{padding:1rem}.topline{font-size:.85rem}}
@media(max-width:460px){.shell{padding:0 .85rem}header{padding:1.3rem 0 1.8rem}.eyebrow{margin-top:1.8rem}.summary{gap:.6rem}.stat{padding:.8rem}.stat strong{font-size:1.4rem}.filters label{width:100%}.filters input{min-width:0;width:100%}.filters select{width:100%}.section{margin:1.5rem 0}.badge{font-size:.7rem}}
@media print{header{background:white;color:black}header .intro,.stamp,.eyebrow{color:#333}.filters,.skip{display:none}.section{break-inside:avoid}.shell{padding:0}.table-wrap{overflow:visible}.metric-table{min-width:0;font-size:.65rem}th,td{padding:.3rem}}
"""

SCRIPT = """
(() => {
  const rows = [...document.querySelectorAll('#metrics-body tr')];
  const ids = ['metric-search', 'weight-filter', 'clock-filter', 'objective-filter'];
  const controls = ids.map(id => document.getElementById(id));
  const count = document.getElementById('visible-count');
  function update() {
    const [search, weight, clock, objective] = controls.map(x => x.value.toLowerCase());
    let visible = 0;
    rows.forEach(row => {
      const matches = (!search || row.textContent.toLowerCase().includes(search)) &&
        (!weight || row.dataset.weight.toLowerCase() === weight) &&
        (!clock || row.dataset.clock.toLowerCase() === clock) &&
        (!objective || row.dataset.objective.toLowerCase() === objective);
      row.hidden = !matches;
      if (matches) visible++;
    });
    count.textContent = `${visible.toLocaleString()} of ${rows.length.toLocaleString()} saved nomination rows shown`;
    document.getElementById('no-results').hidden = visible !== 0;
  }
  controls.forEach(control => { control.addEventListener('input', update); control.addEventListener('change', update); });
  update();
})();
"""


def table(headers: list[str], rows: list[list[Any]], *, caption: str = "") -> str:
    title = f"<caption>{esc(caption)}</caption>" if caption else ""
    heads = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(c) if c is not None else '<span class=gap>Gap</span>'}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap" tabindex="0"><table>{title}<thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>'


def read_json(name: str) -> Any:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def build() -> str:
    return render(read_json("status.json"), read_json("selected_metrics.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the committed page with its public inputs.")
    args = parser.parse_args()
    expected = build()
    destination = HERE / "index.html"
    if args.check:
        if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
            raise SystemExit("Public review is stale; rerun build_review.py")
        print("PASS: deterministic public review matches both JSON inputs")
    else:
        destination.write_text(expected, encoding="utf-8")
        print("Rendered public aggregate review")


# The explicit input adapters and render function below are the publication boundary.

FORBIDDEN_KEYS = {
    "features", "feature_columns", "feature_transforms", "recipe", "recipe_id",
    "model_id", "champion_id", "model_weights", "calibration_parameters",
    "credentials", "account_id", "private_path", "source_output", "current_output",
    "s3_uri", "raw_feed", "raw_quotes", "forecast_grid", "owner_package",
}


def validate_public(value: Any) -> None:
    """Refuse accidental private fields rather than hiding them in the HTML."""
    if isinstance(value, dict):
        forbidden = FORBIDDEN_KEYS.intersection(value)
        if forbidden:
            raise ValueError("Private field in public aggregate input: " + sorted(forbidden)[0])
        for item in value.values():
            validate_public(item)
    elif isinstance(value, list):
        for item in value:
            validate_public(item)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite public number")
    elif isinstance(value, str):
        if any(token in value for token in ("s3://", "arn:aws:", "/home/", "/workspace/")):
            raise ValueError("Private infrastructure address in public aggregate input")
        if re.search(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", value):
            raise ValueError("Credential-shaped value in public aggregate input")


def options(values: list[str], selected: str = "") -> str:
    return '<option value="">All</option>' + "".join(
        f'<option value="{esc(v)}"{" selected" if v == selected else ""}>{esc(v)}</option>'
        for v in sorted(set(values))
    )


def metric_cell(value: Any, games: Any) -> str:
    display = '<span class="gap">Gap</span>' if value is None else number(value, 6)
    denominator = "not available" if games is None else number(games)
    return f'<td class="num">{display}<small>n = {denominator}</small></td>'


def metric_table(rows: list[dict[str, Any]]) -> str:
    weights = [f"{r['weight_2024']}/{r['weight_2025']}" for r in rows]
    clocks = [r["clock_group"] for r in rows]
    # Public clock labels are prose; select by the retained information clock.
    default_clock = next((r["clock_group"] for r in rows
                          if re.search(r"(?<!\d)60(?!\d)", r.get("information_clock", ""))), "")
    controls = f'''<div class="filters">
<label>Search nominations<input id="metric-search" type="search" placeholder="Role, objective or evidence"></label>
<label>Validation ratio<select id="weight-filter">{options(weights, '50/50')}</select></label>
<label>Clock group<select id="clock-filter">{options(clocks, default_clock)}</select></label>
<label>Objective<select id="objective-filter">{options([r['objective'] for r in rows])}</select></label>
</div><p id="visible-count" class="rowcount" role="status" aria-live="polite">{len(rows):,} saved nomination rows</p>'''
    body = []
    for r in rows:
        weight = f"{r['weight_2024']}/{r['weight_2025']}"
        cohort = "; ".join(f"{year}: {r.get('ids_' + year) or 'gap'}" for year in ("2024", "2025", "2026"))
        qualification = r.get("test_status", "Gap")
        body.append(f'''<tr data-weight="{esc(weight)}" data-clock="{esc(r['clock_group'])}" data-objective="{esc(r['objective'])}">
<td>{esc(r['role_alias'])}<small>{esc(r.get('model_family', 'Unspecified family'))}</small></td>
<td>{esc(r['objective'])}<small>{esc(r['clock_group'])} · {esc(r.get('information_clock', ''))}</small></td>
<td class="num">{esc(weight)}<small>{'Primary' if r.get('primary') else 'Sensitivity'}</small></td>
{metric_cell(r.get('season_2024'), r.get('games_2024'))}
{metric_cell(r.get('season_2025'), r.get('games_2025'))}
{metric_cell(r.get('test_2026'), r.get('games_2026'))}
<td class="num">{number(r.get('validation_score'), 6)}<small>rank {number(r.get('rank'))} · {number(r.get('validation_coleader_count'))} co-leader(s)</small></td>
<td>{esc(qualification)}<small>{esc(r.get('evidence', ''))}</small><details><summary>Cohort identities</summary><span class="mono">{esc(cohort)}</span></details></td></tr>''')
    headers = ["Selected role", "Objective / clock", "2024:2025", "2024 validation", "2025 validation", "2026 exposed test", "Validation selection", "Qualification"]
    return controls + '<div class="table-wrap" tabindex="0" aria-label="Scrollable nomination table"><table class="metric-table"><thead><tr>' + "".join(f'<th scope="col">{esc(h)}</th>' for h in headers) + '</tr></thead><tbody id="metrics-body">' + "".join(body) + '</tbody></table></div><p id="no-results" class="notice" hidden>No saved nomination matches these filters.</p>'


def historical_accounting(status: dict[str, Any]) -> str:
    accounting = status.get("failure_accounting")
    incident = status.get("prior_r17_incident")
    if not accounting or not incident:
        return ""
    labels = [
        ("Attributable builds", "attributable_builds"),
        ("Named revisions", "named_revisions"),
        ("Recorded owner entries", "recorded_owner_entries"),
        ("Verified partial returns", "verified_partial_returns"),
        ("Identified owner recovery or completion failures", "identified_owner_recovery_or_completion_failures"),
        ("Pre-owner launch failures", "pre_owner_launch_failures"),
        ("Scoped attempts", "scoped_attempts"),
        ("Full V13 returns", "full_v13_returns"),
        ("Recorded scientific estimator calls across the ledger", "recorded_scientific_estimator_calls"),
    ]
    ledger = table(["Accounting category", "Recorded count"],
                   [[label, number(accounting.get(key))] for label, key in labels])
    return f'''<section class="section" id="history"><h2>Historical work and failure accounting</h2>
<p class="sub">{esc(accounting['scope'])}. Builds and named revisions are separate from execution attempts and failures. A verified partial return preserves work; it does not establish a full V13 completion.</p>
<details><summary>Reconciled counts and prior R17 resource incident</summary>{ledger}
<h3>Prior R17 incident: {esc(incident['status'])}</h3><p>The recorded cause was <strong>{esc(incident['cause'])}</strong> after {number(incident['wait_seconds_each'])}-second waits. I/O PSI full pressure was {number(incident['current_io_full_percent'], 2)}% in the current sample and {number(incident['ten_second_io_full_percent'], 2)}% over ten seconds.</p>
<p>Exclusive pressure origin established: <strong>{number(incident['exclusive_origin_established'])}</strong>. Forecast corruption established: <strong>{number(incident['forecast_corruption_established'])}</strong>. The pressure receipt alone cannot attribute the load to another workload.</p>
<p>Earlier R17 fitting recorded {number(incident['overlapping_fit_pids'])} overlapping fit PIDs and a peak of {number(incident['peak_fit_core_equivalents'], 2)} logical core equivalents. These fitting measurements do not describe later resource admission or prove sustained occupancy for R18.</p></details></section>'''


def render(status: dict[str, Any], metrics: dict[str, Any]) -> str:
    validate_public(status)
    validate_public(metrics)
    if status.get("owner") != "NFL" or status.get("revision") != "N127R18":
        raise ValueError("This renderer is scoped to NFL N127R18")
    if metrics.get("status") != "VALIDATION_NOMINATIONS_PARTIAL_ACCEPTANCE":
        raise ValueError("A different scientific qualification requires a reviewed renderer")
    if metrics.get("prior_test_exposure") is not True or status["science"].get("prior_test_exposure") is not True:
        raise ValueError("Prior test exposure must remain disclosed")
    if status["science"].get("weights_used_in_training") is not False:
        raise ValueError("Validation ratios must not be training weights")
    run = status["owner_run"]
    if run.get("status") != "PARTIAL_RESUMABLE" or run.get("return_integrity") != "VERIFIED" or run.get("pointer_readback") is not True:
        raise ValueError("A verified partial owner return and pointer read-back are required")
    if status.get("publication", {}).get("hosted_deployment") is not False:
        raise ValueError("A hosted deployment requires a separate reviewed publication receipt")
    science = status["science"]
    rows = metrics["rows"]
    counts = status["stage_counts"]
    if any(r.get("primary") != (r.get("weight_2024") == 50 and r.get("weight_2025") == 50) for r in rows):
        raise ValueError("Primary nomination flag differs from the declared 50/50 ratio")
    digest = hashlib.sha256(safe_json(status).encode()).hexdigest()
    metrics_digest = hashlib.sha256(safe_json(metrics).encode()).hexdigest()
    stages = table(["Stage", "Disposition", "Recorded seconds"], [[s["name"].replace("_", " "), s["status"], number(s.get("elapsed_seconds"), 2)] for s in status["stages"]], caption="Current invocation stage ledger")
    sources = []
    for source in status["source_admissions"]:
        reasons = source.get("reasons", [])
        if not isinstance(reasons, list):
            reasons = [reasons]
        coverage = table(["Season", "Horizon", "Full games", "Full team rows", "Retained source rows", "Retained objects for year", "Admissible team rows", "Both-team admissible games"], [[r["season"], f"T−{r['horizon_minutes']}", number(r.get("full_games")), number(r.get("full_team_rows")), number(r.get("retained_source_rows")), r.get("retained_source_objects_for_year"), number(r.get("admissible_team_rows")), number(r.get("both_team_admissible_games"))] for r in source.get("coverage", [])])
        sources.append(f'<h3>{esc(source["source"].replace("_", " ").title())} — {esc(source["status"].replace("_", " ").title())}</h3><ul>' + "".join(f"<li>{esc(str(r).replace('_', ' ').capitalize())}</li>" for r in reasons) + f'</ul><details><summary>Year and decision-horizon coverage</summary>{coverage}</details>')
    benchmarks = table(["Dataset", "Shape", "CSV read", "Parquet read", "CSV RSS", "Parquet RSS"], [[b["dataset"], f"{b['rows']:,} × {b['columns']}", f"{number(b['csv_ms'], 3)} ms", f"{number(b['parquet_ms'], 3)} ms", f"{number(b['csv_rss_mib'], 2)} MiB", f"{number(b['parquet_rss_mib'], 2)} MiB"] for b in status["parquet_benchmarks"]], caption="Bounded full-column reads; reader RSS includes runtime")
    evidence = "".join(f'<div class="evidence-item"><strong>{esc(e["id"].replace("_", " "))}</strong><span class="mono">{esc(e["sha256"])}</span></div>' for e in status["evidence"])
    remaining = "".join(f"<li>{esc(item)}</li>" for item in status["remaining_work"])
    prep = status["preparation"]
    stage_summary = " · ".join(f"{number(counts.get(k, 0))} {k.lower()}" for k in ("COMPLETED", "REUSED", "PARTIAL", "DEFERRED"))
    full = science["full_games_by_season"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="NFL N127R18 verified partial return, saved validation nominations, source gaps and recovery evidence."><title>NFL N127R18 · Verified partial return</title><style>{CSS}</style></head>
<body><a class="skip" href="#main">Skip to evidence</a>
<header><div class="shell"><div class="topline"><a href="../README.md">Sports Edge Lab / NFL</a><span class="badge">{esc(run['status'])}</span></div><p class="eyebrow">NFL · N127R18 · Owner research review</p><h1>Verified return.<br>Research remains partial.</h1><p class="intro">Completed work survived recovery. The latest owner run resumed saved model groups and produced a verified partial return. This page separates that execution from preparation tests, historical nominations, source gaps and publication status.</p><p class="stamp">Evidence observed: {esc(status['evidence_as_of_utc'])}</p></div></header>
<main id="main" class="shell">
<div class="summary"><div class="stat"><strong>{number(run['new_estimator_fits'])}</strong><span>New estimator fits in this invocation</span></div><div class="stat"><strong>{number(run['reused_fold_groups'])}</strong><span>Completed fold groups reused</span></div><div class="stat"><strong>{number(run['requested_workers'])}</strong><span>Requested worker ceiling · not measured occupancy</span></div><div class="stat"><strong>{number(full.get('2026', full.get(2026)))}</strong><span>Completed 2026 games in the recorded full population</span></div></div>
<div class="notice"><p><strong>Validation nominations, not completed scientific acceptance.</strong> The 2026 test results were previously inspected. Missing test coverage stays missing, and no production promotion or prospective performance claim is established.</p><p>Annual validation uses 2024 and 2025. The declared primary ratio is 50/50; sensitivity ratios change selection scores only. They do not refit estimators or weight training rows.</p></div>
<section class="section" id="execution"><h2>What the owner run completed</h2><p class="sub">{esc(stage_summary)}. Reused work is counted separately from newly completed work.</p>
<div class="grid"><div><h3>Return and recovery</h3><p>Return integrity: <strong>{esc(run['return_integrity'])}</strong>. Pointer read-back: <strong>{number(run['pointer_readback'])}</strong>. The private return contains {number(run['return_parts'])} ordered parts totaling {number(run['return_bytes'])} bytes.</p><p class="mono">Logical return SHA-256: {esc(run['return_sha256'])}</p><p>Scientific promotion count: <strong>{number(run['production_promotions'])}</strong>. Sustained occupancy claimed: <strong>{number(run['sustained_occupancy_claimed'])}</strong>.</p></div><div><h3>Time, compute and scope</h3><p>Recorded execution before sealing: <strong>{number(run['elapsed_seconds_before_seal'] / 60, 2)} minutes</strong>. Recorded compute estimate before sealing: <strong>${number(run['compute_estimate_before_seal_usd'], 4)}</strong>.</p><p class="sub">These measures exclude the subsequent sealing interval and are not an invoice. A requested worker ceiling does not establish utilization. No extra fitting is inferred from report generation or checkpoint reuse.</p></div></div><details><summary>Full stage dispositions and recorded durations</summary>{stages}</details></section>
{historical_accounting(status)}
<section class="section" id="nominations"><h2>Saved validation nominations</h2><p class="sub">Full recorded populations: {number(full.get('2024', full.get(2024)))} games in 2024; {number(full.get('2025', full.get(2025)))} in 2025; {number(full.get('2026', full.get(2026)))} completed games in 2026. Individual metric denominators and exact cohort identities remain separate. Compare rows only when objective, information clock and cohort agree.</p><p>Values below are saved same-candidate annual metrics. Display precision does not rescore or select models. Role aliases replace private model identifiers. Ties, incomplete test populations and qualifications remain visible.</p>{metric_table(rows)}<noscript><p class="notice">All saved rows remain visible without JavaScript. Interactive filters require JavaScript.</p></noscript></section>
<section class="section" id="sources"><h2>Historical source admission remains incomplete</h2><p class="sub">These results concern the three proposed historical feature groups. They do not mean that every NFL input or every historical market source is inadmissible. Retained objects or rows do not by themselves establish predecision availability, rights, or an authenticated modeling matrix.</p>{''.join(sources)}<p>Current source captures retain their actual availability times and do not retroactively qualify historical observations.</p></section>
<section class="section" id="engineering"><h2>Engineering preparation, reported separately</h2><p>The preceding exact-package native qualification passed <strong>{number(prep['tests_passed'])} tests</strong>, with {number(prep['tests_failed'])} failures, {number(prep['tests_errors'])} errors and {number(prep['tests_skipped'])} skips. These are engineering tests, not new NFL model fits or proof of complete scientific acceptance.</p><h3>Local typed-storage measurements</h3>{benchmarks}<p class="sub">The larger schedule read improved; the small calendar read regressed. Both readers used more memory with Parquet. Typed equivalence was verified for these conversions. The measurements do not establish whole-campaign speedup or completion of every legacy migration.</p></section>
<section class="section" id="remaining"><h2>Remaining work</h2><ul>{remaining}</ul></section>
<section class="section" id="provenance"><h2>Evidence and publication</h2><p><strong>GitHub source update.</strong> This page and its sanitized aggregate inputs are repository artifacts. A hosted website deployment is a separate event and is not claimed here. The owner-side private dashboard receipt does not constitute a public deployment receipt.</p><p><a href="status.json">Public status JSON</a> · <a href="selected_metrics.json">Saved nomination metrics</a> · <a href="README.md">Scope and verification</a></p><details><summary>Private evidence references</summary><p class="sub">Opaque SHA-256 references bind the reported evidence. They are not links to publicly downloadable private receipts.</p><div class="evidence-list">{evidence}</div></details><p class="mono">Canonical public status data digest: {digest}<br>Canonical public nomination data digest: {metrics_digest}</p></section>
</main><footer><div class="shell">Sports Edge Lab · NFL only · Research review. Original issues, historical reconstructions and prior test exposure retain their distinct evidence classes. This publication does not refresh providers, launch research or promote a model.</div></footer><script>{SCRIPT}</script></body></html>
'''


if __name__ == "__main__":
    main()
