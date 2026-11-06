"""Public, rounded distribution evidence; no fitted state or source feed is exported."""
import hashlib,json,math
from pathlib import Path
from point_markets import require
from market_clock import instant
HERE=Path(__file__).resolve().parent

def validate_cover(d,coverage,issues):
    require(d['schema']=='sports-edge-lab.nfl.margin-distribution-research.n047.v1','Unknown cover schema')
    require(d['owner_return_sha256']==issues['owner_return_sha256'],'Cover owner differs')
    require(d['status']=='COMPLETE_REGISTERED_DISTRIBUTION_RESEARCH','Unsupported study status')
    require(d['new_distribution_fits']==15 and d['new_native_fits']==0,'Fit classes confused')
    require(all(d[k] is False for k in ('automatic_promotion','calibration_validated','owner_research_acceptance')),'Unvalidated transfer promoted')
    require(d['actual_orders']==0 and d['final_hour_qualified_cards']==0,'Invented order or qualification')
    require(d['pre2024_selection_games']==569 and d['final_distribution_training_games']==854,'Selection scope differs')
    require(len(d['season_metrics'])==9 and len(d['provider_metrics'])==6 and len(d['paired_intervals'])==6,'Missing research cohort')
    require(len(d['cards'])==28 and len(d['threshold_rows'])==82 and len(d['historical_games'])==636,'Report population differs')
    games={g['game_id']:g for g in coverage['all_games']};parents={c['game_id']:c for s in issues['streams'] if s['role']=='designation' for c in s['cards']}
    require({c['game_id']for c in d['cards']}==set(parents),'Cover parents differ')
    for c in d['cards']:
        p=parents[c['game_id']];require(c['home_margin']==p['home_margin'],'Current point parent differs')
        require(c['parent_point_issue_at_utc']==p['actual_issue_at'] and c['parent_feature_asof_at_utc']==p['base_feature_asof_at'],'Parent clocks changed')
        require(instant(c['parent_point_issue_at_utc'])<=instant(c['distribution_fit_completed_at'])<=instant(c['actual_issue_at_utc'])<instant(c['kickoff_utc']),'Invalid issue clock')
        require(c['actual'] is None and c['automatic_promotion'] is False and c['calibration_validated'] is False,'Future outcome or promotion')
        prev=None
        for q in ('50','80','90','95'):
            a,b=c['intervals'][q];require(type(a)is int and type(b)is int and a<=b,'Invalid discrete interval')
            if prev:require(a<=prev[0] and b>=prev[1],'Intervals not nested')
            prev=(a,b)
    for r in d['threshold_rows']:
        require(r['game_id']in parents and r['provider']in ('kalshi','polymarket','draftkings'),'Unknown reference identity')
        probs=[r[k]for k in ('probability_above_threshold','probability_equal_threshold','probability_below_threshold')]
        require(all(0<=v<=1 for v in probs)and abs(sum(probs)-1)<=.00101,'Rounded probability mass differs')
        require(r['actual'] is None and r['executable_quote_claimed'] is False and r['fee_adjusted_ev'] is None,'Invented wager result')
        require(instant(r['observed_at_utc'])<=instant(r['actual_issue_at_utc']),'Quote observed after issue')
        if r['settlement_policy']=='UNKNOWN':require(r['scoring_probability'] is None and r['settlement_scoring_eligible'] is False,'Unknown settlement cannot be scored')
    require(sum(r['settlement_policy']=='UNKNOWN'for r in d['threshold_rows'])==54,'Settlement gaps changed')
    for r in d['provider_metrics']:
        require(r['games']==(120 if r['provider']=='kalshi' else 92),'Provider cohort changed')
        require(r['correct']-r['provider_correct']==r['model_right_provider_wrong']-r['provider_right_model_wrong'],'Disagreement reconciliation fails')
    # Adverse evidence cannot be erased by the older winner comparison.
    for r in d['paired_intervals']:
        if r['provider']=='kalshi':require(r['model_minus_provider_log_loss_paired_week_bootstrap_95'][0]>0,'Negative cover finding changed')
    return {'cover_n047_validation':'PASS','new_distribution_states':15,'cover_current_rows':82,'cover_interval_cards':28,'historical_contract_rows':636,'calibration_validated':False}

def load_cover(coverage,issues):
    p=HERE/'cover_research_n047.json';d=json.loads(p.read_text());return d,{**validate_cover(d,coverage,issues),'cover_n047_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
