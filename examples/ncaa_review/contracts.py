"""Credential-free information-time and paired-evaluation demonstration.

All examples are invented. This is generic public engineering code, not the
private NCAA feature pipeline or a recreation of its fitted models.
Python 3.11+, standard library only. No network or wagering operations.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
PROVIDERS = ('Kalshi', 'Polymarket', 'DraftKings')
SETTLEMENT = 'full_game_including_overtime'
EPS = 1e-15

def clock(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be an explicit string')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('naive timestamp')
    return stamp.astimezone(timezone.utc)

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (not math.isfinite(value)):
        raise ValueError('finite numeric value required')
    return float(value)

def win_metrics(actual, predicted):
    if not actual or len(actual) != len(predicted):
        raise ValueError('nonempty equal-length scoring cohort required')
    y = [number(v) for v in actual]
    p = [number(v) for v in predicted]
    if any((v not in (0, 1) for v in y)) or any((not 0 <= v <= 1 for v in p)):
        raise ValueError('binary outcome and probability required')
    n = len(y)
    bins = []
    for b in range(10):
        selected = [(a, q) for a, q in zip(y, p) if min(9, int(q * 10)) == b]
        if selected:
            bins.append({'bin': b, 'N': len(selected), 'mean_probability': sum((q for a, q in selected)) / len(selected), 'observed_rate': sum((a for a, q in selected)) / len(selected)})
    positives = sum(y)
    negatives = n - positives
    auc = None
    if positives and negatives:
        ordered = sorted(zip(p, y))
        rank_sum = 0.0
        i = 0
        while i < n:
            j = i + 1
            while j < n and ordered[j][0] == ordered[i][0]:
                j += 1
            rank = (i + 1 + j) / 2
            rank_sum += rank * sum((a for q, a in ordered[i:j]))
            i = j
        auc = (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
    return {'N': n, 'LogLoss': sum((-a * math.log(min(1 - EPS, max(EPS, q))) - (1 - a) * math.log(1 - min(1 - EPS, max(EPS, q))) for a, q in zip(y, p))) / n, 'Brier': sum(((q - a) ** 2 for a, q in zip(y, p))) / n, 'Accuracy': sum((0.5 if q == 0.5 else float((q > 0.5) == bool(a)) for a, q in zip(y, p))) / n, 'CalibrationBias': sum((q - a for a, q in zip(y, p))) / n, 'ECE10': sum((b['N'] * abs(b['mean_probability'] - b['observed_rate']) for b in bins)) / n, 'ROC_AUC': auc, 'probability_ties': sum((q == 0.5 for q in p)), 'calibration_bins': bins}

def point_metrics(actual, predicted, target, lines=None):
    if target not in ('margin', 'total') or not actual or len(actual) != len(predicted):
        raise ValueError('point cohort or target')
    y = [number(v) for v in actual]
    p = [number(v) for v in predicted]
    if target == 'total' and any((v < 0 for v in y + p)):
        raise ValueError('nonnegative total required')
    errors = [q - a for a, q in zip(y, p)]
    n = len(y)
    result = {'N': n, 'MAE': sum((abs(e) for e in errors)) / n, 'RMSE': math.sqrt(sum((e * e for e in errors)) / n), 'Bias': sum(errors) / n, 'OverUnderAccuracy': None}
    if target == 'margin':
        result['DirectionAccuracy'] = sum((0.5 if q == 0 else float((q > 0) == (a > 0)) for a, q in zip(y, p))) / n
    if target == 'total' and lines is not None:
        if len(lines) != n:
            raise ValueError('same line population required')
        lines = [number(v) for v in lines]
        eligible = [(a, q, line) for a, q, line in zip(y, p, lines) if a != line and q != line]
        result.update(OverUnderAccuracy=sum(((q > line) == (a > line) for a, q, line in eligible)) / len(eligible) if eligible else None, OverUnderN=len(eligible), actual_pushes=sum((a == line for a, line in zip(y, lines))), prediction_abstentions=sum((q == line for q, line in zip(p, lines))))
    return result

def identity(row):
    required = ('league', 'event_id', 'home_id', 'away_id', 'event_time', 'cutoff_time', 'target', 'settlement')
    if any((not isinstance(row.get(k), str) or not row[k] for k in required)):
        raise ValueError('complete canonical identity required')
    if row['league'] not in ('ncaam', 'ncaaw') or row['home_id'] == row['away_id']:
        raise ValueError('league or ordered team identity')
    if row['target'] not in ('win', 'margin', 'total') or row['settlement'] != SETTLEMENT:
        raise ValueError('incompatible product or settlement')
    event, cutoff = (clock(row['event_time']), clock(row['cutoff_time']))
    if not timedelta(hours=1) <= event - cutoff <= timedelta(hours=2):
        raise ValueError('one-to-two-hour prediction horizon required')
    return tuple((clock(row[k]).isoformat() if k in ('event_time', 'cutoff_time') else row[k] for k in required))

def validate_prediction(row):
    key = identity(row)
    cutoff = clock(row['cutoff_time'])
    value = number(row['prediction'])
    if row['target'] == 'win' and (not 0 <= value <= 1):
        raise ValueError('invalid probability')
    if row['target'] == 'total' and value < 0:
        raise ValueError('invalid total')
    if not row.get('model_version'):
        raise ValueError('immutable model version required')
    for name in ('feature_available_at', 'training_label_max'):
        if clock(row[name]) >= cutoff:
            raise ValueError(name + ' must precede cutoff')
    track = row.get('track')
    if track not in ('frozen_original', 'rolling_reconstructed', 'issued_prospective'):
        raise ValueError('explicit evaluation track required')
    if track == 'issued_prospective':
        issued = clock(row['issued_at'])
        if issued > cutoff or not timedelta(hours=1) <= clock(row['event_time']) - issued <= timedelta(hours=2):
            raise ValueError('late or early issue cannot claim final-hour provenance')
        if clock(row['model_created_at']) > issued or clock(row['feature_available_at']) > issued:
            raise ValueError('unavailable model or features at issue')
        if clock(row['training_label_max']) >= clock(row['model_created_at']):
            raise ValueError('model cannot precede its training label release')
    else:
        if row.get('issued_at') is not None:
            raise ValueError('reconstruction cannot manufacture an issue')
        clock(row['reconstruction_at'])
    return key

def validate_quote(quote):
    key = identity(quote)
    if quote.get('provider') not in PROVIDERS:
        raise ValueError('provider outside declared comparison scope')
    if quote.get('historical_availability_verified') is not True:
        raise ValueError('quote availability not verified')
    if clock(quote['available_at']) > clock(quote['cutoff_time']):
        raise ValueError('quote arrived after cutoff')
    value = number(quote['prediction'])
    if quote['target'] == 'win' and (not 0 <= value <= 1):
        raise ValueError('invalid quote probability')
    return key

def score_paired(predictions, quotes, *, evaluated_at):
    """Score each provider and model on exactly that provider's shared cohort."""
    evaluated = clock(evaluated_at)
    models = {}
    by_provider = {p: {} for p in PROVIDERS}
    rejected = []
    if len({r.get('track') for r in predictions}) > 1:
        raise ValueError('evaluation tracks must remain separate')
    for row in predictions:
        key = validate_prediction(row)
        if key in models:
            raise ValueError('duplicate model game')
        if row.get('actual') is None or row.get('label_available_at') is None:
            continue
        if clock(row['label_available_at']) > evaluated:
            continue
        if clock(row['label_available_at']) <= clock(row['event_time']):
            raise ValueError('outcome released before event')
        models[key] = row
    for row in quotes:
        if row.get('provider') not in PROVIDERS:
            raise ValueError('provider outside declared comparison scope')
        try:
            key = validate_quote(row)
        except ValueError as exc:
            rejected.append({'provider': row['provider'], 'event_id': row.get('event_id'), 'reason': str(exc)})
            continue
        if key in by_provider[row['provider']]:
            raise ValueError('duplicate provider game')
        model = models.get(key)
        if model and model['track'] == 'issued_prospective' and (clock(row['available_at']) > clock(model['issued_at'])):
            rejected.append({'provider': row['provider'], 'event_id': row['event_id'], 'reason': 'quote arrived after model issue'})
            continue
        by_provider[row['provider']][key] = row
    panels = []
    for provider, available in by_provider.items():
        keys = sorted(models.keys() & available.keys())
        for league, target in ((league, target) for league in ('ncaam', 'ncaaw') for target in ('win', 'margin', 'total')):
            group = [k for k in keys if models[k]['target'] == target and models[k]['league'] == league]
            if not group:
                continue
            y = [models[k]['actual'] for k in group]
            a = [models[k]['prediction'] for k in group]
            b = [available[k]['prediction'] for k in group]
            scorer = win_metrics if target == 'win' else lambda y, p: point_metrics(y, p, target)
            disagreements = []
            if target == 'win':
                for k, truth, model, reference in zip(group, y, a, b):
                    if model == 0.5 or reference == 0.5 or (model > 0.5) == (reference > 0.5):
                        continue
                    disagreements.append({'event_id': models[k]['event_id'], 'model_correct': (model > 0.5) == bool(truth), 'provider_correct': (reference > 0.5) == bool(truth)})
            panels.append({'provider': provider, 'league': league, 'target': target, 'model': scorer(y, a), 'reference': scorer(y, b), 'paired_events': [models[k]['event_id'] for k in group], 'cohort_sha256': hashlib.sha256(json.dumps(group, separators=(',', ':')).encode()).hexdigest(), 'disagreements': disagreements, 'demonstrated_profit': None})
    return {'panels': panels, 'rejected_quotes': rejected, 'unmatched_by_provider': {p: len(set(models) - set(q)) for p, q in by_provider.items()}, 'orders': 0}

def toy_fit(history, origin, league):
    """An intentionally simple three-intercept baseline on invented history."""
    boundary = clock(origin)
    admitted = []
    for row in history:
        if row['league'] != league:
            continue
        if clock(row['label_available_at']) >= boundary:
            continue
        if clock(row['event_time']) >= clock(row['label_available_at']):
            raise ValueError('invalid label order')
        if clock(row['feature_available_at']) >= clock(row['cutoff_time']):
            raise ValueError('invalid training feature clock')
        for field in ('win', 'margin', 'total'):
            number(row[field])
        if row['win'] not in (0, 1) or row['win'] != int(row['margin'] > 0):
            raise ValueError('inconsistent synthetic outcome')
        admitted.append(row)
    if not admitted:
        raise ValueError('no released history')
    n = len(admitted)
    return {'win': (1 + sum((r['win'] for r in admitted))) / (n + 2), 'margin': sum((r['margin'] for r in admitted)) / n, 'total': sum((r['total'] for r in admitted)) / n, 'training_rows': n, 'training_label_max': max((r['label_available_at'] for r in admitted), key=clock), 'fixture_only': True, 'owner_fit_credit': 0}

def hypothetical_win_decision(probability, quote, actual=None):
    """A declared toy one-unit policy, not a provider fee calculator or order."""
    p = number(probability)
    if not 0 <= p <= 1:
        raise ValueError('invalid probability')
    if quote.get('provider') not in PROVIDERS:
        raise ValueError('undeclared provider')
    if quote.get('target') != 'win' or quote.get('executable') is not True or quote.get('fee_verified') is not True:
        return {'selection': 'NO BET', 'reason': 'executable winner quote and fee evidence required', 'orders': 0}
    validate_quote(quote)
    choices = []
    for side, prob in [('home', p), ('away', 1 - p)]:
        fee = number(quote.get(side + '_fee_per_unit'))
        if fee < 0:
            raise ValueError('negative fee')
        if quote.get('price_type') == 'decimal':
            price = number(quote.get(side + '_decimal'))
            if price <= 1:
                raise ValueError('invalid decimal price')
            ev = prob * price - 1 - fee
            win_net = price - 1 - fee
            lose_net = -1 - fee
            cost = 1 + fee
        elif quote.get('price_type') == 'binary_contract':
            price = number(quote.get(side + '_ask'))
            if not 0 < price < 1:
                raise ValueError('invalid executable ask')
            ev = prob - price - fee
            win_net = 1 - price - fee
            lose_net = -price - fee
            cost = price + fee
        else:
            return {'selection': 'NO BET', 'reason': 'unsupported price semantics', 'orders': 0}
        choices.append((ev, side, win_net, lose_net, cost))
    chosen = max(choices, key=lambda c: (c[0], c[1] == 'home'))
    if chosen[0] <= 0:
        return {'selection': 'NO BET', 'reason': 'no strictly positive expected net value', 'orders': 0}
    ev, side, win_net, lose_net, cost = chosen
    profit = None
    if actual is not None:
        truth = number(actual)
        if truth not in (0, 1):
            raise ValueError('binary settled outcome required')
        profit = win_net if (side == 'home') == bool(truth) else lose_net
    return {'selection': side, 'expected_value_per_unit': ev, 'hypothetical_profit': profit, 'hypothetical_return_on_cash': None if profit is None else profit / cost, 'cash_at_risk': cost, 'fee_scope': 'invented explicit fixture fees, not any provider actual tariff', 'orders': 0}

def verified_read(stream, expected, *, maximum=16 << 20, chunk_size=65536):
    """A wrapper is read directly; context entry may return a different object."""
    h = hashlib.sha256()
    parts = []
    n = 0
    try:
        if type(expected.get('bytes')) is not int or not 0 <= expected['bytes'] <= maximum:
            raise ValueError('bounded integer byte pin required')
        while True:
            block = stream.read(chunk_size)
            if not isinstance(block, bytes):
                raise ValueError('binary reader required')
            if not block:
                break
            n += len(block)
            if n > maximum:
                raise ValueError('stream exceeded bound')
            h.update(block)
            parts.append(block)
        if {'bytes': n, 'sha256': h.hexdigest()} != expected:
            raise ValueError('full byte pin mismatch')
        return b''.join(parts)
    finally:
        stream.close()

def demo():
    start = datetime(2026, 1, 1, 18, tzinfo=timezone.utc)
    history = []
    for i in range(40):
        event = start + timedelta(days=i)
        margin = 8 if i % 5 in (0, 1, 2) else -6
        history.append({'league': 'ncaam', 'event_time': event.isoformat(), 'cutoff_time': (event - timedelta(hours=2)).isoformat(), 'feature_available_at': (event - timedelta(days=2)).isoformat(), 'label_available_at': (event + timedelta(hours=24)).isoformat(), 'win': int(margin > 0), 'margin': margin, 'total': 140 + i % 7})
    origin = (start + timedelta(days=45)).isoformat()
    fit = toy_fit(history, origin, 'ncaam')
    predictions = []
    quotes = []
    for i in range(8):
        event = start + timedelta(days=46 + i)
        cutoff = event - timedelta(hours=2)
        actual_margin = [8, -4, 12, 3, -9, 6, -2, 9][i]
        actual_total = 145 + i
        for target, actual in [('win', int(actual_margin > 0)), ('margin', actual_margin), ('total', actual_total)]:
            row = {'league': 'ncaam', 'event_id': 'invented-game-' + str(i), 'home_id': 'invented-home-' + str(i), 'away_id': 'invented-away-' + str(i), 'event_time': event.isoformat(), 'cutoff_time': cutoff.isoformat(), 'target': target, 'settlement': SETTLEMENT, 'prediction': fit[target], 'actual': actual, 'feature_available_at': (cutoff - timedelta(days=2)).isoformat(), 'training_label_max': fit['training_label_max'], 'model_version': 'invented-three-intercept-v1', 'track': 'rolling_reconstructed', 'issued_at': None, 'reconstruction_at': '2026-03-20T12:00:00+00:00', 'label_available_at': (event + timedelta(hours=24)).isoformat()}
            predictions.append(row)
            for j, provider in enumerate(PROVIDERS):
                if i == 7 and provider == 'DraftKings':
                    continue
                ref = 0.55 + 0.03 * j + 0.08 * ((i + j) % 2) if target == 'win' else 4 + j if target == 'margin' else 144 + j
                q = {k: row[k] for k in ('league', 'event_id', 'home_id', 'away_id', 'event_time', 'cutoff_time', 'target', 'settlement')}
                q.update(provider=provider, prediction=ref, available_at=(cutoff - timedelta(minutes=5)).isoformat(), historical_availability_verified=True, fixture_only=True)
                quotes.append(q)
    comparison = score_paired(predictions, quotes, evaluated_at='2026-03-20T12:00:00+00:00')
    winner = next((q for q in quotes if q['provider'] == 'DraftKings' and q['target'] == 'win'))
    winner.update(executable=True, fee_verified=True, price_type='decimal', home_decimal=1.9, away_decimal=2.0, home_fee_per_unit=0.0, away_fee_per_unit=0.0)
    bet = hypothetical_win_decision(fit['win'], winner, 1)
    return {'schema': 'sports-edge-lab.invented.ncaa-contract-demo.v1', 'fixture_only': True, 'real_sports_performance_claimed': False, 'fit': fit, 'paired_comparison': comparison, 'toy_policy_example': bet, 'orders': 0, 'owner_fit_credit': 0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    body = json.dumps(demo(), sort_keys=True, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body)
    print(body, end='')
if __name__ == '__main__':
    main()
