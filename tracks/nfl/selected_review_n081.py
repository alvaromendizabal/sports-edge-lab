"""Retain authenticated N079 science while reporting the failed N080 refresh."""
import argparse
import hashlib
import html
import json
from pathlib import Path

import selected_review_n080 as previous

STATUS = '2026-11-13-n080-actual-n081-status.json'


def validate(raw, metrics_raw, status):
    for field, body in (('preserved_selected_forecasts_sha256', raw),
                        ('preserved_metrics_sha256', metrics_raw)):
        if hashlib.sha256(body).hexdigest() != status[field]:
            raise ValueError('PRESERVED_SCIENCE_BYTES_CHANGED')
    value = previous.validate(raw, json.loads(metrics_raw))
    if status['schema'] != 'nfl.n081.latest-attempt-status.v1' or status['sport'] != 'NFL':
        raise ValueError('STATUS_SCHEMA_MISMATCH')
    if status['latest_attempt'] != 'N080' or status['status'] != 'FAILED':
        raise ValueError('LATEST_ATTEMPT_FAILURE_MUST_REMAIN_VISIBLE')
    if any(status[k] != 0 for k in ('new_fits', 'new_native_fits', 'new_meta_fits',
                                    'new_forecasts', 'new_paid_calls')):
        raise ValueError('FAILED_ATTEMPT_CANNOT_CLAIM_NEW_WORK')
    if any(status[k] for k in ('owner_research_acceptance', 'new_n081_owner_science_claimed',
                              'new_provider_refresh_claimed', 'automatic_promotion')):
        raise ValueError('UNOBSERVED_COMPLETION_OR_PROMOTION')
    if status['preserved_scientific_source'] != 'N079' or status['preserved_selected_snapshot_utc'] != value['display_cutoff_utc']:
        raise ValueError('PRESERVED_SOURCE_CLOCK_CHANGED')
    for field, count in (('preserved_games', 'schedule_games'),
                         ('preserved_selected_rows', 'current_selected_rows'),
                         ('preserved_selected_games', 'current_selected_games')):
        if status[field] != value['counts'][count]:
            raise ValueError('PRESERVED_DENOMINATOR_CHANGED')
    if status['preserved_selected_forecasts_file'] != previous.FORECAST or status['preserved_metrics_file'] != previous.HEALTH:
        raise ValueError('PRESERVED_SOURCE_FILE_CHANGED')
    return value


def banner(status):
    e = html.escape
    return ('<section class="panel" id="latest-attempt" aria-labelledby="latest-attempt-heading" '
            'style="border:2px solid #aa4c25;background:#fff4e8">'
            '<h2 id="latest-attempt-heading">Latest refresh failed · N080</h2>'
            '<p><strong>0 new fits · 0 new forecasts · 0 paid calls. '
            'Owner research acceptance: false.</strong></p>'
            '<p>The attempt finished at ' + e(status['finished_at']) + ' after '
            + format(status['elapsed_seconds'], '.6f') + ' seconds. '
            + e(status['failure_reason']) + '. ' + e(status['failure_stage']) + '.</p>'
            '<p><strong>Prior valid selected snapshot: '
            + e(status['preserved_selected_snapshot_utc']) + ' (N079).</strong> '
            'All 272 saved games, 448 selected outputs across 112 games, original clocks '
            'and historical metrics below are preserved unchanged. Upcoming games and '
            'results describe that saved census; this failed attempt did not refresh them.</p>'
            '<p>This failure is not an execution speedup or a completed experiment. '
            'No N081 owner-run scientific result or rolling promotion is claimed. '
            '<a href="' + STATUS + '" download>Authenticated attempt status</a> · '
            '<a href="season_review_n080.html">Preserved N079 dated view</a></p></section>')


def render(raw, metrics_raw, status):
    validate(raw, metrics_raw, status)
    page = previous.render(raw, json.loads(metrics_raw))
    return previous.replace_once(page, '<main class="wrap">', '<main class="wrap">' + banner(status))


def main():
    root = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=root / 'season_review_n081.html')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    page = render((root / previous.FORECAST).read_bytes(),
                  (root / previous.HEALTH).read_bytes(), json.loads((root / STATUS).read_bytes()))
    if args.check:
        if not args.output.is_file() or args.output.read_text() != page:
            raise SystemExit('N081 review differs from authenticated attempt and preserved science')
        print('N081 failed-attempt review preserves exact N079 source bytes.')
    else:
        args.output.write_text(page)


if __name__ == '__main__':
    main()
