"""Validate identical-event direction comparisons without inventing quote probabilities."""
import hashlib,json
from datetime import datetime,timedelta
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
    recovered=d['restored_draftkings_t2'];rows=recovered['rows']
    require(recovered['status']=='ORIGINAL_RAW_PRICE_AND_CLOCKS_VERIFIED' and recovered['provider']=='DraftKings' and recovered['horizon']=='T2','Unknown restored clock scope')
    require(len(rows)==120 and len({r['game_id']for r in rows})==120,'Restored DraftKings event scope changed')
    require(recovered['original_raw_bodies_verified']==31 and recovered['source_capsule_payloads']==18,'Original source verification differs')
    require(recovered['new_paid_calls']==recovered['new_model_fits']==recovered['new_forecasts']==0,'Restored references cannot become new work')
    require(recovered['execution_qualified']is False and recovered['latest_quote_claim']is False and recovered['actual_pnl']is None,'Retained references do not prove latest prices or executable profit')
    dt=lambda x:datetime.fromisoformat(x.replace('Z','+00:00'))
    for r in rows:
        g=source[r['game_id']];cut=dt(r['cutoff_at']);quote=dt(r['quote_at']);observed=dt(r['acquired_at']);snapshot=dt(r['provider_snapshot_at']) if r['provider_snapshot_at'] else observed
        require(dt(g['kickoff_utc'])==dt(r['kickoff_utc']) and cut==dt(r['kickoff_utc'])-timedelta(hours=2),'Restored kickoff or horizon differs')
        require(quote<=snapshot<=cut and abs((cut-quote).total_seconds()-r['quote_age_at_cutoff_seconds'])<1e-6,'Restored quote clock is after cutoff or age differs')
        require(r['contemporaneously_possessed_by_t2']==(observed<=cut),'Historical acquisition cannot become contemporaneous possession')
        old=next(x for x in g['providers']if x['provider']=='DraftKings' and x['horizon']=='T2')
        require(r['provider_pick']==old['derived_pick'],'Recovered direction changed')
    require(sum(r['contemporaneously_possessed_by_t2']for r in rows)==40 and recovered['historical_retrievals']==80,'Restored possession accounting differs')
    require(min(r['quote_age_at_cutoff_seconds']for r in rows)==3204 and max(r['quote_age_at_cutoff_seconds']for r in rows)==79549,'Restored quote-age range differs')
    require(recovered['non_ties']==119 and recovered['correct']==77 and abs(recovered['log_loss']-0.6471026136108166)<1e-12 and abs(recovered['brier']-0.22642348653906716)<1e-12,'Retained full-precision probability metrics changed')
    p=d['restored_probability_review']
    require(p['common_non_tie_games']==91 and p['weeks']==list(range(1,9)) and p['cohort_sha256']==cohort,'Probability cohort differs')
    require(p['provider_order']==PROVIDERS and len(p['metrics'])==5 and len(p['intervals'])==18,'Probability comparison incomplete')
    require(p['new_fits']==p['new_forecasts']==p['new_paid_calls']==0 and p['latest_or_T1_relabeling']is False and p['prospective_or_durable_edge_established']is False,'Retained probabilities do not establish new work or edge')
    require(p['zero_tie_proxy']is True and p['half_tie_settlement_preserved']is True and p['model_label_clock_publication_proxy_unverified']is True and p['historical_snapshot_acquisition_may_postdate_game']is True and p['no_rounding_rescore']is True,'Original source and scientific limitations must remain explicit')
    expected={'DraftKings':(62,.6203217285927107,.21460957604332695),'Kalshi':(62,.6166888127339715,.213014010989011),'Polymarket':(63,.6153173648197255,.21245357142857144),'market_error_feedback':(63,.6060826675996539,.209164752870539),'market_legacy_synergy':(61,.6316434264428007,.22112595340466323)}
    require({r['name']for r in p['metrics']}==set(expected),'Missing probability record')
    for r in p['metrics']:
        correct,ll,brier=expected[r['name']]
        require(r['n']==91 and r['correct']==correct and abs(r['accuracy']-correct/91)<1e-12 and abs(r['log_loss']-ll)<1e-12 and abs(r['brier']-brier)<1e-12,'Recovered full-precision metric changed')
    require(len({(r['model'],r['provider'],r['metric'])for r in p['intervals']})==18,'Duplicate probability interval')
    for r in p['intervals']:
        require(r['common_non_tie_games']==91 and r['week_clusters']==8 and r['whole_week_bootstrap_draws']==5000 and r['seed']==44045 and r['ci95_low']<0<r['ci95_high'],'Probability uncertainty changed or zero-crossing concealed')
        if r['metric']=='accuracy':
            mid={'market_error_feedback':'descriptive_feedback','market_legacy_synergy':'descriptive_accuracy'}[r['model']]
            same=next(x for x in d['summary']if x['model_id']==mid and x['provider']==r['provider'])
            require(abs(r['difference_model_minus_provider']-same['accuracy_difference'])<1e-12 and abs(r['ci95_low']-same['week_bootstrap_95_low'])<1e-12 and abs(r['ci95_high']-same['week_bootstrap_95_high'])<1e-12,'Identical accuracy comparisons must use identical bootstrap draws')
    return {'three_provider_common_games':91,'three_provider_common_directions':18,'three_provider_common_weekly_rows':144,'three_provider_common_disagreements':226,'three_provider_new_model_fits':0,'restored_draftkings_t2_clocks':120,'restored_common_probability_records':5}

def load_three_provider(coverage):
    p=HERE/'three_provider_directions.json';d=json.loads(p.read_text())
    require(d['source_sha256']==hashlib.sha256((HERE/'current_coverage.json').read_bytes()).hexdigest(),'Retained evidence source changed')
    return d,validate_three_provider(d,coverage)
