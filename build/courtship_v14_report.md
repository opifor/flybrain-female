# Courtship v14

## Design record
Protocol v14: olfactory dose sweep, fixed before data.
SMELL_DOSES = (200, 50, 20) Hz; no configurable smell-max list.
Male: base build/graph.npz, required positive finite --male-scale; positive weights restored between cells. MALE_EYE = contrast as v13: ground 0.5, L1=clip(lum-ground,0,1)/(1-ground)*180 Hz, L2=clip(ground-lum,0,1)/ground*108 Hz.
Female = v8: own restored SAG graph required, both SAG types, virgin 50 Hz, positive-weight scale 0.7, blind eye.
Only his Or47b (ORN_VA1v, 130 cells) input changes: dose * clip(1-distance/20 mm,0,1). Contact, other scent channels and her inputs are unchanged.
Ten seeds, 400 steps, paired by seed and start across nine cells: song, mute (P1 outputs zero), noscent_orn (Or47b zero regardless of dose) at each dose.
P41: dose lowers ignition: song total male rate at 200 > 20 Hz dose.
P42: command carries song at some dose: song > mute for BOTH pIP10 mean rate and delivered RMS at the SAME dose.
P43: he notices her at some dose: song > noscent_orn for P1 mean rate; report reversals at each dose.
Rule as v5: paired mean difference > 2 SE, n=10. Reversal means paired mean < -2 SE. Multiple-dose rule as v9: established only with ten valid pairs at every dose, support at at least one dose and no reversal of any required component at another dose. Negative means are also reported descriptively.
P44 descriptive: P1, pIP10, delivered RMS, total male rate, her vpoDN and accept, mean distance and approach/retreat per cell; fraction of windows with male total rate strictly >30 Hz per neuron (chosen ignition marker).
Quick = two seeds x 80 steps x nine cells (one seed allowed for tests); smoke only, never establishes predictions.
Measured motivation, v13: total male rate near 42 Hz in song, mute and blind, versus 22.7 Hz without Or47b. Lower dose may prevent ignition and expose P1 -> pIP10; this is a hypothesis, not an outcome.

Male scale: 0.9; MALE_EYE: contrast; doses: [200, 50, 20].
Male graph: {"path": "build/graph.npz", "sha256": "5a6e6fbfa5f2d3840218cb32cc0182828829c9212b483ce771cfea7718a7b947"}
Female graph: {"file": "graph_female_own_sag.npz", "path": "build/graph_female_own_sag.npz", "sha256": "f2452ec31b830931c01a3985ed8e6cbf61264a76e37f70337e57b2ece2fcb02a", "restore": {"csv_rows": 5342446, "empty_types": [], "excluded_synapses": 0, "floor": 5, "mapping": "individual female pre/post ids; pair sum >= 5; post cell must be in graph", "per_target_type": [{"by_source_type": {"AN_FLA_SMP_2": 76, "AN_SMP_2": 539}, "synapses": 615, "target_type": "pC1a"}, {"by_source_type": {"AN_FLA_SMP_2": 558, "AN_SMP_2": 10}, "synapses": 568, "target_type": "CB0959"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 387}, "synapses": 387, "target_type": "pC1b"}, {"by_source_type": {"AN_FLA_SMP_2": 291, "AN_SMP_2": 6}, "synapses": 297, "target_type": "CB0699"}, {"by_source_type": {"AN_FLA_SMP_2": 195, "AN_SMP_2": 0}, "synapses": 195, "target_type": ""}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 179}, "synapses": 179, "target_type": "pC1c"}, {"by_source_type": {"AN_FLA_SMP_2": 168, "AN_SMP_2": 5}, "synapses": 173, "target_type": "SMP094"}, {"by_source_type": {"AN_FLA_SMP_2": 149, "AN_SMP_2": 0}, "synapses": 149, "target_type": "CB1024"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 128}, "synapses": 134, "target_type": "CB0094"}, {"by_source_type": {"AN_FLA_SMP_2": 114, "AN_SMP_2": 0}, "synapses": 114, "target_type": "AN_SMP_1"}, {"by_source_type": {"AN_FLA_SMP_2": 78, "AN_SMP_2": 0}, "synapses": 78, "target_type": "CB0075"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 60}, "synapses": 60, "target_type": "CB0405"}, {"by_source_type": {"AN_FLA_SMP_2": 54, "AN_SMP_2": 0}, "synapses": 54, "target_type": "PAL01"}, {"by_source_type": {"AN_FLA_SMP_2": 52, "AN_SMP_2": 0}, "synapses": 52, "target_type": "SMP025a"}, {"by_source_type": {"AN_FLA_SMP_2": 21, "AN_SMP_2": 17}, "synapses": 38, "target_type": "SMP286"}, {"by_source_type": {"AN_FLA_SMP_2": 31, "AN_SMP_2": 0}, "synapses": 31, "target_type": "SMP172"}, {"by_source_type": {"AN_FLA_SMP_2": 19, "AN_SMP_2": 7}, "synapses": 26, "target_type": "AN_FLA_SMP_2"}, {"by_source_type": {"AN_FLA_SMP_2": 17, "AN_SMP_2": 8}, "synapses": 25, "target_type": "pC1e"}, {"by_source_type": {"AN_FLA_SMP_2": 15, "AN_SMP_2": 0}, "synapses": 15, "target_type": "CB1610"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 11}, "synapses": 11, "target_type": "CB1371"}, {"by_source_type": {"AN_FLA_SMP_2": 11, "AN_SMP_2": 0}, "synapses": 11, "target_type": "CB2165"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 5}, "synapses": 11, "target_type": "NPFL1-I"}, {"by_source_type": {"AN_FLA_SMP_2": 10, "AN_SMP_2": 0}, "synapses": 10, "target_type": "SMP538"}, {"by_source_type": {"AN_FLA_SMP_2": 9, "AN_SMP_2": 0}, "synapses": 9, "target_type": "SMP513"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 8}, "synapses": 8, "target_type": "CB4204"}, {"by_source_type": {"AN_FLA_SMP_2": 8, "AN_SMP_2": 0}, "synapses": 8, "target_type": "SMP515"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "FLA101f_c"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SIP076"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SMP123b"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "CB4233"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "SMP034"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "pC1d"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "AN_SMP_FLA_1"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB0015"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB2422"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "DNpe034"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 5}, "synapses": 5, "target_type": "SMP161"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "SMP593"}], "per_type": {"AN_FLA_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 1033, "restored_synapses": 1033, "root_id": 720575940614614162}, {"exported_synapses": 919, "restored_synapses": 919, "root_id": 720575940638396998}], "exported_synapses": 1952, "restored_synapses": 1952}, "AN_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 690, "restored_synapses": 690, "root_id": 720575940623363000}, {"exported_synapses": 685, "restored_synapses": 685, "root_id": 720575940631004202}], "exported_synapses": 1375, "restored_synapses": 1375}}, "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; the BANC prediction for the same types is dopamine. Neither prediction fixes the sign of the effect.", "sources": [{"file": "connections_princeton.csv.gz", "sha256": "445f996bf6c4b1803b9ba186189138a3061ff8623aa94c0abcf38af30a5bd48b"}, {"file": "graph_female.npz", "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"}], "synapse_mv": 0.275, "synapses_restored": 3327}, "state_cells": 4, "state_cells_per_type": {"AN_SMP_2": 2, "AN_FLA_SMP_2": 2, "ANXXX983": 0}}
Environment: {"brain_class": "flysim_gpu.FlyBrainGPU"}

## Per-dose verdicts
| Dose Hz | Prediction | Difference | SE | n | Verdict | Reversed | Established |
|---|---|---:|---:|---:|---|---|---|
| 200 - 20 song | P41 | -1.2322364373009065 | 0.47110952380176635 | 10 | not supported | True | False |
| 200 | P42_command | 0.595 | 2.193857586788876 | 10 | not supported | False | False |
| 200 | P42_rms | -0.002367944982403814 | 0.006698005205716163 | 10 | not supported | False | False |
| 200 | P43 | -1.7883139534883725 | 1.180617452450754 | 10 | not supported | False | False |
| 50 | P42_command | 1.4750000000000008 | 6.6954099119388415 | 10 | not supported | False | False |
| 50 | P42_rms | -0.0034592386538732567 | 0.014926970150658827 | 10 | not supported | False | False |
| 50 | P43 | -0.8422674418604652 | 1.2343914046891913 | 10 | not supported | False | False |
| 20 | P42_command | 5.977500000000001 | 9.463359494210641 | 10 | not supported | False | False |
| 20 | P42_rms | 0.0032784502711342344 | 0.013880208325539494 | 10 | not supported | False | False |
| 20 | P43 | -0.439011627906977 | 0.8938127635638894 | 10 | not supported | False | False |

## P44 per cell
| smell_dose_hz | condition | n | p1_hz | pip10_hz | delivered_rms | male_total_hz | vpodn_hz | distance_mm | approach | retreat | ignition_fraction | accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 200 | song | 10 | 1.76017 | 6.4575 | 0.0170872 | 41.8657 | 73.3375 | 9.89076 | 0.1 | 0.9 | 0.99925 | 10 |
| 200 | mute | 10 | 1.84703 | 5.8625 | 0.0194551 | 41.8203 | 73.3675 | 7.73738 | 0.5 | 0.5 | 0.99975 | 10 |
| 200 | noscent_orn | 10 | 3.54849 | 15.5025 | 0.0267661 | 22.6924 | 73.385 | 6.49271 | 0.5 | 0.5 | 0.504 | 10 |
| 50 | song | 10 | 2.70622 | 8.28 | 0.0182122 | 43.8479 | 72.925 | 7.65014 | 0.3 | 0.7 | 0.9895 | 10 |
| 50 | mute | 10 | 2.55128 | 6.805 | 0.0216714 | 42.9611 | 75.47 | 6.40611 | 0.4 | 0.6 | 0.98775 | 10 |
| 50 | noscent_orn | 10 | 3.54849 | 15.5025 | 0.0267661 | 22.6924 | 73.385 | 6.49271 | 0.5 | 0.5 | 0.504 | 10 |
| 20 | song | 10 | 3.10948 | 19.0225 | 0.0337038 | 43.0979 | 73.4975 | 7.08282 | 0.5 | 0.5 | 0.95625 | 10 |
| 20 | mute | 10 | 3.29558 | 13.045 | 0.0304254 | 40.8316 | 74.02 | 6.56849 | 0.2 | 0.8 | 0.919 | 10 |
| 20 | noscent_orn | 10 | 3.54849 | 15.5025 | 0.0267661 | 22.6924 | 73.385 | 6.49271 | 0.5 | 0.5 | 0.504 | 10 |

## Per-seed outcomes
| seed | smell_dose_hz | condition | p1_hz | pip10_hz | delivered_rms | male_total_hz | vpodn_hz | distance_mm | approach | retreat | ignition_fraction | accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 200 | song | 1.96453 | 1.35 | 0.00754297 | 43.2452 | 74 | 11.8146 | False | True | 1 | True |
| 0 | 200 | mute | 2.20581 | 7.025 | 0.0200745 | 42.9219 | 77.275 | 9.2942 | False | True | 1 | True |
| 0 | 200 | noscent_orn | 1.16047 | 1.725 | 0.00969744 | 10.3283 | 76.475 | 12.0203 | False | True | 0.235 | True |
| 0 | 50 | song | 1.18547 | 0 | 0 | 44.422 | 73.7 | 3.9539 | True | False | 0.995 | True |
| 0 | 50 | mute | 2.29651 | 2.35 | 0.0139978 | 43.2058 | 76.775 | 6.06732 | False | True | 0.98 | True |
| 0 | 50 | noscent_orn | 1.16047 | 1.725 | 0.00969744 | 10.3283 | 76.475 | 12.0203 | False | True | 0.235 | True |
| 0 | 20 | song | 3.0157 | 37.525 | 0.0670914 | 45.8218 | 74.75 | 4.6351 | False | True | 0.98 | True |
| 0 | 20 | mute | 3.55988 | 0.25 | 0.00250388 | 42.6522 | 79.125 | 7.39882 | False | True | 0.9375 | True |
| 0 | 20 | noscent_orn | 1.16047 | 1.725 | 0.00969744 | 10.3283 | 76.475 | 12.0203 | False | True | 0.235 | True |
| 1 | 200 | song | 2.01802 | 10.55 | 0.0210015 | 40.5019 | 76.375 | 7.7362 | False | True | 1 | True |
| 1 | 200 | mute | 1.76453 | 1.075 | 0.00616349 | 41.6955 | 74.325 | 8.3346 | False | True | 1 | True |
| 1 | 200 | noscent_orn | 7.26686 | 79.575 | 0.0838101 | 48.3217 | 72.6 | 6.49656 | True | False | 1 | True |
| 1 | 50 | song | 3.79884 | 4.675 | 0.018169 | 41.9787 | 75.975 | 6.64695 | True | False | 0.975 | True |
| 1 | 50 | mute | 1.52442 | 2.85 | 0.00621169 | 46.8897 | 76.55 | 9.70717 | False | True | 1 | True |
| 1 | 50 | noscent_orn | 7.26686 | 79.575 | 0.0838101 | 48.3217 | 72.6 | 6.49656 | True | False | 1 | True |
| 1 | 20 | song | 3.20988 | 3.15 | 0.0182808 | 44.0592 | 74.325 | 5.90056 | True | False | 0.98 | True |
| 1 | 20 | mute | 7.47267 | 62.1 | 0.0965175 | 44.0648 | 71.525 | 2.63725 | True | False | 0.9725 | True |
| 1 | 20 | noscent_orn | 7.26686 | 79.575 | 0.0838101 | 48.3217 | 72.6 | 6.49656 | True | False | 1 | True |
| 2 | 200 | song | 1.08198 | 0.65 | 0.00313959 | 40.4667 | 70.475 | 12.3848 | False | True | 0.9975 | True |
| 2 | 200 | mute | 1.78314 | 5.05 | 0.0175878 | 44.5321 | 70.2 | 7.57658 | False | True | 1 | True |
| 2 | 200 | noscent_orn | 0.901744 | 0.15 | 0.00218445 | 2.38407 | 70.675 | 6.11087 | False | True | 0.0525 | True |
| 2 | 50 | song | 6.02849 | 10.975 | 0.0156618 | 45.3225 | 73.25 | 11.8033 | False | True | 1 | True |
| 2 | 50 | mute | 1.06279 | 4.525 | 0.0118096 | 40.0783 | 69.85 | 11.0243 | False | True | 0.9625 | True |
| 2 | 50 | noscent_orn | 0.901744 | 0.15 | 0.00218445 | 2.38407 | 70.675 | 6.11087 | False | True | 0.0525 | True |
| 2 | 20 | song | 3.02849 | 17.85 | 0.0514867 | 42.9008 | 71.95 | 6.78545 | False | True | 0.9825 | True |
| 2 | 20 | mute | 1.54767 | 2.85 | 0.014937 | 38.5134 | 69.45 | 5.23447 | False | True | 0.8675 | True |
| 2 | 20 | noscent_orn | 0.901744 | 0.15 | 0.00218445 | 2.38407 | 70.675 | 6.11087 | False | True | 0.0525 | True |
| 3 | 200 | song | 1.61163 | 9.075 | 0.0230673 | 40.8162 | 73.55 | 8.10522 | False | True | 1 | True |
| 3 | 200 | mute | 1.06628 | 7.175 | 0.0287313 | 41.1327 | 73.175 | 3.13429 | True | False | 1 | True |
| 3 | 200 | noscent_orn | 4.81105 | 15.4 | 0.0419414 | 42.7355 | 70.45 | 3.51083 | True | False | 0.98 | True |
| 3 | 50 | song | 1.40349 | 0.275 | 0.00233245 | 45.1884 | 71.35 | 4.3746 | True | False | 0.995 | True |
| 3 | 50 | mute | 1.84593 | 46.9 | 0.12606 | 41.976 | 78.95 | 2.74481 | True | False | 0.99 | True |
| 3 | 50 | noscent_orn | 4.81105 | 15.4 | 0.0419414 | 42.7355 | 70.45 | 3.51083 | True | False | 0.98 | True |
| 3 | 20 | song | 2.61337 | 5.125 | 0.019576 | 43.545 | 72.625 | 6.06711 | True | False | 0.9675 | True |
| 3 | 20 | mute | 3.20233 | 0 | 0 | 43.3916 | 73.725 | 4.84717 | False | True | 0.9825 | True |
| 3 | 20 | noscent_orn | 4.81105 | 15.4 | 0.0419414 | 42.7355 | 70.45 | 3.51083 | True | False | 0.98 | True |
| 4 | 200 | song | 1.28081 | 14.275 | 0.0487382 | 40.893 | 74.6 | 9.73285 | False | True | 0.9975 | True |
| 4 | 200 | mute | 1.27791 | 7.55 | 0.0251018 | 41.3154 | 73.975 | 7.19706 | True | False | 1 | True |
| 4 | 200 | noscent_orn | 0.601163 | 0.55 | 0.00396048 | 1.48897 | 74.925 | 6.95667 | True | False | 0.0375 | True |
| 4 | 50 | song | 2.09942 | 1.25 | 0.00697854 | 42.3415 | 75.975 | 12.2472 | False | True | 0.9925 | True |
| 4 | 50 | mute | 1.20581 | 0.575 | 0.0052355 | 42.553 | 76.65 | 8.21923 | False | True | 0.9825 | True |
| 4 | 50 | noscent_orn | 0.601163 | 0.55 | 0.00396048 | 1.48897 | 74.925 | 6.95667 | True | False | 0.0375 | True |
| 4 | 20 | song | 1.26919 | 4.9 | 0.0186223 | 40.1557 | 76.075 | 5.38481 | True | False | 0.91 | True |
| 4 | 20 | mute | 2.49709 | 27.9 | 0.0748899 | 37.7999 | 74.85 | 5.68258 | False | True | 0.8525 | True |
| 4 | 20 | noscent_orn | 0.601163 | 0.55 | 0.00396048 | 1.48897 | 74.925 | 6.95667 | True | False | 0.0375 | True |
| 5 | 200 | song | 1.12907 | 3.625 | 0.0160443 | 42.0436 | 72.925 | 8.70616 | False | True | 1 | True |
| 5 | 200 | mute | 1.32616 | 2.85 | 0.00866263 | 41.366 | 73.9 | 11.0144 | False | True | 1 | True |
| 5 | 200 | noscent_orn | 5.49651 | 1.1 | 0.00984706 | 18.0757 | 76.05 | 7.79253 | False | True | 0.4 | True |
| 5 | 50 | song | 2.02907 | 21.475 | 0.0620944 | 43.762 | 70.175 | 8.4896 | False | True | 0.9925 | True |
| 5 | 50 | mute | 5.18779 | 3.9 | 0.014198 | 41.3508 | 76.625 | 5.09394 | True | False | 0.985 | True |
| 5 | 50 | noscent_orn | 5.49651 | 1.1 | 0.00984706 | 18.0757 | 76.05 | 7.79253 | False | True | 0.4 | True |
| 5 | 20 | song | 2.45349 | 14.975 | 0.020368 | 41.5973 | 72.9 | 11.6177 | False | True | 0.935 | True |
| 5 | 20 | mute | 2.21919 | 6.05 | 0.0267814 | 41.7304 | 77.825 | 7.72021 | False | True | 0.9525 | True |
| 5 | 20 | noscent_orn | 5.49651 | 1.1 | 0.00984706 | 18.0757 | 76.05 | 7.79253 | False | True | 0.4 | True |
| 6 | 200 | song | 2.56802 | 7.1 | 0.0062105 | 40.803 | 70.5 | 12.8167 | False | True | 0.9975 | True |
| 6 | 200 | mute | 4.31279 | 20.975 | 0.0560105 | 42.4486 | 70.65 | 2.48891 | True | False | 1 | True |
| 6 | 200 | noscent_orn | 0.484884 | 0.025 | 8.52769e-05 | 1.07945 | 72.975 | 6.60877 | False | True | 0.025 | True |
| 6 | 50 | song | 2.77442 | 0 | 0 | 42.3662 | 75.025 | 6.9094 | False | True | 0.9825 | True |
| 6 | 50 | mute | 0.78314 | 0.8 | 0.00558748 | 44.0185 | 70.6 | 3.92564 | True | False | 0.9975 | True |
| 6 | 50 | noscent_orn | 0.484884 | 0.025 | 8.52769e-05 | 1.07945 | 72.975 | 6.60877 | False | True | 0.025 | True |
| 6 | 20 | song | 1.96512 | 1.8 | 0.00757625 | 41.9814 | 73.85 | 5.53192 | True | False | 0.925 | True |
| 6 | 20 | mute | 1.46686 | 7.225 | 0.0225327 | 38.0413 | 73.4 | 5.52265 | False | True | 0.915 | True |
| 6 | 20 | noscent_orn | 0.484884 | 0.025 | 8.52769e-05 | 1.07945 | 72.975 | 6.60877 | False | True | 0.025 | True |
| 7 | 200 | song | 1.68779 | 9.25 | 0.0267164 | 41.7033 | 69.875 | 6.23791 | True | False | 1 | True |
| 7 | 200 | mute | 1.39593 | 2.975 | 0.0120749 | 40.5997 | 71.975 | 6.57514 | True | False | 1 | True |
| 7 | 200 | noscent_orn | 11.3965 | 48.95 | 0.086737 | 39.1148 | 72.95 | 3.40326 | False | True | 0.855 | True |
| 7 | 50 | song | 2.9064 | 2.95 | 0.0142932 | 44.1886 | 73.3 | 6.21472 | False | True | 0.99 | True |
| 7 | 50 | mute | 6.85407 | 2.95 | 0.011418 | 45.9675 | 74.225 | 8.0957 | False | True | 1 | True |
| 7 | 50 | noscent_orn | 11.3965 | 48.95 | 0.086737 | 39.1148 | 72.95 | 3.40326 | False | True | 0.855 | True |
| 7 | 20 | song | 6.47151 | 45.7 | 0.0645938 | 42.0652 | 75.5 | 7.61403 | False | True | 0.9525 | True |
| 7 | 20 | mute | 1.60698 | 12.05 | 0.0318268 | 40.905 | 71.475 | 7.52929 | False | True | 0.8925 | True |
| 7 | 20 | noscent_orn | 11.3965 | 48.95 | 0.086737 | 39.1148 | 72.95 | 3.40326 | False | True | 0.855 | True |
| 8 | 200 | song | 2.90698 | 2.575 | 0.0135149 | 42.0721 | 75.925 | 9.78368 | False | True | 1 | True |
| 8 | 200 | mute | 1.65 | 1.375 | 0.00525344 | 41.1131 | 75.55 | 13.39 | False | True | 1 | True |
| 8 | 200 | noscent_orn | 1.99767 | 5.3 | 0.0174493 | 41.7072 | 73.6 | 6.16893 | True | False | 0.96 | True |
| 8 | 50 | song | 3.63663 | 40.5 | 0.0571663 | 46.3246 | 69.975 | 8.19209 | False | True | 0.9975 | True |
| 8 | 50 | mute | 2.55465 | 1.5 | 0.0109083 | 43.7158 | 77.475 | 5.44986 | False | True | 1 | True |
| 8 | 50 | noscent_orn | 1.99767 | 5.3 | 0.0174493 | 41.7072 | 73.6 | 6.16893 | True | False | 0.96 | True |
| 8 | 20 | song | 2.96337 | 44.225 | 0.0259809 | 42.4725 | 69.825 | 11.9618 | False | True | 0.93 | True |
| 8 | 20 | mute | 3.42326 | 6.175 | 0.0208809 | 41.1738 | 75.85 | 6.84398 | True | False | 0.915 | True |
| 8 | 20 | noscent_orn | 1.99767 | 5.3 | 0.0174493 | 41.7072 | 73.6 | 6.16893 | True | False | 0.96 | True |
| 9 | 200 | song | 1.35291 | 6.125 | 0.00489607 | 46.112 | 75.15 | 11.5895 | False | True | 1 | True |
| 9 | 200 | mute | 1.68779 | 2.575 | 0.0148909 | 41.0775 | 72.65 | 8.3686 | True | False | 0.9975 | True |
| 9 | 200 | noscent_orn | 1.36802 | 2.25 | 0.0119483 | 21.6887 | 73.15 | 5.85835 | True | False | 0.495 | True |
| 9 | 50 | song | 1.2 | 0.7 | 0.00542592 | 42.5848 | 70.525 | 7.66964 | False | True | 0.975 | True |
| 9 | 50 | mute | 2.19767 | 1.7 | 0.011288 | 39.8552 | 77 | 3.73315 | True | False | 0.98 | True |
| 9 | 50 | noscent_orn | 1.36802 | 2.25 | 0.0119483 | 21.6887 | 73.15 | 5.85835 | True | False | 0.495 | True |
| 9 | 20 | song | 4.10465 | 14.975 | 0.0434623 | 46.3805 | 73.175 | 5.32963 | True | False | 1 | True |
| 9 | 20 | mute | 5.95988 | 5.85 | 0.0133839 | 40.0438 | 72.975 | 12.2685 | False | True | 0.9025 | True |
| 9 | 20 | noscent_orn | 1.36802 | 2.25 | 0.0119483 | 21.6887 | 73.15 | 5.85835 | True | False | 0.495 | True |

## Result
P41: not established.
P42: not established.
P43: not established.
P41 song total-rate difference, 200 minus 20: -1.2322364373009065 Hz per neuron.
Dose 200 Hz: song minus mute pIP10 = 0.595 Hz, RMS = -0.002367944982403814; song minus noscent_orn P1 = -1.7883139534883725 Hz.
P42_rms at 200 Hz has a negative mean: descriptive sign reversal only.
P43 at 200 Hz has a negative mean: descriptive sign reversal only.
Dose 50 Hz: song minus mute pIP10 = 1.4750000000000008 Hz, RMS = -0.0034592386538732567; song minus noscent_orn P1 = -0.8422674418604652 Hz.
P42_rms at 50 Hz has a negative mean: descriptive sign reversal only.
P43 at 50 Hz has a negative mean: descriptive sign reversal only.
Dose 20 Hz: song minus mute pIP10 = 5.977500000000001 Hz, RMS = 0.0032784502711342344; song minus noscent_orn P1 = -0.439011627906977 Hz.
P43 at 20 Hz has a negative mean: descriptive sign reversal only.
Ten-seed paired experiment.
Estimated ten-seed cost: 2.55388 hours, excluding setup/rendering.

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
- Olfactory dose is a chosen input rate, not a measured pheromone concentration; the distance falloff is chosen.
- The 30 Hz per-neuron ignition threshold is chosen, not a measured transition.
- Three fixed doses are compared without a multiplicity correction; paired significance does not identify a unique circuit mechanism.
