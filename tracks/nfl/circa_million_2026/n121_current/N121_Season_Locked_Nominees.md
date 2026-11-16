# NFL season-locked validation nominees

All three policies were evaluated on the same 285 finals from 2024 and the same 285 finals from 2025. The comparison gives 2024 a 30% weight and 2025 a 70% weight. Each policy uses the weights and calibration available at Week 1 of that season. No outcome from the season being scored enters a fit or calibration. The 2026 column grades those same registered policies on all 147 finals, including the tie. The historical exercise conditions on the eventual matchups.

Pooled opponent ridge has the lowest validation joint loss, winner log loss and margin MAE. It also leads in winner Brier, winner accuracy and margin CRPS. Recent opponent ridge leads for total MAE and total CRPS. All eight first-versus-second validation differences have paired 95% intervals that include zero. These results support a nominal choice by objective. The differences are too small relative to week-to-week variability to establish superiority.

| Objective | First on validation | Second | Validation first / second | Paired difference [95% interval] | 2026 first / second | 2026 difference [95% interval] |
|---|---|---|---|---|---|---|
| Joint loss | Pooled opponent ridge | Recent opponent ridge | 0.534362 / 0.534435 | -0.000072 [-0.002272, +0.001956] | 0.518059 / 0.516290 | +0.001769 [-0.004105, +0.007443] |
| Winner log loss | Pooled opponent ridge | Team-score baseline | 0.716819 / 0.718644 | -0.001825 [-0.012086, +0.009141] | 0.712902 / 0.722438 | -0.009535 [-0.022995, +0.004880] |
| Winner Brier | Pooled opponent ridge | Team-score baseline | 0.487600 / 0.489327 | -0.001726 [-0.010722, +0.007838] | 0.477300 / 0.485953 | -0.008653 [-0.020691, +0.003749] |
| Winner accuracy | Pooled opponent ridge | Recent opponent ridge | 0.599649 / 0.585263 | +0.014386 [-0.003335, +0.032400] | 0.591837 / 0.598639 | -0.006803 [-0.040541, +0.027972] |
| Margin MAE | Pooled opponent ridge | Recent opponent ridge | 10.819966 / 10.822241 | -0.002275 [-0.092336, +0.085475] | 10.282731 / 10.178101 | +0.104630 [-0.081325, +0.336070] |
| Total MAE | Recent opponent ridge | Team-score baseline | 10.582336 / 10.586851 | -0.004516 [-0.085358, +0.072822] | 10.835331 / 10.920462 | -0.085131 [-0.303208, +0.143120] |
| Margin CRPS | Pooled opponent ridge | Recent opponent ridge | 7.796433 / 7.811433 | -0.014999 [-0.070754, +0.037115] | 7.405196 / 7.347060 | +0.058136 [-0.051595, +0.163410] |
| Total CRPS | Recent opponent ridge | Pooled opponent ridge | 7.663651 / 7.677548 | -0.013897 [-0.052261, +0.026047] | 7.616853 / 7.607627 | +0.009226 [-0.099562, +0.129725] |

The differences use the validation nominee minus its validation runner-up. Lower is better for each loss and error. Higher is better for accuracy. Weekly intervals resample 16,384 whole-week blocks per season. The point differences, intervals, game-set hashes and leave-one-week-out ranges for every pair and all three seasons are in the JSON. The winner metrics in this table score all three outcomes, including ties. Separate decisive-only winner metrics appear in the case-matched exports. The 2026 results are descriptive and do not choose the nominees. N025 has its own rolling historical comparison and is ineligible for this three-policy fixed panel.
