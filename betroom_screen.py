"""An offline page with live public quotes and the real female brain.

The fixture presents card centres in turn, as the upstream offline screen
does. It does not move the cursor from motor output. Stops, relative drive,
side and size still come from the ordinary pilot, room and bookie. This is a
wiring check, not evidence of autonomous browsing or predictive skill.
"""
import argparse
import asyncio
import json
import os
import secrets
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import betbook
import betroom
import bookie
import calibration
from flyeye import FlyPilot
from flysim import FlyBrain, load_gains
from mushroom import MushroomBody
from olfaction import Nose
from polymarket import Markets


class Page:
    def __init__(self, cards):
        self.rects = []
        counts = {"fast": 0, "slow": 0}
        canvas = Image.new("RGB", (1280, 800), "#0b0c0e")
        draw = ImageDraw.Draw(canvas)
        for card in cards:
            shelf = card["shelf"]
            n = counts[shelf]
            counts[shelf] += 1
            x = 56 + (n % 4) * 294
            y = (80 if shelf == "fast" else 280) + (n // 4) * 174
            self.rects.append({"token": card["market_id"], "held": False,
                               "x": x, "y": y, "w": 280, "h": 160})
            draw.rounded_rectangle((x, y, x + 279, y + 159), radius=12, fill="#181b20", outline="#aaaaaa", width=3)
            draw.rectangle((x + 14, y + 16, x + 32, y + 66), fill="#b99bd9" if shelf == "fast" else "#c4b28e")
            draw.text((x + 44, y + 16), card["question"][:32], fill="#e9edf3")
            draw.rectangle((x + 14, y + 94, x + 264, y + 110), fill="#2b3038")
            draw.rectangle((x + 14, y + 94, x + 14 + int(250 * card["yes_price"]), y + 110), fill="#9aa7b8")
        self.image = np.asarray(canvas.convert("L"), dtype=np.float32) / 255.0

    async def evaluate(self, js):
        return self.rects


async def session(args):
    markets = Markets()
    cards = markets.board()
    if len(cards) < 2:
        raise RuntimeError("fewer than two public markets; no relative reading is possible")
    state = args.state_dir
    state.mkdir(parents=True, exist_ok=True)
    (state / "board.json").write_text(json.dumps(cards, indent=1), encoding="utf-8")
    print(f"Gamma board: {len(cards)} cards", flush=True)
    fb = FlyBrain(args.graph)
    motor, tag = load_gains(fb, roam=True)
    odor = calibration.gains_for(fb, calibration.CHOSEN)
    gains = odor if motor is None else motor * odor
    mb = MushroomBody(fb, store=state / "betroom" / "mb_gains_dry.npz")
    pilot = FlyPilot(fb, sim_steps=60)
    nose = Nose(fb, equal_sniff=2.0)
    nose.max_hz = calibration.SETTINGS[calibration.CHOSEN]["odour_max_hz"]
    token = secrets.token_hex(32)
    led = betbook.Ledger(betbook.paths(state)["ledger"])
    ex = bookie.Bookie(markets, led, token)
    server = bookie.make_server(ex, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    room = betroom.Room(fb, pilot, mb, nose, gains, state,
                        f"http://127.0.0.1:{server.server_address[1]}", token,
                        fetch_board=lambda: cards)
    page = Page(cards)
    try:
        await room.enter(page)
        for step in range(args.steps):
            rect = page.rects[(step // 8) % len(page.rects)]
            x, y = rect["x"] + 140, rect["y"] + 80
            result = await room.step(page, page.image, x, y, step + 1)
            if step % 8 == 0 or result[2]:
                print(json.dumps({"step": step + 1, "stop": bool(result[2]), **room.state()}), flush=True)
            room.poll_events()
        if room._intent:
            deadline = time.monotonic() + 45
            while not room._intent.get("done") and time.monotonic() < deadline:
                await asyncio.sleep(0.1)
        print(json.dumps({"steps": args.steps, "open_bets": led.book.public()["open_bets"],
                          "refusals": led.book.refusals}), flush=True)
        if led.book.positions:
            return 0
        print("No fill in this session. The room did not invent a stop or a drive.", flush=True)
        return 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def main():
    if os.environ.get("FLY_BETROOM_LIVE") == "1":
        raise SystemExit(bookie.LIVE_REFUSAL)
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=Path("build/graph_female.npz"))
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=400)
    return asyncio.run(session(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
