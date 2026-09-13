"""The betting door leaves pin mode and the disabled random stream intact."""
import ast
import json
import random
from pathlib import Path
from unittest.mock import patch

import pytest
import roam


def test_disabled_room_preserves_random_stream():
    with patch.object(roam, "load_env", return_value={}), patch.object(roam, "PIN", ""):
        rng, expected = random.Random(17), random.Random(17)
        assert [roam.next_place(rng)[0] for _ in range(30)] == [expected.choice(roam.SEEDS) for _ in range(30)]
        assert roam.load_room() is None


def test_pin_takes_precedence():
    with patch.object(roam, "load_env", return_value={"FLY_BETROOM_SHARE": "1"}), \
            patch.object(roam, "PIN", "https://example.com/chart"), \
            patch.object(roam, "SEEDS", ["https://example.com/chart"]):
        assert roam.next_place(random.Random(4))[0] == "https://example.com/chart"
        assert roam.allowed_host("https://example.com/chart")
        assert not roam.allowed_host(roam.betroom_url())
        assert roam.load_room() is None


@pytest.mark.parametrize("suffix", ["/public.json", "?x=1", "#x", "er"])
def test_only_the_room_page_is_a_destination(suffix):
    with patch.object(roam, "load_env", return_value={"FLY_BETROOM_SHARE": "1"}), \
            patch.object(roam, "PIN", ""), patch.object(roam, "OPEN", True):
        assert roam.allowed_host(roam.betroom_url())
        assert not roam.allowed_host(roam.betroom_url() + suffix)
        for url in ("http://127.0.0.2:4672/health", "http://10.0.0.1/", "http://localhost:4672/"):
            assert not roam.allowed_host(url)


def test_missing_room_is_not_a_destination():
    with patch.object(roam, "load_env", return_value={"FLY_BETROOM_SHARE": "1"}), patch.object(roam, "PIN", ""):
        assert roam.next_place(random.Random(3))[0] == roam.betroom_url()
        assert roam.next_place(random.Random(3), False)[0] in roam.SEEDS


def test_page_and_public_file(tmp_path):
    path = tmp_path / "betroom" / "public" / "public.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"mode": "paper", "balance": 90.59}))
    with patch.object(roam, "load_env", return_value={"FLY_STATE_DIR": str(tmp_path)}):
        assert roam.betroom_state() == {"mode": "paper", "balance": 90.59}
    assert Path(roam.betroom_page().path).name == "betroom.html"


def test_room_guards_the_browser_click_and_observation():
    tree = ast.parse(Path(roam.__file__).read_text(encoding="utf-8"))
    parent = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    checked = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if name not in ("page.mouse.click", "mb.observe", "room.step"):
            continue
        checked.add(name)
        guards, current = [], node
        while current in parent:
            up = parent[current]
            if isinstance(up, ast.If) and current in up.body:
                guards.append(ast.unparse(up.test))
            current = up
        assert any(("not in_room" if name != "room.step" else "in_room") in g for g in guards)
    assert checked == {"page.mouse.click", "mb.observe", "room.step"}


def test_live_room_flag_stops_even_in_pin_mode():
    with patch.object(roam, "load_env", return_value={"FLY_BETROOM_LIVE": "1"}):
        with pytest.raises(SystemExit):
            roam.load_room()
