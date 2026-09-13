import numpy as np
import pandas as pd

from build_graph import select_neurons


def test_brain_only_drops_vnc_prefix():
    ann = pd.DataFrame({
        'bodyId': [9, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12],
        'status': ['Traced'] * 9 + ['Untraced', 'Traced'],
        'statusLabel': ['Neuron'] * 10 + ['Glia'],
        'superclass': ['vnc_motor', 'vnc_sensory', 'vnc_intrinsic',
                       'ascending_neuron', 'descending_neuron', 'cb_motor',
                       None, 'other_vnc_motor', 'vnc_future', 'vnc_motor', 'vnc_motor'],
    })
    bodies, dropped = select_neurons(ann, brain_only=True)
    assert bodies.tolist() == [4, 5, 6, 7, 8]
    assert dropped.to_dict() == {
        'vnc_future': 1, 'vnc_intrinsic': 1, 'vnc_motor': 1, 'vnc_sensory': 1,
    }
    original = np.sort(ann.loc[(ann.status == 'Traced') &
                               (ann.statusLabel != 'Glia'), 'bodyId'].unique())
    default, dropped = select_neurons(ann)
    np.testing.assert_array_equal(default, original)
    assert dropped.empty
