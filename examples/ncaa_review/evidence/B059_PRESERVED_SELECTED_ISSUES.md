# Preserved selected NCAA issues from the B059 archive

The saved archive contains **96 selected forecast values for 32 games: 18 men’s and 14 women’s**, with winner probability, point margin and total points for each game. Their original scheduled tip times run from **November 6, 2026, 02:00 UTC through November 10, 2026, 03:00 UTC**. These forecasts were issued before their recorded cutoffs and retained durably in the original forecast journal.

[Selected prior issues, CSV](../data/ncaa_preserved_selected_issues_b059.csv) · [Selected prior issues, JSON](../data/ncaa_preserved_selected_issues_b059.json)

The export follows the six saved historical league/target selections: log loss for winner probability and MAE for margin and total points. These selections used exposed 2024–25 and 2025–26 research. For each matching selected role and game, the export preserves the latest eligible original issue without consulting current-season outcomes. Of the 35 distinct games in the wider issued archive, three have no issue matching these selected roles and remain outside this export.

Original ESPN game and ordered team IDs, event time, cutoff, issue time, feature availability, and training clocks remain visible. Probabilities are rounded to six decimal places and point estimates to three. Margin is home minus away; total is the combined score. The underlying private issues remain unchanged.

**These are preserved prior research forecasts, with no new issue or promotion credit.** They are separate from the unmatched official-game inventory and from any newly qualified current champion. The original B003 model has no issued rows in this export. No fresh forecast for a later upcoming game is implied.

The archive has no authenticated exact NCAA-to-ESPN final-result link for these issues. Outcome and performance fields therefore remain unavailable; no score, new accuracy, log loss, MAE, RMSE or matched Kalshi result is inferred. The selected outputs document earlier work that remains usable once exact outcome identity and source-clock gates are satisfied.
