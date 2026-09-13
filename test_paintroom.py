"""Marks survive restarts, refusals and the two-hour canvas clock."""
import asyncio
import builtins
import io
import json
import random
import subprocess
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

import painter
import paintroom
import room
from life import Life
from roomkit import make_server
from test_betroom import FakeBrain, FakeMB, FakeNose, FakePilot


def make_room(tmp_path, now):
    brain = FakeBrain()
    return paintroom.Room(brain, FakePilot(), FakeMB(brain), FakeNose(), None, tmp_path,
                          "http://127.0.0.1:4676", "fixture", clock=lambda: now[0],
                          spawn=lambda fn, *args: fn(*args))


def body(now, card="rose", look="one", **fields):
    return dict(card_id=card, look_id=look, seen_at=now[0], drive=.2, x=400, y=300, size=20, **fields)


def test_board_shuffle_position_and_rects(tmp_path):
    now = [1700000000.0]
    walk = make_room(tmp_path, now)
    walk.refresh_board(force=True)
    first = walk.board()
    names = list(paintroom.COLOURS) + list(paintroom.BRUSHES)
    random.Random(0).shuffle(names)
    assert [c["token"] for c in first["cards"]] == names
    assert len(first["cards"]) == 12
    assert not walk.refresh_board()
    now[0] += 60
    assert walk.refresh_board()
    assert walk.board()["order_seed"] == 1
    assert walk.board()["cards"] != first["cards"]
    rects = [dict(token=c["token"], x=56+296*(i % 4), y=48+216*(i // 4), w=280, h=200)
             for i, c in enumerate(walk.board()["cards"])]
    walk._last_rects = rects
    assert walk.state()["rects"] == {r["token"]: {k: r[k] for k in ("x", "y", "w", "h")} for r in rects}
    with patch.object(room.Room, "_commit"):
        walk._commit(None, 411, 312, 0, {"token": "rose", "x": 56, "y": 48}, {"steps": 9}, .2, None)
    assert walk.intent_body("rose", .2, now[0], "position") == dict(
        card_id="rose", drive=.2, seen_at=now[0], look_id="position", x=411, y=312, size=26)
    for steps, size in ((2, 12), (3, 14), (16, 40), (30, 40)):
        with patch.object(room.Room, "_commit"):
            walk._commit(None, 411, 312, 0, {}, {"steps": steps}, .2, None)
        assert walk.mark_position[2] == size


def test_marks_rest_refusals_and_replay(tmp_path):
    now = [1700000000.0]
    clock = lambda: now[0]
    ex = painter.Painter(painter.Ledger(tmp_path, clock), "fixture", clock)
    assert ex.intent(body(now))[1]["status"] == "booked"
    canvas = tmp_path / "paintroom/canvas.png"
    assert Image.open(canvas).getpixel((400, 300)) == (255, 121, 176)
    assert Image.open(canvas).getpixel((56, 48)) == (0, 0, 0)
    assert ex.intent(body(now))[0] == 409
    assert ex.intent(body(now, "ring", "ring"))[1]["event"]["colour"] == "rose"
    assert ex.intent(body(now, "white", "white"))[1]["event"]["brush"] == "ring"
    before = canvas.read_bytes()
    assert ex.intent(body(now, "rest", "rest"))[1]["status"] == "booked"
    assert canvas.read_bytes() == before
    public = ex.ledger.book.public()
    assert public["marks"] == 3 and public["rests"] == 1
    assert public["colour_distribution"] == {"rose": 2, "white": 1}
    for field, value, status in (("card_id", "bad", 400), ("x", -1, 400), ("y", 620, 400),
                                 ("size", 11, 400), ("size", 41, 400), ("size", float("nan"), 400), ("x", True, 400)):
        ask = body(now, look="invalid")
        ask[field] = value
        assert ex.intent(ask)[0] == status
    for i, changes in enumerate(({"seen_at": now[0] - 21}, {"seen_at": now[0] + 1}, {"drive": 0}, {"drive": 2})):
        ask = {**body(now, look=f"refuse{i}"), **changes}
        assert ex.intent(ask)[1]["status"] == "refused"
    assert all(e["kind"] == "fill" for e in ex.events()[1]["events"])
    assert len(ex.events()[1]["events"]) == 4
    strokes = [json.loads(line) for line in (canvas.parent / "strokes.jsonl").read_text().splitlines()]
    assert len(strokes) == 3 and set(strokes[0]) == {"at", "colour", "brush", "x", "y", "size", "look_id"}
    recovered = painter.Ledger(tmp_path, clock)
    assert recovered.ok and recovered.book.public() == ex.ledger.book.public()
    assert canvas.read_bytes() == before


def test_rotation_and_gallery_survive_restart(tmp_path):
    now = [1700000000.0]
    clock = lambda: now[0]
    ex = painter.Painter(painter.Ledger(tmp_path, clock), "fixture", clock)
    ex.intent(body(now))
    before = (tmp_path / "paintroom/canvas.png").read_bytes()
    now[0] += 7199
    ex.resolve_once()
    assert ex.ledger.book.public()["gallery"] == []
    now[0] += 1
    ex.resolve_once()
    public = ex.ledger.book.public()
    assert public["canvas_marks"] == 0 and public["coverage_percent"] == 0
    assert public["gallery"] == [dict(file="2023-11-14-2213.png", marks=1, dominant_colour="rose")]
    assert (tmp_path / "paintroom/gallery" / public["gallery"][0]["file"]).read_bytes() == before
    assert Image.open(tmp_path / "paintroom/canvas.png").getbbox() is None
    assert painter.Ledger(tmp_path, clock).book.public() == public
    now[0] += 14400
    ex.resolve_once()
    assert len(ex.ledger.book.public()["gallery"]) == 3


def test_minimal_png_and_coverage():
    pixels, coverage = painter.raster([dict(colour="rose", brush="dot", x=10, y=10, size=12)])
    assert coverage == 113 * 100 / (1280 * 620)
    original = builtins.__import__
    def without_pillow(name, *args, **kwargs):
        if name == "PIL":
            raise ImportError("fixture")
        return original(name, *args, **kwargs)
    with patch("builtins.__import__", without_pillow):
        raw = painter.png(pixels)
    image = Image.open(io.BytesIO(raw))
    assert image.size == (1280, 620) and image.getpixel((10, 10)) == (255, 121, 176)


def test_corruption_fails_closed(tmp_path):
    led = painter.Ledger(tmp_path, lambda: 1700000000)
    with led.path.open("a", encoding="utf-8") as stream:
        stream.write("broken\n")
    ex = painter.Painter(painter.Ledger(tmp_path, lambda: 1700000000), "fixture")
    assert ex.intent(body([1700000000]))[0] == 503


def test_life_paint_lines_are_once_and_under_limit(tmp_path):
    now = 1700000000
    life = Life(tmp_path)
    state = dict(rooms={"/paintroom": {"book": dict(opened_at=now, strokes=[
        dict(at=now, look_id="one", colour="ice blue", brush="stroke")])}})
    result = life.observe(state, now)
    assert {r["text"] for r in result["feed"] if r["kind"].startswith("paint.")} == {
        "a new canvas opened", "she painted ice blue stroke"}
    again = life.observe(state, now + 1)
    assert len([r for r in again["feed"] if r["kind"].startswith("paint.")]) == 2
    assert all(len(r["text"]) <= 48 for r in again["feed"])


def test_http_auth_and_fill_only_feed(tmp_path):
    now = [1700000000.0]
    ex = painter.Painter(painter.Ledger(tmp_path, lambda: now[0]), "fixture", lambda: now[0])
    server = make_server(ex, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        http = room.LoopbackHttp()
        url = f"http://127.0.0.1:{server.server_port}"
        assert http.post_json(url + '/intent', body(now))[0] == 403
        assert http.post_json(url + '/intent', body(now), headers={'X-Fly-Intent': 'fixture'})[1]['status'] == 'booked'
        assert http.get_json(url + '/events', headers={'X-Fly-Intent': 'fixture'})[1]['events'][0]['kind'] == 'fill'
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def test_room_time_and_no_reward(tmp_path):
    now = [1700000000.0]
    walk = make_room(tmp_path, now)
    asyncio.run(walk.enter(None))
    now[0] += 30
    assert walk.state()['time_in_room'] == 30
    walk.leave()
    now[0] += 30
    assert walk.state()['time_in_room'] == 30
    assert make_room(tmp_path, now).state()['time_in_room'] == 30
    walk._apply_event(dict(kind='dopamine', sign=1))
    assert walk.counters['sugar'] == 0


def test_paint_relay_storage_and_auth():
    result = subprocess.run(['node', str(Path(__file__).with_name('test_paint_relay.mjs'))],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '3 passed' in result.stdout


def test_changed_canvas_publication(tmp_path, monkeypatch):
    import paint_publish
    painter.Ledger(tmp_path, lambda: 1700000000)
    calls = []
    class Reply:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    def send(request, timeout):
        calls.append(request)
        return Reply()
    monkeypatch.setattr(paint_publish.urllib.request, 'urlopen', send)
    monkeypatch.setattr(paint_publish, '_sent', {})
    paint_publish.publish(tmp_path / 'paintroom', 'https://fixture.test', 'fixture')
    paint_publish.publish(tmp_path / 'paintroom', 'https://fixture.test', 'fixture')
    assert len(calls) == 1 and calls[0].full_url == 'https://fixture.test/paintroom/canvas.png'
    assert calls[0].get_header('Authorization') == 'Bearer fixture'
    assert calls[0].data.startswith(b'\x89PNG')


def test_site_canvas_and_gallery(tmp_path):
    from playwright.sync_api import sync_playwright, expect
    from test_rooms_site import pages
    pages.generate(tmp_path / 'rooms')
    data = painter.png(painter.raster([])[0])
    state = dict(live=True, age=0, rooms={'/paintroom': {'book': dict(marks=2, rests=1,
        coverage_percent=.5, colour_distribution={'rose': 2}, last_seq=3, opened_at=1700000000,
        gallery=[dict(file='2023-11-14-2213.png', marks=2, dominant_colour='rose')])}})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        def respond(route):
            if route.request.url.endswith('/state'):
                route.fulfill(json=state)
            elif '/paintroom/' in route.request.url:
                route.fulfill(body=data, content_type='image/png')
            else:
                route.abort()
        page.route('**/*', respond)
        page.set_content((tmp_path / 'rooms/paint.html').read_text(encoding='utf-8'))
        expect(page.locator('img[alt="Her current canvas"]')).to_be_visible()
        expect(page.locator('[data-live="book"]')).to_contain_text('2 marks, 1 rests, 0.5% covered')
        expect(page.locator('a[href*="/paintroom/gallery/"]')).to_have_text('2023-11-14-2213.png: 2 marks, rose')
        browser.close()
