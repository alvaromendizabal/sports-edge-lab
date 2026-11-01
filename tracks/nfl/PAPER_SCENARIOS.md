# Understand paper returns without inventing an edge

This credential-free example converts stated odds into dollars and preserves unknown inputs. Its teams, probabilities and prices are invented. It makes no provider request, real-game recommendation, account assumption or order.

```bash
python tracks/nfl/paper_scenarios.py --demo
python -m unittest discover -s tracks/nfl -p 'test_*.py' -v
```

For a hypothetical $100 straight bet at **−200**, a win earns **$50 profit** and returns **$150 total**, including the original $100. A loss costs **$100**. At **+150**, a win earns **$150 profit** and returns **$250 total**. Gross payout and profit are different numbers.

The demonstration uses four hypothetical $100 positions and enumerates all 16 win/loss combinations. It gives no probability to those combinations: doing so would require a justified dependence model. Ties are excluded from that particular win/loss table and handled separately by each position's explicit refund-or-loss rule. A $400 illustration does not become a proposed allocation: unknown prior weekly commitments leave the remaining amount unknown and the new proposed stake at zero.

## Percentages and payoff distributions

Normalizing a genuine paired two-side quote removes its margin once. The resulting percentage is a **market reference**, not an independent model forecast or evidence of an advantage. Settlement may include a third state. A 60% chance of winning *conditional on no tie* does not establish an unconditional 60% chance of winning.

With a hypothetical $100 even-money bet, 60% conditional win chance and an explicitly assumed 10% tie chance, unconditional win chance is 54%. If a tie refunds the stake, expected profit is $18; if it loses, expected profit is $8. The example does not claim 10% is a realistic NFL tie probability. When tie probability is unknown, unconditional expected profit remains unknown. The optional fixed fee is charged once in every state under the explicitly declared toy contract, including refunds; real fee schedules require their own model.

The module does not turn a PrizePicks or Underdog component into a straight bet, multiply dependent leg probabilities, infer exchange fees, or treat a last trade as an executable ask. Complete entry payouts, void rules, depth and instrument eligibility need additional evidence before evaluating those products.

## Actual issue time matters

A quote acquired after the day-before cutoff stays late even if its represented quote time is older. The clock checker requires timezone-aware source, acquisition, issue and kickoff times. Meeting the T−24 time boundary is only temporal eligibility; it does not prove an approved model, correct event binding or executable offer.

## Engineering scope

The public tests cover arithmetic, missing tie mass, refund/loss rules, fees, weekly-budget reconciliation, actual issue clocks and deterministic scenario enumeration. They establish software behavior on invented inputs. They do not train models, improve the authenticated NFL scores or modify the preserved historical aggregate review.
