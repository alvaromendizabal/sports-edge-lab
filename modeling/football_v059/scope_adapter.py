"""Local pinned-data integration; no acquisition, fitting, or silent relabeling."""
import json
import pathlib

import pandas as pd

from common import require
from fbs_repair import TARGET_GAME_IDS, prepare_fbs_scope, repair_targeted_games, verify_local_inputs


def prepare_loaded_inputs(frame, canonical, queue, links, raw_by_season, sources,
                          target_game_ids=TARGET_GAME_IDS):
    target, context, scope_audit = prepare_fbs_scope(canonical, frame)
    require(set(frame.track) <= {'nfl', 'ncaaf'}, 'DATA', 'Unexpected modeling track')
    keep = frame.track.eq('nfl') | (frame.track.eq('ncaaf') & frame.home_fbs.eq(1) & frame.away_fbs.eq(1))
    model_frame = frame.loc[keep].copy().reset_index(drop=True)
    # No mutation of any existing feature, target, or source-time field.
    pd.testing.assert_frame_equal(model_frame, frame.loc[keep].reset_index(drop=True))
    require(int(model_frame.track.eq('nfl').sum()) == int(frame.track.eq('nfl').sum()),
            'DATA', 'NFL rows dropped by college scope filtering')
    selected_canonical = canonical.loc[canonical.track.eq('nfl') |
        (canonical.track.eq('ncaaf') & canonical.home_fbs.eq(1) & canonical.away_fbs.eq(1))].copy().reset_index(drop=True)
    require(set(zip(model_frame.track, model_frame.game_id)) ==
            set(zip(selected_canonical.track, selected_canonical.game_id)),
            'DATA', 'Canonical/model target identities disagree')
    repairs = repair_targeted_games(canonical, queue, links, raw_by_season, sources,
                                    target_game_ids=target_game_ids)
    scope_audit.update(dict(input_model_rows=len(frame), scoped_model_rows=len(model_frame),
        excluded_context_model_rows=int((~keep).sum()), nfl_rows_preserved=int(model_frame.track.eq('nfl').sum()),
        target_labels_replaced=False, repaired_aggregates_inserted_into_model_features=False,
        canonical_final_updates_require_matched_baseline_cohort=True))
    return dict(frame=model_frame, model_frame=model_frame, canonical_games=selected_canonical,
        fbs_history_context=context, scope_audit=scope_audit, repair_outputs=repairs,
        regulation_efficiency_additions=repairs['features'],
        new_canonical_finals=scope_audit['newly_completed_since_frozen'])


def prepare_inputs(cache, frame, pins=None):
    """Consume exactly the declared eleven local cached inputs.

    The public distribution requires explicit caller-supplied pins. No private
    owner pin manifest is packaged or inferred.
    A pin list from a local-development manifest may contain local_path metadata;
    it is never used to read outside the supplied runtime cache directory.
    """
    require(pins is not None, 'SOURCE_STATE',
            'Public core requires explicit local input pins; owner configuration is not distributed')
    verify_local_inputs(cache, pins)
    cache = pathlib.Path(cache)
    by_name = {p['name']: p for p in pins}
    required = {'canonical_games_current.parquet', 'remaining_recovery_queue.json',
                'identity_gap_links.json', 'college_quarantine.json'}
    require(required <= set(by_name), 'SOURCE_STATE', 'Required repair evidence pin missing')
    assets = [p for p in pins if p.get('kind') == 'ncaa_mfb_drives']
    require(len(assets) == 7 and len(pins) == 11, 'SOURCE_STATE', 'Unexpected repair source scope')
    sources = {int(p['season']): p for p in assets}
    require(len(sources) == len(assets), 'SOURCE_STATE', 'Duplicate raw repair season')
    canonical = pd.read_parquet(cache / 'canonical_games_current.parquet')
    queue = json.loads((cache / 'remaining_recovery_queue.json').read_text())
    links = json.loads((cache / 'identity_gap_links.json').read_text())
    raw = {y: pd.read_parquet(cache / p['name']) for y, p in sources.items()}
    out = prepare_loaded_inputs(frame, canonical, queue, links, raw, sources)
    out['college_quarantine'] = json.loads((cache / 'college_quarantine.json').read_text())
    out['verified_input_receipts'] = [{k:p[k] for k in ('name', 'key', 'bytes', 'sha256')} for p in pins]
    return out
