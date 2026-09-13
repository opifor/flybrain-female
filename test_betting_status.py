from types import SimpleNamespace
from unittest.mock import patch

import betroom
import roam


def test_bookie_health_failure_clears_the_live_claim():
    replies = iter([(200, {"ok": True}), (200, {"events": [{"seq": 1}]}),
                    (200, {"ok": True, "publish_error": "disk full"}),
                    (200, {"events": []})])
    room = SimpleNamespace(http=SimpleNamespace(get_json=lambda *a, **k: next(replies)),
                           executor_url="http://127.0.0.1:4672", intent_token="fixture",
                           _now=lambda: 100, public_events=[], _say=lambda text: None)
    betroom.Room._events_worker(room, 0)
    assert room.bookie_status == {"at": 100, "ok": True}
    assert room.public_events == [{"seq": 1}]
    betroom.Room._events_worker(room, 1)
    assert room.bookie_status == {"at": 100, "ok": False}


def test_room_presence_and_health_are_separate():
    room = SimpleNamespace(in_room=False, bookie_status={"at": 100, "ok": True},
                           public_events=[], state=lambda: {"learning": {"last": []}})
    with patch.dict(roam.STATE, room=room):
        assert roam.betting_status() == {"in_room": False, "bookie": room.bookie_status,
                                          "events": [], "learning": {"last": []}}
    with patch.dict(roam.STATE, room=None):
        assert roam.betting_status()["bookie"]["ok"] is False
