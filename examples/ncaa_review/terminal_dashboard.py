"""Render the bounded terminal-return NCAA report; no fitting or acquisition."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD_SHA256 = 'ca90e4e6375995bdc4e0e8a5dd3278100e8347a0d8b23a23d4b5ee5d332dc130'

def validate(data):
    if data['schema'] != 'sel.ncaa.b063.terminal_dashboard.v1':
        raise ValueError('terminal schema')
    if len(data['science']['frozen_core_roles']) != 14 or len(data['science']['retained_historical_metric_roles']) != 14:
        raise ValueError('role closure')
    if len(data['science']['per_season_selected_model_metrics']) != 50:
        raise ValueError('annual metric closure')
    if len(data['games']) != 3425 or len(data['replay']) != 6567:
        raise ValueError('observed/replay closure')
    if len(data['issues']) != 142:
        raise ValueError('original issue closure')
    latest = [r for r in data['issues'] if r['display_evidence_mode']=='recovered_native_original']
    if len(latest) != 46 or len({(r['league'],r['event_id']) for r in latest}) != 8:
        raise ValueError('recovered original closure')
    for row in latest:
        t=lambda key:datetime.fromisoformat(row[key].replace('Z','+00:00'))
        if not (t('issued_at') <= t('server_last_modified_utc') <= t('cutoff_time') < t('event_time')):
            raise ValueError('original issue clock')
        if row['actual'] is not None or row['automatic_promotion'] or not row['durable_issued_before_cutoff']:
            raise ValueError('original issue scope')
        if not (row['frozen_research_roles'] or row['selected_ensemble_component_roles']):
            raise ValueError('not a frozen selected role')
    execution=data['execution']
    if execution['new_owner_verified_fits'] is not None or any(execution[k] for k in ('new_dashboard_fits','new_dashboard_issues','promotions','b063_owner_execution_verified','b063_parallelism_on_owner_verified','full_catalog_complete')):
        raise ValueError('publication cannot claim execution or promotion')
    if data['complete_official_universe'] or data['science']['selection_qualification']['automatic_promotion']:
        raise ValueError('coverage/promotion scope')
    return data

def load_payload():
    raw=(HERE/'B063_TERMINAL_PUBLIC_DATA.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PAYLOAD_SHA256:
        raise ValueError('terminal payload content identity')
    return validate(json.loads(raw)),raw.decode().strip()

def render(prior_html):
    _,raw=load_payload()
    panel=(HERE/'terminal_dashboard.html.tmpl').read_text().replace('__TERMINAL_DATA__',raw.replace('<','\\u003c'))
    start=prior_html.index('<main>')+len('<main>')
    end=prior_html.rindex('</main>')
    output=prior_html[:start]+panel+'<details id="terminal-archive" class="terminal-archive"><summary>Earlier published snapshot · PR 239 · November 11 source evidence</summary><p>This dated view is preserved unchanged. The terminal-return report above supersedes its latest-evidence status; original numbers and qualifications remain inspectable.</p>'+prior_html[start:end]+'</details>'+prior_html[end:]
    return output.replace('NCAA Basketball · Preserved Science & Recovery · Sports Edge Lab','NCAA Basketball · Recovered Research & Original Issues · Sports Edge Lab')
