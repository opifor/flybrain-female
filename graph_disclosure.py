import numpy as np

from flyeye import FlyPilot


def disclose(fb, record):
    pilot = FlyPilot(fb)
    for name, indices in pilot.motor.items():
        if not len(indices):
            raise ValueError(name + ' motor population could not be resolved')
        record['selections'][name] = dict(total=len(indices))
    record['click_readout'] = dict(source=pilot.click_source,
                                  bodies=fb.bodies[pilot.motor['click']].tolist())
    with np.load(fb.graph_path, allow_pickle=False) as graph:
        if 'dropped_superclasses' in graph.files:
            record['dropped_superclasses'] = dict(zip(
                graph['dropped_superclasses'].tolist(),
                graph['dropped_superclass_counts'].tolist()))
