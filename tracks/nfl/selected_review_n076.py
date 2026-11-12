"""Show an authenticated resource deferral without changing retained forecasts."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from selected_review_n073 import render as render_forecasts

HEALTH = '2026-11-11-n075-actual-n076-continuation.json'


def render(forecast_bytes, health):
    if health.get('schema') != 'nfl.n076.latest-execution-retained-forecasts.v1' or health.get('sport') != 'NFL':
        raise ValueError('EXECUTION_HEALTH_SCHEMA_REQUIRED')
    retained = health['retained_forecasts']
    if hashlib.sha256(forecast_bytes).hexdigest() != retained['sha256']:
        raise ValueError('RETAINED_FORECAST_BYTES_CHANGED')
    data = json.loads(forecast_bytes)
    rows = sum(len(t['current_forecasts']) for g in data['games'] for t in g['targets'].values())
    if rows != retained['selected_rows'] or len(data['games']) != health['current_census']['games']:
        raise ValueError('RETAINED_COVERAGE_MISMATCH')
    if health['automatic_promotion'] or health['original_predictions_changed'] or retained['reissued']:
        raise ValueError('FAILURE_REPORT_CANNOT_PROMOTE_OR_REISSUE')
    if health.get('counts_known') is not True or any(type(health.get(k)) is not int or health[k] != 0 for k in ('new_fits','new_native_fits','new_meta_fits','new_forecasts')):
        raise ValueError('KNOWN_ZERO_DEFERRAL_RECEIPTS_REQUIRED')
    admission = health['resource_admission']
    if health['status'] != 'RESOURCE_DEFERRED_RESUMABLE' or admission['observed_reason'] != 'EXTERNAL_IO_PRESSURE':
        raise ValueError('ACTUAL_DEFERRAL_REASON_REQUIRED')
    absent = ('current_effective_vcpus','current_per_project_ceiling','measured_pressure','requested_or_granted_threads')
    if admission['current_capacity_recorded'] or admission['detailed_decision_in_return'] or any(admission[k] is not None for k in absent):
        raise ValueError('UNOBSERVED_RESOURCE_TELEMETRY_CANNOT_BE_FILLED')
    if admission['other_owner_cause_proven'] or admission['pressure_was_stale_proven']:
        raise ValueError('UNPROVEN_RESOURCE_CAUSE')
    if health['source_activity']['source_refresh_invoked'] or health['source_activity']['new_paid_calls'] != 0 or health['current_census']['refreshed_by_latest_execution']:
        raise ValueError('NO_SOURCE_OR_CENSUS_REFRESH_OCCURRED')
    esc = lambda value: html.escape(str(value), quote=True)
    failures = ''.join('<li>'+esc(x['effect'])+'</li>' for x in health['failures'])
    panel = f'''<section class="panel" id="execution-health"><h2>Latest execution: N075 resource-deferred</h2>
<p class="note"><strong>Zero new fits and zero new forecasts.</strong> The latest selected forecasts remain N072's {rows} rows for {retained['future_games']} upcoming games. Their original values, metric roles and issue clocks are preserved.</p>
<p>N075 ran from 3:56:05 to 3:56:41 p.m. Pacific on November 11, 2026, for {health['elapsed_seconds']:.3f} seconds. It returned resumable with <code>{esc(admission['observed_reason'])}</code> before source refresh or scientific dispatch. This resource deferral is not a negative model experiment.</p><ul>{failures}</ul>
<p>Current CPU capacity, I/O-pressure measurements and detailed requested/granted leases were <strong>not recorded in this return</strong>. The physical cause and the contribution of other workloads remain unresolved. The previously observed 48-vCPU host and 12-CPU NFL ceiling belong to N074 evidence; no new CPU utilization or speedup is claimed.</p>
<p>N075 made zero paid source calls. It did not refresh the retained 272-game schedule or create new DraftKings, Kalshi or Polymarket comparisons. All 136 completed games, 112 timed future games and 24 kickoff-TBD games remain visible with their original evidence gaps.</p>
<p><a href="{HEALTH}">Actual N075 execution evidence</a> · <a href="CURRENT_MODEL_CARD.md">Historical leaders, current-season gaps and promotion gates</a></p>
<p class="muted">N076 is the V8 engineering continuation; owner execution and scientific results are pending. No production promotion is established. Source publication does not deploy or refresh the separately hosted Site.</p></section>'''
    page = render_forecasts(data)
    marker = '<section class="panel" id="latest-return">'
    if page.count(marker) != 1:
        raise ValueError('RETAINED_RENDERER_INSERTION_POINT_CHANGED')
    page = page.replace(marker, panel+'\n'+marker, 1)
    page = page.replace('Latest owner execution: frozen research resumed','Forecast-producing execution: retained N072 evidence',1)
    return page.replace('<th>New observations</th>','<th>N072 observations</th>',1)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('season_review_n076.html'))
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    expected=render((here/'selected_forecasts_n073.json').read_bytes(),json.loads((here/HEALTH).read_bytes()))
    if args.check:
        if args.output.read_text()!=expected:raise SystemExit('N076_PAGE_DIFFERS_FROM_BOUND_EVIDENCE')
        print('N076_SAVED_PAGE_EXACT_PASS')
    else:args.output.write_text(expected)


if __name__=='__main__':main()
