"""Quiet outages and held cards keep the room's record honest."""
import json

import pytest

import betroom
from test_rooms import make_room, registry
from test_betroom import IMG, RECTS


@pytest.mark.parametrize("failure", [OSError("connection refused"), (503, {}), (200, {"ok": False})])
def test_events_backoff_and_transition_logs(tmp_path, capsys, failure):
    class Http:
        down = True
        calls = 0

        def get_json(self, url, **kwargs):
            if url.endswith("/health"):
                self.calls += 1
                if self.down:
                    if isinstance(failure, Exception):
                        raise failure
                    return failure
                return 200, {"ok": True}
            return 200, {"events": []}

    http = Http()
    room = make_room(betroom.Room, tmp_path, fetch_board=lambda: [], http=http)
    now = [100.0]
    room.clock = lambda: now[0]
    room.poll_events()
    assert http.calls == 1
    for delay in (30, 60, 120, 120):
        assert room._events_delay == delay
        before = http.calls
        now[0] += delay - 1
        room.poll_events()
        assert http.calls == before
        now[0] += 1
        room.poll_events()
        assert http.calls == before + 1
    assert capsys.readouterr().out.count("events unavailable:") == 1
    assert registry().healthy(http) == []
    http.down = False
    now[0] += 120
    room.poll_events()
    assert room.bookie_status["ok"] and room._events_delay == 2
    assert capsys.readouterr().out.splitlines() == ["[betroom] events recovered"]
    before = http.calls
    now[0] += 1
    room.poll_events()
    assert http.calls == before
    now[0] += 1
    room.poll_events()
    assert http.calls == before + 1
    assert capsys.readouterr().out == ""
    assert len(registry().healthy(http)) == 2


@pytest.mark.parametrize("held_side,drive", [("YES", 0.5), ("NO", -0.5)])
def test_held_market_records_look_allows_sale_and_reopens(tmp_path, held_side, drive):
    room = make_room(betroom.Room, tmp_path, fetch_board=lambda: [])
    room.spawn = lambda *args: None
    room.meta["111"] = {"question": "Will it rain?", "token_ids": ["1111", "1112"]}
    room.public.parent.mkdir(parents=True)
    room.public.write_text(json.dumps({"open_bets": [
        {"market_id": "111", "side": held_side, "look_id": "held"}]}), encoding="utf-8")
    room.refs["111"] = ["held"]
    dwell = room._advance_dwell(RECTS[0])
    dwell["steps"] = 2
    room._commit(IMG, 100, 100, 1, RECTS[0], dwell, drive, None)
    assert room._intent is None and room.counters["intents"] == 0
    assert len(list(room.looks_dir.glob("*.json"))) == 1
    room._commit(IMG, 100, 100, 2, RECTS[0], dwell, -drive, None)
    assert room._intent["body"]["side"] != held_side
    assert room.counters["intents"] == 1
    room._intent = None
    room.refs["111"] = ["held"]
    room.public.write_text('{"open_bets": []}', encoding="utf-8")
    room._apply_event({"kind": "settled", "seq": 1, "market_id": "111", "look_id": "held",
                       "side": held_side, "outcome": held_side})
    room._commit(IMG, 100, 100, 3, RECTS[0], dwell, drive, None)
    assert room._intent["body"]["side"] == held_side
    assert room.counters["intents"] == 2
