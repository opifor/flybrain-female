"""Type-level transplant arithmetic and source protection."""
import json

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from graft_sag import build, sha256


@pytest.fixture
def graft_files(tmp_path):
    source = tmp_path/'female.npz'
    w = sp.csr_matrix(([3.], ([0], [2])), shape=(5, 5), dtype=np.float32)
    np.savez_compressed(source, data=w.data, indices=w.indices, indptr=w.indptr,
                        shape=w.shape, types=['AN_SMP_2', 'AN_SMP_2', 'pC1a', 'pC1a', 'other'],
                        extra=np.array(['preserve']))
    pd.DataFrame(dict(banc_888_id=[1, 2, 3, 4, 5],
                      cell_type=['ANXXX983', 'ANXXX983', 'local', 'absent', 'local'],
                      fafb_cell_type=['AN_SMP_2', 'AN_FLA_SMP_2', 'pC1a', 'missing', None],
                      neurotransmitter_predicted=['dopamine']*5)).to_feather(tmp_path/'banc_888_meta.feather')
    pd.DataFrame(dict(pre=[1, 2, 1, 1, 3], post=[3, 3, 4, 5, 3],
                      count=[8, 4, 3, 7, 100])).to_feather(tmp_path/'banc_888_edgelist_simple_v3.feather')
    return source, tmp_path, tmp_path/'grafted.npz', tmp_path/'graft.json'


def test_graft_arithmetic_accounting_idempotence(graft_files):
    source, _, out, report = graft_files
    before = sha256(source)
    build(*graft_files)
    with np.load(out) as z:
        w = sp.csr_matrix((z['data'], z['indices'], z['indptr']), shape=tuple(z['shape'])).toarray()
        expected = np.zeros((5, 5), np.float32)
        expected[0, 2] = 3
        expected[2:4, :2] = 12*.275/4
        np.testing.assert_array_equal(w, expected)
        assert z['extra'].tolist() == ['preserve']
        graft = json.loads(z['graft'].item())
    assert graft['synapses_placed'] == 12 and graft['synapses_missing'] == 3
    assert graft['missing_types'] == ['missing']
    assert graft['unnamed_synapses_excluded'] == 7
    assert graft['total_outgoing_synapses'] == 22
    assert '+1' in graft['sign_choice'] and 'dopamine' in graft['sign_choice']
    assert graft['sources'][0]['sha256'] == before
    assert len(json.loads(report.read_text())['per_type']) == 2
    hashes = sha256(out), sha256(report)
    build(*graft_files)
    assert hashes == (sha256(out), sha256(report))
    assert sha256(source) == before


def test_graft_refuses_existing_outputs_and_source_alias(graft_files):
    source, folder, out, report = graft_files
    build(*graft_files)
    with pytest.raises(ValueError, match='already have outputs'):
        build(out, folder, folder/'again.npz', report)
    with pytest.raises(ValueError, match='aliases'):
        build(source, folder, source, report)


def test_graft_by_type_keeps_donors_separate(graft_files):
    source, folder, output, report = graft_files
    with np.load(source) as z:
        archive = dict(z)
    archive['types'][1] = 'AN_FLA_SMP_2'
    # Widen string storage before assigning the longer second receiver type.
    archive['types'] = np.array(['AN_SMP_2', 'AN_FLA_SMP_2', 'pC1a', 'pC1a', 'other'])
    np.savez_compressed(source, **archive)
    build(*graft_files, receivers='by-type')
    with np.load(output) as z:
        w = sp.csr_matrix((z['data'], z['indices'], z['indptr']), shape=tuple(z['shape'])).toarray()
        np.testing.assert_allclose(w[2:4, 0], 8*.275/2)
        np.testing.assert_allclose(w[2:4, 1], 4*.275/2)
        assert json.loads(z['graft'].item())['receivers'] == 'by-type'
    assert json.loads(report.read_text())['synapses_placed'] == 12
    with pytest.raises(ValueError, match='already have outputs'):
        build(output, folder, folder/'again.npz', report, receivers='by-type')
