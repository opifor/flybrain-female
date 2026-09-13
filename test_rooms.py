"""Doors, paper tips and remembered thanks use the same walk."""
import asyncio
from dataclasses import replace
import json
import random
import os
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

import pytest
import betroom
import hall
import roam
import roomkit
import room_pages
import tipper
import tiproom
from room import LoopbackHttp
from test_betroom import FakeBrain, FakeMB, FakeNose, FakePilot, FakePage, IMG


def registry():
    result = roomkit.Registry()
    result.register(betroom.DECLARATION, "http://127.0.0.1:4672")
    result.register(tiproom.DECLARATION, "http://127.0.0.1:4673")
    return result


class Health:
    def __init__(self):
        self.bad = set()

    def get_json(self, url, **kwargs):
        if url in self.bad:
            raise OSError("no executor answer")
        return 200, {"ok": True}


def make_room(cls, tmp_path, **kwargs):
    fb = FakeBrain()
    return cls(fb, FakePilot(), FakeMB(fb), FakeNose(), None, tmp_path,
               "http://127.0.0.1:4672", "fixture", clock=lambda: 1700000000,
               spawn=lambda fn, *args: fn(*args), **kwargs)


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("stale_health", [False, True])
def test_new_book_replays_rewards_without_old_claims(tmp_path, capsys, legacy, stale_health):
    class Events:
        def __init__(self):
            self.afters = []

        def get_json(self, url, **kwargs):
            if url.endswith("/health"):
                return 200, {"ok": True, "book": "old" if stale_health else "new"}
            after = int(url.split("after=")[1])
            self.afters.append(after)
            return 200, {"book": "new", "last": 1, "events": [reward] if after == 0 else []}

    http = Events()
    room = make_room(betroom.Room, tmp_path, fetch_board=lambda: [], http=http)
    room.book_id = "old"
    room.last_seq = 928
    room._look_seq = 42
    room.refs = {"keep": ["look-keep"]}
    room._save_room()
    if legacy:
        saved = json.loads(room.room_file.read_text(encoding="utf-8"))
        del saved["book_id"]
        room.room_file.write_text(json.dumps(saved), encoding="utf-8")
    history = json.dumps({"seq": 1, **({} if legacy else {"book": "old"})}) + "\n"
    room.dopamine_file.write_text(history, encoding="utf-8")
    room = make_room(betroom.Room, tmp_path, fetch_board=lambda: [], http=http)
    room.looks_dir.mkdir(parents=True)
    (room.looks_dir / "reward-look.json").write_text(json.dumps({
        "token": "market", "brain_id": room.brain_id, "eligible": [2, 4]}), encoding="utf-8")
    reward = {"seq": 1, "kind": "dopamine", "market_id": "market",
              "look_id": "reward-look", "sign": 1}
    room.poll_events()
    room.poll_events()
    assert http.afters[-1] == 0
    assert room.book_id == "new" and room.last_seq == 1
    assert room._claimed == {1}
    assert room.refs == {"keep": ["look-keep"]} and room._look_seq == 42
    assert room.mb.log.count(("dopamine", (1, 1.0))) == 1
    assert capsys.readouterr().out.count("new book new, cursor reset") == 1
    saved = json.loads(room.room_file.read_text(encoding="utf-8"))
    assert saved["book_id"] == "new" and saved["last_seq"] == 1
    text = room.dopamine_file.read_text(encoding="utf-8")
    assert text.startswith(history)
    records = [json.loads(line) for line in text.splitlines()[1:]]
    assert [r["status"] for r in records] == ["pending", "delivered"]
    assert all(r["book"] == "new" for r in records)
    with room.dopamine_file.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"book": "old", "seq": 929}) + "\n")
    again = make_room(betroom.Room, tmp_path, fetch_board=lambda: [], http=http)
    assert again.last_seq == 1 and again._claimed == {1}
    again.poll_events()
    again.poll_events()
    assert again.mb.log == []
    assert "cursor reset" not in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["betroom", "tiproom", "musicroom"])
def test_room_door_uses_the_same_dwell_and_never_calls_executor(tmp_path, kind):
    import musicroom
    cls = {"betroom": betroom.Room, "tiproom": tiproom.Room, "musicroom": musicroom.Room}[kind]
    room = make_room(cls, tmp_path, fetch_board=lambda: [])
    room.read_book = lambda: {"now_playing": {"track_id": "song", "started_at": room._now()}}
    room.spawn = lambda *args: pytest.fail("the door must not contact the executor")
    room.refresh_board = lambda **kwargs: None
    boxes = [dict(x=0, y=0, w=1280, h=40), dict(x=0, y=760, w=1280, h=40),
             dict(x=0, y=0, w=48, h=800), dict(x=1232, y=0, w=48, h=800)]
    page = FakePage([dict(token="/hall", **box) for box in boxes])
    assert len(asyncio.run(room._rects(page))) == 4
    asyncio.run(room.enter(page))
    assert room.state()["entered_at"] == 1700000000
    assert room.state()["last_exit"] is None
    assert room.can_commit("/hall", room._now())
    room._seen["other"] = (1.0, 0.0)
    room.pilot.fired[None] = room.fb.fired
    room.pilot.click = True
    asyncio.run(room.step(page, IMG, 24, 400, 1))
    assert room.destination is None
    dwell = room._dwell
    assert room.state()["rects"]["/hall"] == boxes[2]
    room.pilot.click = False
    asyncio.run(room.step(page, IMG, 640, 20, 2))
    assert room._dwell is dwell and dwell["steps"] == 2
    assert dwell["card"] == dict(token="/hall", **boxes[0])
    assert room.state()["rects"]["/hall"] == boxes[0]
    assert room.state()["door_rects"] == boxes
    for x, y in [(24, 400), (640, 20), (640, 780), (1256, 400)] * 2:
        room._margin_steps = 5
        asyncio.run(room.step(page, IMG, x, y, 3))
        assert room._margin_steps == 0 and room.counters["nudges"] == 0
    room.pilot.click = True
    asyncio.run(room.step(page, IMG, 640, 20, 4))
    assert room.destination == "/hall"
    assert room.state()["rects"]["/hall"] == boxes[0]
    assert room.state()["last_exit"] == {"by": "door", "at": 1700000000}
    assert room.last_intents[-1]["side"] == "door"
    assert room._intent is None
    room.leave()
    room.clock = lambda: 1700000010
    asyncio.run(room.enter(page))
    assert room.destination is None
    assert room.entered_at == 1700000010


def test_room_clock_closes_at_six_minutes_only_while_visiting(tmp_path):
    room = make_room(tiproom.Room, tmp_path, fetch_board=lambda: [])
    assert roam.room_clock(room, 1700000600) is None
    asyncio.run(room.enter(FakePage([])))
    assert roam.ROOM_STAY_MAX_S == 360
    assert roam.room_clock(room, room.entered_at + 359.999) is None
    assert room.destination is None and room.last_exit is None
    assert roam.room_clock(room, room.entered_at + 360) == "clock"
    assert room.destination == "/hall"
    assert room.state()["last_exit"] == {"by": "clock", "at": 1700000360}
    room.leave()
    assert roam.room_clock(room, 1700000700) is None
    hallway = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    asyncio.run(hallway.enter(FakePage([])))
    assert roam.room_clock(hallway, hallway.entered_at + 600) is None


def test_only_rooms_have_the_hall_frame():
    for name, text in room_pages.pages().items():
        assert text.count('data-token="/hall"') == (0 if name == "hall" else 4)


@pytest.mark.parametrize("kind", ["hall", "betroom", "tiproom", "musicroom"])
def test_last_round_rectangles_are_exported(tmp_path, kind):
    import musicroom
    cls = {"hall": hall.Hall, "betroom": betroom.Room,
           "tiproom": tiproom.Room, "musicroom": musicroom.Room}[kind]
    kwargs = {"registry": registry(), "http": Health()} if kind == "hall" else {}
    room = make_room(cls, tmp_path, fetch_board=lambda: [], **kwargs)
    room.refresh_board = lambda **kwargs: None
    room.read_book = lambda: {}
    assert room.state()["rects"] == {}
    room.remember("card", {"name": "card"})
    boxes = [{"token": "card", "x": 56.5, "y": 48.0, "w": 368.0, "h": 320.0}]
    if kind != "hall":
        boxes.append({"token": "/hall", "x": 56, "y": 760, "w": 1168, "h": 40})
    asyncio.run(room.step(FakePage(boxes), IMG, 0, 0, 1))
    expected = {box["token"]: {key: int(box[key]) for key in ("x", "y", "w", "h")} for box in boxes}
    assert room.state()["rects"] == expected
    assert all(type(value) is int for box in room.state()["rects"].values() for value in box.values())
    with patch.dict(roam.STATE, {"rooms": {room.declaration.path: room}}):
        assert roam.rooms_status()[room.declaration.path]["rects"] == expected
    asyncio.run(room.step(FakePage([]), IMG, 0, 0, 2))
    assert room.state()["rects"] == {}


@pytest.mark.parametrize("reward", ["", " ", None])
def test_registration_requires_a_reward_source(reward):
    rooms = roomkit.Registry()
    with pytest.raises(ValueError, match="reward_source is required"):
        rooms.register(replace(tiproom.DECLARATION, reward_source=reward), "http://127.0.0.1:4673")
    assert rooms.rooms == {}


@pytest.mark.parametrize("how", [("one.",), tuple("sentence." for _ in range(9)),
                                 ("x" * 120 + ".", "two.", "three."),
                                 ("one\ntwo.", "two.", "three."),
                                 ("<b>one</b>.", "two.", "three."),
                                 ("no ending", "two.", "three."),
                                 (None, "two.", "three.")])
def test_how_requires_short_plain_sentences(how):
    with pytest.raises(ValueError, match="how needs"):
        replace(tiproom.DECLARATION, how=how).validate()


def test_rooms_explain_their_own_play():
    import musicroom
    for declaration in (betroom.DECLARATION, tiproom.DECLARATION, musicroom.DECLARATION):
        assert 3 <= len(declaration.public()["how"]) <= 8
    assert "YES" in betroom.DECLARATION.how[3]
    assert "practice thank-you" in tiproom.DECLARATION.how[-3]
    assert "Johnston organs" in musicroom.DECLARATION.how[-3]


def test_declarations_keep_code_out_of_prose():
    import musicroom
    for declaration in (hall.DECLARATION, betroom.DECLARATION, tiproom.DECLARATION, musicroom.DECLARATION):
        prose = [declaration.commit_means, declaration.reward_source, declaration.cards["source"],
                 *declaration.chosen, *declaration.measured, *declaration.how]
        for sentence in prose:
            assert not any(term in sentence for term in ("(", "abs(", "floor(")), sentence


def test_hall_hides_an_executor_that_does_not_answer(tmp_path):
    http = Health()
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=http)
    room.refresh_board(force=True)
    assert {c["path"] for c in room.board()["cards"]} == {"/betroom", "/tiproom"}
    http.bad.add("http://127.0.0.1:4673/health")
    room.refresh_board(force=True)
    assert [c["path"] for c in room.board()["cards"]] == ["/betroom"] * 12
    assert room.state()["doors"] == [{"name": "the betting room", "path": "/betroom", "preview": ""}] * 12
    room.clock = lambda: 1700000005
    assert room.state()["doors"] == []


def test_hall_order_shuffles_with_visits_and_survives_restart(tmp_path):
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    for visit in range(1, 5):
        asyncio.run(room.enter(FakePage([])))
        board = room.board()
        expected = [f"{path}#{i}" for path in ("/betroom", "/tiproom") for i in range(6)]
        random.Random(visit - 1).shuffle(expected)
        assert board["order_seed"] == visit - 1
        state = room.state()
        assert state["order_seed"] == visit - 1
        names = {"/betroom": "the betting room", "/tiproom": "the tipping room"}
        assert state["doors"] == [{"name": names[token.split("#")[0]], "path": token.split("#")[0], "preview": ""} for token in expected]
        assert [c["token"] for c in board["cards"]] == expected
        assert [c["token"] for c in room.registry.healthy(room.http)] == ["/betroom", "/tiproom"]
        assert [c["token"] for c in room.board()["cards"]] == expected
        room.leave()
        room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())


def test_margin_escape_replaces_only_the_sixth_motor_output(tmp_path):
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    room.refresh_board(force=True)
    page = FakePage([{"token": "/betroom#0", "x": 400, "y": 400, "w": 100, "h": 100},
                     {"token": "/tiproom#0", "x": 100, "y": 200, "w": 100, "h": 100}])
    room.pilot.click = True
    async def walk():
        for step in range(1, 13):
            before = len(room.mb.log)
            dx, dy, click, hz, info = await room.step(page, IMG, 0, 50, step)
            if step % 6:
                assert (dx, dy, click) == (0, 0, True)
            else:
                assert (dx, dy, click) == pytest.approx((36, 48, False))
            assert room.counters["nudges"] == step // 6
            assert room.mb.log[before:] == [("observe", 2), ("forget", None)]
            assert info["hall"]["drive"] is None and room._dwell is None
        assert room.state()["nudges"] == 2
    asyncio.run(walk())


@pytest.mark.parametrize("position", [(100, 100), (-12, 100), (292, 100), (100, -12), (100, 212)])
def test_card_and_its_padding_reset_margin_rounds(tmp_path, position):
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    room.refresh_board(force=True)
    page = FakePage([{"token": "/betroom#0", "x": 0, "y": 0, "w": 280, "h": 200}])
    async def walk():
        for _ in range(5):
            await room.step(page, IMG, 900, 600, 1)
        for _ in range(7):
            assert (await room.step(page, IMG, *position, 1))[:2] == (0, 0)
        for _ in range(5):
            await room.step(page, IMG, 900, 600, 1)
        assert room.state()["nudges"] == 0
        await room.enter(page)
        await room.step(page, IMG, 900, 600, 1)
        assert room.state()["nudges"] == 0
    asyncio.run(walk())


@pytest.mark.parametrize("reply", [(503, {"ok": True}), (200, {"ok": False}),
                                   (200, {"ok": True, "publish_error": "disk full"}), (200, [])])
def test_unhealthy_replies_leave_no_door(reply):
    class Http:
        def get_json(self, *args, **kwargs):
            return reply
    assert registry().healthy(Http()) == []


@pytest.mark.parametrize("target", ["/betroom", "/tiproom"])
def test_door_stop_enters_only_after_two_readings(tmp_path, target):
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    room.refresh_board(force=True)
    page = FakePage([{"token": path + "#0", "x": i * 300, "y": 0, "w": 280, "h": 200}
                     for i, path in enumerate(("/betroom", "/tiproom"))])
    async def walk():
        await room.enter(page)
        x = 100 if target == "/betroom" else 400
        await room.step(page, IMG, 500 - x, 100, 1)
        room.pilot.click = True
        await room.step(page, IMG, x, 100, 2)
        assert room.destination is None
        await room.step(page, IMG, x, 100, 3)
        assert room.destination == target
        room.record_entry(room.destination)
    asyncio.run(walk())
    public = json.loads(room.public.read_text())
    assert public["events"][-1]["text"] == "entered " + registry().rooms[target][0].name
    assert not list(tmp_path.rglob("ledger*"))
    assert make_room(hall.Hall, tmp_path, registry=registry(), http=Health()).entered == room.entered


def test_unhealthy_door_cannot_commit_a_stale_card(tmp_path):
    http = Health()
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=http)
    room.refresh_board(force=True)
    http.bad.add("http://127.0.0.1:4673/health")
    room._commit(IMG, 100, 100, 1, {"token": "/tiproom#0"}, {}, 0.5, None)
    assert room.destination is None and room.entered == []


def body(address=0, drive=0.1, look="look-1", at=1700000000):
    return {"address": tiproom.wallets()[address]["address"], "drive": drive, "look_id": look, "seen_at": at}


def executor(tmp_path, now=1700000000, thanks=None):
    clock = lambda: now
    return tipper.Tipper(tipper.Ledger(tmp_path, clock), "fixture", clock, thanks)


def test_tip_is_durable_and_replays_before_balance_changes(tmp_path, monkeypatch):
    ex = executor(tmp_path)
    observed = []
    real = os.fsync
    def sync(fd):
        observed.append((ex.ledger.book.balance_cents, ex.ledger.path.read_text().splitlines()[-1]))
        real(fd)
    monkeypatch.setattr(os, "fsync", sync)
    code, reply = ex.intent(body())
    assert (code, reply["status"]) == (200, "booked")
    assert ex.ledger.book.balance_cents == 9000
    assert observed[-1][0] == 10000
    assert json.loads(observed[-1][1])["kind"] == "fill"
    assert [json.loads(s)["kind"] for s in ex.ledger.path.read_text().splitlines()] == ["open", "intent", "fill"]
    assert executor(tmp_path).ledger.book.public() == ex.ledger.book.public()


def test_daily_cap_refuses_and_survives_restart(tmp_path):
    ex = executor(tmp_path)
    assert ex.intent(body(0, .1, "one"))[1]["status"] == "booked"
    assert ex.intent(body(1, .1, "two"))[1]["status"] == "booked"
    ex = executor(tmp_path)
    before = ex.ledger.book.balance_cents
    result = ex.intent(body(2, .1, "three"))[1]
    assert result["reason"] == "daily cap"
    assert ex.ledger.book.balance_cents == before == 8100
    ex = executor(tmp_path, 1700000000 + 86400)
    assert ex.intent(body(2, .1, "tomorrow", at=1700000000 + 86400))[1]["status"] == "booked"


def test_per_address_cap_is_lifetime_and_refuses_without_clipping(tmp_path):
    ex = executor(tmp_path)
    ex.intent(body())
    ex = executor(tmp_path, 1700000000 + 86400)
    assert ex.intent(body(0, .1, "again", at=1700000000 + 86400))[1]["reason"] == "per-address cap"
    assert ex.ledger.book.balance_cents == 9000


def test_fixture_thanks_delivers_stored_eligibility_once(tmp_path):
    ex = executor(tmp_path)
    room = make_room(tiproom.Room, tmp_path)
    room.looks_dir.mkdir(parents=True)
    (room.looks_dir / "look-1.json").write_text(json.dumps({"token": body()["address"],
        "brain_id": room.brain_id, "eligible": [2, 4]}), encoding="utf-8")
    ex.intent(body())
    assert not any(e["kind"] == "dopamine" for e in ex.ledger.book.events)
    rewards = ex.resolve_once()
    assert len(rewards) == 1
    room._apply_event(rewards[0])
    assert ("dopamine", (1, 1.0)) in room.mb.log
    assert room.last_dopamine[-1]["eligible"] == [2, 4]
    assert room.last_dopamine[-1]["address"] == body()["address"]
    assert ex.resolve_once() == []
    assert executor(tmp_path).resolve_once() == []
    again = make_room(tiproom.Room, tmp_path)
    again._apply_event(rewards[0])
    assert not again.mb.log


def test_silence_does_not_teach(tmp_path):
    ex = executor(tmp_path, thanks=[])
    ex.intent(body())
    assert ex.resolve_once() == []
    assert [e["kind"] for e in ex.ledger.book.events] == ["fill"]


def test_tip_replay_refuses_a_forged_cap_bypass(tmp_path):
    ex = executor(tmp_path)
    ex.intent(body())
    ex.ledger.intent(body(0, .1, "bypass"))
    before = ex.ledger.path.read_bytes()
    with pytest.raises(roomkit.LedgerError, match="cap"):
        ex.ledger.terminal("fill", 2, amount_cents=900)
    assert ex.ledger.path.read_bytes() == before
    assert ex.ledger.book.balance_cents == 9000


def test_tip_walk_sends_the_unmodified_drive_over_loopback(tmp_path):
    ex = executor(tmp_path)
    server = roomkit.make_server(ex, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        room = make_room(tiproom.Room, tmp_path)
        room.executor_url = f"http://127.0.0.1:{server.server_address[1]}"
        room.refresh_board(force=True)
        room.mb.base[:] = [120, 100, 100, 100]
        cards = tiproom.wallets()[:2]
        page = FakePage([{"token": c["token"], "x": i * 300, "y": 0, "w": 280, "h": 200}
                         for i, c in enumerate(cards)])
        async def walk():
            await room.enter(page)
            await room.step(page, IMG, 400, 100, 1)
            await room.step(page, IMG, 100, 100, 2)
            room.pilot.click = True
            await room.step(page, IMG, 100, 100, 3)
        asyncio.run(walk())
        room._collect_intent()
        assert room.last_intents[-1]["status"] == "booked"
        assert ex.ledger.book.events[-1]["amount_cents"] == 909
        assert room.refs[cards[0]["token"]]
        ex.resolve_once()
        room._events_result = ex.events()[1]
        room.poll_events()
        assert room.counters["sugar"] == 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


@pytest.mark.parametrize("change", [{"amount": 100}, {"drive": True}, {"drive": float("nan")}, {"address": "bad"}])
def test_tip_body_is_exact(tmp_path, change):
    ex = executor(tmp_path)
    before = ex.ledger.path.read_bytes()
    assert ex.intent({**body(), **change})[0] == 400
    assert ex.ledger.path.read_bytes() == before


def test_tip_busy_duplicate_age_and_recovery(tmp_path):
    ex = executor(tmp_path)
    with ex.lock:
        assert ex.intent(body())[0] == 409
    assert ex.ledger.book.intents == 0
    ex.intent(body())
    assert ex.intent(body())[0] == 409
    assert ex.intent(body(1, .1, "old", 0))[1]["reason"] == "stale or future look"
    ex.ledger.intent(body(1, .1, "interrupted"))
    again = executor(tmp_path)
    assert again.ledger.book.events[-1]["reason"] == "interrupted"
    with again.ledger.path.open("ab") as stream:
        stream.write(b"broken\n")
    assert executor(tmp_path).intent(body(1, .1, "new"))[0] == 503


def test_tip_live_flag_stops_before_opening_the_ledger(tmp_path):
    result = subprocess.run([sys.executable, "tipper.py"], capture_output=True, text=True,
        env={**os.environ, "FLY_TIPROOM_LIVE": "1", "FLY_STATE_DIR": str(tmp_path)})
    assert result.returncode == 2 and tipper.LIVE_REFUSAL in result.stderr
    assert not (tmp_path / "tiproom").exists()


def test_hall_reset_and_exact_destinations(tmp_path):
    room = make_room(betroom.Room, tmp_path)
    with patch.object(roam, "load_env", return_value={"FLY_HALL": "1", "FLY_STATE_DIR": str(tmp_path)}), patch.object(roam, "PIN", ""), patch.dict(roam.STATE):
        roam.register_rooms(room)
        url, name = roam.next_place(None)
        assert name == "the hall" and url.endswith("/hall")
        assert roam.next_place(None, False) == (url, "the hall")
        assert roam.allowed_host(url)
        assert roam.allowed_host(url.replace("/hall", "/tiproom"))
        assert not roam.allowed_host(url + "/public.json")
        assert not roam.allowed_host(url + "?x=1")
        assert set(roam.rooms_status()) == {"/hall", "/betroom", "/tiproom", "/musicroom", "/gameroom", "/paintroom"}


def test_pages_carry_the_declarations_and_share_the_skeleton():
    for name, generated in room_pages.pages().items():
        assert (room_pages.WEB / (name + ".html")).read_text(encoding="utf-8") == generated
        assert 'id="room-declaration"' in generated and 'id="disclosure"' in generated
    cards = tiproom.wallets()
    assert len(cards) == 8
    assert cards[0]["area_scale"] < cards[6]["area_scale"] == cards[7]["area_scale"] == 1
