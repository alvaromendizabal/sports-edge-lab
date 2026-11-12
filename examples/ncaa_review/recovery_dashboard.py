"""Add a dated B063 recovery panel without changing earlier science snapshots."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD_SHA256 = 'b6aa42edb8416909c4d82039731cb634f356e8a079f18ec016c45dc717ba890e'
START = '<!-- B063R1_RECOVERY_START -->'
END = '<!-- B063R1_RECOVERY_END -->'


def validate(data):
    if data['schema'] != 'sel.ncaa.b063r1.recovery_dashboard.v1':
        raise ValueError('recovery schema')
    owner = data['actual_owner']
    if owner['status'] != 'FAILED_PARTIAL_WORK_PRESERVED' or owner['science_started']:
        raise ValueError('failed owner scope')
    if any(owner[k] != 0 for k in ('new_verified_fits', 'runtime_verified_reused_fits', 'new_issues', 'promotions')):
        raise ValueError('failed owner cannot earn scientific credit')
    if owner['actual_owner_parallel_benchmark_reached'] or owner['actual_startup_lease_cpus'] != 1:
        raise ValueError('owner benchmark or reservation scope')
    if data['repair']['actual_owner_execution_verified']:
        raise ValueError('prepared repair is not owner execution')
    if data['complete_current_season_coverage'] or data['verified_new_upcoming_forecasts'] != 0:
        raise ValueError('schedule coverage not refreshed')
    rows = data['selected_originals']
    if len(rows) != 90 or len({r['issue_fingerprint'] for r in rows}) != 90:
        raise ValueError('selected original closure')
    if len({r['event_id'] for r in rows}) != 30:
        raise ValueError('selected game closure')
    if {league: sum(r['league'] == league for r in rows) for league in ('ncaam', 'ncaaw')} != {'ncaam': 12, 'ncaaw': 78}:
        raise ValueError('selected league closure')
    asof = datetime.fromisoformat(data['asof_utc'])
    for row in rows:
        t = lambda k: datetime.fromisoformat(row[k].replace('Z', '+00:00'))
        if not (t('issued_at') <= t('server_last_modified_utc') < t('cutoff_time') < t('event_time') < asof):
            raise ValueError('original clock or current upcoming mislabel')
        if row['actual'] is not None or row['automatic_promotion'] or not row['durable_issued_before_cutoff']:
            raise ValueError('original preservation or promotion')
        if row['selection_scope'] != 'preserved_role' or row['new_B063_issue_credit'] != 0:
            raise ValueError('selected role or new issue scope')
        if round(row['prediction'], 6 if row['target'] == 'win' else 3) != row['prediction']:
            raise ValueError('public display rounding')
    if data['selected_recovery']['source_current_outcomes_used_for_selection']:
        raise ValueError('selection used later outcomes')
    prior = json.loads((HERE / 'B063_TERMINAL_PUBLIC_DATA.json').read_text())
    if len(prior['issues']) != 142:
        raise ValueError('prior issue closure')
    if {r['issue_record_sha256'] for r in rows} & {r.get('issue_record_sha256') for r in prior['issues']}:
        raise ValueError('prior issue double count')
    monitor = data['late_monitor']
    if monitor.get('status') == 'VERIFIED_FULL_PRECISION_POSTISSUE_MONITORING':
        if monitor['new_fits'] or monitor['promotions'] or monitor['original_issues_mutated']:
            raise ValueError('monitor cannot mutate or promote')
        if monitor['prediction_precision_basis'] != 'AUTHENTICATED_FULL_PRECISION_ORIGINAL_RECORDS':
            raise ValueError('rounded forecasts cannot supply metric authority')
        proof_bytes = (HERE / 'B063R1_POSTISSUE_MONITORING.json').read_bytes()
        if hashlib.sha256(proof_bytes).hexdigest() != monitor['evidence_sha256']:
            raise ValueError('postissue monitoring evidence identity')
        proof = json.loads(proof_bytes)
        expected = [{'league': r['league'], 'public_model_id': r['public_model_id'], 'target': r['target'],
                     'n': r['metrics']['games'], **{k: v for k, v in r['metrics'].items() if k != 'games'}}
                    for r in proof['groups']]
        if monitor['metrics'] != expected or monitor['outcomes'] != proof['outcomes']:
            raise ValueError('postissue metrics or outcome projection changed')
    forbidden = ('s3://', 'sagemaker-user', 'arn:aws:', 'secret_key', 'access_key',
                 's3_bucket', 'checkpoint_path', 'model_weights', 'feature_columns', 'recipe_id')
    serialized = json.dumps(data)
    if any(marker in serialized for marker in forbidden):
        raise ValueError('private publication boundary')
    return data


def load_payload():
    body = (HERE / 'B063R1_PUBLIC_RECOVERY_DATA.json').read_bytes()
    if hashlib.sha256(body).hexdigest() != PAYLOAD_SHA256:
        raise ValueError('recovery payload identity')
    return validate(json.loads(body)), body.decode().strip()


def render(prior_html):
    _, body = load_payload()
    panel = (HERE / 'recovery_dashboard.html.tmpl').read_text().replace(
        '__RECOVERY_DATA__', body.replace('<', '\\u003c'))
    if START in prior_html:
        begin = prior_html.index(START)
        end = prior_html.index(END, begin) + len(END)
        prior_html = prior_html[:begin] + prior_html[end:]
    insertion = prior_html.index('<main>') + len('<main>')
    return prior_html[:insertion] + START + panel + END + prior_html[insertion:]

