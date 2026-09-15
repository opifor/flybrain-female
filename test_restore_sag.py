"""Own-map restoration preserves individual pairs and discloses exclusions."""
import json

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from graft_sag import sha256
from restore_sag import build, banc_table, comparison_table


@pytest.fixture
def restore_files(tmp_path):
    source, csv = tmp_path/'female.npz', tmp_path/'connections.csv.gz'
    w = sp.csr_matrix(([-2.], ([0], [2])), shape=(4, 4), dtype=np.float32)
    np.savez_compressed(source, data=w.data, indices=w.indices, indptr=w.indptr, shape=w.shape,
                        bodies=np.array([101, 102, 103, 104], dtype=np.int64),
                        types=['AN_SMP_2', 'AN_FLA_SMP_2', 'pC1a', ''],
                        sign=[0., 0., -1., 1.], nt=['serotonin', 'serotonin', 'gaba', 'acetylcholine'],
                        extra=['preserve'])
    pd.DataFrame(dict(pre_root_id=[101, 101, 102, 102, 102, 103],
                      post_root_id=[103, 104, 103, 104, 999, 101],
                      syn_count=[5, 4, 7, 6, 9, 50])).to_csv(csv, index=False)
    banc = tmp_path/'banc.json'
    banc.write_text(json.dumps(dict(per_type=[dict(target_type='pC1a', synapses=10)])), encoding='utf-8')
    return source, csv, tmp_path/'restored.npz', tmp_path/'restore.json', banc


def test_restore_sign_floor_individual_pairs_and_metadata(restore_files):
    source, _, output, report, _ = restore_files
    before = sha256(source)
    build(*restore_files)
    with np.load(output, allow_pickle=False) as z:
        w = sp.csr_matrix((z['data'], z['indices'], z['indptr']), shape=tuple(z['shape'])).toarray()
        expected = np.zeros((4, 4), np.float32)
        expected[0, 2] = -2
        expected[2, 0] = 5*.275
        expected[2, 1] = 7*.275
        expected[3, 1] = 6*.275
        np.testing.assert_allclose(w, expected)
        assert z['extra'].tolist() == ['preserve']
        assert z['sign'].tolist() == [1., 1., -1., 1.]
        assert z['nt'][0] == 'serotonin'
        metadata = json.loads(z['restore'].item())
    assert metadata == json.loads(report.read_text(encoding='utf-8'))
    assert metadata['synapses_restored'] == 18 and metadata['excluded_synapses'] == 13
    assert metadata['empty_types'] == []
    assert metadata['per_type']['AN_SMP_2']['restored_synapses'] == 5
    assert metadata['per_type']['AN_FLA_SMP_2']['restored_synapses'] == 13
    assert all(v['cell_count'] == 1 for v in metadata['per_type'].values())
    table = {r['target_type']: r for r in metadata['per_target_type']}
    assert table['pC1a'] == dict(target_type='pC1a', synapses=12,
                               by_source_type=dict(AN_SMP_2=5, AN_FLA_SMP_2=7))
    assert table['']['synapses'] == 6
    assert metadata['sources'][1]['sha256'] == before == sha256(source)
    assert '+1' in metadata['sign_choice'] and 'Neither prediction' in metadata['sign_choice']
    first = sha256(output)
    build(*restore_files)
    assert sha256(output) == first


def test_restore_refusal_and_empty_type(restore_files):
    source, csv, output, report, banc = restore_files
    build(*restore_files)
    with pytest.raises(ValueError, match='already have outputs'):
        build(output, csv, output.parent/'again.npz', report, banc)
    with pytest.raises(ValueError, match='aliases'):
        build(source, csv, source, report, banc)
    rows = pd.read_csv(csv)
    rows[rows.pre_root_id != 102].to_csv(csv, index=False)
    build(*restore_files)
    metadata = json.loads(report.read_text(encoding='utf-8'))
    assert metadata['empty_types'] == ['AN_FLA_SMP_2']
    assert metadata['per_type']['AN_FLA_SMP_2']['cells'][0]['restored_synapses'] == 0


def test_banc_fallback_without_writing_graft(tmp_path):
    pd.DataFrame(dict(banc_888_id=[1, 2, 3], cell_type=['ANXXX983', 'ANXXX983', 'x'],
                      fafb_cell_type=['AN_SMP_2', 'AN_FLA_SMP_2', 'pC1a'])).to_feather(tmp_path/'banc_888_meta.feather')
    pd.DataFrame(dict(pre=[1, 2], post=[3, 3], count=[4, 8])).to_feather(tmp_path/'banc_888_edgelist_simple_v3.feather')
    report = tmp_path/'old.json'
    report.write_text('{}', encoding='utf-8')
    rows = banc_table(report, tmp_path)
    assert rows == [dict(target_type='pC1a', synapses=12)]
    assert report.read_text() == '{}'
    assert '| pC1a | 0 | 0 | 0 | 12 |' in comparison_table([], rows)
