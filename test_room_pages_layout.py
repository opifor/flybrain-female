"""The cards and live line leave the hall door clear."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time

import pytest
from playwright.sync_api import sync_playwright, expect
from room import RECTS_JS


@pytest.fixture(scope="module")
def room_origin():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(
        SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "web")))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("room", ["betroom", "musicroom", "tiproom", "hall", "paintroom"])
def test_room_screen_bands(room_origin, room, tmp_path):
    cards = [dict(token=f"card-{i}", name=f"Track {i}", artist="River", license="CC BY 3.0",
                  path="/musicroom", preview=f"Preview {i}", duration=60, market_id=f"card-{i}", slot=i, shelf="fast", question=f"Question {i}?",
                  end_at=time.time() + 900, yes_price=0.5, category="other",
                  room={"commit_means": "enter the room"}) for i in range(12 if room in ("hall", "musicroom", "paintroom") else 6)]
    if room == "paintroom":
        import paintroom
        cards = [dict(token=name, name=name, colour=paintroom.COLOURS.get(name), room=paintroom.DECLARATION.public())
                 for name in list(paintroom.COLOURS) + list(paintroom.BRUSHES)]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.route("**/board.json", lambda route: route.fulfill(json={"cards": cards}))
        page.route("**/public.json", lambda route: route.fulfill(json={"now_playing": None}))
        page.goto(f"{room_origin}/{room}.html")
        expect(page.locator(".card:not(.empty)")).to_have_count(len(cards))
        expect(page.locator("#status")).to_be_visible()
        status = page.locator("#status").bounding_box()
        assert status == {"x": 56, "y": 700, "width": 1168, "height": 56}
        boxes = page.locator(".card").evaluate_all("nodes => nodes.map(n => {const r=n.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height};})")
        assert all(box["y"] + box["h"] <= 696 for box in boxes)
        assert all(box["x"] >= 56 and box["x"] + box["w"] <= 1224 and box["y"] >= 48 for box in boxes)
        if room == "betroom":
            assert boxes == [dict(x=56 + i % 3 * 400, y=48 + i // 3 * 328, w=368, h=320) for i in range(6)]
        if room == "paintroom":
            assert boxes == [dict(x=56 + i % 4 * 296, y=48 + i // 4 * 216, w=280, h=200) for i in range(12)]
            assert page.locator('#paint-canvas').bounding_box() == dict(x=0, y=0, width=1280, height=620)
            expect(page.locator('.swatch')).to_have_count(8)
            expect(page.locator('.name')).to_have_text([c['name'] for c in cards])
            assert page.locator('.card').evaluate_all('nodes => nodes.every(n => n.scrollHeight <= n.clientHeight)')
        if room != "hall":
            expected = [dict(x=0, y=0, w=1280, h=40), dict(x=0, y=760, w=1280, h=40),
                        dict(x=0, y=0, w=48, h=800), dict(x=1232, y=0, w=48, h=800)]
            expect(page.locator('.door[data-token="/hall"]')).to_have_count(4)
            doors = [r for r in page.evaluate(RECTS_JS) if r["token"] == "/hall"]
            assert doors == [dict(token="/hall", held=False, **box) for box in expected]
            for edge in ("top", "bottom", "left", "right"):
                expect(page.locator(f"#door-{edge}")).to_be_visible()
            for door in doors:
                for box in boxes + [dict(x=status["x"], y=status["y"], w=status["width"], h=status["height"])]:
                    assert (box["x"] + box["w"] <= door["x"] or door["x"] + door["w"] <= box["x"] or
                            box["y"] + box["h"] <= door["y"] or door["y"] + door["h"] <= box["y"])
        else:
            expect(page.locator(".door")).to_have_count(4)
            assert boxes == [dict(x=56 + i % 4 * 300, y=48 + i // 4 * 216, w=268, h=200) for i in range(12)]
            expect(page.locator(".detail")).to_have_text([f"Preview {i}" for i in range(12)])
        if room == "musicroom":
            expected_cards = [dict(x=56 + i % 4 * 296, y=48 + i // 4 * 216, w=280, h=200) for i in range(12)]
            assert boxes == expected_cards
            from test_musicroom import room_at
            music = room_at(tmp_path, [1700000000.0])
            music._last_rects = page.evaluate(RECTS_JS)
            assert {token: rect for token, rect in music.state()["rects"].items() if token != "/hall"} == {
                card["token"]: box for card, box in zip(cards, expected_cards)}
            for i, card in enumerate(cards):
                node = page.locator(".card").nth(i)
                expect(node.locator(".name")).to_have_text(card["name"])
                expect(node.locator(".detail")).to_have_text("River / CC BY 3.0 / 60 seconds")
                assert node.evaluate("n => n.scrollHeight <= n.clientHeight && n.scrollWidth <= n.clientWidth")
            expect(page.locator("#status")).to_have_text("now playing: nothing")
            expect(page.locator("#status audio")).to_be_hidden()
            assert page.locator("audio").evaluate("a => !a.controls")
            page.route("**/public.json", lambda route: route.fulfill(json={"now_playing": {
                "track_id": "card-0", "title": "<b>Rain</b>", "started_at": time.time(), "duration": 60}}))
            page.route("**/track/*", lambda route: route.fulfill(status=404))
            expect(page.locator("#status")).to_have_text("now playing: <b>Rain</b> · River · CC BY 3.0")
            assert page.locator("#status b").count() == 0
        if room == "hall":
            expect(page.locator("#status")).to_have_text("door order: " + " · ".join(f"Track {i}" for i in range(12)))
            from test_rooms import make_room, registry, Health
            import hall
            hallway = make_room(hall.Hall, tmp_path, registry=registry(), http=Health(), fetch_board=lambda: cards)
            hallway.refresh_board(force=True)
            hallway._last_rects = page.evaluate(RECTS_JS)
            assert hallway.state()['rects'] == {card['token']: box for card, box in zip(cards, boxes)}
            assert page.locator('.door').evaluate_all("nodes => nodes.map(n => {const r=n.getBoundingClientRect(); return [r.x,r.y,r.width,r.height];})") == [[0, 0, 1280, 40], [0, 760, 1280, 40], [0, 0, 48, 800], [1232, 0, 48, 800]]
        page.screenshot(path=str(tmp_path / f"{room}.png"))
        browser.close()
