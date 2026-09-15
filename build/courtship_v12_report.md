# Courtship v12

Protocol v12. Identical to v9 except the required functional-sign male graph and scales {0.9, 0.8}.
CHOSEN: 0.9 is the v10/v11 dose; 0.8 is the neighbour where v9's RMS comparison passed while the pIP10 difference sat just under threshold.
Ten paired seeds, 400 steps, six scale/condition cells; quick = two seeds x 80 steps (explicit --seeds 1 permitted).
Male build/graph_male_fsign.npz: dictionary vAB3 sign +1; mAL unclear sign -1. Record graph SHA256 and override table.
Hypothesis: these narrow functional-sign corrections recover P1 control of song and its response to her scent.
Risk: vAB3 to mAL input exceeds direct vAB3 to P1 input in this map, so restoring mAL inhibition may lower P1 rather than raise it.
A null means this narrow correction does not recover P1 control at these doses, not that the pathway is absent.
Female side = v8: own restored SAG graph, both SAG types, virgin 50 Hz, positive-weight scale 0.7, blind eye.
Positive male weights alone are scaled before room construction and restored between trials. Conditions song/mute/noscent and all remaining v9 settings retained; starts paired across all scales and conditions.
- P33 the command carries the song under the functional signs: his pIP10 mean rate and delivered RMS, song > mute (both).
- P34 he notices her under the functional signs: his P1 mean rate, song > noscent.
- P35 (descriptive): P1, pIP10, RMS, male total rate per scale; mAL and vAB3 mean rates per condition (record both groups); her vpoDN and accept per cell.
Verdict rule per scale as v5: paired difference > 2 SE, n = 10. A step counts as established only if it holds at at least one scale AND the direction is not reversed (difference < -2 SE) at any other scale in the sweep; report every scale. P33 requires both comparisons at the same scale; reversal of either comparison at any scale prevents establishment. Quick runs are smoke tests and cannot establish a step.

## Override record
{
  "path": "build/graph_male_fsign.npz",
  "sha256": "17b13e662088b3bfa42c4bed7da60af53eb3f08b85ce66e5aeb9a43ad6e150b5",
  "fsign": {
    "overrides": [
      {
        "group": "vAB3",
        "transmitter": null,
        "sign": 1.0,
        "rationale": "CHOSEN: functional excitation of P1; applied to all dictionary vAB3 outputs",
        "citation": "Clowney et al. 2015 Neuron 87:1036-1049, https://doi.org/10.1016/j.neuron.2015.07.025",
        "selected_cells": 6,
        "changed_cells": 6,
        "bodies": [
          11998,
          13341,
          13693,
          14320,
          512498,
          922722
        ],
        "indices": [
          1868,
          3126,
          3445,
          4009,
          124685,
          162530
        ],
        "edges": 1789,
        "synapses": 34809,
        "action": "flipped"
      },
      {
        "group": "mAL",
        "transmitter": "unclear",
        "sign": -1.0,
        "rationale": "CHOSEN: restore the known GABAergic group sign only for unclear cells",
        "citation": "Clowney et al. 2015 Neuron 87:1036-1049, https://doi.org/10.1016/j.neuron.2015.07.025",
        "selected_cells": 23,
        "changed_cells": 23,
        "bodies": [
          11147,
          13701,
          15604,
          15618,
          20215,
          20771,
          30116,
          34612,
          38290,
          38743,
          46697,
          71416,
          84395,
          369210,
          513126,
          514411,
          515272,
          515541,
          517048,
          518673,
          519905,
          535834,
          539322
        ],
        "indices": [
          1060,
          3452,
          5153,
          5166,
          9282,
          9777,
          18128,
          22069,
          25327,
          25719,
          32731,
          53496,
          63946,
          123452,
          125008,
          125749,
          126234,
          126384,
          127294,
          128251,
          128972,
          135576,
          136462
        ],
        "edges": 2081,
        "synapses": 17169,
        "action": "added"
      }
    ],
    "source_sha256s": {
      "connectome-weights.feather": "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1",
      "body-neurotransmitters.feather": "95c9289220663abeb3409f3ad9e5a7f8a53f8093f5139d15502cd08da8879621",
      "body-annotations.feather": "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2",
      "build_graph.py": "07c9859f8a6799483b9d94f8c5bc165fe3a98cc1503b764bf5ded51fffc27a9c",
      "backrooms_dictionary.py": "02209ed39d6702984a510221ed9efaad725e8216013b0a885406cced090f97ac",
      "functional_sign.py": "e0f718b25333e89c0102ccbd05e784169f584b0576084cb8e418fa521bf1ab94",
      "graph.npz": "5a6e6fbfa5f2d3840218cb32cc0182828829c9212b483ce771cfea7718a7b947"
    },
    "outside_columns_max_abs_diff": 0.0,
    "vab3_target_synapses": {
      "mAL": 11508,
      "P1": 1111
    },
    "original_zero_sign_cells": 4143,
    "cells": 165122,
    "min_syn": 3,
    "mv_per_synapse": 0.275
  }
}
## Female graph record
{"file": "graph_female_own_sag.npz", "path": "build/graph_female_own_sag.npz", "sha256": "f2452ec31b830931c01a3985ed8e6cbf61264a76e37f70337e57b2ece2fcb02a", "restore": {"csv_rows": 5342446, "empty_types": [], "excluded_synapses": 0, "floor": 5, "mapping": "individual female pre/post ids; pair sum >= 5; post cell must be in graph", "per_target_type": [{"by_source_type": {"AN_FLA_SMP_2": 76, "AN_SMP_2": 539}, "synapses": 615, "target_type": "pC1a"}, {"by_source_type": {"AN_FLA_SMP_2": 558, "AN_SMP_2": 10}, "synapses": 568, "target_type": "CB0959"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 387}, "synapses": 387, "target_type": "pC1b"}, {"by_source_type": {"AN_FLA_SMP_2": 291, "AN_SMP_2": 6}, "synapses": 297, "target_type": "CB0699"}, {"by_source_type": {"AN_FLA_SMP_2": 195, "AN_SMP_2": 0}, "synapses": 195, "target_type": ""}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 179}, "synapses": 179, "target_type": "pC1c"}, {"by_source_type": {"AN_FLA_SMP_2": 168, "AN_SMP_2": 5}, "synapses": 173, "target_type": "SMP094"}, {"by_source_type": {"AN_FLA_SMP_2": 149, "AN_SMP_2": 0}, "synapses": 149, "target_type": "CB1024"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 128}, "synapses": 134, "target_type": "CB0094"}, {"by_source_type": {"AN_FLA_SMP_2": 114, "AN_SMP_2": 0}, "synapses": 114, "target_type": "AN_SMP_1"}, {"by_source_type": {"AN_FLA_SMP_2": 78, "AN_SMP_2": 0}, "synapses": 78, "target_type": "CB0075"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 60}, "synapses": 60, "target_type": "CB0405"}, {"by_source_type": {"AN_FLA_SMP_2": 54, "AN_SMP_2": 0}, "synapses": 54, "target_type": "PAL01"}, {"by_source_type": {"AN_FLA_SMP_2": 52, "AN_SMP_2": 0}, "synapses": 52, "target_type": "SMP025a"}, {"by_source_type": {"AN_FLA_SMP_2": 21, "AN_SMP_2": 17}, "synapses": 38, "target_type": "SMP286"}, {"by_source_type": {"AN_FLA_SMP_2": 31, "AN_SMP_2": 0}, "synapses": 31, "target_type": "SMP172"}, {"by_source_type": {"AN_FLA_SMP_2": 19, "AN_SMP_2": 7}, "synapses": 26, "target_type": "AN_FLA_SMP_2"}, {"by_source_type": {"AN_FLA_SMP_2": 17, "AN_SMP_2": 8}, "synapses": 25, "target_type": "pC1e"}, {"by_source_type": {"AN_FLA_SMP_2": 15, "AN_SMP_2": 0}, "synapses": 15, "target_type": "CB1610"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 11}, "synapses": 11, "target_type": "CB1371"}, {"by_source_type": {"AN_FLA_SMP_2": 11, "AN_SMP_2": 0}, "synapses": 11, "target_type": "CB2165"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 5}, "synapses": 11, "target_type": "NPFL1-I"}, {"by_source_type": {"AN_FLA_SMP_2": 10, "AN_SMP_2": 0}, "synapses": 10, "target_type": "SMP538"}, {"by_source_type": {"AN_FLA_SMP_2": 9, "AN_SMP_2": 0}, "synapses": 9, "target_type": "SMP513"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 8}, "synapses": 8, "target_type": "CB4204"}, {"by_source_type": {"AN_FLA_SMP_2": 8, "AN_SMP_2": 0}, "synapses": 8, "target_type": "SMP515"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "FLA101f_c"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SIP076"}, {"by_source_type": {"AN_FLA_SMP_2": 7, "AN_SMP_2": 0}, "synapses": 7, "target_type": "SMP123b"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "CB4233"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "SMP034"}, {"by_source_type": {"AN_FLA_SMP_2": 6, "AN_SMP_2": 0}, "synapses": 6, "target_type": "pC1d"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "AN_SMP_FLA_1"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB0015"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "CB2422"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "DNpe034"}, {"by_source_type": {"AN_FLA_SMP_2": 0, "AN_SMP_2": 5}, "synapses": 5, "target_type": "SMP161"}, {"by_source_type": {"AN_FLA_SMP_2": 5, "AN_SMP_2": 0}, "synapses": 5, "target_type": "SMP593"}], "per_type": {"AN_FLA_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 1033, "restored_synapses": 1033, "root_id": 720575940614614162}, {"exported_synapses": 919, "restored_synapses": 919, "root_id": 720575940638396998}], "exported_synapses": 1952, "restored_synapses": 1952}, "AN_SMP_2": {"cell_count": 2, "cells": [{"exported_synapses": 690, "restored_synapses": 690, "root_id": 720575940623363000}, {"exported_synapses": 685, "restored_synapses": 685, "root_id": 720575940631004202}], "exported_synapses": 1375, "restored_synapses": 1375}}, "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; the BANC prediction for the same types is dopamine. Neither prediction fixes the sign of the effect.", "sources": [{"file": "connections_princeton.csv.gz", "sha256": "445f996bf6c4b1803b9ba186189138a3061ff8623aa94c0abcf38af30a5bd48b"}, {"file": "graph_female.npz", "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"}], "synapse_mv": 0.275, "synapses_restored": 3327}, "state_cells": 4, "state_cells_per_type": {"AN_SMP_2": 2, "AN_FLA_SMP_2": 2, "ANXXX983": 0}}

## Per-scale verdicts
| Scale | Prediction | Difference | SE | n | Verdict | Reversed |
|---|---|---|---|---|---|---|
| 0.9 | P33_command | 1.1025 | 2.737997671657155 | 10 | not supported | False |
| 0.9 | P33_rms | 0.004528023854110952 | 0.006029471315250528 | 10 | not supported | False |
| 0.9 | P34 | -1.4493023255813955 | 1.0293110923040225 | 10 | not supported | False |
P33 joint at 0.9: not supported.
| 0.8 | P33_command | 3.0474999999999994 | 2.2487078079545046 | 10 | not supported | False |
| 0.8 | P33_rms | 0.0019284481616694271 | 0.002379220490757609 | 10 | not supported | False |
| 0.8 | P34 | -2.065813953488372 | 0.35413483616069347 | 10 | not supported | True |
P33 joint at 0.8: not supported.

## Per-seed outcomes
Per-trial outcome (CHOSEN, disclosed): `accept` = her vpoDN window rate exceeds 0 Hz in at least `ACCEPT_WINDOWS` = 3 windows of the trial; `approach` = mean distance in the last quarter of the trial is smaller than in the first quarter; `retreat` = the opposite. Report all three per seed and per condition in a table in the JSON and in the report; never only the pooled mean.
| male_exc_scale | seed | condition | p1_hz | pip10_hz | delivered_rms | male_total_hz | mal_hz | vab3_hz | vpodn_hz | accept | approach | retreat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.9 | 0 | song | 2.122093023255814 | 2.9 | 0.011128466138419004 | 41.85538965128814 | 15.405612244897961 | 0.0 | 74.375 | True | False | True |
| 0.9 | 0 | mute | 1.4180232558139536 | 3.45 | 0.011195824328694945 | 40.97562317559138 | 11.097448979591837 | 0.0 | 74.275 | True | False | True |
| 0.9 | 0 | noscent | 1.788953488372093 | 6.5 | 0.032171282875063156 | 41.60486488777994 | 12.33520408163265 | 0.0 | 72.05 | True | True | False |
| 0.9 | 1 | song | 0.9947674418604652 | 10.8 | 0.01890316919631685 | 42.63039389057787 | 12.005102040816327 | 0.0 | 73.275 | True | False | True |
| 0.9 | 1 | mute | 5.81453488372093 | 0.5 | 0.004524895841370448 | 44.442913118784894 | 23.54234693877551 | 21.958333333333336 | 74.85 | True | False | True |
| 0.9 | 1 | noscent | 6.474999999999999 | 2.45 | 0.013412110862271284 | 47.83833831954555 | 26.20204081632653 | 0.0 | 71.3 | True | False | True |
| 0.9 | 2 | song | 6.578488372093023 | 5.95 | 0.02039634463685543 | 41.95719801116749 | 36.83163265306123 | 39.15 | 72.4 | True | True | False |
| 0.9 | 2 | mute | 1.6098837209302326 | 0.3 | 0.0023561895683022454 | 42.62351867104323 | 9.714795918367347 | 0.0 | 72.825 | True | False | True |
| 0.9 | 2 | noscent | 2.3726744186046513 | 4.075 | 0.0057382510322714336 | 44.78198937755114 | 17.373979591836736 | 0.0 | 72.3 | True | False | True |
| 0.9 | 3 | song | 2.026744186046512 | 2.675 | 0.010118020655702324 | 43.91323203449571 | 14.831632653061224 | 0.0 | 77.05 | True | False | True |
| 0.9 | 3 | mute | 1.6 | 11.775 | 0.008442541770148112 | 42.65431741379101 | 13.753571428571426 | 0.0 | 73.4 | True | False | True |
| 0.9 | 3 | noscent | 2.9040697674418605 | 10.775 | 0.020135294314924897 | 40.93535022589358 | 11.287244897959184 | 0.0 | 70.75 | True | False | True |
| 0.9 | 4 | song | 3.7476744186046513 | 2.45 | 0.010925914556130612 | 45.47913875800923 | 10.692346938775511 | 0.0 | 72.95 | True | False | True |
| 0.9 | 4 | mute | 2.930813953488372 | 8.8 | 0.025065818343716604 | 42.312681532442674 | 15.906122448979591 | 9.916666666666668 | 77.225 | True | True | False |
| 0.9 | 4 | noscent | 4.456976744186046 | 3.9 | 0.02491159547190791 | 41.77388355276704 | 14.361734693877551 | 0.0 | 76.125 | True | False | True |
| 0.9 | 5 | song | 0.6360465116279069 | 0.45 | 0.0045673407497810355 | 42.69058302346144 | 10.461224489795917 | 0.0 | 72.7 | True | True | False |
| 0.9 | 5 | mute | 5.375 | 9.525 | 0.031189112731810673 | 42.193181405263985 | 26.915816326530614 | 28.516666666666666 | 72.35 | True | True | False |
| 0.9 | 5 | noscent | 6.5709302325581405 | 4.425 | 0.021834765428506354 | 48.173152880900176 | 15.244897959183673 | 0.0 | 72.2 | True | False | True |
| 0.9 | 6 | song | 3.08953488372093 | 23.675 | 0.056078832029364326 | 44.69287223991958 | 18.596938775510203 | 9.416666666666668 | 71.7 | True | False | True |
| 0.9 | 6 | mute | 0.9244186046511628 | 5.225 | 0.011309056782326599 | 40.44901073145916 | 10.235204081632654 | 0.0 | 72.75 | True | False | True |
| 0.9 | 6 | noscent | 3.15 | 4.85 | 0.0160376088397915 | 44.062477743728884 | 11.711734693877553 | 0.0 | 73.675 | True | False | True |
| 0.9 | 7 | song | 0.8895348837209304 | 2.7 | 0.012764973765399977 | 46.65404246557091 | 9.355102040816327 | 0.0 | 72.6 | True | True | False |
| 0.9 | 7 | mute | 0.7831395348837211 | 2.625 | 0.01049784923453207 | 45.896930148617386 | 12.11887755102041 | 0.0 | 74.975 | True | False | True |
| 0.9 | 7 | noscent | 6.544186046511627 | 9.475 | 0.019534945253247605 | 43.654666852387926 | 12.270408163265307 | 0.0 | 76.425 | True | False | True |
| 0.9 | 8 | song | 1.7011627906976745 | 5.775 | 0.017650050417394945 | 44.02355288816754 | 13.906632653061225 | 0.0 | 75.55 | True | False | True |
| 0.9 | 8 | mute | 4.072093023255814 | 4.15 | 0.012770977345377486 | 48.978033817419856 | 22.5719387755102 | 0.0 | 72.65 | True | False | True |
| 0.9 | 8 | noscent | 1.8337209302325583 | 8.925 | 0.033759237238930075 | 44.15885527064837 | 11.837755102040816 | 0.0 | 71.0 | True | True | False |
| 0.9 | 9 | song | 2.650581395348837 | 0.05 | 0.0004849921629448825 | 45.9697193590194 | 17.908163265306122 | 0.0 | 73.175 | True | False | True |
| 0.9 | 9 | mute | 5.311627906976744 | 0.05 | 0.0003855998209206825 | 44.79634452102082 | 9.206122448979592 | 0.0 | 75.725 | True | False | True |
| 0.9 | 9 | noscent | 2.8331395348837214 | 0.55 | 0.005089948394646444 | 43.447929106963336 | 14.610204081632656 | 0.0 | 75.55 | True | True | False |
| 0.8 | 0 | song | 0.6162790697674418 | 2.25 | 0.009909035067902281 | 32.678471069875606 | 5.522959183673469 | 0.0 | 74.75 | True | False | True |
| 0.8 | 0 | mute | 0.8174418604651162 | 3.4 | 0.015250380168054712 | 32.775229830065044 | 5.106122448979591 | 0.0 | 72.6 | True | False | True |
| 0.8 | 0 | noscent | 3.4406976744186046 | 6.925 | 0.01585212130194685 | 20.99707973498383 | 5.894387755102041 | 0.0 | 75.5 | True | False | True |
| 0.8 | 1 | song | 0.6936046511627907 | 5.05 | 0.02234873264686957 | 33.24951581255072 | 5.510204081632653 | 0.0 | 73.6 | True | True | False |
| 0.8 | 1 | mute | 0.7313953488372092 | 3.25 | 0.011017743528411842 | 32.88401908891608 | 5.115816326530612 | 0.0 | 76.0 | True | False | True |
| 0.8 | 1 | noscent | 2.626744186046511 | 10.9 | 0.03225747160710692 | 25.57170546626131 | 6.009693877551022 | 0.0 | 70.0 | True | True | False |
| 0.8 | 2 | song | 0.4906976744186046 | 4.6 | 0.015992790660833627 | 32.733111578105884 | 4.703571428571428 | 0.0 | 70.5 | True | False | True |
| 0.8 | 2 | mute | 0.4186046511627907 | 1.4 | 0.005782566864794327 | 31.979344666367897 | 4.247448979591836 | 0.0 | 73.625 | True | False | True |
| 0.8 | 2 | noscent | 2.923837209302326 | 9.25 | 0.016991660121723755 | 25.09653952834874 | 5.485204081632653 | 0.0 | 68.95 | True | False | True |
| 0.8 | 3 | song | 0.7075581395348837 | 2.35 | 0.012085576260562753 | 33.250335509502065 | 5.490816326530612 | 0.0 | 76.15 | True | True | False |
| 0.8 | 3 | mute | 0.6441860465116279 | 4.675 | 0.021014229469706963 | 33.33084598054772 | 4.613775510204082 | 0.0 | 75.375 | True | True | False |
| 0.8 | 3 | noscent | 3.270348837209302 | 8.125 | 0.02828282687971115 | 22.884220757985005 | 6.369897959183672 | 0.0 | 74.075 | True | False | True |
| 0.8 | 4 | song | 0.6383720930232559 | 2.85 | 0.009950355922604459 | 32.40443914196776 | 2.4989795918367346 | 0.0 | 76.15 | True | True | False |
| 0.8 | 4 | mute | 0.875 | 2.2 | 0.012230419832576146 | 34.1404891534744 | 4.518877551020408 | 0.0 | 76.6 | True | False | True |
| 0.8 | 4 | noscent | 1.988953488372093 | 6.125 | 0.019048159018160437 | 24.75372239919575 | 6.1 | 0.0 | 76.1 | True | False | True |
| 0.8 | 5 | song | 0.4691860465116279 | 0.9 | 0.0046566385995590156 | 32.91693293443635 | 5.480102040816327 | 0.0 | 72.85 | True | True | False |
| 0.8 | 5 | mute | 0.5180232558139535 | 1.775 | 0.01173223027828621 | 32.4734744613074 | 4.2785714285714285 | 0.0 | 75.175 | True | False | True |
| 0.8 | 5 | noscent | 4.277325581395349 | 18.85 | 0.028418605761080906 | 25.168026973994984 | 6.025510204081634 | 0.0 | 71.85 | True | False | True |
| 0.8 | 6 | song | 3.7122093023255816 | 27.45 | 0.029773410247971064 | 39.081021305459 | 9.64234693877551 | 0.0 | 72.175 | True | False | True |
| 0.8 | 6 | mute | 0.6517441860465115 | 5.625 | 0.020017397670097935 | 33.38467466479331 | 5.178061224489796 | 0.0 | 72.225 | True | True | False |
| 0.8 | 6 | noscent | 3.1965116279069763 | 16.675 | 0.030731959167489702 | 23.870562372064292 | 5.204591836734694 | 0.0 | 69.325 | True | False | True |
| 0.8 | 7 | song | 0.7674418604651163 | 9.05 | 0.016771420788222857 | 31.514408740204214 | 4.352551020408163 | 0.0 | 72.925 | True | False | True |
| 0.8 | 7 | mute | 0.8034883720930233 | 2.0 | 0.010711023302409138 | 32.302896948922616 | 3.352551020408163 | 0.0 | 73.025 | True | False | True |
| 0.8 | 7 | noscent | 2.7715116279069765 | 5.6 | 0.021469413423248474 | 21.593832439045073 | 5.958163265306123 | 0.0 | 73.0 | True | True | False |
| 0.8 | 8 | song | 0.8005813953488372 | 1.625 | 0.010013557697396295 | 33.20755713956953 | 5.519387755102041 | 0.0 | 74.775 | True | True | False |
| 0.8 | 8 | mute | 0.7383720930232559 | 1.975 | 0.00849713280613596 | 33.0881424037984 | 2.7040816326530615 | 0.0 | 73.375 | True | False | True |
| 0.8 | 8 | noscent | 2.718604651162791 | 10.6 | 0.02804538263249976 | 20.72829695618997 | 4.9255102040816325 | 0.0 | 71.875 | True | True | False |
| 0.8 | 9 | song | 0.7366279069767441 | 2.25 | 0.011352341528295291 | 33.08436519664249 | 4.089795918367347 | 0.0 | 75.2 | True | False | True |
| 0.8 | 9 | mute | 0.8017441860465115 | 1.6 | 0.007316253883049715 | 32.92671872918206 | 4.656632653061224 | 0.0 | 76.5 | True | True | False |
| 0.8 | 9 | noscent | 3.076162790697674 | 9.35 | 0.021507041874812404 | 20.405006601179736 | 6.4862244897959185 | 0.0 | 73.85 | True | False | True |

## P35 (descriptive)
| male_exc_scale | condition | n | p1_hz | pip10_hz | delivered_rms | male_total_hz | mal_hz | vab3_hz | vpodn_hz | accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.9 | song | 10 | 2.44366 | 5.7425 | 0.0163018 | 43.9866 | 15.9994 | 4.85667 | 73.5775 | 10 |
| 0.9 | mute | 10 | 2.98395 | 4.64 | 0.0117738 | 43.5323 | 15.5062 | 6.03917 | 74.1025 | 10 |
| 0.9 | noscent | 10 | 3.89297 | 5.5925 | 0.0192625 | 44.0432 | 14.7235 | 0 | 73.1375 | 10 |
| 0.8 | song | 10 | 0.963256 | 5.8375 | 0.0142854 | 33.412 | 5.28107 | 0 | 73.9075 | 10 |
| 0.8 | mute | 10 | 0.7 | 2.79 | 0.0123569 | 32.9286 | 4.37719 | 0 | 74.45 | 10 |
| 0.8 | noscent | 10 | 3.02907 | 10.24 | 0.0242605 | 23.1069 | 5.84592 | 0 | 72.4525 | 10 |

## Result
P33: not established. P34: not established.
All ten paired seeds reported at both scales.
A null means this narrow correction does not recover P1 control at these doses, not that the pathway is absent.
At scale 0.9, song minus mute is 1.1025 Hz in pIP10 and 0.00452802 in delivered RMS; song minus noscent is -1.4493 Hz in P1.
At scale 0.8, song minus mute is 3.0475 Hz in pIP10 and 0.00192845 in delivered RMS; song minus noscent is -2.06581 Hz in P1.
Across the recorded scale/condition cells, vAB3 mean rates span 0 to 6.03917 Hz; mAL means span 4.37719 to 15.9994 Hz (descriptive).
Ten-seed cost: 1.73104 hours; excludes setup and rendering.

## Limitations
- The male scale is a chosen dose, not a measurement.
- The sweep is small and pre-registered; the multiple-scale rule is not a multiplicity-adjusted significance test.
- His eye still floods on uniform grey.
- LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v12
- No silence cell is included in v12; silence staying silent is calibration evidence only, not tested by this sweep.
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
- The override list is chosen from literature for three cell groups only: male vAB3, male mAL and the already restored female SAG. Every other modulatory class stays silenced.
- Functional excitation of P1 is extrapolated to all dictionary vAB3 outputs; receptor-specific effects are not modelled.
