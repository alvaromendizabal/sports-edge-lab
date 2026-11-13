"""Render actual R8 failure and qualified R9 repair without changing science."""
from pathlib import Path
import html
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
START = '<!-- B063R9_ACTUAL_RETURN_STATUS_START -->'
END = '<!-- B063R9_ACTUAL_RETURN_STATUS_END -->\n'


def load_payload():
    value = json.loads((HERE/'B063R9_PUBLIC_STATUS.json').read_text())
    actual, cpu, cache = value['latest_actual_owner'], value['actual_cpu'], value['actual_cache']
    logs, prepared, coverage = value['actual_logging'], value['prepared_continuation'], value['coverage_status']
    if (actual['release'], actual['status'], actual['failure_code']) != (
            'B063R8', 'FAILED_PARTIAL_WORK_PRESERVED', 'B051_SCHEDULE_EXACT_FULL_READBACK_REQUIRED'):
        raise ValueError('Actual R8 failure attribution changed')
    if any(actual[name] != 0 for name in ('new_owner_fits','reused_verified_fits','new_checkpoints',
            'reused_checkpoints','new_forecasts','new_metric_scores','new_market_quotes')):
        raise ValueError('Failed R8 pre-model return cannot claim scientific progress')
    if actual['native_fixture_sports_fit_credit'] != 0 or actual['full_scientific_run_completed']:
        raise ValueError('Native contracts are engineering evidence only')
    if (cpu['host_effective_vcpus'], cpu['configured_project_cap'],
            cpu['peak_granted_cpus'], cpu['peak_active_scientific_workers']) != (48,12,1,0):
        raise ValueError('Actual CPU scope changed')
    if cpu['scientific_native_callback_starts'] != 0 or cpu['twelve_core_scientific_acceptance_proven']:
        raise ValueError('Failed startup does not prove scientific CPU utilization')
    if (cache['verified_local_reads'], cache['verified_local_bytes'], cache['full_S3_GETs'],
            cache['full_S3_GET_bytes']) != (118,1396887267,2,24079252):
        raise ValueError('Actual store/cache evidence changed')
    if cache['repeat_frozen_scientific_cache_acceptance_proven'] or cache['cache_hit_clocks_changed']:
        raise ValueError('Local byte reuse does not establish scientific rerun acceptance or a new clock')
    if (logs['jsonl_rows'],logs['heartbeats'],logs['terminal_flush_status']) != (55,26,'ACKNOWLEDGED'):
        raise ValueError('Actual log capture changed')
    if (logs['complete_final_owner_log_claimed'] or logs['validation_errors']
            or not logs['post_capture_events_remain_external']):
        raise ValueError('Bounded capture cannot become an unqualified complete log')
    if any(coverage[name] for name in ('current_season_complete','upcoming_schedule_complete',
            'latest_attempt_refreshed_game_inventory')):
        raise ValueError('Missing season/upcoming coverage must remain explicit')
    if not coverage['populations_are_distinct_and_not_added']:
        raise ValueError('Saved population counts cannot be summed into complete coverage')
    if value['actual_cost']['actual_invoice_cost_usd'] is not None:
        raise ValueError('Returned rate estimate is not invoice cost')
    if prepared['owner_execution_performed'] or prepared['new_owner_scientific_fits'] != 0:
        raise ValueError('Prepared R9 is not an executed owner result')
    if prepared['twelve_core_owner_utilization_proven']:
        raise ValueError('Local validation does not prove owner utilization')
    replay = prepared['receipt_replay']
    if (replay['selected_files'] != 112 or replay['scientific_fits'] != 0
            or replay['full_adoption_speedup_claimed']
            or replay['original_181_second_owner_adoption_workload_reproduced']
            or not replay['legacy_adoption_chain_still_runs']
            or not replay['current_files_fully_hashed_at_all_existing_recheck_boundaries']):
        raise ValueError('Receipt subset replay cannot establish full owner-adoption performance')
    source = prepared['source_sha256']
    if source is not None and (re.fullmatch('[0-9a-f]{64}',source) is None
            or type(prepared['source_bytes']) is not int or prepared['source_bytes'] <= 0):
        raise ValueError('Invalid prepared source fingerprint')
    prior = json.loads((HERE/'B063R8_PUBLIC_STATUS.json').read_text())
    for field in ('preserved_science','preserved_evidence','metric_policy'):
        if value[field] != prior[field]:
            raise ValueError('Dated public scientific evidence changed: '+field)
    return value


def strip_banner(body):
    if START not in body and END not in body:
        return body
    if body.count(START) != 1 or body.count(END) != 1:
        raise ValueError('Ambiguous R9 status banner')
    left = body.index(START)
    right = body.index(END,left)+len(END)
    return body[:left]+body[right:]


def render_banner(body):
    value = load_payload()
    body = strip_banner(body)
    if body.count('<main>') != 1:
        raise ValueError('Expected one NCAA landing main')
    banner = (HERE/'b063r9_banner.html.tmpl').read_text()
    status = ('R9 final package verification is pending' if value['prepared_continuation']['source_sha256'] is None
              else 'R9 is prepared; owner execution remains pending')
    banner = banner.replace('__R9_PREPARED_STATUS__',html.escape(status))
    return body.replace('<main>','<main>'+banner,1)


def render_page():
    value = load_payload()
    prepared = value['prepared_continuation']
    metric_rows = []
    for row in value['preserved_science']['current_observed_replay_leaders']:
        label = 'Men' if row['league'] == 'ncaam' else 'Women'
        metric_rows.append('<tr><td>'+label+'</td><td>'+html.escape(row['metric_name_for_display'].replace('_',' '))
            +'</td><td>'+f"{row['value']:.6f}"+'</td><td>'+str(row['games'])+'</td><td>'
            +html.escape(' / '.join(row['public_model_ids']))+'</td></tr>')
    providers = []
    for row in value['preserved_science']['provider_coverage']:
        names = {'draftkings_us':'DraftKings US','kalshi_us':'Kalshi US',
                 'polymarket_us':'Polymarket US','polymarket_international':'Polymarket International'}
        providers.append('<tr><td>'+names[row['provider_product']]+'</td><td>'
            +str(row['maximum_matched_games_in_one_comparison'])+'</td><td>'
            +('Saved men’s retrospective comparisons only' if row['maximum_matched_games_in_one_comparison']
              else 'No qualified positive matched comparison')+'</td></tr>')
    validation = prepared['validation']
    validation_text = (validation.get('public_summary','See the linked engineering status JSON for the final validation scope.')
                       if isinstance(validation,dict) else
                       'Targeted local repairs and regression checks are being finalized. Final sealed package verification is pending; no R9 owner execution or scientific throughput is claimed.')
    embedded = (json.dumps(value,indent=2,ensure_ascii=False)+'\n').replace('</','<\\/')
    return ((HERE/'b063r9_status.html.tmpl').read_text()
        .replace('__R9_JSON__',embedded)
        .replace('__R9_METRICS__',''.join(metric_rows))
        .replace('__R9_PROVIDERS__',''.join(providers))
        .replace('__R9_SOURCE__',prepared['source_sha256'] or 'Final source fingerprint pending')
        .replace('__R9_VALIDATION__',html.escape(validation_text)))


def status_outputs(prior):
    result = dict(prior)
    landing = ROOT/'docs/ncaa/index.html'
    if landing in result:
        result[landing] = render_banner(result[landing])
    result[ROOT/'docs/ncaa/b063r9.html'] = render_page()
    result[ROOT/'docs/ncaa/data/B063R9_PUBLIC_STATUS.json'] = (HERE/'B063R9_PUBLIC_STATUS.json').read_text()
    return result


if __name__ == '__main__':
    outputs = status_outputs({ROOT/'docs/ncaa/index.html':(ROOT/'docs/ncaa/index.html').read_text()})
    for path, body in outputs.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(body)
    print(json.dumps({'status':'R9_ADDITIVE_STATUS_RENDERED','paths':[str(p.relative_to(ROOT)) for p in outputs]}))
