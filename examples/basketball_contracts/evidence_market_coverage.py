"""Validate public aggregate arithmetic; no fitting, inference or private data access."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/evidence/2026-10-28-basketball-market-coverage.json'
REPORT = ROOT / 'docs/BASKETBALL_MARKET_COVERAGE.md'


def near(actual, expected, label):
    if not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-11):
        raise ValueError(f'{label}: {actual!r} != {expected!r}')


def validate(data):
    if data['historical_years'] != [2025, 2026] or data['current_2027_used'] is not False:
        raise ValueError('current outcomes cannot enter the historical study')
    if any(data[k] != 0 for k in ('new_real_fits', 'model_inferences', 'new_source_requests', 'new_forecasts')) or data['promotion'] is not False:
        raise ValueError('saved-prediction study is not a new model execution')
    owner = data['owner_recovery']
    if owner['status'] != 'SUCCESS_EVIDENCE_RECOVERY' or owner['latest_completed_real_modeling_release'] != 'B003' or owner['b004_acceptance_status_unchanged'] != 'STOPPED':
        raise ValueError('recovery must preserve modeling release status')
    if any(owner[k] != 0 for k in ('new_real_fits', 'model_inferences', 'network_requests', 'new_forecasts', 'new_orders')):
        raise ValueError('B005 recovery cannot acquire or model new data')
    if owner['budget_expanded'] or owner['future_training_or_source_budget_authorized']:
        raise ValueError('no additional budget is authorized')
    near(owner['conservative_available_work_seconds'], owner['work_ceiling_seconds'] - max(owner['measured_active_floor_seconds'], owner['open_finalization_reservation_until_seconds']), 'open reservation remainder')
    if owner['public_requests_consumed'] != owner['public_request_ceiling'] or owner['cumulative_real_basketball_units'] != 238:
        raise ValueError('preserve cumulative accounting')
    if data['baseline_by_league'] != {'nba': 'basketball_strength', 'ncaam': 'basketball_combined', 'ncaaw': 'basketball_combined'}:
        raise ValueError('league control identity')
    rows = data['year_coverage']
    index = {(r['league'], r['year'], r['covered']): r for r in rows}
    if len(index) != len(rows) or any(r['year'] not in (2025, 2026, 'pooled') for r in rows):
        raise ValueError('duplicate or unsupported historical cohort')
    if ('ncaam', 2025, 1) in index:
        raise ValueError('there is no men 2025 covered comparison')
    for row in rows:
        if row['base_recipe'] != data['baseline_by_league'][row['league']]:
            raise ValueError('league control identity')
        if row['base_n'] != row['rich_n'] or row['base_n'] <= 0:
            raise ValueError('exact same-game comparison required')
        near(row['delta_mean'], row['rich_log_loss'] - row['base_log_loss'], 'loss delta')
        near(row['brier_delta'], row['rich_brier'] - row['base_brier'], 'Brier delta')
        for prefix in ('base', 'rich'):
            if row[prefix + '_correct'] + row[prefix + '_incorrect'] != row[prefix + '_n']:
                raise ValueError('pick counts')
        if row['year'] == 'pooled':
            years = [index[(row['league'], y, row['covered'])] for y in (2025, 2026) if (row['league'], y, row['covered']) in index]
            if sum(r['base_n'] for r in years) != row['base_n']:
                raise ValueError('pooled support differs from its years')
            for metric in ('base_log_loss', 'rich_log_loss', 'delta_mean'):
                near(row[metric], sum(r[metric] * r['base_n'] for r in years) / row['base_n'], 'pooled arithmetic')
    uncovered, covered = (index[('ncaam', 2026, c)] for c in (0, 1))
    gap = covered['delta_mean'] - uncovered['delta_mean']
    near(data['ncaam_2026_raw_gap']['covered_minus_uncovered_delta'], gap, 'same-year gap')
    strata = data['supported_strata']
    if len({(r['spec'], r['stratum']) for r in strata}) != len(strata):
        raise ValueError('duplicate supported stratum')
    for spec in data['standardizations']:
        selected = [r for r in strata if r['spec'] == spec['spec']]
        if len(selected) != spec['common_strata']:
            raise ValueError('supported strata missing')
        n0, n1 = (sum(r[f'n_{c}'] for r in selected) for c in (0, 1))
        if n0 != spec['common_uncovered_n'] or n1 != spec['common_covered_n']:
            raise ValueError('common-support counts')
        if spec['full_uncovered_n'] != uncovered['base_n'] or spec['full_covered_n'] != covered['base_n']:
            raise ValueError('standardization must use same-year full cohort')
        for r in selected:
            if not r['supported'] or min(r['n_0'], r['n_1']) < spec['min_observed_per_cohort_per_stratum']:
                raise ValueError('unsupported stratum admitted')
            near(r['covered_weight'], r['n_1'] / n1, 'covered stratum weight')
            near(r['uncovered_weight'], r['n_0'] / n0, 'uncovered stratum weight')
            for c in (0, 1):
                near(r[f'delta_sum_{c}'], r[f'mean_delta_{c}'] * r[f'n_{c}'], 'stratum sum')
        cmean = sum(r['mean_delta_1'] * r['covered_weight'] for r in selected)
        umean = sum(r['mean_delta_0'] * r['uncovered_weight'] for r in selected)
        uweighted = sum(r['mean_delta_0'] * r['covered_weight'] for r in selected)
        within, composition = cmean - uweighted, uweighted - umean
        for key, value in {
            'covered_retention': n1 / covered['base_n'],
            'uncovered_retention': n0 / uncovered['base_n'],
            'common_covered_delta': cmean, 'common_uncovered_delta': umean,
            'uncovered_reweighted_to_covered_delta': uweighted,
            'within_stratum_component_covered_reference': within,
            'composition_component_uncovered_reference': composition,
            'common_gap': cmean - umean,
            'support_exclusion_component': gap - (cmean - umean),
            'full_gap': gap,
            'uncovered_reweighting_ess': 1 / sum(r['covered_weight'] ** 2 / r['n_0'] for r in selected),
            'uncovered_max_weight_factor': max(r['covered_weight'] / r['uncovered_weight'] for r in selected),
        }.items():
            near(spec[key], value, spec['spec'] + ':' + key)
        for interval in spec['descriptive_intervals'].values():
            if len(interval) != 2 or interval[0] > interval[1] or not all(math.isfinite(v) for v in interval):
                raise ValueError('invalid descriptive interval')
    if data['next_research']['active_budget_allowance'] != 0 or data['next_research']['extra_training_authorized'] or data['next_research']['extra_source_requests_authorized']:
        raise ValueError('future research needs explicit budget approval')
    return {'year_coverage_rows': len(rows), 'standardizations': len(data['standardizations']), 'supported_strata': len(strata), 'new_real_fits': 0}


def render(data):
    validate(data)
    rows = ['# Basketball: why covered and uncovered gains differ', '',
        'The larger NCAA men improvement outside the saved sportsbook panel is partly a calendar-composition and support problem. Matching baseline probability alone leaves almost the entire difference. Adding month and game type greatly reduces it, while discarding 29.09% of uncovered games. This is descriptive evidence about the comparison population, not a causal explanation or a qualified MARKET edge.', '',
        'This review recomputes saved 2025–2026 predictions. It performs zero real fits, model inferences, source requests or new forecasts. B005 actually completed evidence recovery with zero fits; B003 remains the latest fully completed real modeling release, and B004 remains a stopped execution. The cumulative real-unit count stays 238.', '',
        '## First correct the season comparison', '',
        'Covered means a valid saved T60 sportsbook benchmark; uncovered does not mean no real-world market. All 1,143 covered NCAA men games are from 2026. The earlier pooled uncovered gain mixed 2025 and 2026, so it cannot identify a coverage effect. The college controls are exact B002 combined models. NBA compares the rejected rich candidate with its selected strength model; no champion changes.', '',
        '| League | Season | Saved MARKET | Games | Control log loss | Rich log loss | Rich − control |',
        '|---|---|---|---:|---:|---:|---:|']
    names = {'nba': 'NBA', 'ncaam': 'NCAA men', 'ncaaw': 'NCAA women'}
    for r in data['year_coverage']:
        if r['year'] != 'pooled':
            rows.append(f"| {names[r['league']]} | {r['year']} | {'Covered' if r['covered'] else 'Uncovered'} | {r['base_n']:,} | {r['base_log_loss']:.9f} | {r['rich_log_loss']:.9f} | {r['delta_mean']:+.9f} |")
    rows += ['', 'Negative deltas favor the rich candidate over its league control. In NCAA men 2026, the covered-minus-uncovered improvement gap is +0.008515371, with a shared seven-day calendar-block interval [0.002993166, 0.014439907]. There is no covered men 2025 control. NBA has only 9 and 16 covered games; its small panel does not support a confident coverage explanation.', '',
        '## Competitiveness alone does not explain the gap', '',
        'Covered games have lower mean baseline favorite confidence (0.7172 versus 0.7326), but their central 0.4–0.6 home-win probability share is slightly lower: 253/1,143 (22.13%) versus 1,060/4,606 (23.01%). Calling the covered panel simply “more competitive” depends on the chosen definition. Reweighting uncovered games to the covered probability-quintile distribution retains every game and leaves a +0.008104461 gap. Probability deciles give +0.008414666.', '',
        'The calendar mix is much more different: January–February supplies 1,002/1,143 (87.66%) of covered games versus 1,894/4,606 (41.12%) of uncovered games. November has 1 covered and 1,241 uncovered games. Month-only matching leaves +0.001553897, but retains only 72.77% of uncovered games. Month is both a context proxy and a coverage-support constraint; it does not isolate a causal mechanism.', '',
        '## Report adjustment together with support loss', '',
        'Each row below uses a fixed descriptive grouping and requires at least five observed games in each cohort per stratum, or twenty for the named sensitivity. Uncovered stratum means are reweighted to the retained covered distribution. Different rows can describe different retained populations. All fifteen declared sensitivities are shown; none selects a model. This independent forensic analysis uses minimum five plus minimum-twenty sensitivities. The offline B006 owner-analysis default uses minimum twenty with its own declared confidence strata and is a separate specification, not an exact numeric replay of the forensic table.', '',
        '| Grouping | Covered retained | Uncovered retained | Uncovered ESS | Within-stratum gap | Descriptive 95% interval |',
        '|---|---:|---:|---:|---:|---|']
    for s in data['standardizations']:
        lo, hi = s['descriptive_intervals']['within_stratum_component']
        rows.append(f"| `{s['spec']}` | {s['covered_retention']:.2%} | {s['uncovered_retention']:.2%} | {s['uncovered_reweighting_ess']:,.1f} | {s['within_stratum_component_covered_reference']:+.9f} | [{lo:+.9f}, {hi:+.9f}] |")
    rows += ['', 'For probability quintile × month × game type, 1,137 covered and 3,266 uncovered games remain (99.48% and 70.91%). The within-stratum gap is +0.001829468 with interval [−0.002102329, +0.004976417] and uncovered effective sample size 2,289.0. The full raw gap decomposes into +0.003423843 from support exclusion, +0.003262061 from composition within retained support, and +0.001829468 within strata. It would be misleading to attribute the entire reduction to competitiveness or say the cohorts are now equivalent. The decomposition also depends on the reference distribution: a symmetric decomposition on the same support gives −0.000291602 within strata and +0.005383131 composition. No reference choice is a unique causal explanation.', '',
        'The raw interval resamples shared seven-day calendar blocks. The adjusted intervals use positive exponential multipliers on shared seven-day blocks with supported strata frozen before resampling. They are exploratory sensitivity intervals, unadjusted for multiple comparisons, from development-exposed seasons. They are not independent validation or causal confidence intervals.', '',
        '## What the prediction changes show', '',
        'On covered men games, rich combined corrects 22 baseline mistakes but loses 23 baseline correct picks; on uncovered games it corrects 131 and loses 113. Rich probability updates move toward the realized winner on 45.49% versus 55.67% of games. These are outcome-conditioned diagnostics, not available pregame signals.', '',
        'The covered rich model moves closer to sportsbook probabilities: mean absolute disagreement is 0.04258 versus 0.05253 for combined. Its signed probability-error correlation with MARKET is 0.99317 (shared subtraction of the same outcome mechanically raises residual correlations), and its mean log loss remains 0.010443758 worse than MARKET. Similar probabilities and highly correlated errors do not establish incremental information. No learned MARKET-only or integrated model is qualified; the 300-base/80-calibration requirements and stability gates remain intact.', '',
        '## Limits and the next controlled investigation', '']
    rows += ['- ' + s for s in data['context_limits']]
    rows += ['', 'Future work is registered for explicit budget approval: obtain sufficiently early MARKET training support; qualify original timing and genuinely new pregame information; then compare frozen residual or integrated candidates on exact historical cohorts and untouched future monitoring. More similar blends are not treated as new information. Current 2027 outcomes remain monitoring-only and cannot select features, hyperparameters, calibration, ensembles or champions.', '',
        'B005 preserved all 330 forecast versions across 18 files and 61 games, with no new forecast or order. Its recovered scorecards are reused evidence, not additional fits. The measured active floor is 4,250.265382922 seconds. The still-open finalization reservation extends to 4,430.265382922 seconds; that reservation is not measured spent time. Against the 4,500-second work ceiling, conservative availability is 69.734617078 seconds until a later authenticated closed receipt replaces the reservation. Public-source requests are 48/48. No extra training, source access or spending allowance is active. Offline B006 audit/code preparation stays within inherited authority.', '',
        'The project rating stays 8.5/10: the recovery and cohort diagnosis improve auditability, not independent MARKET advantage or trading evidence.', '',
        '## Reproduce the public aggregate checks', '',
        'The [sanitized aggregate evidence](evidence/2026-10-28-basketball-market-coverage.json) includes all fifteen sensitivities and supported-stratum sums. The [executed notebook](../notebooks/basketball_market_coverage.ipynb) retains two interactive Plotly figures, exact tables and a later completion cell. The validator recomputes pooled/year arithmetic, support counts, weights, decomposition and effective sample size. Bootstrap intervals are retained owner-data analysis outputs; public aggregates cannot independently regenerate their block resamples.', '',
        '```bash', 'python -m examples.basketball_contracts.evidence_market_coverage --check', 'python -m unittest discover -s examples/basketball_contracts/tests -v', 'python -m examples.basketball_contracts.execute_coverage_notebook --output /tmp/basketball-market-coverage.ipynb', '```', '',
        'See the preserved [B004 execution outcome](BASKETBALL_B004_EXECUTION.md), [historical leaderboards](BASKETBALL_RESULTS.md) and [model card](BASKETBALL_MODEL_CARD.md). No private event-level predictions, feature matrices, source identifiers, production weights or trading configuration are published.', '']
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads(EVIDENCE.read_text())
    receipt = validate(data)
    page = render(data)
    if args.check:
        if REPORT.read_text() != page:
            raise SystemExit('generated coverage report differs')
    else:
        REPORT.write_text(page)
    print(json.dumps({'status': 'PASS', **receipt}, sort_keys=True))


if __name__ == '__main__':
    main()
