# Courtship v10

## Calibration/design record
Protocol v10: he adapts, a pre-registered intervention.
CHOSEN: ten seeds, 400 steps, paired by seed and start; quick = two seeds x 80 steps (one seed allowed for CPU budget).
Female = v8: required own restored SAG graph, virgin SAG 50 Hz, positive-weight scale 0.7.
Male positive-weight scale is required via --male-scale, a chosen dose from v9; no default.
CHOSEN: LC10A_HZ_MAX = 100.0 Hz; SIZE_FULL = 28.0724869359 degrees, the vertical angular diameter at 2 mm for the room's 1 mm body height.
Use ellipse_of ry_raw / px_per_deg x 2 (unfloored vertical angular diameter). Drive = 100 x clip(size / SIZE_FULL, 0, 1).
Sight: drive each LC10a cell by soma_side while her centre bearing is in the front field (+/-90 degrees, boundaries included); positive bearing drives left, negative right, both within +/-10 degrees. Behind = zero.
Blind: no LC10a drive. His v5 eye, including grey flooding, stays the same in all conditions.
Shuffled: run sight first; replay its left/right drive pairs using numpy default_rng(SeedSequence([seed, 1025])).permutation, with an identity permutation rotated once. Preserve each cell's total drive, break the temporal link to current geometry.
Drive scalar for P26 = mean input Hz across all LC10a cells, including the zero side. Record both side rates and replay indices.
P25 the drive lands: LC10a mean rate, sight > blind (intervention check, not vision).
P26 he adapts: Spearman rho(m_neural[t], drive[t-1]) and rho(a_neural[t], drive[t-1]), sight > shuffled; at least one channel must pass, both reported.
P27 he turns toward her: fraction of all windows where his heading change reduces absolute bearing to her pre-window position, sight > blind. Zero turns do not count; translations are excluded.
P28 descriptive: pIP10, delivered RMS, her vpoDN and accept; mean distance, approach and retreat per condition and seed.
Predictions fixed before data: paired difference > 2 SE, n=10, as v5. Missing/constant correlations are undefined, excluded as pairs; fewer than ten valid pairs cannot establish a prediction. Quick comparisons are smoke evidence only.

CHOSEN male positive-weight scale: 0.9.
Female graph record: {"file": "graph_female_own_sag.npz", "path": "build/graph_female_own_sag.npz", "sha256": "f2452ec31b830931c01a3985ed8e6cbf61264a76e37f70337e57b2ece2fcb02a", "restore": {"csv_rows": 5342446, "empty_types": [], "excluded_synapses": 0, "floor": 5, "mapping": "individual female pre/post ids; pair sum >= 5; post cell must be in graph", "per_target_type": [{"by_source_type": {"AN_FLA_SMP_2": 76, "AN_SMP_2": 539}, "synapses": 615, "target_type": "pC1a"}, {"by_source_type": {"AN_FLA_SMP_2": 558, "AN_SMP_2": 10}, "synapses": 568, "target_type": "CB0959"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 387}, "synapses": 387, "target_type": "pC1b"}, {"by_source_type": {"AN_FLA_SMP_2": 291, "AN_SMP_2": 6}, "synapses": 297, "target_type": "CB0699"}, {"by_source_type": {"AN_FLA_SMP_2": 195, "AN_SMP_2": 0}, "synapses": 195, "target_type": ""}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 179}, "synapses": 179, "target_type": "pC1c"}, {"by_source_type": {"AN_FLA_SMP_2": 168, "AN_SMP_2": 5}, "synapses": 173, "target_type": "SMP094"}, {"by_source_type": {"AN_FLA_SMP_2": 149, "AN_SMP_2": 0}, "synapses": 149, "target_type": "CB1024"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 128}, "synapses": 134, "target_type": "CB0094"}, {"by_source_type": {"AN_FLA_SMP_2": 114, "AN_SMP_2": 0}, "synapses": 114, "target_type": "AN_SMP_1"}, {"by_source_type": {"AN_FLA_SMP_2": 78, "AN_SMP_2": 0}, "synapses": 78, "target_type": "CB0075"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 60}, "synapses": 60, "target_type": "CB0405"}, {"by_source_type": {"AN_FLA_SMP_2": 54, "AN_SMP_2": 0}, "synapses": 54, "target_type": "PAL01"}, {"by_source_type": {"AN_FLA_SMP_2": 52, "AN_SMP_2": 0}, "synapses": 52, "target_type": "SMP025a"}, {"by_source_type": {"AN_FLA_SMP_2": 21, "AN_SMP_2": 17}, "synapses": 38, "target_type": "SMP286"}, {"by_source_type": {"AN_FLA_SMP_2": 31, "AN_SMP_2": 0}, "synapses": 31, "target_type": "SMP172"}, {"by_source_type": {"AN_FLA_SMP_2": 19, "AN_SMP_2": 7}, "synapses": 26, "target_type": "AN_FLA_SMP_2"}, {"by_source_type": {"AN_FLA_SMP_2": 17, "AN_SMP_2": 8}, "synapses": 25, "target_type": "pC1e"}, {"by_source_type": {"AN_FLA_SMP_2": 15, "AN_SMP_2": 0}, "synapses": 15, "target_type": "CB1610"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 11}, "synapses": 11, "target_type": "CB1371"}, {"by_source_type": {"AN_FLA_SMP_2": 11, "AN_SMP_2": 0}, "synapses": 11, "target_type": "CB2165"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 5}, "synapses": 11, "target_type": "NPFL1-I"}, {"by_source_type": {"AN_FLA_SMP_2": 10, "AN_SMP_2": 0}, "synapses": 10, "target_type": "SMP538"}, {"by_source_type": {"AN_FLA_SMP_2": 9, "AN_SMP_2": 0}, "synapses": 9, "target_type": "SMP513"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 8}, "synapses": 8, "target_type": "CB4204"}, {"by_source_type": {"AN_FLA_SMP_2": 8, "AN_SMP_2": 0}, "synapses": 8, "target_type": "SMP515"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "FLA101f_c"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SIP076"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SMP123b"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "CB4233"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "SMP034"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "pC1d"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "AN_SMP_FLA_1"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB0015"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB2422"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "DNpe034"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 5}, "synapses": 5, "target_type": "SMP161"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "SMP593"}], "per_type": {"AN_FLA_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 1033, "restored_synapses": 1033, "root_id": 720575940614614162}, {"exported_synapses": 919, "restored_synapses": 919, "root_id": 720575940638396998}], "exported_synapses": 1952, "restored_synapses": 1952}, "AN_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 690, "restored_synapses": 690, "root_id": 720575940623363000}, {"exported_synapses": 685, "restored_synapses": 685, "root_id": 720575940631004202}], "exported_synapses": 1375, "restored_synapses": 1375}}, "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; the BANC prediction for the same types is dopamine. Neither prediction fixes the sign of the effect.", "sources": [{"file": "connections_princeton.csv.gz", "sha256": "445f996bf6c4b1803b9ba186189138a3061ff8623aa94c0abcf38af30a5bd48b"}, {"file": "graph_female.npz", "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"}], "synapse_mv": 0.275, "synapses_restored": 3327}, "state_cells": 4, "state_cells_per_type": {"AN_SMP_2": 2, "AN_FLA_SMP_2": 2, "ANXXX983": 0}}

## Verdicts
| Prediction | Difference | SE | n | >2 SE comparison | Established (n=10) |
|---|---:|---:|---:|---|---|
| P25 | 14.302200000000003 | 2.4221561468995487 | 10 | supported | True |
| P26_a | 0.006174308335808581 | 0.03389053668709058 | 10 | not supported | False |
| P26_m | -0.010538647613415624 | 0.04198129671540688 | 10 | not supported | False |
| P27 | -0.008500000000000013 | 0.008098353742170895 | 10 | not supported | False |

## Per-seed outcomes and P28 (descriptive)
| seed | condition | lc10a_hz | a_neural_drive_lagged_rho | m_neural_drive_lagged_rho | turn_toward_fraction | pip10_hz | delivered_rms | vpodn_hz | accept | distance_mm | approach | retreat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | sight | 7.42255 | 0.100327 | 0.139419 | 0.415 | 0.525 | 0.00364218 | 71.3 | True | 5.51386 | True | False |
| 0 | blind | 0.0587273 | None | None | 0.3825 | 12.45 | 0.0338693 | 72.625 | True | 9.31193 | True | False |
| 0 | shuffled | 7.35945 | -0.00803623 | -0.0104665 | 0.28 | 6.775 | 0.00962447 | 75.65 | True | 12.2207 | False | True |
| 1 | sight | 28.3542 | 0.0859432 | -0.0532063 | 0.38 | 9.25 | 0.0298045 | 74.225 | True | 3.67774 | True | False |
| 1 | blind | 0.0730909 | None | None | 0.3975 | 7.175 | 0.0271281 | 72.05 | True | 7.51075 | True | False |
| 1 | shuffled | 28.4256 | -0.019652 | -0.0347683 | 0.335 | 2.9 | 0.0124576 | 73.8 | True | 8.74268 | False | True |
| 2 | sight | 18.1949 | 0.0111837 | -0.145152 | 0.39 | 2.9 | 0.0128898 | 72.975 | True | 4.22957 | True | False |
| 2 | blind | 0.113818 | None | None | 0.39 | 1.3 | 0.00805192 | 70.025 | True | 5.64803 | True | False |
| 2 | shuffled | 18.3409 | 0.0442443 | -0.032693 | 0.3625 | 2.25 | 0.0081102 | 72.45 | True | 10.704 | False | True |
| 3 | sight | 10.9493 | -0.126344 | 0.064173 | 0.38 | 33.875 | 0.0683265 | 75.875 | True | 6.09384 | False | True |
| 3 | blind | 0.0796364 | None | None | 0.39 | 2.1 | 0.0127491 | 72.325 | True | 8.76727 | True | False |
| 3 | shuffled | 11.0047 | 0.0721723 | -0.0183935 | 0.3825 | 9.1 | 0.0195176 | 73.275 | True | 5.22933 | True | False |
| 4 | sight | 19.1209 | 0.0865271 | -0.10804 | 0.3975 | 11.025 | 0.0389816 | 75.775 | True | 3.5275 | True | False |
| 4 | blind | 0.102364 | None | None | 0.385 | 4.25 | 0.0117637 | 79.725 | True | 8.54561 | True | False |
| 4 | shuffled | 19.1751 | -0.00368732 | -0.101455 | 0.39 | 4.55 | 0.0177758 | 74.95 | True | 5.99527 | True | False |
| 5 | sight | 13.468 | 0.0779843 | -0.168683 | 0.3575 | 7.875 | 0.0308531 | 75.775 | True | 6.03559 | True | False |
| 5 | blind | 0.0389091 | None | None | 0.3325 | 1.4 | 0.0121265 | 74.375 | True | 7.68641 | False | True |
| 5 | shuffled | 13.4596 | -0.00682984 | 0.0411089 | 0.385 | 3.2 | 0.0169055 | 75.9 | True | 4.59623 | True | False |
| 6 | sight | 7.14236 | -0.0296189 | 0.158761 | 0.3675 | 6.65 | 0.0209759 | 71.15 | True | 7.8025 | False | True |
| 6 | blind | 0.0752727 | None | None | 0.3875 | 2.25 | 0.0077861 | 74.7 | True | 6.72231 | True | False |
| 6 | shuffled | 7.18673 | -0.00698098 | -0.00542378 | 0.42 | 7.9 | 0.0273232 | 72.425 | True | 2.95803 | True | False |
| 7 | sight | 6.23527 | 0.0584088 | -0.151137 | 0.3925 | 0.275 | 0.00250821 | 74.35 | True | 9.73207 | False | True |
| 7 | blind | 0.396182 | None | None | 0.425 | 0.4 | 0.00485403 | 74.15 | True | 8.72608 | False | True |
| 7 | shuffled | 6.29091 | 0.0763788 | -0.0600579 | 0.3625 | 3.725 | 0.00856846 | 68.8 | True | 10.5447 | False | True |
| 8 | sight | 23.8136 | -0.0604001 | -0.168685 | 0.355 | 7.575 | 0.0265173 | 75.625 | True | 3.71776 | True | False |
| 8 | blind | 0.155455 | None | None | 0.4 | 4.875 | 0.0204624 | 77.175 | True | 9.48897 | False | True |
| 8 | shuffled | 23.6613 | 0.0736062 | -0.00245305 | 0.3525 | 5.1 | 0.017712 | 76.175 | True | 7.93321 | True | False |
| 9 | sight | 9.54164 | 0.198974 | -0.0073417 | 0.3675 | 5.5 | 0.0202915 | 76.225 | True | 6.97317 | True | False |
| 9 | blind | 0.127273 | None | None | 0.3975 | 1.55 | 0.00951407 | 75.65 | True | 4.65483 | True | False |
| 9 | shuffled | 9.54109 | 0.120027 | -0.109902 | 0.4025 | 22.675 | 0.0598392 | 74.7 | True | 3.12731 | True | False |

## Result
P25: established. P27: not established.
P26: not established; qualifying channels: none. Both a and m are reported above.
Ten-seed design; undefined pairs cannot establish a prediction.

## Limitations
- LC10a measured-geometry drive replaces the visual pathway with chosen constants; it does not validate the native lamina-to-LC10a pathway. His eye still floods on grey.
- The male scale is a chosen dose from v9; the quick-run dose 0.9 is a smoke-test choice, not a sweep-selected final dose.
- The old m_lc10a_lagged_rho compares rendered m[t] from neural window t-1 with LC10a[t-1], so it does not measure a one-window neural lag. Legacy fields remain unchanged; new neural fields use current rates against previous-window LC10a.
- P26 tests either of two reported correlations with the specified >2 SE rule, without multiplicity adjustment. Correlation is not a learned adaptation mechanism.
- Angular size uses the unfloored vertical diameter; bearing and size vary with movement, but no separate motion gain is added.
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
