"""Create a public, whitelisted all-game view from the authenticated V037 report.

This projection carries existing values. It neither fits models nor estimates
missing probabilities, historical possession, intervals, fees, or liquidity.
The private input is never copied into the public repository.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_BYTES = 22685842
EXPECTED_SHA256 = '93333d34a4f337cf436938717950173f8fd05f0b5d81eb8e58b85a33871c5ad0'
PROVIDERS = ['DraftKings', 'Kalshi', 'Polymarket US', 'Polymarket Global']
TARGETS = ['winner', 'margin', 'total']
BASE = ['id','away','home','kickoff','week','phase','population','completed',
        'away_score','home_score','winner','home_margin','total_points','period',
        'schedule_join','previous_kickoff','changed_result','replay_status',
        'replay_winner','replay_p_home','replay_margin','replay_total',
        'replay_away','replay_home','replay_correct','cover_status','uncertainty_status',
        'rolling_status','injury_status']
DETAIL = ['value','status','quote_at','captured_at',
          'declared_cutoff_from_matching_retained_detail',
          'interval_end_from_matching_retained_detail',
          'product_from_matching_retained_detail','reference_kind',
          'clock_evidence_status','interpretation','point_support',
          'historical_possession_proved','full_detail_match_status']

def number(value):
    if value is None or value == '': return None
    return float(value)

def build(source):
    raw = Path(source).read_bytes()
    if len(raw) != EXPECTED_BYTES or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError('V037 cumulative input does not match its physical byte and SHA-256 pin')
    report = json.loads(raw)
    columns = BASE + [f'{p}_{t}_{k}' for p in PROVIDERS for t in TARGETS for k in DETAIL]
    rows=[]
    for record in report['games']:
        official=record['latest_authenticated_dated_official_observation']
        prior=record['retained_reconstructed_model_and_four_provider_report']
        kickoff=official['kickoff_utc']
        period=('previous' if '2026-10-26T07:00:00Z' <= kickoff < '2026-11-02T08:00:00Z'
                else 'current' if '2026-11-02T08:00:00Z' <= kickoff < '2026-11-09T08:00:00Z' else 'other')
        row=[str(record['game_id']), official['away_team'],official['home_team'],kickoff,
             official['week'],official['season_type'],official['population_scope'],official['completed'],
             official['away_points'],official['home_points'],official['winner_team'],official['home_margin'],official['total_points'],period,
             record['retained_snapshot_join_status'],prior.get('kickoff_utc') if not record['retained_snapshot_exact_current_join_qualified'] else None,
             record['source_status_changed_since_retained_report'],prior.get('replay_status'),prior.get('replay_winner') or None,
             number(prior.get('replay_p_home')),number(prior.get('replay_home_margin')),number(prior.get('replay_total')),
             number(prior.get('replay_projected_away')),number(prior.get('replay_projected_home')),
             prior.get('replay_correct') == 'true' if prior.get('replay_correct') else None,
             prior.get('cover_probability_status'),prior.get('forecast_uncertainty_status'),prior.get('rolling_status'),prior.get('injury_adjusted_forecast')]
        for provider in PROVIDERS:
            for target in TARGETS:
                for key in DETAIL:
                    value=prior.get(f'{provider}_{target}_{key}')
                    row.append(number(value) if key == 'value' else value or None)
        rows.append(row)
    rows.sort(key=lambda row:(row[3],row[0]))
    if len(rows)!=888 or len({r[0] for r in rows})!=888: raise ValueError('Game identity census failed')
    counts={period:sum(r[13]==period for r in rows) for period in ['previous','current']}
    if counts!={'previous':56,'current':63}: raise ValueError('Pacific interval census failed')
    data={'schema':'fbs.public.complete-season.v038.1','columns':columns,'rows':rows,
      'season':2026,'source_observed_at':'2026-11-06T20:28:52Z',
      'capture_completed_at':report['capture_completed_at'],'projection_prepared_at':report['prepared_at'],
      'source_report_sha256':EXPECTED_SHA256,'source_report_bytes':EXPECTED_BYTES,
      'original_source_sha256':report['source_physical']['sha256'],
      'retained_model_report_at':'2026-11-06T06:26:17.272676Z',
      'providers':PROVIDERS,'provider_targets':TARGETS,
      'counts':{'identified_games':888,'observed_completed':sum(r[7] for r in rows),
        'retained_replay':sum(r[19] is not None for r in rows),'genuine_rolling_forecasts':0,
        'previous_week':56,'current_week':63,'current_week_completed':sum(r[7] and r[13]=='current' for r in rows),
        'kickoff_quarantines':sum(not g['retained_snapshot_exact_current_join_qualified'] for g in report['games'])},
      'periods':{'previous':{'label':'Oct 26–Nov 1','start':'2026-10-26T07:00:00Z','end':'2026-11-02T08:00:00Z'},
        'current':{'label':'Nov 2–8','start':'2026-11-02T08:00:00Z','end':'2026-11-09T08:00:00Z'}},
      'metadata':{'unbound_championship_slots':10,'army_navy_native_week_conflict':True,
        'historical_possession_verified':0,'new_provider_requests':0,'new_model_fits':0,'new_issues':0,
        'owner_observation':'V037 deferred at the ownership gate; V036 was active in the supplied owner observation.',
        'full_workload_status':'NO_GO'},
      'replay_headline':{'games':622,'correct':465,'winner_accuracy':465/622,'log_loss':0.5133276378012555,
        'record_class':'retrospective_replay','historical_availability_proven':False},
      'provider_value_counts':{p:{t:sum(r[columns.index(f'{p}_{t}_value')] is not None for r in rows) for t in TARGETS} for p in PROVIDERS}}
    return data

def write(data,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    encoded=json.dumps(data,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    (output/'complete-season.json').write_text(encoded+'\n')
    (output/'complete-data.js').write_text('"use strict";window.FBS_COMPLETE_DATA='+encoded+';\n')
    registry=json.loads((ROOT/'docs/fbs/model-registry.json').read_text())
    common=json.loads((ROOT/'docs/fbs/common-game-review.json').read_text())
    common.pop('betting_edge_proven',None)
    for cohort in common['cohorts']: cohort.pop('betting_edge_proven',None)
    (output/'complete-history.js').write_text('"use strict";window.FBS_COMPLETE_HISTORY='+json.dumps({'registry':registry,'common':common},separators=(',',':'))+';\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',default=str(ROOT/'docs/fbs'))
    args=parser.parse_args();data=build(args.source);write(data,args.output)
    print(json.dumps({'counts':data['counts'],'provider_value_counts':data['provider_value_counts'],'new_fits':0,'new_requests':0}))
