"""Add exact later execution health without replacing earlier authenticated issues."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from selected_review_n073 import render as render_forecasts

HEALTH='2026-11-11-n073-actual-n074-continuation.json'

def render(forecast_bytes, health):
    if health.get('schema')!='nfl.n074.latest-execution-retained-forecasts.v1' or health.get('sport')!='NFL':
        raise ValueError('EXECUTION_HEALTH_SCHEMA_REQUIRED')
    retained=health['retained_forecasts']
    if hashlib.sha256(forecast_bytes).hexdigest()!=retained['sha256']:
        raise ValueError('RETAINED_FORECAST_BYTES_CHANGED')
    data=json.loads(forecast_bytes)
    rows=sum(len(t['current_forecasts']) for g in data['games'] for t in g['targets'].values())
    if rows!=retained['selected_rows'] or len(data['games'])!=health['current_census']['games']:
        raise ValueError('RETAINED_COVERAGE_MISMATCH')
    if health['automatic_promotion'] or health['original_predictions_changed'] or retained['reissued']:
        raise ValueError('FAILURE_REPORT_CANNOT_PROMOTE_OR_REISSUE')
    esc=lambda x:html.escape(str(x),quote=True)
    failures=''.join('<li>'+esc(x['effect'])+'</li>' for x in health['failures'])
    panel=f'''<section class="panel" id="execution-health"><h2>Latest execution: N073 blocked</h2>
<p class="note"><strong>No new fits or forecasts verified.</strong> The latest selected forecasts remain N072's {rows} rows for {retained['future_games']} upcoming games. Their original values, roles and issue clocks are preserved. The failed run's smaller fallback export does not replace them.</p>
<p>N073 ran for {health['elapsed_seconds']:.3f} seconds. Whole-run counts remain unknown; zero new fits or issues are verified. Main and final current stages explicitly failed before model dispatch. No model promotion is established.</p><ul>{failures}</ul>
<p>Source refresh recorded {health['source_activity']['normalized_market_rows']} normalized Kalshi/Polymarket observations, a separate DraftKings capture and official source updates. Qualified current winner comparison probabilities: {health['source_activity']['qualified_current_winner_probabilities']}. Source observations are not new training examples or forecasts; R13–R20 were not executed.</p>
<p><a href="{HEALTH}">Actual N073 status and source activity</a> · <a href="CURRENT_MODEL_CARD.md">Preserved historical leaders</a></p>
<p class="muted">N074 is the V8 engineering continuation; owner execution and scientific results are pending. Source publication does not deploy or refresh the separately hosted Site.</p></section>'''
    page=render_forecasts(data)
    marker='<section class="panel" id="latest-return">'
    if page.count(marker)!=1:raise ValueError('RETAINED_RENDERER_INSERTION_POINT_CHANGED')
    page=page.replace(marker,panel+'\n'+marker,1)
    page=page.replace('Latest owner execution: frozen research resumed','Forecast-producing execution: retained N072 evidence',1)
    page=page.replace('<th>New observations</th>','<th>N072 observations</th>',1)
    return page

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path(__file__).with_name('season_review_n074.html'));parser.add_argument('--check',action='store_true');args=parser.parse_args()
    here=Path(__file__).resolve().parent
    expected=render((here/'selected_forecasts_n073.json').read_bytes(),json.loads((here/HEALTH).read_bytes()))
    if args.check:
        if args.output.read_text()!=expected:raise SystemExit('N074_PAGE_DIFFERS_FROM_BOUND_EVIDENCE')
        print('N074_SAVED_PAGE_EXACT_PASS')
    else:args.output.write_text(expected)
if __name__=='__main__':main()
