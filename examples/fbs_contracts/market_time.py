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


def reference_signature(row):
    """Recognize only explicitly equivalent sportsbook labels on value/time ties."""
    target=row.get('target');kind=row.get('reference_kind');product=row.get('product')
    products={'winner':{'SPORTSBOOK_WINNER_H2H_DEVIGGED','sportsbook_winner','sportsbook_game_market'},
              'margin':{'SPORTSBOOK_HOME_MARGIN_LINE','sportsbook_home_margin_line','sportsbook_game_market'},
              'total':{'SPORTSBOOK_TOTAL_LINE','sportsbook_total_line','sportsbook_game_market'}}
    kinds={'winner':{'archived_devigged_probability','captured_devigged_probability','vig_removed_two_way_probability'},
           'margin':{'archived_line','captured_line','sportsbook_point_line'},
           'total':{'archived_line','captured_line','sportsbook_point_line'}}
    if product in products.get(target,set()) and kind in kinds.get(target,set()):
        return row['value'],row.get('picked_home'),'equivalent_sportsbook_'+target
    return row['value'],kind,product


def reference_at(observations, target, cutoff, *, strict_before=False, registered_cutoff_kind=None):
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
        if row.get('registered_cutoff_kind') and row['registered_cutoff_kind']!=registered_cutoff_kind:
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
    signatures = {reference_signature(row) for row in candidates}
    if len(signatures) != 1:
        raise ValueError('Conflicting observations at the same source clock')
    return min(candidates, key=lambda row: (not bool(row.get('captured_at')), row.get('captured_at') or '', row.get('evidence_kind') or ''))


def availability_reference_at(observations, target, cutoff, *, strict_before=False,
                              registered_cutoff_kind=None, assessed_at=None,
                              max_observations=100000):
    """Latest supported observation clock, without preferring older source time.

    This is a separate descriptive display selector. Existing ``reference_at``
    and its benchmark cohorts are unchanged. A provider-timestamped historical
    observation may have been recovered after kickoff: its source quote and
    complete interval must qualify before the chosen boundary, but its later
    retrieval clock is retained, not backdated. A capture-only record qualifies
    using that actual capture time; a postgame capture cannot reconstruct an
    earlier price. If supplied, ``assessed_at`` excludes observations/captures
    not yet available in that report snapshot.

    The caller must authenticate raw values, identities and clocks separately.
    This function proves neither feed completeness, possession before a past
    forecast, an executable offer, nor model/feature admission. Use the distinct
    ``known_before_prediction`` clock test when historical possession matters.
    Pass ``strict_before=True`` for latest strictly pre-kickoff displays.

    Conflicting latest-clock values or non-equivalent products raise ValueError
    instead of selecting by file order. An exceeded scan bound also raises;
    no partial-inventory result is returned. All input rows remain untouched.
    """
    if type(max_observations) is not int or not 1 <= max_observations <= 1000000:
        raise ValueError('Invalid bounded availability observation limit')
    end = instant(cutoff)
    assessed = instant(assessed_at) if assessed_at is not None else None
    latest, candidates = None, []
    for count, row in enumerate(observations, 1):
        if count > max_observations:
            raise ValueError('Availability observation bound exceeded; no partial selection')
        if row.get('target') != target or row.get('join_status') != 'matched':
            continue
        if row.get('registered_cutoff_kind') and row['registered_cutoff_kind'] != registered_cutoff_kind:
            continue
        value = row.get('value')
        if value is None or not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
            continue
        value_clock = row.get('quote_at') or row.get('captured_at')
        if not value_clock:
            continue
        observed = instant(value_clock)
        interval_end = instant(row.get('interval_end_at') or value_clock)
        if interval_end < observed:
            raise ValueError('Invalid availability observation interval')
        if observed > end or interval_end > end or (strict_before and (observed == end or interval_end == end)):
            continue
        captured = instant(row['captured_at']) if row.get('captured_at') else None
        if assessed is not None and (observed > assessed or interval_end > assessed or captured is not None and captured > assessed):
            continue
        if latest is None or observed > latest:
            latest, candidates = observed, [row]
        elif observed == latest:
            candidates.append(row)
    if not candidates:
        return None
    # Ordered home-team identity cannot silently change when numeric values
    # coincide. Equivalent sportsbook aliases remain equivalent as before.
    signatures = {(reference_signature(row), row.get('picked_home')) for row in candidates}
    if len(signatures) != 1:
        raise ValueError('Conflicting availability observations at the same supported clock')
    return min(candidates, key=lambda row: (not bool(row.get('captured_at')), row.get('captured_at') or '', row.get('evidence_kind') or ''))


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
