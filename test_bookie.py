"""Recorded public responses, with no network in the tests."""
import copy
import json
import math
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

import betbook
import bookie
import polymarket

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "betroom"


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text(encoding="utf-8"))


class World:
    def __init__(self):
        self.raw = fixture("gamma_btc")[0]
        self.now = fixture("provenance")["captured_at"]
        self.mid = fixture("clob_midpoint")
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if url.startswith(polymarket.CLOB):
            return copy.deepcopy(self.mid)
        assert url.startswith(polymarket.GAMMA)
        return [copy.deepcopy(self.raw)]

    def body(self, drive=0.5, look="look-1"):
        return {"market_id": self.raw["id"],
                "token_id": json.loads(self.raw["clobTokenIds"])[0 if drive > 0 else 1],
                "side": "YES" if drive > 0 else "NO", "drive": drive,
                "seen_at": self.now, "look_id": look}


@pytest.fixture
def setup(tmp_path):
    world = World()
    ledger = betbook.Ledger(betbook.paths(tmp_path)["ledger"])
    ex = bookie.Bookie(polymarket.Markets(world.fetch, lambda: world.now), ledger,
                       "test-secret", clock=lambda: world.now)
    return world, ledger, ex


@pytest.mark.parametrize("drive", [0.5, -0.5])
def test_one_open_bet_per_market_until_settlement(setup, drive):
    world, led, ex = setup
    assert ex.intent(world.body(drive))[1]["status"] == "booked"
    balance = led.book.balance_cents
    for n in range(3):
        reply = ex.intent(world.body(drive, look=f"second-{n}"))[1]
        assert (reply["status"], reply["reason"]) == ("refused", "open position")
    assert led.book.balance_cents == balance
    assert len(led.book.positions) == 1
    public = json.loads(led.public_path.read_text())
    assert public["markets"][world.raw["id"]]["open"] is True
    assert public["refusals"] == {"open position": 3}
    replay = betbook.rebuild(led.path)
    assert replay.refusals == public["refusals"]
    assert [e["reason"] for e in replay.events if e["kind"] == "refused"] == ["open position"] * 3
    world.raw.update(closed=True, outcomePrices=json.dumps(["1", "0"]))
    assert len(ex.resolve_once()) == 1
    assert json.loads(led.public_path.read_text())["markets"][world.raw["id"]]["open"] is False
    world.raw = fixture("gamma_btc")[0]
    assert ex.intent(world.body(look="after-settlement"))[1]["status"] == "booked"


def test_an_open_bet_does_not_close_another_market(setup):
    world, led, ex = setup
    assert ex.intent(world.body())[1]["status"] == "booked"
    world.raw["id"] = "999"
    assert ex.intent(world.body(look="other-market"))[1]["status"] == "booked"
    assert {p["market_id"] for p in led.book.positions.values()} == {fixture("gamma_btc")[0]["id"], "999"}


@pytest.mark.parametrize("drive", [1.0, -1.0, 0.37, -0.27, 0.0001])
def test_stake_and_shares_come_only_from_drive_and_balance(setup, drive):
    world, led, ex = setup
    code, reply = ex.intent(world.body(drive))
    assert (code, reply["status"]) == (200, "booked")
    stake = math.floor(Fraction(abs(drive)) * 10000)
    assert led.book.balance_cents == 10000 - stake
    fill = reply["event"]
    assert int(fill["stake_cents"]) == stake
    assert Fraction(fill["shares"]) == Fraction(stake, 100) / Fraction(world.mid["mid"])
    assert json.loads(led.public_path.read_text())["open_bets"][0]["look_id"] == "look-1"
    assert [json.loads(line)["kind"] for line in led.path.read_text().splitlines()] == ["open", "intent", "fill"]


@pytest.mark.parametrize("change", [{"amount": 1}, {"drive": True}, {"drive": float("nan")},
                                   {"side": "buy"}, {"market_id": "../x"}, {"look_id": "../x"}])
def test_malformed_body_cannot_write_an_intent(setup, change):
    world, led, ex = setup
    before = led.path.read_bytes()
    assert ex.intent({**world.body(), **change})[0] == 400
    assert led.path.read_bytes() == before


@pytest.mark.parametrize("change", [{"side": "NO"}, {"drive": 0}, {"drive": 2},
                                   {"seen_at": 0}, {"token_id": "123"}])
def test_refusal_leaves_balance_untouched(setup, change):
    world, led, ex = setup
    assert ex.intent({**world.body(), **change})[1]["status"] == "refused"
    assert led.book.balance_cents == 10000
    assert [json.loads(line)["kind"] for line in led.path.read_text().splitlines()] == ["open", "intent", "refused"]


def test_retries_and_busy_requests_do_not_double_book(setup):
    world, led, ex = setup
    ex.lock.acquire()
    try:
        assert ex.intent(world.body())[0] == 409
    finally:
        ex.lock.release()
    assert led.book.intents == 0
    assert ex.intent(world.body())[1]["status"] == "booked"
    before = led.path.read_bytes()
    assert ex.intent(world.body())[0] == 409
    assert led.path.read_bytes() == before


def test_interrupted_intent_and_replay(setup):
    world, led, ex = setup
    led.intent(world.body())
    again = betbook.Ledger(led.path)
    assert again.book.events[-1]["reason"] == "interrupted"
    assert again.book.balance_cents == 10000
    assert betbook.rebuild(led.path).state() == again.book.state()


def test_corrupt_ledger_fails_closed(setup):
    world, led, ex = setup
    ex.intent(world.body())
    published = led.public_path.read_bytes()
    with led.path.open("ab") as f:
        f.write(b'{bad\xff\n')
    ex.ledger = betbook.Ledger(led.path)
    assert not ex.ledger.ok
    assert ex.intent(world.body(look="look-2"))[0] == 503
    assert ex.events()[0] == 503
    assert ex.health()["balance"] is None
    assert led.public_path.read_bytes() == published


def test_publication_failure_does_not_erase_fill(setup, monkeypatch):
    world, led, ex = setup
    def fail(*args):
        raise PermissionError("reader holds derived file")
    monkeypatch.setattr(betbook, "atomic_write", fail)
    assert ex.intent(world.body())[1]["status"] == "booked"
    assert led.publish_error
    assert betbook.rebuild(led.path).state() == led.book.state()


@pytest.mark.parametrize("side", ["YES", "NO"])
@pytest.mark.parametrize("outcome", ["YES", "NO"])
def test_resolution_pays_once_and_teaches_the_recorded_cells(setup, tmp_path, side, outcome):
    import betroom
    from test_betroom import FakeBrain, FakeMB, FakePilot, FakeNose
    world, led, ex = setup
    fill = ex.intent(world.body(0.5 if side == "YES" else -0.5))[1]["event"]
    # This variant changes only the recorded response's resolution fields.
    world.raw.update(closed=True, outcomePrices=json.dumps(["1", "0"] if outcome == "YES" else ["0", "1"]))
    events = ex.resolve_once()
    assert len(events) == 1
    payout = math.floor(Fraction(fill["shares"]) * 100) if side == outcome else 0
    assert led.book.balance_cents == 5000 + payout
    assert ex.resolve_once() == []
    assert not led.book.positions
    public = json.loads(led.public_path.read_text())
    assert public["win_count"] == int(side == outcome)
    assert public["loss_count"] == int(side != outcome)
    assert public["settled_bets"][0]["outcome"] == outcome
    fb = FakeBrain()
    mb = FakeMB(fb)
    observed = []
    mb.observe = lambda cells: observed.append(list(cells))
    room = betroom.Room(fb, FakePilot(), mb, FakeNose(), None, tmp_path,
                        "http://127.0.0.1:4672", "test-secret", fetch_board=lambda: [])
    room.looks_dir.mkdir(parents=True)
    (room.looks_dir / "look-1.json").write_text(json.dumps({"token": world.raw["id"], "eligible": [2, 4], "brain_id": room.brain_id}))
    room._events_result = {"events": events}
    room.spawn = lambda *args: None
    room.poll_events()
    assert observed == [[2, 4]]
    assert ("dopamine", (1 if side == outcome else -1, 1.0)) in mb.log
    assert mb.log[0][0] == mb.log[-1][0] == "forget_trace"
    room._events_result = {"events": events}
    room.poll_events()
    assert observed == [[2, 4]]
    assert betbook.rebuild(led.path).state() == led.book.state()


def test_closed_without_binary_resolution_waits(setup):
    world, led, ex = setup
    ex.intent(world.body())
    world.raw["closed"] = True
    assert ex.resolve_once() == []
    assert len(led.book.positions) == 1


def test_full_paper_balance_has_no_minimum_order_size(setup):
    world, led, ex = setup
    world.raw["orderMinSize"] = 1000000000
    assert ex.intent(world.body(0.0001))[1]["status"] == "booked"
    assert led.book.balance_cents == 9999


def test_live_flag_stops_before_creating_state(tmp_path):
    env = dict(os.environ, FLY_BETROOM_LIVE="1", FLY_STATE_DIR=str(tmp_path))
    result = subprocess.run([sys.executable, "bookie.py"], env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert bookie.LIVE_REFUSAL in result.stderr
    assert not (tmp_path / "betroom").exists()


def test_board_builds_six_current_slugs_and_leaves_missing_slots_empty():
    now = fixture("provenance")["captured_at"] + 350
    calls = []
    expected = ["btc-updown-5m-1789263300", "eth-updown-5m-1789263300",
                "btc-updown-15m-1789263000", "eth-updown-15m-1789263000",
                "sol-updown-15m-1789263000", "xrp-updown-15m-1789263000"]
    def fetch(url):
        q = parse_qs(urlparse(url).query)
        calls.append(q)
        slug = q["slug"][0]
        return [{**fixture("gamma_btc")[0], "slug": slug, "id": str(expected.index(slug) + 1)}]
    cards = polymarket.Markets(fetch, lambda: now).board()
    assert [q["slug"][0] for q in calls] == expected
    assert [c["slug"] for c in cards] == expected
    assert [c["slot"] for c in cards] == list(range(6))
    assert all(c["shelf"] == "fast" for c in cards)
    missing = polymarket.Markets(lambda url: [] if expected[1] in url else fetch(url), lambda: now).board()
    assert [c["slot"] for c in missing] == [0, 2, 3, 4, 5]
    assert polymarket.Markets(lambda url: [], lambda: now).board() == []


def test_binary_rejects_negative_risk_and_other_shapes():
    raw = fixture("gamma_btc")[0]
    for changes in ({"negRisk": True}, {"events": [{"negRisk": True}]}, {"outcomes": '["Up","Down","Flat"]'},
                    {"clobTokenIds": '["1","1"]'}, {"outcomePrices": '["NaN","0"]'}):
        with pytest.raises(ValueError):
            polymarket.binary({**raw, **changes}, fast=True)


def test_recorded_resolution_pays_the_no_position(setup):
    world, led, ex = setup
    resolved = fixture("gamma_resolved")[0]
    world.raw = {**resolved, "closed": False, "active": True,
                 "endDate": "2099-01-01T00:00:00Z", "outcomePrices": '["0.5","0.5"]'}
    fill = ex.intent(world.body(-0.5))[1]["event"]
    world.raw = resolved
    events = ex.resolve_once()
    assert events[0]["outcome"] == "NO"
    assert led.book.balance_cents == 5000 + math.floor(Fraction(fill["shares"]) * 100)


def test_append_is_durable_before_balance_changes(setup, monkeypatch):
    world, led, ex = setup
    observed = []
    real = os.fsync
    def sync(fd):
        observed.append((led.book.balance_cents, [json.loads(line)["kind"] for line in led.path.read_text().splitlines()]))
        real(fd)
    monkeypatch.setattr(os, "fsync", sync)
    ex.intent(world.body())
    assert observed[-1] == (10000, ["open", "intent", "fill"])
    assert led.book.balance_cents == 5000


def test_wrong_fill_cannot_enter_the_ledger(setup):
    world, led, ex = setup
    i = led.intent(world.body())
    before = led.path.read_bytes()
    with pytest.raises(betbook.LedgerError):
        led.terminal("fill", i, stake_cents="9000", price="1/2", shares="180", question="bad")
    assert led.path.read_bytes() == before


def test_settlement_cannot_point_to_another_look(setup):
    world, led, ex = setup
    ex.intent(world.body())
    world.raw.update(closed=True, outcomePrices='["1","0"]')
    ex.resolve_once()
    entries = [json.loads(line) for line in led.path.read_text().splitlines()]
    entries[-1]["look_id"] = "some-other-card"
    book = betbook.Book()
    for entry in entries[:-1]:
        book.apply(entry)
    with pytest.raises(betbook.LedgerError, match="differs"):
        book.apply(entries[-1])


def test_only_last_fifty_settlements_are_published(setup):
    world, led, ex = setup
    for i in range(55):
        world.raw.update(closed=False, outcomePrices='["0.5","0.5"]')
        assert ex.intent(world.body(0.001, look=f"look-{i}"))[1]["status"] == "booked"
        world.raw.update(closed=True, outcomePrices='["1","0"]')
        ex.resolve_once()
    public = led.book.public()
    assert len(public["settled_bets"]) == 50
    assert public["settled_bets"][0]["look_id"] == "look-5"
    assert public["win_count"] == 55


def test_http_header_body_and_paper_health(setup):
    import threading
    from betroom import LoopbackHttp
    world, led, ex = setup
    server = bookie.make_server(ex, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    client = LoopbackHttp()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        assert server.server_address[0] == "127.0.0.1"
        code, health = client.get_json(url + "/health")
        assert code == 200 and health["mode"] == "paper" and health["balance"] == 100
        assert client.post_json(url + "/intent", world.body())[0] == 403
        headers = {"X-Fly-Intent": "test-secret"}
        assert client.post_json(url + "/intent", {**world.body(), "stake": 1}, headers)[0] == 400
        assert client.post_json(url + "/intent", world.body(), headers)[1]["status"] == "booked"
        assert client.get_json(url + "/events?after=0", headers)[1]["events"][0]["kind"] == "fill"
        assert client.post_json(url + "/bet", world.body(), headers)[0] == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


@pytest.mark.parametrize("drive", [1.0, -1.0])
@pytest.mark.parametrize("mid,sign", [("0.9", 1), ("0.01", -1), (None, 0)])
def test_sell_closes_whole_position_and_teaches_original_buy(setup, tmp_path, drive, mid, sign):
    import betroom
    from test_betroom import FakeBrain, FakeMB, FakePilot, FakeNose
    world, led, ex = setup
    buy = ex.intent(world.body(drive))[1]["event"]
    assert led.book.balance_cents == 0
    if mid is not None:
        world.mid = {"mid": mid}
    result = ex.intent(world.body(-drive / 2, look="sell-look"))[1]
    assert result["status"] == "booked"
    fill = result["event"]
    assert parse_qs(urlparse(world.calls[-1]).query)["token_id"] == [buy["token_id"]]
    payout = math.floor(Fraction(buy["shares"]) * Fraction(world.mid["mid"]) * 100)
    assert int(fill["pnl_cents"]) == payout - 10000
    assert led.book.balance_cents == payout
    assert not led.book.positions
    assert [json.loads(s)["kind"] for s in led.path.read_text().splitlines()][-3:] == ["intent", "fill", "dopamine"]
    sold = led.book.public()["settled_bets"][0]
    assert (sold["kind"], sold["look_id"], sold["pnl"], sold["exit_price"]) == (
        "sold", "look-1", (payout - 10000) / 100, float(Fraction(world.mid["mid"])))
    fb = FakeBrain()
    mb = FakeMB(fb)
    room = betroom.Room(fb, FakePilot(), mb, FakeNose(), None, tmp_path,
                        "http://127.0.0.1:4672", "secret", fetch_board=lambda: [], spawn=lambda *args: None)
    room.looks_dir.mkdir(parents=True)
    for name, cells in (("look-1", [2, 4]), ("sell-look", [1, 3])):
        (room.looks_dir / (name + ".json")).write_text(json.dumps(
            {"token": world.raw["id"], "eligible": cells, "brain_id": room.brain_id}), encoding="utf-8")
    observed = []
    mb.observe = lambda cells: observed.append(list(cells))
    room.refs = {world.raw["id"]: ["look-1", "sell-look"]}
    room._events_result = {"events": led.book.events}
    room.poll_events()
    assert observed == ([[2, 4]] if sign else [])
    assert [v for k, v in mb.log if k == "dopamine"] == ([(sign, 1.0)] if sign else [])
    assert not room.refs
    room._events_result = {"events": led.book.events}
    room.poll_events()
    assert observed == ([[2, 4]] if sign else [])
    world.raw.update(closed=True, outcomePrices='["1","0"]')
    assert ex.resolve_once() == []
    assert betbook.rebuild(led.path).state() == led.book.state()


def test_restart_records_missing_sell_dopamine(setup, monkeypatch):
    world, led, ex = setup
    ex.intent(world.body())
    monkeypatch.setattr(led, "teach_sell", lambda fill: None)
    ex.intent(world.body(-0.5, look="sell-look"))
    again = betbook.Ledger(led.path)
    assert [e["kind"] for e in again.book.events][-2:] == ["fill", "dopamine"]
    assert again.book.events[-1]["look_id"] == "look-1"
    assert betbook.Ledger(led.path).book.state() == again.book.state()


@pytest.mark.parametrize("change", [{"buy_look_id": "wrong"}, {"payout_cents": "999999"},
                                   {"held_token_id": "wrong"}, {"pnl_cents": "999999"}])
def test_sell_replay_rejects_wrong_position_or_arithmetic(setup, change):
    world, led, ex = setup
    ex.intent(world.body())
    ex.intent(world.body(-0.5, look="sell-look"))
    entries = [json.loads(line) for line in led.path.read_text().splitlines()]
    book = betbook.Book()
    for entry in entries[:-2]:
        book.apply(entry)
    with pytest.raises(betbook.LedgerError):
        book.apply({**entries[-2], **change})


def test_unquotable_sell_keeps_position_for_resolver(setup):
    world, led, ex = setup
    ex.intent(world.body())
    before = led.book.balance_cents
    world.mid = {"mid": "NaN"}
    assert ex.intent(world.body(-0.5, look="sell-look"))[1]["status"] == "refused"
    assert led.book.balance_cents == before and len(led.book.positions) == 1
    world.raw.update(closed=True, outcomePrices='["1","0"]')
    assert len(ex.resolve_once()) == 1


def test_board_drops_old_window_when_next_is_not_indexed():
    calls = []
    def fetch(url):
        calls.append(parse_qs(urlparse(url).query)["slug"][0])
        return fixture("gamma_btc")
    cards = polymarket.Markets(fetch, lambda: 1789263900).board()
    assert cards == []
    assert calls == ["btc-updown-5m-1789263900", "eth-updown-5m-1789263900",
                     "btc-updown-15m-1789263900", "eth-updown-15m-1789263900",
                     "sol-updown-15m-1789263900", "xrp-updown-15m-1789263900"]
