"""Current NCAA evidence navigation; older scientific rows remain unchanged."""
from __future__ import annotations

PREVIOUS_BANNER = '<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" style="margin-bottom:28px"><p class="b063-eyebrow" style="margin-top:0">Current dated evidence · V12 / R14 · November 15, 2026 UTC</p><h2 id="v12-current-title">Current models, observed games and market comparison</h2><p>The newer V12 dashboard contains 2,503 observed source games, current frozen-model reconstruction scores, historical metric roles and the exact DraftKings, Kalshi and Polymarket qualification gaps. Complete current-season coverage and a current champion remain unverified.</p><p><strong><a href="v12.html">Open the current V12 comparison dashboard →</a></strong></p><p class="b063-note">The reports and original issues below remain preserved historical evidence. Publishing the dashboard does not refresh data or issue new forecasts.</p></section>'
R15_BANNER = '<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" style="margin-bottom:28px"><p class="b063-eyebrow" style="margin-top:0">Latest execution R15 · Model comparison R14 · November 14, 2026 Pacific</p><h2 id="v12-current-title">Current models, observed games and market comparison</h2><p>The latest R15 execution stopped at a memory-pressure admission deferral during checkpoint authentication, with no new target or calibration fits and no verified reused target fits. The model scores, 2,503 observed games and DraftKings, Kalshi and Polymarket comparisons remain the dated R14 evidence. Complete current-season coverage and a current champion remain unverified.</p><p><strong><a href="v12.html">Open the current V12 comparison dashboard →</a></strong></p><p class="b063-note">The reports and original issues below remain preserved historical evidence. Publishing the dashboard does not refresh data or issue new forecasts.</p></section>'


CURRENT_BANNER = '<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" style="margin-bottom:28px"><p class="b063-eyebrow" style="margin-top:0">Latest execution R16 · Model comparison R14 · November 14, 2026 Pacific</p><h2 id="v12-current-title">Current models, observed games and market comparison</h2><p>The latest R16 execution reused 40 historical target models, then stopped at a memory-pressure admission latch during later cache imports. It committed no new target, residual or calibration fits and verified no current target reuse. The model scores, 2,503 observed games and DraftKings, Kalshi and Polymarket comparisons remain the dated R14 evidence. Complete current-season coverage and a current champion remain unverified.</p><p><strong><a href="v12.html">Open the current V12 comparison dashboard →</a></strong></p><p class="b063-note">The reports and original issues below remain preserved historical evidence. Publishing the dashboard does not refresh data or issue new forecasts.</p></section>'

def strip_banner(html: str) -> str:
    """Remove only the exact current wrapper to recover prior archive bytes."""
    if 'id="v12-current-evidence"' not in html:
        return html
    matches = [banner for banner in (CURRENT_BANNER, R15_BANNER, PREVIOUS_BANNER) if html.count(banner) == 1]
    if len(matches) != 1:
        raise ValueError('Unexpected current evidence banner')
    return html.replace(matches[0], '', 1)


def render_banner(html: str) -> str:
    """Compose the current link without modifying dated historical content."""
    html = strip_banner(html)
    if html.count('<main>') != 1:
        raise ValueError('Historical landing must have one main element')
    return html.replace('<main>', '<main>' + CURRENT_BANNER, 1)
