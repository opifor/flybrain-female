"""BANC archive contract, map-independent selectors, and optional real counts."""
import os

import numpy as np
import pandas as pd
import pytest

from build_graph_banc import build
from courtship import female_groups, load_female
from flysim import BUILD, FlyBrain


@pytest.fixture
def archive(tmp_path):
    n = 9
    pd.DataFrame(dict(
        banc_888_id=[str(720575941000000000 + i) for i in range(n)],
        cell_type=['JO-A', 'JO-B', None, 'DNp37', 'oviDNb', 'SPSN', 'ANXXX983', 'M', 'glia'],
        fafb_cell_type=['', '', 'pC1c', '', '', '', '', '', ''],
        super_class=['sensory', 'sensory', 'central', 'descending', 'descending',
                     'sensory', 'ascending', 'motor', 'glia'],
        cell_sub_class=['']*5 + ['sex_peptide_sensory_neuron', '', '', ''],
        neurotransmitter_predicted=['acetylcholine', 'gaba', 'glutamate', 'dopamine',
                                   'histamine', 'serotonin', 'octopamine', 'tyramine', 'acetylcholine'],
        side=['left', 'right', None] * 3,
        root_position=['1, 2, 3', None, ''] * 3,
        body_part_effector=[None]*7 + ['wing', ''], region=['central_brain']*n,
        cell_class=['test']*n)).to_feather(tmp_path / 'banc_888_meta.feather')
    ids = [str(720575941000000000 + i) for i in range(n)]
    pd.DataFrame(dict(pre=[ids[i] for i in [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 0]],
                      post=[ids[i] for i in [1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 8]],
                      count=[5, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14])).to_feather(
                          tmp_path / 'banc_888_edgelist_simple_v3.feather')
    return build(tmp_path, tmp_path / 'graph.npz')


def test_builder_contract(archive, capsys):
    fb = FlyBrain(archive)
    assert fb.n == 8
    expected = np.zeros((8, 8), np.float32)
    expected[1, 0], expected[2, 1], expected[0, 2] = 5*.275, -6*.275, -7*.275
    np.testing.assert_allclose(fb.W.toarray(), expected)
    assert fb.bodies[0] == 720575941000000000
    assert fb.types[2] == 'pC1c'
    with np.load(archive, allow_pickle=False) as z:
        np.testing.assert_array_equal(z['sign'], [1, -1, -1, 0, 0, 0, 0, 0])
        assert z['fafb_types'][2] == 'pC1c'
        assert z['effector'].tolist() == ['']*7 + ['wing']
        for key in ('types', 'fafb_types', 'region', 'cell_class', 'effector', 'nt', 'nt_cell'):
            assert z[key].dtype.kind == 'U' and z[key].shape == (8,)
        for key in ('data', 'sign', 'soma', 'exc_scale', 'click_hz', 'back_scale'):
            assert z[key].dtype == np.float32
        for key in ('indices', 'indptr', 'hex1', 'hex2'):
            assert z[key].dtype == np.int32
        assert z['bodies'].dtype == np.int64
        assert z['soma'].shape == (8, 3)
        np.testing.assert_array_equal(z['soma'][0], [1, 2, 3])
        assert np.isnan(z['soma'][1:3]).all()
        assert z['soma_side'].tolist() == ['L', 'R', '', 'L', 'R', '', 'L', 'R']
        assert z['eye'].tolist() == ['none']
        assert not z['has_hex'].any() and not z['hex1'].any() and not z['hex2'].any()
        assert z['exc_scale'] == z['back_scale'] == 1 and z['click_hz'] == 100
        assert not z['adapt'] and (z['receptor'] == '').all() and (z['fru'] == '').all()
    assert np.isfinite(fb.run({}, 2)['_total_hz'])


def test_selectors_and_override(archive, monkeypatch):
    monkeypatch.setenv('FEMALE_GRAPH', str(archive))
    fb = load_female()
    groups = female_groups(fb)
    assert {k: v.tolist() for k, v in groups.items()} == dict(
        JO_A=[0], JO_B=[1], pC1=[2], vpoDN=[3], oviDN=[4], SpsP=[5],
        SAG=[6], wing_mn=[7], leg_mn=[], abd_mn=[])
    for effector, key in [('front_leg', 'leg_mn'), ('middle_leg', 'leg_mn'),
                          ('hind_leg', 'leg_mn'), ('abdomen', 'abd_mn')]:
        fb.effector = np.array(['']*7 + [effector])
        assert female_groups(fb)[key].tolist() == [7]
    del fb.effector
    assert all(female_groups(fb)[k].size == 0 for k in ('wing_mn', 'leg_mn', 'abd_mn'))
    monkeypatch.setenv('FEMALE_GRAPH', 'missing.npz')
    assert load_female(archive).n == 8  # Explicit path wins.


@pytest.mark.skipif(os.environ.get('COURTSHIP_REAL_BRAIN') != '1', reason='set COURTSHIP_REAL_BRAIN=1')
def test_real_banc_counts():
    fb = load_female(BUILD / 'graph_banc.npz')
    groups = female_groups(fb)
    expected = dict(JO_A=93, JO_B=416, pC1=10, vpoDN=2, oviDN=6, SpsP=6, SAG=2)
    assert {key: len(groups[key]) for key in expected} == expected
    np.testing.assert_array_equal(groups['SpsP'], fb.where(type_re='^SPSN$'))
    assert (fb.region[groups['pC1']] == 'central_brain').all()
    assert not np.intersect1d(groups['SpsP'], fb.where(type_re='^SpsP$')).size
