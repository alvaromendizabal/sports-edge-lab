"""Generate static NCAA review pages from the committed sanitized aggregates."""
from __future__ import annotations
import argparse
from datetime import date, datetime
import hashlib
from html import escape
import json
from pathlib import Path

from progress import demo_scenarios
from preflight import demo_scenarios as preflight_scenarios
from handoff import demo as handoff_demo
from spread_ats import demo as spread_ats_demo

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
HOST='https://alvaro-ncaa-research-review.alv-mendizabal.chatgpt.site'


def scientific_attempt(data):
    """Resolve the dated owner of displayed scientific evidence independently."""
    release = data['current_results_status']['release']
    attempts = [data['current_owner_attempt'], *data['owner_attempt_history']]
    matches = [attempt for attempt in attempts if attempt['release'] == release]
    if len(matches) != 1:raise ValueError('scientific evidence owner is not unique')
    return matches[0]


def dated_readback(data):
    """The 182 storage GETs belong to B044, never a later owner's work."""
    attempts = [data['current_owner_attempt'], *data['owner_attempt_history']]
    matches = [attempt for attempt in attempts if attempt['release'] == 'B044']
    if len(matches) != 1:raise ValueError('dated readback owner is not unique')
    return matches[0]['storage_readback']


def validate_stages(attempt):
    if len(attempt['stages']) != attempt['planned_scientific_stages']:raise ValueError('stage inventory')
    if sum(s['status'] == 'COMPLETED' for s in attempt['stages']) != attempt['completed_scientific_stages']:raise ValueError('completed stage count')
    if sum(s['status'] != 'NOT_STARTED' for s in attempt['stages']) != attempt['attempted_scientific_stages']:raise ValueError('attempted stage count')


def evidence(league):
    data=json.loads((ROOT/'tracks'/league/'evidence.json').read_text())
    if data['schema']!='sports-edge-lab.public.ncaa-review.v1' or data['league']!=league:raise ValueError('evidence identity')
    if [r['name'] for r in data['providers']]!=['Kalshi','Polymarket','DraftKings']:raise ValueError('exclusive provider scope')
    if data['market_advantage']['demonstrated'] is not False:raise ValueError('unqualified market claim')
    if data['evaluation']['current_outcomes_used_for_selection'] is not False:raise ValueError('current selection leakage')
    attempt = data['current_owner_attempt']
    validate_stages(attempt)
    scientific = scientific_attempt(data)
    validate_stages(scientific)
    if attempt['completed_scientific_stages'] == 0 and any(attempt[k] != 0 for k in ('new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_prospective_issues', 'new_prediction_rows')):raise ValueError('unstarted science receives credit')
    if attempt['fit_count_status'] == 'UNKNOWN_PENDING_COMPLETE_DURABLE_PRODUCER_AUDIT':
        if any(attempt[k] is not None for k in ('new_real_target_fits', 'league_new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_injury_fits', 'new_prediction_rows', 'new_prospective_issues', 'reused_target_fits')):raise ValueError('unknown owner work receives invented counts')
    if attempt['status'] == 'WORKER_EXITED_WITHOUT_TERMINAL_RETURN':
        if attempt['completed_at'] is not None or attempt['external_shell_exit_code'] is not None or attempt['durable_return_verified'] is not False:raise ValueError('unexpected exit receives unsupported terminal completion')
        if attempt['out_of_memory_proved'] or attempt['kill_cause'] != 'UNKNOWN':raise ValueError('unproved signal-exit cause')
    baseline = data['b045_baseline_observation']
    if baseline['source_release'] != 'B045' or baseline['new_issue_credit'] is not None or baseline['new_fit_credit_from_report_recovery'] != 0:raise ValueError('report labels receive unverified issue or fit credit')
    if baseline['independent_metric_panels_checked'] != baseline['independent_season_panels_checked'] + baseline['independent_weekly_panels_checked'] or baseline['calibration_slope_intercept_independently_refit'] is not False:raise ValueError('unsupported metric reconciliation claim')
    readback = dated_readback(data)
    if readback['source_release'] != scientific['release'] or readback['observations'] != data['current_coverage_gaps']['market_observations']:raise ValueError('readback evidence population')
    if readback['new_provider_requests'] != 0 or readback['new_fit_credit'] != 0 or readback['earlier_availability_credit'] is not False or readback['source_clocks_unchanged'] is not True:raise ValueError('readback grants unsupported credit')
    if data['prepared_execution']['owner_execution_observed'] is not False or data['prepared_execution']['new_scientific_credit'] != 0:raise ValueError('prepared execution receives credit')
    if sum(p['retained_observations_both_leagues'] for p in data['providers']) != data['current_coverage_gaps']['market_observations']:raise ValueError('provider observation closure')
    result = data['current_results_status']
    if result['new_issues_created_by_recovery'] != 0 or result['new_fits_created_by_recovery'] != 0:raise ValueError('recovery creates scientific credit')
    if result['authenticated_issue_rows_this_league'] != data['observed_inventory']['authenticated_current_issues']:raise ValueError('issue scope')
    if result['authenticated_issue_rows_both_leagues'] != scientific['retained_prior_prospective_issues']:raise ValueError('retained issue count')
    if result['new_owner_issues'] != scientific['new_prospective_issues']:raise ValueError('new owner issue count')
    if result['pre_study_target_rows'] != sum(result['prediction_rows'].values()) + result['retained_prior_issue_rows']:raise ValueError('pre-study target closure')
    if result['browser_display_rows'] != result['pre_study_game_model_rows'] + data['current_coverage_gaps']['unresolved_source_candidates']:raise ValueError('display row closure')
    pair = data['latest_reconstructed_comparison']
    if pair['as_issued'] or pair['current_outcomes_selected_model'] or pair['qualified_settled_bets'] != 0 or pair['profit'] is not None:raise ValueError('unqualified current comparison claim')
    if pair['release'] != scientific['release'] or pair['evidence_snapshot_at'] != data['freshness']['pre_study_report_asof']:raise ValueError('current comparison clock')
    if data['coverage_evidence_release'] != data['freshness']['owner_release']:raise ValueError('capture release')
    for model in data['models']:
        if set(model['panels'])!={'pooled','2025','2026'}:raise ValueError('season closure')
        if model['panels']['pooled']['N']!=model['panels']['2025']['N']+model['panels']['2026']['N']:
            raise ValueError('pooled game count')
        for panel in model['panels'].values():
            if model['target']=='win' and sum(b['N'] for b in panel['calibration_bins'])!=panel['N']:
                raise ValueError('calibration support')
    return data


def render_track(data):
    league=data['league'];sibling='ncaaw' if league=='ncaam' else 'ncaam'
    template=(HERE/'dashboard.html.tmpl').read_text()
    embedded=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    for key,value in {'__TITLE__':escape(data['league_label']),'__SIBLING__':sibling,
        '__SIBLING_LABEL__':"women's basketball" if sibling=='ncaaw' else "men's basketball",
        '__LEAGUE__':league,'__EVIDENCE__':embedded,
        '__REVIEW_DATE__':date.fromisoformat(data['published_snapshot_date']).strftime('%d %B %Y')+' UTC',
        '__HANDOFF_DEMO__':json.dumps(handoff_demo(),sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
        '__SPREAD_ATS_DEMO__':json.dumps(spread_ats_demo(),sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
        '__PREFLIGHT_DEMO__':json.dumps(preflight_scenarios(),sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
        '__PROGRESS_DEMO__':json.dumps(demo_scenarios(),sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')}.items():template=template.replace(key,value)
    return template


def landing_status(data):
    """Derive the landing status from the same aggregates as both track pages."""
    a = data[0]['current_owner_attempt']
    gaps = data[0]['current_coverage_gaps']
    result = data[0]['current_results_status']
    if any(d['current_owner_attempt']['release'] != a['release'] or d['coverage_evidence_release'] != data[0]['coverage_evidence_release'] for d in data):
        raise ValueError('landing release disagreement')
    if sum(d['observed_inventory']['candidate_games'] for d in data) != gaps['both_leagues_source_records']:
        raise ValueError('landing source inventory closure')
    if sum(d['current_results_status']['authenticated_issue_rows_this_league'] for d in data) != result['authenticated_issue_rows_both_leagues']:
        raise ValueError('landing issue population closure')
    release = escape(a['release'])
    capture = datetime.fromisoformat(data[0]['freshness']['source_acquisition_completed_at']).strftime('%d %b %Y, %H:%M UTC')
    previous = scientific_attempt(data[0])
    return (f'<strong>{release}: {a["completed_scientific_stages"]} of {a["planned_scientific_stages"]} stages completed; child exited without its terminal return.</strong>'
            '<p>The injury stage exhausted a bounded resource wait. The wrapper later recorded child exit −9 and an unpersisted return; the cause of that exit is unknown. Complete new-fit counts, final CPU/peak-memory totals and the external shell exit remain unavailable in this public snapshot. Unknown work is not zero work. B046 is prepared; no B046 owner execution or model gain is claimed.</p>'
            f'<p>Dated B044 readback verified 90 preserved chunks, {gaps["market_observations"]:,} observations and 1,504,058,360 logical bytes through 182 full storage GETs. Those remain B044 reads of earlier evidence with unchanged clocks; they are not B045 provider acquisition or earlier availability proof.</p>'
            f'<p>Preserved {previous["release"]} research: {previous["completed_scientific_stages"]}/{previous["planned_scientific_stages"]} stages, {previous["new_real_target_fits"]} target / {previous["new_calibration_fits"]} scalar / {previous["new_empirical_residual_fits"]} empirical fits. {result["authenticated_issue_rows_both_leagues"]:,} existing research issue rows across {result["authenticated_issue_games_both_leagues"]} games retain their B042 identity. Its durable pre-study report contains {result["pre_study_target_rows"]:,} target rows and {result["browser_display_rows"]:,} browser rows.</p>'
            f'<p>The dated inventory contains {gaps["market_observations"]:,} market observations and {gaps["both_leagues_source_records"]:,} source/candidate records with {gaps["both_leagues_observed_finals"]:,} numeric finals. Source acquisition completed {capture}; this is a static evidence snapshot, not a reconciled physical-game denominator.</p>'
            '<p>The B043 129-game men’s Polymarket international comparison remains reconstructed: the model has higher pick accuracy but worse log loss and Brier. The earlier 122-game panel and historical selections remain unchanged. No injury improvement, market-path gain or profitable betting record is established.</p>'
            '<p>The new <a href="'+HOST+'/tracks/ncaam/index.html#spread-review">spread and ATS example</a> separates a quoted-line cover probability from a past win–loss–push record. It uses invented inputs with explicit clocks, orientation, pushes and missing-data denominators.</p>')


def render_landing(data):
    cards=[]
    for d in data:
        model=next(m for m in d['models'] if m['target']=='win' and 'LogLoss' in m['selected_for'])
        p=model['panels']['pooled'];league=d['league'];label="Men's basketball" if league=='ncaam' else "Women's basketball"
        cards.append(f'<a class="card" href="{HOST}/tracks/{league}/index.html"><div class="label">{label}</div><div class="score">{p["LogLoss"]:.4f}<span>historical log loss</span></div><p>{p["N"]:,} games · two separately evaluated seasons</p><strong>Explore the evidence <span aria-hidden="true">↗</span></strong></a>')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Sports Edge Lab college basketball: objective-specific historical evidence, uncertainty and reproducible engineering contracts."><title>NCAA Evidence Review · Sports Edge Lab</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#172723;font:16px/1.65 system-ui,sans-serif}main{max-width:1110px;margin:auto;padding:36px 32px 42px}a{color:#136a55;text-underline-offset:4px}a:focus-visible{outline:3px solid #285b86;outline-offset:5px}header{display:flex;align-items:center;justify-content:space-between;padding-bottom:30px;border-bottom:1px solid #cedbd0;font-size:13px}.brand{font-weight:750;letter-spacing:-.035em;font-size:18px;color:#172723;text-decoration:none}.tag{font-size:11px;letter-spacing:.17em;text-transform:uppercase;font-weight:700;color:#136a55;margin-top:64px}h1{font-size:clamp(44px,7vw,78px);line-height:1.04;letter-spacing:-.065em;max-width:840px;margin:20px 0 26px}h1 span{color:#136a55}.intro{max-width:740px;color:#53665a;font-size:19px;margin:0}.cards{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:42px 0 25px}.card{display:block;border:1px solid #c8d8ca;background:#fffefb;border-radius:18px;padding:28px;text-decoration:none;color:#172723;transition:transform .15s,border-color .15s}.card:hover{border-color:#136a55;transform:translateY(-3px)}.label{font-size:15px;font-weight:700}.score{font-size:59px;line-height:1.15;letter-spacing:-.06em;margin-top:20px;font-variant-numeric:tabular-nums}.score span{display:block;font-size:12px;letter-spacing:0;color:#596b65;font-weight:400;margin-top:9px}.card p{font-size:13px;color:#596b65;margin:18px 0 25px}.card strong{font-size:13px;display:flex;justify-content:space-between;color:#136a55}.note{font-size:13px;color:#596b65;max-width:900px}.status{margin-top:34px;padding:22px 24px;border-radius:14px;background:#fcf0d5;border:1px solid #e7d7b2}.status strong{color:#714217;font-size:14px}.status p{margin:8px 0 0;font-size:13px;color:#66513a}.links{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;border-top:1px solid #cedbd0;margin-top:44px;padding-top:26px}.links a{font-weight:700;font-size:13px}.links p{font-size:12px;color:#596b65}.footer{font-size:11px;color:#68796e;margin-top:40px}@media(max-width:640px){main{padding:25px 20px}.tag{margin-top:40px}h1{font-size:47px}.intro{font-size:16px}.cards,.links{grid-template-columns:1fr}.cards{gap:15px;margin-top:30px}.card{padding:25px}.score{font-size:50px}.links{gap:7px}.status{padding:18px}.footer{line-height:1.8}}@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style></head><body><main><header><a class="brand" href="https://github.com/alvaromendizabal/sports-edge-lab">Sports Edge Lab</a><span>College basketball / 2026</span></header><div class="tag">Evidence review · '''+date.fromisoformat(data[0]['published_snapshot_date']).strftime('%d %B %Y')+''' UTC</div><h1>Forecasts you can<br><span>interrogate.</span></h1><p class="intro">Explore the historical models by objective, inspect the uncertainty, and follow the engineering contracts that keep current-season claims separate.</p><section class="cards" aria-label="Separate NCAA basketball reviews">'''+''.join(cards)+'''</section><p class="note">These are development-exposed historical selections on exact shared cohorts, not untouched test results or a prospective betting record. Men's and women's populations remain separate. The public model IDs disclose results while keeping active research recipes private.</p><section class="status">'''+landing_status(data)+'''<p><a href="'''+HOST+'''/private-report/index.html"><strong>Open your private game report →</strong></a> Load the delivered JSON to inspect every supplied game and unresolved market record locally in this browser. The report is never uploaded.</p></section><section class="links" aria-label="Review resources"><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/tree/main/examples/ncaa_review">Run the invented example ↗</a><p>Chronological scoring, explicit fees, measured admission, portable preflight and honest progress estimates. Python standard library only.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/ncaa_review/README.md">Read the methodology ↗</a><p>Selection exposure, calibration, point errors and week-level descriptive uncertainty, with meaningful negative tests.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/docs/PUBLICATION_BOUNDARY.md">Inspect the publication boundary ↗</a><p>Sanitized aggregates and generic contracts are public. Private data, active weights and execution artifacts remain private.</p></div></section><footer class="footer">Built by Alvaro Mendizabal · Sports Edge Lab<br>Static, self-contained review pages. No tracking, external fonts, third-party scripts or live provider requests.</footer></main></body></html>
'''


def outputs():
    data=[evidence(league) for league in ('ncaam','ncaaw')]
    return {**{ROOT/'tracks'/d['league']/'index.html':render_track(d) for d in data},
            ROOT/'docs/ncaa/index.html':render_landing(data),
            ROOT/'docs/ncaa/private-report/index.html':(HERE/'private_report.html.tmpl').read_text()}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    receipts=[]
    for path,text in outputs().items():
        if args.check:
            if not path.is_file() or path.read_text()!=text:raise SystemExit('Stale generated page: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        b=text.encode();receipts.append({'path':str(path.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    print(json.dumps({'status':'EXACT_GENERATION_VERIFIED' if args.check else 'GENERATED','pages':receipts},indent=2))


if __name__=='__main__':main()

