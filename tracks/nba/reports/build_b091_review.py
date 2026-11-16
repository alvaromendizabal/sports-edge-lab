"""Build a standalone NBA aggregate review without any provider or model access."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FORBIDDEN_KEYS = {'recipe_id', 'feature_names', 'feature_values', 'feature_columns',
    'calibration_parameters', 'model_weights', 'weights', 'raw_payload', 'raw_record',
    'credentials', 'access_token', 'account_id', 'source_path', 'private_path',
    'player_id', 'event_id', 'game_id', 'predictions', 'prediction_rows'}

def validate(value):
    def visit(node):
        if isinstance(node, dict):
            if FORBIDDEN_KEYS.intersection(node): raise ValueError('Private payload field')
            for key, child in node.items():
                if key == 'model_id' and not re.fullmatch(r'NBA-C\d{3}', child):
                    raise ValueError('Model identity must be a public alias')
                visit(child)
        elif isinstance(node, list):
            for child in node: visit(child)
        elif isinstance(node, str):
            if any(token in node.lower() for token in ('circa', 's3://', 'arn:aws:',
                    '/home/', '/workspace/', 'nba:espn:event:', 'aws_access_key')):
                raise ValueError('Private or wrong-sport payload content')
        elif isinstance(node, float) and not math.isfinite(node):
            raise ValueError('Nonfinite metric')
    visit(value)
    if value['schema'] != 'sports_edge_lab.nba.b091.champion_review_public.v1':
        raise ValueError('Unexpected review schema')
    if value['final_champions_selected'] is not False or value['automatic_promotions'] != 0:
        raise ValueError('Unsupported promotion claim')
    if value['strict_current_full_cells'] != 0: raise ValueError('Unsupported strict current score')
    populations=value['populations']
    if [(p['season'], p.get('regular_games'), p.get('postseason_games')) for p in populations[:2]] != [
            ('2024-25',1230,84),('2025-26',1230,85)]:
        raise ValueError('Validation population changed')
    current=populations[2]
    if current['regular_completed_games'] != 197 or current['postseason_completed_games'] != 0:
        raise ValueError('Frozen current population changed')
    models={m['model_id']:m for m in value['models']}
    if len(models) != len(value['models']): raise ValueError('Duplicate model alias')
    if len(value['roles']) != 28: raise ValueError('Incomplete objective role inventory')
    for role in value['roles']:
        if any(k not in models for k in role['leader_model_ids']): raise ValueError('Unknown leader alias')
        low, high=role['paired_95pct_improvement_interval']
        if not low <= 0 <= high: raise ValueError('Uncertainty narrative changed')
        eligible=[m for m in models.values() if (m['phase'],m['objective'],m['horizon_minutes']) ==
            (role['phase'],role['objective'],role['horizon_minutes'])]
        metric=role['metric']; scores=[m['pooled_validation_metrics'][metric] for m in eligible]
        best=max(scores) if metric=='accuracy' else min(scores)
        if any(abs(models[k]['pooled_validation_metrics'][metric]-best)>1e-12 for k in role['leader_model_ids']):
            raise ValueError('Leader is not validation-leading')
    if len(value['current_descriptive_cells']) != value['current_descriptive_cell_count']:
        raise ValueError('Current cell count mismatch')
    for cell in value['current_descriptive_cells']:
        if (cell['required_games']!=197 or cell['metrics']['games']!=197 or
            cell['population_sha256'] != current['regular_population_sha256'] or
            cell['same_full_membership_verified'] is not True):
            raise ValueError('Current population differs across models')
        if (cell['original_issued_claim'] is not False or cell['promotion_eligible'] is not False or
            cell['strict_point_in_time_metrics'] is not None):
            raise ValueError('Reconstruction promoted to original evidence')
    if value['source_policy']['comparison_only_providers'] != ['DraftKings','Kalshi','Polymarket']:
        raise ValueError('Comparison-only source policy changed')
    return value

def build(root=ROOT):
    value=validate(json.loads((root/'B091_CHAMPION_AUDIT_PUBLIC.json').read_text()))
    raw=json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':')).replace('<','\\u003c')
    template=(root/'b091_review.template.html').read_text()
    if template.count('__B091_PUBLIC_JSON__')!=1: raise ValueError('Missing unique payload slot')
    return template.replace('__B091_PUBLIC_JSON__',raw).encode()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    raw=build();path=ROOT/'b091_review.html'
    if args.check:
        if path.read_bytes()!=raw: raise SystemExit('B091 review differs from its aggregate source/template')
        print('B091 deterministic review and public evidence validated')
    else:
        path.write_bytes(raw);print('B091 standalone aggregate review built')

if __name__=='__main__': main()
