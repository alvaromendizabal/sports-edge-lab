# NFL season-locked validation nominees

All three policies were evaluated on the same 285 finals from 2024 and the same 285 finals from 2025. The comparison gives 2024 a 30% weight and 2025 a 70% weight. Each policy uses the weights and calibration available at Week 1 of that season. No outcome from the season being scored enters a fit or calibration. The 2026 column grades those same registered policies on all 148 finals, including the tie. The historical exercise conditions on the eventual matchups.

Pooled opponent ridge has the lowest validation joint loss, winner log loss and margin MAE. It also leads in winner Brier, winner accuracy and margin CRPS. Recent opponent ridge leads for total MAE and total CRPS. All eight first-versus-second validation differences have paired 95% intervals that include zero. These results support a nominal choice by objective. The differences are too small relative to week-to-week variability to establish superiority.

| Objective | First on validation | Second | Validation first / second | Paired difference [95% interval] | 2026 first / second | 2026 difference [95% interval] |
|---|---|---|---|---|---|---|
| Joint loss | Pooled opponent ridge | Recent opponent ridge | 0.534362 / 0.534435 | -0.000072 [-0.002272, +0.001956] | 0.521812 / 0.520051 | +0.001761 [-0.004063, +0.007426] |
| Winner log loss | Pooled opponent ridge | Team-score baseline | 0.716819 / 0.718644 | -0.001825 [-0.012086, +0.009141] | 0.712696 / 0.722691 | -0.009995 [-0.023741, +0.004623] |
| Winner Brier | Pooled opponent ridge | Team-score baseline | 0.487600 / 0.489327 | -0.001726 [-0.010722, +0.007838] | 0.477172 / 0.486285 | -0.009113 [-0.021378, +0.003542] |
| Winner accuracy | Pooled opponent ridge | Recent opponent ridge | 0.599649 / 0.585263 | +0.014386 [-0.003335, +0.032400] | 0.594595 / 0.601351 | -0.006757 [-0.040268, +0.027778] |
| Margin MAE | Pooled opponent ridge | Recent opponent ridge | 10.819966 / 10.822241 | -0.002275 [-0.092336, +0.085475] | 10.251133 / 10.145706 | +0.105426 [-0.077593, +0.335682] |
| Total MAE | Recent opponent ridge | Team-score baseline | 10.582336 / 10.586851 | -0.004516 [-0.085358, +0.072822] | 10.998084 / 11.096009 | -0.097925 [-0.309901, +0.124339] |
| Margin CRPS | Pooled opponent ridge | Recent opponent ridge | 7.796433 / 7.811433 | -0.014999 [-0.070754, +0.037115] | 7.381710 / 7.323207 | +0.058503 [-0.049347, +0.163219] |
| Total CRPS | Recent opponent ridge | Pooled opponent ridge | 7.663651 / 7.677548 | -0.013897 [-0.052261, +0.026047] | 7.755239 / 7.745372 | +0.009867 [-0.098115, +0.129510] |

The differences use the validation nominee minus its validation runner-up. Lower is better for each loss and error. Higher is better for accuracy. Weekly intervals resample 16,384 whole-week blocks per season. The point differences, intervals, game-set hashes and leave-one-week-out ranges for every pair and all three seasons are in the JSON. The winner metrics in this table score all three outcomes, including ties. Separate decisive-only winner metrics appear in the case-matched exports. The 2026 results are descriptive and do not choose the nominees. N025 has its own rolling historical comparison and is ineligible for this three-policy fixed panel.
