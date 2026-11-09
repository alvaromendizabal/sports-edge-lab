"""Current dated public counts and evidence classes; no active scientific recipe."""
OWNER = set('cycle status started_at finished_at first_error_at native_states meta_states issue_rows aggregate_fit_total aggregate_issue_total actual_V5_fits actual_V5_issues monitor_evaluations monitor_supported_pointer_repair_rows monitor_conditional_identity_rows monitor_other_unsupported_rows monitor_not_final_rows independent_terminal_stdout_available'.split())

def validate_n061(data, only, instant):
    owner = data['n061_owner_status']
    only(owner, OWNER, 'actual N060 owner status')
    if set(owner) != OWNER or owner['cycle'] != 'N060' or owner['status'] != 'PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED':
        raise ValueError('Actual N060 partial status must remain exact')
    if (owner['native_states'], owner['meta_states'], owner['issue_rows']) != (27, 0, 2294):
        raise ValueError('Exact N060 physical partials')
    if owner['aggregate_fit_total'] is not None or owner['aggregate_issue_total'] is not None:
        raise ValueError('Original aggregate nulls may not be repaired in presentation')
    if any(owner[key] for key in ('actual_V5_fits','actual_V5_issues','monitor_evaluations','independent_terminal_stdout_available')):
        raise ValueError('Unsupported V5, scoring or terminal evidence credit')
    if tuple(owner[key] for key in ('monitor_supported_pointer_repair_rows','monitor_conditional_identity_rows','monitor_other_unsupported_rows','monitor_not_final_rows')) != (345,108,13,4620):
        raise ValueError('Supported monitor failures and unsupported conditions must stay separate')
    if not instant(owner['started_at']) < instant(owner['first_error_at']) <= instant(owner['finished_at']):
        raise ValueError('Actual owner error chronology')
    counts = data['counts']
    if tuple(counts[key] for key in ('private_model_roles','private_model_cells','private_provider_cells','provider_horizons','season_metric_rows','actual_latest_issue_rows')) != (141,115056,53856,22,1289,2294):
        raise ValueError('New dated inventory counts')
    snapshot = data['snapshot']
    if tuple(snapshot[key] for key in ('completed','decisive','ties','remaining','in_progress','halftime','scheduled')) != (134,133,1,138,1,0,137):
        raise ValueError('Exact actual N060 schedule snapshot')
    capabilities = data['provider_capabilities']
    if len(capabilities) != 5 or {row['provider'] for row in capabilities} != {'DraftKings','Kalshi','Polymarket','PrizePicks','Underdog'}:
        raise ValueError('All five provider capabilities must be accounted for')
    for row in capabilities:
        only(row, {'provider','status','scope','reason'}, 'provider capability')
        if row['provider'] in {'PrizePicks','Underdog'} and row['status'] != 'NO_ADMITTED_COMPARABLE_GAME_LEVEL_SOURCE_IN_THIS_RETURN':
            raise ValueError('No invented comparable provider product')
        if not row['reason']:
            raise ValueError('Explicit provider support reason')
    return data
