"""A chosen nose response, with the earlier protocols held to their main records."""
import hashlib
import json
import os
from pathlib import Path
import types
from unittest.mock import patch

import numpy as np
import pytest

import plume_experiment as pe
import plume_fly as pf
from test_plume_fly import FakeBrain, fake_motor, fake_root_side
from test_plume_experiment import FakeWorld


class Nose:
    def __init__(self, hz):
        self.hz = hz
        self.orn = {"DM1": np.array([0, 1])}
        self.door = types.SimpleNamespace(key_of={"ethyl acetate": "ea"}, profile=lambda key: {"DM1": 0.8})

    def drive(self, odour):
        return {(0, 1): odour["profile"]["DM1"] * self.hz}


def fly_factory(module=pf):
    class Fly(module.PlumeFly):
        def __init__(self, fb, gains=None, protocol="v1", smooth_tau_s=0.0, **kw):
            super().__init__(fb, gains, protocol=protocol, smooth_tau_s=smooth_tau_s,
                             nose=Nose(kw.get("odour_hz", 200.0)), motor=fake_motor(fb),
                             root_side=fake_root_side(fb), **kw)
    return Fly


def make_fly(protocol):
    fb = FakeBrain(["DM1"])
    return fb, fly_factory()(fb, protocol=protocol)


@pytest.mark.parametrize("protocol", ["v1", "v2", "v3"])
def test_step_formula_onset_plateau_offset_and_clipping(protocol):
    fb, fly = make_fly(protocol)
    fly.begin_trial(123)
    adaptation = 0.0
    trace = [-1.0, 0.0] + [0.5] * 100 + [0.0, 0.0, 2.0]
    for k, concentration in enumerate(trace):
        level = min(1.0, max(0.0, concentration))
        adaptation = 0.9 * adaptation + 0.1 * level
        response = min(1.0, 0.3 * level + max(0.0, level - adaptation)) if protocol == "v3" else level
        _, _, info = fly.step(concentration, 0.2, seed=k)
        assert fb.calls[-1]["drive"][(0, 1)] == pytest.approx(0.8 * response * 200.0)
        if protocol == "v3":
            assert info["orn_adapt"] == pytest.approx(adaptation)
            assert info["orn_drive_hz"] == pytest.approx(160.0 * response)
        else:
            assert "orn_adapt" not in info


def test_discrete_tau_carry_and_trial_reset():
    fb, fly = make_fly("v3")
    fly.begin_trial(12)
    observed = []
    for n in range(1, 101):
        _, _, info = fly.step(0.5, 0.0, seed=n)
        expected_a = 0.5 * (1.0 - 0.9 ** n)
        assert info["orn_adapt"] == pytest.approx(expected_a)
        assert info["orn_drive_hz"] == pytest.approx(160 * (0.15 + 0.5 * 0.9 ** n))
        observed.append(info["orn_drive_hz"])
    assert observed[0] == pytest.approx(96.0)
    assert observed[9] == pytest.approx(24 + 80 * 0.9 ** 10)
    assert observed[-1] == pytest.approx(24, abs=0.003)
    assert np.all(np.diff(observed) < 0)
    assert fb.calls[-1]["state"]["v"][0] == 99
    assert fly.step(0, 0)[2]["orn_drive_hz"] == 0
    fly.begin_trial(13)
    assert fly.orn_adapt == 0
    assert fly.step(0.5, 0)[2]["orn_drive_hz"] == pytest.approx(observed[0])
    assert fb.calls[-1]["state"] is None
    assert fb.calls[-1]["seed"] == 13
    assert fly.describe()["orn_adaptation"]["tau_s"] == 0.5
    assert fly.protocol == "v3"


def test_real_nose_profile_and_unchanged_wind_on_synthetic_trace():
    from test_plume_fly import make_fly as door_fly, orn_rates
    fb2, v2 = door_fly(protocol="v2")
    fb3, v3 = door_fly(protocol="v3")
    a = 0.0
    for c in [0.0] + [0.5] * 20 + [0.0]:
        a += (c - a) * 0.1
        response = min(1.0, 0.3 * c + max(0.0, c - a))
        drive2, drive3 = v2.drives(c, 0.8), v3.drives(c, 0.8)
        for fly, brain, drive, level in ((v2, fb2, drive2, c), (v3, fb3, drive3, response)):
            actual = orn_rates(brain, drive)
            for glomerulus, profile in fly.profile.items():
                for neuron in fly.nose.orn[glomerulus]:
                    assert actual[neuron] == pytest.approx(profile * level * fly.odour_hz)
        assert v2.wind_drive(0.8) == v3.wind_drive(0.8)


def cli_record(runner, coupling, protocol, prefix, graph="male"):
    class Brain(FakeBrain):
        def run(self, *args, **kwargs):
            result = super().run(*args, **kwargs)
            window = result["_state"]["v"][0]
            for name, rate in {"steer_L": 20, "steer_R": 30, "fwd_L": 120,
                               "fwd_R": 180, "back": 5, "stop": 10}.items():
                result[name] = result[name] + rate + window
            return result
    fake_brain = types.SimpleNamespace(FlyBrain=lambda: Brain(["DM1"]))
    fake_cal = types.SimpleNamespace(CHOSEN="fixed_fake", gains_for=lambda fb, setting: None)
    class World(FakeWorld):
        def __init__(self, seed, odour=True, protocol="v1"):
            super().__init__(seed, odour, protocol=protocol,
                             field=lambda x, y, t: 0.5 if 0.6 <= t < 3.0 else 0.0)
    fake_world = types.SimpleNamespace(World=World, start_rule_v2_check=lambda n: {"n_seeds": n,
                                      "n_start_above_threshold": 9, "seeds_above_threshold": [0, 16]})
    fake_fly = types.SimpleNamespace(PlumeFly=fly_factory(coupling))
    for name in dir(coupling):
        if name.isupper():
            setattr(fake_fly, name, getattr(coupling, name))
    modules = {"flysim": fake_brain, "calibration": fake_cal, "plume": fake_world, "plume_fly": fake_fly}
    args = ["--protocol", protocol, "--quick", "1"]
    if prefix is not None:
        args += ["--out", str(prefix)]
    with patch.dict("sys.modules", modules), patch.object(runner, "free_ram_gb", return_value=100.0), \
            patch.object(runner, "V1_JSON", pe.BUILD / "plume_v3_absent_baseline.json"), \
            patch.dict(os.environ, {"FLY_GRAPH": "build/graph_" + graph + ".npz"}):
        assert runner.main(args) == 0
    if prefix is None:
        output = pe.BUILD / ("plume_v3_" + graph + "_quick")
    else:
        output = runner.out_prefix_from(str(prefix), quick=True)
    payload = json.loads(output.with_name(output.name + "_experiment.json").read_text(encoding="utf-8"))
    with np.load(output.with_name(output.name + "_trajectories.npz")) as saved:
        arrays = {k: saved[k].tolist() for k in saved.files}
    return payload, arrays, output


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items()
                if k not in {"started", "finished", "elapsed_s", "sec_per_step", "sec_per_brain_run", "source_json"}}
    if isinstance(value, list):
        return [stable(v) for v in value]
    if isinstance(value, str):
        return value.replace(str(pe.ROOT), "<ROOT>").replace("\\", "/")
    return value


def digest(value):
    return hashlib.sha256(json.dumps(stable(value), sort_keys=True, allow_nan=True).encode()).hexdigest()


# Captured by build/plume_v3_capture.py from the pinned main sources, with no brain loaded.
BASELINE = {'v1': '64bafb20c76b691599dbb63484356357258c3792791496f055463023e14b043b', 'v2': '38f6c9a6488ae32b7b1adfd7330ec2a25cb999142f5094206d1127b9b04f9a85'}


@pytest.mark.parametrize("protocol", ["v1", "v2"])
def test_legacy_cli_matches_captured_main(protocol):
    payload, arrays, _ = cli_record(pe, pf, protocol, pe.BUILD / ("plume_v3_regression_" + protocol))
    assert digest([payload, arrays]) == BASELINE[protocol]


@pytest.mark.parametrize("graph", ["female", "male"])
def test_v3_cli_records_and_round_trip(graph):
    prefix = pe.BUILD / ("plume_v3_fake_" + graph)
    payload, arrays, output = cli_record(pe, pf, "v3", prefix, graph)
    assert payload["protocol"] == "v3"
    assert payload["run"]["design_seeds"] == 10
    assert payload["run"]["design_budget_s"] == 9000
    assert payload["constants"]["fly_instance"]["protocol"] == "v3"
    assert payload["run"]["smooth_tau_s"] == 0.15
    assert payload["constants"]["world_start_rule_v2"]["n_start_above_threshold"] == 9
    assert [c["letter"] for c in payload["protocol_changes"]] == ["I"]
    assert [c["letter"] for c in payload["inherited_protocol_changes"]] == list("ABCDEFGH")
    assert not any("no receptor adaptation" in s for s in payload["simulator_limits"] + payload["design_limits"])
    assert arrays["condition"] == ["odour", "odour", "blank", "blank", "shuffled", "shuffled"]
    assert all(row[0] == 0.25 for row in arrays["x"])
    trials = pe.load_trials(output.with_name(output.name + "_trajectories.npz"),
                            output.with_name(output.name + "_experiment.json"))
    for condition, rows in trials.items():
        for trial in rows:
            a = 0.0
            for k, c in enumerate(trial["c"][:-1]):
                a = 0.9 * a + 0.1 * np.clip(c, 0, 1)
                assert trial["rates"]["orn_adapt"][k] == pytest.approx(a)
            if condition == "blank":
                assert np.all(trial["rates"]["orn_drive_hz"] == 0)
    before = pe.summarise(trials, protocol="v3")
    inherited = pe.summarise(trials, protocol="v2")
    assert pe._clean(before["predictions"]) == pe._clean(inherited["predictions"])
    assert pe.compare_preregistered(before["predictions"], inherited["predictions"], protocol="v3")[0]
    _, _, npz, _ = pe.write_outputs(trials, payload["run"], output, protocol="v3")
    with np.load(npz) as saved:
        np.testing.assert_equal(saved["orn_adapt"], arrays["orn_adapt"])


def test_v3_namespace_and_alias_guard():
    for bad in (pe.BUILD / "plume", pe.BUILD / "plume_v2_quick", pe.BUILD.parent / "plume_v3_wrong"):
        with pytest.raises(ValueError):
            pe.assert_v3_output(bad)
    pe.assert_v3_output(pe.BUILD / "plume_v3_female_quick")
    original = pe.BUILD / "plume_guard_owned_probe.json"
    alias = pe.BUILD / "plume_v3_guard_alias_experiment.json"
    original.write_text("owned probe", encoding="utf-8")
    if not alias.exists():
        os.link(original, alias)
    with pytest.raises(ValueError, match="aliases"):
        pe.assert_v3_output(pe.BUILD / "plume_v3_guard_alias")


def test_v3_refuses_legacy_interfaces():
    with pytest.raises(TypeError):
        pe.make_world(types.SimpleNamespace(World=lambda seed, odour: None), 0, True, "v3")
    with pytest.raises(TypeError):
        pe.make_fly(types.SimpleNamespace(PlumeFly=lambda fb, gains: None), None, None, "v3")


@pytest.mark.parametrize("graph", ["female", "male"])
def test_v3_default_graph_prefix_before_any_output(graph):
    class BeforeLog(Exception):
        pass
    def capture(path):
        assert Path(path).name == "plume_v3_" + graph + "_quick_experiment.log"
        raise BeforeLog
    with patch.dict(os.environ, {"FLY_GRAPH": "build/graph_" + graph + ".npz"}), \
            patch.object(pe, "Log", side_effect=capture), pytest.raises(BeforeLog):
        pe.main(["--protocol", "v3", "--quick", "1"])


def test_production_diff_only_adds_lines():
    import subprocess
    diff = subprocess.check_output(["git", "diff", "88b5f0b", "--", "plume_experiment.py", "plume_fly.py"], text=True)
    assert not [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    unchanged = subprocess.check_output(["git", "diff", "88b5f0b", "--", "plume.py", "olfaction.py",
                                         "calibration.py", "plume_graph.py"], text=True)
    assert unchanged == ""
