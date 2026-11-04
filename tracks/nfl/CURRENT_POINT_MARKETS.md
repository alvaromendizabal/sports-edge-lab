# NFL spread and total references

[Open the dashboard](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/#latest-coverage) · [Track overview](README.md) · [Curated data](point_markets.json) · [Executable validation](point_markets.py)

**Scope: preserved N034 point-reference export.** Its original coverage counts remain below. The dashboard also includes [separate recovered N035 current references](CURRENT_SOURCE_RECOVERY.md): Week 9 Kalshi margin 14/15 and total 10/15, DraftKings 14/15 for both, and Polymarket 11/15 for both. This later partial source recovery does not imply final owner completion or replace historical rows.

The dashboard shows captured point-market evidence alongside model predictions. The data was already acquired by the authenticated November 3 N034 owner run. Recovering and displaying it adds no model fits, new forecasts, new provider acquisition or wagering results. The prepared N035 executable remains separate from this report extension.

## Find a game

Choose **Games to inspect** and a **Model forecast stream**. Select one hour before kickoff, two hours before kickoff, latest before kickoff or the currently observed upcoming market. The model's inputs and original issue time remain fixed when the market reference changes.

The Monday-night shortcut opens **CHI 34–17 SEA** and its separate genuine T1 issue. The model backed Seattle at a rounded 62.9%, projected Seattle by 5.2 and a 46.5-point total. The pick lost; the actual home margin was −17 and the total was 51. It is not backfilled into the earlier reconstructed 120-game cohort.

## Read the point references correctly

| Display | Meaning | What it does not establish |
|---|---|---|
| Model home margin | Predicted home points minus away points | A probability of covering every possible spread |
| Model total | Predicted combined points | A complete predictive distribution |
| `Home margin > 3.5`, observed probability | A particular market condition and its recorded probability | The market's mean score margin |
| `Total points > 46.5`, observed probability | Probability attached to that exact total threshold | A projected final total of 46.5 |
| DraftKings line | A normalized quoted spread or total reference | A reconstructed contract probability, guaranteed fair price or exact score mean |

Home-margin predicates always use the displayed home team. Away-team conditions are translated with their correct inequality and sign. Integer sportsbook lines may push at equality; binary contracts retain their own settlement definitions. These are not interchangeable products.

For a compact public view, one predicate-qualified contract is chosen per game, provider, target and horizon by its probability's distance from 50%, with deterministic ties. Selection does not inspect the game outcome. Counts and ranges describe captured evidence, not independent bets. Current two-sided order-book references require compatible clocks. Original raw ladders, provider responses and complete private exports remain outside this repository.

## Preserved N034 export coverage

- **Kalshi:** margin and total conditions for all 121 completed games at both T1 and T2. Current Week 9 books remain unavailable in this snapshot.
- **Polymarket:** margin and total conditions for 92 completed games at T1 and T2. Both targets have timestamped current references for 11 of 15 Week 9 games.
- **DraftKings:** current margin and total lines for 14 of 15 Week 9 games. Preserved historical lines for 120 finals are visible separately, with unavailable quote/acquisition clocks explicitly labelled. No new timestamp is inferred from those saved values.
- **LV–SF:** source quotes were captured, but provider and canonical kickoff times disagree. They remain outside matched game references.
- **Latest before kickoff:** not acquired by the N034 pass. This view never silently substitutes an earlier T1 or T2 observation.

The coverage table distinguishes timestamped references from saved lines with unavailable clocks. A current snapshot can be useful before the final hour, but it cannot be relabelled as the eventual closing market. Historical acquisition time may occur after the game because the preserved historical quote has its own earlier timestamp. All actual clocks remain inspectable on each card.

The new threshold rows are display-only. They do not enter the existing margin/total MAE or RMSE panels and do not alter winner metrics, model probabilities, original issue clocks or disagreement records. No fees, liquidity, fills or profit are inferred.

## Reproduce the public checks

```bash
python tracks/nfl/point_markets.py
python -m unittest discover -s tracks/nfl -p 'test_point_markets.py'
python tracks/nfl/contracts.py --check-review
```

The tests reject later quotes at earlier cutoffs, invented source clocks, flipped home-margin orientation, duplicated references, raw payload fields and attempts to treat thresholds as score projections. This validates the public report contract; it does not replace private owner authentication or reproduce the research training.
