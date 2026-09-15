"""Paired controls and report contracts without graph archives."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pytest

import courtship_experiment as ce
import backrooms_world as bw
from test_courtship import make_parts


def test_v10_required_dose_and_graph(tmp_path, monkeypatch):
    args = ['--protocol', 'v10', '--quick', '1', '--out', str(tmp_path/'run')]
    for dose in ([], ['--male-scale', 'nan'], ['--male-scale', '0']):
        with pytest.raises(ValueError, match='requires --male-scale'):
            ce.main(args+dose, room_factory=FakeRoom)
    monkeypatch.setattr(ce, 'V8_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='requires build/graph_female_own_sag'):
        ce.main(args+['--male-scale', '.9'], room_factory=FakeRoom)
    with pytest.raises(ValueError, match='ten seeds and 400 steps'):
        ce.main(['--protocol', 'v10', '--male-scale', '.9', '--seeds', '1',
                 '--out', str(tmp_path/'run')], room_factory=FakeRoom)


@pytest.mark.parametrize('bearing,expected', [(30, (100, 0)), (-30, (0, 100)),
    (0, (100, 100)), (10, (100, 100)), (-10, (100, 100)),
    (120, (0, 0)), (-120, (0, 0)), (180, (0, 0))])
def test_v10_geometry(bearing, expected):
    arena, ch = bw.Arena(seed=1), bw.Channels()
    arena.A.heading = 0.
    arena.B.x = arena.A.x+2*np.cos(np.radians(bearing))
    arena.B.y = arena.A.y+2*np.sin(np.radians(bearing))
    np.testing.assert_allclose(ce.lc10a_geometry(ch, arena.A, arena.B), expected, atol=1e-4)


def test_v10_size_and_replay():
    arena, ch = bw.Arena(seed=1), bw.Channels(min_radius_px=500.)
    arena.A.heading = 0.
    for distance in (1., 2., 4., 8.):
        arena.B.x, arena.B.y = arena.A.x+distance, arena.A.y
        expected = 100*min(np.degrees(2*np.arctan(.5/distance))/ce.SIZE_FULL, 1)
        np.testing.assert_allclose(ce.lc10a_geometry(ch, arena.A, arena.B), [expected]*2)
    trace = dict(lc10a_drive_left_hz=np.arange(20.), lc10a_drive_right_hz=np.arange(20.)**2)
    replay, order = ce.shuffled_drive(trace, 7)
    assert not np.array_equal(order, np.arange(20))
    source = np.column_stack(tuple(trace.values()))
    np.testing.assert_array_equal(replay, source[order])
    np.testing.assert_array_equal(replay.sum(axis=0), source.sum(axis=0))
    np.testing.assert_array_equal(ce.shuffled_drive(trace, 7)[1], order)


def test_neural_lag_is_previous_neural_window():
    _, trace = ce.run_trial(FakeRoom(0, 'song'), 8, 0, 'song')
    np.testing.assert_allclose(trace['a_neural'], trace['pip10_hz']/ce.Singer().pip10_full)
    np.testing.assert_allclose(trace['a'][1:], trace['a_neural'][:-1])
    assert trace['a'][0] == 0 and trace['a_neural'][0] > 0
    lc = np.array([4., 1., 7., 2., 6., 3., 5., 8.])
    singer = ce.Singer(pulse_cells=4, sine_cells=2, pip10_full=100.)
    pip = np.r_[9., lc[:-1]]*10
    mode = np.r_[.9, lc[:-1]/10]
    values = [ce.neural_song(p, m*4, (1-m)*2, singer) for p, m in zip(pip, mode)]
    trace.update(lc10a_hz=lc, lc10a_drive_hz=lc,
                 a_neural=np.array(values)[:, 0], m_neural=np.array(values)[:, 1])
    row = ce.outcome(0, 'song', trace, {})
    for channel in ('a', 'm'):
        assert row[channel+'_neural_lc10a_lagged_rho'] == pytest.approx(1.)
        assert row[channel+'_neural_drive_lagged_rho'] == pytest.approx(1.)
        assert ce.correlation(trace[channel+'_neural'], lc) != pytest.approx(1.)
    assert row['m_lc10a_lagged_rho'] == ce.correlation(trace['m'][1:], lc[:-1])
    assert ce.neural_song(200, 0, 0, singer) == (1., 0.)
    assert ce.neural_song(50, 4, 2, singer) == (.5, .5)


def test_v10_turn_oracle():
    assert ce.heading_reduces_bearing(30, 0, np.radians(10))
    assert not ce.heading_reduces_bearing(30, 0, np.radians(-10))
    assert not ce.heading_reduces_bearing(30, 0, 0)
    assert not ce.heading_reduces_bearing(10, 0, np.radians(30))  # overshoot
    assert ce.heading_reduces_bearing(30, np.radians(175), np.radians(-175))


def test_v10_predictions_missing_pairs_and_channel_rule():
    rows = [dict(seed=s, condition=c, lc10a_hz=10. if c == 'sight' else 0.,
        a_neural_drive_lagged_rho=.8 if c == 'sight' else .1,
        m_neural_drive_lagged_rho=-.5 if c == 'sight' else .5,
        turn_toward_fraction=.7 if c == 'sight' else .2)
        for s in range(10) for c in ce.V10_CONDITIONS]
    summary = ce.summarise_v10(rows[::-1])
    assert summary['P26_channels'] == ['a']
    for label in ('P25', 'P26_a', 'P27'):
        assert summary['predictions'][label]['established']
    assert summary['predictions']['P25']['paired_differences'] == [10.]*10
    rows[0]['a_neural_drive_lagged_rho'] = None
    summary = ce.summarise_v10(rows)
    assert summary['P26_verdict'] == 'not established'
    assert summary['predictions']['P26_a']['n'] == 9
    assert summary['predictions']['P26_a']['excluded_seeds'] == [0]
    for r in rows:
        r['lc10a_hz'] = float(r['seed']) if r['condition'] == 'sight' else 0.
    p = ce.summarise_v10(rows)['predictions']['P25']
    assert p['mean'] == 4.5
    assert p['se'] == pytest.approx(np.std(np.arange(10.), ddof=1)/np.sqrt(10))


def test_v10_fake_brains_quick(tmp_path, monkeypatch):
    from test_courtship import female_fake
    from test_backrooms_world import FakeEye
    import flyeye
    graph = tmp_path/'own.npz'
    np.savez_compressed(graph, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', graph)
    male = make_parts()[0]
    male.wdata = np.array([-2., 0., 10.], dtype=np.float32)
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    monkeypatch.setattr(ce.bw, 'brain_class', lambda name: lambda: male)
    def load(**kwargs):
        assert kwargs['path'] == graph and kwargs['exc_scale'] == .7
        return female
    monkeypatch.setattr(ce, 'load_female', load)
    original = ce.build_room
    seen = []
    annotations = tmp_path/'annotations.feather'
    annotations.touch()
    sides = np.full(male.n, '', dtype=str)
    sides[male.where(type_re='^LC10a$')] = ['L', 'R']
    monkeypatch.setattr(ce.bw, 'soma_sides', lambda *args: sides)
    monkeypatch.setattr(flyeye, 'FlyEye', lambda fb, **kwargs: FakeEye(fb))
    def factory(seed, condition, brains, protocol):
        np.testing.assert_allclose(male.wdata, [-2., 0., 9.])
        assert protocol == 'v10'
        room = original(seed, condition, brains=brains, protocol=protocol, annotations_path=annotations)
        assert room.bodies['B'].state_group == 'SAG'
        assert room.bodies['B'].state == 'virgin'
        assert len(room.bodies['B'].groups['SAG']) == 4
        seen.append(condition)
        return room
    monkeypatch.setattr(ce, 'build_room', factory)
    prefix = tmp_path/'v10'
    assert ce.main(['--protocol', 'v10', '--male-scale', '.9', '--quick', '1', '--out', str(prefix)]) == 0
    np.testing.assert_array_equal(male.wdata, [-2., 0., 10.])
    assert seen == list(ce.V10_CONDITIONS)*2
    data = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))
    assert data['male_exc_scale'] == .9 and data['steps'] == 80
    assert len(data['outcomes']) == 6
    for seed in (0, 1):
        rr = [r for r in data['outcomes'] if r['seed'] == seed]
        assert all(r['start'] == rr[0]['start'] for r in rr)
    with np.load(ce.paths(prefix)[1]) as z:
        for seed in (0, 1):
            get = lambda c, k: z[f's{seed}_{c}_{k}']
            order = get('shuffled', 'lc10a_replay_index').astype(int)
            assert not np.array_equal(order, np.arange(80))
            for side in ('left', 'right'):
                key = f'lc10a_drive_{side}_hz'
                np.testing.assert_array_equal(get('shuffled', key), get('sight', key)[order])
                assert get('shuffled', key).sum() == pytest.approx(get('sight', key).sum())
            for c in ce.V10_CONDITIONS:
                np.testing.assert_allclose(get(c, 'lc10a_hz'), get(c, 'lc10a_drive_hz'))
            assert np.all(get('blind', 'lc10a_drive_hz') == 0)
    report = ce.paths(prefix)[3].read_text(encoding='utf-8')
    for text in ('## Result', 'P25', 'P26_a', 'P26_m', 'P27', 'P28', 'SIZE_FULL', '0.9', 'one-window neural lag'):
        assert text in report
    assert all(p.is_file() for p in ce.paths(prefix))


def test_v10_refuses_unknown_sides():
    from test_courtship import female_fake
    male = make_parts()[0]
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    with pytest.raises(ValueError, match='known left/right soma_side'):
        ce.build_room(0, 'sight', brains=(male, female), protocol='v10', annotations_path='build/missing')


def test_v9_missing_graph(tmp_path, monkeypatch):
    monkeypatch.setattr(ce, 'V8_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='requires build/graph_female_own_sag'):
        ce.main(['--protocol', 'v9', '--quick', '1', '--out', str(tmp_path/'run')], room_factory=FakeRoom)


def test_v9_positive_weights_restored_even_on_failure():
    from types import SimpleNamespace
    fb = SimpleNamespace(wdata=np.array([-3., 0., 10., 20.], dtype=np.float32))
    original = fb.wdata.copy()
    for scale in ce.MALE_EXC_SCALES:
        for _ in ce.V9_CONDITIONS:
            with ce.male_excitation(fb, scale):
                np.testing.assert_allclose(fb.wdata, [-3., 0., 10*scale, 20*scale])
            np.testing.assert_array_equal(fb.wdata, original)
    with pytest.raises(RuntimeError), ce.male_excitation(fb, .7):
        raise RuntimeError('trial failure')
    np.testing.assert_array_equal(fb.wdata, original)


def test_v9_body_controls():
    from test_courtship import female_fake
    for condition in ce.V9_CONDITIONS:
        male = make_parts()[0]
        male.type_names, male.type_code = np.unique(male.types, return_inverse=True)
        female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
        room = ce.build_room(3, condition, brains=(male, female), protocol='v9', annotations_path='build/missing')
        body = room.bodies['B']
        assert body.state_group == 'SAG' and body.state == 'virgin'
        assert len(body.groups['SAG']) == 4
        drive = body.drive(np.zeros((bw.FRAME_H, bw.FRAME_W)), 0., 0.)
        np.testing.assert_array_equal(drive[tuple(body.groups['SAG'])], 50.)
        gains = room.bodies['A'].gains
        if condition == 'mute':
            expected = np.ones(len(male.type_names))
            expected[np.unique(male.type_code[room.bodies['A'].groups['P1']])] = 0
            np.testing.assert_array_equal(gains, expected)
        else:
            assert gains is None
        scent = room.listener_scent({'A': {'female_scent_orn': 80., 'female_scent_contact': 90.}, 'B': 0.})
        assert scent['A']['female_scent_orn'] == (0. if condition == 'noscent' else 80.)
        assert scent['A']['female_scent_contact'] == (0. if condition == 'noscent' else 90.)


def test_v9_fake_quick_and_multiple_scale_rule(tmp_path, monkeypatch, capsys):
    graph = tmp_path/'own.npz'
    np.savez_compressed(graph, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', graph)
    class V9FakeRoom(FakeRoom):
        def step(self):
            result = super().step()
            result['A']['total_hz'] = 17.
            return result
    from types import SimpleNamespace
    male = SimpleNamespace(wdata=np.array([-3., 0., 10.], dtype=np.float32))
    female = object()
    seen = []
    monkeypatch.setattr(ce.bw, 'brain_class', lambda name: lambda: male)
    def load(**options):
        assert options['path'] == graph and options['exc_scale'] == .7
        return female
    def factory(seed, condition, brains, protocol):
        assert protocol == 'v9' and brains == (male, female)
        scale = ce.MALE_EXC_SCALES[len(seen)//6]
        np.testing.assert_allclose(male.wdata, [-3., 0., 10*scale])
        seen.append((scale, seed, condition))
        return V9FakeRoom(seed, condition)
    monkeypatch.setattr(ce, 'load_female', load)
    monkeypatch.setattr(ce, 'build_room', factory)
    prefix = tmp_path/'v9'
    assert ce.main(['--protocol', 'v9', '--quick', '1', '--out', str(prefix)]) == 0
    np.testing.assert_array_equal(male.wdata, [-3., 0., 10.])
    assert len(seen) == 18
    assert all(p.is_file() for p in ce.paths(prefix))
    data = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))
    assert ce.MALE_EXC_SCALES == (.9, .8, .7)
    assert tuple(ce.V9_CONDITIONS) == ('song', 'mute', 'noscent')
    assert len(data['outcomes']) == 18 and data['steps'] == 80
    assert data['female_exc_scale'] == .7
    assert data['estimated_ten_seed_hours'] == pytest.approx(np.mean([t['step_s'] for t in data['timing']])*36000/3600)
    assert '9 cells x 10 seeds x 400 steps' in capsys.readouterr().out
    assert len(data['summary']['cells']) == 9
    assert set(data['summary']['established'].values()) == {'not established'}
    for seed in (0, 1):
        rr = [r for r in data['outcomes'] if r['seed'] == seed]
        assert all(r['start'] == rr[0]['start'] and r['male_total_hz'] == 17. and r['state_group'] == 'SAG' for r in rr)
    with np.load(ce.paths(prefix)[1]) as z:
        assert len([k for k in z if k.endswith('_male_total_hz')]) == 18
    report = ce.paths(prefix)[3].read_text(encoding='utf-8')
    assert ce.V9_PREDICTIONS in report and ce.V9_RULE in report and ce.V9_CALIBRATION in report
    assert '## Result' in report
    rows = [dict(data['outcomes'][0], seed=s, condition=c, male_exc_scale=scale,
                 pip10_hz=10. if c == 'song' else 1., delivered_rms=10. if c == 'song' else 1.,
                 p1_hz=10. if c == 'song' else 1.)
            for scale in ce.MALE_EXC_SCALES for s in range(10) for c in ce.V9_CONDITIONS]
    assert set(ce.summarise_v9(rows)['established'].values()) == {'established'}
    for r in rows:
        if r['male_exc_scale'] == .8 and r['condition'] == 'song':
            r.update(pip10_hz=0., p1_hz=0.)
    summary = ce.summarise_v9(rows[::-1])
    assert set(summary['established'].values()) == {'not established'}
    assert summary['per_scale']['0.8']['P21_command']['reversed']
    assert summary['per_scale']['0.9']['P21_command']['paired_differences'] == [9.]*10
    assert ce.main(['--reanalyse', str(ce.paths(prefix)[0])]) == 0


def test_v8_missing_graph(tmp_path, monkeypatch):
    monkeypatch.setattr(ce, 'V8_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='v8 requires'):
        ce.main(['--protocol', 'v8', '--quick', '1', '--out', str(tmp_path/'run')], room_factory=FakeRoom)


def test_v8_protocol_graph_record_and_verdict_prose(tmp_path, monkeypatch):
    from graft_sag import sha256
    graph, ladder = tmp_path/'own.npz', tmp_path/'ladder.json'
    np.savez_compressed(graph, types=['AN_SMP_2']*2 + ['AN_FLA_SMP_2']*2,
                        restore=[json.dumps(dict(sign_choice='chosen +1', per_type={}))])
    monkeypatch.setattr(ce, 'V8_GRAPH', graph)
    monkeypatch.setattr(ce, 'V8_CALIBRATION', ladder)
    ladder.write_text(json.dumps(dict(graph_sha256=sha256(graph), text='Measured test ladder')), encoding='utf-8')
    out = tmp_path/'v8'
    assert ce.main(['--protocol', 'v8', '--quick', '1', '--out', str(out)], room_factory=FakeRoom) == 0
    data = json.loads(ce.paths(out)[0].read_text(encoding='utf-8'))
    assert data['female_graph']['sha256'] == sha256(graph)
    assert data['state_cells'] == 4
    assert data['state_cells_per_type'] == dict(AN_SMP_2=2, AN_FLA_SMP_2=2, ANXXX983=0)
    assert data['female_exc_scale'] == .7
    spec = data['protocol_spec']
    assert spec['conditions'] == {k: list(v) for k, v in ce.V7_CONDITIONS.items()}
    assert ce.V7_PREDICTIONS in spec['text']
    assert spec['state_pattern'] == ce.V8_STATE_PATTERN
    assert 'Measured test ladder' in spec['text']
    assert data['FEMALE_GRAPH_present'] == ('FEMALE_GRAPH' in os.environ)
    report = ce.paths(out)[3].read_text(encoding='utf-8')
    for label, prediction in data['summary']['predictions'].items():
        assert f"{label} was {prediction['verdict']}:" in report
    assert ce.SAG_AUDIT_CORRECTION in report
    assert ce.main(['--reanalyse', str(ce.paths(out)[0])]) == 0
    ladder.write_text(json.dumps(dict(graph_sha256='wrong', text='bad')), encoding='utf-8')
    with pytest.raises(ValueError, match='SHA256 mismatch'):
        ce.v8_protocol_spec(ce.v8_graph_record())


def test_v8_body_drives_both_types_and_v7_retains_legacy_group():
    from test_courtship import female_fake
    for protocol, count in (('v7', 2), ('v8', 4)):
        female = female_fake(list(female_fake().types) + ['AN_SMP_2']*2 + ['AN_FLA_SMP_2']*2)
        room = ce.build_room(3, 'virgin_song', brains=(make_parts()[0], female),
                             annotations_path='build/missing', protocol=protocol)
        body = room.bodies['B']
        assert len(body.groups['SAG']) == count
        drive = body.drive(np.zeros((bw.FRAME_H, bw.FRAME_W)), 0., 0.)
        assert np.all(drive[tuple(body.groups['SAG'])] == ce.courtship.STATE_HZ)


def test_v7_missing_graph(tmp_path, monkeypatch):
    monkeypatch.setattr(ce, 'V7_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='v7 requires'):
        ce.main(['--protocol', 'v7', '--quick', '1', '--out', str(tmp_path/'run')], room_factory=FakeRoom)


def test_v7_fake_quick_and_predictions(tmp_path, monkeypatch):
    graph = tmp_path/'graft.npz'
    np.savez_compressed(graph, graft=np.array([json.dumps(dict(sources=[], sign_choice='chosen +1'))]))
    monkeypatch.setattr(ce, 'V7_GRAPH', graph)
    out = tmp_path/'v7'
    assert ce.main(['--protocol', 'v7', '--quick', '1', '--out', str(out)], room_factory=FakeRoom) == 0
    data = json.loads(ce.paths(out)[0].read_text())
    assert [(r['seed'], r['condition']) for r in data['outcomes']] == [(s, c) for s in (0, 1) for c in ce.V7_CONDITIONS]
    from graft_sag import sha256
    assert data['female_graph']['sha256'] == sha256(graph)
    assert data['female_exc_scale'] == .7 and ce.FEMALE_EXC_SCALE == 1.
    assert ce.main(['--reanalyse', str(ce.paths(out)[0])]) == 0
    report = ce.paths(out)[3].read_text()
    assert ce.V7_PREDICTIONS in report and ce.V7_CALIBRATION in report
    assert ce.SAG_AUDIT_CORRECTION in report
    assert 'P17 was ' in report and 'P18 was ' in report and 'P19 was ' in report
    for r in data['outcomes']:
        assert r['state_group'] == 'SAG'
        assert r['state_drive_hz'] == (50. if r['condition'].startswith('virgin') else 0.)
        r['vpodn_hz'] = {'virgin_song': 10 + r['seed']*2, 'mated_song': 3, 'virgin_silence': 1, 'mated_silence': 0}[r['condition']]
        r['pc1_hz'] = 20 if r['condition'] == 'virgin_song' else 5
    summary = ce.summarise_v7(data['outcomes'][::-1])
    for label, diffs, mean, se in [('P17', [7, 9], 8, 1), ('P18', [9, 11], 10, 1), ('P19', [15, 15], 15, 0)]:
        p = summary['predictions'][label]
        assert p['paired_differences'] == diffs
        assert p['mean'] == mean and p['se'] == se and p['verdict'] == 'supported'
    assert len(summary['P20']) == 8


def test_v7_real_body_configuration_with_fake_brains():
    from test_courtship import female_fake
    starts = []
    for c in ce.V7_CONDITIONS:
        female = female_fake(list(female_fake().types) + ['AN_SMP_2']*2)
        room = ce.build_room(3, c, brains=(make_parts()[0], female), annotations_path='build/missing')
        starts.append(room.arena.geometry())
        body = room.bodies['B']
        assert body.state_group == 'SAG'
        assert body.state == c.split('_')[0]
        room.previous_rates = dict(pip10_hz=100., pulse_hz=8., sine_hz=0.)
        assert bool(np.any(room.listener_sound(0))) == c.endswith('_song')
    assert all(s == FakeRoom(3, 'song').arena.geometry() for s in starts)


def test_v6_requires_baseline():
    with pytest.raises(ValueError, match="requires --baseline"):
        ce.main(["--protocol", "v6", "--quick", "1", "--out", "build/courtship_v6_quick"], room_factory=FakeRoom)


def test_v6_intervention_inputs():
    from test_courtship import female_fake
    for condition in ("song", "gated", "p1drive", "mated", "mute"):
        male, female = make_parts()[0], female_fake()
        for fb in (male, female):
            fb.type_names, fb.type_code = np.unique(fb.types, return_inverse=True)
        room = ce.build_room(3, condition, brains=(male, female), annotations_path="build/missing")
        female_gains = room.bodies["B"].gains
        if condition == "gated":
            expected = np.where(np.isin(female.type_names, ["pC1a", "pC1b", "pC1c", "pC1d", "pC1e"]), 0., 1.)
            np.testing.assert_array_equal(female_gains, expected)
        else:
            assert female_gains is None
        body = room.bodies["A"]
        for _ in range(2):
            drive = body.drive(np.zeros((bw.FRAME_H, bw.FRAME_W)), 0., 0.)
            key = tuple(body.groups["P1"])
            assert (key in drive) == (condition == "p1drive")
            if condition == "p1drive":
                np.testing.assert_array_equal(drive[key], np.full(len(key), 100.))
        assert room.arena.geometry() == FakeRoom(3, "song").arena.geometry()


def test_v6_fake_quick_and_mismatches(tmp_path):
    base = tmp_path / "baseline"
    assert ce.main(["--quick", "1", "--out", str(base)], room_factory=FakeRoom) == 0
    jp = ce.paths(base)[0]
    baseline = json.loads(jp.read_text(encoding="utf-8"))
    out = tmp_path / "addendum"
    argv = ["--protocol", "v6", "--quick", "1", "--baseline", str(jp), "--out", str(out)]
    assert ce.main(argv, room_factory=FakeRoom) == 0
    data = json.loads(ce.paths(out)[0].read_text(encoding="utf-8"))
    from graft_sag import sha256
    for record in (baseline, data):
        assert record['female_graph']['sha256'] == sha256(record['female_graph']['path'])
        assert record['FEMALE_GRAPH_present'] == ('FEMALE_GRAPH' in os.environ)
    assert [(r["seed"], r["condition"]) for r in data["outcomes"]] == [(s, c) for s in (0, 1) for c in ("gated", "p1drive")]
    import hashlib
    assert data["baseline"]["sha256"] == hashlib.sha256(jp.read_bytes()).hexdigest()
    assert data["baseline"]["date"] == baseline["date"]
    assert ce.main(["--reanalyse", str(ce.paths(out)[0])]) == 0
    report = ce.paths(out)[3].read_text(encoding="utf-8")
    for text in ("P9'", "P10'", "P13", "P14", "P15", "no outgoing synapses", "vision also drives", "every seed gives the same outcome"):
        assert text in report
    for mutation, message in (("seeds", "seeds"), ("start", "start"), ("brain", "brain classes"), ("steps", "steps")):
        changed = json.loads(json.dumps(baseline))
        if mutation == "seeds":
            changed["seeds"] = [0]
        elif mutation == "start":
            changed["outcomes"][0]["start"]["A"]["x"] += 1.
        elif mutation == "brain":
            changed["environment"]["brain_classes"] = {"male": "flysim.FlyBrain", "female": "other.Brain"}
        else:
            changed["steps"] += 1
        jp.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            ce.main(argv, room_factory=FakeRoom)


def test_v6_seed_paired_predictions_and_joint_verdict():
    baseline = [trials(s)["song"][0] for s in (0, 1)]
    rows = []
    for b in baseline:
        b.update(vpodn_hz=10.+b["seed"], pip10_hz=20.+b["seed"], delivered_rms=.1)
        rows += [dict(b, condition="gated", vpodn_hz=b["vpodn_hz"]-3),
                 dict(b, condition="p1drive", vpodn_hz=b["vpodn_hz"]+4, pip10_hz=b["pip10_hz"]+5, delivered_rms=.2)]
    summary = ce.summarise_v6(rows[::-1], baseline[::-1])
    for label, expected in (("P9'", 3), ("P13_command", 5), ("P13_rms", .1), ("P14", 4)):
        assert summary["predictions"][label]["paired_differences"] == pytest.approx([expected, expected])
        assert summary["predictions"][label]["verdict"] == "supported"
    assert summary["P13_verdict"] == "supported"
    for r in rows:
        if r["condition"] == "p1drive":
            r["delivered_rms"] = 0.
    assert ce.summarise_v6(rows, baseline)["P13_verdict"] == "not supported"
    assert len(summary["P10'"]) == len(summary["P15"]) == 4


@pytest.mark.parametrize("seed", [0, 1, 3])
def test_jittered_waveform_energy_and_silent_controls(seed):
    from song import PIP10_FULL, rms
    room = FakeRoom(seed, "song")
    room.previous_rates = dict(pip10_hz=PIP10_FULL, pulse_hz=8., sine_hz=0.)
    waves, records = [], []
    for _ in range(80):
        waves.append(room.listener_sound(0))
        records.append(dict(room.singer.record, distance_mm=room.arena.distance()))
    source = {k: np.array([r[k] for r in records]) for k in records[0]}
    replay = FakeRoom(seed, "jittered", source)
    replay.previous_rates = dict(pip10_hz=0., pulse_hz=0., sine_hz=100.)
    replay.arena = bw.Arena(start=[(1., 1., 0.), (19., 19., 0.)])
    heard = np.concatenate([replay.listener_sound(0) for _ in range(80)])
    assert rms(heard)/rms(np.concatenate(waves)) == pytest.approx(1., rel=.05)
    assert not np.array_equal(heard, np.concatenate(waves))
    for c in ('silence', 'dark'):
        assert np.all(FakeRoom(seed, c).listener_sound(0) == 0)


def test_noscent_removes_both_actual_drives():
    from test_courtship import female_fake
    for condition in ("song", "noscent"):
        room = ce.build_room(0, condition, brains=(make_parts()[0], female_fake()), annotations_path='build/missing')
        room.arena = bw.Arena(start=[(10., 10., 0.), (11., 10., 0.)])
        delivered = room.step()['A']['in']['smell_hz']
        for key in ('female_scent_orn', 'female_scent_contact'):
            assert (delivered[key] > 0) == (condition == 'song')
        assert delivered[bw.SMELL_KEY] == 0


def test_mute_gains_exactly_dictionary_p1():
    from test_courtship import female_fake
    male = make_parts()[0]
    male.types[0] = bd_type = ce.bd._P1_TYPES[0]
    male.type_names, male.type_code = np.unique(male.types, return_inverse=True)
    groups = ce.bd.present_groups(male)
    gains = ce.p1_lesion(male, groups)
    np.testing.assert_array_equal(np.flatnonzero(gains == 0), np.unique(male.type_code[groups['P1']]))
    other = np.setdiff1d(np.arange(len(gains)), np.unique(male.type_code[groups['P1']]))
    assert np.all(gains[other] == 1)
    room = ce.build_room(2, 'mute', brains=(male, female_fake()), annotations_path='build/missing')
    np.testing.assert_array_equal(room.bodies['A'].gains, gains)


def test_p6_lag_direction_and_p1_threshold():
    row, trace = trials()["song"]
    n = len(trace["distance_mm"])
    trace["p1_hz"] = np.array([0., 1., 0., 2.] + [0.] * (n - 4))
    trace["distance_mm"] = np.arange(n, dtype=float)
    trace["her_speed_mm_s"] = -np.arange(n, dtype=float)
    trace["pulse_hz"] = np.r_[999., np.arange(n - 1)]
    trace["sine_hz"] = np.r_[-999., -np.arange(n - 1)]
    result = ce.outcome(0, "song", trace, row["start"])
    assert result["p1_active_windows"] == 2
    assert result["pulse_distance_lagged_rho"] == pytest.approx(1.)
    assert result["pulse_speed_lagged_rho"] == pytest.approx(-1.)
    assert result["sine_distance_lagged_rho"] == pytest.approx(-1.)
    assert result["sine_speed_lagged_rho"] == pytest.approx(1.)


def test_clipped_windows_are_counted_per_channel():
    row, trace = trials()["song"]
    trace["her_sound_a_clipped"] = np.array([0, 1, 0, 1])
    trace["her_sound_b_clipped"] = np.array([1, 1, 1, 0])
    result = ce.outcome(0, "song", trace, row["start"])
    assert result["her_sound_a_clipped"] == 2
    assert result["her_sound_b_clipped"] == 3


@pytest.mark.parametrize("missing", ["pulse_hz", "sine_hz"])
def test_trial_refuses_missing_song_readout(missing):
    room = FakeRoom(0, "song")
    step = room.bodies["A"].step
    def without_group(*args):
        result = step(*args)
        result[missing] = None
        return result
    room.bodies["A"].step = without_group
    with pytest.raises(ValueError, match="requires both male song groups"):
        ce.run_trial(room, 4, 0, "song")


def test_sight_ok_measures_actual_start_not_only_front_probe():
    for x, expected in ((12., True), (8., False)):
        room = FakeRoom(0, "song")
        room.arena = bw.Arena(start=[(10., 10., 0.), (x, 10., 0.)])
        row, _ = ce.run_trial(room, 4, 0, "song")
        assert row["sight_ok"] is expected
        assert any(c["L1_columns_on_fly"] for c in row["sight_check"]["cases"])


def test_annotation_eye_and_sides_recorded(tmp_path):
    import pandas as pd
    from flyeye import FlyEye
    from test_courtship import female_fake
    from test_backrooms_world import fake_sides
    male = make_parts()[0]
    annotations = tmp_path / "body-annotations.feather"
    sides = fake_sides(male)
    pd.DataFrame(dict(bodyId=male.bodies[::-1], somaSide=sides[::-1],
        assignedOlHex1=np.arange(male.n)[::-1],
        assignedOlHex2=(np.arange(male.n) % 3)[::-1])).to_feather(annotations)
    room = ce.build_room(0, "song", brains=(male, female_fake()), annotations_path=annotations)
    assert isinstance(room.bodies["A"].eye, FlyEye)
    assert room.male_setup["sides_restored"] is True
    assert room.male_setup["male_eye"] == "columnar"
    for key in ("fwd_L", "fwd_R", "steer_L", "steer_R"):
        assert len(room.bodies["A"].motor[key]) == 1
    assert room.channels.min_radius == pytest.approx(bw.column_spacing_px(bw.distinct_columns(room.bodies["A"].eye)))
    with patch.object(room, "sight_check", wraps=room.sight_check) as check:
        row, trace = ce.run_trial(room, 4, 0, "song")
    check.assert_called_once_with()
    assert isinstance(row["sight_ok"], bool)
    assert row["male_eye"] == "columnar" and row["sides_restored"]
    assert {"p1_hz", "pulse_hz", "sine_hz", "her_sound_a_hz", "her_sound_b_hz"} <= trace.keys()
    room = ce.build_room(0, "song", brains=(male, female_fake()), annotations_path=tmp_path / "missing")
    assert isinstance(room.bodies["A"].eye, ce.LuminanceEye)
    assert room.male_setup["sides_restored"] is False
    assert room.male_setup["male_eye"] == "luminance"
    assert all(len(room.bodies["A"].motor[k]) == 0 for k in ("fwd_L", "fwd_R", "steer_L", "steer_R"))


@pytest.mark.skipif(os.environ.get("COURTSHIP_REAL_BRAIN") != "1", reason="set COURTSHIP_REAL_BRAIN=1")
def test_real_cpu_gpu_song_exact():
    results = []
    for cls in ("flysim.FlyBrain", "flysim_gpu.FlyBrainGPU"):
        room = ce.build_room(0, "song", brain_class=cls)
        results.append(ce.run_trial(room, 10, 0, "song"))
        del room
    (cpu_row, cpu), (gpu_row, gpu) = results
    differences = []
    for key in cpu:
        if key == "her_brain_s":
            continue  # Wall time is measured separately, not a spike readout.
        indices = np.flatnonzero(cpu[key] != gpu[key])
        if indices.size:
            step = int(indices[0])
            differences.append((step, key, cpu[key][step], gpu[key][step]))
    assert not differences, f"first differing step (zero-based), channel, CPU, GPU: {min(differences) if differences else None}"
    assert cpu_row == gpu_row


def test_build_room_selected_class(monkeypatch, tmp_path):
    from test_courtship import female_fake
    calls = []
    def selected():
        calls.append("male")
        return make_parts()[0]
    def female(**kwargs):
        assert kwargs == dict(exc_scale=ce.FEMALE_EXC_SCALE, brain_class=selected)
        calls.append("female")
        return female_fake()
    monkeypatch.setattr(bw, "SelectedMale", selected, raising=False)
    monkeypatch.setattr(ce, "load_female", female)
    ce.build_room(0, "song", brain_class="backrooms_world.SelectedMale", annotations_path=tmp_path / "missing")
    assert calls == ["male", "female"]


class FakeFly:
    def __init__(self, name, seed, ignores_sound=False):
        self.name, self.seed, self.window = name, seed, 0
        self.state = "virgin"
        self.ignores_sound = ignores_sound

    def step(self, frame, smell, sound):
        self.window += 1
        sound = (float(np.sqrt(np.mean(sound**2)))*200 if isinstance(sound, np.ndarray)
                 else max(ce.HerBody.sound_pair(sound)))
        answer = 0 if self.ignores_sound else sound * (self.window % 3 != 0)
        return dict(turn=0.05 * np.sin(self.window + self.seed), speed=0.02 + self.seed * 0.01,
            pulse_hz=float((self.window * 37 + self.seed * 13) % 101), sine_hz=0.,
            song_hz=float((self.window * 37 + self.seed * 13) % 101) if self.name == "A" else 0.,
            rates={"pIP10": 0. if getattr(self, "muted", False) else 10.+self.window, "LC10a": 3.}, p1_hz=1.,
            her_answer=dict(vpodn_hz=answer, pc1_hz=answer/2, ovidn_hz=0., spsp_hz=50. if self.state == "virgin" else 0.), **{"in": {"sound_hz": sound}})


class FakeRoom(ce.ExperimentRoom):
    def __init__(self, seed, condition, song_sound=None, brains=None, ignores_sound=False):
        self.arena = bw.Arena(seed=seed)
        self.channels = bw.Channels()
        self.song = dict(A=0., B=0.)
        self.bodies = {n: FakeFly(n, seed, ignores_sound) for n in ("A", "B")}
        from test_backrooms_world import FakeEye
        self.bodies["A"].eye = FakeEye(make_parts()[0])
        self.male_setup = dict(male_eye="fake", sides_restored=False)
        self.bodies["A"].muted = condition == "mute"
        self.configure(seed, condition, song_sound)


def trials(seed=0, steps=12, ignores_sound=False):
    result = {}
    sound = None
    for c in ce.CONDITIONS:
        result[c] = ce.run_trial(FakeRoom(seed, c, sound, ignores_sound=ignores_sound), steps, seed, c)
        if c == "song":
            sound = result[c][1]
    return result


def test_v5_geometry_many_seeds():
    headings, offsets = [], []
    for seed in range(100):
        song = FakeRoom(seed, 'song')
        mated = FakeRoom(seed, 'mated')
        assert song.arena.geometry() == mated.arena.geometry()
        a, b = song.arena.A, song.arena.B
        assert song.arena.distance() == pytest.approx(6.)
        offset = np.arctan2(np.sin(np.arctan2(b.y-a.y, b.x-a.x)-a.heading),
                            np.cos(np.arctan2(b.y-a.y, b.x-a.x)-a.heading))
        assert abs(offset) <= np.pi/6
        assert all(2-1e-12 <= v <= 18+1e-12 for v in (a.x, a.y, b.x, b.y))
        headings.append(b.heading)
        offsets.append(offset)
    assert len(set(headings)) == len(set(offsets)) == 100


def test_mated_song_only_state_drive_differs_on_fake():
    from test_courtship import female_fake
    rooms = [ce.build_room(4, c, brains=(make_parts()[0], female_fake()),
                          annotations_path='build/missing') for c in ('song', 'mated')]
    assert rooms[0].arena.geometry() == rooms[1].arena.geometry()
    for _ in range(4):
        results = [room.step() for room in rooms]
        for key in ('A', 'before', 'after', 'song_wave'):
            assert {k: v for k, v in results[0][key].items() if k != 'brain_s'} == {
                k: v for k, v in results[1][key].items() if k != 'brain_s'}
        drives = [room.bodies['B'].drive(np.zeros((800, 1280)), 0., (20., 30.)) for room in rooms]
        spsp = tuple(rooms[0].bodies['B'].groups['SpsP'])
        assert drives[0].keys() == drives[1].keys()
        for key in drives[0]:
            if key == spsp:
                assert np.all(drives[0][key] == 50.) and np.all(drives[1][key] == 0.)
            else:
                np.testing.assert_array_equal(drives[0][key], drives[1][key])
        assert results[0]['B']['her_answer']['spsp_hz'] == 50.
        assert results[1]['B']['her_answer']['spsp_hz'] == 0.


def test_window_sight_and_v5_outcomes():
    room = FakeRoom(0, 'song')
    step = room.step
    def alternating():
        result = step()
        room.arena.A.x, room.arena.A.y, room.arena.A.heading = 10., 10., 0.
        room.arena.B.x, room.arena.B.y = (8. if room.bodies['A'].window % 2 else 12.), 10.
        return result
    room.arena = bw.Arena(start=[(10., 10., 0.), (12., 10., 0.)])
    room.step = alternating
    row, trace = ce.run_trial(room, 4, 0, 'song')
    np.testing.assert_array_equal(trace['sight_ok'], [1, 0, 1, 0])
    assert row['sight_fraction'] == .5
    trace['lc10a_hz'] = np.array([8., 1., 6., 3.])
    trace['m'] = np.array([99., 8., 1., 6.])
    trace['distance_mm'] = np.array([6., 5., 7., 8.])
    row = ce.outcome(0, 'song', trace, row['start'])
    assert row['lc10a_sight_difference'] == 5.
    assert row['m_lc10a_lagged_rho'] == 1.
    assert row['retreat_fraction'] == pytest.approx(2/3)


def test_p9_p11_wiring_and_strict_two_se_rule():
    rows = [r[0] for seed in (0, 1) for r in trials(seed).values()]
    for r in rows:
        r['vpodn_hz'] = 7. if r['condition'] == 'song' else 2.
        r['lc10a_sight_difference'] = 4. if r['condition'] == 'song' else 999.
    summary = ce.summarise(rows)
    assert summary['predictions']['P9']['paired_differences'] == [5., 5.]
    assert summary['predictions']['P9']['control'] == 'mated'
    assert summary['predictions']['P9']['verdict'] == 'supported'
    assert summary['predictions']['P11']['paired_differences'] == [4., 4.]
    assert summary['predictions']['P11']['verdict'] == 'supported'
    assert len(summary['P10']) == 4 and len(summary['P12']) == 12
    assert summary['seed_spread']['mated']['state_sentence'] == 'the state did not produce a no'
    assert ce.verdict(2., 1., 2) == 'not supported'
    assert ce.verdict(2.001, 1., 2) == 'supported'
    assert ce.verdict(-1., 0., 2) == 'not supported'
    rows[0]['lc10a_sight_difference'] = None
    p11 = ce.summarise(rows)['predictions']['P11']
    assert p11['n'] == 1 and p11['excluded_seeds'] == [0]
    assert p11['verdict'] == 'undetermined'
    rows[6]['lc10a_sight_difference'] = None
    assert ce.summarise(rows)['predictions']['P11']['mean'] is None


class Paired(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def temporary_path(self, tmp_path):
        self.tmp_path = tmp_path

    def test_seed_start_and_multiset(self):
        r = trials(3)
        self.assertEqual(set(r), {"song", "jittered", "silence", "mute", "noscent", "mated"})
        for condition in r:
            self.assertEqual(r[condition][0]["seed"], 3)
            self.assertEqual(r[condition][0]["start"], r["song"][0]["start"])
        self.assertEqual(r["song"][0]["start"], r["silence"][0]["start"])
        self.assertEqual(r["song"][0]["start"], r["jittered"][0]["start"])
        self.assertFalse(np.array_equal(r["song"][1]["her_sound_hz"], r["jittered"][1]["her_sound_hz"]))
        self.assertNotEqual(r["song"][0]["start"], trials(4)["song"][0]["start"])

    def test_listener_hook_does_not_touch_his_channel(self):
        r = trials(2, ignores_sound=True)
        self.assertTrue(np.all(r["silence"][1]["her_sound_hz"] == 0))
        self.assertGreater(r["song"][1]["her_sound_hz"].sum(), 0)
        for key in ("his_sound_hz",):
            np.testing.assert_array_equal(r["song"][1][key], r["silence"][1][key])

    def test_hook_changes_actual_body_input(self):
        fb, eye, groups, motor = make_parts()
        from test_courtship import her
        room = ce.ExperimentRoom(fb, eye, groups, motor, body_b=her())
        room.configure(0, "silence")
        room.song["A"] = 1000
        room.song["B"] = 500
        expected = room.channels.sound_hz(500, room.arena.distance())
        r = room.step()
        self.assertEqual(r["B"]["in"]["sound_hz"], (0., 0.))
        self.assertEqual(r["A"]["in"]["sound_hz"], expected)

    def test_dark_eye_and_sound(self):
        from test_courtship import female_fake
        male, _, _, _ = make_parts()
        for eye_setting in ("blind", "luminance"):
            with patch.object(ce, "FEMALE_EYE", eye_setting):
                room = ce.build_room(2, "dark", brains=(male, female_fake()),
                                     annotations_path=self.tmp_path / "missing")
            body = room.bodies["B"]
            self.assertIsInstance(body.eye, ce.BlindEye)
            room.song["A"] = 1000
            r = room.step()
            self.assertEqual(r["B"]["in"]["sound_hz"], (0., 0.))
            drive = body.drive(np.ones((bw.FRAME_H, bw.FRAME_W)), 0, (0., 0.))
            self.assertEqual(set(drive), {tuple(body.sound_idx), tuple(body.groups["SpsP"])})
            np.testing.assert_array_equal(drive[tuple(body.sound_idx)], 0)


class Verdicts(unittest.TestCase):
    def test_threshold(self):
        self.assertEqual(ce.verdict(.5, .2, 2), "supported")
        for mean, se in ((.4, .2), (0, 0), (-1, .1)):
            self.assertEqual(ce.verdict(mean, se, 2), "not supported")
        self.assertEqual(ce.verdict(1, None, 1), "undetermined")

    def test_paired_values_and_direction(self):
        rows = [r[0] for seed in (0, 1) for r in trials(seed).values()]
        s = ce.summarise(rows)
        self.assertEqual(s["predictions"]["P1"]["paired_differences"],
                         [rows[0]["vpodn_hz"]-rows[2]["vpodn_hz"], rows[6]["vpodn_hz"]-rows[8]["vpodn_hz"]])
        self.assertEqual(s["predictions"]["P4"]["paired_differences"][0], rows[2]["last_distance_mm"]-rows[0]["last_distance_mm"])


class Deterministic(unittest.TestCase):
    def test_repeat(self):
        a, b = trials(4), trials(4)
        self.assertEqual(json.dumps([v[0] for v in a.values()], sort_keys=True), json.dumps([v[0] for v in b.values()], sort_keys=True))
        for c in a:
            for k in a[c][1]:
                np.testing.assert_array_equal(a[c][1][k], b[c][1][k])


class RunTrial(unittest.TestCase):
    def test_outcome_boundary_and_constant_correlation(self):
        row, t = trials()["song"]
        t["vpodn_hz"][:] = 0
        t["vpodn_hz"][:2] = 1
        self.assertFalse(ce.outcome(0, "song", t, row["start"])["accept"])
        t["vpodn_hz"][2] = 1
        self.assertTrue(ce.outcome(0, "song", t, row["start"])["accept"])
        self.assertIsNone(ce.correlation([1, 1], [1, 2]))
        self.assertAlmostEqual(ce.correlation([1, 2, 3], [3, 2, 1]), -1)

    def test_missing_replay(self):
        with self.assertRaises(ValueError):
            FakeRoom(0, "unknown")


class MainWithFakes(unittest.TestCase):
    def test_quick_outputs_and_reanalysis(self):
        with tempfile.TemporaryDirectory() as td:
            prefix = Path(td) / "run"
            self.assertEqual(ce.main(["--quick", "1", "--out", str(prefix)], room_factory=FakeRoom), 0)
            for p in ce.paths(prefix):
                self.assertTrue(p.is_file())
                self.assertGreater(p.stat().st_size, 0)
            jp = ce.paths(prefix)[0]
            data = json.loads(jp.read_text())
            self.assertEqual(len(data["outcomes"]), 12)
            self.assertEqual({(r["seed"], r["condition"]) for r in data["outcomes"]}, {(s, c) for s in (0, 1) for c in ce.CONDITIONS})
            self.assertEqual(data["steps"], 80)
            self.assertEqual(data["environment"], dict(brain_class="flysim.FlyBrain",
                torch_devices=dict(male=None, female=None)))
            self.assertEqual(data["budget_ladder"]["selected"], 2)
            self.assertEqual(data["summary"]["P0"]["per_seed"], [dict(seed=s, condition=c, active_windows=0) for s in (0, 1) for c in ("silence", "mute")])
            report = ce.paths(prefix)[3].read_text()
            self.assertIn("## P0: baseline (descriptive, no verdict)", report)
            self.assertIn("brain class flysim.FlyBrain", report)
            self.assertIn("same numbers on either device, verified by test", report)
            self.assertIn("## P7 his response (descriptive)", report)
            self.assertIn("P1 active windows", report)
            self.assertIn("LC10a mean rate per window", report)
            self.assertIn("FEMALE_EXC_SCALE = 1.0; FEMALE_EYE = blind", report)
            self.assertIn("Seed 1, silence: 0 active windows.", report)
            self.assertIn("<!-- interpretation: to be written after the run -->", report)
            self.assertIn("every seed gives the same outcome", report)
            for label in ('P9', 'P10', 'P11', 'P12'):
                self.assertIn('## '+label, report)
            self.assertEqual(ce.main(["--reanalyse", str(jp)]), 0)
            self.assertEqual(json.loads(jp.read_text())["outcomes"], data["outcomes"])


class Cli(unittest.TestCase):
    def test_published_file_identity(self):
        with tempfile.TemporaryDirectory() as td:
            published = Path(td) / "published"
            alias = Path(td) / "alias"
            ce.paths(published)[2].write_bytes(b"protected")
            os.link(ce.paths(published)[2], ce.paths(alias)[0])
            for constant in ("PUBLISHED", "PUBLISHED_ADDENDUM", "PUBLISHED_V7", "PUBLISHED_V8", "PUBLISHED_V9", "PUBLISHED_V10", "PUBLISHED_V11"):
                with self.subTest(constant=constant), patch.object(ce, constant, published):
                    with self.assertRaisesRegex(ValueError, "published prefix is refused"):
                        ce.assert_not_published(alias)
            self.assertEqual(ce.paths(published)[2].read_bytes(), b"protected")

    def test_budget_ladder(self):
        self.assertEqual(ce.budget_ladder(10, 100, 6000)["selected"], 10)
        self.assertEqual(ce.budget_ladder(10, 100, 4000)["selected"], 8)
        self.assertTrue(ce.budget_ladder(10, 100, 100)["budget_exceeded"])
        self.assertEqual(ce.budget_ladder(2, 100, 100)["selected"], 2)

    def test_published_refusal(self):
        self.assertEqual(ce.PUBLISHED, Path("build/courtship"))
        self.assertEqual(ce.PUBLISHED_ADDENDUM, Path("build/courtship_addendum"))
        self.assertEqual(ce.PUBLISHED_V7, Path("build/courtship_v7"))
        self.assertEqual(ce.PUBLISHED_V8, Path("build/courtship_v8"))
        self.assertEqual(ce.PUBLISHED_V9, Path("build/courtship_v9"))
        self.assertEqual(ce.PUBLISHED_V10, Path("build/courtship_v10"))
        self.assertEqual(ce.PUBLISHED_V11, Path("build/courtship_v11"))
        for prefix in ("build/courtship", "build/COURTSHIP", "build/../build/courtship",
                       "build/courtship_addendum", "build/COURTSHIP_ADDENDUM",
                       "build/../build/courtship_addendum"):
            with self.subTest(prefix=prefix):
                self.assertEqual(ce.main(["--out", prefix], room_factory=FakeRoom), 4)

    def test_invalid_steps(self):
        with self.assertRaises(SystemExit):
            ce.main(["--steps", "0"], room_factory=FakeRoom)


class Outputs(unittest.TestCase):
    def test_spread_and_protocol(self):
        rows = [r[0] for seed in (0, 1) for r in trials(seed).values()]
        spread = ce.summarise(rows)["seed_spread"]
        self.assertEqual(spread["silence"]["accept"], 0)
        self.assertEqual(spread["song"]["accept"], 2)
        identical = [dict(r, approach=True, retreat=False) for r in rows]
        self.assertIn("every seed gives the same outcome", ce.summarise(identical)["seed_spread"]["song"]["sentence"])
        self.assertEqual(ce.PROTOCOLS["v5"]["default_seeds"], 10)
        self.assertEqual(ce.PROTOCOLS["v5"]["steps"], 400)


def test_p5_p6_verdict_wiring():
    rows = [r[0] for seed in (0, 1) for r in trials(seed).values()]
    summary = ce.summarise(rows)
    for label, metric in [('P5_command', 'pip10_hz'), ('P5_rms', 'delivered_rms'), ('P6', 'vpodn_hz')]:
        prediction = summary['predictions'][label]
        assert prediction['control'] == 'mute'
        assert prediction['metric'] == metric
        assert prediction['paired_differences'] == [rows[0][metric]-rows[3][metric], rows[6][metric]-rows[9][metric]]
    assert summary['P5_verdict'] == 'supported'
    for row in rows:
        if row['condition'] == 'mute':
            row['delivered_rms'] = 100.
    assert ce.summarise(rows)['P5_verdict'] == 'not supported'


def test_p7_amplitude_mode_lag_direction():
    row, trace = trials()['song']
    n = len(trace['a'])
    trace['distance_mm'] = np.arange(n, dtype=float)
    trace['her_speed_mm_s'] = -np.arange(n, dtype=float)
    trace['a'] = np.r_[99., np.arange(n-1)]
    trace['m'] = np.r_[-99., -np.arange(n-1)]
    trace['lc10a_hz'] = np.arange(n, dtype=float)
    result = ce.outcome(0, 'song', trace, row['start'])
    assert result['a_distance_lagged_rho'] == pytest.approx(1.)
    assert result['a_speed_lagged_rho'] == pytest.approx(-1.)
    assert result['m_distance_lagged_rho'] == pytest.approx(-1.)
    assert result['m_speed_lagged_rho'] == pytest.approx(1.)
    assert result['lc10a_hz'] == pytest.approx((n-1)/2)


def test_p8_presence_and_p8b_descriptive():
    rows = [r[0] for seed in (0, 1) for r in trials(seed).values()]
    for row in rows:
        row['p1_hz'] = 4. if row['condition'] == 'song' else 1.
        row['lc10a_hz'] = 7. if row['condition'] == 'song' else 2.
    predictions = ce.summarise(rows)['predictions']
    assert predictions['P8']['control'] == 'noscent'
    assert predictions['P8']['paired_differences'] == [3., 3.]
    assert predictions['P8']['verdict'] == 'supported'
    assert predictions['P8b']['paired_differences'] == [5., 5.]
    assert predictions['P8b']['verdict'] == 'descriptive; no verdict'


def test_jittered_requires_song_and_replays_source_trace():
    with pytest.raises(ValueError, match='paired song trace first'):
        FakeRoom(0, 'jittered')
    result = trials()
    song, replay = result['song'][1], result['jittered'][1]
    np.testing.assert_allclose(replay['a'], song['a'])
    np.testing.assert_allclose(replay['m'], song['m'])
    np.testing.assert_array_equal(replay['source_distance_mm'], song['distance_mm'])
    assert result['jittered'][0]['delivered_rms'] == pytest.approx(result['song'][0]['delivered_rms'], rel=.05)


def test_previous_measured_command_and_distance_scale():
    room = FakeRoom(0, 'song')
    first = room.step()
    assert first['song_wave']['a'] == 0
    second = room.step()
    assert second['song_wave']['pip10_hz'] == first['A']['rates']['pIP10']
    assert second['song_wave']['a'] == pytest.approx(first['A']['rates']['pIP10']/(1000/2.2))
    from song import Singer, rms
    expected = Singer().render(**room.previous_rates)
    attenuated = Singer().render(**room.previous_rates, attenuation=room.channels.falloff(5))
    assert rms(attenuated) == pytest.approx(rms(expected)*room.channels.falloff(5))


@pytest.mark.parametrize('condition,orn,contact', [
    ('song', False, False), ('noscent_orn', True, False),
    ('noscent_contact', False, True), ('noscent', True, True)])
def test_v11_drives(condition, orn, contact):
    from test_courtship import female_fake
    male = make_parts()[0]
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    room = ce.build_room(3, condition, brains=(male, female), protocol='v11', annotations_path='build/missing')
    source = {'A': {'female_scent_orn': 80., 'female_scent_contact': 90., bw.SMELL_KEY: 0.}, 'B': 0.}
    actual = room.listener_scent(source)
    assert actual == {'A': {'female_scent_orn': 0. if orn else 80.,
        'female_scent_contact': 0. if contact else 90., bw.SMELL_KEY: 0.}, 'B': 0.}
    assert source['A']['female_scent_orn'] == 80. and source['A']['female_scent_contact'] == 90.
    assert ce.v11_drive_flags(condition) == dict(orn_zeroed=orn, contact_zeroed=contact)
    assert room.bodies['A'].gains is None
    assert room.bodies['B'].state_group == 'SAG'
    assert len(room.bodies['B'].groups['SAG']) == 4


def test_v11_required_dose_and_graph(tmp_path, monkeypatch):
    args = ['--protocol', 'v11', '--quick', '1', '--out', str(tmp_path/'run')]
    for dose in ([], ['--male-scale', 'nan'], ['--male-scale', '0']):
        with pytest.raises(ValueError, match='requires --male-scale'):
            ce.main(args+dose, room_factory=FakeRoom)
    monkeypatch.setattr(ce, 'V8_GRAPH', tmp_path/'missing.npz')
    with pytest.raises(ValueError, match='requires build/graph_female_own_sag'):
        ce.main(args+['--male-scale', '.9'], room_factory=FakeRoom)
    with pytest.raises(ValueError, match='ten seeds and 400 steps'):
        ce.main(['--protocol', 'v11', '--male-scale', '.9', '--seeds', '1',
                 '--out', str(tmp_path/'run')], room_factory=FakeRoom)


def test_v11_predictions():
    rows = [dict(seed=s, condition=c, p1_hz=float(s+1) if c!='song' else 0.,
        pip10_hz=10. if c!='song' else 0., delivered_rms=1. if c=='noscent_orn' else 0.)
        for s in range(10) for c in ce.V11_CONDITIONS]
    summary = ce.summarise_v11(rows[::-1])
    assert summary['predictions']['P29']['mean'] == 5.5
    assert summary['predictions']['P29']['se'] == pytest.approx(np.std(np.arange(1., 11.), ddof=1)/np.sqrt(10))
    assert summary['predictions']['P30']['established']
    assert summary['P31_joint'] == dict(orn=True, contact=False)
    assert summary['P32']['noscent_orn']['delivered_rms']['mean'] == -1.
    assert 'verdict' not in summary['P32']['noscent_orn']['delivered_rms']
    rows = [r for r in rows if not (r['seed']==0 and r['condition']=='noscent_orn')]
    summary = ce.summarise_v11(rows)
    assert summary['predictions']['P29']['excluded_seeds'] == [0]
    assert not summary['predictions']['P29']['established']


def test_v11_fake_quick(tmp_path, monkeypatch):
    graph = tmp_path/'own.npz'
    np.savez_compressed(graph, types=['AN_SMP_2']*2+['AN_FLA_SMP_2']*2, restore=json.dumps({}))
    monkeypatch.setattr(ce, 'V8_GRAPH', graph)
    from test_courtship import female_fake
    male = make_parts()[0]
    male.wdata = np.array([-2., 0., 10.], dtype=np.float32)
    female = female_fake(list(female_fake().types)+['AN_SMP_2']*2+['AN_FLA_SMP_2']*2)
    monkeypatch.setattr(ce.bw, 'brain_class', lambda name: lambda: male)
    def load(**kwargs):
        assert kwargs['path'] == graph and kwargs['exc_scale'] == .7
        return female
    monkeypatch.setattr(ce, 'load_female', load)
    original = ce.build_room
    def factory(seed, condition, brains, protocol):
        np.testing.assert_allclose(male.wdata, [-2., 0., 9.])
        assert protocol == 'v11'
        return original(seed, condition, brains=brains, protocol=protocol, annotations_path='build/missing')
    monkeypatch.setattr(ce, 'build_room', factory)
    prefix = tmp_path/'v11'
    assert ce.main(['--protocol', 'v11', '--male-scale', '.9', '--quick', '1',
        '--out', str(prefix)]) == 0
    np.testing.assert_array_equal(male.wdata, [-2., 0., 10.])
    data = json.loads(ce.paths(prefix)[0].read_text(encoding='utf-8'))
    assert data['male_exc_scale'] == .9 and data['steps'] == 80
    assert len(data['outcomes']) == 8
    assert data['environment']['brain_class'] == 'flysim.FlyBrain'
    with np.load(ce.paths(prefix)[1]) as z:
        for r in data['outcomes']:
            assert r['orn_zeroed'] == (r['condition'] in ('noscent_orn', 'noscent'))
            assert r['contact_zeroed'] == (r['condition'] in ('noscent_contact', 'noscent'))
            distance = z[f"s{r['seed']}_{r['condition']}_distance_mm"]
            assert r['contact_fraction'] == np.mean(distance < 2.)
            assert r['distance_mm'] == np.mean(distance)
    for seed in (0, 1):
        starts = [r['start'] for r in data['outcomes'] if r['seed']==seed]
        assert all(s==starts[0] for s in starts)
    assert not any(p['established'] for p in data['summary']['predictions'].values())
    report = ce.paths(prefix)[3].read_text(encoding='utf-8')
    for text in ('## Result', 'P29', 'P30', 'P31_orn', 'P31_contact', 'P32', 'orn_zeroed', 'contact_zeroed', 'contact_fraction'):
        assert text in report
    assert data['estimated_ten_seed_hours'] == pytest.approx(np.mean([t['seconds']/80 for t in data['timing']])*16000/3600)
