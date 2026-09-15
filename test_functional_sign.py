"""CPU fake-data contracts for the two chosen overrides and protocol v12."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp
import functional_sign as fs
import courtship_experiment as ce
from test_courtship_experiment import FakeRoom


def test_overrides():
    types = np.array(['AN09B017e', 'mAL_m1', 'mAL_m2', 'other', 'mAL4A'])
    sign = np.array([-1., 0., -1., 0., 0.], dtype=np.float32)
    actual, record = fs.apply_overrides(types, ['glutamate', 'unclear', 'gaba', 'dopamine', 'unclear'], sign, np.arange(5))
    np.testing.assert_array_equal(actual, [1., -1., -1., 0., 0.])
    np.testing.assert_array_equal(sign, [-1., 0., -1., 0., 0.])
    assert [r['changed_cells'] for r in record] == [1, 1]


def test_build_contract_and_force(tmp_path):
    types = ['AN09B017e', 'mAL_m1', 'other', 'target']
    ann = pd.DataFrame(dict(bodyId=[1, 2, 3, 4, 5], type=types+['glia'],
        flywireType=['']*5, instance=['']*5, status=['Traced']*5,
        statusLabel=['']*4+['Glia'], superclass=['']*5, subclass=['']*5,
        receptorType=['']*5, fruDsx=['']*5))
    ann.to_feather(tmp_path/'body-annotations.feather')
    pd.DataFrame(dict(body=[1, 2, 3, 4], consensus_nt=['glutamate', 'unclear', 'acetylcholine', 'dopamine'])).to_feather(tmp_path/'body-neurotransmitters.feather')
    pd.DataFrame(dict(body_pre=[1, 2, 3, 1, 1, 5, 4], body_post=[4, 4, 4, 3, 5, 4, 1], weight=[4, 5, 6, 2, 9, 8, 7])).to_feather(tmp_path/'connectome-weights.feather')
    w = sp.csr_matrix((np.array([4, 6], dtype=np.float32)*fs.MV_PER_SYNAPSE*np.array([-1, 1], dtype=np.float32), ([3, 3], [0, 2])), shape=(4, 4))
    baseline = tmp_path/'baseline.npz'
    np.savez(baseline, data=w.data, indices=w.indices, indptr=w.indptr, shape=w.shape,
             bodies=np.arange(1, 5), sign=np.array([-1., 0., 1., 0.], dtype=np.float32))
    output = tmp_path/'result.npz'
    record = fs.build(tmp_path, output, baseline)
    assert record['outside_columns_max_abs_diff'] == 0
    assert [(r['edges'], r['synapses']) for r in record['overrides']] == [(1, 4), (1, 5)]
    with np.load(output, allow_pickle=False) as z:
        assert set(z.files) == {'data', 'indices', 'indptr', 'shape', 'bodies', 'sign', 'types', 'superclass', 'subclass', 'receptor', 'fru', 'nt', 'fsign'}
        assert json.loads(str(z['fsign'])) == record
        actual = sp.csr_matrix((z['data'], z['indices'], z['indptr']), shape=tuple(z['shape'])).toarray()
        np.testing.assert_allclose(actual[3], [1.1, -1.375, 1.65, 0])
    from flysim import FlyBrain
    assert FlyBrain(output).n == 4
    with pytest.raises(FileExistsError):
        fs.build(tmp_path, output, baseline)
    assert fs.build(tmp_path, output, baseline, force=True) == record
    with pytest.raises(ValueError, match='aliases'):
        fs.build(tmp_path, baseline, baseline, force=True)


def test_v12_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ce, 'V12_GRAPH', tmp_path/'missing')
    with pytest.raises(ValueError, match='v12 requires build/graph_male_fsign'):
        ce.main(['--protocol', 'v12', '--quick', '1', '--out', str(tmp_path/'run')], room_factory=FakeRoom)
    with pytest.raises(ValueError, match='ten seeds'):
        ce.main(['--protocol', 'v12', '--seeds', '1'], room_factory=FakeRoom)


def test_v12_predictions():
    assert ce.V12_SCALES == (.9, .8)
    rows = [dict(seed=s, condition=c, male_exc_scale=scale, accept=True,
        **{m: float(s+1) if c == 'song' else 0. for m in ('pip10_hz', 'delivered_rms', 'p1_hz', 'male_total_hz', 'vpodn_hz', 'lc10a_hz', 'mal_hz', 'vab3_hz')})
        for scale in ce.V12_SCALES for s in range(10) for c in ce.V9_CONDITIONS]
    result = ce.summarise_v12(rows[::-1])
    assert result['established'] == {'P33': 'established', 'P34': 'established'}
    p = result['per_scale']['0.9']['P34']
    assert p['paired_differences'] == list(range(1, 11))
    assert p['se'] == pytest.approx(np.std(np.arange(1, 11), ddof=1)/np.sqrt(10))
    for row in rows:
        if row['male_exc_scale'] == .8 and row['condition'] == 'mute':
            row['delivered_rms'] = 100.
    assert ce.summarise_v12(rows)['established']['P33'] == 'not established'


def test_v12_fake_quick(tmp_path, monkeypatch):
    graph = tmp_path/'functional.npz'
    np.savez(graph, fsign=json.dumps({'overrides': list(fs.OVERRIDES)}))
    monkeypatch.setattr(ce, 'V12_GRAPH', graph)
    female = tmp_path/'female.npz'
    np.savez(female, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', female)
    class Room(FakeRoom):
        def step(self):
            result = super().step()
            result['A']['total_hz'] = 17.
            result['A']['rates'].update(mAL=12., vAB3=13.)
            return result
    prefix = tmp_path/'v12'
    assert ce.main(['--protocol', 'v12', '--quick', '1', '--seeds', '1', '--out', str(prefix)], room_factory=Room) == 0
    data = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))
    assert data['steps'] == 80 and len(data['outcomes']) == 6
    assert data['male_graph']['fsign']['overrides'] == list(fs.OVERRIDES)
    assert len(data['male_graph']['sha256']) == 64
    assert all(r['mal_hz'] == 12. and r['vab3_hz'] == 13. and r['male_total_hz'] == 17. for r in data['outcomes'])
    assert all(r['start'] == data['outcomes'][0]['start'] for r in data['outcomes'])
    assert set(data['summary']['established'].values()) == {'not established'}
    assert data['estimated_ten_seed_hours'] == pytest.approx(np.mean([t['step_s'] for t in data['timing']])*24000/3600)
    report = ce.paths(prefix)[3].read_text(encoding='utf-8')
    for marker in ('## Result', 'P33', 'P34', 'P35', '## Override record', '## Per-seed outcomes', 'mal_hz', 'vab3_hz'):
        assert marker in report
    assert ce.main(['--reanalyse', str(ce.paths(prefix)[0])]) == 0


def test_v12_loads_graph_scales_and_records_groups(tmp_path, monkeypatch):
    from test_courtship import MaleFake, female_fake
    from test_backrooms_world import FakeBrain
    graph = tmp_path/'functional.npz'
    np.savez(graph, fsign=json.dumps({'overrides': list(fs.OVERRIDES)}))
    monkeypatch.setattr(ce, 'V12_GRAPH', graph)
    female_path = tmp_path/'female.npz'
    np.savez(female_path, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', female_path)
    male = MaleFake()
    FakeBrain.__init__(male, list(male.types)+['mAL_m1', 'AN09B017e'])
    male.type_names, male.type_code = np.unique(male.types, return_inverse=True)
    male.wdata = np.array([-2., 0., 10.], dtype=np.float32)
    original_run = male.run
    def run(*args, **kwargs):
        return dict(original_run(*args, **kwargs), _total_hz=17.)
    male.run = run
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    def constructor(**kwargs):
        assert kwargs == dict(graph_path=graph)
        return male
    monkeypatch.setattr(ce.bw, 'brain_class', lambda _: constructor)
    def load(**kwargs):
        assert kwargs['path'] == female_path and kwargs['exc_scale'] == .7
        return female
    monkeypatch.setattr(ce, 'load_female', load)
    original = ce.build_room
    calls = []
    def factory(seed, condition, brains, protocol):
        calls.append(condition)
        scale = .9 if len(calls) <= 3 else .8
        np.testing.assert_array_equal(male.wdata, [-2., 0., 10*scale])
        room = original(seed, condition, brains=brains, protocol=protocol, annotations_path='build/missing')
        assert room.bodies['B'].state_group == 'SAG'
        assert len(room.bodies['B'].groups['SAG']) == 4
        return room
    monkeypatch.setattr(ce, 'build_room', factory)
    prefix = tmp_path/'loaded'
    assert ce.main(['--protocol', 'v12', '--quick', '1', '--seeds', '1', '--out', str(prefix)]) == 0
    np.testing.assert_array_equal(male.wdata, [-2., 0., 10.])
    rows = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))['outcomes']
    assert all(r['male_recorded_groups']['mAL'] == r['male_recorded_groups']['vAB3'] == 1 for r in rows)
