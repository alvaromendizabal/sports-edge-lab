"""Build the public FBS evidence page from aggregate facts and invented execution."""
import argparse
from dataclasses import replace
import html
import json
from pathlib import Path
import tempfile
from .core import run_demo
from .matched_cohort import invented_comparison, score_matched
from .public_release import release

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/fbs/index.html'


def evidence():
    data = json.loads((ROOT / 'docs/fbs/evidence.json').read_text())
    old = data['last_completed_science']
    plan = data['prepared_program']
    assert data['latest_owner_attempt']['new_real_fits'] == 0
    assert old['fbs_recent_completed_fits'] == 18 and old['fbs_recent_fit_attempts'] == 19
    assert plan['total_registered_fit_units'] == plan['core_registered_fit_units'] + plan['cross_fitted_pool_gate_units'] == 203
    assert plan['completed_owner_fit_units'] == 0 and plan['2026_used_for_selection'] is False
    assert data['current_paper_policy']['cash_usd'] == data['current_paper_policy']['budget_usd'] == 100
    assert data['current_paper_policy']['qualified_stake_usd'] == 0
    return data



def cohort_demo():
    models = invented_comparison()
    panels = score_matched(models)
    result = {"paired": {"status": "PAIRED", "reason": "Two invented events, exact identity and label agreement. Scores can be compared."}}
    for name, changes in (("different_identity", {"event": "other-invented-event"}),
                          ("label_drift", {"actual": 0}),
                          ("late_issue", {"issued_at": "2024-10-01T18:00:00Z"})):
        changed = invented_comparison()
        changed["invented-challenger"][0] = replace(changed["invented-challenger"][0], **changes)
        try:
            score_matched(changed)
        except ValueError as error:
            result[name] = {"status": "BLOCKED", "reason": str(error)}
        else:
            raise AssertionError("invalid invented comparison was admitted")
    return result, panels


def render():
    legacy = evidence()
    latest = release()
    with tempfile.TemporaryDirectory() as temporary:
        demo = run_demo(temporary)
        reentry = run_demo(temporary)
    assert demo["new_synthetic_fits"] == 3 and reentry["new_synthetic_fits"] == 0
    scenarios, comparison = cohort_demo()
    labels = {"raw_market": "MARKET reference", "v130_minimax_conditional_pool": "Retained minimax",
              "v133_market_calibration": "Calibration control", "v133_orthogonal_innovation": "Orthogonal innovation"}
    panels = []
    for year in (2024, 2025, 2026):
        rows = [x for x in legacy["panels"] if x["season"] == year]
        table = "".join(f'<tr><th scope="row">{labels[x["arm"]]}</th><td>{x["games"]}</td><td>{x["win_brier"]:.6f}</td><td>{x["win_logloss"]:.6f}</td><td>{x["ece10"]:.6f}</td><td>{x["correct"]}/{x["games"]}</td></tr>' for x in rows)
        kind = "Exposed monitoring only" if year == 2026 else "Repeatedly examined historical season"
        panels.append(f'<section class="legacy-panel"><h3>{year} · {kind}</h3><div class="tablewrap" role="region" aria-label="Legacy {year} scores" tabindex="0"><table><thead><tr><th scope="col">Model</th><th scope="col">Games</th><th scope="col">Brier</th><th scope="col">Log loss</th><th scope="col">ECE10</th><th scope="col">Correct</th></tr></thead><tbody>{table}</tbody></table></div></section>')
    model_labels = {m["id"]: m["label"] for m in latest["models"]}
    options = "".join(f'<option value="{m["id"]}"' + (' selected' if m["id"] == "previous-study" else '') + f'>{html.escape(m["label"])}</option>' for m in latest["models"])
    selected = [r for r in latest["panels"] if r["season"] == 2025]
    base = next(r["metrics"]["winner_logloss"] for r in selected if r["model"] == "previous-study")
    initial_rows = []
    for row in selected:
        value = row["metrics"]["winner_logloss"]
        delta = value - base
        name = row["model"]
        cls = 'reference' if name == 'previous-study' else ('challenger' if name == 'registered-challenger' else '')
        delta_text = '—' if name == 'previous-study' else f'{delta:+.6f}'
        initial_rows.append(f'<tr data-model="{name}" class="{cls}"><th scope="row">{html.escape(model_labels[name])}</th><td>{row["games"]}</td><td class="metric-value">{value:.6f}</td><td>{delta_text}</td><td class="sr-only">Historical comparison</td></tr>')
    interval_rows = "".join(f'<tr><th scope="row">{r["season"]}</th><td>{r["target"].title()}</td><td>{r["covered"]} / {r["games"]}</td><td>{r["empirical_coverage"]:.2%}</td><td>{r["mean_width"]:.2f}</td></tr>' for r in latest["intervals"])
    fixture_rows = "".join(f'<tr><th scope="row">{r["model"].replace("invented-", "").title()}</th><td>{r["games"]}</td><td>{r["metrics"]["brier"]:.6f}</td><td>{r["metrics"]["logloss"]:.6f}</td></tr>' for r in comparison)
    payload = json.dumps({"latest": latest, "evidence": legacy, "invented": demo,
                          "cohort_demo": scenarios, "reentry_new_synthetic_fits": 0}, sort_keys=True, allow_nan=False).replace("<", "\\u003c")
    replacements = {"REFERENCE_OPTIONS": options, "INITIAL_ROWS": "".join(initial_rows),
                    "INTERVAL_ROWS": interval_rows, "COHORT_DEMO_ROWS": fixture_rows,
                    "LEGACY_PANELS": "".join(panels), "RETURN_SHA": latest["verification"]["return_sha256"],
                    "COMPLETION_SHA": latest["verification"]["completion_sha256"], "PAYLOAD": payload}
    text = (Path(__file__).with_name("review_template.html.in")).read_text()
    for key, value in replacements.items():
        text = text.replace("@@" + key + "@@", value)
    if "@@" in text:
        raise ValueError("unfilled page template")
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("FBS page is stale: python -m examples.fbs_contracts.build_review")
        print("FBS aggregate page exactly matches dated evidence and invented execution")
    else:
        OUTPUT.write_text(text)
        print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
