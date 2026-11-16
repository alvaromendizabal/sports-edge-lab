"""Public selected-role NBA comparison, with complete observed-game membership.

This copies already published analytical values. It neither fits nor scores a
model and never invents a per-game market observation from an aggregate count.
"""
from __future__ import annotations
import argparse
import base64
import copy
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from equal_population_public import validate_public as validate_equal_population
from draftkings_public import download_projection

ROOT = Path(__file__).resolve().parent
PROVIDERS = ('DRAFTKINGS', 'KALSHI', 'POLYMARKET_US', 'POLYMARKET_INTERNATIONAL')
PUBLIC_OWNER_FIELDS = ('release', 'observed_at_utc', 'started_at_utc', 'finished_at_utc', 'status',
                       'exit_code', 'new_estimator_method_returns', 'new_unique_model_count',
                       'reused_model_count', 'failed_model_count', 'new_forecast_rows',
                       'return_verified', 'return_parts', 'active_run', 'limitations',
                       'verified_payloads', 'scientific_status', 'source_receipt_sha256',
                       'return_logical_bytes', 'return_representation', 'total_elapsed_seconds',
                       'new_calibration_fits', 'successful_jobs', 'failed_jobs',
                       'return_verified_at_utc', 'return_verification_receipt_sha256',
                       'historical_snapshot_utc', 'full_current_model_test_cells', 'automatic_promotions',
                       'execution_receipt_sha256s', 'forward_source_correction_pending')

def validate_cached_science(value):
    """Reject private data and unsupported claims in the aggregate-only audit."""
    forbidden_keys = {'event_id', 'game_id', 'memberships', 'predictions', 'prediction',
        'recipe_id', 'cohort_id', 'feature_names', 'feature_values', 'raw_payload',
        'raw_record', 'source_url', 'source_path', 'account_id', 'credentials',
        'access_token', 'yes_bid', 'yes_ask', 'no_bid', 'no_ask', 'player_id', 'person_id'}
    def public(node):
        if isinstance(node, dict):
            if forbidden_keys.intersection(node): raise ValueError('Private audit field')
            for child in node.values(): public(child)
        elif isinstance(node, list):
            for child in node: public(child)
        elif isinstance(node, str) and any(x in node.lower() for x in
                ('s3://', 'arn:aws:', '/home/', '/workspace/', 'https://', 'http://', 'nba:espn:event:')):
            raise ValueError('Private audit content')
    public(value)
    audit = value['paired_audit']
    if audit['promotion_allowed'] is not False or audit['provider_baseline_comparison'] is not False:
        raise ValueError('Unsupported audit qualification')
    if any(audit['new_work'][k] != 0 for k in ('new_fits', 'new_forecasts', 'models_modified')):
        raise ValueError('Audit cannot claim fits or forecasts')
    aliases = {'HGB72', 'market_only9', 'ExtraTrees63'}
    def cohort(row):
        n = row['games']
        if type(n) is not int or n <= 0 or set(row['metrics']) != aliases:
            raise ValueError('Invalid paired cohort')
        for metrics in row['metrics'].values():
            if metrics['games'] != n: raise ValueError('Paired cohort size mismatch')
            for metric in ('accuracy', 'brier', 'log_loss'):
                number = metrics[metric]
                if isinstance(number, bool) or not isinstance(number, (float, int)) or not math.isfinite(number) or number < 0:
                    raise ValueError('Invalid paired metric')
            if metrics['accuracy'] > 1: raise ValueError('Invalid paired accuracy')
        expected_pairs = {f'{left}__minus__{right}' for left, right in
            (('ExtraTrees63', 'HGB72'), ('ExtraTrees63', 'market_only9'), ('HGB72', 'market_only9'))}
        if set(row['pairs']) != expected_pairs: raise ValueError('Incomplete paired differences')
        for key, pair in row['pairs'].items():
            if pair['games'] != n: raise ValueError('Paired cohort difference size mismatch')
            left, right = key.split('__minus__')
            for metric, paired_metric in [('brier','brier'), ('log_loss','log_loss'), ('accuracy','correctness')]:
                expected = row['metrics'][left][metric] - row['metrics'][right][metric]
                if not math.isclose(expected, pair['mean_left_minus_right'][paired_metric], rel_tol=0, abs_tol=1e-12):
                    raise ValueError('Inconsistent paired difference')
        return n
    total = cohort(audit['overall'])
    if total != audit['games'] or total + audit['missing_from_common'] != audit['completed_denominator_in_prior_snapshot']:
        raise ValueError('Inconsistent paired cohort denominator')
    if set(audit['week_views']) != {'UTC', 'America/Los_Angeles'}:
        raise ValueError('Unsupported week boundary')
    for view in audit['week_views'].values():
        if view['bounds_are_confidence_intervals'] is not False:
            raise ValueError('Sensitivity bounds are not confidence intervals')
        weeks = view['weekly']
        excluded = view['leave_one_week_out']
        if set(weeks) != set(excluded) or len(weeks) != view['week_clusters']:
            raise ValueError('Inconsistent weekly cohort partition')
        if sum(cohort(row) for row in weeks.values()) != total:
            raise ValueError('Incomplete weekly cohort partition')
        for week, row in excluded.items():
            if cohort(row) + weeks[week]['games'] != total:
                raise ValueError('Inconsistent deleted-week cohort')
    feature = value['secondary_features']
    if feature['promotion_allowed'] is not False or feature['predictive_improvement_established'] is not False:
        raise ValueError('Materialization does not establish predictive improvement')
    if any(feature[k] != 0 for k in ('new_model_fits', 'new_calibration_fits', 'new_forecasts', 'new_provider_requests')):
        raise ValueError('Materialization cannot claim fits, forecasts or source calls')
    source = value['source_recovery']
    if source['current_quote_refresh_verified'] is not False or source['current_market_rows_newly_admitted'] != 0:
        raise ValueError('Connection check cannot qualify market quotes')
    return value

def read_json(path):
    raw = path.read_bytes()
    if path.suffix == '.gz': raw = gzip.decompress(raw)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()

def apply_current_inventory(result, inventory):
    """Update official game facts while preserving original forecast clocks."""
    if inventory.get('schema') != 'sel.nba.current_game_inventory.v1':
        raise ValueError('Unsupported current game inventory')
    old = {game['game_id']: game for game in result['games']}
    fresh = {game['game_id']: game for game in inventory['rows']}
    if len(fresh) != len(inventory['rows']) or not set(old).issubset(fresh):
        raise ValueError('Current inventory duplicates or drops observed official games')
    allowed = {'game_id','season','phase','away_team','home_team','scheduled_start_utc',
               'status','status_asof_utc','schedule_source_asof_utc','actual'}
    seen_final = 0
    for game_id, row in fresh.items():
        if set(row) != allowed or row['season'] != '2026-27':
            raise ValueError('Unsupported current game field or season')
        if row['status'] not in ('FINAL','LIVE','SCHEDULED','TBD'):
            raise ValueError('Secondary or unknown status cannot be an official game')
        actual = row['actual']
        if row['status'] == 'FINAL':
            if not all(isinstance(actual.get(k), (int,float)) and math.isfinite(actual[k]) for k in ('home_points','away_points')):
                raise ValueError('Final current game lacks a verified score')
            seen_final += 1
        elif actual:
            raise ValueError('Nonfinal current game cannot acquire a final outcome')
        if game_id in old:
            prior = old[game_id]
            for field in ('home_team','away_team','scheduled_start_utc'):
                # A changed schedule requires a separately qualified issue view;
                # this refresh cannot silently rebind an original forecast.
                a,b = prior.get(field),row.get(field)
                equal = datetime.fromisoformat(a.replace('Z','+00:00')) == datetime.fromisoformat(b.replace('Z','+00:00')) if field == 'scheduled_start_utc' and a and b else a == b
                if not equal and prior['forecasts']:
                    raise ValueError('Current identity changed beneath an original issue')
            prior.update(copy.deepcopy(row))
        else:
            old[game_id] = {**copy.deepcopy(row),'away_team_name':None,'home_team_name':None,'forecasts':{},
                'markets':{provider:{'status':'NO_CANONICAL_BINDING_IN_AUDITED_SNAPSHOT','value':None,
                    'provider_quote_at_utc':None,'observed_at_utc':None,'bound_observations':0} for provider in PROVIDERS}}
    result['games'] = sorted(old.values(),key=lambda g:(g.get('scheduled_start_utc') or '9999',g['game_id']))
    regular = [g for g in result['games'] if g['phase'] == 'regular']
    counts = dict(sorted(Counter(g['status'] for g in result['games']).items()))
    expected = inventory['regular_season_expected_games']
    if len(regular) > expected:
        raise ValueError('Canonical regular inventory exceeds expected season')
    result['current_game_inventory'] = {k:copy.deepcopy(v) for k,v in inventory.items() if k != 'rows'}
    result['game_inventory_evidence_as_of_utc'] = inventory['observed_at_utc']
    result['coverage'].update(observed_games=len(old),current_official_inventory_games=len(old),
        regular_observed_games=len(regular),regular_full_season_denominator=expected,
        unobserved_regular_slots=expected-len(regular),row_backed_status_counts=counts,
        regular_status_counts=dict(sorted(Counter(g['status'] for g in regular).items())),
        secondary_observations=inventory['secondary_observation_count'],
        games_with_source_bound_final_score=seen_final,
        future_tips_at_evidence_snapshot=sum(g['status'] in ('SCHEDULED','TBD') for g in result['games']),
        full_season_completion_claim=False,future_full_schedule_complete=False)

def apply_reference_coverage(result, references):
    by_game = {r['game_id']: r for r in result['games']}
    seen = set()
    stamp = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00'))
    for reference in references['rows']:
        row = by_game.get(reference['game_id'])
        if row is None or (row['away_team'], row['home_team']) != (reference['away_team'], reference['home_team']):
            raise ValueError('Reference game identity mismatch')
        if stamp(row['scheduled_start_utc']) != stamp(reference['scheduled_start_utc']):
            raise ValueError('Reference scheduled-start mismatch')
        if stamp(reference['observed_at_utc']) >= stamp(reference['scheduled_start_utc']):
            raise ValueError('Reference observed after pregame boundary')
        if reference['provider'] not in PROVIDERS or reference.get('value') is not None:
            raise ValueError('Unqualified public provider price')
        if reference.get('provider_quote_at_utc') is not None or reference.get('quote_age_unknown') is not True:
            raise ValueError('Unproven provider quote clock')
        key = (reference['game_id'], reference['provider'])
        if key in seen: raise ValueError('Duplicate selected reference coverage')
        seen.add(key)
        row['markets'][reference['provider']].update(copy.deepcopy(reference))
    result['per_game_reference_coverage_rows'] = len(seen)
    result['reference_coverage'] = {k:copy.deepcopy(v) for k,v in references.items() if k!='rows'}

def project(selected, review, acceptance, leaders, owner=None):
    games = selected['games']
    issue_views = {}
    for view in selected['role_views']:
        key = view.get('current_issue_ref')
        issue = selected['issues'].get(key) if key else None
        if issue is None: continue
        if issue['game_id'] != view['game_id']:
            raise ValueError('Issue/game mismatch')
        if not issue.get('original_pregame_issue'):
            raise ValueError('Selected forecast lacks its original pregame issue qualification')
        issue_views.setdefault(view['game_id'], {})[view['champion_role']] = {
            'home_win_probability': issue.get('home_win_probability'),
            'prediction': issue.get('prediction'),
            'issued_at_utc': issue.get('issued_at_utc'),
            'source_asof_utc': issue.get('source_asof_utc'),
            'issue_horizon_class': issue.get('issue_horizon_class'),
            'actual_lead_minutes': issue.get('actual_lead_minutes'),
            'family': issue.get('champion_at_issue_family'),
            'prediction_intervals': copy.deepcopy(issue.get('prediction_intervals')),
            'scheduled_start_at_issue_utc': issue.get('scheduled_start_at_issue_utc'),
        }
    actuals = {g['game_id']: copy.deepcopy(g.get('actual', {})) for g in acceptance['game_rows']}
    rows = []
    for game_id, g in sorted(games.items(), key=lambda p: (p[1].get('scheduled_start_utc') or '9999', p[0])):
        rows.append({
            'game_id': game_id, 'season': g.get('season'), 'phase': g.get('phase'),
            'away_team': g.get('away_team'), 'home_team': g.get('home_team'),
            'away_team_name': g.get('away_team_name'), 'home_team_name': g.get('home_team_name'),
            'scheduled_start_utc': g.get('scheduled_start_utc'),
            'status': g.get('last_confirmed_status'),
            'status_asof_utc': g.get('last_confirmed_status_asof_utc'),
            'schedule_source_asof_utc': g.get('schedule_source_asof_utc'),
            'actual': actuals.get(game_id, {}),
            'forecasts': issue_views.get(game_id, {}),
            'markets': {provider: {'status': 'ROW_LEVEL_OBSERVATION_NOT_EXPORTED', 'value': None,
                'provider_quote_at_utc': None, 'observed_at_utc': None,
                'reason': 'No authenticated per-game comparison record supplied to this public projection.'}
                for provider in PROVIDERS},
        })
    if len(rows) != len(games) or {g['game_id'] for g in rows} != set(games):
        raise ValueError('Observed schedule membership changed')
    owner = owner or {}
    public_owner = {key: copy.deepcopy(owner[key]) for key in PUBLIC_OWNER_FIELDS if key in owner}
    return {
        'schema': 'sports-edge-lab.nba.season-market-comparison.v1',
        'title': 'NBA Models & Market Comparison',
        'scientific_evidence_as_of_utc': selected['evidence_as_of_utc'],
        'latest_original_issue_at_utc': selected['latest_forecast_issue_at_utc'],
        'market_comparison_evidence_as_of_utc': review['evidence_as_of_utc'],
        'game_inventory_evidence_as_of_utc': acceptance['evidence_as_of_utc'],
        'schedule_observation': copy.deepcopy(selected['schedule_observation']),
        'coverage': copy.deepcopy(acceptance['coverage']),
        'owner_execution': public_owner,
        'providers': list(PROVIDERS),
        'market_coverage_complete': False,
        'market_coverage_scope': 'Saved admitted comparisons and explicit gaps. Raw acquisition coverage is not inferred from this export.',
        'per_game_market_rows_exported': 0,
        'provider_coverage': copy.deepcopy(review['venue_coverage']),
        'matched_comparisons': copy.deepcopy(review['venue_comparisons']),
        'saved_model_metrics': copy.deepcopy(review['metric_rows']),
        'saved_current_cohort_leaders': copy.deepcopy(leaders['rows']),
        'champions': copy.deepcopy(selected['champions']),
        'games': rows,
        'publication_effects': {'new_model_fits': 0, 'new_forecasts': 0, 'new_scoring': 0, 'provider_requests': 0, 'automatic_promotions': 0},
        'qualifications': [
            'Every observed game remains in the table, including games without forecasts, market references or resolved matchups.',
            'Future games have no final outcome. Not-yet-listed markets and unavailable historical observations require separate source evidence.',
            'Current-season scores, historical reconstructions and original issued forecasts remain separate. Historical roles are not newly promoted winners.',
            'A raw binary bid/ask midpoint is a descriptive reference, not a fair no-vig probability, an executable price, an expected margin or an expected total.',
            'A nominal T60 or T120 model label does not establish the actual issue time. Early outlooks preserve their real clocks.',
            'No admitted comparison is different from no acquired data; absent row-level records are unknown, never zero prices.',
            'Latest owner execution, forecast issue, game inventory, source inventory and matched-scoreboard timestamps are distinct.',
        ],
    }

def build(root=ROOT):
    config_path = root / 'season_comparison_sources.json'
    config = read_json(config_path)[0] if config_path.exists() else {
        'selected_outputs': 'latest_research_outputs.json.gz',
        'model_review': 'latest_model_review.json',
        'acceptance': 'latest_v9_acceptance.json.gz',
        'cohort_leaders': 'current_saved_cohort_leaders.json',
    }
    def source(key):
        path = (root / config[key]).resolve()
        if not path.is_relative_to(root.resolve()): raise ValueError('Source path leaves public report root')
        return read_json(path)
    selected, a = source('selected_outputs')
    review, b = source('model_review')
    acceptance, c = source('acceptance')
    leaders, d = source('cohort_leaders')
    owner_path = root / 'latest_owner_summary.json'
    owner = read_json(owner_path)[0] if owner_path.exists() else {}
    result = project(selected, review, acceptance, leaders, owner)
    result['source_payload_sha256'] = {'selected_outputs': a, 'model_review': b, 'acceptance': c, 'cohort_leaders': d}
    result['source_public_files'] = config
    inventory_path = root / 'current_provider_game_coverage.json'
    if inventory_path.exists():
        inventory, inventory_hash = read_json(inventory_path)
        result['source_payload_sha256']['provider_game_coverage'] = inventory_hash
        result['provider_game_coverage'] = {k:copy.deepcopy(v) for k,v in inventory.items() if k!='rows'}
        by_game = {r['game_id']:r for r in result['games']}
        for game in result['games']:
            for provider, market in game['markets'].items():
                market.update(status='NO_CANONICAL_BINDING_IN_AUDITED_SNAPSHOT', bound_observations=0,
                    reason='No observation is bound to this game in the audited snapshot. Unbound provider observations cannot be assigned to a game.')
        for bound in inventory['rows']:
            if bound['game_id'] not in by_game or bound['provider'] not in PROVIDERS:
                raise ValueError('Provider inventory game/provider mismatch')
            if bound['strict_contracts'] != 0 or bound['provider_quote_at_utc'] is not None:
                raise ValueError('Inventory cannot manufacture qualified contracts or quote clocks')
            target = by_game[bound['game_id']]['markets'][bound['provider']]
            target.update(copy.deepcopy(bound),status='GAME_BOUND_OBSERVATIONS_CONTRACT_UNQUALIFIED',
                reason='Retained observations have a canonical game binding. Exact contract, side and quote-clock validation remains incomplete.')
    if config.get('winner_references'):
        references, ref_hash = source('winner_references')
        result['source_payload_sha256']['winner_references'] = ref_hash
        apply_reference_coverage(result, references)
    coverage_path = root / 'latest_source_coverage.json'
    if coverage_path.exists():
        result['source_coverage'], source_coverage_hash = read_json(coverage_path)
        result['source_payload_sha256']['source_coverage'] = source_coverage_hash
    model_details_path = root / 'current_model_role_details.json'
    if model_details_path.exists():
        result['current_model_role_details'], detail_hash = read_json(model_details_path)
        result['source_payload_sha256']['current_model_role_details'] = detail_hash
    score_path = root / 'current_science_scores.json'
    if score_path.exists():
        result['current_science_scores'], score_hash = read_json(score_path)
        result['source_payload_sha256']['current_science_scores'] = score_hash
    recovery_path = root / 'b088_cached_science.json'
    if recovery_path.exists():
        recovery, recovery_hash = read_json(recovery_path)
        result['b088_cached_science'] = validate_cached_science(recovery)
        result['source_payload_sha256']['b088_cached_science'] = recovery_hash
    equal_path = root / 'all_candidate_scoreboard.json.gz'
    if not equal_path.exists(): equal_path = root / 'equal_cohort_scoreboard.json'
    if equal_path.exists():
        equal, equal_hash = read_json(equal_path)
        result['equal_population_evaluation'] = validate_equal_population(equal)
        result['source_payload_sha256']['equal_population_evaluation'] = equal_hash
    validation_path = root / 'validation_leaders.json'
    if validation_path.exists():
        from validation_leaders_public import validate_public as validate_leaders
        validation, validation_hash = read_json(validation_path)
        result['validation_leaders'] = validate_leaders(validation, result['equal_population_evaluation'])
        result['source_payload_sha256']['validation_leaders'] = validation_hash
    inventory_path = root / 'current_game_inventory.json'
    if inventory_path.exists():
        inventory, inventory_hash = read_json(inventory_path)
        apply_current_inventory(result, inventory)
        result['source_payload_sha256']['current_game_inventory'] = inventory_hash
        current_populations = [p for p in result.get('equal_population_evaluation',{}).get('populations',[])
                               if p['season']=='2026-27' and p['phase']=='regular']
        if current_populations and current_populations[0]['required_games'] != result['coverage']['regular_status_counts'].get('FINAL',0):
            raise ValueError('Evaluation and refreshed official final populations disagree')
    # Optional private build input. This file is not a standalone public feed;
    # only its minimal analytical projection is embedded in the dashboard HTML.
    draftkings_path = root / 'draftkings_analytical.private.json'
    if draftkings_path.exists():
        from draftkings_public import project_normalized
        market_input, _ = read_json(draftkings_path)
        normalized = json.dumps(market_input['normalized'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        result['draftkings_analytical'] = project_normalized(normalized,
            expected_sha256=market_input['normalized_canonical_sha256'], games=result['games'],
            required_game_ids=market_input['required_game_ids'])
        result['source_payload_sha256']['draftkings_normalized'] = market_input['normalized_canonical_sha256']
    elif (root / 'draftkings_public_summary.json').exists():
        # The immutable analytical HTML is itself the public display receipt.
        # Reuse only cryptographically identical embedded UI bytes; a summary
        # does not manufacture unavailable private source rows for regeneration.
        summary, _ = read_json(root / 'draftkings_public_summary.json')
        prior = (root / 'season_comparison.html').read_text()
        matched = re.search(r'<script id="nba-comparison-payload" type="application/octet-stream">([^<]+)</script>', prior)
        if not matched: raise ValueError('Prior analytical display receipt missing')
        saved = json.loads(gzip.decompress(base64.b64decode(matched.group(1))))['draftkings_analytical']
        encoded_saved = json.dumps(saved,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        if hashlib.sha256(encoded_saved).hexdigest() != summary['analytical_ui_projection_sha256']:
            raise ValueError('Prior analytical display receipt fingerprint changed')
        actual_summary = download_projection({'draftkings_analytical':saved})['draftkings_analytical']
        if actual_summary != summary['summary']:
            raise ValueError('Prior analytical display disagrees with public aggregate summary')
        result['draftkings_analytical'] = saved
        result['source_payload_sha256']['draftkings_normalized'] = saved['source_normalized_sha256']
    exchange_path = root / 'current_exchange_inventory.json'
    if exchange_path.exists():
        from exchange_inventory_public import validate_public as validate_exchange_inventory
        exchange, exchange_hash = read_json(exchange_path)
        result['current_exchange_inventory'] = validate_exchange_inventory(
            exchange, result['games'], inventory['source_snapshot_sha256'])
        result['source_payload_sha256']['current_exchange_inventory'] = exchange_hash
    paired_path = root / 'all_candidate_market_comparison.json.gz'
    if not paired_path.exists(): paired_path = root / 'model_market_comparison.json'
    if paired_path.exists():
        from model_market_public import validate_public as validate_model_market
        paired, paired_hash = read_json(paired_path)
        paired = validate_model_market(paired,result['equal_population_evaluation'])
        if paired['model_scoreboard_source_sha256'] != result['equal_population_evaluation']['source_receipt_sha256']:
            raise ValueError('Paired scores refer to a different model scoreboard receipt')
        if paired['normalized_quotes_sha256'] != result.get('draftkings_analytical',{}).get('source_normalized_sha256'):
            raise ValueError('Paired scores refer to a different market snapshot')
        if any(g['required_games'] != result['coverage']['regular_status_counts'].get('FINAL',0) for g in paired['groups']):
            raise ValueError('Paired scores changed the current completed denominator')
        result['model_market_comparison'] = paired
        result['source_payload_sha256']['model_market_comparison'] = paired_hash
    ats_path = root / 'ats_point_diagnostics.json'
    if ats_path.exists():
        from ats_public import validate_public as validate_ats
        ats, ats_hash = read_json(ats_path)
        result['ats_point_diagnostics'] = validate_ats(ats, result['model_market_comparison'])
        result['source_payload_sha256']['ats_point_diagnostics'] = ats_hash
    forward_path = root / 'forward_forecasts_public.json.gz'
    if forward_path.exists():
        from forward_forecasts_public import apply_public as apply_forward
        forward, forward_hash = read_json(forward_path)
        apply_forward(result,forward)
        result['source_payload_sha256']['forward_forecasts_public'] = forward_hash
    for current_forward_name in ('b090_earlier_forward_forecasts_public.json.gz', 'current_forward_forecasts_public.json.gz'):
        current_forward_path = root / current_forward_name
        if not current_forward_path.exists(): continue
        from forward_forecasts_public import apply_public as apply_forward
        forward, forward_hash = read_json(current_forward_path)
        apply_forward(result, forward)
        result['source_payload_sha256'][current_forward_name.removesuffix('.json.gz')] = forward_hash
    encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    template = (root / 'season_comparison.template.html').read_text()
    packed = base64.b64encode(gzip.compress(encoded, mtime=0)).decode()
    rendered = template.replace('__NBA_DATA_GZIP_BASE64__', packed)
    if '__NBA_DATA_' in rendered: raise ValueError('Unreplaced data placeholder')
    downloadable = json.dumps(download_projection(result), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return downloadable + b'\n', rendered.encode()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    raw, html = build()
    pairs = [(ROOT / 'season_comparison.json.gz', gzip.compress(raw, mtime=0)), (ROOT / 'season_comparison.html', html)]
    if args.check:
        for path, body in pairs:
            if path.read_bytes() != body: raise SystemExit(f'Generated file differs: {path.name}')
        print('NBA season comparison: deterministic generation verified')
    else:
        for path, body in pairs: path.write_bytes(body)
        print('NBA season comparison: observed schedule and saved analytical evidence projected')

if __name__ == '__main__': main()
