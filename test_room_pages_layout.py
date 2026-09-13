"""The cards and live line leave the hall door clear."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time

import pytest
from playwright.sync_api import sync_playwright, expect


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


@pytest.mark.parametrize("room", ["betroom", "musicroom", "hall"])
def test_room_screen_bands(room_origin, room, tmp_path):
    cards = [dict(token=f"card-{i}", name=f"Track {i}", artist="River", license="CC BY 3.0",
                  duration=60, market_id=f"card-{i}", slot=i, shelf="fast", question=f"Question {i}?",
                  end_at=time.time() + 900, yes_price=0.5, category="other",
                  room={"commit_means": "enter the room"}) for i in range(2 if room == "hall" else 6)]
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
        if room == "betroom":
            assert boxes == [dict(x=56 + i % 3 * 400, y=48 + i // 3 * 328, w=368, h=320) for i in range(6)]
        if room != "hall":
            expect(page.locator("#door")).to_be_visible()
            assert page.locator("#door").bounding_box() == {"x": 56, "y": 760, "width": 1168, "height": 40}
            overlaps = page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => {
                if (e.id === 'door' || e.contains(document.querySelector('#door'))) return false;
                const r = e.getBoundingClientRect(), s = getComputedStyle(e);
                return s.visibility !== 'hidden' && r.width > 0 && r.height > 0 &&
                    r.top < 800 && r.bottom > 760 && r.left < 1224 && r.right > 56;
            }).map(e => e.tagName + '#' + e.id)""")
            assert overlaps == []
        if room == "musicroom":
            expect(page.locator("#status")).to_have_text("now playing: nothing")
            expect(page.locator("#status audio")).to_be_hidden()
            assert page.locator("audio").evaluate("a => !a.controls")
            page.route("**/public.json", lambda route: route.fulfill(json={"now_playing": {
                "track_id": "card-0", "title": "<b>Rain</b>", "started_at": time.time(), "duration": 60}}))
            page.route("**/track/*", lambda route: route.fulfill(status=404))
            expect(page.locator("#status")).to_have_text("now playing: <b>Rain</b> · River · CC BY 3.0")
            assert page.locator("#status b").count() == 0
        if room == "hall":
            expect(page.locator("#status")).to_have_text("door order: Track 0 · Track 1")
        page.screenshot(path=str(tmp_path / f"{room}.png"))
        browser.close()
