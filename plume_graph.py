import hashlib
import time
from pathlib import Path

import numpy as np

import calibration


def file_record(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path.resolve()), 'sha256': digest.hexdigest()}


def prepare(fb):
    gains = calibration.gains_for(fb, calibration.CHOSEN)
    side = fb.soma_side
    if side is None:
        import pandas as pd
        annotations = pd.read_feather('data/body-annotations.feather').drop_duplicates('bodyId').set_index('bodyId')
        side = annotations['somaSide'].reindex(fb.bodies).fillna('').to_numpy().astype(str)
    from plume_fly import root_side_of, motor_groups
    wind_side = root_side_of(fb)
    selections = {}
    for name, regex in [('ORN', '^ORN_'), ('JO_C', '^JO-C'), ('JO_E', '^JO-E'), ('JO_CE', '^JO-(C|E)')]:
        indices = fb.where(type_re=regex)
        sides = np.asarray(side if name == 'ORN' else wind_side)[indices]
        selections[name] = dict(total=len(indices), types=len(set(fb.types[indices])),
                                L=int(np.sum(sides == 'L')), R=int(np.sum(sides == 'R')),
                                unsided=int(np.sum(~np.isin(sides, ['L', 'R']))))
        if name != 'ORN' and selections[name]['unsided']:
            raise ValueError(name + ' has unresolved sides')
    if any(len(indices) == 0 for indices in motor_groups(fb).values()):
        raise ValueError('A walking motor population could not be resolved')
    record = dict(graph=file_record(fb.graph_path), neurons=fb.n, exc_scale=fb.exc_scale,
                  calibration_file=file_record('calibration.py'), calibration_setting=calibration.CHOSEN,
                  calibration_rule=calibration.SETTINGS[calibration.CHOSEN]['gains'],
                  effective_gains={str(t): float(v) for t, v in zip(fb.type_names, gains)},
                  effective_gains_sha256=hashlib.sha256(gains.tobytes()).hexdigest(), selections=selections)
    timings = record['brain_wall_time_s'] = []
    original_run = fb.run

    def timed_run(*args, **kwargs):
        start = time.perf_counter()
        result = original_run(*args, **kwargs)
        timings.append(time.perf_counter() - start)
        return result

    fb.run = timed_run
    return gains, record
