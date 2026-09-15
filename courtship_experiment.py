"""Seed-paired courtship: a male sings and a female graph answers."""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from contextlib import contextmanager

import numpy as np
from scipy.stats import spearmanr

import courtship
import backrooms_world as bw
import backrooms_dictionary as bd
from courtship import BlindEye, HerBody, female_groups, female_motor, load_female
from flysim import FlyBrain
from song import Singer, BIOLOGY
from courtship import WaveEar
from courtship import pc1_lesion, install_p1_drive, P1_DRIVE_HZ

# CHOSEN: raw female weights match the male loading convention.
FEMALE_EXC_SCALE = 1.0
# CHOSEN: uniform grey luminance carries no information and floods her brain.
FEMALE_EYE = "blind"
ENABLE_DARK = False
CONDITIONS = {"song": (True, False), "jittered": (True, True),
              "silence": (False, False), "mute": (True, False), "noscent": (True, False),
              "mated": (True, False)}
if ENABLE_DARK:
    CONDITIONS["dark"] = (False, False)
DEFAULT_STEPS = 400
ACCEPT_WINDOWS = 3
PROTOCOL_TEXT = """Protocol v5. CHOSEN before data: all six conditions share seed and arena start.
- virgin: SpsP driven at a tonic SPSN_HZ = 50 Hz every window (CHOSEN; "the sensory pathway that reports an unmated uterus is on").
- mated: SpsP driven at 0 Hz (CHOSEN; "sex peptide has silenced it").
CHOSEN: song, jittered, silence, mute and noscent are virgin; mated is identical to song except her state is mated. This adds a tonic SpsP drive relative to v4 and changes the physics: v5 predictions are fixed again before data. Today's prior experiment had no SpsP drive at all: it silently ran the mated encoding.
CHOSEN: courtship starts when he can see her. She starts 6 mm ahead of him, offset by a seed-derived angle within +/-30 degrees of his heading, facing a seed-derived random heading. All other arena rules are unchanged.
UNCERTAIN: SpsP identity is taken from the FlyWire name and not verified. Biology (not verified in session): active virgin SPSN, through SAG, keep pC1 receptive; sex peptide silences SPSN after mating and receptivity falls. Citations, not verified in session: Yapici et al. 2008 Nature 451:33 (sex peptide receptor); Feng et al. 2014 Neuron 83:135 (SPSN to SAG to pC1); Wang et al. 2021 Nature 589:577 (vpoDN); Wang et al. 2020 Nature 579:101 (oviDN, mating and egg laying).
- song: his previous measured pIP10 mean sets amplitude; per-cell pulse and sine motor means set mode.
- jittered: replay the paired song first-recorded a, m and distance series; each IPI is uniform 15-60 ms, seed-derived RNG (seed, 731). CHOSEN: one trial-wide gain matches delivered RMS to song, including pulse-density differences; his live brain still runs and is recorded.
- silence: her waveform is zero; his brain still runs.
- mute: a lesion, the way the tests already lesion; it asks whether the song we synthesise depends on P1. Outgoing gains zero exactly on every dictionary P1 type; all other gains one.
- noscent: identical to song with both Or47b and contact scent drives to him zero.
- dark is excluded because it duplicates silence while FEMALE_EYE is blind; ENABLE_DARK can re-enable it.
CHOSEN: pIP10 is the descending song command; zero pIP10 produces zero song. Dependence on P1 is tested, not assumed. Amplitude clips pIP10 mean / (1000 / refractory_ms). No explicit P1 gate is applied.
CHOSEN: mode = pulse per-cell mean / (pulse per-cell mean + sine per-cell mean), zero if both zero. Waveform = a * (m * pulse + (1-m) * sine), scaled by existing distance falloff.
CHOSEN: 22050 Hz waveform; 35 ms IPI, 4 ms Hann-windowed 250 Hz pulse, 150 Hz sine; phases and sample clock carry across windows.
CHOSEN: JO-A 100-500 Hz, JO-B 500-2500 Hz, Butterworth order 4, sosfiltfilt with padlen 27 per 50 ms waveform. Each of ten 5 ms band-RMS windows drives SOUND_MAX_HZ * clip(RMS / RMS_FULL, 0, 1), equalised per soma side.
CHOSEN: RMS_FULL is JO-A RMS of a one-second full-amplitude pure pulse train including filter edges, computed once at import and printed with ear settings.
CHOSEN: her brain runs in real time so pulse timing can reach it. Ten carried 25-step runs; full-window answers average all 250 steps. His constructor also uses 250 steps: both brains run 50 ms per world step.
CHOSEN: female raw weights (FEMALE_EXC_SCALE = 1.0), female blind eye. Uniform grey is not contrast vision. Male annotation-backed columns and soma sides when available; otherwise luminance and unknown sides, with no invented identities.
CHOSEN: female scent = SMELL_MAX_HZ * falloff(distance) into ORN_VA1v; putative_ppk23 only within CONTACT_MM = 2.0 mm. His ORN_DA1 cVA drive is zero because no other male is present.
CHOSEN: P1 > 0 counts active windows; P7 correlates a[1:], m[1:] with her distance[:-1], speed[:-1]. No adaptation mechanism is added. These readouts decide nothing.
MEASURED: brain rates, song amplitude and mode, delivered waveform RMS, distance, speed, LC10a and P1 activity. Nothing gates either brain.

Predictions fixed before data (paired difference > 2 SE across seeds; P5 requires both comparisons):
- P1 answer: her vpoDN, song > silence.
- P2 pC1: song > silence.
- P3 timing: her vpoDN, song > jittered (now meaningful: a real-time ear and a 35 ms rhythm).
- P4 approach: last-quarter distance, song < silence.
- P5 command: pIP10 mean rate, song > mute, and delivered song RMS, song > mute (the causal chain P1 → pIP10 → song).
- P6 answer follows command: her vpoDN, song > mute.
- P8 presence: his P1 mean rate, song > noscent.
- P8b (descriptive): his LC10a mean rate, song versus noscent; no verdict.
- P0 baselines (descriptive): silence/mute active windows per seed.
- P7 (descriptive): his P1 active windows, LC10a mean rate per window (275 cells), and lagged correlations of his song amplitude a and mode m with her previous distance and speed.
- P9 she can say no: her vpoDN mean rate, song (virgin) > mated.
- P10 rejection (descriptive, no verdict): oviDN mean rate and retreat fraction per seed, mated vs song.
- Seed spread: per condition, seeds with accept / no-accept; if `mated` gives accept on every seed the report says "the state did not produce a no" in one sentence.
- P11 he sees her (descriptive with a verdict rule): his LC10a mean rate in windows with sight > in windows without sight, paired within trial, across seeds, > 2 SE (song condition).
- P12 adaptation (descriptive, no verdict): lagged correlations already in P7, plus `m[1:]` vs `LC10a[:-1]` (does his song mode follow what his LC10a saw a window earlier).
MEASURED: per-window ovidn_hz (mean over six oviDN cells), spsp_hz and sight_ok (silhouette reaches his retinal samples); per-trial sight fraction. P11 uses only song trials with both sight and no-sight windows; missing pairs are excluded and fewer than two pairs is undetermined. P10 retreat fraction is the fraction of adjacent pre-window distances that increase, excluding the first window, which has no previous distance.
- Seed spread: accept / approach / retreat per seed and condition; say plainly when every seed gives the same outcome.
""" + "\n" + BIOLOGY
PROTOCOLS = {"v5": {"text": PROTOCOL_TEXT, "conditions": CONDITIONS,
    "default_seeds": 10, "steps": DEFAULT_STEPS, "seed_ladder": (10, 8),
    "budget_s": 9000, "accept_windows": ACCEPT_WINDOWS, "sim_steps": 250,
    "world_dt_s": bw.WORLD_DT_S, "state_carry": True,
    "trial_text": "Trial: `steps` world steps (default 400 = 20 s at 0.05 s; `--quick 1` = 2 seeds x 80 steps). Both brains carry state across steps (the room already does). Record per step: positions and headings of both, distance, her speed, her `vpodn_hz`, `pc1_hz`, her delivered `sound_hz`, his `song_hz`, `p1_hz`, `pulse_hz`, `sine_hz`, both her sound channels, his delivered `sound_hz`; trial eye choice, sides restored, and sight_ok.",
    "outcome_text": "Per-trial outcome (CHOSEN, disclosed): `accept` = her vpoDN window rate exceeds 0 Hz in at least `ACCEPT_WINDOWS` = 3 windows of the trial; `approach` = mean distance in the last quarter of the trial is smaller than in the first quarter; `retreat` = the opposite. Report all three per seed and per condition in a table in the JSON and in the report; never only the pooled mean.",
    "jitter_rng": "numpy default_rng(SeedSequence([seed, 731])).uniform(.015, .060)",
    "quarter_rule": "floor(steps / 4) windows at each end; geometry before the window",
    "budget_note": "First trial measures both graphs per step; choose largest fitting seed count, with floor 8 (requests below 8 kept). Setup and rendering excluded from estimate."}}
LIMITATIONS = [
    "her state is a chosen tonic drive on SpsP, an identity taken from the FlyWire name and not verified; oviDN is a readout of a descending command, she has no body to extrude an ovipositor with; the start geometry is chosen so that she is visible to him",
    "His wing motor neurons run near ceiling from background activity; the song is taken from the command neuron pIP10, not from the motor sum. Mode still uses the motor means.",
    "Her ear now hears a waveform in 5 ms sub-windows; the brain runs in real time for her. His brain also runs in real time.",
    "Pulse rhythm and carriers are chosen synthesis, not measured spike timing or a biomechanical wing model.",
    "The fork's zero-phase filter uses the whole current 50 ms block; boundary effects and within-block lookahead remain. Sample bins alternate lengths at 22050 Hz.",
    "Jitter changes pulse density as well as timing (mean IPI 37.5 ms versus 35 ms). Replay holds source amplitude, mode and distance fixed; one trial-wide gain matches energy. Local envelopes and spectral energy can still differ.",
    "The contact chemosensory cells are a putative receptor label (putative_ppk23), not verified ppk23 expression.",
    "His female-scent input is a chosen drive at the smell ceiling with distance falloff, not a measured pheromone plume; the cVA channel is held at zero because there is no other male.",
    "He is inside the loop: his trajectory and song can change when she moves differently. Mute additionally changes his P1 outgoing gains.",
    "vpoDN identified as DNp37 by alias, 2 cells; pC1a-e 10 cells. No pheromone channel to her.",
    "In closed-loop 50 ms windows, silencing P1 outputs did not reduce pIP10 in the v4 smoke run; pIP10 is driven mainly by AVLP717m and aIPg7 in this graph, so the song dependence on P1 is not established here.",
    "Male P1 membership is the dictionary's uncertain 86-cell group. Outgoing-gain lesion need not silence P1's own spikes.",
    "No adaptation mechanism was added on his side; correlation does not establish causation.",
    "CHOSEN: female raw weights for parity; female eye blind. Earlier luminance silence measured vpoDN 54-206 Hz; contrast/motion vision remains a later step.",
    "Dark and silence coincide with the blind female eye.",
    "Male eye and soma-side availability are recorded per trial; gains remain uncalibrated.",
    "Distance changes include both bodies; approach is not an isolated female command.",
    "Retired v3 limitations: rate-only ear, motor-sum song, 12 ms brain windows, separate motor-reference clipping and shuffled-rate multiset no longer describe this protocol."]
PUBLISHED = Path("build/courtship")
PUBLISHED_ADDENDUM = Path("build/courtship_addendum")
PUBLISHED_V7 = Path("build/courtship_v7")
PUBLISHED_V8 = Path("build/courtship_v8")
PUBLISHED_V9 = Path("build/courtship_v9")
PUBLISHED_V10 = Path("build/courtship_v10")
PUBLISHED_V11 = Path("build/courtship_v11")
V6_CONDITIONS = {"gated": (True, False), "p1drive": (True, False)}
V6_PROTOCOL_TEXT = """Protocol v6 ADDENDUM. Only gated and p1drive are run; controls are the v5 song records paired by seed. Seed RNGs, start geometry, steps, brains and all other v5 song settings are retained.
CHOSEN gated: identical to v5 song (virgin), with outgoing gains 0.0 on exactly pC1a, pC1b, pC1c, pC1d, pC1e; other gains one. a mated female cannot be encoded through her own sex-peptide pathway in this map, because the SPSN and SAG axons carry no synapses here; the receptivity gate is closed by hand instead, as a lesion, the way the tests lesion.
CHOSEN p1drive: identical to v5 song, plus P1_DRIVE_HZ = 100 Hz to his P1 cells every window. asks whether the courtship command group can drive the song and her answer from above; it is an intervention, not a claim that P1 fires like this on its own.
Predictions, fixed before data:
- P9' she can be made to say no: her vpoDN mean rate, v5 song > gated (paired by seed), > 2 SE.
- P10' rejection (descriptive): oviDN mean and retreat fraction, gated vs v5 song.
- P13 the command can sing: his pIP10 mean rate and the delivered song RMS, p1drive > v5 song, both > 2 SE (joint verdict as P5).
- P14 the command reaches her: her vpoDN mean rate, p1drive > v5 song, > 2 SE.
- P15 (descriptive): his P1 active windows and LC10a in p1drive vs v5 song.
- Seed spread: per condition, seeds with accept / no-accept and approach / retreat; say plainly when every seed gives the same outcome.
"""
PROTOCOLS["v6"] = dict(PROTOCOLS["v5"], text=V6_PROTOCOL_TEXT,
    conditions=V6_CONDITIONS, budget_note="Run exactly the requested paired baseline seeds; no seed-count adaptation.")
V6_LIMITATIONS = [
    "Measured on the real graphs in GPU 250-step probes: the female brain-only FlyWire FAFB v783 map has no outgoing synapses from any of seven SpsP cells or either of two AN_SMP_2 (SAG) cells. Driving SpsP at 25-400 Hz or SAG at 25-200 Hz left pC1, vpoDN and oviDN unchanged within noise. v5 mated drives a dead switch: P9 cannot be supported for this anatomical reason. Gated is a manual lesion, not a mating-state encoding.",
    "Measured male probes: silence gave P1 0 Hz; Or47b scent gave P1 24-50 Hz, putative_ppk23 contact 24-46 Hz, and LC10a vision 26 Hz. LC10a drive gave pIP10 111 Hz; direct P1 drive at 100 Hz gave pIP10 76 Hz. P1 can drive pIP10, but vision also drives it, explaining why mute did not lower pIP10 in the loop. These are motivating probes, not v6 outcomes.",
    *LIMITATIONS,
    "The baseline is a separate v5 run; its path and byte SHA256 identify the controls. P1 drive is an imposed intervention, not spontaneous firing. The retained v5 state-drive limitation describes the disconnected tonic input; v6 closes pC1 by hand."]

V7_GRAPH = Path('build/graph_female_sag.npz')
V7_EXC_SCALE = .7
V7_CONDITIONS = {'virgin_song': (True, False), 'mated_song': (True, False),
                 'virgin_silence': (False, False), 'mated_silence': (False, False)}
V7_PREDICTIONS = """- P17 she can say no: her vpoDN mean rate, virgin_song > mated_song.
- P18 she still hears: her vpoDN, virgin_song > virgin_silence.
- P19 the state reaches her receptivity cells: her pC1 mean rate, virgin_song > mated_song.
- P20 (descriptive, no verdict): mated_song vs mated_silence vpoDN and pC1; accept rule per condition; approach/retreat per condition; oviDN per condition; his P1/pIP10 per condition (does her state change his song, descriptively)."""
V7_CALIBRATION = """Calibration record, measured before v7 data: GPU, eight carried windows x 250 steps, JO 60 Hz.
Grafted raw graph: SAG 0 / 50 / 200 Hz -> pC1 7.0 / 28.0 / 68.3 Hz; raw vpoDN 172 vs 160 Hz (SAG 0 vs 50).
Positive-weight scale -> vpoDN Hz (SAG 0 vs 50): 0.9 -> 53.8 vs 100.0; 0.8 -> 33.8 vs 50.0; 0.7 -> 2.5 (1/8 windows active) vs 38.8 (5/8), and 87.5 at SAG 100; 0.6 -> 5.0 vs 80.0. Silence gives 0 at every scale.
CHOSEN before data: FEMALE_EXC_SCALE = 0.7, for the female's vpoDN to depend on her state while silence still drives nothing. Nothing else is tuned.
Second calibration record, measured after the quick run and before the ten-seed run, same method, on the grafted graph: with SAG driven and NO sound, her vpoDN fires at every rate tested (scale 0.7: SAG 5 -> 12.5 Hz, 10 -> 22.5, 20 -> 43.8, 50 -> 67.5; scale 0.8: SAG 5 -> 5.0, 15 -> 73.8, 50 -> 78.8; scale 0.6: SAG 5 -> 8.8, 50 -> 72.5), and sound plus SAG is at most additive (scale 0.7, JO 60 Hz: SAG 0 -> 25.0, 50 -> 38.8). No scale or tonic rate in these ladders made her yes require both the song and her state. The protocol is kept as written: STATE_HZ 50, scale 0.7. P18 therefore may fail; if it does, the honest reading is that in this map her state opens the gate on its own and the song is not required once she is willing."""
V7_PROTOCOL_TEXT = """Protocol v7. All v5 song/silence settings are retained except the female graph, positive-weight scale, state group and four conditions specified here.
CHOSEN: female graph build/graph_female_sag.npz, a type-name transplant of named BANC SAG outputs, evenly split over matching FAFB targets and both SAG cells; +1 sign and 0.275 mV per synapse. Source SHA256s and the sign choice are recorded in the graft metadata.
CHOSEN: state enters at SAG, matching ^(AN_SMP_2|ANXXX983)$; virgin = STATE_HZ = 50 Hz tonic, mated = 0 Hz. SPSN themselves are not modelled.
CHOSEN: virgin_song and mated_song deliver song exactly as v5 song; virgin_silence and mated_silence zero her waveform exactly as v5 silence. His brain remains live in all four conditions.
His side is unchanged from v5: raw male, same eye, same scent, same start geometry, same seeds. No lesion or P1 drive is added.
""" + V7_CALIBRATION + "\nPredictions fixed before data (verdict rule as v5: paired difference across ten seeds > 2 SE):\n" + V7_PREDICTIONS + "\n" + "\n".join(
    line for line in PROTOCOL_TEXT.splitlines()
    if line.startswith(('CHOSEN: courtship starts', '- song:', '- silence:', 'CHOSEN: pIP10',
                        'CHOSEN: mode', 'CHOSEN: 22050', 'CHOSEN: JO-A', 'CHOSEN: RMS_FULL',
                        'CHOSEN: her brain', 'CHOSEN: female scent'))) + "\n" + BIOLOGY
PROTOCOLS['v7'] = dict(PROTOCOLS['v5'], text=V7_PROTOCOL_TEXT, conditions=V7_CONDITIONS,
    female_graph=V7_GRAPH.as_posix(), female_exc_scale=V7_EXC_SCALE, state_group='SAG',
    jitter_rng=None)
V7_LIMITATIONS = [
    'The graft is a type-level transplant from another individual\'s map; absent target types and unnamed targets are not placed.',
    'The SAG sign is chosen on functional evidence, not its predicted dopamine transmitter.',
    'The positive-weight scale is chosen before data using the disclosed calibration ladder.',
    'SPSN themselves are not modelled; the state enters at SAG.',
    'The male is unchanged and runs at raw scale.',
    'oviDN is a descending command readout; she has no ovipositor body model. Start geometry is chosen so she is visible to him.',
    *[s for i, s in enumerate(LIMITATIONS) if i not in (0, 5, 8, 13, 17)],
    'He is inside the loop: his trajectory and song can change when she moves differently. Female eye remains blind; contrast/motion vision remains a later step.']

SAG_AUDIT_CORRECTION = (
    'Correction to the historical v5/v6 anatomical explanation: the female export does '
    'carry SAG outgoing synapses. Their serotonin consensus maps to sign zero in '
    'build_graph_female.py, so the transmitter-sign rule drops their edges. This is '
    'a modelling exclusion, not an anatomical absence. The earlier protocol and '
    'limitation strings are retained unchanged as published records.')
V7_LIMITATIONS.append(SAG_AUDIT_CORRECTION)
V8_GRAPH = Path('build/graph_female_own_sag.npz')
V8_CALIBRATION = Path('build/sag_calibration.json')
V8_STATE_PATTERN = '^(AN_SMP_2|AN_FLA_SMP_2|ANXXX983)$'
V8_PROTOCOL_TEXT = """Protocol v8. v7 grafted BANC's measured SAG outputs onto her map; this audit found her own export already carries the same route, dropped by the transmitter-sign rule; v8 restores her own synapses instead and keeps everything else. The BANC measurement stands as a second individual showing the same wiring.
CHOSEN: female graph build/graph_female_own_sag.npz restores her individual SAG pre/post pairs at +1 sign and 0.275 mV per synapse, with the export's >= 5 synapse pair floor and only postsynaptic cells in the graph. Source and graph SHA256s and restore metadata are recorded.
CHOSEN: state enters at SAG, matching ^(AN_SMP_2|AN_FLA_SMP_2|ANXXX983)$; both FAFB SAG types carry the state. Virgin = STATE_HZ tonic every window, mated = 0 Hz. SPSN themselves are not modelled.
CHOSEN: FEMALE_EXC_SCALE = 0.7, carried over from the v7 calibration. The before-data ladder is recorded below; 0.7 is retained even if silence produces nonzero vpoDN. No tuning follows this ladder.
CHOSEN: virgin_song and mated_song deliver song exactly as v5 song; virgin_silence and mated_silence zero her waveform exactly as v5 silence. His brain remains live in all four conditions.
His side is unchanged from v5: raw male, same eye, same scent, same start geometry, same seeds. No lesion or P1 drive is added.
""" + '\nPredictions fixed before data (verdict rule as v5: paired difference across ten seeds > 2 SE):\n' + V7_PREDICTIONS + '\n' + '\n'.join(
    line for line in PROTOCOL_TEXT.splitlines()
    if line.startswith(('CHOSEN: courtship starts', '- song:', '- silence:', 'CHOSEN: pIP10',
                        'CHOSEN: mode', 'CHOSEN: 22050', 'CHOSEN: JO-A', 'CHOSEN: RMS_FULL',
                        'CHOSEN: her brain', 'CHOSEN: female scent'))) + '\n' + BIOLOGY
PROTOCOLS['v8'] = dict(PROTOCOLS['v7'], text=V8_PROTOCOL_TEXT,
    female_graph=V8_GRAPH.as_posix(), state_pattern=V8_STATE_PATTERN)
V8_LIMITATIONS = [SAG_AUDIT_CORRECTION,
    'The restored edges are her own measured synapses. BANC is a second individual, not a donor for v8.',
    'Both FAFB SAG types are restored and driven; AN_FLA_SMP_2 has additional targets beyond the pC1 route.',
    'CHOSEN: the SAG effect sign is +1 on functional evidence; neither FAFB serotonin nor BANC dopamine fixes that sign.',
    'CHOSEN: positive-weight scale 0.7 is carried over from v7, without tuning on the v8 ladder.',
    *V7_LIMITATIONS[3:-1]]


def v8_graph_record():
    if not V8_GRAPH.is_file():
        raise ValueError('v8 requires build/graph_female_own_sag.npz; run restore_sag.py first')
    from graft_sag import sha256
    with np.load(V8_GRAPH, allow_pickle=False) as z:
        restore = json.loads(z['restore'].item())
        counts = {t: int(np.sum(z['types'] == t)) for t in ('AN_SMP_2', 'AN_FLA_SMP_2', 'ANXXX983')}
    return dict(file=V8_GRAPH.name, path=Path(os.path.relpath(V8_GRAPH)).as_posix(),
                sha256=sha256(V8_GRAPH), restore=restore, state_cells=sum(counts.values()),
                state_cells_per_type=counts)


def v8_protocol_spec(graph_record):
    if not V8_CALIBRATION.is_file():
        raise ValueError('v8 requires the before-data ladder; run calibrate_sag.py first')
    calibration = json.loads(V8_CALIBRATION.read_text(encoding='utf-8'))
    if calibration['graph_sha256'] != graph_record['sha256']:
        raise ValueError('v8 calibration graph SHA256 mismatch')
    return dict(PROTOCOLS['v8'], calibration=calibration,
                text=V8_PROTOCOL_TEXT + f"\nState group: {graph_record['state_cells']} cells; "
                + str(graph_record['state_cells_per_type']) + f'; STATE_HZ = {courtship.STATE_HZ:g} Hz.\n'
                + calibration['text'])


def v7_graph_record():
    if not V7_GRAPH.is_file():
        raise ValueError('v7 requires build/graph_female_sag.npz; run graft_sag.py first')
    from graft_sag import sha256
    with np.load(V7_GRAPH, allow_pickle=False) as z:
        graft = json.loads(z['graft'].item())
    return dict(file=V7_GRAPH.name, path=Path(os.path.relpath(V7_GRAPH)).as_posix(), sha256=sha256(V7_GRAPH), graft=graft)


def summarise_v7(rows):
    indexed = {(r['seed'], r['condition']): r for r in rows}
    seeds = sorted({r['seed'] for r in rows})
    predictions = {}
    for label, metric, control in (('P17', 'vpodn_hz', 'mated_song'),
                                  ('P18', 'vpodn_hz', 'virgin_silence'),
                                  ('P19', 'pc1_hz', 'mated_song')):
        diffs = [indexed[s, 'virgin_song'][metric] - indexed[s, control][metric] for s in seeds]
        mean = float(np.mean(diffs))
        se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs) > 1 else None
        predictions[label] = dict(mean=mean, se=se, n=len(diffs), paired_differences=diffs,
            metric=metric, control=control, direction='virgin_song - ' + control,
            verdict=verdict(mean, se, len(diffs)))
    metrics = ('seed', 'condition', 'vpodn_hz', 'pc1_hz', 'accept', 'active_windows',
               'approach', 'retreat', 'retreat_fraction', 'ovidn_hz', 'p1_hz', 'pip10_hz')
    return dict(predictions=predictions, P20=[{k: r[k] for k in metrics} for r in rows])


def write_v7_report(json_path, data):
    lines = [f"# Courtship {data['protocol']}", '', 'Quick runs are smoke tests; two-seed verdicts are not the ten-seed experiment.',
             data['protocol_spec']['text'], '', '## Female graph record',
             json.dumps(data['female_graph'], indent=2), '', '## Per-seed outcomes / P20',
             data['protocol_spec']['outcome_text']]
    keys = ('seed', 'condition', 'state_group', 'state_drive_hz', 'accept', 'approach', 'retreat',
            'active_windows', 'vpodn_hz', 'pc1_hz', 'ovidn_hz', 'p1_hz', 'pip10_hz')
    lines += ['| ' + ' | '.join(keys) + ' |', '| ' + ' | '.join(['---'] * len(keys)) + ' |']
    lines += ['| ' + ' | '.join(str(r[k]) for k in keys) + ' |' for r in data['outcomes']]
    lines += ['', '## P17-P19', json.dumps(data['summary']['predictions'], indent=2), '', '## Result']
    lines.append(' '.join(
        f"{label} was {p['verdict']}: {p['direction']} in {p['metric']} was {p['mean']:.6g} Hz "
        + f"(SE {p['se']}, n={p['n']}); the required positive difference must exceed 2 SE."
        for label, p in data['summary']['predictions'].items()))
    lines += ['', '## P20 (descriptive, no verdict)', json.dumps(data['summary']['P20'], indent=2)]
    for c in V7_CONDITIONS:
        rr = [r for r in data['outcomes'] if r['condition'] == c]
        counts = {k: sum(r[k] for r in rr) for k in ('accept', 'approach', 'retreat')}
        same = len({tuple(r[k] for k in counts) for r in rr}) == 1
        lines.append(f"{c}: {counts}, n={len(rr)}. " + ('Every seed gives the same outcome.' if same else 'Outcomes differ across seeds.'))
    hours = data['estimated_ten_seed_hours']
    limitations = list(data['limitations'])
    if SAG_AUDIT_CORRECTION not in limitations:
        limitations.append(SAG_AUDIT_CORRECTION)
    lines += ['', f'Estimated ten-seed cost (4 x 400 windows each): {hours:.3g} hours, excluding setup and rendering.',
              '', '## Limitations', *['- ' + s for s in limitations]]
    destination = Path(str(json_path).replace('_experiment.json', '_report.md'))
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return destination


def read_baseline(path, seeds, steps, brain):
    if not path:
        raise ValueError("v6 requires --baseline")
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    if data.get("protocol") != "v5" or data.get("seeds") != seeds or data.get("steps") != steps:
        raise ValueError("baseline protocol, seeds or steps mismatch")
    env = data.get("environment", {})
    classes = env.get("brain_classes", {"male": env.get("brain_class"), "female": env.get("brain_class")})
    if classes != {"male": brain, "female": brain}:
        raise ValueError("baseline male/female brain classes mismatch")
    for key, expected in (("female_exc_scale", FEMALE_EXC_SCALE), ("female_eye", FEMALE_EYE)):
        if data.get(key) != expected:
            raise ValueError("baseline settings mismatch: " + key)
    song = [r for r in data["outcomes"] if r["condition"] == "song"]
    if sorted(r["seed"] for r in song) != seeds:
        raise ValueError("baseline song seeds mismatch")
    for key in ("sim_steps", "world_dt_s", "state_carry", "accept_windows", "quarter_rule"):
        if data.get("protocol_spec", {}).get(key) != PROTOCOLS["v5"][key]:
            raise ValueError("baseline protocol settings mismatch: " + key)
    for r in data["outcomes"]:
        check_baseline_start(data, r["seed"], r["start"])
    return data, dict(path=Path(os.path.relpath(path)).as_posix(), sha256=hashlib.sha256(raw).hexdigest(),
                      date=data.get("date", "not recorded"))


def check_baseline_start(baseline, seed, start):
    expected = next(r["start"] for r in baseline["outcomes"] if r["seed"] == seed and r["condition"] == "song")
    if expected != start:
        raise ValueError(f"baseline start mismatch for seed {seed}")


def summarise_v6(rows, baseline_rows):
    indexed = {(r["seed"], r["condition"]): r for r in rows + baseline_rows}
    seeds = sorted({r["seed"] for r in rows})
    predictions = {}
    for label, metric, condition, sign in (("P9'", "vpodn_hz", "gated", -1),
        ("P13_command", "pip10_hz", "p1drive", 1), ("P13_rms", "delivered_rms", "p1drive", 1),
        ("P14", "vpodn_hz", "p1drive", 1)):
        diffs = [sign*(indexed[s, condition][metric]-indexed[s, "song"][metric]) for s in seeds]
        mean = float(np.mean(diffs))
        se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs) > 1 else None
        predictions[label] = dict(mean=mean, se=se, n=len(diffs), paired_differences=diffs,
            metric=metric, control="v5 song", direction=f"{condition} - v5 song" if sign == 1 else "v5 song - gated",
            verdict=verdict(mean, se, len(diffs)))
    spread = {}
    for c in V6_CONDITIONS:
        rr = [r for r in rows if r["condition"] == c]
        counts = {k: sum(r[k] for r in rr) for k in ("accept", "approach", "retreat")}
        same = len({tuple(r[k] for k in counts) for r in rr}) == 1
        spread[c] = dict(n=len(rr), **counts, no_accept=len(rr)-counts["accept"],
            accept_seeds=[r["seed"] for r in rr if r["accept"]], no_accept_seeds=[r["seed"] for r in rr if not r["accept"]],
            sentence=f"{c}: every seed gives the same outcome." if same else f"{c}: outcomes differ across seeds.")
    descriptive = {}
    for label, c, metrics in (("P10'", "gated", ("ovidn_hz", "retreat_fraction")),
                             ("P15", "p1drive", ("p1_active_windows", "lc10a_hz"))):
        descriptive[label] = [{k: indexed[s, cc][k] for k in ("seed", "condition", *metrics)}
                              for s in seeds for cc in (c, "song")]
    joint = [predictions[k]["verdict"] for k in ("P13_command", "P13_rms")]
    return dict(predictions=predictions, seed_spread=spread, **descriptive,
                P13_verdict="supported" if all(v == "supported" for v in joint) else
                "undetermined" if len(seeds) < 2 else "not supported")


def write_v6_report(json_path, data):
    lines = ["# Courtship v6 addendum", "", "Baseline: " + str(data["baseline"]),
        "Quick runs are smoke tests, not the full experiment.", data["protocol_spec"]["text"],
        "| Seed | Condition | Accept | Approach | Retreat | vpoDN Hz | pIP10 Hz | Delivered RMS |",
        "|---:|---|---|---|---|---:|---:|---:|"]
    for r in data["outcomes"]:
        lines.append("| " + " | ".join(str(r[k]) for k in ("seed", "condition", "accept", "approach", "retreat", "vpodn_hz", "pip10_hz", "delivered_rms")) + " |")
    for label, p in data["summary"]["predictions"].items():
        lines.append(f"{label}: {p}")
    lines.append("P13 joint verdict: " + data["summary"]["P13_verdict"])
    for label in ("P10'", "P15"):
        lines += [label + " (descriptive):", *[str(r) for r in data["summary"][label]]]
    for s in data["summary"]["seed_spread"].values():
        lines.append(str(s))
    lines += ["", "## Limitations", *["- " + s for s in data["limitations"]]]
    destination = Path(str(json_path).replace("_experiment.json", "_report.md"))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


class LuminanceEye:
    """CHOSEN: the real-brain integration test's luminance encoding."""
    def __init__(self, fb):
        self.on_idx = fb.where(type_re="^L1$")
        self.off_idx = fb.where(type_re="^L2$")

    def look(self, img, cx, cy):
        h, w = img.shape
        x0, x1 = int(cx - bw.EYE_FOV_W / 2), int(cx + bw.EYE_FOV_W / 2)
        y0, y1 = int(cy - bw.EYE_FOV_H / 2), int(cy + bw.EYE_FOV_H / 2)
        m = float(img[max(0, y0):min(h, y1), max(0, x0):min(w, x1)].mean())
        return {tuple(self.on_idx): np.full(len(self.on_idx), m * 180, np.float32),
                tuple(self.off_idx): np.full(len(self.off_idx), (1-m) * 108, np.float32)}


class ExperimentRoom(bw.Room):
    def configure(self, seed, condition, song_sound=None):
        if condition not in CONDITIONS and condition not in V6_CONDITIONS and condition not in V7_CONDITIONS and condition not in V10_CONDITIONS and condition not in V11_CONDITIONS and condition != "dark":
            raise ValueError("unknown condition")
        self.condition = condition
        rng = np.random.default_rng(np.random.SeedSequence([seed, 905]))
        angle = self.arena.A.heading + rng.uniform(-np.pi/6, np.pi/6)
        # Translate the pair together only if needed to retain the existing arena bounds.
        dx, dy = 6*np.cos(angle), 6*np.sin(angle)
        margin = bw.START_MARGIN_MM
        self.arena.A.x = float(np.clip(self.arena.A.x, margin-min(0., dx), bw.ARENA_MM-margin-max(0., dx)))
        self.arena.A.y = float(np.clip(self.arena.A.y, margin-min(0., dy), bw.ARENA_MM-margin-max(0., dy)))
        self.arena.B.x, self.arena.B.y = self.arena.A.x+dx, self.arena.A.y+dy
        self.arena.B.heading = float(rng.uniform(-np.pi, np.pi))
        self.bodies["B"].state = "mated" if condition in ("mated", "mated_song", "mated_silence") else "virgin"
        body = self.bodies["A"]
        groups = getattr(body, "groups", {})
        self.singer = Singer(seed, condition == "jittered",
            pulse_cells=len(groups.get("song_pulse_mn", range(8))),
            sine_cells=len(groups.get("song_sine_hg1", range(2))),
            pip10_full=1000/getattr(getattr(getattr(body, "fb", None), "p", None), "refractory", 2.2))
        self.previous_rates = dict(pip10_hz=0., pulse_hz=0., sine_hz=0.)
        self.replay = []
        self.replay_step = 0
        if condition == "jittered":
            if song_sound is None:
                raise ValueError("jittered requires the paired song trace first")
            for a, m, d in zip(song_sound["a"], song_sound["m"], song_sound["distance_mm"]):
                wave = self.singer.render(a*self.singer.pip10_full,
                    m*self.singer.pulse_cells, (1-m)*self.singer.sine_cells,
                    attenuation=self.channels.falloff(d))
                self.replay.append((wave, dict(self.singer.record, source_distance_mm=float(d))))
            raw = np.sqrt(np.mean([r[1]["delivered_rms"]**2 for r in self.replay]))
            target = np.sqrt(np.mean(song_sound["delivered_rms"]**2))
            if raw == 0 and target > 0:
                raise ValueError("cannot energy-match an empty jittered waveform")
            gain = float(target/raw) if raw else 1.
            for wave, record in self.replay:
                wave *= gain
                record.update(delivered_rms=float(np.sqrt(np.mean(wave**2))), replay_gain=gain)

    def listener_scent(self, smell):
        if self.condition == "noscent":
            return {"A": {"female_scent_orn": 0., "female_scent_contact": 0., bw.SMELL_KEY: 0.}, "B": 0.}
        if self.condition in ('noscent_orn', 'noscent_contact'):
            male = dict(smell['A'])
            male['female_scent_' + self.condition.removeprefix('noscent_')] = 0.
            return dict(smell, A=male)
        return smell

    def listener_sound(self, sound_hz):
        if self.condition == "jittered":
            wave, self.singer.record = self.replay[self.replay_step]
            self.replay_step += 1
            return wave.copy()
        wave = self.singer.render(**self.previous_rates,
                                  attenuation=self.channels.falloff(self.arena.distance()))
        if self.condition in ("silence", "dark", "virgin_silence", "mated_silence"):
            wave[:] = 0.
            self.singer.record["delivered_rms"] = 0.
        return wave

    def step(self):
        result = super().step()
        male = result["A"]
        rates = male.get("rates", {})
        self.previous_rates = dict(pip10_hz=rates["pIP10"],
                                   pulse_hz=male["pulse_hz"], sine_hz=male["sine_hz"])
        result["song_wave"] = dict(self.singer.record)
        result["sound_clipped"] = result["B"].get("ear_clipped", (False, False))
        return result


def p1_lesion(fb, groups):
    gains = np.ones(len(fb.type_names), dtype=np.float32)
    gains[np.unique(fb.type_code[groups["P1"]])] = 0.
    return gains


def build_room(seed, condition, song_sound=None, brains=None,
               annotations_path="data/body-annotations.feather", brain_class=FlyBrain, protocol=None):
    """One construction for every condition; new bodies reset both states."""
    cls = bw.brain_class(brain_class) if isinstance(brain_class, str) else brain_class
    v7 = condition in V7_CONDITIONS or protocol in ('v9', 'v10', 'v11', 'v12')
    if v7 and brains is None:
        (v8_graph_record if protocol in ('v8', 'v9', 'v10', 'v11', 'v12') else v7_graph_record)()
    female_options = dict(exc_scale=V7_EXC_SCALE if v7 else FEMALE_EXC_SCALE, brain_class=cls)
    if v7:
        female_options['path'] = V8_GRAPH if protocol in ('v8', 'v9', 'v10', 'v11', 'v12') else V7_GRAPH
    if protocol == 'v12' and brains is None:
        v12_graph_record()
    male, female = brains if brains is not None else (
        cls(graph_path=V12_GRAPH) if protocol == 'v12' else cls(), load_female(**female_options))
    eye = BlindEye(female) if condition == "dark" or FEMALE_EYE == "blind" else LuminanceEye(female)
    groups_b = female_groups(female, sag_pattern=V8_STATE_PATTERN) if protocol in ('v8', 'v9', 'v10', 'v11', 'v12') else female_groups(female)
    body = HerBody("B", female, eye, groups_b,
                   female_motor(female), seed=seed * 2 + 2, sim_steps=250,
                   state_group="SAG" if v7 else "SpsP")
    available = Path(annotations_path).is_file()
    if available:
        from flyeye import FlyEye
        male_eye = FlyEye(male, annotations_path=str(annotations_path))
        sides = bw.soma_sides(male, annotations_path)
    else:
        male_eye = LuminanceEye(male)
        sides = np.full(male.n, "", dtype=str)
    groups = bd.present_groups(male)
    if protocol == 'v12' and any(k not in groups for k in ('mAL', 'vAB3')):
        raise ValueError('v12 requires measured male groups mAL and vAB3')
    groups["LC10a"] = male.where(type_re="^LC10a$")
    for key in ("P1", "pIP10", "LC10a"):
        if key not in groups or not len(groups[key]):
            raise ValueError(f"v5 requires measured male group {key}")
    gains = p1_lesion(male, groups) if condition == "mute" else None
    room = ExperimentRoom(male, male_eye, groups,
        bw.motor_groups(male, sides), gains=gains, seed=seed, body_b=body,
        sim_steps=250,
        min_radius_px=bw.column_spacing_px(bw.distinct_columns(male_eye)))
    room.male_setup = dict(male_eye="columnar" if available else "luminance",
        sides_restored=available,
        male_recorded_groups={k: len(groups[k]) for k in ("P1", "pIP10", "LC10a")},
        disclosure=("MEASURED: annotation columns and soma sides loaded by bodyId." if available
                    else "CHOSEN: missing annotations use luminance and unknown soma sides; no column or side identities are invented."))
    if protocol == 'v12':
        room.male_setup['male_recorded_groups'].update({k: len(groups[k]) for k in ('mAL', 'vAB3')})
    room.configure(seed, condition, song_sound)
    if condition == "gated":
        body.gains = pc1_lesion(female)
    if condition == "p1drive":
        install_p1_drive(room.bodies["A"])
    if protocol == 'v10':
        install_lc10a_drive(room, sides)
    return room


def correlation(a, b):
    if len(a) < 2 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    return float(spearmanr(a, b).statistic)


def outcome(seed, condition, trace, start):
    q = max(1, len(trace["distance_mm"]) // 4)
    first = float(np.mean(trace["distance_mm"][:q]))
    last = float(np.mean(trace["distance_mm"][-q:]))
    active = int(np.count_nonzero(trace["vpodn_hz"] > 0))
    result = dict(seed=seed, condition=condition, start=start, accept=active >= ACCEPT_WINDOWS,
        state="mated" if condition in ("mated", "mated_song", "mated_silence") else "virgin",
        state_group="SAG" if condition in V7_CONDITIONS else "SpsP",
        state_drive_hz=0. if condition in ("mated", "mated_song", "mated_silence") else courtship.STATE_HZ,
        ovidn_hz=float(np.mean(trace["ovidn_hz"])), spsp_hz=float(np.mean(trace["spsp_hz"])),
        sight_fraction=float(np.mean(trace["sight_ok"])),
        retreat_fraction=float(np.mean(np.diff(trace["distance_mm"]) > 0)),
        approach=last < first, retreat=last > first, active_windows=active,
        vpodn_hz=float(np.mean(trace["vpodn_hz"])), pc1_hz=float(np.mean(trace["pc1_hz"])),
        first_distance_mm=first, last_distance_mm=last,
        song_distance_rho=correlation(trace["song_hz"], trace["distance_mm"]),
        song_speed_rho=correlation(trace["song_hz"], trace["her_speed_mm_s"]))
    # CHOSEN: P1 mean > 0 Hz counts active windows descriptively; it decides nothing.
    p1 = trace.get("p1_hz")
    for channel in ("a", "b"):
        key = f"her_sound_{channel}_clipped"
        result[key] = int(np.count_nonzero(trace[key])) if key in trace else None
    result["p1_active_windows"] = (int(np.count_nonzero(p1 > 0))
                                    if p1 is not None and np.all(np.isfinite(p1)) else None)
    for channel in ("pulse", "sine"):
        values = trace.get(channel + "_hz")
        for label, key in (("distance", "distance_mm"), ("speed", "her_speed_mm_s")):
            result[f"{channel}_{label}_lagged_rho"] = (
                correlation(values[1:], trace[key][:-1]) if values is not None else None)
    for key in ("p1_hz", "pip10_hz", "lc10a_hz", "a", "m"):
        result[key] = float(np.mean(trace[key])) if key in trace else None
    result["delivered_rms"] = float(np.sqrt(np.mean(trace["delivered_rms"]**2))) if "delivered_rms" in trace else None
    for channel in ("a", "m"):
        for label, key in (("distance", "distance_mm"), ("speed", "her_speed_mm_s")):
            result[f"{channel}_{label}_lagged_rho"] = correlation(trace[channel][1:], trace[key][:-1]) if channel in trace else None
    result["m_lc10a_lagged_rho"] = correlation(trace["m"][1:], trace["lc10a_hz"][:-1])
    for channel in ('a', 'm'):
        neural = trace.get(channel + '_neural')
        result[channel + '_neural_lc10a_lagged_rho'] = (
            correlation(neural[1:], trace['lc10a_hz'][:-1]) if neural is not None else None)
        if 'lc10a_drive_hz' in trace:
            result[channel + '_neural_drive_lagged_rho'] = correlation(
                neural[1:], trace['lc10a_drive_hz'][:-1])
    if 'turn_toward' in trace:
        result.update(turn_toward_fraction=float(trace['turn_toward'].mean()),
                      distance_mm=float(trace['distance_mm'].mean()), state_group='SAG')
    seen = trace["sight_ok"].astype(bool)
    result["lc10a_sight_hz"] = float(trace["lc10a_hz"][seen].mean()) if seen.any() else None
    result["lc10a_no_sight_hz"] = float(trace["lc10a_hz"][~seen].mean()) if (~seen).any() else None
    result["lc10a_sight_difference"] = (result["lc10a_sight_hz"]-result["lc10a_no_sight_hz"]
                                        if seen.any() and (~seen).any() else None)
    return result


def run_trial(room, steps, seed, condition):
    if steps < 4:
        raise ValueError("at least four steps required")
    start = room.arena.geometry()
    sight = room.sight_check()
    # MEASURED: compare the actual starting silhouette with a ground-only frame.
    eye, ch = room.bodies["A"].eye, room.channels
    blank = np.full((ch.h, ch.w), ch.ground, dtype=np.float32)
    baseline = eye.look(blank, *ch.gaze)
    image = eye.look(ch.sight_frame(room.arena.A, room.arena.B), *ch.gaze)
    sight_ok = any(np.any(np.abs(np.asarray(image[k]) - v) > 1e-6)
                   for k, v in baseline.items())
    rows = []
    for window in range(steps):
        if getattr(room, 'protocol', None) == 'v10':
            prepare_lc10a_window(room, window)
        image = eye.look(ch.sight_frame(room.arena.A, room.arena.B), *ch.gaze)
        window_sight = any(np.any(np.abs(np.asarray(image[k])-v) > 1e-6)
                           for k, v in baseline.items())
        r = room.step()
        if any(r["A"].get(k) is None for k in ("pulse_hz", "sine_hz")):
            raise ValueError("experiment protocol requires both male song groups: song_pulse_mn and song_sine_hg1")
        g = r["before"]
        # MEASURED: pre-window geometry; speed is realised displacement in this window.
        row = {f"{name}_{key}": g[name][key] for name in ("A", "B")
               for key in ("x", "y", "heading_rad")}
        displacement = np.hypot(r["after"]["B"]["x"]-g["B"]["x"],
                                r["after"]["B"]["y"]-g["B"]["y"])
        sound_a, sound_b = HerBody.sound_pair(r["B"]["in"]["sound_hz"])
        row.update(time_s=g["time_s"], distance_mm=g["distance_mm"], sight_ok=bool(window_sight),
            p1_hz=r["A"].get("p1_hz"), pulse_hz=r["A"]["pulse_hz"],
            sine_hz=r["A"]["sine_hz"],
            her_sound_a_clipped=r["sound_clipped"][0],
            her_sound_b_clipped=r["sound_clipped"][1],
            her_speed_mm_s=float(displacement / bw.WORLD_DT_S),
            **r["B"]["her_answer"], her_sound_hz=max(sound_a, sound_b),
            her_sound_a_hz=sound_a, her_sound_b_hz=sound_b,
            song_hz=r["A"]["song_hz"], his_sound_hz=r["A"]["in"]["sound_hz"])
        wave = r.get("song_wave", {})
        a_neural, m_neural = neural_song(r['A']['rates']['pIP10'],
            r['A']['pulse_hz'], r['A']['sine_hz'], room.singer)
        row.update(a_neural=a_neural, m_neural=m_neural)
        if getattr(room, 'protocol', None) == 'v10':
            drive = room.lc10a_current
            before_bearing = g['bearing_deg']['A']
            row.update(lc10a_drive_hz=float(np.mean(drive)),
                lc10a_drive_left_hz=float(room.lc10a_pair[0]),
                lc10a_drive_right_hz=float(room.lc10a_pair[1]),
                lc10a_replay_index=room.lc10a_source_index,
                turn_toward=heading_reduces_bearing(before_bearing,
                    g['A']['heading_rad'], r['after']['A']['heading_rad']))
        row.update(pip10_hz=r["A"]["rates"]["pIP10"],
                   lc10a_hz=r["A"]["rates"]["LC10a"],
                   source_pip10_hz=wave.get("pip10_hz", 0.),
                   a=wave.get("a", 0.), m=wave.get("m", 0.),
                   delivered_rms=wave.get("delivered_rms", 0.),
                   source_distance_mm=wave.get("source_distance_mm", g["distance_mm"]),
                   replay_gain=wave.get("replay_gain", 1.),
                   her_brain_s=r["B"].get("brain_s", 0.))
        rows.append(row)
        if getattr(room, 'protocol', None) in ('v9', 'v12'):
            row['male_total_hz'] = r['A']['total_hz']
        if getattr(room, 'protocol', None) == 'v12':
            row.update(mal_hz=r['A']['rates']['mAL'], vab3_hz=r['A']['rates']['vAB3'])
    trace = {k: np.asarray([r[k] for r in rows], dtype=float) for k in rows[0]}
    result = outcome(seed, condition, trace, start)
    if getattr(room, 'protocol', None) in ('v9', 'v12'):
        result.update(male_total_hz=float(trace['male_total_hz'].mean()), state_group='SAG')
    if getattr(room, 'protocol', None) == 'v12':
        result.update(mal_hz=float(trace['mal_hz'].mean()), vab3_hz=float(trace['vab3_hz'].mean()))
    result.update(sight_ok=bool(sight_ok), sight_check=sight, **room.male_setup)
    return result, trace


def verdict(mean, se, n):
    if n < 2 or se is None:
        return "undetermined"
    return "supported" if mean > 2 * se else "not supported"


def budget_ladder(requested, first_seconds, budget_s):
    candidates = [requested] if requested < 8 else sorted({requested, *[v for v in (10, 8) if v <= requested]}, reverse=True)
    estimates = {str(v): first_seconds * len(CONDITIONS) * v for v in candidates}
    selected = next((v for v in candidates if estimates[str(v)] <= budget_s), min(candidates))
    return dict(requested=requested, candidates=candidates, budget_s=budget_s,
                selected=selected, estimated_seconds=estimates,
                budget_exceeded=estimates[str(selected)] > budget_s)


def summarise(rows):
    indexed = {(r["seed"], r["condition"]): r for r in rows}
    predictions = {}
    for label, key, control, sign in (("P1", "vpodn_hz", "silence", 1),
        ("P2", "pc1_hz", "silence", 1), ("P3", "vpodn_hz", "jittered", 1),
        ("P4", "last_distance_mm", "silence", -1),
        ("P5_command", "pip10_hz", "mute", 1),
        ("P5_rms", "delivered_rms", "mute", 1),
        ("P6", "vpodn_hz", "mute", 1),
        ("P8", "p1_hz", "noscent", 1),
        ("P8b", "lc10a_hz", "noscent", 1),
        ("P9", "vpodn_hz", "mated", 1)):
        diffs = [sign * (indexed[s, "song"][key] - indexed[s, control][key])
                 for s in sorted({r["seed"] for r in rows})]
        mean = float(np.mean(diffs))
        se = float(np.std(diffs, ddof=1) / np.sqrt(len(diffs))) if len(diffs) > 1 else None
        predictions[label] = dict(mean=mean, se=se, n=len(diffs), paired_differences=diffs,
            metric=key, control=control, direction="song - control" if sign == 1 else "control - song",
            verdict=verdict(mean, se, len(diffs)))
        if label == "P8b":
            predictions[label]["verdict"] = "descriptive; no verdict"
    song = [r for r in rows if r["condition"] == "song"]
    diffs = [r["lc10a_sight_difference"] for r in song if r["lc10a_sight_difference"] is not None]
    mean = float(np.mean(diffs)) if diffs else None
    se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs) > 1 else None
    predictions["P11"] = dict(mean=mean, se=se, n=len(diffs), paired_differences=diffs,
        excluded_seeds=[r["seed"] for r in song if r["lc10a_sight_difference"] is None],
        metric="lc10a_hz", control="no-sight windows within song trial", direction="sight - no sight",
        verdict=verdict(mean, se, len(diffs)))
    spread = {}
    for c in CONDITIONS:
        rr = [r for r in rows if r["condition"] == c]
        counts = {k: sum(r[k] for r in rr) for k in ("accept", "approach", "retreat")}
        same = len({tuple(r[k] for k in counts) for r in rr}) == 1
        sentence = f"{c}: every seed gives the same outcome." if same else f"{c}: outcomes differ across seeds."
        spread[c] = dict(n=len(rr), **counts, no_accept=len(rr)-counts["accept"],
                        accept_seeds=[r["seed"] for r in rr if r["accept"]],
                        no_accept_seeds=[r["seed"] for r in rr if not r["accept"]], sentence=sentence)
        if c == "mated" and rr and counts["accept"] == len(rr):
            spread[c]["state_sentence"] = "the state did not produce a no"
    p0 = dict(per_seed=[
        dict(seed=r["seed"], condition=r["condition"], active_windows=r["active_windows"])
        for r in rows if r["condition"] in ("dark", "silence", "mute")])
    ratios = []
    for seed in sorted({r["seed"] for r in rows}):
        baseline = indexed[seed, "song"]["delivered_rms"]
        ratios.append(dict(seed=seed, jittered_song_rms_ratio=(indexed[seed, "jittered"]["delivered_rms"]/baseline if baseline else None)))
    p5 = "supported" if all(predictions[k]["verdict"] == "supported" for k in ("P5_command", "P5_rms")) else ("undetermined" if len(ratios) < 2 else "not supported")
    p10 = [dict(seed=r["seed"], condition=r["condition"], ovidn_hz=r["ovidn_hz"],
                retreat_fraction=r["retreat_fraction"]) for r in rows if r["condition"] in ("song", "mated")]
    p12 = [{k: r[k] for k in ("seed", "condition", "a_distance_lagged_rho", "a_speed_lagged_rho",
            "m_distance_lagged_rho", "m_speed_lagged_rho", "m_lc10a_lagged_rho")} for r in rows]
    return dict(P0=p0, P5_verdict=p5, P10=p10, P12=p12, rms_ratios=ratios, predictions=predictions, seed_spread=spread)


def paths(prefix):
    return [Path(str(prefix) + s) for s in ("_experiment.json", "_trajectories.npz", "_trajectories.png", "_report.md")]


def assert_not_published(prefix):
    for target, protected in ((t, p) for t in paths(prefix)
                              for root in (PUBLISHED, PUBLISHED_ADDENDUM, PUBLISHED_V7, PUBLISHED_V8, PUBLISHED_V9, PUBLISHED_V10, PUBLISHED_V11) for p in paths(root)):
        # Resolve the parent identity, including aliases, before the files exist.
        same_parent = target.parent.exists() and protected.parent.exists() and os.path.samefile(target.parent, protected.parent)
        same_file = target.exists() and protected.exists() and os.path.samefile(target, protected)
        if same_file or (same_parent and target.name.casefold() == protected.name.casefold()):
            raise ValueError("published prefix is refused")


def write_report(json_path):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    if data['protocol'] == 'v12':
        return write_v12_report(json_path, data)
    if data['protocol'] == 'v11':
        return write_v11_report(json_path, data)
    if data['protocol'] == 'v10':
        return write_v10_report(json_path, data)
    if data['protocol'] == 'v9':
        return write_v9_report(json_path, data)
    if data["protocol"] == "v6":
        return write_v6_report(json_path, data)
    if data["protocol"] in ("v7", "v8"):
        return write_v7_report(json_path, data)
    environment = data.get("environment", {"brain_class": "flysim.FlyBrain", "torch_devices": {"male": None, "female": None}})
    lines = ["# Courtship experiment", "", f"Run: {len(data['seeds'])} seeds x {len(data['protocol_spec']['conditions'])} conditions x {data['steps']} steps; quick={data['quick']}.",
        "Quick runs are smoke tests; their two-seed verdicts are not the full ten-seed experiment.", "",
        "## Question", "Does his song change her graph's answer and their distance?", "",
        "## Measured versus chosen", "MEASURED: positions and headings, realised female speed, delivered sound, song, pC1 and vpoDN window rates.",
        f"IMPLEMENTATION: brain class {environment['brain_class']}; torch devices {environment['torch_devices']}. Device is not a scientific choice. Required equivalence: same numbers on either device, verified by test (COURTSHIP_REAL_BRAIN=1); a failing test invalidates this claim.",
        "CHOSEN: accept means vpoDN > 0 Hz in at least 3 windows; approach/retreat compare last and first quarter mean distance. Equal distance is neither. Geometry is sampled before each window; speed is displacement during it.",
        "CHOSEN: paired seeds, annotation-backed male eye when available, uncalibrated gains, 50 ms brain windows, and the rate-to-motion mapping. No outcomes were tuned to differ across seeds.", "",
        f"CHOSEN: FEMALE_EXC_SCALE = {data['female_exc_scale']}; FEMALE_EYE = {data['female_eye']}.",
        data["protocol_spec"]["text"], "", "## Predictions", "| Prediction | Paired difference | SE | n | Verdict |", "|---|---:|---:|---:|---|"]
    for k, p in data["summary"]["predictions"].items():
        lines.append(f"| {k}: {p['metric']}, {p['direction']} ({p['control']}) | {p['mean']} | {p['se']} | {p['n']} | {p['verdict']} |")
    lines += ["", "## P0: baseline (descriptive, no verdict)"]
    for r in data["summary"]["P0"]["per_seed"]:
        lines.append(f"Seed {r['seed']}, {r['condition']}: {r['active_windows']} active windows.")
    lines += ["", "## Per-seed outcomes", "MEASURED: clipped windows count actual ear sub-window clipping in each band.", "| Seed | Condition | State | Accept | Approach | Retreat | Active windows | vpoDN Hz | pC1 Hz | oviDN Hz | Sight fraction | Last distance mm | pIP10 Hz | Delivered RMS |", "|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in data["outcomes"]:
        lines.append("| " + " | ".join(str(r[k]) for k in ("seed", "condition", "state", "accept", "approach", "retreat", "active_windows", "vpodn_hz", "pc1_hz", "ovidn_hz", "sight_fraction", "last_distance_mm", "pip10_hz", "delivered_rms")) + " |")
    lines += ["", "## Seed spread"]
    for c, s in data["summary"]["seed_spread"].items():
        lines += [f"{c}: accept {s['accept']}/{s['n']}, approach {s['approach']}/{s['n']}, retreat {s['retreat']}/{s['n']}. {s['sentence']}"]
        lines.append(f"Accept seeds: {s['accept_seeds']}; no-accept seeds: {s['no_accept_seeds']}.")
        if "state_sentence" in s:
            lines.append(s["state_sentence"])
    lines += ["", "## P9 she can say no", str(data["summary"]["predictions"]["P9"]),
              "", "## P10 rejection (descriptive, no verdict)",
              "Retreat fraction: adjacent pre-window distances that increase / all adjacent pairs."]
    lines += [str(r) for r in data["summary"]["P10"]]
    lines += ["", "## P11 he sees her", str(data["summary"]["predictions"]["P11"]),
              "Paired within song trial; exclude trials missing either category; fewer than two pairs is undetermined."]
    lines += [str({k: r[k] for k in ("seed", "sight_fraction", "lc10a_sight_hz", "lc10a_no_sight_hz")})
              for r in data["outcomes"] if r["condition"] == "song"]
    lines += ["", "## P12 adaptation (descriptive, no verdict)",
              "Spearman correlations: a[1:] and m[1:] versus previous distance/speed, and m[1:] versus LC10a[:-1]; None means constant data."]
    lines += [str(r) for r in data["summary"]["P12"]]
    lines += ["", "## P7 his response (descriptive)",
        "MEASURED: P1 active windows, LC10a mean rate per window, lagged amplitude/mode correlations with her previous distance/speed. None means constant data. No adaptation mechanism was added.",
        "| Seed | Condition | P1 active windows | LC10a Hz | a-distance | a-speed | m-distance | m-speed |",
        "|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in data["outcomes"]:
        lines.append("| " + " | ".join(str(r.get(k)) for k in ("seed", "condition", "p1_active_windows", "lc10a_hz", "a_distance_lagged_rho", "a_speed_lagged_rho", "m_distance_lagged_rho", "m_speed_lagged_rho")) + " |")
    lines += ["", f"P5 joint verdict: {data['summary']['P5_verdict']}.",
              "MEASURED jittered/song RMS ratios: " + str(data["summary"]["rms_ratios"]),
              "CHOSEN ear settings: " + str(data.get("ear", WaveEar().describe()))]
    lines.append("Replay uses song command, mode and distance with a disclosed trial-wide energy gain; "
                 "P3 cannot isolate timing when energy differs substantially. Mute tests the "
                 "command chain; its name does not guarantee silence.")
    if data.get("timing"):
        step = float(np.mean([t["step_s"] for t in data["timing"]]))
        female = float(np.mean([t["her_brain_s"] for t in data["timing"]]))
        lines += [f"MEASURED: mean world step {step:.6g} s; female brain step {female:.6g} s. "
                  f"Estimated ten-seed cost ({len(CONDITIONS)} x 400 windows each): {step*len(CONDITIONS)*4000/3600:.3g} hours, excluding setup and rendering."]
        if female > .5:
            lines.append("MEASURED: female brain step exceeds 0.5 s; the full experiment was not run.")
    interpretation = "; ".join(f"{k} was {p['verdict']}" for k, p in data["summary"]["predictions"].items())
    lines += ["", "## What it means", f"Under this protocol, {interpretation}. These comparisons concern this simulator and input encoding.",
        "<!-- interpretation: to be written after the run -->", "", "## Limitations"]
    lines += ["- " + s for s in data["limitations"]]
    destination = Path(str(json_path).replace("_experiment.json", "_report.md"))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def render_pil(path, data, traces):
    """The plume runner's existing Pillow fallback, with rate traces."""
    from PIL import Image, ImageDraw
    conditions = data["protocol_spec"]["conditions"]
    img = Image.new("RGB", (420 * len(conditions), 740), "white")
    draw = ImageDraw.Draw(img)
    colors = ("blue", "red", "green", "purple", "orange", "brown", "teal", "magenta", "navy", "gray")
    for col, c in enumerate(conditions):
        left = 50 + col * 420
        draw.text((left, 10), c + ": her solid / his dashed", fill="black")
        draw.rectangle((left, 50, left+320, 370), outline="black")
        draw.text((left, 375), "x, y: 0 to 20 mm; y increases upward", fill="black")
        selected = [r for r in data["outcomes"] if r["condition"] == c]
        peak = max(1., max(float(traces[f"s{r['seed']}_{c}_vpodn_hz"].max()) for r in selected))
        draw.rectangle((left, 470, left+320, 670), outline="black")
        duration = data["steps"] * bw.WORLD_DT_S
        draw.text((left, 685), f"time 0 to {duration:g} s; vpoDN 0 to {peak:.4g} Hz", fill="black")
        for r in selected:
            color = colors[r["seed"] % len(colors)]
            key = f"s{r['seed']}_{c}_"
            draw.text((left + (r["seed"] % 5)*65, 405 + (r["seed"]//5)*18), f"seed {r['seed']}", fill=color)
            for name in ("A", "B"):
                xy = [(left + x*16, 370-y*16) for x, y in zip(traces[key+name+"_x"], traces[key+name+"_y"])]
                if name == "B":
                    draw.line(xy, fill=color, width=2)
                else:
                    for i in range(0, len(xy)-1, 2):
                        draw.line(xy[i:i+2], fill=color, width=1)
                x, y = xy[0]
                draw.ellipse((x-3, y-3, x+3, y+3), outline=color)
            draw.line([(left + t/duration*320, 670-v/peak*200) for t, v in
                       zip(traces[key+"time_s"], traces[key+"vpodn_hz"])], fill=color, width=2)
    img.save(path)


def save(prefix, data, traces):
    jp, npz, png, _ = paths(prefix)
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    np.savez_compressed(npz, **traces)
    try:
        import matplotlib
    except ImportError:
        render_pil(png, data, traces)
        write_report(jp)
        return
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    conditions = data["protocol_spec"]["conditions"]
    fig, axes = plt.subplots(2, len(conditions), figsize=(4 * len(conditions), 7))
    for col, c in enumerate(conditions):
        for r in data["outcomes"]:
            if r["condition"] != c:
                continue
            key = f"s{r['seed']}_{c}_"
            line, = axes[0, col].plot(traces[key+"B_x"], traces[key+"B_y"], label=f"her, seed {r['seed']}")
            axes[0, col].plot(traces[key+"A_x"], traces[key+"A_y"], "--", color=line.get_color(), label=f"his, seed {r['seed']}")
            axes[1, col].plot(traces[key+"time_s"], traces[key+"vpodn_hz"], color=line.get_color())
        axes[0, col].set(title=c, xlim=(0, bw.ARENA_MM), ylim=(0, bw.ARENA_MM), xlabel="x (mm)", ylabel="y (mm)")
        axes[0, col].legend(fontsize=6)
        axes[1, col].set(xlabel="time (s)", ylabel="her vpoDN (Hz)")
    fig.tight_layout()
    fig.savefig(png, dpi=140)
    plt.close(fig)
    write_report(jp)


MALE_EXC_SCALES = (0.9, 0.8, 0.7)
V9_CONDITIONS = {c: CONDITIONS[c] for c in ('song', 'mute', 'noscent')}
V9_PREDICTIONS = '''- P21 the command carries the song: his pIP10 mean rate and delivered song RMS, song > mute (both, as P5).
- P22 he notices her: his P1 mean rate, song > noscent (as P8).
- P23 (descriptive, no verdict): pIP10 and delivered RMS by scale; P1 by scale; total male rate by scale (is there a scale where silence stays silent and song still sings); her vpoDN by scale (does cooling him change what reaches her); accept rule per cell.
- P24 (descriptive, stated as not testable): LC10a per cell, with the sentence "LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9".'''
V9_RULE = 'Verdict rule per scale as v5: paired difference > 2 SE, n = 10. A step counts as established only if it holds at at least one scale AND the direction is not reversed (difference < -2 SE) at any other scale in the sweep; report every scale. P21 requires both comparisons at the same scale; reversal of either comparison at any scale prevents establishment. Quick runs are smoke tests and cannot establish a step.'
V9_CALIBRATION = '''Calibration record: raw male graph (GPU, 8 carried windows x 250 steps; these are calibration probes, not outcomes):
- Silence gives 0 Hz everywhere; any input (her scent on Or47b, her silhouette on his eye, either eye model) ignites the whole male network to ~45-60 Hz total, after which pIP10 is erratic: at one scale it ranges 2 to 245 Hz across conditions, and a P1 lesion sometimes raises pIP10. A ladder of positive-weight scales 1.00/0.98/0.96/0.94/0.92/0.90 showed NO monotone dependence of pIP10 on P1 and no stable scent effect on P1 in eight-window probes. An earlier probe at 0.9 and 0.8 with scent+contact drive at 100 Hz on each class gave pIP10 0-4 Hz (song command gone) while P1 stayed 10-25 Hz. So the regime where P1 controls pIP10, if it exists, lies somewhere in 0.7-0.95 and eight-window probes cannot find it: it needs seeds and the closed loop.
- LC10a cannot be reached from his eye in this map: lamina L1/L2 drive, T4/T5 drive, T2/T3, Tm3/Mi1 all leave LC10a at 0-2 Hz; only driving LC10a's own strongest medulla input types (Tm5Y, LC9, LC10c, TmY21, Tm5a) lights it (47-137 Hz). Its strongest inputs by weight include large inhibitory classes (TuTuA_2, AOTU042). So "he adapts" measured through LC10a is not testable with the current eye; say so.'''
V9_PROTOCOL_TEXT = '''Protocol v9. CHOSEN before data: MALE_EXC_SCALE swept over {0.9, 0.8, 0.7}, positive weights only, before room construction, restored between cells. Raw 1.0 is already on record in v5 and failed P5/P8.
Ten seeds, 400 steps, paired by seed and start across nine cells. Quick mode: two seeds, 80 steps, nine cells. No seed-count adaptation.
Female side = v8 exactly: own restored SAG graph build/graph_female_own_sag.npz (required), both SAG types, virgin STATE_HZ = 50 Hz, positive-weight scale 0.7, blind eye.
Conditions at every scale: song as v5; mute sets only his P1 outgoing gains to zero as v5; noscent zeros both her scent and contact drives to him as v5. All other v5 song settings retained.
Predictions fixed before data:
''' + V9_PREDICTIONS + '\n' + V9_RULE
PROTOCOLS['v9'] = dict(PROTOCOLS['v8'], text=V9_PROTOCOL_TEXT, conditions=V9_CONDITIONS,
    male_exc_scales=MALE_EXC_SCALES, seed_ladder=(10,), budget_note='Exactly 9 cells x 10 seeds; no seed reduction.')
V9_LIMITATIONS = [
    'The male scale is a chosen dose, not a measurement.',
    'The sweep is small and pre-registered; the multiple-scale rule is not a multiplicity-adjusted significance test.',
    'His eye still floods on uniform grey.',
    'LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9',
    'No silence cell is included in v9; silence staying silent is calibration evidence only, not tested by this sweep.',
    *[s for s in V8_LIMITATIONS if s != 'The male is unchanged and runs at raw scale.'],
    'Mute changes only his P1 outgoing gains; its spikes need not be silent.']


@contextmanager
def male_excitation(fb, scale):
    """Indexed writes notify GPU weights, as in load_female; never compound doses."""
    original = fb.wdata.copy()
    try:
        fb.wdata[fb.wdata > 0] *= scale
        yield
    finally:
        fb.wdata[:] = original


def summarise_v9(rows, scale_set=MALE_EXC_SCALES):
    scales, cells = {}, []
    for scale in scale_set:
        rr = [r for r in rows if r['male_exc_scale'] == scale]
        indexed = {(r['seed'], r['condition']): r for r in rr}
        seeds = sorted({r['seed'] for r in rr})
        predictions = {}
        for label, metric, control in (('P21_command', 'pip10_hz', 'mute'),
                ('P21_rms', 'delivered_rms', 'mute'), ('P22', 'p1_hz', 'noscent')):
            diffs = [indexed[s, 'song'][metric] - indexed[s, control][metric] for s in seeds]
            mean = float(np.mean(diffs))
            se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs) > 1 else None
            predictions[label] = dict(mean=mean, se=se, n=len(diffs), paired_differences=diffs,
                metric=metric, control=control, verdict=verdict(mean, se, len(diffs)),
                reversed=bool(se is not None and mean < -2*se))
        predictions['P21_verdict'] = ('supported' if all(predictions[k]['verdict'] == 'supported'
            for k in ('P21_command', 'P21_rms')) else 'not supported')
        scales[str(scale)] = predictions
        for c in V9_CONDITIONS:
            cell = [r for r in rr if r['condition'] == c]
            cells.append(dict(male_exc_scale=scale, condition=c, n=len(cell),
                accept=sum(r['accept'] for r in cell),
                **{k: float(np.mean([r[k] for r in cell])) for k in
                   ('pip10_hz', 'delivered_rms', 'p1_hz', 'male_total_hz', 'vpodn_hz', 'lc10a_hz')}))
    established = {}
    for step, keys in (('P21', ('P21_command', 'P21_rms')), ('P22', ('P22',))):
        holds = any(all(p[k]['verdict'] == 'supported' for k in keys) for p in scales.values())
        reverse = any(p[k]['reversed'] for p in scales.values() for k in keys)
        full = all(p[k]['n'] == 10 for p in scales.values() for k in keys)
        established[step] = 'established' if full and holds and not reverse else 'not established'
    return dict(per_scale=scales, established=established, cells=cells)


def v9_cell_table(data):
    keys = ('male_exc_scale', 'condition', 'n', 'pip10_hz', 'delivered_rms', 'p1_hz',
            'male_total_hz', 'vpodn_hz', 'lc10a_hz', 'accept')
    return ['| ' + ' | '.join(keys) + ' |', '| ' + ' | '.join(['---']*len(keys)) + ' |'] + [
        '| ' + ' | '.join(f'{r[k]:.6g}' if isinstance(r[k], float) else str(r[k]) for k in keys) + ' |'
        for r in data['summary']['cells']]


def write_v9_report(json_path, data):
    lines = ['# Courtship v9', '', data['protocol_spec']['text'], '', '## Calibration record',
        V9_CALIBRATION, '', '## Female graph record', json.dumps(data['female_graph'], indent=2),
        '', '## Per-scale verdicts', '| Scale | Prediction | Difference | SE | n | Verdict | Reversed |',
        '|---|---|---:|---:|---:|---|---|']
    for scale, ps in data['summary']['per_scale'].items():
        for label, p in ps.items():
            if isinstance(p, dict):
                lines.append(f"| {scale} | {label} | {p['mean']} | {p['se']} | {p['n']} | {p['verdict']} | {p['reversed']} |")
        lines.append(f"P21 joint verdict at {scale}: {ps['P21_verdict']}.")
    lines += ['', '## Per-seed outcomes', data['protocol_spec']['outcome_text']]
    keys = ('male_exc_scale', 'seed', 'condition', 'pip10_hz', 'delivered_rms', 'p1_hz',
            'male_total_hz', 'vpodn_hz', 'lc10a_hz', 'accept', 'active_windows', 'approach', 'retreat')
    lines += ['| ' + ' | '.join(keys) + ' |', '| ' + ' | '.join(['---']*len(keys)) + ' |']
    lines += ['| ' + ' | '.join(str(r[k]) for k in keys) + ' |' for r in data['outcomes']]
    lines += ['', '## P23/P24 descriptives (no verdict)', *v9_cell_table(data),
        'LC10a is not reachable from this eye model; adaptation through LC10a is not tested in v9',
        'No silence cell was run; the silent baseline is from calibration only.', '', '## Result',
        ' '.join(f"{k} is {v} under the multiple-scale rule." for k, v in data['summary']['established'].items()),
        'Two-seed quick comparisons are smoke evidence only.' if data['quick'] else 'All ten paired seeds are reported at every scale.',
        '', f"Ten-seed cost: {data['estimated_ten_seed_hours']:.6g} hours (9 cells x 10 seeds x 400 steps), excluding setup and rendering.",
        '', '## Limitations', *['- '+s for s in data['limitations']]]
    destination = Path(str(json_path).replace('_experiment.json', '_report.md'))
    destination.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return destination


def run_v9(args, prefix, room_factory=None):
    if not args.quick and (args.seeds != 10 or args.steps != 400):
        raise ValueError('v9 requires ten seeds and 400 steps; use --quick 1 for smoke tests')
    graph = v8_graph_record()
    n, steps = (2, 80) if args.quick else (10, 400)
    cls = bw.brain_class(args.brain)
    brains = None if room_factory else (cls(), load_female(path=V8_GRAPH, exc_scale=.7, brain_class=cls))
    rows, traces, timings, starts = [], {}, [], {}
    from contextlib import nullcontext
    for scale in MALE_EXC_SCALES:
        for seed in range(n):
            for condition in V9_CONDITIONS:
                with male_excitation(brains[0], scale) if brains else nullcontext():
                    room = (room_factory(seed, condition, brains=brains) if room_factory else
                            build_room(seed, condition, brains=brains, protocol='v9'))
                    room.protocol = 'v9'
                    start = room.arena.geometry()
                    if seed in starts and start != starts[seed]:
                        raise ValueError('v9 paired start mismatch')
                    starts[seed] = start
                    t0 = time.perf_counter()
                    row, trace = run_trial(room, steps, seed, condition)
                    elapsed = time.perf_counter()-t0
                row['male_exc_scale'] = scale
                rows.append(row)
                timings.append(dict(male_exc_scale=scale, seed=seed, condition=condition, step_s=elapsed/steps))
                traces.update({f's{seed}_{condition}_scale{scale}_{k}': v for k, v in trace.items()})
                print(f'scale={scale} seed={seed} condition={condition} step_s={elapsed/steps:.6f}', flush=True)
                if len(rows) == 1:
                    print(f'First-trial ten-seed estimate: {elapsed/steps*9*10*400/3600:.6g} hours (9 cells x 10 seeds x 400 steps).', flush=True)
    hours = float(np.mean([t['step_s'] for t in timings]))*9*10*400/3600
    data = dict(protocol='v9', protocol_spec=PROTOCOLS['v9'], seeds=list(range(n)), steps=steps,
        quick=bool(args.quick), male_exc_scales=MALE_EXC_SCALES, female_exc_scale=.7,
        female_graph=graph, female_eye=FEMALE_EYE, state_group='SAG', state_drive_hz=50.,
        outcomes=rows, summary=summarise_v9(rows), timing=timings, estimated_ten_seed_hours=hours,
        limitations=V9_LIMITATIONS, calibration=V9_CALIBRATION, ear=WaveEar().describe(),
        environment=dict(brain_class=args.brain, torch_devices={name: str(getattr(fb, 'device', None))
            for name, fb in zip(('male', 'female'), brains or (None, None))}),
        date=datetime.now(timezone.utc).isoformat())
    jp, npz, png, _ = paths(prefix)
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    np.savez_compressed(npz, **traces)
    # Keep the existing four-artifact contract, with one labelled panel per cell.
    plot_data = dict(data, protocol_spec=dict(data['protocol_spec'], conditions={
        f'{c} scale {scale}': V9_CONDITIONS[c] for scale in MALE_EXC_SCALES for c in V9_CONDITIONS}),
        outcomes=[dict(r, condition=f"{r['condition']} scale {r['male_exc_scale']}") for r in rows])
    plot_traces = {}
    for r in rows:
        source = f"s{r['seed']}_{r['condition']}_scale{r['male_exc_scale']}_"
        target = f"s{r['seed']}_{r['condition']} scale {r['male_exc_scale']}_"
        plot_traces.update({target+k[len(source):]: v for k, v in traces.items() if k.startswith(source)})
    render_pil(png, plot_data, plot_traces)
    write_report(jp)
    print('\n'.join(v9_cell_table(data)), flush=True)
    print(f'Ten-seed cost: {hours:.6g} hours (9 cells x 10 seeds x 400 steps), excluding setup and rendering.', flush=True)
    return 0


LC10A_HZ_MAX = 100.0
SIZE_FULL = float(np.degrees(2*np.arctan((bw.BODY_HEIGHT_MM/2)/2.0)))
V10_CONDITIONS = {'sight': (True, False), 'blind': (True, False), 'shuffled': (True, False)}
V10_TEXT = f'''Protocol v10: he adapts, a pre-registered intervention.
CHOSEN: ten seeds, 400 steps, paired by seed and start; quick = two seeds x 80 steps (one seed allowed for CPU budget).
Female = v8: required own restored SAG graph, virgin SAG 50 Hz, positive-weight scale 0.7.
Male positive-weight scale is required via --male-scale, a chosen dose from v9; no default.
CHOSEN: LC10A_HZ_MAX = {LC10A_HZ_MAX} Hz; SIZE_FULL = {SIZE_FULL:.12g} degrees, the vertical angular diameter at 2 mm for the room's 1 mm body height.
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
'''
V10_LIMITATIONS = [
    'LC10a measured-geometry drive replaces the visual pathway with chosen constants; it does not validate the native lamina-to-LC10a pathway. His eye still floods on grey.',
    'The male scale is a chosen dose from v9; the quick-run dose 0.9 is a smoke-test choice, not a sweep-selected final dose.',
    'The old m_lc10a_lagged_rho compares rendered m[t] from neural window t-1 with LC10a[t-1], so it does not measure a one-window neural lag. Legacy fields remain unchanged; new neural fields use current rates against previous-window LC10a.',
    'P26 tests either of two reported correlations with the specified >2 SE rule, without multiplicity adjustment. Correlation is not a learned adaptation mechanism.',
    'Angular size uses the unfloored vertical diameter; bearing and size vary with movement, but no separate motion gain is added.',
    *[s for s in V8_LIMITATIONS if s != 'The male is unchanged and runs at raw scale.']]
PROTOCOLS['v10'] = dict(PROTOCOLS['v8'], text=V10_TEXT, conditions=V10_CONDITIONS,
    lc10a_hz_max=LC10A_HZ_MAX, size_full_deg=SIZE_FULL, male_scale_required=True,
    jitter_rng=None, seed_ladder=(10,), budget_note='No seed reduction except explicit one-seed quick CPU run.')


def neural_song(pip10, pulse, sine, singer):
    """Same normalization as song.Singer.render, without its one-window delay."""
    p, s = pulse/singer.pulse_cells, sine/singer.sine_cells
    return float(np.clip(pip10/singer.pip10_full, 0, 1)), float(p/(p+s)) if p+s > 0 else 0.


def heading_reduces_bearing(bearing, before, after):
    """Hold the pre-window line of sight fixed: isolate his heading change."""
    turned = (bearing - np.degrees(after-before) + 180) % 360 - 180
    return abs(turned) < abs(bearing)


def lc10a_geometry(channels, viewer, other):
    ellipse = channels.ellipse_of(viewer, other)
    bearing = ellipse['bearing_deg']
    size = 2*ellipse['ry_raw']/channels.px_per_deg
    rate = LC10A_HZ_MAX*float(np.clip(size/SIZE_FULL, 0, 1))
    if abs(bearing) > min(90., channels.fov_w/(2*channels.px_per_deg)):
        return np.zeros(2, dtype=np.float32)
    return np.asarray([rate if bearing >= -10 else 0.,
                       rate if bearing <= 10 else 0.], dtype=np.float32)


def shuffled_drive(trace, seed):
    pairs = np.column_stack((trace['lc10a_drive_left_hz'], trace['lc10a_drive_right_hz']))
    order = np.random.default_rng(np.random.SeedSequence([seed, 1025])).permutation(len(pairs))
    if len(order) > 1 and np.array_equal(order, np.arange(len(order))):
        order = np.roll(order, 1)
    return pairs[order].copy(), order


def install_lc10a_drive(room, soma_side):
    body = room.bodies['A']
    idx = body.groups['LC10a']
    sides = np.asarray(soma_side)[idx]
    if not np.all(np.isin(sides, ['L', 'R'])) or not all(np.any(sides == s) for s in ('L', 'R')):
        raise ValueError('v10 requires known left/right soma_side for all LC10a cells')
    room.lc10a_sides = sides
    original = body.drive

    def drive(frame, smell_hz, sound_hz):
        result = original(frame, smell_hz, sound_hz)
        if any(np.intersect1d(k, idx).size for k in result):
            raise ValueError('LC10a drive overlaps another input')
        result[tuple(idx)] = room.lc10a_current.copy()
        return result

    body.drive = drive


def prepare_lc10a_window(room, window):
    if room.condition == 'shuffled':
        pair = room.lc10a_replay[window]
        source = int(room.lc10a_order[window])
    else:
        pair = (lc10a_geometry(room.channels, room.arena.A, room.arena.B)
                if room.condition == 'sight' else np.zeros(2, dtype=np.float32))
        source = window
    room.lc10a_pair, room.lc10a_source_index = pair, source
    room.lc10a_current = np.where(room.lc10a_sides == 'L', pair[0], pair[1]).astype(np.float32)


def summarise_v10(rows):
    indexed = {(r['seed'], r['condition']): r for r in rows}
    seeds = sorted({r['seed'] for r in rows})
    predictions = {}
    for label, metric, control in (
            ('P25', 'lc10a_hz', 'blind'),
            ('P26_a', 'a_neural_drive_lagged_rho', 'shuffled'),
            ('P26_m', 'm_neural_drive_lagged_rho', 'shuffled'),
            ('P27', 'turn_toward_fraction', 'blind')):
        pairs = [(s, indexed[s, 'sight'][metric], indexed[s, control][metric]) for s in seeds]
        valid = [(s, a-b) for s, a, b in pairs if a is not None and b is not None]
        diffs = [d for _, d in valid]
        mean = float(np.mean(diffs)) if diffs else None
        se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs) > 1 else None
        v = verdict(mean, se, len(diffs))
        predictions[label] = dict(metric=metric, control=control, mean=mean, se=se,
            n=len(diffs), paired_differences=diffs, valid_seeds=[s for s, _ in valid],
            excluded_seeds=[s for s, a, b in pairs if a is None or b is None], verdict=v,
            established=len(diffs) == 10 and v == 'supported')
    channels = [c for c in ('a', 'm') if predictions['P26_'+c]['established']]
    return dict(predictions=predictions, P26_channels=channels,
        P26_verdict='established' if channels else 'not established')


def v10_seed_table(data):
    keys = ('seed', 'condition', 'lc10a_hz', 'a_neural_drive_lagged_rho',
        'm_neural_drive_lagged_rho', 'turn_toward_fraction', 'pip10_hz',
        'delivered_rms', 'vpodn_hz', 'accept', 'distance_mm', 'approach', 'retreat')
    return ['| '+' | '.join(keys)+' |', '| '+' | '.join(['---']*len(keys))+' |'] + [
        '| '+' | '.join(f'{r[k]:.6g}' if isinstance(r[k], float) else str(r[k]) for k in keys)+' |'
        for r in data['outcomes']]


def write_v10_report(json_path, data):
    lines = ['# Courtship v10', '', '## Calibration/design record', V10_TEXT,
        f"CHOSEN male positive-weight scale: {data['male_exc_scale']}.",
        'Female graph record: '+json.dumps(data['female_graph']), '', '## Verdicts',
        '| Prediction | Difference | SE | n | >2 SE comparison | Established (n=10) |',
        '|---|---:|---:|---:|---|---|']
    for label, p in data['summary']['predictions'].items():
        lines.append(f"| {label} | {p['mean']} | {p['se']} | {p['n']} | {p['verdict']} | {p['established']} |")
    lines += ['', '## Per-seed outcomes and P28 (descriptive)', *v10_seed_table(data),
        '', '## Result',
        ' '.join(f"{k}: {'established' if data['summary']['predictions'][k]['established'] else 'not established'}." for k in ('P25', 'P27')),
        f"P26: {data['summary']['P26_verdict']}; qualifying channels: {', '.join(data['summary']['P26_channels']) or 'none'}. Both a and m are reported above.",
        'Quick run: smoke evidence only.' if data['quick'] else 'Ten-seed design; undefined pairs cannot establish a prediction.',
        '', '## Limitations', *['- '+s for s in data['limitations']]]
    destination = Path(str(json_path).replace('_experiment.json', '_report.md'))
    destination.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return destination


def run_v10(args, prefix, room_factory=None):
    if args.male_scale is None or not np.isfinite(args.male_scale) or args.male_scale <= 0:
        raise ValueError('v10 requires --male-scale with a finite positive value')
    if not args.quick and (args.seeds != 10 or args.steps != 400):
        raise ValueError('v10 requires ten seeds and 400 steps; use --quick 1 for smoke tests')
    graph = v8_graph_record()
    n, steps = (1 if args.seeds == 1 else 2, 80) if args.quick else (10, 400)
    cls = bw.brain_class(args.brain)
    brains = None if room_factory else (cls(), load_female(path=V8_GRAPH, exc_scale=.7, brain_class=cls))
    from contextlib import nullcontext
    rows, traces, timings = [], {}, []
    print(V10_TEXT+f'CHOSEN male positive-weight scale: {args.male_scale}', flush=True)
    for seed in range(n):
        sight_trace, start = None, None
        for condition in V10_CONDITIONS:
            with male_excitation(brains[0], args.male_scale) if brains else nullcontext():
                room = (room_factory(seed, condition, brains=brains) if room_factory else
                        build_room(seed, condition, brains=brains, protocol='v10'))
                room.protocol = 'v10'
                if start is not None and room.arena.geometry() != start:
                    raise ValueError('v10 paired start mismatch')
                start = room.arena.geometry()
                if condition == 'shuffled':
                    room.lc10a_replay, room.lc10a_order = shuffled_drive(sight_trace, seed)
                t0 = time.perf_counter()
                row, trace = run_trial(room, steps, seed, condition)
                elapsed = time.perf_counter()-t0
            row['male_exc_scale'] = args.male_scale
            rows.append(row)
            timings.append(dict(seed=seed, condition=condition, seconds=elapsed))
            traces.update({f's{seed}_{condition}_{k}': v for k, v in trace.items()})
            if condition == 'sight':
                sight_trace = trace
            print(f'seed={seed} condition={condition} seconds={elapsed:.3f}', flush=True)
    data = dict(protocol='v10', protocol_spec=PROTOCOLS['v10'], seeds=list(range(n)),
        steps=steps, quick=bool(args.quick), male_exc_scale=args.male_scale,
        female_exc_scale=.7, female_graph=graph, female_eye=FEMALE_EYE,
        state_group='SAG', state_drive_hz=50., outcomes=rows, summary=summarise_v10(rows),
        limitations=V10_LIMITATIONS, timing=timings, ear=WaveEar().describe(),
        environment=dict(brain_class=args.brain), date=datetime.now(timezone.utc).isoformat())
    save(prefix, data, traces)
    print('\n'.join(v10_seed_table(data)), flush=True)
    print(json.dumps(data['summary'], indent=2), flush=True)
    return 0


V11_CONDITIONS = {c: CONDITIONS['song'] for c in ('song', 'noscent_orn', 'noscent_contact', 'noscent')}
V11_TEXT = '''Protocol v11: which of her cues suppresses his command.
CHOSEN before data: required --male-scale, positive male weights only, restored between trials; 0.9 is the v9 rule choice. Female = v8: required own restored SAG graph, both SAG types, virgin 50 Hz, positive-weight scale 0.7, blind eye.
Ten paired seeds, 400 steps, four conditions; quick = two seeds x 80 steps (explicit --seeds 1 permitted for cost). Same starting geometry per seed.
song: both cues on; noscent_orn: only Or47b zero; noscent_contact: only contact zero; noscent: both zero. Interventions occur only in listener_scent.
Or47b: ORN_VA1v (130 cells), SMELL_MAX_HZ with distance falloff. Contact: putative_ppk23 (269 cells), same drive within 2 mm. Existing drive includes the 2 mm boundary; contact_fraction is strictly distance < 2 mm, using pre-window geometry.
P29: P1 mean rate, noscent_orn > song.
P30: P1 mean rate, noscent_contact > song.
P31_orn: pIP10 mean rate AND delivered RMS, noscent_orn > song (both).
P31_contact: pIP10 mean rate AND delivered RMS, noscent_contact > song (both, separately reported).
P32 descriptive: noscent versus each partial removal (one cue alone); her vpoDN and accept, distance, approach/retreat and contact fraction per seed and condition.
Verdict rule as v5: paired difference > 2 SE, n = 10. Quick runs cannot establish predictions. Predictions fixed before data.
'''
PROTOCOLS['v11'] = dict(PROTOCOLS['v8'], text=V11_TEXT, conditions=V11_CONDITIONS,
    male_scale_required=True, seed_ladder=(10,), budget_note='Exactly four conditions x ten seeds; no full-run reduction.')
V11_LIMITATIONS = [
    'This characterises a suppression; it does not establish that he decides.',
    'Drives are chosen rates on chosen cell groups.',
    'The transmitter-sign rule treats the dictionary vAB3 cells as inhibitory because they are glutamatergic here.',
    *[s.replace('in v9', 'in v11').replace('by this sweep', 'by this protocol')
      for s in V9_LIMITATIONS if not s.startswith(('The sweep', 'Mute changes'))]]


def v11_drive_flags(condition):
    return dict(orn_zeroed=condition in ('noscent_orn', 'noscent'),
                contact_zeroed=condition in ('noscent_contact', 'noscent'))


def summarise_v11(rows):
    indexed = {(r['seed'], r['condition']): r for r in rows}
    seeds = sorted({r['seed'] for r in rows})
    def comparison(metric, treatment, control):
        valid = []
        for seed in seeds:
            a = indexed.get((seed, treatment), {}).get(metric)
            b = indexed.get((seed, control), {}).get(metric)
            if a is not None and b is not None and np.isfinite(a) and np.isfinite(b):
                valid.append((seed, a-b))
        diffs = [d for _, d in valid]
        mean = float(np.mean(diffs)) if diffs else None
        se = float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs)>1 else None
        v = verdict(mean, se, len(diffs))
        return dict(metric=metric, treatment=treatment, control=control, mean=mean, se=se,
            n=len(diffs), paired_differences=diffs, valid_seeds=[s for s, _ in valid],
            excluded_seeds=[s for s in seeds if s not in [i for i, _ in valid]],
            verdict=v, established=len(diffs)==10 and v=='supported')
    predictions = {}
    for cue, label in (('orn', 'P29'), ('contact', 'P30')):
        predictions[label] = comparison('p1_hz', 'noscent_'+cue, 'song')
        for metric in ('pip10_hz', 'delivered_rms'):
            predictions['P31_'+cue+'_'+metric] = comparison(metric, 'noscent_'+cue, 'song')
    joint = {cue: all(predictions['P31_'+cue+'_'+m]['established']
                     for m in ('pip10_hz', 'delivered_rms')) for cue in ('orn', 'contact')}
    descriptive = {c: {m: {k: v for k, v in comparison(m, 'noscent', c).items()
                           if k not in ('verdict', 'established')}
                      for m in ('p1_hz', 'pip10_hz', 'delivered_rms')}
                   for c in ('noscent_orn', 'noscent_contact')}
    return dict(predictions=predictions, P31_joint=joint, P32=descriptive)


def v11_seed_table(data):
    keys = ('seed', 'condition', 'orn_zeroed', 'contact_zeroed', 'p1_hz', 'pip10_hz',
        'delivered_rms', 'vpodn_hz', 'accept', 'distance_mm', 'approach', 'retreat', 'contact_fraction')
    return ['| '+' | '.join(keys)+' |', '| '+' | '.join(['---']*len(keys))+' |'] + [
        '| '+' | '.join(f'{r[k]:.6g}' if isinstance(r[k], float) else str(r[k]) for k in keys)+' |'
        for r in data['outcomes']]


def write_v11_report(json_path, data):
    lines = ['# Courtship v11', '', '## Design record', data['protocol_spec']['text'],
        f"CHOSEN male positive-weight scale: {data['male_exc_scale']}.",
        'Female graph record: '+json.dumps(data['female_graph']),
        'Environment: '+json.dumps(data['environment']), '', '## Verdicts',
        '| Prediction | Difference | SE | n | >2 SE | Established (n=10) |',
        '|---|---:|---:|---:|---|---|']
    for label, p in data['summary']['predictions'].items():
        lines.append(f"| {label} | {p['mean']} | {p['se']} | {p['n']} | {p['verdict']} | {p['established']} |")
    lines += ['', '## Per-seed outcomes / P32', *v11_seed_table(data),
        '', 'P32: both removed minus each single removal (descriptive, no verdict):',
        json.dumps(data['summary']['P32']), '', '## Result',
        ' '.join(f"{k}: {'established' if data['summary']['predictions'][k]['established'] else 'not established'}." for k in ('P29', 'P30')),
        ' '.join(f"P31_{cue}: {'established' if ok else 'not established'} (both command and RMS required)." for cue, ok in data['summary']['P31_joint'].items()),
        'Quick run: smoke evidence only.' if data['quick'] else 'Ten-seed design; undefined pairs cannot establish a prediction.',
        'This characterises suppression and does not establish that he decides.',
        f"Estimated ten-seed cost: {data['estimated_ten_seed_hours']:.6g} hours; excludes setup and rendering.",
        '', '## Limitations', *['- '+s for s in data['limitations']]]
    destination = Path(str(json_path).replace('_experiment.json', '_report.md'))
    destination.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return destination


def run_v11(args, prefix, room_factory=None):
    if args.male_scale is None or not np.isfinite(args.male_scale) or args.male_scale <= 0:
        raise ValueError('v11 requires --male-scale with a finite positive value')
    if not args.quick and (args.seeds != 10 or args.steps != 400):
        raise ValueError('v11 requires ten seeds and 400 steps; use --quick 1 for smoke tests')
    graph = v8_graph_record()
    n, steps = (1 if args.seeds == 1 else 2, 80) if args.quick else (10, 400)
    cls = bw.brain_class(args.brain)
    brains = None if room_factory else (cls(), load_female(path=V8_GRAPH, exc_scale=.7, brain_class=cls))
    from contextlib import nullcontext
    rows, traces, timings = [], {}, []
    print(V11_TEXT+f'CHOSEN male positive-weight scale: {args.male_scale}', flush=True)
    for seed in range(n):
        start = None
        for condition in V11_CONDITIONS:
            with male_excitation(brains[0], args.male_scale) if brains else nullcontext():
                room = (room_factory(seed, condition, brains=brains) if room_factory else
                        build_room(seed, condition, brains=brains, protocol='v11'))
                room.protocol = 'v11'
                if start is not None and room.arena.geometry() != start:
                    raise ValueError('v11 paired start mismatch')
                start = room.arena.geometry()
                t0 = time.perf_counter()
                row, trace = run_trial(room, steps, seed, condition)
                elapsed = time.perf_counter()-t0
            row.update(male_exc_scale=args.male_scale, state_group='SAG',
                **v11_drive_flags(condition),
                distance_mm=float(np.mean(trace['distance_mm'])),
                contact_fraction=float(np.mean(trace['distance_mm'] < 2.)))
            rows.append(row)
            timings.append(dict(seed=seed, condition=condition, seconds=elapsed))
            traces.update({f's{seed}_{condition}_{k}': v for k, v in trace.items()})
            print(f'seed={seed} condition={condition} seconds={elapsed:.3f}', flush=True)
    data = dict(protocol='v11', protocol_spec=PROTOCOLS['v11'], seeds=list(range(n)),
        steps=steps, quick=bool(args.quick), male_exc_scale=args.male_scale,
        female_exc_scale=.7, female_graph=graph, female_eye=FEMALE_EYE,
        state_group='SAG', state_drive_hz=50., outcomes=rows, summary=summarise_v11(rows),
        limitations=V11_LIMITATIONS, timing=timings, ear=WaveEar().describe(),
        environment=dict(brain_class=args.brain), date=datetime.now(timezone.utc).isoformat())
    data['estimated_ten_seed_hours'] = float(np.mean([t['seconds']/steps for t in timings]))*16000/3600
    save(prefix, data, traces)
    print('\n'.join(v11_seed_table(data)), flush=True)
    print(json.dumps(data['summary'], indent=2), flush=True)
    return 0



V12_GRAPH = Path('build/graph_male_fsign.npz')
V12_SCALES = (0.9, 0.8)
V12_TEXT = """Protocol v12. Identical to v9 except the required functional-sign male graph and scales {0.9, 0.8}.
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
""" + V9_RULE.replace('P21', 'P33')
V12_LIMITATIONS = [s.replace('v9', 'v12') for s in V9_LIMITATIONS] + [
    'The override list is chosen from literature for three cell groups only: male vAB3, male mAL and the already restored female SAG. Every other modulatory class stays silenced.',
    'Functional excitation of P1 is extrapolated to all dictionary vAB3 outputs; receptor-specific effects are not modelled.']
PROTOCOLS['v12'] = dict(PROTOCOLS['v9'], text=V12_TEXT, male_exc_scales=V12_SCALES,
    male_graph=V12_GRAPH.as_posix(), budget_note='Exactly six cells x ten seeds; no full-run reduction.')


def v12_graph_record():
    from graft_sag import sha256
    if not V12_GRAPH.exists():
        raise ValueError('v12 requires build/graph_male_fsign.npz; run functional_sign.py first')
    with np.load(V12_GRAPH, allow_pickle=False) as z:
        record = json.loads(str(z['fsign']))
    return dict(path=V12_GRAPH.as_posix(), sha256=sha256(V12_GRAPH), fsign=record)


def summarise_v12(rows):
    result = summarise_v9(rows, V12_SCALES)
    def rename(value):
        if isinstance(value, dict):
            return {k.replace('P21', 'P33').replace('P22', 'P34'): rename(v) for k, v in value.items()}
        return value
    result = rename(result)
    for cell in result['cells']:
        rr = [r for r in rows if r['male_exc_scale'] == cell['male_exc_scale'] and r['condition'] == cell['condition']]
        cell.update({k: float(np.mean([r[k] for r in rr])) for k in ('mal_hz', 'vab3_hz')})
    return result


def v12_cell_table(data):
    keys = ('male_exc_scale', 'condition', 'n', 'p1_hz', 'pip10_hz', 'delivered_rms', 'male_total_hz', 'mal_hz', 'vab3_hz', 'vpodn_hz', 'accept')
    return ['| '+' | '.join(keys)+' |', '| '+' | '.join(['---']*len(keys))+' |'] + [
        '| '+' | '.join(f'{r[k]:.6g}' if isinstance(r[k], float) else str(r[k]) for k in keys)+' |' for r in data['summary']['cells']]


def write_v12_report(json_path, data):
    lines = ['# Courtship v12', '', data['protocol_spec']['text'], '', '## Override record',
        json.dumps(data['male_graph'], indent=2), '## Female graph record', json.dumps(data['female_graph']),
        '', '## Per-scale verdicts', '| Scale | Prediction | Difference | SE | n | Verdict | Reversed |', '|---|---|---|---|---|---|---|']
    for scale, predictions in data['summary']['per_scale'].items():
        for label, p in predictions.items():
            if isinstance(p, dict):
                lines.append(f"| {scale} | {label} | {p['mean']} | {p['se']} | {p['n']} | {p['verdict']} | {p['reversed']} |")
        lines.append(f"P33 joint at {scale}: {predictions['P33_verdict']}.")
    keys = ('male_exc_scale', 'seed', 'condition', 'p1_hz', 'pip10_hz', 'delivered_rms', 'male_total_hz', 'mal_hz', 'vab3_hz', 'vpodn_hz', 'accept', 'approach', 'retreat')
    lines += ['', '## Per-seed outcomes', data['protocol_spec']['outcome_text'], '| '+' | '.join(keys)+' |', '| '+' | '.join(['---']*len(keys))+' |']
    lines += ['| '+' | '.join(str(r[k]) for k in keys)+' |' for r in data['outcomes']]
    lines += ['', '## P35 (descriptive)', *v12_cell_table(data), '', '## Result',
        ' '.join(f'{k}: {v}.' for k, v in data['summary']['established'].items()),
        'Quick run: smoke evidence only.' if data['quick'] else 'All ten paired seeds reported at both scales.',
        'A null means this narrow correction does not recover P1 control at these doses, not that the pathway is absent.',
        *[f"At scale {scale}, song minus mute is {p['P33_command']['mean']:.6g} Hz in pIP10 and {p['P33_rms']['mean']:.6g} in delivered RMS; song minus noscent is {p['P34']['mean']:.6g} Hz in P1."
          for scale, p in data['summary']['per_scale'].items()],
        f"Across the recorded scale/condition cells, vAB3 mean rates span {min(r['vab3_hz'] for r in data['summary']['cells']):.6g} to {max(r['vab3_hz'] for r in data['summary']['cells']):.6g} Hz; mAL means span {min(r['mal_hz'] for r in data['summary']['cells']):.6g} to {max(r['mal_hz'] for r in data['summary']['cells']):.6g} Hz (descriptive).",
        f"Ten-seed cost: {data['estimated_ten_seed_hours']:.6g} hours; excludes setup and rendering.",
        '', '## Limitations', *['- '+s for s in data['limitations']]]
    destination = Path(str(json_path).replace('_experiment.json', '_report.md'))
    destination.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return destination


def run_v12(args, prefix, room_factory=None):
    if not args.quick and (args.seeds != 10 or args.steps != 400):
        raise ValueError('v12 requires ten seeds and 400 steps; use --quick 1 for smoke tests')
    male_graph = v12_graph_record()
    graph = v8_graph_record()
    n, steps = (1 if args.seeds == 1 else 2, 80) if args.quick else (10, 400)
    cls = bw.brain_class(args.brain)
    brains = None if room_factory else (cls(graph_path=V12_GRAPH), load_female(path=V8_GRAPH, exc_scale=.7, brain_class=cls))
    rows, traces, timings, starts = [], {}, [], {}
    from contextlib import nullcontext
    for scale in V12_SCALES:
        for seed in range(n):
            for condition in V9_CONDITIONS:
                with male_excitation(brains[0], scale) if brains else nullcontext():
                    room = (room_factory(seed, condition, brains=brains) if room_factory else
                            build_room(seed, condition, brains=brains, protocol='v12'))
                    room.protocol = 'v12'
                    start = room.arena.geometry()
                    if seed in starts and start != starts[seed]:
                        raise ValueError('v12 paired start mismatch')
                    starts[seed] = start
                    t0 = time.perf_counter()
                    row, trace = run_trial(room, steps, seed, condition)
                    elapsed = time.perf_counter()-t0
                row['male_exc_scale'] = scale
                rows.append(row)
                timings.append(dict(male_exc_scale=scale, seed=seed, condition=condition, step_s=elapsed/steps))
                traces.update({f's{seed}_{condition}_scale{scale}_{k}': v for k, v in trace.items()})
                print(f'scale={scale} seed={seed} condition={condition} step_s={elapsed/steps:.6f}', flush=True)
                if len(rows) == 1:
                    print(f'First-trial ten-seed estimate: {elapsed/steps*6*10*400/3600:.6g} hours (6 cells x 10 seeds x 400 steps).', flush=True)
    hours = float(np.mean([t['step_s'] for t in timings]))*6*10*400/3600
    data = dict(protocol='v12', protocol_spec=PROTOCOLS['v12'], seeds=list(range(n)), steps=steps,
        quick=bool(args.quick), male_exc_scales=V12_SCALES, female_exc_scale=.7,
        male_graph=male_graph, female_graph=graph, female_eye=FEMALE_EYE, state_group='SAG', state_drive_hz=50.,
        outcomes=rows, summary=summarise_v12(rows), timing=timings, estimated_ten_seed_hours=hours,
        limitations=V12_LIMITATIONS, ear=WaveEar().describe(),
        environment=dict(brain_class=args.brain, torch_devices={name: str(getattr(fb, 'device', None))
            for name, fb in zip(('male', 'female'), brains or (None, None))}),
        date=datetime.now(timezone.utc).isoformat())
    jp, npz, png, _ = paths(prefix)
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    np.savez_compressed(npz, **traces)
    # Keep the existing four-artifact contract, with one labelled panel per cell.
    plot_data = dict(data, protocol_spec=dict(data['protocol_spec'], conditions={
        f'{c} scale {scale}': V9_CONDITIONS[c] for scale in V12_SCALES for c in V9_CONDITIONS}),
        outcomes=[dict(r, condition=f"{r['condition']} scale {r['male_exc_scale']}") for r in rows])
    plot_traces = {}
    for r in rows:
        source = f"s{r['seed']}_{r['condition']}_scale{r['male_exc_scale']}_"
        target = f"s{r['seed']}_{r['condition']} scale {r['male_exc_scale']}_"
        plot_traces.update({target+k[len(source):]: v for k, v in traces.items() if k.startswith(source)})
    render_pil(png, plot_data, plot_traces)
    write_report(jp)
    print('\n'.join(v12_cell_table(data)), flush=True)
    print(f'Ten-seed cost: {hours:.6g} hours (6 cells x 10 seeds x 400 steps), excluding setup and rendering.', flush=True)
    return 0


def main(argv=None, room_factory=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol", choices=PROTOCOLS, default="v5")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    ap.add_argument("--quick", type=int, choices=(0, 1), default=0)
    ap.add_argument("--brain", default="flysim.FlyBrain")
    ap.add_argument('--male-scale', type=float)
    ap.add_argument("--baseline")
    ap.add_argument("--out")
    ap.add_argument("--budget-min", type=float, default=150)
    ap.add_argument("--log")
    ap.add_argument("--reanalyse")
    ap.add_argument("--note")
    args = ap.parse_args(argv)
    prefix = Path(args.out or f"build/courtship_{args.protocol}_quick")
    if args.reanalyse:
        jp = Path(args.reanalyse)
        if not str(jp).endswith("_experiment.json"):
            jp = paths(jp)[0]
        prefix = Path(str(jp)[:-len("_experiment.json")])
    try:
        assert_not_published(prefix)
    except ValueError as exc:
        print(exc)
        return 4
    if args.reanalyse:
        data = json.loads(jp.read_text(encoding="utf-8"))
        if data['protocol'] == 'v12':
            data['summary'] = summarise_v12(data['outcomes'])
            jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
            write_report(jp)
            return 0
        if data['protocol'] == 'v11':
            data['summary'] = summarise_v11(data['outcomes'])
            jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
            write_report(jp)
            return 0
        if data['protocol'] == 'v10':
            data['summary'] = summarise_v10(data['outcomes'])
            jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
            write_report(jp)
            return 0
        if data['protocol'] == 'v9':
            data['summary'] = summarise_v9(data['outcomes'])
            jp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
            write_report(jp)
            return 0
        with np.load(paths(prefix)[1]) as z:
            traces = dict(z)
        data["outcomes"] = [dict(r, **outcome(r["seed"], r["condition"],
            {k.split(f"s{r['seed']}_{r['condition']}_", 1)[1]: v for k, v in traces.items()
             if k.startswith(f"s{r['seed']}_{r['condition']}_")}, r["start"])) for r in data["outcomes"]]
        if data["protocol"] == "v6":
            baseline, identity = read_baseline(args.baseline or data["baseline"]["path"], data["seeds"], data["steps"], data["environment"]["brain_class"])
            if identity["sha256"] != data["baseline"]["sha256"]:
                raise ValueError("baseline SHA256 changed")
            for r in data["outcomes"]:
                check_baseline_start(baseline, r["seed"], r["start"])
            data["summary"] = summarise_v6(data["outcomes"], baseline["outcomes"])
        else:
            data["summary"] = (summarise_v7 if data["protocol"] in ("v7", "v8") else summarise)(data["outcomes"])
        data["reanalysis_note"] = args.note
        save(prefix, data, traces)
        return 0
    n, steps = (2, 80) if args.quick else (args.seeds, args.steps)
    if n < 1 or steps < 4 or not np.isfinite(args.budget_min) or args.budget_min <= 0:
        ap.error("positive seeds and budget, and at least four steps required")
    conditions = PROTOCOLS[args.protocol]["conditions"]
    if args.protocol == 'v12':
        return run_v12(args, prefix, room_factory)
    if args.protocol == 'v9':
        return run_v9(args, prefix, room_factory)
    if args.protocol == 'v11':
        return run_v11(args, prefix, room_factory)
    if args.protocol == 'v10':
        return run_v10(args, prefix, room_factory)
    baseline = baseline_identity = None
    if args.protocol == "v6":
        baseline, baseline_identity = read_baseline(args.baseline, list(range(n)), steps, args.brain)
    factory = room_factory or build_room
    sag_protocol = args.protocol in ('v7', 'v8')
    graph_record = v8_graph_record() if args.protocol == 'v8' else v7_graph_record() if args.protocol == 'v7' else None
    protocol_spec = v8_protocol_spec(graph_record) if args.protocol == 'v8' else PROTOCOLS[args.protocol]
    if graph_record is None:
        from graft_sag import sha256
        graph_path = Path(os.environ.get('FEMALE_GRAPH') or courtship.BUILD/'graph_female.npz')
        graph_record = dict(path=Path(os.path.relpath(graph_path)).as_posix(), sha256=sha256(graph_path))
    exc_scale = V7_EXC_SCALE if sag_protocol else FEMALE_EXC_SCALE
    cls = bw.brain_class(args.brain)
    female_options = dict(exc_scale=exc_scale, brain_class=cls)
    if sag_protocol:
        female_options['path'] = V8_GRAPH if args.protocol == 'v8' else V7_GRAPH
    brains = None if room_factory else (cls(), load_female(**female_options))
    environment = dict(brain_class=args.brain, torch_devices={
        name: str(fb.device) if getattr(fb, "device", None) is not None else None
        for name, fb in zip(("male", "female"), brains or (None, None))})
    rows, traces, timings = [], {}, []
    ladder = None
    seed = 0
    while seed < n:
        sound = None
        for c in conditions:
            room_options = dict(song_sound=sound, brains=brains)
            if room_factory is None:
                room_options['protocol'] = args.protocol
            room = factory(seed, c, **room_options)
            if baseline is not None:
                check_baseline_start(baseline, seed, room.arena.geometry())
            t0 = time.perf_counter()
            row, trace = run_trial(room, steps, seed, c)
            elapsed = time.perf_counter() - t0
            timings.append(dict(seed=seed, condition=c, seconds=elapsed, step_s=elapsed/steps,
                                her_brain_s=float(trace["her_brain_s"].mean())))
            message = f"seed={seed} condition={c} step_s={elapsed/steps:.6f} active_windows={row['active_windows']}"
            print(message, flush=True)
            if args.log:
                with Path(args.log).open("a", encoding="utf-8") as log:
                    log.write(message + "\n")
            if seed == 0 and c in ("song", "virgin_song"):
                budget_elapsed = elapsed * len(conditions)/len(CONDITIONS) if sag_protocol else elapsed
                ladder = budget_ladder(n, budget_elapsed, args.budget_min * 60)
                ladder["first_step_s"] = elapsed / steps
                n = ladder["selected"]
            if c == "song":
                sound = trace
            rows.append(row)
            traces.update({f"s{seed}_{c}_{k}": v for k, v in trace.items()})
        seed += 1
    data = dict(protocol=args.protocol, protocol_spec=protocol_spec, steps=steps,
        seeds=list(range(n)), quick=bool(args.quick), outcomes=rows,
        summary=summarise_v6(rows, baseline["outcomes"]) if baseline is not None else (summarise_v7(rows) if sag_protocol else summarise(rows)),
        female_exc_scale=exc_scale, female_eye=FEMALE_EYE,
        FEMALE_GRAPH_present='FEMALE_GRAPH' in os.environ,
        state_group="SAG" if sag_protocol else "SpsP",
        ear=WaveEar().describe(), limitations=V6_LIMITATIONS if baseline is not None else (V8_LIMITATIONS if args.protocol == 'v8' else V7_LIMITATIONS if args.protocol == "v7" else LIMITATIONS),
        budget_ladder=ladder, timing=timings, environment=environment, note=args.note,
        date=datetime.now(timezone.utc).isoformat())
    if baseline_identity is not None:
        data["baseline"] = baseline_identity
    data['female_graph'] = graph_record
    if args.protocol == 'v8':
        data['state_cells'] = graph_record['state_cells']
        data['state_cells_per_type'] = graph_record['state_cells_per_type']
    if sag_protocol:
        data['estimated_ten_seed_hours'] = float(np.mean([t['step_s'] for t in timings])) * 4 * 4000 / 3600
        print(f"Estimated ten-seed cost (4 x 400 windows each): {data['estimated_ten_seed_hours']:.3g} hours, excluding setup and rendering.", flush=True)
    save(prefix, data, traces)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
