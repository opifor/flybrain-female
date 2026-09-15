# Courtship v8

Quick runs are smoke tests; two-seed verdicts are not the ten-seed experiment.
Protocol v8. v7 grafted BANC's measured SAG outputs onto her map; this audit found her own export already carries the same route, dropped by the transmitter-sign rule; v8 restores her own synapses instead and keeps everything else. The BANC measurement stands as a second individual showing the same wiring.
CHOSEN: female graph build/graph_female_own_sag.npz restores her individual SAG pre/post pairs at +1 sign and 0.275 mV per synapse, with the export's >= 5 synapse pair floor and only postsynaptic cells in the graph. Source and graph SHA256s and restore metadata are recorded.
CHOSEN: state enters at SAG, matching ^(AN_SMP_2|AN_FLA_SMP_2|ANXXX983)$; both FAFB SAG types carry the state. Virgin = STATE_HZ tonic every window, mated = 0 Hz. SPSN themselves are not modelled.
CHOSEN: FEMALE_EXC_SCALE = 0.7, carried over from the v7 calibration. The before-data ladder is recorded below; 0.7 is retained even if silence produces nonzero vpoDN. No tuning follows this ladder.
CHOSEN: virgin_song and mated_song deliver song exactly as v5 song; virgin_silence and mated_silence zero her waveform exactly as v5 silence. His brain remains live in all four conditions.
His side is unchanged from v5: raw male, same eye, same scent, same start geometry, same seeds. No lesion or P1 drive is added.

Predictions fixed before data (verdict rule as v5: paired difference across ten seeds > 2 SE):
- P17 she can say no: her vpoDN mean rate, virgin_song > mated_song.
- P18 she still hears: her vpoDN, virgin_song > virgin_silence.
- P19 the state reaches her receptivity cells: her pC1 mean rate, virgin_song > mated_song.
- P20 (descriptive, no verdict): mated_song vs mated_silence vpoDN and pC1; accept rule per condition; approach/retreat per condition; oviDN per condition; his P1/pIP10 per condition (does her state change his song, descriptively).
CHOSEN: courtship starts when he can see her. She starts 6 mm ahead of him, offset by a seed-derived angle within +/-30 degrees of his heading, facing a seed-derived random heading. All other arena rules are unchanged.
- song: his previous measured pIP10 mean sets amplitude; per-cell pulse and sine motor means set mode.
- silence: her waveform is zero; his brain still runs.
CHOSEN: pIP10 is the descending song command; zero pIP10 produces zero song. Dependence on P1 is tested, not assumed. Amplitude clips pIP10 mean / (1000 / refractory_ms). No explicit P1 gate is applied.
CHOSEN: mode = pulse per-cell mean / (pulse per-cell mean + sine per-cell mean), zero if both zero. Waveform = a * (m * pulse + (1-m) * sine), scaled by existing distance falloff.
CHOSEN: 22050 Hz waveform; 35 ms IPI, 4 ms Hann-windowed 250 Hz pulse, 150 Hz sine; phases and sample clock carry across windows.
CHOSEN: JO-A 100-500 Hz, JO-B 500-2500 Hz, Butterworth order 4, sosfiltfilt with padlen 27 per 50 ms waveform. Each of ten 5 ms band-RMS windows drives SOUND_MAX_HZ * clip(RMS / RMS_FULL, 0, 1), equalised per soma side.
CHOSEN: RMS_FULL is JO-A RMS of a one-second full-amplitude pure pulse train including filter edges, computed once at import and printed with ear settings.
CHOSEN: her brain runs in real time so pulse timing can reach it. Ten carried 25-step runs; full-window answers average all 250 steps. His constructor also uses 250 steps: both brains run 50 ms per world step.
CHOSEN: female scent = SMELL_MAX_HZ * falloff(distance) into ORN_VA1v; putative_ppk23 only within CONTACT_MM = 2.0 mm. His ORN_DA1 cVA drive is zero because no other male is present.
CHOSEN: D. melanogaster pulse IPI approximately 35 ms, carrier approximately 250 Hz, sine approximately 150 Hz; von Philipsborn et al. 2011 Neuron 69:509 (descending circuit; https://pubmed.ncbi.nlm.nih.gov/21315261/); Fast intensity adaptation enhances the encoding of sound in Drosophila, Nat Commun 2018 (carriers; https://doi.org/10.1038/s41467-017-02453-9); Zhou et al. 2015 eLife 4:e08477 (IPI; https://elifesciences.org/articles/08477). These numbers are synthesis choices, not brain measurements.
State group: 4 cells; {'AN_SMP_2': 2, 'AN_FLA_SMP_2': 2, 'ANXXX983': 0}; STATE_HZ = 50 Hz.
Calibration record measured before v8 data: GPU CUDA, JO 60 Hz and silence, eight carried windows x 250 steps per arm; each arm starts at rest with seed 0. Both JO groups receive the stated uniform rate; state group has both FAFB SAG types. Zero-rate keys remain in the drive in every arm, preserving paired random draws.
| Positive-weight scale | JO Hz | SAG Hz | pC1 Hz | vpoDN Hz | Active windows / 8 |
|---:|---:|---:|---:|---:|---:|
| 0.9 | 60 | 0 | 3.25 | 42.5 | 5 |
| 0.9 | 60 | 50 | 13.5 | 61.25 | 6 |
| 0.9 | 0 | 0 | 0 | 0 | 0 |
| 0.9 | 0 | 50 | 49.75 | 157.5 | 8 |
| 0.8 | 60 | 0 | 5.5 | 90 | 7 |
| 0.8 | 60 | 50 | 15.25 | 83.75 | 6 |
| 0.8 | 0 | 0 | 0 | 0 | 0 |
| 0.8 | 0 | 50 | 17.5 | 63.75 | 6 |
| 0.7 | 60 | 0 | 2.25 | 18.75 | 3 |
| 0.7 | 60 | 50 | 15.75 | 30 | 5 |
| 0.7 | 0 | 0 | 0 | 0 | 0 |
| 0.7 | 0 | 50 | 46.5 | 73.75 | 8 |
| 0.6 | 60 | 0 | 0.5 | 2.5 | 1 |
| 0.6 | 60 | 50 | 28 | 57.5 | 7 |
| 0.6 | 0 | 0 | 0 | 0 | 0 |
| 0.6 | 0 | 50 | 39.75 | 72.5 | 8 |
Silence gives nonzero vpoDN at scale 0.7 with SAG driven; scale 0.7 is nevertheless retained as specified before this ladder.

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

## Per-seed outcomes / P20
Per-trial outcome (CHOSEN, disclosed): `accept` = her vpoDN window rate exceeds 0 Hz in at least `ACCEPT_WINDOWS` = 3 windows of the trial; `approach` = mean distance in the last quarter of the trial is smaller than in the first quarter; `retreat` = the opposite. Report all three per seed and per condition in a table in the JSON and in the report; never only the pooled mean.
| seed | condition | state_group | state_drive_hz | accept | approach | retreat | active_windows | vpodn_hz | pc1_hz | ovidn_hz | p1_hz | pip10_hz |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | virgin_song | SAG | 50.0 | True | False | True | 388 | 74.35 | 38.245 | 0.0 | 1.8063953488372093 | 4.125 |
| 0 | mated_song | SAG | 0.0 | True | False | True | 5 | 0.3 | 0.03 | 0.0 | 0.9808139534883721 | 3.825 |
| 0 | virgin_silence | SAG | 50.0 | True | False | True | 382 | 73.7 | 38.57 | 0.0 | 2.8319767441860466 | 10.175 |
| 0 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 2.2430232558139536 | 7.925 |
| 1 | virgin_song | SAG | 50.0 | True | False | True | 388 | 75.425 | 39.08 | 0.0 | 1.2575581395348836 | 2.175 |
| 1 | mated_song | SAG | 0.0 | True | False | True | 4 | 0.35 | 0.11 | 0.0 | 1.7593023255813955 | 0.7 |
| 1 | virgin_silence | SAG | 50.0 | True | False | True | 384 | 73.525 | 39.05 | 0.0 | 1.175581395348837 | 1.225 |
| 1 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.3279069767441862 | 0.45 |
| 2 | virgin_song | SAG | 50.0 | True | False | True | 388 | 72.7 | 38.065 | 0.0 | 6.23546511627907 | 0.05 |
| 2 | mated_song | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.005 | 0.0 | 5.7116279069767435 | 0.325 |
| 2 | virgin_silence | SAG | 50.0 | True | True | False | 382 | 72.175 | 36.79 | 0.0 | 2.457558139534884 | 7.025 |
| 2 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 29.0656976744186 | 1.625 |
| 3 | virgin_song | SAG | 50.0 | True | False | True | 385 | 74.65 | 39.07 | 0.0 | 3.7936046511627897 | 0.575 |
| 3 | mated_song | SAG | 0.0 | True | False | True | 6 | 0.5 | 0.075 | 0.0 | 1.205813953488372 | 2.625 |
| 3 | virgin_silence | SAG | 50.0 | True | True | False | 386 | 73.725 | 39.32 | 0.0 | 2.46453488372093 | 0.275 |
| 3 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 3.1819767441860463 | 0.275 |
| 4 | virgin_song | SAG | 50.0 | True | False | True | 389 | 76.625 | 39.345 | 0.0 | 2.726744186046511 | 5.375 |
| 4 | mated_song | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.005 | 0.0 | 14.608720930232558 | 0.375 |
| 4 | virgin_silence | SAG | 50.0 | True | False | True | 385 | 75.325 | 40.26 | 0.0 | 4.280813953488372 | 44.05 |
| 4 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.1093023255813954 | 1.175 |
| 5 | virgin_song | SAG | 50.0 | True | False | True | 384 | 75.175 | 39.675 | 0.0 | 2.6226744186046513 | 5.0 |
| 5 | mated_song | SAG | 0.0 | False | False | True | 1 | 0.2 | 0.045 | 0.0 | 2.3895348837209305 | 2.2 |
| 5 | virgin_silence | SAG | 50.0 | True | True | False | 387 | 73.85 | 39.46 | 0.0 | 3.11453488372093 | 1.575 |
| 5 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.3174418604651164 | 0.9 |
| 6 | virgin_song | SAG | 50.0 | True | False | True | 368 | 65.775 | 36.275 | 0.0 | 0.8494186046511629 | 5.225 |
| 6 | mated_song | SAG | 0.0 | False | False | True | 2 | 0.075 | 0.03 | 0.0 | 1.1343023255813953 | 1.15 |
| 6 | virgin_silence | SAG | 50.0 | True | True | False | 384 | 75.025 | 37.68 | 0.0 | 2.609883720930233 | 3.725 |
| 6 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.2354651162790697 | 1.275 |
| 7 | virgin_song | SAG | 50.0 | True | False | True | 385 | 74.925 | 38.43 | 0.0 | 4.576744186046512 | 0.55 |
| 7 | mated_song | SAG | 0.0 | False | True | False | 0 | 0.0 | 0.0 | 0.0 | 1.7122093023255816 | 0.975 |
| 7 | virgin_silence | SAG | 50.0 | True | False | True | 380 | 74.35 | 38.315 | 0.0 | 1.6819767441860463 | 2.3 |
| 7 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 0.9953488372093022 | 0.975 |
| 8 | virgin_song | SAG | 50.0 | True | False | True | 384 | 75.975 | 40.24 | 0.0 | 1.272093023255814 | 4.525 |
| 8 | mated_song | SAG | 0.0 | False | True | False | 2 | 0.075 | 0.04 | 0.0 | 1.9848837209302326 | 0.825 |
| 8 | virgin_silence | SAG | 50.0 | True | False | True | 392 | 77.6 | 40.255 | 0.0 | 0.8273255813953487 | 0.4 |
| 8 | mated_silence | SAG | 0.0 | False | True | False | 0 | 0.0 | 0.0 | 0.0 | 1.169767441860465 | 1.2 |
| 9 | virgin_song | SAG | 50.0 | True | False | True | 388 | 74.4 | 38.855 | 0.0 | 0.8046511627906977 | 0.15 |
| 9 | mated_song | SAG | 0.0 | True | False | True | 12 | 0.9 | 0.13 | 0.0 | 15.858720930232558 | 19.675 |
| 9 | virgin_silence | SAG | 50.0 | True | False | True | 391 | 73.95 | 38.38 | 0.0 | 14.055232558139535 | 0.15 |
| 9 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 12.037790697674417 | 0.15 |

## P17-P19
{
  "P17": {
    "mean": 73.76,
    "se": 0.9646041214462594,
    "n": 10,
    "paired_differences": [
      74.05,
      75.075,
      72.7,
      74.15,
      76.625,
      74.975,
      65.7,
      74.925,
      75.89999999999999,
      73.5
    ],
    "metric": "vpodn_hz",
    "control": "mated_song",
    "direction": "virgin_song - mated_song",
    "verdict": "supported"
  },
  "P18": {
    "mean": -0.32249999999999945,
    "se": 1.034437917690354,
    "n": 10,
    "paired_differences": [
      0.6499999999999915,
      1.8999999999999915,
      0.5250000000000057,
      0.9250000000000114,
      1.2999999999999972,
      1.3250000000000028,
      -9.25,
      0.5750000000000028,
      -1.625,
      0.45000000000000284
    ],
    "metric": "vpodn_hz",
    "control": "virgin_silence",
    "direction": "virgin_song - virgin_silence",
    "verdict": "not supported"
  },
  "P19": {
    "mean": 38.681,
    "se": 0.3403623885736432,
    "n": 10,
    "paired_differences": [
      38.214999999999996,
      38.97,
      38.059999999999995,
      38.995,
      39.339999999999996,
      39.629999999999995,
      36.245,
      38.43,
      40.2,
      38.724999999999994
    ],
    "metric": "pc1_hz",
    "control": "mated_song",
    "direction": "virgin_song - mated_song",
    "verdict": "supported"
  }
}

## Result
P17 was supported: virgin_song - mated_song in vpodn_hz was 73.76 Hz (SE 0.9646041214462594, n=10); the required positive difference must exceed 2 SE. P18 was not supported: virgin_song - virgin_silence in vpodn_hz was -0.3225 Hz (SE 1.034437917690354, n=10); the required positive difference must exceed 2 SE. P19 was supported: virgin_song - mated_song in pc1_hz was 38.681 Hz (SE 0.3403623885736432, n=10); the required positive difference must exceed 2 SE.

## P20 (descriptive, no verdict)
[
  {
    "seed": 0,
    "condition": "virgin_song",
    "vpodn_hz": 74.35,
    "pc1_hz": 38.245,
    "accept": true,
    "active_windows": 388,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.39598997493734334,
    "ovidn_hz": 0.0,
    "p1_hz": 1.8063953488372093,
    "pip10_hz": 4.125
  },
  {
    "seed": 0,
    "condition": "mated_song",
    "vpodn_hz": 0.3,
    "pc1_hz": 0.03,
    "accept": true,
    "active_windows": 5,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.07268170426065163,
    "ovidn_hz": 0.0,
    "p1_hz": 0.9808139534883721,
    "pip10_hz": 3.825
  },
  {
    "seed": 0,
    "condition": "virgin_silence",
    "vpodn_hz": 73.7,
    "pc1_hz": 38.57,
    "accept": true,
    "active_windows": 382,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.43358395989974935,
    "ovidn_hz": 0.0,
    "p1_hz": 2.8319767441860466,
    "pip10_hz": 10.175
  },
  {
    "seed": 0,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.24060150375939848,
    "ovidn_hz": 0.0,
    "p1_hz": 2.2430232558139536,
    "pip10_hz": 7.925
  },
  {
    "seed": 1,
    "condition": "virgin_song",
    "vpodn_hz": 75.425,
    "pc1_hz": 39.08,
    "accept": true,
    "active_windows": 388,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.41604010025062654,
    "ovidn_hz": 0.0,
    "p1_hz": 1.2575581395348836,
    "pip10_hz": 2.175
  },
  {
    "seed": 1,
    "condition": "mated_song",
    "vpodn_hz": 0.35,
    "pc1_hz": 0.11,
    "accept": true,
    "active_windows": 4,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.16040100250626566,
    "ovidn_hz": 0.0,
    "p1_hz": 1.7593023255813955,
    "pip10_hz": 0.7
  },
  {
    "seed": 1,
    "condition": "virgin_silence",
    "vpodn_hz": 73.525,
    "pc1_hz": 39.05,
    "accept": true,
    "active_windows": 384,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.42105263157894735,
    "ovidn_hz": 0.0,
    "p1_hz": 1.175581395348837,
    "pip10_hz": 1.225
  },
  {
    "seed": 1,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.21303258145363407,
    "ovidn_hz": 0.0,
    "p1_hz": 1.3279069767441862,
    "pip10_hz": 0.45
  },
  {
    "seed": 2,
    "condition": "virgin_song",
    "vpodn_hz": 72.7,
    "pc1_hz": 38.065,
    "accept": true,
    "active_windows": 388,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.2932330827067669,
    "ovidn_hz": 0.0,
    "p1_hz": 6.23546511627907,
    "pip10_hz": 0.05
  },
  {
    "seed": 2,
    "condition": "mated_song",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.005,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.20802005012531327,
    "ovidn_hz": 0.0,
    "p1_hz": 5.7116279069767435,
    "pip10_hz": 0.325
  },
  {
    "seed": 2,
    "condition": "virgin_silence",
    "vpodn_hz": 72.175,
    "pc1_hz": 36.79,
    "accept": true,
    "active_windows": 382,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.3558897243107769,
    "ovidn_hz": 0.0,
    "p1_hz": 2.457558139534884,
    "pip10_hz": 7.025
  },
  {
    "seed": 2,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.19298245614035087,
    "ovidn_hz": 0.0,
    "p1_hz": 29.0656976744186,
    "pip10_hz": 1.625
  },
  {
    "seed": 3,
    "condition": "virgin_song",
    "vpodn_hz": 74.65,
    "pc1_hz": 39.07,
    "accept": true,
    "active_windows": 385,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3533834586466165,
    "ovidn_hz": 0.0,
    "p1_hz": 3.7936046511627897,
    "pip10_hz": 0.575
  },
  {
    "seed": 3,
    "condition": "mated_song",
    "vpodn_hz": 0.5,
    "pc1_hz": 0.075,
    "accept": true,
    "active_windows": 6,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.12280701754385964,
    "ovidn_hz": 0.0,
    "p1_hz": 1.205813953488372,
    "pip10_hz": 2.625
  },
  {
    "seed": 3,
    "condition": "virgin_silence",
    "vpodn_hz": 73.725,
    "pc1_hz": 39.32,
    "accept": true,
    "active_windows": 386,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.3308270676691729,
    "ovidn_hz": 0.0,
    "p1_hz": 2.46453488372093,
    "pip10_hz": 0.275
  },
  {
    "seed": 3,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.14536340852130325,
    "ovidn_hz": 0.0,
    "p1_hz": 3.1819767441860463,
    "pip10_hz": 0.275
  },
  {
    "seed": 4,
    "condition": "virgin_song",
    "vpodn_hz": 76.625,
    "pc1_hz": 39.345,
    "accept": true,
    "active_windows": 389,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.39348370927318294,
    "ovidn_hz": 0.0,
    "p1_hz": 2.726744186046511,
    "pip10_hz": 5.375
  },
  {
    "seed": 4,
    "condition": "mated_song",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.005,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.08521303258145363,
    "ovidn_hz": 0.0,
    "p1_hz": 14.608720930232558,
    "pip10_hz": 0.375
  },
  {
    "seed": 4,
    "condition": "virgin_silence",
    "vpodn_hz": 75.325,
    "pc1_hz": 40.26,
    "accept": true,
    "active_windows": 385,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.44110275689223055,
    "ovidn_hz": 0.0,
    "p1_hz": 4.280813953488372,
    "pip10_hz": 44.05
  },
  {
    "seed": 4,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.18796992481203006,
    "ovidn_hz": 0.0,
    "p1_hz": 1.1093023255813954,
    "pip10_hz": 1.175
  },
  {
    "seed": 5,
    "condition": "virgin_song",
    "vpodn_hz": 75.175,
    "pc1_hz": 39.675,
    "accept": true,
    "active_windows": 384,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.37844611528822053,
    "ovidn_hz": 0.0,
    "p1_hz": 2.6226744186046513,
    "pip10_hz": 5.0
  },
  {
    "seed": 5,
    "condition": "mated_song",
    "vpodn_hz": 0.2,
    "pc1_hz": 0.045,
    "accept": false,
    "active_windows": 1,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3032581453634085,
    "ovidn_hz": 0.0,
    "p1_hz": 2.3895348837209305,
    "pip10_hz": 2.2
  },
  {
    "seed": 5,
    "condition": "virgin_silence",
    "vpodn_hz": 73.85,
    "pc1_hz": 39.46,
    "accept": true,
    "active_windows": 387,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.40100250626566414,
    "ovidn_hz": 0.0,
    "p1_hz": 3.11453488372093,
    "pip10_hz": 1.575
  },
  {
    "seed": 5,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.21303258145363407,
    "ovidn_hz": 0.0,
    "p1_hz": 1.3174418604651164,
    "pip10_hz": 0.9
  },
  {
    "seed": 6,
    "condition": "virgin_song",
    "vpodn_hz": 65.775,
    "pc1_hz": 36.275,
    "accept": true,
    "active_windows": 368,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3057644110275689,
    "ovidn_hz": 0.0,
    "p1_hz": 0.8494186046511629,
    "pip10_hz": 5.225
  },
  {
    "seed": 6,
    "condition": "mated_song",
    "vpodn_hz": 0.075,
    "pc1_hz": 0.03,
    "accept": false,
    "active_windows": 2,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.13032581453634084,
    "ovidn_hz": 0.0,
    "p1_hz": 1.1343023255813953,
    "pip10_hz": 1.15
  },
  {
    "seed": 6,
    "condition": "virgin_silence",
    "vpodn_hz": 75.025,
    "pc1_hz": 37.68,
    "accept": true,
    "active_windows": 384,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.40852130325814534,
    "ovidn_hz": 0.0,
    "p1_hz": 2.609883720930233,
    "pip10_hz": 3.725
  },
  {
    "seed": 6,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.18546365914786966,
    "ovidn_hz": 0.0,
    "p1_hz": 1.2354651162790697,
    "pip10_hz": 1.275
  },
  {
    "seed": 7,
    "condition": "virgin_song",
    "vpodn_hz": 74.925,
    "pc1_hz": 38.43,
    "accept": true,
    "active_windows": 385,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.5112781954887218,
    "ovidn_hz": 0.0,
    "p1_hz": 4.576744186046512,
    "pip10_hz": 0.55
  },
  {
    "seed": 7,
    "condition": "mated_song",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.2656641604010025,
    "ovidn_hz": 0.0,
    "p1_hz": 1.7122093023255816,
    "pip10_hz": 0.975
  },
  {
    "seed": 7,
    "condition": "virgin_silence",
    "vpodn_hz": 74.35,
    "pc1_hz": 38.315,
    "accept": true,
    "active_windows": 380,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40100250626566414,
    "ovidn_hz": 0.0,
    "p1_hz": 1.6819767441860463,
    "pip10_hz": 2.3
  },
  {
    "seed": 7,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.18796992481203006,
    "ovidn_hz": 0.0,
    "p1_hz": 0.9953488372093022,
    "pip10_hz": 0.975
  },
  {
    "seed": 8,
    "condition": "virgin_song",
    "vpodn_hz": 75.975,
    "pc1_hz": 40.24,
    "accept": true,
    "active_windows": 384,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.39097744360902253,
    "ovidn_hz": 0.0,
    "p1_hz": 1.272093023255814,
    "pip10_hz": 4.525
  },
  {
    "seed": 8,
    "condition": "mated_song",
    "vpodn_hz": 0.075,
    "pc1_hz": 0.04,
    "accept": false,
    "active_windows": 2,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.19298245614035087,
    "ovidn_hz": 0.0,
    "p1_hz": 1.9848837209302326,
    "pip10_hz": 0.825
  },
  {
    "seed": 8,
    "condition": "virgin_silence",
    "vpodn_hz": 77.6,
    "pc1_hz": 40.255,
    "accept": true,
    "active_windows": 392,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.45614035087719296,
    "ovidn_hz": 0.0,
    "p1_hz": 0.8273255813953487,
    "pip10_hz": 0.4
  },
  {
    "seed": 8,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.05764411027568922,
    "ovidn_hz": 0.0,
    "p1_hz": 1.169767441860465,
    "pip10_hz": 1.2
  },
  {
    "seed": 9,
    "condition": "virgin_song",
    "vpodn_hz": 74.4,
    "pc1_hz": 38.855,
    "accept": true,
    "active_windows": 388,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40100250626566414,
    "ovidn_hz": 0.0,
    "p1_hz": 0.8046511627906977,
    "pip10_hz": 0.15
  },
  {
    "seed": 9,
    "condition": "mated_song",
    "vpodn_hz": 0.9,
    "pc1_hz": 0.13,
    "accept": true,
    "active_windows": 12,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.2807017543859649,
    "ovidn_hz": 0.0,
    "p1_hz": 15.858720930232558,
    "pip10_hz": 19.675
  },
  {
    "seed": 9,
    "condition": "virgin_silence",
    "vpodn_hz": 73.95,
    "pc1_hz": 38.38,
    "accept": true,
    "active_windows": 391,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.5363408521303258,
    "ovidn_hz": 0.0,
    "p1_hz": 14.055232558139535,
    "pip10_hz": 0.15
  },
  {
    "seed": 9,
    "condition": "mated_silence",
    "vpodn_hz": 0.0,
    "pc1_hz": 0.0,
    "accept": false,
    "active_windows": 0,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.15538847117794485,
    "ovidn_hz": 0.0,
    "p1_hz": 12.037790697674417,
    "pip10_hz": 0.15
  }
]
virgin_song: {'accept': 10, 'approach': 0, 'retreat': 10}, n=10. Every seed gives the same outcome.
mated_song: {'accept': 4, 'approach': 2, 'retreat': 8}, n=10. Outcomes differ across seeds.
virgin_silence: {'accept': 10, 'approach': 4, 'retreat': 6}, n=10. Outcomes differ across seeds.
mated_silence: {'accept': 0, 'approach': 1, 'retreat': 9}, n=10. Outcomes differ across seeds.

Estimated ten-seed cost (4 x 400 windows each): 1.16 hours, excluding setup and rendering.

## Limitations
- Correction to the historical v5/v6 anatomical explanation: the female export does carry SAG outgoing synapses. Their serotonin consensus maps to sign zero in build_graph_female.py, so the transmitter-sign rule drops their edges. This is a modelling exclusion, not an anatomical absence. The earlier protocol and limitation strings are retained unchanged as published records.
- The restored edges are her own measured synapses. BANC is a second individual, not a donor for v8.
- Both FAFB SAG types are restored and driven; AN_FLA_SMP_2 has additional targets beyond the pC1 route.
- CHOSEN: the SAG effect sign is +1 on functional evidence; neither FAFB serotonin nor BANC dopamine fixes that sign.
- CHOSEN: positive-weight scale 0.7 is carried over from v7, without tuning on the v8 ladder.
- SPSN themselves are not modelled; the state enters at SAG.
- The male is unchanged and runs at raw scale.
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
