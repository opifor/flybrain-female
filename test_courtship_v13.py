"""CPU-only v13 contracts, with synthetic columns and fake brains."""
import json
import numpy as np
import pytest
import courtship_experiment as ce
from test_courtship import make_parts, female_fake


class ColumnEye:
    on_idx = np.array([0, 1, 2])
    off_idx = np.array([3, 4, 5])
    on_uv = (np.array([0., .5, 1.]), np.zeros(3))

    def look(self, img, cx, cy):
        return {tuple(self.on_idx): img[0]*180., tuple(self.off_idx): (1-img[0])*108.}


def test_contrast_columns():
    eye = ce.ContrastEye(ColumnEye())
    rates = eye.look(np.array([[.5, 0., 1.]]), 0, 0)
    np.testing.assert_allclose(rates[(0, 1, 2)], [0, 0, 180])
    np.testing.assert_allclose(rates[(3, 4, 5)], [0, 108, 0])
    rates = eye.look(np.array([[.25, .5, .75]]), 0, 0)
    np.testing.assert_allclose(rates[(0, 1, 2)], [0, 0, 90])
    np.testing.assert_allclose(rates[(3, 4, 5)], [54, 0, 0])
    assert ce.bw.distinct_columns(eye) == 3
    eye.blind = True
    assert all(np.count_nonzero(v) == 0 for v in eye.look(np.zeros((1, 3)), 0, 0).values())
    for ground in (0, 1):
        with pytest.raises(ValueError):
            ce.ContrastEye(ColumnEye(), ground)


def test_circular_shift_lag():
    lc = np.array([4., 1., 7., 2., 6., 3., 5., 8.])
    trace = dict(lc10a_hz=lc, a_neural=np.r_[9., lc[:-1]],
                 m_neural=np.r_[-9., -lc[:-1]], sight_ok=np.zeros(8), male_total_hz=lc)
    result = ce.v13_correlations(trace)
    assert result['a_neural_lc10a_lagged_rho'] == pytest.approx(1.)
    assert result['m_neural_lc10a_lagged_rho'] == pytest.approx(-1.)
    # Independent explicit half-trial rotation, followed by the lag.
    shifted = np.r_[lc[4:], lc[:4]]
    expected = ce.correlation(trace['a_neural'][1:], shifted[:-1])
    assert expected != pytest.approx(1.)
    assert result['a_neural_lc10a_shifted_rho'] == expected
    assert result['male_total_sight_hz'] is None
    assert result['male_total_no_sight_hz'] == 4.5
    trace['lc10a_hz'][:] = 0
    assert ce.v13_correlations(trace)['a_neural_lc10a_shifted_rho'] is None


def test_predictions():
    rows = [dict(seed=s, condition=c, lc10a_hz=10. if c=='song' else 0.,
        pip10_hz=5. if c=='song' else 0., delivered_rms=2. if c=='song' else 0.,
        p1_hz=3. if c=='song' else 0., a_neural_lc10a_lagged_rho=.8,
        a_neural_lc10a_shifted_rho=.1, m_neural_lc10a_lagged_rho=-.8,
        m_neural_lc10a_shifted_rho=.1) for s in range(10) for c in ce.V13_CONDITIONS]
    summary = ce.summarise_v13(rows[::-1])
    assert summary['P37_joint'] and summary['P39_channels'] == ['a']
    assert all(summary['predictions'][k]['established'] for k in ('P36', 'P37_command', 'P37_rms', 'P38', 'P39_a'))
    assert summary['predictions']['P36']['paired_differences'] == [10.]*10
    for r in rows:
        if r['condition']=='song':
            r['lc10a_hz'] = r['seed']
            r['delivered_rms'] = -1.
    p = ce.summarise_v13(rows)
    assert not p['P37_joint']
    assert p['predictions']['P36']['se'] == pytest.approx(np.std(np.arange(10), ddof=1)/np.sqrt(10))
    rows[0]['a_neural_lc10a_lagged_rho'] = None
    p = ce.summarise_v13(rows)
    assert not p['P39_channels']
    assert p['predictions']['P39_a']['excluded_seeds'] == [0]
    assert not ce.summarise_v13(rows[:4])['predictions']['P36']['established']


def test_required_dose_and_female(tmp_path, monkeypatch):
    args = ['--protocol', 'v13', '--quick', '1', '--out', str(tmp_path/'run')]
    for dose in ([], ['--male-scale', 'nan'], ['--male-scale', '0']):
        with pytest.raises(ValueError, match='requires --male-scale'):
            ce.main(args+dose)
    monkeypatch.setattr(ce, 'V8_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='requires build/graph_female_own_sag'):
        ce.main(args+['--male-scale', '.9'])
    with pytest.raises(ValueError, match='ten seeds and 400 steps'):
        ce.main(['--protocol', 'v13', '--male-scale', '.9', '--seeds', '1', '--out', str(tmp_path/'run')])


def test_fake_quick(tmp_path, monkeypatch):
    graph = tmp_path/'own.npz'
    np.savez_compressed(graph, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', graph)
    male = make_parts()[0]
    male.type_names, male.type_code = np.unique(male.types, return_inverse=True)
    male.wdata = np.array([-2., 0., 10.], dtype=np.float32)
    original_run = male.run
    def run(*args, **kwargs):
        result = original_run(*args, **kwargs)
        result['_total_hz'] = 12.
        return result
    male.run = run
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    import graft_sag
    monkeypatch.setattr(graft_sag, 'sha256', lambda path: 'fake-graph-hash')
    def male_class(graph_path):
        assert graph_path == 'build/graph.npz'
        return male
    monkeypatch.setattr(ce.bw, 'brain_class', lambda name: male_class)
    def load(**kwargs):
        assert kwargs['path'] == graph and kwargs['exc_scale'] == .7
        return female
    monkeypatch.setattr(ce, 'load_female', load)
    original = ce.build_room
    seen = []
    def factory(seed, condition, brains, protocol):
        np.testing.assert_allclose(male.wdata, [-2., 0., 9.])
        room = original(seed, condition, brains=brains, protocol=protocol, annotations_path='build/missing')
        assert protocol == 'v13' and isinstance(room.bodies['A'].eye, ce.ContrastEye)
        assert room.bodies['B'].state_group == 'SAG' and len(room.bodies['B'].groups['SAG']) == 4
        assert room.bodies['B'].state == 'virgin'
        source = {'A': {'female_scent_orn': 80., 'female_scent_contact': 90., ce.bw.SMELL_KEY: 7.}, 'B': 3.}
        actual = room.listener_scent(source)
        assert actual['A'] == dict(source['A'], female_scent_orn=0. if condition=='noscent_orn' else 80.)
        assert actual['B'] == 3. and source['A']['female_scent_orn'] == 80.
        eye = room.bodies['A'].eye
        drives = eye.look(np.zeros((300, 400), dtype=np.float32), 200, 150)
        assert all(np.count_nonzero(v)==0 for v in drives.values()) == (condition=='blind')
        assert (room.bodies['A'].gains is not None) == (condition=='mute')
        if condition == 'mute':
            gains = room.bodies['A'].gains
            assert np.all(gains[male.type_code[room.bodies['A'].groups['P1']]] == 0)
        assert not hasattr(room, 'lc10a_current')
        seen.append(condition)
        return room
    monkeypatch.setattr(ce, 'build_room', factory)
    prefix = tmp_path/'v13'
    assert ce.main(['--protocol', 'v13', '--male-scale', '.9', '--quick', '1', '--seeds', '1', '--out', str(prefix)]) == 0
    assert seen == list(ce.V13_CONDITIONS)
    np.testing.assert_array_equal(male.wdata, [-2., 0., 10.])
    data = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))
    assert data['MALE_EYE'] == data['protocol_spec']['MALE_EYE'] == 'contrast'
    assert data['male_graph']['path'] == 'build/graph.npz'
    assert data['male_exc_scale'] == .9 and data['steps'] == 80
    assert len(data['outcomes']) == 4
    assert all(r['start']==data['outcomes'][0]['start'] for r in data['outcomes'])
    assert not any(p['established'] for p in data['summary']['predictions'].values())
    with np.load(ce.paths(prefix)[1]) as z:
        for r in data['outcomes']:
            assert r['orn_zeroed'] == (r['condition']=='noscent_orn') and not r['contact_zeroed']
            distance = z[f"s0_{r['condition']}_distance_mm"]
            assert r['contact_fraction'] == np.mean(distance < 2.)
    report = ce.paths(prefix)[3].read_text(encoding='utf-8')
    for text in ('## Result', 'P36', 'P37', 'P38', 'P39_a', 'P39_m', 'P40', '45-60', '209 of 275', 'clip(lum-ground'):
        assert text in report
    assert all(p.is_file() for p in ce.paths(prefix))
    assert data['estimated_ten_seed_hours'] == pytest.approx(np.mean([t['seconds']/80 for t in data['timing']])*16000/3600)
