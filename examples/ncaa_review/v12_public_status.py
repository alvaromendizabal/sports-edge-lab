"""Current NCAA evidence navigation; older scientific rows remain unchanged."""
from __future__ import annotations

CURRENT_BANNER = '<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" style="margin-bottom:28px"><p class="b063-eyebrow" style="margin-top:0">Current dated evidence · V12 / R14 · November 15, 2026 UTC</p><h2 id="v12-current-title">Current models, observed games and market comparison</h2><p>The newer V12 dashboard contains 2,503 observed source games, current frozen-model reconstruction scores, historical metric roles and the exact DraftKings, Kalshi and Polymarket qualification gaps. Complete current-season coverage and a current champion remain unverified.</p><p><strong><a href="v12.html">Open the current V12 comparison dashboard →</a></strong></p><p class="b063-note">The reports and original issues below remain preserved historical evidence. Publishing the dashboard does not refresh data or issue new forecasts.</p></section>'

def render_banner(html: str) -> str:
    """Add one current-evidence link to the generated historical NCAA landing."""
    if 'id="v12-current-evidence"' in html:
        raise ValueError('Current evidence banner is already present')
    if '<main>' not in html:
        raise ValueError('Historical landing has no main element')
    return (html.replace('<main>', '<main>' + CURRENT_BANNER, 1)
            .replace('Latest authenticated owner return', 'Archived authenticated owner return')
            .replace('Latest authenticated', 'Archived authenticated'))
