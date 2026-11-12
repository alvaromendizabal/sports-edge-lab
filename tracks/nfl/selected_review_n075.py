"""Report an authenticated failed execution without rewriting preserved forecasts."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from selected_review_n073 import render as render_forecasts

HEALTH = '2026-11-11-n074-actual-n075-continuation.json'

def render(forecast_bytes, health):
    if health.get('schema') != 'nfl.n075.latest-execution-retained-forecasts.v1' or health.get('sport') != 'NFL':
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
    if health.get('counts_known') is not True or any(health.get(k) != 0 for k in ('new_fits', 'new_native_fits', 'new_meta_fits', 'new_forecasts')):
        raise ValueError('KNOWN_ZERO_FAILURE_RECEIPTS_REQUIRED')
    esc = lambda x: html.escape(str(x), quote=True)
    failures = ''.join('<li>' + esc(x['effect']) + '</li>' for x in health['failures'])
    panel = f'''<section class="panel" id="execution-health"><h2>Latest execution: N074 blocked</h2>
<p class="note"><strong>Zero new fits and zero new forecasts.</strong> The latest selected forecasts remain N072's {rows} rows for {retained['future_games']} upcoming games. Their original values, roles and issue clocks are preserved. Later failure exports do not replace this richer retained evidence.</p>
<p>N074 ran from 2:29:53 to 2:37:20 p.m. Pacific on November 11, 2026, for {health['elapsed_seconds']:.3f} seconds. Terminal receipts establish known zero work. Every current-model phase failed before child dispatch. No model promotion is established.</p><ul>{failures}</ul>
<p>The owner detected {health['cpu_contract']['effective_vcpus']} effective vCPUs and a {health['cpu_contract']['per_project_ceiling']}-CPU NFL ceiling, but no scientific fit workers launched. Source collection used {health['source_activity']['new_paid_calls']} paid calls and {health['source_activity']['known_credits']} known credits. A source capture is not a new fit, forecast or admitted market comparison. R13–R20 remain unexecuted.</p>
<p><a href="{HEALTH}">Actual N074 execution evidence</a> · <a href="CURRENT_MODEL_CARD.md">Preserved historical leaders and promotion gates</a></p>
<p class="muted">N075 is the V8 engineering continuation; owner execution and scientific results are pending. Full-season 2026 former-champion scores and complete matched provider comparisons remain unavailable. Source publication does not deploy or refresh the separately hosted Site.</p></section>'''
    page = render_forecasts(data)
    marker = '<section class="panel" id="latest-return">'
    if page.count(marker) != 1:
        raise ValueError('RETAINED_RENDERER_INSERTION_POINT_CHANGED')
    page = page.replace(marker, panel + '\n' + marker, 1)
    page = page.replace('Latest owner execution: frozen research resumed', 'Forecast-producing execution: retained N072 evidence', 1)
    return page.replace('<th>New observations</th>', '<th>N072 observations</th>', 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('season_review_n075.html'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    expected = render((here / 'selected_forecasts_n073.json').read_bytes(), json.loads((here / HEALTH).read_bytes()))
    if args.check:
        if args.output.read_text() != expected:
            raise SystemExit('N075_PAGE_DIFFERS_FROM_BOUND_EVIDENCE')
        print('N075_SAVED_PAGE_EXACT_PASS')
    else:
        args.output.write_text(expected)

if __name__ == '__main__':
    main()
