"""Sanitized partial-owner status layered over unchanged prior NCAA evidence."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
START='<!-- B063R4_PARTIAL_OWNER_STATUS_START -->'
END='<!-- B063R4_PARTIAL_OWNER_STATUS_END -->\n'
BANNER=(HERE/'b063r4_banner.html.tmpl').read_text()
def load_payload():
 value=json.loads((HERE/'B063R4_PUBLIC_STATUS.json').read_text());a=value['latest_attempt'];p=value['prepared_continuation'];m=value['metric_policy']
 if a['terminal_return_verified'] or a['whole_run_completed'] or a['twelve_core_acceptance_proven'] or a['checkpoint_events_are_fit_counts']:
  raise ValueError('Partial owner evidence cannot claim completion or scientific parallel acceptance')
 if (a['authenticated_prior_target_fits'],a['authenticated_content_objects'])!=(22,134):raise ValueError('Authenticated prior fit population changed')
 if (a['new_distinct_checkpoint_contracts'],a['reused_distinct_checkpoint_contracts'],a['total_distinct_checkpoint_contracts'])!=(167,248,415):raise ValueError('Distinct checkpoint population changed')
 if a['new_fits_in_this_preparation'] or p['new_preparation_scientific_fits'] or p['owner_execution_verified'] or p['engineering_tests_are_owner_performance']:
  raise ValueError('Engineering preparation cannot claim owner science')
 if m['new_scores'] is not None or m['current_season_complete'] or m['rolling_or_original_issue_promotion']:
  raise ValueError('Incident update cannot invent fresh scores or promotion')
 return value

def strip_banner(body):
 if START not in body and END not in body:return body
 if body.count(START)!=1 or body.count(END)!=1 or body.count(BANNER)!=1:raise ValueError('Unexpected partial-owner banner bytes')
 return body.replace(BANNER,'',1)

def render_banner(body):
 body=strip_banner(body)
 if body.count('<main>')!=1:raise ValueError('Expected one NCAA main element')
 return body.replace('<main>','<main>'+BANNER,1)

def render_page():
 payload=load_payload();raw=json.dumps(payload,indent=2,ensure_ascii=False)+'\n'
 return (HERE/'b063r4_status.html.tmpl').read_text().replace('__B063R4_JSON__',raw.replace('</','<\\/'))

def status_outputs(prior):
 result=dict(prior);landing=ROOT/'docs/ncaa/index.html'
 if landing in result:result[landing]=render_banner(result[landing])
 result[ROOT/'docs/ncaa/b063r4.html']=render_page()
 result[ROOT/'docs/ncaa/data/B063R4_PUBLIC_STATUS.json']=(HERE/'B063R4_PUBLIC_STATUS.json').read_text()
 return result
