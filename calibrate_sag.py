"""Before-data v8 ladder: GPU, JO 60 Hz, eight carried 250-step windows.

For each scale, reset each of the four JO/state combinations to rest with seed 0.
Silence is recorded for both state rates so its meaning is explicit.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import courtship
from courtship_experiment import V8_GRAPH, V8_STATE_PATTERN, V8_CALIBRATION
from flysim_gpu import FlyBrainGPU
from graft_sag import sha256


def run(graph=V8_GRAPH, output=V8_CALIBRATION):
    rows = []
    for scale in (.9, .8, .7, .6):
        fb = courtship.load_female(graph, exc_scale=scale, brain_class=FlyBrainGPU)
        if str(fb.device) != 'cuda':
            raise ValueError('calibration requires CUDA')
        groups = courtship.female_groups(fb, sag_pattern=V8_STATE_PATTERN)
        jo = np.unique(np.concatenate([groups['JO_A'], groups['JO_B']]))
        for sound in (60., 0.):
            for sag in (0., courtship.STATE_HZ):
                state, windows = None, []
                drive = {tuple(jo): sound, tuple(groups['SAG']): sag}
                for _ in range(8):
                    result = fb.run(drive, 250, record={k: groups[k] for k in ('pC1', 'vpoDN')}, seed=0, state=state)
                    state = result['_state']
                    windows.append({k: float(np.mean(result[k])) for k in ('pC1', 'vpoDN')})
                row = dict(scale=scale, jo_hz=sound, sag_hz=sag, seed=0,
                           pc1_hz=float(np.mean([w['pC1'] for w in windows])),
                           vpodn_hz=float(np.mean([w['vpoDN'] for w in windows])),
                           active_windows=sum(w['vpoDN'] > 0 for w in windows), windows=windows)
                rows.append(row)
                print(json.dumps({k: v for k, v in row.items() if k != 'windows'}), flush=True)
        del fb
    lines = ['Calibration record measured before v8 data: GPU CUDA, JO 60 Hz and silence, '
             'eight carried windows x 250 steps per arm; each arm starts at rest with seed 0. '
             'Both JO groups receive the stated uniform rate; state group has both FAFB SAG types. '
             'Zero-rate keys remain in the drive in every arm, preserving paired random draws.',
             '| Positive-weight scale | JO Hz | SAG Hz | pC1 Hz | vpoDN Hz | Active windows / 8 |',
             '|---:|---:|---:|---:|---:|---:|']
    lines += [f"| {r['scale']} | {r['jo_hz']:g} | {r['sag_hz']:g} | {r['pc1_hz']:.6g} | {r['vpodn_hz']:.6g} | {r['active_windows']} |" for r in rows]
    if any(r['scale'] == .7 and r['jo_hz'] == 0 and r['vpodn_hz'] > 0 for r in rows):
        lines.append('Silence gives nonzero vpoDN at scale 0.7 with SAG driven; scale 0.7 is nevertheless retained as specified before this ladder.')
    else:
        lines.append('Silence gives zero vpoDN at scale 0.7; scale 0.7 is retained as specified before this ladder.')
    record = dict(graph=Path(graph).as_posix(), graph_sha256=sha256(graph),
                  date=datetime.now(timezone.utc).isoformat(), brain_class='flysim_gpu.FlyBrainGPU',
                  device='cuda', state_pattern=V8_STATE_PATTERN, state_cells=len(groups['SAG']),
                  state_hz=courtship.STATE_HZ, steps=250, windows=8, rows=rows, text='\n'.join(lines))
    Path(output).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(record['text'], flush=True)
    return record


if __name__ == '__main__':
    run()
