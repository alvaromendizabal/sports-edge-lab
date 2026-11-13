"""Generate static NCAA review pages from the committed sanitized aggregates."""
from __future__ import annotations
import argparse
from datetime import date, datetime
import hashlib
from html import escape
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from progress import demo_scenarios
from preflight import demo_scenarios as preflight_scenarios
from handoff import demo as handoff_demo
from spread_ats import demo as spread_ats_demo

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
HOST='https://alvaro-ncaa-research-review.alv-mendizabal.chatgpt.site'


def latest_review_evidence():
    """Read the dated aggregate update without rewriting older model exports."""
    value=json.loads((HERE/'evidence/B057_ACTUAL_B058_PREPARED.json').read_text())
    actual=value['latest_actual_owner'];prepared=value['prepared_engineering'];stages=actual['stages']
    if (value['public_scope']!='SANITIZED_AGGREGATES_ONLY' or actual['release']!='B057'
            or prepared['release']!='B058' or sum(stages[k] for k in ('completed','failed','unentered'))!=stages['total']):
        raise ValueError('latest NCAA aggregate identity or stage closure')
    checks=actual['owner_fixture_validation']
    if sum(checks[k] for k in ('passed','skipped','failed','errors'))!=checks['planned']:
        raise ValueError('latest NCAA fixture population closure')
    coverage=value['latest_source_coverage'];dates=coverage['date_query_dispositions']
    if (sum(dates[k] for k in ('valid','empty','halted','ambiguous'))!=dates['total']
            or coverage['new_canonical_source_game_rows']!=actual['fresh_source_game_rows']):
        raise ValueError('latest NCAA source population closure')
    if (prepared['new_owner_fits_credited']!=0 or prepared['new_owner_forecasts_credited']!=0
            or prepared['new_model_improvement_claim'] or prepared['current_season_outcomes_select_champions']):
        raise ValueError('prepared NCAA work cannot acquire owner science credit')
    return value


def latest_review_html():
    value=latest_review_evidence();a=value['latest_actual_owner'];p=value['prepared_engineering']
    coverage=value['latest_source_coverage'];dates=coverage['date_query_dispositions']
    s=a['stages'];f=a['frozen_research'];checks=a['owner_fixture_validation']
    link='https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/ncaa_review/evidence/B057_ACTUAL_B058_PREPARED.md'
    return (
        '<strong>Latest actual owner result · B057 · November 10, 2026 UTC.</strong>'
        f'<p><b>{s["completed"]}/{s["total"]} stages completed, {s["failed"]} failed and {s["unentered"]} unentered.</b> '
        f'The partial run preserved <b>{a["new_committed_fits"]["target_estimator"]} new target fits</b> and '
        f'<b>{f["completed_contexts"]} completed frozen contexts with {f["prediction_rows"]:,} prediction rows</b>. '
        f'The full frozen registry contains {f["registered_contexts"]:,} contexts. These are population/recipe/season contexts and prediction records, not unique physical games or current issues. '
        'The preserved manifests contain no completed metric-comparison or candidate-eligibility rows; they do not establish a new performance score.</p>'
        f'<p><b>{a["fresh_source_game_rows"]} new fresh source game rows; {f["new_current_forecasts"]} new current forecasts; '
        f'{f["promotions"]} promotions.</b> Restoration and provider request counts remain separate. '
        f'Recorded owner time: <b>{a["elapsed_seconds"]:,.3f} seconds</b>. Attributable cost and a defensible whole-successor ETA remain unknown.</p>'
        f'<p>Frozen research stopped at <code>{escape(a["failure"]["category"])}</code>. '
        'Committed work remains recoverable. The full comparison, metric-specific champion selection and selected rolling work remain incomplete; a validation failure does not establish a feature loss or a platform root cause.</p>'
        f'<p>The actual owner checks recorded <b>{checks["passed"]:,} passed, {checks["skipped"]} skipped, '
        f'{checks["failed"]} failed and {checks["errors"]} errors</b>. '
        f'<b>{a["owner_notebook_validation"]["executed_jupyter_cells"]} Jupyter cells</b> executed in the owner environment. '
        'Those engineering checks are distinct from predictive performance.</p>'
        f'<p>The latest schedule display records <b>{coverage["provider_native_fullseason_display_identifiers"]:,} provider-native identifiers</b>. '
        f'Its {dates["total"]:,} date-query dispositions comprise {dates["valid"]} valid, {dates["empty"]} empty, {dates["halted"]} halted and {dates["ambiguous"]} ambiguous results. '
        'Display IDs do not certify unique games, complete seasons or qualified model inputs. '
        f'The {coverage["retained_prior_canonical_source_identities"]:,} prior canonical identities retain their older clocks. '
        f'Latest injury inventory: {coverage["injury_observations"]:,} observations, {coverage["bound_injury_observations"]} bound. '
        f'Ranking support: {coverage["qualified_ranking_editions"]} qualified editions. Missing data never becomes an observed zero.</p>'
        '<h3>Prepared B058 engineering</h3><p>Early native-model serialization checks, verified prior-fit recovery, bounded scalar comparisons and partial-result reports are implemented preparation. '
        f'<b>{p["inherited_scalar_candidates"]} inherited candidates; {p["new_feature_count"]} newly engineered features.</b> '
        'Standalone, additive and removal studies retain negative findings and unavailable features. Fixed blend and cross-family error diagnostics reuse predictions; they do not create extra fits or automatic champions.</p>'
        '<p><b>2024–25 and 2025–26 supply frozen historical evaluation; 2026–27 remains prospective monitoring.</b> '
        'Only qualified metric champions and precommitted selected ensemble components advance to expensive rolling fits. Current-season outcomes do not select champions. Original issues and reconstructions remain separate.</p>'
        '<p>B058 local synthetic tests are separate from an actual successor owner result. No new owner forecast or model improvement is claimed. '
        f'<a href="{link}">Read the actual-versus-prepared aggregate evidence</a>, including the preserved earlier unfavorable comparison and open coverage gaps.</p>'
        '<p><b>Earlier dated evidence follows.</b> Its original clocks, populations and status labels are retained; the latest actual owner result is B057 above.</p>')

B056_CHAMPION_POLICY=(
    '<strong>Prepared B056 policy · completed-season research, then metric champions · November 10, 2026 UTC.</strong>'
    '<p>The registered research comparison retains <b>10 model families and 26 target heads</b> on the completed <b>2024–25 and 2025–26 seasons</b>, with frozen evaluation rules and separate men’s and women’s populations. Seven metric roles select eligible champions: <b>winner accuracy, winner log loss, winner Brier, margin MAE, margin RMSE, total MAE and total RMSE</b>. Current <b>2026–27 outcomes cannot select or promote a model</b>.</p>'
    '<p><b>Current rolling fits are limited to qualified native champions and the selected, precommitted components of a champion ensemble.</b> The full research registry is not refit for every current game. Each selected configuration uses only eligible information available before that game. Current-season historical rolling reconstructions stay separate from original frozen forecasts, numeric unissued references and genuinely issued future forecasts; an old game never acquires a retroactive issue timestamp.</p>'
    '<details><summary>Feature research and remaining evidence</summary><p>The prepared V5 bank registers <b>202 scalar interaction and nonlinear candidates across 44 state columns</b>, with <b>seven groups and 44 group-ablation plans</b>. The 202 individual scalar ablations remain registered and pending. These are implementation and study-plan counts, with <b>no new owner results or improvement credit</b>. The historical configuration registry is still incomplete; no claim is made that every earlier variant has been recovered. Earlier negative findings and original forecasts remain preserved. AP/Coaches still has <b>zero admitted ranking features</b>. Package-validation and actual-owner evidence stay separate.</p></details>'
    '<p><b>One-PYZ handoff:</b> upload the final PYZ, then copy the matching one-line command from its handoff or chat. No command TXT upload is required. The plain Python command checks the delivered bytes and SHA-256 before ZIP imports and then runs the sealed gate; an optional saved TXT is only a convenience. Use the command matched to that exact delivered release. This public viewer does not start the owner workflow.</p>'
    '<p><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/ncaa_review/MODEL_CARD.md">Read the NCAA policy and evidence model card</a>. The policy is prepared implementation; the authenticated B055 result below remains the latest actual owner evidence displayed here.</p>'
)

B055_OWNER_STATUS=(
    '<strong>Latest owner result · B055 · November 9, 2026 UTC.</strong>'
    '<p><b>New rolling work was committed before shared-resource admission deferred the run.</b> The recorded result is <code>RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED</code>, with <code>AdmissionDeferred</code> and <code>WITHIN_STAGE_RESOURCE_HEADROOM_UNAVAILABLE</code>. The run completed <b>9/17 stages</b>; <b>one failed wrapper stage</b> and <b>seven unentered stages</b> remain separate from its inner resource disposition. Recorded owner wall time is <b>71,209.031 seconds</b>. No platform root cause, measured speedup, attributable cost or remaining-run ETA is inferred.</p>'
    '<p>The authenticated typed ledger contains <b>2,583 new physical fits: 2,514 target, 45 scalar and 24 empirical</b>. The rolling subset accounts for <b>2,413 target fits</b> and <b>26,122 prediction commits with zero new physical fits</b>. The full ledger has <b>28,798 committed contracts</b>. These contracts, reused accesses, prediction records and fits are different units; the compact checkpoint inventory still requires full remote closure at actual use.</p>'
    '<p>The separate owner rolling report records <b>18 new issued forecasts</b>, <b>5,949 reconstructed rows</b>, <b>6,093 numeric unissued reference rows</b> and <b>4,032 source-only blocked rows</b>. These are report populations, not unique physical games or a complete-season certificate. It records <b>zero promotions</b>. B055 is the latest partial owner work; earlier scientific baselines and immutable issues remain dated evidence. No new model-improvement claim follows from the work counts.</p>'
    '<p><a href="'+HOST+'/private-report/index.html#v4-review">Open the actual B055 rolling review</a> to keep original issues, reconstruction, future issues and source references separate. The additive <a href="'+HOST+'/private-report/index.html#execution-review">B056 execution-review panel</a> reports a bounded admitted batch, completed dispositions, remaining work and explicit resource scope. Registered research contexts never become a physical-fit count or whole-project ETA.</p>'
    '<p><b>AP and other ranking transfer remains incomplete.</b> The actual B055 ranking report retains four source-catalog entries but <b>zero qualified editions, zero mapped ranking rows and zero newly admitted ranking features</b>. March Madness remains at its reviewed source revision; reusable transforms and a transfer crosswalk do not prove every feature has been acquired, admitted, fit or tested on NCAA games. Both ranking requests returned HTTP 200, but the native league-identity gate rejected their bodies before edition parsing; the source-authorization contract was also absent. The isolated B056 reader has now parsed four candidate editions and 100 edition-scoped native team mappings in local replay of those exact bytes. Publication clocks remain null and all four editions remain authorization-blocked; this replay supplies no owner fit or forecast credit.</p>'
)

B054_OWNER_STATUS=(
    '<strong>Latest owner check · B054 · November 8, 2026 UTC.</strong>'
    '<p><b>The required package checks stopped the run before research began.</b> All <b>17 research stages were unentered</b>: zero completed and zero numbered stages failed. The run-level result is <code>FAILED_PARTIAL_WORK_PRESERVED</code>. The owner suite recorded <b>2,314 passed, one failed, one optional skip and zero errors</b> across 2,316 cases. A required mutation-rejection assertion failed; this is an implementation check, not a scientific model loss or an established platform fault.</p>'
    '<p>The typed scientific ledger was not initialized. The return reports <b>zero new owner fits</b>; it does not supply an empty committed-fit ledger. No new source acquisition, forecast or model improvement is credited. Diagnostic-return persistence is separate from research acquisition. Recorded wall time is <b>270.817 seconds</b>; literal external terminal lines were not supplied.</p>'
    '<p><b>B053 remains the latest admitted partial scientific work.</b> Load <code>B053_CURRENT_DASHBOARD_DATA.json</code> for its existing game/model report. B054 supplied no completed V4 study to load. The next <a href="'+HOST+'/private-report/index.html#refresh-review">refresh-coverage view</a> accepts the separately supplied B055 owner manifest: plans, missed windows, source blocks and actual issue evidence remain separate.</p>'
)

B053_OWNER_STATUS=(
    '<strong>Retained B053 scientific result · authenticated November 8, 2026 UTC.</strong>'
    '<p><b>Real partial scientific work is preserved.</b> The owner recorded <b>9/16 stages completed</b>, <b>one failed wrapper stage</b> and <b>six not entered</b>. Shared-resource admission deferred within the injury stage. The outer wrapper failure and the inner <code>AdmissionDeferred</code> state remain distinct; no platform root cause is inferred.</p>'
    '<p>The typed ledger records <b>145 new target fits, 45 new scalar fits and 24 new empirical fits</b>, with <b>360 newly committed contracts</b>. It separately retains <b>108 reused historical target fits</b>, <b>13 reused native fits</b> and <b>7 reused scalar fits</b>. The broader accounting contains <b>557 receipt roles and 577 contracts</b>; roles, contracts, forecasts and physical fits are different counts.</p>'
    '<p>The current private pre-study game report is available for inspection. It is a partial owner checkpoint, not a completed rolling frontier study. B046 remains preserved as the earlier scientific baseline. No new champion, complete-season certificate, qualified spread-probability population or current-season promotion is asserted.</p>'
    '<p><a href="'+HOST+'/private-report/index.html#v4-review">The V4 rolling review</a> separates original frozen issues, historical rolling reconstruction, genuinely future rolling issues and model/market/source references. Prepared ranking and rolling capabilities require an actual admitted owner run. AP and other ranking editions require source, publication, availability and team-identity evidence; missing rankings are never replaced by invented ranks. Private recipes and inputs remain in the owner handoff.</p>'
)

B052_OWNER_STATUS=(
    '<strong>Dated B052 return · authenticated November 8, 2026 UTC.</strong>'
    '<p><b>Source inventory, parent restoration and current feature work were preserved.</b> Owner run <code>20261108T063651Z_d7a6c2ff</code> recorded <b>FAILED_PARTIAL_WORK_PRESERVED</b>: <b>5/16 stages completed</b>, <b>zero stages recorded failed</b> and <b>11 not entered</b>. The run stopped between stages 05 and 05b while serializing its coverage summary, with <code>B048_SUMMARY_EXCEEDS_REPORT_PART_BOUND</code>. The stage ledger and run-level failure are separate evidence; no hardware or connection cause is asserted.</p>'
    '<p>The actual owner-produced <code>B052_FULL_SEASON_SCHEDULE_COMPACT.json</code> contains all <b>23,603 retained provider-native IDs</b> in <b>4,744,902 bytes</b>, with the original B051 source-index owner, source version and clocks. The earlier 4,744,935-byte assistant projection remains dated evidence. <b>2,520 exact tip times remain null</b>; 39 ambiguous date responses and 110 rejected source records still prevent a complete-season claim. Schedule observations do not supply missing forecasts or change the older model denominators.</p>'
    '<p>The new <a href="'+HOST+'/private-report/index.html#eligibility-review">per-game input eligibility view</a> accounts for <b>1,793 exact source identities = 1,322 input-gate passes + 445 rejected feature rows + 26 without a feature row</b>. It retains every overlapping failure reason, original input clocks and source references. Input-gate passes are not forecast issues. The old 447 per-game rejection causes remain unretained and are not inferred.</p>'
    '<p>The owner fixture suite recorded <b>1,819 passed, 1 skipped, zero failures and zero errors</b>; this is fixture validation, not new scientific work. The typed physical ledger verifies <b>zero newly committed target, scalar, empirical or unclassified model artifacts</b> and <b>108 reused historical target fits</b>; uncommitted estimation remains unasserted. Recorded wall time is <b>748.452 seconds</b>. No new rolling forecast, cover probability, injury/path gain or model improvement is credited.</p>'
    '<p>Authentication verifies safe unique regular names, CRCs and exact manifest closure across <b>4 outer, 201 nested-return and 501 embedded-source members</b>, active B052/runtime b052. Recorded completion and the final-return readback receipt remain separate from absent literal RETURN, worker-terminal, bootstrap-terminal, source-preflight, source-retrieval and observed shell-exit lines.</p>'
    '<p>B046 remains the last scientific partial execution at 9/16. The older 47,130-row baseline and 2,445 display groups retain zero supplied per-game rolling winner records and zero qualified cover/push/loss groups. All 1,923 immutable issues and the 52-context priority-calibration and all-family paired-study gaps remain unchanged. Current-season outcomes cannot select or promote a model.</p>'
)

B051_OWNER_STATUS=(
    '<strong>Dated B051 return · authenticated November 8, 2026 UTC.</strong>'
    '<p><b>Source refresh completed; model restoration stopped.</b> Owner run <code>20261108T015946Z_d34f8020</code> recorded <b>FAILED_PARTIAL_WORK_PRESERVED</b>: <b>1/16 stages completed</b>, parent restoration failed, and 14 stages were not entered. The exact error is <code>B035_REUSE_SCIENTIFIC_IMPLEMENTATION_CHANGED:b032_resume.py</code>. The preserved return identifies this compatibility guard; it does not establish a hardware or connection cause.</p>'
    '<p>The owner produced a full-season collection report accounting for <b>1,460/1,460 provider, gender and date slots</b>: 458 validated responses, 963 empty responses and 39 ambiguous responses. Its retained index has <b>23,603 provider-native IDs</b> and 110 rejected source records. These are source-specific identities, not a cross-provider count of physical games or forecasts. The original 25 MiB display export contains references and zero rows. The private <code>B052_FULL_SEASON_SCHEDULE_COMPACT.json</code> losslessly exposes all <b>23,603 retained index records</b> in <b>4,744,935 bytes</b>, below the unchanged limit. It is a review-derived projection of that owner capture, with no new owner run or forecast.</p>'
    '<p>The initialized physical ledger verifies <b>zero newly committed target, scalar, empirical or unclassified model artifacts</b>; uncommitted estimation remains unasserted. Owner fixtures passed <b>1,686 cases with 1 skipped</b>, zero failures and zero errors. The earlier local 1,687/1,687 result remains preparation evidence. No new rolling forecast, cover probability, injury/path gain or model improvement is credited.</p>'
    '<p>Authentication verifies safe unique regular names, CRCs and exact manifest closure across <b>4 outer, 178 nested-return and 478 embedded-source members</b>, with active B051/runtime b051. Recorded completion and the final-return readback receipt remain separate from absent literal RETURN, worker-terminal, bootstrap-terminal, source-preflight, source-retrieval and observed shell-exit lines.</p>'
    '<p>B046 remains the last scientific partial execution at 9/16. The older 47,130-row baseline and 2,445 display groups retain zero supplied per-game rolling winner records and zero qualified cover/push/loss groups. The 52-context priority-calibration gap and all-family paired-study gap remain open. Current-season outcomes cannot select or promote a model. B052 preparation receives no owner-execution or improvement credit.</p>'
)

B050_OWNER_STATUS=(
    '<strong>Dated B050 return · authenticated November 8, 2026 UTC.</strong>'
    '<p>The actual owner run <code>20261107T235154Z_0a962d1c</code> recorded <b>FAILED_PARTIAL_WORK_PRESERVED</b>: <b>0/16 stages completed</b>, the first source-refresh stage failed, and the other 15 stages were not entered. Its owner fixture gate passed <b>1,578 cases with 1 skipped</b>, zero failures and zero errors. The earlier local 1,579/1,579 result remains preparation evidence.</p>'
    '<p>Source acquisition and bounded observation queues were preserved before a schedule-input validation failure. The exact acquisition-report reference is <b>113,330,820 bytes</b>, exceeding the schedule reader\'s <b>48 MiB</b> bound. The recorded error is <code>B050_SCHEDULE_REFERENCE_SCHEMA_OR_BOUND</code>. The full-season collector had not initialized; this return supplies no authenticated full-season schedule export to load. The evidence identifies this input-bound failure, not a hardware or connection cause.</p>'
    '<p>The initialized physical ledger verifies <b>zero newly committed target, scalar or empirical fits and zero committed model artifacts</b>. That does not assert zero uncommitted fit attempts. No new owner forecast, rolling result, injury gain, cover probability, model improvement or complete-season claim is credited. B046 remains the last scientific partial execution at 9/16; the historical metrics below retain their original scientific source.</p>'
    '<p>Physical authentication verifies safe unique regular names, CRCs and manifest closure across <b>4 outer, 151 nested-return and 459 embedded-source members</b>, with active release B050/runtime b050. Recorded completion and final-return receipts are retained separately from literal terminal evidence; no separate worker-terminal, bootstrap-terminal, source-preflight or observed shell-exit lines accompanied this attachment.</p>'
    '<p>The retained baseline still has 47,130 rows and 2,445 separate display groups, with zero supplied per-game rolling winner records and zero qualified cover/push/loss groups. The 52-context priority-calibration gap and all-family paired-study gap remain open. B051 is successor preparation until authenticated owner work establishes otherwise; current-season outcomes cannot select or promote a model. Earlier dated startup and owner records follow.</p>'
)

LATEST_OWNER_STARTUP=(
    '<strong>Dated reported B049 startup · November 7, 2026 UTC.</strong>'
    '<p>The reported B049 command stopped before the research program started, with a Python archive-reading error and observed shell exit 1. No program return was supplied for that attempt, and the file on the owner machine has not been authenticated. No new game forecasts, provider data or model improvements are credited to it.</p>'
    '<p>The B050 viewer preparation makes original and per-game rolling records easier to compare, exposes hidden-game counts and exports the exact filtered inventory. Load the supplied baseline dashboard JSON and its matching identity overlay to inspect the retained evidence. Earlier source dates and scientific results remain in force.</p>'
)

B048_OWNER_STATUS=(
    '<strong>Dated B048 return · authenticated November 7, 2026 UTC.</strong>'
    '<p>B048 ran and recorded <b>FAILED_PARTIAL_WORK_PRESERVED</b> at its fresh-package fixture gate, before scientific stage entry: <b>0/16 stages completed</b>, all 16 unreached. The owner summary records zero new owner fits. No new forecast, provider coverage, model improvement or complete-season certification is credited.</p>'
    '<p>The actual owner suite recorded <b>1,456 parent cases: 1,454 passed, 1 skipped and one errored case</b>. That single unsuccessful case emitted one error event and one failure event across its subtests. The regression concerns mutation detection in the predecessor-worker liveness guard. The earlier local <b>1,456/1,456 passed</b> result remains dated preparation evidence.</p>'
    '<p>The physical return passes safe casefold-unique regular-file names, every CRC and exact active-manifest closure across <b>4 outer, 99 nested owner-return and 434 embedded-source members</b>. Its source exactly matches the prepared B048 package, and the retained final-return full-readback receipt matches the enclosed bytes. Separate literal worker-terminal and observed shell-exit receipts remain unobserved. Earlier B047R1 and B046 evidence below retains its dated scope.</p>'
)

B047R1_PHYSICAL_STATUS=(
    '<strong>Dated B047R1 return · authenticated November 7, 2026 UTC.</strong>'
    '<p>B047R1 ran and recorded <b>FAILED_PARTIAL_WORK_PRESERVED</b> before scientific stage entry: <b>0/16 stages completed</b>, all 16 unreached, zero newly committed target/scalar/empirical fits or contract objects, and zero reuses. No new forecast, provider coverage, model improvement or complete-season certification is credited.</p>'
    '<p>The uploaded physical return now passes safe casefold-unique regular-file names, all CRCs and exact active-manifest closure across 4 outer, 105 nested owner-return and 416 embedded-source members. Its nested bytes match the previously verified cloud return. Owner fixtures recorded 1,368 passed / 1 skipped / 0 failures / 0 errors, separately from the earlier prepared 1,369/1,369 result.</p>'
    '<p>The retained durable-return record matches the enclosed bytes. Separate literal worker-terminal and observed shell-exit receipts remain unobserved. Earlier B046 results and the B047R1 prepared registry below retain their dated scope.</p>'
)

def review_date(data):
    return datetime.fromisoformat(data['published_snapshot_at']).astimezone(ZoneInfo('America/Los_Angeles')).strftime('%d %B %Y %Z')


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
    for attempt in [data['current_owner_attempt'], *data['owner_attempt_history']]:
        if attempt['release'] in ('B043', 'B044', 'B045', 'B046'):validate_stages(attempt)
        if attempt.get('completed_scientific_stages') == 0 and any(attempt.get(k, 0) != 0 for k in ('new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_prospective_issues', 'new_prediction_rows')):raise ValueError('unstarted science receives credit')
        if attempt.get('fit_count_status') == 'UNKNOWN_PENDING_COMPLETE_DURABLE_PRODUCER_AUDIT':
            if any(attempt[k] is not None for k in ('new_real_target_fits', 'league_new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_injury_fits', 'new_prediction_rows', 'new_prospective_issues', 'reused_target_fits')):raise ValueError('unknown owner work receives invented counts')
        if attempt['status'] == 'WORKER_EXITED_WITHOUT_TERMINAL_RETURN':
            if attempt['completed_at'] is not None or attempt['external_shell_exit_code'] is not None or attempt['durable_return_verified'] is not False:raise ValueError('unexpected exit receives unsupported terminal completion')
            if attempt['out_of_memory_proved'] or attempt['kill_cause'] != 'UNKNOWN':raise ValueError('unproved signal-exit cause')
    attempt = data['current_owner_attempt']
    if attempt['release'] == 'B046':
        if (attempt['new_real_target_fits'], attempt['new_calibration_fits'], attempt['new_empirical_residual_fits'], attempt['committed_contract_objects']) != (4033, 701, 24, 4851):raise ValueError('B046 physical typed fit scope')
        if not attempt['durable_return_verified'] or attempt['external_shell_exit_code'] is not None or attempt['new_prospective_issues'] is not None:raise ValueError('B046 terminal or owner-issue proof scope')
    b = data['b046_baseline_observation']
    if (b['browser_display_rows'] != b['game_model_rows'] + b['unresolved_source_candidate_rows'] or b['independent_metric_panels_checked'] != b['independent_model_panels_checked'] + b['independent_provider_panels_checked'] or b['independent_scalar_checks'] != b['independent_model_scalar_checks'] + b['independent_provider_scalar_checks'] or b['physical_universe_certified'] or b['new_fit_credit_from_report_recovery']):raise ValueError('B046 report or scientific scope')
    repair = data['b047_source_identity_repair']
    if (repair['comparison_contexts'] != repair['source_game_versions'] * repair['provider_products'] * repair['horizons'] * repair['evidence_tiers'] or repair['qualified_probabilities'] or repair['qualified_ats_records'] or repair['new_model_fits'] or repair['new_issues'] or not repair['source_bytes_and_clocks_unchanged']):raise ValueError('source repair gains unsupported scientific credit')
    j = data['b046_forecast_journal_observation']
    if (j['distinct_immutable_issues'] != j['b046_source_issues'] + j['b045_source_issues'] + j['b042_source_issues']
            or j['b046_source_issues'] != j['b046_baseline_rows'] + j['b046_journal_only_rows']
            or j['baseline_issued_rows'] != j['b046_baseline_rows'] + j['b045_source_issues'] + j['b042_source_issues']
            or j['owner_run_identity_proved'] or j['complete_remote_inventory_proved'] or j['new_issues_created_by_audit']
            or not all(j[k] for k in ('all_original_predictions_identities_and_clocks_match', 'original_outcomes_absent', 'original_server_intervals_end_by_cutoff'))):raise ValueError('B046 source journal scope')
    for fit_key, count_key in [('target_estimator_fits', 'new_real_target_fits'), ('scalar_calibration_fits', 'new_calibration_fits'), ('empirical_residual_fits', 'new_empirical_residual_fits')]:
        if sum(r[fit_key] for r in attempt['physical_family_totals'].values()) != attempt[count_key]:raise ValueError('B046 typed family closure')
    baseline = data['b045_baseline_observation']
    if baseline['source_release'] != 'B045' or baseline['new_issue_credit'] is not None or baseline['new_fit_credit_from_report_recovery'] != 0:raise ValueError('report labels receive unverified issue or fit credit')
    if (baseline['independent_model_panels_checked'] != baseline['independent_season_panels_checked'] + baseline['independent_weekly_panels_checked']
            or baseline['independent_metric_panels_checked'] != baseline['independent_model_panels_checked'] + baseline['independent_provider_panels_checked']
            or baseline['independent_scalar_checks'] != baseline['independent_model_scalar_checks'] + baseline['independent_provider_scalar_checks']
            or baseline['calibration_slope_intercept_independently_refit'] is not False):raise ValueError('unsupported metric reconciliation claim')
    journal = data['b045_forecast_journal_observation']
    if (journal['source_scope'] != 'B045_SOURCE_VERSION_NOT_OWNER_RUN_ID'
            or journal['b045_verified_issue_rows'] != journal['b045_distinct_issue_fingerprints']
            or journal['b045_verified_issue_rows'] != journal['b045_baseline_exact_match_rows'] + journal['b045_journal_only_rows']
            or journal['b045_baseline_exact_match_rows'] != baseline['source_labeled_b045_prospective_unsettled_rows']
            or journal['b045_games'] != baseline['source_labeled_b045_games']
            or journal['b042_retained_issue_rows'] != baseline['source_labeled_b042_prospective_settled_rows']
            or journal['baseline_prospective_exact_matches'] != journal['b045_baseline_exact_match_rows'] + journal['b042_retained_issue_rows']):raise ValueError('journal source and baseline population mismatch')
    if any(journal[key] is not True for key in ('original_issue_validation_passed', 'original_prediction_identity_and_clocks_unchanged', 'outcome_fields_absent_at_issue', 'issue_before_server_interval_upper', 'server_interval_upper_at_or_before_cutoff')):raise ValueError('unsupported original issue availability')
    if (journal['new_issues_created_by_audit'] != 0 or journal['baseline_rewritten'] is not False
            or journal['global_remote_inventory_exhaustion_proved'] is not False
            or journal['owner_run_identity_proved_by_journal'] is not False
            or journal['full_model_input_closure_proved'] is not False
            or journal['forecast_performance_or_profit_proved'] is not False):raise ValueError('journal audit grants unsupported scope or scientific credit')
    readback = dated_readback(data)
    if readback['source_release'] != scientific['release'] or readback['observations'] != data['current_coverage_gaps']['market_observations']:raise ValueError('readback evidence population')
    if readback['new_provider_requests'] != 0 or readback['new_fit_credit'] != 0 or readback['earlier_availability_credit'] is not False or readback['source_clocks_unchanged'] is not True:raise ValueError('readback grants unsupported credit')
    if data['prepared_execution']['owner_execution_observed'] is not False or data['prepared_execution']['new_scientific_credit'] != 0:raise ValueError('prepared execution receives credit')
    registry = data['prepared_model_registry']
    if (registry['release'] != data['prepared_execution']['release']
            or registry['family_count'] != len(registry['families'])
            or len({row['family'] for row in registry['families']}) != registry['family_count']
            or registry['target_head_count'] != sum(len(row['targets']) for row in registry['families'])
            or registry['new_owner_fits_credited'] != 0 or registry['measured_gain'] is not None
            or registry['current_outcomes_used_for_selection']):raise ValueError('prepared model registry receives unsupported scope or credit')
    frontier = data['current_frontier_research']
    if (frontier['release'] != data['current_owner_attempt']['release']
            or frontier['completed_paired_study'] or frontier['measured_gain'] is not None
            or frontier['current_outcomes_used_for_selection']):raise ValueError('uncompleted current frontier study receives credit')
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
        '__REVIEW_DATE__':review_date(data),
        '__B058_LATEST_REVIEW__':latest_review_html(),
        '__B056_CHAMPION_POLICY__':B056_CHAMPION_POLICY,
        '__B055_OWNER_STATUS__':B055_OWNER_STATUS,
        '__B054_OWNER_STATUS__':B054_OWNER_STATUS,
        '__B053_OWNER_STATUS__':B053_OWNER_STATUS,
        '__B052_OWNER_STATUS__':B052_OWNER_STATUS,
        '__B051_OWNER_STATUS__':B051_OWNER_STATUS,
        '__B050_OWNER_STATUS__':B050_OWNER_STATUS,
        '__B048_OWNER_STATUS__':LATEST_OWNER_STARTUP+B048_OWNER_STATUS,
        '__B047R1_PHYSICAL_STATUS__':B047R1_PHYSICAL_STATUS,
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
    baseline = data[0]['b045_baseline_observation']; journal = data[0]['b045_forecast_journal_observation']
    if any(d['b045_forecast_journal_observation'] != journal for d in data):raise ValueError('landing journal population disagreement')
    b=data[0]['b046_baseline_observation']; repair=data[0]['b047_source_identity_repair']
    return (latest_review_html() + '<details><summary>Dated B056 preparation and B055 owner result</summary>' + B056_CHAMPION_POLICY + B055_OWNER_STATUS + '</details><details><summary>Dated B054 startup result</summary>' + B054_OWNER_STATUS + '</details>' + B053_OWNER_STATUS + '<details><summary>Earlier dated owner returns</summary>' + B052_OWNER_STATUS + B051_OWNER_STATUS + B050_OWNER_STATUS + LATEST_OWNER_STARTUP + B048_OWNER_STATUS + B047R1_PHYSICAL_STATUS + '</details>'
            + f'<p><strong>Dated {release}: {a["completed_scientific_stages"]}/{a["planned_scientific_stages"]} stages completed; partial work and final return preserved.</strong></p>'
            f'<p>The authenticated physical ledger reconciles {a["new_real_target_fits"]:,} target, {a["new_calibration_fits"]:,} scalar and {a["new_empirical_residual_fits"]:,} empirical fits across {a["committed_contract_objects"]:,} contract objects. Injury research deferred at its bounded shared-memory admission gate. Full model import and new scientific superiority are not established by that accounting.</p>'
            f'<p>The B046 pre-study view contains {b["target_rows"]:,} target rows, {b["game_model_rows"]:,} game-model rows and {b["browser_display_rows"]:,} display rows, including three unresolved source candidates. Independent arithmetic reconciles {b["independent_metric_panels_checked"]:,} model/provider panels through {b["independent_scalar_checks"]:,} checks with zero mismatches. These source/version populations do not certify every official physical game.</p>'
            '<p>The private report opens with a filterable season table: winner, home probability, projected scores, margin, total, spread qualification and all three providers. Detailed games preserve every supplied model/version. Readable season/week metrics, a recovery queue and a bounded frontier/ATS viewer keep each missing capability visible with an action.</p>'
            f'<p>The exact team-identity repair restores {repair["source_game_versions"]:,} source-game bindings and {repair["comparison_contexts"]:,} explicit comparison contexts. All remain unavailable under their retained evidence gates: zero qualified spread probabilities, zero admitted ATS records and zero model fits from this repair.</p>'
            f'<p>Dated B045 baseline evidence remains {baseline["target_rows"]:,} target / {baseline["browser_display_rows"]:,} display rows and {baseline["independent_metric_panels_checked"]:,} metric panels. Its {journal["b045_verified_issue_rows"]} source-version issues and {journal["b045_journal_only_rows"]} journal-only rows remain separate. The 339 B042 immutable issues, B043 scientific results and 129/122-game comparisons are retained unchanged.</p>'
            '<p>Historical 2024–25 and 2025–26 evaluations are development-exposed. Current 2026–27 data cannot select or promote a model. The dated B047R1 preparation registered ten base estimator families and 26 target heads, including Extra Trees classification and regression. B047R1 and B048 were subsequently owner-executed and failed before scientific stage entry, with no new scientific results credited. Exact missing clocks, official denominator gaps and unfinished injury/path comparisons remain open.</p>')


def render_legacy_landing(data):
    cards=[]
    for d in data:
        model=next(m for m in d['models'] if m['target']=='win' and 'LogLoss' in m['selected_for'])
        p=model['panels']['pooled'];league=d['league'];label="Men's basketball" if league=='ncaam' else "Women's basketball"
        cards.append(f'<a class="card" href="{HOST}/tracks/{league}/index.html"><div class="label">{label}</div><div class="score">{p["LogLoss"]:.4f}<span>historical log loss</span></div><p>{p["N"]:,} games · two separately evaluated seasons</p><strong>Explore the evidence <span aria-hidden="true">↗</span></strong></a>')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Sports Edge Lab college basketball: objective-specific historical evidence, uncertainty and reproducible engineering contracts."><title>NCAA Evidence Review · Sports Edge Lab</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#172723;font:16px/1.65 system-ui,sans-serif}main{max-width:1110px;margin:auto;padding:36px 32px 42px}a{color:#136a55;text-underline-offset:4px}a:focus-visible{outline:3px solid #285b86;outline-offset:5px}header{display:flex;align-items:center;justify-content:space-between;padding-bottom:30px;border-bottom:1px solid #cedbd0;font-size:13px}.brand{font-weight:750;letter-spacing:-.035em;font-size:18px;color:#172723;text-decoration:none}.tag{font-size:11px;letter-spacing:.17em;text-transform:uppercase;font-weight:700;color:#136a55;margin-top:64px}h1{font-size:clamp(44px,7vw,78px);line-height:1.04;letter-spacing:-.065em;max-width:840px;margin:20px 0 26px}h1 span{color:#136a55}.intro{max-width:740px;color:#53665a;font-size:19px;margin:0}.cards{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:42px 0 25px}.card{display:block;border:1px solid #c8d8ca;background:#fffefb;border-radius:18px;padding:28px;text-decoration:none;color:#172723;transition:transform .15s,border-color .15s}.card:hover{border-color:#136a55;transform:translateY(-3px)}.label{font-size:15px;font-weight:700}.score{font-size:59px;line-height:1.15;letter-spacing:-.06em;margin-top:20px;font-variant-numeric:tabular-nums}.score span{display:block;font-size:12px;letter-spacing:0;color:#596b65;font-weight:400;margin-top:9px}.card p{font-size:13px;color:#596b65;margin:18px 0 25px}.card strong{font-size:13px;display:flex;justify-content:space-between;color:#136a55}.note{font-size:13px;color:#596b65;max-width:900px}.status{overflow-wrap:anywhere;margin-top:34px;padding:22px 24px;border-radius:14px;background:#fcf0d5;border:1px solid #e7d7b2}.status strong{color:#714217;font-size:14px}.status p{margin:8px 0 0;font-size:13px;color:#66513a}.links{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;border-top:1px solid #cedbd0;margin-top:44px;padding-top:26px}.links a{font-weight:700;font-size:13px}.links p{font-size:12px;color:#596b65}.footer{font-size:11px;color:#68796e;margin-top:40px}@media(max-width:640px){main{padding:25px 20px}.tag{margin-top:40px}h1{font-size:47px}.intro{font-size:16px}.cards,.links{grid-template-columns:1fr}.cards{gap:15px;margin-top:30px}.card{padding:25px}.score{font-size:50px}.links{gap:7px}.status{padding:18px}.footer{line-height:1.8}}@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style></head><body><main><header><a class="brand" href="https://github.com/alvaromendizabal/sports-edge-lab">Sports Edge Lab</a><span>College basketball / 2026</span></header><div class="tag">Evidence review · '''+review_date(data[0])+''' </div><h1>Forecasts you can<br><span>interrogate.</span></h1><p class="intro">Explore the historical models by objective, inspect the uncertainty, and follow the engineering contracts that keep current-season claims separate.</p><section class="cards" aria-label="Separate NCAA basketball reviews">'''+''.join(cards)+'''</section><p class="note">These are development-exposed historical selections on exact shared cohorts, not untouched test results or an untouched prospective performance record. Men's and women's populations remain separate. The public model IDs disclose results while keeping active research recipes private.</p><section class="status">'''+landing_status(data)+'''<p><a href="'''+HOST+'''/private-report/index.html"><strong>Open your private game report →</strong></a> Load the delivered JSON to inspect every supplied game and unresolved market record locally in this browser. The report is never uploaded.</p></section><section class="links" aria-label="Review resources"><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/tree/main/examples/ncaa_review">Run the invented example ↗</a><p>Chronological scoring, measured admission, portable preflight and honest progress estimates. Python standard library only.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/ncaa_review/README.md">Read the methodology ↗</a><p>Selection exposure, calibration, point errors and week-level descriptive uncertainty, with meaningful negative tests.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/docs/PUBLICATION_BOUNDARY.md">Inspect the publication boundary ↗</a><p>Sanitized aggregates and generic contracts are public. Private data, active weights and execution artifacts remain private.</p></div></section><footer class="footer">Built by Alvaro Mendizabal · Sports Edge Lab<br>Static, self-contained review pages. No tracking, external fonts, third-party scripts or live provider requests.</footer></main></body></html>
'''


def render_landing(data):
    from b063_dashboard import render
    from b063r4_status import render_banner
    from b063r5_status import render_banner as render_r5_banner
    from b063r6_status import render_banner as render_r6_banner
    from b063r7_status import render_banner as render_latest_banner
    return render_latest_banner(render_r6_banner(render_r5_banner(render_banner(render(render_legacy_landing(data))))))


def outputs():
    """Return the full-history pages covered by the original review contract."""
    data=[evidence(league) for league in ('ncaam','ncaaw')]
    return {**{ROOT/'tracks'/d['league']/'index.html':render_track(d) for d in data},
            ROOT/'docs/ncaa/index.html':render_landing(data),
            ROOT/'docs/ncaa/private-report/index.html':(HERE/'private_report.html.tmpl').read_text()
                .replace('__B058_LATEST_REVIEW__',latest_review_html())
                .replace('__B056_CHAMPION_POLICY__',B056_CHAMPION_POLICY)
                .replace('__B055_OWNER_STATUS__',B055_OWNER_STATUS)
                .replace('__B054_OWNER_STATUS__',B054_OWNER_STATUS)
                .replace('__EXECUTION_REVIEW_PANEL__',(HERE/'execution_review.html.tmpl').read_text())
                .replace('__V4_REVIEW_PANEL__',(HERE/'v4_review.html.tmpl').read_text().replace('__REFRESH_REVIEW_PANEL__',(HERE/'refresh_review.html.tmpl').read_text()).replace('__PROJECTION_REVIEW_PANEL__',(HERE/'projection_review.html.tmpl').read_text()))
                .replace('__V4_REVIEW_SCRIPT__',(HERE/'refresh_review.js').read_text()+'\n'+(HERE/'projection_review.js').read_text()+'\n'+(HERE/'v4_review.js').read_text()+'\n'+(HERE/'execution_review.js').read_text())}


def publication_outputs():
    """Publish the retained history and the independently validated companion."""
    from b063r2_dashboard import evidence_outputs
    from b063r4_status import status_outputs
    from b063r5_status import status_outputs as r5_status_outputs
    from b063r6_status import status_outputs as r6_status_outputs
    from b063r7_status import status_outputs as latest_status_outputs
    return latest_status_outputs(r6_status_outputs(r5_status_outputs(status_outputs({**outputs(), **evidence_outputs()}))))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    receipts=[]
    for path,text in publication_outputs().items():
        if args.check:
            if not path.is_file() or path.read_text()!=text:raise SystemExit('Stale generated page: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        b=text.encode();receipts.append({'path':str(path.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    print(json.dumps({'status':'EXACT_GENERATION_VERIFIED' if args.check else 'GENERATED','pages':receipts},indent=2))


if __name__=='__main__':main()

