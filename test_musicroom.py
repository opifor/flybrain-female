"""Music plays, listener lessons and the ear share the paper book's clock."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

import dj
import musicroom
import react
import roam
from roomkit import LedgerError, Registry, make_server
from test_betroom import FakeBrain, FakeMB, FakeNose, FakePilot, FakePage, IMG

CATALOGUE = Path(__file__).parent / "tests" / "fixtures" / "musicroom" / "catalog.json"


@pytest.fixture
def now():
    return [1700000000.0]


def executor(tmp_path, now):
    clock = lambda: now[0]
    return dj.DJ(dj.Ledger(tmp_path, clock, CATALOGUE), "fixture", clock)


def room_at(tmp_path, now, **kwargs):
    fb = FakeBrain()
    return musicroom.Room(fb, FakePilot(), FakeMB(fb), FakeNose(), None, tmp_path,
                          "http://127.0.0.1:4674", "fixture", clock=lambda: now[0],
                          spawn=lambda fn, *args: fn(*args), catalogue_path=CATALOGUE, **kwargs)


def body(now, track="111", look="look-1", drive=.2):
    return {"track_id": track, "drive": drive, "seen_at": now[0], "look_id": look}


def reactions(ex, now, *rows):
    with ex.reactions_path.open("a", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps({"at": now[0], "track_id": "111", "kind": "sugar", "who": "listener", **row}) + "\n")


def test_declaration_and_hourly_board(tmp_path, now):
    registry = Registry()
    registry.register(musicroom.DECLARATION, "http://127.0.0.1:4674")
    room = room_at(tmp_path, now)
    room.refresh_board(force=True)
    first = room.board()["cards"]
    assert len(first) == 3 and [c["slot"] for c in first] == list(range(3))
    assert all(c["license"].startswith("CC") and c["room"]["path"] == "/musicroom" for c in first)
    assert room.board_source()() == first
    now[0] += 3600
    second = room.board_source()()
    assert [c["token"] for c in second] == [c["token"] for c in first[1:] + first[:1]]
    assert set(registry.rooms) == {"/musicroom"}


@pytest.mark.parametrize("count", [0, 1, 2, 6, 8, 11, 12, 13, 25])
def test_twelve_slots_rotate_without_repeating_tracks(tmp_path, now, count):
    rows = [{**musicroom.catalogue(CATALOGUE)[0], "id": str(i)} for i in range(count)]
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    room = room_at(tmp_path, now)
    room.catalogue_path = path
    for hour in (0, 1, max(0, count - 1), count, count + 1):
        now[0] = hour * 3600
        cards = room.board_source()()
        assert [c["slot"] for c in cards] == list(range(min(12, count)))
        assert [c["token"] for c in cards] == [str((hour + i) % count) for i in range(min(12, count))]
        assert len({c["token"] for c in cards}) == len(cards)


def test_room_reads_the_public_playback_clock(tmp_path, now):
    ex = executor(tmp_path, now)
    room = room_at(tmp_path, now)
    assert room.can_commit("111", now[0])
    ex.intent(body(now))
    room.refresh_board(force=True)
    assert room.now_playing == ex.ledger.book.public()["now_playing"]
    now[0] += 29.999
    assert not room.can_commit("222", now[0])
    now[0] += .001
    assert room.can_commit("222", now[0])
    assert not room.can_commit("111", now[0])
    ex.intent(body(now, "222", "second"))
    room.poll_events()
    assert room.now_playing["track_id"] == "222"
    now[0] += 120
    ex.resolve_once()
    room.refresh_board()
    assert room.now_playing is None and room.can_commit("222", now[0])


def test_play_is_durable_and_duplicate_look_cannot_start_again(tmp_path, now, monkeypatch):
    ex = executor(tmp_path, now)
    observed = []
    real = os.fsync
    def sync(fd):
        observed.append((len(ex.ledger.book.fills()), ex.ledger.path.read_text().splitlines()[-1]))
        real(fd)
    monkeypatch.setattr(os, "fsync", sync)
    assert ex.intent(body(now))[1]["status"] == "booked"
    assert observed[-1][0] == 0 and json.loads(observed[-1][1])["kind"] == "fill"
    assert ex.intent(body(now))[0] == 409
    assert executor(tmp_path, now).ledger.book.public() == ex.ledger.book.public()
    now[0] += 29
    assert ex.intent(body(now, "222", "too-soon"))[1]["reason"] == "still playing"
    now[0] += 1
    assert ex.intent(body(now, "111", "same"))[1]["reason"] == "already playing"
    assert ex.intent(body(now, "222", "second"))[1]["status"] == "booked"
    public = ex.ledger.book.public()
    assert public["plays"][0]["ended_at"] == now[0]
    assert public["plays"][1]["ended_at"] is None
    assert public["now_playing"]["track_id"] == "222"


def test_ledger_rejects_a_forged_early_fill_before_writing(tmp_path, now):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    i = ex.ledger.intent(body(now, "222", "bypass"))
    before = ex.ledger.path.read_bytes()
    with pytest.raises(LedgerError, match="play differs"):
        ex.ledger.terminal("fill", i, started_at=now[0], duration=120, title="Afternoon")
    assert ex.ledger.path.read_bytes() == before
    assert len(ex.ledger.book.fills()) == 1
    again = executor(tmp_path, now)
    assert again.ledger.book.events[-1]["reason"] == "interrupted"
    with again.ledger.path.open("ab") as stream:
        stream.write(b"broken\n")
    assert executor(tmp_path, now).intent(body(now, "333", "new"))[0] == 503


def test_sugar_and_shock_teach_the_fill_look_once(tmp_path, now):
    ex = executor(tmp_path, now)
    room = room_at(tmp_path, now)
    room.looks_dir.mkdir(parents=True)
    (room.looks_dir / "look-1.json").write_text(json.dumps({"token": "111",
        "brain_id": room.brain_id, "eligible": [2, 4]}), encoding="utf-8")
    ex.intent(body(now))
    reactions(ex, now, {}, {"kind": "shock", "who": "operator"})
    rewards = ex.resolve_once()
    assert [e["sign"] for e in rewards] == [1, -1]
    assert all(e["eligible"] == ["look-1"] and e["fill_seq"] == 1 for e in rewards)
    for reward in rewards:
        room._apply_event(reward)
    assert room.counters["sugar"] == room.counters["shock"] == 1
    assert room.last_dopamine[-1]["eligible"] == [2, 4]
    assert ("dopamine", (-1, 1.0)) in room.mb.log
    assert ex.ledger.book.public()["reactions"] == {"sugar": 1, "shock": 1,
                                                        "tracks": {"111": {"sugar": 1, "shock": 1}}}
    assert ex.resolve_once() == executor(tmp_path, now).resolve_once() == []
    again = room_at(tmp_path, now)
    again._apply_event(rewards[-1])
    assert not again.mb.log


def test_only_current_and_previous_plays_receive_reactions(tmp_path, now, caplog):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    now[0] += 30
    ex.intent(body(now, "222", "second"))
    reactions(ex, now, {}, {"track_id": "unknown"})
    assert [e["track_id"] for e in ex.resolve_once()] == ["111"]
    assert "ignored" in caplog.text
    now[0] += 30
    ex.intent(body(now, "333", "third"))
    reactions(ex, now, {}, {"track_id": "222", "kind": "shock"})
    assert [e["track_id"] for e in ex.resolve_once()] == ["222"]
    assert len(ex.ignored_path.read_text().splitlines()) == 2
    assert executor(tmp_path, now).resolve_once() == []
    assert len(ex.ignored_path.read_text().splitlines()) == 2


def test_partial_reaction_waits_for_its_newline(tmp_path, now):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    ex.reactions_path.write_text(json.dumps({"at": now[0], "track_id": "111", "kind": "sugar", "who": "chat"}), encoding="utf-8")
    assert ex.resolve_once() == []
    with ex.reactions_path.open("a") as stream:
        stream.write("\n")
    assert len(ex.resolve_once()) == 1


def test_loopback_walk_hears_only_while_playing(tmp_path, now, monkeypatch):
    table = [[1, 2, 3, 4]]
    analyses, heard = [], []
    def analyse(path):
        analyses.append(path)
        return table
    class Ear:
        def drive(self, rows, t):
            assert rows is table
            heard.append(t)
            return {(7,): 42.0}
    monkeypatch.setitem(sys.modules, "ear", SimpleNamespace(analyse=analyse))
    ex = executor(tmp_path, now)
    server = make_server(ex, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        room = room_at(tmp_path, now, ear=Ear())
        room.executor_url = f"http://127.0.0.1:{server.server_address[1]}"
        page = FakePage()
        async def walk():
            await room.enter(page)
            await room.step(page, IMG, 400, 100, 1)
            assert room.pilot.calls[-1]["extra_drive"] == {(5, 6): 100.0}
            await room.step(page, IMG, 100, 100, 2)
            room.pilot.click = True
            await room.step(page, IMG, 100, 100, 3)
            room._collect_intent()
            assert room.last_intents[-1]["status"] == "booked"
            room.pilot.click = False
            now[0] += 2
            room.poll_events()
            await room.step(page, IMG, 100, 100, 4)
            assert room.pilot.calls[-1]["extra_drive"] == {(5, 6): 100.0, (7,): 42.0}
            await room.step(page, IMG, 100, 100, 5)
            assert len(analyses) == 1 and heard == [2, 2]
            now[0] += 90
            ex.resolve_once()
            await room.step(page, IMG, 100, 100, 6)
            assert room.pilot.calls[-1]["extra_drive"] == {(5, 6): 100.0}
            assert room.now_playing is None
        asyncio.run(walk())
        assert len(ex.ledger.book.fills()) == 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_ear_cannot_replace_the_nose_drive(tmp_path, now, monkeypatch):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    monkeypatch.setitem(sys.modules, "ear", SimpleNamespace(analyse=lambda path: []))
    room = room_at(tmp_path, now, ear=SimpleNamespace(drive=lambda table, t: {(5, 6): 2}))
    room.refresh_board()
    with pytest.raises(ValueError, match="overlaps"):
        room.extra_drive(room.smell_of("111"))
    room.ear = None
    assert room.extra_drive(room.smell_of("111")) == {(5, 6): 100}


@pytest.mark.parametrize("change", [{"track_id": "unknown"}, {"track_id": []}, {"drive": True},
                                   {"drive": float("nan")}, {"amount": 10}, {"look_id": "../look"}])
def test_exact_intent_validation(tmp_path, now, change):
    ex = executor(tmp_path, now)
    before = ex.ledger.path.read_bytes()
    assert ex.intent({**body(now), **change})[0] == 400
    assert ex.ledger.path.read_bytes() == before


def test_live_flag_refuses_before_creating_a_ledger(tmp_path):
    result = subprocess.run([sys.executable, "dj.py"], capture_output=True, text=True,
                            env={**os.environ, "FLY_MUSICROOM_LIVE": "1", "FLY_STATE_DIR": str(tmp_path)})
    assert result.returncode == 2 and dj.LIVE_REFUSAL in result.stderr
    assert not (tmp_path / "musicroom").exists()


def test_registered_routes_use_the_room_catalogue(tmp_path, now, monkeypatch):
    ex = executor(tmp_path, now)
    room = room_at(tmp_path, now)
    monkeypatch.setitem(roam.STATE, "rooms", {"/musicroom": room})
    assert len(roam.musicroom_board()["cards"]) == 3
    assert roam.musicroom_public()["now_playing"] is None
    ex.intent(body(now))
    assert roam.musicroom_public()["now_playing"]["track_id"] == "111"
    assert roam.musicroom_track("111").status_code == 404
    assert roam.musicroom_track("unknown").status_code == 404
    assert Path(roam.musicroom_page().path).name == "musicroom.html"


def test_registration_connects_the_ear_and_music_door(tmp_path, now, monkeypatch):
    from test_rooms import Health, make_room
    import betroom
    attached = []
    class Ear:
        def __init__(self, fb):
            attached.append(fb)
    monkeypatch.setitem(sys.modules, "ear", SimpleNamespace(FlyEar=Ear))
    monkeypatch.setattr(roam, "load_env", lambda: {"FLY_STATE_DIR": str(tmp_path),
                                                  "FLY_MUSICROOM_CATALOGUE": str(CATALOGUE)})
    monkeypatch.setattr(roam, "STATE", dict(roam.STATE))
    betting = make_room(betroom.Room, tmp_path)
    roam.register_rooms(betting)
    music = roam.STATE["rooms"]["/musicroom"]
    assert attached == [betting.fb] and isinstance(music.ear, Ear)
    assert music.executor_url == "http://127.0.0.1:4674"
    doors = roam.STATE["hall"].registry.healthy(Health())
    assert [d["path"] for d in doors] == ["/betroom", "/tiproom", "/musicroom", "/gameroom"]
    assert len(music.board_source()()) == 3


def test_public_history_keeps_forty_plays_and_natural_end_times(tmp_path, now):
    ex = executor(tmp_path, now)
    starts = []
    for i in range(42):
        starts.append(now[0])
        assert ex.intent(body(now, "111", f"play-{i}"))[1]["status"] == "booked"
        now[0] += 100
    ex.resolve_once()
    public = json.loads(ex.ledger.public_path.read_text())
    assert public["now_playing"] is None
    assert len(public["plays"]) == 40
    assert [p["started_at"] for p in public["plays"]] == starts[2:]
    assert all(p["ended_at"] == p["started_at"] + 90 for p in public["plays"])


def test_fill_uses_one_timestamp_with_a_moving_clock(tmp_path, now):
    def clock():
        now[0] += .001
        return now[0]
    led = dj.Ledger(tmp_path, clock, CATALOGUE)
    ex = dj.DJ(led, "fixture", clock)
    result = ex.intent(body(now))[1]
    assert result["status"] == "booked"
    assert result["event"]["at"] == result["event"]["started_at"]


def test_reaction_for_a_different_look_cannot_enter_the_ledger(tmp_path, now):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    before = ex.ledger.path.read_bytes()
    with pytest.raises(LedgerError, match="reaction differs"):
        ex.ledger.append("dopamine", id=1, seq=2, fill_seq=1, track_id="111", look_id="other",
                         eligible=["other"], reaction_id="fake", reaction_at=now[0],
                         reaction_kind="sugar", who="listener", sign=1)
    assert ex.ledger.path.read_bytes() == before


def test_react_appends_for_the_public_track(tmp_path, now, monkeypatch):
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    monkeypatch.setattr(react, "load_env", lambda: {"FLY_STATE_DIR": str(tmp_path)})
    monkeypatch.setattr(react.time, "time", lambda: now[0])
    monkeypatch.setattr(sys, "argv", ["react.py", "shock", "--who", "operator"])
    react.main()
    assert json.loads(ex.reactions_path.read_text()) == {"at": now[0], "track_id": "111", "kind": "shock", "who": "operator"}
    now[0] += 100
    with pytest.raises(SystemExit) as exc:
        react.main()
    assert exc.value.code == 1
    assert len(ex.reactions_path.read_text().splitlines()) == 1


def test_catalogue_ids_are_text(tmp_path):
    import json
    import musicroom
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps([{"id": 139129578, "title": "t", "artist": "a", "license": "CC0", "duration": 60.0, "file": "x.wav"}]), encoding="utf-8")
    assert musicroom.catalogue(path)[0]["id"] == "139129578"


@pytest.fixture(autouse=True)
def thirty_second_rule(monkeypatch):
    # The walks above were written against a thirty-second minimum; the house
    # rule is ninety now, and one test below covers that number on its own.
    monkeypatch.setattr(dj, "MIN_PLAY_S", 30)
    monkeypatch.setattr(musicroom, "MIN_PLAY_S", 30)


def test_the_house_rule_is_ninety_seconds(tmp_path, now, monkeypatch):
    monkeypatch.setattr(dj, "MIN_PLAY_S", 90)
    monkeypatch.setattr(musicroom, "MIN_PLAY_S", 90)
    ex = executor(tmp_path, now)
    ex.intent(body(now))
    now[0] += 60
    assert ex.intent(body(now, "222", "sixty"))[1]["reason"] == "still playing"
    now[0] += 30
    assert ex.intent(body(now, "222", "ninety"))[1]["status"] == "booked"
