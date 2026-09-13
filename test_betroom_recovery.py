"""A late answer or a restart must not teach the wrong card twice."""
import asyncio
import json

import pytest

from betroom import Room
from test_betroom import FakeBrain, FakeMB, FakeNose, FakePilot, FakeHttp, FakePage, IMG


def make_room(tmp_path):
    fb = FakeBrain()
    return Room(fb, FakePilot(), FakeMB(fb), FakeNose(), None, tmp_path,
                "http://127.0.0.1:4672", "secret", fetch_board=lambda: [],
                http=FakeHttp(), spawn=lambda *args: None)


def settled_look(room):
    room.looks_dir.mkdir(parents=True, exist_ok=True)
    look = {"token": "111", "eligible": [1, 3], "brain_id": room.brain_id}
    path = room.looks_dir / "look.json"
    path.write_text(json.dumps(look))
    return {"kind": "settled", "seq": 3, "market_id": "111", "look_id": "look",
            "side": "YES", "outcome": "YES"}, path


def test_restart_does_not_repeat_dopamine(tmp_path):
    room = make_room(tmp_path)
    ev, _ = settled_look(room)
    room._teach(ev)
    again = make_room(tmp_path)
    again._teach(ev)
    assert not again.mb.log
    assert again.last_seq == 3


def test_failed_save_is_recorded_as_pending_and_not_retried(tmp_path):
    room = make_room(tmp_path)
    ev, _ = settled_look(room)
    room.mb.save = lambda: False
    with pytest.raises(OSError, match="could not save"):
        room._teach(ev)
    records = [json.loads(line) for line in room.dopamine_file.read_text().splitlines()]
    assert [r["status"] for r in records] == ["pending"]
    assert room.mb.log[-1][0] == "forget_trace"
    before = len(room.mb.log)
    room._teach(ev)
    assert len(room.mb.log) == before


@pytest.mark.parametrize("missing", ["look", "identity", "cells"])
def test_missing_or_different_brain_does_not_learn(tmp_path, missing):
    room = make_room(tmp_path)
    ev, path = settled_look(room)
    if missing == "look":
        path.unlink()
    else:
        look = json.loads(path.read_text())
        look["brain_id" if missing == "identity" else "eligible"] = "different" if missing == "identity" else []
        path.write_text(json.dumps(look))
    room._teach(ev)
    assert not room.mb.log
    assert json.loads(room.dopamine_file.read_text())["status"] == "missing eligibility"


def test_pruning_keeps_uncertain_intents(tmp_path):
    room = make_room(tmp_path)
    room.looks_dir.mkdir(parents=True)
    room.max_looks = 1
    for name in ("a", "b", "c"):
        (room.looks_dir / (name + ".json")).write_text("{}")
        (room.looks_dir / (name + ".png")).write_bytes(b"picture")
    room.refs = {"111": ["a"]}
    room._prune_looks()
    assert (room.looks_dir / "a.json").exists()
    assert (room.looks_dir / "a.png").exists()
    assert len(list(room.looks_dir.glob("*.json"))) == 1


def test_late_server_failure_keeps_look_pinned(tmp_path):
    room = make_room(tmp_path)
    room.refs = {"111": ["look"]}
    room._intent = {"done": True, "at": 1, "symbol": "111",
                    "body": {"market_id": "111", "look_id": "look", "side": "YES", "drive": 0.5},
                    "result": {"status": "error", "http": 500}}
    room._collect_intent()
    assert room.refs == {"111": ["look"]}


def test_dwell_records_only_the_cells_from_that_card(tmp_path):
    room = make_room(tmp_path)
    room.meta = {t: {"question": t, "token_ids": [t + "1", t + "2"]} for t in ("111", "222")}
    page = FakePage()
    asyncio.run(room.step(page, IMG, 400, 100, 1))
    asyncio.run(room.step(page, IMG, 100, 100, 2))
    room.pilot.click = True
    asyncio.run(room.step(page, IMG, 100, 100, 3))
    look = json.loads(next(room.looks_dir.glob("*.json")).read_text())
    assert look["eligible"] == [1, 3]
    assert look["dwell_steps"] == 2
    assert look["brain_id"] == room.brain_id


def test_refresh_waits_sixty_seconds_and_keeps_last_good_board(tmp_path):
    room = make_room(tmp_path)
    room._board = {"cards": [{"market_id": "111"}], "updated": 100}
    room.clock = lambda: 159
    assert room.refresh_board() is False
    room.clock = lambda: 160
    assert room.refresh_board() is True
    def fail():
        raise OSError("Gamma unavailable")
    room.fetch_board = fail
    room._board_worker()
    assert room._board["cards"] == [{"market_id": "111"}]
    assert room.state()["board_error"] == "Gamma unavailable"
