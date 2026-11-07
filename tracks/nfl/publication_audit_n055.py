"""Additive public audit; it never rewrites original observations or scores."""
from collections import Counter
import hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent

def audit(data):
 games=data['games'];models=data['model_rows'];providers=data['provider_rows']
 if len({g['game_id'] for g in games})!=272:raise ValueError('schedule identity closure')
 expected_models={(g['game_id'],l['id'],t) for g in games for l in data['lanes'] for t in ['win','margin','total']}
 if {(r['game_id'],r['lane_id'],r['target']) for r in models}!=expected_models:raise ValueError('complete model roles')
 expected_providers={(g['game_id'],p,t,h) for g in games for p in ['DraftKings','Kalshi','Polymarket'] for t in ['win','margin','total'] for h in data['provider_horizons']}
 if {(r['game_id'],r['provider'],r['target'],r['horizon']) for r in providers}!=expected_providers:raise ValueError('equal provider grids')
 if len(models)!=len(expected_models) or len(providers)!=len(expected_providers):raise ValueError('duplicate cells')
 completed=sum(g['completed'] for g in games);decisive=sum(g['completed'] and not g['tie'] for g in games)
 if (completed,decisive)!=(122,121):raise ValueError('dated snapshot changed without a registered schedule revision')
 for pair,score in [({'CHI','SEA'},(34,17)),({'JAX','BAL'},(33,10))]:
  rows=[g for g in games if {g['away'],g['home']}==pair and g['completed']]
  if len(rows)!=1 or (rows[0]['actual']['away_score'],rows[0]['actual']['home_score'])!=score:raise ValueError('official recent result identity')
 rows=[{'record_set':'Schedule events','expected':272,'present':len(games),'numeric_values':None,'interpretation':'All 32 teams; 122 completed, 150 future; one completed tie.'},
 {'record_set':'Model role / target cells','expected':len(expected_models),'present':len(models),'numeric_values':sum(isinstance(r.get('value'),(int,float)) and not isinstance(r.get('value'),bool) for r in models),'interpretation':'272 games × 63 retained roles × 3 targets. Unsupported outputs keep their specific reason.'},
 {'record_set':'Provider / target / horizon cells','expected':len(expected_providers),'present':len(providers),'numeric_values':sum(isinstance(r.get('value'),(int,float)) and not isinstance(r.get('value'),bool) for r in providers),'interpretation':'272 games × 3 providers × 3 targets × 10 explicit horizons. A retained direction may exist without a probability.'},
 {'record_set':'All-model seasonal metrics','expected':len(data['all_model_metrics']),'present':len(data['all_model_metrics']),'numeric_values':None,'interpretation':'Preserved exact cohorts and target-specific metrics; no scores recomputed from rounded public values.'},
 {'record_set':'Raw per-game reconstruction records','expected':18889,'present':len(data['raw_per_game']),'numeric_values':None,'interpretation':'15,116 reconstructed rows plus 3,773 unchanged baseline rows; earlier-label timing does not prove original possession.'},
 {'record_set':'Conditional scale distribution rows','expected':35252,'present':len(data['scale_per_game']),'numeric_values':None,'interpretation':'70 verified states; 140 season metrics, 260 comparisons, two nested checks; zero Holm-confirmed improvement.'}]
 for provider in ['DraftKings','Kalshi','Polymarket']:
  subset=[r for r in providers if r['provider']==provider]
  rows.append({'record_set':provider+' grid','expected':len(expected_providers)//3,'present':len(subset),'numeric_values':sum(isinstance(r.get('value'),(int,float)) and not isinstance(r.get('value'),bool) for r in subset),'interpretation':'Same complete game/target/horizon grid; availability and clock eligibility are separate recorded fields.'})
 return {'schema':'nfl.public.completeness_audit.n055.v1','review_date':'2026-11-07','source_projection_sha256':hashlib.sha256((HERE/'current_season_n054.json.gz').read_bytes()).hexdigest(),
 'owner_attempt':{'cycle':'N054','status':'ACTUAL_DIAGNOSTIC_PACKAGING_FAILURE','full_durable_evidence_closure':False,'failure_stage':'return_packaging','failure':'Return manifest and essential payload exceed bounded delivery capacity','prior_status':'PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED','new_scientific_result_credit':0,'qualification':'Zero additional public scientific credit is not a claim of zero owner execution. Complete fit and issue counts require authenticated durable recovery.'},
 'verified_public_science':{'native_states':3432,'scale_states':70,'cutoff_jobs':7184,'exact_input_reuses':3752,'owner_issue_rows':754,'market_support_blocked_jobs':318,'review_outlook_rows':1464},
 'completeness':rows,'official_checks':[
 {'label':'Los Angeles Rams official 2025 schedule','url':'https://www.therams.com/schedule/2025/','finding':'LA postseason identities refer to the Rams; the source identifier is preserved.'},
 {'label':'Chicago at Seattle official game center','url':'https://www.seahawks.com/game-day/2026/reg-week8/seahawks-vs-bears/','finding':'November 2, 2026; Chicago 34, Seattle 17; retained ledger already contains the result.'},
 {'label':'Jacksonville at Baltimore official game center','url':'https://www.jaguars.com/game-day/2026/reg-week9/jaguars-at-ravens/','finding':'November 5, 2026; Jacksonville 33, Baltimore 10; retained ledger already contains the result.'}],
 'new_fits_from_publication':0,'new_issues_from_publication':0,'new_numeric_source_values_from_publication':0,'original_data_modified':False,'schedule_changes_from_retained_snapshot':0}
