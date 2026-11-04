# Every game, independent market clocks

[Interactive review](review.html#latest-coverage) · [Current model card](CURRENT_MODEL_CARD.md) · [Methodology](CURRENT_METHODOLOGY.md)

The current coverage view keeps all 272 scheduled 2026 games, including 121 completed games and all 15 games in Week 9. Selecting an unavailable model stream or market reference never removes a game. The preserved N033 scorecards retain their own smaller, dated comparison cohorts.

## Four references answer different questions

| Dashboard reference | Meaning | Scientific use |
|---|---|---|
| 2 hours before kickoff | Last genuine observation at or before kickoff minus two hours, also called T2 | A same-cutoff comparison only with an eligible T2 model vector |
| 1 hour before kickoff | Last genuine observation at or before kickoff minus one hour, also called T1 | A distinct comparison; a T2 model versus T1 market is explicitly a later-reference supplement |
| Latest before kickoff | Last authenticated observation strictly before kickoff | A closing market benchmark; it does not reissue or update an earlier model |
| Latest observed upcoming | A real observation captured while the game is still unstarted | An inspectable current market reference; reaching T2 is not a display requirement |

An observation does not have to fall on the exact cutoff minute. Its quote time and age must remain visible, and the source adapter must establish that it is a genuine observation. Missing history is never filled by interpolation, a fabricated snapshot, an unlabelled later quote or a silently carried-forward T2 value. A historical quote can be acquired after the game if its original source timestamp is authentic; that later acquisition is not a historical forecast issue.

## Keep models fixed while changing the reference

The selector changes the displayed market reference, not model features, training outcomes, parameters or issue time. Frozen-original monitoring, causal rolling reconstructions and genuine issues retain their own labels. A reconstruction fitted later can be evaluated only under its registered causal reconstruction policy; it cannot become an original historical issue. A later market benchmark cannot make the earlier model a same-information comparison.

Source publication, quote time, label availability, feature boundary, fit completion and actual issue are separate clocks. The interface exposes the clocks that were exported and explicitly marks those unavailable. It does not infer a missing original-frozen ledger from saved model vectors.

## Completed evidence and incomplete execution

The N034 owner run failed its provider-history completion stage. Its preserved completed artifacts can still be independently authenticated and inspected. Publishing an authenticated derived report does not change that run into a completed scientific pipeline. The newer view is a separate coverage and reporting update; accepted historical scorecards remain intact.

Provider directions are derived report outputs. Raw licensed price arrays, bids, asks, order books, private model recipes and production weights remain private. A winner direction is not a probability distribution for margin or total. A spread or total threshold contract is not a regression point prediction. No executable expected value or profit is established without the appropriate prices, fees, depth and settlement evidence.

## Reproduce the public engineering checks

```bash
python -m unittest discover -s tracks/nfl -p 'test_*.py'
python tracks/nfl/contracts.py --check-review
```

`market_clock.py` uses invented examples to test the boundary directly: a genuine quote two minutes before a cutoff is admissible, a later reference is publishable separately, and a live quote cannot be relabelled pregame. These tests demonstrate public engineering behavior; they do not reproduce private training or authenticate an owner run.
