"""Sanitized failed-owner evidence, separate from preserved scientific data."""
import base64
import hashlib
import html
import json
from pathlib import Path

SOURCE = '2026-11-13-n086-failed-n087-review.json'
ROOT = Path(__file__).parent


def validate(value, forecast_bytes, aggregate_bytes):
    if value['owner_return_sha256'] != 'de635884fe887278aeebe7d78af27810430ea33721aa0a4512f0a7693b5961cd':
        raise ValueError('FAILED_RETURN_IDENTITY_CHANGED')
    if value['status'] != 'FAILED_FINALIZATION_DIAGNOSTIC':
        raise ValueError('FAILED_STATUS_CHANGED')
    if any(value[key] is not None for key in ('new_fits', 'new_native_fits', 'new_meta_fits', 'new_forecasts')):
        raise ValueError('UNKNOWN_FINAL_COUNTS_CANNOT_BECOME_ZERO')
    if any(value[key] is not False for key in ('owner_research_acceptance', 'full_current_evidence_closure', 'completed_new_scientific_receipt', 'n087_owner_execution_claimed', 'automatic_promotion', 'source_refresh_claimed', 'website_deployment_claimed')):
        raise ValueError('UNSUPPORTED_COMPLETION_CLAIM')
    retained = value['preserved_science']
    for raw, key in ((forecast_bytes, 'selected_forecasts_sha256'), (aggregate_bytes, 'aggregate_sha256')):
        if hashlib.sha256(raw).hexdigest() != retained[key]:
            raise ValueError('PRESERVED_SCIENCE_BYTES_CHANGED')
    return value


def panel():
    raw = (ROOT/SOURCE).read_bytes()
    value = json.loads(raw)
    retained = value['preserved_science']
    validate(value, (ROOT/retained['selected_forecasts_file']).read_bytes(),
             (ROOT/retained['aggregate_file']).read_bytes())
    return '''<!-- N087_FAILED_OWNER_BEGIN -->
<section class="panel" id="latest-execution" aria-labelledby="failed-owner-title">
<h2 id="failed-owner-title">Latest execution: N086 failed before scientific workers launched</h2>
<p class="note"><strong>FAILED_FINALIZATION_DIAGNOSTIC · owner acceptance false.</strong> The actual run lasted ''' + f"{value['elapsed_seconds']:.3f}" + ''' seconds. Three current-science stages were rejected by an invalid active-attempt path guard. Finalization then attempted to change an immutable summary.</p>
<p><strong>New fit and forecast totals: unknown (unreconciled).</strong> The diagnostic observed 0 optimizer callbacks and 0 commits; no completed new scientific receipt is available. Unknown final counts are not verified zero totals. The registered 27 candidates / maximum 81 frozen fits remain pending.</p>
<p>Measured process CPU: <strong>''' + f"{value['mean_cpu_core_equivalents']:.3f}" + ''' mean / ''' + f"{value['peak_cpu_core_equivalents']:.3f}" + ''' peak core equivalents</strong>; 15 paid calls. This is a failed execution, not twelve-core performance evidence or a speedup.</p>
<p>Source cache: 456 hits, 320,114,459 reused bytes, 2 source GETs / 3,488 bytes. Separate publication/readback accounting reports 1,367 full readbacks / 115,919,486 bytes. The two source GETs are not total remote traffic. Prior N085 custody used zero remote GETs.</p>
<p>The bounded diagnostic has four unresolved current artifacts. Its summary reports 59 log flushes, but the physical live log streams are absent from this return; the older execution log is present, but continuity of the required live pair cannot be verified. Full current evidence closure is false.</p>
<p><strong>All forecast and metric panels below retain the last valid N085 source cutoff: ''' + html.escape(retained['display_cutoff_utc']) + '''.</strong> The 272 games, 444 selected outputs and 1,530 historical cards retain their existing values and issue clocks. Reusing 579 original-issue evaluations adds zero new score computations. No new schedule, forecast, market refresh or champion promotion is claimed.</p>
<p>N087 is a repair of the owner call sequence and failure finalization; no N087 owner result is claimed. Earlier test and browser passes missed these production call paths and do not establish owner-run success. <a href="data:application/json;base64,''' + base64.b64encode(raw).decode('ascii') + '''" download="''' + SOURCE + '''">Download exact sanitized failure evidence</a>. Source publication is separate from website deployment.</p>
</section>
<!-- N087_FAILED_OWNER_END -->'''
