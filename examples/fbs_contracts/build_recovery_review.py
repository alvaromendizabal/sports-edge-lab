"""Build a public recovery review from allowlisted aggregates and invented data."""
import argparse
from datetime import datetime
import html
import json
from pathlib import Path
from examples.review_lab import numerical_recovery as numerical
from .certified_resume import walkthrough

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'docs/fbs/V025_OPERATIONAL_REVIEW_2026-11-03.json'
OUTPUT=ROOT/'docs/fbs/recovery.html'


def validate(data):
    allowed={'schema','release_date','evidence_class','owner_attempt','last_complete_study','private_recovery_prepared_not_owner_executed','source_snapshot','active_provider_coverage','original_replay_2026','rolling_issued_2026','paper_results','limitations','historical_matched_comparisons'}
    if set(data)!=allowed:raise ValueError('Unknown public release field')
    shapes={
      'owner_attempt':{'release','status','exit_code','planned_learned_fits','attempted_forward_fits','committed_fits','failed_fits','final_fits_not_attempted','reused_fits','new_forecasts','new_orders','new_complete_performance_comparison','failure_class','returned_archive_sha256'},
      'source_snapshot':{'assessment_at','capture_start','capture_end','observed_games','completed_games','pure_fbs_completed_games','upcoming_seven_days','game_market_events','mapped_game_market_events','game_market_rows','mapped_game_market_rows','quarantined_game_market_rows','player_prop_rows','mapped_player_prop_rows','tbd_clock_gaps','explicit_clock_gaps','all_latest_or_complete_coverage_proven'},
      'original_replay_2026':{'evidence_class','games','correct_winners','winner_logloss','winner_brier','margin_mae','total_mae','weekly'},
      'rolling_issued_2026':{'games','winner_logloss','margin_mae','total_mae','status'},
      'paper_results':{'orders','proposed_stake','realized_pnl','roi','status'}}
    for name,shape in shapes.items():
        if set(data[name])!=shape:raise ValueError('Unknown public field in '+name)
    owner=data['owner_attempt'];source=data['source_snapshot']
    count_fields={'planned_learned_fits','attempted_forward_fits','committed_fits','failed_fits','final_fits_not_attempted','reused_fits','new_forecasts','new_orders'}
    if any(type(owner[k]) is not int or owner[k]<0 for k in count_fields):raise ValueError('Owner counts require nonnegative integers')
    if not datetime.fromisoformat(source['capture_start'].replace('Z','+00:00')) <= datetime.fromisoformat(source['capture_end'].replace('Z','+00:00')) <= datetime.fromisoformat(source['assessment_at'].replace('Z','+00:00')):
        raise ValueError('Source capture clock must precede assessment')
    if (owner['committed_fits']+owner['failed_fits']!=owner['attempted_forward_fits'] or
        owner['attempted_forward_fits']+owner['final_fits_not_attempted']!=owner['planned_learned_fits']):
        raise ValueError('Incomplete owner accounting')
    if owner['status']!='PARTIAL' or owner['exit_code']!=2 or owner['new_complete_performance_comparison'] is not False:
        raise ValueError('Partial owner evidence cannot claim a complete new result')
    if source['mapped_game_market_rows']+source['quarantined_game_market_rows']!=source['game_market_rows']:
        raise ValueError('Quote denominator mismatch')
    if source['mapped_game_market_events']+source['tbd_clock_gaps']+source['explicit_clock_gaps']!=source['game_market_events']:
        raise ValueError('Event denominator mismatch')
    if source['all_latest_or_complete_coverage_proven'] is not False:raise ValueError('Unsupported latest/full-coverage claim')
    providers=data['active_provider_coverage']
    if [row['provider'] for row in providers]!=['DraftKings','Kalshi','Polymarket']:raise ValueError('Active provider scope changed')
    provider_shape={'provider','game_market_rows','mapped_rows','observed_events','mapped_events','qualified_current_cutoff_quotes','status'}
    for row in providers:
        if set(row)!=provider_shape or row['qualified_current_cutoff_quotes']!=0:raise ValueError('Unqualified provider payload')
    weeks=data['original_replay_2026']['weekly']
    week_shape={'season','week','games','correct_winner','accuracy','logloss','brier','ece','mcc','margin_mae','margin_rmse','total_mae','total_rmse'}
    if any(set(row)!=week_shape for row in weeks) or len({row['week'] for row in weeks})!=len(weeks):
        raise ValueError('Unknown or duplicate weekly aggregate')
    if sum(row['games'] for row in weeks)!=data['original_replay_2026']['games']:
        raise ValueError('Weekly population mismatch')
    if sum(row['correct_winner'] for row in weeks)!=data['original_replay_2026']['correct_winners']:
        raise ValueError('Weekly outcome count mismatch')
    matched=data['historical_matched_comparisons']
    if set(matched)!={'evidence_class','verification','panels','winner_disagreements','unavailable_providers','live_execution_qualified'}:
        raise ValueError('Unknown matched comparison field')
    if matched['unavailable_providers']!=['Kalshi','Polymarket'] or matched['live_execution_qualified'] is not False:
        raise ValueError('Unsupported historical provider or execution qualification')
    if [(r['provider'],r['market'],r['target']) for r in matched['panels']]!=[('DraftKings','h2h','winner'),('DraftKings','spreads','margin'),('DraftKings','totals','total')]:
        raise ValueError('Unsupported matched provider panels')
    for panel in matched['panels']:
        if set(panel)!={'provider','market','target','n','exact_game_and_label_pairing_verified','cohort_commitment_sha256','model','provider_metrics'}:
            raise ValueError('Unknown matched panel field')
        if panel['exact_game_and_label_pairing_verified'] is not True or panel['n']<=0:
            raise ValueError('Exact matched cohort required')
        if len(panel['cohort_commitment_sha256'])!=64 or any(c not in '0123456789abcdef' for c in panel['cohort_commitment_sha256']):
            raise ValueError('Invalid cohort commitment')
        metrics={'games','correct','accuracy','logloss','brier'} if panel['target']=='winner' else {'games','mae','rmse','bias'}
        for side in ['model','provider_metrics']:
            if set(panel[side])!=metrics or panel[side]['games']!=panel['n']:
                raise ValueError('Matched metric denominator mismatch')
    disagreement=matched['winner_disagreements']
    if set(disagreement)!={'model_right_provider_wrong','model_wrong_provider_right','total_disagreements'} or disagreement['model_right_provider_wrong']+disagreement['model_wrong_provider_right']!=disagreement['total_disagreements']:
        raise ValueError('Disagreement accounting mismatch')
    return data


def fixtures():
    target,curve=(.7,.6,-.1),(1.,1.,1.)
    solved=numerical.recover(target,curve)
    return [
      {'id':'false-success','label':'False success flag','point':[0.,0.,0.],
       'certificate':numerical.certificate(target,curve,(0.,0.,0.),solver_success=True),
       'explanation':'The solver reports success, but the independently computed gap is too large. No state is committed.'},
      {'id':'certified-stop','label':'Certified point, stop retained','point':solved['point'],
       'certificate':solved['certificate'],
       'explanation':'The certificate passes for this explicit convex problem. The original solver-stop status remains visible. This establishes no predictive advantage.'},
      {'id':'infeasible','label':'Infeasible candidate','point':[.7,.6,.1],
       'certificate':numerical.certificate(target,curve,(.7,.6,.1),solver_success=True),
       'explanation':'The coordinates exceed the unit budget. A feasible-domain certificate cannot be issued.'}]


def render():
    data=validate(json.loads(DATA.read_text()));demo=walkthrough();cases=fixtures()
    week_rows=''.join(f'<tr data-week="{r["week"]}"><th scope="row">Week {r["week"]}</th><td>{r["games"]}</td><td>{r["correct_winner"]}</td><td>{r["accuracy"]:.1%}</td><td>{r["logloss"]:.6f}</td><td>{r["brier"]:.6f}</td><td>{r["margin_mae"]:.3f}</td><td>{r["total_mae"]:.3f}</td></tr>' for r in data['original_replay_2026']['weekly'])
    buttons=''.join(f'<button class="button small-button" type="button" data-certificate="{r["id"]}" aria-pressed="'+('true' if i==0 else 'false')+'">'+html.escape(r['label'])+'</button>' for i,r in enumerate(cases))
    provider_rows=''.join('<tr><th scope="row">'+r['provider']+'</th><td>'+('Unavailable' if r['observed_events'] is None else str(r['mapped_events'])+' / '+str(r['observed_events']))+'</td><td>'+('Unavailable' if r['game_market_rows'] is None else str(r['mapped_rows'])+' / '+str(r['game_market_rows']))+'</td><td>0</td><td>'+('Early stale snapshot; 8 event-time gaps' if r['provider']=='DraftKings' else 'Qualified panel unavailable; product absence not established')+'</td></tr>' for r in data['active_provider_coverage'])
    matched_rows=[]
    for panel in data['historical_matched_comparisons']['panels']:
        fields=[('Winner log loss','logloss'),('Winner accuracy','accuracy')] if panel['target']=='winner' else [(panel['target'].title()+' RMSE','rmse')]
        for label,key in fields:
            fmt=(lambda x:f'{x:.2%}') if key=='accuracy' else (lambda x:f'{x:.6f}')
            matched_rows.append(f'<tr><th scope="row">{label}</th><td>{panel["n"]}</td><td>{fmt(panel["model"][key])}</td><td>{fmt(panel["provider_metrics"][key])}</td></tr>')
    payload=json.dumps({'actual':data,'invented':demo,'certificate_cases':cases},sort_keys=True,allow_nan=False).replace('<','\\u003c')
    text=Path(__file__).with_name('recovery_template.html.in').read_text()
    for key,value in {'WEEK_ROWS':week_rows,'PROVIDER_ROWS':provider_rows,'CERTIFICATE_BUTTONS':buttons,'PAYLOAD':payload,'MATCHED_ROWS':''.join(matched_rows)}.items():
        text=text.replace('@@'+key+'@@',value)
    if '@@' in text:raise ValueError('Unfilled recovery template')
    return text


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();result=render()
    if args.check:
        if OUTPUT.read_text()!=result:raise SystemExit('Recovery page differs from its public evidence and invented execution')
        print('Recovery page matches all public aggregates and executable fixtures')
    else:OUTPUT.write_text(result);print(OUTPUT.relative_to(ROOT))

if __name__=='__main__':main()
