"""Render and validate sanitized stopped-run evidence; no private model access."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/evidence/2026-10-28-basketball-b004.json'
REPORT=ROOT/'docs/BASKETBALL_B004_EXECUTION.md'
LEAGUES={'nba':'NBA','ncaam':'NCAA men','ncaaw':'NCAA women'}
CANDIDATES={'basketball_fixed_blend':'Fixed probability blend',
 'basketball_distribution_win':'Probability from margin',
 'basketball_score_distribution':'Corrected score distribution'}

def load_evidence():
    return json.loads(EVIDENCE.read_text())

def close(a,b):
    return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11)

def validate(value):
    owner=value['owner_execution']; budget=value['accounting']; evaluation=value['evaluation']
    if owner['accepted_release'] or owner['status']!='STOPPED' or owner['latest_completed_real_release']!='B003':
        raise ValueError('stopped execution must remain separate from accepted modeling')
    if owner['predecessor_cumulative_basketball_real_units']+owner['new_real_units']!=owner['cumulative_basketball_real_units'] or owner['predecessor_aliases']+owner['new_real_units']!=owner['release_completed_checkpoint_files']:
        raise ValueError('new fits and imported aliases must reconcile separately')
    if not close(budget['maximum_verified_active_floor_seconds']+budget['remaining_work_seconds'],budget['work_ceiling_seconds']) or budget['public_requests_remaining']!=budget['public_requests_ceiling']-budget['public_requests_used']:
        raise ValueError('cumulative budget may not reset')
    if evaluation['current_outcomes_used_for_selection_or_fitting'] or evaluation['validation_seasons']!=[2025,2026]:
        raise ValueError('protected current-season boundary')
    if evaluation['market_advantage_established'] or any(value['publication_boundary'].values()):
        raise ValueError('public evidence boundary')
    if len(value['challengers'])!=9 or len({(g['league'],g['candidate']) for g in value['challengers']})!=9:
        raise ValueError('all nine league-program comparisons required')
    for g in value['challengers']:
        if [r['season'] for r in g['per_season']]!=[2025,2026]:
            raise ValueError('protected current-season boundary')
        pooled=g['pooled_paired']; n=0;delta_sum=0.
        for r in g['per_season']:
            c,i=r['candidate'],r['incumbent'];n+=c['n']
            if c['n']!=i['n'] or c['correct']+c['incorrect']!=c['n']:
                raise ValueError('identical cohort and pick counts required')
            if g['target']=='probability':
                conditions={'log_loss_improves':c['log_loss']<i['log_loss'],
                    'brier_no_regression':c['brier']<=i['brier'],
                    'ece_within_0_01':c['ece_10_fixed_bins']<=i['ece_10_fixed_bins']+.01}
                delta=c['log_loss']-i['log_loss']
            else:
                conditions={'joint_mse_improves':c['joint_mse']<i['joint_mse'],
                    'margin_rmse_no_regression':c['margin_rmse']<=i['margin_rmse'],
                    'total_rmse_no_regression':c['total_rmse']<=i['total_rmse']}
                delta=c['joint_mse']-i['joint_mse']
                for m in (c,i):
                    if not close(m['joint_mse'],m['margin_rmse']**2+m['total_rmse']**2):
                        raise ValueError('point-component arithmetic')
            if conditions!=r['conditions'] or r['passed']!=all(conditions.values()) or not close(delta,r['paired']['delta']):
                raise ValueError('per-season promotion gate or paired arithmetic')
            delta_sum+=delta*c['n']
        if pooled['n']!=n or not close(pooled['delta'],delta_sum/n):
            raise ValueError('pooled paired arithmetic')
        eligible=all(r['passed'] for r in g['per_season']) and pooled['ci95'][1]<0
        if g['promoted']!=eligible:
            raise ValueError('promotion must retain both-season and uncertainty gates')
    if evaluation['new_promotions']!=sum(g['promoted'] for g in value['challengers']):
        raise ValueError('promotion count')
    return value

def render(value):
    validate(value)
    lines=['# B004 execution: useful negative results, resource stop','',
      '[Project](../README.md) · [B003 historical results](BASKETBALL_RESULTS.md) · [B004 aggregate](evidence/2026-10-28-basketball-b004.json)','',
      'B004 actually executed on October 28, 2026, Pacific time. All six reconstructed historical league/horizon scopes completed before optional exchange capture exhausted the public-request allowance. The owner return is **STOPPED**, not accepted. B003 remains the latest fully completed real modeling release.','',
      'Six shared score-correction units completed, bringing cumulative basketball real units from 232 to 238. The 216 predecessor aliases and 222 checkpoint files are reuse/accounting evidence; they are not 222 new fits. The run tally is two accepted, one failed and one stopped basketball execution.','',
      'No challenger earned promotion. NBA retains strength logistic; both college leagues retain rich combined logistic at T−60. The separate B003 point heads and T−24h recipes remain unchanged. Historical 2025/2026 seasons are development-exposed, and all statistical history uses the labeled reconstructed 24-hour assumption.','',
      '## Probability challengers','',
      'Lower log loss is better. Each challenger uses the exact incumbent cohort in each season. Both-season log-loss improvement, no Brier regression, calibration stability and the paired uncertainty gate remain required.','',
      '| League | Challenger | 2025 log loss | 2026 log loss | Pooled Δ vs incumbent | Descriptive 95% interval | Promoted |',
      '|---|---|---:|---:|---:|---|---|']
    for g in value['challengers']:
        if g['target']!='probability':continue
        a,b=g['per_season'];p=g['pooled_paired'];lo,hi=p['ci95']
        lines.append(f"| {LEAGUES[g['league']]} | {CANDIDATES[g['candidate']]} | {a['candidate']['log_loss']:.6f} | {b['candidate']['log_loss']:.6f} | {p['delta']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | No |")
    lines+=['','NBA probability-from-margin improves pooled log loss by only 0.000160, but worsens both log loss and Brier in 2025. The fixed blend worsens both college seasons. The men’s margin probability worsens 2025; the women’s version worsens 2025 Brier and 2026 log loss. Weights and thresholds were not retuned against these exposed results.','',
      '## Corrected point distributions','',
      'The combined margin/total squared-error improvement does not override a component regression. All three leagues fail the margin-RMSE requirement in 2025; women also fail it in 2026.','',
      '| League | 2025 margin RMSE, incumbent → correction | 2026 margin RMSE, incumbent → correction | Pooled Δ combined MSE | Descriptive 95% interval |',
      '|---|---:|---:|---:|---|']
    for g in value['challengers']:
        if g['target']!='points':continue
        a,b=g['per_season'];p=g['pooled_paired'];lo,hi=p['ci95']
        lines.append(f"| {LEAGUES[g['league']]} | {a['incumbent']['margin_rmse']:.6f} → {a['candidate']['margin_rmse']:.6f} | {b['incumbent']['margin_rmse']:.6f} → {b['candidate']['margin_rmse']:.6f} | {p['delta']:+.6f} | [{lo:+.6f}, {hi:+.6f}] |")
    lines+=['','Men’s combined error interval excludes zero, yet its 2025 margin regression still prevents promotion. These are descriptive intervals from 300 paired seven-calendar-day block resamples, not untouched confirmation.','',
      '## Uncertainty remains reportable after rejection','',
      'Pooled diagnostics below describe the rejected corrected distributions, not approved uncertainty for issued forecasts. The aggregate also includes separate 2025/2026 results and home/away-point diagnostics. CRPS means were reaggregated from saved per-game values; the native residual arrays were not deserialized during the audit.','',
      '| League | Target | 80% coverage / width / interval score | 95% coverage / width / interval score | Mean saved CRPS |',
      '|---|---|---:|---:|---:|']
    for r in value['predictive_distribution_metrics']:
        if str(r['season'])!='pooled' or r['target'] not in ('margin','total'):continue
        lines.append(f"| {LEAGUES[r['league']]} | {r['target']} | {float(r['coverage_80']):.2%} / {float(r['width_80']):.3f} / {float(r['interval_score_80']):.3f} | {float(r['coverage_95']):.2%} / {float(r['width_95']):.3f} / {float(r['interval_score_95']):.3f} | {float(r['mean_saved_empirical_crps']):.6f} |")
    lines+=['','## Forecasts, MARKET and execution limits','',
      'B004 issued 110 additional immutable early-outlook versions. B002/B003/B004 now preserve 330 versions in 18 files across 61 distinct games. They are not 330 independent games or named-horizon lock forecasts. The B004 prospective monitor checked the prior 220 versions: all pending, zero settled. Its 110 new versions were not yet scored by that monitor.','',
      'No qualified at-issue sportsbook comparison or game-level predictive uncertainty was admitted for the new issues. Fresh inputs contained 56 completed NBA games, but no new 56-game retrospective scorecard was produced. The earlier B003 52-game retrospective panel remains separate from genuine prospective evidence.','',
      'Sportsbook, Kalshi, Polymarket US and international Polymarket remain separate. No independent MARKET advantage, historical exchange trading backtest, order, fill, profit or basketball bankroll is established. Learned MARKET-only and integrated models retain the earlier-support minimums; no threshold was lowered.','',
      'The maximum verified cumulative active floor is 4,223.356267478 seconds against 4,500, leaving 276.643732522 seconds before any later matching live charge. All 48 public requests are consumed. The separate 180-second finalization reserve cannot fund research. The next bounded recovery may consolidate evidence without new fitting or public requests; fresh acquisition requires an explicitly approved allowance.','',
      '## Reproduce the public evidence checks','',
      '```bash','python -m examples.basketball_contracts.evidence_b004 --check','python -m unittest discover -s examples/basketball_contracts/tests -v','```','',
      'The private-return audit verified 11,670 manifest pins and CRC, native checkpoint hashes, the embedded source, saved notebooks and report links. Independent numerical checks compared 11,732 values across 684 scorecards, 496 interval rows and 248 CRPS aggregation rows; maximum absolute discrepancy was below 4.3×10⁻¹⁴. No private model fitting, inference or deserialization occurred during that audit. The public command validates aggregate arithmetic and regenerates this note; it does not claim to reproduce private training.','',
      'The public update contains sanitized aggregates and generic evidence checks. Raw source records, individual forecasts, active training code, fitted weights and cloud identifiers remain excluded. Portfolio assessment remains 8.5/10: stronger auditability does not establish independent predictive or trading performance.','']
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=render(load_evidence())
    if args.check:
        if REPORT.read_text()!=text:raise SystemExit('B004 execution note differs from verified aggregate rendering')
        print('B004 stopped-run aggregate and rendered note verified')
    else: REPORT.write_text(text)

if __name__=='__main__':main()
