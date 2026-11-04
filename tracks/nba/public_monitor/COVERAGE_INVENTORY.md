# Calendar coverage and comparison eligibility

An inventory built by joining forecasts to quotes hides games whenever either
side is missing. The calendar must be the starting point. The independent
[`coverage_inventory.py`](coverage_inventory.py) example keeps every observed
event, then attaches selected historical winner references and reports the same
game denominator for each provider and cutoff.

Run the invented example and its failure cases from the repository root:

```bash
python -m tracks.nba.public_monitor.coverage_inventory
python -m unittest discover -s tracks/nba/public_monitor/tests -v
```

This module uses Python's standard library and the existing
[historical-reference contracts](HISTORY_PANELS.md). It makes no network requests
and contains no actual NBA records, forecasts, prices, model recipes or private
execution material. It does not alter the dated public evidence capsule or
publish a live prediction service.

## Separate questions, separate counts

| Question | Evidence in this example |
|---|---|
| Did the calendar contain this event? | A timestamped event with ordered teams, an explicit phase and a schedule version. |
| Did the source return a requested date? | An `OBSERVED` date response, including a valid zero-game day. A failed response has an unknown game count. |
| Did we recover a suitable reference? | The quote's event and scheduled tip match the inventory, and its own source clock satisfies the selected cutoff. |
| Was the reference possessed at that cutoff? | Its separate acquisition clock is no later than the cutoff. Later recovery does not create earlier possession. |
| Is a saved forecast available? | A display attribute. It never controls whether an event or recovered reference is retained. |
| Did we prove the full season is present? | Not in this small example. Completion of requested dates is a narrower statement. |

The same observation can appear in several cutoff views. Several contracts or
methods can also describe one event. `selected_contract_records` counts records;
`observed_reference_games` counts distinct games. Neither is an independent
forecast sample size. Polymarket US and international remain separate products.

## Clocks and schedule corrections

The selector reports latest observed before tip, T60 and T120 independently.
A 19:59 quote for a 20:00 game can enter the latest view but cannot fill the
18:00 or 19:00 cutoff. A sampled history whose requested window is exhausted
still does not prove that all ticks were observed.

Schedule updates preserve previously observed games even when a later response
omits them. An observed reschedule records both tip times. Quotes tied to the old
tip remain in the unjoined evidence with a reason; the code never rewrites their
clocks. Changed ordered teams or conflicting schedule records with the same
observation clock require explicit reconciliation. A final game status does not
turn a regular-season game into a cup championship.

Weekly grouping uses Pacific Monday through Sunday, including the local-date
boundary and daylight-saving rules. These are calendar weeks, not a claim about
a league's separately defined week numbering.

## Limits and extension points

The inherited demonstration compares home-side, full-game winner probabilities.
Supporting spread and total contracts requires additional exact target, line,
orientation and settlement contracts. A binary spread probability is not a
projected scoring margin; a total-contract probability is not a projected point
total. This example does not manufacture either conversion.

Calendar inclusion and source recovery do not establish executable prices,
fees, depth, jurisdiction, settlement or positions. The output has zero orders
and allocation, and unknown profit and ROI. Real private acquisition needs its
own access and source authentication. The
[publication boundary](../../../docs/PUBLICATION_BOUNDARY.md) continues to apply.
