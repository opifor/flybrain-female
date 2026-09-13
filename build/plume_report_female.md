# Plume tracking, her brain: the same protocol, the second connectome

Run 2026-09-13, 02:57 to 03:08 local: 10 seeds x 3 conditions x 20 s, 12,000 brain runs, 11.1 min on a laptop. Record `build/plume_female_experiment.json`, paths `build/plume_female_trajectories.npz`, picture `build/plume_female_trajectories.png`, the two brains side by side `build/plume_her_vs_him.png`. The male run this repeats is upstream's of 2026-09-12, kept here as `build/plume_experiment_male_upstream.json` and `build/plume_report_male_upstream.md`.

## What was asked

Exactly what upstream asked of the male brain: does cast-and-surge come out of the wiring by itself, with ethyl acetate on the receptor neurons, wind on the Johnston's organ, and the walking descending neurons read out as turn and speed. Protocol v1, unchanged: the same tunnel, wind, meander, seeds, conditions, drive rates, thresholds, windows, four predictions and the 2 SE bar. The seed count is 10, as in the published male run, set by hand as theirs was. The only change is the graph: FlyWire FAFB v783, a female, 139,255 neurons and 3,641,142 signed edges, instead of the male CNS's 165,122.

Both brains get the same gains: calibration `pn05_apl10_kc03` (PN x 0.5, APL x 10, KC x 0.3 on whichever cells carry those type names) and nothing trained. Her graph file carries an excitatory scale of 0.5 that is applied when it loads, on every run of hers in this repo; it is a property of the graph, not a per-type gain, and it is recorded in the run.

## Measured versus chosen

Measured on her: 2,279 olfactory receptor neurons in the same 53 `ORN_<glomerulus>` types the DoOR mapping addresses (his 2,635); 433 wind cells matching `^JO-(C|E)`, 226 rooting left and 207 right, from the graph's soma sides (his 335, 203 and 132, from the annotation table); DNa02, DNa01, MDN and DNp09 with sides. Her wind classes are named without his subtype numbers (JO-C, JO-CA, JO-CL, JO-CM; JO-E, JO-EDC, JO-EDM, JO-EDP, JO-EV, JO-EVL, JO-EVM, JO-EVP); the same expressions select them.

Chosen: everything upstream chose, taken as it is. Nothing new was chosen for her.

## The four predictions

| | Prediction (fixed before data) | Him (upstream, 2026-09-12) | Her (this run) |
|---|---|---|---|
| P1 surge | upwind speed rises in the 1 s after an encounter, > 2 SE | +2.2 +/- 1.4 mm/s, 1.5 SE, n = 9 (16 events): not supported | -0.8 +/- 0.4 mm/s, -2.3 SE, n = 9 (16 events): not supported (she slows) |
| P2 cast | crosswind speed and heading spread both larger in the 2 s after a loss, > 2 SE | crosswind -0.85 +/- 0.26 mm/s (wrong way); spread +0.06 +/- 0.19 deg: not supported | crosswind -0.31 +/- 0.12 mm/s (wrong way); spread -0.19 +/- 0.20 deg: not supported |
| P3 upwind progress | odour > blank and odour > nowind, each > 2 SE | odour - blank -12.8 +/- 4.8 mm; odour - nowind +37.9 +/- 13.0 mm: not supported | odour - blank -34.9 +/- 4.9 mm; odour - nowind -37.9 +/- 5.6 mm: not supported (both the wrong way) |
| P4 source reached | fraction within 0.03 m of the source: odour > blank | 0/10, 0/10, 0/10 | 0/10, 0/10, 0/10 |

Zero of four for him. Zero of four for her.

## Where the two brains differ

Progress (start x minus end x), odour / blank / nowind: him +45.8 / +58.6 / +7.9 mm; her -36.7 / -1.9 / +1.2 mm. He drifts upwind whatever he smells; she walks downwind when she smells, and barely moves when she does not.

The difference is in the default gait under the same motor mapping. His speed command is negative in every condition (MDN, read as backward, above DNa01, read as forward; MDN mean 175 to 183 Hz): with wind sense he faces downwind on over 90 % of steps and backs upwind at 2 to 3 mm/s. Her speed command is positive (MDN 25 to 55 Hz, DNa01 L 105 to 136 Hz): she faces downwind too (facing upwind on 13 % of steps with odour, 7 % blank), but she walks forward, so downwind. Odour raises her forward command from 0.02 (blank) to 0.13 and her ground speed from 2.0 to 3.2 mm/s. Odour reaches her legs. It does not turn her round.

Without wind sense she turns: heading rate 36 deg/s against 5 deg/s in the other two conditions, turn command -0.20. The nowind control holds every wind cell at 50 Hz; her left and right wind populations are unequal (226 against 207 cells), so equal per-cell drive is unequal total drive, and the difference reads as a turn. Upstream's v2 equalises per side for this reason; v1 does not, and v1 is what was replicated.

Her stop neuron is nearly silent (DNp09 2 to 7 Hz against his 70 to 99 Hz), so the stop-and-click convention the roamer uses never fires here.

## What the result means

Under this protocol neither connectome tracks a plume. The one consistent behaviour in each is set by the wind encoding and the motor mapping, not by olfaction: he backs into the wind because his default command is backward, she walks away from it because hers is forward. Two brains, one simulator, one answer, and the answer points at the simulator. Every limit upstream listed for the male run holds here unchanged: no receptor adaptation, no memory across the 50 ms steps, uniform synapses, a chosen wind encoding, a chosen motor mapping, a start inside the plume. The sentence the numbers support is the same as theirs: this simulator, driven this way, does not track a plume with either brain. It says nothing about what either fly does.

Disclosures the runner printed: 27 of 30 trials began above the odour threshold (seeds 0 to 8, as the meander is the same); no encounter in 1 odour, 10 blank and 1 nowind trials; total wind drive in odour and nowind differed by 66 % (his by 77 %), outside the 15 % the protocol asked for, so the odour-versus-nowind comparison is confounded for both brains in the same way.
