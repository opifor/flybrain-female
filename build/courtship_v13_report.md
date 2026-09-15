# Courtship v13

## Design record
Protocol v13: a contrast eye for him, fixed before data.
CHOSEN: base build/graph.npz, required --male-scale (a positive-weight dose, restored between trials); no functional-sign graph or direct LC10a drive.
MALE_EYE = contrast; all earlier protocols default to columnar.
Per column: L1 = clip(lum-ground, 0, 1)/(1-ground)*180 Hz; L2 = clip(ground-lum, 0, 1)/ground*108 Hz; ground = 0.5.
Ground gives 0/0 Hz; dark silhouette gives 0/108 Hz; white gives 180/0 Hz.
Female = v8: required own restored SAG graph, both SAG types, virgin 50 Hz, positive-weight scale 0.7, blind eye. Geometry and other drives remain as v9/v11.
Ten paired seeds, 400 steps, four conditions: song (both cues); mute (P1 outputs zero); noscent_orn (only Or47b drive zero, contact kept); blind (all male visual rates zero, scent and contact kept).
P36: his LC10a mean rate, song > blind, through the native visual path.
P37: his pIP10 mean rate AND delivered RMS, song > mute (both required).
P38: his P1 mean rate, song > noscent_orn. v11 found the opposite sign under the columnar eye; this is the same comparison with flooding removed. Another reversal will be reported as such.
P39: correlations of a_neural[t] and m_neural[t] with LC10a[t-1] in song, each minus its within-trial null: circularly shift the full LC10a sequence forward by floor(steps/2), then apply the same one-window lag. Either channel may establish; report both.
Rule as v5: mean paired difference > 2 SE across n=10 valid seeds. Undefined correlations are excluded, never replaced by zero; fewer than ten cannot establish. Quick: one or two seeds x 80 steps, smoke only.
P40 descriptive: total male rate per condition, including sight/no-sight windows; her vpoDN and accept, distance, approach/retreat and contact-window fraction (distance < 2 mm).
Calibration only, not outcomes: with the columnar eye any input ignited the male network to approximately 45-60 Hz total. Ground columns carried 90/54 Hz and dark silhouette columns 0/108 Hz. A contrast eye left him silent with nothing in view and lit the network only when she was in view. LC10a stayed at 0-2 Hz under both eyes in short probes.
Read-only census: L2 reaches 209 of 275 LC10a cells within two positive hops; L1's first hop is inhibitory; the strongest LC10a inputs are medulla types and two large inhibitory classes.

MALE_EYE = contrast; male scale = 0.9.
Male graph: {"path": "build/graph.npz", "sha256": "5a6e6fbfa5f2d3840218cb32cc0182828829c9212b483ce771cfea7718a7b947"}
Female graph: {"file": "graph_female_own_sag.npz", "path": "build/graph_female_own_sag.npz", "sha256": "f2452ec31b830931c01a3985ed8e6cbf61264a76e37f70337e57b2ece2fcb02a", "restore": {"csv_rows": 5342446, "empty_types": [], "excluded_synapses": 0, "floor": 5, "mapping": "individual female pre/post ids; pair sum >= 5; post cell must be in graph", "per_target_type": [{"by_source_type": {"AN_FLA_SMP_2": 76, "AN_SMP_2": 539}, "synapses": 615, "target_type": "pC1a"}, {"by_source_type": {"AN_FLA_SMP_2": 558, "AN_SMP_2": 10}, "synapses": 568, "target_type": "CB0959"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 387}, "synapses": 387, "target_type": "pC1b"}, {"by_source_type": {"AN_FLA_SMP_2": 291, "AN_SMP_2": 6}, "synapses": 297, "target_type": "CB0699"}, {"by_source_type": {"AN_FLA_SMP_2": 195, "AN_SMP_2": 0}, "synapses": 195, "target_type": ""}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 179}, "synapses": 179, "target_type": "pC1c"}, {"by_source_type": {"AN_FLA_SMP_2": 168, "AN_SMP_2": 5}, "synapses": 173, "target_type": "SMP094"}, {"by_source_type": {"AN_FLA_SMP_2": 149, "AN_SMP_2": 0}, "synapses": 149, "target_type": "CB1024"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 128}, "synapses": 134, "target_type": "CB0094"}, {"by_source_type": {"AN_FLA_SMP_2": 114, "AN_SMP_2": 0}, "synapses": 114, "target_type": "AN_SMP_1"}, {"by_source_type": {"AN_FLA_SMP_2": 78, "AN_SMP_2": 0}, "synapses": 78, "target_type": "CB0075"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 60}, "synapses": 60, "target_type": "CB0405"}, {"by_source_type": {"AN_FLA_SMP_2": 54, "AN_SMP_2": 0}, "synapses": 54, "target_type": "PAL01"}, {"by_source_type": {"AN_FLA_SMP_2": 52, "AN_SMP_2": 0}, "synapses": 52, "target_type": "SMP025a"}, {"by_source_type": {"AN_FLA_SMP_2": 21, "AN_SMP_2": 17}, "synapses": 38, "target_type": "SMP286"}, {"by_source_type": {"AN_FLA_SMP_2": 31, "AN_SMP_2": 0}, "synapses": 31, "target_type": "SMP172"}, {"by_source_type": {"AN_FLA_SMP_2": 19, "AN_SMP_2": 7}, "synapses": 26, "target_type": "AN_FLA_SMP_2"}, {"by_source_type": {"AN_FLA_SMP_2": 17, "AN_SMP_2": 8}, "synapses": 25, "target_type": "pC1e"}, {"by_source_type": {"AN_FLA_SMP_2": 15, "AN_SMP_2": 0}, "synapses": 15, "target_type": "CB1610"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 11}, "synapses": 11, "target_type": "CB1371"}, {"by_source_type": {"AN_FLA_SMP_2": 11, "AN_SMP_2": 0}, "synapses": 11, "target_type": "CB2165"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 5}, "synapses": 11, "target_type": "NPFL1-I"}, {"by_source_type": {"AN_FLA_SMP_2": 10, "AN_SMP_2": 0}, "synapses": 10, "target_type": "SMP538"}, {"by_source_type": {"AN_FLA_SMP_2": 9, "AN_SMP_2": 0}, "synapses": 9, "target_type": "SMP513"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 8}, "synapses": 8, "target_type": "CB4204"}, {"by_source_type": {"AN_FLA_SMP_2": 8, "AN_SMP_2": 0}, "synapses": 8, "target_type": "SMP515"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "FLA101f_c"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SIP076"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SMP123b"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "CB4233"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "SMP034"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "pC1d"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "AN_SMP_FLA_1"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB0015"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB2422"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "DNpe034"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 5}, "synapses": 5, "target_type": "SMP161"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "SMP593"}], "per_type": {"AN_FLA_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 1033, "restored_synapses": 1033, "root_id": 720575940614614162}, {"exported_synapses": 919, "restored_synapses": 919, "root_id": 720575940638396998}], "exported_synapses": 1952, "restored_synapses": 1952}, "AN_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 690, "restored_synapses": 690, "root_id": 720575940623363000}, {"exported_synapses": 685, "restored_synapses": 685, "root_id": 720575940631004202}], "exported_synapses": 1375, "restored_synapses": 1375}}, "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; the BANC prediction for the same types is dopamine. Neither prediction fixes the sign of the effect.", "sources": [{"file": "connections_princeton.csv.gz", "sha256": "445f996bf6c4b1803b9ba186189138a3061ff8623aa94c0abcf38af30a5bd48b"}, {"file": "graph_female.npz", "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"}], "synapse_mv": 0.275, "synapses_restored": 3327}, "state_cells": 4, "state_cells_per_type": {"AN_SMP_2": 2, "AN_FLA_SMP_2": 2, "ANXXX983": 0}}
Environment: {"brain_class": "flysim_gpu.FlyBrainGPU"}

## Verdicts
| Prediction | Difference | SE | n | >2 SE | Established (n=10) |
|---|---:|---:|---:|---|---|
| P36 | -0.014418181818181821 | 0.0113367698565567 | 10 | not supported | False |
| P37_command | 0.45249999999999985 | 2.1571858275179827 | 10 | not supported | False |
| P37_rms | -0.002622014931580561 | 0.006630797330200979 | 10 | not supported | False |
| P38 | -1.7912209302325586 | 1.1827859322462966 | 10 | not supported | False |
| P39_a | -0.0438049722910105 | 0.026932399168183286 | 10 | not supported | False |
| P39_m | -0.051250825144343724 | 0.04599477886201252 | 10 | not supported | False |

## Per-seed outcomes / P40
| seed | condition | male_eye | p1_hz | pip10_hz | lc10a_hz | delivered_rms | male_total_hz | male_total_sight_hz | male_total_no_sight_hz | a_neural_lc10a_lagged_rho | a_neural_lc10a_shifted_rho | m_neural_lc10a_lagged_rho | m_neural_lc10a_shifted_rho | vpodn_hz | accept | distance_mm | approach | retreat | contact_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | song | contrast | 1.96453 | 1.35 | 0.0829091 | 0.00754297 | 43.2452 | 43.417 | 43.1443 | -0.0563917 | -0.0557939 | 0.0641316 | 0.0817442 | 74 | True | 11.8146 | False | True | 0 |
| 0 | mute | contrast | 2.20581 | 7.025 | 0.131636 | 0.0200745 | 42.9219 | 44.2913 | 42.3828 | -0.111856 | -0.0283686 | 0.0680799 | -0.0211975 | 77.275 | True | 9.2942 | False | True | 0 |
| 0 | noscent_orn | contrast | 1.16047 | 1.725 | 0.0249091 | 0.00969744 | 10.3283 | 41.4881 | 8.68827 | 0.250565 | -0.0206694 | 0.339785 | -0.101323 | 76.475 | True | 12.0203 | False | True | 0 |
| 0 | blind | blind | 1.85349 | 5.575 | 0.0498182 | 0.0146034 | 42.2516 | None | 42.2516 | -0.0294218 | 0.0850746 | 0.0658088 | -0.0640564 | 76.025 | True | 10.4141 | False | True | 0 |
| 1 | song | contrast | 2.01802 | 10.55 | 0.0438182 | 0.0210015 | 40.5019 | 40.4331 | 40.5423 | 0.0361559 | 0.0248111 | -0.125614 | -0.0183106 | 76.375 | True | 7.7362 | False | True | 0 |
| 1 | mute | contrast | 1.76453 | 1.075 | 0.0618182 | 0.00616349 | 41.6955 | 41.5317 | 41.7846 | -0.031344 | 0.250356 | -0.133881 | 0.0338653 | 74.325 | True | 8.3346 | False | True | 0 |
| 1 | noscent_orn | contrast | 7.26686 | 79.575 | 0.0436364 | 0.0838101 | 48.3217 | 47.9758 | 48.4826 | -0.245916 | 0.300076 | -0.09288 | 0.198342 | 72.6 | True | 6.49656 | True | False | 0 |
| 1 | blind | blind | 3.40349 | 28.45 | 0.0910909 | 0.0264437 | 42.1719 | None | 42.1719 | -0.0747707 | 0.0956417 | 0.0235369 | 0.0235219 | 76.05 | True | 12.4661 | True | False | 0 |
| 2 | song | contrast | 1.08198 | 0.65 | 0.0678182 | 0.00313959 | 40.4667 | 41.3356 | 40.177 | -0.0285724 | 0.0808887 | 0.00508853 | -0.0814638 | 70.475 | True | 12.3848 | False | True | 0 |
| 2 | mute | contrast | 1.78314 | 5.05 | 0.130182 | 0.0175878 | 44.5321 | 44.1429 | 44.8349 | -0.0982652 | -0.00675486 | -0.142377 | -0.039901 | 70.2 | True | 7.57658 | False | True | 0 |
| 2 | noscent_orn | contrast | 0.901744 | 0.15 | 0.00163636 | 0.00218445 | 2.38407 | 45.6819 | 1.27387 | None | None | 0.441093 | -0.0237071 | 70.675 | True | 6.11087 | False | True | 0 |
| 2 | blind | blind | 1.64012 | 2.15 | 0.0569091 | 0.012142 | 44.1791 | None | 44.1791 | -0.0380513 | -0.0380513 | -0.151074 | 0.0182322 | 70.95 | True | 10.1071 | False | True | 0 |
| 3 | song | contrast | 1.61163 | 9.075 | 0.0709091 | 0.0230673 | 40.8162 | 41.2376 | 40.6314 | -0.0568122 | -0.0593525 | -0.0283047 | -0.0284558 | 73.55 | True | 8.10522 | False | True | 0 |
| 3 | mute | contrast | 1.06628 | 7.175 | 0.0705455 | 0.0287313 | 41.1327 | 41.5517 | 40.6258 | -0.048836 | -0.0865691 | -0.234132 | 0.083535 | 73.175 | True | 3.13429 | True | False | 0.2 |
| 3 | noscent_orn | contrast | 4.81105 | 15.4 | 0.0916364 | 0.0419414 | 42.7355 | 42.1529 | 43.3182 | 0.0494447 | 0.163744 | 0.0483953 | 0.0682434 | 70.45 | True | 3.51083 | True | False | 0.4275 |
| 3 | blind | blind | 3.71628 | 12.275 | 0.0994545 | 0.00651815 | 40.4376 | None | 40.4376 | -0.0231028 | -0.0581658 | 0.00111647 | 0.0704865 | 76.55 | True | 17.3218 | False | True | 0 |
| 4 | song | contrast | 1.28081 | 14.275 | 0.104364 | 0.0487382 | 40.893 | 40.9847 | 40.8537 | 0.0376277 | 0.0366511 | -0.143388 | 0.20848 | 74.6 | True | 9.73285 | False | True | 0 |
| 4 | mute | contrast | 1.27791 | 7.55 | 0.046 | 0.0251018 | 41.3154 | 43.8785 | 40.4032 | -0.054718 | -0.0890174 | -0.0161724 | 0.0894017 | 73.975 | True | 7.19706 | True | False | 0 |
| 4 | noscent_orn | contrast | 0.601163 | 0.55 | 0.00218182 | 0.00396048 | 1.48897 | 44.4559 | 1.05496 | -0.00436283 | -0.00436283 | 0.248273 | -0.0099045 | 74.925 | True | 6.95667 | True | False | 0 |
| 4 | blind | blind | 1.56744 | 15.7 | 0.0747273 | 0.039287 | 41.1512 | None | 41.1512 | 0.231964 | -0.0580817 | 0.0136271 | 0.00748483 | 75.725 | True | 5.66962 | False | True | 0 |
| 5 | song | contrast | 1.12907 | 3.625 | 0.0712727 | 0.0160443 | 42.0436 | 41.9426 | 42.0928 | 0.0153147 | 0.0145208 | -0.116079 | -0.126549 | 72.925 | True | 8.70616 | False | True | 0 |
| 5 | mute | contrast | 1.32616 | 2.85 | 0.0816364 | 0.00866263 | 41.366 | 42.539 | 41.0156 | 0.0473523 | -0.0198997 | 0.0470493 | 0.058961 | 73.9 | True | 11.0144 | False | True | 0 |
| 5 | noscent_orn | contrast | 5.49651 | 1.1 | 0.0390909 | 0.00984706 | 18.0757 | 42.7804 | 15.1774 | 0.0870565 | -0.0247926 | 0.356286 | -0.225686 | 76.05 | True | 7.79253 | False | True | 0 |
| 5 | blind | blind | 2.45872 | 4.9 | 0.0661818 | 0.00863759 | 40.9267 | None | 40.9267 | -0.08443 | -0.0153921 | 0.043284 | -0.0116207 | 75.3 | True | 13.9491 | False | True | 0 |
| 6 | song | contrast | 2.56802 | 7.1 | 0.0438182 | 0.0062105 | 40.803 | 43.281 | 40.2864 | -0.0589839 | 0.0221476 | 0.00135336 | 0.201364 | 70.5 | True | 12.8167 | False | True | 0 |
| 6 | mute | contrast | 4.31279 | 20.975 | 0.0634545 | 0.0560105 | 42.4486 | 42.4691 | 42.4256 | -0.140982 | -0.052881 | 0.0740926 | -0.0914652 | 70.65 | True | 2.48891 | True | False | 0.43 |
| 6 | noscent_orn | contrast | 0.484884 | 0.025 | 0.000727273 | 8.52769e-05 | 1.07945 | 38.6233 | 0.507718 | None | None | 0.492942 | -0.0153242 | 72.975 | True | 6.60877 | False | True | 0 |
| 6 | blind | blind | 1.87326 | 0.575 | 0.0878182 | 0.00486479 | 45.3586 | None | 45.3586 | -0.0317091 | -0.0317091 | -0.00701202 | -0.0632445 | 71.95 | True | 10.9341 | False | True | 0 |
| 7 | song | contrast | 1.65872 | 7.825 | 0.0150909 | 0.0241757 | 41.7308 | 43.4171 | 41.1383 | 0.00137464 | 0.257757 | 0.046003 | 0.0119303 | 71.075 | True | 6.52146 | True | False | 0.0075 |
| 7 | mute | contrast | 1.39593 | 2.975 | 0.0356364 | 0.0120749 | 40.5997 | 40.726 | 40.5455 | -0.0701608 | -0.0701608 | -0.139346 | -0.0690353 | 71.975 | True | 6.57514 | True | False | 0 |
| 7 | noscent_orn | contrast | 11.3965 | 48.95 | 0.165091 | 0.086737 | 39.1148 | 44.8904 | 35.9361 | 0.258148 | -0.0322535 | 0.0296716 | 0.087148 | 72.95 | True | 3.40326 | False | True | 0.1475 |
| 7 | blind | blind | 1.63837 | 5.375 | 0.0934545 | 0.0182919 | 41.4828 | None | 41.4828 | -0.095356 | -0.064295 | 0.0765237 | 0.0545369 | 77.7 | True | 9.4017 | False | True | 0 |
| 8 | song | contrast | 2.90698 | 2.575 | 0.0694545 | 0.0135149 | 42.0721 | 42.1413 | 42.0287 | -0.0273361 | -0.0212035 | -0.0540288 | 0.0553805 | 75.925 | True | 9.78368 | False | True | 0 |
| 8 | mute | contrast | 1.65 | 1.375 | 0.0501818 | 0.00525344 | 41.1131 | 42.3833 | 40.661 | 0.000271267 | 0.0548958 | -0.0891656 | 0.144365 | 75.55 | True | 13.39 | False | True | 0 |
| 8 | noscent_orn | contrast | 1.99767 | 5.3 | 0.111091 | 0.0174493 | 41.7072 | 39.8996 | 43.0989 | -0.0249756 | -0.0622474 | -0.0666493 | -0.163519 | 73.6 | True | 6.16893 | True | False | 0 |
| 8 | blind | blind | 1.6407 | 5.875 | 0.0749091 | 0.0146528 | 41.4547 | None | 41.4547 | -0.0764341 | 0.0286085 | 0.0442986 | -0.134974 | 76.025 | True | 9.67292 | False | True | 0 |
| 9 | song | contrast | 1.35291 | 6.125 | 0.0556364 | 0.00489607 | 46.112 | 45.6192 | 46.4838 | -0.0628094 | -0.0628094 | -0.00535703 | -0.147806 | 75.15 | True | 11.5895 | False | True | 0 |
| 9 | mute | contrast | 1.68779 | 2.575 | 0.0545455 | 0.0148909 | 41.0775 | 41.8973 | 40.596 | -0.0605108 | -0.0168678 | 0.127458 | 0.0392872 | 72.65 | True | 8.3686 | True | False | 0 |
| 9 | noscent_orn | contrast | 1.36802 | 2.25 | 0.0227273 | 0.0119483 | 21.6887 | 40.7847 | 14.2625 | 0.0310081 | -0.0396281 | 0.158074 | -0.207454 | 73.15 | True | 5.85835 | True | False | 0 |
| 9 | blind | blind | 1.78895 | 2.6 | 0.0749091 | 0.0103368 | 41.4197 | None | 41.4197 | 0.00369776 | 0.114759 | -0.0217266 | 0.0190945 | 70.725 | True | 9.88711 | False | True | 0 |

## Result
P36: not established.
P38: not established.
P37: not established (both command and RMS required).
P39: not established; channels: [].
Song minus blind LC10a: -0.014418181818181821 Hz. Song minus mute: 0.45249999999999985 Hz in pIP10 and -0.002622014931580561 delivered RMS.
Song minus noscent_orn P1: -1.7912209302325586 Hz. Song minus shifted lagged correlations: a=-0.0438049722910105, m=-0.051250825144343724.
P38 reverses the predicted sign again: P1 is higher without Or47b drive, as in v11. This sign alone is descriptive.
Ten-seed design; missing or undefined pairs cannot establish.
Estimated ten-seed cost: 1.1428 hours, excluding setup/rendering.

## Limitations
- The male scale is a chosen dose, not a measurement.
- Correction to the historical v5/v6 anatomical explanation: the female export does carry SAG outgoing synapses. Their serotonin consensus maps to sign zero in build_graph_female.py, so the transmitter-sign rule drops their edges. This is a modelling exclusion, not an anatomical absence. The earlier protocol and limitation strings are retained unchanged as published records.
- The restored edges are her own measured synapses. BANC is a second individual, not a donor for v8.
- Both FAFB SAG types are restored and driven; AN_FLA_SMP_2 has additional targets beyond the pC1 route.
- CHOSEN: the SAG effect sign is +1 on functional evidence; neither FAFB serotonin nor BANC dopamine fixes that sign.
- CHOSEN: positive-weight scale 0.7 is carried over from v7, without tuning on the v8 ladder.
- SPSN themselves are not modelled; the state enters at SAG.
- oviDN is a descending command readout; she has no ovipositor body model. Start geometry is chosen so she is visible to him.
- His wing motor neurons run near ceiling from background activity; the song is taken from the command neuron pIP10, not from the motor sum. Mode still uses the motor means.
- Her ear now hears a waveform in 5 ms sub-windows; the brain runs in real time for her. His brain also runs in real time.
- Pulse rhythm and carriers are chosen synthesis, not measured spike timing or a biomechanical wing model.
- The fork's zero-phase filter uses the whole current 50 ms block; boundary effects and within-block lookahead remain. Sample bins alternate lengths at 22050 Hz.
- The contact chemosensory cells are a putative receptor label (putative_ppk23), not verified ppk23 expression.
- His female-scent input is a chosen drive at the smell ceiling with distance falloff, not a measured pheromone plume; the cVA channel is held at zero because there is no other male.
- vpoDN identified as DNp37 by alias, 2 cells; pC1a-e 10 cells. No pheromone channel to her.
- In closed-loop 50 ms windows, silencing P1 outputs did not reduce pIP10 in the v4 smoke run; pIP10 is driven mainly by AVLP717m and aIPg7 in this graph, so the song dependence on P1 is not established here.
- Male P1 membership is the dictionary's uncertain 86-cell group. Outgoing-gain lesion need not silence P1's own spikes.
- No adaptation mechanism was added on his side; correlation does not establish causation.
- Dark and silence coincide with the blind female eye.
- Male eye and soma-side availability are recorded per trial; gains remain uncalibrated.
- Distance changes include both bodies; approach is not an isolated female command.
- He is inside the loop: his trajectory and song can change when she moves differently. Female eye remains blind; contrast/motion vision remains a later step.
- Mute changes only his P1 outgoing gains; its spikes need not be silent.
- Drives are chosen rates on chosen cell groups.
- The transmitter-sign rule treats the dictionary vAB3 cells as inhibitory because they are glutamatergic here.
- The contrast eye is a chosen transform, not a photoreceptor model.
- The native path to LC10a still passes through a signed LIF network.
- Male positive-weight scale is a dose.
- P39 uses a circular shift with the same marginals, not a separate trial; both channels are reported without a multiplicity correction.
- Correlation is not a learned adaptation mechanism. Legacy rendered-song fields do not measure the corrected one-window neural lag; P39 uses only current neural rates against previous-window LC10a.
- No-sight windows retain scent/contact and network history; they are not an isolated no-input trial.
