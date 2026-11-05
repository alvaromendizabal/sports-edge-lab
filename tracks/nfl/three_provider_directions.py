"""Validate identical-event direction comparisons without inventing quote probabilities."""
import hashlib,json
from pathlib import Path
from point_markets import require
HERE=Path(__file__).resolve().parent
PROVIDERS=['DraftKings','Kalshi','Polymarket']

def validate_three_provider(d,coverage):
    require(d['schema']=='sports-edge-lab.nfl.three-provider-directions.v1','Unknown three-provider contract')
    require(d['providers']==PROVIDERS and d['season']==2026 and d['horizon']=='T2' and d['target']=='winner_direction','Comparison definitions differ')
    require(d['source_refresh_credit']==d['new_model_fits']==d['new_forecasts']==0 and d['historical_values_changed'] is False,'Derived report cannot become new research or source acquisition')
    require(len(d['games'])==91 and len({g['game_id']for g in d['games']})==91,'Three-provider common cohort changed')
    source={g['game_id']:g for g in coverage['all_games']}
    cohort=hashlib.sha256(('\n'.join(sorted(g['game_id']for g in d['games']))+'\n').encode()).hexdigest()
    require(cohort==d['cohort_sha256'],'Event identity differs')
    for g in d['games']:
        original=source[g['game_id']]
        require(original['completed'] and original['actual']['winner']==g['winner'] and g['winner']in(g['home'],g['away']),'Final/result mismatch')
        require(set(g['providers'])==set(PROVIDERS) and set(g['models'])==set(d['models']),'Missing common model or provider')
        for p,r in g['providers'].items():
            rr=next(x for x in original['providers']if x['provider']==p and x['horizon']=='T2')
            require(rr['metric_eligible'] and r['pick']==rr['derived_pick'] and r['correct']==(r['pick']==g['winner']),'Provider direction differs')
            require(all(r[k]==rr[k]for k in ('quote_at','acquired_at','quote_clock_kind','comparison_rule')),'Provider clock or original qualification changed')
        for mid,r in g['models'].items():
            rr=next(x for x in original['forecasts']if x['model_id']==mid)
            require(r['pick']==rr['pick'] and r['origin']==rr['origin'] and r['correct']==(r['pick']==g['winner']),'Model origin or direction changed')
    require(len(d['summary'])==18 and len({(r['model_id'],r['provider'])for r in d['summary']})==18,'Missing/duplicate comparison')
    for r in d['summary']:
        m,p=r['model_id'],r['provider'];mc=sum(g['models'][m]['correct']for g in d['games']);pc=sum(g['providers'][p]['correct']for g in d['games'])
        require(r['games']==91 and r['cohort_sha256']==cohort and r['model_correct']==mc and r['provider_correct']==pc,'Paired denominator or count changed')
        require(abs(r['model_accuracy']-mc/91)<1e-12 and abs(r['provider_accuracy']-pc/91)<1e-12 and abs(r['accuracy_difference']-(mc-pc)/91)<1e-12,'Incorrect paired accuracy')
        disagreements=[g for g in d['games']if g['models'][m]['pick']!=g['providers'][p]['pick']]
        require(r['disagreements_won']==sum(g['models'][m]['correct']for g in disagreements) and r['disagreements_lost']==sum(g['providers'][p]['correct']for g in disagreements),'Disagreement wins/losses omitted')
        require(r['probability_metrics']is None and r['pnl']is None,'Directions cannot establish probability loss or profit')
        require(r['bootstrap_draws']==5000 and r['week_clusters']==8 and -1<=r['week_bootstrap_95_low']<=r['week_bootstrap_95_high']<=1,'Invalid clustered uncertainty')
    require(len(d['weekly'])==144 and len(d['disagreements'])==226,'Weekly/disagreement scope changed')
    return {'three_provider_common_games':91,'three_provider_common_directions':18,'three_provider_common_weekly_rows':144,'three_provider_common_disagreements':226,'three_provider_new_model_fits':0}

def load_three_provider(coverage):
    p=HERE/'three_provider_directions.json';d=json.loads(p.read_text())
    require(d['source_sha256']==hashlib.sha256((HERE/'current_coverage.json').read_bytes()).hexdigest(),'Retained evidence source changed')
    return d,validate_three_provider(d,coverage)
