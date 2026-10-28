"""B003 aggregate accounting, calibration and generated comparison tables.

This module never accesses raw data or models. B002 remains an immutable export.
"""
from __future__ import annotations
import math

NAMES = {"nba":"NBA", "ncaam":"NCAA men", "ncaaw":"NCAA women"}
RECIPES = {"basketball_strength":"Strength logistic · 15", "basketball_style":"Style logistic · 25",
    "basketball_combined":"Combined logistic · 53", "basketball_lightgbm":"Combined LightGBM · 53",
    "basketball_xgboost":"Combined XGBoost · 53", "basketball_catboost":"Combined CatBoost · 53",
    "basketball_opponent_adjusted":"Strength + opponent adjustment · 25",
    "basketball_rich_combined":"Rich combined logistic · 63", "basketball_rich_lightgbm":"Rich combined LightGBM · 63",
    "Elo":"Elo", "Margin_Elo":"Margin Elo", "historical_prior":"Historical prior", "MARKET_raw":"Raw MARKET"}

def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)

def validate_extended(value):
    owner=value['owner_execution']
    new,reused,prior=(owner[k] for k in ('completed_native_fit_units','imported_predecessor_units','predecessor_cumulative_basketball_native_units'))
    if (type(reused) is not int or reused<0 or reused>prior
            or new+reused!=owner['verified_current_release_manifest_units']
            or prior+new!=owner['cumulative_basketball_native_units']
            or sum(t['imported_predecessor_units'] for t in value['tracks'])!=reused):
        raise ValueError('predecessor reuse must not add new fits')
    if not close(owner['remaining_work_seconds_at_return_snapshot'],owner['work_ceiling_seconds']-owner['cumulative_active_seconds_through_return_snapshot']):
        raise ValueError('cumulative budget must carry forward without reset')
    if owner['prior_pending_rows']+owner['prior_quarantined_rows']!=owner['prior_immutable_forecast_rows_checked']:
        raise ValueError('prospective pending-row accounting changed')
    for track in value['tracks']:
        for row in track['season_scorecards']:
            bins=row['calibration_bins']
            if sum(b['n'] for b in bins)!=row['n']:
                raise ValueError('calibration bins do not cover the scored cohort')
            ece=sum(b['n']*abs(b['mean_probability']-b['observed_rate']) for b in bins)/row['n']
            if not close(ece,row['ece_10_fixed_bins']):
                raise ValueError('calibration plot differs from the scored metric')
        for selection in track['selections']:
            for pooled in selection['leaderboard']:
                rows=[r for r in track['season_scorecards'] if r['cohort']==selection['cohort'] and r['recipe']==pooled['recipe']]
                n=sum(r['n'] for r in rows)
                if n!=pooled['n']:
                    raise ValueError('pooled leaderboard cohort does not reconcile')
                for key in ('log_loss','brier','accuracy'):
                    if not close(sum(r[key]*r['n'] for r in rows)/n,pooled[key]):
                        raise ValueError('pooled leaderboard metric does not reconcile')
        for comparison in track['paired_control_comparisons']:
            if comparison['season'] not in (2025,2026,'pooled'):
                raise ValueError('paired comparison crosses protected monitoring boundary')
            if comparison['n']<=0 or len(comparison['ci95'])!=2 or comparison['ci95'][0]>comparison['ci95'][1]:
                raise ValueError('invalid paired comparison interval')

def matched_selected_rows(value):
    """Evaluate the full-cohort selection on its exact MARKET-matched subset."""
    result=[]
    for track in value['tracks']:
        choice=next(s for s in track['selections'] if s['cohort']=='full_basketball')
        for year in (2025,2026):
            rows=[r for r in track['season_scorecards'] if r['cohort']=='matched_MARKET' and r['validation_season']==year]
            scope={'league':track['league'],'horizon_minutes':track['horizon_minutes'],'season':year}
            if not rows:
                result.append({**scope,'n':0,'model_log_loss':None,'market_log_loss':None,'difference':None});continue
            raw=next(r for r in rows if r['recipe']=='MARKET_raw')
            model=next(r for r in rows if r['recipe']==choice['selected_recipe'])
            result.append({**scope,'n':raw['n'],'model_log_loss':model['log_loss'],'market_log_loss':raw['log_loss'],'difference':model['log_loss']-raw['log_loss']})
    return result

def render_results(value):
    from .evidence import selected_season_rows
    lines=['# B003 basketball historical results','',
        '[Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Model card](BASKETBALL_MODEL_CARD.md) · [B003 aggregate](evidence/2026-10-27-basketball-b003.json) · [Preserved B002 aggregate](evidence/2026-10-27-basketball-b002.json)','',
        'B003 completed actual owner execution. These are reconstructed results with a 24-hour statistical-release assumption; original historical publication clocks remain unverified. T−60 is primary and T−24h is separate. The 2025 and 2026 folds are development evidence after selection. Lower selected log loss does not establish an independent MARKET advantage.','',
        '## League leaderboards at T−60','',
        'All recipes within each league share identical games, outcomes and historical cutoffs. Every earlier B002 control probability, point estimate, outcome and cutoff matched exactly in the B003 audit. Predictor counts accompany learned-model names. The minimum pooled log loss is bolded as a numerical result, not a promotion claim.','']
    for track in value['tracks']:
        if track['horizon_minutes']!=60:continue
        selection=next(s for s in track['selections'] if s['cohort']=='full_basketball')
        rows=[r for r in track['season_scorecards'] if r['cohort']=='full_basketball']
        lookup={(r['recipe'],r['validation_season']):r for r in rows}
        counts=[next(r['n'] for r in rows if r['validation_season']==y) for y in (2025,2026)]
        lines += [f"### {NAMES[track['league']]}",'',f"Games: {counts[0]:,} in ending 2025 and {counts[1]:,} in ending 2026. Historical probability selection: {RECIPES[selection['selected_recipe']]}. This is selected development performance.",'',
            '| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |','|---|---:|---:|---:|---:|---:|']
        for row in selection['leaderboard']:
            a,b=lookup[(row['recipe'],2025)],lookup[(row['recipe'],2026)]
            pooled=f"{row['log_loss']:.6f}"
            if row['recipe']==selection['selected_recipe']:pooled=f'**{pooled}**'
            lines.append(f"| {RECIPES[row['recipe']]} | {a['log_loss']:.6f} | {b['log_loss']:.6f} | {a['brier']:.6f} | {b['brier']:.6f} | {pooled} |")
        lines.append('')
    lines += ['## Controlled opponent-adjustment comparisons','',
        'Negative Δ favors B003. Each row compares the declared new architecture with its exact earlier control. Intervals use 300 paired seven-calendar-day block resamples. They are descriptive after development exposure, not multiplicity-adjusted or untouched confirmation. Additional prior-champion contrasts and per-season uncertainty remain in the export.','',
        '| League | B003 arm − B002 control | 2025 Δ log loss | 2026 Δ log loss | Pooled Δ log loss | Pooled descriptive 95% interval | Games / blocks |','|---|---|---:|---:|---:|---|---:|']
    for track in value['tracks']:
        if track['horizon_minutes']!=60:continue
        for arm,control in [('basketball_opponent_adjusted','basketball_strength'),('basketball_rich_combined','basketball_combined'),('basketball_rich_lightgbm','basketball_lightgbm')]:
            lookup={c['season']:c for c in track['paired_control_comparisons'] if (c['arm'],c['control'])==(arm,control)}
            a,b,c=(lookup[y] for y in (2025,2026,'pooled'));lo,hi=c['ci95']
            lines.append(f"| {NAMES[track['league']]} | {RECIPES[arm]} − {RECIPES[control]} | {a['delta_log_loss_a_minus_b']:+.6f} | {b['delta_log_loss_a_minus_b']:+.6f} | {c['delta_log_loss_a_minus_b']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | {c['n']:,} / {c['unique_blocks']} |")
    lines += ['','The richer representation improves both college folds; NBA retains strength logistic. College pooled fixed-bin calibration error increases despite better proper scores: men 0.013393 → 0.014288 and women 0.019232 → 0.023450. The new historical selections are research candidates with a calibration weakness, not universally superior or MARKET-qualified champions.','',
        '## Selected probability and separately selected point-head diagnostics','',
        'Point estimates use Ridge margin and total regressors. Probability recipe names do not imply a different point architecture. These predictions do not provide game-level intervals or a calibrated joint score distribution.','',
        '| League | Season | Games | Correct / incorrect | Accuracy | Calibration error ↓ | Margin MAE / RMSE ↓ | Total MAE / RMSE ↓ | Total bias |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in selected_season_rows(value):
        m,t=r['point_margin'],r['point_total']
        lines.append(f"| {NAMES[r['league']]} | {r['validation_season']} | {r['n']:,} | {r['correct']:,} / {r['incorrect']:,} | {r['accuracy']:.2%} | {r['ece_10_fixed_bins']:.6f} | {m['mae']:.3f} / {m['rmse']:.3f} | {t['mae']:.3f} / {t['rmse']:.3f} | {t['signed_error']:+.3f} |")
    lines += ['','## Equivalent-game sportsbook MARKET comparisons','',
        'The basketball recipe is each full-cohort historical selection, evaluated on its exact MARKET-matched subset. Positive Δ means basketball log loss is worse. Unavailable means no admitted matched events. Larger recent validation cohorts do not create earlier training history.','',
        '| League | Horizon | Season | Matched games | Basketball log loss ↓ | Raw MARKET log loss ↓ | Δ basketball − MARKET |','|---|---:|---:|---:|---:|---:|---:|']
    for r in matched_selected_rows(value):
        prefix=f"| {NAMES[r['league']]} | T−{r['horizon_minutes']}m | {r['season']} | {r['n']:,}"
        lines.append(prefix+(' | Unavailable | Unavailable | Unavailable |' if r['n']==0 else f" | {r['model_log_loss']:.6f} | {r['market_log_loss']:.6f} | {r['difference']:+.6f} |"))
    lines += ['','Learned MARKET-only and integrated classifiers still lack the required chronological training support. No threshold was relaxed. No league establishes a qualified model advantage. Women’s T−60 rich logistic loses to MARKET in 2025 and improves in 2026; both paired intervals include zero. The enlarged men’s 2026 cohort still lacks an earlier validation-year comparison.','',
        '### Venue-separated exchange benchmark status','',
        '| Venue | Admitted historical events | Qualified executable current quotes | Status |','|---|---:|---:|---|']
    for name,r in value['exchange_benchmarks'].items():lines.append(f"| {name.replace('_',' ')} | {r['historical_admitted_events']} | {r['executable_current_quotes']} | Contract, timing and execution evidence incomplete |")
    lines += ['','Displayed page prices are not bid/ask histories or fills. Fees, depth, side direction, settlement and decision-time availability require separate evidence. No exchange trading backtest or basketball bankroll is admitted.','',
        '## T−24h remains a separate experiment','',
        'New opponent-adjustment arms were declared only for T−60. T−24h retains its earlier families; no T−60 improvement transfers to it.','',
        '| League | Season | Probability selection | Games | Log loss ↓ | Brier ↓ |','|---|---:|---|---:|---:|---:|']
    for r in selected_season_rows(value,1440):lines.append(f"| {NAMES[r['league']]} | {r['validation_season']} | {RECIPES[r['recipe']]} | {r['n']:,} | {r['log_loss']:.6f} | {r['brier']:.6f} |")
    lines += ['','## Forward monitoring is separate from historical selection','',
        'B003 verified the exact 110 previously issued B002 rows: all pending, none quarantined or settled. It issued 110 additional rows spanning the same 61 distinct future games. These are later forecast versions, not 122 independent games. Every new row remains an early outlook before its declared lock, with zero qualified contemporary MARKET probabilities and NO_BET status. Prospective accuracy, proper scores and profit are unavailable until verified outcomes arrive. Current-season retrospective rows are excluded from selection and prospective claims.','',
        '## Reproducibility and limits','',
        'The public command checks cohort identities, calibration-bin arithmetic, pooled scoring, new-versus-reused unit accounting and the protected current-season boundary. It recreates these tables without private records or estimator execution. B003 has 60 new real estimator units, 156 byte-verified imported units and 232 cumulative unique basketball units. Its 22.10 active minutes are an observed owner result. B004 execution and proposed scientific benefits remain pending.','']
    return '\n'.join(lines)
