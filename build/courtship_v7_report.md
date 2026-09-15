# Courtship v7

Quick runs are smoke tests; two-seed verdicts are not the ten-seed experiment.
Protocol v7. All v5 song/silence settings are retained except the female graph, positive-weight scale, state group and four conditions specified here.
CHOSEN: female graph build/graph_female_sag.npz, a type-name transplant of named BANC SAG outputs, evenly split over matching FAFB targets and both SAG cells; +1 sign and 0.275 mV per synapse. Source SHA256s and the sign choice are recorded in the graft metadata.
CHOSEN: state enters at SAG, matching ^(AN_SMP_2|ANXXX983)$; virgin = STATE_HZ = 50 Hz tonic, mated = 0 Hz. SPSN themselves are not modelled.
CHOSEN: virgin_song and mated_song deliver song exactly as v5 song; virgin_silence and mated_silence zero her waveform exactly as v5 silence. His brain remains live in all four conditions.
His side is unchanged from v5: raw male, same eye, same scent, same start geometry, same seeds. No lesion or P1 drive is added.
Calibration record, measured before v7 data: GPU, eight carried windows x 250 steps, JO 60 Hz.
Grafted raw graph: SAG 0 / 50 / 200 Hz -> pC1 7.0 / 28.0 / 68.3 Hz; raw vpoDN 172 vs 160 Hz (SAG 0 vs 50).
Positive-weight scale -> vpoDN Hz (SAG 0 vs 50): 0.9 -> 53.8 vs 100.0; 0.8 -> 33.8 vs 50.0; 0.7 -> 2.5 (1/8 windows active) vs 38.8 (5/8), and 87.5 at SAG 100; 0.6 -> 5.0 vs 80.0. Silence gives 0 at every scale.
CHOSEN before data: FEMALE_EXC_SCALE = 0.7, for the female's vpoDN to depend on her state while silence still drives nothing. Nothing else is tuned.
Second calibration record, measured after the quick run and before the ten-seed run, same method, on the grafted graph: with SAG driven and NO sound, her vpoDN fires at every rate tested (scale 0.7: SAG 5 -> 12.5 Hz, 10 -> 22.5, 20 -> 43.8, 50 -> 67.5; scale 0.8: SAG 5 -> 5.0, 15 -> 73.8, 50 -> 78.8; scale 0.6: SAG 5 -> 8.8, 50 -> 72.5), and sound plus SAG is at most additive (scale 0.7, JO 60 Hz: SAG 0 -> 25.0, 50 -> 38.8). No scale or tonic rate in these ladders made her yes require both the song and her state. The protocol is kept as written: STATE_HZ 50, scale 0.7. P18 therefore may fail; if it does, the honest reading is that in this map her state opens the gate on its own and the song is not required once she is willing.
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

## Graft record
{
  "file": "graph_female_sag.npz",
  "sha256": "e395989dcfc89edefb20ec5e4d220f6c610bc2a83a01ac1803eab692e9a77c08",
  "graft": {
    "mapping": "fafb_cell_type only (cross-map names); no count threshold; even split over target cells and SAG cells",
    "missing_types": [
      "SMP602,SMP094",
      "LNd_c",
      "SIP078,SIP080",
      "aSP-f1A,aSP-f1B,aSP-f2",
      "CB1449",
      "CB3192",
      "CB3508",
      "SMP338,SMP534",
      "auto:CB0840",
      "auto:SMP090"
    ],
    "sag_cells": 2,
    "sign_choice": "CHOSEN: SAG sign +1 follows functional evidence that SAG activity promotes virgin receptivity and is silenced after mating by sex peptide acting on SPSN (Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135), not the BANC dopamine transmitter prediction.",
    "sources": [
      {
        "file": "graph_female.npz",
        "sha256": "c3ad89ef738ad58187ff4d2f9978c923aa0335f1e3cbf1dd3ee3191dc7477331"
      },
      {
        "file": "banc_888_meta.feather",
        "sha256": "86ccf5df0c67419f8c5f43e93a7ed38d23a080e9f7fde26737290252f3780098"
      },
      {
        "file": "banc_888_edgelist_simple_v3.feather",
        "sha256": "8c296e946f3c69a8c7222f30ad75fa8a98eeb189124fec6df829c9125f4be64b"
      }
    ],
    "synapse_mv": 0.275,
    "synapses_missing": 24,
    "synapses_placed": 1384,
    "total_outgoing_synapses": 1471,
    "unnamed_synapses_excluded": 63
  }
}

## Per-seed outcomes / P20
Per-trial outcome (CHOSEN, disclosed): `accept` = her vpoDN window rate exceeds 0 Hz in at least `ACCEPT_WINDOWS` = 3 windows of the trial; `approach` = mean distance in the last quarter of the trial is smaller than in the first quarter; `retreat` = the opposite. Report all three per seed and per condition in a table in the JSON and in the report; never only the pooled mean.
| seed | condition | state_group | state_drive_hz | accept | approach | retreat | active_windows | vpodn_hz | pc1_hz | ovidn_hz | p1_hz | pip10_hz |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | virgin_song | SAG | 50.0 | True | False | True | 359 | 58.525 | 30.175 | 0.0 | 4.781395348837209 | 41.175 |
| 0 | mated_song | SAG | 0.0 | True | False | True | 5 | 0.525 | 0.005 | 0.0 | 1.219186046511628 | 3.725 |
| 0 | virgin_silence | SAG | 50.0 | True | True | False | 372 | 61.0 | 35.09 | 0.0 | 5.666860465116279 | 1.8 |
| 0 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 2.2430232558139536 | 7.925 |
| 1 | virgin_song | SAG | 50.0 | True | False | True | 378 | 62.35 | 34.02 | 0.0 | 1.376162790697674 | 1.975 |
| 1 | mated_song | SAG | 0.0 | False | True | False | 1 | 0.05 | 0.02 | 0.0 | 1.9889534883720932 | 1.65 |
| 1 | virgin_silence | SAG | 50.0 | True | False | True | 368 | 62.725 | 33.975 | 0.03333333333333333 | 0.9575581395348837 | 0.675 |
| 1 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.3279069767441862 | 0.45 |
| 2 | virgin_song | SAG | 50.0 | True | False | True | 378 | 62.25 | 35.19 | 0.0 | 2.563953488372093 | 1.6 |
| 2 | mated_song | SAG | 0.0 | True | True | False | 5 | 0.4 | 0.045 | 0.0 | 1.7825581395348837 | 1.625 |
| 2 | virgin_silence | SAG | 50.0 | True | False | True | 375 | 63.45 | 34.605 | 0.0 | 1.8755813953488372 | 0.05 |
| 2 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 29.0656976744186 | 1.625 |
| 3 | virgin_song | SAG | 50.0 | True | False | True | 360 | 57.675 | 31.06 | 0.0 | 2.962209302325582 | 52.325 |
| 3 | mated_song | SAG | 0.0 | True | False | True | 3 | 0.25 | 0.09 | 0.0 | 1.900581395348837 | 1.75 |
| 3 | virgin_silence | SAG | 50.0 | True | False | True | 376 | 62.3 | 33.44 | 0.0 | 6.226162790697675 | 2.15 |
| 3 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 3.1819767441860463 | 0.275 |
| 4 | virgin_song | SAG | 50.0 | True | False | True | 356 | 58.8 | 33.26 | 0.0 | 4.429651162790698 | 5.45 |
| 4 | mated_song | SAG | 0.0 | True | False | True | 3 | 0.225 | 0.02 | 0.0 | 4.2918604651162795 | 1.45 |
| 4 | virgin_silence | SAG | 50.0 | True | False | True | 380 | 63.7 | 36.0 | 0.0 | 1.9186046511627908 | 0.375 |
| 4 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.1093023255813954 | 1.175 |
| 5 | virgin_song | SAG | 50.0 | True | True | False | 370 | 63.4 | 35.625 | 0.0 | 1.7843023255813955 | 2.175 |
| 5 | mated_song | SAG | 0.0 | False | True | False | 2 | 0.075 | 0.02 | 0.0 | 1.9959302325581396 | 1.175 |
| 5 | virgin_silence | SAG | 50.0 | True | True | False | 361 | 60.0 | 34.29 | 0.0 | 3.3860465116279066 | 0.9 |
| 5 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.3174418604651164 | 0.9 |
| 6 | virgin_song | SAG | 50.0 | True | False | True | 368 | 63.075 | 34.535 | 0.0 | 1.3988372093023256 | 6.225 |
| 6 | mated_song | SAG | 0.0 | True | True | False | 8 | 0.975 | 0.125 | 0.0 | 1.097093023255814 | 2.05 |
| 6 | virgin_silence | SAG | 50.0 | True | False | True | 356 | 56.5 | 31.555 | 0.0 | 8.817441860465117 | 45.475 |
| 6 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 1.2354651162790697 | 1.275 |
| 7 | virgin_song | SAG | 50.0 | True | True | False | 382 | 66.15 | 37.99 | 0.0 | 1.2854651162790696 | 1.6 |
| 7 | mated_song | SAG | 0.0 | False | False | True | 2 | 0.225 | 0.055 | 0.0 | 1.0488372093023255 | 1.7 |
| 7 | virgin_silence | SAG | 50.0 | True | True | False | 372 | 65.05 | 35.59 | 0.0 | 0.861046511627907 | 0.625 |
| 7 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 0.9953488372093022 | 0.975 |
| 8 | virgin_song | SAG | 50.0 | True | False | True | 383 | 65.825 | 35.855 | 0.0 | 1.1744186046511629 | 1.025 |
| 8 | mated_song | SAG | 0.0 | False | False | True | 2 | 0.1 | 0.02 | 0.0 | 1.0546511627906976 | 0.35 |
| 8 | virgin_silence | SAG | 50.0 | True | False | True | 385 | 68.325 | 37.945 | 0.0 | 0.65 | 0.35 |
| 8 | mated_silence | SAG | 0.0 | False | True | False | 0 | 0.0 | 0.0 | 0.0 | 1.169767441860465 | 1.2 |
| 9 | virgin_song | SAG | 50.0 | True | True | False | 373 | 63.25 | 35.42 | 0.0 | 27.207558139534886 | 0.175 |
| 9 | mated_song | SAG | 0.0 | True | False | True | 8 | 0.55 | 0.085 | 0.0 | 2.825 | 4.875 |
| 9 | virgin_silence | SAG | 50.0 | True | True | False | 372 | 62.3 | 35.09 | 0.0 | 27.866279069767437 | 0.15 |
| 9 | mated_silence | SAG | 0.0 | False | False | True | 0 | 0.0 | 0.0 | 0.0 | 12.037790697674417 | 0.15 |

## P17-P19
{
  "P17": {
    "mean": 61.792500000000004,
    "se": 0.9421020379980091,
    "n": 10,
    "paired_differences": [
      58.0,
      62.300000000000004,
      61.85,
      57.425,
      58.574999999999996,
      63.324999999999996,
      62.1,
      65.92500000000001,
      65.72500000000001,
      62.7
    ],
    "metric": "vpodn_hz",
    "control": "mated_song",
    "direction": "virgin_song - mated_song",
    "verdict": "supported"
  },
  "P18": {
    "mean": -0.4049999999999997,
    "se": 1.128517956338214,
    "n": 10,
    "paired_differences": [
      -2.4750000000000014,
      -0.375,
      -1.2000000000000028,
      -4.625,
      -4.900000000000006,
      3.3999999999999986,
      6.575000000000003,
      1.1000000000000085,
      -2.5,
      0.9500000000000028
    ],
    "metric": "vpodn_hz",
    "control": "virgin_silence",
    "direction": "virgin_song - virgin_silence",
    "verdict": "not supported"
  },
  "P19": {
    "mean": 34.2645,
    "se": 0.7334592505533093,
    "n": 10,
    "paired_differences": [
      30.17,
      34.0,
      35.144999999999996,
      30.97,
      33.239999999999995,
      35.605,
      34.41,
      37.935,
      35.834999999999994,
      35.335
    ],
    "metric": "pc1_hz",
    "control": "mated_song",
    "direction": "virgin_song - mated_song",
    "verdict": "supported"
  }
}

## P20 (descriptive, no verdict)
[
  {
    "seed": 0,
    "condition": "virgin_song",
    "vpodn_hz": 58.525,
    "pc1_hz": 30.175,
    "accept": true,
    "active_windows": 359,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.42355889724310775,
    "ovidn_hz": 0.0,
    "p1_hz": 4.781395348837209,
    "pip10_hz": 41.175
  },
  {
    "seed": 0,
    "condition": "mated_song",
    "vpodn_hz": 0.525,
    "pc1_hz": 0.005,
    "accept": true,
    "active_windows": 5,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3208020050125313,
    "ovidn_hz": 0.0,
    "p1_hz": 1.219186046511628,
    "pip10_hz": 3.725
  },
  {
    "seed": 0,
    "condition": "virgin_silence",
    "vpodn_hz": 61.0,
    "pc1_hz": 35.09,
    "accept": true,
    "active_windows": 372,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.39097744360902253,
    "ovidn_hz": 0.0,
    "p1_hz": 5.666860465116279,
    "pip10_hz": 1.8
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
    "vpodn_hz": 62.35,
    "pc1_hz": 34.02,
    "accept": true,
    "active_windows": 378,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.37593984962406013,
    "ovidn_hz": 0.0,
    "p1_hz": 1.376162790697674,
    "pip10_hz": 1.975
  },
  {
    "seed": 1,
    "condition": "mated_song",
    "vpodn_hz": 0.05,
    "pc1_hz": 0.02,
    "accept": false,
    "active_windows": 1,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.21804511278195488,
    "ovidn_hz": 0.0,
    "p1_hz": 1.9889534883720932,
    "pip10_hz": 1.65
  },
  {
    "seed": 1,
    "condition": "virgin_silence",
    "vpodn_hz": 62.725,
    "pc1_hz": 33.975,
    "accept": true,
    "active_windows": 368,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3408521303258145,
    "ovidn_hz": 0.03333333333333333,
    "p1_hz": 0.9575581395348837,
    "pip10_hz": 0.675
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
    "vpodn_hz": 62.25,
    "pc1_hz": 35.19,
    "accept": true,
    "active_windows": 378,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.37092731829573933,
    "ovidn_hz": 0.0,
    "p1_hz": 2.563953488372093,
    "pip10_hz": 1.6
  },
  {
    "seed": 2,
    "condition": "mated_song",
    "vpodn_hz": 0.4,
    "pc1_hz": 0.045,
    "accept": true,
    "active_windows": 5,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.23308270676691728,
    "ovidn_hz": 0.0,
    "p1_hz": 1.7825581395348837,
    "pip10_hz": 1.625
  },
  {
    "seed": 2,
    "condition": "virgin_silence",
    "vpodn_hz": 63.45,
    "pc1_hz": 34.605,
    "accept": true,
    "active_windows": 375,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.42355889724310775,
    "ovidn_hz": 0.0,
    "p1_hz": 1.8755813953488372,
    "pip10_hz": 0.05
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
    "vpodn_hz": 57.675,
    "pc1_hz": 31.06,
    "accept": true,
    "active_windows": 360,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40350877192982454,
    "ovidn_hz": 0.0,
    "p1_hz": 2.962209302325582,
    "pip10_hz": 52.325
  },
  {
    "seed": 3,
    "condition": "mated_song",
    "vpodn_hz": 0.25,
    "pc1_hz": 0.09,
    "accept": true,
    "active_windows": 3,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.17543859649122806,
    "ovidn_hz": 0.0,
    "p1_hz": 1.900581395348837,
    "pip10_hz": 1.75
  },
  {
    "seed": 3,
    "condition": "virgin_silence",
    "vpodn_hz": 62.3,
    "pc1_hz": 33.44,
    "accept": true,
    "active_windows": 376,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40852130325814534,
    "ovidn_hz": 0.0,
    "p1_hz": 6.226162790697675,
    "pip10_hz": 2.15
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
    "vpodn_hz": 58.8,
    "pc1_hz": 33.26,
    "accept": true,
    "active_windows": 356,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40350877192982454,
    "ovidn_hz": 0.0,
    "p1_hz": 4.429651162790698,
    "pip10_hz": 5.45
  },
  {
    "seed": 4,
    "condition": "mated_song",
    "vpodn_hz": 0.225,
    "pc1_hz": 0.02,
    "accept": true,
    "active_windows": 3,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.18045112781954886,
    "ovidn_hz": 0.0,
    "p1_hz": 4.2918604651162795,
    "pip10_hz": 1.45
  },
  {
    "seed": 4,
    "condition": "virgin_silence",
    "vpodn_hz": 63.7,
    "pc1_hz": 36.0,
    "accept": true,
    "active_windows": 380,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.45864661654135336,
    "ovidn_hz": 0.0,
    "p1_hz": 1.9186046511627908,
    "pip10_hz": 0.375
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
    "vpodn_hz": 63.4,
    "pc1_hz": 35.625,
    "accept": true,
    "active_windows": 370,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.3684210526315789,
    "ovidn_hz": 0.0,
    "p1_hz": 1.7843023255813955,
    "pip10_hz": 2.175
  },
  {
    "seed": 5,
    "condition": "mated_song",
    "vpodn_hz": 0.075,
    "pc1_hz": 0.02,
    "accept": false,
    "active_windows": 2,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.03007518796992481,
    "ovidn_hz": 0.0,
    "p1_hz": 1.9959302325581396,
    "pip10_hz": 1.175
  },
  {
    "seed": 5,
    "condition": "virgin_silence",
    "vpodn_hz": 60.0,
    "pc1_hz": 34.29,
    "accept": true,
    "active_windows": 361,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.45614035087719296,
    "ovidn_hz": 0.0,
    "p1_hz": 3.3860465116279066,
    "pip10_hz": 0.9
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
    "vpodn_hz": 63.075,
    "pc1_hz": 34.535,
    "accept": true,
    "active_windows": 368,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.39849624060150374,
    "ovidn_hz": 0.0,
    "p1_hz": 1.3988372093023256,
    "pip10_hz": 6.225
  },
  {
    "seed": 6,
    "condition": "mated_song",
    "vpodn_hz": 0.975,
    "pc1_hz": 0.125,
    "accept": true,
    "active_windows": 8,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.2656641604010025,
    "ovidn_hz": 0.0,
    "p1_hz": 1.097093023255814,
    "pip10_hz": 2.05
  },
  {
    "seed": 6,
    "condition": "virgin_silence",
    "vpodn_hz": 56.5,
    "pc1_hz": 31.555,
    "accept": true,
    "active_windows": 356,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.40350877192982454,
    "ovidn_hz": 0.0,
    "p1_hz": 8.817441860465117,
    "pip10_hz": 45.475
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
    "vpodn_hz": 66.15,
    "pc1_hz": 37.99,
    "accept": true,
    "active_windows": 382,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.41102756892230574,
    "ovidn_hz": 0.0,
    "p1_hz": 1.2854651162790696,
    "pip10_hz": 1.6
  },
  {
    "seed": 7,
    "condition": "mated_song",
    "vpodn_hz": 0.225,
    "pc1_hz": 0.055,
    "accept": false,
    "active_windows": 2,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.2631578947368421,
    "ovidn_hz": 0.0,
    "p1_hz": 1.0488372093023255,
    "pip10_hz": 1.7
  },
  {
    "seed": 7,
    "condition": "virgin_silence",
    "vpodn_hz": 65.05,
    "pc1_hz": 35.59,
    "accept": true,
    "active_windows": 372,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.3433583959899749,
    "ovidn_hz": 0.0,
    "p1_hz": 0.861046511627907,
    "pip10_hz": 0.625
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
    "vpodn_hz": 65.825,
    "pc1_hz": 35.855,
    "accept": true,
    "active_windows": 383,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.43859649122807015,
    "ovidn_hz": 0.0,
    "p1_hz": 1.1744186046511629,
    "pip10_hz": 1.025
  },
  {
    "seed": 8,
    "condition": "mated_song",
    "vpodn_hz": 0.1,
    "pc1_hz": 0.02,
    "accept": false,
    "active_windows": 2,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.3533834586466165,
    "ovidn_hz": 0.0,
    "p1_hz": 1.0546511627906976,
    "pip10_hz": 0.35
  },
  {
    "seed": 8,
    "condition": "virgin_silence",
    "vpodn_hz": 68.325,
    "pc1_hz": 37.945,
    "accept": true,
    "active_windows": 385,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.41353383458646614,
    "ovidn_hz": 0.0,
    "p1_hz": 0.65,
    "pip10_hz": 0.35
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
    "vpodn_hz": 63.25,
    "pc1_hz": 35.42,
    "accept": true,
    "active_windows": 373,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.37593984962406013,
    "ovidn_hz": 0.0,
    "p1_hz": 27.207558139534886,
    "pip10_hz": 0.175
  },
  {
    "seed": 9,
    "condition": "mated_song",
    "vpodn_hz": 0.55,
    "pc1_hz": 0.085,
    "accept": true,
    "active_windows": 8,
    "approach": false,
    "retreat": true,
    "retreat_fraction": 0.2531328320802005,
    "ovidn_hz": 0.0,
    "p1_hz": 2.825,
    "pip10_hz": 4.875
  },
  {
    "seed": 9,
    "condition": "virgin_silence",
    "vpodn_hz": 62.3,
    "pc1_hz": 35.09,
    "accept": true,
    "active_windows": 372,
    "approach": true,
    "retreat": false,
    "retreat_fraction": 0.2631578947368421,
    "ovidn_hz": 0.0,
    "p1_hz": 27.866279069767437,
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
virgin_song: {'accept': 10, 'approach': 3, 'retreat': 7}, n=10. Outcomes differ across seeds.
mated_song: {'accept': 6, 'approach': 4, 'retreat': 6}, n=10. Outcomes differ across seeds.
virgin_silence: {'accept': 10, 'approach': 4, 'retreat': 6}, n=10. Outcomes differ across seeds.
mated_silence: {'accept': 0, 'approach': 1, 'retreat': 9}, n=10. Outcomes differ across seeds.

Estimated ten-seed cost (4 x 400 windows each): 1.21 hours, excluding setup and rendering.

## Limitations
- The graft is a type-level transplant from another individual's map; absent target types and unnamed targets are not placed.
- The SAG sign is chosen on functional evidence, not its predicted dopamine transmitter.
- The positive-weight scale is chosen before data using the disclosed calibration ladder.
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
