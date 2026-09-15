# Courtship v9

Protocol v9. CHOSEN before data: MALE_EXC_SCALE swept over {0.9, 0.8, 0.7}, positive weights only, before room construction, restored between cells. Raw 1.0 is already on record in v5 and failed P5/P8.
Ten seeds, 400 steps, paired by seed and start across nine cells. Quick mode: two seeds, 80 steps, nine cells. No seed-count adaptation.
Female side = v8 exactly: own restored SAG graph build/graph_female_own_sag.npz (required), both SAG types, virgin STATE_HZ = 50 Hz, positive-weight scale 0.7, blind eye.
Conditions at every scale: song as v5; mute sets only his P1 outgoing gains to zero as v5; noscent zeros both her scent and contact drives to him as v5. All other v5 song settings retained.
Predictions fixed before data:
- P21 the command carries the song: his pIP10 mean rate and delivered song RMS, song > mute (both, as P5).
- P22 he notices her: his P1 mean rate, song > noscent (as P8).
- P23 (descriptive, no verdict): pIP10 and delivered RMS by scale; P1 by scale; total male rate by scale (is there a scale where silence stays silent and song still sings); her vpoDN by scale (does cooling him change what reaches her); accept rule per cell.
- P24 (descriptive, stated as not testable): LC10a per cell, with the sentence "LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9".
Verdict rule per scale as v5: paired difference > 2 SE, n = 10. A step counts as established only if it holds at at least one scale AND the direction is not reversed (difference < -2 SE) at any other scale in the sweep; report every scale. P21 requires both comparisons at the same scale; reversal of either comparison at any scale prevents establishment. Quick runs are smoke tests and cannot establish a step.

## Calibration record
Calibration record: raw male graph (GPU, 8 carried windows x 250 steps; these are calibration probes, not outcomes):
- Silence gives 0 Hz everywhere; any input (her scent on Or47b, her silhouette on his eye, either eye model) ignites the whole male network to ~45-60 Hz total, after which pIP10 is erratic: at one scale it ranges 2 to 245 Hz across conditions, and a P1 lesion sometimes raises pIP10. A ladder of positive-weight scales 1.00/0.98/0.96/0.94/0.92/0.90 showed NO monotone dependence of pIP10 on P1 and no stable scent effect on P1 in eight-window probes. An earlier probe at 0.9 and 0.8 with scent+contact drive at 100 Hz on each class gave pIP10 0-4 Hz (song command gone) while P1 stayed 10-25 Hz. So the regime where P1 controls pIP10, if it exists, lies somewhere in 0.7-0.95 and eight-window probes cannot find it: it needs seeds and the closed loop.
- LC10a cannot be reached from his eye in this map: lamina L1/L2 drive, T4/T5 drive, T2/T3, Tm3/Mi1 all leave LC10a at 0-2 Hz; only driving LC10a's own strongest medulla input types (Tm5Y, LC9, LC10c, TmY21, Tm5a) lights it (47-137 Hz). Its strongest inputs by weight include large inhibitory classes (TuTuA_2, AOTU042). So "he adapts" measured through LC10a is not testable with the current eye; say so.

## Female graph record
{
  "file": "graph_female_own_sag.npz",
  "path": "build/graph_female_own_sag.npz",
  "sha256": "f2452ec31b830931c01a3985ed8e6cbf61264a76e37f70337e57b2ece2fcb02a",
  "restore": {
    "csv_rows": 5342446,
    "empty_types": [],
    "excluded_synapses": 0,
    "floor": 5,
    "mapping": "individual female pre/post ids; pair sum >= 5; post cell must be in graph",
    "per_target_type": [
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 76,
          "AN_SMP_2": 539
        },
        "synapses": 615,
        "target_type": "pC1a"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 558,
          "AN_SMP_2": 10
        },
        "synapses": 568,
        "target_type": "CB0959"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 387
        },
        "synapses": 387,
        "target_type": "pC1b"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 291,
          "AN_SMP_2": 6
        },
        "synapses": 297,
        "target_type": "CB0699"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 195,
          "AN_SMP_2": 0
        },
        "synapses": 195,
        "target_type": ""
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 179
        },
        "synapses": 179,
        "target_type": "pC1c"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 168,
          "AN_SMP_2": 5
        },
        "synapses": 173,
        "target_type": "SMP094"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 149,
          "AN_SMP_2": 0
        },
        "synapses": 149,
        "target_type": "CB1024"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 6,
          "AN_SMP_2": 128
        },
        "synapses": 134,
        "target_type": "CB0094"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 114,
          "AN_SMP_2": 0
        },
        "synapses": 114,
        "target_type": "AN_SMP_1"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 78,
          "AN_SMP_2": 0
        },
        "synapses": 78,
        "target_type": "CB0075"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 60
        },
        "synapses": 60,
        "target_type": "CB0405"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 54,
          "AN_SMP_2": 0
        },
        "synapses": 54,
        "target_type": "PAL01"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 52,
          "AN_SMP_2": 0
        },
        "synapses": 52,
        "target_type": "SMP025a"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 21,
          "AN_SMP_2": 17
        },
        "synapses": 38,
        "target_type": "SMP286"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 31,
          "AN_SMP_2": 0
        },
        "synapses": 31,
        "target_type": "SMP172"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 19,
          "AN_SMP_2": 7
        },
        "synapses": 26,
        "target_type": "AN_FLA_SMP_2"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 17,
          "AN_SMP_2": 8
        },
        "synapses": 25,
        "target_type": "pC1e"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 15,
          "AN_SMP_2": 0
        },
        "synapses": 15,
        "target_type": "CB1610"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 11
        },
        "synapses": 11,
        "target_type": "CB1371"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 11,
          "AN_SMP_2": 0
        },
        "synapses": 11,
        "target_type": "CB2165"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 6,
          "AN_SMP_2": 5
        },
        "synapses": 11,
        "target_type": "NPFL1-I"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 10,
          "AN_SMP_2": 0
        },
        "synapses": 10,
        "target_type": "SMP538"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 9,
          "AN_SMP_2": 0
        },
        "synapses": 9,
        "target_type": "SMP513"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 8
        },
        "synapses": 8,
        "target_type": "CB4204"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 8,
          "AN_SMP_2": 0
        },
        "synapses": 8,
        "target_type": "SMP515"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 7,
          "AN_SMP_2": 0
        },
        "synapses": 7,
        "target_type": "FLA101f_c"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 7,
          "AN_SMP_2": 0
        },
        "synapses": 7,
        "target_type": "SIP076"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 7,
          "AN_SMP_2": 0
        },
        "synapses": 7,
        "target_type": "SMP123b"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 6,
          "AN_SMP_2": 0
        },
        "synapses": 6,
        "target_type": "CB4233"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 6,
          "AN_SMP_2": 0
        },
        "synapses": 6,
        "target_type": "SMP034"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 6,
          "AN_SMP_2": 0
        },
        "synapses": 6,
        "target_type": "pC1d"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 5,
          "AN_SMP_2": 0
        },
        "synapses": 5,
        "target_type": "AN_SMP_FLA_1"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 5,
          "AN_SMP_2": 0
        },
        "synapses": 5,
        "target_type": "CB0015"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 5,
          "AN_SMP_2": 0
        },
        "synapses": 5,
        "target_type": "CB2422"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 5,
          "AN_SMP_2": 0
        },
        "synapses": 5,
        "target_type": "DNpe034"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 0,
          "AN_SMP_2": 5
        },
        "synapses": 5,
        "target_type": "SMP161"
      },
      {
        "by_source_type": {
          "AN_FLA_SMP_2": 5,
          "AN_SMP_2": 0
        },
        "synapses": 5,
        "target_type": "SMP593"
      }
    ],
    "per_type": {
      "AN_FLA_SMP_2": {
        "cell_count": 2,
        "cells": [
          {
            "exported_synapses": 1033,
            "restored_synapses": 1033,
            "root_id": 720575940614614162
          },
          {
            "exported_synapses": 919,
            "restored_synapses": 919,
            "root_id": 720575940638396998
          }
        ],
        "exported_synapses": 1952,
        "restored_synapses": 1952
      },
      "AN_SMP_2": {
        "cell_count": 2,
        "cells": [
          {
            "exported_synapses": 690,
            "restored_synapses": 690,
            "root_id": 720575940623363000
          },
          {
            "exported_synapses": 685,
            "restored_synapses": 685,
            "root_id": 720575940631004202
          }
        ],
        "exported_synapses": 1375,
        "restored_synapses": 1375
      }
    },
    "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; the BANC prediction for the same types is dopamine. Neither prediction fixes the sign of the effect.",
    "sources": [
      {
        "file": "connections_princeton.csv.gz",
        "sha256": "445f996bf6c4b1803b9ba186189138a3061ff8623aa94c0abcf38af30a5bd48b"
      },
      {
        "file": "graph_female.npz",
        "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"
      }
    ],
    "synapse_mv": 0.275,
    "synapses_restored": 3327
  },
  "state_cells": 4,
  "state_cells_per_type": {
    "AN_SMP_2": 2,
    "AN_FLA_SMP_2": 2,
    "ANXXX983": 0
  }
}

## Per-scale verdicts
| Scale | Prediction | Difference | SE | n | Verdict | Reversed |
|---|---|---:|---:|---:|---|---|
| 0.9 | P21_command | 1.1725 | 1.7512751306785959 | 10 | not supported | False |
| 0.9 | P21_rms | 0.002246069883065692 | 0.003041462480906852 | 10 | not supported | False |
| 0.9 | P22 | -6.321046511627908 | 1.227720161749073 | 10 | not supported | True |
P21 joint verdict at 0.9: not supported.
| 0.8 | P21_command | 1.2775000000000003 | 0.6477144646970436 | 10 | not supported | False |
| 0.8 | P21_rms | 0.004244036517099215 | 0.001986290581267869 | 10 | supported | False |
| 0.8 | P22 | -2.3187790697674417 | 0.24247519661875103 | 10 | not supported | True |
P21 joint verdict at 0.8: not supported.
| 0.7 | P21_command | 0.4225 | 0.45862793562247517 | 10 | not supported | False |
| 0.7 | P21_rms | 0.002130956318801922 | 0.0019284474462972208 | 10 | not supported | False |
| 0.7 | P22 | -1.9853488372093022 | 0.13403117588235558 | 10 | not supported | True |
P21 joint verdict at 0.7: not supported.

## Per-seed outcomes
Per-trial outcome (CHOSEN, disclosed): `accept` = her vpoDN window rate exceeds 0 Hz in at least `ACCEPT_WINDOWS` = 3 windows of the trial; `approach` = mean distance in the last quarter of the trial is smaller than in the first quarter; `retreat` = the opposite. Report all three per seed and per condition in a table in the JSON and in the report; never only the pooled mean.
| male_exc_scale | seed | condition | pip10_hz | delivered_rms | p1_hz | male_total_hz | vpodn_hz | lc10a_hz | accept | active_windows | approach | retreat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.9 | 0 | song | 2.525 | 0.01469816148213452 | 1.8627906976744186 | 44.00405790869782 | 74.9 | 0.040545454545454544 | True | 378 | True | False |
| 0.9 | 0 | mute | 4.5 | 0.01907300659715625 | 1.5529069767441859 | 43.03403210959169 | 74.0 | 0.07 | True | 387 | False | True |
| 0.9 | 0 | noscent | 14.15 | 0.030669257379452832 | 7.667441860465117 | 42.98669771441721 | 75.475 | 0.09272727272727271 | True | 384 | True | False |
| 0.9 | 1 | song | 9.125 | 0.028893778149586276 | 4.153488372093023 | 42.39016151693899 | 74.225 | 0.05290909090909091 | True | 390 | False | True |
| 0.9 | 1 | mute | 4.025 | 0.016018714168719396 | 1.325 | 41.96110663630529 | 73.425 | 0.07418181818181818 | True | 380 | True | False |
| 0.9 | 1 | noscent | 17.9 | 0.029984441626465613 | 6.941860465116279 | 41.952973861750706 | 75.95 | 0.09018181818181818 | True | 390 | True | False |
| 0.9 | 2 | song | 2.325 | 0.012381229675632852 | 0.9953488372093022 | 41.93616477513596 | 71.1 | 0.06781818181818182 | True | 384 | True | False |
| 0.9 | 2 | mute | 2.375 | 0.013172986261376852 | 2.208139534883721 | 44.18339258245418 | 74.225 | 0.04218181818181819 | True | 390 | False | True |
| 0.9 | 2 | noscent | 12.425 | 0.014590796555883906 | 6.369767441860465 | 43.74795000060561 | 74.0 | 0.06563636363636363 | True | 384 | False | True |
| 0.9 | 3 | song | 12.3 | 0.023898769105238 | 1.6511627906976745 | 42.463115454027935 | 74.1 | 0.09345454545454544 | True | 388 | False | True |
| 0.9 | 3 | mute | 3.975 | 0.009376952281878891 | 1.2302325581395348 | 41.43007715507322 | 76.425 | 0.08254545454545453 | True | 394 | False | True |
| 0.9 | 3 | noscent | 82.95 | 0.0776930365937034 | 9.500581395348838 | 43.8170607187413 | 67.75 | 0.14927272727272728 | True | 369 | False | True |
| 0.9 | 4 | song | 4.225 | 0.016650126652982173 | 1.516860465116279 | 41.38890820120881 | 79.85 | 0.05799999999999999 | True | 393 | False | True |
| 0.9 | 4 | mute | 3.375 | 0.012121788623077397 | 2.558720930232558 | 43.63750227104807 | 77.95 | 0.057818181818181824 | True | 388 | False | True |
| 0.9 | 4 | noscent | 0.4 | 0.003367707923582629 | 2.6831395348837206 | 44.21138885187922 | 75.525 | 0.05454545454545455 | True | 385 | False | True |
| 0.9 | 5 | song | 17.125 | 0.045802303199325524 | 3.569186046511628 | 43.55843739780283 | 72.25 | 0.0949090909090909 | True | 381 | True | False |
| 0.9 | 5 | mute | 9.775 | 0.029849049600275412 | 1.4209302325581397 | 42.012372972711084 | 74.625 | 0.03690909090909091 | True | 384 | False | True |
| 0.9 | 5 | noscent | 7.375 | 0.02401877074230714 | 13.526744186046512 | 46.01798427829121 | 72.4 | 0.4792727272727273 | True | 380 | False | True |
| 0.9 | 6 | song | 11.15 | 0.018235494372468183 | 1.341279069767442 | 45.286972359830905 | 74.125 | 0.08563636363636365 | True | 386 | False | True |
| 0.9 | 6 | mute | 10.5 | 0.0245870952066384 | 2.349418604651163 | 43.80902090575453 | 71.65 | 0.04527272727272727 | True | 383 | False | True |
| 0.9 | 6 | noscent | 14.475 | 0.05835855167410528 | 6.061627906976744 | 43.46077142960962 | 73.175 | 0.059454545454545454 | True | 388 | True | False |
| 0.9 | 7 | song | 6.225 | 0.016483203386678316 | 2.6581395348837207 | 44.92503149186662 | 72.5 | 0.07618181818181818 | True | 386 | True | False |
| 0.9 | 7 | mute | 17.675 | 0.02952688262404763 | 3.1069767441860465 | 43.290284153534955 | 74.9 | 0.2761818181818182 | True | 391 | False | True |
| 0.9 | 7 | noscent | 16.55 | 0.04177025965857662 | 10.074418604651163 | 46.035260595196284 | 74.825 | 0.2156363636363637 | True | 384 | True | False |
| 0.9 | 8 | song | 3.25 | 0.010127297340750288 | 2.454651162790698 | 42.73961313453083 | 72.35 | 0.05709090909090909 | True | 388 | False | True |
| 0.9 | 8 | mute | 1.725 | 0.009956346651433079 | 1.7906976744186045 | 42.531257797265056 | 74.225 | 0.10072727272727273 | True | 389 | True | False |
| 0.9 | 8 | noscent | 5.125 | 0.018885713400979727 | 5.996511627906976 | 45.33397245672896 | 74.4 | 0.15836363636363637 | True | 383 | True | False |
| 0.9 | 9 | song | 4.875 | 0.01540116405542638 | 2.708139534883721 | 45.8856257797265 | 74.85 | 0.13545454545454547 | True | 388 | False | True |
| 0.9 | 9 | mute | 3.475 | 0.01642800657496228 | 1.4319767441860467 | 43.169960392921595 | 72.075 | 0.08963636363636363 | True | 383 | True | False |
| 0.9 | 9 | noscent | 41.9 | 0.025257432567161116 | 17.299418604651162 | 44.484248010561885 | 77.075 | 0.2952727272727273 | True | 391 | False | True |
| 0.8 | 0 | song | 4.15 | 0.013616163526949498 | 0.7383720930232559 | 31.61966364263999 | 72.65 | 0.06290909090909091 | True | 374 | False | True |
| 0.8 | 0 | mute | 1.55 | 0.010174415712807111 | 0.49825581395348834 | 32.64549908552464 | 72.175 | 0.09472727272727273 | True | 380 | False | True |
| 0.8 | 0 | noscent | 15.675 | 0.0334624716111959 | 3.7133720930232554 | 21.22843745836412 | 71.9 | 0.06745454545454545 | True | 375 | True | False |
| 0.8 | 1 | song | 2.125 | 0.010277300470264964 | 0.6383720930232558 | 33.24803418078754 | 76.425 | 0.07545454545454545 | True | 384 | True | False |
| 0.8 | 1 | mute | 3.325 | 0.013529292973214646 | 0.7447674418604652 | 32.146774506122746 | 73.675 | 0.12945454545454546 | True | 388 | False | True |
| 0.8 | 1 | noscent | 11.75 | 0.02979698036414503 | 2.772093023255814 | 24.511132677656523 | 72.7 | 0.041090909090909095 | True | 380 | True | False |
| 0.8 | 2 | song | 2.7 | 0.009680601728992733 | 0.6 | 33.8094769322077 | 71.475 | 0.17345454545454544 | True | 388 | False | True |
| 0.8 | 2 | mute | 1.625 | 0.006314346873138707 | 0.3813953488372093 | 32.03794103753589 | 70.525 | 0.092 | True | 383 | False | True |
| 0.8 | 2 | noscent | 4.6 | 0.01691481152476822 | 2.5133720930232557 | 27.061808844369615 | 72.0 | 0.06472727272727273 | True | 387 | True | False |
| 0.8 | 3 | song | 3.925 | 0.015904988496115265 | 0.49825581395348834 | 33.02872663848548 | 73.375 | 0.1050909090909091 | True | 386 | True | False |
| 0.8 | 3 | mute | 0.8 | 0.008435534876398263 | 0.8988372093023256 | 33.66438118482092 | 76.6 | 0.1218181818181818 | True | 389 | False | True |
| 0.8 | 3 | noscent | 4.375 | 0.013863921892808636 | 1.5197674418604652 | 26.498452053633073 | 75.8 | 0.046181818181818185 | True | 390 | True | False |
| 0.8 | 4 | song | 2.225 | 0.00924363481972083 | 1.0011627906976743 | 32.69880875958383 | 75.575 | 0.11127272727272729 | True | 391 | False | True |
| 0.8 | 4 | mute | 0.375 | 0.0028925530392346368 | 0.6436046511627908 | 32.354406741681906 | 77.875 | 0.08436363636363638 | True | 395 | False | True |
| 0.8 | 4 | noscent | 12.25 | 0.03240033867459839 | 3.924418604651163 | 20.152473322755295 | 73.0 | 0.04290909090909091 | True | 388 | True | False |
| 0.8 | 5 | song | 4.15 | 0.018010020191537166 | 0.8505813953488373 | 33.23115393466649 | 74.375 | 0.09345454545454544 | True | 386 | True | False |
| 0.8 | 5 | mute | 1.5 | 0.008818942295586031 | 0.7779069767441861 | 32.74656435847434 | 73.1 | 0.09236363636363634 | True | 387 | False | True |
| 0.8 | 5 | noscent | 8.675 | 0.02892831384657486 | 3.969767441860465 | 21.591264943496327 | 73.625 | 0.040909090909090916 | True | 390 | True | False |
| 0.8 | 6 | song | 5.525 | 0.02499511018007451 | 0.7441860465116278 | 33.13488269279684 | 70.775 | 0.12381818181818183 | True | 384 | True | False |
| 0.8 | 6 | mute | 1.5 | 0.008856405291678 | 0.586046511627907 | 32.605399643899666 | 72.75 | 0.11018181818181817 | True | 386 | False | True |
| 0.8 | 6 | noscent | 7.1 | 0.019846560289135708 | 2.63546511627907 | 23.611875158973362 | 68.075 | 0.041090909090909095 | True | 382 | False | True |
| 0.8 | 7 | song | 2.1 | 0.01071377377626767 | 0.9261627906976745 | 33.36591096280326 | 75.0 | 0.06618181818181817 | True | 387 | True | False |
| 0.8 | 7 | mute | 2.575 | 0.009794694874195589 | 0.7936046511627908 | 32.68901145819454 | 75.8 | 0.08236363636363636 | True | 390 | True | False |
| 0.8 | 7 | noscent | 18.075 | 0.04033422988512688 | 3.4703488372093023 | 22.190646915613907 | 73.55 | 0.04945454545454545 | True | 388 | False | True |
| 0.8 | 8 | song | 4.125 | 0.016906291945989756 | 0.8 | 31.735260595196277 | 72.4 | 0.12690909090909092 | True | 380 | False | True |
| 0.8 | 8 | mute | 6.525 | 0.02292272648428607 | 1.0011627906976743 | 32.76424855561342 | 74.3 | 0.07163636363636364 | True | 386 | False | True |
| 0.8 | 8 | noscent | 18.625 | 0.03922156112108377 | 2.200581395348837 | 27.304389784522954 | 71.4 | 0.060181818181818184 | True | 381 | True | False |
| 0.8 | 9 | song | 2.475 | 0.010350896376573398 | 0.9953488372093023 | 33.26969604292584 | 73.575 | 0.08981818181818181 | True | 388 | True | False |
| 0.8 | 9 | mute | 0.95 | 0.005519503920954587 | 0.8848837209302326 | 32.83351128256683 | 76.975 | 0.07618181818181818 | True | 387 | False | True |
| 0.8 | 9 | noscent | 10.975 | 0.026067694074708513 | 4.2610465116279075 | 22.484402441830888 | 77.0 | 0.038181818181818185 | True | 390 | False | True |
| 0.7 | 0 | song | 1.025 | 0.00660848859631563 | 0.6447674418604652 | 21.29635814730926 | 77.0 | 0.11072727272727273 | True | 387 | True | False |
| 0.7 | 0 | mute | 0.675 | 0.0042308003884540995 | 0.6040697674418605 | 21.557536245927253 | 71.6 | 0.12018181818181818 | True | 382 | False | True |
| 0.7 | 0 | noscent | 19.775 | 0.026783383054439024 | 3.344186046511628 | 11.429500006056127 | 73.775 | 0.09145454545454544 | True | 381 | False | True |
| 0.7 | 1 | song | 0.025 | 0.00020187495946626758 | 0.45058139534883723 | 21.110872869756907 | 73.975 | 0.07636363636363637 | True | 388 | True | False |
| 0.7 | 1 | mute | 1.125 | 0.007106253837028029 | 0.7308139534883721 | 20.796694262424143 | 76.225 | 0.12272727272727274 | True | 387 | True | False |
| 0.7 | 1 | noscent | 29.875 | 0.032548057238171564 | 2.2703488372093026 | 10.926036506340765 | 69.2 | 0.06654545454545455 | True | 379 | True | False |
| 0.7 | 2 | song | 1.025 | 0.005726783242273368 | 0.7581395348837209 | 21.05084361865772 | 69.9 | 0.15127272727272728 | True | 381 | True | False |
| 0.7 | 2 | mute | 0.15 | 0.002226187243301285 | 0.4430232558139535 | 21.31873796344521 | 72.275 | 0.1089090909090909 | True | 384 | True | False |
| 0.7 | 2 | noscent | 11.225 | 0.028924351017675404 | 2.5482558139534883 | 8.544594299972141 | 72.5 | 0.05454545454545455 | True | 387 | False | True |
| 0.7 | 3 | song | 2.85 | 0.016831072716590186 | 0.42034883720930233 | 21.571404476689963 | 71.925 | 0.10636363636363637 | True | 383 | True | False |
| 0.7 | 3 | mute | 0.475 | 0.002440638626145995 | 0.5970930232558139 | 22.260137352987485 | 74.95 | 0.15363636363636363 | True | 386 | True | False |
| 0.7 | 3 | noscent | 7.825 | 0.014456614089198782 | 2.5034883720930234 | 9.080159215610276 | 71.225 | 0.06109090909090909 | True | 382 | False | True |
| 0.7 | 4 | song | 2.0 | 0.010164035901868576 | 0.5511627906976745 | 20.791697956662347 | 76.4 | 0.13763636363636364 | True | 386 | True | False |
| 0.7 | 4 | mute | 0.725 | 0.00476207173693513 | 0.7656976744186046 | 21.394575828781143 | 76.7 | 0.15836363636363637 | True | 387 | False | True |
| 0.7 | 4 | noscent | 15.6 | 0.02902130746870321 | 2.844767441860465 | 11.369167342934315 | 73.475 | 0.06254545454545454 | True | 377 | False | True |
| 0.7 | 5 | song | 0.625 | 0.006160818257848773 | 0.6802325581395349 | 21.49600295539056 | 73.45 | 0.12836363636363635 | True | 389 | False | True |
| 0.7 | 5 | mute | 0.575 | 0.004642013467271367 | 0.7651162790697674 | 20.64924419520112 | 72.55 | 0.10527272727272727 | True | 390 | True | False |
| 0.7 | 5 | noscent | 6.775 | 0.01724729661373658 | 1.9924418604651164 | 9.920764343939632 | 71.25 | 0.04581818181818182 | True | 378 | False | True |
| 0.7 | 6 | song | 3.175 | 0.009000727276009042 | 0.5784883720930233 | 20.32970106951224 | 71.675 | 0.15109090909090908 | True | 382 | False | True |
| 0.7 | 6 | mute | 0.35 | 0.0032831856154433817 | 0.43430232558139537 | 20.844445319218515 | 76.05 | 0.11109090909090909 | True | 393 | False | True |
| 0.7 | 6 | noscent | 6.625 | 0.016114861283827265 | 2.695348837209303 | 9.063517278133743 | 70.675 | 0.08345454545454546 | True | 381 | False | True |
| 0.7 | 7 | song | 0.2 | 0.0023479169550801628 | 0.5325581395348837 | 21.582165913688062 | 78.6 | 0.10981818181818183 | True | 390 | False | True |
| 0.7 | 7 | mute | 1.25 | 0.004213248077675209 | 0.4697674418604651 | 21.907089303666382 | 74.0 | 0.13963636363636364 | True | 386 | True | False |
| 0.7 | 7 | noscent | 6.85 | 0.013657257549305407 | 2.225 | 7.81573987718172 | 68.725 | 0.0630909090909091 | True | 375 | False | True |
| 0.7 | 8 | song | 0.15 | 0.002998749915402494 | 0.4854651162790698 | 21.337127699519144 | 75.575 | 0.102 | True | 392 | True | False |
| 0.7 | 8 | mute | 0.025 | 0.00018219253673042613 | 0.5377906976744187 | 20.99078711498165 | 77.5 | 0.09563636363636363 | True | 393 | True | False |
| 0.7 | 8 | noscent | 6.0 | 0.015719349922538883 | 2.0738372093023254 | 9.338166931117598 | 70.65 | 0.049818181818181824 | True | 388 | False | True |
| 0.7 | 9 | song | 0.375 | 0.0011062950927346574 | 0.43430232558139537 | 20.79122164217972 | 76.775 | 0.16527272727272732 | True | 393 | True | False |
| 0.7 | 9 | mute | 1.875 | 0.00675060819658501 | 0.822093023255814 | 20.261673187098026 | 73.475 | 0.11890909090909091 | True | 383 | True | False |
| 0.7 | 9 | noscent | 12.1 | 0.03894506953526433 | 2.8918604651162787 | 9.488683216046319 | 74.25 | 0.07218181818181818 | True | 385 | True | False |

## P23/P24 descriptives (no verdict)
| male_exc_scale | condition | n | pip10_hz | delivered_rms | p1_hz | male_total_hz | vpodn_hz | lc10a_hz | accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.9 | song | 10 | 7.3125 | 0.0202572 | 2.2911 | 43.4578 | 74.025 | 0.0762 | 10 |
| 0.9 | mute | 10 | 6.14 | 0.0180111 | 1.8975 | 42.9059 | 74.35 | 0.0875455 | 10 |
| 0.9 | noscent | 10 | 21.325 | 0.0324596 | 8.61215 | 44.2048 | 74.0575 | 0.166036 | 10 |
| 0.8 | song | 10 | 3.35 | 0.0139699 | 0.779244 | 32.9142 | 73.5625 | 0.102836 | 10 |
| 0.8 | mute | 10 | 2.0725 | 0.00972584 | 0.721047 | 32.6488 | 74.3775 | 0.0955091 | 10 |
| 0.8 | noscent | 10 | 11.21 | 0.0280837 | 3.09802 | 23.6635 | 72.905 | 0.0492182 | 10 |
| 0.7 | song | 10 | 1.145 | 0.00611468 | 0.553605 | 21.1357 | 74.5275 | 0.123891 | 10 |
| 0.7 | mute | 10 | 0.7225 | 0.00398372 | 0.616977 | 21.1981 | 74.5325 | 0.123436 | 10 |
| 0.7 | noscent | 10 | 12.265 | 0.0233418 | 2.53895 | 9.69763 | 71.5725 | 0.0650545 | 10 |
LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9
No silence cell was run; the silent baseline is from calibration only.

## Result
P21 is not established under the multiple-scale rule. P22 is not established under the multiple-scale rule.
All ten paired seeds are reported at every scale.

Ten-seed cost: 2.6155 hours (9 cells x 10 seeds x 400 steps), excluding setup and rendering.

## Limitations
- The male scale is a chosen dose, not a measurement.
- The sweep is small and pre-registered; the multiple-scale rule is not a multiplicity-adjusted significance test.
- His eye still floods on uniform grey.
- LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9
- No silence cell is included in v9; silence staying silent is calibration evidence only, not tested by this sweep.
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
