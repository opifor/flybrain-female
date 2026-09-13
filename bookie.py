"""The paper bookie, reachable only over loopback with this boot's header.

No cap, no floor, no price test in sizing: floor(abs(drive) * free cents).
Quotes are CLOB midpoints, not promises of an executable fill. This paper
model ignores fees, spread, liquidity and orderMinSize. Live mode stops.

FLY_BETROOM_PAPER_USDC starts a new book at 100.00 by default.
FLY_BETROOM_PORT defaults to 4672. FLY_STATE_DIR holds betroom/.
FLY_INTENT_TOKEN is minted by the parent per boot and shared with roam.py.
FLY_BETROOM_LIVE=1 exits before the ledger is opened.
"""
import hmac
import json
import math
import os
import re
import sys
import threading
import time
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import betbook
from envcfg import load_env
from polymarket import Markets, binary, timestamp, winner

HOST = "127.0.0.1"
FIELDS = {"market_id", "token_id", "side", "drive", "seen_at", "look_id"}
LIVE_REFUSAL = "live betting is not built; this build is paper only"


def setting(name, default=None):
    value = load_env().get(name)
    return default if value in (None, "") else value


def check_body(body):
    if not isinstance(body, dict) or set(body) != FIELDS:
        return "the body must be exactly " + str(sorted(FIELDS))
    for key in ("market_id", "token_id"):
        if not isinstance(body[key], str) or not re.fullmatch(r"[0-9]{1,100}", body[key]):
            return f"invalid {key}"
    if body["side"] not in ("YES", "NO"):
        return "side must be YES or NO"
    for key in ("drive", "seen_at"):
        try:
            valid = type(body[key]) in (int, float) and math.isfinite(body[key])
        except OverflowError:
            valid = False
        if not valid:
            return f"invalid {key}"
    if not isinstance(body["look_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", body["look_id"]):
        return "invalid look_id"
    return None


class Bookie:
    def __init__(self, markets, ledger, intent_token, clock=time.time):
        self.markets, self.ledger, self.intent_token = markets, ledger, intent_token
        self.clock = clock
        self.lock = threading.Lock()
        self.resolver_error = None

    def health(self):
        return {"ok": self.ledger.ok, "mode": "paper",
                "balance": self.ledger.book.balance_cents / 100 if self.ledger.ok else None,
                "error": self.ledger.error, "publish_error": self.ledger.publish_error,
                "resolver_error": self.resolver_error}

    def events(self, after=0):
        with self.lock:
            if not self.ledger.ok:
                return 503, {"error": self.ledger.error, "last": None, "events": []}
            return 200, {"last": self.ledger.book.seq,
                         "events": [e for e in self.ledger.book.events if e["seq"] > after]}

    def intent(self, body):
        why = check_body(body)
        if why:
            return 400, {"status": "error", "reason": why}
        if not self.lock.acquire(blocking=False):
            return 409, {"status": "busy"}
        try:
            led = self.ledger
            if not led.ok:
                return 503, {"status": "error", "reason": led.error}
            if body["look_id"] in led.book.look_ids:
                return 409, {"status": "duplicate", "reason": "look already recorded"}
            i = led.intent(body)

            def refuse(reason):
                return 200, {"status": "refused", "event": led.terminal("refused", i, reason=reason),
                             "reason": reason}

            drive = body["drive"]
            if not 0 < abs(drive) <= 1 or (drive > 0) != (body["side"] == "YES"):
                return refuse("side disagrees with drive")
            age = self.clock() - body["seen_at"]
            if age < 0 or age > 20:
                return refuse("stale or future look")
            stake = math.floor(Fraction(abs(drive)) * led.book.balance_cents)
            if stake <= 0:
                return refuse("nothing to spend")
            try:
                raw = self.markets.market(body["market_id"])
                _, tokens, _ = binary(raw, fast=True)
                if tokens[0 if body["side"] == "YES" else 1] != body["token_id"]:
                    return refuse("outcome token does not match market")
                if raw.get("closed") is not False or raw.get("active") is not True or timestamp(raw["endDate"]) <= self.clock():
                    return refuse("market is not open")
                price = self.markets.midpoint(body["token_id"])
            except (OSError, ValueError, KeyError, TypeError) as exc:
                return refuse(f"unquotable: {exc}")
            ev = led.terminal("fill", i, question=raw["question"], stake_cents=str(stake),
                              price=str(price), shares=str(Fraction(stake, 100) / price),
                              quote_source="CLOB midpoint", quoted_at=self.clock(),
                              outcomes=raw["outcomes"])
            return 200, {"status": "booked", "event": ev}
        finally:
            self.lock.release()

    def resolve_once(self):
        with self.lock:
            if not self.ledger.ok:
                return []
            positions = list(self.ledger.book.positions.items())
        observations, events, errors = {}, [], []
        for i, pos in positions:
            market_id = pos["market_id"]
            try:
                if market_id not in observations:
                    observations[market_id] = self.markets.market(market_id)
                raw = observations[market_id]
                outcome = winner(raw)
                _, tokens, _ = binary(raw, fast=True)
                if tokens[0 if pos["side"] == "YES" else 1] != pos["token_id"]:
                    raise ValueError("resolution token differs from booked token")
                if outcome is not None:
                    with self.lock:
                        if i in self.ledger.book.positions:
                            observation = {k: raw.get(k) for k in ("id", "closed", "outcomePrices", "umaResolutionStatus")}
                            events.append(self.ledger.settle(i, outcome, observation))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f"{market_id}: {exc}")
        self.resolver_error = "; ".join(errors) if errors else None
        return events

    def resolve(self, stop):
        while not stop.is_set():
            self.resolve_once()
            stop.wait(15)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def reply(self, code, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        secret = self.server.bookie.intent_token
        return bool(secret) and hmac.compare_digest(
            (self.headers.get("X-Fly-Intent") or "").encode(), secret.encode())

    def do_GET(self):
        route = urlparse(self.path)
        if route.path == "/health":
            return self.reply(200, self.server.bookie.health())
        if not self.authed():
            return self.reply(403, {"status": "forbidden"})
        if route.path == "/events":
            try:
                after = int(parse_qs(route.query).get("after", ["0"])[0])
            except ValueError:
                return self.reply(400, {"status": "error"})
            return self.reply(*self.server.bookie.events(after))
        return self.reply(404, {"status": "error"})

    def do_POST(self):
        if not self.authed():
            return self.reply(403, {"status": "forbidden"})
        if self.path != "/intent":
            return self.reply(404, {"status": "error"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536 or self.headers.get("Transfer-Encoding"):
                return self.reply(400, {"status": "error", "reason": "invalid body length"})
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            return self.reply(400, {"status": "error", "reason": "invalid JSON"})
        try:
            return self.reply(*self.server.bookie.intent(body))
        except (OSError, ValueError) as exc:
            return self.reply(500, {"status": "error", "reason": str(exc)})


def make_server(bookie, port):
    server = ThreadingHTTPServer((HOST, int(port)), Handler)
    server.daemon_threads = True
    server.bookie = bookie
    return server


def main():
    if setting("FLY_BETROOM_LIVE") == "1":
        print(LIVE_REFUSAL, file=sys.stderr)
        return 2
    token = os.environ.get("FLY_INTENT_TOKEN")
    if not token:
        print("FLY_INTENT_TOKEN must be minted for this boot and shared with the roamer", file=sys.stderr)
        return 2
    port = int(setting("FLY_BETROOM_PORT", "4672"))
    where = betbook.paths(setting("FLY_STATE_DIR", str(Path(__file__).parent / "build")))
    start = math.floor(Fraction(setting("FLY_BETROOM_PAPER_USDC", "100.00")) * 100)
    server = make_server(Bookie(Markets(), betbook.Ledger(where["ledger"], start), token), port)
    stop = threading.Event()
    worker = threading.Thread(target=server.bookie.resolve, args=(stop,), daemon=True)
    worker.start()
    print(f"paper bookie on http://{HOST}:{port}; ledger {where['ledger']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=25)
    return 0


if __name__ == "__main__":
    sys.exit(main())
