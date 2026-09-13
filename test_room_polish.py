"""Quiet outages and held cards keep the room's record honest."""
import json

import pytest

import betroom
import room as room_module
import roam
from types import SimpleNamespace
from unittest.mock import Mock
from test_rooms import make_room, registry
from test_betroom import IMG, RECTS


def test_public_book_retries_and_limits_failure_logs(tmp_path, monkeypatch):
    room = make_room(betroom.Room, tmp_path, fetch_board=lambda: [])
    reader = Mock(side_effect=[PermissionError('locked'), '{"book": "ready"}'])
    room.public = SimpleNamespace(read_text=reader)
    sleep = Mock()
    monkeypatch.setattr(room_module.time, 'sleep', sleep)
    now = [0.0]
    monkeypatch.setattr(room_module.time, 'monotonic', lambda: now[0])
    room._say = Mock()
    assert room.read_book() == {'book': 'ready'}
    assert reader.call_count == 2
    sleep.assert_called_once_with(.05)
    room._say.assert_not_called()
    reader.side_effect = PermissionError('locked')
    sleep.reset_mock()
    assert room.read_book() == {}
    assert sleep.call_count == 3
    assert room._say.call_count == 1
    reader.side_effect = None
    reader.return_value = '{}'
    assert room.read_book() == {}
    reader.side_effect = PermissionError('locked')
    now[0] = 59.999
    assert room.read_book() == {}
    assert room._say.call_count == 1
    now[0] = 60
    assert room.read_book() == {}
    assert room._say.call_count == 2


@pytest.mark.parametrize('custom', [False, True])
def test_only_windows_proactor_connection_reset_is_quiet(monkeypatch, custom):
    from asyncio.proactor_events import _ProactorBasePipeTransport
    monkeypatch.setattr(roam.sys, 'platform', 'win32')
    previous = Mock() if custom else None
    loop = Mock()
    loop.get_exception_handler.return_value = previous
    roam.quiet_windows_pipe_resets(loop)
    handler = loop.set_exception_handler.call_args.args[0]
    error = ConnectionResetError('viewer gone')
    error.winerror = 10054
    callback = SimpleNamespace(__func__=_ProactorBasePipeTransport._call_connection_lost)
    context = dict(exception=error, handle=SimpleNamespace(_callback=callback))
    handler(loop, context)
    target = previous if custom else loop.default_exception_handler
    target.assert_not_called()
    for other in (dict(exception=error), {**context, 'exception': RuntimeError('broken')},
                  {**context, 'exception': ConnectionResetError('different reset')}):
        handler(loop, other)
        if custom:
            target.assert_called_with(loop, other)
        else:
            target.assert_called_with(other)
    assert target.call_count == 3
    monkeypatch.setattr(roam.sys, 'platform', 'linux')
    loop.reset_mock()
    roam.quiet_windows_pipe_resets(loop)
    loop.set_exception_handler.assert_not_called()


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
