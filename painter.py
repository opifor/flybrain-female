"""The paper painter keeps marks and opens a fresh canvas every two hours."""
from collections import Counter
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import threading
import time
import zlib

from envcfg import load_env
from paintroom import COLOURS, BRUSHES, DECLARATION
from roomkit import Executor, WriteAhead, LedgerError, atomic_write, exact_body, stale_look, make_server

WIDTH, HEIGHT, ROTATE_SECONDS = 1280, 620, 7200
FIELDS = {"card_id", "drive", "seen_at", "look_id", "x", "y", "size"}
SIZE_FLOOR, SIZE_FLOOR_EVER = 12, 6   # marks made under the old six-pixel rule stay valid on replay


def check_body(body, floor=SIZE_FLOOR):
    why = exact_body(body, FIELDS)
    if why:
        return why
    if not isinstance(body["card_id"], str) or body["card_id"] not in (*COLOURS, *BRUSHES):
        return "unknown card"
    for key, low, high in (("x", 0, WIDTH - 1), ("y", 0, HEIGHT - 1), ("size", floor, 40)):
        value = body[key]
        try:
            valid = type(value) in (int, float) and math.isfinite(value) and low <= value <= high
        except OverflowError:
            valid = False
        if not valid:
            return "invalid " + key


def raster(marks):
    pixels = bytearray(WIDTH * HEIGHT * 3)
    covered = set()
    for mark in marks:
        radius = mark["size"] / 2
        colour = bytes.fromhex(COLOURS[mark["colour"]][1:])
        for y in range(max(0, math.floor(mark["y"] - radius)), min(HEIGHT, math.ceil(mark["y"] + radius) + 1)):
            for x in range(max(0, math.floor(mark["x"] - radius)), min(WIDTH, math.ceil(mark["x"] + radius) + 1)):
                dx, dy = x - mark["x"], y - mark["y"]
                distance = dx * dx + dy * dy
                hit = (abs(dy) <= max(1, radius / 4) if mark["brush"] == "stroke" else
                       max(0, radius - 2) ** 2 <= distance <= radius ** 2 if mark["brush"] == "ring" else
                       distance <= radius ** 2)
                if hit:
                    index = y * WIDTH + x
                    pixels[index * 3:index * 3 + 3] = colour
                    covered.add(index)
    return pixels, len(covered) * 100 / (WIDTH * HEIGHT)


def png(pixels):
    try:
        from PIL import Image
    except ImportError:
        def chunk(kind, data):
            return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))
        rows = b"".join(b"\0" + pixels[y * WIDTH * 3:(y + 1) * WIDTH * 3] for y in range(HEIGHT))
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", WIDTH, HEIGHT, 8, 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    stream = io.BytesIO()
    Image.frombytes("RGB", (WIDTH, HEIGHT), bytes(pixels)).save(stream, format="PNG")
    return stream.getvalue()


class Book:
    def __init__(self):
        self.book_id = None
        self.balance_cents = self.seq = self.intents = 0
        self.look_ids, self.pending, self.events = set(), {}, []
        self.colour, self.brush = "rose", "dot"
        self.opened_at = None
        self.canvases, self.marks = [], []
        self.rests = 0

    def apply(self, e):
        try:
            self._apply(e)
        except (KeyError, TypeError, OverflowError) as exc:
            raise LedgerError(str(exc)) from exc

    def _apply(self, e):
        if e.get("mode") != "paper" or type(e["at"]) not in (int, float) or not math.isfinite(e["at"]):
            raise LedgerError("invalid paper entry")
        kind = e["kind"]
        if kind == "open":
            if self.book_id is not None:
                raise LedgerError("repeated opening")
            self.book_id, self.opened_at = str(e["at"]), e["at"]
            return
        if self.book_id is None:
            raise LedgerError("entry before opening")
        if kind == "rotate":
            if e["at"] != self.opened_at + ROTATE_SECONDS:
                raise LedgerError("invalid rotation")
            self.canvases.append((self.opened_at, self.marks))
            self.marks, self.opened_at = [], e["at"]
            return
        if kind == "intent":
            if check_body({k: e[k] for k in FIELDS}, SIZE_FLOOR_EVER) or e["id"] != self.intents + 1 or e["look_id"] in self.look_ids:
                raise LedgerError("invalid intent")
            self.intents = e["id"]
            self.look_ids.add(e["look_id"])
            self.pending[e["id"]] = e
            return
        ask = self.pending.get(e["id"])
        if ask is None or any(ask[k] != e[k] for k in FIELDS) or e["seq"] != self.seq + 1:
            raise LedgerError("outcome differs from intent")
        if kind == "fill":
            colour = e["card_id"] if e["card_id"] in COLOURS else self.colour
            brush = e["card_id"] if e["card_id"] in BRUSHES else self.brush
            if (stale_look(ask, e["at"]) or not 0 < abs(e["drive"]) <= 1 or
                    e["colour"] != colour or e["brush"] != brush):
                raise LedgerError("invalid mark")
            self.colour, self.brush = colour, brush
            if brush == "rest":
                self.rests += 1
            else:
                self.marks.append(e)
            self.events.append(e)
        elif kind != "refused" or not e.get("reason"):
            raise LedgerError("unknown outcome")
        self.seq = e["seq"]
        del self.pending[e["id"]]

    def public(self):
        all_marks = [m for _, marks in self.canvases for m in marks] + self.marks
        gallery = []
        for at, marks in self.canvases:
            counts = Counter(m["colour"] for m in marks)
            gallery.append(dict(file=datetime.fromtimestamp(at, timezone.utc).strftime("%Y-%m-%d-%H%M.png"),
                                marks=len(marks), dominant_colour=counts.most_common(1)[0][0] if counts else None))
        return dict(mode="paper", room=DECLARATION.public(), marks=len(all_marks), rests=self.rests,
                    colour_distribution=dict(Counter(m["colour"] for m in all_marks)), gallery=gallery,
                    canvas_marks=len(self.marks), opened_at=self.opened_at, last_seq=self.seq,
                    colour=self.colour, brush=self.brush, strokes=self.events[-100:],
                    canvas="/paintroom/canvas.png", coverage_percent=raster(self.marks)[1])


class Ledger(WriteAhead):
    def __init__(self, state_dir, clock=time.time):
        self.path = Path(state_dir) / "paintroom" / "ledger.paper.jsonl"
        self.public_path = self.path.parent / "public" / "public.json"
        self.clock, self.book = clock, Book()
        self.ok, self.error, self.publish_error = True, None, None
        try:
            if self.path.exists():
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    self.book.apply(json.loads(line))
            if self.book.book_id is None:
                self.append("open")
            for i in list(self.book.pending):
                self.terminal("refused", i, reason="interrupted")
            self.rotate()
            self.write_book()
        except (OSError, ValueError) as exc:
            self.ok, self.error = False, str(exc)

    def terminal(self, kind, i, **fields):
        event = self.append(kind, id=i, seq=self.book.seq + 1,
                            **{k: self.book.pending[i][k] for k in FIELDS}, **fields)
        self.write_book()
        return event

    def rotate(self):
        changed = False
        while self.clock() >= self.book.opened_at + ROTATE_SECONDS:
            self.append("rotate", at=self.book.opened_at + ROTATE_SECONDS)
            changed = True
        if changed:
            self.write_book()

    def write_book(self):
        if not self.ok:
            return
        try:
            public = self.book.public()
            for item, (_, marks) in zip(public["gallery"], self.book.canvases):
                path = self.path.parent / "gallery" / item["file"]
                if not path.exists():
                    atomic_write(path, png(raster(marks)[0]))
            atomic_write(self.path.parent / "canvas.png", png(raster(self.book.marks)[0]))
            strokes = [e for e in self.book.events if e["brush"] != "rest"]
            atomic_write(self.path.parent / "strokes.jsonl", "".join(json.dumps({k: e[k] for k in
                ("at", "colour", "brush", "x", "y", "size", "look_id")}) + "\n" for e in strokes).encode("utf-8"))
            atomic_write(self.public_path, json.dumps(public).encode("utf-8"))
            self.publish_error = None
        except OSError as exc:
            self.publish_error = str(exc)


class Painter(Executor):
    def __init__(self, ledger, intent_token, clock=time.time):
        self.ledger, self.intent_token, self.clock = ledger, intent_token, clock
        self.lock, self.resolver_error = threading.Lock(), None

    def intent(self, body):
        return self.guarded_intent(body, check_body, self._execute)

    def _execute(self, body):
        led = self.ledger
        led.rotate()
        i = led.append("intent", id=led.book.intents + 1, **body)["id"]
        if stale_look(body, self.clock()):
            return self.refuse(i, "stale or future look")
        if not 0 < abs(body["drive"]) <= 1:
            return self.refuse(i, "drive outside range")
        card = body["card_id"]
        event = led.terminal("fill", i, colour=card if card in COLOURS else led.book.colour,
                             brush=card if card in BRUSHES else led.book.brush)
        return 200, {"status": "booked", "event": event}

    def resolve_once(self):
        with self.lock:
            if self.ledger.ok:
                try:
                    self.ledger.rotate()
                    if self.ledger.publish_error:
                        self.ledger.write_book()
                    self.resolver_error = None
                except (OSError, ValueError) as exc:
                    self.resolver_error = str(exc)


def main():
    settings = load_env()
    if settings.get("FLY_PAINTROOM_LIVE") == "1":
        print("live painting is not built; this build is paper only", file=sys.stderr)
        return 2
    token = os.environ.get("FLY_INTENT_TOKEN")
    if not token:
        print("FLY_INTENT_TOKEN must be shared with the roamer", file=sys.stderr)
        return 2
    executor = Painter(Ledger(settings.get("FLY_STATE_DIR", "state")), token)
    server = make_server(executor, int(settings.get("FLY_PAINTROOM_PORT", "4676")))
    stop = threading.Event()
    def resolve():
        while not stop.wait(2):
            executor.resolve_once()
    worker = threading.Thread(target=resolve, daemon=True)
    worker.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
