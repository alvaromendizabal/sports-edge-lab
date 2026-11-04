"""Public, provider-independent time selection; no model or source credentials.

An old observation recovered today may be used in a labelled retrospective
comparison. It cannot be represented as information possessed before an earlier
forecast. These are two different questions and two explicit functions.
"""
from datetime import datetime, timezone
from math import isfinite


def instant(value):
    if not isinstance(value, str):
        raise ValueError('An explicit timestamp is required')
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Timestamp needs a timezone')
    return value.astimezone(timezone.utc)


def reference_at(observations, target, cutoff, *, strict_before=False):
    """Latest *stored* event-time observation, not a claim of feed completeness.

    A timestamped public historical observation may be recovered after cutoff.
    Equal-time conflicts are rejected rather than settled by file order.
    Missing and incompatible products never turn into numeric zeros.
    """
    end = instant(cutoff)
    eligible = []
    for row in observations:
        if row.get('target') != target or row.get('join_status') != 'matched':
            continue
        value = row.get('value')
        if value is None or not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
            continue
        # An authenticated captured snapshot proves availability at capture,
        # without fabricating an individual exchange quote timestamp.
        value_clock = row.get('quote_at') or row.get('captured_at')
        if not value_clock:
            continue
        clock = instant(value_clock)
        # Candle timestamps denote a bucket start in some provider APIs.
        # A bucket that crosses the decision boundary is not eligible.
        interval_end = instant(row.get('interval_end_at') or value_clock)
        if interval_end > end or (strict_before and interval_end == end):
            continue
        if clock < end or (not strict_before and clock == end):
            eligible.append((clock, row))
    if not eligible:
        return None
    # Timestamped historical observations have the stronger source-time
    # meaning. Early captured snapshots are a fallback, never a latest-tick
    # or genuinely issued-forecast claim.
    timestamped = [(clock,row) for clock,row in eligible if row.get('quote_at')]
    eligible = timestamped or eligible
    latest = max(clock for clock, _ in eligible)
    candidates = [row for clock, row in eligible if clock == latest]
    signatures = {(row['value'], row.get('reference_kind'), row.get('product')) for row in candidates}
    if len(signatures) != 1:
        raise ValueError('Conflicting observations at the same source clock')
    return min(candidates, key=lambda row: (row.get('captured_at') or '', row.get('evidence_kind') or ''))


def known_before_prediction(row, cutoff):
    """Clock-only possession test, not feature-value or forecast admission.

    The caller must separately authenticate the observation and verify the
    numeric feature path, identities, teachers and causal dependencies.
    """
    if row is None or not row.get('captured_at'):
        return False
    end = instant(cutoff)
    observed = row.get('quote_at') or row['captured_at']
    return (instant(observed) <= end
            and instant(row.get('interval_end_at') or observed) <= end
            and instant(row['captured_at']) <= end)


def preserve_inventory(games, observations):
    """Left-join every observed game, retaining absent providers explicitly."""
    ids = [str(row['id']) for row in games]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate game identity')
    grouped = {identity: [] for identity in ids}
    unmatched = []
    for row in observations:
        identity = str(row.get('game_id', ''))
        (grouped[identity] if identity in grouped else unmatched).append(row)
    return [{'game': row, 'observations': grouped[str(row['id'])]} for row in games], unmatched
