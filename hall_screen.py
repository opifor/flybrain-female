"""A fixture walk through real loopback doors and the rendered hall page.

The motor trace is supplied by this fixture. This checks the room wiring,
not the female brain's room preference. betroom_screen.py checks that brain.
"""
import argparse
import asyncio
import io
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

import betbook
import betroom
import bookie
import hall
from envcfg import load_env
from roomkit import Registry, make_server
from tipper import Ledger, Tipper
from tiproom import wallets, DECLARATION as TIP_DECLARATION
from test_betroom import FakeBrain, FakeMB, FakeNose

ROOT = Path(__file__).parent


class FixturePilot:
    def step(self, img, cx, cy, **kwargs):
        seed = kwargs["seed"]
        return 0, 0, seed == 3, {"stop": 400 if seed == 3 else 0}, {
            "fired": np.array([2, 4] if seed == 1 else [1, 3])}


async def session(args):
    token = secrets.token_hex(32)
    state = args.state_dir
    ledger = betbook.Ledger(betbook.paths(state)["ledger"])
    bet = bookie.Bookie(None, ledger, token)
    tip = Tipper(Ledger(state), token)
    servers = [make_server(bet, 0), make_server(tip, 0)]
    workers = []
    registry = Registry()
    for declaration, server in zip((betroom.DECLARATION, TIP_DECLARATION), servers):
        registry.register(declaration, f"http://127.0.0.1:{server.server_address[1]}")
    fb = FakeBrain()
    room = hall.Hall(fb, FixturePilot(), FakeMB(fb), FakeNose(), None, state,
                     f"http://127.0.0.1:{servers[0].server_address[1]}", token,
                     registry=registry, spawn=lambda fn, *a: fn(*a))

    class PageHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/hall/board.json":
                room.refresh_board(force=True)
                body, kind = json.dumps(room.board()).encode(), "application/json"
            elif self.path == "/hall/public.json":
                body, kind = json.dumps(room.state()).encode(), "application/json"
            elif self.path == "/tiproom/board.json":
                body, kind = json.dumps({"cards": wallets()}).encode(), "application/json"
            elif self.path == "/betroom/board.json":
                body = args.bet_board.read_bytes() if args.bet_board else b"[]"
                rows = json.loads(body)
                body, kind = json.dumps({"cards": rows}).encode(), "application/json"
            elif self.path == "/betroom/public.json":
                body, kind = json.dumps(ledger.book.public()).encode(), "application/json"
            elif self.path in ("/hall", "/tiproom", "/betroom"):
                body, kind = (ROOT / "web" / (self.path[1:] + ".html")).read_bytes(), "text/html"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    web = ThreadingHTTPServer(("127.0.0.1", 0), PageHandler)
    servers.append(web)
    for server in servers:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        workers.append(worker)
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                origin = f"http://127.0.0.1:{web.server_address[1]}"
                await page.goto(origin + "/hall")
                await page.wait_for_function("document.querySelectorAll('[data-token]').length === 2")
                await room.enter(page)
                rects = await room._rects(page)
                assert len(rects) == 2
                raw = await page.screenshot(path=str(args.screenshot_prefix) + "-hall.png")
                img = np.asarray(Image.open(io.BytesIO(raw)).convert("L"), dtype=np.float32) / 255
                for seed, rect in enumerate((rects[1], rects[0], rects[0]), 1):
                    await room.step(page, img, rect["x"] + rect["w"] / 2, rect["y"] + rect["h"] / 2, seed)
                    if seed < 3:
                        assert room.destination is None
                assert room.destination == "/betroom"
                await page.goto(origin + room.destination)
                assert page.url == origin + "/betroom"
                room.record_entry(room.destination)
                public = json.loads(room.public.read_text(encoding="utf-8"))
                assert public["events"][-1]["text"] == "entered the betting room"
                if args.bet_board:
                    rows = json.loads(args.bet_board.read_text(encoding="utf-8"))
                    snapshot_time = min(c["end_at"] for c in rows) - 60
                    await page.evaluate("at => { Date.now = () => at * 1000; draw(); }", snapshot_time)
                    await page.wait_for_function("document.querySelectorAll('[data-token]:not([data-token=\"\"])').length > 0")
                    await page.screenshot(path=str(args.screenshot_prefix) + "-betroom.png")
                await page.goto(origin + "/tiproom")
                await page.wait_for_function("document.querySelectorAll('[data-token]').length === 8")
                await page.screenshot(path=str(args.screenshot_prefix) + "-tiproom.png")
                assert not (state / "hall" / "ledger.paper.jsonl").exists()
                result = {"doors": len(rects), "steps": 3, "event": public["events"][-1],
                          "fixture": "motor trace; two real paper executor health endpoints"}
                (state / "hall-session.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
                print(json.dumps(result))
            finally:
                await browser.close()
    finally:
        for server, worker in zip(servers, workers):
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
    return 0


def main():
    settings = load_env()
    if settings.get("FLY_BETROOM_LIVE") == "1":
        raise SystemExit(bookie.LIVE_REFUSAL)
    if settings.get("FLY_TIPROOM_LIVE") == "1":
        raise SystemExit("live tipping is not built; this build is paper only")
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--screenshot-prefix", type=Path, required=True)
    parser.add_argument("--bet-board", type=Path)
    return asyncio.run(session(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
